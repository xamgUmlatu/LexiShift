#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_signal_palette_en_ja import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_PALETTE_JSON,
)


PAIR = "en-ja"
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_component_matrix_latest.npz"
)
DEFAULT_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_endpoint_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_endpoint_audit_en_ja_latest.md"
)
DEFAULT_CONCERNS_OUT = (
    PROJECT_ROOT / "docs" / "srs" / "srs_learner_difficulty_signal_endpoint_audit_concerns_en_ja.md"
)
EXAMPLE_LIMIT = 8
EPSILON = 1e-6
JLPT_BASE_DIFFICULTY = {5: 0.08, 4: 0.22, 3: 0.42, 2: 0.65, 1: 0.85}
JLPT_BASE_BEGINNER = {5: 1.0, 4: 0.75, 3: 0.35, 2: 0.10, 1: 0.0}


@dataclass(frozen=True)
class MatrixContext:
    component_names: tuple[str, ...]
    component_values: object
    component_present: object
    lemmas: tuple[str, ...]
    readings: tuple[str, ...]
    candidate_states: tuple[str, ...]
    problem_classes: tuple[str, ...]
    core_ranks: object
    frequency_values: object
    jlpt_vocab_levels: object
    current_values: object
    target_curve_positions: object


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit en-ja learner-difficulty signal endpoints without changing signal extraction."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--palette-json", type=Path, default=DEFAULT_PALETTE_JSON)
    parser.add_argument("--sweep-json", type=Path, default=DEFAULT_SWEEP_JSON)
    parser.add_argument("--example-limit", type=int, default=EXAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--concerns-out", type=Path, default=DEFAULT_CONCERNS_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        palette_json_path=_resolve_path(args.palette_json),
        sweep_json_path=_resolve_path(args.sweep_json),
        example_limit=max(1, int(args.example_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    concerns_out = _resolve_path(args.concerns_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    concerns_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report, full=True), encoding="utf-8")
    concerns_out.write_text(render_markdown(report, full=False), encoding="utf-8")
    print(f"Wrote JSON audit to {json_out}")
    print(f"Wrote Markdown audit to {markdown_out}")
    print(f"Wrote concerns file to {concerns_out}")
    return 0


def build_report(
    *,
    component_matrix_path: Path,
    palette_json_path: Path,
    sweep_json_path: Path,
    example_limit: int = EXAMPLE_LIMIT,
) -> dict[str, object]:
    component_npz = np.load(component_matrix_path)
    context = _matrix_context(component_npz)
    palette = _load_json(palette_json_path)
    sweep = _load_json(sweep_json_path)
    palette_signals = [_mapping(row) for row in _sequence(palette.get("signals"))]
    supporting_signals = [_mapping(row) for row in _sequence(palette.get("supporting_signals"))]
    active_names = set(context.component_names)
    signal_reports = [
        _signal_report(row, context=context, example_limit=example_limit) for row in palette_signals
    ]
    supporting_reports = [
        _supporting_signal_report(row, context=context, example_limit=example_limit)
        for row in supporting_signals
    ]
    concerns: list[dict[str, object]] = []
    concerns.extend(_global_concerns(context, palette, sweep))
    for report in signal_reports:
        concerns.extend(_signal_concerns(report, active_names=active_names))
    for report in supporting_reports:
        concerns.extend(_supporting_concerns(report))
    special_checks = _special_checks(context, sweep)
    concerns.extend(special_checks.get("concerns", []))
    severity_counts = Counter(str(row.get("severity") or "review") for row in concerns)
    category_counts = Counter(str(row.get("category") or "uncategorized") for row in concerns)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "signals_changed": False,
        "method": {
            "purpose": (
                "Audit signal endpoints and modeling semantics. This artifact reports "
                "concerns only; it intentionally does not correct or rewrite signals."
            ),
            "limits": (
                "The component matrix supports endpoint/value checks and row examples. "
                "It does not contain all raw source evidence, so some parser/source-truth "
                "claims remain flagged for source-backed follow-up."
            ),
        },
        "inputs": {
            "component_matrix": _repo_path(component_matrix_path),
            "palette_json": _repo_path(palette_json_path),
            "sweep_json": _repo_path(sweep_json_path),
            "matrix_row_count": len(context.lemmas),
            "matrix_component_count": len(context.component_names),
            "palette_signal_count": len(palette_signals),
            "supporting_signal_count": len(supporting_signals),
            "latest_sweep_generated_at": sweep.get("generated_at"),
        },
        "summary": {
            "audited_active_signal_count": sum(
                1 for row in signal_reports if row.get("status") == "audited_active"
            ),
            "palette_signals_not_in_matrix": sum(
                1 for row in signal_reports if row.get("status") != "audited_active"
            ),
            "supporting_signal_count": len(supporting_reports),
            "concern_count": len(concerns),
            "concern_severity_counts": dict(sorted(severity_counts.items())),
            "concern_category_counts": dict(sorted(category_counts.items())),
        },
        "special_checks": special_checks,
        "concerns": concerns,
        "signals": signal_reports,
        "supporting_signals": supporting_reports,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "palette_json": palette_json_path,
                "sweep_json": sweep_json_path,
            },
            code_paths={"signal_endpoint_audit": Path(__file__)},
        ),
    }


