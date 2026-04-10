from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_shadow_frequency import (
    build_frequency_similarity_details,
    candidate_has_frequency_representative_bonus,
)

DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS = 0.0
DEFAULT_FREQUENCY_SIMILARITY_WEIGHT = 0.0
DEFAULT_FREQUENCY_SIMILARITY_TAU = 0.15
SHADOW_SUPPORT_SCORE_WEIGHTS = {
    "reviewed_trigger_support": 2.0,
    "benchmark_target_present": 1.0,
    "same_pos_as_active": 1.0,
    "active_side_support": 1.0,
    "semantic_bridge_support": 1.0,
    "cross_pos_mismatch_penalty": -1.0,
}


def build_shadow_candidate_support_details(
    *,
    candidate: Mapping[str, object],
    active_candidates: Sequence[Mapping[str, object]],
    frequency_representative_targets: Sequence[str] = (),
    frequency_representative_bonus: float = DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    frequency_similarity_weight: float = DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
    frequency_similarity_tau: float = DEFAULT_FREQUENCY_SIMILARITY_TAU,
) -> dict[str, object]:
    active_pos_values = {
        str(active_candidate.get("canonical_pos") or "").strip().lower()
        for active_candidate in active_candidates
        if str(active_candidate.get("canonical_pos") or "").strip()
    }
    has_active_candidates = bool(active_candidates)
    has_active_pos = bool(active_pos_values)
    canonical_pos = str(candidate.get("canonical_pos") or "").strip().lower()
    reviewed_trigger_support = bool(candidate.get("reviewed_trigger_support"))
    benchmark_target_present = bool(candidate.get("benchmark_target_present"))
    same_pos = bool(canonical_pos and canonical_pos in active_pos_values)
    cross_pos_mismatch = bool(has_active_pos and canonical_pos and not same_pos)
    semantic_bridge_support = bool(
        candidate.get("semantic_bridge_markers")
        or float(candidate.get("embedding_bridge_similarity") or 0.0) > 0.0
    )
    frequency_representative = candidate_has_frequency_representative_bonus(
        candidate=candidate,
        representative_targets=frequency_representative_targets,
    )
    frequency_similarity_details = build_frequency_similarity_details(
        candidate=candidate,
        active_candidates=active_candidates,
        tau=float(frequency_similarity_tau),
    )
    frequency_similarity_present = bool(
        frequency_similarity_details.get("frequency_similarity_present")
    )
    frequency_similarity_score = float(
        frequency_similarity_details.get("frequency_similarity_score") or 0.0
    )

    support_breakdown = {
        "reviewed_trigger_support": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["reviewed_trigger_support"]
            if reviewed_trigger_support
            else 0.0
        ),
        "benchmark_target_present": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["benchmark_target_present"]
            if benchmark_target_present
            else 0.0
        ),
        "same_pos_as_active": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["same_pos_as_active"] if same_pos else 0.0
        ),
        "active_side_support": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["active_side_support"] if has_active_candidates else 0.0
        ),
        "semantic_bridge_support": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["semantic_bridge_support"]
            if semantic_bridge_support
            else 0.0
        ),
        "frequency_representative_bonus": (
            float(frequency_representative_bonus) if frequency_representative else 0.0
        ),
        "frequency_similarity_bonus": (
            float(frequency_similarity_weight) * frequency_similarity_score
            if frequency_similarity_present and float(frequency_similarity_weight) > 0.0
            else 0.0
        ),
        "cross_pos_mismatch_penalty": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["cross_pos_mismatch_penalty"]
            if cross_pos_mismatch
            else 0.0
        ),
    }
    positive_features = [
        feature
        for feature, value in (
            ("reviewed_trigger_support", reviewed_trigger_support),
            ("benchmark_target_present", benchmark_target_present),
            ("same_pos_as_active", same_pos),
            ("active_side_support", has_active_candidates),
            ("semantic_bridge_support", semantic_bridge_support),
            ("frequency_representative_bonus", frequency_representative),
            ("frequency_similarity_bonus", frequency_similarity_present),
        )
        if value
    ]
    penalties = ["cross_pos_mismatch_penalty"] if cross_pos_mismatch else []
    return {
        "same_pos_as_active": same_pos,
        "support_features": positive_features,
        "support_penalties": penalties,
        "support_score_breakdown": support_breakdown,
        "support_score": sum(float(value) for value in support_breakdown.values()),
        "promotion_reasons": positive_features,
        **frequency_similarity_details,
    }
