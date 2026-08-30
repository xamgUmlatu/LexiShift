#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SWEEP_ARTIFACT_PREFIX,
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
    FormulaCandidate,
    _normalized_values_for_formula,
)


PAIR = "en-ja"
DEFAULT_TRACE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / f"{DEFAULT_SWEEP_ARTIFACT_PREFIX}_trace_latest.json"
)
DEFAULT_SEARCH_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_proficiency_ordering_search_en_ja_latest.json"
)
DEFAULT_STABILITY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_proficiency_ordering_stability_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_method_sample_compare_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_method_sample_compare_en_ja_latest.md"
)
DEFAULT_BAND_WIDTH = 0.10
DEFAULT_SAMPLE_COUNT = 8
DEFAULT_SAMPLE_STATES = ("normal_vocab",)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate qualitative band samples comparing the old balanced-score "
            "winner with the new proficiency-ordering winner."
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
    parser.add_argument("--band-width", type=float, default=DEFAULT_BAND_WIDTH)
    parser.add_argument("--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument(
        "--sample-states",
        default=",".join(DEFAULT_SAMPLE_STATES),
        help="Comma-separated candidate states included in qualitative samples.",
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
        band_width=max(0.01, float(args.band_width)),
        sample_count=max(1, int(args.sample_count)),
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
    band_width: float,
    sample_count: int,
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
    label_lookup = _label_lookup(calibration_context, holdout_context)
    rows = _sample_rows(
        component_context=component_context,
        problem_classes=tuple(str(value) for value in component["problem_classes"]),
        core_ranks=np.asarray(component["core_ranks"], dtype=np.float32),
        old_values=old_values,
        new_values=new_values,
        label_lookup=label_lookup,
    )
    bands = _bands(band_width)
    band_reports = [
        _band_report(
            band,
            rows=rows,
            sample_count=sample_count,
            sample_states=sample_states,
        )
        for band in bands
    ]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Qualitative sample comparison across difficulty bands for the "
                "old balanced-score sweep winner and the new proficiency-ordering winner."
            ),
            "sampling": (
                "Rows are sampled per model from the same full component matrix, "
                "filtered to sample_states, deduped by lemma/reading, then spread "
                "within each predicted difficulty band."
            ),
            "target_curve_id": TARGET_CURVE_ID,
        },
        "parameters": {
            "old_score_key": old_score_key,
            "band_width": _rounded(band_width),
            "sample_count": int(sample_count),
            "sample_states": list(sample_states),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "search_json": _repo_or_home_path(search_json),
            "stability_json": _repo_or_home_path(stability_json),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "normalization_population_count": len(component_context.lemmas),
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
        "global_comparison": _global_comparison(rows, sample_states=sample_states),
        "bands": band_reports,
    }


def _select_old_trace_record(
    trace: Mapping[str, object],
    *,
    score_key: str,
) -> Mapping[str, object]:
    records = _mapping_rows(trace.get("variant_records"))
    if not records:
        raise ValueError("Trace artifact has no variant_records")
    return max(
        records,
        key=lambda row: _optional_float(_mapping(row.get("scores")).get(score_key)) or -999.0,
    )


def _new_method_candidate_id(stability: Mapping[str, object]) -> str:
    primary = _mapping(stability.get("primary_candidates"))
    fold_training = _mapping(primary.get("fold_training_selector"))
    candidate_id = str(fold_training.get("candidate_id") or "")
    if candidate_id:
        return candidate_id
    stability_selector = _mapping(primary.get("stability_selector"))
    return str(stability_selector.get("candidate_id") or "")


def _search_candidate_row(
    search: Mapping[str, object],
    candidate_id: str,
) -> Mapping[str, object]:
    for row in _mapping_rows(search.get("candidate_results")):
        if str(row.get("candidate_id") or "") == candidate_id:
            return row
    raise ValueError(f"Candidate not found in search artifact: {candidate_id}")


def _formula_from_search_row(row: Mapping[str, object]) -> FormulaCandidate:
    return FormulaCandidate(
        formula_id=str(row.get("formula_id") or row.get("candidate_id") or ""),
        feature_set_id=str(row.get("feature_set_id") or ""),
        weights=_float_mapping(row.get("weights")),
        max_shift_from_frequency=_optional_float(row.get("max_shift_from_frequency")),
        transforms=_mapping(row.get("transforms")),
        missing_features=tuple(str(value) for value in row.get("missing_features") or ()),
    )


def _label_lookup(
    calibration_context: object,
    holdout_context: object,
) -> dict[tuple[str, str], Mapping[str, object]]:
    lookup = {}
    for source, context in (("calibration", calibration_context), ("holdout", holdout_context)):
        expected = np.asarray(context.expected_values, dtype=np.float32)
        states = np.asarray(context.expected_candidate_states, dtype=str)
        for index, (lemma, reading) in enumerate(zip(context.lemmas, context.readings)):
            key = (str(lemma), str(reading))
            if key in lookup:
                continue
            lookup[key] = {
                "label_source": source,
                "expected": _rounded(float(expected[index]))
                if np.isfinite(expected[index])
                else None,
                "expected_band": context.expected_bands[index],
                "expected_candidate_state": str(states[index]),
            }
    return lookup


