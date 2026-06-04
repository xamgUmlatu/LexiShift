from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _safe_float
from semantic_veto_formula_shape_bakeoff_common import (
    PRIMARY_SELECTION_MODE,
    _brier,
    _kendall_tau,
    _pairs_for,
    _primary_score_rows,
    _priority_public_row,
    _public_top_cells,
    _round4,
    _rotate,
    _rows_for_priority,
    _spearman,
    _top_k,
    _top_k_lift,
)


def _comparison_rows(
    *,
    cells: Sequence[Mapping[str, object]],
    score_rows: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    by_cell = {str(cell.get("cell_id") or ""): cell for cell in cells}
    scope_rows: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in score_rows:
        if row.get("formula_kind") != "candidate":
            continue
        scope_rows[(str(row.get("formula_id") or ""), "primary_all_scorers")].append(row)
        scope_rows[
            (str(row.get("formula_id") or ""), f"primary::{row.get('scorer_id') or ''}")
        ].append(row)
        scope_rows[
            (
                str(row.get("formula_id") or ""),
                f"all_including_sentinel::{row.get('scorer_id') or ''}",
            )
        ].append(row)
    result = []
    for (formula_id, scope_id), rows in sorted(scope_rows.items()):
        if scope_id.startswith("primary"):
            rows = _primary_score_rows(rows)
        if not rows:
            continue
        comparison = _comparison_metrics(
            formula_id=formula_id,
            scope_id=scope_id,
            rows=rows,
            by_cell=by_cell,
            top_k=top_k,
            shuffled=False,
        )
        shuffled = _comparison_metrics(
            formula_id=formula_id,
            scope_id=scope_id,
            rows=rows,
            by_cell=by_cell,
            top_k=top_k,
            shuffled=True,
        )
        comparison["shuffled_observed_spearman"] = shuffled.get("spearman_rank_correlation")
        comparison["shuffled_observed_brier_score"] = shuffled.get("brier_score")
        result.append(comparison)
    result.sort(
        key=lambda row: (
            0 if str(row.get("scope_id") or "") == "primary_all_scorers" else 1,
            str(row.get("scope_id") or ""),
            -_safe_float(row.get("spearman_rank_correlation")),
            _safe_float(row.get("brier_score")),
            str(row.get("formula_id") or ""),
        )
    )
    return result


def _comparison_metrics(
    *,
    formula_id: str,
    scope_id: str,
    rows: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    top_k: int,
    shuffled: bool,
) -> dict[str, object]:
    observed = [_safe_float(row.get("posterior_failure_rate")) for row in rows]
    predicted = [_safe_float(row.get("predicted_failure_risk")) for row in rows]
    if shuffled:
        observed = _rotate(observed)
    pairs = list(zip(predicted, observed))
    ranked_by_predicted = sorted(
        rows,
        key=lambda row: (
            -_safe_float(row.get("predicted_failure_risk")),
            str(row.get("cell_id") or ""),
        ),
    )
    ranked_by_priority = sorted(
        rows,
        key=lambda row: (
            -_safe_float(row.get("normalized_data_help_priority")),
            str(row.get("cell_id") or ""),
        ),
    )
    discovery = [row for row in rows if row.get("cell_split") == "discovery"]
    locked = [row for row in rows if row.get("cell_split") == "internal_locked_eval"]
    return {
        "formula_id": formula_id,
        "scope_id": scope_id,
        "cell_count": len(rows),
        "discovery_cell_count": len(discovery),
        "internal_locked_eval_cell_count": len(locked),
        "spearman_rank_correlation": _round4(_spearman(pairs)),
        "kendall_tau": _round4(_kendall_tau(pairs)),
        "brier_score": _round4(_brier(predicted=predicted, observed=observed)),
        "top_k": min(top_k, len(rows)),
        "top_k_lift": _round4(_top_k_lift(ranked_by_predicted, rows, top_k=top_k)),
        "priority_top_k_lift": _round4(_top_k_lift(ranked_by_priority, rows, top_k=top_k)),
        "discovery_spearman": _round4(_spearman(_pairs_for(discovery))),
        "internal_locked_eval_spearman": _round4(_spearman(_pairs_for(locked))),
        "top_predicted_cells": _public_top_cells(ranked_by_predicted[:top_k], by_cell=by_cell),
        "top_priority_cells": _public_top_cells(ranked_by_priority[:top_k], by_cell=by_cell),
    }


def _calibration_rows(*, score_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    result = []
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in score_rows:
        if row.get("formula_kind") != "candidate":
            continue
        grouped[(str(row.get("formula_id") or ""), str(row.get("scorer_id") or ""))].append(row)
    for (formula_id, scorer_id), rows in sorted(grouped.items()):
        for bucket_id, lower, upper in (
            ("low", 0.0, 0.33),
            ("mid", 0.33, 0.66),
            ("high", 0.66, 1.01),
        ):
            bucket_rows = [
                row
                for row in rows
                if lower <= _safe_float(row.get("predicted_failure_risk")) < upper
                and row.get("selection_mode") == PRIMARY_SELECTION_MODE
            ]
            if not bucket_rows:
                continue
            predicted_mean = sum(
                _safe_float(row.get("predicted_failure_risk")) for row in bucket_rows
            ) / len(bucket_rows)
            observed_mean = sum(
                _safe_float(row.get("posterior_failure_rate")) for row in bucket_rows
            ) / len(bucket_rows)
            result.append(
                {
                    "formula_id": formula_id,
                    "scorer_id": scorer_id,
                    "bucket_id": bucket_id,
                    "cell_count": len(bucket_rows),
                    "predicted_mean": _round4(predicted_mean),
                    "observed_mean": _round4(observed_mean),
                    "absolute_error": _round4(abs(predicted_mean - observed_mean)),
                }
            )
    return result


def _negative_control_rows(
    *,
    cells: Sequence[Mapping[str, object]],
    score_rows: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    by_cell = {str(cell.get("cell_id") or ""): cell for cell in cells}
    control_rows = [
        row for row in score_rows if str(row.get("formula_kind") or "") == "negative_control"
    ]
    result = []
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in control_rows:
        grouped[str(row.get("formula_id") or "")].append(row)
    for control_id, rows in sorted(grouped.items()):
        primary = _primary_score_rows(rows)
        result.append(
            _comparison_metrics(
                formula_id=control_id,
                scope_id="negative_control_primary_all_scorers",
                rows=primary,
                by_cell=by_cell,
                top_k=top_k,
                shuffled=False,
            )
        )
    candidate_primary = [
        row
        for row in score_rows
        if row.get("formula_kind") == "candidate"
        and row.get("formula_id") == "linear_baseline"
        and row.get("selection_mode") == PRIMARY_SELECTION_MODE
    ]
    if candidate_primary:
        shuffled = _comparison_metrics(
            formula_id="shuffled_observed_order",
            scope_id="negative_control_primary_all_scorers",
            rows=candidate_primary,
            by_cell=by_cell,
            top_k=top_k,
            shuffled=True,
        )
        result.append(shuffled)
    return result


def _top_priority_cells(
    *,
    score_rows: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    top_k = _top_k(manifest)
    rows = [
        row
        for row in score_rows
        if row.get("formula_kind") == "candidate"
        and row.get("selection_mode") == PRIMARY_SELECTION_MODE
    ]
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("cell_id") or "")].append(row)
    result = []
    for cell_rows in grouped.values():
        ranked = sorted(
            cell_rows,
            key=lambda item: (
                -_safe_float(item.get("normalized_data_help_priority")),
                -_safe_float(item.get("predicted_failure_risk")),
                str(item.get("formula_id") or ""),
            ),
        )
        public = _priority_public_row(ranked[0])
        public["supporting_formulas"] = [
            {
                "formula_id": row.get("formula_id"),
                "normalized_data_help_priority": row.get("normalized_data_help_priority"),
                "predicted_failure_risk": row.get("predicted_failure_risk"),
            }
            for row in ranked[: min(5, len(ranked))]
        ]
        result.append(public)
    result.sort(
        key=lambda row: (
            -_safe_float(row.get("normalized_data_help_priority")),
            -_safe_float(row.get("predicted_failure_risk")),
            str(row.get("formula_id") or ""),
            str(row.get("cell_id") or ""),
        )
    )
    return result[: max(top_k * 3, top_k)]


def _recommendations(
    *,
    top_priority_cells: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    seen: set[str] = set()
    recommendations = []
    for row in top_priority_cells:
        cell_id = str(row.get("cell_id") or "")
        if cell_id in seen:
            continue
        seen.add(cell_id)
        score = _safe_float(row.get("normalized_data_help_priority"))
        case_type = str(row.get("manual_case_type") or "")
        priority = "P0" if score >= 0.75 else "P1" if score >= 0.45 else "P2"
        action = "expand_discovery_then_locked_eval"
        if case_type == "phrase_no_winner":
            action = "add_phrase_no_winner_and_order_sensitive_mention_rows"
        elif case_type == "shadow_negative":
            action = "add_real_shadow_negative_rows_and_review_shadow_evidence"
        elif case_type == "positive_active":
            action = "review_active_evidence_then_add_positive_context_rows"
        recommendations.append(
            {
                "priority": priority,
                "cell_id": cell_id,
                "formula_id": row.get("formula_id"),
                "manual_case_type": case_type,
                "heuristic_group": row.get("heuristic_group"),
                "scorer_id": row.get("scorer_id"),
                "recommended_action": action,
                "manual_discovery_rows": _rows_for_priority(
                    manifest=manifest,
                    key="manual_rows_by_priority",
                    priority=priority,
                ),
                "llm_discovery_rows": _rows_for_priority(
                    manifest=manifest,
                    key="llm_rows_by_priority",
                    priority=priority,
                ),
                "locked_eval_rows": _rows_for_priority(
                    manifest=manifest,
                    key="locked_eval_rows_by_priority",
                    priority=priority,
                ),
                "notes": (
                    "Use as a spend-priority queue, not as proof of runtime "
                    "accuracy or policy promotion."
                ),
            }
        )
        if len(recommendations) >= _top_k(manifest):
            break
    return recommendations
