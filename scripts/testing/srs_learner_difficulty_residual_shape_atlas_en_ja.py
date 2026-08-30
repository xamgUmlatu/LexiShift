#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_method_sample_compare_en_ja import (  # noqa: E402
    _select_old_trace_record,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_CHALLENGE_OFFSET,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_PROFICIENCY_POINTS,
    DEFAULT_TRACE_JSON,
    DEFAULT_WINDOW_SIGMA,
    DEFAULT_WINDOW_TOP_K,
    _calibration_context,
    _component_context,
    _escape,
    _label_context_from_json,
    _load_json,
    _mapping,
    _normalized_values_for_trace_record,
    _optional_float,
    _parse_float_csv,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_proficiency_ordering_stability_en_ja import (  # noqa: E402
    DEFAULT_FOLD_COUNT,
    _stratified_fold_masks,
    _subset_context,
)
from srs_learner_difficulty_structured_failure_groups_en_ja import (  # noqa: E402
    GroupSpec,
    GroupTerm,
    _bounded_residual_delta,
    _compact_dataset_report,
    _context_group_mask,
    _dataset_report,
    _fold_correction_report,
    _fold_delta_summary,
    _group_mask,
    _group_summary,
    _guardrail_flags,
    _normal_vocab_mae_reduction,
    _residual_profile,
    _residual_structure_score,
    _scope_for_count,
    _score_delta,
    _selector_score,
    _signal_arrays,
    _term_dict,
    generate_group_specs,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_atlas_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_atlas_en_ja_latest.md"
)
DEFAULT_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_atlas_en_ja_latest.csv"
)
DEFAULT_BASE_BANDS = "0.00:0.20,0.20:0.40,0.40:0.60,0.60:0.80,0.80:1.00"
DEFAULT_ERROR_THRESHOLD = 0.20
DEFAULT_MIN_SUPPORT = 4
DEFAULT_MIN_ABS_DELTA = 0.025
DEFAULT_MAX_CORRECTION_ABS = 0.12
DEFAULT_MAX_TOTAL_CORRECTION_ABS = 0.18
DEFAULT_CORRECTION_CELL_LIMIT = 160
DEFAULT_ATLAS_RETAIN_LIMIT = 240
DEFAULT_LEADERBOARD_LIMIT = 24
DEFAULT_COMPOSITE_SIZES = (1, 2, 3, 5, 8)


@dataclass(frozen=True)
class BaseBand:
    band_id: str
    low: float
    high: float
    is_last: bool = False


@dataclass(frozen=True)
class ShapeCell:
    cell_id: str
    group: GroupSpec
    base_band: BaseBand


