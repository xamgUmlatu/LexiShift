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


PAIR = "en-ja"
MODEL_IDS = ("v1", "ordinary_cap", "stitch")
DEFAULT_SOURCE_PAIR_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_pair_validation_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_cleaned_lane_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_cleaned_lane_eval_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate existing en-ja difficulty model scores before/after a "
            "JMDict-exact source-pair normal-vocabulary lane filter."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--stitch-candidate-id", default=None)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        source_pair_json_path=_resolve_path(args.source_pair_json),
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
    source_pair_json_path: Path,
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
    source_pair_payload = load_json(source_pair_json_path)
    source_pair_rows = [
        row for row in source_pair_payload.get("rows", ()) if isinstance(row, Mapping)
    ]
    lookup = component_lookup(component)
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
    dataset_reports = {}
    for dataset_id in sorted({str(row.get("dataset_id") or "") for row in source_pair_rows}):
        if not dataset_id:
            continue
        dataset_rows = [
            row for row in source_pair_rows if str(row.get("dataset_id") or "") == dataset_id
        ]
        dataset_reports[dataset_id] = dataset_report(
            dataset_rows,
            lookup=lookup,
            score_arrays=score_arrays,
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
                "Measure how existing scalar model metrics change when the normal-vocab "
                "lane is restricted to rows with exact JMDict lemma/reading support."
            ),
            "scope": (
                "Only rows with reviewed lemma/reading pairs and finite scalar labels are "
                "eligible. Rows without readings are outside this source-pair diagnostic."
            ),
            "filter": (
                "cleaned_jmdict_exact excludes scalar rows whose primary source-pair "
                "status is not jmdict_exact; excluded rows are preserved as review rows."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            **resolved_ids,
        },
        "summary": summary_for_datasets(dataset_reports),
        "datasets": dataset_reports,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "source_pair_json": source_pair_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "source_pair_validation": SCRIPT_DIR
                / "srs_learner_difficulty_source_pair_validation_en_ja.py",
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def dataset_report(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
    score_arrays: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    scalar_rows = [row for row in rows if row.get("target") == "scalar_vocab"]
    matched_rows = [row for row in scalar_rows if row_component_index(row, lookup) is not None]
    cleaned_rows = [row for row in matched_rows if row.get("primary_pair_status") == "jmdict_exact"]
    excluded_rows = [
        row for row in matched_rows if row.get("primary_pair_status") != "jmdict_exact"
    ]
    scopes = {
        "all_pair_scalar": metrics_scope(matched_rows, lookup=lookup, score_arrays=score_arrays),
        "cleaned_jmdict_exact": metrics_scope(
            cleaned_rows,
            lookup=lookup,
            score_arrays=score_arrays,
        ),
        "excluded_non_jmdict_exact": metrics_scope(
            excluded_rows,
            lookup=lookup,
            score_arrays=score_arrays,
        ),
    }
    return {
        "pair_scalar_count": len(matched_rows),
        "cleaned_jmdict_exact_count": len(cleaned_rows),
        "excluded_non_jmdict_exact_count": len(excluded_rows),
        "status_counts": count_values(row.get("primary_pair_status") for row in rows),
        "gate_counts": count_values(row.get("gate_recommendation") for row in rows),
        "scopes": scopes,
        "delta_cleaned_vs_all": scope_delta(
            scopes["all_pair_scalar"],
            scopes["cleaned_jmdict_exact"],
        ),
        "excluded_rows": excluded_row_details(
            excluded_rows,
            lookup=lookup,
            score_arrays=score_arrays,
            limit=detail_limit,
        ),
    }


def metrics_scope(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
    score_arrays: Mapping[str, object],
) -> dict[str, object]:
    context = context_from_rows(rows, lookup=lookup)
    if not context["labels"]:
        return {"count": 0, "leaderboard": []}
    results = []
    for model_id in MODEL_IDS:
        observed = observed_for_context(score_arrays[model_id], context)
        metrics = _difficulty_metrics(
            expected_values=context["expected_values"],
            observed_values=observed,
            expected_bands=context["expected_bands"],
            labels=context["labels"],
        )
        results.append(
            {
                "model_id": model_id,
                "scores": metrics["scores"],
                "metrics": _summary_metrics(metrics),
            }
        )
    return {
        "count": len(context["labels"]),
        "leaderboard": sorted(
            results,
            key=lambda row: float(_mapping(row.get("scores")).get("balanced_score") or -1.0),
            reverse=True,
        ),
    }


def context_from_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
) -> dict[str, object]:
    labels: list[str] = []
    expected_values: list[float] = []
    component_indices: list[int] = []
    for row in rows:
        value = _optional_float(row.get("expected_learner_difficulty"))
        component_index = row_component_index(row, lookup)
        if value is None or component_index is None:
            continue
        labels.append(str(row.get("label") or ""))
        expected_values.append(float(value))
        component_indices.append(int(component_index))
    expected = np.asarray(expected_values, dtype=np.float32)
    return {
        "labels": labels,
        "expected_values": expected,
        "expected_bands": [_difficulty_band(float(value)) for value in expected],
        "component_indices": np.asarray(component_indices, dtype=np.int64),
    }


