from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_shadow_support import normalize_shadow_string_list

_FORWARD_SOURCE_FAMILIES = frozenset({"forward_index", "forward_index_active_profile_fallback"})


def build_semantic_shadow_case_feature_vector(
    *,
    inventory_entry_present: bool,
    active_candidates: Sequence[object],
    active_profile_fallback: Mapping[str, object] | None,
    shadow_candidates: Sequence[object],
    promoted_targets: Sequence[str],
) -> dict[str, object]:
    active_candidate_rows = _coerce_mapping_sequence(active_candidates)
    shadow_candidate_rows = _coerce_mapping_sequence(shadow_candidates)
    active_profile = (
        dict(active_profile_fallback) if isinstance(active_profile_fallback, Mapping) else {}
    )

    active_pos_values = _collect_canonical_pos_values(active_candidate_rows)
    active_profile_pos = _normalize_canonical_pos(active_profile.get("canonical_pos"))
    if not active_pos_values and active_profile_pos:
        active_pos_values.append(active_profile_pos)

    active_support_mode = "none"
    if active_candidate_rows:
        active_support_mode = "active_candidates"
    elif active_profile_pos:
        active_support_mode = "profile_only"

    source_family_histogram: dict[str, int] = {}
    candidate_pos_histogram: dict[str, int] = {}
    reviewed_trigger_support_count = 0
    benchmark_target_present_count = 0
    same_pos_candidate_count = 0
    multi_source_candidate_count = 0
    semantic_bridge_candidate_count = 0
    trigger_family_candidate_count = 0
    forward_neighborhood_candidate_count = 0

    for candidate in shadow_candidate_rows:
        candidate_source_families = _collect_candidate_source_families(candidate)
        for family in candidate_source_families:
            source_family_histogram[family] = source_family_histogram.get(family, 0) + 1
        if len(candidate_source_families) >= 2:
            multi_source_candidate_count += 1

        canonical_pos = _normalize_canonical_pos(candidate.get("canonical_pos"))
        if canonical_pos:
            candidate_pos_histogram[canonical_pos] = (
                candidate_pos_histogram.get(canonical_pos, 0) + 1
            )
            if canonical_pos in active_pos_values:
                same_pos_candidate_count += 1

        if bool(candidate.get("reviewed_trigger_support")):
            reviewed_trigger_support_count += 1
        if bool(candidate.get("benchmark_target_present")):
            benchmark_target_present_count += 1
        if _candidate_has_semantic_bridge_support(candidate):
            semantic_bridge_candidate_count += 1
        if normalize_shadow_string_list(candidate.get("target_trigger_family_terms")):
            trigger_family_candidate_count += 1
        if normalize_shadow_string_list(candidate.get("forward_neighborhood_terms")):
            forward_neighborhood_candidate_count += 1

    candidate_source_families = sorted(source_family_histogram.keys())
    candidate_pos_values = sorted(candidate_pos_histogram.keys())
    promoted_target_count = len([value for value in promoted_targets if str(value or "").strip()])

    return {
        "inventory_entry_present": bool(inventory_entry_present),
        "active_profile_fallback_present": bool(active_profile_pos),
        "active_support_mode": active_support_mode,
        "active_candidate_count": len(active_candidate_rows),
        "active_pos_values": active_pos_values,
        "active_pos_count": len(active_pos_values),
        "shadow_candidate_count": len(shadow_candidate_rows),
        "promoted_target_count": promoted_target_count,
        "candidate_source_families": candidate_source_families,
        "candidate_source_family_count": len(candidate_source_families),
        "candidate_source_family_histogram": source_family_histogram,
        "candidate_pos_values": candidate_pos_values,
        "candidate_pos_count": len(candidate_pos_values),
        "candidate_pos_histogram": candidate_pos_histogram,
        "reviewed_trigger_support_candidate_count": reviewed_trigger_support_count,
        "benchmark_target_present_candidate_count": benchmark_target_present_count,
        "same_pos_candidate_count": same_pos_candidate_count,
        "multi_source_candidate_count": multi_source_candidate_count,
        "semantic_bridge_candidate_count": semantic_bridge_candidate_count,
        "trigger_family_candidate_count": trigger_family_candidate_count,
        "forward_neighborhood_candidate_count": forward_neighborhood_candidate_count,
    }


