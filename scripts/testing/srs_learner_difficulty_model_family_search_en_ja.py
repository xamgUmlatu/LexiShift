#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Iterable
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
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    Expert,
    _band_samples,
    _calibration_context,
    _compact_counts,
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
    _select_experts,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)


DEFAULT_TRACE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_trace_latest.json"
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
    / "srs_learner_difficulty_model_family_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_search_en_ja_latest.md"
)
DEFAULT_CALIBRATION_ROWS_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_calibration_rows_en_ja_latest.csv"
)
DEFAULT_CALIBRATION_ROWS_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_calibration_rows_en_ja_latest.md"
)
SIGNAL_COLUMNS = (
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
    "missing_frequency_rank_risk",
    "missing_jmdict_priority_risk",
    "missing_jlpt_vocab_risk",
    "missing_lesson_vocab_risk",
    "missing_pedagogical_vocab_risk",
    "missing_frequency_and_priority_risk",
    "missing_frequency_and_pedagogical_risk",
    "missing_frequency_source_evidence_risk",
    "missing_frequency_priority_or_kanji_risk",
    "missing_frequency_priority_pedagogy_risk",
    "bccwj_domain_rank_spread",
    "bccwj_domain_rank_variability",
    "bccwj_domain_profile_variability",
    "bccwj_rank_spread",
    "bccwj_rank_variability",
    "bccwj_fixed_variable_rank_delta",
    "jmdict_priority",
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
    "jmdict_pos_count",
    "jmdict_entry_ambiguity",
    "jmdict_pos_ambiguity",
    "jmdict_reading_form_ambiguity",
    "jmdict_sense_ambiguity",
    "jmdict_kanji_form_marked_flag",
    "jmdict_reading_form_marked_flag",
    "jmdict_sense_restricted_flag",
    "jmdict_reading_restricted_flag",
    "jmdict_no_kanji_reading_flag",
    "jmdict_polysemy_flag",
    "jmdict_sinitic_source_flag",
    "jmdict_source_type_flag",
    "jmdict_wasei_source_flag",
    "wtype_wago_ease",
    "wtype_kango_risk",
    "kango_mid_signal",
    "common_kango_register_domain_score",
    "common_kango_written_burden",
    "common_kango_ambiguity_score",
    "common_kango_complexity_score",
    "kango_common_priority_risk",
    "kango_kanji_burden",
    "kanjidic_nanori_reading_count_score",
    "kanjidic_variant_type_count_score",
    "kanjivg_variant_structure",
    "rare_wago_tail_risk",
    "rare_wago_obscure_written_risk",
    "written_wago_tail_risk",
    "max_written_form_burden",
    "written_form_burden",
    "rare_non_standard_reading_risk",
)
TARGET_CURE_ABS_TOLERANCE = 0.10
TARGET_CURE_WATCH_SPECS = (
    {
        "label": "水虻/みずあぶ",
        "lemma": "水虻",
        "reading": "みずあぶ",
        "min_value": 0.85,
        "rationale": "Unranked rare full-word watch item; should land in the upper tail.",
    },
    {
        "label": "総高/そうだか",
        "lemma": "総高",
        "reading": "そうだか",
        "min_value": 0.80,
        "rationale": "Unranked/recondite compound watch item; should not look early merely because its characters are common.",
    },
    {
        "label": "稲光/いなびかり",
        "lemma": "稲光",
        "reading": "いなびかり",
        "min_value": 0.75,
        "rationale": "Rare written wago watch item for tail placement sanity.",
    },
    {
        "label": "試練/しれん",
        "lemma": "試練",
        "reading": "しれん",
        "min_value": 0.45,
        "max_value": 0.75,
        "rationale": "Useful mid/upper-mid kango watch item; should not be pushed above clearly rarer words.",
    },
)
REVIEWED_FOCUS_LABELS = frozenset(
    {
        "侘び/わび",
        "猯/まみ",
        "技術/ぎじゅつ",
        "政治/せいじ",
        "公開/こうかい",
        "影響/えいきょう",
        "特徴/とくちょう",
        "躊躇う/ためらう",
        "埋め立て/うめたて",
        "我が/わが",
        "詭弁/きべん",
        "宿る/やどる",
        "猫/ねこ",
        "胸/むね",
        "的/まと",
    }
)
LEADERBOARD_SCORE_KEYS = (
    "balanced_score",
    "target_cure_score",
    "reviewed_focus_score",
    "numeric_mae_score",
    "bucket_accuracy_score",
    "pairwise_order_score",
    "rank_correlation_score",
)


@dataclass(frozen=True)
class FloorSpec:
    spec_id: str
    signal: str
    min_signal: float
    floor_min: float
    floor_max: float


@dataclass(frozen=True)
class BoostSpec:
    spec_id: str
    signal: str
    threshold: float
    strength: float


@dataclass(frozen=True)
class SoftMixSpec:
    spec_id: str
    other_expert_id: str
    signal: str
    threshold: float
    strength: float


@dataclass(frozen=True)
class FinalFloorSpec:
    spec_id: str
    signal: str
    min_signal: float
    floor_min: float
    floor_max: float


@dataclass(frozen=True)
class FinalAdjustmentSpec:
    spec_id: str
    mode: str
    signal: str
    threshold: float
    strength: float
    floor: float | None = None


@dataclass(frozen=True)
class ModelCandidate:
    candidate_id: str
    family: str
    base_expert_id: str
    floors: tuple[FloorSpec, ...] = ()
    boosts: tuple[BoostSpec, ...] = ()
    soft_mix: SoftMixSpec | None = None
    final_floors: tuple[FinalFloorSpec, ...] = ()
    final_adjustments: tuple[FinalAdjustmentSpec, ...] = ()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only exact search over en-ja learner-difficulty model families "
            "such as bounded floors, hinge/ramp boosts, and soft mixtures."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--expert-pool-size", type=int, default=36)
    parser.add_argument("--top-per-metric", type=int, default=10)
    parser.add_argument("--max-candidates", type=int, default=5000)
    parser.add_argument("--detail-candidate-limit", type=int, default=20)
    parser.add_argument(
        "--candidate-mode",
        choices=("full", "missingness-softening", "missingness-softening-refined"),
        default="full",
        help=(
            "Use 'full' for the broad family sweep, 'missingness-softening' "
            "to freeze the old search space and only sweep soft final adjustments "
            "around known strong bases, or 'missingness-softening-refined' for "
            "a tighter joint search around the proven softening neighborhood."
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
        max_candidates=max(1, int(args.max_candidates)),
        detail_candidate_limit=max(0, int(args.detail_candidate_limit)),
        candidate_mode=str(args.candidate_mode),
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
    trace_json: Path,
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    expert_pool_size: int = 36,
    top_per_metric: int = 10,
    max_candidates: int = 5000,
    detail_candidate_limit: int = 20,
    candidate_mode: str = "full",
) -> dict[str, object]:
    trace = _load_json(trace_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    experts = _select_experts(
        trace.get("variant_records", ()),
        pool_size=expert_pool_size,
        top_per_metric=top_per_metric,
    )
    calibration_context = _calibration_context(calibration, component)
    raw_by_expert = {
        expert.variant_id: _raw_scores_for_expert(expert, component) for expert in experts
    }
    signal_arrays = _signal_arrays(component)
    candidates = list(
        _iter_model_candidates(
            experts=experts,
            max_candidates=max_candidates,
            candidate_mode=candidate_mode,
        )
    )
    exact_top = _evaluate_candidates(
        candidates,
        component=component,
        calibration_context=calibration_context,
        raw_by_expert=raw_by_expert,
        signal_arrays=signal_arrays,
        detail_candidate_limit=detail_candidate_limit,
    )
    leaderboards = _leaderboards(exact_top, limit=25)
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
            code_paths=_model_family_code_paths(),
            version_constants={
                "target_curve": TARGET_CURVE_ID,
            },
            argv=sys.argv,
        ),
        "method": {
            "model": "exact_full_corpus_model_family_search",
            "families": [
                "linear_expert_baseline",
                "bounded_floor",
                "hinge_ramp_boost",
                "combined_floor",
                "final_floor",
                "partial_final_floor",
                "final_tail_boost",
                "soft_mixture_of_experts",
            ],
            "normalization_curve_id": TARGET_CURVE_ID,
            "evaluation": (
                "Every candidate recomputes raw scores over the full component matrix "
                "and then applies the global target-curve normalization."
            ),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "trace_variant_count": len(trace.get("variant_records", ())),
            "calibration_label_count": int(len(calibration["calibration_lemmas"])),
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "component_names": [str(value) for value in component["component_names"]],
            "expert_pool_size": len(experts),
            "top_per_metric": top_per_metric,
            "max_candidates": max_candidates,
            "evaluated_candidate_count": len(candidates),
            "detail_candidate_limit": detail_candidate_limit,
            "candidate_mode": candidate_mode,
        },
        "expert_pool": [_expert_json(expert) for expert in experts],
        "candidate_family_counts": _candidate_family_counts(candidates),
        "leaderboards": leaderboards,
        "exact_top": exact_top,
    }


