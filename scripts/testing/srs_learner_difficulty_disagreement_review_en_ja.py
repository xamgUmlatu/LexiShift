#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
    DEFAULT_TRACE_JSON,
    _formula_from_search_row,
    _label_lookup,
    _new_method_candidate_id,
    _search_candidate_row,
    _select_old_trace_record,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_HOLDOUT_JSON,
    _calibration_context,
    _component_context,
    _escape,
    _label_context_from_json,
    _load_json,
    _mapping,
    _normalized_values_for_trace_record,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_proficiency_ordering_search_en_ja import (  # noqa: E402
    _normalized_values_for_formula,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_disagreement_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_disagreement_review_en_ja_latest.md"
)
DEFAULT_SAMPLE_STATES = ("normal_vocab", "deprioritized_vocab")
DEFAULT_BAND_WIDTH = 0.10
DEFAULT_DELTA_THRESHOLD = 0.12
DEFAULT_SAMPLE_LIMIT = 25
DEFAULT_BAND_SAMPLE_COUNT = 3
TIE_EPSILON = 0.005

SIGNAL_GROUPS: Mapping[str, tuple[str, ...]] = {
    "curriculum_core": (
        "jlpt_vocab_beginner_core",
        "lesson_vocab_beginner_core",
        "jmdict_priority",
    ),
    "frequency_tail": (
        "frequency_unranked_risk",
        "frequency_unranked_tail_risk",
        "frequency_unranked_rare_risk",
        "frequency_tail80",
        "frequency_tail90",
    ),
    "written_burden": (
        "max_written_form_burden",
        "written_form_burden",
        "max_kanji_burden",
        "kanji_burden",
        "kanji_curriculum_missing_risk",
        "stroke_count",
    ),
    "rare_native": (
        "rare_wago_tail_risk",
        "rare_wago_risk",
        "rare_wago_written_risk",
        "rare_wago_obscure_written_risk",
        "rare_non_standard_reading_risk",
    ),
    "marked_dictionary": (
        "jmdict_marked_usage_risk",
        "jmdict_register_marked_risk",
        "jmdict_search_only_form_risk",
        "jmdict_kana_preferred_risk",
        "jmdict_reading_form_marked_risk",
    ),
    "kango": (
        "kango_mid_signal",
        "wtype_kango_risk",
        "jmdict_sinitic_source",
        "sahen_kango_risk",
    ),
    "loanword": (
        "wtype_gairaigo_risk",
        "jmdict_loanword_source_risk",
        "jmdict_foreign_priority_risk",
    ),
    "entity_or_acronym": (
        "named_entity_risk",
        "candidate_deprioritized_named_entity_risk",
        "candidate_deprioritized_named_frequency_risk",
        "problem_class_proper_risk",
        "proper_acronym_entity_risk",
        "news_abbreviation_entity_risk",
        "jmdict_abbreviation_risk",
    ),
}