def _matrix_context(npz: object) -> MatrixContext:
    return MatrixContext(
        component_names=_string_tuple(npz["component_names"]),
        component_values=npz["component_values"],
        component_present=npz["component_present"],
        lemmas=_string_tuple(npz["lemmas"]),
        readings=_string_tuple(npz["readings"]),
        candidate_states=_string_tuple(npz["candidate_states"]),
        problem_classes=_string_tuple(npz["problem_classes"]),
        core_ranks=npz["core_ranks"],
        frequency_values=npz["frequency_values"],
        jlpt_vocab_levels=npz["jlpt_vocab_levels"],
        current_values=npz["current_values"],
        target_curve_positions=npz["target_curve_positions"],
    )


def _signal_report(
    palette_row: Mapping[str, object],
    *,
    context: MatrixContext,
    example_limit: int,
) -> dict[str, object]:
    name = str(palette_row.get("name") or "")
    base = {
        "name": name,
        "source_family": palette_row.get("source_family"),
        "signal_kind": palette_row.get("signal_kind"),
        "roles": list(_sequence(palette_row.get("roles"))),
        "declared_description": palette_row.get("description"),
    }
    if name not in context.component_names:
        return {
            **base,
            "status": "not_in_latest_component_matrix",
            "stats": None,
            "endpoint_examples": {},
        }
    component_index = context.component_names.index(name)
    present = context.component_present[:, component_index]
    values = context.component_values[:, component_index]
    present_indices = np.flatnonzero(present)
    present_values = values[present]
    stats = _value_stats(present_values, row_count=len(context.lemmas))
    return {
        **base,
        "status": "audited_active",
        "stats": stats,
        "endpoint_examples": _endpoint_examples(
            present_indices,
            present_values,
            context=context,
            example_limit=example_limit,
        ),
    }


