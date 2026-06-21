#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_method_sample_compare_en_ja import (  # noqa: E402
    DEFAULT_SEARCH_JSON,
    DEFAULT_STABILITY_JSON,
    _formula_from_search_row,
    _new_method_candidate_id,
    _search_candidate_row,
    _select_old_trace_record,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _difficulty_metrics,
)
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_TRACE_JSON,
    _component_context,
    _escape,
    _label_context_from_json,
    _load_json,
    _mapping,
    _normalized_values_for_trace_record,
    _observed_for_context,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_proficiency_ordering_search_en_ja import (  # noqa: E402
    _normalized_values_for_formula,
)


PAIR = "en-ja"
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_residual_shape_review_labels_en_ja.json"
)
DEFAULT_TRIAGE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_triage_en_ja_latest.json"
)
DEFAULT_REVIEW_PACK_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_pack_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reviewed_focus_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reviewed_focus_eval_en_ja_latest.md"
)
VOCAB_TREATMENT = "vocab"
TOPIC_TREATMENT = "topic_only"
SOURCE_FIX_TREATMENT = "source_fix"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate current en-ja learner-difficulty candidates against the "
            "fully reviewed residual-shape label pack."
        )
    )
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--triage-json", type=Path, default=DEFAULT_TRIAGE_JSON)
    parser.add_argument("--review-pack-json", type=Path, default=DEFAULT_REVIEW_PACK_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--search-json", type=Path, default=DEFAULT_SEARCH_JSON)
    parser.add_argument("--stability-json", type=Path, default=DEFAULT_STABILITY_JSON)
    parser.add_argument("--old-score-key", default="balanced_score")
    parser.add_argument("--new-candidate-id", default="")
    parser.add_argument("--detail-limit", type=int, default=16)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        labels_json=_resolve_path(args.labels_json),
        triage_json=_resolve_path(args.triage_json),
        review_pack_json=_resolve_path(args.review_pack_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        trace_json=_resolve_path(args.trace_json),
        search_json=_resolve_path(args.search_json),
        stability_json=_resolve_path(args.stability_json),
        old_score_key=str(args.old_score_key),
        new_candidate_id=str(args.new_candidate_id or ""),
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
    labels_json: Path,
    triage_json: Path,
    review_pack_json: Path,
    component_matrix_path: Path,
    trace_json: Path,
    search_json: Path,
    stability_json: Path,
    old_score_key: str,
    new_candidate_id: str,
    detail_limit: int,
) -> dict[str, object]:
    labels_payload = _load_json(labels_json)
    triage_payload = _load_json(triage_json)
    review_pack = _load_json(review_pack_json)
    component = np.load(component_matrix_path)
    component_context = _component_context(component)
    label_context = _label_context_from_json(
        labels_payload,
        component_context=component_context,
        context_id="residual_shape_review",
    )
    reviewed_rows = _reviewed_rows(
        labels_payload=labels_payload,
        triage_payload=triage_payload,
        review_pack=review_pack,
        label_context=label_context,
        component=component,
    )
    models = _model_values(
        component_context=component_context,
        trace_payload=_load_json(trace_json),
        search_payload=_load_json(search_json),
        stability_payload=_load_json(stability_json),
        old_score_key=old_score_key,
        new_candidate_id=new_candidate_id,
    )
    model_reports = [
        _evaluate_model(
            model,
            label_context=label_context,
            reviewed_rows=reviewed_rows,
            detail_limit=detail_limit,
        )
        for model in models
    ]
    model_reports = sorted(
        model_reports,
        key=lambda row: (
            _none_as_large(
                _mapping(_mapping(row.get("metrics")).get("difficulty_value")).get("mae")
            ),
            -float(
                _mapping(_mapping(row.get("metrics")).get("pairwise_order")).get("strict_accuracy")
                or -1
            ),
            str(row.get("model_id") or ""),
        ),
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "canonical_calibration_changed": False,
        "method": {
            "purpose": (
                "Evaluate current learner-difficulty candidates against the "
                "reviewed residual-shape pack while keeping numeric difficulty, "
                "topic/admission routing, and source-fix rows separate."
            ),
            "label_policy": (
                "Rows with treatment `vocab` contribute to numeric difficulty "
                "metrics. Rows with treatment `topic_only` or `source_fix` are "
                "routing/admission evidence, not scalar fitting targets."
            ),
        },
        "inputs": {
            "labels_json": _repo_or_home_path(labels_json),
            "triage_json": _repo_or_home_path(triage_json),
            "review_pack_json": _repo_or_home_path(review_pack_json),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "trace_json": _repo_or_home_path(trace_json),
            "search_json": _repo_or_home_path(search_json),
            "stability_json": _repo_or_home_path(stability_json),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "labels_json": labels_json,
                "triage_json": triage_json,
                "review_pack_json": review_pack_json,
                "component_matrix": component_matrix_path,
                "trace_json": trace_json,
                "search_json": search_json,
                "stability_json": stability_json,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
                "piecewise_metrics": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "method_compare": SCRIPT_DIR
                / "srs_learner_difficulty_method_sample_compare_en_ja.py",
            },
            version_constants={},
            argv=sys.argv,
        ),
        "label_context": {
            "total_rows": len(reviewed_rows),
            "mapped_rows": int(
                (np.asarray(label_context.component_indices, dtype=np.int64) >= 0).sum()
            ),
            "missing_rows": list(label_context.missing_rows),
            "treatment_counts": dict(
                sorted(Counter(str(row.get("treatment") or "") for row in reviewed_rows).items())
            ),
            "route_counts": dict(
                sorted(Counter(str(row.get("review_route") or "") for row in reviewed_rows).items())
            ),
            "numeric_vocab_rows": sum(
                1
                for row in reviewed_rows
                if row.get("treatment") == VOCAB_TREATMENT
                and _optional_float(row.get("expected_learner_difficulty")) is not None
            ),
            "routing_rows": sum(
                1
                for row in reviewed_rows
                if row.get("treatment") in {TOPIC_TREATMENT, SOURCE_FIX_TREATMENT}
            ),
            "admission_policy": _admission_policy_summary(reviewed_rows),
        },
        "model_reports": model_reports,
    }


