from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Mapping, MutableMapping, Optional, Sequence

from lexishift_core.srs.admission_features import (
    ADMISSION_CANDIDATE_FEATURES_METADATA_KEY,
    ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY,
    AdmissionCandidateFeatures,
    AdmissionProfileFeatures,
    AdmissionUtilitySignals,
    admission_candidate_features_from_mapping,
    clamp01,
    mapping_or_empty,
    normalize_admission_profile_features,
    normalize_topic_string_list_with_origins,
    normalize_topic_token,
    safe_optional_float,
)
from lexishift_core.srs.candidate_classification import (
    CANDIDATE_STATE_DEPRIORITIZED_VOCAB,
    CANDIDATE_STATE_SUPPRESSED_DEFAULT,
    CANDIDATE_STATE_TOPIC_ONLY,
    CLASSIFICATION_CONFIDENCE_HIGH,
    CLASSIFICATION_CONFIDENCE_REVIEW,
    CandidateClassification,
    PRESENTATION_MODE_SUPPRESS,
    classify_srs_candidate,
)
from lexishift_core.srs.candidate_identity import candidate_identity_key_from_seed
from lexishift_core.srs.learner_difficulty import (
    CorrectedLearnerDifficultyMatch,
    estimate_learner_difficulty,
    lookup_corrected_learner_difficulty,
)
from lexishift_core.srs.profile_bootstrap_support import (
    FrontierGaussianFit,
    build_active_topic_support_summary as _build_active_topic_support_summary,
    build_policy_summary as _build_policy_summary,
    build_preview_entry as _build_preview_entry,
    compute_challenge_fit as _compute_challenge_fit,
    compute_frontier_gaussian_fit as _compute_frontier_gaussian_fit,
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

PROFILE_BOOTSTRAP_POLICY_VERSION = "profile_bootstrap_policy_v5"
PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_POLICY_VERSION = "profile_bootstrap_frontier_gaussian_policy_v1"
PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_POLICY_VERSION = (
    "profile_bootstrap_frontier_gaussian_hybrid_policy_v2"
)
PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_POLICY_VERSION = (
    "profile_bootstrap_frontier_gaussian_hybrid_soft_topic_policy_v3"
)
PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_SELECTION_POLICY = "frontier_gaussian_lanes"
PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_SELECTION_POLICY = "frontier_gaussian_hybrid_lanes"
PROFILE_BOOTSTRAP_SELECTOR_VERSION = "profile_bootstrap_v6"
PROFILE_TOPIC_DEPTH_VERSION = "profile_topic_depth_v1"
PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE_MAX_SIZE = 25000
CORE_LANE = "core"
FRONTIER_LANE = "frontier"
TRAIL_LANE = "trail"
TOPIC_LANE = "topic"

_PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE: dict[
    tuple[str, str, str], ProfileBootstrapCandidateTraits
] = {}

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
                base_freq=0.05,
                topic_bias=0.30,
                scarcity_bonus=0.05,
                user_pref=0.55,
                confidence=0.0,
                difficulty_target=0.0,
            ),
        )
    )
    difficulty_proxy: str = "1_minus_base_weight"
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
    frontier_target_offset: float = 0.0
    frontier_sigma_low_beginner: float = 0.18
    frontier_sigma_low_advanced: float = 0.07
    frontier_sigma_high_beginner: float = 0.14
    frontier_sigma_high_advanced: float = 0.12
    frontier_topic_lower_widen: float = 0.40
    frontier_topic_upper_widen: float = 0.45
    trail_center: float = 0.12
    trail_sigma: float = 0.07
    trail_minimum_difficulty: float = 0.20
    trail_floor_width: float = 0.06
    frontier_lane_share: float = 0.72
    trail_lane_share: float = 0.18
    topic_lane_share: float = 0.10
    hybrid_beginner_core_threshold: float = 0.16
    hybrid_beginner_core_lane_share: float = 0.40
    hybrid_trail_lane_share: float = 0.18
    hybrid_topic_min_share: float = 0.25
    hybrid_topic_max_share: float = 0.45
    hybrid_topic_depth_saturation: float = 6.0
    hybrid_topic_min_lane_score: float = 0.08
    hybrid_topic_lower_margin: float = 0.20
    hybrid_topic_lower_penalty_sigma: Optional[float] = None


NormalizedProfileBootstrapContext = AdmissionProfileFeatures
ProfileBootstrapCandidateTraits = AdmissionCandidateFeatures
ProfileBootstrapSignalPack = AdmissionUtilitySignals


DEFAULT_PROFILE_BOOTSTRAP_POLICY = ProfileBootstrapPolicy()
FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY = ProfileBootstrapPolicy(
    version=PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_POLICY_VERSION,
)
FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY = ProfileBootstrapPolicy(
    version=PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_POLICY_VERSION,
)
FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY = ProfileBootstrapPolicy(
    version=PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_POLICY_VERSION,
    hybrid_topic_lower_penalty_sigma=0.03,
)


@dataclass(frozen=True)
class ProfileBootstrapScoredEntry:
    base_index: int
    seed: object
    traits: ProfileBootstrapCandidateTraits
    signal_pack: ProfileBootstrapSignalPack
    scored_candidate: ScoredCandidate


