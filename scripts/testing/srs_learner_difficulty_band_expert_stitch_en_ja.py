#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _band_samples,
    _calibration_context,
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _load_json,
    _mapping,
    _mapping_rows,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _sequence_values,
    _summary_metrics,
    _target_curve_normalize,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    FormulaVariant,
    PiecewiseFormulaSection,
    TargetCurveScoringContext,
    _target_curve_raw_scores_for_variant,
)


DEFAULT_TRACE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_trace_latest.json"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_calibration_matrix_latest.npz"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_component_matrix_latest.npz"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_band_expert_stitch_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_band_expert_stitch_en_ja_latest.md"
)
DEFAULT_EXPERT_BANDS = (
    "0.00:0.10,0.10:0.20,0.20:0.30,0.30:0.40,0.40:0.50,"
    "0.50:0.60,0.60:0.70,0.70:0.80,0.80:0.90,0.90:1.00"
)
DEFAULT_SOFT_STRENGTHS = (0.25, 0.50, 0.75, 1.0)


@dataclass(frozen=True)
class DifficultyBandSpec:
    band_id: str
    start: float
    end: float


@dataclass(frozen=True)
class StitchCandidate:
    candidate_id: str
    mode: str
    expert_strategy: str
    soft_strength: float | None
    normalized_values: object
    calibration_observed_fallback: object | None
    segment_ids: object
    expert_ids: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only en-ja learner-difficulty harness that finds "
            "band-local experts and stitches them into full-corpus candidates."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--base-candidate", default="")
    parser.add_argument("--expert-bands", default=DEFAULT_EXPERT_BANDS)
    parser.add_argument("--top-experts-per-band", type=int, default=8)
    parser.add_argument("--detail-candidate-limit", type=int, default=12)
    parser.add_argument("--sample-per-band", type=int, default=8)
    parser.add_argument(
        "--soft-strengths", default=",".join(str(v) for v in DEFAULT_SOFT_STRENGTHS)
    )
    parser.add_argument("--guard-balanced-margin", type=float, default=0.03)
    parser.add_argument("--guard-pairwise-margin", type=float, default=0.02)
    parser.add_argument("--guard-beginner-min", type=float, default=0.95)
    parser.add_argument("--guard-upper-tail-min", type=float, default=0.80)
    parser.add_argument("--guard-high-tail-margin", type=float, default=0.0)
    parser.add_argument("--guard-default-decision-margin", type=float, default=0.0)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        base_candidate_id=str(args.base_candidate or ""),
        expert_bands=_parse_band_specs(args.expert_bands),
        top_experts_per_band=max(1, int(args.top_experts_per_band)),
        detail_candidate_limit=max(0, int(args.detail_candidate_limit)),
        sample_per_band=max(1, int(args.sample_per_band)),
        soft_strengths=_parse_float_csv(args.soft_strengths),
        guard_balanced_margin=max(0.0, float(args.guard_balanced_margin)),
        guard_pairwise_margin=max(0.0, float(args.guard_pairwise_margin)),
        guard_beginner_min=max(0.0, min(1.0, float(args.guard_beginner_min))),
        guard_upper_tail_min=max(0.0, min(1.0, float(args.guard_upper_tail_min))),
        guard_high_tail_margin=max(0.0, float(args.guard_high_tail_margin)),
        guard_default_decision_margin=max(
            0.0,
            float(args.guard_default_decision_margin),
        ),
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
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    base_candidate_id: str,
    expert_bands: Sequence[DifficultyBandSpec],
    top_experts_per_band: int,
    detail_candidate_limit: int,
    sample_per_band: int,
    soft_strengths: Sequence[float],
    guard_balanced_margin: float,
    guard_pairwise_margin: float,
    guard_beginner_min: float,
    guard_upper_tail_min: float,
    guard_high_tail_margin: float,
    guard_default_decision_margin: float,
) -> dict[str, object]:
    trace = _load_json(trace_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    variant_records = _variant_records_by_id(trace, calibration)
    base_id = base_candidate_id or _best_trace_variant_id(variant_records)
    if base_id not in variant_records:
        raise ValueError(f"Base candidate not found in trace: {base_id}")
    calibration_ctx = _calibration_context(calibration, component)
    expected_values = np.asarray(calibration_ctx["expected_values"], dtype=np.float32)
    expected_bands = [str(value) for value in calibration_ctx["expected_bands"]]
    labels = [str(value) for value in calibration_ctx["labels"]]
    observed_matrix = np.asarray(calibration["observed_values"], dtype=np.float32)
    variant_ids = [str(value) for value in calibration["variant_ids"]]
    variant_index = {variant_id: index for index, variant_id in enumerate(variant_ids)}
    base_scores = _mapping(variant_records[base_id].get("scores"))
    guard = {
        "balanced_score_min": _rounded(
            (_optional_float(base_scores.get("balanced_score")) or 0.0) - guard_balanced_margin
        ),
        "pairwise_order_score_min": _rounded(
            (_optional_float(base_scores.get("pairwise_order_score")) or 0.0)
            - guard_pairwise_margin
        ),
        "beginner_core_score_min": guard_beginner_min,
        "upper_tail_score_min": guard_upper_tail_min,
        "high_tail_score_min": _rounded(
            max(
                0.0,
                (_optional_float(base_scores.get("high_tail_score")) or 0.0)
                - guard_high_tail_margin,
            )
        ),
        "default_decision_score_min": _rounded(
            max(
                0.0,
                (_optional_float(base_scores.get("default_decision_score")) or 0.0)
                - guard_default_decision_margin,
            )
        ),
    }
    band_rankings = _band_expert_rankings(
        expert_bands=expert_bands,
        expected_values=expected_values,
        observed_matrix=observed_matrix,
        variant_ids=variant_ids,
        variant_records=variant_records,
        top_experts_per_band=top_experts_per_band,
        guard=guard,
    )
    context = _component_context(component)
    base_variant = _variant_from_record(variant_records[base_id])
    base_raw = _target_curve_raw_scores_for_variant(base_variant, context)
    base_normalized = _target_curve_normalize(
        base_raw,
        target_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
    )
    strategies = {
        "unconstrained": _selected_expert_ids(band_rankings, "best_unconstrained", base_id),
        "guarded": _selected_expert_ids(band_rankings, "best_guarded", base_id),
    }
    stitch_candidates = _stitch_candidates(
        strategies=strategies,
        base_id=base_id,
        base_raw=base_raw,
        base_normalized=base_normalized,
        variant_records=variant_records,
        context=context,
        component=component,
        expert_bands=expert_bands,
        soft_strengths=soft_strengths,
        calibration_context=calibration_ctx,
        observed_matrix=observed_matrix,
        variant_index=variant_index,
    )
    exact_top = _evaluate_stitched_candidates(
        stitch_candidates,
        component=component,
        calibration_context=calibration_ctx,
        detail_candidate_limit=detail_candidate_limit,
        sample_per_band=sample_per_band,
    )
    base_reference = _reference_row(
        candidate_id=f"base__{base_id}",
        normalized=base_normalized,
        segment_ids=_segment_ids_for_bands(base_normalized, expert_bands),
        expert_ids=tuple([base_id] * len(expert_bands)),
        component=component,
        calibration_context=calibration_ctx,
        sample_per_band=sample_per_band,
        calibration_observed_fallback=observed_matrix[variant_index[base_id]],
    )
    base_reference["trace_scores"] = {
        key: _rounded(value)
        for key, value in base_scores.items()
        if _optional_float(value) is not None
    }
    band_gain_attribution = _band_gain_attribution(
        expert_bands=expert_bands,
        band_rankings=band_rankings,
        stitch_candidates=stitch_candidates,
        exact_top=exact_top,
        calibration_context=calibration_ctx,
        base_normalized=base_normalized,
        base_calibration_values=observed_matrix[variant_index[base_id]],
        detail_candidate_limit=detail_candidate_limit,
        variant_index=variant_index,
        observed_matrix=observed_matrix,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "trace_json": trace_json,
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
            },
            code_paths={
                "difficulty_signal_sweep": (
                    SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"
                ),
                "difficulty_piecewise_search": (
                    SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
                ),
                "difficulty_normalization": (
                    SCRIPT_DIR / "srs_learner_difficulty_normalization.py"
                ),
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "method": {
            "expert_search": (
                "rank every retained trace candidate by calibration MAE inside "
                "each expected learner-difficulty band"
            ),
            "segment_selector": (
                "assign full-corpus rows to stitch bands using the base candidate's "
                "normalized target-curve score"
            ),
            "hard_partition": (
                "within each base segment, assign that segment's target-curve "
                "positions using the selected band expert's raw order"
            ),
            "raw_replace": (
                "replace base raw scores with the selected band expert raw score "
                "inside each base segment, then apply one global target-curve normalization"
            ),
            "soft_blend": (
                "blend base raw and selected expert raw inside each base segment, "
                "then apply one global target-curve normalization"
            ),
            "normalization_curve_id": TARGET_CURVE_ID,
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "trace_variant_count": len(variant_records),
            "calibration_label_count": int(len(expected_values)),
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "base_candidate_id": base_id,
            "expert_bands": [_band_json(band) for band in expert_bands],
            "top_experts_per_band": top_experts_per_band,
            "soft_strengths": [_rounded(value) for value in soft_strengths],
            "guard": guard,
        },
        "base_reference": base_reference,
        "band_rankings": band_rankings,
        "band_gain_attribution": band_gain_attribution,
        "exact_top": exact_top,
        "leaderboards": _leaderboards(exact_top, limit=12),
        "side_by_side_samples": _side_by_side_samples(
            [base_reference, *exact_top[:3]],
            label_by_candidate_id={
                str(base_reference.get("candidate_id")): "base",
                **{
                    str(row.get("candidate_id")): f"rank {index}"
                    for index, row in enumerate(exact_top[:3], start=1)
                },
            },
        ),
        "calibration_labels_by_band": _calibration_labels_by_band(
            expert_bands,
            expected_values=expected_values,
            labels=labels,
            expected_bands=expected_bands,
        ),
    }


def _variant_records_by_id(
    trace: Mapping[str, object],
    calibration: object,
) -> dict[str, Mapping[str, object]]:
    rows = {
        str(row.get("variant_id") or ""): row
        for row in _mapping_rows(trace.get("variant_records"))
        if row.get("variant_id")
    }
    matrix_ids = [str(value) for value in calibration["variant_ids"]]
    missing = [variant_id for variant_id in matrix_ids if variant_id not in rows]
    if missing:
        raise ValueError(f"Calibration matrix has variants missing from trace: {missing[:5]}")
    return {variant_id: rows[variant_id] for variant_id in matrix_ids}


def _best_trace_variant_id(records: Mapping[str, Mapping[str, object]]) -> str:
    if not records:
        raise ValueError("Trace has no variant records.")
    return max(
        records,
        key=lambda variant_id: (
            _optional_float(_mapping(records[variant_id].get("scores")).get("balanced_score"))
            or -1.0,
            _optional_float(_mapping(records[variant_id].get("scores")).get("pairwise_order_score"))
            or -1.0,
        ),
    )


def _band_expert_rankings(
    *,
    expert_bands: Sequence[DifficultyBandSpec],
    expected_values: object,
    observed_matrix: object,
    variant_ids: Sequence[str],
    variant_records: Mapping[str, Mapping[str, object]],
    top_experts_per_band: int,
    guard: Mapping[str, object],
) -> list[dict[str, object]]:
    expected = np.asarray(expected_values, dtype=np.float32)
    observed = np.asarray(observed_matrix, dtype=np.float32)
    rows: list[dict[str, object]] = []
    for band_index, band in enumerate(expert_bands):
        mask = _expected_band_mask(expected, band, is_last=band_index == len(expert_bands) - 1)
        local_indices = np.where(mask)[0]
        rankings = []
        for variant_row_index, variant_id in enumerate(variant_ids):
            values = observed[variant_row_index, local_indices]
            finite = np.isfinite(values) & np.isfinite(expected[local_indices])
            if not bool(finite.any()):
                continue
            errors = np.abs(values[finite] - expected[local_indices][finite])
            record = variant_records[variant_id]
            scores = _mapping(record.get("scores"))
            rankings.append(
                {
                    "variant_id": variant_id,
                    "local_mae": _rounded(float(errors.mean())),
                    "local_rmse": _rounded(float(np.sqrt(np.mean(errors * errors)))),
                    "local_max_error": _rounded(float(errors.max())),
                    "label_count": int(finite.sum()),
                    "guard_pass": _guard_pass(scores, guard),
                    "scores": {
                        key: _rounded(value)
                        for key, value in scores.items()
                        if _optional_float(value) is not None
                    },
                    "weights": dict(_mapping(record.get("weights"))),
                    "transforms": dict(_mapping(record.get("transforms"))),
                }
            )
        ranked = sorted(
            rankings,
            key=lambda row: (
                _optional_float(row.get("local_mae")) or 999.0,
                -(_optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0),
            ),
        )
        guarded = [row for row in ranked if row.get("guard_pass")]
        rows.append(
            {
                "band": band.band_id,
                "start": _rounded(band.start),
                "end": _rounded(band.end),
                "label_count": int(len(local_indices)),
                "best_unconstrained": ranked[0] if ranked else None,
                "best_guarded": guarded[0] if guarded else None,
                "top_unconstrained": ranked[:top_experts_per_band],
                "top_guarded": guarded[:top_experts_per_band],
            }
        )
    return rows


def _stitch_candidates(
    *,
    strategies: Mapping[str, Sequence[str]],
    base_id: str,
    base_raw: object,
    base_normalized: object,
    variant_records: Mapping[str, Mapping[str, object]],
    context: TargetCurveScoringContext,
    component: object,
    expert_bands: Sequence[DifficultyBandSpec],
    soft_strengths: Sequence[float],
    calibration_context: Mapping[str, object],
    observed_matrix: object,
    variant_index: Mapping[str, int],
) -> list[StitchCandidate]:
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    base_values = np.asarray(base_raw, dtype=np.float32)
    segment_ids = _segment_ids_for_bands(base_normalized, expert_bands)
    needed_ids = {base_id}
    for ids in strategies.values():
        needed_ids.update(str(value) for value in ids)
    raw_by_id = {
        variant_id: _target_curve_raw_scores_for_variant(
            _variant_from_record(variant_records[variant_id]),
            context,
        )
        for variant_id in sorted(needed_ids)
        if variant_id in variant_records
    }
    calibration_matrix_values = np.asarray(observed_matrix, dtype=np.float32)
    base_calibration_values = calibration_matrix_values[variant_index[base_id]]
    candidates: list[StitchCandidate] = []
    for strategy, expert_ids in strategies.items():
        expert_tuple = tuple(str(value) for value in expert_ids)
        hard_partition_calibration_values = _stitched_calibration_fallback_values(
            expert_ids=expert_tuple,
            mode="hard_partition",
            strength=1.0,
            base_calibration_values=base_calibration_values,
            calibration_context=calibration_context,
            expert_bands=expert_bands,
            observed_matrix=calibration_matrix_values,
            variant_index=variant_index,
        )
        candidates.append(
            StitchCandidate(
                candidate_id=f"{strategy}__hard_partition",
                mode="hard_partition",
                expert_strategy=strategy,
                soft_strength=None,
                normalized_values=_hard_partition_normalize(
                    raw_by_id,
                    expert_ids=expert_tuple,
                    segment_ids=segment_ids,
                    base_normalized=base_normalized,
                ),
                calibration_observed_fallback=hard_partition_calibration_values,
                segment_ids=segment_ids,
                expert_ids=expert_tuple,
            )
        )
        replaced = _stitched_raw(
            base_values,
            raw_by_id,
            expert_ids=expert_tuple,
            segment_ids=segment_ids,
            strength=1.0,
        )
        raw_replace_calibration_values = _stitched_calibration_fallback_values(
            expert_ids=expert_tuple,
            mode="raw_replace",
            strength=1.0,
            base_calibration_values=base_calibration_values,
            calibration_context=calibration_context,
            expert_bands=expert_bands,
            observed_matrix=calibration_matrix_values,
            variant_index=variant_index,
        )
        candidates.append(
            StitchCandidate(
                candidate_id=f"{strategy}__raw_replace",
                mode="raw_replace",
                expert_strategy=strategy,
                soft_strength=None,
                normalized_values=_target_curve_normalize(
                    replaced,
                    target_positions=target_positions,
                ),
                calibration_observed_fallback=raw_replace_calibration_values,
                segment_ids=segment_ids,
                expert_ids=expert_tuple,
            )
        )
        for strength in soft_strengths:
            parsed = max(0.0, min(1.0, float(strength)))
            blended = _stitched_raw(
                base_values,
                raw_by_id,
                expert_ids=expert_tuple,
                segment_ids=segment_ids,
                strength=parsed,
            )
            soft_calibration_values = _stitched_calibration_fallback_values(
                expert_ids=expert_tuple,
                mode="soft_blend",
                strength=parsed,
                base_calibration_values=base_calibration_values,
                calibration_context=calibration_context,
                expert_bands=expert_bands,
                observed_matrix=calibration_matrix_values,
                variant_index=variant_index,
            )
            candidates.append(
                StitchCandidate(
                    candidate_id=f"{strategy}__soft_blend_s{_strength_id(parsed)}",
                    mode="soft_blend",
                    expert_strategy=strategy,
                    soft_strength=parsed,
                    normalized_values=_target_curve_normalize(
                        blended,
                        target_positions=target_positions,
                    ),
                    calibration_observed_fallback=soft_calibration_values,
                    segment_ids=segment_ids,
                    expert_ids=expert_tuple,
                )
            )
    return candidates


def _stitched_calibration_fallback_values(
    *,
    expert_ids: Sequence[str],
    mode: str,
    strength: float,
    base_calibration_values: object,
    calibration_context: Mapping[str, object],
    expert_bands: Sequence[DifficultyBandSpec],
    observed_matrix: object,
    variant_index: Mapping[str, int],
) -> object:
    base_values = np.asarray(base_calibration_values, dtype=np.float32)
    values = base_values.copy()
    segments = _segment_ids_for_bands(base_values, expert_bands)
    parsed_strength = max(0.0, min(1.0, float(strength)))
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    fallback_only = component_indices < 0
    finite_base = np.isfinite(base_values)
    matrix_values = np.asarray(observed_matrix, dtype=np.float32)
    for segment_index, expert_id in enumerate(expert_ids):
        expert_index = variant_index.get(str(expert_id))
        if expert_index is None:
            continue
        mask = fallback_only & finite_base & (segments == segment_index)
        if not bool(mask.any()):
            continue
        expert_values = matrix_values[expert_index]
        if mode == "soft_blend":
            values[mask] = ((1.0 - parsed_strength) * base_values[mask]) + (
                parsed_strength * expert_values[mask]
            )
        else:
            values[mask] = expert_values[mask]
    return values


def _hard_partition_normalize(
    raw_by_id: Mapping[str, object],
    *,
    expert_ids: Sequence[str],
    segment_ids: object,
    base_normalized: object,
) -> object:
    segments = np.asarray(segment_ids, dtype=np.int64)
    base_values = np.asarray(base_normalized, dtype=np.float32)
    normalized = np.empty(len(segments), dtype=np.float32)
    for segment_index, expert_id in enumerate(expert_ids):
        indices = np.where(segments == segment_index)[0]
        if not len(indices):
            continue
        raw = np.asarray(raw_by_id[expert_id], dtype=np.float32)
        ordered = indices[np.argsort(raw[indices], kind="stable")]
        normalized[ordered] = np.sort(base_values[indices], kind="stable")
    return normalized


def _stitched_raw(
    base_raw: object,
    raw_by_id: Mapping[str, object],
    *,
    expert_ids: Sequence[str],
    segment_ids: object,
    strength: float,
) -> object:
    result = np.asarray(base_raw, dtype=np.float32).copy()
    segments = np.asarray(segment_ids, dtype=np.int64)
    parsed_strength = max(0.0, min(1.0, float(strength)))
    for segment_index, expert_id in enumerate(expert_ids):
        mask = segments == segment_index
        if not bool(mask.any()):
            continue
        expert_raw = np.asarray(raw_by_id[expert_id], dtype=np.float32)
        result[mask] = ((1.0 - parsed_strength) * result[mask]) + (
            parsed_strength * expert_raw[mask]
        )
    return np.clip(result, 0.0, 1.0)


def _evaluate_stitched_candidates(
    candidates: Sequence[StitchCandidate],
    *,
    component: object,
    calibration_context: Mapping[str, object],
    detail_candidate_limit: int,
    sample_per_band: int,
) -> list[dict[str, object]]:
    rows = [
        _candidate_row(
            candidate,
            component=component,
            calibration_context=calibration_context,
            include_details=False,
            sample_per_band=sample_per_band,
        )
        for candidate in candidates
    ]
    ranked = _top_rows(rows, limit=len(rows))
    detail_ids = {str(row.get("candidate_id") or "") for row in ranked[:detail_candidate_limit]}
    for row in ranked:
        if str(row.get("candidate_id") or "") not in detail_ids:
            continue
        candidate = next(
            item for item in candidates if item.candidate_id == str(row.get("candidate_id"))
        )
        row.update(
            _candidate_row(
                candidate,
                component=component,
                calibration_context=calibration_context,
                include_details=True,
                sample_per_band=sample_per_band,
            )
        )
    return ranked


def _candidate_row(
    candidate: StitchCandidate,
    *,
    component: object,
    calibration_context: Mapping[str, object],
    include_details: bool,
    sample_per_band: int,
) -> dict[str, object]:
    normalized = np.asarray(candidate.normalized_values, dtype=np.float32)
    observed = _calibration_observed(
        normalized,
        calibration_context,
        fallback_values=candidate.calibration_observed_fallback,
    )
    metrics = _difficulty_metrics(
        expected_values=calibration_context["expected_values"],
        observed_values=observed,
        expected_bands=calibration_context["expected_bands"],
        expected_candidate_states=calibration_context["expected_candidate_states"],
        observed_candidate_states=calibration_context["observed_candidate_states"],
        labels=calibration_context["labels"],
    )
    row: dict[str, object] = {
        "candidate_id": candidate.candidate_id,
        "mode": candidate.mode,
        "expert_strategy": candidate.expert_strategy,
        "soft_strength": (
            _rounded(candidate.soft_strength) if candidate.soft_strength is not None else None
        ),
        "expert_ids": list(candidate.expert_ids),
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
    }
    if include_details:
        row.update(
            {
                "wrong_pairwise_examples": metrics["pairwise_order"]["wrong_examples"],
                "difficulty_mismatches": metrics["difficulty_bucket"]["mismatches"],
                "segment_misses": {
                    key: value["misses"]
                    for key, value in metrics["segments"].items()
                    if value.get("misses")
                },
                "band_samples": _band_samples(
                    normalized,
                    component=component,
                    segment_ids=candidate.segment_ids,
                    expert_ids=candidate.expert_ids,
                    per_band=sample_per_band,
                ),
            }
        )
    return row


def _reference_row(
    *,
    candidate_id: str,
    normalized: object,
    segment_ids: object,
    expert_ids: Sequence[str],
    component: object,
    calibration_context: Mapping[str, object],
    sample_per_band: int,
    calibration_observed_fallback: object | None = None,
) -> dict[str, object]:
    candidate = StitchCandidate(
        candidate_id=candidate_id,
        mode="reference",
        expert_strategy="base",
        soft_strength=None,
        normalized_values=normalized,
        calibration_observed_fallback=calibration_observed_fallback,
        segment_ids=segment_ids,
        expert_ids=tuple(expert_ids),
    )
    return _candidate_row(
        candidate,
        component=component,
        calibration_context=calibration_context,
        include_details=True,
        sample_per_band=sample_per_band,
    )


def _calibration_observed(
    normalized: object,
    calibration_context: Mapping[str, object],
    fallback_values: object | None = None,
) -> object:
    indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    if fallback_values is not None:
        fallback = np.asarray(fallback_values, dtype=np.float32)
        count = min(len(observed), len(fallback))
        observed[:count] = fallback[:count]
    valid = indices >= 0
    observed[valid] = np.asarray(normalized, dtype=np.float32)[indices[valid]]
    return observed


def _component_context(component: object) -> TargetCurveScoringContext:
    row_count = len(component["candidate_identity_keys"])
    levels = (
        np.asarray(component["jlpt_vocab_levels"], dtype=np.float32)
        if "jlpt_vocab_levels" in component.files
        else np.full(row_count, np.nan, dtype=np.float32)
    )
    dedupe_values = tuple(str(value) for value in component["dedupe_values"])
    return TargetCurveScoringContext(
        component_names=tuple(str(value) for value in component["component_names"]),
        component_values=np.asarray(component["component_values"], dtype=np.float32),
        component_present=np.asarray(component["component_present"], dtype=bool),
        current_values=np.asarray(component["current_values"], dtype=np.float32),
        frequency_values=np.asarray(component["frequency_values"], dtype=np.float32),
        jlpt_vocab_levels=levels,
        dedupe_values=dedupe_values,
        dedupe_to_index={value: index for index, value in enumerate(dedupe_values)},
        normalized_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
    )


def _variant_from_record(row: Mapping[str, object]) -> FormulaVariant:
    transforms = _mapping(row.get("transforms"))
    return FormulaVariant(
        variant_id=str(row.get("variant_id") or ""),
        description="trace variant",
        weights={
            str(key): float(value)
            for key, value in _mapping(row.get("weights")).items()
            if _optional_float(value) is not None
        },
        max_shift_from_frequency=_optional_float(row.get("max_shift_from_frequency")),
        piecewise_sections=tuple(
            _piecewise_section_from_record(section)
            for section in _mapping_rows(row.get("piecewise_sections"))
        ),
        jlpt_vocab_curve=_jlpt_curve_from_transform(transforms.get("jlpt_vocab_curve")),
        jlpt_kanji_dampening_strength=(
            _optional_float(transforms.get("jlpt_kanji_dampening_strength")) or 0.0
        ),
    )


def _piecewise_section_from_record(row: Mapping[str, object]) -> PiecewiseFormulaSection:
    return PiecewiseFormulaSection(
        section_id=str(row.get("section_id") or ""),
        center=float(_optional_float(row.get("center")) or 0.0),
        radius=float(_optional_float(row.get("radius")) or 1.0),
        weights={
            str(key): float(value)
            for key, value in _mapping(row.get("weights")).items()
            if _optional_float(value) is not None
        },
        max_shift_from_frequency=_optional_float(row.get("max_shift_from_frequency")),
    )


def _jlpt_curve_from_transform(value: object) -> dict[int, float] | None:
    curve = _mapping(value)
    if not curve:
        return None
    parsed: dict[int, float] = {}
    for key, raw in curve.items():
        text = str(key).upper().strip()
        if text.startswith("N"):
            text = text[1:]
        try:
            level = int(text)
        except ValueError:
            continue
        parsed[level] = float(raw)
    return parsed or None


def _selected_expert_ids(
    band_rankings: Sequence[Mapping[str, object]],
    key: str,
    fallback: str,
) -> tuple[str, ...]:
    ids = []
    for row in band_rankings:
        expert = _mapping(row.get(key))
        ids.append(str(expert.get("variant_id") or fallback))
    return tuple(ids)


def _segment_ids_for_bands(values: object, bands: Sequence[DifficultyBandSpec]) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    segment_ids = np.full(len(parsed), len(bands) - 1, dtype=np.int64)
    for index, band in enumerate(bands):
        if index == len(bands) - 1:
            mask = (parsed >= band.start) & (parsed <= band.end)
        else:
            mask = (parsed >= band.start) & (parsed < band.end)
        segment_ids[mask] = index
    return segment_ids


def _expected_band_mask(values: object, band: DifficultyBandSpec, *, is_last: bool) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    finite = np.isfinite(parsed)
    if is_last:
        return finite & (parsed >= band.start) & (parsed <= band.end)
    return finite & (parsed >= band.start) & (parsed < band.end)


def _guard_pass(scores: Mapping[str, object], guard: Mapping[str, object]) -> bool:
    balanced = _optional_float(scores.get("balanced_score")) or 0.0
    pairwise = _optional_float(scores.get("pairwise_order_score")) or 0.0
    beginner = _optional_float(scores.get("beginner_core_score")) or 0.0
    upper_tail = _optional_float(scores.get("upper_tail_score")) or 0.0
    high_tail = _optional_float(scores.get("high_tail_score")) or 0.0
    default_decision = _optional_float(scores.get("default_decision_score")) or 0.0
    return (
        balanced >= float(guard.get("balanced_score_min") or 0.0)
        and pairwise >= float(guard.get("pairwise_order_score_min") or 0.0)
        and beginner >= float(guard.get("beginner_core_score_min") or 0.0)
        and upper_tail >= float(guard.get("upper_tail_score_min") or 0.0)
        and high_tail >= float(guard.get("high_tail_score_min") or 0.0)
        and default_decision >= float(guard.get("default_decision_score_min") or 0.0)
    )


def _band_gain_attribution(
    *,
    expert_bands: Sequence[DifficultyBandSpec],
    band_rankings: Sequence[Mapping[str, object]],
    stitch_candidates: Sequence[StitchCandidate],
    exact_top: Sequence[Mapping[str, object]],
    calibration_context: Mapping[str, object],
    base_normalized: object,
    base_calibration_values: object,
    detail_candidate_limit: int,
    variant_index: Mapping[str, int],
    observed_matrix: object,
) -> list[dict[str, object]]:
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    expected_bands = [str(value) for value in calibration_context["expected_bands"]]
    labels = [str(value) for value in calibration_context["labels"]]
    base_observed = _calibration_observed(
        base_normalized,
        calibration_context,
        fallback_values=base_calibration_values,
    )
    segment_ids = _segment_ids_for_bands(base_normalized, expert_bands)
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    candidate_by_id = {candidate.candidate_id: candidate for candidate in stitch_candidates}
    top_candidate_ids = [
        str(row.get("candidate_id") or "")
        for row in _mapping_rows(exact_top)[: max(1, detail_candidate_limit)]
    ]
    observed_by_candidate_id = {
        candidate_id: _calibration_observed(
            candidate_by_id[candidate_id].normalized_values,
            calibration_context,
            fallback_values=candidate_by_id[candidate_id].calibration_observed_fallback,
        )
        for candidate_id in top_candidate_ids
        if candidate_id in candidate_by_id
    }
    observed_matrix_values = np.asarray(observed_matrix, dtype=np.float32)
    rows = []
    for band_index, band in enumerate(expert_bands):
        ranking = _mapping(band_rankings[band_index]) if band_index < len(band_rankings) else {}
        expected_mask = _expected_band_mask(
            expected,
            band,
            is_last=band_index == len(expert_bands) - 1,
        )
        base_summary = _local_band_summary(
            band=band,
            band_index=band_index,
            expert_bands=expert_bands,
            expected_values=expected,
            observed_values=base_observed,
            expected_bands=expected_bands,
            labels=labels,
        )
        guarded = _mapping(ranking.get("best_guarded"))
        unconstrained = _mapping(ranking.get("best_unconstrained"))
        guarded_summary = _expert_local_summary(
            guarded,
            band=band,
            band_index=band_index,
            expert_bands=expert_bands,
            expected_values=expected,
            expected_bands=expected_bands,
            labels=labels,
            variant_index=variant_index,
            observed_matrix=observed_matrix_values,
        )
        unconstrained_summary = _expert_local_summary(
            unconstrained,
            band=band,
            band_index=band_index,
            expert_bands=expert_bands,
            expected_values=expected,
            expected_bands=expected_bands,
            labels=labels,
            variant_index=variant_index,
            observed_matrix=observed_matrix_values,
        )
        stitched_summaries = []
        for candidate_id, observed in observed_by_candidate_id.items():
            stitched_summaries.append(
                {
                    "candidate_id": candidate_id,
                    "local": _local_band_summary(
                        band=band,
                        band_index=band_index,
                        expert_bands=expert_bands,
                        expected_values=expected,
                        observed_values=observed,
                        expected_bands=expected_bands,
                        labels=labels,
                    ),
                }
            )
        stitched_summaries = sorted(
            stitched_summaries,
            key=lambda row: _optional_float(_mapping(row.get("local")).get("mae")) or 999.0,
        )
        top_global_id = (
            str(_mapping_rows(exact_top)[0].get("candidate_id") or "") if exact_top else ""
        )
        top_global_local = next(
            (
                row
                for row in stitched_summaries
                if str(row.get("candidate_id") or "") == top_global_id
            ),
            None,
        )
        rows.append(
            {
                "band": band.band_id,
                "label_count": int(np.asarray(expected_mask, dtype=bool).sum()),
                "selector": _selector_summary(
                    band=band,
                    band_index=band_index,
                    expert_bands=expert_bands,
                    expected_values=expected,
                    base_observed=base_observed,
                    segment_ids=segment_ids,
                    component_indices=component_indices,
                    labels=labels,
                ),
                "base": base_summary,
                "guarded_expert": {
                    "candidate_id": guarded.get("variant_id"),
                    "local": guarded_summary,
                },
                "unconstrained_expert": {
                    "candidate_id": unconstrained.get("variant_id"),
                    "local": unconstrained_summary,
                },
                "top_global_stitched": top_global_local or {},
                "best_stitched_local": stitched_summaries[0] if stitched_summaries else {},
                "top_stitched_local": stitched_summaries[:5],
                "gain": _gain_summary(
                    base_summary,
                    guarded_summary,
                    _mapping((top_global_local or {}).get("local")),
                    _mapping((stitched_summaries[0] if stitched_summaries else {}).get("local")),
                ),
            }
        )
    return rows


def _expert_local_summary(
    expert: Mapping[str, object],
    *,
    band: DifficultyBandSpec,
    band_index: int,
    expert_bands: Sequence[DifficultyBandSpec],
    expected_values: object,
    expected_bands: Sequence[str],
    labels: Sequence[str],
    variant_index: Mapping[str, int],
    observed_matrix: object,
) -> dict[str, object]:
    variant_id = str(expert.get("variant_id") or "")
    if variant_id not in variant_index:
        return {}
    observed = np.asarray(observed_matrix, dtype=np.float32)[int(variant_index[variant_id])]
    return _local_band_summary(
        band=band,
        band_index=band_index,
        expert_bands=expert_bands,
        expected_values=expected_values,
        observed_values=observed,
        expected_bands=expected_bands,
        labels=labels,
    )


def _local_band_summary(
    *,
    band: DifficultyBandSpec,
    band_index: int,
    expert_bands: Sequence[DifficultyBandSpec],
    expected_values: object,
    observed_values: object,
    expected_bands: Sequence[str],
    labels: Sequence[str],
) -> dict[str, object]:
    expected = np.asarray(expected_values, dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    mask = _expected_band_mask(
        expected,
        band,
        is_last=band_index == len(expert_bands) - 1,
    )
    local_indices = np.where(mask & np.isfinite(expected) & np.isfinite(observed))[0]
    if not len(local_indices):
        return {
            "label_count": 0,
            "mae": None,
            "numeric_score": None,
            "rmse": None,
            "within_0_10_rate": None,
            "bucket_accuracy": None,
            "mismatch_count": 0,
            "top_errors": [],
        }
    errors = np.abs(observed[local_indices] - expected[local_indices])
    bucket_matches = 0
    bucket_rows = []
    mismatches = []
    for row_index in local_indices:
        expected_bucket = expected_bands[row_index]
        if not expected_bucket:
            continue
        observed_bucket = _difficulty_band(observed[row_index])
        bucket_rows.append(row_index)
        if observed_bucket == expected_bucket:
            bucket_matches += 1
        else:
            mismatches.append(
                {
                    "label": labels[row_index],
                    "expected": expected_bucket,
                    "observed": observed_bucket,
                    "expected_value": _rounded(float(expected[row_index])),
                    "observed_value": _rounded(float(observed[row_index])),
                }
            )
    error_rows = sorted(
        (
            {
                "label": labels[row_index],
                "expected_value": _rounded(float(expected[row_index])),
                "observed_value": _rounded(float(observed[row_index])),
                "absolute_error": _rounded(float(abs(observed[row_index] - expected[row_index]))),
            }
            for row_index in local_indices
        ),
        key=lambda row: _optional_float(row.get("absolute_error")) or -1.0,
        reverse=True,
    )
    mae = float(errors.mean())
    return {
        "label_count": int(len(local_indices)),
        "mae": _rounded(mae),
        "numeric_score": _rounded(1.0 - mae),
        "rmse": _rounded(float(np.sqrt(np.mean(errors * errors)))),
        "within_0_10_rate": _rounded(float((errors <= 0.10).sum()) / float(len(errors))),
        "bucket_accuracy": _rounded(_ratio_or_none(bucket_matches, len(bucket_rows))),
        "mismatch_count": int(len(mismatches)),
        "mismatches": mismatches[:8],
        "top_errors": error_rows[:8],
    }


def _selector_summary(
    *,
    band: DifficultyBandSpec,
    band_index: int,
    expert_bands: Sequence[DifficultyBandSpec],
    expected_values: object,
    base_observed: object,
    segment_ids: object,
    component_indices: object,
    labels: Sequence[str],
) -> dict[str, object]:
    expected = np.asarray(expected_values, dtype=np.float32)
    observed = np.asarray(base_observed, dtype=np.float32)
    segments = np.asarray(segment_ids, dtype=np.int64)
    indices = np.asarray(component_indices, dtype=np.int64)
    mask = _expected_band_mask(
        expected,
        band,
        is_last=band_index == len(expert_bands) - 1,
    )
    expected_indices = np.where(mask & np.isfinite(expected))[0]
    valid_indices = [index for index in expected_indices if indices[index] >= 0]
    matched = []
    misses = []
    for label_index in valid_indices:
        component_index = int(indices[label_index])
        selected_index = int(segments[component_index])
        selected_band = (
            expert_bands[selected_index].band_id
            if 0 <= selected_index < len(expert_bands)
            else "out-of-range"
        )
        if selected_index == band_index:
            matched.append(label_index)
        else:
            misses.append(
                {
                    "label": labels[label_index],
                    "expected_value": _rounded(float(expected[label_index])),
                    "base_observed_value": (
                        _rounded(float(observed[label_index]))
                        if np.isfinite(observed[label_index])
                        else None
                    ),
                    "selected_band": selected_band,
                }
            )
    return {
        "expected_label_count": int(len(expected_indices)),
        "valid_component_count": int(len(valid_indices)),
        "match_count": int(len(matched)),
        "match_rate": _rounded(_ratio_or_none(len(matched), len(valid_indices))),
        "missing_component_count": int(len(expected_indices) - len(valid_indices)),
        "misses": misses[:10],
    }


def _gain_summary(
    base: Mapping[str, object],
    guarded_expert: Mapping[str, object],
    top_global_stitched: Mapping[str, object],
    best_stitched: Mapping[str, object],
) -> dict[str, object]:
    base_mae = _optional_float(base.get("mae"))
    expert_mae = _optional_float(guarded_expert.get("mae"))
    top_mae = _optional_float(top_global_stitched.get("mae"))
    best_mae = _optional_float(best_stitched.get("mae"))
    theoretical_gain = (
        base_mae - expert_mae if base_mae is not None and expert_mae is not None else None
    )
    top_gain = base_mae - top_mae if base_mae is not None and top_mae is not None else None
    best_gain = base_mae - best_mae if base_mae is not None and best_mae is not None else None
    return {
        "guarded_expert_theoretical_mae_gain": _rounded(theoretical_gain),
        "top_global_stitched_mae_gain": _rounded(top_gain),
        "best_stitched_mae_gain": _rounded(best_gain),
        "top_global_capture_rate": _rounded(_safe_gain_ratio(top_gain, theoretical_gain)),
        "best_stitched_capture_rate": _rounded(_safe_gain_ratio(best_gain, theoretical_gain)),
    }


def _safe_gain_ratio(value: float | None, denominator: float | None) -> float | None:
    if value is None or denominator is None or denominator <= 0:
        return None
    return value / denominator


def _ratio_or_none(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def _leaderboards(rows: Sequence[Mapping[str, object]], *, limit: int) -> dict[str, object]:
    keys = (
        "balanced_score",
        "numeric_mae_score",
        "bucket_accuracy_score",
        "pairwise_order_score",
        "rank_correlation_score",
        "upper_tail_score",
        "high_tail_score",
    )
    return {
        key: sorted(
            (
                {
                    "candidate_id": str(row.get("candidate_id") or ""),
                    "score": _mapping(row.get("scores")).get(key),
                    "balanced_score": _mapping(row.get("scores")).get("balanced_score"),
                    "mode": row.get("mode"),
                    "expert_strategy": row.get("expert_strategy"),
                }
                for row in rows
                if _optional_float(_mapping(row.get("scores")).get(key)) is not None
            ),
            key=lambda item: _optional_float(item.get("score")) or -1.0,
            reverse=True,
        )[:limit]
        for key in keys
    }


def _top_rows(rows: Sequence[Mapping[str, object]], *, limit: int) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in sorted(
            rows,
            key=lambda row: (
                _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("pairwise_order_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("numeric_mae_score")) or -1.0,
            ),
            reverse=True,
        )[:limit]
    ]


def _calibration_labels_by_band(
    bands: Sequence[DifficultyBandSpec],
    *,
    expected_values: object,
    labels: Sequence[str],
    expected_bands: Sequence[str],
) -> list[dict[str, object]]:
    expected = np.asarray(expected_values, dtype=np.float32)
    rows = []
    for index, band in enumerate(bands):
        mask = _expected_band_mask(expected, band, is_last=index == len(bands) - 1)
        label_rows = [
            {
                "label": labels[row_index],
                "expected_value": _rounded(float(expected[row_index])),
                "expected_band": expected_bands[row_index],
            }
            for row_index in np.where(mask)[0]
        ]
        rows.append({"band": band.band_id, "label_count": len(label_rows), "labels": label_rows})
    return rows


def _side_by_side_samples(
    candidates: Sequence[Mapping[str, object]],
    *,
    label_by_candidate_id: Mapping[str, str],
) -> list[dict[str, object]]:
    sample_maps: dict[str, dict[str, list[str]]] = {}
    band_order: list[str] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        sample_maps[candidate_id] = {}
        for band in _mapping_rows(candidate.get("band_samples")):
            band_id = str(band.get("band") or "")
            if band_id and band_id not in band_order:
                band_order.append(band_id)
            sample_maps[candidate_id][band_id] = [
                f"{sample.get('lemma')}({sample.get('reading')})"
                for sample in _mapping_rows(band.get("samples"))
            ]
    rows = []
    for band_id in band_order:
        rows.append(
            {
                "band": band_id,
                "candidates": [
                    {
                        "candidate_id": str(candidate.get("candidate_id") or ""),
                        "label": label_by_candidate_id.get(
                            str(candidate.get("candidate_id") or ""),
                            str(candidate.get("candidate_id") or ""),
                        ),
                        "samples": sample_maps.get(
                            str(candidate.get("candidate_id") or ""), {}
                        ).get(
                            band_id,
                            [],
                        ),
                    }
                    for candidate in candidates
                ],
            }
        )
    return rows


def _parse_band_specs(value: str) -> tuple[DifficultyBandSpec, ...]:
    bands: list[DifficultyBandSpec] = []
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        if ":" not in text:
            raise ValueError(f"Expected band start:end, got: {text}")
        raw_start, raw_end = text.split(":", 1)
        start = float(raw_start)
        end = float(raw_end)
        if start < 0.0 or end > 1.0 or start >= end:
            raise ValueError(f"Invalid band bounds: {text}")
        bands.append(DifficultyBandSpec(f"{start:.2f}-{end:.2f}", start, end))
    if not bands:
        raise ValueError("At least one expert band is required.")
    return tuple(bands)


def _parse_float_csv(value: str) -> tuple[float, ...]:
    values = []
    for item in str(value or "").split(","):
        text = item.strip()
        if text:
            values.append(float(text))
    return tuple(values)


def _band_json(band: DifficultyBandSpec) -> dict[str, object]:
    return {"band": band.band_id, "start": _rounded(band.start), "end": _rounded(band.end)}


def _strength_id(value: float) -> str:
    return f"{int(round(float(value) * 100)):03d}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    base = _mapping(report.get("base_reference"))
    base_scores = _mapping(base.get("scores"))
    trace_scores = _mapping(base.get("trace_scores"))
    lines = [
        "# en-ja Learner Difficulty Band-Expert Stitch Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Trace variants: `{_escape(inputs.get('trace_variant_count'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Normalization population: `{_escape(inputs.get('normalization_population_count'))}`",
        f"- Base candidate: `{_escape(inputs.get('base_candidate_id'))}`",
        "",
        "## Method",
        "",
        (
            "This harness ranks retained trace candidates independently inside "
            "each expected difficulty band, then stitches the selected band experts "
            "over the full corpus using the base candidate's normalized score as "
            "the segment selector. It is research-only and does not change runtime behavior."
        ),
        "",
        "## Base Reference",
        "",
        (
            f"- Balanced `{_escape(base_scores.get('balanced_score'))}`, "
            f"MAE score `{_escape(base_scores.get('numeric_mae_score'))}`, "
            f"bucket `{_escape(base_scores.get('bucket_accuracy_score'))}`, "
            f"pairwise `{_escape(base_scores.get('pairwise_order_score'))}`, "
            f"upper tail `{_escape(base_scores.get('upper_tail_score'))}`, "
            f"high tail `{_escape(base_scores.get('high_tail_score'))}`"
        ),
        (
            f"- Source trace balanced `{_escape(trace_scores.get('balanced_score'))}`, "
            f"pairwise `{_escape(trace_scores.get('pairwise_order_score'))}`. "
            "The recomputed reference uses this stitch harness' metric path for "
            "apples-to-apples comparison."
        ),
        "",
        "## Band Expert Winners",
        "",
        (
            "| Band | Labels | Unconstrained expert | Local MAE | Guarded expert | "
            "Local MAE | Guard pass |"
        ),
        "| --- | ---: | --- | ---: | --- | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("band_rankings")):
        unconstrained = _mapping(row.get("best_unconstrained"))
        guarded = _mapping(row.get("best_guarded"))
        lines.append(
            "| "
            f"`{_escape(row.get('band'))}` | "
            f"`{_escape(row.get('label_count'))}` | "
            f"`{_escape(unconstrained.get('variant_id'))}` | "
            f"`{_escape(unconstrained.get('local_mae'))}` | "
            f"`{_escape(guarded.get('variant_id'))}` | "
            f"`{_escape(guarded.get('local_mae'))}` | "
            f"`{_escape(guarded.get('guard_pass'))}` |"
        )
    lines.extend(
        [
            "",
            "## Band Gain Attribution",
            "",
            (
                "This table compares the theoretical local gain from the guarded "
                "band expert with the gain actually captured by stitched candidates. "
                "Selector match is the share of labels in the human expected band "
                "that the base model also routes to that same stitch band."
            ),
            "",
            (
                "| Band | Labels | Selector Match | Base MAE | Guarded Expert MAE | "
                "Global #1 MAE | Best Stitched MAE | Theoretical Gain | Captured |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("band_gain_attribution")):
        selector = _mapping(row.get("selector"))
        base_local = _mapping(row.get("base"))
        guarded_local = _mapping(_mapping(row.get("guarded_expert")).get("local"))
        top_global = _mapping(row.get("top_global_stitched"))
        top_global_local = _mapping(top_global.get("local"))
        best_stitched = _mapping(row.get("best_stitched_local"))
        best_stitched_local = _mapping(best_stitched.get("local"))
        gain = _mapping(row.get("gain"))
        captured = (
            f"global `{_escape(gain.get('top_global_capture_rate'))}`, "
            f"best `{_escape(gain.get('best_stitched_capture_rate'))}`"
        )
        lines.append(
            "| "
            f"`{_escape(row.get('band'))}` | "
            f"`{_escape(row.get('label_count'))}` | "
            f"`{_escape(selector.get('match_rate'))}` | "
            f"`{_escape(base_local.get('mae'))}` | "
            f"`{_escape(guarded_local.get('mae'))}` | "
            f"`{_escape(top_global_local.get('mae'))}` | "
            f"`{_escape(best_stitched_local.get('mae'))}` | "
            f"`{_escape(gain.get('guarded_expert_theoretical_mae_gain'))}` | "
            f"{captured} |"
        )
    selector_miss_lines = []
    for row in _mapping_rows(report.get("band_gain_attribution")):
        selector = _mapping(row.get("selector"))
        misses = _mapping_rows(selector.get("misses"))
        if not misses:
            continue
        compact = ", ".join(
            f"{item.get('label')}->{item.get('selected_band')} ({item.get('base_observed_value')})"
            for item in misses[:6]
        )
        selector_miss_lines.append(f"- `{row.get('band')}`: {compact}")
    if selector_miss_lines:
        lines.extend(["", "Selector misses with base-observed value:", ""])
        lines.extend(selector_miss_lines)
    lines.extend(
        [
            "",
            "## Stitched Candidates",
            "",
            (
                "| Rank | Candidate | Mode | Strategy | Strength | Balanced | MAE | "
                "Bucket | Pairwise | Beginner | Upper Tail | High Tail | Mismatches |"
            ),
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, row in enumerate(_mapping_rows(report.get("exact_top"))[:20], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            "| "
            f"{index} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('mode'))}` | "
            f"`{_escape(row.get('expert_strategy'))}` | "
            f"`{_escape(row.get('soft_strength'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(scores.get('numeric_mae_score'))}` | "
            f"`{_escape(scores.get('bucket_accuracy_score'))}` | "
            f"`{_escape(scores.get('pairwise_order_score'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('upper_tail_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_escape(metrics.get('bucket_mismatch_count'))}` |"
        )
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        lines.extend(_candidate_detail_lines(row))
    lines.extend(["", "## Side-By-Side Band Samples", ""])
    for band in _mapping_rows(report.get("side_by_side_samples")):
        lines.append(f"### `{_escape(band.get('band'))}`")
        lines.append("")
        for candidate in _mapping_rows(band.get("candidates")):
            samples = ", ".join(str(value) for value in _sequence_values(candidate.get("samples")))
            lines.append(
                f"- `{_escape(candidate.get('label'))}` `{_escape(candidate.get('candidate_id'))}`: "
                f"{_escape(samples)}"
            )
        lines.append("")
    lines.extend(["", "## Calibration Labels By Band", ""])
    for band in _mapping_rows(report.get("calibration_labels_by_band")):
        labels = ", ".join(
            f"{item.get('label')}={item.get('expected_value')}"
            for item in _mapping_rows(band.get("labels"))
        )
        lines.append(
            f"- `{_escape(band.get('band'))}` ({_escape(band.get('label_count'))}): "
            f"{_escape(labels)}"
        )
    return "\n".join(lines) + "\n"


def _candidate_detail_lines(row: Mapping[str, object]) -> list[str]:
    lines = [
        "",
        f"### `{_escape(row.get('candidate_id'))}`",
        "",
        f"- Experts: `{_escape(', '.join(str(value) for value in _sequence_values(row.get('expert_ids'))))}`",
    ]
    mismatches = _mapping_rows(row.get("difficulty_mismatches"))
    if mismatches:
        compact = ", ".join(
            f"{item.get('label')} ({item.get('expected')}->{item.get('observed')}, "
            f"{item.get('expected_value')}->{item.get('observed_value')})"
            for item in mismatches[:12]
        )
        lines.append(f"- Difficulty mismatches: {compact}")
    misses = _mapping(row.get("segment_misses"))
    if misses:
        lines.append(f"- Segment misses: `{_escape(misses)}`")
    samples = _mapping_rows(row.get("band_samples"))
    if samples:
        lines.extend(["", "Band samples:", ""])
        for band in samples:
            sample_text = ", ".join(
                f"{sample.get('lemma')}({sample.get('reading')})"
                for sample in _mapping_rows(band.get("samples"))
            )
            lines.append(
                f"- `{_escape(band.get('band'))}` count `{_escape(band.get('count'))}`: "
                f"{_escape(sample_text)}"
            )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
