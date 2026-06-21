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
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-ja"
DEFAULT_SWEEP_ARTIFACT_PREFIX = (
    "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010"
)
DEFAULT_TRACE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / f"{DEFAULT_SWEEP_ARTIFACT_PREFIX}_trace_latest.json"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / f"{DEFAULT_SWEEP_ARTIFACT_PREFIX}_calibration_matrix_latest.npz"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / f"{DEFAULT_SWEEP_ARTIFACT_PREFIX}_component_matrix_latest.npz"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_proficiency_ordering_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_proficiency_ordering_en_ja_latest.md"
)

NORMAL_VOCAB_STATES = frozenset({"normal_vocab"})
VOCAB_PLACEMENT_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})
DEFAULT_ACCEPT_STATES = VOCAB_PLACEMENT_STATES
DEFAULT_PROFICIENCY_POINTS = tuple(round(index / 10.0, 2) for index in range(11))
DEFAULT_CHALLENGE_OFFSET = 0.05
DEFAULT_WINDOW_SIGMA = 0.12
DEFAULT_WINDOW_TOP_K = 12
DEFAULT_RETAIN_CANDIDATES = 80
JLPT_DAMPENED_KANJI_COMPONENTS = frozenset(
    {
        "old_jlpt_kanji",
        "kanji_grade",
        "kanji_frequency_rank",
        "stroke_count",
        "kanjivg_visual_complexity",
        "kanji_curriculum_burden",
        "kanji_shape_burden",
        "max_kanji_shape_burden",
        "kanji_burden",
        "max_kanji_burden",
        "written_form_burden",
        "max_written_form_burden",
        "kango_old_jlpt_kanji",
        "kango_kanji_grade",
        "kango_visual_complexity",
        "kango_kanji_burden",
        "kango_uncommon_kanji_burden",
        "kango_mid_signal",
    }
)


@dataclass(frozen=True)
class ComponentContext:
    component_names: tuple[str, ...]
    component_values: object
    component_present: object
    current_values: object
    frequency_values: object
    jlpt_vocab_levels: object
    target_curve_positions: object
    candidate_identity_keys: tuple[str, ...]
    lemmas: tuple[str, ...]
    readings: tuple[str, ...]
    candidate_states: tuple[str, ...]


@dataclass(frozen=True)
class LabelContext:
    context_id: str
    labels: tuple[str, ...]
    lemmas: tuple[str, ...]
    readings: tuple[str, ...]
    component_indices: object
    expected_values: object
    expected_bands: tuple[str, ...]
    expected_candidate_states: object
    observed_candidate_states: object
    missing_rows: tuple[Mapping[str, object], ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate en-ja learner-difficulty trace variants as a lane-first "
            "proficiency-ordering sidecar. This does not change runtime behavior."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument(
        "--proficiency-points",
        default=",".join(str(value) for value in DEFAULT_PROFICIENCY_POINTS),
        help="Comma-separated user proficiency points used for frontier-window scoring.",
    )
    parser.add_argument("--challenge-offset", type=float, default=DEFAULT_CHALLENGE_OFFSET)
    parser.add_argument("--window-sigma", type=float, default=DEFAULT_WINDOW_SIGMA)
    parser.add_argument("--window-top-k", type=int, default=DEFAULT_WINDOW_TOP_K)
    parser.add_argument(
        "--variant-limit",
        type=int,
        default=0,
        help="Optional trace-variant limit for local smoke runs. 0 evaluates all variants.",
    )
    parser.add_argument("--retain-candidates", type=int, default=DEFAULT_RETAIN_CANDIDATES)
    parser.add_argument("--leaderboard-limit", type=int, default=20)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        holdout_json_path=_resolve_path(args.holdout_json),
        proficiency_points=_parse_float_csv(args.proficiency_points),
        challenge_offset=float(args.challenge_offset),
        window_sigma=max(1e-6, float(args.window_sigma)),
        window_top_k=max(1, int(args.window_top_k)),
        variant_limit=max(0, int(args.variant_limit)),
        retain_candidates=max(1, int(args.retain_candidates)),
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
    trace_json: Path,
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    holdout_json_path: Path,
    proficiency_points: Sequence[float] = DEFAULT_PROFICIENCY_POINTS,
    challenge_offset: float = DEFAULT_CHALLENGE_OFFSET,
    window_sigma: float = DEFAULT_WINDOW_SIGMA,
    window_top_k: int = DEFAULT_WINDOW_TOP_K,
    variant_limit: int = 0,
    retain_candidates: int = DEFAULT_RETAIN_CANDIDATES,
    leaderboard_limit: int = 20,
    detail_limit: int = 20,
) -> dict[str, object]:
    trace = _load_json(trace_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    component_context = _component_context(component)
    calibration_context = _calibration_context(calibration, component_context)
    holdout_context = _label_context_from_json(
        _load_json(holdout_json_path),
        component_context=component_context,
        context_id="holdout",
    )
    variant_records = _trace_variant_records(trace)
    if variant_limit > 0:
        variant_records = variant_records[:variant_limit]
    candidates = []
    for record in variant_records:
        normalized_values = _normalized_values_for_trace_record(record, component_context)
        calibration_observed = _observed_for_context(normalized_values, calibration_context)
        holdout_observed = _observed_for_context(normalized_values, holdout_context)
        candidates.append(
            _candidate_report(
                record,
                calibration_context=calibration_context,
                calibration_observed=calibration_observed,
                holdout_context=holdout_context,
                holdout_observed=holdout_observed,
                proficiency_points=proficiency_points,
                challenge_offset=challenge_offset,
                window_sigma=window_sigma,
                window_top_k=window_top_k,
                detail_limit=detail_limit,
            )
        )

    retained = _retained_candidates(candidates, retain_candidates=retain_candidates)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Sidecar evaluation for a lane-first proficiency-placement "
                "interpretation of existing learner-difficulty trace variants."
            ),
            "prediction_shape": (
                "candidate_state/lane diagnostics are evaluated separately from "
                "normal-vocab proficiency placement L_i in [0, 1]."
            ),
            "selector_proxy": (
                "For each user proficiency p, frontier-window quality scores "
                "whether a variant retrieves normal-vocab items whose reviewed "
                "levels are near clamp(p + challenge_offset, 0, 1)."
            ),
            "normal_vocab_states": sorted(NORMAL_VOCAB_STATES),
            "vocab_placement_states": sorted(VOCAB_PLACEMENT_STATES),
            "default_accept_states": sorted(DEFAULT_ACCEPT_STATES),
            "target_curve_id": TARGET_CURVE_ID,
        },
        "parameters": {
            "proficiency_points": [round(float(value), 6) for value in proficiency_points],
            "challenge_offset": round(float(challenge_offset), 6),
            "window_sigma": round(float(window_sigma), 6),
            "window_top_k": int(window_top_k),
            "variant_limit": int(variant_limit),
            "retain_candidates": int(retain_candidates),
            "leaderboard_limit": int(leaderboard_limit),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "trace_variant_count": len(_trace_variant_records(trace)),
            "evaluated_variant_count": len(variant_records),
            "calibration_label_count": len(calibration_context.labels),
            "holdout_label_count": len(holdout_context.labels),
            "normalization_population_count": len(component_context.lemmas),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "trace_json": trace_json,
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
                "holdout_json": holdout_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
                "piecewise_metrics": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "dataset_summaries": {
            "calibration": _context_summary(calibration_context),
            "holdout": _context_summary(holdout_context),
        },
        "lane_diagnostics": {
            "calibration": _lane_metrics(calibration_context),
            "holdout": _lane_metrics(holdout_context),
        },
        "leaderboards": {
            "calibration_proficiency_ordering": _leaderboard(
                candidates,
                dataset="calibration",
                key="proficiency_ordering_score",
                limit=leaderboard_limit,
            ),
            "holdout_proficiency_ordering": _leaderboard(
                candidates,
                dataset="holdout",
                key="proficiency_ordering_score",
                limit=leaderboard_limit,
            ),
            "calibration_normal_vocab_pairwise": _leaderboard(
                candidates,
                dataset="calibration",
                key="normal_vocab_pairwise",
                limit=leaderboard_limit,
            ),
            "holdout_normal_vocab_pairwise": _leaderboard(
                candidates,
                dataset="holdout",
                key="normal_vocab_pairwise",
                limit=leaderboard_limit,
            ),
            "holdout_window_quality": _leaderboard(
                candidates,
                dataset="holdout",
                key="window_quality",
                limit=leaderboard_limit,
            ),
            "generalization_delta": _generalization_delta_leaderboard(
                candidates,
                limit=leaderboard_limit,
            ),
        },
        "primary_candidates": {
            "calibration": _top_candidate(candidates, dataset="calibration"),
            "holdout": _top_candidate(candidates, dataset="holdout"),
        },
        "candidate_results": retained,
    }


