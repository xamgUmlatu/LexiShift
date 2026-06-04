from __future__ import annotations

import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_formula_shape_bakeoff_cells import (
    _build_cells,
    _score_sweep_cells,
    _sweep_candidate_rank_key,
    _sweep_weight_vectors,
)
from semantic_veto_formula_shape_bakeoff_common import (
    PRIMARY_SELECTION_MODE,
    _primary_score_rows,
    _public_comparison_row,
    _round4,
    _string_list,
    _top_k,
)
from semantic_veto_formula_shape_bakeoff_eval import (
    _comparison_metrics,
)
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _mapping_rows,
    _repo_path,
    _safe_float,
    _utility_weights,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_MANIFEST = TEST_INPUTS_ROOT / "semantic_veto_formula_shape_bakeoff_en_es.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_weight_surface_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_weight_surface_en_es_latest.md"
DEFAULT_ALPHA_GRID = tuple(round(index / 10, 2) for index in range(11))
PLATEAU_EPSILON = 0.02


def build_formula_weight_surface_report(
    *,
    manifest: Mapping[str, object],
    difficulty_surface_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    manifest_path: Path | None = None,
    difficulty_surface_path: Path | None = None,
    policy_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy_payload)
    cell_grouping = _string_list(manifest.get("cell_grouping"))
    case_rows = _mapping_rows(difficulty_surface_payload.get("case_traces"))
    issues: list[str] = []
    if not case_rows:
        issues.append("difficulty_surface_has_no_case_traces")
    cells = _build_cells(
        rows=case_rows,
        cell_grouping=cell_grouping,
        weights=weights,
        manifest=manifest,
    )
    by_cell = {str(cell.get("cell_id") or ""): cell for cell in cells}
    sweep_reports = []
    for sweep in _mapping_rows(manifest.get("parameter_sweeps")):
        sweep_report = _analyze_sweep(
            sweep=sweep,
            cells=cells,
            by_cell=by_cell,
            top_k=_top_k(manifest),
        )
        sweep_reports.append(sweep_report)
    if not sweep_reports:
        issues.append("manifest_has_no_parameter_sweeps")
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "formula_weight_surface_established"
            if not issues
            else "formula_weight_surface_incomplete"
        ),
        "generated_at": generated_at,
        "pair": str(
            policy_payload.get("pair") or difficulty_surface_payload.get("pair") or "en-es"
        ),
        "inputs": {
            "manifest_path": _repo_path(manifest_path),
            "difficulty_surface_path": _repo_path(difficulty_surface_path),
            "policy_path": _repo_path(policy_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "selection_scope": "primary discovery cells only",
            "sentinel_policy": "excluded from selection and primary curve metrics",
            "surface_probe": (
                "sampled maxima plus one-dimensional feature-share curves and "
                "pairwise feature-share probes around selected weights"
            ),
            "plateau_epsilon": PLATEAU_EPSILON,
            "alpha_grid": list(DEFAULT_ALPHA_GRID),
        },
        "summary": {
            "issues": issues,
            "case_trace_rows_read": len(case_rows),
            "cell_count": len(cells),
            "primary_cell_count": sum(
                1 for cell in cells if cell.get("selection_mode") == PRIMARY_SELECTION_MODE
            ),
            "sweep_count": len(sweep_reports),
            "sweep_overview": [_public_sweep_summary(row) for row in sweep_reports],
        },
        "sweep_reports": sweep_reports,
        "limitations": [
            "surface_is_over_current_draft_heuristic_cells_not_representative_browsing",
            "internal_locked_eval_split_is_advisory",
            "one_dimensional_curves_hold_other_weights_at_selected_relative_shares",
            "sampled_maximum_is_not_a_proof_of_global_optimum",
            "runtime_policy_remains_unchanged",
        ],
        "next_steps": [
            "Expand top high-uncertainty cells, then rerun surface analysis.",
            (
                "Treat sharp or unstable maxima as curve-sensitivity signals; "
                "use them to choose expansion cells, not to lock coefficients."
            ),
            "Prefer broad plateaus that survive internal locked-eval checks after expansion.",
        ],
    }