def _model_values(
    *,
    component_context: object,
    trace_payload: Mapping[str, object],
    search_payload: Mapping[str, object],
    stability_payload: Mapping[str, object],
    old_score_key: str,
    new_candidate_id: str,
) -> list[dict[str, object]]:
    models = [
        {
            "model_id": "current_component_values",
            "source": "component_matrix",
            "selector": "component.current_values",
            "values": np.asarray(component_context.current_values, dtype=np.float32),
        },
        {
            "model_id": "frequency_baseline",
            "source": "component_matrix",
            "selector": "component.frequency_values",
            "values": np.asarray(component_context.frequency_values, dtype=np.float32),
        },
    ]
    old_record = _select_old_trace_record(trace_payload, score_key=old_score_key)
    models.append(
        {
            "model_id": str(old_record.get("variant_id") or "old_trace_winner"),
            "source": "signal_sweep_trace",
            "selector": f"max:{old_score_key}",
            "scores": old_record.get("scores") or {},
            "weights": old_record.get("weights") or {},
            "transforms": old_record.get("transforms") or {},
            "values": np.asarray(
                _normalized_values_for_trace_record(old_record, component_context),
                dtype=np.float32,
            ),
        }
    )
    selected_new_id = new_candidate_id or _new_method_candidate_id(stability_payload)
    new_row = _search_candidate_row(search_payload, selected_new_id)
    new_formula = _formula_from_search_row(new_row)
    models.append(
        {
            "model_id": str(new_row.get("candidate_id") or selected_new_id),
            "source": "proficiency_ordering_search",
            "selector": "stability.fold_training_selector",
            "scores": {
                "calibration": _mapping(new_row.get("calibration")).get(
                    "proficiency_ordering_score"
                ),
                "holdout": _mapping(new_row.get("holdout")).get("proficiency_ordering_score"),
            },
            "weights": new_row.get("weights") or {},
            "transforms": new_row.get("transforms") or {},
            "values": np.asarray(
                _normalized_values_for_formula(new_formula, component_context),
                dtype=np.float32,
            ),
        }
    )
    return models


