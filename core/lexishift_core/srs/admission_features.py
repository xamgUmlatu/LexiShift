from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Mapping, Optional, Sequence

ADMISSION_PROFILE_FEATURES_VERSION = "admission_profile_features_v1"
ADMISSION_CANDIDATE_FEATURES_VERSION = "admission_candidate_features_v1"
ADMISSION_UTILITY_SIGNALS_VERSION = "admission_utility_signals_v1"
TOPIC_FAMILY_NORMALIZATION_VERSION = "topic_family_v1"

_TOPIC_CANONICAL_ALIASES = {
    "animal": "animals",
    "pet": "pets",
    "game": "games",
    "sport": "sports",
    "live_stream": "livestream",
    "live_streaming": "livestream",
    "video_streaming": "livestream",
}

_TOPIC_PARENT_MAP = {
    "pets": ("animals",),
    "wildlife": ("animals",),
    "zoology": ("animals",),
    "veterinary": ("animals",),
    "ball_games": ("games", "sports"),
    "board_games": ("games",),
    "card_games": ("games",),
    "video_games": ("games",),
    "gaming": ("games",),
    "mahjong": ("games",),
    "soccer": ("games", "sports"),
    "baseball": ("games", "sports"),
    "bowling": ("games", "sports"),
    "musical_instruments": ("music",),
    "orchestra": ("music",),
    "orchestras": ("music",),
    "orchestral_music": ("music",),
    "athletics": ("sports",),
    "martial_arts": ("sports",),
    "archery": ("sports",),
    "banking": ("finance",),
    "business": ("finance",),
    "economics": ("finance",),
    "commerce": ("finance",),
    "investing": ("finance",),
    "streaming": ("livestream",),
    "manga": ("anime",),
    "otaku": ("anime",),
}

_TOPIC_BACKGROUND_HINTS = frozenset(
    {
        "entertainment",
        "general",
        "hobbies",
        "lifestyle",
    }
)


@dataclass(frozen=True)
class AdmissionProfileFeatures:
    version: str = ADMISSION_PROFILE_FEATURES_VERSION
    raw_profile_keys: Sequence[str] = field(default_factory=tuple)
    interests: Sequence[str] = field(default_factory=tuple)
    explicit_topic_weights: Mapping[str, float] = field(default_factory=dict)
    implicit_topic_weights: Mapping[str, float] = field(default_factory=dict)
    topic_weights: Mapping[str, float] = field(default_factory=dict)
    topic_weight_sources: Mapping[str, str] = field(default_factory=dict)
    proficiency_estimate: Optional[float] = None
    challenge_target: Optional[float] = None
    challenge_spread: Optional[float] = None
    goal_mode: Optional[str] = None
    active_signals: Sequence[str] = field(default_factory=tuple)
    missing_signals: Sequence[str] = field(default_factory=tuple)
    signal_sources: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "topic_normalization_version": TOPIC_FAMILY_NORMALIZATION_VERSION,
            "raw_profile_keys": list(self.raw_profile_keys),
            "interests": list(self.interests),
            "explicit_topic_weights": dict(self.explicit_topic_weights),
            "implicit_topic_weights": dict(self.implicit_topic_weights),
            "topic_weights": dict(self.topic_weights),
            "topic_weight_sources": dict(self.topic_weight_sources),
            "proficiency_estimate": rounded_or_none(self.proficiency_estimate),
            "challenge_target": rounded_or_none(self.challenge_target),
            "challenge_spread": rounded_or_none(self.challenge_spread),
            "goal_mode": self.goal_mode,
            "active_signals": list(self.active_signals),
            "missing_signals": list(self.missing_signals),
            "signal_sources": dict(self.signal_sources),
        }