def observed_for_context(scores: object, context: Mapping[str, object]) -> object:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    return np.asarray(scores, dtype=np.float32)[indices]


def scope_delta(
    all_scope: Mapping[str, object],
    cleaned_scope: Mapping[str, object],
) -> dict[str, object]:
    all_best = first_leader(all_scope)
    cleaned_best = first_leader(cleaned_scope)
    return {
        "all_count": all_scope.get("count"),
        "cleaned_count": cleaned_scope.get("count"),
        "removed_count": int(all_scope.get("count") or 0) - int(cleaned_scope.get("count") or 0),
        "all_winner": all_best.get("model_id"),
        "cleaned_winner": cleaned_best.get("model_id"),
        "all_winner_balanced": _mapping(all_best.get("scores")).get("balanced_score"),
        "cleaned_winner_balanced": _mapping(cleaned_best.get("scores")).get("balanced_score"),
        "winner_changed": all_best.get("model_id") != cleaned_best.get("model_id"),
    }


def first_leader(scope: Mapping[str, object]) -> dict[str, object]:
    leaderboard = scope.get("leaderboard") or []
    first = leaderboard[0] if leaderboard else {}
    return dict(first) if isinstance(first, Mapping) else {}


def excluded_row_details(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
    score_arrays: Mapping[str, object],
    limit: int,
) -> list[dict[str, object]]:
    details = []
    for row in rows:
        component_index = row_component_index(row, lookup)
        if component_index is None:
            continue
        expected = _optional_float(row.get("expected_learner_difficulty"))
        model_cells = {}
        for model_id in MODEL_IDS:
            observed = float(np.asarray(score_arrays[model_id], dtype=np.float32)[component_index])
            model_cells[model_id] = {
                "observed": _rounded(observed),
                "absolute_error": _rounded(
                    abs(observed - expected) if expected is not None else None
                ),
            }
        details.append(
            {
                "label": row.get("label"),
                "expected": _rounded(expected),
                "primary_pair_status": row.get("primary_pair_status"),
                "gate_recommendation": row.get("gate_recommendation"),
                "jmdict_status": row.get("jmdict_status"),
                "jmnedict_status": row.get("jmnedict_status"),
                "models": model_cells,
                "rationale": row.get("rationale"),
            }
        )
    return details[:limit]


def summary_for_datasets(datasets: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        "dataset_deltas": {
            dataset_id: _mapping(report.get("delta_cleaned_vs_all"))
            for dataset_id, report in datasets.items()
        },
        "excluded_counts": {
            dataset_id: report.get("excluded_non_jmdict_exact_count")
            for dataset_id, report in datasets.items()
        },
        "interpretation": interpretation(datasets),
    }


