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
    DEFAULT_TRACE_JSON,
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
from srs_learner_difficulty_proficiency_ordering_stability_en_ja import (  # noqa: E402
    DEFAULT_FOLD_COUNT,
    _fold_summary_rows,
    _stratified_fold_masks,
    _subset_context,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_structured_failure_groups_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_structured_failure_groups_en_ja_latest.md"
)
DEFAULT_ERROR_THRESHOLD = 0.20
DEFAULT_MIN_TRAIN_SUPPORT = 4
DEFAULT_MAX_CORRECTION_ABS = 0.18
DEFAULT_GROUP_LIMIT = 0
DEFAULT_RETAIN_LIMIT = 120
DEFAULT_LEADERBOARD_LIMIT = 20
NORMAL_VOCAB_STATES = frozenset({"normal_vocab"})
NARROW_FULL_VOCAB_LIMIT = 10_000
MEDIUM_FULL_VOCAB_LIMIT = 25_000


@dataclass(frozen=True)
class GroupTerm:
    signal: str
    min_value: float | None = None
    max_value: float | None = None


@dataclass(frozen=True)
class GroupSpec:
    group_id: str
    description: str
    terms: tuple[GroupTerm, ...]
    source: str = "source_signal"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Discover and fold-test source-backed structured residual failure "
            "groups for en-ja learner difficulty. This is a sidecar and does not "
            "change runtime behavior."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--old-score-key", default="balanced_score")
    parser.add_argument(
        "--proficiency-points",
        default=",".join(str(value) for value in DEFAULT_PROFICIENCY_POINTS),
    )
    parser.add_argument("--challenge-offset", type=float, default=DEFAULT_CHALLENGE_OFFSET)
    parser.add_argument("--window-sigma", type=float, default=DEFAULT_WINDOW_SIGMA)
    parser.add_argument("--window-top-k", type=int, default=DEFAULT_WINDOW_TOP_K)
    parser.add_argument("--fold-count", type=int, default=DEFAULT_FOLD_COUNT)
    parser.add_argument("--error-threshold", type=float, default=DEFAULT_ERROR_THRESHOLD)
    parser.add_argument("--min-train-support", type=int, default=DEFAULT_MIN_TRAIN_SUPPORT)
    parser.add_argument("--max-correction-abs", type=float, default=DEFAULT_MAX_CORRECTION_ABS)
    parser.add_argument("--group-limit", type=int, default=DEFAULT_GROUP_LIMIT)
    parser.add_argument("--retain-limit", type=int, default=DEFAULT_RETAIN_LIMIT)
    parser.add_argument("--leaderboard-limit", type=int, default=DEFAULT_LEADERBOARD_LIMIT)
    parser.add_argument("--detail-limit", type=int, default=16)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        holdout_json_path=_resolve_path(args.holdout_json),
        old_score_key=str(args.old_score_key),
        proficiency_points=_parse_float_csv(args.proficiency_points),
        challenge_offset=float(args.challenge_offset),
        window_sigma=max(1e-6, float(args.window_sigma)),
        window_top_k=max(1, int(args.window_top_k)),
        fold_count=max(2, int(args.fold_count)),
        error_threshold=max(0.01, float(args.error_threshold)),
        min_train_support=max(1, int(args.min_train_support)),
        max_correction_abs=max(0.01, float(args.max_correction_abs)),
        group_limit=max(0, int(args.group_limit)),
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
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    holdout_json_path: Path,
    old_score_key: str,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    fold_count: int,
    error_threshold: float,
    min_train_support: int,
    max_correction_abs: float,
    group_limit: int,
    retain_limit: int,
    leaderboard_limit: int,
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
    old_values = _normalized_values_for_trace_record(old_record, component_context)
    signal_arrays = _signal_arrays(component_context)
    group_specs = generate_group_specs(signal_arrays)
    if group_limit > 0:
        group_specs = group_specs[:group_limit]
    group_masks = {spec.group_id: _group_mask(spec, signal_arrays) for spec in group_specs}
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
    group_reports = [
        _group_report(
            spec,
            group_mask=group_masks[spec.group_id],
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
            min_train_support=min_train_support,
            max_correction_abs=max_correction_abs,
            detail_limit=detail_limit,
        )
        for spec in group_specs
    ]
    eligible = [row for row in group_reports if bool(row.get("eligible"))]
    selector_profiles = _selector_profiles(eligible, leaderboard_limit=leaderboard_limit)
    fold_training_selectors = {
        profile_id: _fold_training_selector_run(eligible, profile_id=profile_id)
        for profile_id in (
            "train_score",
            "train_score_mae_safe",
            "narrow_train_score_mae_safe",
        )
    }
    fold_training_selector = fold_training_selectors["train_score"]
    retained = _retained_groups(group_reports, limit=retain_limit)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "holdout_used_for_selection": False,
        "method": {
            "purpose": (
                "Identify source-observable residual groups where the old anchor "
                "model is directionally biased, then test bounded corrections on "
                "calibration folds before looking at holdout."
            ),
            "anchor_philosophy": (
                "The old model remains the default score. A group only proposes "
                "old_i + delta for rows matching a full-vocabulary source mask, "
                "where delta is fit from calibration residuals and clipped."
            ),
            "selector_rule": (
                "Group ranking uses calibration-fold validation. The fold-training "
                "selector chooses each fold's group from the other calibration folds "
                "only; holdout is reported afterward."
            ),
            "guardrail_profiles": {
                "validation_positive": (
                    "Eligible groups with positive mean validation delta and no "
                    "large negative validation fold."
                ),
                "validation_positive_mae_safe": (
                    "validation_positive plus non-negative mean validation normal-vocab "
                    "MAE reduction."
                ),
                "narrow_validation_positive_mae_safe": (
                    "validation_positive_mae_safe plus at most 10,000 full-vocabulary rows touched."
                ),
            },
            "target_curve_id": TARGET_CURVE_ID,
        },
        "parameters": {
            "old_score_key": old_score_key,
            "fold_count": int(fold_count),
            "error_threshold": round(float(error_threshold), 6),
            "min_train_support": int(min_train_support),
            "max_correction_abs": round(float(max_correction_abs), 6),
            "group_count": len(group_specs),
            "eligible_group_count": len(eligible),
            "selector_profile_counts": {
                profile_id: row.get("group_count") for profile_id, row in selector_profiles.items()
            },
            "group_limit": int(group_limit),
            "retain_limit": int(retain_limit),
            "leaderboard_limit": int(leaderboard_limit),
            "proficiency_points": [round(float(value), 6) for value in proficiency_points],
            "challenge_offset": round(float(challenge_offset), 6),
            "window_sigma": round(float(window_sigma), 6),
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
                "method_sample_compare": SCRIPT_DIR
                / "srs_learner_difficulty_method_sample_compare_en_ja.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
                "proficiency_ordering_stability": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_stability_en_ja.py",
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "folds": _fold_summary_rows(calibration_context, fold_masks),
        "reference_candidate": {
            "candidate_id": old_record.get("variant_id"),
            "source": "signal_sweep_trace",
            "selector": f"max:{old_score_key}",
            "scores": old_record.get("scores") or {},
            "weights": old_record.get("weights") or {},
        },
        "reference_reports": reference,
        "fold_training_selector": fold_training_selector,
        "fold_training_selectors": fold_training_selectors,
        "selector_profiles": selector_profiles,
        "primary_groups": {
            "fold_validation_selector": _group_summary(_top_group(eligible, "selector_score")),
            "validation_positive_mae_safe": _group_summary(
                _top_group(
                    _profile_rows(eligible, "validation_positive_mae_safe"),
                    "profile_score_validation_positive_mae_safe",
                )
            ),
            "narrow_validation_positive_mae_safe": _group_summary(
                _top_group(
                    _profile_rows(eligible, "narrow_validation_positive_mae_safe"),
                    "profile_score_narrow_validation_positive_mae_safe",
                )
            ),
            "holdout_after_calibration_fit": _group_summary(
                _top_group(eligible, "holdout_score_delta")
            ),
            "largest_holdout_mae_reduction": _group_summary(
                _top_group(eligible, "holdout_normal_vocab_mae_reduction")
            ),
        },
        "leaderboards": {
            "fold_validation_selector": _leaderboard(
                eligible,
                key="selector_score",
                limit=leaderboard_limit,
            ),
            "validation_positive_mae_safe": _leaderboard(
                _profile_rows(eligible, "validation_positive_mae_safe"),
                key="profile_score_validation_positive_mae_safe",
                limit=leaderboard_limit,
            ),
            "narrow_validation_positive_mae_safe": _leaderboard(
                _profile_rows(eligible, "narrow_validation_positive_mae_safe"),
                key="profile_score_narrow_validation_positive_mae_safe",
                limit=leaderboard_limit,
            ),
            "holdout_after_calibration_fit": _leaderboard(
                eligible,
                key="holdout_score_delta",
                limit=leaderboard_limit,
            ),
            "residual_enrichment": _leaderboard(
                eligible,
                key="residual_structure_score",
                limit=leaderboard_limit,
            ),
            "largest_holdout_mae_reduction": _leaderboard(
                eligible,
                key="holdout_normal_vocab_mae_reduction",
                limit=leaderboard_limit,
            ),
        },
        "group_results": retained,
    }


