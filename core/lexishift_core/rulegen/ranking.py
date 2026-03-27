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
    exact_hit_ambiguity_threshold: int = 0
    exact_hit_ambiguity_penalty: float = 0.0
    exact_hit_specificity_bonus: float = 0.0


@dataclass(frozen=True)
class DictionaryEntryOrderRankingMechanism:
    """Ranks candidates by dictionary entry order (earlier glosses rank higher)."""

    missing_index_score: float = 0.0
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)

    def score(self, candidate: CandidateRankingContext) -> float:
        gloss_index = extract_dictionary_order_index(candidate.metadata)
        semantic_demotion = extract_semantic_demotion(candidate.metadata)
        reverse_check_supported = _extract_optional_bool(
            candidate.metadata.get("reverse_check_supported")
        )
        reverse_check_hit = _extract_optional_bool(candidate.metadata.get("reverse_check_hit"))
        reverse_check_rank = _extract_non_negative_int(candidate.metadata.get("reverse_check_rank"))
        reverse_check_total = _extract_non_negative_int(
            candidate.metadata.get("reverse_check_total")
        )
        return score_dictionary_entry_order_values(
            gloss_index=gloss_index,
            semantic_demotion=semantic_demotion,
            semantic_demotion_scale=candidate.semantic_demotion_scale,
            reverse_check_supported=reverse_check_supported,
            reverse_check_hit=reverse_check_hit,
            reverse_check_rank=reverse_check_rank,
            reverse_check_total=reverse_check_total,
            missing_index_score=self.missing_index_score,
            reverse_check=self.reverse_check,
        )

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


def resolve_dictionary_order_base_score(
    *,
    gloss_index: Optional[int],
    missing_index_score: float = 0.0,
) -> float:
    if gloss_index is None:
        return _clamp_float(missing_index_score)
    return _clamp_float(1.0 / (1.0 + float(gloss_index)))


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
    bucket_override = str(candidate.metadata.get("definition_bucket_key") or "").strip().lower()
    if bucket_override:
        return bucket_override
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


def resolve_effective_semantic_demotion_value(
    *,
    semantic_demotion: float,
    scale: float,
) -> float:
    try:
        base = _clamp_float(float(semantic_demotion))
    except (TypeError, ValueError):
        base = 0.0
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
            exact_hit_specificity_bonus = resolve_reverse_exact_hit_specificity_bonus(
                total=total,
                config=config,
            )
            exact_hit_ambiguity_penalty = resolve_reverse_exact_hit_ambiguity_penalty(
                total=total,
                config=config,
            )
            return match_bonus + exact_hit_specificity_bonus - exact_hit_ambiguity_penalty
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


def resolve_reverse_check_delta_from_values(
    *,
    supported: Optional[bool],
    hit: Optional[bool],
    rank: Optional[int],
    total: Optional[int],
    config: ReverseCheckScoringConfig,
) -> float:
    if not bool(config.enabled):
        return 0.0
    if supported is not True:
        return 0.0
    if hit is True:
        match_bonus = _normalize_non_negative_float(config.match_bonus)
        near_bonus = _normalize_non_negative_float(config.near_bonus)
        near_rank_max = _normalize_non_negative_int(config.near_rank_max, default=2)
        if rank is None:
            return match_bonus
        if rank == 0:
            exact_hit_specificity_bonus = resolve_reverse_exact_hit_specificity_bonus(
                total=total,
                config=config,
            )
            exact_hit_ambiguity_penalty = resolve_reverse_exact_hit_ambiguity_penalty(
                total=total,
                config=config,
            )
            return match_bonus + exact_hit_specificity_bonus - exact_hit_ambiguity_penalty
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


def score_dictionary_entry_order_values(
    *,
    gloss_index: Optional[int],
    semantic_demotion: float,
    semantic_demotion_scale: float,
    reverse_check_supported: Optional[bool],
    reverse_check_hit: Optional[bool],
    reverse_check_rank: Optional[int],
    reverse_check_total: Optional[int],
    missing_index_score: float = 0.0,
    reverse_check: Optional[ReverseCheckScoringConfig] = None,
) -> float:
    base_score = resolve_dictionary_order_base_score(
        gloss_index=gloss_index,
        missing_index_score=missing_index_score,
    )
    effective_demotion = resolve_effective_semantic_demotion_value(
        semantic_demotion=semantic_demotion,
        scale=semantic_demotion_scale,
    )
    if effective_demotion > 0.0:
        base_score = max(0.0, base_score * (1.0 - effective_demotion))
    reverse_delta = resolve_reverse_check_delta_from_values(
        supported=reverse_check_supported,
        hit=reverse_check_hit,
        rank=reverse_check_rank,
        total=reverse_check_total,
        config=reverse_check or ReverseCheckScoringConfig(),
    )
    if reverse_delta != 0.0:
        base_score = _clamp_float(base_score + reverse_delta)
    return _clamp_float(base_score)


def resolve_reverse_check_strength(
    metadata: Mapping[str, object],
    *,
    config: ReverseCheckScoringConfig,
) -> Optional[float]:
    supported = _extract_optional_bool(metadata.get("reverse_check_supported"))
    hit = _extract_optional_bool(metadata.get("reverse_check_hit"))
    rank = _extract_non_negative_int(metadata.get("reverse_check_rank"))
    total = _extract_non_negative_int(metadata.get("reverse_check_total"))
    return resolve_reverse_check_strength_from_values(
        supported=supported,
        hit=hit,
        rank=rank,
        total=total,
        config=config,
    )


def resolve_reverse_check_strength_from_values(
    *,
    supported: Optional[bool],
    hit: Optional[bool],
    rank: Optional[int],
    total: Optional[int],
    config: ReverseCheckScoringConfig,
) -> Optional[float]:
    if supported is not True:
        return None
    if hit is not True:
        return 0.0
    if rank is None or rank == 0:
        return 1.0
    if total is not None and total > 1:
        max_rank = max(0, int(total) - 1)
        if max_rank <= 0:
            return 1.0
        effective_rank = min(max(0, int(rank)), max_rank)
        return _clamp_float(1.0 - (effective_rank / float(max_rank)))
    near_rank_max = _normalize_non_negative_int(config.near_rank_max, default=2)
    if rank <= near_rank_max:
        return 0.75
    return 0.25


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


def resolve_reverse_exact_hit_ambiguity_penalty(
    *,
    total: Optional[int],
    config: ReverseCheckScoringConfig,
) -> float:
    threshold = _normalize_non_negative_int(config.exact_hit_ambiguity_threshold, default=0)
    penalty = _normalize_non_negative_float(config.exact_hit_ambiguity_penalty)
    if penalty <= 0.0 or threshold <= 0 or total is None or total <= threshold:
        return 0.0
    overflow = max(0, int(total) - threshold)
    span = max(1, threshold)
    scale = min(1.0, overflow / float(span))
    return penalty * scale


def resolve_reverse_exact_hit_specificity_bonus(
    *,
    total: Optional[int],
    config: ReverseCheckScoringConfig,
) -> float:
    bonus = _normalize_non_negative_float(config.exact_hit_specificity_bonus)
    if bonus <= 0.0 or total is None:
        return 0.0
    normalized_total = max(1, int(total))
    return bonus / float(normalized_total)


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