def _sample_rows(
    *,
    component_context: object,
    problem_classes: Sequence[str],
    core_ranks: object,
    old_values: object,
    new_values: object,
    label_lookup: Mapping[tuple[str, str], Mapping[str, object]],
) -> list[dict[str, object]]:
    old = np.asarray(old_values, dtype=np.float32)
    new = np.asarray(new_values, dtype=np.float32)
    rows = []
    for index, (lemma, reading) in enumerate(
        zip(component_context.lemmas, component_context.readings)
    ):
        if not np.isfinite(old[index]) or not np.isfinite(new[index]):
            continue
        label = _mapping(label_lookup.get((str(lemma), str(reading))))
        rows.append(
            {
                "candidate_identity_key": component_context.candidate_identity_keys[index],
                "lemma": str(lemma),
                "reading": str(reading),
                "candidate_state": component_context.candidate_states[index],
                "problem_class": problem_classes[index],
                "core_rank": _optional_index_float(core_ranks, index),
                "jlpt_vocab_level": _optional_index_float(
                    component_context.jlpt_vocab_levels,
                    index,
                ),
                "old_score": _rounded(float(old[index])),
                "new_score": _rounded(float(new[index])),
                "score_delta_new_minus_old": _rounded(float(new[index] - old[index])),
                "label_source": label.get("label_source"),
                "expected": label.get("expected"),
                "expected_band": label.get("expected_band"),
                "expected_candidate_state": label.get("expected_candidate_state"),
            }
        )
    return _dedupe_rows(rows)


def _optional_index_float(values: object, index: int) -> float | None:
    parsed = _optional_float(np.asarray(values)[index])
    return _rounded(parsed)


def _dedupe_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    best = {}
    for row in rows:
        key = (str(row.get("lemma") or ""), str(row.get("reading") or ""))
        current = best.get(key)
        if current is None or _row_sort_key(row) < _row_sort_key(current):
            best[key] = dict(row)
    return list(best.values())


def _row_sort_key(row: Mapping[str, object]) -> tuple[int, float, str]:
    state = str(row.get("candidate_state") or "")
    normal_rank = 0 if state == "normal_vocab" else 1
    core_rank = _optional_float(row.get("core_rank"))
    return (normal_rank, core_rank if core_rank is not None else 999999.0, str(row.get("lemma")))


def _band_report(
    band: Mapping[str, object],
    *,
    rows: Sequence[Mapping[str, object]],
    sample_count: int,
    sample_states: Sequence[str],
) -> dict[str, object]:
    old_rows = _rows_in_band(rows, band, key="old_score", sample_states=sample_states)
    new_rows = _rows_in_band(rows, band, key="new_score", sample_states=sample_states)
    old_keys = {_lemma_reading_key(row) for row in old_rows}
    new_keys = {_lemma_reading_key(row) for row in new_rows}
    return {
        "label": band["label"],
        "range": {"min": band["min"], "max": band["max"]},
        "old_count": len(old_rows),
        "new_count": len(new_rows),
        "overlap_count": len(old_keys & new_keys),
        "old_only_count": len(old_keys - new_keys),
        "new_only_count": len(new_keys - old_keys),
        "old_samples": [
            _sample_row(row, score_key="old_score")
            for row in _sample_spread_rows(old_rows, sample_count=sample_count)
        ],
        "new_samples": [
            _sample_row(row, score_key="new_score")
            for row in _sample_spread_rows(new_rows, sample_count=sample_count)
        ],
    }


def _rows_in_band(
    rows: Sequence[Mapping[str, object]],
    band: Mapping[str, object],
    *,
    key: str,
    sample_states: Sequence[str],
) -> list[Mapping[str, object]]:
    allowed = {str(state) for state in sample_states}
    low = float(band["min"])
    high = float(band["max"])
    is_last = bool(band.get("is_last"))
    result = []
    for row in rows:
        if allowed and str(row.get("candidate_state") or "") not in allowed:
            continue
        value = _optional_float(row.get(key))
        if value is None:
            continue
        if value >= low and (value < high or (is_last and value <= high)):
            result.append(row)
    return sorted(
        result,
        key=lambda row: (_optional_float(row.get(key)) or 0.0, _row_sort_key(row)),
    )


def _sample_spread_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_count: int,
) -> list[Mapping[str, object]]:
    if len(rows) <= sample_count:
        return list(rows)
    samples = []
    used = set()
    for index in range(sample_count):
        position = int(((index + 0.5) / sample_count) * len(rows))
        position = min(len(rows) - 1, max(0, position))
        while position in used and position + 1 < len(rows):
            position += 1
        while position in used and position > 0:
            position -= 1
        used.add(position)
        samples.append(rows[position])
    return samples


