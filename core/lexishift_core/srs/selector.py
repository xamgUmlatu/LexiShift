from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Iterable, Mapping, Optional, Sequence

SELECTION_POLICY_TOP_N = "top_n"
SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT = "weighted_without_replacement"
SUPPORTED_SELECTION_POLICIES = {
    SELECTION_POLICY_TOP_N,
    SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
}


@dataclass(frozen=True)
class SelectorWeights:
    base_freq: float = 0.55
    topic_bias: float = 0.15
    scarcity_bonus: float = 0.0
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
    sampling_baseline_alpha: float = 0.35
    sampling_temperature: float = 1.0
    sampling_min_mass: float = 0.001


@dataclass(frozen=True)
class SelectorCandidate:
    lemma: str
    language_pair: str
    base_freq: float = 0.0
    topic_bias: float = 0.0
    scarcity_bonus: float = 0.0
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
    allowed_pos_set = {
        str(value).strip().lower() for value in (allowed_pos or set()) if str(value).strip()
    }
    result: list[SelectorCandidate] = []
    for item in candidates:
        if not item.lemma or item.lemma in blocked or item.lemma in existing:
            continue
        if allowed_pairs_set and item.language_pair not in allowed_pairs_set:
            continue
        item_pos = str(item.pos or "").strip().lower()
        if not item_pos and isinstance(item.metadata, Mapping):
            item_pos = str(item.metadata.get("pos_bucket") or "").strip().lower()
        if allowed_pos_set and item_pos and item_pos not in allowed_pos_set:
            continue
        result.append(item)
    return result


def score_candidate(candidate: SelectorCandidate, config: SelectorConfig) -> ScoredCandidate:
    weights = config.weights
    components = {
        "base_freq": candidate.base_freq * weights.base_freq,
        "topic_bias": candidate.topic_bias * weights.topic_bias,
        "scarcity_bonus": candidate.scarcity_bonus * weights.scarcity_bonus,
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


def resolve_selection_policy(config: SelectorConfig) -> str:
    policy = str(config.selection_policy or "").strip().lower()
    if policy not in SUPPORTED_SELECTION_POLICIES:
        return SELECTION_POLICY_TOP_N
    return policy


def resolve_selection_mass(entry: ScoredCandidate, config: SelectorConfig) -> float:
    baseline_alpha = _clamp_01(config.sampling_baseline_alpha)
    score_temperature = max(0.05, float(config.sampling_temperature))
    base_mass = max(0.0, float(entry.candidate.base_freq))
    score_mass = max(0.0, float(entry.breakdown.final_score))
    if score_mass > 0.0 and score_temperature != 1.0:
        score_mass = score_mass ** (1.0 / score_temperature)
    combined_mass = (baseline_alpha * base_mass) + ((1.0 - baseline_alpha) * score_mass)
    if combined_mass <= 0.0:
        return 0.0
    return max(float(config.sampling_min_mass), combined_mass)


def select_candidates(
    candidates: Iterable[SelectorCandidate],
    *,
    config: Optional[SelectorConfig] = None,
    selection_count: Optional[int] = None,
    seed: Optional[int] = None,
) -> list[ScoredCandidate]:
    config = config or SelectorConfig()
    scored = rank_candidates(candidates, config=config)
    target = _resolve_selection_count(selection_count, fallback=config.top_n)
    return select_scored_candidates(
        scored,
        config=config,
        selection_count=target,
        seed=seed,
    )


def select_scored_candidates(
    scored: Sequence[ScoredCandidate],
    *,
    config: SelectorConfig,
    selection_count: Optional[int] = None,
    seed: Optional[int] = None,
) -> list[ScoredCandidate]:
    target = _resolve_selection_count(selection_count, fallback=config.top_n)
    if target <= 0 or not scored:
        return []
    ranked = list(scored)
    if target >= len(ranked):
        return ranked
    if resolve_selection_policy(config) == SELECTION_POLICY_TOP_N:
        return ranked[:target]
    masses = [resolve_selection_mass(entry, config) for entry in ranked]
    selected = _weighted_sample_scored_without_replacement(
        ranked,
        weights=masses,
        selection_count=target,
        seed=seed,
    )
    selected.sort(
        key=lambda entry: (
            -float(entry.breakdown.final_score),
            str(entry.candidate.lemma or ""),
        )
    )
    return selected


def _weighted_sample_scored_without_replacement(
    scored: Sequence[ScoredCandidate],
    *,
    weights: Sequence[float],
    selection_count: int,
    seed: Optional[int],
) -> list[ScoredCandidate]:
    rng = random.Random(seed)
    pool = list(zip(scored, weights))
    selected: list[ScoredCandidate] = []
    target = max(0, int(selection_count))
    while len(selected) < target and pool:
        total = sum(max(0.0, float(weight)) for _entry, weight in pool)
        if total <= 0.0:
            break
        roll = rng.random() * total
        pick_index = len(pool) - 1
        for index, (_entry, weight) in enumerate(pool):
            roll -= max(0.0, float(weight))
            if roll <= 0.0:
                pick_index = index
                break
        entry, _weight = pool.pop(pick_index)
        selected.append(entry)
    return selected


def _resolve_selection_count(value: Optional[int], *, fallback: int) -> int:
    if value is None:
        return max(0, int(fallback))
    return max(0, int(value))


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
