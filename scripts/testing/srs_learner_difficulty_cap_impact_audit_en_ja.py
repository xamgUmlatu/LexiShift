#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_holdout_eval_en_ja import (  # noqa: E402
    DEFAULT_REVIEW_MARKDOWN,
    holdout_context_from_rows,
    parse_holdout_review_markdown,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    BEGINNER_BROAD_MAX,
    BEGINNER_BROAD_OBSERVED_CEILING,
    BEGINNER_CORE_MAX,
    BEGINNER_CORE_OBSERVED_CEILING,
    HIGH_TAIL_MIN,
    HIGH_TAIL_OBSERVED_FLOOR,
    UPPER_TAIL_MIN,
    UPPER_TAIL_OBSERVED_FLOOR,
    _difficulty_metrics,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
    generate_candidates,
    raw_scores_for_candidate,
)


PAIR = "en-ja"
DEFAULT_V1_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_en_ja_latest.json"
)
DEFAULT_CAP_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_ordinary_refine_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_cap_impact_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_cap_impact_audit_en_ja_latest.md"
)
SIGNAL_KEYS = (
    "ordinary_gate_max",
    "ordinary_gate_mean",
    "ordinary_gate_frequency",
    "ordinary_gate_priority",
    "ordinary_gate_freq_priority",
    "ordinary_gate_pedagogical",
    "reading_inheritance_risk",
    "tail_floor_guard",
    "burden_mean",
    "ped_min",
    "native_mean",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit where the source-arbitration ordinary-cap model helps or "
            "hurts relative to the v1 sidecar model."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        review_markdown=_resolve_path(args.review_markdown),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        v1_candidate_id=args.v1_candidate_id,
        cap_candidate_id=args.cap_candidate_id,
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
    calibration_matrix_path: Path,
    review_markdown: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    detail_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    holdout_rows = parse_holdout_review_markdown(review_markdown)
    holdout_context = holdout_context_from_rows(holdout_rows, component)
    v1_payload = _load_json(v1_report_path)
    cap_payload = _load_json(cap_report_path)
    resolved_v1_id = v1_candidate_id or _best_holdout_candidate_id(v1_payload)
    resolved_cap_id = cap_candidate_id or _best_holdout_candidate_id(cap_payload)
    v1_candidate = _candidate_by_id(resolved_v1_id)
    cap_candidate = _candidate_by_id(resolved_cap_id)
    v1_scores = _normalized_scores(v1_candidate, view, parts)
    cap_scores = _normalized_scores(cap_candidate, view, parts)
    cap_pre_raw = raw_scores_for_candidate(
        replace(
            cap_candidate,
            ordinary_cap=0.0,
            ordinary_cap_mode="none",
            ordinary_cap_strength=1.0,
        ),
        view,
        parts=parts,
    )
    cap_ceiling = ordinary_cap_ceiling(cap_candidate, parts)
    rows = row_impacts(
        context=holdout_context,
        component=component,
        view=view,
        parts=parts,
        v1_scores=v1_scores,
        cap_scores=cap_scores,
        cap_pre_raw=cap_pre_raw,
        cap_ceiling=cap_ceiling,
    )
    v1_metrics = metrics_for_context(v1_scores, holdout_context)
    cap_metrics = metrics_for_context(cap_scores, holdout_context)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Explain where the ordinary-cap candidate improves or degrades "
                "reviewed holdout labels relative to the v1 sidecar candidate."
            ),
            "comparison": "best-holdout v1 vs best-holdout ordinary-cap candidate",
            "segments": {
                "beginner_core_expected_max": BEGINNER_CORE_MAX,
                "beginner_core_observed_ceiling": BEGINNER_CORE_OBSERVED_CEILING,
                "beginner_broad_expected_max": BEGINNER_BROAD_MAX,
                "beginner_broad_observed_ceiling": BEGINNER_BROAD_OBSERVED_CEILING,
                "upper_tail_expected_min": UPPER_TAIL_MIN,
                "upper_tail_observed_floor": UPPER_TAIL_OBSERVED_FLOOR,
                "high_tail_expected_min": HIGH_TAIL_MIN,
                "high_tail_observed_floor": HIGH_TAIL_OBSERVED_FLOOR,
            },
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "review_markdown": _repo_or_home_path(review_markdown),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "v1_candidate_id": resolved_v1_id,
            "cap_candidate_id": resolved_cap_id,
            "holdout_numeric_count": len(rows),
        },
        "summary": {
            "v1_holdout": {
                "scores": v1_metrics["scores"],
                "metrics": _summary_metrics(v1_metrics),
            },
            "cap_holdout": {
                "scores": cap_metrics["scores"],
                "metrics": _summary_metrics(cap_metrics),
            },
            "score_deltas_cap_minus_v1": _score_deltas(
                cap_metrics["scores"],
                v1_metrics["scores"],
            ),
            "impact_counts": impact_counts(rows),
            "segment_summary": segment_summary(rows),
            "cap_active_summary": cap_active_summary(rows),
        },
        "top_helped": sorted(rows, key=lambda row: float(row["error_delta"]))[:detail_limit],
        "top_hurt": sorted(rows, key=lambda row: float(row["error_delta"]), reverse=True)[
            :detail_limit
        ],
        "beginner_core_hurts": [
            row
            for row in sorted(rows, key=lambda row: float(row["error_delta"]), reverse=True)
            if row["expected_segment"] == "beginner_core" and row["verdict"] == "hurt"
        ][:detail_limit],
        "cap_active_rows": [row for row in rows if row["cap_active"]][:detail_limit],
        "rows": rows,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "review_markdown": review_markdown,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
            },
            code_paths={
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "holdout_eval": SCRIPT_DIR / "srs_learner_difficulty_holdout_eval_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def _normalized_scores(
    candidate: object, view: ComponentView, parts: Mapping[str, object]
) -> object:
    raw = raw_scores_for_candidate(candidate, view, parts=parts)
    return _target_curve_normalize(raw, target_positions=view.target_positions)