@dataclass(frozen=True)
class ProfileBootstrapFrontierLaneEntry:
    source_entry: ProfileBootstrapScoredEntry
    frontier_fit: FrontierGaussianFit
    lane_scores: Mapping[str, float]
    selected_lane: Optional[str] = None

    @property
    def base_index(self) -> int:
        return self.source_entry.base_index

    @property
    def seed(self) -> object:
        return self.source_entry.seed

    @property
    def traits(self) -> ProfileBootstrapCandidateTraits:
        return self.source_entry.traits

    @property
    def signal_pack(self) -> ProfileBootstrapSignalPack:
        return self.source_entry.signal_pack


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
    metadata = mapping_or_empty(getattr(seed, "metadata", None))
    precomputed = _precomputed_candidate_traits(seed, metadata=metadata, policy=policy)
    if precomputed is not None:
        return precomputed
    cache_key = _candidate_traits_cache_key(seed, metadata=metadata, policy=policy)
    if cache_key is not None:
        cached = _PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE.get(cache_key)
        if cached is not None:
            _PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE.pop(cache_key, None)
            _PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE[cache_key] = cached
            return cached
    source_commonness_value = safe_optional_float(getattr(seed, "base_weight", None))
    if source_commonness_value is None:
        source_commonness_value = safe_optional_float(getattr(seed, "admission_weight", None))
    source_commonness = clamp01(source_commonness_value) or 0.0
    coverage_gain_value = safe_optional_float(getattr(seed, "admission_weight", None))
    if coverage_gain_value is None:
        coverage_gain_value = safe_optional_float(getattr(seed, "base_weight", None))
    coverage_gain = clamp01(coverage_gain_value) or 0.0
    lexical_forms: set[str] = set()
    _add_lexical_form(lexical_forms, getattr(seed, "lemma", None))
    word_package = getattr(seed, "word_package", None)
    if isinstance(word_package, Mapping):
        for lexical_key in ("surface", "reading", "sublemma", "lform_raw"):
            _add_lexical_form(lexical_forms, word_package.get(lexical_key))
        for script_form in mapping_or_empty(word_package.get("script_forms")).values():
            _add_lexical_form(lexical_forms, script_form)

    word_package_source = (
        mapping_or_empty(word_package.get("source")) if isinstance(word_package, Mapping) else {}
    )
    learner_signals = mapping_or_empty(metadata.get("learner_signals"))
    if not learner_signals:
        learner_signals = mapping_or_empty(word_package_source.get("learner_signals"))
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
    reading = _first_present_value(
        _mapping_value(word_package, "reading"),
        _mapping_value(word_package, "lform_raw"),
        metadata.get("lform_raw"),
        word_package_source.get("lform_raw"),
    )
    reading_candidates = tuple(sorted(form for form in lexical_forms if form))
    language_pair = str(getattr(seed, "language_pair", "") or metadata.get("language_pair") or "")
    corrected_difficulty_match = lookup_corrected_learner_difficulty(
        language_pair=language_pair,
        lemma=str(getattr(seed, "lemma", "") or "").strip(),
        reading=reading,
        reading_candidates=reading_candidates,
    )
    classification = _apply_corrected_ranking_admission_overlay(
        _resolve_candidate_classification(seed, metadata=metadata),
        corrected_difficulty_match=corrected_difficulty_match,
    )
    frequency_difficulty = clamp01(1.0 - source_commonness) or 0.0
    learner_difficulty = estimate_learner_difficulty(
        language_pair=language_pair,
        lemma=str(getattr(seed, "lemma", "") or "").strip(),
        reading=reading,
        reading_candidates=reading_candidates,
        frequency_proxy=frequency_difficulty,
        candidate_state=classification.candidate_state,
        presentation_mode=classification.presentation_mode,
        problem_class=classification.problem_class,
    )

    traits = ProfileBootstrapCandidateTraits(
        candidate_identity_key=candidate_identity_key_from_seed(seed),
        lemma=str(getattr(seed, "lemma", "") or "").strip(),
        lexical_commonness=source_commonness,
        coverage_gain=coverage_gain,
        difficulty_estimate=learner_difficulty.value,
        difficulty_proxy=learner_difficulty.proxy,
        difficulty_sources=tuple(learner_difficulty.sources),
        candidate_state=classification.candidate_state,
        presentation_mode=classification.presentation_mode,
        problem_class=classification.problem_class,
        classification_confidence=classification.confidence,
        classification_reasons=tuple(classification.reasons),
        admission_suitability=classification.admission_suitability,
        lexical_forms=tuple(sorted(form for form in lexical_forms if form)),
        learner_signals=learner_signals,
        raw_topic_hints=tuple(sorted(topic for topic in raw_topic_hints if topic)),
        topic_hints=tuple(sorted(topic for topic in topic_hint_origins.keys() if topic)),
        topic_hint_origins={
            key: tuple(sorted(value for value in values if value))
            for key, values in sorted(topic_hint_origins.items())
            if key
        },
    )
    if cache_key is not None:
        _remember_candidate_traits(cache_key, traits)
    return traits


def attach_precomputed_profile_bootstrap_candidate_traits(
    seeds: Sequence[object],
    *,
    policy: ProfileBootstrapPolicy = DEFAULT_PROFILE_BOOTSTRAP_POLICY,
) -> int:
    attached_count = 0
    for seed in seeds:
        metadata = getattr(seed, "metadata", None)
        if not isinstance(metadata, MutableMapping):
            continue
        if _precomputed_candidate_traits(seed, metadata=metadata, policy=policy) is not None:
            continue
        traits = extract_profile_bootstrap_candidate_traits(seed, policy=policy)
        metadata[ADMISSION_CANDIDATE_FEATURES_METADATA_KEY] = traits.to_dict()
        metadata[ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY] = policy.version
        attached_count += 1
    return attached_count


def _precomputed_candidate_traits(
    seed: object,
    *,
    metadata: Mapping[str, object],
    policy: ProfileBootstrapPolicy,
) -> ProfileBootstrapCandidateTraits | None:
    if (
        str(metadata.get(ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY) or "").strip()
        != policy.version
    ):
        return None
    traits = admission_candidate_features_from_mapping(
        metadata.get(ADMISSION_CANDIDATE_FEATURES_METADATA_KEY)
    )
    if traits is None:
        return None
    seed_lemma = str(getattr(seed, "lemma", "") or "").strip()
    if seed_lemma and traits.lemma and traits.lemma != seed_lemma:
        return None
    seed_identity = candidate_identity_key_from_seed(seed)
    if (
        seed_identity
        and traits.candidate_identity_key
        and traits.candidate_identity_key != seed_identity
    ):
        return None
    return traits


