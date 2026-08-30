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
from srs_learner_difficulty_holdout_eval_en_ja import (  # noqa: E402
    DEFAULT_HOLDOUT_JSON_OUT,
    DEFAULT_REVIEW_MARKDOWN,
    ReviewedHoldoutRow,
    holdout_context_from_rows,
    parse_holdout_review_markdown,
)
from srs_learner_difficulty_audit_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
)
from srs_learner_difficulty_normalization import (  # noqa: E402
    DEFAULT_BAND_WIDTH,
    DEFAULT_TARGET_BAND_WEIGHTS,
    difficulty_bands,
    target_band_counts,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _calibration_context,
    _difficulty_band,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    ComponentView,
    family_parts,
    generate_candidates,
    jlpt_bounded_score,
    metrics_for_context,
    raw_scores_for_candidate,
)


PAIR = "en-ja"
DEFAULT_BEFORE_AFTER_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_cross_corpus_typed_rescue_before_after_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_target_curve_bakeoff_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_target_curve_bakeoff_en_ja_latest.md"
)
SELECTED_CANDIDATE_KEYS = (
    ("baseline", "baseline_candidate_id"),
    ("broad_rescue", "broad_candidate_id"),
    ("typed_rescue", "typed_candidate_id"),
)
SCORE_KEYS = (
    "balanced_score",
    "numeric_mae_score",
    "bucket_accuracy_score",
    "pairwise_order_score",
    "rank_correlation_score",
    "beginner_core_score",
    "beginner_broad_score",
    "upper_tail_score",
    "high_tail_score",
    "tail_separation_score",
    "default_decision_score",
)
PROFICIENCY_THRESHOLDS = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
WATCH_ROWS = (
    ("宿る", "やどる"),
    ("糧", "かて"),
    ("亡骸", "なきがら"),
    ("黒潮", "くろしお"),
    ("埋め立て", "うめたて"),
    ("喜び", "よろこび"),
    ("破る", "やぶる"),
    ("霧", "きり"),
    ("騒ぎ", "さわぎ"),
    ("卵焼き", "たまごやき"),
    ("黒蟻", "くろあり"),
)