def _supporting_signal_report(
    palette_row: Mapping[str, object],
    *,
    context: MatrixContext,
    example_limit: int,
) -> dict[str, object]:
    name = str(palette_row.get("name") or "")
    report = {
        "name": name,
        "source_family": palette_row.get("source_family"),
        "signal_kind": palette_row.get("signal_kind"),
        "roles": list(_sequence(palette_row.get("roles"))),
        "model_surface": palette_row.get("model_surface"),
        "declared_description": palette_row.get("description"),
        "status": "supporting_not_component",
        "stats": None,
        "endpoint_examples": {},
    }
    if name == "jlpt_vocab_levels":
        levels = np.asarray(context.jlpt_vocab_levels, dtype=float)
        mask = np.isfinite(levels)
        indices = np.flatnonzero(mask)
        values = levels[mask]
        report["status"] = "audited_supporting_matrix_field"
        report["stats"] = _value_stats(values, row_count=len(context.lemmas))
        report["level_counts"] = _level_counts(values)
        report["endpoint_examples"] = _endpoint_examples(
            indices,
            values,
            context=context,
            example_limit=example_limit,
        )
    elif name.startswith("jlpt_vocab_is_n"):
        level = _level_from_jlpt_gate_name(name)
        if level is not None:
            levels = np.asarray(context.jlpt_vocab_levels, dtype=float)
            mask = np.isfinite(levels)
            values = (levels[mask] == float(level)).astype(float)
            indices = np.flatnonzero(mask)
            report["status"] = "derived_from_easiest_level_matrix_field"
            report["stats"] = _value_stats(values, row_count=len(context.lemmas))
            report["endpoint_examples"] = _endpoint_examples(
                indices,
                values,
                context=context,
                example_limit=example_limit,
            )
    return report


def _value_stats(values: object, *, row_count: int) -> dict[str, object]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return {
            "count": 0,
            "coverage_rate": 0.0,
            "min": None,
            "p01": None,
            "p10": None,
            "median": None,
            "p90": None,
            "p99": None,
            "max": None,
            "mean": None,
            "std": None,
            "zero_rate_within_present": None,
            "one_rate_within_present": None,
            "unique_count": 0,
            "binary_like": False,
        }
    percentiles = np.percentile(arr, [1, 10, 50, 90, 99])
    unique_values = np.unique(np.round(arr, 6))
    return {
        "count": int(arr.size),
        "coverage_rate": _rounded(arr.size / row_count if row_count else 0.0),
        "missing_count": int(max(0, row_count - arr.size)),
        "min": _rounded(float(np.min(arr))),
        "p01": _rounded(float(percentiles[0])),
        "p10": _rounded(float(percentiles[1])),
        "median": _rounded(float(percentiles[2])),
        "p90": _rounded(float(percentiles[3])),
        "p99": _rounded(float(percentiles[4])),
        "max": _rounded(float(np.max(arr))),
        "mean": _rounded(float(np.mean(arr))),
        "std": _rounded(float(np.std(arr))),
        "zero_rate_within_present": _rounded(float(np.mean(np.abs(arr) <= EPSILON))),
        "one_rate_within_present": _rounded(float(np.mean(arr >= 1.0 - EPSILON))),
        "unique_count": int(unique_values.size),
        "unique_values_if_small": (
            [_rounded(float(value)) for value in unique_values.tolist()]
            if unique_values.size <= 12
            else None
        ),
        "binary_like": bool(
            unique_values.size <= 2 and all(value in {0.0, 1.0} for value in unique_values.tolist())
        ),
    }


def _endpoint_examples(
    indices: object,
    values: object,
    *,
    context: MatrixContext,
    example_limit: int,
) -> dict[str, object]:
    idx = np.asarray(indices, dtype=int)
    vals = np.asarray(values, dtype=float)
    if idx.size == 0:
        return {"low": [], "median": [], "high": []}
    order_low = np.lexsort((idx, vals))
    order_high = np.lexsort((idx, -vals))
    median = float(np.percentile(vals, 50))
    order_median = np.lexsort((idx, np.abs(vals - median)))
    return {
        "low": [
            _row_example(int(idx[pos]), float(vals[pos]), context)
            for pos in order_low[:example_limit]
        ],
        "median": [
            _row_example(int(idx[pos]), float(vals[pos]), context)
            for pos in order_median[:example_limit]
        ],
        "high": [
            _row_example(int(idx[pos]), float(vals[pos]), context)
            for pos in order_high[:example_limit]
        ],
    }


