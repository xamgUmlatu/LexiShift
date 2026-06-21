#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_bounded_hybrid_search_en_ja import (  # noqa: E402
    DEFAULT_SEARCH_JSON,
    DEFAULT_STABILITY_JSON,
    DEFAULT_TRACE_JSON,
    _guardrails,
    _is_targeted_policy,
    _policy_dict,
    _signal_group_matrix,
    apply_policy,
    generate_correction_policies,
)
from srs_learner_difficulty_method_sample_compare_en_ja import (  # noqa: E402
    _formula_from_search_row,
    _new_method_candidate_id,
    _search_candidate_row,
    _select_old_trace_record,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_CHALLENGE_OFFSET,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_PROFICIENCY_POINTS,
    DEFAULT_WINDOW_SIGMA,
    DEFAULT_WINDOW_TOP_K,
    _calibration_context,
    _component_context,
    _escape,
    _label_context_from_json,
    _load_json,
    _mapping,
    _metric_path,
    _normalized_values_for_trace_record,
    _observed_for_context,
    _optional_float,
    _parse_float_csv,
    _proficiency_dataset_report,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_proficiency_ordering_search_en_ja import (  # noqa: E402
    _normalized_values_for_formula,
)
from srs_learner_difficulty_proficiency_ordering_stability_en_ja import (  # noqa: E402
    DEFAULT_FOLD_COUNT,
    _compact_fold_report,
    _fold_stability_summary,
    _fold_summary_rows,
    _stratified_fold_masks,
    _subset_context,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_bounded_hybrid_stability_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_bounded_hybrid_stability_en_ja_latest.md"
)
DEFAULT_RESULT_RETAIN_LIMIT = 120
DEFAULT_LEADERBOARD_LIMIT = 20


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run calibration-fold stability selection for bounded old-anchor/new-delta "
            "hybrid policies. Holdout is reported only after selection."
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
    parser.add_argument(
        "--proficiency-points",
        default=",".join(str(value) for value in DEFAULT_PROFICIENCY_POINTS),
    )
    parser.add_argument("--challenge-offset", type=float, default=DEFAULT_CHALLENGE_OFFSET)
    parser.add_argument("--window-sigma", type=float, default=DEFAULT_WINDOW_SIGMA)
    parser.add_argument("--window-top-k", type=int, default=DEFAULT_WINDOW_TOP_K)
    parser.add_argument("--fold-count", type=int, default=DEFAULT_FOLD_COUNT)
    parser.add_argument("--candidate-limit", type=int, default=0)
    parser.add_argument("--result-retain-limit", type=int, default=DEFAULT_RESULT_RETAIN_LIMIT)
    parser.add_argument("--leaderboard-limit", type=int, default=DEFAULT_LEADERBOARD_LIMIT)
    parser.add_argument("--detail-limit", type=int, default=20)
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
        proficiency_points=_parse_float_csv(args.proficiency_points),
        challenge_offset=float(args.challenge_offset),
        window_sigma=max(1e-6, float(args.window_sigma)),
        window_top_k=max(1, int(args.window_top_k)),
        fold_count=max(2, int(args.fold_count)),
        candidate_limit=max(0, int(args.candidate_limit)),
        result_retain_limit=max(1, int(args.result_retain_limit)),
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
    search_json: Path,
    stability_json: Path,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    holdout_json_path: Path,
    old_score_key: str,
    new_candidate_id: str,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    fold_count: int,
    candidate_limit: int,
    result_retain_limit: int,
    leaderboard_limit: int,
    detail_limit: int,
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
    new_row = _search_candidate_row(search, new_candidate_id or _new_method_candidate_id(stability))
    new_formula = _formula_from_search_row(new_row)
    old_values = _normalized_values_for_trace_record(old_record, component_context)
    new_values = _normalized_values_for_formula(new_formula, component_context)
    signal_groups = _signal_group_matrix(component_context)
    policies = generate_correction_policies()
    if candidate_limit > 0:
        policies = policies[:candidate_limit]

    fold_masks = _stratified_fold_masks(calibration_context, fold_count=fold_count)
    train_masks = tuple(~np.asarray(mask, dtype=bool) for mask in fold_masks)
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
            mask,
            context_id=f"calibration_train_{index + 1}",
        )
        for index, mask in enumerate(train_masks)
    )
    reference = _reference_reports(
        old_values=old_values,
        new_values=new_values,
        old_record=old_record,
        new_row=new_row,
        validation_contexts=validation_contexts,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    results = [
        _candidate_stability_report(
            policy,
            old_values=old_values,
            new_values=new_values,
            signal_groups=signal_groups,
            candidate_states=component_context.candidate_states,
            target_positions=component_context.target_curve_positions,
            validation_contexts=validation_contexts,
            train_contexts=train_contexts,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            old_reference=reference["old_method"],
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        for policy in policies
    ]
    scopes: Mapping[str, Callable[[Mapping[str, object]], bool]] = {
        "all": lambda _row: True,
        "targeted": _is_targeted_policy,
        "narrow": _is_narrow_policy,
    }
    selector_runs = {
        scope_id: _fold_training_selector_run([row for row in results if predicate(row)])
        for scope_id, predicate in scopes.items()
    }
    retained = _retained_results(results, limit=result_retain_limit)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "stability_selector_run": True,
        "holdout_used_for_selection": False,
        "method": {
            "purpose": (
                "Calibration-fold stability selector for bounded old-anchor/new-delta "
                "hybrid policies."
            ),
            "selection_rule": (
                "For each fold, select using the other calibration folds only. "
                "Holdout is reported after selection and is never used to choose a policy."
            ),
            "scope_definitions": {
                "all": "Every generated bounded hybrid policy, including broad global blends.",
                "targeted": "Excludes old-anchor controls and broad global-delta blends.",
                "narrow": "Targeted policies with at most 25,000 changed rows.",
            },
            "target_curve_id": TARGET_CURVE_ID,
        },
        "parameters": {
            "old_score_key": old_score_key,
            "fold_count": int(fold_count),
            "candidate_limit": int(candidate_limit),
            "evaluated_policy_count": len(policies),
            "result_retain_limit": int(result_retain_limit),
            "leaderboard_limit": int(leaderboard_limit),
            "proficiency_points": [round(float(value), 6) for value in proficiency_points],
            "challenge_offset": round(float(challenge_offset), 6),
            "window_sigma": round(float(window_sigma), 6),
            "window_top_k": int(window_top_k),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "search_json": _repo_or_home_path(search_json),
            "stability_json": _repo_or_home_path(stability_json),
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
                "search_json": search_json,
                "stability_json": stability_json,
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "holdout_json": holdout_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "bounded_hybrid_search": SCRIPT_DIR
                / "srs_learner_difficulty_bounded_hybrid_search_en_ja.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
                "proficiency_ordering_search": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_search_en_ja.py",
                "proficiency_ordering_stability": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_stability_en_ja.py",
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "folds": _fold_summary_rows(calibration_context, fold_masks),
        "reference_candidates": reference,
        "fold_training_selectors": selector_runs,
        "leaderboards": {
            "stability_selector_all": _leaderboard(
                results,
                sort_key="stability_selector_score",
                dataset="stability",
                limit=leaderboard_limit,
            ),
            "stability_selector_targeted": _leaderboard(
                [row for row in results if _is_targeted_policy(row)],
                sort_key="stability_selector_score",
                dataset="stability",
                limit=leaderboard_limit,
            ),
            "stability_selector_narrow": _leaderboard(
                [row for row in results if _is_narrow_policy(row)],
                sort_key="stability_selector_score",
                dataset="stability",
                limit=leaderboard_limit,
            ),
            "holdout_for_stability_winners": _leaderboard(
                sorted(
                    results,
                    key=lambda row: _optional_float(row.get("stability_selector_score")) or -999.0,
                    reverse=True,
                ),
                sort_key="stability_selector_score",
                dataset="holdout",
                limit=leaderboard_limit,
                keep_order=True,
            ),
            "holdout_oracle": _leaderboard(
                results,
                sort_key="holdout_score",
                dataset="holdout",
                limit=leaderboard_limit,
            ),
            "targeted_holdout_oracle": _leaderboard(
                [row for row in results if _is_targeted_policy(row)],
                sort_key="holdout_score",
                dataset="holdout",
                limit=leaderboard_limit,
            ),
        },
        "primary_candidates": {
            "stability_selector_all": _candidate_summary(
                _top_candidate(results, "stability_selector_score"),
                dataset="stability",
            ),
            "stability_selector_targeted": _candidate_summary(
                _top_candidate(
                    [row for row in results if _is_targeted_policy(row)],
                    "stability_selector_score",
                ),
                dataset="stability",
            ),
            "stability_selector_narrow": _candidate_summary(
                _top_candidate(
                    [row for row in results if _is_narrow_policy(row)],
                    "stability_selector_score",
                ),
                dataset="stability",
            ),
            "holdout_oracle": _candidate_summary(
                _top_candidate(results, "holdout_score"),
                dataset="holdout",
            ),
            "targeted_holdout_oracle": _candidate_summary(
                _top_candidate(
                    [row for row in results if _is_targeted_policy(row)],
                    "holdout_score",
                ),
                dataset="holdout",
            ),
        },
        "candidate_results": retained,
    }


def _candidate_stability_report(
    policy: object,
    *,
    old_values: object,
    new_values: object,
    signal_groups: Mapping[str, object],
    candidate_states: Sequence[str],
    target_positions: object,
    validation_contexts: Sequence[object],
    train_contexts: Sequence[object],
    calibration_context: object,
    holdout_context: object,
    old_reference: Mapping[str, object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    hybrid_values, correction_summary = apply_policy(
        policy,
        old_values=old_values,
        new_values=new_values,
        signal_groups=signal_groups,
        candidate_states=candidate_states,
        target_positions=target_positions,
    )
    full_calibration = _dataset_report(
        calibration_context,
        hybrid_values,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout = _dataset_report(
        holdout_context,
        hybrid_values,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    fold_reports = [
        _dataset_report(
            context,
            hybrid_values,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        for context in validation_contexts
    ]
    train_reports = [
        _dataset_report(
            context,
            hybrid_values,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        for context in train_contexts
    ]
    fold_summary = _fold_stability_summary(fold_reports)
    train_rows = [_compact_fold_report(index, report) for index, report in enumerate(train_reports)]
    full_score = _optional_float(full_calibration.get("proficiency_ordering_score")) or -999.0
    mean_score = _optional_float(fold_summary.get("mean_score")) or -999.0
    min_score = _optional_float(fold_summary.get("min_score")) or -999.0
    std_score = _optional_float(fold_summary.get("score_std")) or 999.0
    optimism = max(0.0, full_score - mean_score)
    stability_score = (0.70 * mean_score) + (0.25 * min_score) - (0.35 * std_score)
    stability_score -= 0.20 * optimism
    old_fold_mean = _metric_path(old_reference, "fold_stability", "mean_score")
    return {
        "candidate_id": policy.policy_id,
        "policy_family": _policy_family(policy.policy_id),
        "scope": _scope_for_policy(policy.policy_id, correction_summary),
        "description": policy.description,
        "policy": _policy_dict(policy),
        "correction_summary": correction_summary,
        "calibration": full_calibration,
        "holdout": holdout,
        "guardrails": _guardrails(full_calibration, old_reference["calibration"]),
        "full_calibration_score": _rounded(full_score),
        "fold_stability": fold_summary,
        "train_folds": train_rows,
        "stability_selector_score": _rounded(stability_score),
        "reference_fold_mean_delta": _rounded(mean_score - old_fold_mean),
        "full_calibration_optimism": _rounded(optimism),
        "holdout_score": holdout.get("proficiency_ordering_score"),
        "holdout_delta_vs_old": _rounded(
            _optional_float(holdout.get("proficiency_ordering_score"))
            - _metric_path(old_reference, "holdout", "proficiency_ordering_score")
        ),
        "holdout_delta_from_fold_mean": _rounded(
            _optional_float(holdout.get("proficiency_ordering_score")) - mean_score
        ),
    }


def _dataset_report(
    context: object,
    values: object,
    *,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    return _proficiency_dataset_report(
        context,
        _observed_for_context(values, context),
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )


def _reference_reports(
    *,
    old_values: object,
    new_values: object,
    old_record: Mapping[str, object],
    new_row: Mapping[str, object],
    validation_contexts: Sequence[object],
    calibration_context: object,
    holdout_context: object,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    return {
        "old_method": _reference_report(
            "old_method",
            old_record.get("variant_id"),
            old_values,
            validation_contexts=validation_contexts,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        ),
        "new_method": _reference_report(
            "new_method",
            new_row.get("candidate_id"),
            new_values,
            validation_contexts=validation_contexts,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        ),
    }


def _reference_report(
    source: str,
    candidate_id: object,
    values: object,
    *,
    validation_contexts: Sequence[object],
    calibration_context: object,
    holdout_context: object,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    fold_reports = [
        _dataset_report(
            context,
            values,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        for context in validation_contexts
    ]
    return {
        "candidate_id": candidate_id,
        "source": source,
        "fold_stability": _fold_stability_summary(fold_reports),
        "calibration": _dataset_report(
            calibration_context,
            values,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        ),
        "holdout": _dataset_report(
            holdout_context,
            values,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        ),
    }


def _fold_training_selector_run(
    results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    events = _fold_training_selector_events(results)
    frequency = _fold_training_selection_frequency(events)
    return {
        "events": events,
        "selection_frequency": frequency,
        "mean_train_score": _rounded(_mean_metric(events, "train_score")),
        "mean_validation_score": _rounded(_mean_metric(events, "validation_score")),
        "mean_holdout_score": _rounded(_mean_metric(events, "holdout_score")),
    }


def _fold_training_selector_events(
    results: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    fold_count = max((len(_mapping_rows(row.get("train_folds"))) for row in results), default=0)
    events = []
    for fold_index in range(fold_count):
        ranked = sorted(
            results,
            key=lambda row: _fold_score(row, "train_folds", fold_index),
            reverse=True,
        )
        if not ranked:
            continue
        selected = ranked[0]
        validation = _fold_row(selected, "fold_stability", fold_index)
        train = _fold_row(selected, "train_folds", fold_index)
        events.append(
            {
                "fold": fold_index + 1,
                "candidate_id": selected.get("candidate_id"),
                "policy_family": selected.get("policy_family"),
                "scope": selected.get("scope"),
                "train_score": train.get("score"),
                "validation_score": validation.get("score"),
                "validation_pairwise": validation.get("normal_vocab_pairwise"),
                "validation_window_quality": validation.get("window_quality"),
                "holdout_score": selected.get("holdout_score"),
                "full_calibration_score": selected.get("full_calibration_score"),
                "stability_selector_score": selected.get("stability_selector_score"),
            }
        )
    return events


def _fold_training_selection_frequency(
    events: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for event in events:
        candidate_id = str(event.get("candidate_id") or "")
        if not candidate_id:
            continue
        row = grouped.setdefault(
            candidate_id,
            {
                "candidate_id": candidate_id,
                "policy_family": event.get("policy_family"),
                "scope": event.get("scope"),
                "folds_selected": [],
                "validation_scores": [],
                "train_scores": [],
                "holdout_scores": [],
            },
        )
        row["folds_selected"].append(event.get("fold"))  # type: ignore[index,union-attr]
        row["validation_scores"].append(event.get("validation_score"))  # type: ignore[index,union-attr]
        row["train_scores"].append(event.get("train_score"))  # type: ignore[index,union-attr]
        row["holdout_scores"].append(event.get("holdout_score"))  # type: ignore[index,union-attr]
    summaries = []
    for row in grouped.values():
        validation_scores = _numbers(row.get("validation_scores"))
        train_scores = _numbers(row.get("train_scores"))
        holdout_scores = _numbers(row.get("holdout_scores"))
        summaries.append(
            {
                "candidate_id": row.get("candidate_id"),
                "policy_family": row.get("policy_family"),
                "scope": row.get("scope"),
                "selected_fold_count": len(row.get("folds_selected") or []),
                "folds_selected": row.get("folds_selected") or [],
                "mean_validation_score": _rounded(_mean_number_list(validation_scores)),
                "min_validation_score": _rounded(
                    min(validation_scores) if validation_scores else None
                ),
                "mean_train_score": _rounded(_mean_number_list(train_scores)),
                "mean_holdout_score": _rounded(_mean_number_list(holdout_scores)),
            }
        )
    return sorted(
        summaries,
        key=lambda row: (
            int(row.get("selected_fold_count") or 0),
            _optional_float(row.get("mean_validation_score")) or -999.0,
        ),
        reverse=True,
    )


def _fold_score(
    row: Mapping[str, object],
    key: str,
    fold_index: int,
) -> float:
    fold_row = _fold_row(row, key, fold_index)
    return _optional_float(fold_row.get("score")) or -999.0


def _fold_row(
    row: Mapping[str, object],
    key: str,
    fold_index: int,
) -> Mapping[str, object]:
    if key == "fold_stability":
        folds = _mapping_rows(_mapping(row.get("fold_stability")).get("folds"))
    else:
        folds = _mapping_rows(row.get(key))
    return folds[fold_index] if fold_index < len(folds) else {}


def _leaderboard(
    candidates: Sequence[Mapping[str, object]],
    *,
    sort_key: str,
    dataset: str,
    limit: int,
    keep_order: bool = False,
) -> list[dict[str, object]]:
    rows = list(candidates)
    if not keep_order:
        rows = sorted(
            rows,
            key=lambda row: _optional_float(row.get(sort_key)) or -999.0,
            reverse=True,
        )
    return [_candidate_summary(row, dataset=dataset) for row in rows[:limit]]


def _candidate_summary(
    row: Mapping[str, object],
    *,
    dataset: str,
) -> dict[str, object]:
    if not row:
        return {}
    stability = _mapping(row.get("fold_stability"))
    calibration = _mapping(row.get("calibration"))
    holdout = _mapping(row.get("holdout"))
    dataset_report = calibration if dataset in {"calibration", "stability"} else holdout
    if dataset == "stability":
        dataset_score = row.get("stability_selector_score")
    else:
        dataset_score = dataset_report.get("proficiency_ordering_score")
    normal_vocab = _mapping(dataset_report.get("normal_vocab"))
    metrics = _mapping(normal_vocab.get("metrics"))
    scores = _mapping(normal_vocab.get("scores"))
    windows = _mapping(dataset_report.get("frontier_windows"))
    correction = _mapping(row.get("correction_summary"))
    return {
        "candidate_id": row.get("candidate_id"),
        "policy_family": row.get("policy_family"),
        "scope": row.get("scope"),
        "dataset_score": dataset_score,
        "stability_selector_score": row.get("stability_selector_score"),
        "fold_mean": stability.get("mean_score"),
        "fold_min": stability.get("min_score"),
        "fold_std": stability.get("score_std"),
        "full_calibration_score": row.get("full_calibration_score"),
        "full_calibration_optimism": row.get("full_calibration_optimism"),
        "holdout_score": row.get("holdout_score"),
        "holdout_delta_vs_old": row.get("holdout_delta_vs_old"),
        "holdout_delta_from_fold_mean": row.get("holdout_delta_from_fold_mean"),
        "normal_vocab_mae": metrics.get("mae"),
        "normal_vocab_pairwise": scores.get("pairwise_order_score"),
        "window_quality": windows.get("average_window_score"),
        "changed_count": correction.get("changed_count"),
        "guardrails_pass": _mapping(row.get("guardrails")).get("pass"),
    }


def _top_candidate(
    candidates: Sequence[Mapping[str, object]],
    sort_key: str,
) -> Mapping[str, object]:
    if not candidates:
        return {}
    return max(candidates, key=lambda row: _optional_float(row.get(sort_key)) or -999.0)


def _retained_results(
    results: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    selected = []
    seen = set()
    for key in ("stability_selector_score", "holdout_score", "full_calibration_score"):
        for row in sorted(
            results,
            key=lambda value: _optional_float(value.get(key)) or -999.0,
            reverse=True,
        ):
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id and candidate_id not in seen:
                selected.append(dict(row))
                seen.add(candidate_id)
            if len(selected) >= limit:
                return selected
    return selected


def _is_narrow_policy(row: Mapping[str, object]) -> bool:
    if not _is_targeted_policy(row):
        return False
    changed = _optional_float(_mapping(row.get("correction_summary")).get("changed_count"))
    return changed is not None and changed <= 25000


def _scope_for_policy(
    policy_id: str,
    correction_summary: Mapping[str, object],
) -> str:
    if policy_id.startswith(("global_delta_blend", "old_anchor")):
        return "all"
    changed = _optional_float(correction_summary.get("changed_count"))
    if changed is not None and changed <= 25000:
        return "narrow"
    return "targeted"


def _policy_family(policy_id: str) -> str:
    if "__" not in policy_id:
        return policy_id
    return policy_id.split("__", 1)[0]


def _mean_metric(rows: Sequence[Mapping[str, object]], key: str) -> float | None:
    return _mean_number_list(_numbers(row.get(key) for row in rows))


def _numbers(values: object) -> list[float]:
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        raw_values = values
    else:
        raw_values = tuple(values) if not isinstance(values, (str, bytes)) else ()
    parsed = []
    for value in raw_values:
        number = _optional_float(value)
        if number is not None:
            parsed.append(number)
    return parsed


def _mean_number_list(values: Sequence[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Learner Difficulty Bounded Hybrid Stability",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Holdout used for selection: `{_escape(report.get('holdout_used_for_selection'))}`",
        f"- Evaluated policies: `{_escape(_mapping(report.get('parameters')).get('evaluated_policy_count'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Holdout labels: `{_escape(inputs.get('holdout_label_count'))}`",
        "",
        "## Method",
        "",
        str(method.get("purpose") or ""),
        "",
        str(method.get("selection_rule") or ""),
        "",
    ]
    lines.extend(_folds_section(report))
    lines.extend(_reference_section(report))
    lines.extend(_primary_section(report))
    for scope_id in ("all", "targeted", "narrow"):
        lines.extend(_fold_training_selector_section(report, scope_id))
    lines.extend(
        _leaderboard_section(
            report,
            "stability_selector_all",
            "Stability Selector All",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "stability_selector_targeted",
            "Stability Selector Targeted",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "stability_selector_narrow",
            "Stability Selector Narrow",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "holdout_for_stability_winners",
            "Holdout For Stability Winners",
        )
    )
    lines.extend(_leaderboard_section(report, "holdout_oracle", "Holdout Oracle"))
    lines.extend(_leaderboard_section(report, "targeted_holdout_oracle", "Targeted Holdout Oracle"))
    return "\n".join(lines).rstrip() + "\n"


def _folds_section(report: Mapping[str, object]) -> list[str]:
    rows = _mapping_rows(report.get("folds"))
    lines = ["## Fold Balance", ""]
    lines.append("| Fold | Labels | Numeric | Normal vocab numeric |")
    lines.append("| ---: | ---: | ---: | ---: |")
    for row in rows:
        lines.append(
            f"| `{_escape(row.get('fold'))}` | `{_escape(row.get('label_count'))}` | "
            f"`{_escape(row.get('numeric_count'))}` | "
            f"`{_escape(row.get('normal_vocab_numeric_count'))}` |"
        )
    lines.append("")
    return lines


def _reference_section(report: Mapping[str, object]) -> list[str]:
    references = _mapping(report.get("reference_candidates"))
    lines = ["## References", ""]
    lines.append("| Reference | Fold mean | Fold min | Fold std | Full cal | Holdout |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for reference_id, raw in sorted(references.items()):
        row = _mapping(raw)
        stability = _mapping(row.get("fold_stability"))
        calibration = _mapping(row.get("calibration"))
        holdout = _mapping(row.get("holdout"))
        lines.append(
            f"| `{_escape(reference_id)}` | "
            f"`{_escape(stability.get('mean_score'))}` | "
            f"`{_escape(stability.get('min_score'))}` | "
            f"`{_escape(stability.get('score_std'))}` | "
            f"`{_escape(calibration.get('proficiency_ordering_score'))}` | "
            f"`{_escape(holdout.get('proficiency_ordering_score'))}` |"
        )
    lines.append("")
    return lines


def _primary_section(report: Mapping[str, object]) -> list[str]:
    primary = _mapping(report.get("primary_candidates"))
    lines = [
        "## Primary Candidates",
        "",
        "| Selector | Candidate | Scope | Fold mean | Stability | Holdout | Holdout vs old | Changed |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in (
        "stability_selector_all",
        "stability_selector_targeted",
        "stability_selector_narrow",
        "holdout_oracle",
        "targeted_holdout_oracle",
    ):
        row = _mapping(primary.get(key))
        lines.append(
            f"| `{_escape(key)}` | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('scope'))}` | `{_escape(row.get('fold_mean'))}` | "
            f"`{_escape(row.get('stability_selector_score'))}` | "
            f"`{_escape(row.get('holdout_score'))}` | "
            f"`{_escape(row.get('holdout_delta_vs_old'))}` | "
            f"`{_escape(row.get('changed_count'))}` |"
        )
    lines.append("")
    return lines


def _fold_training_selector_section(
    report: Mapping[str, object],
    scope_id: str,
) -> list[str]:
    selector = _mapping(_mapping(report.get("fold_training_selectors")).get(scope_id))
    frequency_rows = _mapping_rows(selector.get("selection_frequency"))
    event_rows = _mapping_rows(selector.get("events"))
    lines = [
        f"## Fold-Training Selector {scope_id.title()}",
        "",
        f"- Mean train score: `{_escape(selector.get('mean_train_score'))}`",
        f"- Mean validation score: `{_escape(selector.get('mean_validation_score'))}`",
        f"- Mean holdout score: `{_escape(selector.get('mean_holdout_score'))}`",
        "",
        "| Candidate | Family | Selected folds | Validation mean | Validation min | Holdout mean |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in frequency_rows:
        folds = ",".join(str(value) for value in row.get("folds_selected") or [])
        lines.append(
            f"| `{_escape(row.get('candidate_id'))}` | `{_escape(row.get('policy_family'))}` | "
            f"`{_escape(folds)}` | `{_escape(row.get('mean_validation_score'))}` | "
            f"`{_escape(row.get('min_validation_score'))}` | "
            f"`{_escape(row.get('mean_holdout_score'))}` |"
        )
    lines.extend(["", "| Fold | Selected candidate | Train | Validation | Holdout |"])
    lines.append("| ---: | --- | ---: | ---: | ---: |")
    for row in event_rows:
        lines.append(
            f"| `{_escape(row.get('fold'))}` | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('train_score'))}` | "
            f"`{_escape(row.get('validation_score'))}` | "
            f"`{_escape(row.get('holdout_score'))}` |"
        )
    lines.append("")
    return lines


def _leaderboard_section(
    report: Mapping[str, object],
    key: str,
    title: str,
) -> list[str]:
    rows = _mapping_rows(_mapping(report.get("leaderboards")).get(key))
    lines = [
        f"## {title}",
        "",
        "| Candidate | Scope | Dataset score | Fold mean | Fold min | Holdout | Holdout vs old | Changed |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not rows:
        lines.append("|  |  |  |  |  |  |  |  |")
        lines.append("")
        return lines
    for row in rows:
        lines.append(
            f"| `{_escape(row.get('candidate_id'))}` | `{_escape(row.get('scope'))}` | "
            f"`{_escape(row.get('dataset_score'))}` | "
            f"`{_escape(row.get('fold_mean'))}` | "
            f"`{_escape(row.get('fold_min'))}` | "
            f"`{_escape(row.get('holdout_score'))}` | "
            f"`{_escape(row.get('holdout_delta_vs_old'))}` | "
            f"`{_escape(row.get('changed_count'))}` |"
        )
    lines.append("")
    return lines


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
