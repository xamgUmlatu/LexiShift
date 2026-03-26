from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Sequence

from lexishift_core.rulegen.generation import (
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig


@dataclass(frozen=True)
class RulegenPairTuning:
    pair: str
    confidence_threshold: float = 0.0
    max_definitions_per_target: int = 3
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: float = 1.0
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    notes: Sequence[str] = ()


@dataclass(frozen=True)
class RulegenTuningOverrides:
    confidence_threshold: Optional[float] = None
    max_definitions_per_target: Optional[int] = None
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: Optional[float] = None
    include_variants: Optional[bool] = None
    allow_multiword_glosses: Optional[bool] = None
    pos_scoring_enabled: Optional[bool] = None
    pos_exact_match_bonus: Optional[float] = None
    pos_compatible_match_bonus: Optional[float] = None
    score_weight_dict_priority: Optional[float] = None
    score_weight_frequency_weight: Optional[float] = None
    score_weight_pos_match: Optional[float] = None
    score_weight_variant_penalty: Optional[float] = None
    score_weight_phrase_penalty: Optional[float] = None
    score_weight_embedding: Optional[float] = None
    reverse_check_enabled: Optional[bool] = None
    reverse_check_match_bonus: Optional[float] = None
    reverse_check_near_bonus: Optional[float] = None
    reverse_check_near_rank_max: Optional[int] = None
    reverse_check_far_hit_penalty: Optional[float] = None
    reverse_check_miss_penalty: Optional[float] = None
    reverse_check_exact_hit_ambiguity_threshold: Optional[int] = None
    reverse_check_exact_hit_ambiguity_penalty: Optional[float] = None


@dataclass(frozen=True)
class ResolvedRulegenTuning:
    pair: str
    confidence_threshold: float
    max_definitions_per_target: Optional[int]
    max_rules_per_target: Optional[int]
    semantic_demotion_scale: float
    include_variants: bool
    allow_multiword_glosses: bool
    scoring: RuleScoringConfig
    reverse_check: ReverseCheckScoringConfig


_DEFAULT_PAIR_TUNING = RulegenPairTuning(pair="*")

_PAIR_TUNINGS: dict[str, RulegenPairTuning] = {
    "en-ja": RulegenPairTuning(
        pair="en-ja",
        max_definitions_per_target=2,
        max_rules_per_target=1,
        include_variants=True,
        notes=(
            "Production default tuned from benchmark sweeps: prioritize high-precision top-1 mapping with one rule per target.",
        ),
    ),
    "en-de": RulegenPairTuning(pair="en-de"),
    "en-es": RulegenPairTuning(
        pair="en-es",
        max_definitions_per_target=3,
        max_rules_per_target=None,
        include_variants=False,
        notes=(
            "Production default tuned from benchmark sweeps: variant expansion disabled to reduce forbidden and noisy multi-meaning candidates.",
        ),
    ),
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
    semantic_demotion_scale = (
        _normalize_semantic_demotion_scale(applied_overrides.semantic_demotion_scale)
        if applied_overrides.semantic_demotion_scale is not None
        else _normalize_semantic_demotion_scale(resolved_pair.semantic_demotion_scale)
    )
    include_variants = (
        bool(applied_overrides.include_variants)
        if applied_overrides.include_variants is not None
        else bool(resolved_pair.include_variants)
    )
    allow_multiword_glosses = (
        bool(applied_overrides.allow_multiword_glosses)
        if applied_overrides.allow_multiword_glosses is not None
        else bool(resolved_pair.allow_multiword_glosses)
    )

    weights = _resolve_rule_score_weights(
        resolved_pair.scoring.weights,
        overrides=applied_overrides,
    )
    pos_match = _resolve_pos_match_scoring(
        resolved_pair.scoring.pos_match,
        overrides=applied_overrides,
    )
    reverse_check = _resolve_reverse_check_scoring(
        resolved_pair.reverse_check,
        overrides=applied_overrides,
    )

    return ResolvedRulegenTuning(
        pair=resolved_pair.pair,
        confidence_threshold=confidence_threshold,
        max_definitions_per_target=max_definitions_per_target,
        max_rules_per_target=max_rules_per_target,
        semantic_demotion_scale=semantic_demotion_scale,
        include_variants=include_variants,
        allow_multiword_glosses=allow_multiword_glosses,
        scoring=RuleScoringConfig(weights=weights, pos_match=pos_match),
        reverse_check=reverse_check,
    )


def rulegen_pair_tuning_to_dict(policy: RulegenPairTuning) -> dict[str, object]:
    return {
        "pair": policy.pair,
        "confidence_threshold": float(policy.confidence_threshold),
        "max_definitions_per_target": int(policy.max_definitions_per_target),
        "max_rules_per_target": (
            int(policy.max_rules_per_target) if policy.max_rules_per_target is not None else None
        ),
        "semantic_demotion_scale": float(policy.semantic_demotion_scale),
        "include_variants": bool(policy.include_variants),
        "allow_multiword_glosses": bool(policy.allow_multiword_glosses),
        "scoring": _scoring_to_dict(policy.scoring),
        "reverse_check": _reverse_check_to_dict(policy.reverse_check),
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
            int(tuning.max_rules_per_target) if tuning.max_rules_per_target is not None else None
        ),
        "semantic_demotion_scale": float(tuning.semantic_demotion_scale),
        "include_variants": bool(tuning.include_variants),
        "allow_multiword_glosses": bool(tuning.allow_multiword_glosses),
        "scoring": _scoring_to_dict(tuning.scoring),
        "reverse_check": _reverse_check_to_dict(tuning.reverse_check),
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
        "semantic_demotion_scale": overrides.semantic_demotion_scale,
        "include_variants": overrides.include_variants,
        "allow_multiword_glosses": overrides.allow_multiword_glosses,
        "pos_scoring_enabled": overrides.pos_scoring_enabled,
        "pos_exact_match_bonus": overrides.pos_exact_match_bonus,
        "pos_compatible_match_bonus": overrides.pos_compatible_match_bonus,
        "score_weight_dict_priority": overrides.score_weight_dict_priority,
        "score_weight_frequency_weight": overrides.score_weight_frequency_weight,
        "score_weight_pos_match": overrides.score_weight_pos_match,
        "score_weight_variant_penalty": overrides.score_weight_variant_penalty,
        "score_weight_phrase_penalty": overrides.score_weight_phrase_penalty,
        "score_weight_embedding": overrides.score_weight_embedding,
        "reverse_check_enabled": overrides.reverse_check_enabled,
        "reverse_check_match_bonus": overrides.reverse_check_match_bonus,
        "reverse_check_near_bonus": overrides.reverse_check_near_bonus,
        "reverse_check_near_rank_max": overrides.reverse_check_near_rank_max,
        "reverse_check_far_hit_penalty": overrides.reverse_check_far_hit_penalty,
        "reverse_check_miss_penalty": overrides.reverse_check_miss_penalty,
        "reverse_check_exact_hit_ambiguity_threshold": (
            overrides.reverse_check_exact_hit_ambiguity_threshold
        ),
        "reverse_check_exact_hit_ambiguity_penalty": (
            overrides.reverse_check_exact_hit_ambiguity_penalty
        ),
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


def _normalize_semantic_demotion_scale(value: object) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 1.0
        try:
            return max(0.0, float(text))
        except ValueError:
            return 1.0
    return 1.0


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


def _resolve_reverse_check_scoring(
    defaults: ReverseCheckScoringConfig,
    *,
    overrides: RulegenTuningOverrides,
) -> ReverseCheckScoringConfig:
    resolved = defaults
    if overrides.reverse_check_enabled is not None:
        resolved = replace(resolved, enabled=bool(overrides.reverse_check_enabled))
    if overrides.reverse_check_match_bonus is not None:
        resolved = replace(
            resolved, match_bonus=max(0.0, float(overrides.reverse_check_match_bonus))
        )
    if overrides.reverse_check_near_bonus is not None:
        resolved = replace(resolved, near_bonus=max(0.0, float(overrides.reverse_check_near_bonus)))
    if overrides.reverse_check_near_rank_max is not None:
        resolved = replace(
            resolved,
            near_rank_max=max(0, int(overrides.reverse_check_near_rank_max)),
        )
    if overrides.reverse_check_far_hit_penalty is not None:
        resolved = replace(
            resolved,
            far_hit_penalty=max(0.0, float(overrides.reverse_check_far_hit_penalty)),
        )
    if overrides.reverse_check_miss_penalty is not None:
        resolved = replace(
            resolved,
            miss_penalty=max(0.0, float(overrides.reverse_check_miss_penalty)),
        )
    if overrides.reverse_check_exact_hit_ambiguity_threshold is not None:
        resolved = replace(
            resolved,
            exact_hit_ambiguity_threshold=max(
                0,
                int(overrides.reverse_check_exact_hit_ambiguity_threshold),
            ),
        )
    if overrides.reverse_check_exact_hit_ambiguity_penalty is not None:
        resolved = replace(
            resolved,
            exact_hit_ambiguity_penalty=max(
                0.0,
                float(overrides.reverse_check_exact_hit_ambiguity_penalty),
            ),
        )
    return resolved


def _reverse_check_to_dict(reverse_check: ReverseCheckScoringConfig) -> dict[str, object]:
    return {
        "enabled": bool(reverse_check.enabled),
        "match_bonus": float(reverse_check.match_bonus),
        "near_bonus": float(reverse_check.near_bonus),
        "near_rank_max": int(reverse_check.near_rank_max),
        "far_hit_penalty": float(reverse_check.far_hit_penalty),
        "miss_penalty": float(reverse_check.miss_penalty),
        "exact_hit_ambiguity_threshold": int(reverse_check.exact_hit_ambiguity_threshold),
        "exact_hit_ambiguity_penalty": float(reverse_check.exact_hit_ambiguity_penalty),
    }


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