@dataclass(frozen=True)
class CompositeCell:
    cell_id: str
    delta: float
    mask: object


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a sidecar residual shape atlas for en-ja learner difficulty. "
            "Unlike global formula sweeps, this anchors to the current best score "
            "and looks for signed conditional residual moves by gate and base band."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--old-score-key", default="balanced_score")
    parser.add_argument("--base-bands", default=DEFAULT_BASE_BANDS)
    parser.add_argument(
        "--proficiency-points",
        default=",".join(str(value) for value in DEFAULT_PROFICIENCY_POINTS),
    )
    parser.add_argument("--challenge-offset", type=float, default=DEFAULT_CHALLENGE_OFFSET)
    parser.add_argument("--window-sigma", type=float, default=DEFAULT_WINDOW_SIGMA)
    parser.add_argument("--window-top-k", type=int, default=DEFAULT_WINDOW_TOP_K)
    parser.add_argument("--fold-count", type=int, default=DEFAULT_FOLD_COUNT)
    parser.add_argument("--error-threshold", type=float, default=DEFAULT_ERROR_THRESHOLD)
    parser.add_argument("--min-support", type=int, default=DEFAULT_MIN_SUPPORT)
    parser.add_argument("--min-abs-delta", type=float, default=DEFAULT_MIN_ABS_DELTA)
    parser.add_argument("--max-correction-abs", type=float, default=DEFAULT_MAX_CORRECTION_ABS)
    parser.add_argument(
        "--max-total-correction-abs",
        type=float,
        default=DEFAULT_MAX_TOTAL_CORRECTION_ABS,
    )
    parser.add_argument("--correction-cell-limit", type=int, default=DEFAULT_CORRECTION_CELL_LIMIT)
    parser.add_argument("--atlas-retain-limit", type=int, default=DEFAULT_ATLAS_RETAIN_LIMIT)
    parser.add_argument("--leaderboard-limit", type=int, default=DEFAULT_LEADERBOARD_LIMIT)
    parser.add_argument(
        "--composite-sizes",
        default=",".join(str(value) for value in DEFAULT_COMPOSITE_SIZES),
    )
    parser.add_argument("--detail-limit", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        holdout_json_path=_resolve_path(args.holdout_json),
        old_score_key=str(args.old_score_key),
        base_bands=_parse_base_bands(args.base_bands),
        proficiency_points=_parse_float_csv(args.proficiency_points),
        challenge_offset=float(args.challenge_offset),
        window_sigma=max(1e-6, float(args.window_sigma)),
        window_top_k=max(1, int(args.window_top_k)),
        fold_count=max(2, int(args.fold_count)),
        error_threshold=max(0.01, float(args.error_threshold)),
        min_support=max(1, int(args.min_support)),
        min_abs_delta=max(0.0, float(args.min_abs_delta)),
        max_correction_abs=max(0.01, float(args.max_correction_abs)),
        max_total_correction_abs=max(0.01, float(args.max_total_correction_abs)),
        correction_cell_limit=max(1, int(args.correction_cell_limit)),
        atlas_retain_limit=max(1, int(args.atlas_retain_limit)),
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        composite_sizes=_parse_int_csv(args.composite_sizes),
        detail_limit=max(1, int(args.detail_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    csv_out = _resolve_path(args.csv_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    csv_out.write_text(render_atlas_csv(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    print(f"Wrote atlas CSV artifact to {csv_out}")
    return 0


def build_report(
    *,
    trace_json: Path,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    holdout_json_path: Path,
    old_score_key: str,
    base_bands: Sequence[BaseBand],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    fold_count: int,
    error_threshold: float,
    min_support: int,
    min_abs_delta: float,
    max_correction_abs: float,
    max_total_correction_abs: float,
    correction_cell_limit: int,
    atlas_retain_limit: int,
    leaderboard_limit: int,
    composite_sizes: Sequence[int],
    detail_limit: int,
) -> dict[str, object]:
    trace = _load_json(trace_json)
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
    old_values = np.asarray(
        _normalized_values_for_trace_record(old_record, component_context),
        dtype=np.float32,
    )
    signal_arrays = _signal_arrays(component_context)
    group_specs = generate_group_specs(signal_arrays)
    group_masks = {spec.group_id: _group_mask(spec, signal_arrays) for spec in group_specs}
    cells = _shape_cells(group_specs, base_bands)
    cell_masks = {
        cell.cell_id: _cell_mask(cell, group_masks[cell.group.group_id], old_values)
        for cell in cells
    }
    fold_masks = _stratified_fold_masks(calibration_context, fold_count=fold_count)
    validation_contexts = tuple(
        _subset_context(
            calibration_context,
            mask,
            context_id=f"calibration_validation_{index + 1}",
        )
        for index, mask in enumerate(fold_masks)
    )
    train_contexts = tuple(
        _subset_context(
            calibration_context,
            ~np.asarray(mask, dtype=bool),
            context_id=f"calibration_train_{index + 1}",
        )
        for index, mask in enumerate(fold_masks)
    )
    reference = _reference_reports(
        old_values=old_values,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        validation_contexts=validation_contexts,
        train_contexts=train_contexts,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    atlas_rows = [
        _shape_cell_atlas_row(
            cell,
            cell_mask=cell_masks[cell.cell_id],
            old_values=old_values,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            error_threshold=error_threshold,
            detail_limit=detail_limit,
        )
        for cell in cells
    ]
    correction_candidates = _correction_candidate_cells(
        atlas_rows,
        min_support=min_support,
        min_abs_delta=min_abs_delta,
        limit=correction_cell_limit,
    )
    correction_reports = [
        _shape_cell_correction_report(
            cell,
            cell_mask=cell_masks[cell.cell_id],
            old_values=old_values,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            validation_contexts=validation_contexts,
            train_contexts=train_contexts,
            reference=reference,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            error_threshold=error_threshold,
            min_support=min_support,
            max_correction_abs=max_correction_abs,
            detail_limit=detail_limit,
        )
        for cell in correction_candidates
    ]
    stable_corrections = _stable_correction_reports(
        correction_reports,
        cell_masks=cell_masks,
        limit=max(composite_sizes) if composite_sizes else 0,
    )
    composite_reports = _composite_reports(
        stable_corrections=stable_corrections,
        cell_masks=cell_masks,
        old_values=old_values,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        reference=reference,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        max_total_correction_abs=max_total_correction_abs,
        composite_sizes=composite_sizes,
        detail_limit=detail_limit,
    )
    retained_atlas = _retained_atlas_rows(atlas_rows, limit=atlas_retain_limit)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "holdout_used_for_selection": False,
        "method": {
            "purpose": (
                "Map the residual field around the old anchor model by source gate "
                "and base-score band, then test signed local corrections."
            ),
            "material_difference": (
                "Global formula sweeps search the absolute difficulty surface. "
                "This sidecar holds the old score fixed as an anchor and searches "
                "the conditional residual surface: expected - old_score. The learned "
                "objects are signed deltas inside gates, not positive global weights."
            ),
            "shape_model": (
                "difficulty = clip(old_score + sum(gate_k(x, old_score_band) * "
                "delta_k), 0, 1), with each delta fit from calibration residuals "
                "and clipped before evaluation."
            ),
            "selection_policy": (
                "Correction cells are ranked using calibration residual structure, "
                "then promoted to the stable/composite probe only when calibration "
                "fold validation is non-negative under a MAE-safe profile. Holdout "
                "is reported after selection."
            ),
            "target_curve_id": TARGET_CURVE_ID,
        },
        "parameters": {
            "old_score_key": old_score_key,
            "base_bands": [_base_band_dict(band) for band in base_bands],
            "fold_count": int(fold_count),
            "error_threshold": _rounded(error_threshold),
            "min_support": int(min_support),
            "min_abs_delta": _rounded(min_abs_delta),
            "max_correction_abs": _rounded(max_correction_abs),
            "max_total_correction_abs": _rounded(max_total_correction_abs),
            "group_count": len(group_specs),
            "atlas_cell_count": len(atlas_rows),
            "correction_cell_limit": int(correction_cell_limit),
            "evaluated_correction_cell_count": len(correction_reports),
            "stable_correction_count": len(stable_corrections),
            "atlas_retain_limit": int(atlas_retain_limit),
            "leaderboard_limit": int(leaderboard_limit),
            "composite_sizes": [int(value) for value in composite_sizes],
            "proficiency_points": [round(float(value), 6) for value in proficiency_points],
            "challenge_offset": _rounded(challenge_offset),
            "window_sigma": _rounded(window_sigma),
            "window_top_k": int(window_top_k),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "normalization_population_count": len(component_context.lemmas),
            "calibration_label_count": len(calibration_context.labels),
            "holdout_label_count": len(holdout_context.labels),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "trace_json": trace_json,
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "holdout_json": holdout_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
                "proficiency_ordering_stability": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_stability_en_ja.py",
                "structured_failure_groups": SCRIPT_DIR
                / "srs_learner_difficulty_structured_failure_groups_en_ja.py",
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "reference_candidate": {
            "candidate_id": old_record.get("variant_id"),
            "source": "signal_sweep_trace",
            "selector": f"max:{old_score_key}",
            "scores": old_record.get("scores") or {},
            "weights": old_record.get("weights") or {},
        },
        "reference_reports": reference,
        "shape_summary": _shape_summary(atlas_rows),
        "leaderboards": {
            "calibration_residual_structure": _atlas_leaderboard(
                atlas_rows,
                key="residual_structure_score",
                limit=leaderboard_limit,
            ),
            "largest_abs_calibration_delta": _atlas_leaderboard(
                atlas_rows,
                key="abs_calibration_median_residual",
                limit=leaderboard_limit,
            ),
            "fold_validation_mae_safe": _correction_leaderboard(
                _stable_correction_reports(
                    correction_reports,
                    cell_masks=cell_masks,
                    limit=0,
                ),
                key="stable_selector_score",
                limit=leaderboard_limit,
            ),
            "holdout_after_calibration_fit": _correction_leaderboard(
                correction_reports,
                key="holdout_score_delta",
                limit=leaderboard_limit,
            ),
            "largest_holdout_mae_reduction": _correction_leaderboard(
                correction_reports,
                key="holdout_normal_vocab_mae_reduction",
                limit=leaderboard_limit,
            ),
        },
        "primary_cells": {
            "residual_structure": _atlas_summary(_top_row(atlas_rows, "residual_structure_score")),
            "fold_validation_mae_safe": _correction_summary(
                _top_row(
                    _stable_correction_reports(
                        correction_reports,
                        cell_masks=cell_masks,
                        limit=0,
                    ),
                    "stable_selector_score",
                )
            ),
            "holdout_after_calibration_fit": _correction_summary(
                _top_row(correction_reports, "holdout_score_delta")
            ),
            "largest_holdout_mae_reduction": _correction_summary(
                _top_row(correction_reports, "holdout_normal_vocab_mae_reduction")
            ),
        },
        "composite_probe": composite_reports,
        "stable_corrections": [
            _correction_summary(row) for row in stable_corrections[:leaderboard_limit]
        ],
        "correction_results": correction_reports,
        "atlas_rows": retained_atlas,
    }


def _reference_reports(
    *,
    old_values: object,
    calibration_context: object,
    holdout_context: object,
    validation_contexts: Sequence[object],
    train_contexts: Sequence[object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    calibration = _dataset_report(
        calibration_context,
        old_values,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout = _dataset_report(
        holdout_context,
        old_values,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    return {
        "calibration": _compact_dataset_report(calibration),
        "holdout": _compact_dataset_report(holdout),
        "validation_folds": [
            _compact_dataset_report(
                _dataset_report(
                    context,
                    old_values,
                    proficiency_points=proficiency_points,
                    challenge_offset=challenge_offset,
                    window_sigma=window_sigma,
                    window_top_k=window_top_k,
                    detail_limit=detail_limit,
                )
            )
            for context in validation_contexts
        ],
        "train_folds": [
            _compact_dataset_report(
                _dataset_report(
                    context,
                    old_values,
                    proficiency_points=proficiency_points,
                    challenge_offset=challenge_offset,
                    window_sigma=window_sigma,
                    window_top_k=window_top_k,
                    detail_limit=detail_limit,
                )
            )
            for context in train_contexts
        ],
    }


def _shape_cell_atlas_row(
    cell: ShapeCell,
    *,
    cell_mask: object,
    old_values: object,
    calibration_context: object,
    holdout_context: object,
    error_threshold: float,
    detail_limit: int,
) -> dict[str, object]:
    calibration = _residual_profile(
        calibration_context,
        old_values,
        group_mask=cell_mask,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    holdout = _residual_profile(
        holdout_context,
        old_values,
        group_mask=cell_mask,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    calibration_median = _optional_float(calibration.get("median_residual"))
    full_vocab_count = int(np.asarray(cell_mask, dtype=bool).sum())
    return {
        "cell_id": cell.cell_id,
        "group_id": cell.group.group_id,
        "source": cell.group.source,
        "description": cell.group.description,
        "base_band": _base_band_dict(cell.base_band),
        "terms": [_term_dict(term) for term in cell.group.terms],
        "full_vocab_count": full_vocab_count,
        "scope": _scope_for_count(full_vocab_count),
        "calibration_residual": calibration,
        "holdout_residual": holdout,
        "calibration_median_residual": _rounded(calibration_median),
        "abs_calibration_median_residual": _rounded(
            abs(calibration_median) if calibration_median is not None else None
        ),
        "suggested_direction": _direction_for_delta(calibration_median),
        "residual_structure_score": _rounded(_residual_structure_score(calibration)),
    }


def _shape_cell_correction_report(
    cell: ShapeCell,
    *,
    cell_mask: object,
    old_values: object,
    calibration_context: object,
    holdout_context: object,
    validation_contexts: Sequence[object],
    train_contexts: Sequence[object],
    reference: Mapping[str, object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    error_threshold: float,
    min_support: int,
    max_correction_abs: float,
    detail_limit: int,
) -> dict[str, object]:
    calibration_residual = _residual_profile(
        calibration_context,
        old_values,
        group_mask=cell_mask,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    holdout_residual = _residual_profile(
        holdout_context,
        old_values,
        group_mask=cell_mask,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    calibration_group_mask = _context_group_mask(calibration_context, cell_mask)
    full_delta = _bounded_residual_delta(
        calibration_context,
        old_values,
        calibration_group_mask,
        max_abs=max_correction_abs,
        min_support=min_support,
    )
    adjusted = _apply_cell_delta(old_values, cell_mask, full_delta or 0.0)
    calibration_report = _dataset_report(
        calibration_context,
        adjusted,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout_report = _dataset_report(
        holdout_context,
        adjusted,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    pseudo_group = GroupSpec(
        group_id=cell.cell_id,
        description=f"{cell.group.description} in base band {cell.base_band.band_id}.",
        terms=cell.group.terms,
        source=f"{cell.group.source}:base_band",
    )
    fold_reports = [
        _fold_correction_report(
            fold_index=index,
            spec=pseudo_group,
            group_mask=cell_mask,
            old_values=old_values,
            train_context=train_context,
            validation_context=validation_contexts[index],
            holdout_context=holdout_context,
            reference=reference,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            min_train_support=min_support,
            max_correction_abs=max_correction_abs,
            detail_limit=detail_limit,
        )
        for index, train_context in enumerate(train_contexts)
    ]
    fold_summary = _fold_delta_summary(fold_reports)
    structure_score = _residual_structure_score(calibration_residual)
    selected_count = int(np.asarray(cell_mask, dtype=bool).sum())
    eligible = (
        full_delta is not None
        and int(calibration_residual["selected_count"]) >= min_support
        and float(calibration_residual.get("sign_consistency") or 0.0) >= 0.55
    )
    result = {
        "cell_id": cell.cell_id,
        "group_id": cell.group.group_id,
        "source": cell.group.source,
        "description": cell.group.description,
        "base_band": _base_band_dict(cell.base_band),
        "terms": [_term_dict(term) for term in cell.group.terms],
        "eligible": eligible,
        "full_vocab_count": selected_count,
        "scope": _scope_for_count(selected_count),
        "calibration_residual": calibration_residual,
        "holdout_residual": holdout_residual,
        "calibration_fit_delta": _rounded(full_delta),
        "suggested_direction": _direction_for_delta(full_delta),
        "fold_summary": fold_summary,
        "selector_score": _rounded(_selector_score(fold_summary, structure_score)),
        "residual_structure_score": _rounded(structure_score),
        "calibration": _compact_dataset_report(calibration_report),
        "holdout": _compact_dataset_report(holdout_report),
        "calibration_score_delta": _rounded(
            _score_delta(calibration_report, _mapping(reference.get("calibration")))
        ),
        "holdout_score_delta": _rounded(
            _score_delta(holdout_report, _mapping(reference.get("holdout")))
        ),
        "holdout_normal_vocab_mae_reduction": _rounded(
            _normal_vocab_mae_reduction(
                before=_mapping(reference.get("holdout")),
                after=holdout_report,
            )
        ),
        "folds": fold_reports,
    }
    result["guardrails"] = _guardrail_flags(
        eligible=eligible,
        full_vocab_count=selected_count,
        calibration_residual=calibration_residual,
        fold_summary=fold_summary,
    )
    result["stable_selector_score"] = _rounded(_stable_selector_score(result))
    return result


def _composite_reports(
    *,
    stable_corrections: Sequence[Mapping[str, object]],
    cell_masks: Mapping[str, object],
    old_values: object,
    calibration_context: object,
    holdout_context: object,
    reference: Mapping[str, object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    max_total_correction_abs: float,
    composite_sizes: Sequence[int],
    detail_limit: int,
) -> list[dict[str, object]]:
    rows = []
    for size in sorted({int(value) for value in composite_sizes if int(value) > 0}):
        selected = stable_corrections[:size]
        cells = [
            CompositeCell(
                cell_id=str(row.get("cell_id") or ""),
                delta=float(_optional_float(row.get("calibration_fit_delta")) or 0.0),
                mask=cell_masks[str(row.get("cell_id") or "")],
            )
            for row in selected
            if str(row.get("cell_id") or "") in cell_masks
        ]
        adjusted, shift_summary = _apply_composite_deltas(
            old_values,
            cells,
            max_total_abs=max_total_correction_abs,
        )
        calibration_report = _dataset_report(
            calibration_context,
            adjusted,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        holdout_report = _dataset_report(
            holdout_context,
            adjusted,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        rows.append(
            {
                "composite_id": f"top_{len(cells)}_stable_cells",
                "requested_size": size,
                "cell_count": len(cells),
                "cell_ids": [cell.cell_id for cell in cells],
                "shift_summary": shift_summary,
                "calibration": _compact_dataset_report(calibration_report),
                "holdout": _compact_dataset_report(holdout_report),
                "calibration_score_delta": _rounded(
                    _score_delta(
                        calibration_report,
                        _mapping(reference.get("calibration")),
                    )
                ),
                "holdout_score_delta": _rounded(
                    _score_delta(holdout_report, _mapping(reference.get("holdout")))
                ),
                "holdout_normal_vocab_mae_reduction": _rounded(
                    _normal_vocab_mae_reduction(
                        before=_mapping(reference.get("holdout")),
                        after=holdout_report,
                    )
                ),
            }
        )
    return rows


def _correction_candidate_cells(
    atlas_rows: Sequence[Mapping[str, object]],
    *,
    min_support: int,
    min_abs_delta: float,
    limit: int,
) -> list[ShapeCell]:
    candidates = []
    for row in atlas_rows:
        calibration = _mapping(row.get("calibration_residual"))
        calibration_count = int(calibration.get("selected_count") or 0)
        if calibration_count < min_support:
            continue
        if (_optional_float(row.get("abs_calibration_median_residual")) or 0.0) < min_abs_delta:
            continue
        if (_optional_float(calibration.get("sign_consistency")) or 0.0) < 0.55:
            continue
        candidates.append(row)
    candidates.sort(
        key=lambda row: (
            _optional_float(row.get("residual_structure_score")) or -999.0,
            _optional_float(row.get("abs_calibration_median_residual")) or -999.0,
            int(_mapping(row.get("calibration_residual")).get("selected_count") or 0),
        ),
        reverse=True,
    )
    return [_cell_from_atlas_row(row) for row in candidates[:limit]]


def _stable_correction_reports(
    rows: Sequence[Mapping[str, object]],
    *,
    cell_masks: Mapping[str, object] | None = None,
    limit: int,
) -> list[Mapping[str, object]]:
    stable = [row for row in rows if _stable_selector_score(row) is not None]
    stable.sort(
        key=lambda row: (
            _optional_float(row.get("stable_selector_score")) or -999.0,
            _optional_float(row.get("selector_score")) or -999.0,
            _optional_float(row.get("residual_structure_score")) or -999.0,
        ),
        reverse=True,
    )
    if cell_masks is not None:
        stable = _dedupe_reports_by_mask(stable, cell_masks)
    return stable[:limit] if limit > 0 else stable


def _dedupe_reports_by_mask(
    rows: Sequence[Mapping[str, object]],
    cell_masks: Mapping[str, object],
) -> list[Mapping[str, object]]:
    deduped = []
    seen: set[bytes] = set()
    for row in rows:
        cell_id = str(row.get("cell_id") or "")
        mask = cell_masks.get(cell_id)
        if mask is None:
            deduped.append(row)
            continue
        signature = np.packbits(np.asarray(mask, dtype=bool)).tobytes()
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(row)
    return deduped


def _stable_selector_score(row: Mapping[str, object]) -> float | None:
    if not bool(row.get("eligible")):
        return None
    fold_summary = _mapping(row.get("fold_summary"))
    mean_validation = _optional_float(fold_summary.get("mean_validation_score_delta"))
    min_validation = _optional_float(fold_summary.get("min_validation_score_delta"))
    validation_mae = _optional_float(fold_summary.get("mean_validation_normal_vocab_mae_reduction"))
    if mean_validation is None or min_validation is None or validation_mae is None:
        return None
    if mean_validation <= 0.0 or min_validation < -0.001 or validation_mae < 0.0:
        return None
    if int(fold_summary.get("valid_fold_count") or 0) < DEFAULT_FOLD_COUNT:
        return None
    full_vocab_count = int(row.get("full_vocab_count") or 0)
    return (
        mean_validation
        + (0.30 * min_validation)
        + (0.20 * max(0.0, validation_mae))
        - _shape_breadth_penalty(full_vocab_count)
    )


def _shape_breadth_penalty(full_vocab_count: int) -> float:
    if int(full_vocab_count) <= 10_000:
        return 0.0
    if int(full_vocab_count) <= 25_000:
        return 0.001
    return 0.003


def _apply_cell_delta(values: object, cell_mask: object, delta: float) -> object:
    adjusted = np.asarray(values, dtype=np.float32).copy()
    selected = np.asarray(cell_mask, dtype=bool)
    adjusted[selected] = np.clip(adjusted[selected] + float(delta), 0.0, 1.0)
    return adjusted


def _apply_composite_deltas(
    values: object,
    cells: Sequence[CompositeCell],
    *,
    max_total_abs: float,
) -> tuple[object, dict[str, object]]:
    base = np.asarray(values, dtype=np.float32)
    adjusted = base.copy()
    total_shift = np.zeros(len(base), dtype=np.float32)
    touch_count = np.zeros(len(base), dtype=np.int16)
    for cell in cells:
        selected = np.asarray(cell.mask, dtype=bool)
        proposed = np.clip(
            total_shift[selected] + float(cell.delta),
            -float(max_total_abs),
            float(max_total_abs),
        )
        increment = proposed - total_shift[selected]
        adjusted[selected] = np.clip(adjusted[selected] + increment, 0.0, 1.0)
        total_shift[selected] = proposed
        touch_count[selected] += 1
    touched = touch_count > 0
    return adjusted, {
        "touched_count": int(touched.sum()),
        "overlap_count": int((touch_count > 1).sum()),
        "mean_abs_shift": _rounded(
            float(np.mean(np.abs(total_shift[touched]))) if touched.any() else None
        ),
        "max_abs_shift": _rounded(
            float(np.max(np.abs(total_shift[touched]))) if touched.any() else None
        ),
        "positive_shift_count": int((total_shift > 0.0).sum()),
        "negative_shift_count": int((total_shift < 0.0).sum()),
    }


def _shape_summary(atlas_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    supported = [
        row
        for row in atlas_rows
        if int(_mapping(row.get("calibration_residual")).get("selected_count") or 0) > 0
    ]
    up = [row for row in supported if str(row.get("suggested_direction") or "") == "raise"]
    down = [row for row in supported if str(row.get("suggested_direction") or "") == "lower"]
    stableish = [
        row
        for row in supported
        if (
            _optional_float(_mapping(row.get("calibration_residual")).get("sign_consistency"))
            or 0.0
        )
        >= 0.65
    ]
    return {
        "supported_cell_count": len(supported),
        "raise_cell_count": len(up),
        "lower_cell_count": len(down),
        "sign_consistent_065_count": len(stableish),
        "by_base_band": _summary_by_base_band(supported),
        "by_source": _summary_by_key(supported, "source"),
    }


def _summary_by_base_band(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        band = _mapping(row.get("base_band"))
        grouped.setdefault(str(band.get("band_id") or ""), []).append(row)
    return [
        {
            "base_band": key,
            "cell_count": len(items),
            "raise_count": sum(
                1 for item in items if str(item.get("suggested_direction") or "") == "raise"
            ),
            "lower_count": sum(
                1 for item in items if str(item.get("suggested_direction") or "") == "lower"
            ),
            "median_abs_delta": _rounded(
                _median(
                    _optional_float(item.get("abs_calibration_median_residual")) for item in items
                )
            ),
        }
        for key, items in sorted(grouped.items())
    ]


def _summary_by_key(
    rows: Sequence[Mapping[str, object]],
    key: str,
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or ""), []).append(row)
    result = []
    for value, items in grouped.items():
        result.append(
            {
                key: value,
                "cell_count": len(items),
                "raise_count": sum(
                    1 for item in items if str(item.get("suggested_direction") or "") == "raise"
                ),
                "lower_count": sum(
                    1 for item in items if str(item.get("suggested_direction") or "") == "lower"
                ),
            }
        )
    return sorted(result, key=lambda row: int(row.get("cell_count") or 0), reverse=True)


def _retained_atlas_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[Mapping[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            int(_mapping(row.get("calibration_residual")).get("selected_count") or 0) > 0,
            _optional_float(row.get("residual_structure_score")) or -999.0,
            _optional_float(row.get("abs_calibration_median_residual")) or -999.0,
        ),
        reverse=True,
    )
    return ranked[:limit]


def _shape_cells(
    groups: Sequence[GroupSpec],
    base_bands: Sequence[BaseBand],
) -> list[ShapeCell]:
    return [
        ShapeCell(
            cell_id=f"{group.group_id}__base_{band.band_id}",
            group=group,
            base_band=band,
        )
        for group in groups
        for band in base_bands
    ]


def _cell_mask(cell: ShapeCell, group_mask: object, old_values: object) -> object:
    old = np.asarray(old_values, dtype=np.float32)
    selected = np.asarray(group_mask, dtype=bool).copy()
    selected &= np.isfinite(old)
    if cell.base_band.is_last:
        selected &= old >= cell.base_band.low
        selected &= old <= cell.base_band.high
    else:
        selected &= old >= cell.base_band.low
        selected &= old < cell.base_band.high
    return selected


def _cell_from_atlas_row(row: Mapping[str, object]) -> ShapeCell:
    band = _mapping(row.get("base_band"))
    terms = tuple(
        GroupTerm(
            str(term.get("signal") or ""),
            min_value=_optional_float(term.get("min_value")),
            max_value=_optional_float(term.get("max_value")),
        )
        for term in row.get("terms") or ()
        if isinstance(term, Mapping)
    )
    group = GroupSpec(
        group_id=str(row.get("group_id") or ""),
        description=str(row.get("description") or ""),
        terms=terms,
        source=str(row.get("source") or ""),
    )
    base_band = BaseBand(
        band_id=str(band.get("band_id") or ""),
        low=float(_optional_float(band.get("low")) or 0.0),
        high=float(_optional_float(band.get("high")) or 0.0),
        is_last=bool(band.get("is_last")),
    )
    return ShapeCell(cell_id=str(row.get("cell_id") or ""), group=group, base_band=base_band)


def _atlas_leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
    limit: int,
) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: _optional_float(row.get(key)) or -999.0,
        reverse=True,
    )[:limit]
    return [_atlas_summary(row) for row in ranked]


def _correction_leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
    limit: int,
) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: _optional_float(row.get(key)) or -999.0,
        reverse=True,
    )[:limit]
    return [_correction_summary(row) for row in ranked]


def _top_row(
    rows: Sequence[Mapping[str, object]],
    key: str,
) -> Mapping[str, object]:
    if not rows:
        return {}
    return max(rows, key=lambda row: _optional_float(row.get(key)) or -999.0)


def _atlas_summary(row: Mapping[str, object]) -> dict[str, object]:
    if not row:
        return {}
    calibration = _mapping(row.get("calibration_residual"))
    holdout = _mapping(row.get("holdout_residual"))
    base_band = _mapping(row.get("base_band"))
    return {
        "cell_id": row.get("cell_id"),
        "group_id": row.get("group_id"),
        "source": row.get("source"),
        "base_band": base_band.get("band_id"),
        "full_vocab_count": row.get("full_vocab_count"),
        "scope": row.get("scope"),
        "calibration_count": calibration.get("selected_count"),
        "holdout_count": holdout.get("selected_count"),
        "direction": row.get("suggested_direction"),
        "calibration_median_residual": row.get("calibration_median_residual"),
        "calibration_sign_consistency": calibration.get("sign_consistency"),
        "holdout_median_residual": holdout.get("median_residual"),
        "holdout_sign_consistency": holdout.get("sign_consistency"),
        "residual_structure_score": row.get("residual_structure_score"),
    }


def _correction_summary(row: Mapping[str, object]) -> dict[str, object]:
    if not row:
        return {}
    summary = _group_summary(
        {
            **dict(row),
            "group_id": row.get("cell_id"),
        }
    )
    summary["cell_id"] = row.get("cell_id")
    summary["gate_id"] = row.get("group_id")
    summary["base_band"] = _mapping(row.get("base_band")).get("band_id")
    summary["stable_selector_score"] = row.get("stable_selector_score")
    summary["suggested_direction"] = row.get("suggested_direction")
    return summary


def _direction_for_delta(value: object) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    if parsed > 0.0:
        return "raise"
    if parsed < 0.0:
        return "lower"
    return "flat"


def _parse_base_bands(raw: str) -> tuple[BaseBand, ...]:
    bands = []
    parts = [part.strip() for part in str(raw).split(",") if part.strip()]
    for index, part in enumerate(parts):
        pieces = [piece.strip() for piece in part.split(":")]
        if len(pieces) != 2:
            raise ValueError(f"Invalid base band {part!r}; expected low:high")
        low = float(pieces[0])
        high = float(pieces[1])
        if high <= low:
            raise ValueError(f"Invalid base band {part!r}; high must exceed low")
        bands.append(
            BaseBand(
                band_id=f"{low:.2f}_{high:.2f}".replace(".", "p"),
                low=low,
                high=high,
                is_last=index == len(parts) - 1,
            )
        )
    if not bands:
        raise ValueError("At least one base band is required")
    return tuple(bands)


def _parse_int_csv(raw: str) -> tuple[int, ...]:
    values = []
    for part in str(raw).split(","):
        text = part.strip()
        if not text:
            continue
        values.append(int(text))
    return tuple(values)


def _base_band_dict(band: BaseBand) -> dict[str, object]:
    return {
        "band_id": band.band_id,
        "low": _rounded(band.low),
        "high": _rounded(band.high),
        "is_last": bool(band.is_last),
    }


def _median(values: object) -> float | None:
    parsed = [
        float(value)
        for value in (_optional_float(item) for item in values)
        if value is not None and np.isfinite(value)
    ]
    return float(np.median(parsed)) if parsed else None


def render_markdown(report: Mapping[str, object]) -> str:
    params = _mapping(report.get("parameters"))
    reference = _mapping(report.get("reference_candidate"))
    reference_reports = _mapping(report.get("reference_reports"))
    shape = _mapping(report.get("shape_summary"))
    primary = _mapping(report.get("primary_cells"))
    lines = [
        "# en-ja Learner Difficulty Residual Shape Atlas",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Holdout used for selection: `{_escape(report.get('holdout_used_for_selection'))}`",
        f"- Anchor candidate: `{_escape(reference.get('candidate_id'))}`",
        f"- Anchor selector: `{_escape(reference.get('selector'))}`",
        f"- Atlas cells: `{_escape(params.get('atlas_cell_count'))}`",
        f"- Evaluated correction cells: `{_escape(params.get('evaluated_correction_cell_count'))}`",
        "",
        "## What Is Different",
        "",
        (
            "This sidecar does not search for another absolute weighted score. "
            "It freezes the incumbent as `old_score`, computes `residual = label - "
            "old_score`, then searches signed corrections inside source-visible "
            "gates and old-score bands."
        ),
        "",
        "Mathematically, the tested shape is:",
        "",
        "```text",
        "difficulty = clip(old_score + sum(gate_k(x, old_score_band) * delta_k), 0, 1)",
        "```",
        "",
        "That means the searched object is conditional curvature around the old model, "
        "not another flat positive-weight model.",
        "",
        "## Reference",
        "",
        "| Dataset | Score | Normal vocab MAE | Pairwise | Window quality |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for dataset in ("calibration", "holdout"):
        row = _mapping(reference_reports.get(dataset))
        lines.append(
            "| "
            f"`{dataset}` | `{_escape(row.get('proficiency_ordering_score'))}` | "
            f"`{_escape(row.get('normal_vocab_mae'))}` | "
            f"`{_escape(row.get('normal_vocab_pairwise'))}` | "
            f"`{_escape(row.get('window_quality'))}` |"
        )
    lines.extend(
        [
            "",
            "## Shape Summary",
            "",
            f"- Supported cells: `{_escape(shape.get('supported_cell_count'))}`",
            f"- Raise cells: `{_escape(shape.get('raise_cell_count'))}`",
            f"- Lower cells: `{_escape(shape.get('lower_cell_count'))}`",
            f"- Sign-consistent cells >= 0.65: `{_escape(shape.get('sign_consistent_065_count'))}`",
            "",
            "### By Base Band",
            "",
            "| Base band | Cells | Raise | Lower | Median abs delta |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in shape.get("by_base_band") or ():
        item = _mapping(row)
        lines.append(
            "| "
            f"`{_escape(item.get('base_band'))}` | "
            f"`{_escape(item.get('cell_count'))}` | "
            f"`{_escape(item.get('raise_count'))}` | "
            f"`{_escape(item.get('lower_count'))}` | "
            f"`{_escape(item.get('median_abs_delta'))}` |"
        )
    lines.extend(
        [
            "",
            "## Primary Cells",
            "",
            "| Selector | Cell | Gate | Band | Direction | Cal delta | Validation delta | Holdout delta |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for label, key in (
        ("Residual structure", "residual_structure"),
        ("Fold validation MAE-safe", "fold_validation_mae_safe"),
        ("Holdout after calibration fit", "holdout_after_calibration_fit"),
        ("Largest holdout MAE reduction", "largest_holdout_mae_reduction"),
    ):
        row = _mapping(primary.get(key))
        lines.append(
            "| "
            f"`{label}` | `{_escape(row.get('cell_id'))}` | "
            f"`{_escape(row.get('gate_id') or row.get('group_id'))}` | "
            f"`{_escape(row.get('base_band'))}` | "
            f"`{_escape(row.get('suggested_direction') or row.get('direction'))}` | "
            f"`{_escape(row.get('calibration_delta'))}` | "
            f"`{_escape(row.get('mean_validation_score_delta'))}` | "
            f"`{_escape(row.get('holdout_score_delta'))}` |"
        )
    _append_composite_markdown(lines, report)
    _append_leaderboard_markdown(lines, report)
    _append_stable_corrections_markdown(lines, report)
    return "\n".join(lines) + "\n"


def _append_composite_markdown(
    lines: list[str],
    report: Mapping[str, object],
) -> None:
    lines.extend(
        [
            "",
            "## Composite Probe",
            "",
            (
                "The composite probe stacks the top calibration-stable signed cells. "
                "Selection is still calibration-only; holdout is reported afterward."
            ),
            "",
            "| Composite | Cells | Touched | Overlap | Cal delta | Holdout delta | Holdout MAE reduction |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report.get("composite_probe") or ():
        item = _mapping(row)
        shift = _mapping(item.get("shift_summary"))
        lines.append(
            "| "
            f"`{_escape(item.get('composite_id'))}` | "
            f"`{_escape(item.get('cell_count'))}` | "
            f"`{_escape(shift.get('touched_count'))}` | "
            f"`{_escape(shift.get('overlap_count'))}` | "
            f"`{_escape(item.get('calibration_score_delta'))}` | "
            f"`{_escape(item.get('holdout_score_delta'))}` | "
            f"`{_escape(item.get('holdout_normal_vocab_mae_reduction'))}` |"
        )


def _append_leaderboard_markdown(
    lines: list[str],
    report: Mapping[str, object],
) -> None:
    leaderboards = _mapping(report.get("leaderboards"))
    for title, key in (
        ("Calibration Residual Structure", "calibration_residual_structure"),
        ("Fold Validation MAE-Safe", "fold_validation_mae_safe"),
        ("Holdout After Calibration Fit", "holdout_after_calibration_fit"),
    ):
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                "| Cell | Gate | Band | Direction | Count | Cal delta | Validation delta | Holdout delta |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in leaderboards.get(key) or ():
            item = _mapping(row)
            lines.append(
                "| "
                f"`{_escape(item.get('cell_id'))}` | "
                f"`{_escape(item.get('gate_id') or item.get('group_id'))}` | "
                f"`{_escape(item.get('base_band'))}` | "
                f"`{_escape(item.get('suggested_direction') or item.get('direction'))}` | "
                f"`{_escape(item.get('calibration_count'))}` | "
                f"`{_escape(item.get('calibration_delta') or item.get('calibration_median_residual'))}` | "
                f"`{_escape(item.get('mean_validation_score_delta'))}` | "
                f"`{_escape(item.get('holdout_score_delta'))}` |"
            )


def _append_stable_corrections_markdown(
    lines: list[str],
    report: Mapping[str, object],
) -> None:
    rows = report.get("stable_corrections") or ()
    if not rows:
        lines.extend(
            [
                "",
                "## Stable Corrections",
                "",
                "No correction cells passed the calibration-fold MAE-safe stability profile.",
            ]
        )
        return
    lines.extend(
        [
            "",
            "## Stable Corrections",
            "",
            "| Cell | Gate | Band | Direction | Delta | Validation delta | Holdout delta |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        item = _mapping(row)
        lines.append(
            "| "
            f"`{_escape(item.get('cell_id'))}` | "
            f"`{_escape(item.get('gate_id'))}` | "
            f"`{_escape(item.get('base_band'))}` | "
            f"`{_escape(item.get('suggested_direction'))}` | "
            f"`{_escape(item.get('calibration_delta'))}` | "
            f"`{_escape(item.get('mean_validation_score_delta'))}` | "
            f"`{_escape(item.get('holdout_score_delta'))}` |"
        )


def render_atlas_csv(report: Mapping[str, object]) -> str:
    headers = [
        "cell_id",
        "group_id",
        "source",
        "base_band",
        "full_vocab_count",
        "scope",
        "direction",
        "calibration_count",
        "calibration_median_residual",
        "calibration_sign_consistency",
        "holdout_count",
        "holdout_median_residual",
        "holdout_sign_consistency",
        "residual_structure_score",
    ]
    rows = [",".join(headers)]
    for row in report.get("atlas_rows") or ():
        item = _mapping(row)
        calibration = _mapping(item.get("calibration_residual"))
        holdout = _mapping(item.get("holdout_residual"))
        base_band = _mapping(item.get("base_band"))
        rows.append(
            ",".join(
                _csv_cell(value)
                for value in (
                    item.get("cell_id"),
                    item.get("group_id"),
                    item.get("source"),
                    base_band.get("band_id"),
                    item.get("full_vocab_count"),
                    item.get("scope"),
                    item.get("suggested_direction"),
                    calibration.get("selected_count"),
                    item.get("calibration_median_residual"),
                    calibration.get("sign_consistency"),
                    holdout.get("selected_count"),
                    holdout.get("median_residual"),
                    holdout.get("sign_consistency"),
                    item.get("residual_structure_score"),
                )
            )
        )
    return "\n".join(rows) + "\n"


def _csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if any(char in text for char in {",", '"', "\n"}):
        return '"' + text.replace('"', '""') + '"'
    return text


if __name__ == "__main__":
    raise SystemExit(main())