def _analyze_sweep(
    *,
    sweep: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    top_k: int,
) -> dict[str, object]:
    sweep_id = str(sweep.get("sweep_id") or "")
    candidates = _candidate_rows_for_sweep(
        sweep=sweep,
        cells=cells,
        by_cell=by_cell,
        top_k=top_k,
    )
    if not candidates:
        return {
            "sweep_id": sweep_id,
            "status": "review",
            "issue": "no_candidates",
        }
    selected = sorted(candidates, key=_sweep_candidate_rank_key)[0]
    selected_weights = _as_mapping(selected.get("weights"))
    selected_rows = _mapping_rows(selected.get("score_rows"))
    selected_public = _selected_metrics(
        formula_id=f"surface_{sweep_id}_selected",
        rows=selected_rows,
        by_cell=by_cell,
        top_k=top_k,
    )
    sampled_max = _sampled_maximum_summary(candidates)
    feature_curves = _feature_curve_summaries(
        sweep=sweep,
        cells=cells,
        by_cell=by_cell,
        selected_weights=selected_weights,
        top_k=top_k,
    )
    pairwise_curves = _pairwise_curve_summaries(
        sweep=sweep,
        cells=cells,
        by_cell=by_cell,
        selected_weights=selected_weights,
        top_k=top_k,
    )
    return {
        "sweep_id": sweep_id,
        "status": "ok",
        "formula_class": str(sweep.get("formula_class") or ""),
        "composition": str(sweep.get("composition") or ""),
        "sampled_candidate_count": len(candidates),
        "selected_weights": _public_weights(selected_weights),
        "selected_metrics": selected_public,
        "sampled_maximum": sampled_max,
        "feature_curve_summaries": feature_curves,
        "pairwise_curve_summaries": pairwise_curves,
        "surface_shape": _surface_shape(sampled_max),
        "top_sampled_candidates": [
            _candidate_public_row(row)
            for row in sorted(candidates, key=_sweep_candidate_rank_key)[:8]
        ],
    }


