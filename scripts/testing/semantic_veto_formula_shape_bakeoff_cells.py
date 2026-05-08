from __future__ import annotations

from collections import Counter, defaultdict
import json
from math import log1p
from statistics import median
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _as_mapping, _mapping_rows, _safe_float
from semantic_veto_formula_shape_bakeoff_common import (
    NEGATIVE_CONTROL_IDS,
    PRIMARY_SELECTION_MODE,
    RANK_AGGREGATION_FORMULA,
    _clamp,
    _data_help_priority,
    _dimension_value,
    _failure_count,
    _formula_score,
    _has_phrase_surface_pattern,
    _internal_split,
    _normalize_priorities,
    _primary_score_rows,
    _product_impact_weight,
    _public_comparison_row,
    _rank_risk_score,
    _ratio,
    _round4,
    _round6,
    _sigmoid,
    _stable_unit_float,
    _string_list,
    _wilson_interval,
)
from semantic_veto_formula_shape_bakeoff_eval import _comparison_metrics


def _build_cells(
    *,
    rows: Sequence[Mapping[str, object]],
    cell_grouping: Sequence[str],
    weights: Mapping[str, float],
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(_dimension_value(row, field) for field in cell_grouping)].append(row)
    cells = []
    for key, group in grouped.items():
        dimensions = dict(zip(cell_grouping, key))
        case_type = dimensions.get("manual_case_type", "missing")
        outcomes = Counter(str(row.get("product_outcome") or "") for row in group)
        failures = _failure_count(case_type=case_type, outcomes=outcomes)
        trials = len(group)
        successes = trials - failures
        observed_failure_rate = _ratio(failures, trials)
        posterior = (failures + 0.5) / (trials + 1.0) if trials else None
        interval = _wilson_interval(failures=failures, trials=trials)
        cell_id = "::".join(f"{field}={dimensions[field]}" for field in cell_grouping)
        split = _internal_split(cell_id=cell_id, manifest=manifest)
        features = _cell_features(group=group, dimensions=dimensions, manifest=manifest)
        product_impact = _product_impact_weight(case_type=case_type, weights=weights)
        cell = {
            "cell_id": cell_id,
            "cell_split": split,
            "scorer_id": dimensions.get("scorer_id", "missing"),
            "selection_mode": dimensions.get("selection_mode", "missing"),
            "heuristic_group": dimensions.get("heuristic_group", "missing"),
            "manual_case_type": case_type,
            "shadow_contract": dimensions.get("shadow_contract", "missing"),
            "source_rank_bin": dimensions.get("source_rank_bin", "missing"),
            "polysemy_band": dimensions.get("polysemy_band", "missing"),
            "case_rows": trials,
            "trigger_count": len({str(row.get("trigger") or "") for row in group}),
            "triggers": sorted({str(row.get("trigger") or "") for row in group})[:12],
            "outcome_counts": dict(sorted(outcomes.items())),
            "failure_count": failures,
            "success_count": successes,
            "observed_failure_rate": _round4(observed_failure_rate),
            "posterior_failure_rate": _round4(posterior),
            "uncertainty_interval": {
                "method": "wilson_95",
                "lower": _round4(interval[0]),
                "upper": _round4(interval[1]),
                "width": _round4(interval[1] - interval[0]),
            },
            "product_impact_weight": _round4(product_impact),
            "features": features,
        }
        cells.append(cell)
    cells.sort(key=lambda row: str(row.get("cell_id") or ""))
    return cells