@dataclass(frozen=True)
class AdmissionCandidateFeatures:
    version: str = ADMISSION_CANDIDATE_FEATURES_VERSION
    candidate_identity_key: str = ""
    lemma: str = ""
    lexical_commonness: float = 0.0
    coverage_gain: float = 0.0
    difficulty_estimate: float = 0.0
    difficulty_proxy: str = ""
    difficulty_sources: Sequence[str] = field(default_factory=tuple)
    candidate_state: str = "normal_vocab"
    presentation_mode: str = "vocab"
    problem_class: str = "normal_vocab"
    classification_confidence: str = "review"
    classification_reasons: Sequence[str] = field(default_factory=tuple)
    admission_suitability: float = 1.0
    lexical_forms: Sequence[str] = field(default_factory=tuple)
    learner_signals: Mapping[str, object] = field(default_factory=dict)
    raw_topic_hints: Sequence[str] = field(default_factory=tuple)
    topic_hints: Sequence[str] = field(default_factory=tuple)
    topic_hint_origins: Mapping[str, Sequence[str]] = field(default_factory=dict)

    @property
    def base_freq(self) -> float:
        return self.coverage_gain

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "topic_normalization_version": TOPIC_FAMILY_NORMALIZATION_VERSION,
            "candidate_identity_key": self.candidate_identity_key,
            "lemma": self.lemma,
            "lexical_commonness": rounded_or_none(self.lexical_commonness),
            "coverage_gain": rounded_or_none(self.coverage_gain),
            "base_freq": rounded_or_none(self.coverage_gain),
            "difficulty_estimate": rounded_or_none(self.difficulty_estimate),
            "difficulty_proxy": self.difficulty_proxy,
            "difficulty_sources": list(self.difficulty_sources),
            "candidate_state": self.candidate_state,
            "presentation_mode": self.presentation_mode,
            "problem_class": self.problem_class,
            "classification_confidence": self.classification_confidence,
            "classification_reasons": list(self.classification_reasons),
            "admission_suitability": rounded_or_none(self.admission_suitability),
            "lexical_forms": list(self.lexical_forms),
            "learner_signals": dict(self.learner_signals),
            "raw_topic_hints": list(self.raw_topic_hints),
            "topic_hints": list(self.topic_hints),
            "topic_hint_origins": {
                key: list(values) for key, values in self.topic_hint_origins.items()
            },
        }


@dataclass(frozen=True)
class AdmissionUtilitySignals:
    version: str = ADMISSION_UTILITY_SIGNALS_VERSION
    coverage_gain: float = 0.0
    admission_suitability: float = 1.0
    preference_affinity: float = 0.0
    preference_affinity_source: Optional[str] = None
    scarcity_bonus: float = 0.0
    scarcity_bonus_source: Optional[str] = None
    topic_specificity: float = 0.0
    topic_support_count: int = 0
    topic_hint_count: int = 0
    proficiency_fit: float = 0.0
    challenge_fit: float = 0.0
    readiness_multiplier: float = 1.0
    readiness_center: Optional[float] = None
    readiness_center_source: Optional[str] = None
    readiness_lower_bound: float = 0.0
    readiness_upper_bound: float = 1.0
    readiness_topic_strength: float = 0.0
    readiness_too_easy_gap: float = 0.0
    readiness_too_hard_gap: float = 0.0
    lexical_risk: float = 0.0
    redundancy: float = 0.0
    exploration_bonus: float = 0.0
    difficulty_estimate: float = 0.0

    @property
    def base_freq(self) -> float:
        return self.coverage_gain

    @property
    def topic_affinity(self) -> float:
        return self.preference_affinity

    @property
    def topic_affinity_source(self) -> Optional[str]:
        return self.preference_affinity_source

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "coverage_gain": rounded_or_none(self.coverage_gain),
            "admission_suitability": rounded_or_none(self.admission_suitability),
            "preference_affinity": rounded_or_none(self.preference_affinity),
            "preference_affinity_source": self.preference_affinity_source,
            "scarcity_bonus": rounded_or_none(self.scarcity_bonus),
            "scarcity_bonus_source": self.scarcity_bonus_source,
            "topic_specificity": rounded_or_none(self.topic_specificity),
            "topic_support_count": int(self.topic_support_count),
            "topic_hint_count": int(self.topic_hint_count),
            "proficiency_fit": rounded_or_none(self.proficiency_fit),
            "challenge_fit": rounded_or_none(self.challenge_fit),
            "readiness_multiplier": rounded_or_none(self.readiness_multiplier),
            "readiness_center": rounded_or_none(self.readiness_center),
            "readiness_center_source": self.readiness_center_source,
            "readiness_lower_bound": rounded_or_none(self.readiness_lower_bound),
            "readiness_upper_bound": rounded_or_none(self.readiness_upper_bound),
            "readiness_topic_strength": rounded_or_none(self.readiness_topic_strength),
            "readiness_too_easy_gap": rounded_or_none(self.readiness_too_easy_gap),
            "readiness_too_hard_gap": rounded_or_none(self.readiness_too_hard_gap),
            "lexical_risk": rounded_or_none(self.lexical_risk),
            "redundancy": rounded_or_none(self.redundancy),
            "exploration_bonus": rounded_or_none(self.exploration_bonus),
            "difficulty_estimate": rounded_or_none(self.difficulty_estimate),
            "base_freq": rounded_or_none(self.coverage_gain),
            "topic_affinity": rounded_or_none(self.preference_affinity),
            "topic_affinity_source": self.preference_affinity_source,
        }


