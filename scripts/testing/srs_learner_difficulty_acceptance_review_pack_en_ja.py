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
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
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


DEFAULT_VALIDATION_EVAL_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitch_validation_eval_en_ja_latest.json"
)
DEFAULT_CLEANED_LANE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_cleaned_lane_eval_en_ja_latest.json"
)
DEFAULT_FAILURE_AUDIT_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_validation_failure_group_audit_en_ja_latest.json"
)
DEFAULT_BOUNDED_HYBRID_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_bounded_hybrid_stability_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_acceptance_review_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_acceptance_review_pack_en_ja_latest.md"
)
PREDICTED_BANDS = tuple(
    (round(start, 2), round(start + 0.1, 2)) for start in np.arange(0.0, 1.0, 0.1)
)
MODEL_IDS = ("v1", "ordinary_cap", "stitch")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a compact en-ja learner-difficulty acceptance review pack "
            "from existing latest model outputs."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--validation-eval-json", type=Path, default=DEFAULT_VALIDATION_EVAL_JSON)
    parser.add_argument("--cleaned-lane-json", type=Path, default=DEFAULT_CLEANED_LANE_JSON)
    parser.add_argument("--failure-audit-json", type=Path, default=DEFAULT_FAILURE_AUDIT_JSON)
    parser.add_argument("--bounded-hybrid-json", type=Path, default=DEFAULT_BOUNDED_HYBRID_JSON)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--stitch-candidate-id", default=None)
    parser.add_argument("--anchor-model", choices=MODEL_IDS, default="ordinary_cap")
    parser.add_argument("--sample-count", type=int, default=8)
    parser.add_argument("--detail-limit", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        validation_eval_json_path=_resolve_path(args.validation_eval_json),
        cleaned_lane_json_path=_resolve_path(args.cleaned_lane_json),
        failure_audit_json_path=_resolve_path(args.failure_audit_json),
        bounded_hybrid_json_path=_resolve_path(args.bounded_hybrid_json),
        v1_candidate_id=args.v1_candidate_id,
        cap_candidate_id=args.cap_candidate_id,
        stitch_candidate_id=args.stitch_candidate_id,
        anchor_model=str(args.anchor_model),
        sample_count=max(1, int(args.sample_count)),
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
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    validation_eval_json_path: Path,
    cleaned_lane_json_path: Path,
    failure_audit_json_path: Path,
    bounded_hybrid_json_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    stitch_candidate_id: str | None,
    anchor_model: str,
    sample_count: int,
    detail_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    score_arrays, resolved_ids = score_arrays_for_models(
        view=view,
        parts=parts,
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=v1_candidate_id,
        cap_candidate_id=cap_candidate_id,
        stitch_candidate_id=stitch_candidate_id,
    )
    validation_eval = _load_json(validation_eval_json_path)
    cleaned_lane = _load_json(cleaned_lane_json_path)
    failure_audit = _load_json(failure_audit_json_path)
    bounded_hybrid = _load_json(bounded_hybrid_json_path)
    anchor_scores = np.asarray(score_arrays[anchor_model], dtype=np.float32)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "purpose": (
            "Compact acceptance review pack for current en-ja learner-difficulty "
            "promotion readiness."
        ),
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "validation_eval_json": _repo_or_home_path(validation_eval_json_path),
            "cleaned_lane_json": _repo_or_home_path(cleaned_lane_json_path),
            "failure_audit_json": _repo_or_home_path(failure_audit_json_path),
            "bounded_hybrid_json": _repo_or_home_path(bounded_hybrid_json_path),
            "anchor_model": anchor_model,
            "population_count": int(len(anchor_scores)),
            **resolved_ids,
        },
        "current_model_evidence": current_model_evidence(
            validation_eval=validation_eval,
            cleaned_lane=cleaned_lane,
            failure_audit=failure_audit,
            bounded_hybrid=bounded_hybrid,
        ),
        "predicted_band_samples": predicted_band_samples(
            anchor_scores,
            component=component,
            score_arrays=score_arrays,
            sample_count=sample_count,
        ),
        "full_population_disagreements": full_population_disagreements(
            anchor_model=anchor_model,
            component=component,
            score_arrays=score_arrays,
            detail_limit=detail_limit,
        ),
        "validation_largest_anchor_errors": validation_largest_errors(
            validation_eval,
            anchor_model=anchor_model,
            detail_limit=detail_limit,
        ),
        "acceptance_assessment": acceptance_assessment(),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
                "validation_eval_json": validation_eval_json_path,
                "cleaned_lane_json": cleaned_lane_json_path,
                "failure_audit_json": failure_audit_json_path,
                "bounded_hybrid_json": bounded_hybrid_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "acceptance_review_pack": Path(__file__),
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "stitched_source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_stitched_source_arbitration_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def current_model_evidence(
    *,
    validation_eval: Mapping[str, object],
    cleaned_lane: Mapping[str, object],
    failure_audit: Mapping[str, object],
    bounded_hybrid: Mapping[str, object],
) -> dict[str, object]:
    failure_summary = _mapping(failure_audit.get("summary"))
    return {
        "validation_leaderboard": _mapping(validation_eval.get("summary")).get("leaderboard", []),
        "validation_errors_by_bucket": _mapping(validation_eval.get("summary")).get(
            "mean_errors_by_bucket", {}
        ),
        "cleaned_lane_deltas": _mapping(cleaned_lane.get("summary")).get("dataset_deltas", {}),
        "distribution_mismatch_top": _rows(failure_summary.get("distribution_mismatch"))[:8],
        "largest_failure_groups": _rows(failure_summary.get("largest_failure_groups"))[:10],
        "bounded_hybrid_primary": _mapping(bounded_hybrid.get("primary_candidates")),
    }


