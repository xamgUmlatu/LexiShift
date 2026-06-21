#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_cleaned_lane_eval_en_ja import (  # noqa: E402
    DEFAULT_SOURCE_PAIR_JSON,
    component_lookup,
    row_component_index,
)
from srs_learner_difficulty_gairaigo_curve_sweep_en_ja import (  # noqa: E402
    ROW_SIGNALS,
    CurveSpec,
    adjusted_rows_for_spec,
    current_curve_spec,
    metrics_for_rows,
    spec_from_summary,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_qualitative_failure_hypotheses_en_ja import (  # noqa: E402
    MatrixView,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
)
from srs_learner_difficulty_stitch_validation_eval_en_ja import (  # noqa: E402
    DEFAULT_CAP_REPORT,
    DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    score_arrays_for_models,
)


PAIR = "en-ja"
ANCHOR_MODEL = "ordinary_cap"
DEFAULT_CURVE_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_curve_sweep_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_curve_cross_split_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_curve_cross_split_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the current and validation-best protected gairaigo curves "
            "across calibration, holdout, and stitch-validation scalar rows."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--curve-sweep-json", type=Path, default=DEFAULT_CURVE_SWEEP_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        source_pair_json_path=_resolve_path(args.source_pair_json),
        curve_sweep_json_path=_resolve_path(args.curve_sweep_json),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        anchor_model=str(args.anchor_model),
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
    component_matrix_path: Path,
    source_pair_json_path: Path,
    curve_sweep_json_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    anchor_model: str,
    detail_limit: int,
) -> dict[str, object]:
    component_payload = np.load(component_matrix_path)
    component_view = ComponentView.from_npz(component_payload)
    matrix_view = MatrixView.from_npz(np.load(component_matrix_path))
    source_pair = _load_json(source_pair_json_path)
    curve_sweep = _load_json(curve_sweep_json_path)
    score_arrays, resolved_ids = score_arrays_for_models(
        view=component_view,
        parts=family_parts(component_view),
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=None,
        cap_candidate_id=None,
        stitch_candidate_id=None,
    )
    if anchor_model not in score_arrays:
        raise ValueError(f"Unknown anchor model: {anchor_model}")
    lookup = component_lookup(component_payload)
    scalar_rows = [
        row
        for row in source_pair.get("rows", ())
        if isinstance(row, Mapping) and row.get("target") == "scalar_vocab"
    ]
    current_spec = current_curve_spec()
    best_spec = spec_from_summary(
        _mapping(_mapping(_mapping(curve_sweep.get("summary")).get("best")).get("spec"))
    )
    datasets: dict[str, object] = {}
    for dataset_id in sorted({str(row.get("dataset_id") or "") for row in scalar_rows}):
        if not dataset_id:
            continue
        rows = rows_for_dataset(
            [row for row in scalar_rows if row.get("dataset_id") == dataset_id],
            lookup=lookup,
            matrix=matrix_view,
            anchor_scores=np.asarray(score_arrays[anchor_model], dtype=np.float32),
        )
        datasets[dataset_id] = dataset_report(
            rows,
            current_spec=current_spec,
            best_spec=best_spec,
            detail_limit=detail_limit,
        )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Check whether the validation-best gairaigo floor curve also helps "
                "calibration and holdout rows."
            ),
            "anchor_model": anchor_model,
            "promotion_status": (
                "Diagnostic only. A validation-selected curve must not be promoted "
                "unless cross-split evidence is acceptable."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "curve_sweep_json": _repo_or_home_path(curve_sweep_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "anchor_model": anchor_model,
            **resolved_ids,
        },
        "specs": {
            "current": spec_payload(current_spec),
            "validation_best": spec_payload(best_spec),
        },
        "summary": summary_for_datasets(datasets),
        "datasets": datasets,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "source_pair_json": source_pair_json_path,
                "curve_sweep_json": curve_sweep_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "gairaigo_curve_cross_split": Path(__file__),
                "gairaigo_curve_sweep": SCRIPT_DIR
                / "srs_learner_difficulty_gairaigo_curve_sweep_en_ja.py",
                "cleaned_lane_eval": SCRIPT_DIR
                / "srs_learner_difficulty_cleaned_lane_eval_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def rows_for_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
    matrix: MatrixView,
    anchor_scores: np.ndarray,
) -> list[dict[str, object]]:
    result = []
    for row in rows:
        value = _optional_float(row.get("expected_learner_difficulty"))
        index = row_component_index(row, lookup)
        if value is None or index is None:
            continue
        signals = signal_snapshot(index, matrix=matrix)
        observed = float(anchor_scores[index])
        result.append(
            {
                "dataset_id": row.get("dataset_id"),
                "label": row.get("label") or f"{row.get('lemma')}/{row.get('reading')}",
                "lemma": row.get("lemma"),
                "reading": row.get("reading"),
                "expected": _rounded(value),
                "expected_band": _difficulty_band(value),
                "anchor_observed": _rounded(observed),
                "anchor_abs_error": _rounded(abs(float(value) - observed)),
                "anchor_direction": "too_low" if observed < float(value) else "too_high",
                "candidate_state": matrix.candidate_states[index],
                "problem_class": matrix.problem_classes[index],
                "core_rank": _rounded(float(matrix.core_ranks[index])),
                "primary_pair_status": row.get("primary_pair_status"),
                "is_gairaigo": _float_signal(signals, "wtype_gairaigo_risk") >= 0.75,
                "signals": signals,
            }
        )
    return result