def _model_family_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "difficulty_signal_sweep": (SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"),
        "difficulty_piecewise_search": (
            SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
        ),
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


def _iter_model_candidates(
    *,
    experts: Sequence[Expert],
    max_candidates: int,
    candidate_mode: str = "full",
) -> Iterable[ModelCandidate]:
    if candidate_mode == "missingness-softening":
        yield from _iter_missingness_softening_candidates(
            experts=experts,
            max_candidates=max_candidates,
        )
        return
    if candidate_mode == "missingness-softening-refined":
        yield from _iter_missingness_softening_refined_candidates(
            experts=experts,
            max_candidates=max_candidates,
        )
        return
    emitted = 0
    expert_ids = [expert.variant_id for expert in experts]
    for expert_id in expert_ids:
        candidate = ModelCandidate(
            candidate_id=f"linear__{expert_id}",
            family="linear_expert_baseline",
            base_expert_id=expert_id,
        )
        yield candidate
        emitted += 1
        if emitted >= max_candidates:
            return
    floor_specs = _floor_specs()
    boost_specs = _boost_specs()
    combined_floor_sets = _combined_floor_sets()
    final_floor_specs = _final_floor_specs()
    for expert_id in expert_ids:
        for floor in floor_specs:
            yield ModelCandidate(
                candidate_id=f"floor__{expert_id}__{floor.spec_id}",
                family="bounded_floor",
                base_expert_id=expert_id,
                floors=(floor,),
            )
            emitted += 1
            if emitted >= max_candidates:
                return
        for boost in boost_specs:
            yield ModelCandidate(
                candidate_id=f"boost__{expert_id}__{boost.spec_id}",
                family="hinge_ramp_boost",
                base_expert_id=expert_id,
                boosts=(boost,),
            )
            emitted += 1
            if emitted >= max_candidates:
                return
        for floors in combined_floor_sets:
            floor_id = "__".join(floor.spec_id for floor in floors)
            yield ModelCandidate(
                candidate_id=f"floors__{expert_id}__{floor_id}",
                family="combined_floor",
                base_expert_id=expert_id,
                floors=floors,
            )
            emitted += 1
            if emitted >= max_candidates:
                return
        for final_floor in final_floor_specs:
            yield ModelCandidate(
                candidate_id=f"finalfloor__{expert_id}__{final_floor.spec_id}",
                family="final_floor",
                base_expert_id=expert_id,
                final_floors=(final_floor,),
            )
            emitted += 1
            if emitted >= max_candidates:
                return
    soft_base_ids = expert_ids[: min(10, len(expert_ids))]
    soft_other_ids = expert_ids[: min(12, len(expert_ids))]
    for base_id in soft_base_ids:
        for other_id in soft_other_ids:
            if base_id == other_id:
                continue
            for soft_mix in _soft_mix_specs(other_id):
                yield ModelCandidate(
                    candidate_id=f"softmix__{base_id}__{soft_mix.spec_id}",
                    family="soft_mixture_of_experts",
                    base_expert_id=base_id,
                    soft_mix=soft_mix,
                )
                emitted += 1
                if emitted >= max_candidates:
                    return


def _iter_missingness_softening_candidates(
    *,
    experts: Sequence[Expert],
    max_candidates: int,
) -> Iterable[ModelCandidate]:
    emitted = 0
    expert_ids = {expert.variant_id for expert in experts}
    bases: list[ModelCandidate] = []

    def add_base(candidate: ModelCandidate) -> None:
        if candidate.base_expert_id in expert_ids:
            bases.append(candidate)

    for expert_id in (
        "grid_s10_cnone_000242",
        "grid_s10_cnone_000240",
        "grid_s10_cnone_000237",
        "grid_s10_cnone_000227",
        "grid_s10_cnone_000206",
        "grid_s10_cnone_000180",
        "grid_s10_cnone_000298",
        "grid_s10_cnone_000238",
    ):
        add_base(
            ModelCandidate(
                candidate_id=f"base__{expert_id}",
                family="softening_base",
                base_expert_id=expert_id,
            )
        )

    for expert_id, threshold, strength in (
        ("grid_s10_cnone_000242", 0.10, 0.75),
        ("grid_s10_cnone_000240", 0.10, 0.75),
        ("grid_s10_cnone_000237", 0.10, 0.50),
        ("grid_s10_cnone_000238", 0.10, 0.75),
    ):
        add_base(
            ModelCandidate(
                candidate_id=(
                    f"base__{expert_id}__"
                    f"{_boost_id('kanji_curriculum_missing_risk', threshold, strength)}"
                ),
                family="softening_base",
                base_expert_id=expert_id,
                boosts=(
                    BoostSpec(
                        spec_id=_boost_id(
                            "kanji_curriculum_missing_risk",
                            threshold,
                            strength,
                        ),
                        signal="kanji_curriculum_missing_risk",
                        threshold=threshold,
                        strength=strength,
                    ),
                ),
            )
        )

    if {"grid_s10_cnone_000238", "grid_s10_cnone_000171"} <= expert_ids:
        add_base(
            ModelCandidate(
                candidate_id=(
                    "base__grid_s10_cnone_000238__"
                    "softmix_grid_s10_cnone_000171_frequency_unranked_floor95"
                ),
                family="softening_base",
                base_expert_id="grid_s10_cnone_000238",
                soft_mix=SoftMixSpec(
                    spec_id=(
                        "grid_s10_cnone_000171__"
                        f"{_boost_id('frequency_unranked_floor95_risk', 0.50, 1.00)}"
                    ),
                    other_expert_id="grid_s10_cnone_000171",
                    signal="frequency_unranked_floor95_risk",
                    threshold=0.50,
                    strength=1.00,
                ),
            )
        )

    for base in bases:
        yield base
        emitted += 1
        if emitted >= max_candidates:
            return
        for adjustment in _final_adjustment_specs():
            yield ModelCandidate(
                candidate_id=f"{adjustment.mode}__{base.candidate_id}__{adjustment.spec_id}",
                family=adjustment.mode,
                base_expert_id=base.base_expert_id,
                floors=base.floors,
                boosts=base.boosts,
                soft_mix=base.soft_mix,
                final_adjustments=(adjustment,),
            )
            emitted += 1
            if emitted >= max_candidates:
                return


def _iter_missingness_softening_refined_candidates(
    *,
    experts: Sequence[Expert],
    max_candidates: int,
) -> Iterable[ModelCandidate]:
    emitted = 0
    expert_ids = {expert.variant_id for expert in experts}
    bases: list[ModelCandidate] = []

    def add_base(candidate: ModelCandidate) -> None:
        if candidate.base_expert_id in expert_ids:
            bases.append(candidate)

    for expert_id in (
        "grid_s10_cnone_000237",
        "grid_s10_cnone_000238",
        "grid_s10_cnone_000206",
        "grid_s10_cnone_000240",
    ):
        add_base(
            ModelCandidate(
                candidate_id=f"base__{expert_id}",
                family="softening_refined_base",
                base_expert_id=expert_id,
            )
        )

    for expert_id, strengths in (
        ("grid_s10_cnone_000237", (0.35, 0.45, 0.50, 0.55, 0.65)),
        ("grid_s10_cnone_000238", (0.55, 0.65, 0.75, 0.85)),
        ("grid_s10_cnone_000206", (0.35, 0.50, 0.65)),
    ):
        for threshold in (0.05, 0.10, 0.20):
            for strength in strengths:
                add_base(
                    ModelCandidate(
                        candidate_id=(
                            f"base__{expert_id}__"
                            f"{_boost_id('kanji_curriculum_missing_risk', threshold, strength)}"
                        ),
                        family="softening_refined_base",
                        base_expert_id=expert_id,
                        boosts=(
                            BoostSpec(
                                spec_id=_boost_id(
                                    "kanji_curriculum_missing_risk",
                                    threshold,
                                    strength,
                                ),
                                signal="kanji_curriculum_missing_risk",
                                threshold=threshold,
                                strength=strength,
                            ),
                        ),
                    )
                )

    if {"grid_s10_cnone_000238", "grid_s10_cnone_000171"} <= expert_ids:
        for threshold in (0.35, 0.50, 0.65):
            for strength in (0.60, 0.80, 1.00):
                add_base(
                    ModelCandidate(
                        candidate_id=(
                            "base__grid_s10_cnone_000238__"
                            f"softmix_grid_s10_cnone_000171_"
                            f"{_boost_id('frequency_unranked_floor95_risk', threshold, strength)}"
                        ),
                        family="softening_refined_base",
                        base_expert_id="grid_s10_cnone_000238",
                        soft_mix=SoftMixSpec(
                            spec_id=(
                                "grid_s10_cnone_000171__"
                                f"{_boost_id('frequency_unranked_floor95_risk', threshold, strength)}"
                            ),
                            other_expert_id="grid_s10_cnone_000171",
                            signal="frequency_unranked_floor95_risk",
                            threshold=threshold,
                            strength=strength,
                        ),
                    )
                )

    for base in bases:
        yield base
        emitted += 1
        if emitted >= max_candidates:
            return
        for adjustment in _refined_final_adjustment_specs():
            yield ModelCandidate(
                candidate_id=(
                    f"{adjustment.mode}_refined__{base.candidate_id}__{adjustment.spec_id}"
                ),
                family=f"{adjustment.mode}_refined",
                base_expert_id=base.base_expert_id,
                floors=base.floors,
                boosts=base.boosts,
                soft_mix=base.soft_mix,
                final_adjustments=(adjustment,),
            )
            emitted += 1
            if emitted >= max_candidates:
                return


def _floor_specs() -> tuple[FloorSpec, ...]:
    specs: list[FloorSpec] = []
    for min_signal in (0.50, 0.65, 0.80):
        for floor_min, floor_max in ((0.45, 0.75), (0.55, 0.90)):
            specs.append(
                FloorSpec(
                    spec_id=_floor_id("frequency", min_signal, floor_min, floor_max),
                    signal="frequency",
                    min_signal=min_signal,
                    floor_min=floor_min,
                    floor_max=floor_max,
                )
            )
    for signal, prefix in (
        ("frequency_unranked_floor60_risk", "unranked_floor60"),
        ("frequency_unranked_floor70_risk", "unranked_floor70"),
        ("frequency_unranked_floor80_risk", "unranked_floor80"),
        ("frequency_unranked_floor90_risk", "unranked_floor90"),
        ("frequency_unranked_floor95_risk", "unranked_floor95"),
        ("frequency_unranked_floor99_risk", "unranked_floor99"),
    ):
        for min_signal in (0.10, 0.20, 0.50, 0.75):
            for floor_min, floor_max in (
                (0.55, 0.85),
                (0.65, 0.92),
                (0.70, 0.95),
                (0.80, 0.99),
                (0.90, 1.00),
            ):
                specs.append(
                    FloorSpec(
                        spec_id=_floor_id(prefix, min_signal, floor_min, floor_max),
                        signal=signal,
                        min_signal=min_signal,
                        floor_min=floor_min,
                        floor_max=floor_max,
                    )
                )
    for signal, prefix, ranges in (
        (
            "missing_frequency_rank_risk",
            "missing_freq_rank",
            ((0.55, 0.80), (0.65, 0.88), (0.75, 0.95)),
        ),
        (
            "missing_jmdict_priority_risk",
            "missing_jmdict_priority",
            ((0.25, 0.50), (0.35, 0.65), (0.45, 0.78)),
        ),
        (
            "missing_pedagogical_vocab_risk",
            "missing_pedagogical",
            ((0.15, 0.35), (0.25, 0.50), (0.35, 0.65)),
        ),
        (
            "missing_frequency_and_priority_risk",
            "missing_freq_priority",
            ((0.65, 0.88), (0.75, 0.95), (0.85, 0.99)),
        ),
        (
            "missing_frequency_and_pedagogical_risk",
            "missing_freq_pedagogical",
            ((0.60, 0.85), (0.70, 0.92), (0.80, 0.98)),
        ),
        (
            "kanji_curriculum_missing_risk",
            "kanji_curriculum_missing",
            ((0.40, 0.70), (0.55, 0.85), (0.70, 0.95)),
        ),
    ):
        for floor_min, floor_max in ranges:
            specs.append(
                FloorSpec(
                    spec_id=_floor_id(prefix, 0.50, floor_min, floor_max),
                    signal=signal,
                    min_signal=0.50,
                    floor_min=floor_min,
                    floor_max=floor_max,
                )
            )
    for min_signal in (0.20, 0.35, 0.50):
        for floor_min, floor_max in ((0.30, 0.60), (0.35, 0.65), (0.40, 0.68)):
            specs.append(
                FloorSpec(
                    spec_id=_floor_id("kango_mid", min_signal, floor_min, floor_max),
                    signal="kango_mid_signal",
                    min_signal=min_signal,
                    floor_min=floor_min,
                    floor_max=floor_max,
                )
            )
    for min_signal in (0.10, 0.25, 0.50):
        for floor_min, floor_max in ((0.70, 0.92), (0.75, 0.95), (0.80, 0.98)):
            specs.append(
                FloorSpec(
                    spec_id=_floor_id("rare_wago", min_signal, floor_min, floor_max),
                    signal="rare_wago_tail_risk",
                    min_signal=min_signal,
                    floor_min=floor_min,
                    floor_max=floor_max,
                )
            )
    for min_signal in (0.15, 0.30, 0.45):
        for floor_min, floor_max in ((0.55, 0.80), (0.60, 0.85), (0.65, 0.88)):
            specs.append(
                FloorSpec(
                    spec_id=_floor_id("written_wago", min_signal, floor_min, floor_max),
                    signal="written_wago_tail_risk",
                    min_signal=min_signal,
                    floor_min=floor_min,
                    floor_max=floor_max,
                )
            )
    return tuple(specs)


def _boost_specs() -> tuple[BoostSpec, ...]:
    specs: list[BoostSpec] = []
    for signal in ("kango_mid_signal", "rare_wago_tail_risk", "written_wago_tail_risk"):
        for threshold in (0.20, 0.35, 0.50, 0.70):
            for strength in (0.05, 0.10, 0.18, 0.28):
                specs.append(
                    BoostSpec(
                        spec_id=_boost_id(signal, threshold, strength),
                        signal=signal,
                        threshold=threshold,
                        strength=strength,
                    )
                )
    for signal in (
        "frequency_tail65",
        "frequency_tail80",
        "frequency_tail90",
        "frequency_unranked_floor60_risk",
        "frequency_unranked_floor70_risk",
        "frequency_unranked_floor80_risk",
        "frequency_unranked_floor90_risk",
        "frequency_unranked_floor95_risk",
        "frequency_unranked_floor99_risk",
        "missing_frequency_rank_risk",
        "missing_jmdict_priority_risk",
        "missing_pedagogical_vocab_risk",
        "missing_frequency_and_priority_risk",
        "missing_frequency_and_pedagogical_risk",
        "kanji_curriculum_missing_risk",
    ):
        for threshold in (0.10, 0.20, 0.50, 0.75):
            for strength in (0.10, 0.20, 0.35, 0.50, 0.75):
                specs.append(
                    BoostSpec(
                        spec_id=_boost_id(signal, threshold, strength),
                        signal=signal,
                        threshold=threshold,
                        strength=strength,
                    )
                )
    return tuple(specs)


def _final_floor_specs() -> tuple[FinalFloorSpec, ...]:
    specs: list[FinalFloorSpec] = []
    for signal, prefix, floors in (
        (
            "missing_frequency_rank_risk",
            "missing_freq_rank",
            (0.65, 0.70, 0.75, 0.80, 0.85),
        ),
        (
            "missing_frequency_and_priority_risk",
            "missing_freq_priority",
            (0.70, 0.75, 0.80, 0.85, 0.90),
        ),
        (
            "missing_frequency_and_pedagogical_risk",
            "missing_freq_pedagogical",
            (0.65, 0.70, 0.75, 0.80, 0.85),
        ),
        (
            "kanji_curriculum_missing_risk",
            "kanji_curriculum_missing",
            (0.65, 0.75, 0.85),
        ),
    ):
        for floor in floors:
            specs.append(
                FinalFloorSpec(
                    spec_id=_floor_id(prefix, 0.50, floor, floor),
                    signal=signal,
                    min_signal=0.50,
                    floor_min=floor,
                    floor_max=floor,
                )
            )
    return tuple(specs)


def _final_adjustment_specs() -> tuple[FinalAdjustmentSpec, ...]:
    specs: list[FinalAdjustmentSpec] = []
    partial_floor_signals = (
        ("missing_frequency_rank_risk", "missing_freq_rank", (0.50,)),
        ("missing_frequency_and_priority_risk", "missing_freq_priority", (0.50,)),
        ("missing_frequency_and_pedagogical_risk", "missing_freq_pedagogical", (0.50,)),
        (
            "missing_frequency_source_evidence_risk",
            "missing_freq_source_evidence",
            (0.10, 0.25, 0.50),
        ),
        (
            "missing_frequency_priority_or_kanji_risk",
            "missing_freq_priority_or_kanji",
            (0.10, 0.25, 0.50),
        ),
        (
            "missing_frequency_priority_pedagogy_risk",
            "missing_freq_priority_pedagogy",
            (0.50,),
        ),
    )
    for signal, prefix, thresholds in partial_floor_signals:
        for threshold in thresholds:
            for floor in (0.70, 0.75, 0.80, 0.85, 0.90):
                for strength in (0.15, 0.25, 0.40, 0.60, 0.80):
                    specs.append(
                        FinalAdjustmentSpec(
                            spec_id=_final_adjustment_id(
                                prefix,
                                "partial_floor",
                                threshold,
                                strength,
                                floor=floor,
                            ),
                            mode="partial_final_floor",
                            signal=signal,
                            threshold=threshold,
                            strength=strength,
                            floor=floor,
                        )
                    )
    for signal, prefix, thresholds in (
        ("missing_frequency_rank_risk", "missing_freq_rank", (0.50,)),
        ("missing_frequency_and_priority_risk", "missing_freq_priority", (0.50,)),
        (
            "missing_frequency_source_evidence_risk",
            "missing_freq_source_evidence",
            (0.10, 0.25, 0.50),
        ),
        (
            "missing_frequency_priority_or_kanji_risk",
            "missing_freq_priority_or_kanji",
            (0.10, 0.25, 0.50),
        ),
    ):
        for threshold in thresholds:
            for strength in (0.10, 0.20, 0.35, 0.50, 0.70):
                specs.append(
                    FinalAdjustmentSpec(
                        spec_id=_final_adjustment_id(
                            prefix,
                            "tail_boost",
                            threshold,
                            strength,
                        ),
                        mode="final_tail_boost",
                        signal=signal,
                        threshold=threshold,
                        strength=strength,
                    )
                )
    return tuple(specs)


def _refined_final_adjustment_specs() -> tuple[FinalAdjustmentSpec, ...]:
    specs: list[FinalAdjustmentSpec] = []
    for signal, prefix, thresholds in (
        (
            "missing_frequency_source_evidence_risk",
            "missing_freq_source_evidence",
            (0.05, 0.10, 0.15, 0.25),
        ),
        (
            "missing_frequency_priority_or_kanji_risk",
            "missing_freq_priority_or_kanji",
            (0.05, 0.10, 0.15, 0.25),
        ),
        (
            "missing_frequency_priority_pedagogy_risk",
            "missing_freq_priority_pedagogy",
            (0.10, 0.25, 0.50),
        ),
    ):
        for threshold in thresholds:
            for floor in (0.84, 0.86, 0.88, 0.90, 0.92, 0.94):
                for strength in (0.60, 0.70, 0.75, 0.80, 0.85, 0.90):
                    specs.append(
                        FinalAdjustmentSpec(
                            spec_id=_final_adjustment_id(
                                prefix,
                                "partial_floor",
                                threshold,
                                strength,
                                floor=floor,
                            ),
                            mode="partial_final_floor",
                            signal=signal,
                            threshold=threshold,
                            strength=strength,
                            floor=floor,
                        )
                    )
    for signal, prefix, thresholds in (
        (
            "missing_frequency_source_evidence_risk",
            "missing_freq_source_evidence",
            (0.05, 0.10, 0.15, 0.25),
        ),
        (
            "missing_frequency_priority_or_kanji_risk",
            "missing_freq_priority_or_kanji",
            (0.05, 0.10, 0.15, 0.25),
        ),
    ):
        for threshold in thresholds:
            for strength in (0.25, 0.35, 0.45, 0.55, 0.65, 0.75):
                specs.append(
                    FinalAdjustmentSpec(
                        spec_id=_final_adjustment_id(
                            prefix,
                            "tail_boost",
                            threshold,
                            strength,
                        ),
                        mode="final_tail_boost",
                        signal=signal,
                        threshold=threshold,
                        strength=strength,
                    )
                )
    return tuple(specs)


def _combined_floor_sets() -> tuple[tuple[FloorSpec, ...], ...]:
    kango = (
        FloorSpec("kango_mid_m35_f35_65", "kango_mid_signal", 0.35, 0.35, 0.65),
        FloorSpec("kango_mid_m50_f40_68", "kango_mid_signal", 0.50, 0.40, 0.68),
    )
    rare = (
        FloorSpec("rare_wago_m25_f75_95", "rare_wago_tail_risk", 0.25, 0.75, 0.95),
        FloorSpec("rare_wago_m50_f80_98", "rare_wago_tail_risk", 0.50, 0.80, 0.98),
    )
    written = (
        FloorSpec("written_wago_m30_f60_85", "written_wago_tail_risk", 0.30, 0.60, 0.85),
        FloorSpec("written_wago_m45_f65_88", "written_wago_tail_risk", 0.45, 0.65, 0.88),
    )
    combined: list[tuple[FloorSpec, ...]] = []
    for kango_floor in kango:
        for rare_floor in rare:
            combined.append((kango_floor, rare_floor))
    for rare_floor in rare:
        for written_floor in written:
            combined.append((rare_floor, written_floor))
    for kango_floor in kango:
        for rare_floor in rare:
            for written_floor in written:
                combined.append((kango_floor, rare_floor, written_floor))
    return tuple(combined)


def _soft_mix_specs(other_expert_id: str) -> tuple[SoftMixSpec, ...]:
    specs: list[SoftMixSpec] = []
    for signal in (
        "frequency",
        "frequency_tail65",
        "frequency_tail80",
        "frequency_tail90",
        "frequency_unranked_floor60_risk",
        "frequency_unranked_floor70_risk",
        "frequency_unranked_floor80_risk",
        "frequency_unranked_floor90_risk",
        "frequency_unranked_floor95_risk",
        "frequency_unranked_floor99_risk",
        "kango_mid_signal",
        "rare_wago_tail_risk",
        "written_wago_tail_risk",
    ):
        for threshold in (0.10, 0.25, 0.50, 0.75):
            for strength in (0.50, 1.00):
                specs.append(
                    SoftMixSpec(
                        spec_id=f"{other_expert_id}__{_boost_id(signal, threshold, strength)}",
                        other_expert_id=other_expert_id,
                        signal=signal,
                        threshold=threshold,
                        strength=strength,
                    )
                )
    return tuple(specs)


def _evaluate_candidates(
    candidates: Sequence[ModelCandidate],
    *,
    component: object,
    calibration_context: Mapping[str, object],
    raw_by_expert: Mapping[str, object],
    signal_arrays: Mapping[str, object],
    detail_candidate_limit: int,
) -> list[dict[str, object]]:
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    calibration_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    target_cure_context = _target_cure_context(
        component=component,
        calibration_context=calibration_context,
    )
    results: list[dict[str, object]] = []
    for candidate in candidates:
        raw = _candidate_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        normalized = _candidate_final_scores(
            candidate,
            normalized,
            signal_arrays=signal_arrays,
        )
        observed = np.full(len(calibration_indices), np.nan, dtype=np.float32)
        valid = calibration_indices >= 0
        observed[valid] = normalized[calibration_indices[valid]]
        metrics = _difficulty_metrics(
            expected_values=calibration_context["expected_values"],
            observed_values=observed,
            expected_bands=calibration_context["expected_bands"],
            labels=calibration_context["labels"],
        )
        reviewed_focus = _reviewed_focus_metrics(
            expected_values=calibration_context["expected_values"],
            observed_values=observed,
            labels=calibration_context["labels"],
        )
        scores = dict(metrics["scores"])
        scores["reviewed_focus_score"] = reviewed_focus["score"]
        target_cure = _target_cure_metrics(
            normalized,
            target_cure_context=target_cure_context,
            include_rows=False,
        )
        scores["target_cure_score"] = target_cure["score"]
        summary_metrics = dict(_summary_metrics(metrics))
        summary_metrics["reviewed_focus_mae"] = reviewed_focus["mae"]
        summary_metrics["reviewed_focus_count"] = reviewed_focus["count"]
        summary_metrics["target_cure_pass_rate"] = target_cure["pass_rate"]
        summary_metrics["target_cure_pass_count"] = target_cure["pass_count"]
        summary_metrics["target_cure_count"] = target_cure["count"]
        results.append(
            {
                "candidate_id": candidate.candidate_id,
                "family": candidate.family,
                "base_expert_id": candidate.base_expert_id,
                "floors": [_floor_json(floor) for floor in candidate.floors],
                "boosts": [_boost_json(boost) for boost in candidate.boosts],
                "soft_mix": _soft_mix_json(candidate.soft_mix),
                "final_floors": [_floor_json(floor) for floor in candidate.final_floors],
                "final_adjustments": [
                    _final_adjustment_json(adjustment) for adjustment in candidate.final_adjustments
                ],
                "stage": "exact",
                "scores": scores,
                "metrics": summary_metrics,
                "reviewed_focus": reviewed_focus,
                "target_cure": target_cure,
                "wrong_pairwise_examples": metrics["pairwise_order"]["wrong_examples"],
                "difficulty_mismatches": metrics["difficulty_bucket"]["mismatches"],
                "segment_misses": {
                    key: value["misses"]
                    for key, value in metrics["segments"].items()
                    if value.get("misses")
                },
            }
        )
    ranked = _top_model_rows(results, limit=len(results))
    if detail_candidate_limit <= 0:
        return ranked
    detail_ids = _detail_candidate_ids(
        ranked,
        detail_candidate_limit=detail_candidate_limit,
    )
    for row in ranked:
        if str(row.get("candidate_id") or "") not in detail_ids:
            continue
        candidate = _candidate_by_id(candidates, str(row.get("candidate_id") or ""))
        if candidate is None:
            continue
        raw = _candidate_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        normalized = _candidate_final_scores(
            candidate,
            normalized,
            signal_arrays=signal_arrays,
        )
        row["target_cure"] = _target_cure_metrics(
            normalized,
            target_cure_context=target_cure_context,
            include_rows=True,
        )
        row["calibration_rows"] = _calibration_detail_rows(
            normalized,
            component=component,
            calibration_context=calibration_context,
        )
        row["band_samples"] = _band_samples(
            normalized,
            component=component,
            segment_ids=np.zeros(len(normalized), dtype=np.int64),
            expert_ids=(candidate.candidate_id,),
            per_band=8,
        )
    return ranked


def _candidate_raw_scores(
    candidate: ModelCandidate,
    *,
    raw_by_expert: Mapping[str, object],
    signal_arrays: Mapping[str, object],
) -> object:
    raw = np.asarray(raw_by_expert[candidate.base_expert_id], dtype=np.float32).copy()
    for floor in candidate.floors:
        raw = _apply_floor(raw, floor, signal_arrays=signal_arrays)
    for boost in candidate.boosts:
        raw = _apply_boost(raw, boost, signal_arrays=signal_arrays)
    if candidate.soft_mix is not None:
        raw = _apply_soft_mix(
            raw,
            candidate.soft_mix,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )
    return np.clip(raw, 0.0, 1.0).astype(np.float32)


def _candidate_final_scores(
    candidate: ModelCandidate,
    normalized: object,
    *,
    signal_arrays: Mapping[str, object],
) -> object:
    values = np.asarray(normalized, dtype=np.float32).copy()
    for floor in candidate.final_floors:
        values = _apply_floor(values, floor, signal_arrays=signal_arrays)
    for adjustment in candidate.final_adjustments:
        values = _apply_final_adjustment(
            values,
            adjustment,
            signal_arrays=signal_arrays,
        )
    return np.clip(values, 0.0, 1.0).astype(np.float32)


def _apply_final_adjustment(
    normalized: object,
    adjustment: FinalAdjustmentSpec,
    *,
    signal_arrays: Mapping[str, object],
) -> object:
    signal = _safe_signal(signal_arrays, adjustment.signal)
    gate = _ramp(signal, lower=adjustment.threshold, upper=1.0)
    values = np.asarray(normalized, dtype=np.float32)
    strength = float(adjustment.strength)
    if adjustment.mode == "partial_final_floor":
        floor = float(adjustment.floor if adjustment.floor is not None else 0.0)
        lift = np.maximum(floor - values, 0.0)
        return (values + (strength * gate * lift)).astype(np.float32)
    if adjustment.mode == "final_tail_boost":
        return (values + (strength * gate * (1.0 - values))).astype(np.float32)
    raise ValueError(f"Unknown final adjustment mode: {adjustment.mode}")


def _apply_floor(
    raw: object,
    floor: FloorSpec | FinalFloorSpec,
    *,
    signal_arrays: Mapping[str, object],
) -> object:
    signal = _safe_signal(signal_arrays, floor.signal)
    gate = _ramp(signal, lower=floor.min_signal, upper=1.0)
    floor_value = float(floor.floor_min) + (float(floor.floor_max) - float(floor.floor_min)) * gate
    active = signal >= float(floor.min_signal)
    return np.where(active, np.maximum(raw, floor_value), raw).astype(np.float32)


def _apply_boost(
    raw: object,
    boost: BoostSpec,
    *,
    signal_arrays: Mapping[str, object],
) -> object:
    signal = _safe_signal(signal_arrays, boost.signal)
    gate = _ramp(signal, lower=boost.threshold, upper=1.0)
    values = np.asarray(raw, dtype=np.float32)
    return (values + (float(boost.strength) * gate * (1.0 - values))).astype(np.float32)


def _apply_soft_mix(
    raw: object,
    soft_mix: SoftMixSpec,
    *,
    raw_by_expert: Mapping[str, object],
    signal_arrays: Mapping[str, object],
) -> object:
    signal = _safe_signal(signal_arrays, soft_mix.signal)
    gate = _ramp(signal, lower=soft_mix.threshold, upper=1.0) * float(soft_mix.strength)
    gate = np.clip(gate, 0.0, 1.0)
    base = np.asarray(raw, dtype=np.float32)
    other = np.asarray(raw_by_expert[soft_mix.other_expert_id], dtype=np.float32)
    return ((base * (1.0 - gate)) + (other * gate)).astype(np.float32)


def _ramp(values: object, *, lower: float, upper: float) -> object:
    if upper <= lower:
        return np.zeros_like(np.asarray(values, dtype=np.float32))
    parsed = np.asarray(values, dtype=np.float32)
    return np.clip((parsed - float(lower)) / (float(upper) - float(lower)), 0.0, 1.0)


def _signal_arrays(component: object) -> dict[str, object]:
    names = [str(value) for value in component["component_names"]]
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    arrays: dict[str, object] = {
        "frequency": np.asarray(component["frequency_values"], dtype=np.float32),
    }
    for index, name in enumerate(names):
        arrays[name] = np.where(present[:, index], values[:, index], 0.0).astype(np.float32)
    arrays.update(_synthesized_missingness_signals(names, values, present, arrays))
    return arrays


def _synthesized_missingness_signals(
    names: Sequence[str],
    values: object,
    present: object,
    arrays: Mapping[str, object],
) -> dict[str, object]:
    column_by_name = {name: index for index, name in enumerate(names)}
    values_array = np.asarray(values, dtype=np.float32)
    present_array = np.asarray(present, dtype=bool)
    row_count = int(present_array.shape[0])

    def column_present(name: str) -> object:
        index = column_by_name.get(name)
        if index is None:
            return np.zeros(row_count, dtype=bool)
        return present_array[:, index]

    def column_value(name: str) -> object:
        index = column_by_name.get(name)
        if index is None:
            return np.zeros(row_count, dtype=np.float32)
        return np.where(present_array[:, index], values_array[:, index], 0.0).astype(np.float32)

    missing_frequency = np.asarray(
        arrays.get("frequency_unranked_risk", np.zeros(row_count, dtype=np.float32)),
        dtype=np.float32,
    )
    jmdict_priority_present = np.asarray(column_present("jmdict_priority"), dtype=bool)
    jmdict_priority = np.asarray(column_value("jmdict_priority"), dtype=np.float32)
    missing_jmdict_priority = np.where(
        (~jmdict_priority_present) | (jmdict_priority >= 0.99),
        1.0,
        0.0,
    ).astype(np.float32)
    missing_jlpt_vocab = (~np.asarray(column_present("jlpt_vocab_difficulty"), dtype=bool)).astype(
        np.float32
    )
    missing_lesson_vocab = (
        ~np.asarray(column_present("lesson_vocab_difficulty"), dtype=bool)
    ).astype(np.float32)
    missing_pedagogical_vocab = np.minimum(
        missing_jlpt_vocab,
        missing_lesson_vocab,
    ).astype(np.float32)
    kanji_curriculum_missing = np.asarray(
        arrays.get("kanji_curriculum_missing_risk", np.zeros(row_count, dtype=np.float32)),
        dtype=np.float32,
    )
    source_evidence = np.maximum.reduce(
        (
            missing_jmdict_priority,
            missing_pedagogical_vocab,
            kanji_curriculum_missing,
        )
    ).astype(np.float32)
    priority_or_kanji = np.maximum(
        missing_jmdict_priority,
        kanji_curriculum_missing,
    ).astype(np.float32)
    priority_or_pedagogical = np.maximum(
        missing_jmdict_priority,
        missing_pedagogical_vocab,
    ).astype(np.float32)
    return {
        "missing_frequency_rank_risk": missing_frequency,
        "missing_jmdict_priority_risk": missing_jmdict_priority,
        "missing_jlpt_vocab_risk": missing_jlpt_vocab,
        "missing_lesson_vocab_risk": missing_lesson_vocab,
        "missing_pedagogical_vocab_risk": missing_pedagogical_vocab,
        "missing_frequency_and_priority_risk": (missing_frequency * missing_jmdict_priority).astype(
            np.float32
        ),
        "missing_frequency_and_pedagogical_risk": (
            missing_frequency * missing_pedagogical_vocab
        ).astype(np.float32),
        "missing_frequency_source_evidence_risk": (missing_frequency * source_evidence).astype(
            np.float32
        ),
        "missing_frequency_priority_or_kanji_risk": (missing_frequency * priority_or_kanji).astype(
            np.float32
        ),
        "missing_frequency_priority_pedagogy_risk": (
            missing_frequency * priority_or_pedagogical
        ).astype(np.float32),
    }


def _safe_signal(signal_arrays: Mapping[str, object], signal: str) -> object:
    value = signal_arrays.get(signal)
    if value is not None:
        return np.asarray(value, dtype=np.float32)
    frequency = signal_arrays.get("frequency")
    if frequency is None:
        raise ValueError("frequency signal is required.")
    return np.zeros_like(np.asarray(frequency, dtype=np.float32))


def _calibration_detail_rows(
    normalized: object,
    *,
    component: object,
    calibration_context: Mapping[str, object],
) -> list[dict[str, object]]:
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    expected_values = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    expected_bands = [str(value) for value in calibration_context["expected_bands"]]
    labels = [str(value) for value in calibration_context["labels"]]
    normalized_values = np.asarray(normalized, dtype=np.float32)
    rows: list[dict[str, object]] = []
    for index, component_index in enumerate(component_indices):
        observed = (
            float(normalized_values[component_index])
            if component_index >= 0 and np.isfinite(normalized_values[component_index])
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
        rows.append(
            {
                "label": labels[index],
                "expected_band": expected_bands[index],
                "expected_value": _rounded(expected),
                "observed_value": _rounded(observed),
                "absolute_error": _rounded(error),
                "direction": direction,
                "signals": (
                    _calibration_signal_values(component, int(component_index))
                    if component_index >= 0
                    else {}
                ),
            }
        )
    return rows


def _calibration_signal_values(component: object, row_index: int) -> dict[str, object]:
    names = [str(value) for value in component["component_names"]]
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    by_name = {name: index for index, name in enumerate(names)}
    row: dict[str, object] = {}
    for signal in SIGNAL_COLUMNS:
        if signal == "frequency":
            row[signal] = _rounded(float(component["frequency_values"][row_index]))
            continue
        column = by_name.get(signal)
        if column is None or not bool(present[row_index, column]):
            row[signal] = None
            continue
        row[signal] = _rounded(float(values[row_index, column]))
    return row


def _top_model_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in sorted(
            rows,
            key=lambda row: (
                _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("pairwise_order_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("numeric_mae_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("upper_tail_score")) or -1.0,
            ),
            reverse=True,
        )[:limit]
    ]


def _detail_candidate_ids(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_candidate_limit: int,
) -> set[str]:
    selected: set[str] = set()
    for row in rows[:detail_candidate_limit]:
        if row.get("candidate_id"):
            selected.add(str(row["candidate_id"]))
    per_metric_limit = max(1, min(8, detail_candidate_limit))
    for score_key in (
        "target_cure_score",
        "reviewed_focus_score",
        "numeric_mae_score",
        "pairwise_order_score",
        "bucket_accuracy_score",
    ):
        ranked = sorted(
            rows,
            key=lambda row: _optional_float(_mapping(row.get("scores")).get(score_key)) or -1.0,
            reverse=True,
        )
        for row in ranked[:per_metric_limit]:
            if row.get("candidate_id"):
                selected.add(str(row["candidate_id"]))
    return selected


def _leaderboards(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> dict[str, list[dict[str, object]]]:
    leaderboards: dict[str, list[dict[str, object]]] = {}
    for score_key in LEADERBOARD_SCORE_KEYS:
        ranked = sorted(
            rows,
            key=lambda row: _optional_float(_mapping(row.get("scores")).get(score_key)) or -1.0,
            reverse=True,
        )
        leaderboards[score_key] = [
            {
                "candidate_id": row.get("candidate_id"),
                "family": row.get("family"),
                "score_key": score_key,
                "score": _mapping(row.get("scores")).get(score_key),
                "balanced_score": _mapping(row.get("scores")).get("balanced_score"),
                "reviewed_focus_score": _mapping(row.get("scores")).get("reviewed_focus_score"),
                "target_cure_score": _mapping(row.get("scores")).get("target_cure_score"),
                "mae": _mapping(row.get("metrics")).get("mae"),
                "target_cure_pass_rate": _mapping(row.get("metrics")).get("target_cure_pass_rate"),
                "reviewed_focus_mae": _mapping(row.get("metrics")).get("reviewed_focus_mae"),
                "bucket_accuracy": _mapping(row.get("metrics")).get("bucket_accuracy"),
                "pairwise_accuracy": _mapping(row.get("metrics")).get("pairwise_accuracy"),
            }
            for row in ranked[:limit]
        ]
    return leaderboards


def _reviewed_focus_metrics(
    *,
    expected_values: object,
    observed_values: object,
    labels: Sequence[str],
) -> dict[str, object]:
    expected = np.asarray(expected_values, dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    mask = np.asarray(
        [str(label) in REVIEWED_FOCUS_LABELS for label in labels],
        dtype=bool,
    )
    finite = mask & np.isfinite(expected) & np.isfinite(observed)
    if not bool(finite.any()):
        return {
            "label_set": sorted(REVIEWED_FOCUS_LABELS),
            "count": 0,
            "mae": None,
            "score": None,
            "within_0_10": 0,
        }
    errors = np.abs(observed[finite] - expected[finite])
    return {
        "label_set": sorted(REVIEWED_FOCUS_LABELS),
        "count": int(finite.sum()),
        "mae": _rounded(float(errors.mean())),
        "score": _rounded(max(0.0, 1.0 - float(errors.mean()))),
        "within_0_10": int((errors <= 0.10).sum()),
    }


def _target_cure_metrics(
    normalized: object,
    *,
    target_cure_context: Sequence[Mapping[str, object]],
    include_rows: bool = False,
) -> dict[str, object]:
    rows = _target_cure_rows_for_context(
        normalized,
        target_cure_context=target_cure_context,
        include_signals=include_rows,
    )
    scorable = [row for row in rows if row.get("pass") is not None]
    if not scorable:
        return {
            "score": None,
            "pass_count": 0,
            "count": 0,
            "pass_rate": None,
            "rows": rows if include_rows else [],
        }
    pass_count = sum(1 for row in scorable if row.get("pass") is True)
    error_values = [
        float(row["absolute_error"])
        for row in scorable
        if _optional_float(row.get("absolute_error")) is not None
    ]
    mean_error = sum(error_values) / len(error_values) if error_values else None
    pass_rate = pass_count / len(scorable)
    error_score = 1.0 - mean_error if mean_error is not None else pass_rate
    score = (0.70 * pass_rate) + (0.30 * max(0.0, min(1.0, error_score)))
    return {
        "score": _rounded(score),
        "pass_count": pass_count,
        "count": len(scorable),
        "pass_rate": _rounded(pass_rate),
        "mean_error": _rounded(mean_error),
        "rows": rows if include_rows else [],
    }


def _target_cure_context(
    *,
    component: object,
    calibration_context: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(
        _target_cure_context_from_calibration(
            component=component,
            calibration_context=calibration_context,
        )
    )
    rows.extend(
        _target_cure_context_from_watch_specs(
            component=component,
        )
    )
    return rows


def _target_cure_context_from_calibration(
    *,
    component: object,
    calibration_context: Mapping[str, object],
) -> list[dict[str, object]]:
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    expected_values = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in calibration_context["labels"]]
    rows: list[dict[str, object]] = []
    for index, label in enumerate(labels):
        if label not in REVIEWED_FOCUS_LABELS:
            continue
        component_index = int(component_indices[index])
        expected = float(expected_values[index]) if np.isfinite(expected_values[index]) else None
        rows.append(
            {
                "label": label,
                "source": "calibration",
                "component_index": component_index,
                "expected_value": expected,
                "min_value": None,
                "max_value": None,
                "rationale": "Reviewed calibration focus row.",
                "signals": (
                    _calibration_signal_values(component, component_index)
                    if component_index >= 0
                    else {}
                ),
            }
        )
    return rows


def _target_cure_context_from_watch_specs(
    *,
    component: object,
) -> list[dict[str, object]]:
    row_lookup = _component_row_lookup(component)
    rows: list[dict[str, object]] = []
    for spec in TARGET_CURE_WATCH_SPECS:
        component_index = row_lookup.get(
            (str(spec.get("lemma") or ""), str(spec.get("reading") or ""))
        )
        rows.append(
            {
                "label": str(spec.get("label") or ""),
                "source": "watch",
                "component_index": component_index,
                "expected_value": _optional_float(spec.get("expected_value")),
                "min_value": _optional_float(spec.get("min_value")),
                "max_value": _optional_float(spec.get("max_value")),
                "rationale": str(spec.get("rationale") or ""),
                "signals": (
                    _calibration_signal_values(component, component_index)
                    if component_index is not None
                    else {}
                ),
            }
        )
    return rows


def _component_row_lookup(component: object) -> dict[tuple[str, str], int]:
    lemmas = [str(value) for value in component["lemmas"]]
    readings = [str(value) for value in component["readings"]]
    lookup: dict[tuple[str, str], int] = {}
    for index, (lemma, reading) in enumerate(zip(lemmas, readings)):
        lookup.setdefault((lemma, reading), index)
    return lookup


def _target_cure_rows_for_context(
    normalized: object,
    *,
    target_cure_context: Sequence[Mapping[str, object]],
    include_signals: bool,
) -> list[dict[str, object]]:
    normalized_values = np.asarray(normalized, dtype=np.float32)
    rows: list[dict[str, object]] = []
    for item in target_cure_context:
        component_index = item.get("component_index")
        observed = (
            float(normalized_values[int(component_index)])
            if isinstance(component_index, int) and int(component_index) >= 0
            else None
        )
        rows.append(
            _target_cure_row(
                label=str(item.get("label") or ""),
                source=str(item.get("source") or ""),
                observed=observed,
                expected=_optional_float(item.get("expected_value")),
                min_value=_optional_float(item.get("min_value")),
                max_value=_optional_float(item.get("max_value")),
                rationale=str(item.get("rationale") or ""),
                signals=_mapping(item.get("signals")) if include_signals else {},
            )
        )
    return rows


def _target_cure_row(
    *,
    label: str,
    source: str,
    observed: float | None,
    expected: float | None,
    min_value: float | None,
    max_value: float | None,
    rationale: str,
    signals: Mapping[str, object],
) -> dict[str, object]:
    absolute_error = None
    passed = None
    direction = ""
    if observed is not None and expected is not None:
        absolute_error = abs(observed - expected)
        passed = absolute_error <= TARGET_CURE_ABS_TOLERANCE
        if observed < expected:
            direction = "too_low"
        elif observed > expected:
            direction = "too_high"
    elif observed is not None:
        above_min = min_value is None or observed >= min_value
        below_max = max_value is None or observed <= max_value
        passed = above_min and below_max
        if min_value is not None and observed < min_value:
            direction = "too_low"
            absolute_error = min_value - observed
        elif max_value is not None and observed > max_value:
            direction = "too_high"
            absolute_error = observed - max_value
        else:
            absolute_error = 0.0
    return {
        "label": label,
        "source": source,
        "observed_value": _rounded(observed),
        "expected_value": _rounded(expected),
        "min_value": _rounded(min_value),
        "max_value": _rounded(max_value),
        "absolute_error": _rounded(absolute_error),
        "direction": direction,
        "pass": passed,
        "rationale": rationale,
        "signals": dict(signals),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Learner Difficulty Model Family Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Trace variants: `{_escape(inputs.get('trace_variant_count'))}`",
        f"- Expert pool size: `{_escape(inputs.get('expert_pool_size'))}`",
        f"- Evaluated candidates: `{_escape(inputs.get('evaluated_candidate_count'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Normalization population: `{_escape(inputs.get('normalization_population_count'))}`",
        "",
        "## Method",
        "",
        (
            "This search tests model families that the plain grid sweep cannot "
            "express directly: bounded floors, hinge/ramp boosts, combined floors, "
            "final floors, and soft mixtures of linear experts. Every candidate "
            "is evaluated exactly over the full component matrix, then globally "
            "target-curve normalized; final-floor candidates apply their explicit "
            "floor after that normalization."
        ),
        "",
        "## Candidate Family Counts",
        "",
    ]
    for family, count in _mapping(report.get("candidate_family_counts")).items():
        lines.append(f"- `{_escape(family)}`: `{_escape(count)}`")
    lines.extend(
        [
            "",
            "## Exact Top Candidates",
            "",
            (
                "| Rank | Candidate | Family | Balanced | Cure | Focus | MAE | Bucket | Pairwise | "
                "Spearman | Beginner | High tail | Upper tail |"
            ),
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, row in enumerate(_mapping_rows(report.get("exact_top"))[:25], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            "| "
            f"{index} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('family'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(scores.get('target_cure_score'))}` | "
            f"`{_escape(scores.get('reviewed_focus_score'))}` | "
            f"`{_escape(metrics.get('mae'))}` | "
            f"`{_escape(metrics.get('bucket_accuracy'))}` | "
            f"`{_escape(metrics.get('pairwise_accuracy'))}` | "
            f"`{_escape(metrics.get('spearman'))}` | "
            f"`{_escape(metrics.get('beginner_core_pass_rate'))}` | "
            f"`{_escape(metrics.get('high_tail_pass_rate'))}` | "
            f"`{_escape(scores.get('upper_tail_score'))}` |"
        )
    lines.extend(["", "## Leaderboards", ""])
    for score_key, rows in _mapping(report.get("leaderboards")).items():
        lines.extend(
            [
                f"### `{_escape(score_key)}`",
                "",
                "| Rank | Candidate | Family | Score | Balanced | Cure | Focus | MAE | Pairwise |",
                "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for index, row in enumerate(_mapping_rows(rows)[:10], start=1):
            lines.append(
                "| "
                f"{index} | "
                f"`{_escape(row.get('candidate_id'))}` | "
                f"`{_escape(row.get('family'))}` | "
                f"`{_escape(row.get('score'))}` | "
                f"`{_escape(row.get('balanced_score'))}` | "
                f"`{_escape(row.get('target_cure_score'))}` | "
                f"`{_escape(row.get('reviewed_focus_score'))}` | "
                f"`{_escape(row.get('mae'))}` | "
                f"`{_escape(row.get('pairwise_accuracy'))}` |"
            )
        lines.append("")
    lines.extend(["", "## Top Candidate Details", ""])
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        metrics = _mapping(row.get("metrics"))
        lines.extend(
            [
                f"### `{_escape(row.get('candidate_id'))}`",
                "",
                f"- Family: `{_escape(row.get('family'))}`",
                f"- Base expert: `{_escape(row.get('base_expert_id'))}`",
                f"- Floors: `{_escape(_compact_spec_rows(row.get('floors')) or 'none')}`",
                f"- Boosts: `{_escape(_compact_spec_rows(row.get('boosts')) or 'none')}`",
                f"- Soft mix: `{_escape(_compact_counts(row.get('soft_mix')) if row.get('soft_mix') else 'none')}`",
                f"- Final floors: `{_escape(_compact_spec_rows(row.get('final_floors')) or 'none')}`",
                f"- Final adjustments: `{_escape(_compact_spec_rows(row.get('final_adjustments')) or 'none')}`",
                f"- Scores: `{_compact_counts(row.get('scores'))}`",
                f"- Metrics: `{_compact_counts(metrics)}`",
            ]
        )
        target_cure = _mapping(row.get("target_cure"))
        target_rows = _mapping_rows(target_cure.get("rows"))
        if target_rows:
            cured = sum(1 for item in target_rows if item.get("pass") is True)
            lines.append(
                f"- Target cure: `{cured}/{len(target_rows)}` pass, "
                f"score `{_escape(target_cure.get('score'))}`"
            )
            misses = [item for item in target_rows if item.get("pass") is False]
            if misses:
                text = ", ".join(
                    f"{item.get('label')} obs={item.get('observed_value')} "
                    f"target={item.get('expected_value') or item.get('min_value') or item.get('max_value')} "
                    f"{item.get('direction')}"
                    for item in misses[:10]
                )
                lines.append(f"- Target cure misses: {text}")
        mismatches = _mapping_rows(row.get("difficulty_mismatches"))
        if mismatches:
            text = ", ".join(
                f"{item.get('label')} ({item.get('expected')}->{item.get('observed')})"
                for item in mismatches[:12]
            )
            lines.append(f"- Difficulty mismatches: {text}")
        wrong = _mapping_rows(row.get("wrong_pairwise_examples"))
        if wrong:
            text = ", ".join(
                f"{item.get('expected_easier')} < {item.get('expected_harder')} obs_gap={item.get('observed_gap')}"
                for item in wrong[:8]
            )
            lines.append(f"- Pairwise misses: {text}")
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
            "| Expert | Balanced | MAE | Bucket | Pairwise | Beginner | High tail | Weights | Cap |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for expert in _mapping_rows(report.get("expert_pool")):
        scores = _mapping(expert.get("source_scores"))
        mae_score = _optional_float(scores.get("numeric_mae_score"))
        lines.append(
            "| "
            f"`{_escape(expert.get('variant_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(_rounded(1.0 - mae_score) if mae_score is not None else '')}` | "
            f"`{_escape(scores.get('bucket_accuracy_score'))}` | "
            f"`{_escape(scores.get('pairwise_order_score'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_compact_counts(expert.get('weights'))}` | "
            f"`{_escape(expert.get('max_shift_from_frequency'))}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_calibration_rows_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-ja Model Family Calibration Rows",
        "",
        (
            "| Candidate | Rank | Label | Expected | Observed | Error | Direction | "
            "Freq | KangoMid | RareWagoTail | WrittenWagoTail |"
        ),
        "| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
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
            f"`{_escape(row.get('signal_frequency'))}` | "
            f"`{_escape(row.get('signal_kango_mid_signal'))}` | "
            f"`{_escape(row.get('signal_rare_wago_tail_risk'))}` | "
            f"`{_escape(row.get('signal_written_wago_tail_risk'))}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_calibration_rows_csv(report: Mapping[str, object]) -> str:
    rows = _flat_calibration_rows(report)
    headers = [
        "candidate_id",
        "rank",
        "label",
        "expected_band",
        "expected_value",
        "observed_value",
        "absolute_error",
        "direction",
        *[f"signal_{signal}" for signal in SIGNAL_COLUMNS],
    ]
    lines = [",".join(headers)]
    for row in rows:
        values = [_csv_cell(row.get(header)) for header in headers]
        lines.append(",".join(values))
    return "\n".join(lines).rstrip() + "\n"


def _flat_calibration_rows(report: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, candidate in enumerate(_mapping_rows(report.get("exact_top")), start=1):
        if not candidate.get("calibration_rows"):
            continue
        candidate_id = str(candidate.get("candidate_id") or "")
        for calibration_row in _mapping_rows(candidate.get("calibration_rows")):
            flattened = {
                "candidate_id": candidate_id,
                "rank": rank,
                "label": calibration_row.get("label"),
                "expected_band": calibration_row.get("expected_band"),
                "expected_value": calibration_row.get("expected_value"),
                "observed_value": calibration_row.get("observed_value"),
                "absolute_error": calibration_row.get("absolute_error"),
                "direction": calibration_row.get("direction"),
            }
            signals = _mapping(calibration_row.get("signals"))
            for signal in SIGNAL_COLUMNS:
                flattened[f"signal_{signal}"] = signals.get(signal)
            rows.append(flattened)
    return rows


def _candidate_by_id(
    candidates: Sequence[ModelCandidate],
    candidate_id: str,
) -> ModelCandidate | None:
    for candidate in candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    return None


def _candidate_family_counts(candidates: Sequence[ModelCandidate]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.family] = counts.get(candidate.family, 0) + 1
    return counts


def _floor_json(floor: FloorSpec) -> dict[str, object]:
    return {
        "spec_id": floor.spec_id,
        "signal": floor.signal,
        "min_signal": floor.min_signal,
        "floor_min": floor.floor_min,
        "floor_max": floor.floor_max,
    }


def _boost_json(boost: BoostSpec) -> dict[str, object]:
    return {
        "spec_id": boost.spec_id,
        "signal": boost.signal,
        "threshold": boost.threshold,
        "strength": boost.strength,
    }


def _soft_mix_json(soft_mix: SoftMixSpec | None) -> dict[str, object] | None:
    if soft_mix is None:
        return None
    return {
        "spec_id": soft_mix.spec_id,
        "other_expert_id": soft_mix.other_expert_id,
        "signal": soft_mix.signal,
        "threshold": soft_mix.threshold,
        "strength": soft_mix.strength,
    }


def _final_adjustment_json(adjustment: FinalAdjustmentSpec) -> dict[str, object]:
    return {
        "spec_id": adjustment.spec_id,
        "mode": adjustment.mode,
        "signal": adjustment.signal,
        "threshold": adjustment.threshold,
        "strength": adjustment.strength,
        "floor": adjustment.floor,
    }


def _compact_spec_rows(value: object) -> str:
    rows = _mapping_rows(value)
    return "; ".join(str(_compact_counts(row)) for row in rows)


def _floor_id(prefix: str, min_signal: float, floor_min: float, floor_max: float) -> str:
    return (
        f"{prefix}_m{_value_label(min_signal)}_f{_value_label(floor_min)}_{_value_label(floor_max)}"
    )


def _boost_id(signal: str, threshold: float, strength: float) -> str:
    return f"{signal}_t{_value_label(threshold)}_s{_value_label(strength)}"


def _final_adjustment_id(
    signal: str,
    mode: str,
    threshold: float,
    strength: float,
    *,
    floor: float | None = None,
) -> str:
    floor_label = "" if floor is None else f"_f{_value_label(floor)}"
    return f"{signal}_{mode}_t{_value_label(threshold)}_s{_value_label(strength)}{floor_label}"


def _value_label(value: float) -> str:
    return f"{int(round(float(value) * 100)):02d}"


def _csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if any(char in text for char in (",", '"', "\n")):
        return '"' + text.replace('"', '""') + '"'
    return text


if __name__ == "__main__":
    raise SystemExit(main())
