from __future__ import annotations

from typing import Mapping, Sequence

from semantic_routing_generalization_bound_splits import find_row, select_best_source_only_row


def build_confidence_corridor(
    *,
    veto_proxy_rows: Sequence[Mapping[str, object]],
    veto_proxy_surfaces: Sequence[Mapping[str, object]],
    fixed_shadow_surfaces: Sequence[Mapping[str, object]],
    reference_surface: Mapping[str, object] | None,
    active_only_reference_surface: Mapping[str, object] | None,
    ladder_surface: Mapping[str, object] | None,
    rescue_overlay_surface: Mapping[str, object] | None,
    active_only_rescue_overlay_surface: Mapping[str, object] | None,
) -> dict[str, object]:
    source_only_row = select_best_source_only_row(veto_proxy_rows)
    reviewed_auto_row = find_row(veto_proxy_rows, "reviewed_auto_shadows")
    curated_row = find_row(veto_proxy_rows, "curated_shadows")
    fixed_shadow_control_surface = fixed_shadow_surfaces[0] if fixed_shadow_surfaces else {}

    source_only_surface = None
    source_only_source_id = ""
    if isinstance(source_only_row, Mapping):
        source_only_source_id = str(source_only_row.get("source_id") or "").strip()
        source_only_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip() == source_only_source_id
            ),
            None,
        )

    confidence_corridor = {
        "source_only_source_id": source_only_source_id,
        "source_only_abstain_recall_conservative_floor": (
            _metric_view(source_only_surface or {}, "abstain_recall").get("conservative_floor")
            if isinstance(source_only_surface, Mapping)
            else None
        ),
        "source_only_harmful_allow_conservative_ceiling": (
            _metric_view(source_only_surface or {}, "harmful_allow_rate").get(
                "conservative_ceiling"
            )
            if isinstance(source_only_surface, Mapping)
            else None
        ),
        "fixed_shadow_replace_recall_conservative_floor": _metric_view(
            fixed_shadow_control_surface, "replace_recall"
        ).get("conservative_floor"),
        "fixed_shadow_harmful_replace_conservative_ceiling": _metric_view(
            fixed_shadow_control_surface, "harmful_replace_rate"
        ).get("conservative_ceiling"),
        "fixed_shadow_reference_label": (
            str(reference_surface.get("label") or "")
            if isinstance(reference_surface, Mapping)
            else ""
        ),
        "fixed_shadow_reference_replace_recall_conservative_floor": (
            _metric_view(reference_surface or {}, "replace_recall").get("conservative_floor")
            if isinstance(reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_reference_harmful_replace_conservative_ceiling": (
            _metric_view(reference_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_reference_false_abstain_conservative_ceiling": (
            _metric_view(reference_surface or {}, "false_abstain_rate").get("conservative_ceiling")
            if isinstance(reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_reference_label": (
            str(active_only_reference_surface.get("label") or "")
            if isinstance(active_only_reference_surface, Mapping)
            else ""
        ),
        "fixed_shadow_active_only_reference_replace_recall_conservative_floor": (
            _metric_view(active_only_reference_surface or {}, "replace_recall").get(
                "conservative_floor"
            )
            if isinstance(active_only_reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_reference_harmful_replace_conservative_ceiling": (
            _metric_view(active_only_reference_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_reference_false_abstain_conservative_ceiling": (
            _metric_view(active_only_reference_surface or {}, "false_abstain_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_ladder_label": (
            str(ladder_surface.get("label") or "") if isinstance(ladder_surface, Mapping) else ""
        ),
        "fixed_shadow_ladder_replace_or_soft_recall_conservative_floor": (
            _metric_view(ladder_surface or {}, "replace_or_soft_recall").get("conservative_floor")
            if isinstance(ladder_surface, Mapping)
            else None
        ),
        "fixed_shadow_ladder_soft_noise_conservative_ceiling": (
            _metric_view(ladder_surface or {}, "soft_noise_rate").get("conservative_ceiling")
            if isinstance(ladder_surface, Mapping)
            else None
        ),
        "fixed_shadow_rescue_overlay_label": (
            str(rescue_overlay_surface.get("label") or "")
            if isinstance(rescue_overlay_surface, Mapping)
            else ""
        ),
        "fixed_shadow_rescue_overlay_replace_recall_conservative_floor": (
            _metric_view(rescue_overlay_surface or {}, "replace_recall").get("conservative_floor")
            if isinstance(rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_rescue_overlay_harmful_replace_conservative_ceiling": (
            _metric_view(rescue_overlay_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_rescue_overlay_false_abstain_conservative_ceiling": (
            _metric_view(rescue_overlay_surface or {}, "false_abstain_rate").get(
                "conservative_ceiling"
            )
            if isinstance(rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_rescue_overlay_label": (
            str(active_only_rescue_overlay_surface.get("label") or "")
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else ""
        ),
        "fixed_shadow_active_only_rescue_overlay_replace_recall_conservative_floor": (
            _metric_view(active_only_rescue_overlay_surface or {}, "replace_recall").get(
                "conservative_floor"
            )
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_rescue_overlay_harmful_replace_conservative_ceiling": (
            _metric_view(active_only_rescue_overlay_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_rescue_overlay_false_abstain_conservative_ceiling": (
            _metric_view(active_only_rescue_overlay_surface or {}, "false_abstain_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else None
        ),
        "reviewed_auto_abstain_recall_conservative_floor": None,
        "reviewed_auto_harmful_allow_conservative_ceiling": None,
        "curated_abstain_recall_conservative_floor": None,
        "curated_harmful_allow_conservative_ceiling": None,
    }
    if isinstance(reviewed_auto_row, Mapping):
        reviewed_auto_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip()
                == str(reviewed_auto_row.get("source_id") or "").strip()
            ),
            None,
        )
        if isinstance(reviewed_auto_surface, Mapping):
            confidence_corridor["reviewed_auto_abstain_recall_conservative_floor"] = _metric_view(
                reviewed_auto_surface, "abstain_recall"
            ).get("conservative_floor")
            confidence_corridor["reviewed_auto_harmful_allow_conservative_ceiling"] = _metric_view(
                reviewed_auto_surface, "harmful_allow_rate"
            ).get("conservative_ceiling")
    if isinstance(curated_row, Mapping):
        curated_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip()
                == str(curated_row.get("source_id") or "").strip()
            ),
            None,
        )
        if isinstance(curated_surface, Mapping):
            confidence_corridor["curated_abstain_recall_conservative_floor"] = _metric_view(
                curated_surface, "abstain_recall"
            ).get("conservative_floor")
            confidence_corridor["curated_harmful_allow_conservative_ceiling"] = _metric_view(
                curated_surface, "harmful_allow_rate"
            ).get("conservative_ceiling")

    return confidence_corridor


def _metric_view(surface: Mapping[str, object], metric_name: str) -> Mapping[str, object]:
    metric_views = surface.get("metric_views")
    if isinstance(metric_views, Mapping):
        metric_view = metric_views.get(metric_name)
        if isinstance(metric_view, Mapping):
            return metric_view
    return {}
