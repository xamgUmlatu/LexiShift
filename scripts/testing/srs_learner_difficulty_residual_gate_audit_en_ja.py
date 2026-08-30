#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_curve_search_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_MARKDOWN_OUT as DEFAULT_CURVE_MARKDOWN,
    _feature_matrix,
    _feature_set_specs,
    _observed_for_context,
    _present_arrays,
    _raw_from_candidate_row,
    _signal_rows_for_context,
)
from srs_learner_difficulty_holdout_eval_en_ja import (  # noqa: E402
    DEFAULT_REVIEW_MARKDOWN,
    holdout_context_from_rows,
    parse_holdout_review_markdown,
)
from srs_learner_difficulty_model_family_meta_search_en_ja import (  # noqa: E402
    _load_json,
)
from srs_learner_difficulty_model_family_search_en_ja import (  # noqa: E402
    _signal_arrays,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _calibration_context,
    _escape,
    _mapping,
    _mapping_rows,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _target_curve_normalize,
    _utc_now,
)


DEFAULT_CURVE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_curve_search_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_gate_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_gate_audit_en_ja_latest.md"
)
ERROR_THRESHOLD = 0.25
MIN_GATE_FIT_COUNT = 4
MAX_CORRECTION_ABS = 0.35


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    description: str
    minimums: tuple[tuple[str, float], ...] = ()
    maximums: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class ResidualClusterSpec:
    cluster_id: str
    description: str
    predicate: Callable[[Mapping[str, object]], bool]


