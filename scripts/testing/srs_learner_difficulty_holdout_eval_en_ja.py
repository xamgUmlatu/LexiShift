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
from srs_learner_difficulty_model_family_meta_search_en_ja import (  # noqa: E402
    _expert_from_json,
    _load_json,
    _mapping,
    _mapping_rows,
    _meta_from_row,
    _model_candidate_from_row,
    _raw_for_meta_candidate,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _split_context,
    _utc_now,
)
from srs_learner_difficulty_model_family_search_en_ja import (  # noqa: E402
    ModelCandidate,
    _candidate_raw_scores,
    _signal_arrays,
)
from srs_learner_difficulty_band_expert_stitch_en_ja import (  # noqa: E402
    _best_trace_variant_id,
    _component_context,
    _variant_from_record,
    _variant_records_by_id,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _calibration_context,
    _difficulty_band,
    _difficulty_metrics,
    _raw_scores_for_expert,
    _sequence_values,
    _summary_metrics,
    _target_curve_normalize,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
    _target_curve_raw_scores_for_variant,
)


PAIR = "en-ja"
DEFAULT_REVIEW_MARKDOWN = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_holdout_review_en_ja.md"
)
DEFAULT_HOLDOUT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_component_matrix_latest.npz"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_calibration_matrix_latest.npz"
)
DEFAULT_TRACE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_trace_latest.json"
)
DEFAULT_FAMILY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_search_en_ja_latest.json"
)
DEFAULT_META_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_meta_search_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_holdout_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_holdout_eval_en_ja_latest.md"
)