def interpretation(datasets: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    validation = _mapping(datasets.get("stitch_validation"))
    holdout = _mapping(datasets.get("holdout"))
    return {
        "validation_removed_count": validation.get("excluded_non_jmdict_exact_count"),
        "holdout_removed_count": holdout.get("excluded_non_jmdict_exact_count"),
        "validation_winner_changed": _mapping(validation.get("delta_cleaned_vs_all")).get(
            "winner_changed"
        ),
        "holdout_winner_changed": _mapping(holdout.get("delta_cleaned_vs_all")).get(
            "winner_changed"
        ),
        "recommended_next_step": (
            "Review the small excluded scalar set before deciding whether the JMDict-exact "
            "pair rule should be a hard pre-scalar gate or a review lane."
        ),
    }


def component_lookup(component: object) -> dict[tuple[str, str], int]:
    lookup: dict[tuple[str, str], int] = {}
    for index, (lemma, reading) in enumerate(zip(component["lemmas"], component["readings"])):
        lookup.setdefault((str(lemma), str(reading)), int(index))
    return lookup


def row_component_index(
    row: Mapping[str, object],
    lookup: Mapping[tuple[str, str], int],
) -> int | None:
    lemma = str(row.get("lemma") or "").strip()
    reading = str(row.get("reading") or "").strip()
    if not lemma or not reading:
        return None
    return lookup.get((lemma, reading))


def count_values(values: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    datasets = _mapping(report.get("datasets"))
    interpretation_row = _mapping(summary.get("interpretation"))
    lines = [
        "# en-ja Cleaned Lane Evaluation",
        "",
        "Status: generated sidecar evaluation",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Scope",
        "",
        "- Filter tested: `primary_pair_status == jmdict_exact` for scalar rows with reviewed readings.",
        "- This is not a new model search; it reuses the current v1, ordinary-cap, and stitch scores.",
        "",
        "## Dataset Deltas",
        "",
        "| Dataset | All count | Cleaned count | Removed | All winner | Cleaned winner | Winner changed |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for dataset_id, delta in _mapping(summary.get("dataset_deltas")).items():
        parsed = _mapping(delta)
        lines.append(
            f"| `{_escape(dataset_id)}` | {int(parsed.get('all_count') or 0)} | "
            f"{int(parsed.get('cleaned_count') or 0)} | "
            f"{int(parsed.get('removed_count') or 0)} | "
            f"`{_escape(parsed.get('all_winner'))}` | "
            f"`{_escape(parsed.get('cleaned_winner'))}` | "
            f"`{_escape(parsed.get('winner_changed'))}` |"
        )
    lines.extend(["", "## Leaderboards", ""])
    for dataset_id, dataset in datasets.items():
        parsed_dataset = _mapping(dataset)
        lines.append(f"### `{_escape(dataset_id)}`")
        lines.append("")
        lines.append("All pair-scalar rows:")
        lines.extend(
            leaderboard_table(
                _mapping(_mapping(parsed_dataset.get("scopes")).get("all_pair_scalar")).get(
                    "leaderboard"
                )
            )
        )
        lines.append("")
        lines.append("Cleaned JMDict-exact rows:")
        lines.extend(
            leaderboard_table(
                _mapping(_mapping(parsed_dataset.get("scopes")).get("cleaned_jmdict_exact")).get(
                    "leaderboard"
                )
            )
        )
        lines.append("")
        lines.append("Excluded scalar rows:")
        lines.extend(excluded_table(parsed_dataset.get("excluded_rows")))
        lines.append("")
    lines.extend(["## Interpretation", ""])
    lines.append(
        f"- Validation removed scalar rows: `{_escape(interpretation_row.get('validation_removed_count'))}`"
    )
    lines.append(
        f"- Holdout removed scalar rows: `{_escape(interpretation_row.get('holdout_removed_count'))}`"
    )
    lines.append(
        f"- Validation winner changed: `{_escape(interpretation_row.get('validation_winner_changed'))}`"
    )
    lines.append(f"- Next step: {_escape(interpretation_row.get('recommended_next_step'))}")
    return "\n".join(lines).rstrip() + "\n"


def leaderboard_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    lines = [
        "| Model | Balanced | MAE | Bucket | Pairwise | Spearman |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not values:
        lines.append("|  |  |  |  |  |  |")
        return lines
    for row in values:
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            f"| `{_escape(row.get('model_id'))}` | "
            f"{_escape(scores.get('balanced_score'))} | "
            f"{_escape(metrics.get('mae'))} | "
            f"{_escape(metrics.get('bucket_accuracy'))} | "
            f"{_escape(metrics.get('pairwise_accuracy'))} | "
            f"{_escape(metrics.get('spearman'))} |"
        )
    return lines


def excluded_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    if not values:
        return ["None."]
    lines = [
        "| Label | Expected | Status | Gate | v1 | cap | stitch | Rationale |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in values:
        models = _mapping(row.get("models"))
        lines.append(
            f"| {_escape(row.get('label'))} | {_escape(row.get('expected'))} | "
            f"`{_escape(row.get('primary_pair_status'))}` | "
            f"`{_escape(row.get('gate_recommendation'))}` | "
            f"{_escape(_mapping(models.get('v1')).get('observed'))} | "
            f"{_escape(_mapping(models.get('ordinary_cap')).get('observed'))} | "
            f"{_escape(_mapping(models.get('stitch')).get('observed'))} | "
            f"{_escape(row.get('rationale'))} |"
        )
    return lines


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