def _candidate_traits_cache_key(
    seed: object,
    *,
    metadata: Mapping[str, object],
    policy: ProfileBootstrapPolicy,
) -> tuple[str, str, str] | None:
    identity_key = candidate_identity_key_from_seed(seed)
    if not identity_key:
        return None
    payload = {
        "policy_version": policy.version,
        "identity_key": identity_key,
        "language_pair": str(
            getattr(seed, "language_pair", "") or metadata.get("language_pair") or ""
        ).strip(),
        "lemma": str(getattr(seed, "lemma", "") or metadata.get("lemma") or "").strip(),
        "base_weight": safe_optional_float(getattr(seed, "base_weight", None)),
        "admission_weight": safe_optional_float(getattr(seed, "admission_weight", None)),
        "candidate_state": _string_attr_or_metadata(
            seed,
            metadata,
            attr="candidate_state",
            fallback="normal_vocab",
        ),
        "presentation_mode": _string_attr_or_metadata(
            seed,
            metadata,
            attr="presentation_mode",
            fallback="vocab",
        ),
        "problem_class": _string_attr_or_metadata(
            seed,
            metadata,
            attr="problem_class",
            fallback="normal_vocab",
        ),
        "classification_confidence": _string_attr_or_metadata(
            seed,
            metadata,
            attr="classification_confidence",
            fallback="review",
        ),
        "classification_reasons": _sequence_attr_or_metadata(
            seed,
            metadata,
            attr="classification_reasons",
            fallback=(),
        ),
        "admission_suitability": safe_optional_float(getattr(seed, "admission_suitability", None)),
        "word_package": _word_package_trait_fingerprint_payload(
            getattr(seed, "word_package", None)
        ),
        "metadata": _metadata_trait_fingerprint_payload(metadata, policy=policy),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return (policy.version, identity_key, digest)


def _word_package_trait_fingerprint_payload(value: object) -> object:
    if not isinstance(value, Mapping):
        return None
    source = mapping_or_empty(value.get("source"))
    return {
        "surface": value.get("surface"),
        "reading": value.get("reading"),
        "sublemma": value.get("sublemma"),
        "lform_raw": value.get("lform_raw"),
        "script_forms": value.get("script_forms"),
        "source": {
            "learner_signals": source.get("learner_signals"),
            "source_surface_original": source.get("source_surface_original"),
            "surface_normalized_from": source.get("surface_normalized_from"),
            "sublemma": source.get("sublemma"),
            "lform_raw": source.get("lform_raw"),
        },
        "topics": {
            topic_key: value.get(topic_key)
            for topic_key in (
                "sense_topics",
                "topics",
                "topic",
                "profile_topics",
            )
        },
    }


def _metadata_trait_fingerprint_payload(
    metadata: Mapping[str, object],
    *,
    policy: ProfileBootstrapPolicy,
) -> dict[str, object]:
    keys = {
        "learner_signals",
        "source_surface_original",
        "surface_normalized_from",
        "sublemma",
        "lform_raw",
        "pos_raw",
        "pos",
        "candidate_identity_key",
        "candidate_identity",
        "profile_topic_overlay",
        "candidate_state",
        "presentation_mode",
        "problem_class",
        "classification_confidence",
        "classification_reasons",
        "admission_suitability",
        *tuple(policy.topic_metadata_keys),
    }
    return {key: metadata.get(key) for key in sorted(keys) if key in metadata}


def _remember_candidate_traits(
    key: tuple[str, str, str],
    traits: ProfileBootstrapCandidateTraits,
) -> None:
    if len(_PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE) >= (
        PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE_MAX_SIZE
    ):
        _PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE.pop(
            next(iter(_PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE)),
            None,
        )
    _PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE[key] = traits


def clear_profile_bootstrap_candidate_trait_cache() -> None:
    _PROFILE_BOOTSTRAP_CANDIDATE_TRAIT_CACHE.clear()


def _add_lexical_form(target: set[str], value: object) -> None:
    normalized = normalize_topic_token(value)
    if normalized:
        target.add(normalized)


def _mapping_value(value: object, key: str) -> object:
    if not isinstance(value, Mapping):
        return None
    return value.get(key)


def _first_present_value(*values: object) -> object:
    for value in values:
        if str(value or "").strip():
            return value
    return None


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


def _resolve_candidate_classification(
    seed: object,
    *,
    metadata: Mapping[str, object],
) -> CandidateClassification:
    fallback = classify_srs_candidate(
        language_pair=str(
            getattr(seed, "language_pair", "") or metadata.get("language_pair") or ""
        ),
        lemma=str(getattr(seed, "lemma", "") or metadata.get("lemma") or "").strip(),
        raw_pos=(
            getattr(seed, "pos_raw", None)
            or getattr(seed, "pos", None)
            or metadata.get("pos_raw")
            or metadata.get("pos")
        ),
    )
    candidate_state = _string_attr_or_metadata(
        seed,
        metadata,
        attr="candidate_state",
        fallback=fallback.candidate_state,
    )
    presentation_mode = _string_attr_or_metadata(
        seed,
        metadata,
        attr="presentation_mode",
        fallback=fallback.presentation_mode,
    )
    problem_class = _string_attr_or_metadata(
        seed,
        metadata,
        attr="problem_class",
        fallback=fallback.problem_class,
    )
    confidence = _string_attr_or_metadata(
        seed,
        metadata,
        attr="classification_confidence",
        fallback=fallback.confidence,
    )
    reasons = _sequence_attr_or_metadata(
        seed,
        metadata,
        attr="classification_reasons",
        fallback=tuple(fallback.reasons),
    )
    suitability_value = safe_optional_float(getattr(seed, "admission_suitability", None))
    if suitability_value is None:
        suitability_value = safe_optional_float(metadata.get("admission_suitability"))
    suitability = clamp01(suitability_value)
    if suitability is None:
        suitability = fallback.admission_suitability
    return CandidateClassification(
        candidate_state=candidate_state,
        presentation_mode=presentation_mode,
        problem_class=problem_class,
        confidence=confidence,
        reasons=reasons,
        admission_suitability=suitability,
    )


def _apply_corrected_ranking_admission_overlay(
    classification: CandidateClassification,
    *,
    corrected_difficulty_match: CorrectedLearnerDifficultyMatch | None,
) -> CandidateClassification:
    if corrected_difficulty_match is None:
        return classification
    row = corrected_difficulty_match.row
    correction_types = set(row.correction_types)
    admission_override = str(row.admission_override or "").strip()
    if "exclude_standalone_srs" in correction_types or (
        admission_override == "exclude_standalone_srs"
    ):
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_SUPPRESSED_DEFAULT,
            presentation_mode=PRESENTATION_MODE_SUPPRESS,
            problem_class=admission_override or "manual_exclude_standalone_srs",
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=(
                *classification.reasons,
                "corrected_ranking:exclude_standalone_srs",
            ),
            admission_suitability=0.0,
        )
    if "restricted_admission" in correction_types:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_SUPPRESSED_DEFAULT,
            presentation_mode=PRESENTATION_MODE_SUPPRESS,
            problem_class=admission_override or "manual_restricted_admission",
            confidence=CLASSIFICATION_CONFIDENCE_REVIEW,
            reasons=(
                *classification.reasons,
                f"corrected_ranking:restricted_admission:{admission_override or 'generic'}",
            ),
            admission_suitability=0.0,
        )
    return classification