@dataclass(frozen=True)
class ReviewedHoldoutRow:
    lemma: str
    reading: str
    expected_difficulty: float | None
    treatment: str
    notes: str

    @property
    def label(self) -> str:
        return f"{self.lemma}/{self.reading}" if self.reading else self.lemma


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate latest en-ja learner-difficulty contenders against the "
            "reviewed fresh holdout set without running a new sweep."
        )
    )
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--holdout-json-out", type=Path, default=DEFAULT_HOLDOUT_JSON_OUT)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--trace-candidate-limit", type=int, default=400)
    parser.add_argument("--trace-top-per-score", type=int, default=40)
    parser.add_argument("--family-json", type=Path, default=DEFAULT_FAMILY_JSON)
    parser.add_argument("--meta-json", type=Path, default=DEFAULT_META_JSON)
    parser.add_argument(
        "--skip-family",
        action="store_true",
        help="Evaluate trace candidates only; useful for provenance-isolated reference runs.",
    )
    parser.add_argument(
        "--skip-meta",
        action="store_true",
        help="Do not evaluate meta-search candidates.",
    )
    parser.add_argument("--family-candidate-limit", type=int, default=200)
    parser.add_argument("--family-top-per-leaderboard", type=int, default=20)
    parser.add_argument("--meta-candidate-limit", type=int, default=120)
    parser.add_argument("--meta-top-per-leaderboard", type=int, default=20)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        review_markdown=_resolve_path(args.review_markdown),
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        trace_json_path=_resolve_path(args.trace_json),
        family_json_path=None if args.skip_family else _resolve_path(args.family_json),
        meta_json_path=None if args.skip_meta else _resolve_path(args.meta_json),
        trace_candidate_limit=max(1, int(args.trace_candidate_limit)),
        trace_top_per_score=max(1, int(args.trace_top_per_score)),
        family_candidate_limit=max(1, int(args.family_candidate_limit)),
        family_top_per_leaderboard=max(1, int(args.family_top_per_leaderboard)),
        meta_candidate_limit=max(1, int(args.meta_candidate_limit)),
        meta_top_per_leaderboard=max(1, int(args.meta_top_per_leaderboard)),
        detail_limit=max(1, int(args.detail_limit)),
    )
    holdout_json_out = _resolve_path(args.holdout_json_out)
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    holdout_json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    holdout_json_out.write_text(
        json.dumps(report["holdout_input"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote holdout JSON input to {holdout_json_out}")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    review_markdown: Path,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    trace_json_path: Path,
    family_json_path: Path | None,
    meta_json_path: Path | None,
    trace_candidate_limit: int = 400,
    trace_top_per_score: int = 40,
    family_candidate_limit: int = 200,
    family_top_per_leaderboard: int = 20,
    meta_candidate_limit: int = 120,
    meta_top_per_leaderboard: int = 20,
    detail_limit: int = 20,
) -> dict[str, object]:
    holdout_rows = parse_holdout_review_markdown(review_markdown)
    holdout_input = holdout_json_payload(holdout_rows, review_markdown=review_markdown)
    component = np.load(component_matrix_path)
    calibration_matrix = np.load(calibration_matrix_path)
    trace_report = _load_json(trace_json_path)
    family_report = _load_json(family_json_path) if family_json_path is not None else {}
    meta_report = _load_json(meta_json_path) if meta_json_path is not None else {}
    calibration_context = _calibration_context(calibration_matrix, component)
    holdout_context = holdout_context_from_rows(holdout_rows, component)
    trace_records = _variant_records_by_id(trace_report, calibration_matrix)
    trace_rows = _select_trace_rows(
        trace_records,
        trace_report=trace_report,
        limit=trace_candidate_limit,
        top_per_score=trace_top_per_score,
    )
    trace_variant_index = {
        str(value): index for index, value in enumerate(calibration_matrix["variant_ids"])
    }
    trace_calibration_values = np.asarray(calibration_matrix["observed_values"], dtype=np.float32)
    experts = [_expert_from_json(row) for row in _mapping_rows(family_report.get("expert_pool"))]
    raw_by_expert = {
        expert.variant_id: _raw_scores_for_expert(expert, component) for expert in experts
    }
    signal_arrays = _signal_arrays(component)
    family_candidates = (
        _select_family_candidates(
            family_report,
            limit=family_candidate_limit,
            top_per_leaderboard=family_top_per_leaderboard,
        )
        if family_report
        else []
    )
    meta_rows = (
        _select_meta_rows(
            meta_report,
            limit=meta_candidate_limit,
            top_per_leaderboard=meta_top_per_leaderboard,
        )
        if meta_report
        else []
    )
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    trace_results = evaluate_trace_candidates(
        trace_rows,
        component=component,
        target_positions=target_positions,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        trace_calibration_values=trace_calibration_values,
        trace_variant_index=trace_variant_index,
        detail_limit=detail_limit,
    )
    family_results = evaluate_family_candidates(
        family_candidates,
        component=component,
        target_positions=target_positions,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        raw_by_expert=raw_by_expert,
        signal_arrays=signal_arrays,
        detail_limit=detail_limit,
    )
    meta_results = (
        evaluate_meta_candidates(
            meta_rows,
            family_report=family_report,
            component=component,
            target_positions=target_positions,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
            detail_limit=detail_limit,
        )
        if meta_rows and family_report
        else []
    )
    all_results = sorted(
        [*trace_results, *family_results, *meta_results],
        key=lambda row: _score(row, "holdout", "balanced_score"),
        reverse=True,
    )
    primary_candidate_id = _best_trace_variant_id(trace_records)
    primary = next(
        (
            row
            for row in all_results
            if row.get("candidate_id") == primary_candidate_id and row.get("source") == "trace"
        ),
        all_results[0] if all_results else {},
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Evaluate selected existing trace, model-family, and meta-search contenders "
                "against a fresh reviewed holdout without fitting to the holdout."
            ),
            "normalization": "full-population target-curve normalization from latest component matrix",
            "selection": "latest trace/family/meta report leaders only; no new sweep candidates generated",
        },
        "inputs": {
            "review_markdown": _repo_or_home_path(review_markdown),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "trace_json": _repo_or_home_path(trace_json_path),
            "family_json": (
                _repo_or_home_path(family_json_path) if family_json_path is not None else None
            ),
            "meta_json": (
                _repo_or_home_path(meta_json_path) if meta_json_path is not None else None
            ),
            "trace_variant_count": len(trace_records),
            "trace_candidate_count": len(trace_rows),
            "family_candidate_count": len(family_candidates),
            "meta_candidate_count": len(meta_rows),
        },
        "holdout_input": holdout_input,
        "holdout_summary": {
            "review_row_count": len(holdout_rows),
            "numeric_row_count": int(np.isfinite(holdout_context["expected_values"]).sum()),
            "treatment_row_count": len(holdout_context["treatment_rows"]),
            "mapped_numeric_count": int((holdout_context["component_indices"] >= 0).sum()),
            "missing_numeric_rows": holdout_context["missing_rows"],
            "treatment_rows": holdout_context["treatment_rows"],
        },
        "primary_candidate": primary,
        "leaderboards": {
            "holdout_balanced": _leaderboard(
                all_results, dataset="holdout", score_key="balanced_score"
            ),
            "holdout_balanced_trace": _leaderboard(
                [row for row in all_results if row.get("source") == "trace"],
                dataset="holdout",
                score_key="balanced_score",
            ),
            "holdout_balanced_family": _leaderboard(
                [row for row in all_results if row.get("source") == "family"],
                dataset="holdout",
                score_key="balanced_score",
            ),
            "holdout_balanced_meta": _leaderboard(
                [row for row in all_results if row.get("source") == "meta"],
                dataset="holdout",
                score_key="balanced_score",
            ),
            "holdout_mae": _leaderboard(
                all_results, dataset="holdout", score_key="numeric_mae_score"
            ),
            "holdout_pairwise": _leaderboard(
                all_results,
                dataset="holdout",
                score_key="pairwise_order_score",
            ),
            "calibration_balanced": _leaderboard(
                all_results,
                dataset="calibration",
                score_key="balanced_score",
            ),
            "generalization_delta": _generalization_delta_leaderboard(all_results),
        },
        "candidate_results": all_results,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "review_markdown": review_markdown,
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "trace_json": trace_json_path,
                "family_json": family_json_path,
                "meta_json": meta_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "band_expert_stitch": SCRIPT_DIR
                / "srs_learner_difficulty_band_expert_stitch_en_ja.py",
                "model_family_search": SCRIPT_DIR
                / "srs_learner_difficulty_model_family_search_en_ja.py",
                "model_family_meta_search": SCRIPT_DIR
                / "srs_learner_difficulty_model_family_meta_search_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def parse_holdout_review_markdown(path: Path) -> list[ReviewedHoldoutRow]:
    rows: list[ReviewedHoldoutRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| #") or line.startswith("|---"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 6:
            continue
        _number, lemma, reading, expected, treatment, notes = parts[:6]
        rows.append(
            ReviewedHoldoutRow(
                lemma=lemma,
                reading=reading,
                expected_difficulty=_optional_float(expected),
                treatment=treatment,
                notes=notes,
            )
        )
    return rows


def holdout_json_payload(
    rows: Sequence[ReviewedHoldoutRow],
    *,
    review_markdown: Path,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "holdout_id": "srs_learner_difficulty_holdout_en_ja_v1",
        "language_pair": PAIR,
        "state": "fresh_holdout_reviewed",
        "created_from": _repo_or_home_path(review_markdown),
        "generated_at": _utc_now(),
        "purpose": (
            "Fresh reviewed holdout set for detecting learner-difficulty overfitting; "
            "do not use as a sweep fitting target until explicitly promoted."
        ),
        "difficulty_target_scale": (
            "expected_learner_difficulty is a reviewed continuous 0.00-1.00 "
            "foreign-learner difficulty target, separate from topic priority and "
            "native acquisition age."
        ),
        "labels": [_holdout_label_json(row) for row in rows],
    }


def _holdout_label_json(row: ReviewedHoldoutRow) -> dict[str, object]:
    if row.expected_difficulty is not None:
        return {
            "lemma": row.lemma,
            "expected_reading": row.reading,
            "expected_candidate_state": "normal_vocab",
            "expected_presentation_mode": "vocab",
            "expected_problem_class": "normal_vocab",
            "expected_difficulty_band": _difficulty_band(row.expected_difficulty),
            "expected_learner_difficulty": round(float(row.expected_difficulty), 4),
            "rationale": row.notes,
        }
    state_by_treatment = {
        "omit": ("suppressed_default", "suppress", "reviewed_omit"),
        "topic_only": ("deprioritized_vocab", "vocab", "topic_or_entity_specific"),
        "pattern": ("pattern_item", "pattern", "pattern_item"),
        "unsure": ("review_required", "review", "review_required"),
    }
    state, presentation, problem_class = state_by_treatment.get(
        row.treatment,
        ("review_required", "review", "review_required"),
    )
    return {
        "lemma": row.lemma,
        "expected_reading": row.reading,
        "expected_candidate_state": state,
        "expected_presentation_mode": presentation,
        "expected_problem_class": problem_class,
        "expected_difficulty_band": None,
        "rationale": row.notes,
    }


def holdout_context_from_rows(
    rows: Sequence[ReviewedHoldoutRow],
    component: object,
) -> dict[str, object]:
    component_by_lemma_reading = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(component["lemmas"], component["readings"]))
    }
    numeric_rows = [row for row in rows if row.expected_difficulty is not None]
    indices: list[int] = []
    missing_rows: list[dict[str, object]] = []
    for row in numeric_rows:
        index = component_by_lemma_reading.get((row.lemma, row.reading))
        if index is None:
            missing_rows.append({"lemma": row.lemma, "reading": row.reading})
            indices.append(-1)
        else:
            indices.append(int(index))
    expected_values = np.asarray(
        [float(row.expected_difficulty or np.nan) for row in numeric_rows],
        dtype=np.float32,
    )
    observed_candidate_states = np.full(len(indices), "", dtype="<U64")
    component_indices = np.asarray(indices, dtype=np.int64)
    valid = component_indices >= 0
    if "candidate_states" in component.files:
        observed_candidate_states[valid] = component["candidate_states"][component_indices[valid]]
    return {
        "component_indices": component_indices,
        "expected_values": expected_values,
        "expected_bands": [_difficulty_band(value) for value in expected_values],
        "expected_candidate_states": np.full(len(indices), "normal_vocab", dtype="<U64"),
        "observed_candidate_states": observed_candidate_states,
        "labels": [row.label for row in numeric_rows],
        "lemmas": [row.lemma for row in numeric_rows],
        "readings": [row.reading for row in numeric_rows],
        "treatment_rows": [
            {
                "label": row.label,
                "lemma": row.lemma,
                "reading": row.reading,
                "treatment": row.treatment,
                "notes": row.notes,
            }
            for row in rows
            if row.expected_difficulty is None
        ],
        "missing_rows": missing_rows,
    }