def metrics_for_context(normalized: object, context: Mapping[str, object]) -> dict[str, object]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    valid = indices >= 0
    observed[valid] = np.asarray(normalized, dtype=np.float32)[indices[valid]]
    return _difficulty_metrics(
        expected_values=context["expected_values"],
        observed_values=observed,
        expected_bands=context["expected_bands"],
        expected_candidate_states=context.get("expected_candidate_states"),
        observed_candidate_states=context.get("observed_candidate_states"),
        labels=context["labels"],
    )


def ordinary_cap_ceiling(candidate: object, parts: Mapping[str, object]) -> object:
    if getattr(candidate, "ordinary_cap", 0.0) <= 0.0:
        return np.ones_like(np.asarray(parts["ordinary_gate_max"], dtype=np.float32))
    gate_key = f"ordinary_gate_{candidate.ordinary_gate_mode}"
    ordinary = np.asarray(parts[gate_key], dtype=np.float32)
    reading = np.asarray(parts["reading_inheritance_risk"], dtype=np.float32)
    tail = np.asarray(parts["tail_floor_guard"], dtype=np.float32)
    exception = np.maximum(reading, tail)
    gate = ordinary * np.clip(1.0 - exception, 0.0, 1.0)
    return (
        float(candidate.ordinary_cap) + (1.0 - float(candidate.ordinary_cap)) * (1.0 - gate)
    ).astype(np.float32)