def generate_group_specs(signal_arrays: Mapping[str, object] | None = None) -> list[GroupSpec]:
    specs = _field_knowledge_group_specs()
    available = set(signal_arrays or {})
    for signal in _single_signal_candidates():
        if available and signal not in available:
            continue
        for threshold in (0.25, 0.50, 0.75, 0.90):
            specs.append(
                GroupSpec(
                    group_id=f"{signal}__gte{_token(threshold)}",
                    description=f"{signal} at least {threshold}.",
                    terms=(GroupTerm(signal, min_value=threshold),),
                    source="single_signal_threshold",
                )
            )
    return _dedup_group_specs(specs)


def _field_knowledge_group_specs() -> list[GroupSpec]:
    return [
        GroupSpec(
            "common_kango_mid",
            "Kango rows with moderate kango signal and no common-priority penalty.",
            (
                GroupTerm("wtype_kango_risk", min_value=0.75),
                GroupTerm("kango_mid_signal", min_value=0.25, max_value=0.70),
                GroupTerm("kango_common_priority_risk", max_value=0.25),
            ),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "kango_priority",
            "Kango rows with JMDict priority support.",
            (
                GroupTerm("wtype_kango_risk", min_value=0.75),
                GroupTerm("jmdict_priority", min_value=0.25),
            ),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "kango_not_extreme_frequency_tail",
            "Kango rows not pushed into the extreme corpus rarity tail.",
            (
                GroupTerm("wtype_kango_risk", min_value=0.75),
                GroupTerm("frequency", max_value=0.85),
            ),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "wago_written_or_rare_any",
            "Wago rows with written-form or rare-native pressure.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", min_value=0.25),
            ),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "wago_written_or_rare_moderate",
            "Wago rows with moderate written/rare pressure, excluding the extreme tail.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", min_value=0.25, max_value=0.60),
            ),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "wago_obscure_tail",
            "Wago rows in the clear rare or obscure written tail.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", min_value=0.60),
            ),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "rare_non_standard_reading",
            "Rows with rare or non-standard reading pressure.",
            (GroupTerm("reading_rarity_any", min_value=0.75),),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "non_standard_reading_any",
            "Rows with any non-standard reading signal.",
            (GroupTerm("non_standard_any", min_value=0.75),),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "curriculum_beginner_core",
            "Rows observed in beginner curriculum/JLPT core sources.",
            (GroupTerm("curriculum_core_any", min_value=0.75),),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "entity_or_acronym_any",
            "Rows with proper-name, entity, or acronym pressure.",
            (GroupTerm("entity_or_acronym_any", min_value=0.75),),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "loanword_or_foreign_priority",
            "Rows with loanword or foreign-priority evidence.",
            (GroupTerm("loanword_any", min_value=0.75),),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "extreme_frequency_tail",
            "Rows in the extreme frequency rarity tail.",
            (GroupTerm("frequency", min_value=0.90),),
            source="field_knowledge_composite",
        ),
        GroupSpec(
            "rare_wago_with_nonstandard_reading",
            "Rare native rows that also have non-standard reading pressure.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", min_value=0.50),
                GroupTerm("non_standard_any", min_value=0.50),
            ),
            source="field_knowledge_interaction",
        ),
        GroupSpec(
            "written_burden_kango",
            "Kango rows with high written-form burden.",
            (
                GroupTerm("wtype_kango_risk", min_value=0.75),
                GroupTerm("max_written_form_burden", min_value=0.70),
            ),
            source="field_knowledge_interaction",
        ),
    ]


def _single_signal_candidates() -> tuple[str, ...]:
    return (
        "frequency",
        "frequency_unranked_rare_risk",
        "frequency_unranked_tail_risk",
        "frequency_tail80",
        "frequency_tail90",
        "jlpt_vocab_beginner_core",
        "lesson_vocab_beginner_core",
        "jmdict_priority",
        "jmdict_marked_usage_risk",
        "jmdict_register_marked_risk",
        "jmdict_search_only_form_risk",
        "jmdict_abbreviation_risk",
        "jmdict_kana_preferred_risk",
        "named_entity_risk",
        "candidate_deprioritized_named_entity_risk",
        "candidate_deprioritized_named_frequency_risk",
        "problem_class_proper_risk",
        "proper_acronym_entity_risk",
        "news_abbreviation_entity_risk",
        "wtype_kango_risk",
        "kango_mid_signal",
        "kango_common_priority_risk",
        "sahen_kango_risk",
        "wtype_wago_ease",
        "rare_wago_tail_risk",
        "rare_wago_risk",
        "rare_wago_written_risk",
        "written_wago_tail_risk",
        "rare_wago_obscure_written_risk",
        "non_standard_reading_risk",
        "rare_non_standard_reading_risk",
        "written_form_burden",
        "max_written_form_burden",
        "kanji_burden",
        "max_kanji_burden",
        "kanji_curriculum_missing_risk",
        "wtype_gairaigo_risk",
        "jmdict_loanword_source_risk",
        "jmdict_foreign_priority_risk",
    )


