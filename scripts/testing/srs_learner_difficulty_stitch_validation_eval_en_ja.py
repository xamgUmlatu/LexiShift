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
    _difficulty_band,
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
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
    raw_scores_for_candidate,
)
from srs_learner_difficulty_stitched_source_arbitration_en_ja import (  # noqa: E402
    DEFAULT_CAP_REPORT,
    DEFAULT_JSON_OUT as DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    _best_holdout_candidate_id,
    _candidate_by_id,
    generate_stitch_candidates,
    stitched_scores,
)


PAIR = "en-ja"
DEFAULT_LABEL_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_stitch_validation_labels_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitch_validation_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitch_validation_eval_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate v1, ordinary-cap, and stitched source-arbitration candidates "
            "on the fresh en-ja stitch validation labels."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABEL_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--stitch-candidate-id", default=None)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        labels_json_path=_resolve_path(args.labels_json),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        v1_candidate_id=args.v1_candidate_id,
        cap_candidate_id=args.cap_candidate_id,
        stitch_candidate_id=args.stitch_candidate_id,
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
    labels_json_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    stitch_candidate_id: str | None,
    detail_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    labels_payload = load_json(labels_json_path)
    contexts = validation_contexts(labels_payload, component)
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
    results = {
        model_id: result_for_model(
            model_id,
            scores=scores,
            context=contexts["vocab_numeric"],
            detail_limit=detail_limit,
        )
        for model_id, scores in score_arrays.items()
    }
    rows = comparison_rows(score_arrays, contexts["vocab_numeric"], detail_limit=detail_limit)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Evaluate whether the pedagogical-known v1 / otherwise ordinary-cap "
                "stitch generalizes to the freshly reviewed validation labels."
            ),
            "numeric_scope": (
                "Only labels with treatment=vocab and expected_learner_difficulty "
                "are used for numeric difficulty metrics."
            ),
            "non_vocab_scope": (
                "grammar_item and topic_only rows are reported but excluded from "
                "numeric difficulty metrics; they test admission/category handling, "
                "not the difficulty scalar."
            ),
            "expected_bands": "derived from numeric expected_learner_difficulty values",
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "labels_json": _repo_or_home_path(labels_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            **resolved_ids,
            "label_count": len(labels_payload.get("labels", ())),
            "vocab_numeric_count": len(contexts["vocab_numeric"]["labels"]),
            "non_vocab_rows": contexts["non_vocab_rows"],
            "unmatched_rows": contexts["unmatched_rows"],
        },
        "summary": {
            "leaderboard": leaderboard(results),
            "winner_counts": rows["winner_counts"],
            "mean_errors_by_bucket": mean_errors_by_bucket(rows["all_rows"]),
        },
        "results": results,
        "row_comparison": rows,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "labels_json": labels_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "stitched_source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_stitched_source_arbitration_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def validation_contexts(
    labels_payload: Mapping[str, object],
    component: object,
) -> dict[str, object]:
    lookup = component_lookup(component)
    labels: list[str] = []
    expected_values: list[float] = []
    expected_bands: list[str] = []
    component_indices: list[int] = []
    review_buckets: list[str] = []
    non_vocab_rows: list[dict[str, object]] = []
    unmatched_rows: list[dict[str, object]] = []
    for row in labels_payload.get("labels", ()):
        if not isinstance(row, Mapping):
            continue
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
        label = f"{lemma}/{reading}" if reading else lemma
        component_index = lookup.get((lemma, reading))
        treatment = str(row.get("treatment") or "")
        value = _optional_float(row.get("expected_learner_difficulty"))
        if treatment != "vocab":
            non_vocab_rows.append(
                {
                    "review_row_number": row.get("review_row_number"),
                    "label": label,
                    "treatment": treatment,
                    "reference_difficulty": _rounded(row.get("reference_difficulty")),
                    "expected_learner_difficulty": _rounded(value),
                }
            )
            continue
        if value is None:
            continue
        if component_index is None:
            unmatched_rows.append(
                {
                    "review_row_number": row.get("review_row_number"),
                    "label": label,
                    "reason": "missing_component_row",
                }
            )
            continue
        labels.append(label)
        expected_values.append(float(value))
        expected_bands.append(_difficulty_band(value))
        component_indices.append(int(component_index))
        review_buckets.append(_difficulty_band(value))
    return {
        "vocab_numeric": {
            "labels": labels,
            "expected_values": np.asarray(expected_values, dtype=np.float32),
            "expected_bands": expected_bands,
            "component_indices": np.asarray(component_indices, dtype=np.int64),
            "review_buckets": review_buckets,
        },
        "non_vocab_rows": non_vocab_rows,
        "unmatched_rows": unmatched_rows,
    }