def _string_attr_or_metadata(
    seed: object,
    metadata: Mapping[str, object],
    *,
    attr: str,
    fallback: str,
) -> str:
    value = getattr(seed, attr, None)
    if value is None:
        value = metadata.get(attr)
    text = str(value or "").strip()
    return text or fallback


def _sequence_attr_or_metadata(
    seed: object,
    metadata: Mapping[str, object],
    *,
    attr: str,
    fallback: Sequence[str],
) -> tuple[str, ...]:
    value = getattr(seed, attr, None)
    if value is None:
        value = metadata.get(attr)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        normalized = tuple(str(item).strip() for item in value if str(item).strip())
        if normalized:
            return normalized
    text = str(value or "").strip()
    if text:
        return (text,)
    return tuple(fallback)


def _compute_admission_suitability(
    traits: ProfileBootstrapCandidateTraits,
    *,
    preference_affinity: float,
) -> float:
    base = clamp01(safe_optional_float(traits.admission_suitability)) or 0.0
    affinity = clamp01(safe_optional_float(preference_affinity)) or 0.0
    if traits.candidate_state == CANDIDATE_STATE_DEPRIORITIZED_VOCAB and affinity > 0.0:
        return max(base, min(1.0, base + (0.55 * affinity)))
    if traits.candidate_state == CANDIDATE_STATE_TOPIC_ONLY and affinity > 0.0:
        return max(base, min(1.0, base + (0.75 * affinity)))
    return base


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
    readiness_center, readiness_center_source = _resolve_readiness_center(context)
    readiness_gate = _compute_readiness_gate(
        traits.difficulty_estimate,
        readiness_center,
        preference_affinity,
        policy=policy,
    )
    admission_suitability = _compute_admission_suitability(
        traits,
        preference_affinity=preference_affinity,
    )
    return ProfileBootstrapSignalPack(
        coverage_gain=traits.lexical_commonness,
        admission_suitability=admission_suitability,
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
        readiness_center=readiness_center,
        readiness_center_source=readiness_center_source,
        readiness_lower_bound=readiness_gate.lower_bound,
        readiness_upper_bound=readiness_gate.upper_bound,
        readiness_topic_strength=readiness_gate.topic_strength,
        readiness_too_easy_gap=readiness_gate.too_easy_gap,
        readiness_too_hard_gap=readiness_gate.too_hard_gap,
    )


def _resolve_readiness_center(
    context: NormalizedProfileBootstrapContext,
) -> tuple[float | None, str | None]:
    challenge_target = clamp01(safe_optional_float(context.challenge_target))
    if challenge_target is not None:
        return challenge_target, "challenge_target"
    proficiency = clamp01(safe_optional_float(context.proficiency_estimate))
    if proficiency is not None:
        return proficiency, "proficiency"
    return None, None


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
    active_topic_rows = _mapping_sequence(active_topic_support.get("topics"))
    active_topic_support_by_name = {
        str(entry.get("topic", "")).strip(): entry
        for entry in active_topic_rows
        if str(entry.get("topic", "")).strip()
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
            admission_suitability=float(signal_pack.admission_suitability),
            topic_bias=float(signal_pack.preference_affinity),
            scarcity_bonus=float(signal_pack.scarcity_bonus),
            user_pref=float(signal_pack.proficiency_fit),
            confidence=0.0,
            difficulty_target=float(signal_pack.challenge_fit),
            pos=str(getattr(seed, "pos_bucket", "") or "").strip() or None,
            metadata={
                "candidate_identity_key": traits.candidate_identity_key,
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
    base_rank_by_identity = {
        candidate_identity_key_from_seed(seed): index + 1
        for index, seed in enumerate(seeds)
        if candidate_identity_key_from_seed(seed)
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
            base_rank=base_rank_by_identity.get(entry.traits.candidate_identity_key, 0),
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
            "admission_suitability": 1.0,
        },
        "profile_context": normalized_context.to_dict(),
        "admission_profile": normalized_context.to_dict(),
        "policy": _build_policy_summary(policy),
        "active_topic_support": active_topic_support,
        "topic_depth_by_level": topic_depth_by_level,
        "ranking_preview": ranking_preview,
    }


def score_seed_words_for_frontier_gaussian_profile(
    seeds: Sequence[object],
    *,
    profile_context: Optional[Mapping[str, object]],
    policy: ProfileBootstrapPolicy = FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY,
    selection_count: Optional[int] = 20,
    preview_limit: Optional[int] = 20,
) -> tuple[list[ProfileBootstrapFrontierLaneEntry], dict[str, object]]:
    scored_entries, base_diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        policy=policy,
        preview_limit=preview_limit,
    )
    lane_entries = [
        _build_frontier_gaussian_lane_entry(entry, policy=policy) for entry in scored_entries
    ]
    selected_entries, lane_diagnostics = select_frontier_gaussian_lane_entries(
        lane_entries,
        selection_count=selection_count,
        policy=policy,
    )
    if preview_limit is None:
        preview_entries = selected_entries
    else:
        preview_entries = selected_entries[: max(0, int(preview_limit))]
    return selected_entries, {
        "selector_version": PROFILE_BOOTSTRAP_SELECTOR_VERSION,
        "selector_policy_version": policy.version,
        "selection_policy": PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_SELECTION_POLICY,
        "profile_context": base_diagnostics.get("profile_context", {}),
        "admission_profile": base_diagnostics.get("admission_profile", {}),
        "policy": base_diagnostics.get("policy", _build_policy_summary(policy)),
        "active_topic_support": base_diagnostics.get("active_topic_support", {}),
        "topic_depth_by_level": base_diagnostics.get("topic_depth_by_level", {}),
        "base_profile_bootstrap": {
            "selection_policy": base_diagnostics.get("selection_policy"),
            "selection_weights": _mapping_to_dict(base_diagnostics.get("selection_weights")),
            "ranking_preview": _sequence_to_list(base_diagnostics.get("ranking_preview")),
        },
        **lane_diagnostics,
        "ranking_preview": [
            _build_frontier_gaussian_preview_entry(
                lane_entry=entry,
                reranked_rank=index + 1,
            )
            for index, entry in enumerate(preview_entries)
        ],
    }


