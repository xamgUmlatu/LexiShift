from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_heuristic_difficulty_surface_analysis import _case_type_expansion_recommendations
from semantic_veto_heuristic_difficulty_surface_common import (
    DEFAULT_EXPANSION_SCORER,
    PRIMARY_SELECTION_MODE,
)


def _expansion_plan(
    *,
    rows: Sequence[Mapping[str, object]],
    authored_by_trigger: Mapping[str, Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    scorer_ids = {str(row.get("scorer_id") or "") for row in rows}
    scorer_id = (
        DEFAULT_EXPANSION_SCORER
        if DEFAULT_EXPANSION_SCORER in scorer_ids
        else sorted(scorer_ids)[0]
    )
    scorer_rows = [row for row in rows if row.get("scorer_id") == scorer_id]
    recommendations = []
    recommendations.extend(
        _case_type_expansion_recommendations(
            rows=scorer_rows,
            weights=weights,
            acceptance=acceptance,
        )
    )
    for trigger, authored in sorted(authored_by_trigger.items()):
        if str(authored.get("selection_mode") or "") != PRIMARY_SELECTION_MODE:
            recommendations.append(
                {
                    "cell_id": f"sentinel_metadata:{trigger}",
                    "priority": "P2",
                    "reason": "outcome_informed_sentinel_excluded_from_primary_validation",
                    "recommended_action": "improve_frequency_metadata_or_keep_as_regression_anchor",
                    "manual_discovery_rows": 0,
                    "llm_discovery_rows": 0,
                    "locked_eval_rows": 0,
                    "notes": "Do not use this trigger to prove the frequency/polysemy heuristic.",
                }
            )
        if (
            str(authored.get("group_id") or "") == "core_low_polysemy_control"
            and str(authored.get("shadow_contract") or "") == "not_applicable"
        ):
            recommendations.append(
                {
                    "cell_id": f"core_low_polysemy_phrase:{trigger}",
                    "priority": "P1",
                    "reason": "high_frequency_low_polysemy_control_needs_phrase_and_mention_negatives",
                    "recommended_action": "add_phrase_no_winner_rows_not_fake_shadow_rows",
                    "manual_discovery_rows": 4,
                    "llm_discovery_rows": 12,
                    "locked_eval_rows": 6,
                    "notes": "Keep shadow_negative at zero unless a real alternate sense is found.",
                }
            )
    deduped = _dedupe_recommendations(recommendations)
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    deduped.sort(
        key=lambda row: (
            priority_order.get(str(row.get("priority") or ""), 99),
            str(row.get("cell_id") or ""),
        )
    )
    return {
        "basis_scorer_id": scorer_id,
        "recommendation_count": len(deduped),
        "recommendations": deduped,
    }


def _dedupe_recommendations(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    deduped: dict[str, dict[str, object]] = {}
    for row in rows:
        cell_id = str(row.get("cell_id") or "")
        existing = deduped.get(cell_id)
        if existing is None:
            deduped[cell_id] = dict(row)
            continue
        if _priority_rank(row) < _priority_rank(existing):
            deduped[cell_id] = dict(row)
    return list(deduped.values())


def _priority_rank(row: Mapping[str, object]) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(str(row.get("priority") or ""), 99)
