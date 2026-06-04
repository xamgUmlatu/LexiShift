from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_shadow_neighborhood import (
    build_forward_neighborhood_overlap_details,
    build_trigger_family_reentry_details,
)
from lexishift_core.rulegen.semantic_shadow_frequency import (
    build_frequency_similarity_details,
    candidate_has_frequency_representative_bonus,
)

DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS = 0.0
DEFAULT_FREQUENCY_SIMILARITY_WEIGHT = 0.0
DEFAULT_FREQUENCY_SIMILARITY_TAU = 0.15
SHADOW_SUPPORT_SCORE_WEIGHTS = {
    "reviewed_trigger_support": 2.0,
    "forward_trigger_support": 0.5,
    "benchmark_target_present": 1.0,
    "same_pos_as_active": 1.0,
    "active_side_support": 1.0,
    "active_profile_support": 1.0,
    "multi_source_candidate_support": 0.0,
    "triplet_core_bonus": 0.0,
    "triplet_forward_bonus": 0.0,
    "triplet_bridge_guard_bonus": 0.0,
    "trigger_family_reentry": 0.0,
    "forward_neighborhood_overlap": 0.0,
    "semantic_bridge_support": 1.0,
    "cross_pos_mismatch_penalty": -1.0,
}
_FORWARD_SOURCE_FAMILIES = frozenset({"forward_index", "forward_index_active_profile_fallback"})


def resolve_shadow_support_score_weights(
    overrides: Mapping[str, object] | None = None,
) -> dict[str, float]:
    resolved = {key: float(value) for key, value in SHADOW_SUPPORT_SCORE_WEIGHTS.items()}
    if overrides is None:
        return resolved
    unknown_keys = sorted(
        str(key or "").strip()
        for key in overrides.keys()
        if str(key or "").strip() and str(key or "").strip() not in resolved
    )
    if unknown_keys:
        raise ValueError(
            "Unsupported shadow support score weight override(s): "
            f"{unknown_keys!r}; expected keys drawn from "
            f"{sorted(resolved.keys())!r}"
        )
    for key, value in overrides.items():
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        resolved[normalized_key] = _safe_float(value)
    return resolved


def merge_shadow_candidate_evidence(
    existing_candidate: dict[str, object],
    incoming_candidate: Mapping[str, object],
) -> None:
    for field in (
        "benchmark_target_present",
        "reviewed_trigger_support",
        "forward_trigger_support",
    ):
        if bool(incoming_candidate.get(field)):
            existing_candidate[field] = True

    existing_sources = normalize_shadow_string_list(existing_candidate.get("candidate_sources"))
    for source in normalize_shadow_string_list(incoming_candidate.get("candidate_sources")):
        if source not in existing_sources:
            existing_sources.append(source)
    if existing_sources:
        existing_candidate["candidate_sources"] = existing_sources

    existing_case_ids = normalize_shadow_string_list(existing_candidate.get("benchmark_case_ids"))
    for case_id in normalize_shadow_string_list(incoming_candidate.get("benchmark_case_ids")):
        if case_id not in existing_case_ids:
            existing_case_ids.append(case_id)
    if existing_case_ids:
        existing_candidate["benchmark_case_ids"] = existing_case_ids

    existing_markers = normalize_shadow_string_list(
        existing_candidate.get("semantic_bridge_markers")
    )
    for marker in normalize_shadow_string_list(incoming_candidate.get("semantic_bridge_markers")):
        if marker not in existing_markers:
            existing_markers.append(marker)
    if existing_markers:
        existing_candidate["semantic_bridge_markers"] = existing_markers

    for field in ("forward_neighborhood_terms", "target_trigger_family_terms"):
        existing_values = normalize_shadow_string_list(existing_candidate.get(field))
        for value in normalize_shadow_string_list(incoming_candidate.get(field)):
            if value not in existing_values:
                existing_values.append(value)
        if existing_values:
            existing_candidate[field] = existing_values

    existing_bridge_score = _safe_float(existing_candidate.get("semantic_bridge_score"))
    incoming_bridge_score = _safe_float(incoming_candidate.get("semantic_bridge_score"))
    if incoming_bridge_score > existing_bridge_score:
        existing_candidate["semantic_bridge_score"] = incoming_bridge_score

    existing_embedding_similarity = _safe_float(
        existing_candidate.get("embedding_bridge_similarity")
    )
    incoming_embedding_similarity = _safe_float(
        incoming_candidate.get("embedding_bridge_similarity")
    )
    if incoming_embedding_similarity > existing_embedding_similarity:
        existing_candidate["embedding_bridge_similarity"] = incoming_embedding_similarity

    if (
        not str(existing_candidate.get("canonical_pos") or "").strip()
        and str(incoming_candidate.get("canonical_pos") or "").strip()
    ):
        existing_candidate["canonical_pos"] = str(
            incoming_candidate.get("canonical_pos") or ""
        ).strip()