def _cell_features(
    *,
    group: Sequence[Mapping[str, object]],
    dimensions: Mapping[str, str],
    manifest: Mapping[str, object],
) -> dict[str, object]:
    ranks = [
        float(row.get("source_rank"))
        for row in group
        if isinstance(row.get("source_rank"), (int, float))
    ]
    rank_scores = [_rank_risk_score(rank) for rank in ranks]
    senses = [
        float(row.get("wordnet_sense_count") or 0)
        for row in group
        if isinstance(row.get("wordnet_sense_count"), (int, float))
    ]
    pos_counts = [
        float(row.get("wordnet_pos_count") or 0)
        for row in group
        if isinstance(row.get("wordnet_pos_count"), (int, float))
    ]
    margins = [
        float(row.get("margin")) for row in group if isinstance(row.get("margin"), (int, float))
    ]
    active_scores = [
        float(row.get("active_score"))
        for row in group
        if isinstance(row.get("active_score"), (int, float))
    ]
    phrase_scores = [row.get("phrase_score_lead") for row in group]
    underfilled_target = int(
        _as_mapping(manifest.get("data_help_priority")).get("underfilled_target_rows") or 8
    )
    rank_missing_rate = 1.0 - _ratio(len(ranks), len(group))
    mean_sense = sum(senses) / len(senses) if senses else 0.0
    mean_pos = sum(pos_counts) / len(pos_counts) if pos_counts else 0.0
    near_tie_rate = _ratio(sum(1 for margin in margins if abs(margin) < 0.02), len(margins))
    active_low_rate = _ratio(sum(1 for score in active_scores if score < 0.05), len(active_scores))
    phrase_score_missing_rate = _ratio(
        sum(1 for value in phrase_scores if value is None),
        len(group),
    )
    underfilled_rate = max(0.0, (underfilled_target - len(group)) / underfilled_target)
    case_type = dimensions.get("manual_case_type", "")
    phrase_surface_rate = _ratio(
        sum(1 for row in group if _has_phrase_surface_pattern(row)),
        len(group),
    )
    rank_risk = sum(rank_scores) / len(rank_scores) if rank_scores else 0.0
    sense_risk = min(1.0, log1p(mean_sense) / log1p(40.0))
    pos_risk = min(1.0, max(0.0, mean_pos - 1.0) / 3.0)
    case_type_prior = {
        "positive_active": 0.35,
        "shadow_negative": 0.45,
        "phrase_no_winner": 0.85,
    }.get(case_type, 0.5)
    shadow_contract_risk = {
        "full": 0.75,
        "limited": 0.60,
        "not_applicable": 0.20,
    }.get(dimensions.get("shadow_contract", ""), 0.45)
    coverage_gap = min(
        1.0,
        0.35 * rank_missing_rate + 0.35 * phrase_score_missing_rate + 0.30 * underfilled_rate,
    )
    fixability = min(
        1.0,
        0.35 * near_tie_rate
        + 0.25 * active_low_rate
        + 0.20 * underfilled_rate
        + 0.20 * coverage_gap,
    )
    exposure = max(rank_risk, 0.25 * rank_missing_rate)
    return {
        "rank_risk": _round4(rank_risk),
        "rank_missing_rate": _round4(rank_missing_rate),
        "mean_source_rank": _round4(sum(ranks) / len(ranks)) if ranks else None,
        "sense_risk": _round4(sense_risk),
        "mean_wordnet_sense_count": _round4(mean_sense),
        "pos_risk": _round4(pos_risk),
        "mean_wordnet_pos_count": _round4(mean_pos),
        "case_type_prior": _round4(case_type_prior),
        "shadow_contract_risk": _round4(shadow_contract_risk),
        "near_tie_rate": _round4(near_tie_rate),
        "active_low_rate": _round4(active_low_rate),
        "mean_abs_margin": _round4(sum(abs(value) for value in margins) / len(margins))
        if margins
        else None,
        "phrase_score_missing_rate": _round4(phrase_score_missing_rate),
        "phrase_surface_pattern_rate": _round4(phrase_surface_rate),
        "underfilled_rate": _round4(underfilled_rate),
        "coverage_gap": _round4(coverage_gap),
        "fixability": _round4(fixability),
        "exposure_weight": _round4(exposure),
        "is_positive_case": 1.0 if case_type == "positive_active" else 0.0,
        "is_shadow_case": 1.0 if case_type == "shadow_negative" else 0.0,
        "is_phrase_case": 1.0 if case_type == "phrase_no_winner" else 0.0,
    }