def _row_example(row_index: int, value: float, context: MatrixContext) -> dict[str, object]:
    reading = context.readings[row_index]
    label = context.lemmas[row_index]
    if reading:
        label = f"{label}/{reading}"
    return {
        "row_index": int(row_index),
        "label": label,
        "lemma": context.lemmas[row_index],
        "reading": reading,
        "value": _rounded(value),
        "core_rank": _rounded_optional(_array_float(context.core_ranks, row_index)),
        "frequency": _rounded_optional(_array_float(context.frequency_values, row_index)),
        "jlpt_vocab_level": _rounded_optional(_array_float(context.jlpt_vocab_levels, row_index)),
        "candidate_state": context.candidate_states[row_index],
        "problem_class": context.problem_classes[row_index],
        "current_value": _rounded_optional(_array_float(context.current_values, row_index)),
        "target_curve_position": _rounded_optional(
            _array_float(context.target_curve_positions, row_index)
        ),
    }


def _global_concerns(
    context: MatrixContext,
    palette: Mapping[str, object],
    sweep: Mapping[str, object],
) -> list[dict[str, object]]:
    palette_summary = _mapping(palette.get("summary"))
    inputs = _mapping(sweep.get("inputs"))
    return [
        _concern(
            "audit_limit",
            "medium",
            "global",
            (
                "The component matrix supports endpoint/value checks, but it does not "
                "carry all raw source evidence. JMDict/JMnedict/KANJIDIC/KanjiVG parser "
                "truth still needs source-backed spot checks for flagged endpoints."
            ),
        ),
        _concern(
            "coverage_denominator_mismatch",
            "review",
            "global",
            (
                "Palette coverage comes from sweep seed rows, while this endpoint audit "
                f"uses the deduped normalization component matrix ({len(context.lemmas)} rows). "
                "Small coverage-count differences are expected."
            ),
        ),
        _concern(
            "active_vs_palette_surface",
            "review",
            "global",
            (
                f"The palette has {palette_summary.get('component_count_from_code')} code-exposed "
                f"components, but the latest component matrix has {len(context.component_names)} "
                "active columns. Non-active components are design material, not endpoint-audited "
                "signals in this run."
            ),
        ),
        _concern(
            "jlpt_transform_layering",
            "medium",
            "global",
            (
                "The component matrix stores base `jlpt_vocab_difficulty` values, while "
                f"the latest sweep may remap JLPT levels through `jlpt_vocab_curves`="
                f"{inputs.get('jlpt_vocab_curves')}. Auditing the base component alone "
                "does not prove the final candidate formula's transformed endpoints."
            ),
        ),
    ]