def build_semantic_shadow_feature_dimensions(
    feature_vector: Mapping[str, object],
) -> dict[str, list[str]]:
    candidate_source_families = normalize_shadow_string_list(
        feature_vector.get("candidate_source_families")
    )
    feature_dimensions = {
        "feature_inventory_entry": [
            "present" if bool(feature_vector.get("inventory_entry_present")) else "missing"
        ],
        "feature_active_support_mode": [
            str(feature_vector.get("active_support_mode") or "none").strip() or "none"
        ],
        "feature_active_candidate_count": [
            _bucket_count(int(feature_vector.get("active_candidate_count") or 0))
        ],
        "feature_shadow_candidate_count": [
            _bucket_count(int(feature_vector.get("shadow_candidate_count") or 0))
        ],
        "feature_promoted_target_count": [
            _bucket_count(int(feature_vector.get("promoted_target_count") or 0))
        ],
        "feature_candidate_source_family_count": [
            _bucket_count(int(feature_vector.get("candidate_source_family_count") or 0))
        ],
        "feature_candidate_source_family_signature": [
            "+".join(candidate_source_families) if candidate_source_families else "none"
        ],
        "feature_candidate_pos_count": [
            _bucket_count(int(feature_vector.get("candidate_pos_count") or 0))
        ],
        "feature_reviewed_trigger_support_count": [
            _bucket_count(int(feature_vector.get("reviewed_trigger_support_candidate_count") or 0))
        ],
        "feature_benchmark_target_present_count": [
            _bucket_count(int(feature_vector.get("benchmark_target_present_candidate_count") or 0))
        ],
        "feature_same_pos_candidate_count": [
            _bucket_count(int(feature_vector.get("same_pos_candidate_count") or 0))
        ],
        "feature_multi_source_candidate_count": [
            _bucket_count(int(feature_vector.get("multi_source_candidate_count") or 0))
        ],
        "feature_semantic_bridge_candidate_count": [
            _bucket_count(int(feature_vector.get("semantic_bridge_candidate_count") or 0))
        ],
        "feature_trigger_family_candidate_count": [
            _bucket_count(int(feature_vector.get("trigger_family_candidate_count") or 0))
        ],
        "feature_forward_neighborhood_candidate_count": [
            _bucket_count(int(feature_vector.get("forward_neighborhood_candidate_count") or 0))
        ],
    }
    return {
        name: values
        for name, values in feature_dimensions.items()
        if normalize_shadow_string_list(values)
    }


def _coerce_mapping_sequence(values: Sequence[object]) -> list[Mapping[str, object]]:
    return [value for value in values if isinstance(value, Mapping)]


def _normalize_canonical_pos(value: object) -> str:
    return str(value or "").strip().lower()


def _collect_canonical_pos_values(candidates: Sequence[Mapping[str, object]]) -> list[str]:
    seen: list[str] = []
    for candidate in candidates:
        canonical_pos = _normalize_canonical_pos(candidate.get("canonical_pos"))
        if canonical_pos and canonical_pos not in seen:
            seen.append(canonical_pos)
    return seen


def _collect_candidate_source_families(candidate: Mapping[str, object]) -> list[str]:
    seen: list[str] = []
    for source in normalize_shadow_string_list(candidate.get("candidate_sources")):
        normalized = "forward_index" if source in _FORWARD_SOURCE_FAMILIES else source
        if normalized and normalized not in seen:
            seen.append(normalized)
    return seen


def _candidate_has_semantic_bridge_support(candidate: Mapping[str, object]) -> bool:
    return bool(
        normalize_shadow_string_list(candidate.get("semantic_bridge_markers"))
        or float(candidate.get("semantic_bridge_score") or 0.0) > 0.0
        or float(candidate.get("embedding_bridge_similarity") or 0.0) > 0.0
    )


def _bucket_count(value: int) -> str:
    normalized = max(0, int(value))
    if normalized == 0:
        return "none"
    if normalized == 1:
        return "one"
    if normalized <= 3:
        return "two_to_three"
    return "four_plus"