def _candidate_rows_for_sweep(
    *,
    sweep: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    candidates = []
    sweep_id = str(sweep.get("sweep_id") or "")
    for index, weights in enumerate(_sweep_weight_vectors(sweep)):
        formula_id = f"surface_{sweep_id}_{index:03d}"
        rows = _score_sweep_cells(
            cells=cells,
            sweep=sweep,
            formula_id=formula_id,
            weights=weights,
        )
        discovery_rows = [
            row
            for row in rows
            if row.get("selection_mode") == PRIMARY_SELECTION_MODE
            and row.get("cell_split") == "discovery"
        ]
        if not discovery_rows:
            continue
        candidates.append(
            {
                "formula_id": formula_id,
                "weights": weights,
                "score_rows": rows,
                "selection_metrics": _comparison_metrics(
                    formula_id=formula_id,
                    scope_id=f"surface_discovery::{sweep_id}",
                    rows=discovery_rows,
                    by_cell=by_cell,
                    top_k=top_k,
                    shuffled=False,
                ),
                "primary_metrics": _comparison_metrics(
                    formula_id=formula_id,
                    scope_id=f"surface_primary::{sweep_id}",
                    rows=_primary_score_rows(rows),
                    by_cell=by_cell,
                    top_k=top_k,
                    shuffled=False,
                ),
                "locked_metrics": _comparison_metrics(
                    formula_id=formula_id,
                    scope_id=f"surface_internal_locked::{sweep_id}",
                    rows=[
                        row
                        for row in _primary_score_rows(rows)
                        if row.get("cell_split") == "internal_locked_eval"
                    ],
                    by_cell=by_cell,
                    top_k=top_k,
                    shuffled=False,
                ),
            }
        )
    return candidates


def _sampled_maximum_summary(candidates: Sequence[Mapping[str, object]]) -> dict[str, object]:
    sorted_candidates = sorted(candidates, key=_sweep_candidate_rank_key)
    best = sorted_candidates[0]
    best_score = _safe_float(
        _as_mapping(best.get("selection_metrics")).get("spearman_rank_correlation")
    )
    plateau = [
        row
        for row in candidates
        if _safe_float(_as_mapping(row.get("selection_metrics")).get("spearman_rank_correlation"))
        >= best_score - PLATEAU_EPSILON
    ]
    locked_values = [
        _safe_float(_as_mapping(row.get("locked_metrics")).get("spearman_rank_correlation"))
        for row in plateau
        if _as_mapping(row.get("locked_metrics")).get("spearman_rank_correlation") is not None
    ]
    selected_locked = _safe_float(
        _as_mapping(best.get("locked_metrics")).get("spearman_rank_correlation")
    )
    discovery_locked_pairs = [
        (
            _safe_float(_as_mapping(row.get("selection_metrics")).get("spearman_rank_correlation")),
            _safe_float(_as_mapping(row.get("locked_metrics")).get("spearman_rank_correlation")),
        )
        for row in candidates
        if _as_mapping(row.get("locked_metrics")).get("spearman_rank_correlation") is not None
    ]
    return {
        "best_formula_id": best.get("formula_id"),
        "best_discovery_spearman": _round4(best_score),
        "best_discovery_top_k_lift": _round4(
            _as_mapping(best.get("selection_metrics")).get("top_k_lift")
        ),
        "best_discovery_brier": _round4(
            _as_mapping(best.get("selection_metrics")).get("brier_score")
        ),
        "selected_locked_spearman": _round4(selected_locked)
        if _as_mapping(best.get("locked_metrics")).get("spearman_rank_correlation") is not None
        else None,
        "overfit_gap": _round4(best_score - selected_locked)
        if _as_mapping(best.get("locked_metrics")).get("spearman_rank_correlation") is not None
        else None,
        "plateau_candidate_count": len(plateau),
        "plateau_fraction": _round4(len(plateau) / len(candidates)) if candidates else None,
        "plateau_locked_spearman_min": _round4(min(locked_values)) if locked_values else None,
        "plateau_locked_spearman_max": _round4(max(locked_values)) if locked_values else None,
        "discovery_locked_spearman_correlation": _round4(_pearson_pairs(discovery_locked_pairs)),
    }


def _selected_metrics(
    *,
    formula_id: str,
    rows: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    top_k: int,
) -> dict[str, object]:
    primary = _primary_score_rows(rows)
    discovery = [row for row in primary if row.get("cell_split") == "discovery"]
    locked = [row for row in primary if row.get("cell_split") == "internal_locked_eval"]
    return {
        "discovery": _public_comparison_row(
            _comparison_metrics(
                formula_id=formula_id,
                scope_id="selected_discovery",
                rows=discovery,
                by_cell=by_cell,
                top_k=top_k,
                shuffled=False,
            )
        ),
        "internal_locked_eval": _public_comparison_row(
            _comparison_metrics(
                formula_id=formula_id,
                scope_id="selected_internal_locked_eval",
                rows=locked,
                by_cell=by_cell,
                top_k=top_k,
                shuffled=False,
            )
        )
        if locked
        else {},
        "primary_all": _public_comparison_row(
            _comparison_metrics(
                formula_id=formula_id,
                scope_id="selected_primary_all",
                rows=primary,
                by_cell=by_cell,
                top_k=top_k,
                shuffled=False,
            )
        ),
    }


def _feature_curve_summaries(
    *,
    sweep: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    selected_weights: Mapping[str, object],
    top_k: int,
) -> list[dict[str, object]]:
    curve_specs = _feature_curve_specs(sweep=sweep, selected_weights=selected_weights)
    rows = []
    for spec in curve_specs:
        points = []
        for alpha in DEFAULT_ALPHA_GRID:
            weights = _weights_with_feature_share(
                selected_weights=selected_weights,
                gate_id=spec.get("gate_id"),
                feature_id=str(spec["feature_id"]),
                alpha=alpha,
            )
            metric = _metrics_for_weights(
                sweep=sweep,
                cells=cells,
                by_cell=by_cell,
                weights=weights,
                formula_id=f"curve_{sweep.get('sweep_id')}_{spec['curve_id']}_{alpha}",
                top_k=top_k,
            )
            points.append(
                {
                    "alpha": alpha,
                    "discovery_spearman": metric["discovery_spearman"],
                    "locked_spearman": metric["locked_spearman"],
                    "primary_spearman": metric["primary_spearman"],
                    "brier_score": metric["brier_score"],
                    "top_k_lift": metric["top_k_lift"],
                }
            )
        best = sorted(
            points,
            key=lambda row: (
                -_safe_float(row.get("discovery_spearman")),
                -_safe_float(row.get("top_k_lift")),
                _safe_float(row.get("brier_score")),
            ),
        )[0]
        selected_alpha = _feature_share(
            weights=selected_weights,
            gate_id=spec.get("gate_id"),
            feature_id=str(spec["feature_id"]),
        )
        rows.append(
            {
                "curve_id": spec["curve_id"],
                "gate_id": spec.get("gate_id"),
                "feature_id": spec["feature_id"],
                "selected_alpha": _round4(selected_alpha),
                "best_alpha": best["alpha"],
                "best_discovery_spearman": best["discovery_spearman"],
                "best_locked_spearman": best["locked_spearman"],
                "selected_near_best": abs(selected_alpha - float(best["alpha"])) <= 0.15,
                "curve_shape": _curve_shape(points),
                "points": points,
            }
        )
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("best_discovery_spearman")),
            str(row.get("curve_id") or ""),
        )
    )
    return rows