def _candidate_report(
    record: Mapping[str, object],
    *,
    calibration_context: LabelContext,
    calibration_observed: object,
    holdout_context: LabelContext,
    holdout_observed: object,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    calibration = _proficiency_dataset_report(
        calibration_context,
        calibration_observed,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout = _proficiency_dataset_report(
        holdout_context,
        holdout_observed,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    return {
        "candidate_id": str(record.get("variant_id") or ""),
        "source": "trace_variant",
        "weights": _float_mapping(record.get("weights")),
        "max_shift_from_frequency": _rounded(record.get("max_shift_from_frequency")),
        "piecewise_sections": record.get("piecewise_sections") or [],
        "transforms": record.get("transforms") or {},
        "original_trace_scores": record.get("scores") or {},
        "calibration": calibration,
        "holdout": holdout,
        "generalization": {
            "score_delta_holdout_minus_calibration": _rounded(
                _optional_float(holdout.get("proficiency_ordering_score"))
                - _optional_float(calibration.get("proficiency_ordering_score"))
            ),
            "normal_vocab_mae_delta_holdout_minus_calibration": _rounded(
                _metric_path(holdout, "normal_vocab", "metrics", "mae")
                - _metric_path(calibration, "normal_vocab", "metrics", "mae")
            ),
            "window_quality_delta_holdout_minus_calibration": _rounded(
                _metric_path(holdout, "frontier_windows", "average_window_score")
                - _metric_path(calibration, "frontier_windows", "average_window_score")
            ),
        },
    }


def _proficiency_dataset_report(
    context: LabelContext,
    observed_values: object,
    *,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    all_numeric = _placement_metrics(
        context,
        observed_values,
        expected_states=None,
        detail_limit=detail_limit,
    )
    vocab = _placement_metrics(
        context,
        observed_values,
        expected_states=VOCAB_PLACEMENT_STATES,
        detail_limit=detail_limit,
    )
    normal_vocab = _placement_metrics(
        context,
        observed_values,
        expected_states=NORMAL_VOCAB_STATES,
        detail_limit=detail_limit,
    )
    windows = _frontier_window_metrics(
        context,
        observed_values,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        sigma=window_sigma,
        top_k=window_top_k,
    )
    lane = _lane_metrics(context)
    score = _weighted_average(
        (
            (_metric_path(normal_vocab, "scores", "pairwise_order_score"), 0.25),
            (_metric_path(normal_vocab, "scores", "numeric_mae_score"), 0.25),
            (_metric_path(normal_vocab, "scores", "bucket_accuracy_score"), 0.15),
            (_metric_path(normal_vocab, "scores", "rank_correlation_score"), 0.10),
            (_metric_path(windows, "average_window_score"), 0.15),
            (_metric_path(lane, "normal_vocab_f1"), 0.05),
            (_metric_path(lane, "default_accept_accuracy"), 0.05),
        )
    )
    return {
        "proficiency_ordering_score": _rounded(score),
        "lane": lane,
        "all_numeric": all_numeric,
        "vocab": vocab,
        "normal_vocab": normal_vocab,
        "frontier_windows": windows,
    }


def _placement_metrics(
    context: LabelContext,
    observed_values: object,
    *,
    expected_states: frozenset[str] | None,
    detail_limit: int,
) -> dict[str, object]:
    expected = np.asarray(context.expected_values, dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    expected_states_array = np.asarray(context.expected_candidate_states, dtype=str)
    observed_states_array = np.asarray(context.observed_candidate_states, dtype=str)
    if expected_states is None:
        mask = np.ones(len(expected), dtype=bool)
    else:
        mask = np.asarray(
            [str(state).strip() in expected_states for state in expected_states_array],
            dtype=bool,
        )
    metrics = _difficulty_metrics(
        expected_values=expected[mask],
        observed_values=observed[mask],
        expected_bands=_masked_sequence(context.expected_bands, mask),
        expected_candidate_states=expected_states_array[mask],
        observed_candidate_states=observed_states_array[mask],
        labels=_masked_sequence(context.labels, mask),
    )
    return {
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
        "detail": {
            "difficulty_value": metrics["difficulty_value"],
            "difficulty_bucket": metrics["difficulty_bucket"],
            "pairwise_order": {
                **dict(metrics["pairwise_order"]),
                "wrong_examples": metrics["pairwise_order"]["wrong_examples"][:detail_limit],
            },
            "rank_correlation": metrics["rank_correlation"],
            "segments": metrics["segments"],
            "default_vocab_decision": metrics["default_vocab_decision"],
        },
        "worst_rows": _worst_rows(
            context,
            observed,
            expected_states=expected_states,
            limit=detail_limit,
        ),
    }


def _frontier_window_metrics(
    context: LabelContext,
    observed_values: object,
    *,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    sigma: float,
    top_k: int,
) -> dict[str, object]:
    expected = np.asarray(context.expected_values, dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    states = np.asarray(context.expected_candidate_states, dtype=str)
    eligible = (
        np.isfinite(expected)
        & np.isfinite(observed)
        & np.asarray([str(state).strip() in NORMAL_VOCAB_STATES for state in states])
    )
    indices = np.where(eligible)[0]
    rows = []
    scores = []
    for proficiency in proficiency_points:
        target = _clamp01(float(proficiency) + float(challenge_offset))
        row = _frontier_window_for_target(
            context,
            expected,
            observed,
            indices,
            target=target,
            proficiency=float(proficiency),
            sigma=sigma,
            top_k=top_k,
        )
        rows.append(row)
        score = _optional_float(row.get("window_score"))
        if score is not None:
            scores.append(score)
    return {
        "eligible_count": int(len(indices)),
        "top_k": int(top_k),
        "sigma": _rounded(sigma),
        "challenge_offset": _rounded(challenge_offset),
        "average_window_score": _rounded(sum(scores) / len(scores) if scores else None),
        "windows": rows,
    }


def _frontier_window_for_target(
    context: LabelContext,
    expected: object,
    observed: object,
    indices: object,
    *,
    target: float,
    proficiency: float,
    sigma: float,
    top_k: int,
) -> dict[str, object]:
    if len(indices) == 0:
        return {
            "proficiency": _rounded(proficiency),
            "target": _rounded(target),
            "available_count": 0,
            "window_score": None,
        }
    expected_distances = np.abs(expected[indices] - target)
    observed_distances = np.abs(observed[indices] - target)
    k = min(max(1, int(top_k)), len(indices))
    predicted_offsets = np.argsort(observed_distances, kind="stable")[:k]
    ideal_offsets = np.argsort(expected_distances, kind="stable")[:k]
    predicted_indices = indices[predicted_offsets]
    ideal_indices = indices[ideal_offsets]
    predicted_set = set(int(value) for value in predicted_indices)
    ideal_set = set(int(value) for value in ideal_indices)
    overlap = len(predicted_set & ideal_set)
    predicted_expected_distance = float(np.mean(expected_distances[predicted_offsets]))
    ideal_expected_distance = float(np.mean(expected_distances[ideal_offsets]))
    regret = max(0.0, predicted_expected_distance - ideal_expected_distance)
    distance_score = max(0.0, 1.0 - (regret / max(float(sigma), 1e-9)))
    near_rate = float(np.mean(expected_distances[predicted_offsets] <= float(sigma)))
    overlap_rate = overlap / k
    window_score = (0.40 * overlap_rate) + (0.40 * distance_score) + (0.20 * near_rate)
    return {
        "proficiency": _rounded(proficiency),
        "target": _rounded(target),
        "available_count": int(len(indices)),
        "top_k": int(k),
        "top_k_overlap_rate": _rounded(overlap_rate),
        "near_target_rate": _rounded(near_rate),
        "predicted_expected_distance": _rounded(predicted_expected_distance),
        "ideal_expected_distance": _rounded(ideal_expected_distance),
        "distance_regret": _rounded(regret),
        "distance_score": _rounded(distance_score),
        "window_score": _rounded(window_score),
        "predicted_examples": _window_examples(
            context,
            expected,
            observed,
            predicted_indices,
            target=target,
            limit=6,
        ),
    }


def _lane_metrics(context: LabelContext) -> dict[str, object]:
    expected = np.asarray(context.expected_candidate_states, dtype=str)
    observed = np.asarray(context.observed_candidate_states, dtype=str)
    count = min(len(expected), len(observed), len(context.labels))
    exact_match = 0
    default_match = 0
    normal_true_positive = 0
    normal_false_positive = 0
    normal_false_negative = 0
    normal_true_negative = 0
    evaluated_count = 0
    state_pairs = {}
    mismatches = []
    for index in range(count):
        expected_state = str(expected[index]).strip()
        observed_state = str(observed[index]).strip()
        if not expected_state or not observed_state:
            continue
        evaluated_count += 1
        pair_key = f"{expected_state}->{observed_state}"
        state_pairs[pair_key] = int(state_pairs.get(pair_key, 0)) + 1
        if expected_state == observed_state:
            exact_match += 1
        elif len(mismatches) < 20:
            mismatches.append(
                {
                    "label": context.labels[index],
                    "expected_candidate_state": expected_state,
                    "observed_candidate_state": observed_state,
                }
            )
        expected_default = expected_state in DEFAULT_ACCEPT_STATES
        observed_default = observed_state in DEFAULT_ACCEPT_STATES
        if expected_default == observed_default:
            default_match += 1
        expected_normal = expected_state in NORMAL_VOCAB_STATES
        observed_normal = observed_state in NORMAL_VOCAB_STATES
        if expected_normal and observed_normal:
            normal_true_positive += 1
        elif not expected_normal and observed_normal:
            normal_false_positive += 1
        elif expected_normal and not observed_normal:
            normal_false_negative += 1
        else:
            normal_true_negative += 1
    normal_precision = _ratio_or_none(
        normal_true_positive,
        normal_true_positive + normal_false_positive,
    )
    normal_recall = _ratio_or_none(
        normal_true_positive,
        normal_true_positive + normal_false_negative,
    )
    normal_f1 = _f1(normal_precision, normal_recall)
    return {
        "row_count": int(count),
        "evaluated_count": int(evaluated_count),
        "exact_state_accuracy": _rounded(_ratio_or_none(exact_match, evaluated_count)),
        "default_accept_accuracy": _rounded(_ratio_or_none(default_match, evaluated_count)),
        "normal_vocab_precision": _rounded(normal_precision),
        "normal_vocab_recall": _rounded(normal_recall),
        "normal_vocab_f1": _rounded(normal_f1),
        "normal_vocab_counts": {
            "true_positive": normal_true_positive,
            "false_positive": normal_false_positive,
            "false_negative": normal_false_negative,
            "true_negative": normal_true_negative,
        },
        "state_pair_counts": dict(sorted(state_pairs.items())),
        "mismatches": mismatches,
    }


def _normalized_values_for_trace_record(
    record: Mapping[str, object],
    context: ComponentContext,
) -> object:
    raw = _raw_scores_for_trace_record(record, context)
    return _target_curve_normalize(raw, target_positions=context.target_curve_positions)


def _raw_scores_for_trace_record(
    record: Mapping[str, object],
    context: ComponentContext,
) -> object:
    if (
        bool(record.get("use_current_value"))
        or str(record.get("variant_id")) == "current_production"
    ):
        return np.clip(context.current_values, 0.0, 1.0)
    piecewise_sections = record.get("piecewise_sections")
    if isinstance(piecewise_sections, Sequence) and not isinstance(
        piecewise_sections,
        (str, bytes),
    ):
        sections = [section for section in piecewise_sections if isinstance(section, Mapping)]
        if sections:
            return _raw_scores_for_piecewise_sections(
                sections,
                record=record,
                context=context,
            )
    return _raw_scores_for_weights(
        weights=_float_mapping(record.get("weights")),
        max_shift_from_frequency=_optional_float(record.get("max_shift_from_frequency")),
        transforms=_mapping(record.get("transforms")),
        context=context,
    )


def _raw_scores_for_piecewise_sections(
    sections: Sequence[Mapping[str, object]],
    *,
    record: Mapping[str, object],
    context: ComponentContext,
) -> object:
    frequency = np.nan_to_num(context.frequency_values, nan=0.0)
    section_scores = []
    section_influences = []
    for section in sections:
        section_scores.append(
            _raw_scores_for_weights(
                weights=_float_mapping(section.get("weights")),
                max_shift_from_frequency=_optional_float(section.get("max_shift_from_frequency")),
                transforms=_mapping(record.get("transforms")),
                context=context,
            )
        )
        center = _optional_float(section.get("center")) or 0.5
        radius = max(1e-9, _optional_float(section.get("radius")) or 1.0)
        section_influences.append(np.maximum(0.0, 1.0 - (np.abs(frequency - center) / radius)))
    scores = np.stack(section_scores, axis=1)
    influences = np.stack(section_influences, axis=1)
    influence_sum = influences.sum(axis=1)
    if bool((influence_sum <= 0.0).any()):
        centers = np.asarray(
            [_optional_float(section.get("center")) or 0.5 for section in sections],
            dtype=np.float32,
        )
        nearest = np.argmin(np.abs(frequency[:, None] - centers[None, :]), axis=1)
        fallback = np.zeros_like(influences)
        fallback[np.arange(len(frequency)), nearest] = 1.0
        influences = np.where(influence_sum[:, None] > 0.0, influences, fallback)
        influence_sum = influences.sum(axis=1)
    raw = (scores * influences).sum(axis=1) / influence_sum
    max_shift = _optional_float(record.get("max_shift_from_frequency"))
    if max_shift is not None:
        raw = _cap_shift_from_frequency(raw, context.frequency_values, max_shift)
    return np.clip(raw, 0.0, 1.0)


def _raw_scores_for_weights(
    *,
    weights: Mapping[str, float],
    max_shift_from_frequency: float | None,
    transforms: Mapping[str, object],
    context: ComponentContext,
) -> object:
    weight_array = np.asarray(
        [max(0.0, float(weights.get(name, 0.0))) for name in context.component_names],
        dtype=np.float64,
    )
    active = weight_array > 0.0
    if not bool(active.any()):
        return np.clip(np.nan_to_num(context.frequency_values, nan=0.0), 0.0, 1.0)
    component_values, component_present = _component_arrays_for_transforms(context, transforms)
    active_weights = weight_array[active]
    values = component_values[:, active]
    present = component_present[:, active]
    numerator = (values * present * active_weights).sum(axis=1)
    denominator = (present * active_weights).sum(axis=1)
    fallback = np.nan_to_num(context.frequency_values, nan=0.0)
    raw = fallback.copy()
    np.divide(numerator, denominator, out=raw, where=denominator > 0.0)
    if max_shift_from_frequency is not None:
        raw = _cap_shift_from_frequency(raw, context.frequency_values, max_shift_from_frequency)
    return np.clip(raw, 0.0, 1.0)


def _component_arrays_for_transforms(
    context: ComponentContext,
    transforms: Mapping[str, object],
) -> tuple[object, object]:
    curve = _jlpt_curve_from_transform(transforms.get("jlpt_vocab_curve"))
    strength = _optional_float(transforms.get("jlpt_kanji_dampening_strength")) or 0.0
    if not curve and strength <= 0.0:
        return context.component_values, context.component_present
    values = context.component_values.copy()
    present = context.component_present.copy()
    name_to_index = {name: index for index, name in enumerate(context.component_names)}
    anchor = _jlpt_vocab_anchor_array(context.jlpt_vocab_levels, curve)
    anchor_present = ~np.isnan(anchor)
    jlpt_index = name_to_index.get("jlpt_vocab_difficulty")
    if jlpt_index is not None and curve:
        values[:, jlpt_index] = np.nan_to_num(anchor, nan=0.0)
        present[:, jlpt_index] = anchor_present
    if strength <= 0.0:
        return values, present
    strength = _clamp01(strength)
    for name in JLPT_DAMPENED_KANJI_COMPONENTS:
        index = name_to_index.get(name)
        if index is None:
            continue
        mask = present[:, index] & anchor_present
        if not bool(mask.any()):
            continue
        original = values[:, index]
        adjusted = original - (strength * np.maximum(0.0, original - anchor))
        values[:, index] = np.where(mask, adjusted, original)
    return np.clip(values, 0.0, 1.0), present


def _jlpt_curve_from_transform(value: object) -> dict[int, float]:
    if not isinstance(value, Mapping):
        return {}
    curve = {}
    for key, raw in value.items():
        text = str(key).strip().upper()
        if text.startswith("N"):
            text = text[1:]
        try:
            level = int(text)
            parsed = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if 1 <= level <= 5:
            curve[level] = _clamp01(parsed)
    return curve


def _jlpt_vocab_anchor_array(levels: object, curve: Mapping[int, float]) -> object:
    anchor = np.full(len(levels), np.nan, dtype=np.float32)
    if not curve:
        return anchor
    parsed = np.asarray(levels, dtype=np.float32)
    for level, value in curve.items():
        anchor[np.isfinite(parsed) & (parsed == float(level))] = float(value)
    return anchor


def _cap_shift_from_frequency(raw: object, frequency: object, max_shift: float) -> object:
    capped = np.minimum(frequency + max_shift, np.maximum(frequency - max_shift, raw))
    return np.where(np.isnan(frequency), raw, capped)


def _target_curve_normalize(raw: object, *, target_positions: object) -> object:
    raw_array = np.asarray(raw, dtype=np.float32)
    positions = np.asarray(target_positions, dtype=np.float32)
    if len(raw_array) != len(positions):
        raise ValueError(
            f"Raw score count {len(raw_array)} does not match target positions {len(positions)}"
        )
    order = np.argsort(raw_array, kind="stable")
    normalized = np.empty_like(raw_array)
    normalized[order] = positions
    return normalized


def _component_context(component: object) -> ComponentContext:
    count = len(component["lemmas"])
    return ComponentContext(
        component_names=tuple(str(value) for value in component["component_names"]),
        component_values=np.asarray(component["component_values"], dtype=np.float32),
        component_present=np.asarray(component["component_present"], dtype=bool),
        current_values=_optional_np_array(component, "current_values", count, default=0.0),
        frequency_values=_optional_np_array(component, "frequency_values", count, default=np.nan),
        jlpt_vocab_levels=_optional_np_array(component, "jlpt_vocab_levels", count, default=np.nan),
        target_curve_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
        candidate_identity_keys=tuple(str(value) for value in component["candidate_identity_keys"]),
        lemmas=tuple(str(value) for value in component["lemmas"]),
        readings=tuple(str(value) for value in component["readings"]),
        candidate_states=tuple(
            str(value) for value in _optional_string_array(component, "candidate_states", count)
        ),
    )


def _calibration_context(
    calibration: object,
    component_context: ComponentContext,
) -> LabelContext:
    component_indices = _component_indices_for_rows(
        identities=[str(value) for value in calibration["calibration_identity_keys"]],
        lemmas=[str(value) for value in calibration["calibration_lemmas"]],
        readings=[str(value) for value in calibration["calibration_readings"]],
        component_context=component_context,
    )
    observed_states = _optional_string_array(
        calibration,
        "observed_candidate_states",
        len(component_indices),
        fallback=_observed_states_for_indices(component_indices, component_context),
    )
    labels = tuple(
        _label(lemma, reading)
        for lemma, reading in zip(
            calibration["calibration_lemmas"],
            calibration["calibration_readings"],
        )
    )
    return LabelContext(
        context_id="calibration",
        labels=labels,
        lemmas=tuple(str(value) for value in calibration["calibration_lemmas"]),
        readings=tuple(str(value) for value in calibration["calibration_readings"]),
        component_indices=component_indices,
        expected_values=np.asarray(calibration["expected_values"], dtype=np.float32),
        expected_bands=tuple(str(value) for value in calibration["expected_bands"]),
        expected_candidate_states=_optional_string_array(
            calibration,
            "expected_candidate_states",
            len(component_indices),
        ),
        observed_candidate_states=observed_states,
        missing_rows=_missing_rows(labels, component_indices),
    )


def _label_context_from_json(
    payload: Mapping[str, object],
    *,
    component_context: ComponentContext,
    context_id: str,
) -> LabelContext:
    rows = [row for row in _mapping_rows(payload.get("labels"))]
    identities = [str(row.get("candidate_identity_key") or "") for row in rows]
    lemmas = [str(row.get("lemma") or "") for row in rows]
    readings = [
        str(row.get("observed_reading") or row.get("expected_reading") or "") for row in rows
    ]
    component_indices = _component_indices_for_rows(
        identities=identities,
        lemmas=lemmas,
        readings=readings,
        component_context=component_context,
    )
    expected_values = np.asarray(
        [
            np.nan
            if _optional_float(row.get("expected_learner_difficulty")) is None
            else float(_optional_float(row.get("expected_learner_difficulty")) or 0.0)
            for row in rows
        ],
        dtype=np.float32,
    )
    labels = tuple(_label(lemma, reading) for lemma, reading in zip(lemmas, readings))
    return LabelContext(
        context_id=context_id,
        labels=labels,
        lemmas=tuple(lemmas),
        readings=tuple(readings),
        component_indices=component_indices,
        expected_values=expected_values,
        expected_bands=tuple(str(row.get("expected_difficulty_band") or "") for row in rows),
        expected_candidate_states=np.asarray(
            [str(row.get("expected_candidate_state") or "") for row in rows],
            dtype="<U64",
        ),
        observed_candidate_states=_observed_states_for_indices(
            component_indices,
            component_context,
        ),
        missing_rows=_missing_rows(labels, component_indices),
    )


def _component_indices_for_rows(
    *,
    identities: Sequence[str],
    lemmas: Sequence[str],
    readings: Sequence[str],
    component_context: ComponentContext,
) -> object:
    by_identity = {
        identity: index
        for index, identity in enumerate(component_context.candidate_identity_keys)
        if identity
    }
    by_lemma_reading = {
        (lemma, reading): index
        for index, (lemma, reading) in enumerate(
            zip(component_context.lemmas, component_context.readings)
        )
    }
    indices = []
    for identity, lemma, reading in zip(identities, lemmas, readings):
        index = by_identity.get(identity)
        if index is None:
            index = by_lemma_reading.get((lemma, reading))
        indices.append(-1 if index is None else int(index))
    return np.asarray(indices, dtype=np.int64)


def _observed_for_context(normalized_values: object, context: LabelContext) -> object:
    values = np.asarray(normalized_values, dtype=np.float32)
    indices = np.asarray(context.component_indices, dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    valid = indices >= 0
    observed[valid] = values[indices[valid]]
    return observed


def _observed_states_for_indices(
    component_indices: object,
    component_context: ComponentContext,
) -> object:
    states = np.full(len(component_indices), "", dtype="<U64")
    parsed = np.asarray(component_indices, dtype=np.int64)
    valid = parsed >= 0
    component_states = np.asarray(component_context.candidate_states, dtype="<U64")
    states[valid] = component_states[parsed[valid]]
    return states


def _context_summary(context: LabelContext) -> dict[str, object]:
    expected = np.asarray(context.expected_values, dtype=np.float32)
    states = [str(value).strip() for value in context.expected_candidate_states]
    state_counts = {}
    for state in states:
        key = state or "(missing)"
        state_counts[key] = int(state_counts.get(key, 0)) + 1
    return {
        "label_count": len(context.labels),
        "mapped_count": int((np.asarray(context.component_indices, dtype=np.int64) >= 0).sum()),
        "missing_count": len(context.missing_rows),
        "numeric_count": int(np.isfinite(expected).sum()),
        "normal_vocab_numeric_count": int(
            (
                np.isfinite(expected)
                & np.asarray([state in NORMAL_VOCAB_STATES for state in states])
            ).sum()
        ),
        "vocab_numeric_count": int(
            (
                np.isfinite(expected)
                & np.asarray([state in VOCAB_PLACEMENT_STATES for state in states])
            ).sum()
        ),
        "expected_state_counts": dict(sorted(state_counts.items())),
        "missing_rows": list(context.missing_rows[:20]),
    }


def _worst_rows(
    context: LabelContext,
    observed_values: object,
    *,
    expected_states: frozenset[str] | None,
    limit: int,
) -> list[dict[str, object]]:
    expected = np.asarray(context.expected_values, dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    states = np.asarray(context.expected_candidate_states, dtype=str)
    rows = []
    for index, label in enumerate(context.labels):
        if expected_states is not None and str(states[index]).strip() not in expected_states:
            continue
        if not np.isfinite(expected[index]) or not np.isfinite(observed[index]):
            continue
        delta = float(observed[index] - expected[index])
        rows.append(
            {
                "label": label,
                "expected": _rounded(float(expected[index])),
                "observed": _rounded(float(observed[index])),
                "absolute_error": _rounded(abs(delta)),
                "direction": "too_high" if delta > 0 else "too_low" if delta < 0 else "match",
                "expected_candidate_state": str(states[index]),
            }
        )
    return sorted(
        rows,
        key=lambda row: float(row.get("absolute_error") or 0.0),
        reverse=True,
    )[:limit]


def _window_examples(
    context: LabelContext,
    expected: object,
    observed: object,
    indices: object,
    *,
    target: float,
    limit: int,
) -> list[dict[str, object]]:
    rows = []
    for index in list(indices)[:limit]:
        parsed = int(index)
        rows.append(
            {
                "label": context.labels[parsed],
                "expected": _rounded(float(expected[parsed])),
                "observed": _rounded(float(observed[parsed])),
                "target_gap": _rounded(abs(float(expected[parsed]) - target)),
            }
        )
    return rows


def _leaderboard(
    candidates: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    key: str,
    limit: int,
) -> list[dict[str, object]]:
    ranked = sorted(
        candidates,
        key=lambda row: _candidate_metric(row, dataset=dataset, key=key),
        reverse=True,
    )[:limit]
    return [_candidate_summary(row, dataset=dataset) for row in ranked]


def _generalization_delta_leaderboard(
    candidates: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    ranked = sorted(
        candidates,
        key=lambda row: (
            _optional_float(
                _mapping(row.get("generalization")).get("score_delta_holdout_minus_calibration")
            )
            or -999.0
        ),
        reverse=True,
    )[:limit]
    return [
        {
            **_candidate_summary(row, dataset="holdout"),
            "calibration_score": _metric_path(row, "calibration", "proficiency_ordering_score"),
            "score_delta": _mapping(row.get("generalization")).get(
                "score_delta_holdout_minus_calibration"
            ),
        }
        for row in ranked
    ]


def _top_candidate(
    candidates: Sequence[Mapping[str, object]],
    *,
    dataset: str,
) -> dict[str, object]:
    if not candidates:
        return {}
    row = max(
        candidates,
        key=lambda candidate: _candidate_metric(
            candidate,
            dataset=dataset,
            key="proficiency_ordering_score",
        ),
    )
    return _candidate_summary(row, dataset=dataset)


def _candidate_summary(row: Mapping[str, object], *, dataset: str) -> dict[str, object]:
    dataset_report = _mapping(row.get(dataset))
    normal_vocab = _mapping(dataset_report.get("normal_vocab"))
    metrics = _mapping(normal_vocab.get("metrics"))
    scores = _mapping(normal_vocab.get("scores"))
    windows = _mapping(dataset_report.get("frontier_windows"))
    lane = _mapping(dataset_report.get("lane"))
    return {
        "candidate_id": row.get("candidate_id"),
        "source": row.get("source"),
        "proficiency_ordering_score": dataset_report.get("proficiency_ordering_score"),
        "normal_vocab_mae": metrics.get("mae"),
        "normal_vocab_bucket": metrics.get("bucket_accuracy"),
        "normal_vocab_pairwise": scores.get("pairwise_order_score"),
        "normal_vocab_spearman": metrics.get("spearman"),
        "window_quality": windows.get("average_window_score"),
        "normal_vocab_f1": lane.get("normal_vocab_f1"),
        "default_accept_accuracy": lane.get("default_accept_accuracy"),
        "original_trace_balanced": _mapping(row.get("original_trace_scores")).get("balanced_score"),
    }


def _candidate_metric(row: Mapping[str, object], *, dataset: str, key: str) -> float:
    dataset_report = _mapping(row.get(dataset))
    if key == "proficiency_ordering_score":
        return _optional_float(dataset_report.get("proficiency_ordering_score")) or -999.0
    if key == "window_quality":
        return _metric_path(dataset_report, "frontier_windows", "average_window_score")
    if key == "normal_vocab_pairwise":
        return _metric_path(dataset_report, "normal_vocab", "scores", "pairwise_order_score")
    return _optional_float(dataset_report.get(key)) or -999.0


def _retained_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    retain_candidates: int,
) -> list[dict[str, object]]:
    selected = []
    seen = set()
    for dataset in ("holdout", "calibration"):
        ranked = sorted(
            candidates,
            key=lambda row: _candidate_metric(
                row,
                dataset=dataset,
                key="proficiency_ordering_score",
            ),
            reverse=True,
        )
        for row in ranked:
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id and candidate_id not in seen:
                selected.append(dict(row))
                seen.add(candidate_id)
            if len(selected) >= retain_candidates:
                return selected
    return selected


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Learner Difficulty Proficiency Ordering Sidecar",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        f"- Evaluated trace variants: `{_escape(inputs.get('evaluated_variant_count'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Holdout labels: `{_escape(inputs.get('holdout_label_count'))}`",
        "",
        "## Method",
        "",
        str(method.get("purpose") or ""),
        "",
        str(method.get("prediction_shape") or ""),
        "",
        str(method.get("selector_proxy") or ""),
        "",
    ]
    lines.extend(_dataset_summary_section(report))
    lines.extend(
        _leaderboard_section(
            report,
            "holdout_proficiency_ordering",
            "Holdout proficiency ordering",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "calibration_proficiency_ordering",
            "Calibration proficiency ordering",
        )
    )
    lines.extend(_leaderboard_section(report, "holdout_window_quality", "Holdout window quality"))
    lines.extend(_primary_candidate_section(report))
    return "\n".join(lines).rstrip() + "\n"


def _dataset_summary_section(report: Mapping[str, object]) -> list[str]:
    summaries = _mapping(report.get("dataset_summaries"))
    lane = _mapping(report.get("lane_diagnostics"))
    lines = ["## Dataset Summary", ""]
    lines.append(
        "| Dataset | Labels | Numeric | Normal numeric | Mapped | Exact lane | "
        "Default lane | Normal F1 |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for name in ("calibration", "holdout"):
        summary = _mapping(summaries.get(name))
        lane_metrics = _mapping(lane.get(name))
        lines.append(
            f"| `{name}` | `{_escape(summary.get('label_count'))}` | "
            f"`{_escape(summary.get('numeric_count'))}` | "
            f"`{_escape(summary.get('normal_vocab_numeric_count'))}` | "
            f"`{_escape(summary.get('mapped_count'))}` | "
            f"`{_escape(lane_metrics.get('exact_state_accuracy'))}` | "
            f"`{_escape(lane_metrics.get('default_accept_accuracy'))}` | "
            f"`{_escape(lane_metrics.get('normal_vocab_f1'))}` |"
        )
    lines.append("")
    return lines


def _leaderboard_section(
    report: Mapping[str, object],
    key: str,
    title: str,
) -> list[str]:
    rows = _mapping_rows(_mapping(report.get("leaderboards")).get(key))
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["No rows.", ""])
        return lines
    lines.append(
        "| Rank | Candidate | Score | MAE | Bucket | Pairwise | Spearman | "
        "Window | Lane F1 | Trace balanced |"
    )
    lines.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('proficiency_ordering_score'))}` | "
            f"`{_escape(row.get('normal_vocab_mae'))}` | "
            f"`{_escape(row.get('normal_vocab_bucket'))}` | "
            f"`{_escape(row.get('normal_vocab_pairwise'))}` | "
            f"`{_escape(row.get('normal_vocab_spearman'))}` | "
            f"`{_escape(row.get('window_quality'))}` | "
            f"`{_escape(row.get('normal_vocab_f1'))}` | "
            f"`{_escape(row.get('original_trace_balanced'))}` |"
        )
    lines.append("")
    return lines


def _primary_candidate_section(report: Mapping[str, object]) -> list[str]:
    primaries = _mapping(report.get("primary_candidates"))
    lines = ["## Primary Candidates", ""]
    lines.append("| Dataset | Candidate | Score | MAE | Pairwise | Window |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for dataset in ("calibration", "holdout"):
        row = _mapping(primaries.get(dataset))
        lines.append(
            f"| `{dataset}` | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('proficiency_ordering_score'))}` | "
            f"`{_escape(row.get('normal_vocab_mae'))}` | "
            f"`{_escape(row.get('normal_vocab_pairwise'))}` | "
            f"`{_escape(row.get('window_quality'))}` |"
        )
    lines.append("")
    return lines


def _trace_variant_records(trace: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [row for row in _mapping_rows(trace.get("variant_records"))]


def _optional_np_array(
    source: object,
    key: str,
    count: int,
    *,
    default: float,
) -> object:
    files = getattr(source, "files", ())
    if key in files:
        return np.asarray(source[key], dtype=np.float32)
    return np.full(count, default, dtype=np.float32)


def _optional_string_array(
    source: object,
    key: str,
    count: int,
    *,
    fallback: object | None = None,
) -> object:
    files = getattr(source, "files", ())
    if key in files:
        return np.asarray(source[key], dtype="<U64")
    if fallback is not None:
        return np.asarray(fallback, dtype="<U64")
    return np.full(count, "", dtype="<U64")


def _masked_sequence(values: Sequence[object], mask: object) -> tuple[str, ...]:
    parsed = np.asarray(mask, dtype=bool)
    return tuple(str(value) for value, keep in zip(values, parsed) if bool(keep))


def _missing_rows(
    labels: Sequence[str],
    component_indices: object,
) -> tuple[Mapping[str, object], ...]:
    indices = np.asarray(component_indices, dtype=np.int64)
    return tuple(
        {"label": label, "row_index": int(index)}
        for index, (label, component_index) in enumerate(zip(labels, indices))
        if int(component_index) < 0
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


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


def _metric_path(value: object, *keys: str) -> float:
    current: object = value
    for key in keys:
        current = _mapping(current).get(key)
    return _optional_float(current) or -999.0


def _weighted_average(values_and_weights: Sequence[tuple[object, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values_and_weights:
        parsed = _optional_float(value)
        if parsed is None or weight <= 0.0:
            continue
        numerator += parsed * weight
        denominator += weight
    if denominator <= 0.0:
        return None
    return numerator / denominator


def _ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0.0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _rounded(value: object) -> float | None:
    parsed = _optional_float(value)
    if parsed is None:
        return None
    return round(parsed, 6)


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _label(lemma: object, reading: object) -> str:
    reading_text = str(reading or "").strip()
    if reading_text:
        return f"{lemma}/{reading_text}"
    return str(lemma or "")


def _parse_float_csv(raw: str) -> tuple[float, ...]:
    values = []
    for part in str(raw or "").split(","):
        text = part.strip()
        if not text:
            continue
        values.append(float(text))
    return tuple(values)


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _repo_or_home_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        home = Path.home()
        try:
            return "~/" + str(path.relative_to(home))
        except ValueError:
            return str(path)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