def _evaluate_model(
    model: Mapping[str, object],
    *,
    label_context: object,
    reviewed_rows: Sequence[Mapping[str, object]],
    detail_limit: int,
) -> dict[str, object]:
    values = np.asarray(model.get("values"), dtype=np.float32)
    observed = _observed_for_context(values, label_context)
    metrics = _difficulty_metrics(
        expected_values=label_context.expected_values,
        observed_values=observed,
        expected_bands=label_context.expected_bands,
        labels=label_context.labels,
        expected_candidate_states=label_context.expected_candidate_states,
        observed_candidate_states=label_context.observed_candidate_states,
    )
    return {
        "model_id": model.get("model_id"),
        "source": model.get("source"),
        "selector": model.get("selector"),
        "scores": model.get("scores") or {},
        "weights": model.get("weights") or {},
        "transforms": model.get("transforms") or {},
        "metrics": metrics,
        "route_metrics": _route_metrics(reviewed_rows, observed),
        "topic_score_summary": _topic_score_summary(reviewed_rows, observed),
        "worst_numeric_rows": _worst_numeric_rows(reviewed_rows, observed, limit=detail_limit),
        "topic_low_score_rows": _topic_score_rows(
            reviewed_rows,
            observed,
            limit=detail_limit,
            reverse=False,
        ),
        "topic_high_score_rows": _topic_score_rows(
            reviewed_rows,
            observed,
            limit=detail_limit,
            reverse=True,
        ),
    }


def _reviewed_rows(
    *,
    labels_payload: Mapping[str, object],
    triage_payload: Mapping[str, object],
    review_pack: Mapping[str, object],
    label_context: object,
    component: object,
) -> list[dict[str, object]]:
    triage_by_number = {
        int(row.get("row_number") or 0): _mapping(row)
        for row in triage_payload.get("triage_rows") or ()
        if _optional_float(_mapping(row).get("row_number")) is not None
    }
    pack_by_number = {
        index: _mapping(row)
        for index, row in enumerate(review_pack.get("review_rows") or (), start=1)
    }
    component_indices = np.asarray(label_context.component_indices, dtype=np.int64)
    observed_states = np.asarray(label_context.observed_candidate_states, dtype=str)
    problem_classes = np.asarray(component["problem_classes"], dtype=str)
    rows = []
    for index, raw_label in enumerate(labels_payload.get("labels") or ()):
        label = _mapping(raw_label)
        row_number = int(_optional_float(label.get("review_row_number")) or 0)
        triage = _mapping(triage_by_number.get(row_number))
        pack = _mapping(pack_by_number.get(row_number))
        component_index = int(component_indices[index]) if index < len(component_indices) else -1
        observed_problem_class = (
            str(problem_classes[component_index]) if component_index >= 0 else ""
        )
        expected = _optional_float(label.get("expected_learner_difficulty"))
        reference = _optional_float(label.get("reference_difficulty"))
        rows.append(
            {
                "row_number": row_number,
                "lemma": label.get("lemma"),
                "reading": label.get("expected_reading") or label.get("reading"),
                "label": _label(
                    label.get("lemma"), label.get("expected_reading") or label.get("reading")
                ),
                "treatment": label.get("treatment"),
                "expected_learner_difficulty": expected,
                "reference_difficulty": reference,
                "expected_band": label.get("expected_difficulty_band"),
                "expected_candidate_state": label.get("expected_candidate_state"),
                "expected_problem_class": label.get("expected_problem_class"),
                "observed_candidate_state": str(observed_states[index])
                if index < len(observed_states)
                else "",
                "observed_problem_class": observed_problem_class,
                "review_route": triage.get("review_route"),
                "review_priority": triage.get("review_priority"),
                "review_bucket": pack.get("review_bucket"),
                "gloss": "; ".join(str(value) for value in pack.get("jmdict_glosses") or ()),
                "rationale": label.get("rationale"),
            }
        )
    return sorted(rows, key=lambda row: int(row.get("row_number") or 0))


