#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    BEGINNER_BROAD_MAX,
    BEGINNER_BROAD_OBSERVED_CEILING,
    BEGINNER_CORE_MAX,
    BEGINNER_CORE_OBSERVED_CEILING,
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_TRACE_JSON,
    Expert,
    HIGH_TAIL_MIN,
    HIGH_TAIL_OBSERVED_FLOOR,
    PAIRWISE_MIN_EXPECTED_GAP,
    PAIRWISE_TIE_TOLERANCE,
    UPPER_TAIL_MIN,
    UPPER_TAIL_OBSERVED_FLOOR,
    _band_samples,
    _compact_counts,
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _expert_json,
    _load_json,
    _mapping,
    _mapping_rows,
    _optional_float,
    _raw_scores_for_expert,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _score_summary,
    _select_experts,
    _sequence_values,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_tree_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_tree_search_en_ja_latest.md"
)
DEFAULT_CALIBRATION_ROWS_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_tree_calibration_rows_en_ja_latest.csv"
)
DEFAULT_CALIBRATION_ROWS_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_tree_calibration_rows_en_ja_latest.md"
)
DEFAULT_SPLIT_SIGNALS = (
    "bccwj_domain_rank_coverage",
    "bccwj_domain_rank_spread",
    "bccwj_domain_rank_variability",
    "bccwj_domain_profile_variability",
    "bccwj_fixed_variable_rank_delta",
    "bccwj_pmw_spread",
    "bccwj_rank_spread",
    "bccwj_rank_variability",
    "frequency",
    "frequency_unranked_risk",
    "frequency_unranked_rare_risk",
    "frequency_unranked_priority_risk",
    "frequency_unranked_tail_risk",
    "frequency_sqrt",
    "frequency_power2",
    "frequency_power3",
    "frequency_ease",
    "frequency_tail50",
    "frequency_tail65",
    "frequency_tail80",
    "frequency_tail90",
    "frequency_unranked_power2_risk",
    "frequency_unranked_power3_risk",
    "frequency_unranked_floor60_risk",
    "frequency_unranked_floor70_risk",
    "frequency_unranked_floor80_risk",
    "frequency_unranked_floor90_risk",
    "frequency_unranked_floor95_risk",
    "frequency_unranked_floor99_risk",
    "frequency_unranked_tail65_risk",
    "frequency_unranked_tail80_risk",
    "frequency_unranked_tail90_risk",
    "frequency_rank_known",
    "frequency_value_known",
    "frequency_source_known",
    "source_coverage_count",
    "jmdict_priority_known",
    "jmdict_lexical_known",
    "lexical_source_known",
    "jmnedict_name_known",
    "jlpt_vocab_known",
    "lesson_vocab_known",
    "pedagogical_source_known",
    "kanjidic2_known",
    "kanjivg_known",
    "orthographic_source_known",
    "tubelex_frequency_known",
    "acronym_signal_known",
    "bccwj_domain_rank_known",
    "jmdict_cross_reference_flag",
    "jmdict_ambiguity_score",
    "jmdict_reading_complexity_score",
    "jmdict_restriction_complexity_score",
    "common_jmdict_ambiguity_score",
    "common_reading_complexity_score",
    "common_restriction_complexity_score",
    "jmdict_register_domain_score",
    "common_register_domain_score",
    "jmdict_dialect_flag",
    "jmdict_field_marked_flag",
    "jmdict_field_count",
    "jmdict_gloss_count",
    "jmdict_pos_count",
    "jmdict_entry_ambiguity",
    "jmdict_pos_ambiguity",
    "jmdict_reading_form_ambiguity",
    "jmdict_sense_ambiguity",
    "jmdict_kanji_form_marked_flag",
    "jmdict_non_ladder_entry_risk",
    "jmdict_non_vocab_raw_class_score",
    "jmdict_kana_preferred_flag",
    "jmdict_marked_usage_flag",
    "jmdict_no_kanji_reading_flag",
    "jmdict_polysemy_flag",
    "jmdict_priority",
    "jmdict_reading_form_marked_flag",
    "jmdict_reading_restricted_flag",
    "jmdict_register_marked_flag",
    "jmdict_search_only_form_flag",
    "jmdict_sense_count",
    "jmdict_sense_info_flag",
    "jmdict_sense_restricted_flag",
    "jmdict_sinitic_source_flag",
    "jmdict_source_text_flag",
    "jmdict_source_type_flag",
    "jmdict_wasei_source_flag",
    "kanjidic_nanori_reading_count_score",
    "kanjidic_variant_type_count_score",
    "jmnedict_name_overlap",
    "ordinary_ladder_entity_suppression_risk",
    "kango_common_priority_risk",
    "common_kango_register_domain_score",
    "common_kango_written_burden",
    "common_kango_ambiguity_score",
    "common_kango_complexity_score",
    "kango_kanji_burden",
    "kango_uncommon_kanji_burden",
    "kanji_curriculum_burden",
    "kanji_curriculum_missing_risk",
    "kanji_frequency_rank",
    "kanji_grade",
    "kanji_shape_burden",
    "max_kanji_burden",
    "max_kanji_shape_burden",
    "max_written_form_burden",
    "kanjivg_phonetic_component",
    "kanjivg_position_detail",
    "kanjivg_variant_structure",
    "kanjivg_visual_complexity",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_risk",
    "rare_wago_written_risk",
    "rare_wago_marked_usage_risk",
    "rare_wago_max_kanji_burden",
    "rare_wago_max_written_burden",
    "rare_wago_missing_curriculum_risk",
    "rare_wago_missing_curriculum_shape_risk",
    "rare_wago_non_standard_reading_risk",
    "rare_wago_obscure_written_risk",
    "old_jlpt_kanji",
    "pos_adjective_gate",
    "pos_common_noun_gate",
    "pos_plain_verb_gate",
    "pos_sahen_noun_risk",
    "sahen_kango_risk",
    "script_complexity",
    "stroke_count",
    "wtype_gairaigo_risk",
    "wtype_kango_risk",
    "wtype_mixed_risk",
    "wtype_non_wago_risk",
    "wtype_proper_flag",
    "wtype_wago_ease",
    "wago_kanji_burden",
    "written_form_burden",
)
DEFAULT_THRESHOLD_QUANTILES = (0.20, 0.35, 0.50, 0.65, 0.80)
DEFAULT_MANUAL_SPLIT_THRESHOLDS = {
    "frequency": (0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.80, 0.85),
    "frequency_unranked_risk": (0.50,),
    "frequency_unranked_rare_risk": (0.25, 0.50, 0.75),
    "frequency_unranked_priority_risk": (0.25, 0.50, 0.75),
    "frequency_unranked_tail_risk": (0.25, 0.50, 0.75),
    "frequency_tail50": (0.25, 0.50, 0.75),
    "frequency_tail65": (0.25, 0.50, 0.75),
    "frequency_tail80": (0.25, 0.50, 0.75),
    "frequency_tail90": (0.25, 0.50, 0.75),
    "frequency_unranked_floor60_risk": (0.50, 0.60, 0.75),
    "frequency_unranked_floor70_risk": (0.50, 0.70, 0.85),
    "frequency_unranked_floor80_risk": (0.50, 0.80, 0.90),
    "frequency_unranked_floor90_risk": (0.50, 0.90, 0.95),
    "frequency_unranked_floor95_risk": (0.50, 0.95, 0.99),
    "frequency_unranked_floor99_risk": (0.50, 0.99),
    "frequency_unranked_tail65_risk": (0.25, 0.50, 0.75),
    "frequency_unranked_tail80_risk": (0.25, 0.50, 0.75),
    "frequency_unranked_tail90_risk": (0.25, 0.50, 0.75),
}


@dataclass(frozen=True)
class SplitSpec:
    signal: str
    threshold: float
    missing_left: bool

    @property
    def split_id(self) -> str:
        missing = "ml" if self.missing_left else "mr"
        return f"{self.signal}<={self.threshold:.4f}:{missing}"


