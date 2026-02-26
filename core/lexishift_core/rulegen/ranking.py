from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Protocol


@dataclass(frozen=True)
class CandidateRankingContext:
    source_phrase: str
    replacement: str
    metadata: Mapping[str, object]
    confidence: float
    semantic_demotion_scale: float = 1.0


class CandidateRankingMechanism(Protocol):
    def score(self, candidate: CandidateRankingContext) -> float:
        ...

    def bucket_key(self, candidate: CandidateRankingContext) -> str:
        ...


@dataclass(frozen=True)
class DictionaryEntryOrderRankingMechanism:
    """Ranks candidates by dictionary entry order (earlier glosses rank higher)."""

    missing_index_score: float = 0.0

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
        if demotion <= 0.0:
            return base_score
        return max(0.0, base_score * (1.0 - demotion))

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


def _clamp_float(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))