def _admission_policy_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    topic_rows = [row for row in rows if row.get("treatment") == TOPIC_TREATMENT]
    source_rows = [row for row in rows if row.get("treatment") == SOURCE_FIX_TREATMENT]
    topic_state_counts = Counter(
        str(row.get("observed_candidate_state") or "") for row in topic_rows
    )
    topic_problem_counts = Counter(
        str(row.get("observed_problem_class") or "") for row in topic_rows
    )
    topic_normal_vocab_rows = [
        row
        for row in topic_rows
        if str(row.get("observed_candidate_state") or "") == "normal_vocab"
    ]
    source_normal_vocab_rows = [
        row
        for row in source_rows
        if str(row.get("observed_candidate_state") or "") == "normal_vocab"
    ]
    return {
        "topic_only_count": len(topic_rows),
        "source_fix_count": len(source_rows),
        "topic_only_observed_state_counts": dict(sorted(topic_state_counts.items())),
        "topic_only_observed_problem_class_counts": dict(sorted(topic_problem_counts.items())),
        "topic_only_observed_normal_vocab_count": len(topic_normal_vocab_rows),
        "topic_only_observed_normal_vocab_rate": _rounded(
            len(topic_normal_vocab_rows) / len(topic_rows)
        )
        if topic_rows
        else None,
        "source_fix_observed_normal_vocab_count": len(source_normal_vocab_rows),
        "topic_only_normal_vocab_examples": [
            _row_identity(row) for row in topic_normal_vocab_rows[:12]
        ],
        "source_fix_examples": [_row_identity(row) for row in source_rows[:12]],
    }


