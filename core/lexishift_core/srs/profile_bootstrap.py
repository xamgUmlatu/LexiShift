from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.admission_features import (
    AdmissionCandidateFeatures,
    AdmissionProfileFeatures,
    AdmissionUtilitySignals,
    clamp01,
    expand_topic_token_family,
    is_background_topic_token,
    mapping_or_empty,
    normalize_admission_profile_features,
    normalize_topic_string_list_with_origins,
    normalize_topic_token,
    rounded_or_none as admission_rounded_or_none,
    safe_optional_float,
)
from lexishift_core.srs.selector import (
    ScoredCandidate,
    SelectorCandidate,
    SelectorConfig,
    SelectorWeights,
    resolve_selection_mass,
    score_candidate,
)

PROFILE_BOOTSTRAP_POLICY_VERSION = "profile_bootstrap_policy_v2"
PROFILE_BOOTSTRAP_SELECTOR_VERSION = "profile_bootstrap_v3"


@dataclass(frozen=True)
class ProfileBootstrapPolicy:
    version: str = PROFILE_BOOTSTRAP_POLICY_VERSION
    selector_config: SelectorConfig = field(
        default_factory=lambda: SelectorConfig(
            weights=SelectorWeights(
                base_freq=0.55,
                topic_bias=0.15,
                scarcity_bonus=0.05,
                user_pref=0.10,
                confidence=0.0,
                difficulty_target=0.10,
            )
        )
    )
    difficulty_proxy: str = "1_minus_admission_weight"
    topic_metadata_keys: Sequence[str] = (
        "sense_topics",
        "topics",
        "topic",
        "profile_topics",
    )
    topic_exact_match_multiplier: float = 1.0
    proficiency_taper_width: float = 0.75
    challenge_default_spread: float = 0.18
    challenge_min_spread: float = 0.10
    explanation_component_floor: float = 0.025
    topic_specificity_floor: float = 0.45
    scarcity_support_min_count: int = 3
    scarcity_support_min_mass: float = 1.0
    scarcity_support_mass_proxy: str = "sum(lexical_commonness * topic_specificity)"
    scarcity_bonus_enabled: bool = True
    scarcity_bonus_target_mass: float = 6.0
    scarcity_bonus_mass_smoothing: float = 0.5
    scarcity_bonus_mass_exponent: float = 0.5
    scarcity_bonus_max_extra: float = 0.45


NormalizedProfileBootstrapContext = AdmissionProfileFeatures
ProfileBootstrapCandidateTraits = AdmissionCandidateFeatures
ProfileBootstrapSignalPack = AdmissionUtilitySignals


DEFAULT_PROFILE_BOOTSTRAP_POLICY = ProfileBootstrapPolicy()


@dataclass(frozen=True)
class ProfileBootstrapScoredEntry:
    base_index: int
    seed: object
    traits: ProfileBootstrapCandidateTraits
    signal_pack: ProfileBootstrapSignalPack
    scored_candidate: ScoredCandidate


def normalize_profile_bootstrap_context(
    profile_context: Optional[Mapping[str, object]],
    *,
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
) -> NormalizedProfileBootstrapContext:
    del policy
    return normalize_admission_profile_features(profile_context)


def summarize_profile_bootstrap_context(
    profile_context: Optional[Mapping[str, object]],
    *,
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
) -> dict[str, object]:
    normalized = normalize_profile_bootstrap_context(profile_context, policy=policy)
    return {
        "context": normalized.to_dict(),
        "policy": _build_policy_summary(policy),
        "selector_version": PROFILE_BOOTSTRAP_SELECTOR_VERSION,
    }