def _pairwise_curve_summaries(
    *,
    sweep: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    selected_weights: Mapping[str, object],
    top_k: int,
) -> list[dict[str, object]]:
    pair_specs = _pairwise_curve_specs(sweep=sweep, selected_weights=selected_weights)
    rows = []
    for spec in pair_specs:
        points = []
        for alpha in DEFAULT_ALPHA_GRID:
            weights = _weights_with_pair_share(
                selected_weights=selected_weights,
                gate_id=spec.get("gate_id"),
                left_feature=str(spec["left_feature"]),
                right_feature=str(spec["right_feature"]),
                alpha=alpha,
            )
            metric = _metrics_for_weights(
                sweep=sweep,
                cells=cells,
                by_cell=by_cell,
                weights=weights,
                formula_id=f"pair_{sweep.get('sweep_id')}_{spec['curve_id']}_{alpha}",
                top_k=top_k,
            )
            points.append(
                {
                    "left_alpha": alpha,
                    "right_alpha": round(1.0 - alpha, 2),
                    "discovery_spearman": metric["discovery_spearman"],
                    "locked_spearman": metric["locked_spearman"],
                    "primary_spearman": metric["primary_spearman"],
                    "brier_score": metric["brier_score"],
                    "top_k_lift": metric["top_k_lift"],
                }
            )
        best = sorted(
            points,
            key=lambda row: (
                -_safe_float(row.get("discovery_spearman")),
                -_safe_float(row.get("top_k_lift")),
                _safe_float(row.get("brier_score")),
            ),
        )[0]
        rows.append(
            {
                "curve_id": spec["curve_id"],
                "gate_id": spec.get("gate_id"),
                "left_feature": spec["left_feature"],
                "right_feature": spec["right_feature"],
                "best_left_alpha": best["left_alpha"],
                "best_discovery_spearman": best["discovery_spearman"],
                "best_locked_spearman": best["locked_spearman"],
                "curve_shape": _curve_shape(points, alpha_key="left_alpha"),
                "points": points,
            }
        )
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("best_discovery_spearman")),
            str(row.get("curve_id") or ""),
        )
    )
    return rows