def _route_metrics(
    rows: Sequence[Mapping[str, object]],
    observed_values: object,
) -> list[dict[str, object]]:
    observed = np.asarray(observed_values, dtype=np.float32)
    by_route: dict[str, list[tuple[int, Mapping[str, object]]]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_route[str(row.get("review_route") or "")].append((index, row))
    reports = []
    for route, pairs in sorted(by_route.items()):
        numeric_errors = []
        numeric_rows = []
        policy_rows = []
        for index, row in pairs:
            expected = _optional_float(row.get("expected_learner_difficulty"))
            observed_value = _observed_value(observed, index)
            if expected is not None and observed_value is not None:
                numeric_errors.append(abs(observed_value - expected))
                numeric_rows.append((row, expected, observed_value))
            if row.get("treatment") in {TOPIC_TREATMENT, SOURCE_FIX_TREATMENT}:
                policy_rows.append(row)
        reports.append(
            {
                "route": route,
                "row_count": len(pairs),
                "numeric_count": len(numeric_rows),
                "policy_count": len(policy_rows),
                "numeric_mae": _rounded(float(np.mean(numeric_errors))) if numeric_errors else None,
                "numeric_within_0_10": sum(1 for error in numeric_errors if error <= 0.10),
                "topic_only_count": sum(
                    1 for row in policy_rows if row.get("treatment") == TOPIC_TREATMENT
                ),
                "source_fix_count": sum(
                    1 for row in policy_rows if row.get("treatment") == SOURCE_FIX_TREATMENT
                ),
                "topic_only_observed_normal_vocab_count": sum(
                    1
                    for row in policy_rows
                    if row.get("treatment") == TOPIC_TREATMENT
                    and row.get("observed_candidate_state") == "normal_vocab"
                ),
            }
        )
    return reports


def _topic_score_summary(
    rows: Sequence[Mapping[str, object]],
    observed_values: object,
) -> dict[str, object]:
    observed = np.asarray(observed_values, dtype=np.float32)
    values = [
        value
        for index, row in enumerate(rows)
        if row.get("treatment") in {TOPIC_TREATMENT, SOURCE_FIX_TREATMENT}
        for value in [_observed_value(observed, index)]
        if value is not None
    ]
    if not values:
        return {"evaluated_count": 0}
    return {
        "evaluated_count": len(values),
        "mean": _rounded(float(np.mean(values))),
        "median": _rounded(float(np.median(values))),
        "min": _rounded(float(np.min(values))),
        "max": _rounded(float(np.max(values))),
        "below_0_55": sum(1 for value in values if value < 0.55),
        "below_0_80": sum(1 for value in values if value < 0.80),
        "at_or_above_0_80": sum(1 for value in values if value >= 0.80),
    }


def _worst_numeric_rows(
    rows: Sequence[Mapping[str, object]],
    observed_values: object,
    *,
    limit: int,
) -> list[dict[str, object]]:
    observed = np.asarray(observed_values, dtype=np.float32)
    scored = []
    for index, row in enumerate(rows):
        expected = _optional_float(row.get("expected_learner_difficulty"))
        observed_value = _observed_value(observed, index)
        if expected is None or observed_value is None:
            continue
        scored.append((abs(observed_value - expected), row, expected, observed_value))
    result = []
    for error, row, expected, observed_value in sorted(scored, key=lambda item: -item[0])[:limit]:
        result.append(
            {
                **_row_identity(row),
                "route": row.get("review_route"),
                "expected": _rounded(expected),
                "observed": _rounded(observed_value),
                "observed_band": _difficulty_band(observed_value),
                "delta_observed_minus_expected": _rounded(observed_value - expected),
                "abs_error": _rounded(error),
            }
        )
    return result


def _topic_score_rows(
    rows: Sequence[Mapping[str, object]],
    observed_values: object,
    *,
    limit: int,
    reverse: bool,
) -> list[dict[str, object]]:
    observed = np.asarray(observed_values, dtype=np.float32)
    scored = []
    for index, row in enumerate(rows):
        if row.get("treatment") not in {TOPIC_TREATMENT, SOURCE_FIX_TREATMENT}:
            continue
        observed_value = _observed_value(observed, index)
        if observed_value is None:
            continue
        scored.append((observed_value, row))
    result = []
    for observed_value, row in sorted(scored, key=lambda item: item[0], reverse=reverse)[:limit]:
        result.append(
            {
                **_row_identity(row),
                "route": row.get("review_route"),
                "treatment": row.get("treatment"),
                "reference_difficulty": _rounded(row.get("reference_difficulty")),
                "observed": _rounded(observed_value),
                "observed_band": _difficulty_band(observed_value),
                "observed_candidate_state": row.get("observed_candidate_state"),
            }
        )
    return result


def render_markdown(report: Mapping[str, object]) -> str:
    context = _mapping(report.get("label_context"))
    admission = _mapping(context.get("admission_policy"))
    lines = [
        "# en-ja Reviewed-Focus Learner Difficulty Evaluation",
        "",
        "This sidecar evaluates the fully reviewed residual-shape pack without promoting it into canonical calibration.",
        "",
        "## Label Context",
        "",
        f"- Reviewed rows: `{_escape(context.get('total_rows'))}`",
        f"- Mapped rows: `{_escape(context.get('mapped_rows'))}`",
        f"- Numeric vocab rows: `{_escape(context.get('numeric_vocab_rows'))}`",
        f"- Routing/source rows: `{_escape(context.get('routing_rows'))}`",
        f"- Topic-only rows observed as `normal_vocab`: `{_escape(admission.get('topic_only_observed_normal_vocab_count'))}` / `{_escape(admission.get('topic_only_count'))}`",
        f"- Source-fix rows observed as `normal_vocab`: `{_escape(admission.get('source_fix_observed_normal_vocab_count'))}` / `{_escape(admission.get('source_fix_count'))}`",
        "",
        "## Model Summary",
        "",
        "| Model | Source | Numeric MAE | Bucket acc | Pairwise strict | Topic mean | Topic <0.80 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model in _mapping_rows(report.get("model_reports")):
        metrics = _mapping(model.get("metrics"))
        difficulty_value = _mapping(metrics.get("difficulty_value"))
        difficulty_bucket = _mapping(metrics.get("difficulty_bucket"))
        pairwise = _mapping(metrics.get("pairwise_order"))
        topic_summary = _mapping(model.get("topic_score_summary"))
        lines.append(
            "| "
            f"`{_escape(model.get('model_id'))}` | "
            f"`{_escape(model.get('source'))}` | "
            f"`{_escape(difficulty_value.get('mae'))}` | "
            f"`{_escape(difficulty_bucket.get('accuracy'))}` | "
            f"`{_escape(pairwise.get('strict_accuracy'))}` | "
            f"`{_escape(topic_summary.get('mean'))}` | "
            f"`{_escape(topic_summary.get('below_0_80'))}` |"
        )
    lines.extend(
        [
            "",
            "## Route Metrics",
            "",
        ]
    )
    for model in _mapping_rows(report.get("model_reports")):
        lines.extend(_route_section(model))
    lines.extend(
        [
            "## Worst Numeric Rows",
            "",
        ]
    )
    for model in _mapping_rows(report.get("model_reports")):
        lines.extend(_worst_section(model))
    return "\n".join(lines).rstrip() + "\n"


def _route_section(model: Mapping[str, object]) -> list[str]:
    lines = [
        f"### {_escape(model.get('model_id'))}",
        "",
        "| Route | Rows | Numeric | MAE | Within 0.10 | Policy rows | Topic normal-vocab |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in _mapping_rows(model.get("route_metrics")):
        lines.append(
            "| "
            f"`{_escape(row.get('route'))}` | "
            f"`{_escape(row.get('row_count'))}` | "
            f"`{_escape(row.get('numeric_count'))}` | "
            f"`{_escape(row.get('numeric_mae'))}` | "
            f"`{_escape(row.get('numeric_within_0_10'))}` | "
            f"`{_escape(row.get('policy_count'))}` | "
            f"`{_escape(row.get('topic_only_observed_normal_vocab_count'))}` |"
        )
    lines.append("")
    return lines


def _worst_section(model: Mapping[str, object]) -> list[str]:
    lines = [
        f"### {_escape(model.get('model_id'))}",
        "",
        "| Word | Route | Expected | Observed | Delta | Abs error |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    rows = _mapping_rows(model.get("worst_numeric_rows"))
    if not rows:
        lines.append("|  |  |  |  |  |  |")
    for row in rows[:10]:
        lines.append(
            "| "
            f"{_escape(row.get('label'))} | "
            f"`{_escape(row.get('route'))}` | "
            f"`{_escape(row.get('expected'))}` | "
            f"`{_escape(row.get('observed'))}` | "
            f"`{_escape(row.get('delta_observed_minus_expected'))}` | "
            f"`{_escape(row.get('abs_error'))}` |"
        )
    lines.append("")
    return lines


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _row_identity(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "row_number": row.get("row_number"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "label": row.get("label") or _label(row.get("lemma"), row.get("reading")),
        "gloss": row.get("gloss"),
    }


def _label(lemma: object, reading: object) -> str:
    lemma_text = str(lemma or "")
    reading_text = str(reading or "")
    return f"{lemma_text}/{reading_text}" if reading_text else lemma_text


def _observed_value(observed: object, index: int) -> float | None:
    values = np.asarray(observed, dtype=np.float32)
    if index >= len(values) or not np.isfinite(values[index]):
        return None
    return float(values[index])


def _none_as_large(value: object) -> float:
    parsed = _optional_float(value)
    return 1_000_000.0 if parsed is None else float(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
