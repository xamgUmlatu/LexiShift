from __future__ import annotations

import math
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.admission_features import (
    AdmissionCandidateFeatures,
    AdmissionProfileFeatures,
    AdmissionUtilitySignals,
    clamp01,
    expand_topic_token_family,
    is_background_topic_token,
    rounded_or_none as admission_rounded_or_none,
    safe_optional_float,
)
from lexishift_core.srs.selector import resolve_selection_mass


def build_policy_summary(policy: object) -> dict[str, object]:
    return {
        "version": policy.version,
        "difficulty_proxy": policy.difficulty_proxy,
        "topic_metadata_keys": list(policy.topic_metadata_keys),
        "topic_exact_match_multiplier": rounded_or_none(policy.topic_exact_match_multiplier),
        "proficiency_taper_width": rounded_or_none(policy.proficiency_taper_width),
        "challenge_default_spread": rounded_or_none(policy.challenge_default_spread),
        "challenge_min_spread": rounded_or_none(policy.challenge_min_spread),
        "explanation_component_floor": rounded_or_none(policy.explanation_component_floor),
        "topic_specificity_floor": rounded_or_none(policy.topic_specificity_floor),
        "scarcity_support_min_count": int(policy.scarcity_support_min_count),
        "scarcity_support_min_mass": rounded_or_none(policy.scarcity_support_min_mass),
        "scarcity_support_mass_proxy": policy.scarcity_support_mass_proxy,
        "scarcity_bonus_enabled": bool(policy.scarcity_bonus_enabled),
        "scarcity_bonus_target_mass": rounded_or_none(policy.scarcity_bonus_target_mass),
        "scarcity_bonus_mass_smoothing": rounded_or_none(policy.scarcity_bonus_mass_smoothing),
        "scarcity_bonus_mass_exponent": rounded_or_none(policy.scarcity_bonus_mass_exponent),
        "scarcity_bonus_max_extra": rounded_or_none(policy.scarcity_bonus_max_extra),
        "utility_shape": {
            "positive_terms": [
                "proficiency_fit",
                "challenge_fit",
                "topic_affinity",
                "scarcity_bonus",
                "coverage_gain",
            ],
            "negative_terms": ["lexical_risk", "redundancy"],
            "exploration_terms": ["exploration_bonus"],
        },
    }


def compute_topic_affinity(
    traits: AdmissionCandidateFeatures,
    context: AdmissionProfileFeatures,
    *,
    policy: object,
) -> tuple[float, Optional[str], float, int, int]:
    if not context.topic_weights:
        return 0.0, None, 0.0, 0, 0
    strongest_source = None
    strongest_value = 0.0
    for topic_hint in traits.topic_hints:
        weight = float(context.topic_weights.get(topic_hint, 0.0))
        if weight > strongest_value:
            strongest_value = weight
            strongest_source = _format_topic_affinity_source(
                canonical_topic=topic_hint,
                origins=traits.topic_hint_origins.get(topic_hint),
            )
    for lexical_form in traits.lexical_forms:
        weight = float(context.topic_weights.get(lexical_form, 0.0))
        lexical_score = clamp01(weight * policy.topic_exact_match_multiplier) or 0.0
        if lexical_score > strongest_value:
            strongest_value = lexical_score
            strongest_source = f"lexical:{lexical_form}"
    if strongest_value <= 0.0:
        return 0.0, strongest_source, 0.0, 0, 0

    topic_specificity, topic_support_count, topic_hint_count = _compute_topic_specificity(
        traits,
        context,
        policy=policy,
    )
    dampened_value = clamp01(strongest_value * topic_specificity) or 0.0
    return (
        dampened_value,
        strongest_source,
        topic_specificity,
        topic_support_count,
        topic_hint_count,
    )


