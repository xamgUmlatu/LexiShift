from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.admission_features import (
    AdmissionCandidateFeatures,
    AdmissionProfileFeatures,
    AdmissionUtilitySignals,
    clamp01,
    mapping_or_empty,
    normalize_admission_profile_features,
    normalize_topic_string_list_with_origins,
    normalize_topic_token,
    safe_optional_float,
)
from lexishift_core.srs.profile_bootstrap_support import (
    build_active_topic_support_summary as _build_active_topic_support_summary,
    build_policy_summary as _build_policy_summary,
    build_preview_entry as _build_preview_entry,
    compute_challenge_fit as _compute_challenge_fit,
    compute_proficiency_fit as _compute_proficiency_fit,
    compute_readiness_gate as _compute_readiness_gate,
    compute_scarcity_bonus as _compute_scarcity_bonus,
    compute_topic_affinity as _compute_topic_affinity,
)
from lexishift_core.srs.selector import (
    SELECTION_POLICY_RESERVED_TOPIC_LANE,
    ScoredCandidate,
    SelectorCandidate,
    SelectorConfig,
    SelectorWeights,
    score_candidate,
)

PROFILE_BOOTSTRAP_POLICY_VERSION = "profile_bootstrap_policy_v4"
PROFILE_BOOTSTRAP_SELECTOR_VERSION = "profile_bootstrap_v5"
PROFILE_TOPIC_DEPTH_VERSION = "profile_topic_depth_v1"

PROFILE_TOPIC_DEPTH_BANDS: tuple[tuple[str, float, float], ...] = (
    ("0.00-0.20", 0.0, 0.2),
    ("0.20-0.40", 0.2, 0.4),
    ("0.40-0.60", 0.4, 0.6),
    ("0.60-0.80", 0.6, 0.8),
    ("0.80-1.00", 0.8, 1.0),
)
PROFILE_TOPIC_DEPTH_READY_THRESHOLD = 0.5
PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD = 0.9
PROFILE_TOPIC_DEPTH_EXAMPLE_LIMIT = 5