def _score_formula_cells(
    *,
    cells: Sequence[Mapping[str, object]],
    formula_ids: Sequence[str],
    control_ids: Sequence[str],
) -> list[dict[str, object]]:
    rows = []
    for formula_id in list(formula_ids) + list(control_ids):
        for cell in cells:
            features = _as_mapping(cell.get("features"))
            predicted = _formula_score(formula_id=formula_id, features=features, cell=cell)
            if predicted is None:
                continue
            priority = _data_help_priority(cell=cell, predicted_failure_risk=predicted)
            rows.append(
                {
                    "formula_id": formula_id,
                    "formula_kind": "negative_control"
                    if formula_id in NEGATIVE_CONTROL_IDS
                    else "candidate",
                    "cell_id": str(cell.get("cell_id") or ""),
                    "cell_split": str(cell.get("cell_split") or ""),
                    "scorer_id": str(cell.get("scorer_id") or ""),
                    "selection_mode": str(cell.get("selection_mode") or ""),
                    "heuristic_group": str(cell.get("heuristic_group") or ""),
                    "manual_case_type": str(cell.get("manual_case_type") or ""),
                    "shadow_contract": str(cell.get("shadow_contract") or ""),
                    "source_rank_bin": str(cell.get("source_rank_bin") or ""),
                    "polysemy_band": str(cell.get("polysemy_band") or ""),
                    "case_rows": int(cell.get("case_rows") or 0),
                    "failure_count": int(cell.get("failure_count") or 0),
                    "observed_failure_rate": cell.get("observed_failure_rate"),
                    "posterior_failure_rate": cell.get("posterior_failure_rate"),
                    "uncertainty_width": _as_mapping(cell.get("uncertainty_interval")).get("width"),
                    "predicted_failure_risk": _round4(predicted),
                    "data_help_priority": _round6(priority),
                    "triggers": cell.get("triggers") or [],
                }
            )
    _normalize_priorities(rows)
    return rows


def _rank_aggregation_rows(score_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    candidate_rows = [
        row
        for row in score_rows
        if row.get("formula_kind") == "candidate"
        and row.get("formula_id") != RANK_AGGREGATION_FORMULA
    ]
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("scorer_id") or ""), str(row.get("selection_mode") or ""))].append(row)
    aggregate_rows = []
    for _scope, rows in grouped.items():
        by_formula: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in rows:
            by_formula[str(row.get("formula_id") or "")].append(row)
        ranks_by_cell: dict[str, list[float]] = defaultdict(list)
        for formula_rows in by_formula.values():
            ranked = sorted(
                formula_rows,
                key=lambda row: (
                    -_safe_float(row.get("predicted_failure_risk")),
                    str(row.get("cell_id") or ""),
                ),
            )
            denominator = max(1, len(ranked) - 1)
            for index, row in enumerate(ranked):
                risk_rank = 1.0 - (index / denominator if denominator else 0.0)
                ranks_by_cell[str(row.get("cell_id") or "")].append(risk_rank)
        source_by_cell = {str(row.get("cell_id") or ""): row for row in rows}
        for cell_id, ranks in ranks_by_cell.items():
            source = source_by_cell[cell_id]
            predicted = median(ranks)
            priority = _safe_float(source.get("data_help_priority")) * max(0.1, predicted)
            payload = dict(source)
            payload.update(
                {
                    "formula_id": RANK_AGGREGATION_FORMULA,
                    "formula_kind": "candidate",
                    "predicted_failure_risk": _round4(predicted),
                    "data_help_priority": _round6(priority),
                }
            )
            aggregate_rows.append(payload)
    _normalize_priorities(aggregate_rows)
    return aggregate_rows


