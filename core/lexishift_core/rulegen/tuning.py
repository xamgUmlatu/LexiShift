from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Sequence

from lexishift_core.rulegen.generation import (
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)


@dataclass(frozen=True)
class RulegenPairTuning:
    pair: str
    confidence_threshold: float = 0.0
    max_definitions_per_target: int = 3
    max_rules_per_target: Optional[int] = None
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    notes: Sequence[str] = ()


@dataclass(frozen=True)
class RulegenTuningOverrides:
    confidence_threshold: Optional[float] = None
    max_definitions_per_target: Optional[int] = None
    max_rules_per_target: Optional[int] = None
    pos_scoring_enabled: Optional[bool] = None
    pos_exact_match_bonus: Optional[float] = None
    pos_compatible_match_bonus: Optional[float] = None
    score_weight_dict_priority: Optional[float] = None
    score_weight_frequency_weight: Optional[float] = None
    score_weight_pos_match: Optional[float] = None
    score_weight_variant_penalty: Optional[float] = None
    score_weight_phrase_penalty: Optional[float] = None
    score_weight_embedding: Optional[float] = None


@dataclass(frozen=True)
class ResolvedRulegenTuning:
    pair: str
    confidence_threshold: float
    max_definitions_per_target: Optional[int]
    max_rules_per_target: Optional[int]
    scoring: RuleScoringConfig


_DEFAULT_PAIR_TUNING = RulegenPairTuning(pair="*")

_PAIR_TUNINGS: dict[str, RulegenPairTuning] = {
    "en-ja": RulegenPairTuning(pair="en-ja"),
    "en-de": RulegenPairTuning(pair="en-de"),
    "en-es": RulegenPairTuning(pair="en-es"),
    "es-en": RulegenPairTuning(pair="es-en"),
}


def resolve_pair_rulegen_tuning(pair: str) -> RulegenPairTuning:
    normalized = str(pair or "").strip().lower()
    if not normalized:
        return _DEFAULT_PAIR_TUNING
    return _PAIR_TUNINGS.get(normalized, RulegenPairTuning(pair=normalized))


def resolve_rulegen_tuning(
    pair: str,
    *,
    overrides: Optional[RulegenTuningOverrides] = None,
) -> ResolvedRulegenTuning:
    resolved_pair = resolve_pair_rulegen_tuning(pair)
    applied_overrides = overrides or RulegenTuningOverrides()

    confidence_threshold = (
        float(applied_overrides.confidence_threshold)
        if applied_overrides.confidence_threshold is not None
        else float(resolved_pair.confidence_threshold)
    )

    max_definitions_per_target = (
        _normalize_optional_cap(applied_overrides.max_definitions_per_target)
        if applied_overrides.max_definitions_per_target is not None
        else _normalize_optional_cap(resolved_pair.max_definitions_per_target)
    )
    max_rules_per_target = (
        _normalize_optional_cap(applied_overrides.max_rules_per_target)
        if applied_overrides.max_rules_per_target is not None
        else _normalize_optional_cap(resolved_pair.max_rules_per_target)
    )

    weights = _resolve_rule_score_weights(
        resolved_pair.scoring.weights,
        overrides=applied_overrides,
    )
    pos_match = _resolve_pos_match_scoring(
        resolved_pair.scoring.pos_match,
        overrides=applied_overrides,
    )

    return ResolvedRulegenTuning(
        pair=resolved_pair.pair,
        confidence_threshold=confidence_threshold,
        max_definitions_per_target=max_definitions_per_target,
        max_rules_per_target=max_rules_per_target,
        scoring=RuleScoringConfig(weights=weights, pos_match=pos_match),
    )


def rulegen_pair_tuning_to_dict(policy: RulegenPairTuning) -> dict[str, object]:
    return {
        "pair": policy.pair,
        "confidence_threshold": float(policy.confidence_threshold),
        "max_definitions_per_target": int(policy.max_definitions_per_target),
        "max_rules_per_target": (
            int(policy.max_rules_per_target)
            if policy.max_rules_per_target is not None
            else None
        ),
        "scoring": _scoring_to_dict(policy.scoring),
        "notes": list(policy.notes),
    }


