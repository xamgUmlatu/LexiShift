from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol


@dataclass(frozen=True)
class CandidateRankingContext:
    source_phrase: str
    replacement: str
    metadata: Mapping[str, object]
    confidence: float
    semantic_demotion_scale: float = 1.0


class CandidateRankingMechanism(Protocol):
    def score(self, candidate: CandidateRankingContext) -> float: ...

    def bucket_key(self, candidate: CandidateRankingContext) -> str: ...


@dataclass(frozen=True)
class ReverseCheckScoringConfig:
    enabled: bool = False
    match_bonus: float = 0.2
    near_bonus: float = 0.1
    near_rank_max: int = 2
    far_hit_penalty: float = 0.0
    miss_penalty: float = 0.2


@dataclass(frozen=True)
class DictionaryEntryOrderRankingMechanism:
    """Ranks candidates by dictionary entry order (earlier glosses rank higher)."""

    missing_index_score: float = 0.0
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)

    def score(self, candidate: CandidateRankingContext) -> float:
        gloss_index = extract_dictionary_order_index(candidate.metadata)
        base_score = self.missing_index_score
        if gloss_index is not None:
            # 0 -> 1.0, 1 -> 0.5, 2 -> 0.333..., etc.
            base_score = 1.0 / (1.0 + float(gloss_index))
        demotion = resolve_effective_semantic_demotion(
            candidate.metadata,
            scale=candidate.semantic_demotion_scale,
        )
        if demotion > 0.0:
            base_score = max(0.0, base_score * (1.0 - demotion))
        reverse_delta = resolve_reverse_check_delta(
            candidate.metadata,
            config=self.reverse_check,
        )
        if reverse_delta != 0.0:
            base_score = _clamp_float(base_score + reverse_delta)
        return _clamp_float(base_score)

    def bucket_key(self, candidate: CandidateRankingContext) -> str:
        return resolve_dictionary_order_bucket_key(candidate)


def build_ranking_sort_key(
    candidate: CandidateRankingContext,
    *,
    score: float,
) -> tuple[float, float, str]:
    return (
        -float(score),
        -float(candidate.confidence),
        str(candidate.source_phrase or "").lower(),
    )


def extract_dictionary_order_index(metadata: Mapping[str, object]) -> Optional[int]:
    raw_index = metadata.get("gloss_index")
    if isinstance(raw_index, bool):
        return None
    if isinstance(raw_index, int):
        return raw_index if raw_index >= 0 else None
    if isinstance(raw_index, str):
        text = raw_index.strip()
        if not text:
            return None
        try:
            value = int(text)
        except ValueError:
            return None
        return value if value >= 0 else None
    return None


def resolve_dictionary_order_bucket_key(candidate: CandidateRankingContext) -> str:
    gloss_index = extract_dictionary_order_index(candidate.metadata)
    if gloss_index is not None:
        return f"gloss:{gloss_index}"
    morphology = candidate.metadata.get("morphology")
    if isinstance(morphology, Mapping):
        base = str(morphology.get("source_phrase_base") or "").strip().lower()
        if base:
            return f"base:{base}"
    source = str(candidate.source_phrase or "").strip().lower()
    return f"source:{source}"


def extract_semantic_demotion(metadata: Mapping[str, object]) -> float:
    raw = metadata.get("semantic_demotion")
    if raw is None:
        return 0.0
    if isinstance(raw, bool):
        return 1.0 if raw else 0.0
    if isinstance(raw, (int, float)):
        return _clamp_float(float(raw))
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return 0.0
        try:
            return _clamp_float(float(text))
        except ValueError:
            return 0.0
    return 0.0


def resolve_effective_semantic_demotion(
    metadata: Mapping[str, object],
    *,
    scale: float,
) -> float:
    base = extract_semantic_demotion(metadata)
    if base <= 0.0:
        return 0.0
    try:
        parsed_scale = float(scale)
    except (TypeError, ValueError):
        parsed_scale = 1.0
    if parsed_scale <= 0.0:
        return 0.0
    return _clamp_float(base * parsed_scale)


def resolve_reverse_check_delta(
    metadata: Mapping[str, object],
    *,
    config: ReverseCheckScoringConfig,
) -> float:
    if not bool(config.enabled):
        return 0.0
    supported = _extract_optional_bool(metadata.get("reverse_check_supported"))
    if supported is not True:
        return 0.0
    hit = _extract_optional_bool(metadata.get("reverse_check_hit"))
    if hit is True:
        rank = _extract_non_negative_int(metadata.get("reverse_check_rank"))
        total = _extract_non_negative_int(metadata.get("reverse_check_total"))
        match_bonus = _normalize_non_negative_float(config.match_bonus)
        near_bonus = _normalize_non_negative_float(config.near_bonus)
        near_rank_max = _normalize_non_negative_int(config.near_rank_max, default=2)
        if rank is None:
            return match_bonus
        if rank == 0:
            return match_bonus
        if rank <= near_rank_max:
            return near_bonus
        far_hit_penalty = _normalize_non_negative_float(config.far_hit_penalty)
        if far_hit_penalty <= 0.0:
            return 0.0
        return -resolve_reverse_far_hit_penalty(
            rank=rank,
            total=total,
            penalty=far_hit_penalty,
        )
    if hit is False:
        miss_penalty = _normalize_non_negative_float(config.miss_penalty)
        if miss_penalty <= 0.0:
            return 0.0
        return -miss_penalty
    return 0.0


def resolve_reverse_far_hit_penalty(
    *,
    rank: int,
    total: Optional[int],
    penalty: float,
) -> float:
    normalized_penalty = _normalize_non_negative_float(penalty)
    if normalized_penalty <= 0.0:
        return 0.0
    normalized_rank = max(0, int(rank))
    if total is None or total <= 1:
        return normalized_penalty
    max_rank = max(0, int(total) - 1)
    if max_rank <= 0:
        return normalized_penalty
    effective_rank = min(normalized_rank, max_rank)
    return normalized_penalty * (effective_rank / float(max_rank))


def _extract_optional_bool(value: object) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if not text:
            return None
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return None


def _extract_non_negative_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = int(text)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def _normalize_non_negative_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0.0
        try:
            return max(0.0, float(text))
        except ValueError:
            return 0.0
    return 0.0


def _normalize_non_negative_int(value: object, *, default: int = 0) -> int:
    parsed = _extract_non_negative_int(value)
    if parsed is None:
        return max(0, int(default))
    return parsed


def _clamp_float(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))