def build_active_topic_support_summary(
    seed_traits: Sequence[tuple[int, object, AdmissionCandidateFeatures]],
    context: AdmissionProfileFeatures,
    *,
    policy: object,
) -> dict[str, object]:
    active_topics = [
        (
            str(topic or "").strip(),
            float(weight or 0.0),
            str(context.topic_weight_sources.get(topic, "") or "").strip() or None,
        )
        for topic, weight in context.topic_weights.items()
        if float(weight or 0.0) > 0.0 and str(topic or "").strip()
    ]
    active_topics.sort(key=lambda item: (-item[1], item[0]))
    total_candidates = len(seed_traits)
    total_base_mass = sum(max(0.0, float(entry[2].lexical_commonness)) for entry in seed_traits)
    topic_entries: list[dict[str, object]] = []
    for topic_name, requested_weight, weight_source in active_topics:
        candidate_count = 0
        support_mass = 0.0
        specificity_total = 0.0
        contribution_examples: list[tuple[float, str]] = []
        for _base_index, seed, traits in seed_traits:
            topic_specificity, topic_support_count, topic_hint_count = (
                _compute_topic_specificity_for_topic(
                    traits,
                    topic_name,
                    policy=policy,
                )
            )
            if topic_support_count <= 0 or topic_specificity <= 0.0:
                continue
            candidate_count += 1
            specificity_total += topic_specificity
            contribution = float(traits.lexical_commonness) * topic_specificity
            support_mass += contribution
            lemma = str(getattr(seed, "lemma", "") or "").strip()
            if lemma:
                contribution_examples.append((contribution, lemma))
        insufficient_reasons: list[str] = []
        if candidate_count < int(policy.scarcity_support_min_count):
            insufficient_reasons.append("support_count_below_min")
        if support_mass < float(policy.scarcity_support_min_mass):
            insufficient_reasons.append("support_mass_below_min")
        scarcity_multiplier = _compute_topic_scarcity_multiplier(
            support_mass,
            eligible_for_scarcity_calibration=not insufficient_reasons,
            policy=policy,
        )
        contribution_examples.sort(key=lambda item: (-item[0], item[1]))
        topic_entries.append(
            {
                "topic": topic_name,
                "requested_weight": rounded_or_none(requested_weight),
                "weight_source": weight_source,
                "candidate_count": int(candidate_count),
                "candidate_ratio": rounded_or_none(
                    candidate_count / float(max(1, total_candidates))
                ),
                "support_mass": rounded_or_none(support_mass),
                "support_mass_ratio": rounded_or_none(
                    support_mass / float(max(1e-9, total_base_mass))
                ),
                "mean_topic_specificity": rounded_or_none(
                    specificity_total / float(max(1, candidate_count))
                ),
                "scarcity_multiplier_preview": rounded_or_none(scarcity_multiplier),
                "eligible_for_scarcity_calibration": not insufficient_reasons,
                "scarcity_readiness": (
                    "eligible" if not insufficient_reasons else "insufficient_labeled_support"
                ),
                "scarcity_readiness_reasons": insufficient_reasons,
                "top_examples": [lemma for _contribution, lemma in contribution_examples[:5]],
            }
        )
    return {
        "scope": "neutral_seed_frontier",
        "total_candidates": int(total_candidates),
        "total_base_mass": rounded_or_none(total_base_mass),
        "scarcity_support_min_count": int(policy.scarcity_support_min_count),
        "scarcity_support_min_mass": rounded_or_none(policy.scarcity_support_min_mass),
        "scarcity_support_mass_proxy": policy.scarcity_support_mass_proxy,
        "topics": topic_entries,
    }


def compute_scarcity_bonus(
    traits: AdmissionCandidateFeatures,
    context: AdmissionProfileFeatures,
    *,
    active_topic_support: Optional[Mapping[str, Mapping[str, object]]],
    policy: object,
) -> tuple[float, Optional[str]]:
    if not policy.scarcity_bonus_enabled or not context.topic_weights or not active_topic_support:
        return 0.0, None
    strongest_bonus = 0.0
    strongest_source = None
    for topic_hint in traits.topic_hints:
        topic_name = str(topic_hint or "").strip()
        if not topic_name:
            continue
        topic_entry = active_topic_support.get(topic_name)
        if not isinstance(topic_entry, Mapping):
            continue
        if not bool(topic_entry.get("eligible_for_scarcity_calibration")):
            continue
        multiplier = safe_optional_float(topic_entry.get("scarcity_multiplier_preview")) or 1.0
        extra = max(0.0, float(multiplier) - 1.0)
        if extra <= 0.0:
            continue
        weight = float(context.topic_weights.get(topic_name, 0.0))
        if weight <= 0.0:
            continue
        topic_specificity, topic_support_count, _topic_hint_count = (
            _compute_topic_specificity_for_topic(
                traits,
                topic_name,
                policy=policy,
            )
        )
        if topic_support_count <= 0 or topic_specificity <= 0.0:
            continue
        base_affinity = clamp01(weight * topic_specificity) or 0.0
        bonus = base_affinity * extra
        if bonus > strongest_bonus:
            strongest_bonus = bonus
            strongest_source = f"topic:{topic_name}"
    return clamp01(strongest_bonus) or 0.0, strongest_source


def compute_proficiency_fit(
    difficulty_estimate: float,
    proficiency_estimate: Optional[float],
    *,
    policy: object,
) -> float:
    if proficiency_estimate is None:
        return 0.0
    if difficulty_estimate <= proficiency_estimate:
        return 1.0
    gap = difficulty_estimate - proficiency_estimate
    return clamp01(1.0 - (gap / policy.proficiency_taper_width)) or 0.0