DIAGNOSTIC_SIGNALS = tuple(
    dict.fromkeys(signal for signals in SIGNAL_GROUPS.values() for signal in signals)
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review large old-vs-new learner-difficulty disagreements to diagnose "
            "residual structure before doing another model sweep."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--search-json", type=Path, default=DEFAULT_SEARCH_JSON)
    parser.add_argument("--stability-json", type=Path, default=DEFAULT_STABILITY_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--old-score-key", default="balanced_score")
    parser.add_argument(
        "--new-candidate-id",
        default="",
        help="Optional explicit new-method candidate id. Defaults to stability winner.",
    )
    parser.add_argument("--delta-threshold", type=float, default=DEFAULT_DELTA_THRESHOLD)
    parser.add_argument("--band-width", type=float, default=DEFAULT_BAND_WIDTH)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--band-sample-count", type=int, default=DEFAULT_BAND_SAMPLE_COUNT)
    parser.add_argument(
        "--sample-states",
        default=",".join(DEFAULT_SAMPLE_STATES),
        help="Comma-separated candidate states included in the disagreement review.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        search_json=_resolve_path(args.search_json),
        stability_json=_resolve_path(args.stability_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        holdout_json_path=_resolve_path(args.holdout_json),
        old_score_key=str(args.old_score_key),
        new_candidate_id=str(args.new_candidate_id or ""),
        delta_threshold=max(0.0, float(args.delta_threshold)),
        band_width=max(0.01, float(args.band_width)),
        sample_limit=max(1, int(args.sample_limit)),
        band_sample_count=max(1, int(args.band_sample_count)),
        sample_states=_parse_csv(args.sample_states),
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
    trace_json: Path,
    search_json: Path,
    stability_json: Path,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    holdout_json_path: Path,
    old_score_key: str,
    new_candidate_id: str,
    delta_threshold: float,
    band_width: float,
    sample_limit: int,
    band_sample_count: int,
    sample_states: Sequence[str],
) -> dict[str, object]:
    trace = _load_json(trace_json)
    search = _load_json(search_json)
    stability = _load_json(stability_json)
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    component_context = _component_context(component)
    calibration_context = _calibration_context(calibration, component_context)
    holdout_context = _label_context_from_json(
        _load_json(holdout_json_path),
        component_context=component_context,
        context_id="holdout",
    )

    old_record = _select_old_trace_record(trace, score_key=old_score_key)
    selected_new_id = new_candidate_id or _new_method_candidate_id(stability)
    new_row = _search_candidate_row(search, selected_new_id)
    new_formula = _formula_from_search_row(new_row)
    old_values = _normalized_values_for_trace_record(old_record, component_context)
    new_values = _normalized_values_for_formula(new_formula, component_context)
    feature_lookup = _feature_lookup(component_context)
    label_lookup = _label_lookup(calibration_context, holdout_context)
    rows = _disagreement_rows(
        component_context=component_context,
        component=component,
        feature_lookup=feature_lookup,
        old_values=old_values,
        new_values=new_values,
        label_lookup=label_lookup,
        band_width=band_width,
    )
    filtered_rows = _filter_rows(rows, sample_states=sample_states)
    large_rows = [
        row
        for row in filtered_rows
        if (_optional_float(row.get("abs_delta")) or 0.0) >= delta_threshold
    ]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Diagnose old-vs-new learner-difficulty residual structure by "
                "reviewing rows where the older balanced-score methodology and "
                "new proficiency-ordering methodology disagree."
            ),
            "interpretation": (
                "Positive delta means the new method places the word harder. "
                "Negative delta means the new method places the word easier."
            ),
            "target_curve_id": TARGET_CURVE_ID,
        },
        "parameters": {
            "old_score_key": old_score_key,
            "delta_threshold": _rounded(delta_threshold),
            "band_width": _rounded(band_width),
            "sample_limit": int(sample_limit),
            "band_sample_count": int(band_sample_count),
            "sample_states": list(sample_states),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "search_json": _repo_or_home_path(search_json),
            "stability_json": _repo_or_home_path(stability_json),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "population_count": len(component_context.lemmas),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "trace_json": trace_json,
                "search_json": search_json,
                "stability_json": stability_json,
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "holdout_json": holdout_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "method_sample_compare": SCRIPT_DIR
                / "srs_learner_difficulty_method_sample_compare_en_ja.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
                "proficiency_ordering_search": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_search_en_ja.py",
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "models": {
            "old_method": {
                "model_id": old_record.get("variant_id"),
                "source": "signal_sweep_trace",
                "selector": f"max:{old_score_key}",
                "scores": old_record.get("scores") or {},
                "weights": old_record.get("weights") or {},
                "max_shift_from_frequency": old_record.get("max_shift_from_frequency"),
                "transforms": old_record.get("transforms") or {},
            },
            "new_method": {
                "model_id": new_row.get("candidate_id"),
                "source": "proficiency_ordering_stability",
                "selector": "fold_training_selector",
                "scores": {
                    "calibration": _mapping(new_row.get("calibration")).get(
                        "proficiency_ordering_score"
                    ),
                    "holdout": _mapping(new_row.get("holdout")).get("proficiency_ordering_score"),
                },
                "weights": new_row.get("weights") or {},
                "max_shift_from_frequency": new_row.get("max_shift_from_frequency"),
                "transforms": new_row.get("transforms") or {},
            },
        },
        "global_delta_summary": _global_delta_summary(filtered_rows, delta_threshold),
        "large_disagreement_summary": _large_disagreement_summary(large_rows),
        "state_direction_summary": _state_direction_summary(large_rows),
        "reviewed_label_summary": _reviewed_label_summary(
            filtered_rows,
            large_rows=large_rows,
        ),
        "direction_samples": _direction_samples(
            large_rows,
            sample_limit=sample_limit,
        ),
        "state_direction_samples": _state_direction_samples(
            large_rows,
            sample_limit=max(5, sample_limit // 2),
        ),
        "band_samples": _band_samples(
            large_rows,
            band_width=band_width,
            sample_count=band_sample_count,
        ),
    }


def _disagreement_rows(
    *,
    component_context: object,
    component: object,
    feature_lookup: Mapping[str, int],
    old_values: object,
    new_values: object,
    label_lookup: Mapping[tuple[str, str], Mapping[str, object]],
    band_width: float,
) -> list[dict[str, object]]:
    old = np.asarray(old_values, dtype=np.float32)
    new = np.asarray(new_values, dtype=np.float32)
    problem_classes = tuple(str(value) for value in component["problem_classes"])
    core_ranks = np.asarray(component["core_ranks"], dtype=np.float32)
    rows = []
    for index, (lemma, reading) in enumerate(
        zip(component_context.lemmas, component_context.readings)
    ):
        if not np.isfinite(old[index]) or not np.isfinite(new[index]):
            continue
        label = _mapping(label_lookup.get((str(lemma), str(reading))))
        row = {
            "row_index": index,
            "candidate_identity_key": component_context.candidate_identity_keys[index],
            "lemma": str(lemma),
            "reading": str(reading),
            "candidate_state": component_context.candidate_states[index],
            "problem_class": problem_classes[index],
            "core_rank": _rounded(float(core_ranks[index]))
            if np.isfinite(core_ranks[index])
            else None,
            "jlpt_vocab_level": _optional_index_float(
                component_context.jlpt_vocab_levels,
                index,
            ),
            "old_score": _rounded(float(old[index])),
            "new_score": _rounded(float(new[index])),
            "delta_new_minus_old": _rounded(float(new[index] - old[index])),
            "abs_delta": _rounded(abs(float(new[index] - old[index]))),
            "old_band": _band_label(float(old[index]), band_width),
            "new_band": _band_label(float(new[index]), band_width),
            "direction": _direction(float(new[index] - old[index])),
            "label_source": label.get("label_source"),
            "expected": label.get("expected"),
            "expected_band": label.get("expected_band"),
            "expected_candidate_state": label.get("expected_candidate_state"),
        }
        _attach_label_errors(row)
        row["signal_groups"] = _signal_group_values(index, component_context, feature_lookup)
        row["tags"] = _tags_for_row(row)
        row["top_signals"] = _top_signal_values(index, component_context, feature_lookup)
        rows.append(row)
    return _dedupe_rows(rows)


def _attach_label_errors(row: dict[str, object]) -> None:
    expected = _optional_float(row.get("expected"))
    old_score = _optional_float(row.get("old_score"))
    new_score = _optional_float(row.get("new_score"))
    if expected is None or old_score is None or new_score is None:
        row["old_abs_error"] = None
        row["new_abs_error"] = None
        row["closer_model"] = None
        return
    old_error = abs(old_score - expected)
    new_error = abs(new_score - expected)
    row["old_abs_error"] = _rounded(old_error)
    row["new_abs_error"] = _rounded(new_error)
    if abs(old_error - new_error) <= TIE_EPSILON:
        row["closer_model"] = "tie"
    elif old_error < new_error:
        row["closer_model"] = "old"
    else:
        row["closer_model"] = "new"


def _global_delta_summary(
    rows: Sequence[Mapping[str, object]],
    delta_threshold: float,
) -> dict[str, object]:
    deltas = np.asarray(
        [
            _optional_float(row.get("delta_new_minus_old"))
            for row in rows
            if _optional_float(row.get("delta_new_minus_old")) is not None
        ],
        dtype=np.float32,
    )
    if len(deltas) == 0:
        return {
            "population_count": 0,
            "delta_threshold": _rounded(delta_threshold),
            "large_disagreement_count": 0,
        }
    large_mask = np.abs(deltas) >= delta_threshold
    return {
        "population_count": len(deltas),
        "delta_threshold": _rounded(delta_threshold),
        "mean_delta_new_minus_old": _rounded(float(np.mean(deltas))),
        "median_delta_new_minus_old": _rounded(float(np.median(deltas))),
        "p10_delta": _rounded(float(np.quantile(deltas, 0.10))),
        "p90_delta": _rounded(float(np.quantile(deltas, 0.90))),
        "new_harder_count_gt_002": int(np.sum(deltas > 0.02)),
        "new_easier_count_lt_neg_002": int(np.sum(deltas < -0.02)),
        "near_equal_count_abs_le_002": int(np.sum(np.abs(deltas) <= 0.02)),
        "large_disagreement_count": int(np.sum(large_mask)),
        "large_disagreement_share": _rounded(float(np.mean(large_mask))),
        "large_new_harder_count": int(np.sum(deltas >= delta_threshold)),
        "large_new_easier_count": int(np.sum(deltas <= -delta_threshold)),
    }


def _large_disagreement_summary(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        direction: _direction_summary(
            [row for row in rows if str(row.get("direction") or "") == direction]
        )
        for direction in ("new_easier", "new_harder")
    }


def _state_direction_summary(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    states = sorted({str(row.get("candidate_state") or "") for row in rows})
    return {
        state: {
            direction: _direction_summary(
                [
                    row
                    for row in rows
                    if str(row.get("candidate_state") or "") == state
                    and str(row.get("direction") or "") == direction
                ]
            )
            for direction in ("new_easier", "new_harder")
        }
        for state in states
    }


def _direction_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "count": 0,
            "mean_abs_delta": None,
            "state_counts": {},
            "problem_class_counts": {},
            "tag_counts": {},
            "signal_group_summary": {},
        }
    return {
        "count": len(rows),
        "mean_abs_delta": _mean(rows, "abs_delta"),
        "mean_old_score": _mean(rows, "old_score"),
        "mean_new_score": _mean(rows, "new_score"),
        "state_counts": _counter(rows, "candidate_state"),
        "problem_class_counts": _counter(rows, "problem_class"),
        "new_band_counts": _counter(rows, "new_band"),
        "old_band_counts": _counter(rows, "old_band"),
        "tag_counts": _tag_counts(rows),
        "signal_group_summary": _signal_group_summary(rows),
    }


def _reviewed_label_summary(
    rows: Sequence[Mapping[str, object]],
    *,
    large_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    labeled = [row for row in rows if _optional_float(row.get("expected")) is not None]
    large_labeled = [row for row in large_rows if _optional_float(row.get("expected")) is not None]
    return {
        "all_labeled": _label_subset_summary(labeled),
        "large_disagreements": _label_subset_summary(large_labeled),
        "calibration_labeled": _label_subset_summary(
            [row for row in labeled if row.get("label_source") == "calibration"]
        ),
        "holdout_labeled": _label_subset_summary(
            [row for row in labeled if row.get("label_source") == "holdout"]
        ),
        "large_calibration_disagreements": _label_subset_summary(
            [row for row in large_labeled if row.get("label_source") == "calibration"]
        ),
        "large_holdout_disagreements": _label_subset_summary(
            [row for row in large_labeled if row.get("label_source") == "holdout"]
        ),
        "top_labeled_disagreements": [
            _sample_row(row)
            for row in sorted(
                large_labeled,
                key=lambda row: (
                    -(_optional_float(row.get("abs_delta")) or 0.0),
                    _row_sort_key(row),
                ),
            )[:DEFAULT_SAMPLE_LIMIT]
        ],
    }


def _label_subset_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    closer = Counter(str(row.get("closer_model") or "unlabeled") for row in rows)
    return {
        "count": len(rows),
        "old_mean_abs_error": _mean(rows, "old_abs_error"),
        "new_mean_abs_error": _mean(rows, "new_abs_error"),
        "old_closer_count": int(closer.get("old", 0)),
        "new_closer_count": int(closer.get("new", 0)),
        "tie_count": int(closer.get("tie", 0)),
    }


def _direction_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_limit: int,
) -> dict[str, object]:
    result = {}
    for direction in ("new_easier", "new_harder"):
        direction_rows = [row for row in rows if str(row.get("direction") or "") == direction]
        result[direction] = [
            _sample_row(row)
            for row in sorted(
                direction_rows,
                key=lambda row: (
                    -(_optional_float(row.get("abs_delta")) or 0.0),
                    _row_sort_key(row),
                ),
            )[:sample_limit]
        ]
    return result


def _state_direction_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_limit: int,
) -> dict[str, object]:
    states = sorted({str(row.get("candidate_state") or "") for row in rows})
    result = {}
    for state in states:
        result[state] = {}
        for direction in ("new_easier", "new_harder"):
            direction_rows = [
                row
                for row in rows
                if str(row.get("candidate_state") or "") == state
                and str(row.get("direction") or "") == direction
            ]
            result[state][direction] = [
                _sample_row(row)
                for row in sorted(
                    direction_rows,
                    key=lambda row: (
                        -(_optional_float(row.get("abs_delta")) or 0.0),
                        _row_sort_key(row),
                    ),
                )[:sample_limit]
            ]
    return result


def _band_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    band_width: float,
    sample_count: int,
) -> list[dict[str, object]]:
    reports = []
    for band in _band_labels(band_width):
        band_rows = [row for row in rows if row.get("new_band") == band]
        if not band_rows:
            continue
        reports.append(
            {
                "new_band": band,
                "new_easier_count": sum(
                    1 for row in band_rows if row.get("direction") == "new_easier"
                ),
                "new_harder_count": sum(
                    1 for row in band_rows if row.get("direction") == "new_harder"
                ),
                "new_easier_samples": [
                    _sample_row(row)
                    for row in _sample_spread_rows(
                        [row for row in band_rows if row.get("direction") == "new_easier"],
                        sample_count=sample_count,
                    )
                ],
                "new_harder_samples": [
                    _sample_row(row)
                    for row in _sample_spread_rows(
                        [row for row in band_rows if row.get("direction") == "new_harder"],
                        sample_count=sample_count,
                    )
                ],
            }
        )
    return reports