def score_seed_words_for_frontier_gaussian_hybrid_profile(
    seeds: Sequence[object],
    *,
    profile_context: Optional[Mapping[str, object]],
    policy: ProfileBootstrapPolicy = FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
    selection_count: Optional[int] = 20,
    preview_limit: Optional[int] = 20,
) -> tuple[list[ProfileBootstrapFrontierLaneEntry], dict[str, object]]:
    scored_entries, base_diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        policy=policy,
        preview_limit=preview_limit,
    )
    lane_entries = [
        _build_frontier_gaussian_lane_entry(entry, policy=policy) for entry in scored_entries
    ]
    selected_entries, lane_diagnostics = select_frontier_gaussian_hybrid_lane_entries(
        lane_entries,
        selection_count=selection_count,
        policy=policy,
    )
    if preview_limit is None:
        preview_entries = selected_entries
    else:
        preview_entries = selected_entries[: max(0, int(preview_limit))]
    return selected_entries, {
        "selector_version": PROFILE_BOOTSTRAP_SELECTOR_VERSION,
        "selector_policy_version": policy.version,
        "selection_policy": PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_SELECTION_POLICY,
        "profile_context": base_diagnostics.get("profile_context", {}),
        "admission_profile": base_diagnostics.get("admission_profile", {}),
        "policy": base_diagnostics.get("policy", _build_policy_summary(policy)),
        "active_topic_support": base_diagnostics.get("active_topic_support", {}),
        "topic_depth_by_level": base_diagnostics.get("topic_depth_by_level", {}),
        "base_profile_bootstrap": {
            "selection_policy": base_diagnostics.get("selection_policy"),
            "selection_weights": _mapping_to_dict(base_diagnostics.get("selection_weights")),
            "ranking_preview": _sequence_to_list(base_diagnostics.get("ranking_preview")),
        },
        **lane_diagnostics,
        "ranking_preview": [
            _build_frontier_gaussian_preview_entry(
                lane_entry=entry,
                reranked_rank=index + 1,
            )
            for index, entry in enumerate(preview_entries)
        ],
    }


def select_frontier_gaussian_lane_entries(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    *,
    selection_count: Optional[int],
    policy: ProfileBootstrapPolicy,
) -> tuple[list[ProfileBootstrapFrontierLaneEntry], dict[str, object]]:
    target = 0 if selection_count is None else max(0, int(selection_count))
    selectable_entries = [
        entry for entry in lane_entries if float(entry.signal_pack.admission_suitability) > 0.0
    ]
    lane_targets = _resolve_frontier_lane_targets(target, policy=policy)
    selected: list[ProfileBootstrapFrontierLaneEntry] = []
    selected_keys: set[str] = set()
    filled_counts = {FRONTIER_LANE: 0, TRAIL_LANE: 0, TOPIC_LANE: 0}
    initial_lane_order = (TOPIC_LANE, TRAIL_LANE, FRONTIER_LANE)

    for lane_name in initial_lane_order:
        lane_target = lane_targets.get(lane_name, 0)
        if lane_target <= 0:
            continue
        for entry in _rank_frontier_lane_entries(selectable_entries, lane_name):
            if filled_counts[lane_name] >= lane_target:
                break
            if _frontier_lane_score(entry, lane_name) <= 0.0:
                break
            identity_key = _frontier_lane_identity_key(entry)
            if identity_key in selected_keys:
                continue
            selected.append(_with_selected_frontier_lane(entry, lane_name))
            selected_keys.add(identity_key)
            filled_counts[lane_name] += 1

    spill_count = max(0, target - len(selected))
    for lane_name in (FRONTIER_LANE, TOPIC_LANE, TRAIL_LANE):
        if len(selected) >= target:
            break
        for entry in _rank_frontier_lane_entries(selectable_entries, lane_name):
            if len(selected) >= target:
                break
            if _frontier_lane_score(entry, lane_name) <= 0.0:
                break
            identity_key = _frontier_lane_identity_key(entry)
            if identity_key in selected_keys:
                continue
            selected.append(_with_selected_frontier_lane(entry, lane_name))
            selected_keys.add(identity_key)
            filled_counts[lane_name] += 1

    return selected[:target], {
        "lane_targets": lane_targets,
        "filled_lane_counts": filled_counts,
        "requested_selection_count": target,
        "selectable_candidate_count": len(selectable_entries),
        "selected_candidate_count": min(len(selected), target),
        "spill_count": spill_count,
        "lane_fill_order": list(initial_lane_order),
        "spill_order": [FRONTIER_LANE, TOPIC_LANE, TRAIL_LANE],
    }