def component_lookup(component: object) -> dict[tuple[str, str], int]:
    lemmas = [str(value) for value in component["lemmas"]]
    readings = [str(value) for value in component["readings"]]
    lookup: dict[tuple[str, str], int] = {}
    for index, pair in enumerate(zip(lemmas, readings)):
        lookup.setdefault(pair, index)
    return lookup


def score_arrays_for_models(
    *,
    view: ComponentView,
    parts: Mapping[str, object],
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    stitch_candidate_id: str | None,
) -> tuple[dict[str, object], dict[str, object]]:
    target_positions = np.asarray(view.target_positions, dtype=np.float32)
    v1_payload = load_json(v1_report_path)
    cap_payload = load_json(cap_report_path)
    stitched_payload = load_json(stitched_report_path)
    resolved_v1_id = v1_candidate_id or _best_holdout_candidate_id(v1_payload)
    resolved_cap_id = cap_candidate_id or _best_holdout_candidate_id(cap_payload)
    resolved_stitch_id = stitch_candidate_id or str(
        _mapping(_mapping(stitched_payload.get("summary")).get("best_holdout_guardrail")).get(
            "candidate_id"
        )
        or _mapping(_mapping(stitched_payload.get("summary")).get("best_holdout_balanced")).get(
            "candidate_id"
        )
        or ""
    )
    if not resolved_stitch_id:
        raise ValueError("Could not find stitch candidate id in stitched report")
    v1_model = _candidate_by_id(resolved_v1_id)
    cap_model = _candidate_by_id(resolved_cap_id)
    stitch_model = stitch_candidate_by_id(resolved_stitch_id)
    v1_raw = raw_scores_for_candidate(v1_model, view, parts=parts)
    cap_raw = raw_scores_for_candidate(cap_model, view, parts=parts)
    v1_scores = _target_curve_normalize(v1_raw, target_positions=target_positions)
    cap_scores = _target_curve_normalize(cap_raw, target_positions=target_positions)
    stitch_scores = stitched_scores(
        stitch_model,
        parts=parts,
        target_positions=target_positions,
        v1_raw=v1_raw,
        cap_raw=cap_raw,
        v1_normalized=v1_scores,
        cap_normalized=cap_scores,
    )
    return (
        {
            "v1": np.asarray(v1_scores, dtype=np.float32),
            "ordinary_cap": np.asarray(cap_scores, dtype=np.float32),
            "stitch": np.asarray(stitch_scores, dtype=np.float32),
        },
        {
            "v1_candidate_id": resolved_v1_id,
            "cap_candidate_id": resolved_cap_id,
            "stitch_candidate_id": resolved_stitch_id,
        },
    )


def stitch_candidate_by_id(candidate_id: str) -> object:
    for candidate in generate_stitch_candidates():
        if candidate.candidate_id == candidate_id:
            return candidate
    raise ValueError(f"Stitch candidate not found: {candidate_id}")