def _sample_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "jlpt_vocab_level": row.get("jlpt_vocab_level"),
        "old_score": row.get("old_score"),
        "new_score": row.get("new_score"),
        "delta_new_minus_old": row.get("delta_new_minus_old"),
        "old_band": row.get("old_band"),
        "new_band": row.get("new_band"),
        "label_source": row.get("label_source"),
        "expected": row.get("expected"),
        "expected_band": row.get("expected_band"),
        "old_abs_error": row.get("old_abs_error"),
        "new_abs_error": row.get("new_abs_error"),
        "closer_model": row.get("closer_model"),
        "tags": row.get("tags") or [],
        "top_signals": row.get("top_signals") or {},
    }


def _filter_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_states: Sequence[str],
) -> list[Mapping[str, object]]:
    allowed = {str(state) for state in sample_states}
    return [row for row in rows if not allowed or str(row.get("candidate_state") or "") in allowed]


def _dedupe_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    best = {}
    for row in rows:
        key = (str(row.get("lemma") or ""), str(row.get("reading") or ""))
        current = best.get(key)
        if current is None or _row_sort_key(row) < _row_sort_key(current):
            best[key] = dict(row)
    return list(best.values())


def _row_sort_key(row: Mapping[str, object]) -> tuple[int, float, str, str]:
    state = str(row.get("candidate_state") or "")
    normal_rank = 0 if state == "normal_vocab" else 1
    core_rank = _optional_float(row.get("core_rank"))
    return (
        normal_rank,
        core_rank if core_rank is not None else 999999.0,
        str(row.get("lemma") or ""),
        str(row.get("reading") or ""),
    )