def _group_report(
    spec: GroupSpec,
    *,
    group_mask: object,
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
    min_train_support: int,
    max_correction_abs: float,
    detail_limit: int,
) -> dict[str, object]:
    calibration_residual = _residual_profile(
        calibration_context,
        old_values,
        group_mask=group_mask,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    holdout_residual = _residual_profile(
        holdout_context,
        old_values,
        group_mask=group_mask,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    calibration_group_mask = _context_group_mask(calibration_context, group_mask)
    full_delta = _bounded_residual_delta(
        calibration_context,
        old_values,
        calibration_group_mask,
        max_abs=max_correction_abs,
        min_support=min_train_support,
    )
    full_adjusted = _apply_group_delta(old_values, group_mask, full_delta or 0.0)
    calibration_report = _dataset_report(
        calibration_context,
        full_adjusted,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    holdout_report = _dataset_report(
        holdout_context,
        full_adjusted,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    fold_reports = [
        _fold_correction_report(
            fold_index=index,
            spec=spec,
            group_mask=group_mask,
            old_values=old_values,
            train_context=train_context,
            validation_context=validation_contexts[index],
            holdout_context=holdout_context,
            reference=reference,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            min_train_support=min_train_support,
            max_correction_abs=max_correction_abs,
            detail_limit=detail_limit,
        )
        for index, train_context in enumerate(train_contexts)
    ]
    fold_summary = _fold_delta_summary(fold_reports)
    structure_score = _residual_structure_score(calibration_residual)
    selector_score = _selector_score(fold_summary, structure_score)
    calibration_score_delta = _score_delta(
        calibration_report,
        _mapping(reference.get("calibration")),
    )
    holdout_score_delta = _score_delta(
        holdout_report,
        _mapping(reference.get("holdout")),
    )
    holdout_mae_reduction = _normal_vocab_mae_reduction(
        before=_mapping(reference.get("holdout")),
        after=holdout_report,
    )
    selected_count = int(np.asarray(group_mask, dtype=bool).sum())
    scope = _scope_for_count(selected_count)
    eligible = (
        bool(full_delta is not None)
        and int(calibration_residual["selected_count"]) >= min_train_support
        and float(calibration_residual.get("sign_consistency") or 0.0) >= 0.55
    )
    return {
        "group_id": spec.group_id,
        "description": spec.description,
        "source": spec.source,
        "terms": [_term_dict(term) for term in spec.terms],
        "eligible": eligible,
        "full_vocab_count": selected_count,
        "scope": scope,
        "calibration_residual": calibration_residual,
        "holdout_residual": holdout_residual,
        "calibration_fit_delta": _rounded(full_delta),
        "fold_summary": fold_summary,
        "selector_score": _rounded(selector_score),
        "residual_structure_score": _rounded(structure_score),
        "calibration": _compact_dataset_report(calibration_report),
        "holdout": _compact_dataset_report(holdout_report),
        "calibration_score_delta": _rounded(calibration_score_delta),
        "holdout_score_delta": _rounded(holdout_score_delta),
        "holdout_normal_vocab_mae_reduction": _rounded(holdout_mae_reduction),
        "guardrails": _guardrail_flags(
            eligible=eligible,
            full_vocab_count=selected_count,
            calibration_residual=calibration_residual,
            fold_summary=fold_summary,
        ),
        "profile_score_validation_positive": _rounded(
            _profile_score_by_id(
                "validation_positive",
                fold_summary=fold_summary,
                full_vocab_count=selected_count,
            )
        ),
        "profile_score_validation_positive_mae_safe": _rounded(
            _profile_score_by_id(
                "validation_positive_mae_safe",
                fold_summary=fold_summary,
                full_vocab_count=selected_count,
            )
        ),
        "profile_score_narrow_validation_positive_mae_safe": _rounded(
            _profile_score_by_id(
                "narrow_validation_positive_mae_safe",
                fold_summary=fold_summary,
                full_vocab_count=selected_count,
            )
        ),
        "folds": fold_reports,
    }


def _fold_correction_report(
    *,
    fold_index: int,
    spec: GroupSpec,
    group_mask: object,
    old_values: object,
    train_context: object,
    validation_context: object,
    holdout_context: object,
    reference: Mapping[str, object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    min_train_support: int,
    max_correction_abs: float,
    detail_limit: int,
) -> dict[str, object]:
    train_group_mask = _context_group_mask(train_context, group_mask)
    delta = _bounded_residual_delta(
        train_context,
        old_values,
        train_group_mask,
        max_abs=max_correction_abs,
        min_support=min_train_support,
    )
    adjusted = _apply_group_delta(old_values, group_mask, delta or 0.0)
    train_report = _dataset_report(
        train_context,
        adjusted,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    validation_report = _dataset_report(
        validation_context,
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
    train_support = int(train_group_mask.sum())
    validation_support = int(_context_group_mask(validation_context, group_mask).sum())
    return {
        "fold": fold_index + 1,
        "group_id": spec.group_id,
        "delta": _rounded(delta),
        "train_support": train_support,
        "validation_support": validation_support,
        "train_score_delta": _rounded(
            _score_delta(train_report, _mapping_rows(reference.get("train_folds"))[fold_index])
        ),
        "validation_score_delta": _rounded(
            _score_delta(
                validation_report,
                _mapping_rows(reference.get("validation_folds"))[fold_index],
            )
        ),
        "holdout_score_delta": _rounded(
            _score_delta(holdout_report, _mapping(reference.get("holdout")))
        ),
        "train_normal_vocab_mae_reduction": _rounded(
            _normal_vocab_mae_reduction(
                before=_mapping_rows(reference.get("train_folds"))[fold_index],
                after=train_report,
            )
        ),
        "validation_normal_vocab_mae_reduction": _rounded(
            _normal_vocab_mae_reduction(
                before=_mapping_rows(reference.get("validation_folds"))[fold_index],
                after=validation_report,
            )
        ),
        "holdout_normal_vocab_mae_reduction": _rounded(
            _normal_vocab_mae_reduction(
                before=_mapping(reference.get("holdout")),
                after=holdout_report,
            )
        ),
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


def _compact_dataset_report(report: Mapping[str, object]) -> dict[str, object]:
    normal_vocab = _mapping(report.get("normal_vocab"))
    normal_metrics = _mapping(normal_vocab.get("metrics"))
    normal_scores = _mapping(normal_vocab.get("scores"))
    windows = _mapping(report.get("frontier_windows"))
    return {
        "proficiency_ordering_score": report.get("proficiency_ordering_score"),
        "normal_vocab_mae": normal_metrics.get("mae"),
        "normal_vocab_pairwise": normal_scores.get("pairwise_order_score"),
        "normal_vocab_bucket": normal_scores.get("bucket_accuracy_score"),
        "window_quality": windows.get("average_window_score"),
    }


def _residual_profile(
    context: object,
    values: object,
    *,
    group_mask: object,
    error_threshold: float,
    detail_limit: int,
) -> dict[str, object]:
    observed = np.asarray(_observed_for_context(values, context), dtype=np.float32)
    expected = np.asarray(context.expected_values, dtype=np.float32)
    selected = _context_group_mask(context, group_mask)
    numeric = np.isfinite(observed) & np.isfinite(expected)
    residuals = expected - observed
    selected_numeric = selected & numeric
    rows = _residual_examples(
        context,
        expected=expected,
        observed=observed,
        residuals=residuals,
        selected=selected_numeric,
        limit=detail_limit,
    )
    all_large = numeric & (np.abs(residuals) >= error_threshold)
    all_too_high = numeric & (residuals <= -error_threshold)
    all_too_low = numeric & (residuals >= error_threshold)
    selected_residuals = residuals[selected_numeric]
    positive_fraction = _fraction(selected_residuals > 0.0)
    negative_fraction = _fraction(selected_residuals < 0.0)
    dominant_direction = "too_easy" if positive_fraction >= negative_fraction else "too_hard"
    sign_consistency = max(positive_fraction, negative_fraction)
    return {
        "row_count": int(numeric.sum()),
        "selected_count": int(selected_numeric.sum()),
        "selected_fraction": _rounded(_ratio(selected_numeric.sum(), numeric.sum())),
        "mean_residual": _rounded(_mean(selected_residuals)),
        "median_residual": _rounded(_median(selected_residuals)),
        "mean_absolute_error": _rounded(_mean(np.abs(selected_residuals))),
        "dominant_direction": dominant_direction if len(selected_residuals) else "",
        "sign_consistency": _rounded(sign_consistency),
        "large_error": _enrichment(
            selected=selected_numeric,
            positive=all_large,
        ),
        "too_high": _enrichment(
            selected=selected_numeric,
            positive=all_too_high,
        ),
        "too_low": _enrichment(
            selected=selected_numeric,
            positive=all_too_low,
        ),
        "examples": rows,
    }


def _residual_examples(
    context: object,
    *,
    expected: object,
    observed: object,
    residuals: object,
    selected: object,
    limit: int,
) -> list[dict[str, object]]:
    expected_array = np.asarray(expected, dtype=np.float32)
    observed_array = np.asarray(observed, dtype=np.float32)
    residual_array = np.asarray(residuals, dtype=np.float32)
    selected_array = np.asarray(selected, dtype=bool)
    indices = np.where(selected_array)[0]
    sorted_indices = sorted(
        indices,
        key=lambda index: abs(float(residual_array[index])),
        reverse=True,
    )[:limit]
    return [
        {
            "label": context.labels[index],
            "expected": _rounded(float(expected_array[index])),
            "observed": _rounded(float(observed_array[index])),
            "residual": _rounded(float(residual_array[index])),
            "absolute_error": _rounded(abs(float(residual_array[index]))),
            "direction": ("too_easy" if float(residual_array[index]) > 0.0 else "too_hard"),
        }
        for index in sorted_indices
    ]


def _enrichment(*, selected: object, positive: object) -> dict[str, object]:
    selected_array = np.asarray(selected, dtype=bool)
    positive_array = np.asarray(positive, dtype=bool)
    selected_count = int(selected_array.sum())
    positive_count = int(positive_array.sum())
    true_positive = int((selected_array & positive_array).sum())
    precision = _ratio(true_positive, selected_count)
    recall = _ratio(true_positive, positive_count)
    base_rate = _ratio(positive_count, len(selected_array))
    lift = (precision / base_rate) if base_rate and precision is not None else None
    return {
        "selected_positive_count": true_positive,
        "positive_count": positive_count,
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "lift": _rounded(lift),
    }


def _fold_delta_summary(folds: Sequence[Mapping[str, object]]) -> dict[str, object]:
    validation_deltas = _finite_values(row.get("validation_score_delta") for row in folds)
    train_deltas = _finite_values(row.get("train_score_delta") for row in folds)
    holdout_deltas = _finite_values(row.get("holdout_score_delta") for row in folds)
    validation_mae = _finite_values(
        row.get("validation_normal_vocab_mae_reduction") for row in folds
    )
    return {
        "mean_train_score_delta": _rounded(_mean(train_deltas)),
        "mean_validation_score_delta": _rounded(_mean(validation_deltas)),
        "min_validation_score_delta": _rounded(
            min(validation_deltas) if validation_deltas else None
        ),
        "validation_score_delta_std": _rounded(_std(validation_deltas)),
        "mean_holdout_score_delta": _rounded(_mean(holdout_deltas)),
        "mean_validation_normal_vocab_mae_reduction": _rounded(_mean(validation_mae)),
        "valid_fold_count": len(validation_deltas),
    }


def _selector_profiles(
    groups: Sequence[Mapping[str, object]],
    *,
    leaderboard_limit: int,
) -> dict[str, object]:
    profiles: dict[str, object] = {}
    for profile_id in (
        "validation_positive",
        "validation_positive_mae_safe",
        "narrow_validation_positive_mae_safe",
    ):
        rows = _profile_rows(groups, profile_id)
        profiles[profile_id] = {
            "group_count": len(rows),
            "leaderboard": _leaderboard(
                rows,
                key=f"profile_score_{profile_id}",
                limit=leaderboard_limit,
            ),
            "top_group": _group_summary(_top_group(rows, f"profile_score_{profile_id}")),
        }
    return profiles


def _profile_rows(
    groups: Sequence[Mapping[str, object]],
    profile_id: str,
) -> list[Mapping[str, object]]:
    return [group for group in groups if _passes_profile(group, profile_id)]


def _passes_profile(group: Mapping[str, object], profile_id: str) -> bool:
    if not bool(group.get("eligible")):
        return False
    fold_summary = _mapping(group.get("fold_summary"))
    if profile_id in {
        "validation_positive",
        "validation_positive_mae_safe",
        "narrow_validation_positive_mae_safe",
    }:
        if (
            _float_or(
                fold_summary.get("mean_validation_score_delta"),
                -999.0,
            )
            <= 0.0
        ):
            return False
        if (
            _float_or(
                fold_summary.get("min_validation_score_delta"),
                -999.0,
            )
            < -0.001
        ):
            return False
        if int(fold_summary.get("valid_fold_count") or 0) < 5:
            return False
    if profile_id in {
        "validation_positive_mae_safe",
        "narrow_validation_positive_mae_safe",
    }:
        if (
            _float_or(
                fold_summary.get("mean_validation_normal_vocab_mae_reduction"),
                -999.0,
            )
            < 0.0
        ):
            return False
    if profile_id == "narrow_validation_positive_mae_safe":
        if int(group.get("full_vocab_count") or 0) > NARROW_FULL_VOCAB_LIMIT:
            return False
    return True


def _guardrail_flags(
    *,
    eligible: bool,
    full_vocab_count: int,
    calibration_residual: Mapping[str, object],
    fold_summary: Mapping[str, object],
) -> dict[str, object]:
    mean_validation = _optional_float(fold_summary.get("mean_validation_score_delta"))
    min_validation = _optional_float(fold_summary.get("min_validation_score_delta"))
    validation_mae = _optional_float(fold_summary.get("mean_validation_normal_vocab_mae_reduction"))
    sign_consistency = _optional_float(calibration_residual.get("sign_consistency"))
    return {
        "eligible": bool(eligible),
        "scope": _scope_for_count(full_vocab_count),
        "full_vocab_count": int(full_vocab_count),
        "narrow_scope": int(full_vocab_count) <= NARROW_FULL_VOCAB_LIMIT,
        "medium_or_narrow_scope": int(full_vocab_count) <= MEDIUM_FULL_VOCAB_LIMIT,
        "mean_validation_positive": _float_or(mean_validation, -999.0) > 0.0,
        "min_validation_tolerable": _float_or(min_validation, -999.0) >= -0.001,
        "validation_mae_safe": _float_or(validation_mae, -999.0) >= 0.0,
        "sign_consistency_065": _float_or(sign_consistency, 0.0) >= 0.65,
    }


def _scope_for_count(full_vocab_count: int) -> str:
    if int(full_vocab_count) <= NARROW_FULL_VOCAB_LIMIT:
        return "narrow"
    if int(full_vocab_count) <= MEDIUM_FULL_VOCAB_LIMIT:
        return "medium"
    return "broad"


def _profile_score_by_id(
    profile_id: str,
    *,
    fold_summary: Mapping[str, object],
    full_vocab_count: int,
) -> float | None:
    mean_delta = _optional_float(fold_summary.get("mean_validation_score_delta"))
    min_delta = _optional_float(fold_summary.get("min_validation_score_delta"))
    std_delta = _optional_float(fold_summary.get("validation_score_delta_std")) or 0.0
    mae_reduction = (
        _optional_float(fold_summary.get("mean_validation_normal_vocab_mae_reduction")) or 0.0
    )
    if mean_delta is None or min_delta is None:
        return None
    breadth_penalty = _breadth_penalty(full_vocab_count)
    score = mean_delta + (0.30 * min_delta) - (0.20 * std_delta)
    if profile_id in {
        "validation_positive_mae_safe",
        "narrow_validation_positive_mae_safe",
    }:
        score += 0.20 * max(0.0, mae_reduction)
    score -= breadth_penalty
    return score


def _breadth_penalty(full_vocab_count: int) -> float:
    if int(full_vocab_count) <= NARROW_FULL_VOCAB_LIMIT:
        return 0.0
    if int(full_vocab_count) <= MEDIUM_FULL_VOCAB_LIMIT:
        return 0.001
    return 0.003


def _fold_training_selector_run(
    groups: Sequence[Mapping[str, object]],
    *,
    profile_id: str,
) -> dict[str, object]:
    events = _fold_training_selector_events(groups, profile_id=profile_id)
    validation_deltas = _finite_values(row.get("validation_score_delta") for row in events)
    holdout_deltas = _finite_values(row.get("holdout_score_delta") for row in events)
    return {
        "profile_id": profile_id,
        "selection_rule": _fold_training_selection_rule(profile_id),
        "event_count": len(events),
        "mean_validation_score_delta": _rounded(_mean(validation_deltas)),
        "mean_holdout_score_delta": _rounded(_mean(holdout_deltas)),
        "selection_frequency": _fold_training_selection_frequency(events),
        "events": events,
    }


def _fold_training_selector_events(
    groups: Sequence[Mapping[str, object]],
    *,
    profile_id: str = "train_score",
) -> list[dict[str, object]]:
    fold_numbers = sorted(
        {
            int(fold.get("fold") or 0)
            for group in groups
            for fold in _mapping_rows(group.get("folds"))
            if int(fold.get("fold") or 0) > 0
        }
    )
    events: list[dict[str, object]] = []
    for fold_number in fold_numbers:
        candidates = []
        for group in groups:
            if not _passes_fold_training_static_profile(group, profile_id):
                continue
            fold = next(
                (
                    row
                    for row in _mapping_rows(group.get("folds"))
                    if int(row.get("fold") or 0) == fold_number
                ),
                None,
            )
            if fold is None:
                continue
            train_delta = _optional_float(fold.get("train_score_delta"))
            if train_delta is None:
                continue
            if not _passes_fold_training_fold_profile(fold, profile_id):
                continue
            candidates.append((_fold_training_profile_score(group, fold, profile_id), group, fold))
        if not candidates:
            continue
        candidates.sort(
            key=lambda item: (
                item[0],
                _optional_float(item[1].get("residual_structure_score")) or -999.0,
                -abs(_optional_float(item[2].get("delta")) or 0.0),
            ),
            reverse=True,
        )
        _, group, fold = candidates[0]
        events.append(
            {
                "fold": fold_number,
                "group_id": group.get("group_id"),
                "source": group.get("source"),
                "delta": fold.get("delta"),
                "train_score_delta": fold.get("train_score_delta"),
                "validation_score_delta": fold.get("validation_score_delta"),
                "holdout_score_delta": fold.get("holdout_score_delta"),
                "validation_normal_vocab_mae_reduction": fold.get(
                    "validation_normal_vocab_mae_reduction"
                ),
                "holdout_normal_vocab_mae_reduction": fold.get(
                    "holdout_normal_vocab_mae_reduction"
                ),
            }
        )
    return events


def _fold_training_selection_rule(profile_id: str) -> str:
    if profile_id == "train_score_mae_safe":
        return (
            "per fold, require positive train delta and non-negative train MAE "
            "reduction, then rank by train delta plus MAE reduction"
        )
    if profile_id == "narrow_train_score_mae_safe":
        return (
            "same as train_score_mae_safe, but only groups touching at most "
            "10,000 full-vocabulary rows"
        )
    return "max train_score_delta among eligible groups, per fold"


def _passes_fold_training_static_profile(
    group: Mapping[str, object],
    profile_id: str,
) -> bool:
    if profile_id == "narrow_train_score_mae_safe":
        return int(group.get("full_vocab_count") or 0) <= NARROW_FULL_VOCAB_LIMIT
    return True


def _passes_fold_training_fold_profile(
    fold: Mapping[str, object],
    profile_id: str,
) -> bool:
    if profile_id in {"train_score_mae_safe", "narrow_train_score_mae_safe"}:
        if _float_or(fold.get("train_score_delta"), -999.0) <= 0.0:
            return False
        if _float_or(fold.get("train_normal_vocab_mae_reduction"), -999.0) < 0.0:
            return False
    return True


def _fold_training_profile_score(
    group: Mapping[str, object],
    fold: Mapping[str, object],
    profile_id: str,
) -> float:
    train_delta = _optional_float(fold.get("train_score_delta")) or -999.0
    if profile_id in {"train_score_mae_safe", "narrow_train_score_mae_safe"}:
        train_mae = _optional_float(fold.get("train_normal_vocab_mae_reduction")) or 0.0
        return (
            train_delta
            + (0.20 * max(0.0, train_mae))
            - _breadth_penalty(int(group.get("full_vocab_count") or 0))
        )
    return train_delta


def _fold_training_selection_frequency(
    events: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    groups: dict[str, list[Mapping[str, object]]] = {}
    for event in events:
        groups.setdefault(str(event.get("group_id") or ""), []).append(event)
    rows = []
    for group_id, items in groups.items():
        rows.append(
            {
                "group_id": group_id,
                "selected_fold_count": len(items),
                "selected_folds": ",".join(str(item.get("fold")) for item in items),
                "mean_validation_score_delta": _rounded(
                    _mean(item.get("validation_score_delta") for item in items)
                ),
                "mean_holdout_score_delta": _rounded(
                    _mean(item.get("holdout_score_delta") for item in items)
                ),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            int(row.get("selected_fold_count") or 0),
            _optional_float(row.get("mean_validation_score_delta")) or -999.0,
        ),
        reverse=True,
    )


def _selector_score(
    fold_summary: Mapping[str, object],
    _structure_score: float | None,
) -> float | None:
    mean_delta = _optional_float(fold_summary.get("mean_validation_score_delta"))
    min_delta = _optional_float(fold_summary.get("min_validation_score_delta"))
    std_delta = _optional_float(fold_summary.get("validation_score_delta_std")) or 0.0
    mae_reduction = (
        _optional_float(fold_summary.get("mean_validation_normal_vocab_mae_reduction")) or 0.0
    )
    if mean_delta is None or min_delta is None:
        return None
    return mean_delta + (0.25 * min_delta) - (0.20 * std_delta) + (0.05 * max(0.0, mae_reduction))


def _residual_structure_score(profile: Mapping[str, object]) -> float | None:
    selected_count = int(profile.get("selected_count") or 0)
    if selected_count <= 0:
        return None
    large = _mapping(profile.get("large_error"))
    too_high = _mapping(profile.get("too_high"))
    too_low = _mapping(profile.get("too_low"))
    large_lift = _optional_float(large.get("lift")) or 0.0
    directional_lift = max(
        _optional_float(too_high.get("lift")) or 0.0,
        _optional_float(too_low.get("lift")) or 0.0,
    )
    sign_consistency = _optional_float(profile.get("sign_consistency")) or 0.0
    support_weight = min(1.0, selected_count / 12.0)
    return support_weight * (
        (0.35 * large_lift) + (0.35 * directional_lift) + (0.30 * sign_consistency)
    )


def _bounded_residual_delta(
    context: object,
    values: object,
    context_group_mask: object,
    *,
    max_abs: float,
    min_support: int,
) -> float | None:
    observed = np.asarray(_observed_for_context(values, context), dtype=np.float32)
    expected = np.asarray(context.expected_values, dtype=np.float32)
    selected = np.asarray(context_group_mask, dtype=bool)
    numeric = selected & np.isfinite(observed) & np.isfinite(expected)
    if int(numeric.sum()) < min_support:
        return None
    residuals = expected[numeric] - observed[numeric]
    median = float(np.median(residuals))
    return float(np.clip(median, -max_abs, max_abs))


def _apply_group_delta(values: object, group_mask: object, delta: float) -> object:
    adjusted = np.asarray(values, dtype=np.float32).copy()
    selected = np.asarray(group_mask, dtype=bool)
    adjusted[selected] = np.clip(adjusted[selected] + float(delta), 0.0, 1.0)
    return adjusted


def _signal_arrays(context: object) -> dict[str, object]:
    values = np.asarray(context.component_values, dtype=np.float32)
    present = np.asarray(context.component_present, dtype=bool)
    arrays: dict[str, object] = {}
    for index, name in enumerate(context.component_names):
        arrays[name] = np.where(present[:, index], values[:, index], 0.0)
    arrays["wago_written_or_rare"] = _max_signal(
        arrays,
        (
            "rare_wago_tail_risk",
            "written_wago_tail_risk",
            "rare_wago_obscure_written_risk",
        ),
        count=len(context.lemmas),
    )
    arrays["reading_rarity_any"] = _max_signal(
        arrays,
        ("rare_non_standard_reading_risk", "rare_wago_non_standard_reading_risk"),
        count=len(context.lemmas),
    )
    arrays["non_standard_any"] = _max_signal(
        arrays,
        ("non_standard_reading_risk", "reading_rarity_any"),
        count=len(context.lemmas),
    )
    arrays["entity_or_acronym_any"] = _max_signal(
        arrays,
        (
            "named_entity_risk",
            "candidate_deprioritized_named_entity_risk",
            "candidate_deprioritized_named_frequency_risk",
            "problem_class_proper_risk",
            "proper_acronym_entity_risk",
            "news_abbreviation_entity_risk",
            "jmdict_abbreviation_risk",
        ),
        count=len(context.lemmas),
    )
    arrays["curriculum_core_any"] = _max_signal(
        arrays,
        ("jlpt_vocab_beginner_core", "lesson_vocab_beginner_core"),
        count=len(context.lemmas),
    )
    arrays["loanword_any"] = _max_signal(
        arrays,
        (
            "wtype_gairaigo_risk",
            "jmdict_loanword_source_risk",
            "jmdict_foreign_priority_risk",
        ),
        count=len(context.lemmas),
    )
    return arrays


def _max_signal(
    arrays: Mapping[str, object],
    names: Sequence[str],
    *,
    count: int,
) -> object:
    stacked = [
        np.asarray(arrays.get(name, np.zeros(count, dtype=np.float32)), dtype=np.float32)
        for name in names
    ]
    if not stacked:
        return np.zeros(count, dtype=np.float32)
    return np.maximum.reduce(stacked)


def _group_mask(spec: GroupSpec, signal_arrays: Mapping[str, object]) -> object:
    count = len(next(iter(signal_arrays.values()))) if signal_arrays else 0
    selected = np.ones(count, dtype=bool)
    for term in spec.terms:
        signal = np.asarray(
            signal_arrays.get(term.signal, np.zeros(count, dtype=np.float32)),
            dtype=np.float32,
        )
        if term.min_value is not None:
            selected &= signal >= float(term.min_value)
        if term.max_value is not None:
            selected &= signal <= float(term.max_value)
    return selected


def _context_group_mask(context: object, group_mask: object) -> object:
    indices = np.asarray(context.component_indices, dtype=np.int64)
    mask = np.zeros(len(indices), dtype=bool)
    valid = (indices >= 0) & (indices < len(group_mask))
    parsed = np.asarray(group_mask, dtype=bool)
    mask[valid] = parsed[indices[valid]]
    return mask


def _score_delta(after: Mapping[str, object], before: Mapping[str, object]) -> float | None:
    after_score = _optional_float(after.get("proficiency_ordering_score"))
    before_score = _optional_float(before.get("proficiency_ordering_score"))
    if after_score is None or before_score is None:
        return None
    return after_score - before_score


def _normal_vocab_mae_reduction(
    *,
    before: Mapping[str, object],
    after: Mapping[str, object],
) -> float | None:
    before_mae = _normal_vocab_mae(before)
    after_mae = _normal_vocab_mae(after)
    if before_mae is None or after_mae is None:
        return None
    return before_mae - after_mae


def _normal_vocab_mae(report: Mapping[str, object]) -> float | None:
    if "normal_vocab_mae" in report:
        return _optional_float(report.get("normal_vocab_mae"))
    return _optional_float(_metric_path(report, "normal_vocab", "metrics", "mae"))


def _leaderboard(
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
    return [_group_summary(row) for row in ranked]


def _top_group(rows: Sequence[Mapping[str, object]], key: str) -> Mapping[str, object]:
    if not rows:
        return {}
    return max(rows, key=lambda row: _optional_float(row.get(key)) or -999.0)


def _group_summary(row: Mapping[str, object]) -> dict[str, object]:
    if not row:
        return {}
    calibration_residual = _mapping(row.get("calibration_residual"))
    holdout_residual = _mapping(row.get("holdout_residual"))
    fold_summary = _mapping(row.get("fold_summary"))
    return {
        "group_id": row.get("group_id"),
        "source": row.get("source"),
        "description": row.get("description"),
        "full_vocab_count": row.get("full_vocab_count"),
        "scope": row.get("scope"),
        "calibration_count": calibration_residual.get("selected_count"),
        "holdout_count": holdout_residual.get("selected_count"),
        "dominant_direction": calibration_residual.get("dominant_direction"),
        "calibration_delta": row.get("calibration_fit_delta"),
        "selector_score": row.get("selector_score"),
        "profile_score_validation_positive_mae_safe": (
            row.get("profile_score_validation_positive_mae_safe")
            if _passes_profile(row, "validation_positive_mae_safe")
            else None
        ),
        "profile_score_narrow_validation_positive_mae_safe": (
            row.get("profile_score_narrow_validation_positive_mae_safe")
            if _passes_profile(row, "narrow_validation_positive_mae_safe")
            else None
        ),
        "mean_validation_score_delta": fold_summary.get("mean_validation_score_delta"),
        "min_validation_score_delta": fold_summary.get("min_validation_score_delta"),
        "holdout_score_delta": row.get("holdout_score_delta"),
        "holdout_normal_vocab_mae_reduction": row.get("holdout_normal_vocab_mae_reduction"),
        "residual_structure_score": row.get("residual_structure_score"),
    }


def _retained_groups(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[Mapping[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            bool(row.get("eligible")),
            _optional_float(row.get("selector_score")) or -999.0,
            _optional_float(row.get("residual_structure_score")) or -999.0,
        ),
        reverse=True,
    )
    return ranked[:limit]


def _term_dict(term: GroupTerm) -> dict[str, object]:
    return {
        "signal": term.signal,
        "min_value": _rounded(term.min_value),
        "max_value": _rounded(term.max_value),
    }


def _dedup_group_specs(specs: Sequence[GroupSpec]) -> list[GroupSpec]:
    deduped = []
    seen: set[str] = set()
    for spec in specs:
        if spec.group_id in seen:
            continue
        seen.add(spec.group_id)
        deduped.append(spec)
    return deduped


def _finite_values(values: object) -> list[float]:
    parsed = [_optional_float(value) for value in values]
    return [value for value in parsed if value is not None]


def _float_or(value: object, default: float) -> float:
    parsed = _optional_float(value)
    return float(default) if parsed is None else float(parsed)


def _mean(values: object) -> float | None:
    parsed = _finite_values(values)
    if not parsed:
        return None
    return float(np.mean(np.asarray(parsed, dtype=np.float32)))


def _median(values: object) -> float | None:
    parsed = _finite_values(values)
    if not parsed:
        return None
    return float(np.median(np.asarray(parsed, dtype=np.float32)))


def _std(values: object) -> float | None:
    parsed = _finite_values(values)
    if not parsed:
        return None
    return float(np.std(np.asarray(parsed, dtype=np.float32)))


def _fraction(mask: object) -> float:
    parsed = np.asarray(mask, dtype=bool)
    if len(parsed) == 0:
        return 0.0
    return float(parsed.sum()) / float(len(parsed))


def _ratio(numerator: object, denominator: object) -> float | None:
    parsed_denominator = float(denominator)
    if parsed_denominator <= 0.0:
        return None
    return float(numerator) / parsed_denominator


def _token(value: float) -> str:
    return f"{int(round(float(value) * 100)):03d}"


def _resolve_path(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return PROJECT_ROOT / expanded


def render_markdown(report: Mapping[str, object]) -> str:
    parameters = _mapping(report.get("parameters"))
    inputs = _mapping(report.get("inputs"))
    reference = _mapping(report.get("reference_reports"))
    reference_holdout = _mapping(reference.get("holdout"))
    selector = _mapping(report.get("fold_training_selector"))
    selectors = _mapping(report.get("fold_training_selectors"))
    lines = [
        "# en-ja Learner Difficulty Structured Failure Groups",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Holdout used for selection: `{_escape(report.get('holdout_used_for_selection'))}`",
        f"- Candidate groups: `{_escape(parameters.get('group_count'))}`",
        f"- Eligible groups: `{_escape(parameters.get('eligible_group_count'))}`",
        f"- Selector profile counts: `{_escape(_compact(parameters.get('selector_profile_counts')))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Holdout labels: `{_escape(inputs.get('holdout_label_count'))}`",
        "",
        "## Method",
        "",
        str(_mapping(report.get("method")).get("purpose") or ""),
        "",
        str(_mapping(report.get("method")).get("anchor_philosophy") or ""),
        "",
        str(_mapping(report.get("method")).get("selector_rule") or ""),
        "",
        "## Reference",
        "",
        "| Dataset | Score | Normal vocab MAE | Pairwise | Window quality |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for dataset in ("calibration", "holdout"):
        row = _mapping(reference.get(dataset))
        lines.append(
            "| "
            f"`{dataset}` | "
            f"`{_escape(row.get('proficiency_ordering_score'))}` | "
            f"`{_escape(row.get('normal_vocab_mae'))}` | "
            f"`{_escape(row.get('normal_vocab_pairwise'))}` | "
            f"`{_escape(row.get('window_quality'))}` |"
        )
    lines.extend(
        [
            "",
            "## Fold-Training Selector",
            "",
            f"- Selection rule: `{_escape(selector.get('selection_rule'))}`",
            f"- Mean validation score delta: `{_escape(selector.get('mean_validation_score_delta'))}`",
            f"- Mean holdout score delta: `{_escape(selector.get('mean_holdout_score_delta'))}`",
            "",
            "| Group | Selected folds | Validation delta | Holdout delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(selector.get("selection_frequency")):
        lines.append(
            "| "
            f"`{_escape(row.get('group_id'))}` | "
            f"`{_escape(row.get('selected_folds'))}` | "
            f"`{_escape(row.get('mean_validation_score_delta'))}` | "
            f"`{_escape(row.get('mean_holdout_score_delta'))}` |"
        )
    lines.extend(["", "### Selector Variants", ""])
    lines.extend(
        [
            "| Profile | Events | Validation delta | Holdout delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for profile_id, profile_selector in selectors.items():
        parsed = _mapping(profile_selector)
        lines.append(
            "| "
            f"`{_escape(profile_id)}` | "
            f"`{_escape(parsed.get('event_count'))}` | "
            f"`{_escape(parsed.get('mean_validation_score_delta'))}` | "
            f"`{_escape(parsed.get('mean_holdout_score_delta'))}` |"
        )
    lines.extend(
        ["", "Fold events:", "", "| Fold | Group | Delta | Train | Validation | Holdout |"]
    )
    lines.append("| ---: | --- | ---: | ---: | ---: | ---: |")
    for row in _mapping_rows(selector.get("events")):
        lines.append(
            "| "
            f"`{_escape(row.get('fold'))}` | "
            f"`{_escape(row.get('group_id'))}` | "
            f"`{_escape(row.get('delta'))}` | "
            f"`{_escape(row.get('train_score_delta'))}` | "
            f"`{_escape(row.get('validation_score_delta'))}` | "
            f"`{_escape(row.get('holdout_score_delta'))}` |"
        )
    lines.extend(["", "## Primary Groups", ""])
    lines.extend(_primary_groups_markdown(report))
    lines.extend(["", "## Leaderboards", ""])
    leaderboards = _mapping(report.get("leaderboards"))
    for title, rows in (
        ("Fold Validation Selector", leaderboards.get("fold_validation_selector")),
        (
            "Validation Positive MAE-Safe",
            leaderboards.get("validation_positive_mae_safe"),
        ),
        (
            "Narrow Validation Positive MAE-Safe",
            leaderboards.get("narrow_validation_positive_mae_safe"),
        ),
        ("Holdout After Calibration Fit", leaderboards.get("holdout_after_calibration_fit")),
        ("Residual Enrichment", leaderboards.get("residual_enrichment")),
        ("Largest Holdout MAE Reduction", leaderboards.get("largest_holdout_mae_reduction")),
    ):
        lines.extend(_leaderboard_markdown(title, _mapping_rows(rows)))
    lines.extend(["", "## Top Group Details", ""])
    for row in _mapping_rows(report.get("group_results"))[
        : min(8, int(parameters.get("retain_limit") or 8))
    ]:
        lines.extend(_group_detail_markdown(row, reference_holdout))
    return "\n".join(lines).rstrip() + "\n"


def _primary_groups_markdown(report: Mapping[str, object]) -> list[str]:
    rows = _mapping(report.get("primary_groups"))
    lines = [
        "| Selector | Group | Scope | Validation delta | Holdout delta | MAE reduction | Direction | Count |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for selector_id, row in rows.items():
        parsed = _mapping(row)
        lines.append(
            "| "
            f"`{_escape(selector_id)}` | "
            f"`{_escape(parsed.get('group_id'))}` | "
            f"`{_escape(parsed.get('scope'))}` | "
            f"`{_escape(parsed.get('mean_validation_score_delta'))}` | "
            f"`{_escape(parsed.get('holdout_score_delta'))}` | "
            f"`{_escape(parsed.get('holdout_normal_vocab_mae_reduction'))}` | "
            f"`{_escape(parsed.get('dominant_direction'))}` | "
            f"`{_escape(parsed.get('calibration_count'))}` |"
        )
    return lines


def _leaderboard_markdown(title: str, rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "| Group | Source | Scope | Cal count | Direction | Delta | Validation delta | Holdout delta | MAE reduction |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{_escape(row.get('group_id'))}` | "
            f"`{_escape(row.get('source'))}` | "
            f"`{_escape(row.get('scope'))}` | "
            f"`{_escape(row.get('calibration_count'))}` | "
            f"`{_escape(row.get('dominant_direction'))}` | "
            f"`{_escape(row.get('calibration_delta'))}` | "
            f"`{_escape(row.get('mean_validation_score_delta'))}` | "
            f"`{_escape(row.get('holdout_score_delta'))}` | "
            f"`{_escape(row.get('holdout_normal_vocab_mae_reduction'))}` |"
        )
    return lines + [""]


def _group_detail_markdown(
    row: Mapping[str, object],
    reference_holdout: Mapping[str, object],
) -> list[str]:
    calibration_residual = _mapping(row.get("calibration_residual"))
    holdout = _mapping(row.get("holdout"))
    examples = ", ".join(
        str(example.get("label"))
        for example in _mapping_rows(calibration_residual.get("examples"))[:5]
    )
    lines = [
        f"### `{_escape(row.get('group_id'))}`",
        "",
        f"- Source: `{_escape(row.get('source'))}`",
        f"- Description: {_escape(row.get('description'))}",
        f"- Terms: `{_escape(_compact_terms(row.get('terms')))}`",
        f"- Scope: `{_escape(row.get('scope'))}`; full vocab count: `{_escape(row.get('full_vocab_count'))}`",
        f"- Calibration residual: `{_escape(_compact_residual(calibration_residual))}`",
        f"- Holdout score delta: `{_escape(row.get('holdout_score_delta'))}` "
        f"(score `{_escape(holdout.get('proficiency_ordering_score'))}` vs "
        f"`{_escape(reference_holdout.get('proficiency_ordering_score'))}`)",
        f"- Top calibration examples: {examples}",
        "",
    ]
    return lines


def _compact_terms(value: object) -> str:
    parts = []
    for term in _mapping_rows(value):
        signal = term.get("signal")
        min_value = term.get("min_value")
        max_value = term.get("max_value")
        if min_value is not None and max_value is not None:
            parts.append(f"{signal} in [{min_value}, {max_value}]")
        elif min_value is not None:
            parts.append(f"{signal}>={min_value}")
        elif max_value is not None:
            parts.append(f"{signal}<={max_value}")
    return ", ".join(parts)


def _compact_residual(row: Mapping[str, object]) -> str:
    return (
        f"count={row.get('selected_count')}, "
        f"median={row.get('median_residual')}, "
        f"sign={row.get('sign_consistency')}, "
        f"direction={row.get('dominant_direction')}"
    )


def _compact(value: object) -> str:
    if not isinstance(value, Mapping):
        return str(value)
    parts = []
    for key, raw in sorted(value.items()):
        parts.append(f"{key}={raw}")
    return ", ".join(parts)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