GATE_SPECS = (
    GateSpec(
        "kango_any",
        "Any candidate classified as kango.",
        minimums=(("wtype_kango_risk", 0.75),),
    ),
    GateSpec(
        "kango_commonish_mid",
        "Kango with moderate kango-mid score and no common-priority penalty.",
        minimums=(("wtype_kango_risk", 0.75), ("kango_mid_signal", 0.25)),
        maximums=(("kango_mid_signal", 0.70), ("kango_common_priority_risk", 0.25)),
    ),
    GateSpec(
        "kango_priority",
        "Kango that also has JMDict priority support.",
        minimums=(("wtype_kango_risk", 0.75), ("jmdict_priority", 0.25)),
    ),
    GateSpec(
        "kango_not_rare",
        "Kango whose corpus rarity signal is not in the extreme tail.",
        minimums=(("wtype_kango_risk", 0.75),),
        maximums=(("frequency", 0.85),),
    ),
    GateSpec(
        "wago_written_or_rare_any",
        "Wago with any written-form or rare-wago tail pressure.",
        minimums=(("wtype_wago_ease", 0.75), ("wago_written_or_rare", 0.25)),
    ),
    GateSpec(
        "wago_written_or_rare_moderate",
        "Wago with moderate written/rare pressure, excluding the extreme tail.",
        minimums=(("wtype_wago_ease", 0.75), ("wago_written_or_rare", 0.25)),
        maximums=(("wago_written_or_rare", 0.60),),
    ),
    GateSpec(
        "wago_obscure_tail",
        "Wago in the clear rare/obscure tail.",
        minimums=(("wtype_wago_ease", 0.75), ("wago_written_or_rare", 0.60)),
    ),
    GateSpec(
        "non_standard_reading_any",
        "Any non-standard reading signal.",
        minimums=(("non_standard_any", 0.75),),
    ),
    GateSpec(
        "rare_non_standard_reading",
        "Rare non-standard reading pressure.",
        minimums=(("reading_rarity_any", 0.75),),
    ),
    GateSpec(
        "extreme_frequency_tail",
        "Corpus frequency signal is in the extreme rarity tail.",
        minimums=(("frequency", 0.90),),
    ),
    GateSpec(
        "jmdict_priority_any",
        "JMDict priority signal is present.",
        minimums=(("jmdict_priority", 0.25),),
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only residual gate audit for en-ja learner difficulty. "
            "It audits whether observable gates isolate current failure clusters "
            "and whether bounded residual corrections are plausible."
        )
    )
    parser.add_argument("--curve-json", type=Path, default=DEFAULT_CURVE_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--detail-limit", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        curve_json_path=_resolve_path(args.curve_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        review_markdown=_resolve_path(args.review_markdown),
        detail_limit=max(1, int(args.detail_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    curve_json_path: Path,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    review_markdown: Path,
    detail_limit: int = 12,
) -> dict[str, object]:
    curve_report = _load_json(curve_json_path)
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    holdout_rows = parse_holdout_review_markdown(review_markdown)
    calibration_context = _calibration_context(calibration, component)
    holdout_context = dict(holdout_context_from_rows(holdout_rows, component))
    calibration_context["signal_rows"] = _signal_rows_for_context(calibration_context, component)
    holdout_context["signal_rows"] = _signal_rows_for_context(holdout_context, component)
    base_candidates = _select_base_candidates(curve_report)
    predictions = {
        str(candidate.get("candidate_id")): _predictions_for_candidate(
            candidate, component=component
        )
        for candidate in base_candidates
    }
    candidate_reports = [
        _candidate_audit(
            candidate,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            calibration_observed=_observed_for_context(
                predictions[str(candidate.get("candidate_id"))],
                calibration_context,
            ),
            holdout_observed=_observed_for_context(
                predictions[str(candidate.get("candidate_id"))],
                holdout_context,
            ),
            detail_limit=detail_limit,
        )
        for candidate in base_candidates
    ]
    aggregate = _aggregate_candidate_reports(candidate_reports)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Audit structured residual failures and observable gates before "
                "attempting a bounded correction layer."
            ),
            "base_candidate_selection": (
                "combined leader, holdout leader, CV leader, and the first "
                "pos_origin_curves practical-compromise contender from the latest "
                "curve-search artifact"
            ),
            "correction_probe": (
                "Fits a bounded constant residual shift on calibration rows inside "
                "each gate, then evaluates that shift on holdout rows. This is a "
                "diagnostic, not a runtime change."
            ),
            "oracle_cluster_probe": (
                "Fits the bounded shift directly on each holdout residual cluster "
                "to estimate the upper bound if that cluster were perfectly "
                "detectable. This is intentionally not deployable."
            ),
        },
        "inputs": {
            "curve_json": _repo_or_home_path(curve_json_path),
            "curve_markdown": _repo_or_home_path(DEFAULT_CURVE_MARKDOWN),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "review_markdown": _repo_or_home_path(review_markdown),
            "calibration_rows": int(len(calibration_context["expected_values"])),
            "holdout_rows": int(len(holdout_context["expected_values"])),
            "gate_count": len(GATE_SPECS),
        },
        "residual_clusters": [
            {"cluster_id": cluster.cluster_id, "description": cluster.description}
            for cluster in _cluster_specs()
        ],
        "gates": [
            {
                "gate_id": gate.gate_id,
                "description": gate.description,
                "minimums": [list(item) for item in gate.minimums],
                "maximums": [list(item) for item in gate.maximums],
            }
            for gate in GATE_SPECS
        ],
        "aggregate": aggregate,
        "candidate_reports": candidate_reports,
    }


def _select_base_candidates(curve_report: Mapping[str, object]) -> list[Mapping[str, object]]:
    exact_top = _mapping_rows(curve_report.get("exact_top"))
    exact_by_id = {str(row.get("candidate_id")): row for row in exact_top}
    candidate_ids: list[str] = []
    for leaderboard in ("combined_70_30", "holdout_balanced", "cv_balanced_mean"):
        rows = _mapping_rows(_mapping(curve_report.get("leaderboards")).get(leaderboard))
        if rows:
            candidate_ids.append(str(rows[0].get("candidate_id")))
    pos_origin = next(
        (
            str(row.get("candidate_id"))
            for row in exact_top
            if row.get("feature_set") == "pos_origin_curves"
        ),
        "",
    )
    if pos_origin:
        candidate_ids.append(pos_origin)
    selected: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for candidate_id in candidate_ids:
        if not candidate_id or candidate_id in seen or candidate_id not in exact_by_id:
            continue
        seen.add(candidate_id)
        selected.append(exact_by_id[candidate_id])
    return selected