def _feature_lookup(component_context: object) -> dict[str, int]:
    return {str(name): index for index, name in enumerate(component_context.component_names)}


def _signal_group_values(
    index: int,
    component_context: object,
    feature_lookup: Mapping[str, int],
) -> dict[str, float]:
    values = {}
    for group, signals in SIGNAL_GROUPS.items():
        parsed = [
            _feature_value(index, signal, component_context, feature_lookup) or 0.0
            for signal in signals
        ]
        values[group] = _rounded(max(parsed) if parsed else 0.0)
    return values


def _top_signal_values(
    index: int,
    component_context: object,
    feature_lookup: Mapping[str, int],
) -> dict[str, float]:
    values = []
    for signal in DIAGNOSTIC_SIGNALS:
        value = _feature_value(index, signal, component_context, feature_lookup)
        if value is not None and value >= 0.35:
            values.append((signal, value))
    values.sort(key=lambda item: (-item[1], item[0]))
    return {name: _rounded(value) for name, value in values[:6]}


def _feature_value(
    index: int,
    signal: str,
    component_context: object,
    feature_lookup: Mapping[str, int],
) -> float | None:
    column = feature_lookup.get(signal)
    if column is None:
        return None
    present = bool(component_context.component_present[index, column])
    value = _optional_float(component_context.component_values[index, column])
    if value is None:
        return None
    if not present and value == 0.0:
        return None
    return value