def _sample_row(row: Mapping[str, object], *, score_key: str) -> dict[str, object]:
    return {
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "score": row.get(score_key),
        "old_score": row.get("old_score"),
        "new_score": row.get("new_score"),
        "delta_new_minus_old": row.get("score_delta_new_minus_old"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "jlpt_vocab_level": row.get("jlpt_vocab_level"),
        "label_source": row.get("label_source"),
        "expected": row.get("expected"),
        "expected_band": row.get("expected_band"),
    }


def _global_comparison(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_states: Sequence[str],
) -> dict[str, object]:
    allowed = {str(state) for state in sample_states}
    filtered = [
        row for row in rows if not allowed or str(row.get("candidate_state") or "") in allowed
    ]
    deltas = [
        _optional_float(row.get("score_delta_new_minus_old"))
        for row in filtered
        if _optional_float(row.get("score_delta_new_minus_old")) is not None
    ]
    return {
        "sample_population_count": len(filtered),
        "mean_delta_new_minus_old": _rounded(float(np.mean(deltas)) if deltas else None),
        "median_delta_new_minus_old": _rounded(float(np.median(deltas)) if deltas else None),
        "new_higher_count": sum(1 for value in deltas if value is not None and value > 0.02),
        "old_higher_count": sum(1 for value in deltas if value is not None and value < -0.02),
        "near_equal_count": sum(1 for value in deltas if value is not None and abs(value) <= 0.02),
    }


def _bands(width: float) -> list[dict[str, object]]:
    bands = []
    low = 0.0
    index = 0
    while low < 1.0 - 1e-9:
        high = min(1.0, low + width)
        bands.append(
            {
                "label": f"{low:.2f}-{high:.2f}",
                "min": _rounded(low),
                "max": _rounded(high),
                "is_last": high >= 1.0 - 1e-9,
                "index": index,
            }
        )
        low = high
        index += 1
    return bands


def render_markdown(report: Mapping[str, object]) -> str:
    models = _mapping(report.get("models"))
    old_model = _mapping(models.get("old_method"))
    new_model = _mapping(models.get("new_method"))
    lines = [
        "# en-ja Learner Difficulty Method Sample Comparison",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Old model: `{_escape(old_model.get('model_id'))}`",
        f"- New model: `{_escape(new_model.get('model_id'))}`",
        f"- Sample states: `{_escape(','.join(report['parameters']['sample_states']))}`",
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
    lines.extend(_global_section(report))
    for band in _mapping_rows(report.get("bands")):
        lines.extend(_band_section(band))
    return "\n".join(lines).rstrip() + "\n"


def _global_section(report: Mapping[str, object]) -> list[str]:
    comparison = _mapping(report.get("global_comparison"))
    return [
        "## Global Comparison",
        "",
        "| Population | Mean delta new-old | Median delta | New higher | Old higher | Near equal |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| `{_escape(comparison.get('sample_population_count'))}` | "
            f"`{_escape(comparison.get('mean_delta_new_minus_old'))}` | "
            f"`{_escape(comparison.get('median_delta_new_minus_old'))}` | "
            f"`{_escape(comparison.get('new_higher_count'))}` | "
            f"`{_escape(comparison.get('old_higher_count'))}` | "
            f"`{_escape(comparison.get('near_equal_count'))}` |"
        ),
        "",
    ]


def _band_section(band: Mapping[str, object]) -> list[str]:
    lines = [
        f"## Band {band.get('label')}",
        "",
        (
            f"- Old count: `{_escape(band.get('old_count'))}`; "
            f"new count: `{_escape(band.get('new_count'))}`; "
            f"overlap: `{_escape(band.get('overlap_count'))}`"
        ),
        "",
        "### Old Method Samples",
        "",
    ]
    lines.extend(_sample_table(_mapping_rows(band.get("old_samples"))))
    lines.extend(["", "### New Method Samples", ""])
    lines.extend(_sample_table(_mapping_rows(band.get("new_samples"))))
    lines.append("")
    return lines


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Lemma | Reading | Score | Old | New | Delta | JLPT | Label | Expected |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    if not rows:
        lines.append("|  |  |  |  |  |  |  |  |  |")
        return lines
    for row in rows:
        label = row.get("label_source") or ""
        expected_band = row.get("expected_band") or ""
        if expected_band:
            label = f"{label}:{expected_band}" if label else str(expected_band)
        lines.append(
            f"| {_escape(row.get('lemma'))} | {_escape(row.get('reading'))} | "
            f"`{_escape(row.get('score'))}` | `{_escape(row.get('old_score'))}` | "
            f"`{_escape(row.get('new_score'))}` | "
            f"`{_escape(row.get('delta_new_minus_old'))}` | "
            f"`{_escape(row.get('jlpt_vocab_level'))}` | "
            f"`{_escape(label)}` | `{_escape(row.get('expected'))}` |"
        )
    return lines


def _lemma_reading_key(row: Mapping[str, object]) -> tuple[str, str]:
    return (str(row.get("lemma") or ""), str(row.get("reading") or ""))


def _compact_mapping(value: object) -> str:
    mapping = _mapping(value)
    return ", ".join(f"{key}={_rounded(raw)}" for key, raw in sorted(mapping.items()))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _float_mapping(value: object) -> dict[str, float]:
    result = {}
    for key, raw in _mapping(value).items():
        parsed = _optional_float(raw)
        if parsed is not None:
            result[str(key)] = parsed
    return result


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split(",") if part.strip())


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