def _predictions_for_candidate(
    candidate: Mapping[str, object],
    *,
    component: object,
) -> np.ndarray:
    signal_arrays = _signal_arrays(component)
    present_arrays = _present_arrays(component)
    specs_by_id = {spec.spec_id: spec for spec in _feature_set_specs()}
    feature_set = str(candidate.get("feature_set") or "")
    spec = specs_by_id.get(feature_set)
    if spec is None:
        raise ValueError(f"Unknown feature set in curve candidate: {feature_set}")
    matrix, feature_names = _feature_matrix(
        spec,
        signal_arrays=signal_arrays,
        present_arrays=present_arrays,
    )
    raw = _raw_from_candidate_row(candidate, matrix=matrix, feature_names=feature_names)
    normalized = _target_curve_normalize(
        raw,
        target_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
    )
    return normalized


def _candidate_audit(
    candidate: Mapping[str, object],
    *,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    calibration_observed: object,
    holdout_observed: object,
    detail_limit: int,
) -> dict[str, object]:
    calibration_rows = _residual_rows(calibration_context, calibration_observed)
    holdout_rows = _residual_rows(holdout_context, holdout_observed)
    cluster_specs = _cluster_specs()
    cluster_rows = {
        cluster.cluster_id: [row for row in holdout_rows if cluster.predicate(row)]
        for cluster in cluster_specs
    }
    gate_metrics = {
        cluster.cluster_id: _top_gate_metrics(holdout_rows, cluster.predicate)
        for cluster in cluster_specs
    }
    correction_probes = _correction_probes(
        calibration_rows,
        holdout_rows,
        cluster_specs=cluster_specs,
    )
    oracle_cluster_probes = _oracle_cluster_correction_probes(
        calibration_rows,
        holdout_rows,
        cluster_specs=cluster_specs,
    )
    return {
        "candidate_id": candidate.get("candidate_id"),
        "feature_set": candidate.get("feature_set"),
        "alpha": candidate.get("alpha"),
        "target_transform": candidate.get("target_transform"),
        "sample_weight_mode": candidate.get("sample_weight_mode"),
        "scores": {
            "calibration_balanced": _mapping(
                _mapping(candidate.get("calibration")).get("scores")
            ).get("balanced_score"),
            "holdout_balanced": _mapping(_mapping(candidate.get("holdout")).get("scores")).get(
                "balanced_score"
            ),
            "holdout_mae": _mapping(_mapping(candidate.get("holdout")).get("metrics")).get("mae"),
            "cv_balanced_mean": _mapping(candidate.get("cross_validation")).get("balanced_mean"),
            "cv_balanced_std": _mapping(candidate.get("cross_validation")).get("balanced_std"),
        },
        "holdout_residual_summary": _residual_summary(holdout_rows),
        "clusters": [
            _cluster_summary(cluster, cluster_rows[cluster.cluster_id], limit=detail_limit)
            for cluster in cluster_specs
        ],
        "gate_metrics": gate_metrics,
        "correction_probes": correction_probes[:detail_limit],
        "oracle_cluster_correction_probes": oracle_cluster_probes,
    }


def _residual_rows(
    context: Mapping[str, object],
    observed_values: object,
) -> list[dict[str, object]]:
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    signal_rows = [_enriched_signals(row) for row in _mapping_rows(context.get("signal_rows"))]
    rows: list[dict[str, object]] = []
    for index, label in enumerate(labels):
        if not np.isfinite(expected[index]) or not np.isfinite(observed[index]):
            continue
        residual = float(expected[index] - observed[index])
        signals = signal_rows[index] if index < len(signal_rows) else {}
        rows.append(
            {
                "label": label,
                "expected": float(expected[index]),
                "observed": float(observed[index]),
                "residual": residual,
                "absolute_error": abs(residual),
                "direction": "too_high" if residual < 0.0 else "too_low",
                "signals": signals,
            }
        )
    return rows


def _enriched_signals(row: Mapping[str, object]) -> dict[str, object]:
    signals = dict(row)
    signals["wago_written_or_rare"] = max(
        _signal_value(signals, "rare_wago_tail_risk"),
        _signal_value(signals, "written_wago_tail_risk"),
        _signal_value(signals, "rare_wago_obscure_written_risk"),
    )
    signals["reading_rarity_any"] = max(
        _signal_value(signals, "rare_non_standard_reading_risk"),
        _signal_value(signals, "rare_wago_non_standard_reading_risk"),
    )
    signals["non_standard_any"] = max(
        _signal_value(signals, "non_standard_reading_risk"),
        _signal_value(signals, "reading_rarity_any"),
    )
    return signals