def _signal_concerns(
    report: Mapping[str, object],
    *,
    active_names: set[str],
) -> list[dict[str, object]]:
    name = str(report.get("name") or "")
    concerns: list[dict[str, object]] = []
    if name not in active_names:
        concerns.append(
            _concern(
                "not_in_latest_component_matrix",
                "medium",
                name,
                (
                    "Palette signal is defined in code but absent from the latest component "
                    "matrix, so endpoint examples could not be checked in this run."
                ),
            )
        )
        return concerns
    stats = _mapping(report.get("stats"))
    signal_kind = str(report.get("signal_kind") or "")
    roles = {str(role) for role in _sequence(report.get("roles"))}
    coverage = float(stats.get("coverage_rate") or 0.0)
    zero_rate = stats.get("zero_rate_within_present")
    one_rate = stats.get("one_rate_within_present")
    unique_count = int(stats.get("unique_count") or 0)
    min_value = stats.get("min")
    max_value = stats.get("max")
    if coverage <= 0:
        concerns.append(
            _concern("zero_coverage", "high", name, "Active signal has no present values.")
        )
    elif coverage < 0.01:
        concerns.append(
            _concern(
                "very_low_coverage",
                "medium",
                name,
                f"Only {coverage:.3%} of matrix rows have this signal; endpoint examples are fragile.",
            )
        )
    elif coverage < 0.05:
        concerns.append(
            _concern(
                "low_coverage",
                "review",
                name,
                f"Only {coverage:.3%} of matrix rows have this signal; model use should be gated.",
            )
        )
    if unique_count <= 1 or min_value == max_value:
        concerns.append(
            _concern(
                "no_observed_variation",
                "high",
                name,
                "Signal has no endpoint variation in the latest matrix.",
            )
        )
    if signal_kind in {"ease_or_beginner_anchor", "evidence_confidence", "gate"}:
        concerns.append(
            _concern(
                "non_difficulty_polarity",
                "medium",
                name,
                (
                    f"Signal kind is `{signal_kind}`; higher values should not be blindly "
                    "treated as higher learner difficulty."
                ),
            )
        )
    if "orthographic_burden" in roles and "pedagogical_anchor" not in roles:
        concerns.append(
            _concern(
                "burden_not_priority",
                "review",
                name,
                (
                    "Orthographic burden may be useful mostly as a tie-breaker or tail "
                    "shape signal, not as a primary early presentation-priority signal."
                ),
            )
        )
    if (
        bool(stats.get("binary_like"))
        and coverage > 0.95
        and isinstance(zero_rate, float)
        and zero_rate > 0.98
    ):
        concerns.append(
            _concern(
                "absence_encoded_as_zero",
                "review",
                name,
                (
                    "Binary-like full-coverage signal is almost always zero. Confirm that "
                    "0 means negative evidence rather than missing/unknown evidence."
                ),
            )
        )
    if isinstance(one_rate, float) and one_rate > 0.95:
        concerns.append(
            _concern(
                "mostly_maxed_out",
                "review",
                name,
                "Signal is near 1.0 for most present rows; it may not separate endpoints well.",
            )
        )
    if name in {"jlpt_vocab_difficulty", "jlpt_vocab_beginner_core"}:
        concerns.append(
            _concern(
                "jlpt_levels_compressed",
                "medium",
                name,
                (
                    "Active component compresses N5-N1 into one scalar. Individual JLPT "
                    "level gates are derivable but not active component columns."
                ),
            )
        )
    if name == "frequency" and float(stats.get("median") or 0.0) > 0.90:
        concerns.append(
            _concern(
                "frequency_scale_compression",
                "medium",
                name,
                (
                    "Median frequency difficulty is above 0.90 in the normalization "
                    "matrix. Treat this as a corpus-rank/target-curve scale, not a "
                    "literal human difficulty percentile."
                ),
            )
        )
    high_core_examples = _high_endpoint_common_core_examples(report)
    if high_core_examples and "topic_register_policy" in roles:
        concerns.append(
            _concern(
                "topic_endpoint_hits_core_vocab",
                "high",
                name,
                (
                    "High endpoint includes common normal-vocab rows: "
                    f"{_compact_examples(high_core_examples)}. This may be a broad "
                    "priority/domain cue rather than true topic-only evidence."
                ),
            )
        )
    if high_core_examples and "ordinary_ladder_admission" in roles:
        concerns.append(
            _concern(
                "admission_endpoint_hits_core_vocab",
                "high",
                name,
                (
                    "High admission/entity endpoint includes common normal-vocab rows: "
                    f"{_compact_examples(high_core_examples)}. Check for name/entity "
                    "overlap with ordinary vocabulary."
                ),
            )
        )
    if signal_kind == "count_or_ambiguity":
        concerns.append(
            _concern(
                "count_signal_semantics",
                "review",
                name,
                (
                    "Count/ambiguity endpoint magnitude may not be monotonic presentation "
                    "difficulty. Check endpoint examples before using it as scalar burden."
                ),
            )
        )
    return concerns