def normalize_admission_profile_features(
    profile_context: Optional[Mapping[str, object]],
) -> AdmissionProfileFeatures:
    context = profile_context or {}
    raw_profile_keys = tuple(sorted(str(key) for key in context.keys()))
    interests = tuple(normalize_topic_string_list(context.get("interests")))
    interest_topic_weights = _normalize_interest_topic_weights(interests)
    configured_topic_weights = _normalize_topic_weight_map(
        mapping_or_empty(context.get("topic_weights")),
        source_name="topic_weights",
    )
    explicit_topic_weights = dict(configured_topic_weights)
    for key, interest_entry in interest_topic_weights.items():
        previous_entry = explicit_topic_weights.get(key)
        if previous_entry is None or float(interest_entry[0]) >= float(previous_entry[0]):
            explicit_topic_weights[key] = interest_entry
    empirical_trends = mapping_or_empty(context.get("empirical_trends"))
    if not empirical_trends:
        empirical_trends = mapping_or_empty(context.get("empiricalTrends"))
    implicit_topic_weights = _normalize_topic_weight_map(
        mapping_or_empty(empirical_trends.get("topic_bias")),
        source_name="empirical_trends.topic_bias",
    )
    merged_topic_weights, topic_weight_sources = _merge_topic_weights(
        _expand_weighted_topic_map(implicit_topic_weights),
        _expand_weighted_topic_map(explicit_topic_weights),
    )

    proficiency_estimate, proficiency_source = resolve_first_float(
        (
            ("proficiency_estimate", context.get("proficiency_estimate")),
            (
                "proficiency.estimated_value",
                mapping_or_empty(context.get("proficiency")).get("estimated_value"),
            ),
            (
                "placement_result.proficiency_estimate.value",
                mapping_or_empty(
                    mapping_or_empty(context.get("placement_result")).get("proficiency_estimate")
                ).get("value"),
            ),
            (
                "proficiency.self_reported_level",
                mapping_or_empty(context.get("proficiency")).get("self_reported_level"),
            ),
        )
    )
    challenge_target, challenge_target_source = resolve_first_float(
        (
            ("challenge_target", context.get("challenge_target")),
            (
                "difficulty_preferences.target_challenge_center",
                mapping_or_empty(context.get("difficulty_preferences")).get(
                    "target_challenge_center"
                ),
            ),
            (
                "placement_result.target_challenge.center",
                mapping_or_empty(
                    mapping_or_empty(context.get("placement_result")).get("target_challenge")
                ).get("center"),
            ),
        )
    )
    challenge_spread, challenge_spread_source = resolve_first_float(
        (
            ("challenge_spread", context.get("challenge_spread")),
            (
                "difficulty_preferences.target_challenge_spread",
                mapping_or_empty(context.get("difficulty_preferences")).get(
                    "target_challenge_spread"
                ),
            ),
            (
                "placement_result.target_challenge.spread",
                mapping_or_empty(
                    mapping_or_empty(context.get("placement_result")).get("target_challenge")
                ).get("spread"),
            ),
        )
    )
    goal_mode = _resolve_goal_mode(context)

    active_signals: list[str] = []
    missing_signals: list[str] = []
    signal_sources: dict[str, str] = {}
    if merged_topic_weights:
        active_signals.append("interests")
        signal_sources["interests"] = _summarize_topic_weight_sources(topic_weight_sources)
    else:
        missing_signals.append("interests")
    if proficiency_estimate is not None:
        active_signals.append("proficiency")
        if proficiency_source:
            signal_sources["proficiency"] = proficiency_source
    else:
        missing_signals.append("proficiency")
    if challenge_target is not None:
        active_signals.append("challenge_preference")
        if challenge_target_source:
            signal_sources["challenge_preference"] = challenge_target_source
        if challenge_spread_source:
            signal_sources["challenge_spread"] = challenge_spread_source
    else:
        missing_signals.append("challenge_preference")

    return AdmissionProfileFeatures(
        raw_profile_keys=raw_profile_keys,
        interests=interests,
        explicit_topic_weights={
            key: value for key, (value, _source) in explicit_topic_weights.items()
        },
        implicit_topic_weights={
            key: value for key, (value, _source) in implicit_topic_weights.items()
        },
        topic_weights=merged_topic_weights,
        topic_weight_sources=topic_weight_sources,
        proficiency_estimate=proficiency_estimate,
        challenge_target=challenge_target,
        challenge_spread=challenge_spread,
        goal_mode=goal_mode,
        active_signals=tuple(active_signals),
        missing_signals=tuple(missing_signals),
        signal_sources=signal_sources,
    )


def resolve_first_float(
    candidates: Sequence[tuple[str, object]],
) -> tuple[Optional[float], Optional[str]]:
    for source_name, value in candidates:
        normalized = clamp01(safe_optional_float(value))
        if normalized is not None:
            return normalized, source_name
    return None, None


def normalize_string_list(value: object) -> list[str]:
    return _parse_normalized_string_list(value)


def normalize_topic_string_list(value: object) -> list[str]:
    tokens, _origins = normalize_topic_string_list_with_origins(value)
    return tokens


