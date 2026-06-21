#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reading_specific_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reading_specific_audit_en_ja_latest.md"
)
ROW_SIGNALS = (
    "frequency",
    "frequency_tail80",
    "frequency_unranked_risk",
    "bccwj_domain_rank_coverage",
    "jlpt_vocab_difficulty",
    "jlpt_vocab_beginner_core",
    "lesson_vocab_beginner_core",
    "jmdict_priority",
    "jmdict_marked_usage_risk",
    "jmdict_register_marked_risk",
    "jmdict_reading_form_marked_risk",
    "jmdict_reading_restricted_risk",
    "jmdict_kana_preferred_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
    "wtype_wago_ease",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
    "max_written_form_burden",
    "named_entity_risk",
)
DATASET_ORDER = ("calibration", "holdout", "stitch_validation")


@dataclass(frozen=True)
class ReadingFloorSpec:
    spec_id: str
    family: str
    floor: float
    rare_min: float
    frequency_min: float
    common_frequency_max: float
    common_rank_max: float
    protect_beginner_core: bool


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit marked-form/register en-ja difficulty failures and probe "
            "bounded sidecar upshift floors without changing runtime behavior."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--leaderboard-limit", type=int, default=30)
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
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    anchor_model: str,
    leaderboard_limit: int,
    detail_limit: int,
) -> dict[str, object]:
    component_payload = np.load(component_matrix_path)
    component_view = ComponentView.from_npz(component_payload)
    matrix_view = MatrixView.from_npz(np.load(component_matrix_path))
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
    source_pair = _load_json(source_pair_json_path)
    lookup = component_lookup(component_payload)
    scalar_rows = [
        row
        for row in source_pair.get("rows", ())
        if isinstance(row, Mapping) and row.get("target") == "scalar_vocab"
    ]
    rows = rows_with_signals(
        scalar_rows,
        lookup=lookup,
        matrix=matrix_view,
        anchor_scores=np.asarray(score_arrays[anchor_model], dtype=np.float32),
    )
    segment_rows = {
        segment_id: [row for row in rows if segment_id in row.get("segments", ())]
        for segment_id in segment_definitions()
    }
    candidates = [candidate_report(rows, spec) for spec in reading_floor_specs()]
    ranked = sorted(candidates, key=candidate_rank_key, reverse=True)
    best = next((row for row in ranked if row.get("passes_guardrails")), ranked[0])
    best_spec = spec_from_payload(_mapping(best.get("spec")))
    best_rows = adjusted_rows_for_spec(rows, best_spec)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": True,
        "method": {
            "purpose": (
                "Test whether marked-form/register signals can drive a bounded "
                "difficulty upshift without regressing common readings, source-pair "
                "review rows, or rare wago tail rows."
            ),
            "anchor_model": anchor_model,
            "guardrail_policy": (
                "Promising candidates must improve stitch-validation reading rows, "
                "avoid negative all-row MAE on calibration/holdout/validation, "
                "produce no changed-row or success-row regressions, and change no "
                "source-pair-review rows."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "anchor_model": anchor_model,
            "rows": len(rows),
            **resolved_ids,
        },
        "segment_definitions": segment_definitions(),
        "dataset_summary": dataset_summary(rows),
        "segment_summary": {
            segment_id: segment_report(segment_id, segment_rows[segment_id])
            for segment_id in segment_definitions()
        },
        "candidate_space": candidate_space_summary(),
        "summary": {
            "candidate_count": len(candidates),
            "best_candidate_id": best.get("candidate_id"),
            "best_passes_guardrails": best.get("passes_guardrails"),
            "best": best,
            "interpretation": interpretation(best, segment_rows),
        },
        "leaderboard": ranked[:leaderboard_limit],
        "best_changed_rows": changed_rows_by_dataset(best_rows, detail_limit=detail_limit),
        "best_regression_rows": regression_rows_by_dataset(
            best_rows,
            detail_limit=detail_limit,
        ),
        "best_full_matrix_review": full_matrix_review_pack(
            matrix_view,
            best_spec,
            anchor_scores=np.asarray(score_arrays[anchor_model], dtype=np.float32),
            detail_limit=detail_limit,
        ),
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
                "reading_specific_audit": Path(__file__),
                "cleaned_lane_eval": SCRIPT_DIR
                / "srs_learner_difficulty_cleaned_lane_eval_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def rows_with_signals(
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
        observed = float(anchor_scores[index])
        signals = signal_snapshot(index, matrix=matrix)
        payload = {
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
            "signals": signals,
        }
        payload["segments"] = segment_memberships(payload)
        result.append(payload)
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


def segment_definitions() -> dict[str, str]:
    return {
        "reading_signal_any": (
            "Any selected reading-risk, reading-marked, or reading-restricted signal is active."
        ),
        "source_pair_review": "Scalar row is not JMDict-exact for the lemma/reading pair.",
        "marked_or_restricted_reading": (
            "JMDict marks or restricts the reading/form, independent of KANJIDIC."
        ),
        "nonstandard_reading_any": ("KANJIDIC-derived nonstandard-reading risk is high."),
        "rare_reading_tail": ("Nonstandard-reading risk is also in the rare/high-tail region."),
        "rare_wago_reading_tail": ("Rare-reading tail signal on a wago/native row."),
        "common_nonstandard_false_positive_risk": (
            "Nonstandard-reading risk on a common or beginner-protected row."
        ),
        "kango_marked_or_restricted": ("Kango row with JMDict marked/restricted reading evidence."),
        "upshift_candidate": (
            "Narrow runtime-shaped candidate for an upshift floor: reading evidence, "
            "not common-protected, and tail/unranked/marked evidence."
        ),
    }


def segment_memberships(row: Mapping[str, object]) -> list[str]:
    signals = _mapping(row.get("signals"))
    segments: list[str] = []
    if reading_signal_strength(row) >= 0.5:
        segments.append("reading_signal_any")
    if source_pair_review(row):
        segments.append("source_pair_review")
    if marked_or_restricted_reading(row) >= 0.5:
        segments.append("marked_or_restricted_reading")
    if _float_signal(signals, "non_standard_reading_risk") >= 0.75:
        segments.append("nonstandard_reading_any")
    if _float_signal(signals, "rare_non_standard_reading_risk") >= 0.5:
        segments.append("rare_reading_tail")
    if (
        _float_signal(signals, "rare_wago_non_standard_reading_risk") >= 0.5
        and _float_signal(signals, "wtype_wago_ease") >= 0.75
    ):
        segments.append("rare_wago_reading_tail")
    if common_nonstandard_false_positive_risk(row):
        segments.append("common_nonstandard_false_positive_risk")
    if (
        _float_signal(signals, "wtype_kango_risk") >= 0.75
        and marked_or_restricted_reading(row) >= 0.5
    ):
        segments.append("kango_marked_or_restricted")
    if upshift_candidate(row):
        segments.append("upshift_candidate")
    return segments


def reading_signal_strength(row: Mapping[str, object]) -> float:
    signals = _mapping(row.get("signals"))
    return max(
        _float_signal(signals, "non_standard_reading_risk"),
        _float_signal(signals, "rare_non_standard_reading_risk"),
        _float_signal(signals, "rare_wago_non_standard_reading_risk"),
        _float_signal(signals, "jmdict_reading_form_marked_risk"),
        _float_signal(signals, "jmdict_reading_restricted_risk"),
    )


def source_pair_review(row: Mapping[str, object]) -> bool:
    status = row.get("primary_pair_status")
    return status is not None and status != "jmdict_exact"


def marked_or_restricted_reading(row: Mapping[str, object]) -> float:
    signals = _mapping(row.get("signals"))
    return max(
        _float_signal(signals, "jmdict_reading_form_marked_risk"),
        _float_signal(signals, "jmdict_reading_restricted_risk"),
    )


def common_protected(row: Mapping[str, object], *, spec: ReadingFloorSpec) -> bool:
    signals = _mapping(row.get("signals"))
    rank = _optional_float(row.get("core_rank"))
    beginner_core = max(
        _float_signal(signals, "jlpt_vocab_beginner_core"),
        _float_signal(signals, "lesson_vocab_beginner_core"),
    )
    frequency = _float_signal(signals, "frequency")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    return (
        (frequency <= spec.common_frequency_max and unranked < 0.5)
        or (rank is not None and rank <= spec.common_rank_max)
        or (spec.protect_beginner_core and beginner_core >= 0.1)
    )


def common_nonstandard_false_positive_risk(row: Mapping[str, object]) -> bool:
    signals = _mapping(row.get("signals"))
    rank = _optional_float(row.get("core_rank"))
    return (
        _float_signal(signals, "non_standard_reading_risk") >= 0.75
        and _float_signal(signals, "rare_non_standard_reading_risk") < 0.1
        and (
            _float_signal(signals, "frequency") <= 0.65
            or _float_signal(signals, "jlpt_vocab_beginner_core") >= 0.1
            or _float_signal(signals, "lesson_vocab_beginner_core") >= 0.1
            or (rank is not None and rank <= 5000)
        )
    )


def upshift_candidate(row: Mapping[str, object]) -> bool:
    signals = _mapping(row.get("signals"))
    spec = ReadingFloorSpec(
        spec_id="default_upshift_candidate",
        family="hybrid",
        floor=0.5,
        rare_min=0.25,
        frequency_min=0.8,
        common_frequency_max=0.65,
        common_rank_max=3000.0,
        protect_beginner_core=False,
    )
    if source_pair_review(row) or common_protected(row, spec=spec):
        return False
    rare = _float_signal(signals, "rare_non_standard_reading_risk")
    nonstandard = _float_signal(signals, "non_standard_reading_risk")
    frequency = _float_signal(signals, "frequency")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    return reading_signal_strength(row) >= 0.5 and (
        rare >= 0.25
        or (nonstandard >= 0.75 and unranked >= 0.5)
        or (marked_or_restricted_reading(row) >= 0.5 and frequency >= 0.8)
    )


def reading_floor_specs() -> list[ReadingFloorSpec]:
    specs: list[ReadingFloorSpec] = []
    for family in (
        "rare_tail",
        "unranked_nonstandard",
        "marked_tail",
        "kango_marked",
        "hybrid",
    ):
        for floor in (0.38, 0.46, 0.54, 0.62):
            for rare_min in (0.25, 0.5, 0.75):
                for frequency_min in (0.8, 0.9):
                    for common_frequency_max in (0.6, 0.65, 0.7):
                        for protect_beginner_core in (False, True):
                            specs.append(
                                ReadingFloorSpec(
                                    spec_id=spec_id(
                                        family=family,
                                        floor=floor,
                                        rare_min=rare_min,
                                        frequency_min=frequency_min,
                                        common_frequency_max=common_frequency_max,
                                        protect_beginner_core=protect_beginner_core,
                                    ),
                                    family=family,
                                    floor=floor,
                                    rare_min=rare_min,
                                    frequency_min=frequency_min,
                                    common_frequency_max=common_frequency_max,
                                    common_rank_max=3000.0,
                                    protect_beginner_core=protect_beginner_core,
                                )
                            )
    return specs


def spec_id(
    *,
    family: str,
    floor: float,
    rare_min: float,
    frequency_min: float,
    common_frequency_max: float,
    protect_beginner_core: bool,
) -> str:
    return (
        f"read_{family}_f{id_float(floor)}_r{id_float(rare_min)}"
        f"_t{id_float(frequency_min)}_c{id_float(common_frequency_max)}"
        f"_pbc{1 if protect_beginner_core else 0}"
    )


def id_float(value: float) -> str:
    return f"{value:.2f}".replace("0.", "").replace(".", "p")


def adjusted_rows_for_spec(
    rows: Sequence[Mapping[str, object]],
    spec: ReadingFloorSpec,
) -> list[dict[str, object]]:
    return [dict(row) | adjusted_payload(row, spec) for row in rows]


def adjusted_payload(row: Mapping[str, object], spec: ReadingFloorSpec) -> dict[str, object]:
    observed = _float_or_nan(row.get("anchor_observed"))
    expected = _float_or_nan(row.get("expected"))
    floor = spec.floor if policy_matches(row, spec) else None
    adjusted = observed if floor is None else max(observed, floor)
    return {
        "adjusted_observed": _rounded(adjusted),
        "adjusted_abs_error": _rounded(abs(expected - adjusted)),
        "adjusted_band": _difficulty_band(adjusted),
        "changed": floor is not None and adjusted > observed + 1e-9,
        "policy_floor": floor,
        "policy_reason": "marked_form_register_floor" if floor is not None else "not_matched",
    }


def policy_matches(row: Mapping[str, object], spec: ReadingFloorSpec) -> bool:
    if (
        reading_signal_strength(row) < 0.5
        or source_pair_review(row)
        or common_protected(row, spec=spec)
    ):
        return False
    return raw_family_matches(row, spec)


def raw_family_matches(row: Mapping[str, object], spec: ReadingFloorSpec) -> bool:
    signals = _mapping(row.get("signals"))
    rare = _float_signal(signals, "rare_non_standard_reading_risk")
    rare_wago = _float_signal(signals, "rare_wago_non_standard_reading_risk")
    nonstandard = _float_signal(signals, "non_standard_reading_risk")
    frequency = _float_signal(signals, "frequency")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    marked = marked_or_restricted_reading(row)
    kango = _float_signal(signals, "wtype_kango_risk")
    if spec.family == "rare_tail":
        return rare >= spec.rare_min
    if spec.family == "unranked_nonstandard":
        return nonstandard >= 0.75 and unranked >= 0.5
    if spec.family == "marked_tail":
        return marked >= 0.5 and frequency >= spec.frequency_min
    if spec.family == "kango_marked":
        return kango >= 0.75 and marked >= 0.5
    if spec.family == "hybrid":
        return (
            rare >= spec.rare_min
            or rare_wago >= spec.rare_min
            or (nonstandard >= 0.75 and unranked >= 0.5)
            or (marked >= 0.5 and frequency >= spec.frequency_min)
        )
    raise ValueError(f"Unknown reading floor family: {spec.family}")


def candidate_report(
    rows: Sequence[Mapping[str, object]],
    spec: ReadingFloorSpec,
) -> dict[str, object]:
    adjusted = adjusted_rows_for_spec(rows, spec)
    datasets = {
        dataset_id: curve_result([row for row in adjusted if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }
    return {
        "candidate_id": spec.spec_id,
        "spec": spec_payload(spec),
        "passes_guardrails": passes_guardrails(datasets),
        "datasets": datasets,
        "summary": candidate_summary(datasets),
    }


def curve_result(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    reading_rows = [row for row in rows if "reading_signal_any" in row.get("segments", ())]
    changed_rows = [row for row in rows if row.get("changed")]
    regressions = [
        row
        for row in changed_rows
        if float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    success_regressions = [
        row
        for row in changed_rows
        if float(row.get("anchor_abs_error") or 0.0) <= 0.08
        and float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    return {
        "row_count": len(rows),
        "reading_count": len(reading_rows),
        "changed_count": len(changed_rows),
        "changed_source_pair_review_count": len(
            [row for row in changed_rows if "source_pair_review" in row.get("segments", ())]
        ),
        "changed_common_false_positive_count": len(
            [
                row
                for row in changed_rows
                if "common_nonstandard_false_positive_risk" in row.get("segments", ())
            ]
        ),
        "changed_regressions": len(regressions),
        "success_regressions": len(success_regressions),
        "all_rows": metrics_for_rows(rows),
        "reading_rows": metrics_for_rows(reading_rows),
        "changed_rows": metrics_for_rows(changed_rows),
    }


def metrics_for_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    expected = np.asarray([_float_or_nan(row.get("expected")) for row in rows], dtype=np.float32)
    anchor = np.asarray(
        [_float_or_nan(row.get("anchor_observed")) for row in rows],
        dtype=np.float32,
    )
    adjusted = np.asarray(
        [_float_or_nan(row.get("adjusted_observed", row.get("anchor_observed"))) for row in rows],
        dtype=np.float32,
    )
    labels = [str(row.get("label")) for row in rows]
    expected_bands = [str(row.get("expected_band")) for row in rows]
    anchor_summary = _summary_metrics(
        _difficulty_metrics(
            expected_values=expected,
            observed_values=anchor,
            expected_bands=expected_bands,
            labels=labels,
        )
    )
    adjusted_summary = _summary_metrics(
        _difficulty_metrics(
            expected_values=expected,
            observed_values=adjusted,
            expected_bands=expected_bands,
            labels=labels,
        )
    )
    return {
        "count": len(rows),
        "anchor": anchor_summary,
        "adjusted": adjusted_summary,
        "delta": {
            "mae_reduction": _rounded(
                float(anchor_summary.get("mae") or 0.0) - float(adjusted_summary.get("mae") or 0.0)
            ),
            "bucket_delta": _rounded(
                float(adjusted_summary.get("bucket_accuracy") or 0.0)
                - float(anchor_summary.get("bucket_accuracy") or 0.0)
            ),
            "pairwise_delta": _rounded(
                float(adjusted_summary.get("pairwise_accuracy") or 0.0)
                - float(anchor_summary.get("pairwise_accuracy") or 0.0)
            ),
        },
    }


def passes_guardrails(datasets: Mapping[str, Mapping[str, object]]) -> bool:
    validation = _mapping(datasets.get("stitch_validation"))
    validation_reading_delta = metric_delta(validation, "reading_rows", "mae_reduction")
    if validation_reading_delta <= 0.0:
        return False
    for dataset_id in DATASET_ORDER:
        dataset = _mapping(datasets.get(dataset_id))
        if int(dataset.get("changed_source_pair_review_count") or 0) > 0:
            return False
        if int(dataset.get("changed_regressions") or 0) > 0:
            return False
        if int(dataset.get("success_regressions") or 0) > 0:
            return False
        if metric_delta(dataset, "all_rows", "mae_reduction") < -0.000001:
            return False
    return True


def candidate_summary(datasets: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        dataset_id: {
            "all_mae_reduction": metric_delta(dataset, "all_rows", "mae_reduction"),
            "reading_mae_reduction": metric_delta(
                dataset,
                "reading_rows",
                "mae_reduction",
            ),
            "changed_count": _mapping(dataset).get("changed_count"),
            "changed_source_pair_review_count": _mapping(dataset).get(
                "changed_source_pair_review_count"
            ),
            "changed_common_false_positive_count": _mapping(dataset).get(
                "changed_common_false_positive_count"
            ),
            "changed_regressions": _mapping(dataset).get("changed_regressions"),
            "success_regressions": _mapping(dataset).get("success_regressions"),
        }
        for dataset_id, dataset in datasets.items()
    }


def candidate_rank_key(candidate: Mapping[str, object]) -> tuple[float, ...]:
    datasets = _mapping(candidate.get("datasets"))
    validation = _mapping(datasets.get("stitch_validation"))
    holdout = _mapping(datasets.get("holdout"))
    calibration = _mapping(datasets.get("calibration"))
    return (
        1.0 if candidate.get("passes_guardrails") else 0.0,
        metric_delta(validation, "reading_rows", "mae_reduction"),
        metric_delta(validation, "all_rows", "mae_reduction"),
        metric_delta(holdout, "all_rows", "mae_reduction"),
        metric_delta(calibration, "all_rows", "mae_reduction"),
        -float(_mapping(validation).get("changed_regressions") or 0.0),
        -float(_mapping(holdout).get("changed_regressions") or 0.0),
    )


def metric_delta(dataset: Mapping[str, object], scope: str, key: str) -> float:
    metrics = _mapping(dataset.get(scope))
    return float(_mapping(metrics.get("delta")).get(key) or 0.0)


def dataset_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        dataset_id: segment_report(
            "all_scalar",
            [row for row in rows if row.get("dataset_id") == dataset_id],
        )
        for dataset_id in DATASET_ORDER
    }


def segment_report(segment_id: str, rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_dataset = {
        dataset_id: base_row_stats([row for row in rows if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }
    return {
        "segment_id": segment_id,
        "count": len(rows),
        "by_dataset": by_dataset,
        "overall": base_row_stats(rows),
    }


def base_row_stats(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "count": 0,
            "mae": None,
            "mean_observed_minus_expected": None,
            "too_low": 0,
            "too_high": 0,
        }
    errors = [
        float(row.get("anchor_observed") or 0.0) - float(row.get("expected") or 0.0) for row in rows
    ]
    return {
        "count": len(rows),
        "mae": _rounded(
            sum(abs(float(row.get("anchor_abs_error") or 0.0)) for row in rows) / len(rows)
        ),
        "mean_observed_minus_expected": _rounded(sum(errors) / len(errors)),
        "too_low": len([row for row in rows if row.get("anchor_direction") == "too_low"]),
        "too_high": len([row for row in rows if row.get("anchor_direction") == "too_high"]),
    }


def changed_rows_by_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    return {
        dataset_id: sorted(
            [row for row in rows if row.get("dataset_id") == dataset_id and row.get("changed")],
            key=lambda row: float(row.get("anchor_abs_error") or 0.0),
            reverse=True,
        )[:detail_limit]
        for dataset_id in DATASET_ORDER
    }


def regression_rows_by_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    return {
        dataset_id: sorted(
            [
                row
                for row in rows
                if row.get("dataset_id") == dataset_id
                and row.get("changed")
                and float(row.get("adjusted_abs_error") or 0.0)
                > float(row.get("anchor_abs_error") or 0.0) + 1e-9
            ],
            key=lambda row: (
                float(row.get("adjusted_abs_error") or 0.0)
                - float(row.get("anchor_abs_error") or 0.0)
            ),
            reverse=True,
        )[:detail_limit]
        for dataset_id in DATASET_ORDER
    }


def full_matrix_review_pack(
    matrix: MatrixView,
    spec: ReadingFloorSpec,
    *,
    anchor_scores: np.ndarray,
    detail_limit: int,
) -> dict[str, object]:
    would_match: list[dict[str, object]] = []
    would_change: list[dict[str, object]] = []
    common_protected: list[dict[str, object]] = []
    for index, lemma in enumerate(matrix.lemmas):
        if matrix.candidate_states[index] != "normal_vocab":
            continue
        row = matrix_review_row(index, matrix=matrix, anchor_scores=anchor_scores)
        if policy_matches(row, spec):
            would_match.append(review_pack_row(row, spec, reason="would_match"))
            if float(row.get("anchor_observed") or 0.0) < spec.floor:
                would_change.append(review_pack_row(row, spec, reason="would_change"))
        elif common_protected_near_miss(row, spec):
            common_protected.append(review_pack_row(row, spec, reason="common_protected_near_miss"))
    would_match.sort(key=review_pack_sort_key, reverse=True)
    would_change.sort(key=review_pack_sort_key, reverse=True)
    common_protected.sort(key=review_pack_sort_key, reverse=True)
    return {
        "candidate_id": spec.spec_id,
        "would_match_count": len(would_match),
        "would_change_count": len(would_change),
        "common_protected_near_miss_count": len(common_protected),
        "would_match_examples": would_match[:detail_limit],
        "would_change_examples": would_change[:detail_limit],
        "common_protected_near_miss_examples": common_protected[:detail_limit],
    }


def matrix_review_row(
    index: int,
    *,
    matrix: MatrixView,
    anchor_scores: np.ndarray,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "dataset_id": "full_matrix",
        "label": f"{matrix.lemmas[index]}/{matrix.readings[index]}",
        "lemma": matrix.lemmas[index],
        "reading": matrix.readings[index],
        "anchor_observed": _rounded(float(anchor_scores[index])),
        "candidate_state": matrix.candidate_states[index],
        "problem_class": matrix.problem_classes[index],
        "core_rank": _rounded(float(matrix.core_ranks[index])),
        "primary_pair_status": None,
        "signals": signal_snapshot(index, matrix=matrix),
    }
    payload["segments"] = segment_memberships(payload)
    return payload


def common_protected_near_miss(
    row: Mapping[str, object],
    spec: ReadingFloorSpec,
) -> bool:
    return (
        reading_signal_strength(row) >= 0.5
        and raw_family_matches(row, spec)
        and common_protected(row, spec=spec)
    )


def review_pack_row(
    row: Mapping[str, object],
    spec: ReadingFloorSpec,
    *,
    reason: str,
) -> dict[str, object]:
    return {
        "label": row.get("label"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "core_rank": row.get("core_rank"),
        "anchor_observed": row.get("anchor_observed"),
        "policy_floor": spec.floor,
        "would_change": float(row.get("anchor_observed") or 0.0) < spec.floor,
        "review_reason": reason,
        "reason_flags": reason_flags(row),
        "segments": row.get("segments"),
        "signals": row.get("signals"),
    }


def reason_flags(row: Mapping[str, object]) -> list[str]:
    signals = _mapping(row.get("signals"))
    flags = []
    if marked_or_restricted_reading(row) >= 0.5:
        flags.append("marked_or_restricted")
    if _float_signal(signals, "rare_non_standard_reading_risk") >= 0.5:
        flags.append("rare_reading_tail")
    if _float_signal(signals, "rare_wago_non_standard_reading_risk") >= 0.5:
        flags.append("rare_wago_reading_tail")
    if _float_signal(signals, "frequency_unranked_risk") >= 0.5:
        flags.append("unranked_frequency")
    if _float_signal(signals, "wtype_kango_risk") >= 0.75:
        flags.append("kango")
    if _float_signal(signals, "wtype_wago_ease") >= 0.75:
        flags.append("wago")
    if _float_signal(signals, "named_entity_risk") >= 0.5:
        flags.append("entity_overlap")
    return flags


def review_pack_sort_key(row: Mapping[str, object]) -> tuple[float, ...]:
    signals = _mapping(row.get("signals"))
    return (
        marked_or_restricted_reading(row),
        _float_signal(signals, "rare_non_standard_reading_risk"),
        _float_signal(signals, "rare_wago_non_standard_reading_risk"),
        _float_signal(signals, "frequency_unranked_risk"),
        _float_signal(signals, "frequency"),
    )


def candidate_space_summary() -> dict[str, object]:
    return {
        "families": [
            "rare_tail",
            "unranked_nonstandard",
            "marked_tail",
            "kango_marked",
            "hybrid",
        ],
        "floors": [0.38, 0.46, 0.54, 0.62],
        "rare_thresholds": [0.25, 0.5, 0.75],
        "tail_frequency_thresholds": [0.8, 0.9],
        "common_frequency_protection": [0.6, 0.65, 0.7],
        "protect_beginner_core": [False, True],
        "candidate_count": len(reading_floor_specs()),
    }


def interpretation(
    best: Mapping[str, object],
    segment_rows: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    best_summary = _mapping(best.get("summary"))
    holdout = _mapping(best_summary.get("holdout"))
    validation = _mapping(best_summary.get("stitch_validation"))
    common_false_positive = segment_report(
        "common_nonstandard_false_positive_risk",
        segment_rows.get("common_nonstandard_false_positive_risk", ()),
    )
    rare_tail = segment_report(
        "rare_reading_tail",
        segment_rows.get("rare_reading_tail", ()),
    )
    return {
        "best_passes_guardrails": bool(best.get("passes_guardrails")),
        "promotion_readiness": (
            "review_only_candidate_not_runtime_promotable"
            if best.get("passes_guardrails")
            else "not_promotable_from_current_probe"
        ),
        "validation_reading_delta": validation.get("reading_mae_reduction"),
        "holdout_all_delta": holdout.get("all_mae_reduction"),
        "best_changed_source_pair_review_count": sum(
            int(_mapping(row).get("changed_source_pair_review_count") or 0)
            for row in best_summary.values()
            if isinstance(row, Mapping)
        ),
        "best_changed_common_false_positive_count": sum(
            int(_mapping(row).get("changed_common_false_positive_count") or 0)
            for row in best_summary.values()
            if isinstance(row, Mapping)
        ),
        "common_nonstandard_false_positive_count": common_false_positive.get("count"),
        "rare_tail_count": rare_tail.get("count"),
        "main_caveat": (
            "The broad nonstandard-reading signal is not semantically clean: it "
            "fires on many common learner words and on rare wago tail rows whose "
            "failure direction is often too_high, not too_low. This sweep is "
            "exploratory and uses all labeled splits for diagnosis, so a passing "
            "probe is a review target, not runtime promotion evidence."
        ),
    }


def spec_payload(spec: ReadingFloorSpec) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "family": spec.family,
        "floor": spec.floor,
        "rare_min": spec.rare_min,
        "frequency_min": spec.frequency_min,
        "common_frequency_max": spec.common_frequency_max,
        "common_rank_max": spec.common_rank_max,
        "protect_beginner_core": spec.protect_beginner_core,
    }


def spec_from_payload(payload: Mapping[str, object]) -> ReadingFloorSpec:
    return ReadingFloorSpec(
        spec_id=str(payload.get("spec_id") or ""),
        family=str(payload.get("family") or "hybrid"),
        floor=float(payload.get("floor") or 0.5),
        rare_min=float(payload.get("rare_min") or 0.25),
        frequency_min=float(payload.get("frequency_min") or 0.8),
        common_frequency_max=float(payload.get("common_frequency_max") or 0.65),
        common_rank_max=float(payload.get("common_rank_max") or 3000.0),
        protect_beginner_core=bool(payload.get("protect_beginner_core")),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Reading-Specific Failure Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        f"Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        "",
        "## Interpretation",
        "",
    ]
    for key, value in _mapping(summary.get("interpretation")).items():
        lines.append(f"- `{_escape(key)}`: `{_escape(display_value(value))}`")
    lines.extend(["", "## Dataset Summary", ""])
    lines.extend(dataset_summary_table(_mapping(report.get("dataset_summary"))))
    lines.extend(["", "## Segment Summary", ""])
    lines.extend(segment_summary_table(_mapping(report.get("segment_summary"))))
    lines.extend(["", "## Candidate Space", ""])
    lines.extend(candidate_space_lines(_mapping(report.get("candidate_space"))))
    lines.extend(["", "## Probe Leaderboard", ""])
    lines.extend(leaderboard_table(_rows(report.get("leaderboard"))))
    lines.extend(["", "## Best Candidate Changed Rows", ""])
    for dataset_id, rows in _mapping(report.get("best_changed_rows")).items():
        lines.extend([f"### `{_escape(dataset_id)}`", ""])
        lines.extend(row_table(_rows(rows)))
        lines.append("")
    lines.extend(["## Best Candidate Regression Rows", ""])
    for dataset_id, rows in _mapping(report.get("best_regression_rows")).items():
        lines.extend([f"### `{_escape(dataset_id)}`", ""])
        lines.extend(row_table(_rows(rows)))
        lines.append("")
    full_matrix = _mapping(report.get("best_full_matrix_review"))
    lines.extend(["## Full-Matrix Would-Fire Review", ""])
    lines.append(f"- Candidate: `{_escape(full_matrix.get('candidate_id'))}`")
    lines.append(f"- Would-match count: `{_escape(full_matrix.get('would_match_count'))}`")
    lines.append(f"- Would-change count: `{_escape(full_matrix.get('would_change_count'))}`")
    lines.append(
        "- Common-protected near-miss count: "
        f"`{_escape(full_matrix.get('common_protected_near_miss_count'))}`"
    )
    lines.extend(["", "### Would-Change Examples", ""])
    lines.extend(review_pack_table(_rows(full_matrix.get("would_change_examples"))))
    lines.extend(["", "### Would-Match Examples", ""])
    lines.extend(review_pack_table(_rows(full_matrix.get("would_match_examples"))))
    lines.extend(["", "### Common-Protected Near Misses", ""])
    lines.extend(review_pack_table(_rows(full_matrix.get("common_protected_near_miss_examples"))))
    return "\n".join(lines).rstrip() + "\n"


def dataset_summary_table(summary: Mapping[str, object]) -> list[str]:
    lines = [
        "| Dataset | Rows | MAE | Bias obs-exp | Too low | Too high |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_id, row in summary.items():
        parsed = _mapping(_mapping(row).get("overall"))
        lines.append(
            f"| `{_escape(dataset_id)}` | "
            f"{_escape(parsed.get('count'))} | "
            f"{_escape(parsed.get('mae'))} | "
            f"{_escape(parsed.get('mean_observed_minus_expected'))} | "
            f"{_escape(parsed.get('too_low'))} | "
            f"{_escape(parsed.get('too_high'))} |"
        )
    return lines


def segment_summary_table(summary: Mapping[str, object]) -> list[str]:
    lines = [
        "| Segment | Count | Overall MAE | Bias obs-exp | Calib | Holdout | Validation |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for segment_id, row in summary.items():
        parsed = _mapping(row)
        overall = _mapping(parsed.get("overall"))
        by_dataset = _mapping(parsed.get("by_dataset"))
        lines.append(
            f"| `{_escape(segment_id)}` | "
            f"{_escape(parsed.get('count'))} | "
            f"{_escape(overall.get('mae'))} | "
            f"{_escape(overall.get('mean_observed_minus_expected'))} | "
            f"{_escape(_mapping(by_dataset.get('calibration')).get('count'))} | "
            f"{_escape(_mapping(by_dataset.get('holdout')).get('count'))} | "
            f"{_escape(_mapping(by_dataset.get('stitch_validation')).get('count'))} |"
        )
    return lines


def candidate_space_lines(space: Mapping[str, object]) -> list[str]:
    return [
        f"- Candidate count: `{_escape(space.get('candidate_count'))}`",
        f"- Families: `{_escape(', '.join(str(item) for item in _sequence(space.get('families'))))}`",
        f"- Floors: `{_escape(_sequence(space.get('floors')))}`",
        f"- Rare thresholds: `{_escape(_sequence(space.get('rare_thresholds')))}`",
        f"- Tail frequency thresholds: `{_escape(_sequence(space.get('tail_frequency_thresholds')))}`",
    ]


def leaderboard_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Candidate | Pass | Val reading ΔMAE | Val all ΔMAE | Holdout all ΔMAE | Calib all ΔMAE | Source-pair changes | Val regressions | Holdout regressions |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        summary = _mapping(row.get("summary"))
        validation = _mapping(summary.get("stitch_validation"))
        holdout = _mapping(summary.get("holdout"))
        calibration = _mapping(summary.get("calibration"))
        source_pair_changes = sum(
            int(_mapping(dataset).get("changed_source_pair_review_count") or 0)
            for dataset in summary.values()
            if isinstance(dataset, Mapping)
        )
        lines.append(
            f"| `{_escape(row.get('candidate_id'))}` | "
            f"{_escape(row.get('passes_guardrails'))} | "
            f"{_escape(validation.get('reading_mae_reduction'))} | "
            f"{_escape(validation.get('all_mae_reduction'))} | "
            f"{_escape(holdout.get('all_mae_reduction'))} | "
            f"{_escape(calibration.get('all_mae_reduction'))} | "
            f"{_escape(source_pair_changes)} | "
            f"{_escape(validation.get('changed_regressions'))} | "
            f"{_escape(holdout.get('changed_regressions'))} |"
        )
    return lines


def row_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | Expected | Anchor | Adjusted | Anchor Err | Adj Err | Status | Segments | Freq | Rare | Marked |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |",
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
            f"`{_escape(row.get('primary_pair_status'))}` | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('segments'))))} | "
            f"{_escape(signals.get('frequency'))} | "
            f"{_escape(signals.get('rare_non_standard_reading_risk'))} | "
            f"{_escape(marked_or_restricted_reading(row))} |"
        )
    return lines


def review_pack_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | State | Anchor | Floor | Rank | Flags | Segments | Freq | Rare | Marked | Entity |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        lines.append(
            f"| {_escape(row.get('label'))} | "
            f"`{_escape(row.get('candidate_state'))}` | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('policy_floor'))} | "
            f"{_escape(row.get('core_rank'))} | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('reason_flags'))))} | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('segments'))))} | "
            f"{_escape(signals.get('frequency'))} | "
            f"{_escape(signals.get('rare_non_standard_reading_risk'))} | "
            f"{_escape(marked_or_restricted_reading(row))} | "
            f"{_escape(signals.get('named_entity_risk'))} |"
        )
    return lines


def display_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = _optional_float(signals.get(signal))
    return 0.0 if value is None else float(value)


def _float_or_nan(value: object) -> float:
    parsed = _optional_float(value)
    return float("nan") if parsed is None else float(parsed)


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


if __name__ == "__main__":
    raise SystemExit(main())