def _tags_for_row(row: Mapping[str, object]) -> list[str]:
    groups = _mapping(row.get("signal_groups"))
    tags = []
    if str(row.get("candidate_state") or "") != "normal_vocab":
        tags.append("deprioritized_lane")
    if str(row.get("problem_class") or "") == "proper_noun":
        tags.append("proper_noun")
    if str(row.get("problem_class") or "") == "acronym_or_code":
        tags.append("acronym_or_code")
    if (_optional_float(groups.get("entity_or_acronym")) or 0.0) >= 0.50:
        tags.append("entity_or_acronym")
    if (_optional_float(groups.get("rare_native")) or 0.0) >= 0.50:
        tags.append("rare_native")
    if (_optional_float(groups.get("marked_dictionary")) or 0.0) >= 0.50:
        tags.append("marked_dictionary")
    if (_optional_float(groups.get("written_burden")) or 0.0) >= 0.60:
        tags.append("written_burden")
    if (_optional_float(groups.get("kango")) or 0.0) >= 0.50:
        tags.append("kango")
    if (_optional_float(groups.get("loanword")) or 0.0) >= 0.50:
        tags.append("loanword")
    if (_optional_float(groups.get("frequency_tail")) or 0.0) >= 0.50:
        tags.append("frequency_tail")
    jlpt = _optional_float(row.get("jlpt_vocab_level"))
    if jlpt is not None and jlpt >= 4.0:
        tags.append("beginner_jlpt")
    if not tags:
        tags.append("plain")
    return tags