def _cluster_specs() -> tuple[ResidualClusterSpec, ...]:
    return (
        ResidualClusterSpec(
            "large_error_any",
            "Any holdout row with absolute residual at least 0.25.",
            lambda row: float(row["absolute_error"]) >= ERROR_THRESHOLD,
        ),
        ResidualClusterSpec(
            "beginner_easy_too_high",
            "Expected <= 0.30 but predicted at least 0.25 too hard.",
            lambda row: _too_high(row) and float(row["expected"]) <= 0.30,
        ),
        ResidualClusterSpec(
            "common_kango_too_high",
            "Kango row expected <= 0.60 but predicted at least 0.25 too hard.",
            lambda row: (
                _too_high(row)
                and float(row["expected"]) <= 0.60
                and _signal_value(_signals(row), "wtype_kango_risk") >= 0.75
            ),
        ),
        ResidualClusterSpec(
            "written_wago_too_high",
            "Wago/written-form row predicted at least 0.25 too hard.",
            lambda row: (
                _too_high(row)
                and _signal_value(_signals(row), "wtype_wago_ease") >= 0.75
                and _signal_value(_signals(row), "wago_written_or_rare") >= 0.25
            ),
        ),
        ResidualClusterSpec(
            "obscure_reading_too_low",
            "Rare/non-standard reading row predicted at least 0.25 too easy.",
            lambda row: _too_low(row) and _signal_value(_signals(row), "non_standard_any") >= 0.50,
        ),
        ResidualClusterSpec(
            "upper_tail_too_low",
            "Expected >= 0.70 but predicted at least 0.25 too easy.",
            lambda row: _too_low(row) and float(row["expected"]) >= 0.70,
        ),
    )


def _too_high(row: Mapping[str, object]) -> bool:
    return float(row["observed"]) - float(row["expected"]) >= ERROR_THRESHOLD


def _too_low(row: Mapping[str, object]) -> bool:
    return float(row["expected"]) - float(row["observed"]) >= ERROR_THRESHOLD