def result_for_model(
    model_id: str,
    *,
    scores: object,
    context: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    observed = observed_for_context(scores, context)
    metrics = _difficulty_metrics(
        expected_values=context["expected_values"],
        observed_values=observed,
        expected_bands=context["expected_bands"],
        labels=context["labels"],
    )
    return {
        "model_id": model_id,
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
        "largest_errors": largest_errors(observed, context, limit=detail_limit),
    }


def observed_for_context(scores: object, context: Mapping[str, object]) -> object:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    return np.asarray(scores, dtype=np.float32)[indices]


def comparison_rows(
    score_arrays: Mapping[str, object],
    context: Mapping[str, object],
    *,
    detail_limit: int,
) -> dict[str, object]:
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    observed_by_model = {
        model_id: np.asarray(observed_for_context(scores, context), dtype=np.float32)
        for model_id, scores in score_arrays.items()
    }
    rows = []
    for index, label in enumerate(labels):
        model_cells = {}
        for model_id, observed in observed_by_model.items():
            value = float(observed[index])
            model_cells[model_id] = {
                "observed": _rounded(value),
                "absolute_error": _rounded(abs(value - float(expected[index]))),
            }
        winner = min(
            model_cells,
            key=lambda model_id: float(model_cells[model_id]["absolute_error"] or 0.0),
        )
        rows.append(
            {
                "label": label,
                "expected": _rounded(float(expected[index])),
                "expected_band": _difficulty_band(float(expected[index])),
                "winner": winner,
                "models": model_cells,
            }
        )
    winner_counts = {
        model_id: sum(1 for row in rows if row["winner"] == model_id) for model_id in score_arrays
    }
    return {
        "winner_counts": winner_counts,
        "all_rows": rows,
        "largest_stitch_errors": sorted(
            rows,
            key=lambda row: float(
                _mapping(_mapping(row.get("models")).get("stitch")).get("absolute_error") or 0.0
            ),
            reverse=True,
        )[:detail_limit],
    }


def largest_errors(
    observed: object,
    context: Mapping[str, object],
    *,
    limit: int,
) -> list[dict[str, object]]:
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    values = np.asarray(observed, dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    rows = []
    for index, label in enumerate(labels):
        rows.append(
            {
                "label": label,
                "expected": _rounded(float(expected[index])),
                "observed": _rounded(float(values[index])),
                "absolute_error": _rounded(abs(float(values[index]) - float(expected[index]))),
                "direction": "too_low" if values[index] < expected[index] else "too_high",
            }
        )
    return sorted(rows, key=lambda row: float(row["absolute_error"] or 0.0), reverse=True)[:limit]


def leaderboard(results: Mapping[str, Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    for model_id, result in results.items():
        scores = _mapping(result.get("scores"))
        metrics = _mapping(result.get("metrics"))
        rows.append(
            {
                "model_id": model_id,
                "balanced_score": scores.get("balanced_score"),
                "numeric_mae_score": scores.get("numeric_mae_score"),
                "bucket_accuracy_score": scores.get("bucket_accuracy_score"),
                "pairwise_order_score": scores.get("pairwise_order_score"),
                "rank_correlation_score": scores.get("rank_correlation_score"),
                "mae": metrics.get("mae"),
                "bucket_accuracy": metrics.get("bucket_accuracy"),
                "pairwise_accuracy": metrics.get("pairwise_accuracy"),
                "spearman": metrics.get("spearman"),
            }
        )
    return sorted(
        rows,
        key=lambda row: float(row.get("balanced_score") or -1.0),
        reverse=True,
    )


def mean_errors_by_bucket(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    buckets = sorted({str(row.get("expected_band") or "") for row in rows})
    result: dict[str, dict[str, object]] = {}
    for bucket in buckets:
        bucket_rows = [row for row in rows if row.get("expected_band") == bucket]
        result[bucket] = {"count": len(bucket_rows)}
        for model_id in ("v1", "ordinary_cap", "stitch"):
            errors = [
                _optional_float(
                    _mapping(_mapping(row.get("models")).get(model_id)).get("absolute_error")
                )
                for row in bucket_rows
            ]
            parsed = [float(value) for value in errors if value is not None]
            result[bucket][f"{model_id}_mae"] = _rounded(float(np.mean(parsed)) if parsed else None)
    return result


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Stitch Validation Evaluation",
        "",
        "Status: generated sidecar evaluation",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Scope",
        "",
        f"- Labels: `{_escape(inputs.get('label_count'))}`",
        f"- Numeric vocab rows evaluated: `{_escape(inputs.get('vocab_numeric_count'))}`",
        f"- Non-vocab rows excluded from numeric metrics: `{len(inputs.get('non_vocab_rows') or [])}`",
        f"- Unmatched rows: `{len(inputs.get('unmatched_rows') or [])}`",
        "",
        "## Leaderboard",
        "",
        "| Rank | Model | Balanced | MAE | Bucket | Pairwise | Spearman |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(summary.get("leaderboard") or (), start=1):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| {rank} | `{_escape(row.get('model_id'))}` | "
            f"{_escape(row.get('balanced_score'))} | "
            f"{_escape(row.get('mae'))} | "
            f"{_escape(row.get('bucket_accuracy'))} | "
            f"{_escape(row.get('pairwise_accuracy'))} | "
            f"{_escape(row.get('spearman'))} |"
        )
    lines.extend(["", "## Winner Counts", ""])
    for model_id, count in _mapping(summary.get("winner_counts")).items():
        lines.append(f"- `{_escape(model_id)}`: `{_escape(count)}`")
    lines.extend(["", "## Stitch Largest Errors", ""])
    lines.extend(row_table(_mapping(report.get("row_comparison")).get("largest_stitch_errors")))
    return "\n".join(lines).rstrip() + "\n"


def row_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    lines = [
        "| Label | Expected | v1 | cap | stitch | Winner |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in values[:20]:
        models = _mapping(row.get("models"))
        lines.append(
            f"| {_escape(row.get('label'))} | {_escape(row.get('expected'))} | "
            f"{_escape(_mapping(models.get('v1')).get('observed'))} | "
            f"{_escape(_mapping(models.get('ordinary_cap')).get('observed'))} | "
            f"{_escape(_mapping(models.get('stitch')).get('observed'))} | "
            f"`{_escape(row.get('winner'))}` |"
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