def _parameter_sweep_results(
    *,
    cells: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
    top_k: int,
) -> list[dict[str, object]]:
    results = []
    by_cell = {str(cell.get("cell_id") or ""): cell for cell in cells}
    for sweep in _mapping_rows(manifest.get("parameter_sweeps")):
        sweep_id = str(sweep.get("sweep_id") or "").strip()
        if not sweep_id:
            continue
        candidates = []
        for index, weights in enumerate(_sweep_weight_vectors(sweep)):
            formula_id = f"sweep_{sweep_id}_{index:03d}"
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
            metrics = _comparison_metrics(
                formula_id=formula_id,
                scope_id=f"sweep_discovery::{sweep_id}",
                rows=discovery_rows,
                by_cell=by_cell,
                top_k=top_k,
                shuffled=False,
            )
            candidates.append(
                {
                    "formula_id": formula_id,
                    "weights": weights,
                    "score_rows": rows,
                    "selection_metrics": metrics,
                }
            )
        if not candidates:
            results.append(
                {
                    "sweep_id": sweep_id,
                    "status": "review",
                    "sampled_candidate_count": 0,
                    "issue": "no_discovery_candidates_available",
                }
            )
            continue
        selected = sorted(candidates, key=_sweep_candidate_rank_key)[0]
        selected_formula_id = f"sweep_{sweep_id}_selected"
        selected_rows = []
        for row in _mapping_rows(selected.get("score_rows")):
            payload = dict(row)
            payload["formula_id"] = selected_formula_id
            payload["formula_kind"] = "candidate"
            payload["sweep_id"] = sweep_id
            selected_rows.append(payload)
        _normalize_priorities(selected_rows)
        primary_rows = _primary_score_rows(selected_rows)
        locked_rows = [
            row for row in primary_rows if row.get("cell_split") == "internal_locked_eval"
        ]
        discovery_rows = [row for row in primary_rows if row.get("cell_split") == "discovery"]
        results.append(
            {
                "sweep_id": sweep_id,
                "status": "ok",
                "formula_id": selected_formula_id,
                "formula_class": str(sweep.get("formula_class") or ""),
                "composition": str(sweep.get("composition") or ""),
                "sampled_candidate_count": len(candidates),
                "selection_scope": str(sweep.get("selection_scope") or ""),
                "selection_metric_order": _string_list(sweep.get("selection_metric_order")),
                "selected_weights": _public_weights(selected.get("weights")),
                "selected_discovery_metrics": _public_comparison_row(
                    _comparison_metrics(
                        formula_id=selected_formula_id,
                        scope_id=f"sweep_selected_discovery::{sweep_id}",
                        rows=discovery_rows,
                        by_cell=by_cell,
                        top_k=top_k,
                        shuffled=False,
                    )
                ),
                "selected_internal_locked_eval_metrics": _public_comparison_row(
                    _comparison_metrics(
                        formula_id=selected_formula_id,
                        scope_id=f"sweep_selected_internal_locked_eval::{sweep_id}",
                        rows=locked_rows,
                        by_cell=by_cell,
                        top_k=top_k,
                        shuffled=False,
                    )
                )
                if locked_rows
                else {},
                "selected_primary_all_metrics": _public_comparison_row(
                    _comparison_metrics(
                        formula_id=selected_formula_id,
                        scope_id=f"sweep_selected_primary_all::{sweep_id}",
                        rows=primary_rows,
                        by_cell=by_cell,
                        top_k=top_k,
                        shuffled=False,
                    )
                ),
                "selected_score_rows": selected_rows,
                "top_sampled_candidates": [
                    {
                        "formula_id": candidate.get("formula_id"),
                        "selection_metrics": _public_comparison_row(
                            _as_mapping(candidate.get("selection_metrics"))
                        ),
                        "weights": _public_weights(candidate.get("weights")),
                    }
                    for candidate in sorted(candidates, key=_sweep_candidate_rank_key)[:5]
                ],
            }
        )
    return results


def _score_sweep_cells(
    *,
    cells: Sequence[Mapping[str, object]],
    sweep: Mapping[str, object],
    formula_id: str,
    weights: Mapping[str, object],
) -> list[dict[str, object]]:
    rows = []
    for cell in cells:
        features = _as_mapping(cell.get("features"))
        predicted = _sweep_formula_score(sweep=sweep, features=features, cell=cell, weights=weights)
        priority = _data_help_priority(cell=cell, predicted_failure_risk=predicted)
        rows.append(
            {
                "formula_id": formula_id,
                "formula_kind": "sweep_candidate",
                "cell_id": str(cell.get("cell_id") or ""),
                "cell_split": str(cell.get("cell_split") or ""),
                "scorer_id": str(cell.get("scorer_id") or ""),
                "selection_mode": str(cell.get("selection_mode") or ""),
                "heuristic_group": str(cell.get("heuristic_group") or ""),
                "manual_case_type": str(cell.get("manual_case_type") or ""),
                "shadow_contract": str(cell.get("shadow_contract") or ""),
                "source_rank_bin": str(cell.get("source_rank_bin") or ""),
                "polysemy_band": str(cell.get("polysemy_band") or ""),
                "case_rows": int(cell.get("case_rows") or 0),
                "failure_count": int(cell.get("failure_count") or 0),
                "observed_failure_rate": cell.get("observed_failure_rate"),
                "posterior_failure_rate": cell.get("posterior_failure_rate"),
                "uncertainty_width": _as_mapping(cell.get("uncertainty_interval")).get("width"),
                "predicted_failure_risk": _round4(predicted),
                "data_help_priority": _round6(priority),
                "triggers": cell.get("triggers") or [],
            }
        )
    _normalize_priorities(rows)
    return rows