def select_frontier_gaussian_hybrid_lane_entries(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    *,
    selection_count: Optional[int],
    policy: ProfileBootstrapPolicy,
) -> tuple[list[ProfileBootstrapFrontierLaneEntry], dict[str, object]]:
    target = 0 if selection_count is None else max(0, int(selection_count))
    selectable_entries = [
        entry for entry in lane_entries if float(entry.signal_pack.admission_suitability) > 0.0
    ]
    topic_depth = _hybrid_topic_depth(selectable_entries, policy=policy)
    lane_targets = _resolve_frontier_hybrid_lane_targets(
        selectable_entries,
        selection_count=target,
        policy=policy,
        topic_depth=topic_depth,
    )
    selected: list[ProfileBootstrapFrontierLaneEntry] = []
    selected_keys: set[str] = set()
    filled_counts = {CORE_LANE: 0, FRONTIER_LANE: 0, TRAIL_LANE: 0, TOPIC_LANE: 0}
    initial_lane_order = (CORE_LANE, TOPIC_LANE, TRAIL_LANE, FRONTIER_LANE)

    for lane_name in initial_lane_order:
        lane_target = lane_targets.get(lane_name, 0)
        if lane_target <= 0:
            continue
        for entry in _rank_frontier_hybrid_lane_entries(
            selectable_entries,
            lane_name,
            policy=policy,
        ):
            if filled_counts[lane_name] >= lane_target:
                break
            lane_score = _hybrid_lane_score(
                entry,
                lane_name,
                policy=policy,
            )
            if lane_score < _hybrid_lane_minimum_score(lane_name, policy=policy):
                break
            identity_key = _frontier_lane_identity_key(entry)
            if identity_key in selected_keys:
                continue
            selected.append(
                _with_selected_frontier_lane(
                    entry,
                    lane_name,
                    lane_score_override=lane_score,
                )
            )
            selected_keys.add(identity_key)
            filled_counts[lane_name] += 1

    spill_count = max(0, target - len(selected))
    for lane_name in (FRONTIER_LANE, TOPIC_LANE, TRAIL_LANE, CORE_LANE):
        if len(selected) >= target:
            break
        for entry in _rank_frontier_hybrid_lane_entries(
            selectable_entries,
            lane_name,
            policy=policy,
        ):
            if len(selected) >= target:
                break
            lane_score = _hybrid_lane_score(
                entry,
                lane_name,
                policy=policy,
            )
            if lane_score < _hybrid_lane_minimum_score(lane_name, policy=policy):
                break
            identity_key = _frontier_lane_identity_key(entry)
            if identity_key in selected_keys:
                continue
            selected.append(
                _with_selected_frontier_lane(
                    entry,
                    lane_name,
                    lane_score_override=lane_score,
                )
            )
            selected_keys.add(identity_key)
            filled_counts[lane_name] += 1

    return selected[:target], {
        "lane_targets": lane_targets,
        "filled_lane_counts": filled_counts,
        "requested_selection_count": target,
        "selectable_candidate_count": len(selectable_entries),
        "selected_candidate_count": min(len(selected), target),
        "spill_count": spill_count,
        "lane_fill_order": list(initial_lane_order),
        "spill_order": [FRONTIER_LANE, TOPIC_LANE, TRAIL_LANE, CORE_LANE],
        "hybrid_topic_depth": topic_depth,
    }


def _build_frontier_gaussian_lane_entry(
    entry: ProfileBootstrapScoredEntry,
    *,
    policy: ProfileBootstrapPolicy,
) -> ProfileBootstrapFrontierLaneEntry:
    frontier_fit = _compute_frontier_gaussian_fit(
        entry.signal_pack.difficulty_estimate,
        entry.signal_pack.readiness_center,
        topic_affinity=entry.signal_pack.preference_affinity,
        policy=policy,
    )
    suitability = max(0.0, float(entry.signal_pack.admission_suitability))
    commonness_tie = max(0.0, min(1.0, float(entry.traits.lexical_commonness)))
    topic_affinity = max(0.0, min(1.0, float(entry.signal_pack.preference_affinity)))
    lane_scores = {
        CORE_LANE: max(0.0, float(entry.scored_candidate.breakdown.final_score)),
        FRONTIER_LANE: frontier_fit.frontier_fit * suitability,
        TRAIL_LANE: frontier_fit.trail_fit * (0.75 + (0.25 * commonness_tie)) * suitability,
        TOPIC_LANE: frontier_fit.topic_fit * topic_affinity * suitability,
    }
    return ProfileBootstrapFrontierLaneEntry(
        source_entry=entry,
        frontier_fit=frontier_fit,
        lane_scores=lane_scores,
    )


def _resolve_frontier_lane_targets(
    selection_count: int,
    *,
    policy: ProfileBootstrapPolicy,
) -> dict[str, int]:
    target = max(0, int(selection_count))
    shares = {
        FRONTIER_LANE: max(0.0, float(policy.frontier_lane_share)),
        TRAIL_LANE: max(0.0, float(policy.trail_lane_share)),
        TOPIC_LANE: max(0.0, float(policy.topic_lane_share)),
    }
    share_total = sum(shares.values())
    if target <= 0:
        return {lane: 0 for lane in shares}
    if share_total <= 0.0:
        return {FRONTIER_LANE: target, TRAIL_LANE: 0, TOPIC_LANE: 0}
    raw_targets = {lane: (target * share / share_total) for lane, share in shares.items()}
    lane_targets = {lane: int(raw_value) for lane, raw_value in raw_targets.items()}
    remainder = target - sum(lane_targets.values())
    priority = {
        FRONTIER_LANE: 0,
        TRAIL_LANE: 1,
        TOPIC_LANE: 2,
    }
    fractional_order = sorted(
        raw_targets,
        key=lambda lane: (-(raw_targets[lane] - int(raw_targets[lane])), priority[lane]),
    )
    for lane in fractional_order[:remainder]:
        lane_targets[lane] += 1
    return lane_targets