def evaluate_family_candidates(
    candidates: Sequence[ModelCandidate],
    *,
    component: object,
    target_positions: object,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    raw_by_expert: Mapping[str, object],
    signal_arrays: Mapping[str, object],
    detail_limit: int,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for candidate in candidates:
        raw = _candidate_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        results.append(
            result_for_normalized(
                candidate_id=candidate.candidate_id,
                source="family",
                normalized=normalized,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                detail_limit=detail_limit,
            )
        )
    return results


def evaluate_meta_candidates(
    rows: Sequence[Mapping[str, object]],
    *,
    family_report: Mapping[str, object],
    component: object,
    target_positions: object,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    raw_by_expert: Mapping[str, object],
    signal_arrays: Mapping[str, object],
    detail_limit: int,
) -> list[dict[str, object]]:
    if not rows:
        return []
    family_by_id = {
        candidate.candidate_id: candidate
        for candidate in (
            _model_candidate_from_row(row) for row in _mapping_rows(family_report.get("exact_top"))
        )
    }
    meta_candidates = [_meta_from_row(row) for row in rows]
    required_family_ids = {
        expert_id for candidate in meta_candidates for expert_id in candidate.expert_ids
    }
    raw_by_family_candidate = {
        candidate_id: _candidate_raw_scores(
            family_by_id[candidate_id],
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )
        for candidate_id in required_family_ids
        if candidate_id in family_by_id
    }
    split_context = _split_context(component, calibration_context)
    results: list[dict[str, object]] = []
    for candidate in meta_candidates:
        if any(expert_id not in raw_by_family_candidate for expert_id in candidate.expert_ids):
            continue
        raw, _leaf_ids = _raw_for_meta_candidate(
            candidate,
            raw_by_family_candidate=raw_by_family_candidate,
            split_context=split_context,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        results.append(
            result_for_normalized(
                candidate_id=candidate.candidate_id,
                source="meta",
                normalized=normalized,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                detail_limit=detail_limit,
            )
        )
    return results


def evaluate_trace_candidates(
    rows: Sequence[Mapping[str, object]],
    *,
    component: object,
    target_positions: object,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    trace_calibration_values: object,
    trace_variant_index: Mapping[str, int],
    detail_limit: int,
) -> list[dict[str, object]]:
    context = _component_context(component)
    calibration_values = np.asarray(trace_calibration_values, dtype=np.float32)
    results: list[dict[str, object]] = []
    for row in rows:
        variant = _variant_from_record(row)
        raw = _target_curve_raw_scores_for_variant(variant, context)
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        variant_index = trace_variant_index.get(variant.variant_id)
        fallback = calibration_values[variant_index] if variant_index is not None else None
        results.append(
            result_for_normalized(
                candidate_id=variant.variant_id,
                source="trace",
                normalized=normalized,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                calibration_observed_fallback=fallback,
                detail_limit=detail_limit,
            )
        )
    return results


def result_for_normalized(
    *,
    candidate_id: str,
    source: str,
    normalized: object,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    calibration_observed_fallback: object | None = None,
    detail_limit: int,
) -> dict[str, object]:
    calibration_observed = observed_for_context(
        normalized,
        calibration_context,
        fallback_values=calibration_observed_fallback,
    )
    holdout_observed = observed_for_context(normalized, holdout_context)
    calibration_metrics = metrics_for_context(calibration_context, calibration_observed)
    holdout_metrics = metrics_for_context(holdout_context, holdout_observed)
    return {
        "candidate_id": candidate_id,
        "source": source,
        "calibration": {
            "scores": calibration_metrics["scores"],
            "metrics": _summary_metrics(calibration_metrics),
        },
        "holdout": {
            "scores": holdout_metrics["scores"],
            "metrics": _summary_metrics(holdout_metrics),
            "worst_rows": worst_rows(
                holdout_context,
                holdout_observed,
                limit=detail_limit,
            ),
            "wrong_pairwise_examples": holdout_metrics["pairwise_order"]["wrong_examples"][
                :detail_limit
            ],
            "segment_misses": {
                key: value["misses"][:detail_limit]
                for key, value in _mapping(holdout_metrics.get("segments")).items()
                if value.get("misses")
            },
        },
        "generalization": generalization_summary(calibration_metrics, holdout_metrics),
    }


def observed_for_context(
    normalized: object,
    context: Mapping[str, object],
    *,
    fallback_values: object | None = None,
) -> object:
    values = np.asarray(normalized, dtype=np.float32)
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    if fallback_values is not None:
        fallback = np.asarray(fallback_values, dtype=np.float32)
        count = min(len(observed), len(fallback))
        observed[:count] = fallback[:count]
    valid = indices >= 0
    observed[valid] = values[indices[valid]]
    return observed


def metrics_for_context(
    context: Mapping[str, object],
    observed: object,
) -> dict[str, object]:
    return _difficulty_metrics(
        expected_values=context["expected_values"],
        observed_values=observed,
        expected_bands=context["expected_bands"],
        expected_candidate_states=context.get("expected_candidate_states"),
        observed_candidate_states=context.get("observed_candidate_states"),
        labels=context["labels"],
    )


def worst_rows(
    context: Mapping[str, object],
    observed: object,
    *,
    limit: int,
) -> list[dict[str, object]]:
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    observed_values = np.asarray(observed, dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    rows: list[dict[str, object]] = []
    for index, label in enumerate(labels):
        if not np.isfinite(expected[index]) or not np.isfinite(observed_values[index]):
            continue
        delta = float(observed_values[index] - expected[index])
        rows.append(
            {
                "label": label,
                "expected": _rounded(float(expected[index])),
                "observed": _rounded(float(observed_values[index])),
                "absolute_error": _rounded(abs(delta)),
                "direction": "too_high" if delta > 0 else "too_low" if delta < 0 else "match",
            }
        )
    return sorted(
        rows,
        key=lambda row: float(row.get("absolute_error") or 0.0),
        reverse=True,
    )[:limit]


def generalization_summary(
    calibration_metrics: Mapping[str, object],
    holdout_metrics: Mapping[str, object],
) -> dict[str, object]:
    calibration_scores = _mapping(calibration_metrics.get("scores"))
    holdout_scores = _mapping(holdout_metrics.get("scores"))
    return {
        "balanced_delta_holdout_minus_calibration": _rounded(
            _optional_float(holdout_scores.get("balanced_score"))
            - _optional_float(calibration_scores.get("balanced_score"))
        ),
        "mae_delta_holdout_minus_calibration": _rounded(
            _optional_float(_mapping(holdout_metrics.get("difficulty_value")).get("mae"))
            - _optional_float(_mapping(calibration_metrics.get("difficulty_value")).get("mae"))
        ),
        "pairwise_delta_holdout_minus_calibration": _rounded(
            _optional_float(holdout_scores.get("pairwise_order_score"))
            - _optional_float(calibration_scores.get("pairwise_order_score"))
        ),
    }


def _select_family_candidates(
    report: Mapping[str, object],
    *,
    limit: int,
    top_per_leaderboard: int,
) -> list[ModelCandidate]:
    by_id = {
        str(row.get("candidate_id") or ""): row for row in _mapping_rows(report.get("exact_top"))
    }
    selected: list[Mapping[str, object]] = []
    seen: set[str] = set()

    def add(row: Mapping[str, object]) -> None:
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id and candidate_id not in seen and len(selected) < limit:
            selected.append(row)
            seen.add(candidate_id)

    for row in _mapping_rows(report.get("exact_top"))[:top_per_leaderboard]:
        add(row)
    for rows in _mapping(report.get("leaderboards")).values():
        for row in _mapping_rows(rows)[:top_per_leaderboard]:
            full = by_id.get(str(row.get("candidate_id") or ""))
            if full is not None:
                add(full)
    for row in _mapping_rows(report.get("exact_top")):
        add(row)
        if len(selected) >= limit:
            break
    return [_model_candidate_from_row(row) for row in selected]


def _select_meta_rows(
    report: Mapping[str, object],
    *,
    limit: int,
    top_per_leaderboard: int,
) -> list[Mapping[str, object]]:
    by_id = {
        str(row.get("candidate_id") or ""): row for row in _mapping_rows(report.get("exact_top"))
    }
    selected: list[Mapping[str, object]] = []
    seen: set[str] = set()

    def add(row: Mapping[str, object]) -> None:
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id and candidate_id not in seen and len(selected) < limit:
            selected.append(row)
            seen.add(candidate_id)

    for row in _mapping_rows(report.get("constrained_top"))[:top_per_leaderboard]:
        add(row)
    for row in _mapping_rows(report.get("exact_top"))[:top_per_leaderboard]:
        add(row)
    for rows in _mapping(report.get("leaderboards")).values():
        for row in _mapping_rows(rows)[:top_per_leaderboard]:
            full = by_id.get(str(row.get("candidate_id") or ""))
            if full is not None:
                add(full)
    for row in _mapping_rows(report.get("exact_top")):
        add(row)
        if len(selected) >= limit:
            break
    return selected


def _select_trace_rows(
    records: Mapping[str, Mapping[str, object]],
    *,
    trace_report: Mapping[str, object],
    limit: int,
    top_per_score: int,
) -> list[Mapping[str, object]]:
    selected: list[Mapping[str, object]] = []
    seen: set[str] = set()

    def add(row: Mapping[str, object]) -> None:
        variant_id = str(row.get("variant_id") or "")
        if variant_id and variant_id not in seen and len(selected) < limit:
            selected.append(row)
            seen.add(variant_id)

    score_keys = [
        str(value)
        for value in _sequence_values(trace_report.get("score_keys"))
        if str(value).strip()
    ]
    if not score_keys:
        score_keys = sorted(
            {str(key) for row in records.values() for key in _mapping(row.get("scores")).keys()}
        )
    for score_key in score_keys:
        ranked = sorted(
            records.values(),
            key=lambda row: (
                _optional_float(_mapping(row.get("scores")).get(score_key)) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
            ),
            reverse=True,
        )
        for row in ranked[:top_per_score]:
            add(row)
    ranked_balanced = sorted(
        records.values(),
        key=lambda row: (
            _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
            _optional_float(_mapping(row.get("scores")).get("pairwise_order_score")) or -1.0,
            _optional_float(_mapping(row.get("scores")).get("default_decision_score")) or -1.0,
        ),
        reverse=True,
    )
    for row in ranked_balanced:
        add(row)
        if len(selected) >= limit:
            break
    return selected


def _primary_candidate_id(meta_report: Mapping[str, object]) -> str:
    constrained = _mapping_rows(meta_report.get("constrained_top"))
    if constrained:
        return str(constrained[0].get("candidate_id") or "")
    exact = _mapping_rows(meta_report.get("exact_top"))
    return str(exact[0].get("candidate_id") or "") if exact else ""


def _leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    score_key: str,
    limit: int = 20,
) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: _score(row, dataset, score_key),
        reverse=True,
    )[:limit]
    return [_summary_row(row, dataset=dataset) for row in ranked]


def _generalization_delta_leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int = 20,
) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: _optional_float(
            _mapping(row.get("generalization")).get("balanced_delta_holdout_minus_calibration")
        ),
        reverse=True,
    )[:limit]
    return [
        {
            **_summary_row(row, dataset="holdout"),
            "calibration_balanced": _score(row, "calibration", "balanced_score"),
            "balanced_delta": _mapping(row.get("generalization")).get(
                "balanced_delta_holdout_minus_calibration"
            ),
        }
        for row in ranked
    ]