def extract_profile_bootstrap_candidate_traits(
    seed: object,
    *,
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
) -> ProfileBootstrapCandidateTraits:
    lexical_commonness = (
        clamp01(
            safe_optional_float(getattr(seed, "admission_weight", None))
            or safe_optional_float(getattr(seed, "base_weight", None))
        )
        or 0.0
    )
    lexical_forms: set[str] = set()
    _add_lexical_form(lexical_forms, getattr(seed, "lemma", None))
    word_package = getattr(seed, "word_package", None)
    if isinstance(word_package, Mapping):
        for lexical_key in ("surface", "reading", "sublemma", "lform_raw"):
            _add_lexical_form(lexical_forms, word_package.get(lexical_key))
        for script_form in mapping_or_empty(word_package.get("script_forms")).values():
            _add_lexical_form(lexical_forms, script_form)

    metadata = mapping_or_empty(getattr(seed, "metadata", None))
    word_package_source = (
        mapping_or_empty(word_package.get("source")) if isinstance(word_package, Mapping) else {}
    )
    for lexical_key in (
        "source_surface_original",
        "surface_normalized_from",
        "sublemma",
        "lform_raw",
    ):
        _add_lexical_form(lexical_forms, metadata.get(lexical_key))
        _add_lexical_form(lexical_forms, word_package_source.get(lexical_key))
    raw_topic_hints: set[str] = set()
    topic_hint_origins: dict[str, set[str]] = {}
    for topic_key in policy.topic_metadata_keys:
        _add_topic_hints(raw_topic_hints, topic_hint_origins, metadata.get(topic_key))
        if isinstance(word_package, Mapping):
            _add_topic_hints(raw_topic_hints, topic_hint_origins, word_package.get(topic_key))
        _add_topic_hints(raw_topic_hints, topic_hint_origins, word_package_source.get(topic_key))

    return ProfileBootstrapCandidateTraits(
        lemma=str(getattr(seed, "lemma", "") or "").strip(),
        lexical_commonness=lexical_commonness,
        difficulty_estimate=clamp01(1.0 - lexical_commonness) or 0.0,
        difficulty_proxy=policy.difficulty_proxy,
        lexical_forms=tuple(sorted(form for form in lexical_forms if form)),
        raw_topic_hints=tuple(sorted(topic for topic in raw_topic_hints if topic)),
        topic_hints=tuple(sorted(topic for topic in topic_hint_origins.keys() if topic)),
        topic_hint_origins={
            key: tuple(sorted(value for value in values if value))
            for key, values in sorted(topic_hint_origins.items())
            if key
        },
    )


def _add_lexical_form(target: set[str], value: object) -> None:
    normalized = normalize_topic_token(value)
    if normalized:
        target.add(normalized)


def _add_topic_hints(
    raw_target: set[str],
    expanded_target: dict[str, set[str]],
    value: object,
) -> None:
    expanded, origins = normalize_topic_string_list_with_origins(value)
    for raw_topic in {
        raw_value for raw_values in origins.values() for raw_value in raw_values if raw_value
    }:
        raw_target.add(raw_topic)
    for canonical_topic in expanded:
        canonical_key = str(canonical_topic or "").strip()
        if not canonical_key:
            continue
        bucket = expanded_target.setdefault(canonical_key, set())
        for origin in origins.get(canonical_key, []):
            if origin:
                bucket.add(origin)


def build_profile_bootstrap_signal_pack(
    traits: ProfileBootstrapCandidateTraits,
    context: NormalizedProfileBootstrapContext,
    *,
    active_topic_support: Optional[Mapping[str, Mapping[str, object]]] = None,
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
) -> ProfileBootstrapSignalPack:
    (
        preference_affinity,
        preference_affinity_source,
        topic_specificity,
        topic_support_count,
        topic_hint_count,
    ) = _compute_topic_affinity(
        traits,
        context,
        policy=policy,
    )
    proficiency_fit = _compute_proficiency_fit(
        traits.difficulty_estimate,
        context.proficiency_estimate,
        policy=policy,
    )
    challenge_fit = _compute_challenge_fit(
        traits.difficulty_estimate,
        context.challenge_target,
        context.challenge_spread,
        policy=policy,
    )
    scarcity_bonus, scarcity_bonus_source = _compute_scarcity_bonus(
        traits,
        context,
        active_topic_support=active_topic_support,
        policy=policy,
    )
    return ProfileBootstrapSignalPack(
        coverage_gain=traits.lexical_commonness,
        difficulty_estimate=traits.difficulty_estimate,
        preference_affinity=preference_affinity,
        preference_affinity_source=preference_affinity_source,
        scarcity_bonus=scarcity_bonus,
        scarcity_bonus_source=scarcity_bonus_source,
        topic_specificity=topic_specificity,
        topic_support_count=topic_support_count,
        topic_hint_count=topic_hint_count,
        proficiency_fit=proficiency_fit,
        challenge_fit=challenge_fit,
    )


def rerank_seed_words_for_profile(
    seeds: Sequence[object],
    *,
    profile_context: Optional[Mapping[str, object]],
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
    preview_limit: Optional[int] = 20,
) -> tuple[list[object], dict[str, object]]:
    scored_entries, diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        policy=policy,
        preview_limit=preview_limit,
    )
    return [entry.seed for entry in scored_entries], diagnostics