def compute_challenge_fit(
    difficulty_estimate: float,
    challenge_target: Optional[float],
    challenge_spread: Optional[float],
    *,
    policy: object,
) -> float:
    if challenge_target is None:
        return 0.0
    effective_spread = max(
        policy.challenge_min_spread,
        float(challenge_spread or policy.challenge_default_spread),
    )
    distance = difficulty_estimate - challenge_target
    return clamp01(math.exp(-0.5 * ((distance / effective_spread) ** 2))) or 0.0


def build_preview_entry(
    *,
    reranked_rank: int,
    seed: object,
    traits: AdmissionCandidateFeatures,
    signal_pack: AdmissionUtilitySignals,
    scored_candidate: object,
    base_rank: int,
    policy: object,
) -> dict[str, object]:
    weighted_profile_components = {
        "topic_affinity": float(scored_candidate.breakdown.components.get("topic_bias", 0.0)),
        "scarcity_bonus": float(scored_candidate.breakdown.components.get("scarcity_bonus", 0.0)),
        "proficiency_fit": float(scored_candidate.breakdown.components.get("user_pref", 0.0)),
        "challenge_fit": float(scored_candidate.breakdown.components.get("difficulty_target", 0.0)),
    }
    ranked_profile_components = sorted(
        weighted_profile_components.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    active_profile_drivers = [
        name
        for name, value in ranked_profile_components
        if value >= policy.explanation_component_floor
    ]
    coverage_component = float(scored_candidate.breakdown.components.get("base_freq", 0.0))
    has_coverage_support = coverage_component >= policy.explanation_component_floor
    rank_delta = base_rank - reranked_rank if base_rank else 0
    explanation = _build_explanation(
        rank_delta=rank_delta,
        active_profile_drivers=active_profile_drivers,
        has_coverage_support=has_coverage_support,
    )
    return {
        "lemma": str(getattr(seed, "lemma", "") or "").strip(),
        "base_rank": base_rank,
        "reranked_rank": reranked_rank,
        "rank_delta": rank_delta,
        "pos_bucket": str(getattr(seed, "pos_bucket", "") or "").strip() or None,
        "base_weight": rounded_or_none(safe_optional_float(getattr(seed, "base_weight", None))),
        "admission_weight": rounded_or_none(
            safe_optional_float(getattr(seed, "admission_weight", None))
        ),
        "profile_score": round(float(scored_candidate.breakdown.final_score), 6),
        "selection_mass": round(
            float(resolve_selection_mass(scored_candidate, policy.selector_config)),
            6,
        ),
        "candidate_traits": traits.to_dict(),
        "admission_candidate_features": traits.to_dict(),
        "signals": {
            **signal_pack.to_dict(),
            "topic_affinity_source": signal_pack.topic_affinity_source,
        },
        "utility_signals": signal_pack.to_dict(),
        "weighted_components": {
            key: round(float(value), 6)
            for key, value in scored_candidate.breakdown.components.items()
        },
        "active_profile_drivers": list(active_profile_drivers),
        "has_coverage_support": has_coverage_support,
        "utility_weighted_components": {
            "coverage_gain": round(
                float(scored_candidate.breakdown.components.get("base_freq", 0.0)), 6
            ),
            "topic_affinity": round(
                float(scored_candidate.breakdown.components.get("topic_bias", 0.0)),
                6,
            ),
            "scarcity_bonus": round(
                float(scored_candidate.breakdown.components.get("scarcity_bonus", 0.0)),
                6,
            ),
            "proficiency_fit": round(
                float(scored_candidate.breakdown.components.get("user_pref", 0.0)),
                6,
            ),
            "challenge_fit": round(
                float(scored_candidate.breakdown.components.get("difficulty_target", 0.0)),
                6,
            ),
            "lexical_risk": 0.0,
            "redundancy": 0.0,
            "exploration_bonus": 0.0,
        },
        "explanation": explanation,
    }


def rounded_or_none(value: Optional[float]) -> Optional[float]:
    return admission_rounded_or_none(value)


def _compute_topic_specificity(
    traits: AdmissionCandidateFeatures,
    context: AdmissionProfileFeatures,
    *,
    policy: object,
) -> tuple[float, int, int]:
    active_topics = {
        str(topic or "").strip()
        for topic, weight in context.topic_weights.items()
        if float(weight or 0.0) > 0.0 and str(topic or "").strip()
    }
    if not active_topics:
        return 0.0, 0, 0

    raw_hints = [
        str(topic or "").strip() for topic in traits.raw_topic_hints if str(topic or "").strip()
    ]
    if not raw_hints:
        return 1.0, 0, 0

    significant_hints = [topic for topic in raw_hints if not is_background_topic_token(topic)]
    effective_hints = significant_hints or raw_hints
    support_count = 0
    for raw_hint in effective_hints:
        expanded_hint_family = set(expand_topic_token_family(raw_hint))
        if expanded_hint_family & active_topics:
            support_count += 1
    hint_count = len(effective_hints)
    if hint_count <= 0:
        return 1.0, support_count, 0
    support_ratio = support_count / float(hint_count)
    specificity = max(
        float(policy.topic_specificity_floor),
        math.sqrt(max(0.0, support_ratio)),
    )
    return clamp01(specificity) or 0.0, support_count, hint_count


def _format_topic_affinity_source(
    *,
    canonical_topic: str,
    origins: Optional[Sequence[str]],
) -> str:
    normalized_canonical = str(canonical_topic or "").strip()
    if not normalized_canonical:
        return "topic_hint"
    ordered_origins = [
        str(origin or "").strip() for origin in (origins or ()) if str(origin or "").strip()
    ]
    if not ordered_origins:
        return f"topic_hint:{normalized_canonical}"
    if normalized_canonical in ordered_origins:
        return f"topic_hint:{normalized_canonical}"
    if len(ordered_origins) == 1:
        return f"topic_hint:{ordered_origins[0]}->{normalized_canonical}"
    return f"topic_hint:{'+'.join(ordered_origins)}->{normalized_canonical}"


def _compute_topic_scarcity_multiplier(
    support_mass: float,
    *,
    eligible_for_scarcity_calibration: bool,
    policy: object,
) -> float:
    if not policy.scarcity_bonus_enabled or not eligible_for_scarcity_calibration:
        return 1.0
    effective_mass = max(
        1e-9,
        float(support_mass) + float(policy.scarcity_bonus_mass_smoothing),
    )
    target_mass = max(1e-9, float(policy.scarcity_bonus_target_mass))
    if effective_mass >= target_mass:
        return 1.0
    ratio = target_mass / effective_mass
    extra = max(0.0, (ratio ** float(policy.scarcity_bonus_mass_exponent)) - 1.0)
    bounded_extra = min(float(policy.scarcity_bonus_max_extra), extra)
    return max(1.0, 1.0 + bounded_extra)


def _compute_topic_specificity_for_topic(
    traits: AdmissionCandidateFeatures,
    active_topic: str,
    *,
    policy: object,
) -> tuple[float, int, int]:
    normalized_topic = str(active_topic or "").strip()
    if not normalized_topic:
        return 0.0, 0, 0
    raw_hints = [
        str(topic or "").strip() for topic in traits.raw_topic_hints if str(topic or "").strip()
    ]
    if not raw_hints:
        return 0.0, 0, 0
    significant_hints = [topic for topic in raw_hints if not is_background_topic_token(topic)]
    effective_hints = significant_hints or raw_hints
    support_count = 0
    for raw_hint in effective_hints:
        expanded_hint_family = set(expand_topic_token_family(raw_hint))
        if normalized_topic in expanded_hint_family:
            support_count += 1
    hint_count = len(effective_hints)
    if support_count <= 0 or hint_count <= 0:
        return 0.0, support_count, hint_count
    support_ratio = support_count / float(hint_count)
    specificity = max(
        float(policy.topic_specificity_floor),
        math.sqrt(max(0.0, support_ratio)),
    )
    return clamp01(specificity) or 0.0, support_count, hint_count


def _build_explanation(
    *,
    rank_delta: int,
    active_profile_drivers: Sequence[str],
    has_coverage_support: bool,
) -> str:
    if rank_delta > 0 and active_profile_drivers:
        if has_coverage_support:
            return (
                f"Boosted by {', '.join(active_profile_drivers[:2])}, while remaining "
                "supported by coverage_gain."
            )
        return f"Boosted by {', '.join(active_profile_drivers[:2])}."
    if rank_delta > 0 and has_coverage_support:
        return "Moved up with strong coverage_gain while nearby profile signals stayed neutral."
    if rank_delta < 0 and active_profile_drivers:
        if has_coverage_support:
            return (
                "Still supported by coverage_gain and "
                f"{', '.join(active_profile_drivers[:2])}, but moved down because other items "
                "received stronger overall profile lift."
            )
        return (
            "Demoted relative to the neutral frequency order despite "
            f"{', '.join(active_profile_drivers[:2])} because other items received stronger "
            "overall profile lift."
        )
    if rank_delta < 0 and has_coverage_support:
        return (
            "Still supported by coverage_gain, but moved down because other items received "
            "stronger overall profile lift."
        )
    if rank_delta < 0:
        return (
            "Demoted relative to the neutral frequency order because nearby items matched the "
            "profile better."
        )
    if not active_profile_drivers:
        return "Kept in neutral frequency order because profile signals were effectively neutral."
    if active_profile_drivers:
        if has_coverage_support:
            return (
                "Kept near frequency order with support from coverage_gain; strongest profile "
                f"signal was {active_profile_drivers[0]}."
            )
        return (
            f"Kept near frequency order; strongest profile signal was {active_profile_drivers[0]}."
        )
    return "Kept in neutral frequency order because profile signals were effectively neutral."