def predicted_band_samples(
    anchor_scores: object,
    *,
    component: object,
    score_arrays: Mapping[str, object],
    sample_count: int,
) -> list[dict[str, object]]:
    scores = np.asarray(anchor_scores, dtype=np.float32)
    rows: list[dict[str, object]] = []
    for start, end in PREDICTED_BANDS:
        indices = _band_indices(scores, start=start, end=end)
        sampled = _evenly_spaced_indices(indices, sample_count=sample_count)
        rows.append(
            {
                "band": f"{start:.2f}-{end:.2f}",
                "row_count": int(len(indices)),
                "samples": [
                    row_snapshot(index, component=component, score_arrays=score_arrays)
                    for index in sampled
                ],
            }
        )
    return rows


def full_population_disagreements(
    *,
    anchor_model: str,
    component: object,
    score_arrays: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    anchor = np.asarray(score_arrays[anchor_model], dtype=np.float32)
    result: dict[str, object] = {}
    for model_id in MODEL_IDS:
        if model_id == anchor_model:
            continue
        other = np.asarray(score_arrays[model_id], dtype=np.float32)
        result[f"{model_id}_higher_than_anchor"] = disagreement_rows(
            anchor=anchor,
            other=other,
            component=component,
            score_arrays=score_arrays,
            direction="other_higher",
            limit=detail_limit,
        )
        result[f"anchor_higher_than_{model_id}"] = disagreement_rows(
            anchor=anchor,
            other=other,
            component=component,
            score_arrays=score_arrays,
            direction="anchor_higher",
            limit=detail_limit,
        )
    return result


def disagreement_rows(
    *,
    anchor: object,
    other: object,
    component: object,
    score_arrays: Mapping[str, object],
    direction: str,
    limit: int,
) -> list[dict[str, object]]:
    anchor_scores = np.asarray(anchor, dtype=np.float32)
    other_scores = np.asarray(other, dtype=np.float32)
    if direction == "other_higher":
        delta = other_scores - anchor_scores
    elif direction == "anchor_higher":
        delta = anchor_scores - other_scores
    else:
        raise ValueError(f"unknown disagreement direction: {direction}")
    eligible = np.where(np.isfinite(delta) & (delta >= 0.08))[0]
    ordered = eligible[np.argsort(delta[eligible], kind="stable")[::-1]]
    return [
        row_snapshot(int(index), component=component, score_arrays=score_arrays)
        | {"selected_delta": _rounded(float(delta[int(index)]))}
        for index in ordered[:limit]
    ]


def validation_largest_errors(
    validation_eval: Mapping[str, object],
    *,
    anchor_model: str,
    detail_limit: int,
) -> list[Mapping[str, object]]:
    results = _mapping(validation_eval.get("results"))
    model = _mapping(results.get(anchor_model))
    return _rows(model.get("largest_errors"))[:detail_limit]


def acceptance_assessment() -> dict[str, object]:
    return {
        "source_hygiene": (
            "Useful as a review/lane guardrail; cleaned JMDict-exact evaluation "
            "does not change scalar winners."
        ),
        "scalar_promotion": (
            "Not ready for a new runtime correction; cross-split winners still "
            "disagree and one-group corrections do not pass both holdout and "
            "fresh validation."
        ),
        "realistic_safe_lift": "+0.003 to +0.010 cross-split score",
        "oracle_lift_seen": "about +0.015 on the tested ordering objective",
        "next_decision": (
            "Use this pack to identify a narrow, source-computable failure group; "
            "then test a bounded correction only for that group."
        ),
    }


def row_snapshot(
    index: int,
    *,
    component: object,
    score_arrays: Mapping[str, object],
) -> dict[str, object]:
    return {
        "lemma": str(component["lemmas"][index]),
        "reading": str(component["readings"][index]),
        "candidate_state": str(component["candidate_states"][index]),
        "problem_class": str(component["problem_classes"][index]),
        "core_rank": _rounded(float(component["core_ranks"][index])),
        "v1": _rounded(float(np.asarray(score_arrays["v1"], dtype=np.float32)[index])),
        "ordinary_cap": _rounded(
            float(np.asarray(score_arrays["ordinary_cap"], dtype=np.float32)[index])
        ),
        "stitch": _rounded(float(np.asarray(score_arrays["stitch"], dtype=np.float32)[index])),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    evidence = _mapping(report.get("current_model_evidence"))
    assessment = _mapping(report.get("acceptance_assessment"))
    lines = [
        "# en-ja Learner-Difficulty Acceptance Review Pack",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        f"- Anchor model: `{_escape(inputs.get('anchor_model'))}`",
        f"- Population: `{_escape(inputs.get('population_count'))}`",
        "",
        "## Acceptance Posture",
        "",
        f"- Source hygiene: {_escape(assessment.get('source_hygiene'))}",
        f"- Scalar promotion: {_escape(assessment.get('scalar_promotion'))}",
        f"- Realistic safe lift: `{_escape(assessment.get('realistic_safe_lift'))}`",
        f"- Oracle lift seen: `{_escape(assessment.get('oracle_lift_seen'))}`",
        f"- Next decision: {_escape(assessment.get('next_decision'))}",
        "",
        "## Validation Leaderboard",
        "",
    ]
    lines.extend(_leaderboard_table(_rows(evidence.get("validation_leaderboard"))))
    lines.extend(["", "## Validation MAE By Expected Bucket", ""])
    lines.extend(_bucket_table(_mapping(evidence.get("validation_errors_by_bucket"))))
    lines.extend(["", "## Cleaned-Lane Winner Deltas", ""])
    lines.extend(_cleaned_delta_table(_mapping(evidence.get("cleaned_lane_deltas"))))
    lines.extend(["", "## Predicted-Band Samples", ""])
    for band in _rows(report.get("predicted_band_samples")):
        lines.append(f"### `{_escape(band.get('band'))}` rows `{_escape(band.get('row_count'))}`")
        lines.extend(_sample_table(_rows(band.get("samples"))))
        lines.append("")
    lines.extend(["## Largest Anchor Errors On Fresh Validation", ""])
    lines.extend(_validation_error_table(_rows(report.get("validation_largest_anchor_errors"))))
    lines.extend(["", "## Full-Population Model Disagreements", ""])
    disagreements = _mapping(report.get("full_population_disagreements"))
    for key, rows in disagreements.items():
        lines.append(f"### `{_escape(key)}`")
        lines.extend(_sample_table(_rows(rows), include_selected_delta=True))
        lines.append("")
    lines.extend(["## Largest Failure Groups", ""])
    lines.extend(_failure_group_table(_rows(evidence.get("largest_failure_groups"))))
    lines.extend(["", "## Distribution Mismatch Top", ""])
    lines.extend(_distribution_table(_rows(evidence.get("distribution_mismatch_top"))))
    return "\n".join(lines).rstrip() + "\n"


def _leaderboard_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Model | Balanced | MAE | Bucket | Pairwise | Spearman |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('model_id'))}`",
                    _escape(row.get("balanced_score")),
                    _escape(row.get("mae")),
                    _escape(row.get("bucket_accuracy")),
                    _escape(row.get("pairwise_accuracy")),
                    _escape(row.get("spearman")),
                ]
            )
            + " |"
        )
    return lines


def _bucket_table(buckets: Mapping[str, object]) -> list[str]:
    lines = [
        "| Bucket | Count | v1 MAE | ordinary_cap MAE | stitch MAE |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for bucket, payload in buckets.items():
        row = _mapping(payload)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(bucket)}`",
                    _escape(row.get("count")),
                    _escape(row.get("v1_mae")),
                    _escape(row.get("ordinary_cap_mae")),
                    _escape(row.get("stitch_mae")),
                ]
            )
            + " |"
        )
    return lines