def resolved_rulegen_tuning_to_dict(tuning: ResolvedRulegenTuning) -> dict[str, object]:
    return {
        "pair": tuning.pair,
        "confidence_threshold": float(tuning.confidence_threshold),
        "max_definitions_per_target": (
            int(tuning.max_definitions_per_target)
            if tuning.max_definitions_per_target is not None
            else None
        ),
        "max_rules_per_target": (
            int(tuning.max_rules_per_target)
            if tuning.max_rules_per_target is not None
            else None
        ),
        "scoring": _scoring_to_dict(tuning.scoring),
    }


def rulegen_tuning_overrides_to_dict(
    overrides: RulegenTuningOverrides,
    *,
    include_none: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "confidence_threshold": overrides.confidence_threshold,
        "max_definitions_per_target": overrides.max_definitions_per_target,
        "max_rules_per_target": overrides.max_rules_per_target,
        "pos_scoring_enabled": overrides.pos_scoring_enabled,
        "pos_exact_match_bonus": overrides.pos_exact_match_bonus,
        "pos_compatible_match_bonus": overrides.pos_compatible_match_bonus,
        "score_weight_dict_priority": overrides.score_weight_dict_priority,
        "score_weight_frequency_weight": overrides.score_weight_frequency_weight,
        "score_weight_pos_match": overrides.score_weight_pos_match,
        "score_weight_variant_penalty": overrides.score_weight_variant_penalty,
        "score_weight_phrase_penalty": overrides.score_weight_phrase_penalty,
        "score_weight_embedding": overrides.score_weight_embedding,
    }
    if include_none:
        return payload
    return {key: value for key, value in payload.items() if value is not None}


def _normalize_optional_cap(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    parsed = int(value)
    if parsed <= 0:
        return None
    return parsed


def _resolve_rule_score_weights(
    defaults: RuleScoreWeights,
    *,
    overrides: RulegenTuningOverrides,
) -> RuleScoreWeights:
    weights = defaults
    if overrides.score_weight_dict_priority is not None:
        weights = replace(weights, dict_priority=float(overrides.score_weight_dict_priority))
    if overrides.score_weight_frequency_weight is not None:
        weights = replace(weights, frequency_weight=float(overrides.score_weight_frequency_weight))
    if overrides.score_weight_pos_match is not None:
        weights = replace(weights, pos_match=float(overrides.score_weight_pos_match))
    if overrides.score_weight_variant_penalty is not None:
        weights = replace(weights, variant_penalty=float(overrides.score_weight_variant_penalty))
    if overrides.score_weight_phrase_penalty is not None:
        weights = replace(weights, phrase_penalty=float(overrides.score_weight_phrase_penalty))
    if overrides.score_weight_embedding is not None:
        weights = replace(weights, embedding_weight=float(overrides.score_weight_embedding))
    return weights


def _resolve_pos_match_scoring(
    defaults: PosMatchScoringConfig,
    *,
    overrides: RulegenTuningOverrides,
) -> PosMatchScoringConfig:
    resolved = defaults
    if overrides.pos_scoring_enabled is not None:
        resolved = replace(resolved, enabled=bool(overrides.pos_scoring_enabled))
    if overrides.pos_exact_match_bonus is not None:
        resolved = replace(resolved, exact_match_bonus=float(overrides.pos_exact_match_bonus))
    if overrides.pos_compatible_match_bonus is not None:
        resolved = replace(
            resolved,
            compatible_match_bonus=float(overrides.pos_compatible_match_bonus),
        )
    return resolved


def _scoring_to_dict(scoring: RuleScoringConfig) -> dict[str, object]:
    return {
        "weights": {
            "dict_priority": float(scoring.weights.dict_priority),
            "frequency_weight": float(scoring.weights.frequency_weight),
            "pos_match": float(scoring.weights.pos_match),
            "variant_penalty": float(scoring.weights.variant_penalty),
            "phrase_penalty": float(scoring.weights.phrase_penalty),
            "embedding_weight": float(scoring.weights.embedding_weight),
        },
        "pos_match": {
            "enabled": bool(scoring.pos_match.enabled),
            "exact_match_bonus": float(scoring.pos_match.exact_match_bonus),
            "compatible_match_bonus": float(scoring.pos_match.compatible_match_bonus),
            "compatibility_classes": (
                dict(scoring.pos_match.compatibility_classes)
                if scoring.pos_match.compatibility_classes is not None
                else None
            ),
        },
    }