@dataclass(frozen=True)
class TreeCandidate:
    candidate_id: str
    root: SplitSpec | None
    child_side: str | None
    child: SplitSpec | None
    expert_ids: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search shallow model-tree learner-difficulty scorers over existing "
            "en-ja signal components."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--expert-pool-size", type=int, default=24)
    parser.add_argument("--top-per-metric", type=int, default=8)
    parser.add_argument(
        "--split-signals",
        default=",".join(DEFAULT_SPLIT_SIGNALS),
        help="Comma-separated component names eligible for model-tree splits.",
    )
    parser.add_argument(
        "--threshold-quantiles",
        default=",".join(f"{value:g}" for value in DEFAULT_THRESHOLD_QUANTILES),
    )
    parser.add_argument(
        "--manual-split-thresholds",
        default=_format_manual_thresholds(DEFAULT_MANUAL_SPLIT_THRESHOLDS),
        help=(
            "Semicolon-separated signal thresholds, e.g. "
            "'frequency:0.35,0.45,0.85;kanji_grade:0.7'."
        ),
    )
    parser.add_argument("--leaf-expert-limit", type=int, default=4)
    parser.add_argument("--leaf-global-expert-limit", type=int, default=4)
    parser.add_argument(
        "--tree-depth",
        choices=("linear", "stump", "depth2"),
        default="depth2",
        help=(
            "Maximum model-tree structure to evaluate. Use 'linear' or 'stump' "
            "for fast interactive research before running depth-2 search."
        ),
    )
    parser.add_argument(
        "--max-split-specs",
        type=int,
        default=0,
        help=(
            "Optional cap on generated split specs before enumeration. "
            "0 keeps all eligible split specs."
        ),
    )
    parser.add_argument(
        "--expert-exclude-signals",
        default="",
        help=(
            "Comma-separated component names. Linear experts with nonzero weights "
            "on these components are excluded from the pool; split gates may still "
            "use the same component if listed in --split-signals."
        ),
    )
    parser.add_argument("--root-retain-limit", type=int, default=40)
    parser.add_argument("--approximate-retain-limit", type=int, default=1000)
    parser.add_argument("--exact-limit", type=int, default=1000)
    parser.add_argument(
        "--detail-candidate-limit",
        type=int,
        default=20,
        help=(
            "Attach full calibration rows to this many top exact candidates. "
            "The flat CSV artifact is generated from these attached rows."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--calibration-rows-csv-out",
        type=Path,
        default=DEFAULT_CALIBRATION_ROWS_CSV_OUT,
    )
    parser.add_argument(
        "--calibration-rows-markdown-out",
        type=Path,
        default=DEFAULT_CALIBRATION_ROWS_MARKDOWN_OUT,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        expert_pool_size=max(1, int(args.expert_pool_size)),
        top_per_metric=max(1, int(args.top_per_metric)),
        split_signals=_parse_csv(args.split_signals),
        threshold_quantiles=_parse_float_csv(args.threshold_quantiles),
        manual_split_thresholds=_parse_manual_thresholds(args.manual_split_thresholds),
        leaf_expert_limit=max(1, int(args.leaf_expert_limit)),
        leaf_global_expert_limit=max(0, int(args.leaf_global_expert_limit)),
        tree_depth=str(args.tree_depth),
        max_split_specs=max(0, int(args.max_split_specs)),
        expert_exclude_signals=_parse_csv(args.expert_exclude_signals),
        root_retain_limit=max(1, int(args.root_retain_limit)),
        approximate_retain_limit=max(1, int(args.approximate_retain_limit)),
        exact_limit=max(1, int(args.exact_limit)),
        detail_candidate_limit=max(0, int(args.detail_candidate_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    calibration_rows_csv_out = _resolve_path(args.calibration_rows_csv_out)
    calibration_rows_markdown_out = _resolve_path(args.calibration_rows_markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    calibration_rows_csv_out.parent.mkdir(parents=True, exist_ok=True)
    calibration_rows_markdown_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    write_calibration_rows_csv(calibration_rows_csv_out, report)
    calibration_rows_markdown_out.write_text(
        render_calibration_rows_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    print(f"Wrote calibration rows CSV artifact to {calibration_rows_csv_out}")
    print(f"Wrote calibration rows Markdown artifact to {calibration_rows_markdown_out}")
    return 0


def build_report(
    *,
    trace_json: Path,
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    expert_pool_size: int = 24,
    top_per_metric: int = 8,
    split_signals: Sequence[str] = DEFAULT_SPLIT_SIGNALS,
    threshold_quantiles: Sequence[float] = DEFAULT_THRESHOLD_QUANTILES,
    manual_split_thresholds: Mapping[str, Sequence[float]] = DEFAULT_MANUAL_SPLIT_THRESHOLDS,
    leaf_expert_limit: int = 4,
    leaf_global_expert_limit: int = 4,
    tree_depth: str = "depth2",
    max_split_specs: int = 0,
    expert_exclude_signals: Sequence[str] = (),
    root_retain_limit: int = 40,
    approximate_retain_limit: int = 1000,
    exact_limit: int = 1000,
    detail_candidate_limit: int = 20,
) -> dict[str, object]:
    trace = _load_json(trace_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    raw_records = _filter_expert_records(
        trace.get("variant_records", ()),
        exclude_signals=expert_exclude_signals,
    )
    experts = _select_experts(
        raw_records,
        pool_size=expert_pool_size,
        top_per_metric=top_per_metric,
    )
    variant_ids = [str(value) for value in calibration["variant_ids"]]
    variant_index = {variant_id: index for index, variant_id in enumerate(variant_ids)}
    calibration_context = _model_tree_calibration_context(calibration, component)
    split_specs = _split_specs(
        component,
        split_signals=split_signals,
        threshold_quantiles=threshold_quantiles,
        manual_split_thresholds=manual_split_thresholds,
    )
    split_specs = _limit_split_specs(split_specs, max_split_specs)
    root_candidates = _linear_and_stump_candidates(
        experts=experts,
        split_specs=split_specs,
        variant_index=variant_index,
        calibration_context=calibration_context,
        retain_limit=root_retain_limit,
        include_stumps=tree_depth != "linear",
    )
    approximate_candidates = (
        _depth2_candidates(
            root_candidates=root_candidates,
            experts=experts,
            split_specs=split_specs,
            variant_index=variant_index,
            calibration_context=calibration_context,
            leaf_expert_limit=leaf_expert_limit,
            leaf_global_expert_ids=tuple(
                expert.variant_id for expert in experts[:leaf_global_expert_limit]
            ),
            retain_limit=approximate_retain_limit,
        )
        if tree_depth == "depth2"
        else list(root_candidates)
    )
    exact_candidates = _exact_evaluate_trees(
        approximate_candidates[:exact_limit],
        experts_by_id={expert.variant_id: expert for expert in experts},
        component=component,
        calibration_context=calibration_context,
        detail_candidate_limit=detail_candidate_limit,
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
            code_paths=_model_tree_code_paths(),
            version_constants={
                "target_curve": TARGET_CURVE_ID,
            },
            argv=sys.argv,
        ),
        "method": {
            "model": "shallow_hard_gated_model_tree",
            "split_space": "existing normalized component signals",
            "approximate_stage": (
                "uses expert calibration predictions to preselect root/stump and "
                "depth-2 tree candidates"
            ),
            "exact_stage": (
                "recomputes raw tree scores over the full component matrix and "
                "then applies global target-curve normalization"
            ),
            "normalization_curve_id": TARGET_CURVE_ID,
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "trace_variant_count": len(trace.get("variant_records", ())),
            "expert_eligible_variant_count": len(raw_records),
            "calibration_label_count": int(len(calibration["calibration_lemmas"])),
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "component_names": [str(value) for value in component["component_names"]],
            "expert_pool_size": len(experts),
            "top_per_metric": top_per_metric,
            "split_signals": list(split_signals),
            "threshold_quantiles": [round(float(value), 4) for value in threshold_quantiles],
            "manual_split_thresholds": {
                signal: [round(float(value), 4) for value in values]
                for signal, values in manual_split_thresholds.items()
            },
            "split_spec_count": len(split_specs),
            "leaf_expert_limit": leaf_expert_limit,
            "leaf_global_expert_limit": leaf_global_expert_limit,
            "tree_depth": tree_depth,
            "max_split_specs": max_split_specs,
            "expert_exclude_signals": list(expert_exclude_signals),
            "root_retained": len(root_candidates),
            "approximate_retained": len(approximate_candidates),
            "exact_limit": exact_limit,
            "detail_candidate_limit": detail_candidate_limit,
        },
        "expert_pool": [_expert_json(expert) for expert in experts],
        "split_specs": [_split_json(split) for split in split_specs],
        "root_top": root_candidates[:50],
        "approximate_top": approximate_candidates[:80],
        "exact_top": exact_candidates,
    }


def _model_tree_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "difficulty_signal_sweep": (SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"),
        "difficulty_piecewise_search": (
            SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
        ),
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


def _filter_expert_records(
    records: object,
    *,
    exclude_signals: Sequence[str],
) -> list[Mapping[str, object]]:
    rows = _mapping_rows(records)
    excluded = frozenset(str(signal).strip() for signal in exclude_signals if str(signal).strip())
    if not excluded:
        return rows
    filtered: list[Mapping[str, object]] = []
    for row in rows:
        weights = _mapping(row.get("weights"))
        if any((_optional_float(weights.get(signal)) or 0.0) > 0.0 for signal in excluded):
            continue
        filtered.append(row)
    return filtered


def _linear_and_stump_candidates(
    *,
    experts: Sequence[Expert],
    split_specs: Sequence[SplitSpec],
    variant_index: Mapping[str, int],
    calibration_context: Mapping[str, object],
    retain_limit: int,
    include_stumps: bool = True,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for expert in experts:
        candidate = TreeCandidate(
            candidate_id=f"linear__{expert.variant_id}",
            root=None,
            child_side=None,
            child=None,
            expert_ids=(expert.variant_id,),
        )
        rows.append(
            _approximate_tree_record(
                candidate,
                variant_index=variant_index,
                calibration_context=calibration_context,
            )
        )
    if not include_stumps:
        return _top_tree_rows(rows, limit=retain_limit)
    for split in split_specs:
        leaf_ids = _tree_leaf_ids_for_values(
            root=split,
            child_side=None,
            child=None,
            split_values=calibration_context["split_values"],
            split_present=calibration_context["split_present"],
        )
        left_top = _top_leaf_experts(
            experts,
            mask=leaf_ids == 0,
            variant_index=variant_index,
            calibration_context=calibration_context,
            limit=len(experts),
        )
        right_top = _top_leaf_experts(
            experts,
            mask=leaf_ids == 1,
            variant_index=variant_index,
            calibration_context=calibration_context,
            limit=len(experts),
        )
        for left in left_top:
            for right in right_top:
                if left == right:
                    continue
                candidate = TreeCandidate(
                    candidate_id=f"stump__{split.split_id}__{left}__{right}",
                    root=split,
                    child_side=None,
                    child=None,
                    expert_ids=(left, right),
                )
                rows.append(
                    _approximate_tree_record(
                        candidate,
                        variant_index=variant_index,
                        calibration_context=calibration_context,
                    )
                )
        if len(rows) > retain_limit * 6:
            rows = _top_tree_rows(rows, limit=retain_limit)
    return _top_tree_rows(rows, limit=retain_limit)


def _depth2_candidates(
    *,
    root_candidates: Sequence[Mapping[str, object]],
    experts: Sequence[Expert],
    split_specs: Sequence[SplitSpec],
    variant_index: Mapping[str, int],
    calibration_context: Mapping[str, object],
    leaf_expert_limit: int,
    leaf_global_expert_ids: Sequence[str],
    retain_limit: int,
) -> list[dict[str, object]]:
    rows = [dict(row) for row in root_candidates]
    root_stumps = [
        root
        for root in (
            _split_from_json(_mapping(_mapping(row.get("tree")).get("root")))
            for row in root_candidates
            if _mapping(row.get("tree")).get("root") and not _mapping(row.get("tree")).get("child")
        )
        if root is not None
    ]
    seen_root_ids = {root.split_id for root in root_stumps}
    root_stumps.extend(split for split in split_specs if split.split_id not in seen_root_ids)
    for root in root_stumps:
        for child_side in ("left", "right"):
            for child in split_specs:
                if child.split_id == root.split_id:
                    continue
                leaf_ids = _tree_leaf_ids_for_values(
                    root=root,
                    child_side=child_side,
                    child=child,
                    split_values=calibration_context["split_values"],
                    split_present=calibration_context["split_present"],
                )
                leaf_experts = [
                    _top_leaf_experts(
                        experts,
                        mask=leaf_ids == leaf_id,
                        variant_index=variant_index,
                        calibration_context=calibration_context,
                        limit=leaf_expert_limit,
                        global_expert_ids=leaf_global_expert_ids,
                    )
                    for leaf_id in range(3)
                ]
                if any(not options for options in leaf_experts):
                    continue
                for first in leaf_experts[0]:
                    for second in leaf_experts[1]:
                        for third in leaf_experts[2]:
                            expert_ids = (first, second, third)
                            if len(set(expert_ids)) == 1:
                                continue
                            candidate = TreeCandidate(
                                candidate_id=(
                                    f"tree2__root_{root.split_id}__{child_side}_"
                                    f"{child.split_id}__{first}__{second}__{third}"
                                ),
                                root=root,
                                child_side=child_side,
                                child=child,
                                expert_ids=expert_ids,
                            )
                            rows.append(
                                _approximate_tree_record(
                                    candidate,
                                    variant_index=variant_index,
                                    calibration_context=calibration_context,
                                )
                            )
                if len(rows) > retain_limit * 8:
                    rows = _top_tree_rows(rows, limit=retain_limit)
    return _top_tree_rows(rows, limit=retain_limit)


def _approximate_tree_record(
    candidate: TreeCandidate,
    *,
    variant_index: Mapping[str, int],
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    observed = _approximate_tree_values(
        candidate,
        variant_index=variant_index,
        calibration_context=calibration_context,
    )
    scores, metrics = _fast_difficulty_summary(
        observed,
        calibration_context=calibration_context,
    )
    return {
        "candidate_id": candidate.candidate_id,
        "tree": _tree_json(candidate),
        "stage": "approximate",
        "scores": scores,
        "metrics": metrics,
    }


def _approximate_tree_values(
    candidate: TreeCandidate,
    *,
    variant_index: Mapping[str, int],
    calibration_context: Mapping[str, object],
) -> object:
    observed_matrix = calibration_context["observed_matrix"]
    if candidate.root is None:
        return np.asarray(
            observed_matrix[variant_index[candidate.expert_ids[0]]],
            dtype=np.float32,
        )
    leaf_ids = _tree_leaf_ids_for_values(
        root=candidate.root,
        child_side=candidate.child_side,
        child=candidate.child,
        split_values=calibration_context["split_values"],
        split_present=calibration_context["split_present"],
    )
    values = np.full(len(leaf_ids), np.nan, dtype=np.float32)
    for leaf_id, expert_id in enumerate(candidate.expert_ids):
        mask = leaf_ids == leaf_id
        values[mask] = observed_matrix[variant_index[expert_id], mask]
    return values


def _top_leaf_experts(
    experts: Sequence[Expert],
    *,
    mask: object,
    variant_index: Mapping[str, int],
    calibration_context: Mapping[str, object],
    limit: int,
    global_expert_ids: Sequence[str] = (),
) -> list[str]:
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    finite = np.asarray(mask, dtype=bool) & np.isfinite(expected)
    if not bool(finite.any()):
        return _append_global_experts(
            [expert.variant_id for expert in experts[:limit]],
            global_expert_ids,
        )
    rows = []
    observed_matrix = calibration_context["observed_matrix"]
    for expert in experts:
        observed = np.asarray(observed_matrix[variant_index[expert.variant_id]], dtype=np.float32)
        valid = finite & np.isfinite(observed)
        if not bool(valid.any()):
            continue
        mae = float(np.mean(np.abs(observed[valid] - expected[valid])))
        rows.append(
            (mae, -float(expert.source_scores.get("balanced_score", 0.0)), expert.variant_id)
        )
    return _append_global_experts(
        [variant_id for _mae, _neg_score, variant_id in sorted(rows)[:limit]],
        global_expert_ids,
    )


def _append_global_experts(
    leaf_expert_ids: Sequence[str],
    global_expert_ids: Sequence[str],
) -> list[str]:
    merged = list(leaf_expert_ids)
    seen = set(merged)
    for expert_id in global_expert_ids:
        if expert_id in seen:
            continue
        merged.append(expert_id)
        seen.add(expert_id)
    return merged


def _fast_difficulty_summary(
    observed_values: object,
    *,
    calibration_context: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    expected_finite = np.asarray(calibration_context["expected_finite"], dtype=bool)
    finite = expected_finite & np.isfinite(observed)
    errors = np.abs(observed[finite] - expected[finite])
    mae = float(errors.mean()) if len(errors) else None
    observed_bucket_ids = np.where(observed < 0.55, 0, np.where(observed < 0.80, 1, 2)).astype(
        np.int8
    )
    expected_bucket_ids = np.asarray(calibration_context["expected_bucket_ids"], dtype=np.int8)
    bucket_mask = finite & (expected_bucket_ids >= 0)
    bucket_matches = bucket_mask & (observed_bucket_ids == expected_bucket_ids)
    bucket_count = int(bucket_mask.sum())
    bucket_match_count = int(bucket_matches.sum())
    pairwise = _fast_pairwise_summary(observed, calibration_context=calibration_context)
    rank_proxy = (2.0 * pairwise["accuracy"]) - 1.0 if pairwise["accuracy"] is not None else None
    beginner_core = _fast_segment_summary(
        observed,
        mask=calibration_context["beginner_core_mask"],
        observed_ceiling=BEGINNER_CORE_OBSERVED_CEILING,
    )
    beginner_broad = _fast_segment_summary(
        observed,
        mask=calibration_context["beginner_broad_mask"],
        observed_ceiling=BEGINNER_BROAD_OBSERVED_CEILING,
    )
    upper_tail = _fast_segment_summary(
        observed,
        mask=calibration_context["upper_tail_mask"],
        observed_floor=UPPER_TAIL_OBSERVED_FLOOR,
    )
    high_tail = _fast_segment_summary(
        observed,
        mask=calibration_context["high_tail_mask"],
        observed_floor=HIGH_TAIL_OBSERVED_FLOOR,
    )
    separation = _fast_tail_separation(observed, calibration_context=calibration_context)
    difficulty_value = {
        "evaluated_count": int(finite.sum()),
        "mae": _rounded(mae),
    }
    difficulty_bucket = {
        "evaluated_count": bucket_count,
        "match_count": bucket_match_count,
        "mismatch_count": bucket_count - bucket_match_count,
        "accuracy": _rounded(_fast_ratio(bucket_match_count, bucket_count)),
        "mismatches": [],
    }
    pairwise_order = {
        "comparable_count": pairwise["comparable_count"],
        "correct_count": pairwise["correct_count"],
        "tie_count": pairwise["tie_count"],
        "wrong_count": pairwise["wrong_count"],
        "accuracy": _rounded(pairwise["accuracy"]),
        "strict_accuracy": _rounded(pairwise["strict_accuracy"]),
        "wrong_examples": [],
    }
    rank_correlation = {
        "evaluated_count": int(finite.sum()),
        "spearman": _rounded(rank_proxy),
        "pearson": None,
    }
    segments = {
        "beginner_core": beginner_core,
        "beginner_broad": beginner_broad,
        "upper_tail": upper_tail,
        "high_tail": high_tail,
    }
    scores = _score_summary(
        difficulty_value=difficulty_value,
        difficulty_bucket=difficulty_bucket,
        pairwise_order=pairwise_order,
        rank_correlation=rank_correlation,
        segments=segments,
        separation=separation,
    )
    metrics = {
        "mae": difficulty_value["mae"],
        "bucket_accuracy": difficulty_bucket["accuracy"],
        "bucket_mismatch_count": difficulty_bucket["mismatch_count"],
        "pairwise_accuracy": pairwise_order["accuracy"],
        "pairwise_wrong_count": pairwise_order["wrong_count"],
        "spearman": rank_correlation["spearman"],
        "beginner_core_pass_rate": beginner_core["pass_rate"],
        "high_tail_pass_rate": high_tail["pass_rate"],
    }
    return scores, metrics


def _fast_pairwise_summary(
    observed: object,
    *,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    left = np.asarray(calibration_context["pair_left"], dtype=np.int64)
    right = np.asarray(calibration_context["pair_right"], dtype=np.int64)
    expected_gap = np.asarray(calibration_context["pair_expected_gap"], dtype=np.float32)
    if not len(left):
        return {
            "comparable_count": 0,
            "correct_count": 0,
            "tie_count": 0,
            "wrong_count": 0,
            "accuracy": None,
            "strict_accuracy": None,
        }
    observed_array = np.asarray(observed, dtype=np.float32)
    observed_gap = observed_array[right] - observed_array[left]
    valid = np.isfinite(observed_gap)
    if not bool(valid.any()):
        return {
            "comparable_count": 0,
            "correct_count": 0,
            "tie_count": 0,
            "wrong_count": 0,
            "accuracy": None,
            "strict_accuracy": None,
        }
    expected_gap = expected_gap[valid]
    observed_gap = observed_gap[valid]
    ties = np.abs(observed_gap) <= PAIRWISE_TIE_TOLERANCE
    correct = (~ties) & (np.sign(expected_gap) == np.sign(observed_gap))
    wrong = (~ties) & (~correct)
    comparable_count = int(len(expected_gap))
    correct_count = int(correct.sum())
    tie_count = int(ties.sum())
    wrong_count = int(wrong.sum())
    return {
        "comparable_count": comparable_count,
        "correct_count": correct_count,
        "tie_count": tie_count,
        "wrong_count": wrong_count,
        "accuracy": _fast_ratio(correct_count + (0.5 * tie_count), comparable_count),
        "strict_accuracy": _fast_ratio(correct_count, comparable_count),
    }


def _fast_segment_summary(
    observed: object,
    *,
    mask: object,
    observed_floor: float | None = None,
    observed_ceiling: float | None = None,
) -> dict[str, object]:
    observed_array = np.asarray(observed, dtype=np.float32)
    segment_mask = np.asarray(mask, dtype=bool) & np.isfinite(observed_array)
    values = observed_array[segment_mask]
    if not len(values):
        return {
            "count": 0,
            "pass_count": 0,
            "pass_rate": None,
            "misses": [],
        }
    passes = np.ones(len(values), dtype=bool)
    if observed_floor is not None:
        passes &= values >= observed_floor
    if observed_ceiling is not None:
        passes &= values <= observed_ceiling
    pass_count = int(passes.sum())
    return {
        "count": int(len(values)),
        "pass_count": pass_count,
        "pass_rate": _rounded(_fast_ratio(pass_count, len(values))),
        "misses": [],
    }


def _fast_tail_separation(
    observed: object,
    *,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    observed_array = np.asarray(observed, dtype=np.float32)
    beginner_mask = np.asarray(calibration_context["beginner_core_mask"], dtype=bool)
    high_tail_mask = np.asarray(calibration_context["high_tail_mask"], dtype=bool)
    beginner = observed_array[beginner_mask & np.isfinite(observed_array)]
    high_tail = observed_array[high_tail_mask & np.isfinite(observed_array)]
    beginner_avg = float(beginner.mean()) if len(beginner) else None
    high_tail_avg = float(high_tail.mean()) if len(high_tail) else None
    return {
        "beginner_count": int(len(beginner)),
        "high_tail_count": int(len(high_tail)),
        "beginner_observed_avg": _rounded(beginner_avg),
        "high_tail_observed_avg": _rounded(high_tail_avg),
        "mean_gap": _rounded(
            high_tail_avg - beginner_avg
            if high_tail_avg is not None and beginner_avg is not None
            else None
        ),
        "minmax_gap": _rounded(
            float(high_tail.min() - beginner.max()) if len(high_tail) and len(beginner) else None
        ),
    }


def _sampled_pairwise_indices(
    expected_values: object,
    *,
    max_pairs: int = 5000,
) -> tuple[object, object, object]:
    expected = np.asarray(expected_values, dtype=np.float32)
    indices = np.where(np.isfinite(expected))[0]
    if len(indices) < 2:
        empty = np.asarray([], dtype=np.int64)
        return empty, empty, np.asarray([], dtype=np.float32)
    left_offsets, right_offsets = np.triu_indices(len(indices), k=1)
    left = indices[left_offsets]
    right = indices[right_offsets]
    gaps = expected[right] - expected[left]
    comparable = np.abs(gaps) >= PAIRWISE_MIN_EXPECTED_GAP
    left = left[comparable]
    right = right[comparable]
    gaps = gaps[comparable]
    if len(left) > max_pairs:
        sample = np.linspace(0, len(left) - 1, max_pairs, dtype=np.int64)
        left = left[sample]
        right = right[sample]
        gaps = gaps[sample]
    return left.astype(np.int64), right.astype(np.int64), gaps.astype(np.float32)


def _fast_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _exact_evaluate_trees(
    candidates: Sequence[Mapping[str, object]],
    *,
    experts_by_id: Mapping[str, Expert],
    component: object,
    calibration_context: Mapping[str, object],
    detail_candidate_limit: int = 20,
) -> list[dict[str, object]]:
    needed_expert_ids = sorted(
        {
            str(expert_id)
            for candidate in candidates
            for expert_id in _sequence_values(_mapping(candidate.get("tree")).get("expert_ids"))
        }
    )
    raw_by_expert = {
        expert_id: _raw_scores_for_expert(experts_by_id[expert_id], component)
        for expert_id in needed_expert_ids
        if expert_id in experts_by_id
    }
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    component_split_values = _component_split_values(component)
    component_split_present = _component_split_present(component)
    calibration_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    results: list[dict[str, object]] = []
    for row in candidates:
        candidate = _tree_from_row(row)
        raw, leaf_ids = _tree_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            split_values=component_split_values,
            split_present=component_split_present,
            row_count=len(component["candidate_identity_keys"]),
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        observed = np.full(len(calibration_indices), np.nan, dtype=np.float32)
        valid = calibration_indices >= 0
        observed[valid] = normalized[calibration_indices[valid]]
        metrics = _difficulty_metrics(
            expected_values=calibration_context["expected_values"],
            observed_values=observed,
            expected_bands=calibration_context["expected_bands"],
            labels=calibration_context["labels"],
        )
        results.append(
            {
                "candidate_id": candidate.candidate_id,
                "tree": _tree_json(candidate),
                "stage": "exact",
                "scores": metrics["scores"],
                "metrics": _summary_metrics(metrics),
                "wrong_pairwise_examples": metrics["pairwise_order"]["wrong_examples"],
                "difficulty_mismatches": metrics["difficulty_bucket"]["mismatches"],
                "segment_misses": {
                    key: value["misses"]
                    for key, value in metrics["segments"].items()
                    if value.get("misses")
                },
                "approximate_scores": row.get("scores"),
            }
        )
    ranked = _top_tree_rows(results, limit=len(results))
    if detail_candidate_limit <= 0:
        return ranked
    candidate_by_id = {_tree_from_row(row).candidate_id: _tree_from_row(row) for row in candidates}
    for row in ranked[:detail_candidate_limit]:
        candidate = candidate_by_id.get(str(row.get("candidate_id") or ""))
        if candidate is None:
            continue
        raw, leaf_ids = _tree_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            split_values=component_split_values,
            split_present=component_split_present,
            row_count=len(component["candidate_identity_keys"]),
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        row["calibration_rows"] = _calibration_detail_rows(
            candidate=candidate,
            normalized=normalized,
            leaf_ids=leaf_ids,
            component=component,
            calibration_context=calibration_context,
        )
        row["leaf_summary"] = _leaf_summary(
            leaf_ids,
            candidate.expert_ids,
            normalized=normalized,
            component=component,
            calibration_rows=row["calibration_rows"],
        )
        row["band_samples"] = _band_samples(
            normalized,
            component=component,
            segment_ids=leaf_ids,
            expert_ids=candidate.expert_ids,
            per_band=8,
        )
    return ranked


def _tree_raw_scores(
    candidate: TreeCandidate,
    *,
    raw_by_expert: Mapping[str, object],
    split_values: Mapping[str, object],
    split_present: Mapping[str, object],
    row_count: int,
) -> tuple[object, object]:
    if candidate.root is None:
        leaf_ids = np.zeros(row_count, dtype=np.int64)
        return np.asarray(raw_by_expert[candidate.expert_ids[0]], dtype=np.float32), leaf_ids
    leaf_ids = _tree_leaf_ids_for_values(
        root=candidate.root,
        child_side=candidate.child_side,
        child=candidate.child,
        split_values=split_values,
        split_present=split_present,
    )
    raw = np.empty(row_count, dtype=np.float32)
    for leaf_id, expert_id in enumerate(candidate.expert_ids):
        mask = leaf_ids == leaf_id
        raw[mask] = raw_by_expert[expert_id][mask]
    return raw, leaf_ids


def _tree_leaf_ids_for_values(
    *,
    root: SplitSpec,
    child_side: str | None,
    child: SplitSpec | None,
    split_values: Mapping[str, object],
    split_present: Mapping[str, object],
) -> object:
    root_left = _split_mask(root, split_values=split_values, split_present=split_present)
    if child is None or child_side is None:
        return np.where(root_left, 0, 1).astype(np.int64)
    child_left = _split_mask(child, split_values=split_values, split_present=split_present)
    if child_side == "left":
        return np.where(root_left, np.where(child_left, 0, 1), 2).astype(np.int64)
    if child_side == "right":
        return np.where(root_left, 0, np.where(child_left, 1, 2)).astype(np.int64)
    raise ValueError(f"Unsupported child side: {child_side}")


def _split_mask(
    split: SplitSpec,
    *,
    split_values: Mapping[str, object],
    split_present: Mapping[str, object],
) -> object:
    values = np.asarray(split_values[split.signal], dtype=np.float32)
    present = np.asarray(split_present[split.signal], dtype=bool)
    comparison = values <= float(split.threshold)
    return np.where(present, comparison, split.missing_left)


def _split_specs(
    component: object,
    *,
    split_signals: Sequence[str],
    threshold_quantiles: Sequence[float],
    manual_split_thresholds: Mapping[str, Sequence[float]],
) -> list[SplitSpec]:
    values_by_signal = _component_split_values(component)
    present_by_signal = _component_split_present(component)
    specs: list[SplitSpec] = []
    for signal in split_signals:
        if signal not in values_by_signal:
            continue
        values = np.asarray(values_by_signal[signal], dtype=np.float32)
        present = np.asarray(present_by_signal[signal], dtype=bool)
        finite = present & np.isfinite(values)
        if int(finite.sum()) < 50:
            continue
        thresholds = sorted(
            {
                round(float(np.quantile(values[finite], quantile)), 4)
                for quantile in threshold_quantiles
            }
            | {round(float(threshold), 4) for threshold in manual_split_thresholds.get(signal, ())}
        )
        missing_options = (False, True) if int((~present).sum()) else (False,)
        for threshold in thresholds:
            if threshold <= 0.0 or threshold >= 1.0:
                continue
            for missing_left in missing_options:
                specs.append(
                    SplitSpec(
                        signal=signal,
                        threshold=threshold,
                        missing_left=missing_left,
                    )
                )
    return specs


def _limit_split_specs(specs: Sequence[SplitSpec], max_split_specs: int) -> list[SplitSpec]:
    if max_split_specs <= 0:
        return list(specs)
    return list(specs[:max_split_specs])


def _component_split_values(component: object) -> dict[str, object]:
    names = [str(value) for value in component["component_names"]]
    values = np.asarray(component["component_values"], dtype=np.float32)
    result = {name: values[:, index] for index, name in enumerate(names)}
    result["frequency"] = np.asarray(component["frequency_values"], dtype=np.float32)
    return result


def _component_split_present(component: object) -> dict[str, object]:
    names = [str(value) for value in component["component_names"]]
    present = np.asarray(component["component_present"], dtype=bool)
    result = {name: present[:, index] for index, name in enumerate(names)}
    result["frequency"] = np.isfinite(component["frequency_values"])
    return result


def _model_tree_calibration_context(calibration: object, component: object) -> dict[str, object]:
    component_by_identity = {
        str(identity): index
        for index, identity in enumerate(component["candidate_identity_keys"])
        if str(identity)
    }
    component_by_lemma_reading = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(component["lemmas"], component["readings"]))
    }
    indices: list[int] = []
    for identity, lemma, reading in zip(
        calibration["calibration_identity_keys"],
        calibration["calibration_lemmas"],
        calibration["calibration_readings"],
    ):
        index = component_by_identity.get(str(identity))
        if index is None:
            index = component_by_lemma_reading.get((str(lemma), str(reading)))
        indices.append(-1 if index is None else int(index))
    component_indices = np.asarray(indices, dtype=np.int64)
    component_split_values = _component_split_values(component)
    component_split_present = _component_split_present(component)
    split_values: dict[str, object] = {}
    split_present: dict[str, object] = {}
    valid = component_indices >= 0
    for signal, values in component_split_values.items():
        projected = np.full(len(component_indices), np.nan, dtype=np.float32)
        projected[valid] = values[component_indices[valid]]
        split_values[signal] = projected
    for signal, present in component_split_present.items():
        projected_present = np.zeros(len(component_indices), dtype=bool)
        projected_present[valid] = present[component_indices[valid]]
        split_present[signal] = projected_present
    labels = [
        f"{lemma}/{reading}" if str(reading) else str(lemma)
        for lemma, reading in zip(
            calibration["calibration_lemmas"],
            calibration["calibration_readings"],
        )
    ]
    expected_values = np.asarray(calibration["expected_values"], dtype=np.float32)
    expected_bands = np.asarray(
        [str(value) for value in calibration["expected_bands"]],
        dtype=object,
    )
    expected_bucket_ids = np.full(len(expected_bands), -1, dtype=np.int8)
    expected_bucket_ids[expected_bands == "beginner"] = 0
    expected_bucket_ids[expected_bands == "intermediate"] = 1
    expected_bucket_ids[expected_bands == "advanced"] = 2
    pair_left, pair_right, pair_expected_gap = _sampled_pairwise_indices(expected_values)
    return {
        "component_indices": component_indices,
        "identity_keys": [str(value) for value in calibration["calibration_identity_keys"]],
        "lemmas": [str(value) for value in calibration["calibration_lemmas"]],
        "readings": [str(value) for value in calibration["calibration_readings"]],
        "split_values": split_values,
        "split_present": split_present,
        "observed_matrix": np.asarray(calibration["observed_values"], dtype=np.float32),
        "expected_values": expected_values,
        "expected_bands": [str(value) for value in expected_bands],
        "expected_bucket_ids": expected_bucket_ids,
        "expected_finite": np.isfinite(expected_values),
        "beginner_core_mask": np.isfinite(expected_values) & (expected_values <= BEGINNER_CORE_MAX),
        "beginner_broad_mask": np.isfinite(expected_values)
        & (expected_values <= BEGINNER_BROAD_MAX),
        "upper_tail_mask": np.isfinite(expected_values) & (expected_values >= UPPER_TAIL_MIN),
        "high_tail_mask": np.isfinite(expected_values) & (expected_values >= HIGH_TAIL_MIN),
        "pair_left": pair_left,
        "pair_right": pair_right,
        "pair_expected_gap": pair_expected_gap,
        "labels": labels,
    }


def _leaf_summary(
    leaf_ids: object,
    expert_ids: Sequence[str],
    *,
    normalized: object | None = None,
    component: object | None = None,
    calibration_rows: object | None = None,
) -> list[dict[str, object]]:
    parsed_leaf_ids = np.asarray(leaf_ids, dtype=np.int64)
    calibration_by_leaf = _calibration_status_counts_by_leaf(calibration_rows)
    rows: list[dict[str, object]] = []
    for leaf_id in range(int(np.max(parsed_leaf_ids)) + 1 if len(parsed_leaf_ids) else 0):
        mask = parsed_leaf_ids == leaf_id
        row: dict[str, object] = {
            "leaf_id": leaf_id,
            "expert_id": expert_ids[leaf_id] if leaf_id < len(expert_ids) else "",
            "row_count": int(mask.sum()),
        }
        if normalized is not None:
            row["difficulty_summary"] = _difficulty_value_summary(
                np.asarray(normalized, dtype=np.float32)[mask]
            )
            row["difficulty_band_counts"] = _difficulty_band_counts(
                np.asarray(normalized, dtype=np.float32)[mask]
            )
        if component is not None:
            row["candidate_state_counts"] = _top_counts(component["candidate_states"][mask])
            row["problem_class_counts"] = _top_counts(component["problem_classes"][mask])
            row["signal_averages"] = _leaf_signal_averages(component, mask)
        if leaf_id in calibration_by_leaf:
            row["calibration_status_counts"] = calibration_by_leaf[leaf_id]
        rows.append(row)
    return rows


def _calibration_detail_rows(
    *,
    candidate: TreeCandidate,
    normalized: object,
    leaf_ids: object,
    component: object,
    calibration_context: Mapping[str, object],
) -> list[dict[str, object]]:
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    expected_values = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    expected_bands = [
        str(value) for value in _sequence_values(calibration_context["expected_bands"])
    ]
    identity_keys = [str(value) for value in _sequence_values(calibration_context["identity_keys"])]
    lemmas = [str(value) for value in _sequence_values(calibration_context["lemmas"])]
    readings = [str(value) for value in _sequence_values(calibration_context["readings"])]
    labels = [str(value) for value in _sequence_values(calibration_context["labels"])]
    normalized_values = np.asarray(normalized, dtype=np.float32)
    parsed_leaf_ids = np.asarray(leaf_ids, dtype=np.int64)
    rows: list[dict[str, object]] = []
    component_names = [str(value) for value in component["component_names"]]
    component_values = np.asarray(component["component_values"], dtype=np.float32)
    component_present = np.asarray(component["component_present"], dtype=bool)
    frequency_values = np.asarray(component["frequency_values"], dtype=np.float32)
    for calibration_index, component_index in enumerate(component_indices):
        observed_value = None
        observed_band = ""
        leaf_id = None
        expert_id = ""
        candidate_state = ""
        problem_class = ""
        core_rank = None
        frequency = None
        signals: dict[str, object] = {}
        if component_index >= 0:
            row_index = int(component_index)
            observed = float(normalized_values[row_index])
            if np.isfinite(observed):
                observed_value = _rounded(observed)
                observed_band = _difficulty_band(observed)
            leaf_id = int(parsed_leaf_ids[row_index])
            if 0 <= leaf_id < len(candidate.expert_ids):
                expert_id = candidate.expert_ids[leaf_id]
            candidate_state = str(component["candidate_states"][row_index])
            problem_class = str(component["problem_classes"][row_index])
            rank = float(component["core_ranks"][row_index])
            core_rank = _rounded(rank) if np.isfinite(rank) else None
            freq = float(frequency_values[row_index])
            frequency = _rounded(freq) if np.isfinite(freq) else None
            signals = {
                name: (
                    _rounded(float(component_values[row_index, signal_index]))
                    if component_present[row_index, signal_index]
                    and np.isfinite(component_values[row_index, signal_index])
                    else None
                )
                for signal_index, name in enumerate(component_names)
            }
        expected = float(expected_values[calibration_index])
        expected_value = _rounded(expected) if np.isfinite(expected) else None
        expected_band = (
            expected_bands[calibration_index] if calibration_index < len(expected_bands) else ""
        )
        error = (
            _rounded(abs(float(observed_value) - float(expected_value)))
            if observed_value is not None and expected_value is not None
            else None
        )
        rows.append(
            {
                "calibration_index": calibration_index,
                "identity_key": identity_keys[calibration_index],
                "lemma": lemmas[calibration_index],
                "reading": readings[calibration_index],
                "label": labels[calibration_index],
                "component_index": int(component_index),
                "expected_value": expected_value,
                "observed_value": observed_value,
                "absolute_error": error,
                "expected_band": expected_band,
                "observed_band": observed_band,
                "difficulty_status": _calibration_status(expected_band, observed_band),
                "direction": _calibration_error_direction(expected_value, observed_value),
                "leaf_id": leaf_id,
                "expert_id": expert_id,
                "candidate_state": candidate_state,
                "problem_class": problem_class,
                "core_rank": core_rank,
                "frequency": frequency,
                "signals": signals,
            }
        )
    return rows


def _calibration_status(expected_band: str, observed_band: str) -> str:
    expected = str(expected_band or "").strip()
    observed = str(observed_band or "").strip()
    if not expected:
        return "not_labeled"
    if not observed:
        return "missing"
    if expected == observed:
        return "match"
    return "mismatch"


def _calibration_error_direction(
    expected_value: object,
    observed_value: object,
) -> str:
    expected = _optional_float(expected_value)
    observed = _optional_float(observed_value)
    if expected is None or observed is None:
        return ""
    if observed > expected:
        return "too_high"
    if observed < expected:
        return "too_low"
    return "exact"


def _calibration_status_counts_by_leaf(rows: object) -> dict[int, dict[str, int]]:
    counts: dict[int, dict[str, int]] = {}
    for row in _mapping_rows(rows):
        leaf_id = row.get("leaf_id")
        if not isinstance(leaf_id, int):
            continue
        status = str(row.get("difficulty_status") or "unknown")
        counts.setdefault(leaf_id, {})
        counts[leaf_id][status] = counts[leaf_id].get(status, 0) + 1
    return counts


def _difficulty_value_summary(values: object) -> dict[str, object]:
    parsed = np.asarray(values, dtype=np.float32)
    finite = parsed[np.isfinite(parsed)]
    if not len(finite):
        return {
            "count": 0,
            "min": None,
            "avg": None,
            "max": None,
        }
    return {
        "count": int(len(finite)),
        "min": _rounded(float(finite.min())),
        "avg": _rounded(float(finite.mean())),
        "max": _rounded(float(finite.max())),
    }


def _difficulty_band_counts(values: object) -> dict[str, int]:
    counts = {"beginner": 0, "intermediate": 0, "advanced": 0, "missing": 0}
    for value in np.asarray(values, dtype=np.float32):
        if not np.isfinite(value):
            counts["missing"] += 1
            continue
        band = _difficulty_band(float(value))
        counts[band or "missing"] = counts.get(band or "missing", 0) + 1
    return {key: value for key, value in counts.items() if value}


def _top_counts(values: object, *, limit: int = 8) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "")
        if not key:
            key = "(blank)"
        counts[key] = counts.get(key, 0) + 1
    return dict(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    )


def _leaf_signal_averages(component: object, mask: object) -> dict[str, object]:
    parsed_mask = np.asarray(mask, dtype=bool)
    names = [str(value) for value in component["component_names"]]
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    result = {
        "frequency": _finite_average(
            np.asarray(component["frequency_values"], dtype=np.float32)[parsed_mask]
        )
    }
    for index, name in enumerate(names):
        valid = parsed_mask & present[:, index] & np.isfinite(values[:, index])
        result[name] = _finite_average(values[valid, index])
    return {key: value for key, value in result.items() if value is not None}


def _finite_average(values: object) -> float | None:
    parsed = np.asarray(values, dtype=np.float32)
    finite = parsed[np.isfinite(parsed)]
    if not len(finite):
        return None
    return _rounded(float(finite.mean()))


def _top_tree_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    best_by_id: dict[str, Mapping[str, object]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        previous = best_by_id.get(candidate_id)
        if previous is None or _tree_sort_key(row) > _tree_sort_key(previous):
            best_by_id[candidate_id] = row
    return [
        dict(row)
        for row in sorted(
            best_by_id.values(),
            key=_tree_sort_key,
            reverse=True,
        )[:limit]
    ]


def _tree_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    scores = _mapping(row.get("scores"))
    return (
        _optional_float(scores.get("balanced_score")) or -1.0,
        _optional_float(scores.get("pairwise_order_score")) or -1.0,
        _optional_float(scores.get("numeric_mae_score")) or -1.0,
    )


def _tree_json(candidate: TreeCandidate) -> dict[str, object]:
    return {
        "root": _split_json(candidate.root),
        "child_side": candidate.child_side,
        "child": _split_json(candidate.child),
        "expert_ids": list(candidate.expert_ids),
    }


def _split_json(split: SplitSpec | None) -> dict[str, object] | None:
    if split is None:
        return None
    return {
        "signal": split.signal,
        "threshold": _rounded(split.threshold),
        "missing_left": split.missing_left,
        "split_id": split.split_id,
    }


def _split_from_json(row: Mapping[str, object]) -> SplitSpec | None:
    if not row:
        return None
    threshold = _optional_float(row.get("threshold"))
    if threshold is None:
        return None
    return SplitSpec(
        signal=str(row.get("signal") or ""),
        threshold=threshold,
        missing_left=bool(row.get("missing_left")),
    )


def _tree_from_row(row: Mapping[str, object]) -> TreeCandidate:
    tree = _mapping(row.get("tree"))
    root = _split_from_json(_mapping(tree.get("root")))
    child = _split_from_json(_mapping(tree.get("child")))
    return TreeCandidate(
        candidate_id=str(row.get("candidate_id") or ""),
        root=root,
        child_side=str(tree.get("child_side") or "") or None,
        child=child,
        expert_ids=tuple(str(value) for value in _sequence_values(tree.get("expert_ids"))),
    )


def write_calibration_rows_csv(path: Path, report: Mapping[str, object]) -> None:
    rows = _flat_calibration_rows(report)
    base_fields = [
        "rank",
        "candidate_id",
        "label",
        "lemma",
        "reading",
        "expected_value",
        "observed_value",
        "absolute_error",
        "expected_band",
        "observed_band",
        "difficulty_status",
        "direction",
        "leaf_id",
        "expert_id",
        "candidate_state",
        "problem_class",
        "core_rank",
        "frequency",
        "component_index",
        "identity_key",
    ]
    signal_fields = sorted(
        {key for row in rows for key in row if key.startswith("signal_") and key not in base_fields}
    )
    fieldnames = base_fields + signal_fields
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_calibration_rows_markdown(report: Mapping[str, object]) -> str:
    rows_by_candidate = [
        row
        for row in _mapping_rows(report.get("exact_top"))
        if _mapping_rows(row.get("calibration_rows"))
    ]
    lines = [
        "# en-ja Learner Difficulty Model-Tree Calibration Rows",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Detailed candidates: `{len(rows_by_candidate)}`",
        f"- Flat row count: `{len(_flat_calibration_rows(report))}`",
        "",
        "## Candidate Summary",
        "",
        "| Rank | Candidate | Balanced | MAE | Bucket | Pairwise | Status Counts |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, row in enumerate(rows_by_candidate[:20], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            "| "
            f"{rank} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(metrics.get('mae'))}` | "
            f"`{_escape(metrics.get('bucket_accuracy'))}` | "
            f"`{_escape(metrics.get('pairwise_accuracy'))}` | "
            f"`{_compact_counts(_status_counts(row.get('calibration_rows')))}` |"
        )
    for rank, row in enumerate(rows_by_candidate[:5], start=1):
        detail_rows = _mapping_rows(row.get("calibration_rows"))
        lines.extend(
            [
                "",
                f"## Rank {rank}: `{_escape(row.get('candidate_id'))}`",
                "",
                f"- Tree: `{_tree_summary(row)}`",
                f"- Status counts: `{_compact_counts(_status_counts(detail_rows))}`",
                "",
                "### Mismatches",
                "",
            ]
        )
        mismatches = [
            detail
            for detail in detail_rows
            if str(detail.get("difficulty_status") or "") == "mismatch"
        ]
        lines.extend(_calibration_rows_table(mismatches, limit=40))
        lines.extend(["", "### Largest Numeric Errors", ""])
        numeric_errors = sorted(
            [
                detail
                for detail in detail_rows
                if _optional_float(detail.get("absolute_error")) is not None
            ],
            key=lambda detail: _optional_float(detail.get("absolute_error")) or -1.0,
            reverse=True,
        )
        lines.extend(_calibration_rows_table(numeric_errors, limit=40))
        if rank == 1:
            lines.extend(["", "### Full Best-Candidate Rows", ""])
            lines.extend(_calibration_rows_table(detail_rows, limit=len(detail_rows)))
    return "\n".join(lines).rstrip() + "\n"


def _flat_calibration_rows(report: Mapping[str, object]) -> list[dict[str, object]]:
    flat_rows: list[dict[str, object]] = []
    for rank, candidate in enumerate(_mapping_rows(report.get("exact_top")), start=1):
        candidate_id = str(candidate.get("candidate_id") or "")
        for row in _mapping_rows(candidate.get("calibration_rows")):
            flat = {
                "rank": rank,
                "candidate_id": candidate_id,
                "label": row.get("label"),
                "lemma": row.get("lemma"),
                "reading": row.get("reading"),
                "expected_value": row.get("expected_value"),
                "observed_value": row.get("observed_value"),
                "absolute_error": row.get("absolute_error"),
                "expected_band": row.get("expected_band"),
                "observed_band": row.get("observed_band"),
                "difficulty_status": row.get("difficulty_status"),
                "direction": row.get("direction"),
                "leaf_id": row.get("leaf_id"),
                "expert_id": row.get("expert_id"),
                "candidate_state": row.get("candidate_state"),
                "problem_class": row.get("problem_class"),
                "core_rank": row.get("core_rank"),
                "frequency": row.get("frequency"),
                "component_index": row.get("component_index"),
                "identity_key": row.get("identity_key"),
            }
            for signal, value in _mapping(row.get("signals")).items():
                flat[f"signal_{signal}"] = value
            flat_rows.append(flat)
    return flat_rows


def _status_counts(rows: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in _mapping_rows(rows):
        status = str(row.get("difficulty_status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _calibration_rows_table(rows: Sequence[Mapping[str, object]], *, limit: int) -> list[str]:
    if not rows:
        return ["No rows."]
    lines = [
        "| Label | Expected | Observed | Error | Status | Direction | Leaf | State | Problem |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            f"`{_escape(row.get('label'))}` | "
            f"`{_escape(row.get('expected_value'))}` {_escape(row.get('expected_band'))} | "
            f"`{_escape(row.get('observed_value'))}` {_escape(row.get('observed_band'))} | "
            f"`{_escape(row.get('absolute_error'))}` | "
            f"`{_escape(row.get('difficulty_status'))}` | "
            f"`{_escape(row.get('direction'))}` | "
            f"`{_escape(row.get('leaf_id'))}` | "
            f"`{_escape(row.get('candidate_state'))}` | "
            f"`{_escape(row.get('problem_class'))}` |"
        )
    if len(rows) > limit:
        lines.append(
            f"| ... | ... | ... | ... | ... | ... | ... | ... | {len(rows) - limit} more rows |"
        )
    return lines


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Learner Difficulty Model-Tree Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Trace variants: `{_escape(inputs.get('trace_variant_count'))}`",
        f"- Expert-eligible variants: `{_escape(inputs.get('expert_eligible_variant_count'))}`",
        f"- Expert pool size: `{_escape(inputs.get('expert_pool_size'))}`",
        f"- Expert exclude signals: `{_escape(', '.join(_sequence_values(inputs.get('expert_exclude_signals'))))}`",
        f"- Tree depth: `{_escape(inputs.get('tree_depth'))}`",
        f"- Max split specs: `{_escape(inputs.get('max_split_specs'))}`",
        f"- Split specs: `{_escape(inputs.get('split_spec_count'))}`",
        f"- Root retained: `{_escape(inputs.get('root_retained'))}`",
        f"- Approximate retained: `{_escape(inputs.get('approximate_retained'))}`",
        f"- Exact evaluated: `{_escape(inputs.get('exact_limit'))}`",
        "",
        "## Exact Top Trees",
        "",
        (
            "| Rank | Candidate | Balanced | MAE | Bucket | Pairwise | Spearman | "
            "Beginner | High tail | Tree |"
        ),
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(_mapping_rows(report.get("exact_top"))[:20], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            "| "
            f"{index} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(metrics.get('mae'))}` | "
            f"`{_escape(metrics.get('bucket_accuracy'))}` | "
            f"`{_escape(metrics.get('pairwise_accuracy'))}` | "
            f"`{_escape(metrics.get('spearman'))}` | "
            f"`{_escape(metrics.get('beginner_core_pass_rate'))}` | "
            f"`{_escape(metrics.get('high_tail_pass_rate'))}` | "
            f"`{_tree_summary(row)}` |"
        )
    lines.extend(["", "## Top Tree Details", ""])
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        lines.extend(
            [
                f"### `{_escape(row.get('candidate_id'))}`",
                "",
                f"- Tree: `{_tree_summary(row)}`",
                f"- Scores: `{_compact_counts(row.get('scores'))}`",
                f"- Metrics: `{_compact_counts(row.get('metrics'))}`",
                "",
                "Leaf summary:",
                "",
            ]
        )
        lines.extend(_leaf_summary_table(_mapping_rows(row.get("leaf_summary"))))
        mismatches = _mapping_rows(row.get("difficulty_mismatches"))
        if mismatches:
            text = ", ".join(
                f"{item.get('label')} ({item.get('expected')}->{item.get('observed')})"
                for item in mismatches[:12]
            )
            lines.append(f"- Difficulty mismatches: {text}")
        lines.extend(["", "Band samples:", ""])
        for band in _mapping_rows(row.get("band_samples")):
            samples = ", ".join(
                f"{sample.get('lemma')}({sample.get('reading')})"
                for sample in _mapping_rows(band.get("samples"))[:8]
            )
            lines.append(
                f"- `{_escape(band.get('band'))}` count `{_escape(band.get('count'))}`: {samples}"
            )
        lines.append("")
    lines.extend(["", "## Expert Pool", ""])
    lines.extend(
        [
            "| Expert | Balanced | Bucket | Pairwise | Beginner | High tail | Weights | Cap |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for expert in _mapping_rows(report.get("expert_pool")):
        scores = _mapping(expert.get("source_scores"))
        lines.append(
            "| "
            f"`{_escape(expert.get('variant_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(scores.get('bucket_accuracy_score'))}` | "
            f"`{_escape(scores.get('pairwise_order_score'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_compact_counts(expert.get('weights'))}` | "
            f"`{_escape(expert.get('max_shift_from_frequency'))}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _leaf_summary_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["No leaf summary rows."]
    lines = [
        "| Leaf | Expert | Rows | Avg | Min | Max | Bands | Calibration | Problem Classes |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        difficulty = _mapping(row.get("difficulty_summary"))
        lines.append(
            "| "
            f"`{_escape(row.get('leaf_id'))}` | "
            f"`{_escape(row.get('expert_id'))}` | "
            f"`{_escape(row.get('row_count'))}` | "
            f"`{_escape(difficulty.get('avg'))}` | "
            f"`{_escape(difficulty.get('min'))}` | "
            f"`{_escape(difficulty.get('max'))}` | "
            f"`{_compact_counts(row.get('difficulty_band_counts'))}` | "
            f"`{_compact_counts(row.get('calibration_status_counts'))}` | "
            f"`{_compact_counts(row.get('problem_class_counts'))}` |"
        )
    return lines


def _tree_summary(row: Mapping[str, object]) -> str:
    tree = _mapping(row.get("tree"))
    root = _mapping(tree.get("root"))
    child = _mapping(tree.get("child"))
    parts = []
    if root:
        parts.append(f"root {root.get('split_id')}")
    if child:
        parts.append(f"{tree.get('child_side')} child {child.get('split_id')}")
    parts.append(
        "experts " + ", ".join(str(value) for value in _sequence_values(tree.get("expert_ids")))
    )
    return "; ".join(parts)


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in str(value or "").split(",") if item.strip())


def _parse_float_csv(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in str(value or "").split(",") if item.strip())


def _parse_manual_thresholds(value: str) -> dict[str, tuple[float, ...]]:
    parsed: dict[str, tuple[float, ...]] = {}
    for group in str(value or "").split(";"):
        group = group.strip()
        if not group:
            continue
        signal, sep, thresholds = group.partition(":")
        if not sep:
            raise ValueError(f"Expected manual threshold group as signal:v1,v2, got {group!r}")
        parsed[signal.strip()] = _parse_float_csv(thresholds)
    return parsed


def _format_manual_thresholds(value: Mapping[str, Sequence[float]]) -> str:
    return ";".join(
        f"{signal}:{','.join(f'{float(threshold):g}' for threshold in thresholds)}"
        for signal, thresholds in sorted(value.items())
    )


if __name__ == "__main__":
    raise SystemExit(main())
