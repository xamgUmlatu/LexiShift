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
from srs_learner_difficulty_model_family_search_en_ja import (  # noqa: E402
    BoostSpec,
    FloorSpec,
    ModelCandidate,
    REVIEWED_FOCUS_LABELS,
    SoftMixSpec,
    _candidate_raw_scores,
    _reviewed_focus_metrics,
    _signal_arrays,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    Expert,
    _band_samples,
    _calibration_context,
    _compact_counts,
    _difficulty_metrics,
    _escape,
    _load_json,
    _mapping,
    _mapping_rows,
    _optional_float,
    _raw_scores_for_expert,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)


DEFAULT_FAMILY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_search_en_ja_latest.json"
)
DEFAULT_BASELINE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_tree_search_en_ja_reading_wago_depth2_latest.json"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_calibration_matrix_latest.npz"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_component_matrix_latest.npz"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_meta_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_meta_search_en_ja_latest.md"
)
DEFAULT_CALIBRATION_ROWS_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_meta_calibration_rows_en_ja_latest.csv"
)
DEFAULT_CALIBRATION_ROWS_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_meta_calibration_rows_en_ja_latest.md"
)
DEFAULT_SPLIT_SIGNALS = (
    "frequency",
    "frequency_ease",
    "bccwj_domain_rank_spread",
    "bccwj_domain_rank_variability",
    "bccwj_domain_profile_variability",
    "bccwj_rank_spread",
    "bccwj_rank_variability",
    "bccwj_fixed_variable_rank_delta",
    "frequency_source_known",
    "source_coverage_count",
    "jmdict_priority_known",
    "jmdict_lexical_known",
    "lexical_source_known",
    "jmnedict_name_known",
    "pedagogical_source_known",
    "orthographic_source_known",
    "jmdict_ambiguity_score",
    "jmdict_reading_complexity_score",
    "jmdict_restriction_complexity_score",
    "common_jmdict_ambiguity_score",
    "common_reading_complexity_score",
    "common_restriction_complexity_score",
    "jmdict_register_domain_score",
    "common_register_domain_score",
    "jmdict_field_marked_flag",
    "jmdict_kanji_form_marked_flag",
    "jmdict_reading_form_marked_flag",
    "jmdict_sense_restricted_flag",
    "jmdict_no_kanji_reading_flag",
    "jmdict_sinitic_source_flag",
    "jmdict_source_type_flag",
    "jmdict_wasei_source_flag",
    "kango_mid_signal",
    "common_kango_register_domain_score",
    "common_kango_written_burden",
    "common_kango_ambiguity_score",
    "common_kango_complexity_score",
    "kango_common_priority_risk",
    "kanjidic_nanori_reading_count_score",
    "kanjidic_variant_type_count_score",
    "kanjivg_variant_structure",
    "rare_wago_tail_risk",
    "written_wago_tail_risk",
    "rare_wago_obscure_written_risk",
    "max_written_form_burden",
    "wtype_kango_risk",
    "wtype_wago_ease",
)
DEFAULT_MANUAL_SPLIT_THRESHOLDS = {
    "frequency": (0.35, 0.50, 0.65, 0.75, 0.85, 0.90),
    "frequency_ease": (0.20, 0.35, 0.50, 0.65, 0.80),
    "kango_mid_signal": (0.25, 0.35, 0.45, 0.55, 0.65),
    "common_kango_complexity_score": (0.10, 0.20, 0.35, 0.50),
    "kango_common_priority_risk": (0.10, 0.25, 0.45),
    "common_jmdict_ambiguity_score": (0.10, 0.20, 0.35, 0.50),
    "common_reading_complexity_score": (0.10, 0.20, 0.35, 0.50),
    "common_register_domain_score": (0.10, 0.20, 0.35, 0.50),
    "rare_wago_tail_risk": (0.10, 0.25, 0.50, 0.75),
    "written_wago_tail_risk": (0.10, 0.25, 0.40, 0.55),
    "rare_wago_obscure_written_risk": (0.25, 0.50, 0.75),
    "max_written_form_burden": (0.35, 0.55, 0.75),
    "wtype_kango_risk": (0.50,),
    "wtype_wago_ease": (0.50,),
}
DEFAULT_THRESHOLD_QUANTILES = (0.20, 0.35, 0.50, 0.65, 0.80)
BASELINE_TOLERANCES = {
    "balanced_score": 0.000,
    "bucket_accuracy_score": 0.005,
    "pairwise_order_score": 0.005,
    "beginner_core_score": 0.000,
    "high_tail_score": 0.000,
    "upper_tail_score": 0.000,
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
class MetaCandidate:
    candidate_id: str
    root: SplitSpec | None
    child_side: str | None
    child: SplitSpec | None
    expert_ids: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only post-sweep/meta search that blends model-family "
            "candidates across signal-gated segments."
        )
    )
    parser.add_argument("--family-json", type=Path, default=DEFAULT_FAMILY_JSON)
    parser.add_argument("--baseline-json", type=Path, default=DEFAULT_BASELINE_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--candidate-pool-size", type=int, default=48)
    parser.add_argument("--top-per-leaderboard", type=int, default=10)
    parser.add_argument(
        "--split-signals",
        default=",".join(DEFAULT_SPLIT_SIGNALS),
    )
    parser.add_argument(
        "--threshold-quantiles",
        default=",".join(str(value) for value in DEFAULT_THRESHOLD_QUANTILES),
    )
    parser.add_argument(
        "--manual-split-thresholds",
        default=_format_manual_thresholds(DEFAULT_MANUAL_SPLIT_THRESHOLDS),
    )
    parser.add_argument("--max-split-specs", type=int, default=32)
    parser.add_argument("--leaf-candidate-limit", type=int, default=4)
    parser.add_argument("--leaf-global-candidate-limit", type=int, default=3)
    parser.add_argument("--root-retain-limit", type=int, default=80)
    parser.add_argument("--approximate-retain-limit", type=int, default=1500)
    parser.add_argument("--exact-limit", type=int, default=240)
    parser.add_argument("--detail-candidate-limit", type=int, default=20)
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
        family_json=_resolve_path(args.family_json),
        baseline_json=_resolve_path(args.baseline_json),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        candidate_pool_size=max(1, int(args.candidate_pool_size)),
        top_per_leaderboard=max(1, int(args.top_per_leaderboard)),
        split_signals=_parse_csv(args.split_signals),
        threshold_quantiles=_parse_float_csv(args.threshold_quantiles),
        manual_split_thresholds=_parse_manual_thresholds(args.manual_split_thresholds),
        max_split_specs=max(0, int(args.max_split_specs)),
        leaf_candidate_limit=max(1, int(args.leaf_candidate_limit)),
        leaf_global_candidate_limit=max(0, int(args.leaf_global_candidate_limit)),
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
    calibration_rows_csv_out.write_text(_render_calibration_rows_csv(report), encoding="utf-8")
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
    family_json: Path,
    baseline_json: Path,
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    candidate_pool_size: int = 48,
    top_per_leaderboard: int = 10,
    split_signals: Sequence[str] = DEFAULT_SPLIT_SIGNALS,
    threshold_quantiles: Sequence[float] = DEFAULT_THRESHOLD_QUANTILES,
    manual_split_thresholds: Mapping[str, Sequence[float]] = DEFAULT_MANUAL_SPLIT_THRESHOLDS,
    max_split_specs: int = 32,
    leaf_candidate_limit: int = 4,
    leaf_global_candidate_limit: int = 3,
    root_retain_limit: int = 80,
    approximate_retain_limit: int = 1500,
    exact_limit: int = 240,
    detail_candidate_limit: int = 20,
) -> dict[str, object]:
    family_report = _load_json(family_json)
    baseline_report = _load_json(baseline_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    baseline = _baseline_scores(baseline_report)
    experts = [_expert_from_json(row) for row in _mapping_rows(family_report.get("expert_pool"))]
    family_candidates = [
        _model_candidate_from_row(row)
        for row in _mapping_rows(family_report.get("exact_top"))
        if row.get("candidate_id")
    ]
    selected_family_candidates = _select_family_candidates(
        family_report,
        family_candidates=family_candidates,
        candidate_pool_size=candidate_pool_size,
        top_per_leaderboard=top_per_leaderboard,
    )
    raw_by_expert = {
        expert.variant_id: _raw_scores_for_expert(expert, component) for expert in experts
    }
    signal_arrays = _signal_arrays(component)
    raw_by_family_candidate = {
        candidate.candidate_id: _candidate_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )
        for candidate in selected_family_candidates
    }
    calibration_context = _calibration_context(calibration, component)
    split_context = _split_context(component, calibration_context)
    split_specs = _split_specs(
        split_context,
        split_signals=split_signals,
        threshold_quantiles=threshold_quantiles,
        manual_split_thresholds=manual_split_thresholds,
        max_split_specs=max_split_specs,
    )
    normalized_by_family_candidate = {
        candidate_id: _target_curve_normalize(
            raw,
            target_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
        )
        for candidate_id, raw in raw_by_family_candidate.items()
    }
    calibration_values = _calibration_values_by_candidate(
        normalized_by_family_candidate,
        calibration_context=calibration_context,
    )
    root_candidates = _linear_and_stump_candidates(
        family_candidates=selected_family_candidates,
        split_specs=split_specs,
        calibration_values=calibration_values,
        calibration_context=calibration_context,
        split_context=split_context,
        retain_limit=root_retain_limit,
        leaf_candidate_limit=leaf_candidate_limit,
        leaf_global_candidate_limit=leaf_global_candidate_limit,
    )
    approximate_candidates = _depth2_candidates(
        root_candidates=root_candidates,
        family_candidates=selected_family_candidates,
        split_specs=split_specs,
        calibration_values=calibration_values,
        calibration_context=calibration_context,
        split_context=split_context,
        retain_limit=approximate_retain_limit,
        leaf_candidate_limit=leaf_candidate_limit,
        leaf_global_candidate_limit=leaf_global_candidate_limit,
    )
    exact_input_candidates = _exact_candidate_rows(
        root_candidates=root_candidates,
        approximate_candidates=approximate_candidates,
        limit=exact_limit,
    )
    exact_candidates = _exact_evaluate_candidates(
        exact_input_candidates,
        component=component,
        calibration_context=calibration_context,
        split_context=split_context,
        raw_by_family_candidate=raw_by_family_candidate,
        baseline_scores=baseline,
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
                "family_json": family_json,
                "baseline_json": baseline_json,
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
            },
            code_paths=_model_family_meta_code_paths(),
            version_constants={
                "target_curve": TARGET_CURVE_ID,
            },
            argv=sys.argv,
        ),
        "method": {
            "model": "post_sweep_family_candidate_meta_blend",
            "candidate_pool": "selected from model-family leaderboards",
            "search": "linear, stump, and depth-2 hard signal-gated blends",
            "exact_stage": (
                "recomputes raw blend scores over the full component matrix and "
                "then applies global target-curve normalization"
            ),
            "normalization_curve_id": TARGET_CURVE_ID,
            "reviewed_focus_labels": sorted(REVIEWED_FOCUS_LABELS),
        },
        "inputs": {
            "family_json": _repo_or_home_path(family_json),
            "baseline_json": _repo_or_home_path(baseline_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "family_candidate_count": len(family_candidates),
            "selected_family_candidate_count": len(selected_family_candidates),
            "calibration_label_count": int(len(calibration["calibration_lemmas"])),
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "split_signals": list(split_signals),
            "split_spec_count": len(split_specs),
            "leaf_candidate_limit": leaf_candidate_limit,
            "leaf_global_candidate_limit": leaf_global_candidate_limit,
            "root_retained": len(root_candidates),
            "approximate_retained": len(approximate_candidates),
            "exact_selected": len(exact_input_candidates),
            "exact_limit": exact_limit,
            "detail_candidate_limit": detail_candidate_limit,
        },
        "baseline": baseline,
        "selected_family_candidates": [
            _family_candidate_json(candidate, family_report)
            for candidate in selected_family_candidates
        ],
        "split_specs": [_split_json(split) for split in split_specs],
        "root_top": root_candidates[:50],
        "approximate_top": approximate_candidates[:80],
        "exact_top": exact_candidates,
        "leaderboards": _leaderboards(exact_candidates, limit=25),
        "constrained_top": [
            row for row in exact_candidates if bool(row.get("passes_baseline_constraints"))
        ][:25],
    }