def _signals(row: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(row.get("signals"))


def _top_gate_metrics(
    rows: Sequence[Mapping[str, object]],
    positive_predicate: Callable[[Mapping[str, object]], bool],
    *,
    limit: int = 6,
) -> list[dict[str, object]]:
    metrics = [_gate_metrics(rows, gate, positive_predicate) for gate in GATE_SPECS]
    return sorted(
        metrics,
        key=lambda row: (
            _optional_float(row.get("f1")) or 0.0,
            _optional_float(row.get("lift")) or 0.0,
            _optional_float(row.get("precision")) or 0.0,
        ),
        reverse=True,
    )[:limit]


def _gate_metrics(
    rows: Sequence[Mapping[str, object]],
    gate: GateSpec,
    positive_predicate: Callable[[Mapping[str, object]], bool],
) -> dict[str, object]:
    positives = [positive_predicate(row) for row in rows]
    selected = [_gate_matches(gate, _signals(row)) for row in rows]
    tp = sum(
        1 for is_positive, is_selected in zip(positives, selected) if is_positive and is_selected
    )
    fp = sum(
        1
        for is_positive, is_selected in zip(positives, selected)
        if not is_positive and is_selected
    )
    fn = sum(
        1
        for is_positive, is_selected in zip(positives, selected)
        if is_positive and not is_selected
    )
    positive_count = sum(1 for is_positive in positives if is_positive)
    selected_count = sum(1 for is_selected in selected if is_selected)
    precision = _ratio(tp, selected_count)
    recall = _ratio(tp, positive_count)
    base_rate = _ratio(positive_count, len(rows))
    f1 = _f1(precision, recall)
    return {
        "gate_id": gate.gate_id,
        "selected_count": selected_count,
        "positive_count": positive_count,
        "true_positive_count": tp,
        "false_positive_count": fp,
        "false_negative_count": fn,
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "f1": _rounded(f1),
        "lift": _rounded((precision / base_rate) if base_rate else None),
    }


def _gate_matches(gate: GateSpec, signals: Mapping[str, object]) -> bool:
    for signal, threshold in gate.minimums:
        if _signal_value(signals, signal) < threshold:
            return False
    for signal, threshold in gate.maximums:
        if _signal_value(signals, signal) > threshold:
            return False
    return True


def _correction_probes(
    calibration_rows: Sequence[Mapping[str, object]],
    holdout_rows: Sequence[Mapping[str, object]],
    *,
    cluster_specs: Sequence[ResidualClusterSpec],
    gate_specs: Sequence[GateSpec] = GATE_SPECS,
) -> list[dict[str, object]]:
    probes: list[dict[str, object]] = []
    base_mae = _mae(row["residual"] for row in holdout_rows)
    for gate in gate_specs:
        calibration_selected = [
            row for row in calibration_rows if _gate_matches(gate, _signals(row))
        ]
        holdout_selected = [row for row in holdout_rows if _gate_matches(gate, _signals(row))]
        if len(calibration_selected) < MIN_GATE_FIT_COUNT or not holdout_selected:
            continue
        delta = _bounded_median_residual(calibration_selected)
        adjusted_rows = _adjust_rows(holdout_rows, gate=gate, delta=delta)
        adjusted_mae = _mae(row["adjusted_residual"] for row in adjusted_rows)
        selected_adjusted = [row for row in adjusted_rows if _gate_matches(gate, _signals(row))]
        cluster_impacts = [
            _cluster_correction_impact(cluster, holdout_rows, adjusted_rows)
            for cluster in cluster_specs
        ]
        probes.append(
            {
                "gate_id": gate.gate_id,
                "delta": _rounded(delta),
                "calibration_fit_count": len(calibration_selected),
                "holdout_gate_count": len(holdout_selected),
                "holdout_mae_before": _rounded(base_mae),
                "holdout_mae_after": _rounded(adjusted_mae),
                "holdout_mae_delta": _rounded(adjusted_mae - base_mae),
                "gate_mae_before": _rounded(_mae(row["residual"] for row in holdout_selected)),
                "gate_mae_after": _rounded(
                    _mae(row["adjusted_residual"] for row in selected_adjusted)
                ),
                "cluster_impacts": cluster_impacts,
            }
        )
    return sorted(
        probes,
        key=lambda row: (
            float(row.get("holdout_mae_delta") or 0.0),
            float(row.get("gate_mae_after") or 0.0) - float(row.get("gate_mae_before") or 0.0),
        ),
    )


def _oracle_cluster_correction_probes(
    calibration_rows: Sequence[Mapping[str, object]],
    holdout_rows: Sequence[Mapping[str, object]],
    *,
    cluster_specs: Sequence[ResidualClusterSpec],
) -> list[dict[str, object]]:
    base_mae = _mae(row["residual"] for row in holdout_rows)
    probes: list[dict[str, object]] = []
    for cluster in cluster_specs:
        calibration_selected = [row for row in calibration_rows if cluster.predicate(row)]
        holdout_selected = [row for row in holdout_rows if cluster.predicate(row)]
        if not holdout_selected:
            probes.append(
                {
                    "cluster_id": cluster.cluster_id,
                    "delta": None,
                    "calibration_cluster_count": len(calibration_selected),
                    "holdout_cluster_count": len(holdout_selected),
                    "fit_source": "holdout_oracle",
                    "holdout_mae_before": _rounded(base_mae),
                    "holdout_mae_after": None,
                    "holdout_mae_delta": None,
                    "cluster_mae_before": (
                        _rounded(_mae(row["residual"] for row in holdout_selected))
                        if holdout_selected
                        else None
                    ),
                    "cluster_mae_after": None,
                    "cluster_mae_delta": None,
                    "diagnostic_only": True,
                }
            )
            continue
        delta = _bounded_median_residual(holdout_selected)
        adjusted = []
        for row in holdout_rows:
            next_row = dict(row)
            if cluster.predicate(row):
                observed = float(row["observed"]) + delta
                observed = float(np.clip(observed, 0.0, 1.0))
                next_row["adjusted_observed"] = observed
                next_row["adjusted_residual"] = float(row["expected"]) - observed
            else:
                next_row["adjusted_observed"] = row["observed"]
                next_row["adjusted_residual"] = row["residual"]
            adjusted.append(next_row)
        adjusted_selected = [row for row in adjusted if cluster.predicate(row)]
        after_mae = _mae(row["adjusted_residual"] for row in adjusted)
        cluster_before = _mae(row["residual"] for row in holdout_selected)
        cluster_after = _mae(row["adjusted_residual"] for row in adjusted_selected)
        probes.append(
            {
                "cluster_id": cluster.cluster_id,
                "delta": _rounded(delta),
                "calibration_cluster_count": len(calibration_selected),
                "holdout_cluster_count": len(holdout_selected),
                "fit_source": "holdout_oracle",
                "holdout_mae_before": _rounded(base_mae),
                "holdout_mae_after": _rounded(after_mae),
                "holdout_mae_delta": _rounded(after_mae - base_mae),
                "cluster_mae_before": _rounded(cluster_before),
                "cluster_mae_after": _rounded(cluster_after),
                "cluster_mae_delta": _rounded(cluster_after - cluster_before),
                "diagnostic_only": True,
            }
        )
    return sorted(
        probes,
        key=lambda row: (
            _optional_float(row.get("cluster_mae_delta")) or 999.0,
            _optional_float(row.get("holdout_mae_delta")) or 999.0,
        ),
    )


def _bounded_median_residual(rows: Sequence[Mapping[str, object]]) -> float:
    residuals = np.asarray([float(row["residual"]) for row in rows], dtype=np.float32)
    median = float(np.median(residuals))
    return float(np.clip(median, -MAX_CORRECTION_ABS, MAX_CORRECTION_ABS))


def _adjust_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    gate: GateSpec,
    delta: float,
) -> list[dict[str, object]]:
    adjusted: list[dict[str, object]] = []
    for row in rows:
        next_row = dict(row)
        if _gate_matches(gate, _signals(row)):
            observed = float(row["observed"]) + delta
            observed = float(np.clip(observed, 0.0, 1.0))
            next_row["adjusted_observed"] = observed
            next_row["adjusted_residual"] = float(row["expected"]) - observed
        else:
            next_row["adjusted_observed"] = row["observed"]
            next_row["adjusted_residual"] = row["residual"]
        adjusted.append(next_row)
    return adjusted