def _metrics_for_weights(
    *,
    sweep: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    by_cell: Mapping[str, Mapping[str, object]],
    weights: Mapping[str, object],
    formula_id: str,
    top_k: int,
) -> dict[str, object]:
    rows = _score_sweep_cells(
        cells=cells,
        sweep=sweep,
        formula_id=formula_id,
        weights=weights,
    )
    primary = _primary_score_rows(rows)
    discovery = [row for row in primary if row.get("cell_split") == "discovery"]
    locked = [row for row in primary if row.get("cell_split") == "internal_locked_eval"]
    discovery_metrics = _comparison_metrics(
        formula_id=formula_id,
        scope_id="curve_discovery",
        rows=discovery,
        by_cell=by_cell,
        top_k=top_k,
        shuffled=False,
    )
    primary_metrics = _comparison_metrics(
        formula_id=formula_id,
        scope_id="curve_primary",
        rows=primary,
        by_cell=by_cell,
        top_k=top_k,
        shuffled=False,
    )
    locked_metrics = (
        _comparison_metrics(
            formula_id=formula_id,
            scope_id="curve_locked",
            rows=locked,
            by_cell=by_cell,
            top_k=top_k,
            shuffled=False,
        )
        if locked
        else {}
    )
    return {
        "discovery_spearman": discovery_metrics.get("spearman_rank_correlation"),
        "locked_spearman": locked_metrics.get("spearman_rank_correlation"),
        "primary_spearman": primary_metrics.get("spearman_rank_correlation"),
        "brier_score": discovery_metrics.get("brier_score"),
        "top_k_lift": discovery_metrics.get("top_k_lift"),
    }


def _feature_curve_specs(
    *,
    sweep: Mapping[str, object],
    selected_weights: Mapping[str, object],
) -> list[dict[str, object]]:
    if str(sweep.get("composition") or "") == "gated_linear":
        specs = []
        for gate_id, raw_weights in selected_weights.items():
            weights = _as_mapping(raw_weights)
            for feature_id in _top_weight_features(weights, limit=4):
                specs.append(
                    {
                        "curve_id": f"{gate_id}.{feature_id}",
                        "gate_id": str(gate_id),
                        "feature_id": str(feature_id),
                    }
                )
        return specs
    return [
        {"curve_id": str(feature_id), "feature_id": str(feature_id)}
        for feature_id in _top_weight_features(selected_weights, limit=8)
    ]


def _pairwise_curve_specs(
    *,
    sweep: Mapping[str, object],
    selected_weights: Mapping[str, object],
) -> list[dict[str, object]]:
    if str(sweep.get("composition") or "") == "gated_linear":
        specs = []
        for gate_id, raw_weights in selected_weights.items():
            features = _top_weight_features(_as_mapping(raw_weights), limit=3)
            for left, right in itertools.combinations(features, 2):
                specs.append(
                    {
                        "curve_id": f"{gate_id}.{left}_vs_{right}",
                        "gate_id": str(gate_id),
                        "left_feature": str(left),
                        "right_feature": str(right),
                    }
                )
        return specs[:9]
    features = _top_weight_features(selected_weights, limit=5)
    return [
        {
            "curve_id": f"{left}_vs_{right}",
            "left_feature": str(left),
            "right_feature": str(right),
        }
        for left, right in itertools.combinations(features, 2)
    ][:8]


def _weights_with_feature_share(
    *,
    selected_weights: Mapping[str, object],
    gate_id: object,
    feature_id: str,
    alpha: float,
) -> dict[str, object]:
    if gate_id is not None:
        result = json.loads(json.dumps(selected_weights, sort_keys=True))
        result[str(gate_id)] = _one_feature_share(
            weights=_as_mapping(selected_weights.get(str(gate_id))),
            feature_id=feature_id,
            alpha=alpha,
        )
        return result
    return _one_feature_share(weights=selected_weights, feature_id=feature_id, alpha=alpha)


def _one_feature_share(
    *,
    weights: Mapping[str, object],
    feature_id: str,
    alpha: float,
) -> dict[str, float]:
    features = [str(key) for key in weights]
    if feature_id not in features:
        features.append(feature_id)
    remaining = [feature for feature in features if feature != feature_id]
    original_remaining_total = sum(_safe_float(weights.get(feature)) for feature in remaining)
    result = {feature: 0.0 for feature in features}
    result[feature_id] = round(alpha, 6)
    for feature in remaining:
        if original_remaining_total > 0:
            result[feature] = round(
                (1.0 - alpha) * _safe_float(weights.get(feature)) / original_remaining_total,
                6,
            )
        else:
            result[feature] = round((1.0 - alpha) / max(1, len(remaining)), 6)
    return result