def _resolve_frontier_hybrid_lane_targets(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    *,
    selection_count: int,
    policy: ProfileBootstrapPolicy,
    topic_depth: Mapping[str, object],
) -> dict[str, int]:
    target = max(0, int(selection_count))
    if target <= 0:
        return {CORE_LANE: 0, FRONTIER_LANE: 0, TRAIL_LANE: 0, TOPIC_LANE: 0}
    proficiency = _frontier_lane_profile_proficiency(lane_entries)
    if proficiency is None:
        return {CORE_LANE: target, FRONTIER_LANE: 0, TRAIL_LANE: 0, TOPIC_LANE: 0}
    core_target = 0
    if proficiency <= float(policy.hybrid_beginner_core_threshold):
        core_target = round(target * max(0.0, float(policy.hybrid_beginner_core_lane_share)))
    topic_target = 0
    eligible_topic_count = int(str(topic_depth.get("eligible_candidate_count") or 0))
    topic_mass = max(0.0, float(str(topic_depth.get("eligible_mass") or 0.0)))
    if eligible_topic_count > 0 and topic_mass > 0.0:
        saturation = max(1e-6, float(policy.hybrid_topic_depth_saturation))
        depth_ratio = topic_mass / (topic_mass + saturation)
        min_share = max(0.0, min(1.0, float(policy.hybrid_topic_min_share)))
        max_share = max(min_share, min(1.0, float(policy.hybrid_topic_max_share)))
        topic_share = min_share + ((max_share - min_share) * depth_ratio)
        topic_target = min(eligible_topic_count, round(target * topic_share))
    trail_target = round(target * max(0.0, float(policy.hybrid_trail_lane_share)))
    fixed_total = core_target + topic_target + trail_target
    if fixed_total > target:
        overflow = fixed_total - target
        trail_reduction = min(trail_target, overflow)
        trail_target -= trail_reduction
        overflow -= trail_reduction
        if overflow:
            topic_reduction = min(topic_target, overflow)
            topic_target -= topic_reduction
            overflow -= topic_reduction
        if overflow:
            core_target = max(0, core_target - overflow)
    frontier_target = max(0, target - core_target - topic_target - trail_target)
    return {
        CORE_LANE: core_target,
        FRONTIER_LANE: frontier_target,
        TRAIL_LANE: trail_target,
        TOPIC_LANE: topic_target,
    }


def _hybrid_topic_depth(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    *,
    policy: ProfileBootstrapPolicy,
) -> dict[str, object]:
    minimum_score = _hybrid_lane_minimum_score(TOPIC_LANE, policy=policy)
    eligible_scores = [
        _hybrid_lane_score(entry, TOPIC_LANE, policy=policy)
        for entry in lane_entries
        if _hybrid_lane_score(entry, TOPIC_LANE, policy=policy) >= minimum_score
    ]
    all_topic_scores = [
        _hybrid_lane_score(entry, TOPIC_LANE, policy=policy)
        for entry in lane_entries
        if _hybrid_lane_score(entry, TOPIC_LANE, policy=policy) > 0.0
    ]
    return {
        "eligible_candidate_count": len(eligible_scores),
        "eligible_mass": round(sum(eligible_scores), 6),
        "candidate_count": len(all_topic_scores),
        "mass": round(sum(all_topic_scores), 6),
        "minimum_lane_score": round(minimum_score, 6),
    }


def _hybrid_lane_minimum_score(
    lane_name: str,
    *,
    policy: ProfileBootstrapPolicy,
) -> float:
    if lane_name == TOPIC_LANE:
        return max(0.0, float(policy.hybrid_topic_min_lane_score))
    return 0.0


def _hybrid_lane_score(
    lane_entry: ProfileBootstrapFrontierLaneEntry,
    lane_name: str,
    *,
    policy: ProfileBootstrapPolicy,
) -> float:
    score = _frontier_lane_score(lane_entry, lane_name)
    if lane_name == TOPIC_LANE:
        proficiency = lane_entry.frontier_fit.proficiency
        if proficiency is not None:
            minimum_difficulty = max(
                0.0,
                float(proficiency) - max(0.0, float(policy.hybrid_topic_lower_margin)),
            )
            lower_gap = minimum_difficulty - float(lane_entry.frontier_fit.difficulty)
            if lower_gap > 0.0:
                sigma = policy.hybrid_topic_lower_penalty_sigma
                if sigma is None or float(sigma) <= 0.0:
                    return 0.0
                score *= math.exp(-((lower_gap / float(sigma)) ** 2))
    return score


def _rank_frontier_hybrid_lane_entries(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    lane_name: str,
    *,
    policy: ProfileBootstrapPolicy,
) -> list[ProfileBootstrapFrontierLaneEntry]:
    return sorted(
        lane_entries,
        key=lambda entry: (
            -_hybrid_lane_score(entry, lane_name, policy=policy),
            -float(entry.traits.lexical_commonness),
            entry.base_index,
            entry.traits.lemma,
        ),
    )


def _frontier_lane_profile_proficiency(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
) -> float | None:
    for entry in lane_entries:
        proficiency = entry.frontier_fit.proficiency
        if proficiency is not None:
            return float(proficiency)
    return None


def _rank_frontier_lane_entries(
    lane_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    lane_name: str,
) -> list[ProfileBootstrapFrontierLaneEntry]:
    return sorted(
        lane_entries,
        key=lambda entry: (
            -_frontier_lane_score(entry, lane_name),
            -float(entry.traits.lexical_commonness),
            entry.base_index,
        ),
    )