def _signal_group_summary(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    summary = {}
    for group in SIGNAL_GROUPS:
        values = [
            _optional_float(_mapping(row.get("signal_groups")).get(group)) or 0.0 for row in rows
        ]
        if not values:
            continue
        high_count = sum(1 for value in values if value >= 0.50)
        summary[group] = {
            "mean": _rounded(float(np.mean(values))),
            "high_count": high_count,
            "high_share": _rounded(high_count / len(values)),
        }
    return summary


def _tag_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counter = Counter(tag for row in rows for tag in row.get("tags") or ("plain",))
    return dict(counter.most_common())


def _counter(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key) or "") for row in rows).most_common())


def _mean(rows: Sequence[Mapping[str, object]], key: str) -> float | None:
    values = [
        _optional_float(row.get(key)) for row in rows if _optional_float(row.get(key)) is not None
    ]
    return _rounded(float(np.mean(values))) if values else None


def _direction(delta: float) -> str:
    if delta < 0.0:
        return "new_easier"
    if delta > 0.0:
        return "new_harder"
    return "equal"


def _band_label(score: float, width: float) -> str:
    clamped = min(1.0, max(0.0, score))
    index = int(clamped / width)
    if clamped >= 1.0 - 1e-9:
        index = int(round(1.0 / width)) - 1
    low = index * width
    high = min(1.0, low + width)
    return f"{low:.2f}-{high:.2f}"


def _band_labels(width: float) -> list[str]:
    labels = []
    low = 0.0
    while low < 1.0 - 1e-9:
        high = min(1.0, low + width)
        labels.append(f"{low:.2f}-{high:.2f}")
        low = high
    return labels


def _sample_spread_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_count: int,
) -> list[Mapping[str, object]]:
    ordered = sorted(
        rows,
        key=lambda row: (
            _optional_float(row.get("new_score")) or 0.0,
            -(_optional_float(row.get("abs_delta")) or 0.0),
            _row_sort_key(row),
        ),
    )
    if len(ordered) <= sample_count:
        return ordered
    samples = []
    used = set()
    for index in range(sample_count):
        position = int(((index + 0.5) / sample_count) * len(ordered))
        position = min(len(ordered) - 1, max(0, position))
        while position in used and position + 1 < len(ordered):
            position += 1
        while position in used and position > 0:
            position -= 1
        used.add(position)
        samples.append(ordered[position])
    return samples


def _optional_index_float(values: object, index: int) -> float | None:
    parsed = _optional_float(np.asarray(values)[index])
    return _rounded(parsed)