def _model_family_meta_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "difficulty_model_family_search": (
            SCRIPT_DIR / "srs_learner_difficulty_model_family_search_en_ja.py"
        ),
        "difficulty_piecewise_search": (
            SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
        ),
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


def _select_family_candidates(
    family_report: Mapping[str, object],
    *,
    family_candidates: Sequence[ModelCandidate],
    candidate_pool_size: int,
    top_per_leaderboard: int,
) -> list[ModelCandidate]:
    by_id = {candidate.candidate_id: candidate for candidate in family_candidates}
    selected: list[ModelCandidate] = []
    seen: set[str] = set()

    def add(candidate_id: object) -> None:
        parsed = str(candidate_id or "")
        if not parsed or parsed in seen or parsed not in by_id:
            return
        selected.append(by_id[parsed])
        seen.add(parsed)

    for row in _mapping_rows(family_report.get("exact_top"))[:top_per_leaderboard]:
        add(row.get("candidate_id"))
    for rows in _mapping(family_report.get("leaderboards")).values():
        for row in _mapping_rows(rows)[:top_per_leaderboard]:
            add(row.get("candidate_id"))
    for row in _mapping_rows(family_report.get("exact_top")):
        if len(selected) >= candidate_pool_size:
            break
        add(row.get("candidate_id"))
    return selected[:candidate_pool_size]