def _frontier_lane_score(
    lane_entry: ProfileBootstrapFrontierLaneEntry,
    lane_name: str,
) -> float:
    return max(0.0, float(lane_entry.lane_scores.get(lane_name, 0.0)))


def _with_selected_frontier_lane(
    lane_entry: ProfileBootstrapFrontierLaneEntry,
    lane_name: str,
    *,
    lane_score_override: Optional[float] = None,
) -> ProfileBootstrapFrontierLaneEntry:
    lane_scores = lane_entry.lane_scores
    if lane_score_override is not None:
        lane_scores = {**dict(lane_entry.lane_scores), lane_name: lane_score_override}
    return ProfileBootstrapFrontierLaneEntry(
        source_entry=lane_entry.source_entry,
        frontier_fit=lane_entry.frontier_fit,
        lane_scores=lane_scores,
        selected_lane=lane_name,
    )


def _frontier_lane_identity_key(lane_entry: ProfileBootstrapFrontierLaneEntry) -> str:
    lemma = str(lane_entry.traits.lemma or "").strip()
    pair = str(getattr(lane_entry.seed, "language_pair", "") or "").strip()
    if lemma and pair:
        return f"{pair}:{lemma}"
    identity_key = str(lane_entry.traits.candidate_identity_key or "").strip()
    if identity_key:
        return identity_key
    return f"{lane_entry.base_index}:{lemma}"


def _build_frontier_gaussian_preview_entry(
    *,
    lane_entry: ProfileBootstrapFrontierLaneEntry,
    reranked_rank: int,
) -> dict[str, object]:
    base_rank = lane_entry.base_index + 1
    selected_lane = str(lane_entry.selected_lane or "")
    selected_lane_score = _frontier_lane_score(lane_entry, selected_lane) if selected_lane else None
    preview = _build_preview_entry(
        reranked_rank=reranked_rank,
        seed=lane_entry.seed,
        traits=lane_entry.traits,
        signal_pack=lane_entry.signal_pack,
        scored_candidate=lane_entry.source_entry.scored_candidate,
        base_rank=base_rank,
        policy=DEFAULT_PROFILE_BOOTSTRAP_POLICY,
    )
    preview.update(
        {
            "selected_lane": lane_entry.selected_lane,
            "difficulty_estimate": round(
                float(lane_entry.signal_pack.difficulty_estimate),
                6,
            ),
            "lexical_commonness": round(float(lane_entry.traits.lexical_commonness), 6),
            "topic_affinity": round(float(lane_entry.signal_pack.preference_affinity), 6),
            "admission_suitability": round(
                float(lane_entry.signal_pack.admission_suitability),
                6,
            ),
            "profile_score": round(
                float(selected_lane_score)
                if selected_lane_score is not None
                else float(lane_entry.source_entry.scored_candidate.breakdown.final_score),
                6,
            ),
            "current_profile_score": round(
                float(lane_entry.source_entry.scored_candidate.breakdown.final_score),
                6,
            ),
            "lane_scores": {
                key: round(float(value), 6) for key, value in sorted(lane_entry.lane_scores.items())
            },
            "frontier_gaussian": lane_entry.frontier_fit.to_dict(),
        }
    )
    return preview


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
    bands: list[dict[str, object]] = [
        _new_depth_band(label, lower, upper) for label, lower, upper in PROFILE_TOPIC_DEPTH_BANDS
    ]
    topic_entries: list[dict[str, object]] = [
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
        _increment_payload_counter(band, "candidate_count")
        if topic_affinity > 0.0:
            _increment_payload_counter(band, "preferred_topic_count")
            if readiness >= PROFILE_TOPIC_DEPTH_READY_THRESHOLD:
                _increment_payload_counter(band, "ready_preferred_topic_count")
            if readiness >= PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD:
                _increment_payload_counter(band, "high_readiness_preferred_topic_count")
            _append_topic_depth_example(band["top_preferred_examples"], entry)

        for topic, _weight in active_topics:
            if not _entry_matches_active_topic(entry, topic):
                continue
            topic_entry = topic_entry_by_name[topic]
            _increment_payload_counter(topic_entry, "candidate_count")
            if readiness >= PROFILE_TOPIC_DEPTH_READY_THRESHOLD:
                _increment_payload_counter(topic_entry, "ready_candidate_count")
            if readiness >= PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD:
                _increment_payload_counter(topic_entry, "high_readiness_candidate_count")
            max_difficulty = topic_entry["max_difficulty"]
            parsed_max_difficulty = _safe_float(max_difficulty)
            if parsed_max_difficulty is None or difficulty > parsed_max_difficulty:
                topic_entry["max_difficulty"] = round(difficulty, 6)
            topic_band = _topic_band_at(topic_entry, band_index)
            if topic_band is None:
                continue
            _increment_payload_counter(topic_band, "candidate_count")
            if readiness >= PROFILE_TOPIC_DEPTH_READY_THRESHOLD:
                _increment_payload_counter(topic_band, "ready_candidate_count")
            if readiness >= PROFILE_TOPIC_DEPTH_HIGH_READINESS_THRESHOLD:
                _increment_payload_counter(topic_band, "high_readiness_candidate_count")
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


def _mapping_sequence(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [entry for entry in value if isinstance(entry, Mapping)]


def _topic_band_at(
    topic_entry: Mapping[str, object],
    band_index: int,
) -> MutableMapping[str, object] | None:
    bands = topic_entry.get("bands")
    if not isinstance(bands, Sequence) or isinstance(bands, (str, bytes)):
        return None
    if band_index < 0 or band_index >= len(bands):
        return None
    band = bands[band_index]
    return band if isinstance(band, dict) else None


def _increment_payload_counter(payload: MutableMapping[str, object], key: str) -> None:
    payload[key] = _safe_int(payload.get(key)) + 1


def _safe_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value or "").strip() or "0")
    except (TypeError, ValueError):
        return 0


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (float, int)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _mapping_to_dict(value: object) -> dict[object, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence_to_list(value: object) -> list[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return []
    return list(value)


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