def render_markdown(report: Mapping[str, object]) -> str:
    models = _mapping(report.get("models"))
    old_model = _mapping(models.get("old_method"))
    new_model = _mapping(models.get("new_method"))
    params = _mapping(report.get("parameters"))
    lines = [
        "# en-ja Learner Difficulty Disagreement Review",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Old model: `{_escape(old_model.get('model_id'))}`",
        f"- New model: `{_escape(new_model.get('model_id'))}`",
        f"- Delta threshold: `{_escape(params.get('delta_threshold'))}`",
        f"- Sample states: `{_escape(','.join(params.get('sample_states') or []))}`",
        "",
        "## Model Summary",
        "",
        "| Method | Selector | Model | Key score | Weights |",
        "| --- | --- | --- | ---: | --- |",
        (
            f"| Old | `{_escape(old_model.get('selector'))}` | "
            f"`{_escape(old_model.get('model_id'))}` | "
            f"`{_escape(_mapping(old_model.get('scores')).get('balanced_score'))}` | "
            f"`{_escape(_compact_mapping(old_model.get('weights')))}` |"
        ),
        (
            f"| New | `{_escape(new_model.get('selector'))}` | "
            f"`{_escape(new_model.get('model_id'))}` | "
            f"`{_escape(_mapping(new_model.get('scores')).get('calibration'))}` | "
            f"`{_escape(_compact_mapping(new_model.get('weights')))}` |"
        ),
        "",
    ]
    lines.extend(_global_delta_section(report))
    lines.extend(_large_disagreement_section(report))
    lines.extend(_label_section(report))
    lines.extend(_state_direction_section(report))
    lines.extend(
        _sample_section("New Easier Top Disagreements", _sample_rows_for(report, "new_easier"))
    )
    lines.extend(
        _sample_section("New Harder Top Disagreements", _sample_rows_for(report, "new_harder"))
    )
    lines.extend(_band_sample_section(report))
    return "\n".join(lines).rstrip() + "\n"


def _global_delta_section(report: Mapping[str, object]) -> list[str]:
    summary = _mapping(report.get("global_delta_summary"))
    return [
        "## Global Delta Summary",
        "",
        "| Population | Mean delta | Median delta | P10 | P90 | Large | Large share | New easier large | New harder large |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| `{_escape(summary.get('population_count'))}` | "
            f"`{_escape(summary.get('mean_delta_new_minus_old'))}` | "
            f"`{_escape(summary.get('median_delta_new_minus_old'))}` | "
            f"`{_escape(summary.get('p10_delta'))}` | "
            f"`{_escape(summary.get('p90_delta'))}` | "
            f"`{_escape(summary.get('large_disagreement_count'))}` | "
            f"`{_escape(summary.get('large_disagreement_share'))}` | "
            f"`{_escape(summary.get('large_new_easier_count'))}` | "
            f"`{_escape(summary.get('large_new_harder_count'))}` |"
        ),
        "",
    ]