def _summary_row(row: Mapping[str, object], *, dataset: str) -> dict[str, object]:
    metrics = _mapping(_mapping(row.get(dataset)).get("metrics"))
    scores = _mapping(_mapping(row.get(dataset)).get("scores"))
    return {
        "candidate_id": row.get("candidate_id"),
        "source": row.get("source"),
        "balanced": scores.get("balanced_score"),
        "mae": metrics.get("mae"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "spearman": metrics.get("spearman"),
        "beginner_core": metrics.get("beginner_core_pass_rate"),
        "high_tail": metrics.get("high_tail_pass_rate"),
    }


def _score(row: Mapping[str, object], dataset: str, score_key: str) -> float:
    return (
        _optional_float(_mapping(_mapping(row.get(dataset)).get("scores")).get(score_key)) or -1.0
    )


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    holdout = _mapping(report.get("holdout_summary"))
    primary = _mapping(report.get("primary_candidate"))
    lines = [
        "# en-ja learner difficulty holdout evaluation",
        "",
        "No new sweep was run. This report scores selected existing trace/family/meta contenders against the reviewed holdout.",
        "",
        "## Inputs",
        "",
        f"- Review Markdown: `{_escape(str(inputs.get('review_markdown')))}`",
        f"- Trace JSON: `{_escape(str(inputs.get('trace_json')))}`",
        f"- Trace variants available: `{inputs.get('trace_variant_count')}`",
        f"- Trace candidates evaluated: `{inputs.get('trace_candidate_count')}`",
        f"- Family candidates evaluated: `{inputs.get('family_candidate_count')}`",
        f"- Meta candidates evaluated: `{inputs.get('meta_candidate_count')}`",
        f"- Holdout numeric rows: `{holdout.get('numeric_row_count')}`",
        f"- Holdout treatment rows: `{holdout.get('treatment_row_count')}`",
        f"- Holdout mapped numeric rows: `{holdout.get('mapped_numeric_count')}`",
        f"- Sweeps run: `{report.get('sweeps_run')}`",
        "",
        "## Primary Current Candidate",
        "",
        _candidate_metrics_table([primary]),
        "",
        "### Primary Holdout Worst Rows",
        "",
        _worst_rows_table(_mapping_rows(_mapping(primary.get("holdout")).get("worst_rows"))),
        "",
        "## Holdout Balanced Leaderboard",
        "",
        _leaderboard_table(
            _mapping_rows(_mapping(report.get("leaderboards")).get("holdout_balanced"))
        ),
        "",
        "### Holdout Balanced By Source",
        "",
        "Trace candidates:",
        "",
        _leaderboard_table(
            _mapping_rows(_mapping(report.get("leaderboards")).get("holdout_balanced_trace"))[:10]
        ),
        "",
        "Family candidates:",
        "",
        _leaderboard_table(
            _mapping_rows(_mapping(report.get("leaderboards")).get("holdout_balanced_family"))[:10]
        ),
        "",
        "Meta candidates:",
        "",
        _leaderboard_table(
            _mapping_rows(_mapping(report.get("leaderboards")).get("holdout_balanced_meta"))[:10]
        ),
        "",
        "## Calibration Balanced Leaderboard",
        "",
        _leaderboard_table(
            _mapping_rows(_mapping(report.get("leaderboards")).get("calibration_balanced"))
        ),
        "",
        "## Generalization Delta Leaderboard",
        "",
        _delta_table(
            _mapping_rows(_mapping(report.get("leaderboards")).get("generalization_delta"))
        ),
        "",
        "## Treatment Rows",
        "",
        _treatment_table(_mapping_rows(holdout.get("treatment_rows"))),
        "",
    ]
    if holdout.get("missing_numeric_rows"):
        lines.extend(
            [
                "## Missing Numeric Rows",
                "",
                _missing_table(_mapping_rows(holdout.get("missing_numeric_rows"))),
                "",
            ]
        )
    return "\n".join(lines)


def _candidate_metrics_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| Candidate | Source | Cal balanced | Cal MAE | Cal pairwise | "
        "Holdout balanced | Holdout MAE | Holdout pairwise | Delta balanced |\n"
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    )
    body = []
    for row in rows:
        calibration = _mapping(row.get("calibration"))
        holdout = _mapping(row.get("holdout"))
        gen = _mapping(row.get("generalization"))
        body.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(str(row.get('candidate_id') or ''))}`",
                    _escape(str(row.get("source") or "")),
                    str(_mapping(calibration.get("scores")).get("balanced_score")),
                    str(_mapping(calibration.get("metrics")).get("mae")),
                    str(_mapping(calibration.get("metrics")).get("pairwise_accuracy")),
                    str(_mapping(holdout.get("scores")).get("balanced_score")),
                    str(_mapping(holdout.get("metrics")).get("mae")),
                    str(_mapping(holdout.get("metrics")).get("pairwise_accuracy")),
                    str(gen.get("balanced_delta_holdout_minus_calibration")),
                ]
            )
            + " |"
        )
    return "\n".join([header, *body])


def _leaderboard_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| Candidate | Source | Balanced | MAE | Bucket | Pairwise | Spearman | Beginner | High tail |\n"
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    )
    body = [
        "| "
        + " | ".join(
            [
                f"`{_escape(str(row.get('candidate_id') or ''))}`",
                _escape(str(row.get("source") or "")),
                str(row.get("balanced")),
                str(row.get("mae")),
                str(row.get("bucket_accuracy")),
                str(row.get("pairwise_accuracy")),
                str(row.get("spearman")),
                str(row.get("beginner_core")),
                str(row.get("high_tail")),
            ]
        )
        + " |"
        for row in rows
    ]
    return "\n".join([header, *body])


def _delta_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| Candidate | Source | Holdout balanced | Calibration balanced | Delta | Holdout MAE |\n"
        "|---|---|---:|---:|---:|---:|"
    )
    body = [
        "| "
        + " | ".join(
            [
                f"`{_escape(str(row.get('candidate_id') or ''))}`",
                _escape(str(row.get("source") or "")),
                str(row.get("balanced")),
                str(row.get("calibration_balanced")),
                str(row.get("balanced_delta")),
                str(row.get("mae")),
            ]
        )
        + " |"
        for row in rows
    ]
    return "\n".join([header, *body])


def _worst_rows_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = "| Label | Expected | Observed | Error | Direction |\n|---|---:|---:|---:|---|"
    body = [
        "| "
        + " | ".join(
            [
                _escape(str(row.get("label") or "")),
                str(row.get("expected")),
                str(row.get("observed")),
                str(row.get("absolute_error")),
                str(row.get("direction")),
            ]
        )
        + " |"
        for row in rows
    ]
    return "\n".join([header, *body])


def _treatment_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = "| Label | Treatment | Notes |\n|---|---|---|"
    body = [
        "| "
        + " | ".join(
            [
                _escape(str(row.get("label") or "")),
                _escape(str(row.get("treatment") or "")),
                _escape(str(row.get("notes") or "")),
            ]
        )
        + " |"
        for row in rows
    ]
    return "\n".join([header, *body])


def _missing_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = "| Lemma | Reading |\n|---|---|"
    body = [
        f"| {_escape(str(row.get('lemma') or ''))} | {_escape(str(row.get('reading') or ''))} |"
        for row in rows
    ]
    return "\n".join([header, *body])


def _optional_float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if np.isfinite(parsed) else None


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