def score_seed_words_for_profile(
    seeds: Sequence[object],
    *,
    profile_context: Optional[Mapping[str, object]],
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
    preview_limit: Optional[int] = 20,
) -> tuple[list[ProfileBootstrapScoredEntry], dict[str, object]]:
    normalized_context = normalize_profile_bootstrap_context(profile_context, policy=policy)
    seed_traits = [
        (
            base_index,
            seed,
            extract_profile_bootstrap_candidate_traits(seed, policy=policy),
        )
        for base_index, seed in enumerate(seeds)
    ]
    active_topic_support = _build_active_topic_support_summary(
        seed_traits,
        normalized_context,
        policy=policy,
    )
    active_topic_support_by_name = {
        str(entry.get("topic", "")).strip(): entry
        for entry in active_topic_support.get("topics", [])
        if isinstance(entry, Mapping) and str(entry.get("topic", "")).strip()
    }
    ranked_entries: list[ProfileBootstrapScoredEntry] = []
    for base_index, seed, traits in seed_traits:
        signal_pack = build_profile_bootstrap_signal_pack(
            traits,
            normalized_context,
            active_topic_support=active_topic_support_by_name,
            policy=policy,
        )
        selector_candidate = SelectorCandidate(
            lemma=traits.lemma,
            language_pair=str(getattr(seed, "language_pair", "") or "").strip(),
            base_freq=float(signal_pack.coverage_gain),
            topic_bias=float(signal_pack.preference_affinity),
            scarcity_bonus=float(signal_pack.scarcity_bonus),
            user_pref=float(signal_pack.proficiency_fit),
            confidence=0.0,
            difficulty_target=float(signal_pack.challenge_fit),
            pos=str(getattr(seed, "pos_bucket", "") or "").strip() or None,
            metadata={
                "profile_bootstrap_traits": traits.to_dict(),
                "profile_bootstrap_signals": signal_pack.to_dict(),
            },
        )
        ranked_entries.append(
            ProfileBootstrapScoredEntry(
                base_index=base_index,
                seed=seed,
                traits=traits,
                signal_pack=signal_pack,
                scored_candidate=score_candidate(selector_candidate, policy.selector_config),
            )
        )

    ranked_entries.sort(
        key=lambda entry: (
            -entry.scored_candidate.breakdown.final_score,
            entry.base_index,
        )
    )
    base_rank_by_lemma = {
        str(getattr(seed, "lemma", "") or "").strip(): index + 1
        for index, seed in enumerate(seeds)
        if str(getattr(seed, "lemma", "") or "").strip()
    }
    if preview_limit is None:
        ranking_preview_limit = len(ranked_entries)
    else:
        ranking_preview_limit = max(0, int(preview_limit))
    ranking_preview = [
        _build_preview_entry(
            reranked_rank=index + 1,
            seed=entry.seed,
            traits=entry.traits,
            signal_pack=entry.signal_pack,
            scored_candidate=entry.scored_candidate,
            base_rank=base_rank_by_lemma.get(
                str(getattr(entry.seed, "lemma", "") or "").strip(), 0
            ),
            policy=policy,
        )
        for index, entry in enumerate(ranked_entries[:ranking_preview_limit])
    ]
    return ranked_entries, {
        "selector_version": PROFILE_BOOTSTRAP_SELECTOR_VERSION,
        "selector_policy_version": policy.version,
        "selection_weights": policy.selector_config.weights.__dict__,
        "selection_policy": policy.selector_config.selection_policy,
        "utility_weights": {
            "coverage_gain": policy.selector_config.weights.base_freq,
            "topic_affinity": policy.selector_config.weights.topic_bias,
            "scarcity_bonus": policy.selector_config.weights.scarcity_bonus,
            "proficiency_fit": policy.selector_config.weights.user_pref,
            "challenge_fit": policy.selector_config.weights.difficulty_target,
            "lexical_risk": 0.0,
            "redundancy": 0.0,
            "exploration_bonus": 0.0,
        },
        "profile_context": normalized_context.to_dict(),
        "admission_profile": normalized_context.to_dict(),
        "policy": _build_policy_summary(policy),
        "active_topic_support": active_topic_support,
        "ranking_preview": ranking_preview,
    }