def normalize_shadow_string_list(*values: object) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                text = str(item).strip()
                if text and text not in normalized:
                    normalized.append(text)
        else:
            text = str(value or "").strip()
            if text and text not in normalized:
                normalized.append(text)
    return normalized


def parse_shadow_optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _safe_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (float, int)):
        return float(value)
    try:
        return float(str(value or "").strip() or "0")
    except (TypeError, ValueError):
        return 0.0


def build_shadow_candidate_support_details(
    *,
    candidate: Mapping[str, object],
    active_candidates: Sequence[Mapping[str, object]],
    active_trigger: str = "",
    active_profile_pos: str = "",
    active_profile_support: bool = False,
    active_profile_trigger_family_terms: Sequence[str] = (),
    active_profile_forward_neighborhood_terms: Sequence[str] = (),
    frequency_representative_targets: Sequence[str] = (),
    frequency_representative_bonus: float = DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    frequency_similarity_weight: float = DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
    frequency_similarity_tau: float = DEFAULT_FREQUENCY_SIMILARITY_TAU,
    score_weights: Mapping[str, object] | None = None,
) -> dict[str, object]:
    resolved_weights = resolve_shadow_support_score_weights(score_weights)
    active_pos_values = {
        str(active_candidate.get("canonical_pos") or "").strip().lower()
        for active_candidate in active_candidates
        if str(active_candidate.get("canonical_pos") or "").strip()
    }
    has_active_candidates = bool(active_candidates)
    normalized_active_profile_pos = str(active_profile_pos or "").strip().lower()
    has_active_profile_support = bool(
        active_profile_support and not has_active_candidates and normalized_active_profile_pos
    )
    if not active_pos_values and normalized_active_profile_pos:
        active_pos_values.add(normalized_active_profile_pos)
    has_active_pos = bool(active_pos_values)
    canonical_pos = str(candidate.get("canonical_pos") or "").strip().lower()
    reviewed_trigger_support = bool(candidate.get("reviewed_trigger_support"))
    forward_trigger_support = bool(candidate.get("forward_trigger_support"))
    benchmark_target_present = bool(candidate.get("benchmark_target_present"))
    same_pos = bool(canonical_pos and canonical_pos in active_pos_values)
    cross_pos_mismatch = bool(has_active_pos and canonical_pos and not same_pos)
    candidate_sources = set(normalize_shadow_string_list(candidate.get("candidate_sources")))
    candidate_source_families = {
        "forward_index" if source in _FORWARD_SOURCE_FAMILIES else source
        for source in candidate_sources
    }
    multi_source_candidate_support = {
        "reverse_lookup",
        "forward_index",
    }.issubset(candidate_source_families)
    semantic_bridge_support = bool(
        candidate.get("semantic_bridge_markers")
        or _safe_float(candidate.get("embedding_bridge_similarity")) > 0.0
    )
    triplet_core_bonus = bool(benchmark_target_present and same_pos and has_active_candidates)
    triplet_forward_bonus = bool(triplet_core_bonus and forward_trigger_support)
    triplet_bridge_guard_bonus = bool(triplet_core_bonus and semantic_bridge_support)
    forward_neighborhood_overlap = build_forward_neighborhood_overlap_details(
        candidate=candidate,
        active_candidates=active_candidates,
        active_profile_forward_neighborhood_terms=active_profile_forward_neighborhood_terms,
    )
    trigger_family_reentry = build_trigger_family_reentry_details(
        candidate=candidate,
        active_candidates=active_candidates,
        active_trigger=active_trigger,
        active_profile_forward_neighborhood_terms=active_profile_forward_neighborhood_terms,
        active_profile_trigger_family_terms=active_profile_trigger_family_terms,
    )
    trigger_family_reentry_present = bool(
        trigger_family_reentry.get("trigger_family_reentry_present")
    )
    trigger_family_reentry_score = _safe_float(
        trigger_family_reentry.get("trigger_family_reentry_score")
    )
    forward_neighborhood_overlap_present = bool(
        forward_neighborhood_overlap.get("forward_neighborhood_overlap_present")
    )
    forward_neighborhood_overlap_score = _safe_float(
        forward_neighborhood_overlap.get("forward_neighborhood_overlap_score")
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
    frequency_similarity_score = _safe_float(
        frequency_similarity_details.get("frequency_similarity_score")
    )

    support_breakdown = {
        "reviewed_trigger_support": (
            resolved_weights["reviewed_trigger_support"] if reviewed_trigger_support else 0.0
        ),
        "forward_trigger_support": (
            resolved_weights["forward_trigger_support"] if forward_trigger_support else 0.0
        ),
        "benchmark_target_present": (
            resolved_weights["benchmark_target_present"] if benchmark_target_present else 0.0
        ),
        "same_pos_as_active": (resolved_weights["same_pos_as_active"] if same_pos else 0.0),
        "active_side_support": (
            resolved_weights["active_side_support"] if has_active_candidates else 0.0
        ),
        "active_profile_support": (
            resolved_weights["active_profile_support"] if has_active_profile_support else 0.0
        ),
        "multi_source_candidate_support": (
            resolved_weights["multi_source_candidate_support"]
            if multi_source_candidate_support
            else 0.0
        ),
        "triplet_core_bonus": (
            resolved_weights["triplet_core_bonus"] if triplet_core_bonus else 0.0
        ),
        "triplet_forward_bonus": (
            resolved_weights["triplet_forward_bonus"] if triplet_forward_bonus else 0.0
        ),
        "triplet_bridge_guard_bonus": (
            resolved_weights["triplet_bridge_guard_bonus"] if triplet_bridge_guard_bonus else 0.0
        ),
        "trigger_family_reentry": (
            resolved_weights["trigger_family_reentry"] * trigger_family_reentry_score
            if trigger_family_reentry_present
            else 0.0
        ),
        "forward_neighborhood_overlap": (
            resolved_weights["forward_neighborhood_overlap"] * forward_neighborhood_overlap_score
            if forward_neighborhood_overlap_present
            else 0.0
        ),
        "semantic_bridge_support": (
            resolved_weights["semantic_bridge_support"] if semantic_bridge_support else 0.0
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
            resolved_weights["cross_pos_mismatch_penalty"] if cross_pos_mismatch else 0.0
        ),
    }
    positive_features = [
        feature
        for feature, value in (
            ("reviewed_trigger_support", reviewed_trigger_support),
            ("forward_trigger_support", forward_trigger_support),
            ("benchmark_target_present", benchmark_target_present),
            ("same_pos_as_active", same_pos),
            ("active_side_support", has_active_candidates),
            ("active_profile_support", has_active_profile_support),
            ("multi_source_candidate_support", multi_source_candidate_support),
            (
                "triplet_core_bonus",
                triplet_core_bonus and float(resolved_weights["triplet_core_bonus"]) > 0.0,
            ),
            (
                "triplet_forward_bonus",
                triplet_forward_bonus and float(resolved_weights["triplet_forward_bonus"]) > 0.0,
            ),
            (
                "triplet_bridge_guard_bonus",
                triplet_bridge_guard_bonus
                and float(resolved_weights["triplet_bridge_guard_bonus"]) > 0.0,
            ),
            ("trigger_family_reentry", trigger_family_reentry_present),
            ("forward_neighborhood_overlap", forward_neighborhood_overlap_present),
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
        **trigger_family_reentry,
        **forward_neighborhood_overlap,
        **frequency_similarity_details,
    }