def normalize_topic_string_list_with_origins(
    value: object,
) -> tuple[list[str], dict[str, list[str]]]:
    base_tokens = _parse_normalized_string_list(value)
    origins: dict[str, list[str]] = {}
    for token in base_tokens:
        for expanded in expand_topic_token_family(token):
            entries = origins.setdefault(expanded, [])
            if token not in entries:
                entries.append(token)
    return list(origins.keys()), origins


def _parse_normalized_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                decoded = None
            if decoded is not None:
                return _parse_normalized_string_list(decoded)
        if "," in stripped:
            return _parse_normalized_string_list([part.strip() for part in stripped.split(",")])
        normalized = canonicalize_topic_token(stripped)
        return [normalized] if normalized else []
    if isinstance(value, Sequence):
        normalized_tokens: list[str] = []
        for item in value:
            if isinstance(item, (str, int, float)):
                token = canonicalize_topic_token(item)
                if token:
                    normalized_tokens.append(token)
        return normalized_tokens
    return []


def canonicalize_topic_token(value: object) -> str:
    normalized = normalize_topic_token(value)
    if not normalized:
        return ""
    return _TOPIC_CANONICAL_ALIASES.get(normalized, normalized)


def expand_topic_token_family(value: object) -> tuple[str, ...]:
    root = canonicalize_topic_token(value)
    if not root:
        return tuple()
    expanded: list[str] = []
    seen: set[str] = set()
    pending = [root]
    while pending:
        current = pending.pop(0)
        if current in seen:
            continue
        seen.add(current)
        expanded.append(current)
        for parent in _TOPIC_PARENT_MAP.get(current, ()):
            canonical_parent = canonicalize_topic_token(parent)
            if canonical_parent and canonical_parent not in seen:
                pending.append(canonical_parent)
    return tuple(expanded)


def is_background_topic_token(value: object) -> bool:
    return canonicalize_topic_token(value) in _TOPIC_BACKGROUND_HINTS


def normalize_topic_token(value: object) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    normalized = raw.replace("\\", "_").replace("/", "_").replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def mapping_or_empty(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def safe_optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def clamp01(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def rounded_or_none(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 6)


def _normalize_interest_topic_weights(
    interests: Sequence[str],
) -> dict[str, tuple[float, str]]:
    normalized: dict[str, tuple[float, str]] = {}
    for interest in interests:
        key = canonicalize_topic_token(interest)
        if key:
            normalized[key] = (1.0, "interests")
    return normalized


def _normalize_topic_weight_map(
    mapping: Mapping[str, object],
    *,
    source_name: str,
) -> dict[str, tuple[float, str]]:
    normalized: dict[str, tuple[float, str]] = {}
    for key, value in mapping.items():
        normalized_key = canonicalize_topic_token(key)
        normalized_value = clamp01(safe_optional_float(value))
        if normalized_key and normalized_value and normalized_value > 0.0:
            previous = normalized.get(normalized_key)
            if previous is None or normalized_value > previous[0]:
                normalized[normalized_key] = (normalized_value, source_name)
    return normalized


def _expand_weighted_topic_map(
    weighted_map: Mapping[str, tuple[float, str]],
) -> dict[str, tuple[float, str]]:
    expanded: dict[str, tuple[float, str]] = {}
    for key, (value, source_name) in weighted_map.items():
        for expanded_key in expand_topic_token_family(key):
            previous = expanded.get(expanded_key)
            if previous is None or float(value) > float(previous[0]):
                expanded[expanded_key] = (value, source_name)
    return expanded


def _merge_topic_weights(
    *weighted_maps: Mapping[str, tuple[float, str]],
) -> tuple[dict[str, float], dict[str, str]]:
    merged: dict[str, float] = {}
    sources: dict[str, str] = {}
    for weighted_map in weighted_maps:
        for key, (value, source_name) in weighted_map.items():
            previous_value = float(merged.get(key, 0.0))
            if value > previous_value:
                merged[key] = value
                sources[key] = source_name
    return merged, sources


def _resolve_goal_mode(context: Mapping[str, object]) -> Optional[str]:
    for raw_value in (
        context.get("goal_mode"),
        mapping_or_empty(context.get("difficulty_preferences")).get("goal_mode"),
        mapping_or_empty(context.get("placement_result")).get("goal_mode"),
        mapping_or_empty(mapping_or_empty(context.get("placement_result")).get("context")).get(
            "goal_mode"
        ),
    ):
        normalized = str(raw_value or "").strip()
        if normalized:
            return normalized
    return None


def _summarize_topic_weight_sources(topic_weight_sources: Mapping[str, str]) -> str:
    ordered = sorted({str(value) for value in topic_weight_sources.values() if str(value).strip()})
    if not ordered:
        return "interests"
    return "+".join(ordered)