def _weights_with_pair_share(
    *,
    selected_weights: Mapping[str, object],
    gate_id: object,
    left_feature: str,
    right_feature: str,
    alpha: float,
) -> dict[str, object]:
    pair_weights = {left_feature: round(alpha, 6), right_feature: round(1.0 - alpha, 6)}
    if gate_id is not None:
        result = json.loads(json.dumps(selected_weights, sort_keys=True))
        result[str(gate_id)] = pair_weights
        return result
    return pair_weights


def _feature_share(
    *,
    weights: Mapping[str, object],
    gate_id: object,
    feature_id: str,
) -> float:
    if gate_id is not None:
        weights = _as_mapping(weights.get(str(gate_id)))
    return _safe_float(weights.get(feature_id))


def _top_weight_features(weights: Mapping[str, object], *, limit: int) -> list[str]:
    rows = [(str(key), _safe_float(value)) for key, value in weights.items()]
    rows.sort(key=lambda item: (-item[1], item[0]))
    return [key for key, _value in rows[:limit]]


def _curve_shape(points: Sequence[Mapping[str, object]], *, alpha_key: str = "alpha") -> str:
    if not points:
        return "empty"
    sorted_points = sorted(points, key=lambda row: _safe_float(row.get(alpha_key)))
    values = [_safe_float(row.get("discovery_spearman")) for row in sorted_points]
    best = max(values)
    plateau_count = sum(1 for value in values if value >= best - PLATEAU_EPSILON)
    best_index = values.index(best)
    if plateau_count >= max(3, len(values) // 3):
        return "broad_plateau"
    if best_index in {0, len(values) - 1}:
        return "edge_maximum"
    return "interior_peak"


def _surface_shape(summary: Mapping[str, object]) -> str:
    plateau_fraction = _safe_float(summary.get("plateau_fraction"))
    overfit_gap = _safe_float(summary.get("overfit_gap"))
    if overfit_gap > 0.15:
        return "sharp_or_unstable"
    if plateau_fraction >= 0.20:
        return "broad_plateau"
    if plateau_fraction <= 0.05:
        return "sharp_sampled_peak"
    return "moderate_peak"


def _public_sweep_summary(row: Mapping[str, object]) -> dict[str, object]:
    selected = _as_mapping(row.get("selected_metrics"))
    discovery = _as_mapping(selected.get("discovery"))
    locked = _as_mapping(selected.get("internal_locked_eval"))
    primary = _as_mapping(selected.get("primary_all"))
    sampled = _as_mapping(row.get("sampled_maximum"))
    return {
        "sweep_id": row.get("sweep_id"),
        "sampled_candidate_count": row.get("sampled_candidate_count"),
        "selected_discovery_spearman": discovery.get("spearman_rank_correlation"),
        "selected_locked_spearman": locked.get("spearman_rank_correlation"),
        "selected_primary_spearman": primary.get("spearman_rank_correlation"),
        "selected_discovery_brier": discovery.get("brier_score"),
        "selected_top_k_lift": discovery.get("top_k_lift"),
        "plateau_candidate_count": sampled.get("plateau_candidate_count"),
        "plateau_fraction": sampled.get("plateau_fraction"),
        "overfit_gap": sampled.get("overfit_gap"),
        "discovery_locked_spearman_correlation": sampled.get(
            "discovery_locked_spearman_correlation"
        ),
        "surface_shape": row.get("surface_shape"),
    }


def _candidate_public_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "formula_id": row.get("formula_id"),
        "selection_metrics": _public_comparison_row(_as_mapping(row.get("selection_metrics"))),
        "locked_metrics": _public_comparison_row(_as_mapping(row.get("locked_metrics"))),
        "primary_metrics": _public_comparison_row(_as_mapping(row.get("primary_metrics"))),
    }


def _pearson_pairs(pairs: Sequence[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    left = [pair[0] for pair in pairs]
    right = [pair[1] for pair in pairs]
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((x - mean_left) * (y - mean_right) for x, y in pairs)
    denom_left = sum((x - mean_left) ** 2 for x in left) ** 0.5
    denom_right = sum((y - mean_right) ** 2 for y in right) ** 0.5
    denominator = denom_left * denom_right
    if denominator == 0:
        return None
    return numerator / denominator


def _public_weights(value: Mapping[str, object]) -> object:
    return json.loads(json.dumps(value, sort_keys=True))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