def row_impacts(
    *,
    context: Mapping[str, object],
    component: object,
    view: ComponentView,
    parts: Mapping[str, object],
    v1_scores: object,
    cap_scores: object,
    cap_pre_raw: object,
    cap_ceiling: object,
) -> list[dict[str, object]]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    v1 = np.asarray(v1_scores, dtype=np.float32)
    cap = np.asarray(cap_scores, dtype=np.float32)
    pre_raw = np.asarray(cap_pre_raw, dtype=np.float32)
    ceiling = np.asarray(cap_ceiling, dtype=np.float32)
    rows: list[dict[str, object]] = []
    for offset, component_index in enumerate(indices):
        if component_index < 0 or not np.isfinite(expected[offset]):
            continue
        index = int(component_index)
        expected_value = float(expected[offset])
        v1_value = float(v1[index])
        cap_value = float(cap[index])
        v1_error = abs(v1_value - expected_value)
        cap_error = abs(cap_value - expected_value)
        error_delta = cap_error - v1_error
        signal_values = {
            key: _rounded(float(np.asarray(parts[key], dtype=np.float32)[index]))
            for key in SIGNAL_KEYS
            if key in parts
        }
        row = {
            "label": labels[offset],
            "lemma": str(component["lemmas"][index]),
            "reading": str(component["readings"][index]),
            "candidate_identity_key": str(view.identities[index]),
            "expected": _rounded(expected_value),
            "expected_segment": expected_segment(expected_value),
            "v1_observed": _rounded(v1_value),
            "cap_observed": _rounded(cap_value),
            "cap_minus_v1": _rounded(cap_value - v1_value),
            "v1_abs_error": _rounded(v1_error),
            "cap_abs_error": _rounded(cap_error),
            "error_delta": _rounded(error_delta),
            "verdict": verdict(error_delta),
            "cap_active": bool(pre_raw[index] > ceiling[index] + 1e-6),
            "cap_pre_raw": _rounded(float(pre_raw[index])),
            "cap_ceiling": _rounded(float(ceiling[index])),
            "v1_beginner_core_pass": (
                bool(v1_value <= BEGINNER_CORE_OBSERVED_CEILING)
                if expected_value <= BEGINNER_CORE_MAX
                else None
            ),
            "cap_beginner_core_pass": (
                bool(cap_value <= BEGINNER_CORE_OBSERVED_CEILING)
                if expected_value <= BEGINNER_CORE_MAX
                else None
            ),
            "signals": signal_values,
        }
        rows.append(row)
    return rows


def expected_segment(value: float) -> str:
    if value <= BEGINNER_CORE_MAX:
        return "beginner_core"
    if value <= BEGINNER_BROAD_MAX:
        return "beginner_broad"
    if value >= HIGH_TAIL_MIN:
        return "high_tail"
    if value >= UPPER_TAIL_MIN:
        return "upper_tail"
    return "middle"


def verdict(error_delta: float) -> str:
    if error_delta < -1e-6:
        return "helped"
    if error_delta > 1e-6:
        return "hurt"
    return "neutral"


def impact_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {
        "helped": sum(1 for row in rows if row["verdict"] == "helped"),
        "hurt": sum(1 for row in rows if row["verdict"] == "hurt"),
        "neutral": sum(1 for row in rows if row["verdict"] == "neutral"),
        "cap_active": sum(1 for row in rows if row["cap_active"]),
    }


def segment_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["expected_segment"]), []).append(row)
    return {
        segment: group_summary(segment_rows) for segment, segment_rows in sorted(grouped.items())
    }


def cap_active_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "active": group_summary([row for row in rows if row["cap_active"]]),
        "inactive": group_summary([row for row in rows if not row["cap_active"]]),
    }


def group_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "count": 0,
            "helped": 0,
            "hurt": 0,
            "mean_error_delta": None,
            "mean_cap_minus_v1": None,
        }
    error_delta = [float(row["error_delta"]) for row in rows]
    cap_delta = [float(row["cap_minus_v1"]) for row in rows]
    return {
        "count": len(rows),
        "helped": sum(1 for row in rows if row["verdict"] == "helped"),
        "hurt": sum(1 for row in rows if row["verdict"] == "hurt"),
        "neutral": sum(1 for row in rows if row["verdict"] == "neutral"),
        "cap_active": sum(1 for row in rows if row["cap_active"]),
        "mean_error_delta": _rounded(float(np.mean(error_delta))),
        "mean_cap_minus_v1": _rounded(float(np.mean(cap_delta))),
    }


