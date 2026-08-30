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

from srs_learner_difficulty_cleaned_lane_eval_en_ja import (  # noqa: E402
    DEFAULT_SOURCE_PAIR_JSON,
    component_lookup,
)
from srs_learner_difficulty_constituent_transparency_audit_en_ja import (  # noqa: E402
    ANCHOR_MODEL,
    DATASET_ORDER,
    DEFAULT_CAP_REPORT,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    MatrixSupport,
    adjusted_payload,
    build_constituent_inventory,
    candidate_report,
    candidate_rank_key,
    candidate_summary,
    changed_rows_by_dataset,
    curve_result,
    full_matrix_rows,
    labeled_passes_guardrails,
    policy_matches,
    rows_with_transparency,
    spec_from_payload,
    transparency_specs,
)
from srs_learner_difficulty_constituent_transparency_label_eval_en_ja import (  # noqa: E402
    DEFAULT_LABELS_JSON,
    OPACITY_GATE_SIGNALS,
    entry_label,
    opacity_gate_search_report,
    rows_with_source_features,
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
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    family_parts,
)
from srs_learner_difficulty_stitch_validation_eval_en_ja import (  # noqa: E402
    score_arrays_for_models,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_opacity_gate_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_opacity_gate_eval_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate source-backed opacity gates for the en-ja constituent "
            "transparency difficulty sidecar."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--leaderboard-limit", type=int, default=12)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        source_pair_json_path=_resolve_path(args.source_pair_json),
        labels_json_path=_resolve_path(args.labels_json),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        anchor_model=str(args.anchor_model),
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
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
    labels_json_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    anchor_model: str,
    leaderboard_limit: int,
    detail_limit: int,
) -> dict[str, object]:
    raw_component = np.load(component_matrix_path)
    matrix = MatrixSupport.from_npz(raw_component)
    component_view = ComponentView.from_npz(raw_component)
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
    anchor_scores = np.asarray(score_arrays[anchor_model], dtype=np.float32)
    inventory = build_constituent_inventory(matrix)
    source_pair = _load_json(source_pair_json_path)
    lookup = component_lookup(raw_component)
    scalar_rows = [
        row
        for row in source_pair.get("rows", ())
        if isinstance(row, Mapping) and row.get("target") == "scalar_vocab"
    ]
    labeled_rows = rows_with_transparency(
        scalar_rows,
        lookup=lookup,
        matrix=matrix,
        inventory=inventory,
        anchor_scores=anchor_scores,
    )
    full_rows = full_matrix_rows(
        matrix=matrix,
        inventory=inventory,
        anchor_scores=anchor_scores,
    )
    base_candidates = [
        candidate_report(labeled_rows, full_rows, spec) for spec in transparency_specs()
    ]
    base_ranked = sorted(base_candidates, key=candidate_rank_key, reverse=True)
    base_best = next(
        (row for row in base_ranked if row.get("passes_guardrails")),
        base_ranked[0],
    )
    base_spec = spec_from_payload(_mapping(base_best.get("spec")))
    labels_payload = _load_json(labels_json_path)
    review_label_rows = [
        row for row in labels_payload.get("labels", ()) if isinstance(row, Mapping)
    ]
    gate_search = opacity_gate_search_report(
        rows=review_label_rows,
        component_matrix_path=component_matrix_path,
    )
    gate_specs = unique_gate_specs(gate_search)
    gate_candidates = [
        gated_candidate_report(
            labeled_rows=labeled_rows,
            full_rows=full_rows,
            component_matrix_path=component_matrix_path,
            base_spec=base_spec,
            gate_signals=tuple(gate.get("signals", ())),
            review_gate=gate,
            detail_limit=detail_limit,
        )
        for gate in gate_specs
    ]
    ranked_gates = sorted(gate_candidates, key=gated_rank_key, reverse=True)
    best_gate = ranked_gates[0] if ranked_gates else {}
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "labels_json": _repo_or_home_path(labels_json_path),
            "anchor_model": anchor_model,
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "v1_candidate_id": resolved_ids.get("v1"),
            "cap_candidate_id": resolved_ids.get("cap"),
            "stitch_candidate_id": resolved_ids.get("stitch"),
        },
        "method": {
            "purpose": (
                "Test whether reviewed-set opacity gates can make the guarded "
                "constituent-transparency sidecar safer without touching runtime."
            ),
            "base_candidate_id": base_best.get("candidate_id"),
            "opacity_gate_signals": list(OPACITY_GATE_SIGNALS),
        },
        "base_candidate": base_best,
        "review_gate_search": gate_search,
        "gated_leaderboard": ranked_gates[:leaderboard_limit],
        "summary": summary_payload(base_best=base_best, best_gate=best_gate),
    }


