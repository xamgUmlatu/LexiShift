from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class SelectorWeights:
    base_freq: float = 0.55
    topic_bias: float = 0.15
    user_pref: float = 0.10
    confidence: float = 0.10
    difficulty_target: float = 0.10


@dataclass(frozen=True)
class SelectorPenalties:
    recency_threshold: float = 0.25
    recency_multiplier: float = 0.30
    mastered_multiplier: float = 0.20
    oversubscribed_multiplier: float = 0.80


@dataclass(frozen=True)
class SelectorConfig:
    weights: SelectorWeights = field(default_factory=SelectorWeights)
    penalties: SelectorPenalties = field(default_factory=SelectorPenalties)
    selection_policy: str = "top_n"  # top_n, weighted_sample, hybrid
    top_n: int = 20


@dataclass(frozen=True)
class SelectorCandidate:
    lemma: str
    language_pair: str
    base_freq: float = 0.0
    topic_bias: float = 0.0
    user_pref: float = 0.0
    confidence: float = 0.0
    difficulty_target: float = 0.0
    recency: Optional[float] = None
    source_type: Optional[str] = None
    pos: Optional[str] = None
    mastered: bool = False
    oversubscribed: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoreBreakdown:
    components: Mapping[str, float]
    weighted_sum: float
    penalties: Sequence[str]
    final_score: float


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: SelectorCandidate
    breakdown: ScoreBreakdown


def filter_candidates(
    candidates: Iterable[SelectorCandidate],
    *,
    blocked_lemmas: Optional[set[str]] = None,
    in_s: Optional[set[str]] = None,
    allowed_pairs: Optional[Sequence[str]] = None,
    allowed_pos: Optional[set[str]] = None,
) -> list[SelectorCandidate]:
    blocked = blocked_lemmas or set()
    existing = in_s or set()
    allowed_pairs_set = set(allowed_pairs or [])
    result: list[SelectorCandidate] = []
    for item in candidates:
        if not item.lemma or item.lemma in blocked or item.lemma in existing:
            continue
        if allowed_pairs_set and item.language_pair not in allowed_pairs_set:
            continue
        if allowed_pos and item.pos and item.pos not in allowed_pos:
            continue
        result.append(item)
    return result


def score_candidate(candidate: SelectorCandidate, config: SelectorConfig) -> ScoredCandidate:
    weights = config.weights
    components = {
        "base_freq": candidate.base_freq * weights.base_freq,
        "topic_bias": candidate.topic_bias * weights.topic_bias,
        "user_pref": candidate.user_pref * weights.user_pref,
        "confidence": candidate.confidence * weights.confidence,
        "difficulty_target": candidate.difficulty_target * weights.difficulty_target,
    }
    weighted_sum = sum(components.values())
    penalties: list[str] = []
    score = weighted_sum

    recency = candidate.recency
    if recency is not None and recency < config.penalties.recency_threshold:
        score *= config.penalties.recency_multiplier
        penalties.append("recent")

    if candidate.mastered:
        score *= config.penalties.mastered_multiplier
        penalties.append("mastered")

    if candidate.oversubscribed:
        score *= config.penalties.oversubscribed_multiplier
        penalties.append("oversubscribed")

    return ScoredCandidate(
        candidate=candidate,
        breakdown=ScoreBreakdown(
            components=components,
            weighted_sum=weighted_sum,
            penalties=tuple(penalties),
            final_score=score,
        ),
    )


def rank_candidates(
    candidates: Iterable[SelectorCandidate],
    *,
    config: Optional[SelectorConfig] = None,
) -> list[ScoredCandidate]:
    config = config or SelectorConfig()
    scored = [score_candidate(item, config) for item in candidates]
    scored.sort(key=lambda entry: entry.breakdown.final_score, reverse=True)
    return scored