def _build_policy_summary(policy: ProfileBootstrapPolicy) -> dict[str, object]:
    return {
        "version": policy.version,
        "difficulty_proxy": policy.difficulty_proxy,
        "topic_metadata_keys": list(policy.topic_metadata_keys),
        "topic_exact_match_multiplier": _rounded_or_none(policy.topic_exact_match_multiplier),
        "proficiency_taper_width": _rounded_or_none(policy.proficiency_taper_width),
        "challenge_default_spread": _rounded_or_none(policy.challenge_default_spread),
        "challenge_min_spread": _rounded_or_none(policy.challenge_min_spread),
        "explanation_component_floor": _rounded_or_none(policy.explanation_component_floor),
        "topic_specificity_floor": _rounded_or_none(policy.topic_specificity_floor),
        "scarcity_support_min_count": int(policy.scarcity_support_min_count),
        "scarcity_support_min_mass": _rounded_or_none(policy.scarcity_support_min_mass),
        "scarcity_support_mass_proxy": policy.scarcity_support_mass_proxy,
        "scarcity_bonus_enabled": bool(policy.scarcity_bonus_enabled),
        "scarcity_bonus_target_mass": _rounded_or_none(policy.scarcity_bonus_target_mass),
        "scarcity_bonus_mass_smoothing": _rounded_or_none(policy.scarcity_bonus_mass_smoothing),
        "scarcity_bonus_mass_exponent": _rounded_or_none(policy.scarcity_bonus_mass_exponent),
        "scarcity_bonus_max_extra": _rounded_or_none(policy.scarcity_bonus_max_extra),
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


def _compute_topic_affinity(
    traits: ProfileBootstrapCandidateTraits,
    context: NormalizedProfileBootstrapContext,
    *,
    policy: ProfileBootstrapPolicy,
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


def _compute_topic_specificity(
    traits: ProfileBootstrapCandidateTraits,
    context: NormalizedProfileBootstrapContext,
    *,
    policy: ProfileBootstrapPolicy,
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


def _build_active_topic_support_summary(
    seed_traits: Sequence[tuple[int, object, ProfileBootstrapCandidateTraits]],
    context: NormalizedProfileBootstrapContext,
    *,
    policy: ProfileBootstrapPolicy,
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
                "requested_weight": _rounded_or_none(requested_weight),
                "weight_source": weight_source,
                "candidate_count": int(candidate_count),
                "candidate_ratio": _rounded_or_none(
                    candidate_count / float(max(1, total_candidates))
                ),
                "support_mass": _rounded_or_none(support_mass),
                "support_mass_ratio": _rounded_or_none(
                    support_mass / float(max(1e-9, total_base_mass))
                ),
                "mean_topic_specificity": _rounded_or_none(
                    specificity_total / float(max(1, candidate_count))
                ),
                "scarcity_multiplier_preview": _rounded_or_none(scarcity_multiplier),
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
        "total_base_mass": _rounded_or_none(total_base_mass),
        "scarcity_support_min_count": int(policy.scarcity_support_min_count),
        "scarcity_support_min_mass": _rounded_or_none(policy.scarcity_support_min_mass),
        "scarcity_support_mass_proxy": policy.scarcity_support_mass_proxy,
        "topics": topic_entries,
    }


def _compute_topic_scarcity_multiplier(
    support_mass: float,
    *,
    eligible_for_scarcity_calibration: bool,
    policy: ProfileBootstrapPolicy,
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


def _compute_scarcity_bonus(
    traits: ProfileBootstrapCandidateTraits,
    context: NormalizedProfileBootstrapContext,
    *,
    active_topic_support: Optional[Mapping[str, Mapping[str, object]]],
    policy: ProfileBootstrapPolicy,
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


def _compute_topic_specificity_for_topic(
    traits: ProfileBootstrapCandidateTraits,
    active_topic: str,
    *,
    policy: ProfileBootstrapPolicy,
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


def _compute_proficiency_fit(
    difficulty_estimate: float,
    proficiency_estimate: Optional[float],
    *,
    policy: ProfileBootstrapPolicy,
) -> float:
    if proficiency_estimate is None:
        return 0.0
    if difficulty_estimate <= proficiency_estimate:
        return 1.0
    gap = difficulty_estimate - proficiency_estimate
    return clamp01(1.0 - (gap / policy.proficiency_taper_width)) or 0.0


def _compute_challenge_fit(
    difficulty_estimate: float,
    challenge_target: Optional[float],
    challenge_spread: Optional[float],
    *,
    policy: ProfileBootstrapPolicy,
) -> float:
    if challenge_target is None:
        return 0.0
    effective_spread = max(
        policy.challenge_min_spread,
        float(challenge_spread or policy.challenge_default_spread),
    )
    distance = difficulty_estimate - challenge_target
    return clamp01(math.exp(-0.5 * ((distance / effective_spread) ** 2))) or 0.0


def _build_preview_entry(
    *,
    reranked_rank: int,
    seed: object,
    traits: ProfileBootstrapCandidateTraits,
    signal_pack: ProfileBootstrapSignalPack,
    scored_candidate: object,
    base_rank: int,
    policy: ProfileBootstrapPolicy,
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
        "base_weight": _rounded_or_none(safe_optional_float(getattr(seed, "base_weight", None))),
        "admission_weight": _rounded_or_none(
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
            "Kept near frequency order; strongest profile signal was "
            f"{active_profile_drivers[0]}."
        )
    return "Kept in neutral frequency order because profile signals were effectively neutral."


def _rounded_or_none(value: Optional[float]) -> Optional[float]:
    return admission_rounded_or_none(value)