@dataclass(frozen=True)
class CurveVariant:
    curve_id: str
    description: str
    weights: tuple[float, ...]
    positions: object
    kind: str = "band_weights"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bake off alternate target-curve distributions against fixed en-ja "
            "source-arbitration candidates."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON_OUT)
    parser.add_argument("--before-after-json", type=Path, default=DEFAULT_BEFORE_AFTER_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--candidate-family",
        default="cross_corpus_typed_rescue_refine",
        help="Candidate family containing the saved baseline/broad/typed candidate IDs.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        calibration_json=_resolve_path(args.calibration_json),
        review_markdown=_resolve_path(args.review_markdown),
        holdout_json=_resolve_path(args.holdout_json),
        before_after_json=_resolve_path(args.before_after_json),
        candidate_family=str(args.candidate_family),
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
    calibration_matrix_path: Path,
    calibration_json: Path,
    review_markdown: Path,
    holdout_json: Path,
    before_after_json: Path,
    candidate_family: str,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    view = ComponentView.from_npz(component)
    calibration_context = _refresh_context_expected_from_label_json(
        _calibration_context(calibration, component),
        calibration_json,
    )
    holdout_rows = _load_holdout_rows(holdout_json, fallback_markdown=review_markdown)
    holdout_context = holdout_context_from_rows(holdout_rows, component)
    parts = family_parts(view)
    candidates = generate_candidates(candidate_family=candidate_family)
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    selected_candidate_ids = _selected_candidate_ids(before_after_json)
    missing = [
        candidate_id
        for _, candidate_id in selected_candidate_ids
        if candidate_id not in candidate_by_id
    ]
    if missing:
        raise ValueError(
            "Saved candidate IDs are not present in the generated family: " + ", ".join(missing)
        )
    curve_variants = _curve_variants(
        total_count=len(view.frequency),
        current_positions=view.target_positions,
    )
    expected_by_key = _expected_lookup(
        calibration_context=calibration_context,
        holdout_context=holdout_context,
    )
    index_by_key = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings))
    }
    rows: list[dict[str, object]] = []
    watch_rows: list[dict[str, object]] = []
    threshold_rows: list[dict[str, object]] = []
    for candidate_label, candidate_id in selected_candidate_ids:
        candidate = candidate_by_id[candidate_id]
        raw = raw_scores_for_candidate(candidate, view, parts=parts)
        previous_pairwise: float | None = None
        for curve in curve_variants:
            normalized = _target_curve_normalize(raw, target_positions=curve.positions)
            normalized = jlpt_bounded_score(candidate, normalized, parts=parts)
            calibration_metrics = metrics_for_context(normalized, calibration_context)
            holdout_metrics = metrics_for_context(normalized, holdout_context)
            holdout_scores = _score_subset(holdout_metrics["scores"])
            calibration_scores = _score_subset(calibration_metrics["scores"])
            pairwise = _optional_float(holdout_scores.get("pairwise_order_score"))
            pairwise_delta = (
                _rounded(pairwise - previous_pairwise)
                if pairwise is not None and previous_pairwise is not None
                else None
            )
            if pairwise is not None and previous_pairwise is None:
                previous_pairwise = pairwise
            rows.append(
                {
                    "candidate_label": candidate_label,
                    "candidate_id": candidate_id,
                    "curve_id": curve.curve_id,
                    "calibration_scores": calibration_scores,
                    "calibration_metrics": _summary_metrics(calibration_metrics),
                    "holdout_scores": holdout_scores,
                    "holdout_metrics": _summary_metrics(holdout_metrics),
                    "generalization_delta": _rounded(
                        (_optional_float(holdout_scores.get("balanced_score")) or 0.0)
                        - (_optional_float(calibration_scores.get("balanced_score")) or 0.0)
                    ),
                    "holdout_pairwise_delta_vs_first_curve": pairwise_delta,
                }
            )
            threshold_rows.append(
                _threshold_counts(
                    normalized,
                    candidate_label=candidate_label,
                    curve_id=curve.curve_id,
                )
            )
            if candidate_label == "typed_rescue":
                watch_rows.extend(
                    _watch_rows(
                        normalized,
                        curve_id=curve.curve_id,
                        expected_by_key=expected_by_key,
                        index_by_key=index_by_key,
                    )
                )
    best_by_candidate = {
        label: _best_row(
            [row for row in rows if str(row.get("candidate_label") or "") == label],
            score_key="balanced_score",
        )
        for label, _ in selected_candidate_ids
    }
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Controlled sidecar bakeoff of target-score distributions with "
                "candidate formulas frozen."
            ),
            "mathematical_constraint": (
                "For a fixed candidate, target-curve remapping is monotone: it "
                "can alter numeric calibration, bucket membership, and proficiency "
                "threshold counts, but it cannot repair pairwise order mistakes."
            ),
            "candidate_family": candidate_family,
            "selected_candidates": [
                {"label": label, "candidate_id": candidate_id}
                for label, candidate_id in selected_candidate_ids
            ],
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "calibration_json": _repo_or_home_path(calibration_json),
            "review_markdown": _repo_or_home_path(review_markdown),
            "holdout_json": _repo_or_home_path(holdout_json),
            "before_after_json": _repo_or_home_path(before_after_json),
            "component_count": int(len(view.frequency)),
            "generated_candidate_count": int(len(candidates)),
        },
        "curves": [
            {
                "curve_id": curve.curve_id,
                "kind": curve.kind,
                "description": curve.description,
                "band_width": DEFAULT_BAND_WIDTH,
                "weights": [_rounded(value) for value in curve.weights],
                "half_band_distribution": _band_distribution(curve.positions, width=0.05),
                "decile_distribution": _band_distribution(curve.positions, width=0.10),
                "shape_diagnostics": _shape_diagnostics(curve.positions),
            }
            for curve in curve_variants
        ],
        "results": rows,
        "best_by_candidate": best_by_candidate,
        "typed_watch_rows": watch_rows,
        "threshold_counts": threshold_rows,
        "summary": {
            "best_overall_holdout_balanced": _best_row(rows, score_key="balanced_score"),
            "best_by_candidate": best_by_candidate,
            "pairwise_invariance_note": (
                "Pairwise scores should remain effectively unchanged within each "
                "candidate unless a post-normalization bound creates order changes."
            ),
        },
        "artifact_provenance": build_artifact_provenance(
            producer_script=SCRIPT_DIR / "srs_learner_difficulty_target_curve_bakeoff_en_ja.py",
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "calibration_json": calibration_json,
                "review_markdown": review_markdown,
                "holdout_json": holdout_json,
                "before_after_json": before_after_json,
            },
            code_paths={
                "target_curve_bakeoff": SCRIPT_DIR
                / "srs_learner_difficulty_target_curve_bakeoff_en_ja.py",
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def _selected_candidate_ids(before_after_json: Path) -> list[tuple[str, str]]:
    if not before_after_json.exists():
        raise FileNotFoundError(f"Before/after artifact not found: {before_after_json}")
    data = json.loads(before_after_json.read_text(encoding="utf-8"))
    summary = _mapping(data.get("summary"))
    rows: list[tuple[str, str]] = []
    for label, key in SELECTED_CANDIDATE_KEYS:
        candidate_id = str(summary.get(key) or "")
        if not candidate_id:
            raise ValueError(f"Missing {key} in {before_after_json}")
        rows.append((label, candidate_id))
    return rows


def _load_holdout_rows(
    holdout_json: Path,
    *,
    fallback_markdown: Path,
) -> list[ReviewedHoldoutRow]:
    if holdout_json.exists():
        payload = json.loads(holdout_json.read_text(encoding="utf-8"))
        rows: list[ReviewedHoldoutRow] = []
        for label in payload.get("labels") or []:
            if not isinstance(label, Mapping):
                continue
            expected = _optional_float(label.get("expected_learner_difficulty"))
            if expected is None:
                continue
            rows.append(
                ReviewedHoldoutRow(
                    lemma=str(label.get("lemma") or ""),
                    reading=str(label.get("expected_reading") or ""),
                    expected_difficulty=expected,
                    treatment=str(label.get("treatment") or ""),
                    notes=str(label.get("rationale") or label.get("notes") or ""),
                )
            )
        if rows:
            return rows
    return parse_holdout_review_markdown(fallback_markdown)


def _refresh_context_expected_from_label_json(
    context: Mapping[str, object],
    label_json: Path,
) -> dict[str, object]:
    refreshed = dict(context)
    if not label_json.exists():
        return refreshed
    payload = json.loads(label_json.read_text(encoding="utf-8"))
    overrides: dict[tuple[str, str], float] = {}
    lemma_overrides: dict[str, float] = {}
    for label in payload.get("labels") or []:
        if not isinstance(label, Mapping):
            continue
        expected = _optional_float(label.get("expected_learner_difficulty"))
        if expected is None:
            continue
        lemma = str(label.get("lemma") or "")
        reading = str(label.get("expected_reading") or "")
        if reading:
            overrides[(lemma, reading)] = expected
        else:
            lemma_overrides[lemma] = expected

    expected_values = np.asarray(context["expected_values"], dtype=np.float32).copy()
    expected_bands = list(context["expected_bands"])
    for index, label in enumerate(str(value) for value in context["labels"]):
        lemma, reading = _split_label(label)
        expected = overrides.get((lemma, reading), lemma_overrides.get(lemma))
        if expected is None:
            continue
        expected_values[index] = float(expected)
        expected_bands[index] = _difficulty_band(float(expected))
    refreshed["expected_values"] = expected_values
    refreshed["expected_bands"] = expected_bands
    return refreshed


def _curve_variants(*, total_count: int, current_positions: object) -> list[CurveVariant]:
    specs = [
        (
            "current_v1",
            "Current checked-in target curve; 0.90-1.00 is intentionally tiny.",
            DEFAULT_TARGET_BAND_WEIGHTS,
            np.asarray(current_positions, dtype=np.float32),
            "current",
        ),
        (
            "tail05",
            "Smooth curve with about 5% of the population in 0.90-1.00.",
            _half_band_weights(
                (0.005, 0.018, 0.034, 0.064, 0.100, 0.140, 0.180, 0.210, 0.199, 0.050)
            ),
            None,
            "manual_band_weights",
        ),
        (
            "tail08",
            "Smooth curve with about 8% of the population in 0.90-1.00.",
            _half_band_weights(
                (0.004, 0.016, 0.030, 0.055, 0.090, 0.130, 0.170, 0.200, 0.225, 0.080)
            ),
            None,
            "manual_band_weights",
        ),
        (
            "tail12",
            "Smooth curve with about 12% of the population in 0.90-1.00.",
            _half_band_weights(
                (0.003, 0.012, 0.025, 0.045, 0.075, 0.115, 0.155, 0.185, 0.265, 0.120)
            ),
            None,
            "manual_band_weights",
        ),
        (
            "tail18",
            "Aggressive curve with about 18% of the population in 0.90-1.00.",
            _half_band_weights(
                (0.002, 0.008, 0.018, 0.035, 0.060, 0.095, 0.135, 0.165, 0.302, 0.180)
            ),
            None,
            "manual_band_weights",
        ),
        (
            "uniform_deciles",
            "Control curve: each 0.10 proficiency decile has about the same count.",
            _half_band_weights((0.100,) * 10),
            None,
            "manual_band_weights",
        ),
    ]
    variants: list[CurveVariant] = []
    for curve_id, description, weights, positions, kind in specs:
        curve_positions = (
            np.asarray(positions, dtype=np.float32)
            if positions is not None
            else _target_positions(total_count=total_count, weights=weights)
        )
        variants.append(
            CurveVariant(
                curve_id=curve_id,
                description=description,
                weights=tuple(float(value) for value in weights),
                positions=curve_positions,
                kind=kind,
            )
        )
    variants.extend(_smooth_warp_variants(current_positions=np.asarray(current_positions)))
    return variants


def _smooth_warp_variants(*, current_positions: object) -> list[CurveVariant]:
    positions = np.asarray(current_positions, dtype=np.float32)
    variants: list[CurveVariant] = []
    for pivot in (0.0, 0.4, 0.5, 0.6, 0.7):
        for gamma in (1.12, 1.16, 1.20, 1.25, 1.30, 1.40, 1.55):
            warped = _warp_upper_tail_positions(positions, pivot=pivot, gamma=gamma)
            tail_fraction = float((warped >= 0.90).sum()) / float(len(warped))
            if tail_fraction < 0.05 or tail_fraction > 0.13:
                continue
            curve_id = f"warp_p{int(round(pivot * 100)):02d}_g{int(round(gamma * 100)):03d}"
            variants.append(
                CurveVariant(
                    curve_id=curve_id,
                    description=(
                        "Smooth monotone warp of current_v1: scores below "
                        f"{pivot:.2f} are preserved, upper-tail complement is "
                        f"raised with gamma={gamma:.2f}."
                    ),
                    weights=(),
                    positions=warped,
                    kind="smooth_warp",
                )
            )
    return variants


def _warp_upper_tail_positions(values: object, *, pivot: float, gamma: float) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    if pivot <= 0.0:
        return (1.0 - np.power(1.0 - parsed, gamma)).astype(np.float32)
    warped = parsed.copy()
    mask = warped > float(pivot)
    scaled = (warped[mask] - float(pivot)) / (1.0 - float(pivot))
    warped[mask] = float(pivot) + ((1.0 - float(pivot)) * (1.0 - np.power(1.0 - scaled, gamma)))
    return np.clip(warped, 0.0, 1.0).astype(np.float32)


def _half_band_weights(decile_shares: Sequence[float]) -> tuple[float, ...]:
    if len(decile_shares) != 10:
        raise ValueError("Expected 10 decile shares.")
    weights: list[float] = []
    for decile_index, share in enumerate(decile_shares):
        lower_half_share = 0.45 if decile_index < 8 else 0.70
        weights.append(float(share) * lower_half_share)
        weights.append(float(share) * (1.0 - lower_half_share))
    return tuple(weights)


def _target_positions(*, total_count: int, weights: Sequence[float]) -> object:
    bands = difficulty_bands(DEFAULT_BAND_WIDTH)
    if len(weights) != len(bands):
        raise ValueError(f"Expected {len(bands)} weights, got {len(weights)}.")
    counts = target_band_counts(total_count, weights)
    positions = np.empty(total_count, dtype=np.float32)
    cursor = 0
    for band, count in zip(bands, counts):
        if count <= 0:
            continue
        offsets = np.arange(count, dtype=np.float32)
        positions[cursor : cursor + count] = band.start + (
            ((offsets + 0.5) / count) * (band.end - band.start)
        )
        cursor += count
    return positions


def _band_distribution(values: object, *, width: float) -> list[dict[str, object]]:
    parsed = np.asarray(values, dtype=np.float32)
    total = int(len(parsed))
    rows = []
    for band in difficulty_bands(width):
        if band.end >= 1.0:
            mask = (parsed >= band.start) & (parsed <= band.end)
        else:
            mask = (parsed >= band.start) & (parsed < band.end)
        count = int(mask.sum())
        rows.append(
            {
                "band": band.label,
                "count": count,
                "percent": _rounded(count / total) if total else None,
            }
        )
    return rows


def _shape_diagnostics(values: object) -> dict[str, object]:
    half_counts = [int(row["count"]) for row in _band_distribution(values, width=0.05)]
    adjacent_ratios = [
        max(left, right) / max(1, min(left, right))
        for left, right in zip(half_counts, half_counts[1:])
    ]
    second_diffs = [
        abs(half_counts[index + 1] - (2 * half_counts[index]) + half_counts[index - 1])
        for index in range(1, len(half_counts) - 1)
    ]
    return {
        "max_adjacent_half_band_ratio": _rounded(max(adjacent_ratios)) if adjacent_ratios else None,
        "mean_second_difference": _rounded(float(np.mean(second_diffs))) if second_diffs else None,
        "tail_half_counts_0_80_to_1_00": half_counts[16:20],
    }


def _score_subset(scores: object) -> dict[str, object]:
    mapped = _mapping(scores)
    return {key: mapped.get(key) for key in SCORE_KEYS}


def _threshold_counts(
    normalized: object,
    *,
    candidate_label: str,
    curve_id: str,
) -> dict[str, object]:
    values = np.asarray(normalized, dtype=np.float32)
    total = int(len(values))
    counts = {}
    for threshold in PROFICIENCY_THRESHOLDS:
        count = int((values >= threshold).sum())
        counts[f"at_or_above_{threshold:.2f}"] = {
            "count": count,
            "percent": _rounded(count / total) if total else None,
        }
    return {
        "candidate_label": candidate_label,
        "curve_id": curve_id,
        "thresholds": counts,
    }


def _expected_lookup(
    *,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for source, context in (
        ("calibration", calibration_context),
        ("holdout", holdout_context),
    ):
        labels = [str(label) for label in context["labels"]]
        expected = np.asarray(context["expected_values"], dtype=np.float32)
        for label, value in zip(labels, expected):
            lemma, reading = _split_label(label)
            lookup[(lemma, reading)] = {
                "source": source,
                "expected": _rounded(float(value)) if np.isfinite(value) else None,
            }
    return lookup


def _split_label(label: str) -> tuple[str, str]:
    if "/" not in label:
        return label, ""
    lemma, reading = label.rsplit("/", 1)
    return lemma, reading


def _watch_rows(
    normalized: object,
    *,
    curve_id: str,
    expected_by_key: Mapping[tuple[str, str], Mapping[str, object]],
    index_by_key: Mapping[tuple[str, str], int],
) -> list[dict[str, object]]:
    values = np.asarray(normalized, dtype=np.float32)
    rows = []
    for lemma, reading in WATCH_ROWS:
        index = index_by_key.get((lemma, reading))
        expected = _mapping(expected_by_key.get((lemma, reading), {}))
        rows.append(
            {
                "curve_id": curve_id,
                "lemma": lemma,
                "reading": reading,
                "expected": expected.get("expected"),
                "expected_source": expected.get("source"),
                "score": _rounded(float(values[index])) if index is not None else None,
                "component_index": index,
            }
        )
    return rows


def _best_row(rows: Sequence[Mapping[str, object]], *, score_key: str) -> dict[str, object]:
    sortable = [
        row
        for row in rows
        if _optional_float(_mapping(row.get("holdout_scores")).get(score_key)) is not None
    ]
    if not sortable:
        return {}
    best = max(
        sortable,
        key=lambda row: float(_mapping(row.get("holdout_scores")).get(score_key) or -1.0),
    )
    return {
        "candidate_label": best.get("candidate_label"),
        "candidate_id": best.get("candidate_id"),
        "curve_id": best.get("curve_id"),
        "calibration_scores": _mapping(best.get("calibration_scores")),
        "holdout_scores": _mapping(best.get("holdout_scores")),
        "generalization_delta": best.get("generalization_delta"),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Target-Curve Bakeoff",
        "",
        "Status: generated sidecar experiment",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Method",
        "",
        _escape(_mapping(report.get("method")).get("mathematical_constraint")),
        "",
        "This freezes the candidate formulas and changes only the global rank-to-score target curve.",
        "",
        "## Inputs",
        "",
        f"- Component matrix: `{_escape(inputs.get('component_matrix'))}`",
        f"- Calibration matrix: `{_escape(inputs.get('calibration_matrix'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_json'))}`",
        f"- Holdout review: `{_escape(inputs.get('review_markdown'))}`",
        f"- Holdout labels: `{_escape(inputs.get('holdout_json'))}`",
        f"- Before/after anchor: `{_escape(inputs.get('before_after_json'))}`",
        f"- Component count: `{_escape(inputs.get('component_count'))}`",
        f"- Generated candidate count: `{_escape(inputs.get('generated_candidate_count'))}`",
        "",
        "## Curve Populations",
        "",
        "| Curve | Kind | 0.80-0.90 | 0.90-1.00 | >=0.90 words | >=0.95 words | Tail half-bands | Max adjacent ratio |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for curve in _sequence_dicts(report.get("curves")):
        deciles = {
            str(row.get("band")): row for row in _sequence_dicts(curve.get("decile_distribution"))
        }
        half = {
            str(row.get("band")): row
            for row in _sequence_dicts(curve.get("half_band_distribution"))
        }
        shape = _mapping(curve.get("shape_diagnostics"))
        tail90 = _mapping(deciles.get("0.90-1.00"))
        tail80 = _mapping(deciles.get("0.80-0.90"))
        tail95 = _mapping(half.get("0.95-1.00"))
        lines.append(
            f"| `{_escape(curve.get('curve_id'))}` | "
            f"{_escape(curve.get('kind'))} | "
            f"{_count_percent(tail80)} | {_count_percent(tail90)} | "
            f"{_escape(tail90.get('count'))} | {_escape(tail95.get('count'))} | "
            f"`{_escape(shape.get('tail_half_counts_0_80_to_1_00'))}` | "
            f"{_escape(shape.get('max_adjacent_half_band_ratio'))} |"
        )
    lines.extend(
        [
            "",
            "## Fixed-Candidate Results",
            "",
            "| Candidate | Curve | Calibration balanced | Holdout balanced | Holdout MAE score | Holdout bucket | Holdout pairwise |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _sequence_dicts(report.get("results")):
        calibration = _mapping(row.get("calibration_scores"))
        holdout = _mapping(row.get("holdout_scores"))
        lines.append(
            f"| `{_escape(row.get('candidate_label'))}` | `{_escape(row.get('curve_id'))}` | "
            f"{_escape(calibration.get('balanced_score'))} | "
            f"{_escape(holdout.get('balanced_score'))} | "
            f"{_escape(holdout.get('numeric_mae_score'))} | "
            f"{_escape(holdout.get('bucket_accuracy_score'))} | "
            f"{_escape(holdout.get('pairwise_order_score'))} |"
        )
    lines.extend(
        [
            "",
            "## Best Holdout By Candidate",
            "",
            "| Candidate | Best curve | Holdout balanced | Holdout MAE score | Holdout bucket |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for candidate_label, row in _mapping(summary.get("best_by_candidate")).items():
        mapped = _mapping(row)
        holdout = _mapping(mapped.get("holdout_scores"))
        lines.append(
            f"| `{_escape(candidate_label)}` | `{_escape(mapped.get('curve_id'))}` | "
            f"{_escape(holdout.get('balanced_score'))} | "
            f"{_escape(holdout.get('numeric_mae_score'))} | "
            f"{_escape(holdout.get('bucket_accuracy_score'))} |"
        )
    watch_curve_ids = _watch_curve_ids(report)
    lines.extend(
        [
            "",
            "## Typed Rescue Watch Rows",
            "",
            "| Word | Expected | "
            + " | ".join(f"`{_escape(curve_id)}`" for curve_id in watch_curve_ids)
            + " |",
            "| --- | ---: | " + " | ".join("---:" for _ in watch_curve_ids) + " |",
        ]
    )
    lines.extend(_watch_markdown(report.get("typed_watch_rows"), curve_ids=watch_curve_ids))
    lines.extend(
        [
            "",
            "## Typed Rescue Threshold Counts",
            "",
            "| Curve | >=0.80 | >=0.90 | >=0.95 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in _sequence_dicts(report.get("threshold_counts")):
        if row.get("candidate_label") != "typed_rescue":
            continue
        thresholds = _mapping(row.get("thresholds"))
        lines.append(
            f"| `{_escape(row.get('curve_id'))}` | "
            f"{_threshold_count(thresholds, 'at_or_above_0.80')} | "
            f"{_threshold_count(thresholds, 'at_or_above_0.90')} | "
            f"{_threshold_count(thresholds, 'at_or_above_0.95')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _watch_curve_ids(report: Mapping[str, object]) -> list[str]:
    ids = ["current_v1", "tail08"]
    curves = {
        str(curve.get("curve_id") or ""): _mapping(curve)
        for curve in _sequence_dicts(report.get("curves"))
    }
    typed_rows = [
        row
        for row in _sequence_dicts(report.get("results"))
        if row.get("candidate_label") == "typed_rescue"
    ]
    top_smooth = [
        str(row.get("curve_id") or "")
        for row in sorted(
            [
                row
                for row in typed_rows
                if _mapping(curves.get(str(row.get("curve_id") or ""))).get("kind") == "smooth_warp"
            ],
            key=lambda row: float(
                _mapping(row.get("holdout_scores")).get("balanced_score") or -1.0
            ),
            reverse=True,
        )[:3]
    ]
    ids.extend(top_smooth)
    for curve_id in ("warp_p60_g140", "warp_p70_g155"):
        if curve_id in curves:
            ids.append(curve_id)
    return [curve_id for curve_id in dict.fromkeys(ids) if curve_id in curves]


def _watch_markdown(value: object, *, curve_ids: Sequence[str]) -> list[str]:
    by_word: dict[tuple[str, str], dict[str, object]] = {}
    for row in _sequence_dicts(value):
        key = (str(row.get("lemma") or ""), str(row.get("reading") or ""))
        entry = by_word.setdefault(
            key,
            {
                "expected": row.get("expected"),
                "scores": {},
            },
        )
        _mapping(entry["scores"])[str(row.get("curve_id") or "")] = row.get("score")
    lines = []
    for (lemma, reading), row in by_word.items():
        scores = _mapping(row.get("scores"))
        lines.append(
            f"| {_escape(lemma)}/{_escape(reading)} | {_escape(row.get('expected'))} | "
            + " | ".join(_escape(scores.get(curve_id)) for curve_id in curve_ids)
            + " |"
        )
    return lines


def _threshold_count(thresholds: Mapping[str, object], key: str) -> str:
    row = _mapping(thresholds.get(key))
    return f"{_escape(row.get('count'))} ({_escape(row.get('percent'))})"


def _count_percent(row: Mapping[str, object]) -> str:
    return f"{_escape(row.get('count'))} ({_escape(row.get('percent'))})"


def _sequence_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
