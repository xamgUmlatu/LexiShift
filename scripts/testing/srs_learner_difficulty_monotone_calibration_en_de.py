#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_sweep_en_de import (  # noqa: E402
    _candidate_by_id,
    _score_row,
    generate_candidates,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-de"
PRIMARY_STATE = "normal_vocab"
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_REFINED_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_sweep_en_de_refined_latest.json"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_de.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_de.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_monotone_calibration_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_monotone_calibration_en_de_latest.md"
)
CHECKPOINTS = tuple(index / 10.0 for index in range(11))


@dataclass(frozen=True)
class CalibrationProfile:
    profile_id: str
    description: str
    transform: Callable[[float], float]
    learned_from_calibration: bool
    monotone: bool = True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test whether en-de difficulty score distribution problems are mostly "
            "absolute calibration problems. Fits monotone score remaps on calibration "
            "labels and evaluates them on holdout labels; this is a sidecar diagnostic."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_REFINED_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--candidate-id")
    parser.add_argument("--candidate-grid", choices=("refined", "broad"), default="refined")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        signal_rows=_load_jsonl(Path(args.rows_jsonl).expanduser()),
        sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        candidate_id=args.candidate_id,
        candidate_grid=str(args.candidate_grid),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
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
    signal_rows: Sequence[Mapping[str, object]],
    sweep_payload: Mapping[str, object] | None,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    candidate_id: str | None = None,
    candidate_grid: str = "refined",
    generated_at: str | None = None,
) -> dict[str, object]:
    selected_candidate_id = candidate_id or _selected_candidate_id(sweep_payload)
    candidate = _candidate_by_id(generate_candidates(candidate_grid), selected_candidate_id)
    if candidate is None and candidate_grid != "broad":
        candidate = _candidate_by_id(generate_candidates("broad"), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")

    scored_rows = _scored_rows(signal_rows=signal_rows, candidate=candidate)
    scored_by_lemma = {str(row.get("lemma") or "").lower(): row for row in scored_rows}
    calibration_points = _label_points(
        labels=_as_sequence(calibration_payload.get("labels")),
        scored_by_lemma=scored_by_lemma,
    )
    holdout_points = _label_points(
        labels=_as_sequence(holdout_payload.get("labels")),
        scored_by_lemma=scored_by_lemma,
    )
    profiles = _calibration_profiles(calibration_points)
    records = [
        _profile_record(
            profile=profile,
            scored_rows=scored_rows,
            calibration_points=calibration_points,
            holdout_points=holdout_points,
        )
        for profile in profiles
    ]
    identity_record = _record_by_id(records, "identity")
    best_calibration_balanced = max(records, key=_calibration_sort_key)
    best_holdout_balanced = max(records, key=_holdout_sort_key)
    best_calibration_mae = min(
        records, key=lambda record: _mae_sort_key(record, "calibration_primary")
    )
    best_holdout_mae = min(records, key=lambda record: _mae_sort_key(record, "holdout_primary"))
    selected_for_calibration_detail = best_calibration_mae
    selected_profile = _profile_by_id(
        profiles,
        str(selected_for_calibration_detail.get("profile_id")),
    )
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_learner_difficulty_monotone_calibration_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "candidate_id": selected_candidate_id,
            "candidate_grid": candidate_grid,
            "purpose": (
                "Diagnostic bakeoff for monotone post-score remaps. A monotone remap "
                "can repair absolute score calibration and band distribution, but it "
                "cannot introduce new pairwise inversions in the underlying ranking."
            ),
            "profile_policy": (
                "Identity, fixed power curves, affine calibration, isotonic calibration, "
                "and blended isotonic profiles are evaluated. Learned profiles fit only "
                "calibration labels and are judged on holdout labels."
            ),
        },
        "inputs": {
            "signal_row_count": len(scored_rows),
            "calibration_numeric_primary_count": len(calibration_points),
            "holdout_numeric_primary_count": len(holdout_points),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
        },
        "summary": {
            "identity": _compact_record(identity_record),
            "best_calibration_balanced_profile": _compact_record(best_calibration_balanced),
            "best_holdout_balanced_profile": _compact_record(best_holdout_balanced),
            "best_calibration_mae_profile": _compact_record(best_calibration_mae),
            "best_holdout_mae_profile": _compact_record(best_holdout_mae),
            "score_distribution_diagnosis": _distribution_diagnosis(
                identity_record=identity_record,
                selected_record=best_calibration_mae,
            ),
        },
        "profile_records": records,
        "best_calibration_mae_details": {
            "profile_id": selected_for_calibration_detail.get("profile_id"),
            "mapping_checkpoints": _mapping_checkpoints(selected_profile),
            "label_changes": _label_changes(
                profile=selected_profile,
                calibration_points=calibration_points,
                holdout_points=holdout_points,
            ),
        },
        "limitations": [
            "This artifact does not change the production ranking or formula sweep.",
            "Monotone remaps preserve order except for ties introduced by flat isotonic segments.",
            "If holdout improves only weakly or residual directions stay mixed, structural signal fixes are still needed.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    selected = _as_mapping(report.get("best_calibration_mae_details"))
    lines = [
        "# en-de Learner Difficulty Monotone Calibration Bakeoff",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate: `{method.get('candidate_id')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Summary",
        "",
        _record_table(
            [
                ("identity", _as_mapping(summary.get("identity"))),
                (
                    "best calibration balanced",
                    _as_mapping(summary.get("best_calibration_balanced_profile")),
                ),
                (
                    "best holdout balanced",
                    _as_mapping(summary.get("best_holdout_balanced_profile")),
                ),
                (
                    "best calibration MAE",
                    _as_mapping(summary.get("best_calibration_mae_profile")),
                ),
                (
                    "best holdout MAE",
                    _as_mapping(summary.get("best_holdout_mae_profile")),
                ),
            ]
        ),
        "",
        "Distribution diagnosis:",
        "",
    ]
    for item in _as_sequence(summary.get("score_distribution_diagnosis")):
        lines.append(f"- {item}")
    lines.extend(["", "## Profile Bakeoff", ""])
    lines.append(
        "| Profile | Learned | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | "
        "Cal Pairwise | Holdout Pairwise | <0.30 | 0.90-1.00 |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for raw in _as_sequence(report.get("profile_records")):
        record = _as_mapping(raw)
        band_counts = _as_mapping(record.get("score_band_counts"))
        low_count = sum(
            int(band_counts.get(band, 0)) for band in ("0.00-0.10", "0.10-0.20", "0.20-0.30")
        )
        lines.append(
            f"| `{record.get('profile_id')}` | `{record.get('learned_from_calibration')}` | "
            f"{_fmt_metric(record, 'calibration_primary', 'balanced_score')} | "
            f"{_fmt_metric(record, 'holdout_primary', 'balanced_score')} | "
            f"{_fmt_metric(record, 'calibration_primary', 'mae')} | "
            f"{_fmt_metric(record, 'holdout_primary', 'mae')} | "
            f"{_fmt_metric(record, 'calibration_primary', 'pairwise_accuracy')} | "
            f"{_fmt_metric(record, 'holdout_primary', 'pairwise_accuracy')} | "
            f"{low_count} | {int(band_counts.get('0.90-1.00', 0))} |"
        )
    lines.extend(["", "## Best Calibration-MAE Mapping", ""])
    lines.append("| Raw score | Remapped score |")
    lines.append("| ---: | ---: |")
    for raw in _as_sequence(selected.get("mapping_checkpoints")):
        item = _as_mapping(raw)
        lines.append(f"| {_fmt(item.get('raw_score'))} | {_fmt(item.get('mapped_score'))} |")
    lines.extend(["", "## Band Counts", ""])
    selected_record = _record_by_id(
        [_as_mapping(record) for record in _as_sequence(report.get("profile_records"))],
        str(selected.get("profile_id") or ""),
    )
    identity = _as_mapping(summary.get("identity"))
    lines.append("| Band | Identity | Best calibration MAE |")
    lines.append("| --- | ---: | ---: |")
    identity_counts = _as_mapping(identity.get("score_band_counts"))
    selected_counts = _as_mapping(selected_record.get("score_band_counts"))
    for band in _bands():
        lines.append(
            f"| `{band}` | {int(identity_counts.get(band, 0))} | "
            f"{int(selected_counts.get(band, 0))} |"
        )
    lines.extend(["", "## Label Changes For Best Calibration-MAE Profile", ""])
    for split_key, title in (("calibration", "Calibration"), ("holdout", "Holdout")):
        changes = _as_mapping(selected.get("label_changes"))
        split = _as_mapping(changes.get(split_key))
        lines.extend([f"### {title} biggest improvements", ""])
        lines.append(_change_table(_as_sequence(split.get("biggest_improvements"))))
        lines.extend(["", f"### {title} biggest regressions", ""])
        lines.append(_change_table(_as_sequence(split.get("biggest_regressions"))))
        lines.append("")
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _scored_rows(
    *,
    signal_rows: Sequence[Mapping[str, object]],
    candidate: object,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in signal_rows:
        lemma = str(row.get("lemma") or "").strip()
        if not lemma:
            continue
        score = _score_row(candidate, row)
        if score is None:
            continue
        rows.append(
            {
                "lemma": lemma,
                "raw_score": _round_float(score),
                "core_rank": row.get("core_rank"),
                "pos_bucket": row.get("pos_bucket"),
                "translations": list(_as_sequence(row.get("translations")))[:5],
            }
        )
    return rows


def _label_points(
    *,
    labels: Sequence[object],
    scored_by_lemma: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for raw_label in labels:
        label = _as_mapping(raw_label)
        expected = _safe_float(label.get("expected_learner_difficulty"))
        if expected is None:
            continue
        if str(label.get("expected_candidate_state") or "") != PRIMARY_STATE:
            continue
        lemma = str(label.get("lemma") or "").strip()
        row = scored_by_lemma.get(lemma.lower())
        if row is None:
            continue
        points.append(
            {
                "lemma": lemma,
                "expected": _clamp01(expected),
                "raw_score": _safe_float(row.get("raw_score")) or 0.0,
                "expected_band": str(label.get("expected_difficulty_band") or ""),
                "review_flags": list(_as_sequence(label.get("review_flags"))),
                "pos_bucket": row.get("pos_bucket"),
                "translations": list(_as_sequence(row.get("translations")))[:3],
            }
        )
    return points


def _calibration_profiles(points: Sequence[Mapping[str, object]]) -> list[CalibrationProfile]:
    xs = np.asarray(
        [_safe_float(point.get("raw_score")) or 0.0 for point in points], dtype=np.float64
    )
    ys = np.asarray(
        [_safe_float(point.get("expected")) or 0.0 for point in points], dtype=np.float64
    )
    profiles = [
        CalibrationProfile(
            profile_id="identity",
            description="No post-score remap.",
            transform=lambda value: _clamp01(value),
            learned_from_calibration=False,
        )
    ]
    for gamma in (0.55, 0.70, 0.85, 1.15, 1.35, 1.60):
        profiles.append(
            CalibrationProfile(
                profile_id=f"power_g{str(gamma).replace('.', 'p')}",
                description=f"Fixed monotone power curve: score ** {gamma}.",
                transform=lambda value, gamma=gamma: _clamp01((_clamp01(value)) ** gamma),
                learned_from_calibration=False,
            )
        )
    profiles.append(_affine_profile(xs=xs, ys=ys))
    profiles.append(_isotonic_profile(xs=xs, ys=ys, profile_id="isotonic", anchor_weight=0.0))
    anchored = _isotonic_profile(
        xs=xs,
        ys=ys,
        profile_id="isotonic_anchored",
        anchor_weight=1.0,
    )
    profiles.append(anchored)
    for blend in (0.35, 0.50, 0.65):
        profiles.append(
            CalibrationProfile(
                profile_id=f"blend_iso{int(blend * 100):02d}",
                description=(
                    f"Blend raw score with anchored isotonic remap: "
                    f"{1.0 - blend:.2f} * raw + {blend:.2f} * isotonic."
                ),
                transform=lambda value, blend=blend, iso=anchored.transform: _clamp01(
                    (1.0 - blend) * _clamp01(value) + blend * iso(value)
                ),
                learned_from_calibration=True,
            )
        )
    return profiles


def _affine_profile(*, xs: np.ndarray, ys: np.ndarray) -> CalibrationProfile:
    finite = np.isfinite(xs) & np.isfinite(ys)
    if int(finite.sum()) < 2:
        slope = 1.0
        intercept = 0.0
    else:
        slope, intercept = np.polyfit(xs[finite], ys[finite], deg=1)
        slope = max(0.0, float(slope))
        intercept = float(intercept)
    return CalibrationProfile(
        profile_id="affine_fit",
        description=f"Least-squares monotone affine fit: {slope:.4f} * score + {intercept:.4f}.",
        transform=lambda value, slope=slope, intercept=intercept: _clamp01(
            slope * _clamp01(value) + intercept
        ),
        learned_from_calibration=True,
    )


def _isotonic_profile(
    *,
    xs: np.ndarray,
    ys: np.ndarray,
    profile_id: str,
    anchor_weight: float,
) -> CalibrationProfile:
    finite = np.isfinite(xs) & np.isfinite(ys)
    fit_xs = xs[finite]
    fit_ys = ys[finite]
    weights = np.ones(len(fit_xs), dtype=np.float64)
    if anchor_weight > 0.0:
        fit_xs = np.concatenate([np.asarray([0.0, 1.0]), fit_xs])
        fit_ys = np.concatenate([np.asarray([0.0, 1.0]), fit_ys])
        weights = np.concatenate([np.asarray([anchor_weight, anchor_weight]), weights])
    if len(fit_xs) == 0:
        unique_xs = np.asarray([0.0, 1.0], dtype=np.float64)
        unique_ys = np.asarray([0.0, 1.0], dtype=np.float64)
    else:
        order = np.argsort(fit_xs, kind="stable")
        sorted_xs = fit_xs[order]
        sorted_ys = fit_ys[order]
        sorted_weights = weights[order]
        fitted = _pava(sorted_ys, sorted_weights)
        unique_xs, unique_ys = _unique_curve_points(sorted_xs, fitted, sorted_weights)
    description = "Isotonic non-decreasing remap fit on calibration labels."
    if anchor_weight > 0.0:
        description += " Endpoints are lightly anchored at 0->0 and 1->1."
    return CalibrationProfile(
        profile_id=profile_id,
        description=description,
        transform=lambda value, x=unique_xs, y=unique_ys: _clamp01(
            float(np.interp(_clamp01(value), x, y))
        ),
        learned_from_calibration=True,
    )


def _pava(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    blocks: list[dict[str, float | int]] = []
    for index, (value, weight) in enumerate(zip(values, weights, strict=True)):
        block = {
            "start": index,
            "end": index + 1,
            "weight": float(weight),
            "value": float(value),
        }
        blocks.append(block)
        while len(blocks) >= 2 and float(blocks[-2]["value"]) > float(blocks[-1]["value"]):
            right = blocks.pop()
            left = blocks.pop()
            merged_weight = float(left["weight"]) + float(right["weight"])
            merged_value = (
                float(left["value"]) * float(left["weight"])
                + float(right["value"]) * float(right["weight"])
            ) / merged_weight
            blocks.append(
                {
                    "start": int(left["start"]),
                    "end": int(right["end"]),
                    "weight": merged_weight,
                    "value": merged_value,
                }
            )
    fitted = np.empty(len(values), dtype=np.float64)
    for block in blocks:
        fitted[int(block["start"]) : int(block["end"])] = float(block["value"])
    return fitted


def _unique_curve_points(
    xs: np.ndarray,
    ys: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    curve_xs: list[float] = []
    curve_ys: list[float] = []
    index = 0
    while index < len(xs):
        end = index + 1
        while end < len(xs) and xs[end] == xs[index]:
            end += 1
        weight_sum = float(np.sum(weights[index:end]))
        if weight_sum <= 0.0:
            y_value = float(np.mean(ys[index:end]))
        else:
            y_value = float(np.average(ys[index:end], weights=weights[index:end]))
        curve_xs.append(float(xs[index]))
        curve_ys.append(y_value)
        index = end
    if curve_xs[0] > 0.0:
        curve_xs.insert(0, 0.0)
        curve_ys.insert(0, curve_ys[0])
    if curve_xs[-1] < 1.0:
        curve_xs.append(1.0)
        curve_ys.append(curve_ys[-1])
    return np.asarray(curve_xs, dtype=np.float64), np.asarray(curve_ys, dtype=np.float64)


def _profile_record(
    *,
    profile: CalibrationProfile,
    scored_rows: Sequence[Mapping[str, object]],
    calibration_points: Sequence[Mapping[str, object]],
    holdout_points: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "profile_id": profile.profile_id,
        "description": profile.description,
        "learned_from_calibration": profile.learned_from_calibration,
        "monotone": profile.monotone,
        "calibration_primary": _evaluate_points(points=calibration_points, profile=profile),
        "holdout_primary": _evaluate_points(points=holdout_points, profile=profile),
        "score_band_counts": _score_band_counts(scored_rows=scored_rows, profile=profile),
        "mapping_checkpoints": _mapping_checkpoints(profile),
    }


def _evaluate_points(
    *,
    points: Sequence[Mapping[str, object]],
    profile: CalibrationProfile,
) -> dict[str, object]:
    expected_values = []
    observed_values = []
    expected_bands = []
    labels = []
    states = []
    for point in points:
        raw_score = _safe_float(point.get("raw_score")) or 0.0
        expected_values.append(_safe_float(point.get("expected")) or 0.0)
        observed_values.append(profile.transform(raw_score))
        expected_bands.append(str(point.get("expected_band") or ""))
        labels.append(str(point.get("lemma") or ""))
        states.append(PRIMARY_STATE)
    metrics = _difficulty_metrics(
        expected_values=np.asarray(expected_values, dtype=np.float32),
        observed_values=np.asarray(observed_values, dtype=np.float32),
        expected_bands=expected_bands,
        labels=labels,
        expected_candidate_states=np.asarray(states, dtype="<U64"),
        observed_candidate_states=np.asarray(states, dtype="<U64"),
    )
    return {
        "label_count": len(points),
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
    }


def _score_band_counts(
    *,
    scored_rows: Sequence[Mapping[str, object]],
    profile: CalibrationProfile,
) -> dict[str, int]:
    counts = {band: 0 for band in _bands()}
    for row in scored_rows:
        score = profile.transform(_safe_float(row.get("raw_score")) or 0.0)
        counts[_score_band(score)] += 1
    return counts


def _label_changes(
    *,
    profile: CalibrationProfile,
    calibration_points: Sequence[Mapping[str, object]],
    holdout_points: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "calibration": _split_label_changes(points=calibration_points, profile=profile),
        "holdout": _split_label_changes(points=holdout_points, profile=profile),
    }


def _split_label_changes(
    *,
    points: Sequence[Mapping[str, object]],
    profile: CalibrationProfile,
) -> dict[str, object]:
    rows = []
    for point in points:
        raw_score = _safe_float(point.get("raw_score")) or 0.0
        expected = _safe_float(point.get("expected")) or 0.0
        mapped = profile.transform(raw_score)
        raw_error = abs(raw_score - expected)
        mapped_error = abs(mapped - expected)
        rows.append(
            {
                "lemma": point.get("lemma"),
                "expected": _round_float(expected),
                "raw_score": _round_float(raw_score),
                "mapped_score": _round_float(mapped),
                "raw_error": _round_float(raw_error),
                "mapped_error": _round_float(mapped_error),
                "error_delta": _round_float(mapped_error - raw_error),
                "review_flags": list(_as_sequence(point.get("review_flags"))),
                "translations": list(_as_sequence(point.get("translations"))),
            }
        )
    return {
        "biggest_improvements": sorted(
            rows, key=lambda row: _safe_float(row.get("error_delta")) or 0.0
        )[:12],
        "biggest_regressions": sorted(
            rows, key=lambda row: _safe_float(row.get("error_delta")) or 0.0, reverse=True
        )[:12],
    }


def _mapping_checkpoints(profile: CalibrationProfile) -> list[dict[str, float]]:
    return [
        {
            "raw_score": _round_float(value),
            "mapped_score": _round_float(profile.transform(value)),
        }
        for value in CHECKPOINTS
    ]


def _distribution_diagnosis(
    *,
    identity_record: Mapping[str, object],
    selected_record: Mapping[str, object],
) -> list[str]:
    identity_counts = _as_mapping(identity_record.get("score_band_counts"))
    selected_counts = _as_mapping(selected_record.get("score_band_counts"))
    identity_total = sum(int(value) for value in identity_counts.values())
    selected_total = sum(int(value) for value in selected_counts.values())
    identity_tail = int(identity_counts.get("0.90-1.00", 0))
    selected_tail = int(selected_counts.get("0.90-1.00", 0))
    identity_low = sum(
        int(identity_counts.get(band, 0)) for band in ("0.00-0.10", "0.10-0.20", "0.20-0.30")
    )
    selected_low = sum(
        int(selected_counts.get(band, 0)) for band in ("0.00-0.10", "0.10-0.20", "0.20-0.30")
    )
    return [
        (
            "Identity tail share is "
            f"{_percent(identity_tail, identity_total)}; best calibration-MAE tail share is "
            f"{_percent(selected_tail, selected_total)}."
        ),
        (
            "Identity under-0.30 share is "
            f"{_percent(identity_low, identity_total)}; best calibration-MAE under-0.30 share is "
            f"{_percent(selected_low, selected_total)}."
        ),
        (
            "If holdout MAE and bucket accuracy improve while pairwise remains similar, "
            "absolute calibration is doing real work. If not, the odd distribution is mostly "
            "coming from structural scoring errors."
        ),
    ]


def _record_table(rows: Sequence[tuple[str, Mapping[str, object]]]) -> str:
    lines = [
        "| Role | Profile | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | <0.30 | 0.90-1.00 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for role, row in rows:
        band_counts = _as_mapping(row.get("score_band_counts"))
        low_count = sum(
            int(band_counts.get(band, 0)) for band in ("0.00-0.10", "0.10-0.20", "0.20-0.30")
        )
        lines.append(
            f"| {role} | `{row.get('profile_id')}` | "
            f"{_fmt_metric(row, 'calibration_primary', 'balanced_score')} | "
            f"{_fmt_metric(row, 'holdout_primary', 'balanced_score')} | "
            f"{_fmt_metric(row, 'calibration_primary', 'mae')} | "
            f"{_fmt_metric(row, 'holdout_primary', 'mae')} | "
            f"{low_count} | {int(band_counts.get('0.90-1.00', 0))} |"
        )
    return "\n".join(lines)


def _change_table(rows: Sequence[object]) -> str:
    lines = [
        "| Lemma | Expected | Raw | Mapped | Raw Error | Mapped Error | Delta | Flags |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('lemma'))}` | {_fmt(row.get('expected'))} | "
            f"{_fmt(row.get('raw_score'))} | {_fmt(row.get('mapped_score'))} | "
            f"{_fmt(row.get('raw_error'))} | {_fmt(row.get('mapped_error'))} | "
            f"{_fmt_signed(row.get('error_delta'))} | "
            f"{_escape(', '.join(str(item) for item in _as_sequence(row.get('review_flags')))) or '-'} |"
        )
    return "\n".join(lines)


def _selected_candidate_id(sweep_payload: Mapping[str, object] | None) -> str:
    summary = _as_mapping(_as_mapping(sweep_payload).get("summary"))
    for key in (
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
        "best_calibration_candidate",
    ):
        candidate_id = str(_as_mapping(summary.get(key)).get("candidate_id") or "")
        if candidate_id:
            return candidate_id
    return "rw075_rg120_pg100_wg118_wf22_pedmix_modtail_long16_poly04"


def _record_by_id(records: Sequence[Mapping[str, object]], profile_id: str) -> Mapping[str, object]:
    return next((record for record in records if record.get("profile_id") == profile_id), {})


def _profile_by_id(profiles: Sequence[CalibrationProfile], profile_id: str) -> CalibrationProfile:
    return next(profile for profile in profiles if profile.profile_id == profile_id)


def _compact_record(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "profile_id": record.get("profile_id"),
        "description": record.get("description"),
        "learned_from_calibration": record.get("learned_from_calibration"),
        "calibration_primary": _as_mapping(record.get("calibration_primary")),
        "holdout_primary": _as_mapping(record.get("holdout_primary")),
        "score_band_counts": _as_mapping(record.get("score_band_counts")),
    }


def _calibration_sort_key(record: Mapping[str, object]) -> tuple[float, float, float]:
    metrics = _as_mapping(_as_mapping(record.get("calibration_primary")).get("metrics"))
    scores = _as_mapping(_as_mapping(record.get("calibration_primary")).get("scores"))
    return (
        _safe_float(scores.get("balanced_score")) or -1.0,
        -(_safe_float(metrics.get("mae")) or 999.0),
        _safe_float(metrics.get("pairwise_accuracy")) or -1.0,
    )


def _holdout_sort_key(record: Mapping[str, object]) -> tuple[float, float, float]:
    metrics = _as_mapping(_as_mapping(record.get("holdout_primary")).get("metrics"))
    scores = _as_mapping(_as_mapping(record.get("holdout_primary")).get("scores"))
    return (
        _safe_float(scores.get("balanced_score")) or -1.0,
        -(_safe_float(metrics.get("mae")) or 999.0),
        _safe_float(metrics.get("pairwise_accuracy")) or -1.0,
    )


def _mae_sort_key(record: Mapping[str, object], split: str) -> tuple[float, float]:
    payload = _as_mapping(record.get(split))
    metrics = _as_mapping(payload.get("metrics"))
    scores = _as_mapping(payload.get("scores"))
    return (
        _safe_float(metrics.get("mae")) or 999.0,
        -(_safe_float(scores.get("balanced_score")) or -1.0),
    )


def _fmt_metric(record: Mapping[str, object], split: str, key: str) -> str:
    payload = _as_mapping(record.get(split))
    source = _as_mapping(payload.get("scores" if key.endswith("_score") else "metrics"))
    if key in source:
        return _fmt(source.get(key))
    scores = _as_mapping(payload.get("scores"))
    metrics = _as_mapping(payload.get("metrics"))
    return _fmt(scores.get(key) if key in scores else metrics.get(key))


def _score_band(value: float) -> str:
    score = _clamp01(value)
    index = min(9, int(score * 10.0))
    return f"{index / 10.0:.2f}-{(index + 1) / 10.0:.2f}"


def _bands() -> list[str]:
    return [f"{index / 10.0:.2f}-{(index + 1) / 10.0:.2f}" for index in range(10)]


def _load_optional_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return _load_json(path)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if isinstance(row, Mapping):
                rows.append(row)
    return rows


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


def _clamp01(value: object) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return min(1.0, max(0.0, float(numeric)))


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _fmt_signed(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:+.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _percent(count: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{count / total * 100.0:.1f}%"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