def _high_endpoint_common_core_examples(report: Mapping[str, object]) -> tuple[object, ...]:
    examples = _sequence(_mapping(report.get("endpoint_examples")).get("high"))
    matches: list[object] = []
    for example in examples:
        row = _mapping(example)
        core_rank = row.get("core_rank")
        value = row.get("value")
        if not isinstance(core_rank, int | float) or not isinstance(value, int | float):
            continue
        if (
            float(value) >= 0.99
            and float(core_rank) <= 500.0
            and row.get("candidate_state") == "normal_vocab"
        ):
            matches.append(example)
    return tuple(matches[:5])


def _supporting_concerns(report: Mapping[str, object]) -> list[dict[str, object]]:
    name = str(report.get("name") or "")
    status = str(report.get("status") or "")
    if status == "supporting_not_component":
        return [
            _concern(
                "supporting_not_active_component",
                "review",
                name,
                (
                    "Supporting signal is available as raw metadata, derivable feature, or "
                    "sweep control, but it is not an active component-matrix column."
                ),
            )
        ]
    if status == "derived_from_easiest_level_matrix_field":
        return [
            _concern(
                "derived_from_collapsed_jlpt_level",
                "medium",
                name,
                (
                    "This audit can derive the gate from the stored easiest JLPT level only. "
                    "Checking whether a raw multi-level record includes this level requires "
                    "source metadata beyond the component matrix."
                ),
            )
        ]
    return []


def _special_checks(context: MatrixContext, sweep: Mapping[str, object]) -> dict[str, object]:
    checks: dict[str, object] = {}
    concerns: list[dict[str, object]] = []
    names = context.component_names
    if "jlpt_vocab_difficulty" in names:
        checks["jlpt_vocab_difficulty_by_level"] = _component_values_by_jlpt_level(
            "jlpt_vocab_difficulty",
            context,
        )
        if _component_values_by_jlpt_level("jlpt_vocab_difficulty", context) != {
            str(level): [value] for level, value in JLPT_BASE_DIFFICULTY.items()
        }:
            concerns.append(
                _concern(
                    "jlpt_base_mapping_changed",
                    "medium",
                    "jlpt_vocab_difficulty",
                    "Observed base JLPT difficulty mapping differs from the expected source mapping.",
                )
            )
    if "jlpt_vocab_beginner_core" in names:
        checks["jlpt_vocab_beginner_core_by_level"] = _component_values_by_jlpt_level(
            "jlpt_vocab_beginner_core",
            context,
        )
    checks["latest_sweep_jlpt_vocab_curves"] = _mapping(sweep.get("inputs")).get(
        "jlpt_vocab_curves"
    )
    checks["jlpt_vocab_level_counts"] = _level_counts(
        np.asarray(context.jlpt_vocab_levels)[
            np.isfinite(np.asarray(context.jlpt_vocab_levels, dtype=float))
        ]
    )
    checks["concerns"] = concerns
    return checks


def _component_values_by_jlpt_level(
    component_name: str,
    context: MatrixContext,
) -> dict[str, list[float]]:
    if component_name not in context.component_names:
        return {}
    component_index = context.component_names.index(component_name)
    present = context.component_present[:, component_index]
    values = np.asarray(context.component_values[:, component_index], dtype=float)
    levels = np.asarray(context.jlpt_vocab_levels, dtype=float)
    result: dict[str, list[float]] = {}
    for level in (5, 4, 3, 2, 1):
        mask = present & (levels == float(level))
        unique_values = sorted(float(value) for value in np.unique(np.round(values[mask], 6)))
        result[str(level)] = [_rounded(value) for value in unique_values]
    return result