def _score_deltas(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> dict[str, object]:
    keys = sorted(set(left) | set(right))
    result = {}
    for key in keys:
        left_value = _optional_float(left.get(key))
        right_value = _optional_float(right.get(key))
        result[key] = _rounded(
            left_value - right_value if left_value is not None and right_value is not None else None
        )
    return result


def _best_holdout_candidate_id(payload: Mapping[str, object]) -> str:
    candidate_id = _mapping(_mapping(payload.get("summary")).get("best_holdout_balanced")).get(
        "candidate_id"
    )
    if not candidate_id:
        raise ValueError("Could not find summary.best_holdout_balanced.candidate_id")
    return str(candidate_id)


def _candidate_by_id(candidate_id: str) -> object:
    for family in ("v1", "v2", "ordinary_refine"):
        for candidate in generate_candidates(candidate_family=family):
            if candidate.candidate_id == candidate_id:
                return candidate
    raise ValueError(f"Candidate not found in known source-arbitration families: {candidate_id}")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Source-Arbitration Cap Impact Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Inputs",
        "",
        f"- v1 candidate: `{_escape(inputs.get('v1_candidate_id'))}`",
        f"- cap candidate: `{_escape(inputs.get('cap_candidate_id'))}`",
        f"- Holdout rows: `{_escape(inputs.get('holdout_numeric_count'))}`",
        "",
        "## Score Delta",
        "",
        "| Metric | v1 | cap | cap - v1 |",
        "| --- | ---: | ---: | ---: |",
    ]
    v1_scores = _mapping(_mapping(summary.get("v1_holdout")).get("scores"))
    cap_scores = _mapping(_mapping(summary.get("cap_holdout")).get("scores"))
    deltas = _mapping(summary.get("score_deltas_cap_minus_v1"))
    for key in (
        "balanced_score",
        "numeric_mae_score",
        "bucket_accuracy_score",
        "pairwise_order_score",
        "rank_correlation_score",
        "beginner_core_score",
        "beginner_broad_score",
        "upper_tail_score",
        "high_tail_score",
    ):
        lines.append(
            f"| `{_escape(key)}` | {_escape(v1_scores.get(key))} | "
            f"{_escape(cap_scores.get(key))} | {_escape(deltas.get(key))} |"
        )
    lines.extend(["", "## Impact Counts", ""])
    counts = _mapping(summary.get("impact_counts"))
    lines.extend(
        [
            f"- Helped rows: `{_escape(counts.get('helped'))}`",
            f"- Hurt rows: `{_escape(counts.get('hurt'))}`",
            f"- Neutral rows: `{_escape(counts.get('neutral'))}`",
            f"- Cap-active rows: `{_escape(counts.get('cap_active'))}`",
        ]
    )
    lines.extend(["", "## Segment Summary", ""])
    lines.extend(_summary_table(_mapping(summary.get("segment_summary"))))
    lines.extend(["", "## Cap Active Summary", ""])
    lines.extend(_summary_table(_mapping(summary.get("cap_active_summary"))))
    lines.extend(["", "## Top Helped", ""])
    lines.extend(_row_table(report.get("top_helped")))
    lines.extend(["", "## Top Hurt", ""])
    lines.extend(_row_table(report.get("top_hurt")))
    lines.extend(["", "## Beginner-Core Hurts", ""])
    lines.extend(_row_table(report.get("beginner_core_hurts")))
    return "\n".join(lines).rstrip() + "\n"


def _summary_table(value: Mapping[str, object]) -> list[str]:
    lines = [
        "| Group | Count | Helped | Hurt | Cap active | Mean error delta | Mean score delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group, raw in value.items():
        row = _mapping(raw)
        lines.append(
            f"| `{_escape(group)}` | {_escape(row.get('count'))} | "
            f"{_escape(row.get('helped'))} | {_escape(row.get('hurt'))} | "
            f"{_escape(row.get('cap_active'))} | {_escape(row.get('mean_error_delta'))} | "
            f"{_escape(row.get('mean_cap_minus_v1'))} |"
        )
    return lines


def _row_table(value: object) -> list[str]:
    rows = (
        [dict(row) for row in value if isinstance(row, Mapping)]
        if isinstance(value, Sequence)
        else []
    )
    lines = [
        "| Label | Segment | Expected | v1 | cap | score delta | error delta | cap active | Signals |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows[:20]:
        signals = _mapping(row.get("signals"))
        signal_text = ",".join(
            f"{key}={signals.get(key)}"
            for key in (
                "ordinary_gate_mean",
                "ordinary_gate_frequency",
                "ordinary_gate_priority",
                "ordinary_gate_pedagogical",
                "reading_inheritance_risk",
                "tail_floor_guard",
            )
            if key in signals
        )
        lines.append(
            f"| {_escape(row.get('label'))} | `{_escape(row.get('expected_segment'))}` | "
            f"{_escape(row.get('expected'))} | {_escape(row.get('v1_observed'))} | "
            f"{_escape(row.get('cap_observed'))} | {_escape(row.get('cap_minus_v1'))} | "
            f"{_escape(row.get('error_delta'))} | {_escape(row.get('cap_active'))} | "
            f"`{_escape(signal_text)}` |"
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