def _linear_and_stump_candidates(
    *,
    family_candidates: Sequence[ModelCandidate],
    split_specs: Sequence[SplitSpec],
    calibration_values: Mapping[str, object],
    calibration_context: Mapping[str, object],
    split_context: Mapping[str, object],
    retain_limit: int,
    leaf_candidate_limit: int,
    leaf_global_candidate_limit: int,
) -> list[dict[str, object]]:
    linear_rows: list[dict[str, object]] = []
    stump_rows: list[dict[str, object]] = []
    for candidate in family_candidates:
        meta = MetaCandidate(
            candidate_id=f"linear__{candidate.candidate_id}",
            root=None,
            child_side=None,
            child=None,
            expert_ids=(candidate.candidate_id,),
        )
        linear_rows.append(
            _approximate_meta_record(
                meta,
                calibration_values=calibration_values,
                calibration_context=calibration_context,
                split_context=split_context,
            )
        )
    global_ids = tuple(
        candidate.candidate_id for candidate in family_candidates[:leaf_global_candidate_limit]
    )
    for split in split_specs:
        leaf_ids = _leaf_ids_for_calibration(
            root=split,
            child_side=None,
            child=None,
            split_context=split_context,
        )
        left = _top_leaf_candidate_ids(
            family_candidates,
            mask=leaf_ids == 0,
            calibration_values=calibration_values,
            calibration_context=calibration_context,
            limit=leaf_candidate_limit,
            global_candidate_ids=global_ids,
        )
        right = _top_leaf_candidate_ids(
            family_candidates,
            mask=leaf_ids == 1,
            calibration_values=calibration_values,
            calibration_context=calibration_context,
            limit=leaf_candidate_limit,
            global_candidate_ids=global_ids,
        )
        for left_id in left:
            for right_id in right:
                if left_id == right_id:
                    continue
                meta = MetaCandidate(
                    candidate_id=f"stump__{split.split_id}__{left_id}__{right_id}",
                    root=split,
                    child_side=None,
                    child=None,
                    expert_ids=(left_id, right_id),
                )
                stump_rows.append(
                    _approximate_meta_record(
                        meta,
                        calibration_values=calibration_values,
                        calibration_context=calibration_context,
                        split_context=split_context,
                    )
                )
        if len(stump_rows) > retain_limit * 8:
            stump_rows = _top_meta_rows(
                stump_rows,
                limit=max(0, retain_limit - len(linear_rows)),
            )
    retained_stumps = _top_meta_rows(
        stump_rows,
        limit=max(0, retain_limit - len(linear_rows)),
    )
    return linear_rows + retained_stumps