def render_markdown(report: Mapping[str, object], *, full: bool) -> str:
    summary = _mapping(report.get("summary"))
    inputs = _mapping(report.get("inputs"))
    concerns = [_mapping(row) for row in _sequence(report.get("concerns"))]
    lines = [
        "# en-ja Signal Endpoint Audit Concerns",
        "",
        "Status: review artifact, no signal corrections applied",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "This audit checks endpoint behavior for the learner-difficulty signal palette. "
        "It is intentionally diagnostic: concerns below are discussion points, not fixes.",
        "",
        "## Inputs",
        "",
        f"- Component matrix: `{_escape(inputs.get('component_matrix'))}`",
        f"- Palette JSON: `{_escape(inputs.get('palette_json'))}`",
        f"- Sweep JSON: `{_escape(inputs.get('sweep_json'))}`",
        f"- Matrix rows: `{_escape(inputs.get('matrix_row_count'))}`",
        f"- Matrix components: `{_escape(inputs.get('matrix_component_count'))}`",
        f"- Palette signals: `{_escape(inputs.get('palette_signal_count'))}`",
        f"- Supporting signals: `{_escape(inputs.get('supporting_signal_count'))}`",
        "",
        "## Summary",
        "",
        f"- Audited active signals: `{_escape(summary.get('audited_active_signal_count'))}`",
        f"- Palette signals not in latest matrix: `{_escape(summary.get('palette_signals_not_in_matrix'))}`",
        f"- Total concerns: `{_escape(summary.get('concern_count'))}`",
        f"- Severity counts: `{_compact_counts(summary.get('concern_severity_counts'))}`",
        f"- Category counts: `{_compact_counts(summary.get('concern_category_counts'))}`",
        "",
        "## Concern Groups",
        "",
        "| Category | Count | Example signals |",
        "| --- | ---: | --- |",
    ]
    grouped: dict[str, list[str]] = defaultdict(list)
    for concern in concerns:
        grouped[str(concern.get("category") or "")].append(str(concern.get("signal") or ""))
    for category in sorted(grouped, key=lambda key: (-len(grouped[key]), key)):
        examples = ", ".join(f"`{_escape(signal)}`" for signal in grouped[category][:8])
        if len(grouped[category]) > 8:
            examples += f", ... +{len(grouped[category]) - 8}"
        lines.append(f"| `{_escape(category)}` | {len(grouped[category])} | {examples} |")
    display_concerns = sorted(concerns, key=_concern_sort_key)
    lines.extend(
        [
            "",
            "## Main Concerns",
            "",
        ]
    )
    for concern in display_concerns[:80]:
        lines.append(
            f"- **{_escape(concern.get('severity'))}** "
            f"`{_escape(concern.get('category'))}` "
            f"`{_escape(concern.get('signal'))}`: "
            f"{_escape(concern.get('message'))}"
        )
    if len(display_concerns) > 80:
        lines.append(
            f"- ... `{len(display_concerns) - 80}` more concerns are in the JSON/full audit artifact."
        )
    lines.extend(_special_check_markdown(report))
    lines.extend(_high_signal_examples(report))
    if full:
        lines.extend(_full_signal_tables(report))
    lines.append("")
    return "\n".join(lines)


def _concern_sort_key(concern: Mapping[str, object]) -> tuple[int, str, str]:
    severity_rank = {"high": 0, "medium": 1, "review": 2}
    return (
        severity_rank.get(str(concern.get("severity") or ""), 3),
        str(concern.get("category") or ""),
        str(concern.get("signal") or ""),
    )


def _special_check_markdown(report: Mapping[str, object]) -> list[str]:
    checks = _mapping(report.get("special_checks"))
    lines = ["", "## Special Checks", ""]
    for key in (
        "jlpt_vocab_difficulty_by_level",
        "jlpt_vocab_beginner_core_by_level",
        "latest_sweep_jlpt_vocab_curves",
        "jlpt_vocab_level_counts",
    ):
        if key in checks:
            lines.append(
                f"- `{_escape(key)}`: `{_escape(json.dumps(checks.get(key), ensure_ascii=False, sort_keys=True))}`"
            )
    return lines