@dataclass(frozen=True)
class ProfileBootstrapPolicy:
    version: str = PROFILE_BOOTSTRAP_POLICY_VERSION
    selector_config: SelectorConfig = field(
        default_factory=lambda: SelectorConfig(
            selection_policy=SELECTION_POLICY_RESERVED_TOPIC_LANE,
            weights=SelectorWeights(
                base_freq=0.55,
                topic_bias=0.15,
                scarcity_bonus=0.05,
                user_pref=0.10,
                confidence=0.0,
                difficulty_target=0.10,
            ),
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
    readiness_base_lower_margin: float = 0.15
    readiness_base_upper_margin: float = 0.18
    readiness_topic_extra_lower_margin: float = 0.12
    readiness_topic_extra_upper_margin: float = 0.08
    readiness_too_easy_penalty: float = 60.0
    readiness_too_hard_penalty: float = 35.0
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
    readiness_gate = _compute_readiness_gate(
        traits.difficulty_estimate,
        context.proficiency_estimate,
        preference_affinity,
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
        readiness_multiplier=readiness_gate.multiplier,
        readiness_lower_bound=readiness_gate.lower_bound,
        readiness_upper_bound=readiness_gate.upper_bound,
        readiness_topic_strength=readiness_gate.topic_strength,
        readiness_too_easy_gap=readiness_gate.too_easy_gap,
        readiness_too_hard_gap=readiness_gate.too_hard_gap,
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
                "readiness_multiplier": signal_pack.readiness_multiplier,
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
    topic_depth_by_level = _build_topic_depth_by_level(
        ranked_entries,
        normalized_context,
        policy=policy,
    )
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
        "topic_depth_by_level": topic_depth_by_level,
        "ranking_preview": ranking_preview,
    }


def _build_topic_depth_by_level(
    ranked_entries: Sequence[ProfileBootstrapScoredEntry],
    context: NormalizedProfileBootstrapContext,
    *,
    policy: ProfileBootstrapPolicy,
) -> dict[str, object]:
    active_topics = [
        (str(topic or "").strip(), float(weight or 0.0))
        for topic, weight in context.topic_weights.items()
        if str(topic or "").strip() and float(weight or 0.0) > 0.0
    ]
    active_topics.sort(key=lambda item: (-item[1], item[0]))
    bands = [
        _new_depth_band(label, lower, upper) for label, lower, upper in PROFILE_TOPIC_DEPTH_BANDS
    ]
    topic_entries = [
        {
            "topic": topic,
            "requested_weight": round(weight, 6),
            "candidate_count": 0,
            "ready_candidate_count": 0,
            "high_readiness_candidate_count": 0,
            "max_difficulty": None,
            "bands": [
                _new_topic_depth_band(label, lower, upper)
                for label, lower, upper in PROFILE_TOPIC_DEPTH_BANDS
            ],
            "hardest_examples": [],
        }
        for topic, weight in active_topics
    ]
    topic_entry_by_name = {str(entry["topic"]): entry for entry in topic_entries}
    hardest_examples_by_topic: dict[str, list[tuple[float, dict[str, object]]]] = {
        topic: [] for topic, _weight in active_topics
    }

    for entry in ranked_entries:
        difficulty = _clamped_signal_value(entry.signal_pack.difficulty_estimate)
        readiness = _clamped_signal_value(entry.signal_pack.readiness_multiplier)
        topic_affinity = _clamped_signal_value(entry.signal_pack.preference_affinity)
        band_index = _topic_depth_band_index(difficulty)
        band = bands[band_index]
        band["candidate_count"] = int(band["candidate_count"]) + 1
        if topic_affinity > 0.0:
            band["preferred_topic_count"] = int(band["preferred_topic_count"]) + 1
            if readiness >= PROFILE_TOPIC_DEPTH_READY_THRESHOLD:
                band["ready_preferred_topic_count"] = int(band["ready_preferred_topic_count"]) + 1
            if readiness >= PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD:
                band["high_readiness_preferred_topic_count"] = (
                    int(band["high_readiness_preferred_topic_count"]) + 1
                )
            _append_topic_depth_example(band["top_preferred_examples"], entry)

        for topic, _weight in active_topics:
            if not _entry_matches_active_topic(entry, topic):
                continue
            topic_entry = topic_entry_by_name[topic]
            topic_entry["candidate_count"] = int(topic_entry["candidate_count"]) + 1
            if readiness >= PROFILE_TOPIC_DEPTH_READY_THRESHOLD:
                topic_entry["ready_candidate_count"] = int(topic_entry["ready_candidate_count"]) + 1
            if readiness >= PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD:
                topic_entry["high_readiness_candidate_count"] = (
                    int(topic_entry["high_readiness_candidate_count"]) + 1
                )
            max_difficulty = topic_entry["max_difficulty"]
            if max_difficulty is None or difficulty > float(max_difficulty):
                topic_entry["max_difficulty"] = round(difficulty, 6)
            topic_band = topic_entry["bands"][band_index]
            topic_band["candidate_count"] = int(topic_band["candidate_count"]) + 1
            if readiness >= PROFILE_TOPIC_DEPTH_READY_THRESHOLD:
                topic_band["ready_candidate_count"] = int(topic_band["ready_candidate_count"]) + 1
            if readiness >= PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD:
                topic_band["high_readiness_candidate_count"] = (
                    int(topic_band["high_readiness_candidate_count"]) + 1
                )
            _append_topic_depth_example(topic_band["top_examples"], entry)
            hardest_examples_by_topic[topic].append((difficulty, _topic_depth_example(entry)))

    for topic_entry in topic_entries:
        topic = str(topic_entry["topic"])
        hardest = sorted(
            hardest_examples_by_topic.get(topic, []),
            key=lambda item: (-item[0], str(item[1].get("lemma") or "")),
        )
        topic_entry["hardest_examples"] = [
            example for _difficulty, example in hardest[:PROFILE_TOPIC_DEPTH_EXAMPLE_LIMIT]
        ]

    return {
        "version": PROFILE_TOPIC_DEPTH_VERSION,
        "difficulty_proxy": policy.difficulty_proxy,
        "ready_threshold": PROFILE_TOPIC_DEPTH_READY_THRESHOLD,
        "high_readiness_threshold": PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD,
        "total_candidates": len(ranked_entries),
        "active_topic_count": len(active_topics),
        "bands": bands,
        "topics": topic_entries,
    }


def _new_depth_band(label: str, lower: float, upper: float) -> dict[str, object]:
    return {
        "band": label,
        "lower": lower,
        "upper": upper,
        "candidate_count": 0,
        "preferred_topic_count": 0,
        "ready_preferred_topic_count": 0,
        "high_readiness_preferred_topic_count": 0,
        "top_preferred_examples": [],
    }


def _new_topic_depth_band(label: str, lower: float, upper: float) -> dict[str, object]:
    return {
        "band": label,
        "lower": lower,
        "upper": upper,
        "candidate_count": 0,
        "ready_candidate_count": 0,
        "high_readiness_candidate_count": 0,
        "top_examples": [],
    }


def _topic_depth_band_index(difficulty: float) -> int:
    for index, (_label, lower, upper) in enumerate(PROFILE_TOPIC_DEPTH_BANDS):
        if index == len(PROFILE_TOPIC_DEPTH_BANDS) - 1:
            if lower <= difficulty <= upper:
                return index
        elif lower <= difficulty < upper:
            return index
    return len(PROFILE_TOPIC_DEPTH_BANDS) - 1


def _append_topic_depth_example(target: object, entry: ProfileBootstrapScoredEntry) -> None:
    if not isinstance(target, list):
        return
    if len(target) >= PROFILE_TOPIC_DEPTH_EXAMPLE_LIMIT:
        return
    target.append(_topic_depth_example(entry))


def _topic_depth_example(entry: ProfileBootstrapScoredEntry) -> dict[str, object]:
    return {
        "lemma": entry.traits.lemma,
        "difficulty_estimate": round(float(entry.signal_pack.difficulty_estimate), 6),
        "readiness_multiplier": round(float(entry.signal_pack.readiness_multiplier), 6),
        "topic_affinity": round(float(entry.signal_pack.preference_affinity), 6),
        "topic_affinity_source": entry.signal_pack.preference_affinity_source,
        "profile_score": round(float(entry.scored_candidate.breakdown.final_score), 6),
    }


def _entry_matches_active_topic(entry: ProfileBootstrapScoredEntry, topic: str) -> bool:
    if topic in entry.traits.topic_hints:
        return True
    source = str(entry.signal_pack.preference_affinity_source or "")
    return source == f"lexical:{topic}"


def _clamped_signal_value(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
