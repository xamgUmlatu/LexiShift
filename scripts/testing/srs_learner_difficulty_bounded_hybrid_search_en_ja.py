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
from srs_learner_difficulty_disagreement_review_en_ja import (  # noqa: E402
    SIGNAL_GROUPS,
)
from srs_learner_difficulty_method_sample_compare_en_ja import (  # noqa: E402
    DEFAULT_SEARCH_JSON,
    DEFAULT_STABILITY_JSON,
    DEFAULT_TRACE_JSON,
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
    _target_curve_normalize,
    _utc_now,
)
from srs_learner_difficulty_proficiency_ordering_search_en_ja import (  # noqa: E402
    _normalized_values_for_formula,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_bounded_hybrid_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_bounded_hybrid_search_en_ja_latest.md"
)
DEFAULT_RETAIN_LIMIT = 80
DEFAULT_LEADERBOARD_LIMIT = 20


@dataclass(frozen=True)
class CorrectionPolicy:
    policy_id: str
    description: str
    positive_groups: tuple[str, ...]
    negative_groups: tuple[str, ...]
    positive_threshold: float
    negative_threshold: float
    scale: float
    cap: float
    normalization: str
    normal_vocab_only: bool = True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search bounded old-anchor/new-delta hybrid corrections for en-ja "
            "learner difficulty. This is a sidecar and does not change runtime behavior."
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
    parser.add_argument("--retain-limit", type=int, default=DEFAULT_RETAIN_LIMIT)
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
        retain_limit=max(1, int(args.retain_limit)),
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
    retain_limit: int,
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
    reference = _reference_reports(
        old_values=old_values,
        new_values=new_values,
        old_record=old_record,
        new_row=new_row,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    candidates = [
        _candidate_report(
            policy,
            old_values=old_values,
            new_values=new_values,
            signal_groups=signal_groups,
            component_context=component_context,
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
    ranked = sorted(
        candidates,
        key=lambda row: _candidate_metric(row, "calibration"),
        reverse=True,
    )
    guardrail_passing = [row for row in candidates if _guardrails_pass(row)]
    targeted_guardrail_passing = [row for row in guardrail_passing if _is_targeted_policy(row)]
    narrow_guardrail_passing = [
        row
        for row in targeted_guardrail_passing
        if (_optional_float(_mapping(row.get("correction_summary")).get("changed_count")) or 0.0)
        <= 25000
    ]
    retained = _retained_candidates(candidates, retain_limit=retain_limit)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "search_run": True,
        "method": {
            "purpose": (
                "Test whether the old balanced-score winner can be improved by "
                "narrow bounded corrections derived from the new proficiency-ordering "
                "winner's disagreements."
            ),
            "score_shape": (
                "hybrid_i = old_i + clipped(scale * (new_i - old_i)) on a "
                "source-signal mask; candidates use either clipped absolute scores "
                "or rank-normalization back to the target curve."
            ),
            "selection_rule": (
                "Candidate generation and ranking use calibration only. Holdout is "
                "reported as a non-selector generalization check."
            ),
            "target_curve_id": TARGET_CURVE_ID,
            "signal_groups": {key: list(value) for key, value in SIGNAL_GROUPS.items()},
        },
        "parameters": {
            "old_score_key": old_score_key,
            "policy_count": len(policies),
            "retain_limit": int(retain_limit),
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
                "disagreement_review": SCRIPT_DIR
                / "srs_learner_difficulty_disagreement_review_en_ja.py",
                "method_sample_compare": SCRIPT_DIR
                / "srs_learner_difficulty_method_sample_compare_en_ja.py",
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
            },
        },
        "reference_candidates": reference,
        "leaderboards": {
            "calibration_proficiency_ordering": _leaderboard(
                candidates,
                dataset="calibration",
                limit=leaderboard_limit,
            ),
            "calibration_guardrail_passing": _leaderboard(
                guardrail_passing,
                dataset="calibration",
                limit=leaderboard_limit,
            ),
            "targeted_calibration_guardrail_passing": _leaderboard(
                targeted_guardrail_passing,
                dataset="calibration",
                limit=leaderboard_limit,
            ),
            "narrow_calibration_guardrail_passing": _leaderboard(
                narrow_guardrail_passing,
                dataset="calibration",
                limit=leaderboard_limit,
            ),
            "holdout_of_calibration_winners": _leaderboard(
                ranked[:leaderboard_limit],
                dataset="holdout",
                limit=leaderboard_limit,
                keep_order=True,
            ),
            "holdout_of_targeted_calibration_winners": _leaderboard(
                sorted(
                    targeted_guardrail_passing,
                    key=lambda row: _candidate_metric(row, "calibration"),
                    reverse=True,
                )[:leaderboard_limit],
                dataset="holdout",
                limit=leaderboard_limit,
                keep_order=True,
            ),
            "holdout_oracle": _leaderboard(
                candidates,
                dataset="holdout",
                limit=leaderboard_limit,
            ),
            "targeted_holdout_oracle": _leaderboard(
                [row for row in candidates if _is_targeted_policy(row)],
                dataset="holdout",
                limit=leaderboard_limit,
            ),
        },
        "primary_candidates": {
            "calibration_selector": _primary_candidate(ranked),
            "guardrail_selector": _primary_candidate(
                sorted(
                    guardrail_passing,
                    key=lambda row: _candidate_metric(row, "calibration"),
                    reverse=True,
                )
            ),
            "targeted_guardrail_selector": _primary_candidate(
                sorted(
                    targeted_guardrail_passing,
                    key=lambda row: _candidate_metric(row, "calibration"),
                    reverse=True,
                )
            ),
            "narrow_guardrail_selector": _primary_candidate(
                sorted(
                    narrow_guardrail_passing,
                    key=lambda row: _candidate_metric(row, "calibration"),
                    reverse=True,
                )
            ),
            "holdout_oracle": _primary_candidate(
                sorted(
                    candidates,
                    key=lambda row: _candidate_metric(row, "holdout"),
                    reverse=True,
                )
            ),
            "targeted_holdout_oracle": _primary_candidate(
                sorted(
                    [row for row in candidates if _is_targeted_policy(row)],
                    key=lambda row: _candidate_metric(row, "holdout"),
                    reverse=True,
                )
            ),
        },
        "candidate_results": retained,
    }


def generate_correction_policies() -> list[CorrectionPolicy]:
    policies = [
        CorrectionPolicy(
            policy_id="old_anchor_clip",
            description="No correction; old model scores clipped to [0, 1].",
            positive_groups=(),
            negative_groups=(),
            positive_threshold=1.1,
            negative_threshold=1.1,
            scale=0.0,
            cap=0.0,
            normalization="clip",
        ),
        CorrectionPolicy(
            policy_id="old_anchor_rerank",
            description="No correction; old model reranked back to the target curve.",
            positive_groups=(),
            negative_groups=(),
            positive_threshold=1.1,
            negative_threshold=1.1,
            scale=0.0,
            cap=0.0,
            normalization="rerank",
        ),
    ]
    for normalization in ("clip", "rerank"):
        for scale in (0.25, 0.50, 0.75, 1.00):
            for cap in (0.04, 0.08, 0.12, 0.16):
                for threshold in (0.50, 0.65, 0.80):
                    policies.append(
                        CorrectionPolicy(
                            policy_id=(
                                "rare_tail_lift"
                                f"__t{_token(threshold)}"
                                f"__s{_token(scale)}"
                                f"__c{_token(cap)}"
                                f"__{normalization}"
                            ),
                            description=(
                                "Only borrow positive new-model deltas for normal-vocab "
                                "rows with both rare-native and frequency-tail evidence."
                            ),
                            positive_groups=("rare_native", "frequency_tail"),
                            negative_groups=(),
                            positive_threshold=threshold,
                            negative_threshold=1.1,
                            scale=scale,
                            cap=cap,
                            normalization=normalization,
                        )
                    )
                    policies.append(
                        CorrectionPolicy(
                            policy_id=(
                                "rare_or_tail_lift"
                                f"__t{_token(threshold)}"
                                f"__s{_token(scale)}"
                                f"__c{_token(cap)}"
                                f"__{normalization}"
                            ),
                            description=(
                                "Borrow positive deltas when rare-native or frequency-tail "
                                "evidence is high."
                            ),
                            positive_groups=("rare_native|frequency_tail",),
                            negative_groups=(),
                            positive_threshold=threshold,
                            negative_threshold=1.1,
                            scale=scale,
                            cap=cap,
                            normalization=normalization,
                        )
                    )
                for written_threshold in (0.70, 0.85):
                    policies.append(
                        CorrectionPolicy(
                            policy_id=(
                                "written_downshift_small"
                                f"__t{_token(written_threshold)}"
                                f"__s{_token(scale)}"
                                f"__c{_token(min(cap, 0.08))}"
                                f"__{normalization}"
                            ),
                            description=(
                                "Borrow small negative deltas for very written-burden-heavy "
                                "normal-vocab rows."
                            ),
                            positive_groups=(),
                            negative_groups=("written_burden",),
                            positive_threshold=1.1,
                            negative_threshold=written_threshold,
                            scale=scale,
                            cap=min(cap, 0.08),
                            normalization=normalization,
                        )
                    )
                for threshold in (0.50, 0.65):
                    policies.append(
                        CorrectionPolicy(
                            policy_id=(
                                "rare_lift_written_small_downshift"
                                f"__t{_token(threshold)}"
                                f"__s{_token(scale)}"
                                f"__c{_token(cap)}"
                                f"__{normalization}"
                            ),
                            description=(
                                "Lift rare-tail rows and allow only small written-burden "
                                "downshifts in the opposite direction."
                            ),
                            positive_groups=("rare_native", "frequency_tail"),
                            negative_groups=("written_burden",),
                            positive_threshold=threshold,
                            negative_threshold=0.85,
                            scale=scale,
                            cap=cap,
                            normalization=normalization,
                        )
                    )
        for scale in (0.10, 0.20, 0.35):
            for cap in (0.04, 0.08, 0.12):
                policies.append(
                    CorrectionPolicy(
                        policy_id=f"global_delta_blend__s{_token(scale)}__c{_token(cap)}__{normalization}",
                        description=(
                            "Control candidate: borrow bounded deltas for all normal-vocab rows."
                        ),
                        positive_groups=("all",),
                        negative_groups=("all",),
                        positive_threshold=0.0,
                        negative_threshold=0.0,
                        scale=scale,
                        cap=cap,
                        normalization=normalization,
                    )
                )
    return _dedupe_policies(policies)


def _candidate_report(
    policy: CorrectionPolicy,
    *,
    old_values: object,
    new_values: object,
    signal_groups: Mapping[str, object],
    component_context: object,
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
        candidate_states=component_context.candidate_states,
        target_positions=component_context.target_curve_positions,
    )
    calibration = _proficiency_dataset_report(
        calibration_context,
        _observed_for_context(hybrid_values, calibration_context),
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout = _proficiency_dataset_report(
        holdout_context,
        _observed_for_context(hybrid_values, holdout_context),
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    return {
        "candidate_id": policy.policy_id,
        "source": "bounded_old_new_hybrid",
        "description": policy.description,
        "policy": _policy_dict(policy),
        "correction_summary": correction_summary,
        "calibration": calibration,
        "holdout": holdout,
        "guardrails": _guardrails(calibration, old_reference["calibration"]),
        "generalization": {
            "score_delta_holdout_minus_calibration": _rounded(
                _optional_float(holdout.get("proficiency_ordering_score"))
                - _optional_float(calibration.get("proficiency_ordering_score"))
            ),
            "holdout_score_delta_vs_old": _rounded(
                _optional_float(holdout.get("proficiency_ordering_score"))
                - _metric_path(old_reference, "holdout", "proficiency_ordering_score")
            ),
            "calibration_score_delta_vs_old": _rounded(
                _optional_float(calibration.get("proficiency_ordering_score"))
                - _metric_path(old_reference, "calibration", "proficiency_ordering_score")
            ),
            "holdout_mae_delta_vs_old": _rounded(
                _metric_path(holdout, "normal_vocab", "metrics", "mae")
                - _metric_path(old_reference, "holdout", "normal_vocab", "metrics", "mae")
            ),
        },
    }


def apply_policy(
    policy: CorrectionPolicy,
    *,
    old_values: object,
    new_values: object,
    signal_groups: Mapping[str, object],
    candidate_states: Sequence[str],
    target_positions: object,
) -> tuple[object, dict[str, object]]:
    old = np.asarray(old_values, dtype=np.float32)
    new = np.asarray(new_values, dtype=np.float32)
    delta = new - old
    normal_mask = np.asarray([state == "normal_vocab" for state in candidate_states], dtype=bool)
    positive_mask = _group_mask(
        signal_groups,
        policy.positive_groups,
        threshold=policy.positive_threshold,
        length=len(old),
    )
    negative_mask = _group_mask(
        signal_groups,
        policy.negative_groups,
        threshold=policy.negative_threshold,
        length=len(old),
    )
    if policy.normal_vocab_only:
        positive_mask &= normal_mask
        negative_mask &= normal_mask
    positive_mask &= delta > 0.0
    negative_mask &= delta < 0.0
    correction = np.zeros_like(old)
    if policy.cap > 0.0 and policy.scale > 0.0:
        correction[positive_mask] = np.minimum(
            float(policy.cap),
            np.maximum(0.0, delta[positive_mask] * float(policy.scale)),
        )
        correction[negative_mask] = -np.minimum(
            float(policy.cap),
            np.maximum(0.0, -delta[negative_mask] * float(policy.scale)),
        )
    hybrid = np.clip(old + correction, 0.0, 1.0)
    if policy.normalization == "rerank":
        hybrid = _target_curve_normalize(hybrid, target_positions=target_positions)
    nonzero = np.abs(correction) > 1e-9
    positive = correction > 1e-9
    negative = correction < -1e-9
    return hybrid, {
        "changed_count": int(np.sum(nonzero)),
        "positive_changed_count": int(np.sum(positive)),
        "negative_changed_count": int(np.sum(negative)),
        "mean_abs_correction": _rounded(
            float(np.mean(np.abs(correction[nonzero]))) if np.any(nonzero) else 0.0
        ),
        "max_abs_correction": _rounded(
            float(np.max(np.abs(correction))) if len(correction) else 0.0
        ),
    }


def _group_mask(
    signal_groups: Mapping[str, object],
    groups: Sequence[str],
    *,
    threshold: float,
    length: int,
) -> object:
    if not groups:
        return np.zeros(length, dtype=bool)
    mask = np.ones(length, dtype=bool)
    for group in groups:
        if group == "all":
            group_mask = np.ones(length, dtype=bool)
        elif "|" in group:
            group_mask = np.zeros(length, dtype=bool)
            for part in group.split("|"):
                group_mask |= np.asarray(signal_groups[part], dtype=np.float32) >= threshold
        else:
            group_mask = np.asarray(signal_groups[group], dtype=np.float32) >= threshold
        mask &= group_mask
    return mask


def _signal_group_matrix(component_context: object) -> dict[str, object]:
    feature_lookup = {
        str(name): index for index, name in enumerate(component_context.component_names)
    }
    result = {}
    for group, signals in SIGNAL_GROUPS.items():
        columns = [feature_lookup[name] for name in signals if name in feature_lookup]
        if not columns:
            result[group] = np.zeros(len(component_context.lemmas), dtype=np.float32)
            continue
        values = np.asarray(component_context.component_values[:, columns], dtype=np.float32)
        present = np.asarray(component_context.component_present[:, columns], dtype=bool)
        result[group] = np.max(np.where(present, values, 0.0), axis=1)
    return result


def _reference_reports(
    *,
    old_values: object,
    new_values: object,
    old_record: Mapping[str, object],
    new_row: Mapping[str, object],
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
    calibration_context: object,
    holdout_context: object,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, object]:
    calibration = _proficiency_dataset_report(
        calibration_context,
        _observed_for_context(values, calibration_context),
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout = _proficiency_dataset_report(
        holdout_context,
        _observed_for_context(values, holdout_context),
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    return {
        "candidate_id": candidate_id,
        "source": source,
        "calibration": calibration,
        "holdout": holdout,
    }


def _guardrails(
    calibration: Mapping[str, object],
    old_calibration: Mapping[str, object],
) -> dict[str, object]:
    score_delta = _optional_float(calibration.get("proficiency_ordering_score")) - _optional_float(
        old_calibration.get("proficiency_ordering_score")
    )
    mae_delta = _metric_path(calibration, "normal_vocab", "metrics", "mae") - _metric_path(
        old_calibration, "normal_vocab", "metrics", "mae"
    )
    pairwise_delta = _metric_path(
        calibration, "normal_vocab", "scores", "pairwise_order_score"
    ) - _metric_path(old_calibration, "normal_vocab", "scores", "pairwise_order_score")
    window_delta = _metric_path(
        calibration, "frontier_windows", "average_window_score"
    ) - _metric_path(old_calibration, "frontier_windows", "average_window_score")
    return {
        "pass": bool(
            score_delta >= -0.01
            and mae_delta <= 0.01
            and pairwise_delta >= -0.02
            and window_delta >= -0.05
        ),
        "score_delta_vs_old": _rounded(score_delta),
        "mae_delta_vs_old": _rounded(mae_delta),
        "pairwise_delta_vs_old": _rounded(pairwise_delta),
        "window_delta_vs_old": _rounded(window_delta),
    }


def _guardrails_pass(row: Mapping[str, object]) -> bool:
    return bool(_mapping(row.get("guardrails")).get("pass"))


def _is_targeted_policy(row: Mapping[str, object]) -> bool:
    candidate_id = str(row.get("candidate_id") or "")
    return not candidate_id.startswith(("global_delta_blend", "old_anchor"))


def _leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    limit: int,
    keep_order: bool = False,
) -> list[dict[str, object]]:
    ordered = (
        list(rows)
        if keep_order
        else sorted(
            rows,
            key=lambda row: _candidate_metric(row, dataset),
            reverse=True,
        )
    )
    return [_leaderboard_row(row, dataset=dataset) for row in ordered[:limit]]


def _leaderboard_row(row: Mapping[str, object], *, dataset: str) -> dict[str, object]:
    dataset_report = _mapping(row.get(dataset))
    normal = _mapping(dataset_report.get("normal_vocab"))
    normal_metrics = _mapping(normal.get("metrics"))
    normal_scores = _mapping(normal.get("scores"))
    windows = _mapping(dataset_report.get("frontier_windows"))
    generalization = _mapping(row.get("generalization"))
    correction = _mapping(row.get("correction_summary"))
    return {
        "candidate_id": row.get("candidate_id"),
        "score": dataset_report.get("proficiency_ordering_score"),
        "normal_vocab_mae": normal_metrics.get("mae"),
        "normal_vocab_pairwise": normal_scores.get("pairwise_order_score"),
        "window_quality": windows.get("average_window_score"),
        "changed_count": correction.get("changed_count"),
        "holdout_score_delta_vs_old": generalization.get("holdout_score_delta_vs_old"),
        "guardrails_pass": _mapping(row.get("guardrails")).get("pass"),
    }


def _primary_candidate(rows: Sequence[Mapping[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None
    return _leaderboard_row(rows[0], dataset="calibration") | {
        "holdout_score": _mapping(rows[0].get("holdout")).get("proficiency_ordering_score"),
        "holdout_score_delta_vs_old": _mapping(rows[0].get("generalization")).get(
            "holdout_score_delta_vs_old"
        ),
    }


def _candidate_metric(row: Mapping[str, object], dataset: str) -> float:
    return _optional_float(_mapping(row.get(dataset)).get("proficiency_ordering_score")) or -999.0


def _retained_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    retain_limit: int,
) -> list[Mapping[str, object]]:
    by_id = {}
    for row in sorted(
        candidates,
        key=lambda item: _candidate_metric(item, "calibration"),
        reverse=True,
    )[:retain_limit]:
        by_id[str(row.get("candidate_id"))] = row
    for row in sorted(
        candidates,
        key=lambda item: _candidate_metric(item, "holdout"),
        reverse=True,
    )[:retain_limit]:
        by_id[str(row.get("candidate_id"))] = row
    for row in candidates:
        if str(row.get("candidate_id")).startswith("old_anchor"):
            by_id[str(row.get("candidate_id"))] = row
    return list(by_id.values())


def render_markdown(report: Mapping[str, object]) -> str:
    models = _mapping(report.get("models"))
    old_model = _mapping(models.get("old_method"))
    new_model = _mapping(models.get("new_method"))
    lines = [
        "# en-ja Learner Difficulty Bounded Hybrid Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Old anchor: `{_escape(old_model.get('model_id'))}`",
        f"- New delta source: `{_escape(new_model.get('model_id'))}`",
        f"- Policy count: `{_escape(_mapping(report.get('parameters')).get('policy_count'))}`",
        "",
    ]
    lines.extend(_reference_section(report))
    lines.extend(_primary_section(report))
    lines.extend(
        _leaderboard_section(report, "calibration_proficiency_ordering", "Calibration Selector")
    )
    lines.extend(
        _leaderboard_section(
            report, "calibration_guardrail_passing", "Calibration Guardrail-Passing"
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "targeted_calibration_guardrail_passing",
            "Targeted Calibration Guardrail-Passing",
        )
    )
    lines.extend(
        _leaderboard_section(
            report, "narrow_calibration_guardrail_passing", "Narrow Calibration Guardrail-Passing"
        )
    )
    lines.extend(
        _leaderboard_section(
            report, "holdout_of_calibration_winners", "Holdout Of Calibration Winners"
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "holdout_of_targeted_calibration_winners",
            "Holdout Of Targeted Calibration Winners",
        )
    )
    lines.extend(_leaderboard_section(report, "holdout_oracle", "Holdout Oracle"))
    lines.extend(_leaderboard_section(report, "targeted_holdout_oracle", "Targeted Holdout Oracle"))
    return "\n".join(lines).rstrip() + "\n"


def _reference_section(report: Mapping[str, object]) -> list[str]:
    refs = _mapping(report.get("reference_candidates"))
    lines = [
        "## References",
        "",
        "| Candidate | Calibration score | Calibration MAE | Holdout score | Holdout MAE |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for key in ("old_method", "new_method"):
        row = _mapping(refs.get(key))
        lines.append(
            f"| `{_escape(key)}` | "
            f"`{_escape(_mapping(row.get('calibration')).get('proficiency_ordering_score'))}` | "
            f"`{_escape(_metric_path(row, 'calibration', 'normal_vocab', 'metrics', 'mae'))}` | "
            f"`{_escape(_mapping(row.get('holdout')).get('proficiency_ordering_score'))}` | "
            f"`{_escape(_metric_path(row, 'holdout', 'normal_vocab', 'metrics', 'mae'))}` |"
        )
    lines.append("")
    return lines


def _primary_section(report: Mapping[str, object]) -> list[str]:
    primary = _mapping(report.get("primary_candidates"))
    lines = [
        "## Primary Candidates",
        "",
        "| Selector | Candidate | Calibration score | Holdout score | Holdout delta vs old | Changed | Guardrails |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for key in (
        "calibration_selector",
        "guardrail_selector",
        "targeted_guardrail_selector",
        "narrow_guardrail_selector",
        "holdout_oracle",
        "targeted_holdout_oracle",
    ):
        row = _mapping(primary.get(key))
        lines.append(
            f"| `{_escape(key)}` | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('score'))}` | "
            f"`{_escape(row.get('holdout_score'))}` | "
            f"`{_escape(row.get('holdout_score_delta_vs_old'))}` | "
            f"`{_escape(row.get('changed_count'))}` | "
            f"`{_escape(row.get('guardrails_pass'))}` |"
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
        "| Candidate | Score | MAE | Pairwise | Window | Changed | Holdout delta vs old | Guardrails |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("|  |  |  |  |  |  |  |  |")
        lines.append("")
        return lines
    for row in rows:
        lines.append(
            f"| `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('score'))}` | "
            f"`{_escape(row.get('normal_vocab_mae'))}` | "
            f"`{_escape(row.get('normal_vocab_pairwise'))}` | "
            f"`{_escape(row.get('window_quality'))}` | "
            f"`{_escape(row.get('changed_count'))}` | "
            f"`{_escape(row.get('holdout_score_delta_vs_old'))}` | "
            f"`{_escape(row.get('guardrails_pass'))}` |"
        )
    lines.append("")
    return lines


def _policy_dict(policy: CorrectionPolicy) -> dict[str, object]:
    return {
        "positive_groups": list(policy.positive_groups),
        "negative_groups": list(policy.negative_groups),
        "positive_threshold": _rounded(policy.positive_threshold),
        "negative_threshold": _rounded(policy.negative_threshold),
        "scale": _rounded(policy.scale),
        "cap": _rounded(policy.cap),
        "normalization": policy.normalization,
        "normal_vocab_only": policy.normal_vocab_only,
    }


def _dedupe_policies(
    policies: Sequence[CorrectionPolicy],
) -> list[CorrectionPolicy]:
    seen = set()
    result = []
    for policy in policies:
        if policy.policy_id in seen:
            continue
        seen.add(policy.policy_id)
        result.append(policy)
    return result


def _token(value: float) -> str:
    return f"{int(round(float(value) * 100)):03d}"


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