def _exact_candidate_rows(
    *,
    root_candidates: Sequence[Mapping[str, object]],
    approximate_candidates: Sequence[Mapping[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()

    def add(row: Mapping[str, object]) -> None:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id or candidate_id in seen or len(rows) >= limit:
            return
        rows.append(dict(row))
        seen.add(candidate_id)

    # Always exact-check standalone family candidates. They are the best sanity
    # anchors for judging whether a segmented blend is actually adding value.
    for row in root_candidates:
        if not _mapping(_mapping(row.get("tree")).get("root")):
            add(row)
    for row in root_candidates[: max(20, limit // 4)]:
        add(row)
    for row in approximate_candidates:
        add(row)
    return rows


def _depth2_candidates(
    *,
    root_candidates: Sequence[Mapping[str, object]],
    family_candidates: Sequence[ModelCandidate],
    split_specs: Sequence[SplitSpec],
    calibration_values: Mapping[str, object],
    calibration_context: Mapping[str, object],
    split_context: Mapping[str, object],
    retain_limit: int,
    leaf_candidate_limit: int,
    leaf_global_candidate_limit: int,
) -> list[dict[str, object]]:
    rows = [dict(row) for row in root_candidates]
    root_splits = _root_splits_from_rows(root_candidates, split_specs)
    global_ids = tuple(
        candidate.candidate_id for candidate in family_candidates[:leaf_global_candidate_limit]
    )
    child_splits = split_specs[: max(1, min(len(split_specs), 24))]
    for root in root_splits[: max(1, min(len(root_splits), 24))]:
        for child_side in ("left", "right"):
            for child in child_splits:
                if child.split_id == root.split_id:
                    continue
                leaf_ids = _leaf_ids_for_calibration(
                    root=root,
                    child_side=child_side,
                    child=child,
                    split_context=split_context,
                )
                leaf_options = [
                    _top_leaf_candidate_ids(
                        family_candidates,
                        mask=leaf_ids == leaf_id,
                        calibration_values=calibration_values,
                        calibration_context=calibration_context,
                        limit=leaf_candidate_limit,
                        global_candidate_ids=global_ids,
                    )
                    for leaf_id in range(3)
                ]
                if any(not options for options in leaf_options):
                    continue
                for first in leaf_options[0]:
                    for second in leaf_options[1]:
                        for third in leaf_options[2]:
                            expert_ids = (first, second, third)
                            if len(set(expert_ids)) == 1:
                                continue
                            meta = MetaCandidate(
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
                                _approximate_meta_record(
                                    meta,
                                    calibration_values=calibration_values,
                                    calibration_context=calibration_context,
                                    split_context=split_context,
                                )
                            )
                if len(rows) > retain_limit * 8:
                    rows = _top_meta_rows(rows, limit=retain_limit)
    return _top_meta_rows(rows, limit=retain_limit)


def _approximate_meta_record(
    candidate: MetaCandidate,
    *,
    calibration_values: Mapping[str, object],
    calibration_context: Mapping[str, object],
    split_context: Mapping[str, object],
) -> dict[str, object]:
    observed = _approximate_values(
        candidate,
        calibration_values=calibration_values,
        split_context=split_context,
    )
    metrics = _fast_approx_metrics(
        observed,
        calibration_context=calibration_context,
    )
    return {
        "candidate_id": candidate.candidate_id,
        "tree": _tree_json(candidate),
        "stage": "approximate",
        "scores": metrics["scores"],
        "metrics": _approx_summary_metrics(metrics),
    }


def _fast_approx_metrics(
    observed: object,
    *,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    observed_values = np.asarray(observed, dtype=np.float32)
    labels = [str(value) for value in calibration_context["labels"]]
    finite = np.isfinite(expected) & np.isfinite(observed_values)
    errors = np.abs(observed_values[finite] - expected[finite])
    mae = float(errors.mean()) if len(errors) else None
    expected_bands = [str(value) for value in calibration_context["expected_bands"]]
    expected_bucket_ids = np.asarray([_bucket_id_for_band(value) for value in expected_bands])
    observed_bucket_ids = np.where(
        observed_values < 0.55,
        0,
        np.where(observed_values < 0.80, 1, 2),
    )
    bucket_mask = finite & (expected_bucket_ids >= 0)
    bucket_accuracy = _ratio_or_none(
        int((observed_bucket_ids[bucket_mask] == expected_bucket_ids[bucket_mask]).sum()),
        int(bucket_mask.sum()),
    )
    beginner_core = _segment_pass_rate(
        expected,
        observed_values,
        expected_max=0.20,
        observed_ceiling=0.25,
    )
    beginner_broad = _segment_pass_rate(
        expected,
        observed_values,
        expected_max=0.40,
        observed_ceiling=0.50,
    )
    upper_tail = _segment_pass_rate(
        expected,
        observed_values,
        expected_min=0.88,
        observed_floor=0.80,
    )
    high_tail = _segment_pass_rate(
        expected,
        observed_values,
        expected_min=0.94,
        observed_floor=0.88,
    )
    focus = _reviewed_focus_metrics(
        expected_values=expected,
        observed_values=observed_values,
        labels=labels,
    )
    numeric_mae_score = 1.0 - mae if mae is not None else None
    scores = {
        "numeric_mae_score": _rounded(numeric_mae_score),
        "bucket_accuracy_score": _rounded(bucket_accuracy),
        "pairwise_order_score": None,
        "rank_correlation_score": None,
        "beginner_core_score": _rounded(beginner_core),
        "beginner_broad_score": _rounded(beginner_broad),
        "upper_tail_score": _rounded(upper_tail),
        "high_tail_score": _rounded(high_tail),
        "tail_separation_score": None,
        "default_decision_score": 1.0,
        "reviewed_focus_score": focus["score"],
    }
    scores["balanced_score"] = _rounded(
        _weighted_average(
            (
                (scores["numeric_mae_score"], 0.22),
                (scores["bucket_accuracy_score"], 0.18),
                (scores["beginner_core_score"], 0.12),
                (scores["beginner_broad_score"], 0.08),
                (scores["upper_tail_score"], 0.12),
                (scores["high_tail_score"], 0.08),
                (scores["reviewed_focus_score"], 0.17),
                (scores["default_decision_score"], 0.03),
            )
        )
    )
    return {
        "difficulty_value": {"mae": _rounded(mae)},
        "difficulty_bucket": {
            "accuracy": _rounded(bucket_accuracy),
            "mismatch_count": (
                int(bucket_mask.sum())
                - int((observed_bucket_ids[bucket_mask] == expected_bucket_ids[bucket_mask]).sum())
            ),
        },
        "segments": {
            "beginner_core": {"pass_rate": _rounded(beginner_core)},
            "beginner_broad": {"pass_rate": _rounded(beginner_broad)},
            "upper_tail": {"pass_rate": _rounded(upper_tail)},
            "high_tail": {"pass_rate": _rounded(high_tail)},
        },
        "reviewed_focus": focus,
        "scores": scores,
    }


def _approx_summary_metrics(metrics: Mapping[str, object]) -> dict[str, object]:
    difficulty_value = _mapping(metrics.get("difficulty_value"))
    difficulty_bucket = _mapping(metrics.get("difficulty_bucket"))
    segments = _mapping(metrics.get("segments"))
    return {
        "mae": difficulty_value.get("mae"),
        "bucket_accuracy": difficulty_bucket.get("accuracy"),
        "bucket_mismatch_count": difficulty_bucket.get("mismatch_count"),
        "pairwise_accuracy": None,
        "pairwise_wrong_count": None,
        "spearman": None,
        "beginner_core_pass_rate": _mapping(segments.get("beginner_core")).get("pass_rate"),
        "high_tail_pass_rate": _mapping(segments.get("high_tail")).get("pass_rate"),
        "reviewed_focus_mae": _mapping(metrics.get("reviewed_focus")).get("mae"),
        "reviewed_focus_count": _mapping(metrics.get("reviewed_focus")).get("count"),
    }


def _approximate_values(
    candidate: MetaCandidate,
    *,
    calibration_values: Mapping[str, object],
    split_context: Mapping[str, object],
) -> object:
    if candidate.root is None:
        return np.asarray(calibration_values[candidate.expert_ids[0]], dtype=np.float32)
    leaf_ids = _leaf_ids_for_calibration(
        root=candidate.root,
        child_side=candidate.child_side,
        child=candidate.child,
        split_context=split_context,
    )
    values = np.full(len(leaf_ids), np.nan, dtype=np.float32)
    for leaf_id, expert_id in enumerate(candidate.expert_ids):
        values[leaf_ids == leaf_id] = np.asarray(calibration_values[expert_id], dtype=np.float32)[
            leaf_ids == leaf_id
        ]
    return values


def _top_leaf_candidate_ids(
    family_candidates: Sequence[ModelCandidate],
    *,
    mask: object,
    calibration_values: Mapping[str, object],
    calibration_context: Mapping[str, object],
    limit: int,
    global_candidate_ids: Sequence[str],
) -> list[str]:
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    finite = np.asarray(mask, dtype=bool) & np.isfinite(expected)
    rows: list[tuple[float, str]] = []
    for candidate in family_candidates:
        observed = np.asarray(calibration_values[candidate.candidate_id], dtype=np.float32)
        valid = finite & np.isfinite(observed)
        if not bool(valid.any()):
            continue
        mae = float(np.mean(np.abs(observed[valid] - expected[valid])))
        rows.append((mae, candidate.candidate_id))
    selected = [candidate_id for _mae, candidate_id in sorted(rows)[:limit]]
    seen = set(selected)
    for candidate_id in global_candidate_ids:
        if candidate_id not in seen:
            selected.append(candidate_id)
            seen.add(candidate_id)
    return selected


def _exact_evaluate_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    component: object,
    calibration_context: Mapping[str, object],
    split_context: Mapping[str, object],
    raw_by_family_candidate: Mapping[str, object],
    baseline_scores: Mapping[str, object],
    detail_candidate_limit: int,
) -> list[dict[str, object]]:
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    calibration_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    results: list[dict[str, object]] = []
    for row in candidates:
        candidate = _meta_from_row(row)
        raw, leaf_ids = _raw_for_meta_candidate(
            candidate,
            raw_by_family_candidate=raw_by_family_candidate,
            split_context=split_context,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        observed = np.full(len(calibration_indices), np.nan, dtype=np.float32)
        valid = calibration_indices >= 0
        observed[valid] = normalized[calibration_indices[valid]]
        metrics = _metrics_with_focus(
            observed,
            calibration_context=calibration_context,
        )
        scores = _mapping(metrics["scores"])
        results.append(
            {
                "candidate_id": candidate.candidate_id,
                "tree": _tree_json(candidate),
                "stage": "exact",
                "scores": dict(scores),
                "metrics": _summary_metrics_with_focus(metrics),
                "passes_baseline_constraints": _passes_baseline_constraints(
                    scores,
                    baseline_scores=baseline_scores,
                ),
                "constraint_margins": _constraint_margins(
                    scores,
                    baseline_scores=baseline_scores,
                ),
                "wrong_pairwise_examples": metrics["pairwise_order"]["wrong_examples"],
                "difficulty_mismatches": metrics["difficulty_bucket"]["mismatches"],
                "segment_misses": {
                    key: value["misses"]
                    for key, value in _mapping(metrics.get("segments")).items()
                    if _mapping(value).get("misses")
                },
                "approximate_scores": row.get("scores"),
            }
        )
    ranked = _top_meta_rows(results, limit=len(results))
    detail_ids = _detail_candidate_ids(ranked, detail_candidate_limit=detail_candidate_limit)
    for row in ranked:
        if str(row.get("candidate_id") or "") not in detail_ids:
            continue
        candidate = _meta_from_row(row)
        raw, leaf_ids = _raw_for_meta_candidate(
            candidate,
            raw_by_family_candidate=raw_by_family_candidate,
            split_context=split_context,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        row["calibration_rows"] = _calibration_detail_rows(
            candidate=candidate,
            normalized=normalized,
            leaf_ids=leaf_ids,
            component=component,
            calibration_context=calibration_context,
        )
        row["band_samples"] = _band_samples(
            normalized,
            component=component,
            segment_ids=leaf_ids,
            expert_ids=candidate.expert_ids,
            per_band=8,
        )
    return ranked


def _raw_for_meta_candidate(
    candidate: MetaCandidate,
    *,
    raw_by_family_candidate: Mapping[str, object],
    split_context: Mapping[str, object],
) -> tuple[object, object]:
    row_count = len(next(iter(raw_by_family_candidate.values())))
    if candidate.root is None:
        return (
            np.asarray(raw_by_family_candidate[candidate.expert_ids[0]], dtype=np.float32),
            np.zeros(row_count, dtype=np.int64),
        )
    leaf_ids = _leaf_ids_for_population(
        root=candidate.root,
        child_side=candidate.child_side,
        child=candidate.child,
        split_context=split_context,
    )
    raw = np.empty(row_count, dtype=np.float32)
    for leaf_id, expert_id in enumerate(candidate.expert_ids):
        mask = leaf_ids == leaf_id
        raw[mask] = np.asarray(raw_by_family_candidate[expert_id], dtype=np.float32)[mask]
    return raw, leaf_ids


def _metrics_with_focus(
    observed: object,
    *,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    metrics = _difficulty_metrics(
        expected_values=calibration_context["expected_values"],
        observed_values=observed,
        expected_bands=calibration_context["expected_bands"],
        expected_candidate_states=calibration_context["expected_candidate_states"],
        observed_candidate_states=calibration_context["observed_candidate_states"],
        labels=calibration_context["labels"],
    )
    reviewed_focus = _reviewed_focus_metrics(
        expected_values=calibration_context["expected_values"],
        observed_values=observed,
        labels=calibration_context["labels"],
    )
    metrics["reviewed_focus"] = reviewed_focus
    scores = dict(metrics["scores"])
    scores["reviewed_focus_score"] = reviewed_focus["score"]
    metrics["scores"] = scores
    return metrics


def _summary_metrics_with_focus(metrics: Mapping[str, object]) -> dict[str, object]:
    summary = dict(_summary_metrics(metrics))
    focus = _mapping(metrics.get("reviewed_focus"))
    summary["reviewed_focus_mae"] = focus.get("mae")
    summary["reviewed_focus_count"] = focus.get("count")
    return summary


def _passes_baseline_constraints(
    scores: Mapping[str, object],
    *,
    baseline_scores: Mapping[str, object],
) -> bool:
    for key, tolerance in BASELINE_TOLERANCES.items():
        value = _optional_float(scores.get(key))
        baseline = _optional_float(baseline_scores.get(key))
        if value is None or baseline is None:
            return False
        if value < baseline - tolerance - 1e-9:
            return False
    return True


def _constraint_margins(
    scores: Mapping[str, object],
    *,
    baseline_scores: Mapping[str, object],
) -> dict[str, object]:
    margins: dict[str, object] = {}
    for key, tolerance in BASELINE_TOLERANCES.items():
        value = _optional_float(scores.get(key))
        baseline = _optional_float(baseline_scores.get(key))
        margins[key] = (
            _rounded(value - (baseline - tolerance))
            if value is not None and baseline is not None
            else None
        )
    return margins


def _calibration_values_by_candidate(
    normalized_by_candidate: Mapping[str, object],
    *,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    values: dict[str, object] = {}
    valid = indices >= 0
    for candidate_id, normalized in normalized_by_candidate.items():
        observed = np.full(len(indices), np.nan, dtype=np.float32)
        observed[valid] = np.asarray(normalized, dtype=np.float32)[indices[valid]]
        values[candidate_id] = observed
    return values


def _split_context(
    component: object,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    names = [str(value) for value in component["component_names"]]
    name_to_index = {name: index for index, name in enumerate(names)}
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    frequency = np.asarray(component["frequency_values"], dtype=np.float32)
    population_values: dict[str, object] = {"frequency": frequency}
    population_present: dict[str, object] = {"frequency": np.isfinite(frequency)}
    for name, index in name_to_index.items():
        population_values[name] = values[:, index]
        population_present[name] = present[:, index]
    calibration_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    calibration_values: dict[str, object] = {}
    calibration_present: dict[str, object] = {}
    valid = calibration_indices >= 0
    for name, full_values in population_values.items():
        target = np.full(len(calibration_indices), np.nan, dtype=np.float32)
        target[valid] = np.asarray(full_values, dtype=np.float32)[calibration_indices[valid]]
        calibration_values[name] = target
        full_present = np.asarray(population_present[name], dtype=bool)
        target_present = np.zeros(len(calibration_indices), dtype=bool)
        target_present[valid] = full_present[calibration_indices[valid]]
        calibration_present[name] = target_present
    return {
        "population_values": population_values,
        "population_present": population_present,
        "calibration_values": calibration_values,
        "calibration_present": calibration_present,
    }


def _split_specs(
    split_context: Mapping[str, object],
    *,
    split_signals: Sequence[str],
    threshold_quantiles: Sequence[float],
    manual_split_thresholds: Mapping[str, Sequence[float]],
    max_split_specs: int,
) -> list[SplitSpec]:
    specs: list[SplitSpec] = []
    population_values = _mapping(split_context.get("population_values"))
    population_present = _mapping(split_context.get("population_present"))
    seen: set[tuple[str, float, bool]] = set()
    for signal in split_signals:
        thresholds: set[float] = {
            round(float(value), 4)
            for value in manual_split_thresholds.get(signal, ())
            if 0.0 <= float(value) <= 1.0
        }
        values = population_values.get(signal)
        present = population_present.get(signal)
        if values is not None and present is not None:
            finite = np.asarray(present, dtype=bool) & np.isfinite(
                np.asarray(values, dtype=np.float32)
            )
            if bool(finite.any()):
                parsed_values = np.asarray(values, dtype=np.float32)[finite]
                for quantile in threshold_quantiles:
                    threshold = float(np.quantile(parsed_values, float(quantile)))
                    if 0.0 <= threshold <= 1.0:
                        thresholds.add(round(threshold, 4))
        for threshold in sorted(thresholds):
            for missing_left in (False, True):
                key = (signal, threshold, missing_left)
                if key in seen:
                    continue
                seen.add(key)
                specs.append(SplitSpec(signal, threshold, missing_left))
    if max_split_specs > 0:
        return specs[:max_split_specs]
    return specs


def _leaf_ids_for_calibration(
    *,
    root: SplitSpec,
    child_side: str | None,
    child: SplitSpec | None,
    split_context: Mapping[str, object],
) -> object:
    return _leaf_ids_for_values(
        root=root,
        child_side=child_side,
        child=child,
        values_by_signal=_mapping(split_context.get("calibration_values")),
        present_by_signal=_mapping(split_context.get("calibration_present")),
    )


def _leaf_ids_for_population(
    *,
    root: SplitSpec,
    child_side: str | None,
    child: SplitSpec | None,
    split_context: Mapping[str, object],
) -> object:
    return _leaf_ids_for_values(
        root=root,
        child_side=child_side,
        child=child,
        values_by_signal=_mapping(split_context.get("population_values")),
        present_by_signal=_mapping(split_context.get("population_present")),
    )


def _leaf_ids_for_values(
    *,
    root: SplitSpec,
    child_side: str | None,
    child: SplitSpec | None,
    values_by_signal: Mapping[str, object],
    present_by_signal: Mapping[str, object],
) -> object:
    root_left = _split_mask(
        root,
        values_by_signal=values_by_signal,
        present_by_signal=present_by_signal,
    )
    if child is None or child_side is None:
        return np.where(root_left, 0, 1).astype(np.int64)
    child_left = _split_mask(
        child,
        values_by_signal=values_by_signal,
        present_by_signal=present_by_signal,
    )
    if child_side == "left":
        return np.where(root_left, np.where(child_left, 0, 1), 2).astype(np.int64)
    return np.where(root_left, 0, np.where(child_left, 1, 2)).astype(np.int64)


def _split_mask(
    split: SplitSpec,
    *,
    values_by_signal: Mapping[str, object],
    present_by_signal: Mapping[str, object],
) -> object:
    values = np.asarray(values_by_signal[split.signal], dtype=np.float32)
    present = np.asarray(present_by_signal[split.signal], dtype=bool) & np.isfinite(values)
    result = values <= float(split.threshold)
    return np.where(present, result, bool(split.missing_left))


def _root_splits_from_rows(
    rows: Sequence[Mapping[str, object]],
    fallback_specs: Sequence[SplitSpec],
) -> list[SplitSpec]:
    roots: list[SplitSpec] = []
    seen: set[str] = set()
    for row in rows:
        root = _split_from_json(_mapping(_mapping(row.get("tree")).get("root")))
        if root is not None and root.split_id not in seen:
            roots.append(root)
            seen.add(root.split_id)
    for spec in fallback_specs:
        if spec.split_id not in seen:
            roots.append(spec)
            seen.add(spec.split_id)
    return roots


def _top_meta_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
            _optional_float(_mapping(row.get("scores")).get("reviewed_focus_score")) or -1.0,
            _optional_float(_mapping(row.get("scores")).get("pairwise_order_score")) or -1.0,
            _optional_float(_mapping(row.get("scores")).get("numeric_mae_score")) or -1.0,
        ),
        reverse=True,
    )
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in ranked:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id or candidate_id in seen:
            continue
        selected.append(dict(row))
        seen.add(candidate_id)
        if len(selected) >= limit:
            break
    return selected


def _leaderboards(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> dict[str, list[dict[str, object]]]:
    score_keys = (
        "balanced_score",
        "reviewed_focus_score",
        "numeric_mae_score",
        "bucket_accuracy_score",
        "pairwise_order_score",
        "rank_correlation_score",
    )
    return {
        key: [
            _leaderboard_row(row, score_key=key)
            for row in sorted(
                rows,
                key=lambda item: _optional_float(_mapping(item.get("scores")).get(key)) or -1.0,
                reverse=True,
            )[:limit]
        ]
        for key in score_keys
    }


def _leaderboard_row(row: Mapping[str, object], *, score_key: str) -> dict[str, object]:
    scores = _mapping(row.get("scores"))
    metrics = _mapping(row.get("metrics"))
    return {
        "candidate_id": row.get("candidate_id"),
        "score_key": score_key,
        "score": scores.get(score_key),
        "balanced_score": scores.get("balanced_score"),
        "reviewed_focus_score": scores.get("reviewed_focus_score"),
        "mae": metrics.get("mae"),
        "reviewed_focus_mae": metrics.get("reviewed_focus_mae"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "passes_baseline_constraints": row.get("passes_baseline_constraints"),
    }


def _detail_candidate_ids(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_candidate_limit: int,
) -> set[str]:
    selected: set[str] = set()
    for row in rows[:detail_candidate_limit]:
        if row.get("candidate_id"):
            selected.add(str(row["candidate_id"]))
    per_metric = max(1, min(8, detail_candidate_limit))
    for key in ("reviewed_focus_score", "pairwise_order_score", "numeric_mae_score"):
        ranked = sorted(
            rows,
            key=lambda row: _optional_float(_mapping(row.get("scores")).get(key)) or -1.0,
            reverse=True,
        )
        for row in ranked[:per_metric]:
            if row.get("candidate_id"):
                selected.add(str(row["candidate_id"]))
    for row in rows:
        if bool(row.get("passes_baseline_constraints")) and row.get("candidate_id"):
            selected.add(str(row["candidate_id"]))
            if len(selected) >= detail_candidate_limit * 3:
                break
    return selected


def _calibration_detail_rows(
    *,
    candidate: MetaCandidate,
    normalized: object,
    leaf_ids: object,
    component: object,
    calibration_context: Mapping[str, object],
) -> list[dict[str, object]]:
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    expected_values = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    expected_bands = [str(value) for value in calibration_context["expected_bands"]]
    labels = [str(value) for value in calibration_context["labels"]]
    values = np.asarray(normalized, dtype=np.float32)
    leaf_array = np.asarray(leaf_ids, dtype=np.int64)
    rows: list[dict[str, object]] = []
    for index, component_index in enumerate(component_indices):
        observed = (
            float(values[component_index])
            if component_index >= 0 and np.isfinite(values[component_index])
            else None
        )
        expected = float(expected_values[index]) if np.isfinite(expected_values[index]) else None
        direction = ""
        error = None
        if observed is not None and expected is not None:
            error = abs(observed - expected)
            if observed < expected:
                direction = "too_low"
            elif observed > expected:
                direction = "too_high"
        leaf_id = int(leaf_array[component_index]) if component_index >= 0 else -1
        expert_id = (
            candidate.expert_ids[leaf_id] if 0 <= leaf_id < len(candidate.expert_ids) else ""
        )
        rows.append(
            {
                "label": labels[index],
                "expected_band": expected_bands[index],
                "expected_value": _rounded(expected),
                "observed_value": _rounded(observed),
                "absolute_error": _rounded(error),
                "direction": direction,
                "leaf_id": leaf_id,
                "expert_id": expert_id,
            }
        )
    return rows


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    baseline = _mapping(report.get("baseline"))
    lines = [
        "# en-ja Learner Difficulty Model-Family Meta Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Selected family candidates: `{_escape(inputs.get('selected_family_candidate_count'))}`",
        f"- Split specs: `{_escape(inputs.get('split_spec_count'))}`",
        f"- Approximate retained: `{_escape(inputs.get('approximate_retained'))}`",
        f"- Exact evaluated: `{_escape(inputs.get('exact_limit'))}`",
        "",
        "## Baseline",
        "",
        f"- Candidate: `{_escape(baseline.get('candidate_id'))}`",
        f"- Scores: `{_compact_counts(baseline)}`",
        "",
        "## Exact Top Candidates",
        "",
        (
            "| Rank | Candidate | Balanced | Focus | MAE | Bucket | Pairwise | "
            "Beginner | High Tail | Upper Tail | Constrained |"
        ),
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(_mapping_rows(report.get("exact_top"))[:25], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            "| "
            f"{index} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(scores.get('reviewed_focus_score'))}` | "
            f"`{_escape(metrics.get('mae'))}` | "
            f"`{_escape(metrics.get('bucket_accuracy'))}` | "
            f"`{_escape(metrics.get('pairwise_accuracy'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_escape(scores.get('upper_tail_score'))}` | "
            f"`{_escape(row.get('passes_baseline_constraints'))}` |"
        )
    lines.extend(["", "## Constrained Top", ""])
    constrained = _mapping_rows(report.get("constrained_top"))
    if not constrained:
        lines.append("No candidate passed the baseline guardrails.")
    else:
        lines.extend(
            [
                "| Rank | Candidate | Balanced | Focus | MAE | Bucket | Pairwise |",
                "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for index, row in enumerate(constrained[:15], start=1):
            scores = _mapping(row.get("scores"))
            metrics = _mapping(row.get("metrics"))
            lines.append(
                "| "
                f"{index} | "
                f"`{_escape(row.get('candidate_id'))}` | "
                f"`{_escape(scores.get('balanced_score'))}` | "
                f"`{_escape(scores.get('reviewed_focus_score'))}` | "
                f"`{_escape(metrics.get('mae'))}` | "
                f"`{_escape(metrics.get('bucket_accuracy'))}` | "
                f"`{_escape(metrics.get('pairwise_accuracy'))}` |"
            )
    lines.extend(["", "## Leaderboards", ""])
    for score_key, rows in _mapping(report.get("leaderboards")).items():
        lines.extend(
            [
                f"### `{_escape(score_key)}`",
                "",
                "| Rank | Candidate | Score | Balanced | Focus | MAE | Pairwise | Constrained |",
                "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for index, row in enumerate(_mapping_rows(rows)[:10], start=1):
            lines.append(
                "| "
                f"{index} | "
                f"`{_escape(row.get('candidate_id'))}` | "
                f"`{_escape(row.get('score'))}` | "
                f"`{_escape(row.get('balanced_score'))}` | "
                f"`{_escape(row.get('reviewed_focus_score'))}` | "
                f"`{_escape(row.get('mae'))}` | "
                f"`{_escape(row.get('pairwise_accuracy'))}` | "
                f"`{_escape(row.get('passes_baseline_constraints'))}` |"
            )
        lines.append("")
    lines.extend(["", "## Top Candidate Details", ""])
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        scores = _mapping(row.get("scores"))
        lines.extend(
            [
                f"### `{_escape(row.get('candidate_id'))}`",
                "",
                f"- Tree: `{_escape(_compact_counts(row.get('tree')))}`",
                f"- Scores: `{_compact_counts(scores)}`",
                f"- Metrics: `{_compact_counts(row.get('metrics'))}`",
                f"- Constraint margins: `{_compact_counts(row.get('constraint_margins'))}`",
            ]
        )
        mismatches = _mapping_rows(row.get("difficulty_mismatches"))
        if mismatches:
            lines.append(
                "- Difficulty mismatches: "
                + ", ".join(
                    f"{item.get('label')} ({item.get('expected')}->{item.get('observed')})"
                    for item in mismatches[:12]
                )
            )
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
    return "\n".join(lines).rstrip() + "\n"


def render_calibration_rows_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-ja Model-Family Meta Calibration Rows",
        "",
        "| Candidate | Rank | Label | Expected | Observed | Error | Direction | Leaf | Expert |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in _flat_calibration_rows(report):
        lines.append(
            "| "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('rank'))}` | "
            f"`{_escape(row.get('label'))}` | "
            f"`{_escape(row.get('expected_value'))}` | "
            f"`{_escape(row.get('observed_value'))}` | "
            f"`{_escape(row.get('absolute_error'))}` | "
            f"`{_escape(row.get('direction'))}` | "
            f"`{_escape(row.get('leaf_id'))}` | "
            f"`{_escape(row.get('expert_id'))}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_calibration_rows_csv(report: Mapping[str, object]) -> str:
    headers = [
        "candidate_id",
        "rank",
        "label",
        "expected_band",
        "expected_value",
        "observed_value",
        "absolute_error",
        "direction",
        "leaf_id",
        "expert_id",
    ]
    lines = [",".join(headers)]
    for row in _flat_calibration_rows(report):
        lines.append(",".join(_csv_cell(row.get(header)) for header in headers))
    return "\n".join(lines).rstrip() + "\n"


def _flat_calibration_rows(report: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, candidate in enumerate(_mapping_rows(report.get("exact_top")), start=1):
        if not candidate.get("calibration_rows"):
            continue
        candidate_id = str(candidate.get("candidate_id") or "")
        for calibration_row in _mapping_rows(candidate.get("calibration_rows")):
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "rank": rank,
                    "label": calibration_row.get("label"),
                    "expected_band": calibration_row.get("expected_band"),
                    "expected_value": calibration_row.get("expected_value"),
                    "observed_value": calibration_row.get("observed_value"),
                    "absolute_error": calibration_row.get("absolute_error"),
                    "direction": calibration_row.get("direction"),
                    "leaf_id": calibration_row.get("leaf_id"),
                    "expert_id": calibration_row.get("expert_id"),
                }
            )
    return rows


def _model_candidate_from_row(row: Mapping[str, object]) -> ModelCandidate:
    return ModelCandidate(
        candidate_id=str(row.get("candidate_id") or ""),
        family=str(row.get("family") or "unknown"),
        base_expert_id=str(row.get("base_expert_id") or ""),
        floors=tuple(_floor_from_json(item) for item in _mapping_rows(row.get("floors"))),
        boosts=tuple(_boost_from_json(item) for item in _mapping_rows(row.get("boosts"))),
        soft_mix=_soft_mix_from_json(_mapping(row.get("soft_mix"))),
    )


def _floor_from_json(row: Mapping[str, object]) -> FloorSpec:
    return FloorSpec(
        spec_id=str(row.get("spec_id") or ""),
        signal=str(row.get("signal") or ""),
        min_signal=float(row.get("min_signal") or 0.0),
        floor_min=float(row.get("floor_min") or 0.0),
        floor_max=float(row.get("floor_max") or 0.0),
    )


def _boost_from_json(row: Mapping[str, object]) -> BoostSpec:
    return BoostSpec(
        spec_id=str(row.get("spec_id") or ""),
        signal=str(row.get("signal") or ""),
        threshold=float(row.get("threshold") or 0.0),
        strength=float(row.get("strength") or 0.0),
    )


def _soft_mix_from_json(row: Mapping[str, object]) -> SoftMixSpec | None:
    if not row:
        return None
    return SoftMixSpec(
        spec_id=str(row.get("spec_id") or ""),
        other_expert_id=str(row.get("other_expert_id") or ""),
        signal=str(row.get("signal") or ""),
        threshold=float(row.get("threshold") or 0.0),
        strength=float(row.get("strength") or 0.0),
    )


def _expert_from_json(row: Mapping[str, object]) -> Expert:
    return Expert(
        variant_id=str(row.get("variant_id") or ""),
        weights={
            str(key): float(value)
            for key, value in _mapping(row.get("weights")).items()
            if _optional_float(value) is not None
        },
        max_shift_from_frequency=_optional_float(row.get("max_shift_from_frequency")),
        source_scores={
            str(key): float(value)
            for key, value in _mapping(row.get("source_scores")).items()
            if _optional_float(value) is not None
        },
    )


def _family_candidate_json(
    candidate: ModelCandidate,
    family_report: Mapping[str, object],
) -> dict[str, object]:
    by_id = {
        str(row.get("candidate_id") or ""): row
        for row in _mapping_rows(family_report.get("exact_top"))
    }
    source = _mapping(by_id.get(candidate.candidate_id))
    return {
        "candidate_id": candidate.candidate_id,
        "family": candidate.family,
        "base_expert_id": candidate.base_expert_id,
        "source_scores": source.get("scores"),
        "source_metrics": source.get("metrics"),
    }


def _tree_json(candidate: MetaCandidate) -> dict[str, object]:
    return {
        "root": _split_json(candidate.root),
        "child_side": candidate.child_side,
        "child": _split_json(candidate.child),
        "expert_ids": list(candidate.expert_ids),
    }


def _meta_from_row(row: Mapping[str, object]) -> MetaCandidate:
    tree = _mapping(row.get("tree"))
    return MetaCandidate(
        candidate_id=str(row.get("candidate_id") or ""),
        root=_split_from_json(_mapping(tree.get("root"))),
        child_side=str(tree.get("child_side") or "") or None,
        child=_split_from_json(_mapping(tree.get("child"))),
        expert_ids=tuple(str(value) for value in _sequence(tree.get("expert_ids"))),
    )


def _split_json(split: SplitSpec | None) -> dict[str, object] | None:
    if split is None:
        return None
    return {
        "signal": split.signal,
        "threshold": round(float(split.threshold), 6),
        "missing_left": split.missing_left,
        "split_id": split.split_id,
    }


def _split_from_json(row: Mapping[str, object]) -> SplitSpec | None:
    if not row:
        return None
    return SplitSpec(
        signal=str(row.get("signal") or ""),
        threshold=float(row.get("threshold") or 0.0),
        missing_left=bool(row.get("missing_left")),
    )


def _baseline_scores(report: Mapping[str, object]) -> dict[str, object]:
    top = _mapping_rows(report.get("exact_top"))[0]
    scores = dict(_mapping(top.get("scores")))
    scores["candidate_id"] = top.get("candidate_id")
    return scores


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in str(value or "").split(",") if item.strip())


def _parse_float_csv(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in str(value or "").split(",") if item.strip())


def _parse_manual_thresholds(value: str) -> dict[str, tuple[float, ...]]:
    parsed: dict[str, tuple[float, ...]] = {}
    for item in str(value or "").split(";"):
        item = item.strip()
        if not item:
            continue
        signal, separator, raw_values = item.partition(":")
        if not separator:
            raise ValueError(f"Expected signal:v1,v2 thresholds, got {item!r}")
        parsed[signal.strip()] = tuple(
            float(value.strip()) for value in raw_values.split(",") if value.strip()
        )
    return parsed


def _bucket_id_for_band(value: str) -> int:
    if value == "beginner":
        return 0
    if value == "intermediate":
        return 1
    if value == "advanced":
        return 2
    return -1


def _segment_pass_rate(
    expected: object,
    observed: object,
    *,
    expected_min: float | None = None,
    expected_max: float | None = None,
    observed_floor: float | None = None,
    observed_ceiling: float | None = None,
) -> float | None:
    expected_values = np.asarray(expected, dtype=np.float32)
    observed_values = np.asarray(observed, dtype=np.float32)
    mask = np.isfinite(expected_values) & np.isfinite(observed_values)
    if expected_min is not None:
        mask &= expected_values >= float(expected_min)
    if expected_max is not None:
        mask &= expected_values <= float(expected_max)
    if not bool(mask.any()):
        return None
    passes = np.ones(int(mask.sum()), dtype=bool)
    segment_observed = observed_values[mask]
    if observed_floor is not None:
        passes &= segment_observed >= float(observed_floor)
    if observed_ceiling is not None:
        passes &= segment_observed <= float(observed_ceiling)
    return float(passes.sum()) / float(len(passes))


def _ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _weighted_average(values_and_weights: Sequence[tuple[object, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values_and_weights:
        parsed = _optional_float(value)
        if parsed is None or weight <= 0.0:
            continue
        numerator += parsed * float(weight)
        denominator += float(weight)
    if denominator <= 0.0:
        return None
    return numerator / denominator


def _format_manual_thresholds(thresholds: Mapping[str, Sequence[float]]) -> str:
    return ";".join(
        f"{signal}:{','.join(f'{float(value):g}' for value in values)}"
        for signal, values in thresholds.items()
    )


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or value is None:
        return ()
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return ()


def _csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if any(char in text for char in (",", '"', "\n")):
        return '"' + text.replace('"', '""') + '"'
    return text


if __name__ == "__main__":
    raise SystemExit(main())