def unique_gate_specs(gate_search: Mapping[str, object]) -> list[Mapping[str, object]]:
    seen = set()
    output = []
    for gate in _rows(gate_search.get("top_gates")):
        signals = tuple(str(signal) for signal in _rows(gate.get("signals")))
        if not signals or signals in seen:
            continue
        seen.add(signals)
        output.append(gate)
    return output


def gated_candidate_report(
    *,
    labeled_rows: Sequence[Mapping[str, object]],
    full_rows: Sequence[Mapping[str, object]],
    component_matrix_path: Path,
    base_spec: object,
    gate_signals: tuple[str, ...],
    review_gate: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    labeled_with_features = rows_with_source_features(
        rows=labeled_rows,
        component_matrix_path=component_matrix_path,
        signals=gate_signals,
    )
    full_with_features = rows_with_source_features(
        rows=full_rows,
        component_matrix_path=component_matrix_path,
        signals=gate_signals,
    )
    adjusted = [
        dict(row) | gated_adjusted_payload(row, base_spec=base_spec, gate_signals=gate_signals)
        for row in labeled_with_features
    ]
    datasets = {
        dataset_id: curve_result([row for row in adjusted if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }
    full_counts = gated_full_matrix_counts(
        full_with_features,
        base_spec=base_spec,
        gate_signals=gate_signals,
    )
    labeled_passes = labeled_passes_guardrails(datasets)
    candidate_id = "opacity_gate__" + "__".join(gate_signals)
    return {
        "candidate_id": candidate_id,
        "gate_signals": list(gate_signals),
        "review_gate": review_gate,
        "labeled_passes_guardrails": labeled_passes,
        "passes_guardrails": labeled_passes,
        "datasets": datasets,
        "full_matrix": full_counts,
        "summary": candidate_summary(datasets, full_counts),
        "changed_rows": changed_rows_by_dataset(adjusted, detail_limit=detail_limit),
        "full_matrix_review_pack": gated_full_matrix_review_pack(
            full_with_features,
            base_spec=base_spec,
            gate_signals=gate_signals,
            detail_limit=detail_limit,
        ),
    }


def gated_adjusted_payload(
    row: Mapping[str, object],
    *,
    base_spec: object,
    gate_signals: Sequence[str],
) -> dict[str, object]:
    if gated_policy_matches(row, base_spec=base_spec, gate_signals=gate_signals):
        return adjusted_payload(row, base_spec)
    observed = float(row.get("anchor_observed") or 0.0)
    payload = {
        "adjusted_observed": _rounded(observed),
        "adjusted_band": _difficulty_band(observed),
        "changed": False,
        "policy_ceiling": None,
        "policy_reason": (
            "constituent_opacity_gate_blocked" if policy_matches(row, base_spec) else "not_matched"
        ),
    }
    expected = _optional_float(row.get("expected"))
    if expected is not None:
        payload["adjusted_abs_error"] = _rounded(abs(expected - observed))
    return payload


def gated_policy_matches(
    row: Mapping[str, object],
    *,
    base_spec: object,
    gate_signals: Sequence[str],
) -> bool:
    if not policy_matches(row, base_spec):
        return False
    features = _mapping(row.get("source_features"))
    return not any(bool(features.get(signal)) for signal in gate_signals)


def gated_full_matrix_counts(
    rows: Sequence[Mapping[str, object]],
    *,
    base_spec: object,
    gate_signals: Sequence[str],
) -> dict[str, object]:
    matched = 0
    changed = 0
    gated = 0
    for row in rows:
        if policy_matches(row, base_spec) and opacity_gate_matches(row, gate_signals):
            gated += 1
        if gated_policy_matches(row, base_spec=base_spec, gate_signals=gate_signals):
            matched += 1
            if float(row.get("anchor_observed") or 0.0) > base_spec.ceiling:
                changed += 1
    return {
        "would_match_count": matched,
        "would_change_count": changed,
        "opacity_gated_count": gated,
    }


def gated_full_matrix_review_pack(
    rows: Sequence[Mapping[str, object]],
    *,
    base_spec: object,
    gate_signals: Sequence[str],
    detail_limit: int,
) -> dict[str, object]:
    selected = [
        gated_review_row(row, gate_signals, reason="opacity_gate_selected")
        for row in rows
        if gated_policy_matches(row, base_spec=base_spec, gate_signals=gate_signals)
        and float(row.get("anchor_observed") or 0.0) > base_spec.ceiling
    ]
    gated = [
        gated_review_row(row, gate_signals, reason="opacity_gate_blocked")
        for row in rows
        if policy_matches(row, base_spec)
        and opacity_gate_matches(row, gate_signals)
        and float(row.get("anchor_observed") or 0.0) > base_spec.ceiling
    ]
    return {
        "selected_examples": selected[:detail_limit],
        "gated_examples": gated[:detail_limit],
        "selected_count": len(selected),
        "gated_count": len(gated),
    }


def gated_review_row(
    row: Mapping[str, object],
    gate_signals: Sequence[str],
    *,
    reason: str,
) -> dict[str, object]:
    features = _mapping(row.get("source_features"))
    return {
        "label": row.get("label"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "anchor_observed": row.get("anchor_observed"),
        "review_reason": reason,
        "matched_gate_signals": [signal for signal in gate_signals if bool(features.get(signal))],
        "entry": entry_label(row),
    }


def opacity_gate_matches(
    row: Mapping[str, object],
    gate_signals: Sequence[str],
) -> bool:
    features = _mapping(row.get("source_features"))
    return any(bool(features.get(signal)) for signal in gate_signals)


def gated_rank_key(candidate: Mapping[str, object]) -> tuple[float, ...]:
    review = _mapping(candidate.get("review_gate"))
    summary = _mapping(candidate.get("summary"))
    validation = _mapping(summary.get("stitch_validation"))
    holdout = _mapping(summary.get("holdout"))
    full_matrix = _mapping(summary.get("full_matrix"))
    return (
        1.0 if candidate.get("passes_guardrails") else 0.0,
        float(review.get("precision") or 0.0),
        float(review.get("f1") or 0.0),
        float(review.get("recall") or 0.0),
        float(validation.get("transparent_failure_mae_reduction") or 0.0),
        float(validation.get("all_mae_reduction") or 0.0),
        float(holdout.get("all_mae_reduction") or 0.0),
        -float(full_matrix.get("would_change_count") or 0.0),
    )


def summary_payload(
    *,
    base_best: Mapping[str, object],
    best_gate: Mapping[str, object],
) -> dict[str, object]:
    base_summary = _mapping(base_best.get("summary"))
    gated_summary = _mapping(best_gate.get("summary"))
    review = _mapping(best_gate.get("review_gate"))
    return {
        "base_candidate_id": base_best.get("candidate_id"),
        "base_validation_transparent_failure_delta": _mapping(
            base_summary.get("stitch_validation")
        ).get("transparent_failure_mae_reduction"),
        "base_validation_all_delta": _mapping(base_summary.get("stitch_validation")).get(
            "all_mae_reduction"
        ),
        "base_holdout_all_delta": _mapping(base_summary.get("holdout")).get("all_mae_reduction"),
        "base_full_matrix_would_change": _mapping(base_summary.get("full_matrix")).get(
            "would_change_count"
        ),
        "best_gate_candidate_id": best_gate.get("candidate_id"),
        "best_gate_review_precision": review.get("precision"),
        "best_gate_review_recall": review.get("recall"),
        "best_gate_review_f1": review.get("f1"),
        "best_gate_review_lost_accepted": review.get("lost_accepted"),
        "best_gate_review_remaining_non_accepts": review.get("remaining_non_accepts"),
        "best_gate_validation_transparent_failure_delta": _mapping(
            gated_summary.get("stitch_validation")
        ).get("transparent_failure_mae_reduction"),
        "best_gate_validation_all_delta": _mapping(gated_summary.get("stitch_validation")).get(
            "all_mae_reduction"
        ),
        "best_gate_holdout_all_delta": _mapping(gated_summary.get("holdout")).get(
            "all_mae_reduction"
        ),
        "best_gate_full_matrix_would_change": _mapping(gated_summary.get("full_matrix")).get(
            "would_change_count"
        ),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# SRS Learner Difficulty Constituent Transparency Opacity Gate Eval (en-ja)",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in (
        "base_validation_transparent_failure_delta",
        "base_validation_all_delta",
        "base_holdout_all_delta",
        "base_full_matrix_would_change",
        "best_gate_review_precision",
        "best_gate_review_recall",
        "best_gate_review_f1",
        "best_gate_validation_transparent_failure_delta",
        "best_gate_validation_all_delta",
        "best_gate_holdout_all_delta",
        "best_gate_full_matrix_would_change",
    ):
        lines.append(f"| `{key}` | {_escape(summary.get(key))} |")
    lines.extend(
        [
            "",
            "Best gate lost accepted review rows:",
            "",
            ", ".join(str(value) for value in _rows(summary.get("best_gate_review_lost_accepted")))
            or "None",
            "",
            "Best gate remaining non-accepted review rows:",
            "",
            ", ".join(
                str(value) for value in _rows(summary.get("best_gate_review_remaining_non_accepts"))
            )
            or "None",
            "",
            "## Gated Leaderboard",
            "",
            "| Rank | Review precision | Review recall | Validation transparent delta | Validation all delta | Holdout all delta | Full changes | Gate signals | Lost accepted |",
            "|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for rank, candidate in enumerate(_rows(report.get("gated_leaderboard")), start=1):
        review = _mapping(candidate.get("review_gate"))
        summary_row = _mapping(candidate.get("summary"))
        validation = _mapping(summary_row.get("stitch_validation"))
        holdout = _mapping(summary_row.get("holdout"))
        full = _mapping(summary_row.get("full_matrix"))
        lines.append(
            "| "
            f"{rank} | "
            f"{_escape(review.get('precision'))} | "
            f"{_escape(review.get('recall'))} | "
            f"{_escape(validation.get('transparent_failure_mae_reduction'))} | "
            f"{_escape(validation.get('all_mae_reduction'))} | "
            f"{_escape(holdout.get('all_mae_reduction'))} | "
            f"{_escape(full.get('would_change_count'))} | "
            f"{_escape(', '.join(str(value) for value in _rows(candidate.get('gate_signals'))))} | "
            f"{_escape(', '.join(str(value) for value in _rows(review.get('lost_accepted'))))} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The opacity gate improves reviewed precision by holding many risky rows out of automatic downshift.",
            "- The best reviewed-set gate is not free: it loses accepted rows, including `黒百合/くろゆり`.",
            "- Because `黒百合/くろゆり` is one of the labeled validation fixes, gate promotion should depend on the labeled metric comparison, not only review precision.",
            "- This remains a sidecar search result, not runtime behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _rows(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


if __name__ == "__main__":
    raise SystemExit(main())