def _cleaned_delta_table(deltas: Mapping[str, object]) -> list[str]:
    lines = [
        "| Dataset | All count | Cleaned count | Removed | All winner | Cleaned winner | Changed |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for dataset, payload in deltas.items():
        row = _mapping(payload)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(dataset)}`",
                    _escape(row.get("all_count")),
                    _escape(row.get("cleaned_count")),
                    _escape(row.get("removed_count")),
                    f"`{_escape(row.get('all_winner'))}`",
                    f"`{_escape(row.get('cleaned_winner'))}`",
                    f"`{_escape(row.get('winner_changed'))}`",
                ]
            )
            + " |"
        )
    return lines


def _sample_table(
    rows: Sequence[Mapping[str, object]],
    *,
    include_selected_delta: bool = False,
) -> list[str]:
    headers = [
        "Lemma",
        "Reading",
        "v1",
        "ordinary_cap",
        "stitch",
        "Class",
        "State",
        "Rank",
    ]
    if include_selected_delta:
        headers.append("Delta")
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = [
            _escape(row.get("lemma")),
            _escape(row.get("reading")),
            _escape(row.get("v1")),
            _escape(row.get("ordinary_cap")),
            _escape(row.get("stitch")),
            _escape(row.get("problem_class")),
            _escape(row.get("candidate_state")),
            _escape(row.get("core_rank")),
        ]
        if include_selected_delta:
            values.append(_escape(row.get("selected_delta")))
        lines.append("| " + " | ".join(f"`{value}`" for value in values) + " |")
    return lines


def _validation_error_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Label | Expected | Observed | Error | Direction |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(row.get("label")),
                    _escape(row.get("expected")),
                    _escape(row.get("observed")),
                    _escape(row.get("absolute_error")),
                    f"`{_escape(row.get('direction'))}`",
                ]
            )
            + " |"
        )
    return lines


def _failure_group_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Group | Dataset | Count | MAE | Bias | Winner |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('group_id'))}`",
                    f"`{_escape(row.get('dataset_id'))}`",
                    _escape(row.get("count")),
                    _escape(row.get("mae")),
                    _escape(row.get("signed_error_mean")),
                    f"`{_escape(row.get('winner_by_mae'))}`",
                ]
            )
            + " |"
        )
    return lines


def _distribution_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Group | Calibration | Holdout | Validation | Max gap |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        shares = _mapping(row.get("shares"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('group_id'))}`",
                    _escape(shares.get("calibration")),
                    _escape(shares.get("holdout")),
                    _escape(shares.get("stitch_validation")),
                    _escape(row.get("max_share_gap")),
                ]
            )
            + " |"
        )
    return lines


def _band_indices(values: object, *, start: float, end: float) -> object:
    scores = np.asarray(values, dtype=np.float32)
    if end >= 1.0:
        indices = np.where((scores >= start) & (scores <= end))[0]
    else:
        indices = np.where((scores >= start) & (scores < end))[0]
    return indices[np.argsort(scores[indices], kind="stable")]


def _evenly_spaced_indices(indices: object, *, sample_count: int) -> list[int]:
    parsed = np.asarray(indices, dtype=np.int64)
    if len(parsed) <= sample_count:
        return [int(index) for index in parsed]
    offsets = np.linspace(0, len(parsed) - 1, num=sample_count, dtype=np.int64)
    return [int(parsed[offset]) for offset in offsets]


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