def _public_parameter_sweep_results(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    public_rows = []
    for row in rows:
        selected_score_rows = _mapping_rows(row.get("selected_score_rows"))
        public_rows.append(
            {
                "sweep_id": row.get("sweep_id"),
                "status": row.get("status"),
                "formula_id": row.get("formula_id"),
                "formula_class": row.get("formula_class"),
                "composition": row.get("composition"),
                "sampled_candidate_count": row.get("sampled_candidate_count"),
                "selection_scope": row.get("selection_scope"),
                "selection_metric_order": row.get("selection_metric_order"),
                "selected_weights": row.get("selected_weights"),
                "selected_discovery_metrics": row.get("selected_discovery_metrics"),
                "selected_internal_locked_eval_metrics": row.get(
                    "selected_internal_locked_eval_metrics"
                ),
                "selected_primary_all_metrics": row.get("selected_primary_all_metrics"),
                "selected_score_row_count": len(selected_score_rows),
                "top_sampled_candidates": row.get("top_sampled_candidates"),
            }
        )
    return public_rows


def _sweep_formula_score(
    *,
    sweep: Mapping[str, object],
    features: Mapping[str, object],
    cell: Mapping[str, object],
    weights: Mapping[str, object],
) -> float:
    composition = str(sweep.get("composition") or "linear")
    if composition == "gated_linear":
        case_type = str(cell.get("manual_case_type") or "")
        gate_weights = _as_mapping(weights.get(case_type)) or _as_mapping(weights.get("default"))
        return _clamp(
            sum(
                _safe_float(gate_weights.get(feature_id)) * _safe_float(features.get(feature_id))
                for feature_id in gate_weights
            )
        )
    feature_weights = _as_mapping(weights)
    linear = sum(
        _safe_float(weight) * _safe_float(features.get(feature_id))
        for feature_id, weight in feature_weights.items()
    )
    if composition == "logistic":
        return _sigmoid(4.0 * (linear - 0.5))
    return _clamp(linear)


def _sweep_weight_vectors(sweep: Mapping[str, object]) -> list[dict[str, object]]:
    composition = str(sweep.get("composition") or "linear")
    sample_count = max(1, int(sweep.get("sample_count") or 64))
    seed = str(sweep.get("seed") or sweep.get("sweep_id") or "semantic_veto_sweep")
    if composition == "gated_linear":
        gate_features = _as_mapping(sweep.get("gate_features"))
        gates = {
            str(gate_id): _string_list(features)
            for gate_id, features in gate_features.items()
            if _string_list(features)
        }
        vectors = []
        for index in range(sample_count):
            vectors.append(
                {
                    gate_id: _sample_simplex_weights(
                        features=features,
                        seed=f"{seed}:{gate_id}",
                        index=index,
                    )
                    for gate_id, features in gates.items()
                }
            )
        if gates:
            vectors.insert(
                0,
                {gate_id: _equal_weights(features) for gate_id, features in gates.items()},
            )
        return _dedupe_weight_vectors(vectors)
    features = _string_list(sweep.get("features"))
    if not features:
        return []
    vectors = [_equal_weights(features)]
    vectors.extend(
        {feature_id: 1.0 if feature_id == selected else 0.0 for feature_id in features}
        for selected in features
    )
    for index in range(sample_count):
        vectors.append(_sample_simplex_weights(features=features, seed=seed, index=index))
    return _dedupe_weight_vectors(vectors)


def _sample_simplex_weights(
    *,
    features: Sequence[str],
    seed: str,
    index: int,
) -> dict[str, float]:
    raw = []
    for feature_id in features:
        value = max(1e-6, _stable_unit_float(f"{seed}:{index}:{feature_id}"))
        raw.append(-log1p(-min(0.999999, value)))
    total = sum(raw) or 1.0
    return {feature_id: round(value / total, 6) for feature_id, value in zip(features, raw)}


def _equal_weights(features: Sequence[str]) -> dict[str, float]:
    if not features:
        return {}
    value = round(1.0 / len(features), 6)
    return {feature_id: value for feature_id in features}


def _dedupe_weight_vectors(vectors: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    result = []
    for vector in vectors:
        payload = json.dumps(vector, sort_keys=True)
        if payload in seen:
            continue
        seen.add(payload)
        result.append(dict(vector))
    return result


def _sweep_candidate_rank_key(row: Mapping[str, object]) -> tuple[float, float, float, str]:
    metrics = _as_mapping(row.get("selection_metrics"))
    return (
        -_safe_float(metrics.get("spearman_rank_correlation")),
        -_safe_float(metrics.get("top_k_lift")),
        _safe_float(metrics.get("brier_score")),
        str(row.get("formula_id") or ""),
    )


def _public_weights(value: object) -> object:
    if not isinstance(value, Mapping):
        return {}
    return json.loads(json.dumps(value, sort_keys=True))