def dataset_report(
    rows: Sequence[Mapping[str, object]],
    *,
    current_spec: CurveSpec,
    best_spec: CurveSpec,
    detail_limit: int,
) -> dict[str, object]:
    current_rows = adjusted_rows_for_spec(rows, current_spec)
    best_rows = adjusted_rows_for_spec(rows, best_spec)
    gairaigo_rows = [row for row in rows if row.get("is_gairaigo")]
    return {
        "row_count": len(rows),
        "gairaigo_count": len(gairaigo_rows),
        "anchor": metrics_for_rows(anchor_as_adjusted(rows)),
        "current_curve": curve_result(current_rows, detail_limit=detail_limit),
        "validation_best_curve": curve_result(best_rows, detail_limit=detail_limit),
        "best_vs_current": compare_curve_results(
            curve_result(best_rows, detail_limit=detail_limit),
            curve_result(current_rows, detail_limit=detail_limit),
        ),
    }


def curve_result(rows: Sequence[Mapping[str, object]], *, detail_limit: int) -> dict[str, object]:
    gairaigo_rows = [row for row in rows if row.get("is_gairaigo")]
    changed_rows = [row for row in rows if row.get("changed")]
    changed_gairaigo = [row for row in gairaigo_rows if row.get("changed")]
    regressions = [
        row
        for row in changed_rows
        if float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    success_regressions = [
        row
        for row in gairaigo_rows
        if float(row.get("anchor_abs_error") or 0.0) <= 0.08
        and float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    return {
        "metrics": {
            "all_rows": metrics_for_rows(rows),
            "gairaigo_rows": metrics_for_rows(gairaigo_rows),
            "changed_rows": metrics_for_rows(changed_rows),
        },
        "counts": {
            "changed_rows": len(changed_rows),
            "changed_gairaigo_rows": len(changed_gairaigo),
            "changed_regressions": len(regressions),
            "success_regressions": len(success_regressions),
        },
        "changed_gairaigo_rows": sorted(
            changed_gairaigo,
            key=lambda row: float(row.get("anchor_abs_error") or 0.0),
            reverse=True,
        )[:detail_limit],
        "regression_rows": sorted(
            regressions,
            key=lambda row: (
                float(row.get("adjusted_abs_error") or 0.0)
                - float(row.get("anchor_abs_error") or 0.0)
            ),
            reverse=True,
        )[:detail_limit],
    }


def compare_curve_results(
    best: Mapping[str, object],
    current: Mapping[str, object],
) -> dict[str, object]:
    return {
        "all_mae_reduction_delta": _rounded(
            curve_delta(best, "all_rows", "mae_reduction")
            - curve_delta(current, "all_rows", "mae_reduction")
        ),
        "gairaigo_mae_reduction_delta": _rounded(
            curve_delta(best, "gairaigo_rows", "mae_reduction")
            - curve_delta(current, "gairaigo_rows", "mae_reduction")
        ),
        "gairaigo_pairwise_delta_delta": _rounded(
            curve_delta(best, "gairaigo_rows", "pairwise_delta")
            - curve_delta(current, "gairaigo_rows", "pairwise_delta")
        ),
        "regression_delta": int(_mapping(best.get("counts")).get("changed_regressions") or 0)
        - int(_mapping(current.get("counts")).get("changed_regressions") or 0),
    }


def curve_delta(curve: Mapping[str, object], scope: str, key: str) -> float:
    metrics = _mapping(_mapping(curve.get("metrics")).get(scope))
    return float(_mapping(metrics.get("delta")).get(key) or 0.0)


def anchor_as_adjusted(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    result = []
    for row in rows:
        result.append(
            dict(row)
            | {
                "adjusted_observed": row.get("anchor_observed"),
                "adjusted_abs_error": row.get("anchor_abs_error"),
                "adjusted_band": _difficulty_band(row.get("anchor_observed")),
                "changed": False,
                "policy_floor": None,
                "policy_reason": "anchor",
            }
        )
    return result


def signal_snapshot(index: int, *, matrix: MatrixView) -> dict[str, object]:
    component_index = matrix.component_index()
    snapshot: dict[str, object] = {}
    for signal in ROW_SIGNALS:
        column = component_index.get(signal)
        snapshot[signal] = (
            None if column is None else _rounded(float(matrix.component_values[index, column]))
        )
    return snapshot


def summary_for_datasets(datasets: Mapping[str, object]) -> dict[str, object]:
    by_dataset = {}
    for dataset_id, dataset in datasets.items():
        parsed = _mapping(dataset)
        current = _mapping(parsed.get("current_curve"))
        best = _mapping(parsed.get("validation_best_curve"))
        gairaigo_count = int(parsed.get("gairaigo_count") or 0)
        by_dataset[dataset_id] = {
            "row_count": parsed.get("row_count"),
            "gairaigo_count": gairaigo_count,
            "has_gairaigo_evidence": gairaigo_count > 0,
            "current_all_mae_reduction": curve_delta(current, "all_rows", "mae_reduction"),
            "best_all_mae_reduction": curve_delta(best, "all_rows", "mae_reduction"),
            "current_gairaigo_mae_reduction": curve_delta(
                current, "gairaigo_rows", "mae_reduction"
            ),
            "best_gairaigo_mae_reduction": curve_delta(best, "gairaigo_rows", "mae_reduction"),
            "best_changed_regressions": _mapping(best.get("counts")).get("changed_regressions"),
            "best_success_regressions": _mapping(best.get("counts")).get("success_regressions"),
        }
    return {
        "by_dataset": by_dataset,
        "interpretation": interpretation(by_dataset),
    }


def interpretation(by_dataset: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    holdout = _mapping(by_dataset.get("holdout"))
    validation = _mapping(by_dataset.get("stitch_validation"))
    calibration = _mapping(by_dataset.get("calibration"))
    holdout_has_gairaigo = bool(holdout.get("has_gairaigo_evidence"))
    validation_has_gairaigo = bool(validation.get("has_gairaigo_evidence"))
    calibration_has_gairaigo = bool(calibration.get("has_gairaigo_evidence"))
    holdout_best_ok = None
    if holdout_has_gairaigo:
        holdout_best_ok = (
            float(holdout.get("best_gairaigo_mae_reduction") or 0.0) >= 0.0
            and int(holdout.get("best_changed_regressions") or 0) == 0
        )
    missing_evidence = [
        dataset_id
        for dataset_id in ("calibration", "holdout")
        if not bool(_mapping(by_dataset.get(dataset_id)).get("has_gairaigo_evidence"))
    ]
    return {
        "validation_best_improves_validation_gairaigo": (
            None
            if not validation_has_gairaigo
            else float(validation.get("best_gairaigo_mae_reduction") or 0.0)
            > float(validation.get("current_gairaigo_mae_reduction") or 0.0)
        ),
        "validation_best_improves_calibration_gairaigo": (
            None
            if not calibration_has_gairaigo
            else float(calibration.get("best_gairaigo_mae_reduction") or 0.0)
            >= float(calibration.get("current_gairaigo_mae_reduction") or 0.0)
        ),
        "validation_best_holdout_nonnegative": holdout_best_ok,
        "missing_cross_split_gairaigo_evidence": missing_evidence,
        "promotion_readiness": (
            "not_promotable_no_holdout_gairaigo_coverage"
            if not holdout_has_gairaigo
            else (
                "not_promotable"
                if not holdout_best_ok
                else "needs_qualitative_holdout_changed_row_review"
            )
        ),
    }


def spec_payload(spec: CurveSpec) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "tail_lower": spec.tail_lower,
        "tail_shape": spec.tail_shape,
        "ranked_base": spec.ranked_base,
        "ranked_slope": spec.ranked_slope,
        "ranked_cap": spec.ranked_cap,
        "unranked_floor": spec.unranked_floor,
        "unranked_low_domain_floor": spec.unranked_low_domain_floor,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    specs = _mapping(report.get("specs"))
    lines = [
        "# en-ja Gairaigo Curve Cross-Split Evaluation",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        f"Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        "",
        "## Specs",
        "",
        f"- Current: `{_escape(_mapping(specs.get('current')).get('spec_id'))}`",
        f"- Validation best: `{_escape(_mapping(specs.get('validation_best')).get('spec_id'))}`",
        "",
        "## Dataset Summary",
        "",
    ]
    lines.extend(summary_table(_mapping(summary.get("by_dataset"))))
    lines.extend(["", "## Interpretation", ""])
    for key, value in _mapping(summary.get("interpretation")).items():
        lines.append(f"- `{_escape(key)}`: `{_escape(display_value(value))}`")
    for dataset_id, dataset in _mapping(report.get("datasets")).items():
        lines.extend(["", f"## `{_escape(dataset_id)}`", ""])
        lines.extend(dataset_tables(_mapping(dataset)))
    return "\n".join(lines).rstrip() + "\n"


def summary_table(rows: Mapping[str, object]) -> list[str]:
    lines = [
        "| Dataset | Rows | Gairaigo | Current all ΔMAE | Best all ΔMAE | Current gairaigo ΔMAE | Best gairaigo ΔMAE | Best regressions |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_id, row in rows.items():
        parsed = _mapping(row)
        lines.append(
            f"| `{_escape(dataset_id)}` | "
            f"{_escape(parsed.get('row_count'))} | "
            f"{_escape(parsed.get('gairaigo_count'))} | "
            f"{_escape(parsed.get('current_all_mae_reduction'))} | "
            f"{_escape(parsed.get('best_all_mae_reduction'))} | "
            f"{_escape(parsed.get('current_gairaigo_mae_reduction'))} | "
            f"{_escape(parsed.get('best_gairaigo_mae_reduction'))} | "
            f"{_escape(parsed.get('best_changed_regressions'))} |"
        )
    return lines


def dataset_tables(dataset: Mapping[str, object]) -> list[str]:
    current = _mapping(dataset.get("current_curve"))
    best = _mapping(dataset.get("validation_best_curve"))
    lines = [
        "### Metric Comparison",
        "",
        "| Curve | Changed | Regressions | Success regressions | All ΔMAE | Gairaigo ΔMAE | Gairaigo pairwise Δ |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, curve in (("current", current), ("validation_best", best)):
        counts = _mapping(curve.get("counts"))
        lines.append(
            f"| `{label}` | "
            f"{_escape(counts.get('changed_rows'))} | "
            f"{_escape(counts.get('changed_regressions'))} | "
            f"{_escape(counts.get('success_regressions'))} | "
            f"{_escape(curve_delta(curve, 'all_rows', 'mae_reduction'))} | "
            f"{_escape(curve_delta(curve, 'gairaigo_rows', 'mae_reduction'))} | "
            f"{_escape(curve_delta(curve, 'gairaigo_rows', 'pairwise_delta'))} |"
        )
    lines.extend(["", "### Validation-Best Changed Gairaigo Rows", ""])
    lines.extend(row_table(_rows(best.get("changed_gairaigo_rows"))))
    lines.extend(["", "### Validation-Best Regression Rows", ""])
    lines.extend(row_table(_rows(best.get("regression_rows"))))
    return lines


def row_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | Expected | Anchor | Adjusted | Anchor Err | Adj Err | Freq | Rank | Reason | Floor |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        lines.append(
            f"| {_escape(row.get('label'))} | "
            f"{_escape(row.get('expected'))} | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('adjusted_observed'))} | "
            f"{_escape(row.get('anchor_abs_error'))} | "
            f"{_escape(row.get('adjusted_abs_error'))} | "
            f"{_escape(signals.get('frequency'))} | "
            f"{_escape(row.get('core_rank'))} | "
            f"`{_escape(row.get('policy_reason'))}` | "
            f"{_escape(row.get('policy_floor'))} |"
        )
    return lines


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = _optional_float(signals.get(signal))
    return 0.0 if value is None else float(value)


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def display_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