def _large_disagreement_section(report: Mapping[str, object]) -> list[str]:
    summaries = _mapping(report.get("large_disagreement_summary"))
    lines = [
        "## Large Disagreement Structure",
        "",
        "| Direction | Count | Mean abs delta | Mean old | Mean new | Top states | Top tags |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for direction in ("new_easier", "new_harder"):
        summary = _mapping(summaries.get(direction))
        lines.append(
            f"| `{direction}` | `{_escape(summary.get('count'))}` | "
            f"`{_escape(summary.get('mean_abs_delta'))}` | "
            f"`{_escape(summary.get('mean_old_score'))}` | "
            f"`{_escape(summary.get('mean_new_score'))}` | "
            f"{_escape(_compact_counter(summary.get('state_counts'), limit=3))} | "
            f"{_escape(_compact_counter(summary.get('tag_counts'), limit=5))} |"
        )
    lines.extend(["", "### Signal Group Shares", ""])
    lines.extend(_signal_group_table(summaries))
    lines.append("")
    return lines


def _signal_group_table(summaries: Mapping[str, object]) -> list[str]:
    lines = [
        "| Group | New easier high share | New harder high share | New easier mean | New harder mean |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    easier = _mapping(_mapping(summaries.get("new_easier")).get("signal_group_summary"))
    harder = _mapping(_mapping(summaries.get("new_harder")).get("signal_group_summary"))
    for group in SIGNAL_GROUPS:
        easier_row = _mapping(easier.get(group))
        harder_row = _mapping(harder.get(group))
        lines.append(
            f"| `{group}` | `{_escape(easier_row.get('high_share'))}` | "
            f"`{_escape(harder_row.get('high_share'))}` | "
            f"`{_escape(easier_row.get('mean'))}` | "
            f"`{_escape(harder_row.get('mean'))}` |"
        )
    return lines


def _label_section(report: Mapping[str, object]) -> list[str]:
    summary = _mapping(report.get("reviewed_label_summary"))
    lines = [
        "## Reviewed Label Comparison",
        "",
        "| Subset | Count | Old MAE | New MAE | Old closer | New closer | Tie |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in (
        "all_labeled",
        "large_disagreements",
        "calibration_labeled",
        "holdout_labeled",
        "large_calibration_disagreements",
        "large_holdout_disagreements",
    ):
        row = _mapping(summary.get(key))
        lines.append(
            f"| `{key}` | `{_escape(row.get('count'))}` | "
            f"`{_escape(row.get('old_mean_abs_error'))}` | "
            f"`{_escape(row.get('new_mean_abs_error'))}` | "
            f"`{_escape(row.get('old_closer_count'))}` | "
            f"`{_escape(row.get('new_closer_count'))}` | "
            f"`{_escape(row.get('tie_count'))}` |"
        )
    lines.extend(["", "### Top Labeled Disagreements", ""])
    lines.extend(_sample_table(_mapping_rows(summary.get("top_labeled_disagreements"))))
    lines.append("")
    return lines


def _sample_section(title: str, rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [f"## {title}", ""]
    lines.extend(_sample_table(rows))
    lines.append("")
    return lines


def _state_direction_section(report: Mapping[str, object]) -> list[str]:
    summaries = _mapping(report.get("state_direction_summary"))
    samples = _mapping(report.get("state_direction_samples"))
    lines = [
        "## Lane-Specific Disagreements",
        "",
        "| State | Direction | Count | Mean abs delta | Top tags |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for state, raw_state_summary in summaries.items():
        state_summary = _mapping(raw_state_summary)
        for direction in ("new_easier", "new_harder"):
            summary = _mapping(state_summary.get(direction))
            lines.append(
                f"| `{_escape(state)}` | `{direction}` | "
                f"`{_escape(summary.get('count'))}` | "
                f"`{_escape(summary.get('mean_abs_delta'))}` | "
                f"{_escape(_compact_counter(summary.get('tag_counts'), limit=5))} |"
            )
    lines.append("")
    for state, raw_state_samples in samples.items():
        state_samples = _mapping(raw_state_samples)
        for direction in ("new_easier", "new_harder"):
            rows = _mapping_rows(state_samples.get(direction))
            if not rows:
                continue
            lines.extend(
                [
                    f"### {state} / {direction}",
                    "",
                ]
            )
            lines.extend(_sample_table(rows))
            lines.append("")
    return lines


def _band_sample_section(report: Mapping[str, object]) -> list[str]:
    lines = ["## New-Placement Band Samples", ""]
    for band in _mapping_rows(report.get("band_samples")):
        lines.extend(
            [
                f"### Band {band.get('new_band')}",
                "",
                (
                    f"- New easier count: `{_escape(band.get('new_easier_count'))}`; "
                    f"new harder count: `{_escape(band.get('new_harder_count'))}`"
                ),
                "",
                "New easier samples:",
                "",
            ]
        )
        lines.extend(_sample_table(_mapping_rows(band.get("new_easier_samples"))))
        lines.extend(["", "New harder samples:", ""])
        lines.extend(_sample_table(_mapping_rows(band.get("new_harder_samples"))))
        lines.append("")
    return lines


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Lemma | Reading | State | Old | New | Delta | Label | Expected | Closer | Tags | Top signals |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    if not rows:
        lines.append("|  |  |  |  |  |  |  |  |  |  |  |")
        return lines
    for row in rows:
        label = row.get("label_source") or ""
        expected_band = row.get("expected_band") or ""
        if expected_band:
            label = f"{label}:{expected_band}" if label else str(expected_band)
        lines.append(
            f"| {_escape(row.get('lemma'))} | {_escape(row.get('reading'))} | "
            f"`{_escape(row.get('candidate_state'))}` | "
            f"`{_escape(row.get('old_score'))}` | "
            f"`{_escape(row.get('new_score'))}` | "
            f"`{_escape(row.get('delta_new_minus_old'))}` | "
            f"`{_escape(label)}` | "
            f"`{_escape(row.get('expected'))}` | "
            f"`{_escape(row.get('closer_model'))}` | "
            f"`{_escape(','.join(row.get('tags') or []))}` | "
            f"`{_escape(_compact_mapping(row.get('top_signals')))}` |"
        )
    return lines


def _sample_rows_for(
    report: Mapping[str, object],
    direction: str,
) -> list[Mapping[str, object]]:
    samples = _mapping(report.get("direction_samples"))
    return _mapping_rows(samples.get(direction))


def _compact_mapping(value: object) -> str:
    mapping = _mapping(value)
    return ", ".join(f"{key}={_rounded(raw)}" for key, raw in sorted(mapping.items()))


def _compact_counter(value: object, *, limit: int) -> str:
    rows = list(_mapping(value).items())[:limit]
    return ", ".join(f"{key}={raw}" for key, raw in rows)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split(",") if part.strip())


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