def _cluster_correction_impact(
    cluster: ResidualClusterSpec,
    rows: Sequence[Mapping[str, object]],
    adjusted_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    indices = [index for index, row in enumerate(rows) if cluster.predicate(row)]
    if not indices:
        return {
            "cluster_id": cluster.cluster_id,
            "count": 0,
            "mae_before": None,
            "mae_after": None,
            "mae_delta": None,
        }
    before = _mae(rows[index]["residual"] for index in indices)
    after = _mae(adjusted_rows[index]["adjusted_residual"] for index in indices)
    return {
        "cluster_id": cluster.cluster_id,
        "count": len(indices),
        "mae_before": _rounded(before),
        "mae_after": _rounded(after),
        "mae_delta": _rounded(after - before),
    }


def _cluster_summary(
    cluster: ResidualClusterSpec,
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> dict[str, object]:
    return {
        "cluster_id": cluster.cluster_id,
        "description": cluster.description,
        "count": len(rows),
        "mae": _rounded(_mae(row["residual"] for row in rows)) if rows else None,
        "mean_residual": _rounded(_mean(row["residual"] for row in rows)) if rows else None,
        "examples": [
            _row_example(row)
            for row in sorted(
                rows,
                key=lambda item: float(item["absolute_error"]),
                reverse=True,
            )[:limit]
        ],
    }


def _row_example(row: Mapping[str, object]) -> dict[str, object]:
    signals = _signals(row)
    return {
        "label": row.get("label"),
        "expected": _rounded(row.get("expected")),
        "observed": _rounded(row.get("observed")),
        "residual": _rounded(row.get("residual")),
        "absolute_error": _rounded(row.get("absolute_error")),
        "direction": row.get("direction"),
        "signals": {
            key: _rounded(signals.get(key))
            for key in (
                "frequency",
                "jmdict_priority",
                "kango_mid_signal",
                "kango_common_priority_risk",
                "wtype_kango_risk",
                "wtype_wago_ease",
                "wago_written_or_rare",
                "non_standard_any",
            )
        },
    }


def _residual_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    residuals = [float(row["residual"]) for row in rows]
    too_high = [row for row in rows if _too_high(row)]
    too_low = [row for row in rows if _too_low(row)]
    return {
        "row_count": len(rows),
        "mae": _rounded(_mae(residuals)),
        "mean_residual": _rounded(_mean(residuals)),
        "too_high_large_count": len(too_high),
        "too_low_large_count": len(too_low),
    }


def _aggregate_candidate_reports(
    reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    cluster_counts: dict[str, list[int]] = {}
    probe_deltas: dict[str, list[float]] = {}
    for report in reports:
        for cluster in _mapping_rows(report.get("clusters")):
            cluster_counts.setdefault(str(cluster.get("cluster_id")), []).append(
                int(cluster.get("count") or 0)
            )
        for probe in _mapping_rows(report.get("correction_probes")):
            delta = _optional_float(probe.get("holdout_mae_delta"))
            if delta is not None:
                probe_deltas.setdefault(str(probe.get("gate_id")), []).append(delta)
    return {
        "cluster_count_ranges": [
            {
                "cluster_id": cluster_id,
                "min_count": min(values),
                "max_count": max(values),
                "mean_count": _rounded(float(np.mean(np.asarray(values, dtype=np.float32)))),
            }
            for cluster_id, values in sorted(cluster_counts.items())
        ],
        "best_average_correction_gates": [
            {
                "gate_id": gate_id,
                "mean_holdout_mae_delta": _rounded(
                    float(np.mean(np.asarray(values, dtype=np.float32)))
                ),
                "min_holdout_mae_delta": _rounded(min(values)),
                "max_holdout_mae_delta": _rounded(max(values)),
            }
            for gate_id, values in sorted(
                probe_deltas.items(),
                key=lambda item: float(np.mean(np.asarray(item[1], dtype=np.float32))),
            )[:8]
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-ja Learner Difficulty Residual Gate Audit",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Calibration rows: `{_escape(_mapping(report.get('inputs')).get('calibration_rows'))}`",
        f"- Holdout rows: `{_escape(_mapping(report.get('inputs')).get('holdout_rows'))}`",
        f"- Gates audited: `{_escape(_mapping(report.get('inputs')).get('gate_count'))}`",
        "",
        "## Method",
        "",
        str(_mapping(report.get("method")).get("purpose") or ""),
        "",
        str(_mapping(report.get("method")).get("correction_probe") or ""),
        "",
        "## Aggregate",
        "",
        "Cluster count ranges across audited base candidates:",
        "",
        "| Cluster | Min | Max | Mean |",
        "| --- | ---: | ---: | ---: |",
    ]
    aggregate = _mapping(report.get("aggregate"))
    for row in _mapping_rows(aggregate.get("cluster_count_ranges")):
        lines.append(
            "| "
            f"`{_escape(row.get('cluster_id'))}` | "
            f"`{_escape(row.get('min_count'))}` | "
            f"`{_escape(row.get('max_count'))}` | "
            f"`{_escape(row.get('mean_count'))}` |"
        )
    lines.extend(
        [
            "",
            "Best average bounded correction probes across audited candidates:",
            "",
            "| Gate | Mean MAE delta | Min | Max |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(aggregate.get("best_average_correction_gates")):
        lines.append(
            "| "
            f"`{_escape(row.get('gate_id'))}` | "
            f"`{_escape(row.get('mean_holdout_mae_delta'))}` | "
            f"`{_escape(row.get('min_holdout_mae_delta'))}` | "
            f"`{_escape(row.get('max_holdout_mae_delta'))}` |"
        )
    lines.extend(["", "## Candidate Audits", ""])
    for candidate in _mapping_rows(report.get("candidate_reports")):
        lines.extend(_candidate_markdown(candidate))
    return "\n".join(lines).rstrip() + "\n"


def _candidate_markdown(candidate: Mapping[str, object]) -> list[str]:
    scores = _mapping(candidate.get("scores"))
    summary = _mapping(candidate.get("holdout_residual_summary"))
    lines = [
        f"### `{_escape(candidate.get('candidate_id'))}`",
        "",
        f"- Feature set: `{_escape(candidate.get('feature_set'))}`",
        f"- Scores: `{_compact(scores)}`",
        f"- Holdout residual summary: `{_compact(summary)}`",
        "",
        "Cluster counts:",
        "",
        "| Cluster | Count | MAE | Mean residual | Top examples |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for cluster in _mapping_rows(candidate.get("clusters")):
        examples = ", ".join(
            str(example.get("label")) for example in _mapping_rows(cluster.get("examples"))[:5]
        )
        lines.append(
            "| "
            f"`{_escape(cluster.get('cluster_id'))}` | "
            f"`{_escape(cluster.get('count'))}` | "
            f"`{_escape(cluster.get('mae'))}` | "
            f"`{_escape(cluster.get('mean_residual'))}` | "
            f"{_escape(examples)} |"
        )
    lines.extend(["", "Top gate separability by cluster:", ""])
    for cluster_id, rows in _mapping(candidate.get("gate_metrics")).items():
        best = _mapping_rows(rows)[:4]
        rendered = ", ".join(
            (
                f"{row.get('gate_id')} "
                f"P={row.get('precision')} R={row.get('recall')} "
                f"F1={row.get('f1')} lift={row.get('lift')}"
            )
            for row in best
        )
        lines.append(f"- `{_escape(cluster_id)}`: {rendered}")
    lines.extend(["", "Top bounded correction probes:", ""])
    lines.extend(
        [
            "| Gate | Delta | Cal fit | Holdout gate | MAE before | MAE after | MAE delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for probe in _mapping_rows(candidate.get("correction_probes"))[:8]:
        lines.append(
            "| "
            f"`{_escape(probe.get('gate_id'))}` | "
            f"`{_escape(probe.get('delta'))}` | "
            f"`{_escape(probe.get('calibration_fit_count'))}` | "
            f"`{_escape(probe.get('holdout_gate_count'))}` | "
            f"`{_escape(probe.get('holdout_mae_before'))}` | "
            f"`{_escape(probe.get('holdout_mae_after'))}` | "
            f"`{_escape(probe.get('holdout_mae_delta'))}` |"
        )
    oracle = _mapping_rows(candidate.get("oracle_cluster_correction_probes"))
    if oracle:
        lines.extend(
            [
                "",
                "Holdout-oracle cluster correction upper bounds:",
                "",
                (
                    "| Cluster | Delta | Cal cluster | Holdout cluster | "
                    "Cluster MAE before | Cluster MAE after | Cluster delta | "
                    "Total MAE delta |"
                ),
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for probe in oracle:
            lines.append(
                "| "
                f"`{_escape(probe.get('cluster_id'))}` | "
                f"`{_escape(probe.get('delta'))}` | "
                f"`{_escape(probe.get('calibration_cluster_count'))}` | "
                f"`{_escape(probe.get('holdout_cluster_count'))}` | "
                f"`{_escape(probe.get('cluster_mae_before'))}` | "
                f"`{_escape(probe.get('cluster_mae_after'))}` | "
                f"`{_escape(probe.get('cluster_mae_delta'))}` | "
                f"`{_escape(probe.get('holdout_mae_delta'))}` |"
            )
    lines.append("")
    return lines


def _signal_value(signals: Mapping[str, object], signal: str) -> float:
    parsed = _optional_float(signals.get(signal))
    return float(parsed) if parsed is not None else 0.0


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0.0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def _mae(values: object) -> float:
    parsed = np.asarray(list(values), dtype=np.float32)
    if len(parsed) == 0:
        return float("nan")
    return float(np.mean(np.abs(parsed)))


def _mean(values: object) -> float:
    parsed = np.asarray(list(values), dtype=np.float32)
    if len(parsed) == 0:
        return float("nan")
    return float(np.mean(parsed))


def _compact(value: object) -> str:
    mapping = _mapping(value)
    return ", ".join(f"{key}={_rounded(val)}" for key, val in mapping.items())


if __name__ == "__main__":
    raise SystemExit(main())