def _high_signal_examples(report: Mapping[str, object]) -> list[str]:
    selected_names = (
        "frequency",
        "jlpt_vocab_difficulty",
        "jlpt_vocab_beginner_core",
        "named_entity_risk",
        "news_or_policy_topic_risk",
        "max_written_form_burden",
        "rare_wago_tail_risk",
    )
    by_name = {
        str(row.get("name")): _mapping(row)
        for row in _sequence(report.get("signals"))
        if isinstance(row, Mapping)
    }
    lines = ["", "## Endpoint Samples For Discussion", ""]
    for name in selected_names:
        row = by_name.get(name)
        if not row or row.get("status") != "audited_active":
            continue
        examples = _mapping(row.get("endpoint_examples"))
        lines.append(f"### `{_escape(name)}`")
        lines.append("")
        lines.append("| Endpoint | Examples |")
        lines.append("| --- | --- |")
        for endpoint in ("low", "median", "high"):
            lines.append(
                "| "
                + " | ".join(
                    (
                        endpoint,
                        _escape(_compact_examples(_sequence(examples.get(endpoint))[:5])),
                    )
                )
                + " |"
            )
        lines.append("")
    return lines


def _full_signal_tables(report: Mapping[str, object]) -> list[str]:
    lines = ["", "## Per-Signal Endpoint Stats", ""]
    lines.append(
        "| Signal | Status | Count | Coverage | Min | Median | Max | Zero rate | One rate | Concerns |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    concerns_by_signal: dict[str, list[str]] = defaultdict(list)
    for concern in _sequence(report.get("concerns")):
        row = _mapping(concern)
        concerns_by_signal[str(row.get("signal") or "")].append(str(row.get("category") or ""))
    for row in sorted(
        (_mapping(signal) for signal in _sequence(report.get("signals"))),
        key=lambda item: str(item.get("name") or ""),
    ):
        stats = _mapping(row.get("stats"))
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape(row.get('name'))}`",
                    _escape(row.get("status")),
                    _escape(stats.get("count", "")),
                    _escape(stats.get("coverage_rate", "")),
                    _escape(stats.get("min", "")),
                    _escape(stats.get("median", "")),
                    _escape(stats.get("max", "")),
                    _escape(stats.get("zero_rate_within_present", "")),
                    _escape(stats.get("one_rate_within_present", "")),
                    ", ".join(
                        f"`{_escape(value)}`"
                        for value in concerns_by_signal.get(str(row.get("name")), ())
                    ),
                )
            )
            + " |"
        )
    return lines


def _level_counts(values: object) -> dict[str, int]:
    arr = np.asarray(values, dtype=float)
    result: dict[str, int] = {}
    for level in (5, 4, 3, 2, 1):
        result[str(level)] = int(np.sum(arr == float(level)))
    return result


def _level_from_jlpt_gate_name(name: str) -> int | None:
    suffix = name.removeprefix("jlpt_vocab_is_n")
    if suffix.isdigit():
        level = int(suffix)
        if 1 <= level <= 5:
            return level
    return None


def _concern(
    category: str,
    severity: str,
    signal: str,
    message: str,
) -> dict[str, object]:
    return {
        "category": category,
        "severity": severity,
        "signal": signal,
        "message": message,
    }


def _compact_examples(examples: Sequence[object]) -> str:
    parts: list[str] = []
    for raw in examples:
        row = _mapping(raw)
        parts.append(
            f"{row.get('label')}={row.get('value')} "
            f"(rank={row.get('core_rank')}, state={row.get('candidate_state')})"
        )
    return "; ".join(parts)


def _compact_counts(value: object) -> str:
    mapping = _mapping(value)
    return ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def _array_float(array: object, index: int) -> float | None:
    value = float(np.asarray(array)[index])
    return None if not np.isfinite(value) else value


def _rounded(value: float) -> float:
    return round(float(value), 6)


def _rounded_optional(value: float | None) -> float | None:
    return None if value is None else _rounded(value)


def _string_tuple(values: object) -> tuple[str, ...]:
    return tuple(str(value) for value in np.asarray(values).tolist())


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return value
    return ()


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
