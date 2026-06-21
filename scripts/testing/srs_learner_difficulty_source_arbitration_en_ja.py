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
    DEFAULT_REVIEW_MARKDOWN,
    holdout_context_from_rows,
    parse_holdout_review_markdown,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _band_samples,
    _calibration_context,
    _difficulty_metrics,
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


PAIR = "en-ja"
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_calibration_matrix_latest.npz"
)
DEFAULT_REFERENCE_HOLDOUT_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_holdout_eval_en_ja_source_arbitration_surface_s010_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_en_ja_latest.md"
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
GUARDRAIL_PAIRWISE_MIN = 0.880
GUARDRAIL_BEGINNER_CORE_MIN = 0.900
GUARDRAIL_HIGH_TAIL_MIN = 0.500
READING_FORM_SOURCE_SIGNALS = (
    "jmdict_reading_form_marked_risk",
    "jmdict_reading_form_marked_flag",
    "jmdict_reading_restricted_risk",
    "jmdict_reading_restricted_flag",
    "jmdict_kana_preferred_risk",
    "jmdict_no_kanji_reading_risk",
    "jmdict_kanji_form_marked_risk",
    "jmdict_search_only_form_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
)
RARE_READING_FORM_SIGNALS = (
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
)
SAME_SURFACE_FOCUS_ROWS = (
    ("外国", "とつくに"),
    ("外国", "がいこく"),
    ("誘う", "いざなう"),
    ("誘う", "さそう"),
    ("辛い", "つらい"),
    ("真", "まこと"),
    ("火", "か"),
    ("否", "いや"),
    ("上", "へ"),
    ("海", "あま"),
    ("厳しい", "いつくしい"),
    ("居る", "いる"),
    ("呉れる", "くれる"),
)


@dataclass(frozen=True)
class SourceArbitrationCandidate:
    candidate_id: str
    candidate_family: str
    ped_mode: str
    native_mode: str
    base_mode: str
    ped_strength: float
    tail_source: str
    tail_lower: float
    tail_upper: float
    burden_mode: str
    burden_delta: float
    entity_delta: float
    entity_gate_mode: str
    topic_delta: float
    topic_gate_mode: str
    ordinary_cap: float
    ordinary_cap_mode: str
    ordinary_cap_strength: float
    ordinary_gate_mode: str
    reading_guard_delta: float
    tail_floor: float
    tail_floor_mode: str
    same_surface_floor: float
    same_surface_floor_mode: str
    same_surface_source_attenuation: float
    same_surface_source_attenuation_mode: str
    jlpt_ped_mode: str = "broad"
    jlpt_exact_blend: float = 0.0
    jlpt_exact_blend_gate_mode: str = "none"
    jlpt_exact_min_gap: float = 0.0
    jlpt_inherited_penalty: float = 0.0
    jlpt_inherited_penalty_mode: str = "none"
    same_surface_secondary_floor: float = 0.0
    same_surface_secondary_floor_mode: str = "none"
    gairaigo_source_delta: float = 0.0
    gairaigo_source_gate_mode: str = "none"
    gairaigo_english_ease_delta: float = 0.0
    gairaigo_english_ease_mode: str = "none"
    gairaigo_jlpt_raise_block: bool = False
    jlpt_bound_mode: str = "none"
    jlpt_bound_margin: float = 0.0
    jlpt_bound_strength: float = 1.0


@dataclass(frozen=True)
class ComponentView:
    names: tuple[str, ...]
    name_to_index: Mapping[str, int]
    values: object
    present: object
    frequency: object
    target_positions: object
    lemmas: object
    readings: object
    identities: object
    candidate_states: object
    core_ranks: object

    @classmethod
    def from_npz(cls, component: object) -> "ComponentView":
        names = tuple(str(value) for value in component["component_names"])
        frequency = np.asarray(component["frequency_values"], dtype=np.float32)
        count = len(frequency)
        return cls(
            names=names,
            name_to_index={name: index for index, name in enumerate(names)},
            values=np.asarray(component["component_values"], dtype=np.float32),
            present=np.asarray(component["component_present"], dtype=bool),
            frequency=frequency,
            target_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
            lemmas=component["lemmas"],
            readings=component["readings"],
            identities=component["candidate_identity_keys"],
            candidate_states=(
                component["candidate_states"]
                if "candidate_states" in component.files
                else np.full(count, "normal_vocab", dtype="<U12")
            ),
            core_ranks=(
                np.asarray(component["core_ranks"], dtype=np.float32)
                if "core_ranks" in component.files
                else np.full(count, np.nan, dtype=np.float32)
            ),
        )

    def value(self, name: str, *, fill: float = np.nan) -> object:
        index = self.name_to_index.get(name)
        if index is None:
            return np.full(len(self.frequency), fill, dtype=np.float32)
        values = self.values[:, index]
        present = self.present[:, index]
        return np.where(present, values, fill).astype(np.float32)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a field-knowledge source-arbitration learner-difficulty "
            "candidate family for en-ja."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument(
        "--reference-holdout-json",
        type=Path,
        default=DEFAULT_REFERENCE_HOLDOUT_JSON,
        help=(
            "Optional holdout-eval artifact for old-method reference candidates. "
            "If missing, the source-arbitration report is still generated."
        ),
    )
    parser.add_argument("--leaderboard-limit", type=int, default=20)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--band-sample-size", type=int, default=6)
    parser.add_argument(
        "--candidate-family",
        choices=(
            "v1",
            "v2",
            "ordinary_refine",
            "same_surface_alt",
            "same_surface_attenuate",
            "same_surface_combo",
            "gairaigo_source_refine",
            "jlpt_guard_refine",
            "jlpt_exact_ped_refine",
            "jlpt_exact_surface_inheritance_sweep",
        ),
        default="v1",
        help=(
            "Candidate grid to evaluate. v1 preserves the original sidecar shape; "
            "v2 adds ordinary/common protection, reading-inheritance guards, "
            "and high-tail floor repair around the promising v1 neighborhood; "
            "ordinary_refine focuses on ordinary-cap values, gate definitions, "
            "and hard/soft cap operators around the v2 winner; "
            "same_surface_alt tests a narrow same-written-form alternate-reading "
            "floor around the ordinary_refine winner; same_surface_attenuate "
            "tests discounting inherited source easiness before base scoring; "
            "same_surface_combo sweeps both shapes together around the current "
            "ordinary-cap winner; gairaigo_source_refine tests JMDict "
            "source-language and English-frequency loanword refinements around "
            "the same-surface combo winner; jlpt_guard_refine tests broad "
            "JLPT-known guards and bounds around the gairaigo refinement; "
            "jlpt_exact_ped_refine tests exact JLPT pedagogical anchors and "
            "surface-family inheritance floors around the current candidate; "
            "jlpt_exact_surface_inheritance_sweep broadly sweeps exact-JLPT "
            "blending, family-only JLPT inheritance penalties, and primary/"
            "secondary same-surface floors."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        review_markdown=_resolve_path(args.review_markdown),
        reference_holdout_json=_resolve_path(args.reference_holdout_json)
        if args.reference_holdout_json
        else None,
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        detail_limit=max(1, int(args.detail_limit)),
        band_sample_size=max(1, int(args.band_sample_size)),
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
    review_markdown: Path,
    reference_holdout_json: Path | None,
    leaderboard_limit: int = 20,
    detail_limit: int = 20,
    band_sample_size: int = 6,
    candidate_family: str = "v1",
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    view = ComponentView.from_npz(component)
    calibration_context = _calibration_context(calibration, component)
    holdout_rows = parse_holdout_review_markdown(review_markdown)
    holdout_context = holdout_context_from_rows(holdout_rows, component)
    candidates = generate_candidates(candidate_family=candidate_family)
    parts = family_parts(view)
    candidate_results: list[dict[str, object]] = []
    for candidate in candidates:
        normalized = normalized_scores_for_candidate(candidate, view, parts=parts)
        candidate_results.append(
            result_for_candidate(
                candidate,
                normalized=normalized,
                component=component,
                view=view,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                include_details=False,
                detail_limit=detail_limit,
                band_sample_size=band_sample_size,
            )
        )
    leaderboards = build_leaderboards(candidate_results, limit=leaderboard_limit)
    detailed_candidate_ids = _detailed_candidate_ids(leaderboards)
    detailed_results = []
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    for candidate_id in detailed_candidate_ids:
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            continue
        normalized = normalized_scores_for_candidate(candidate, view, parts=parts)
        detailed_results.append(
            result_for_candidate(
                candidate,
                normalized=normalized,
                component=component,
                view=view,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                include_details=True,
                detail_limit=detail_limit,
                band_sample_size=band_sample_size,
            )
        )
    reference_summary = load_reference_summary(reference_holdout_json)
    best_holdout = leaderboards["holdout_balanced"][0] if leaderboards["holdout_balanced"] else {}
    best_calibration = (
        leaderboards["calibration_balanced"][0] if leaderboards["calibration_balanced"] else {}
    )
    same_surface_alt_impact = same_surface_alt_impact_report(
        candidate_family=candidate_family,
        candidate_results=candidate_results,
        candidate_by_id=candidate_by_id,
        view=view,
        parts=parts,
        component=component,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Controlled sidecar search over conditional source-arbitration "
                "and bounded-adjustment model shapes."
            ),
            "shape": (
                "base = source-arbitrated pedagogical/native spine; burden, "
                "entity, topic, optional same-surface alternate-reading floors, "
                "and optional same-surface source attenuation are gated and bounded."
            ),
            "candidate_family": candidate_family,
            "selection_policy": (
                "Candidates are generated from a constrained field-knowledge grid. "
                "Calibration and holdout are reported separately; holdout is not "
                "used to generate candidates."
            ),
            "guardrails": {
                "pairwise_order_score_min": GUARDRAIL_PAIRWISE_MIN,
                "beginner_core_score_min": GUARDRAIL_BEGINNER_CORE_MIN,
                "high_tail_score_min": GUARDRAIL_HIGH_TAIL_MIN,
            },
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "review_markdown": _repo_or_home_path(review_markdown),
            "reference_holdout_json": (
                _repo_or_home_path(reference_holdout_json)
                if reference_holdout_json and reference_holdout_json.exists()
                else None
            ),
            "component_count": len(view.names),
            "candidate_count": len(candidate_results),
            "candidate_family": candidate_family,
            "holdout_numeric_count": int(np.isfinite(holdout_context["expected_values"]).sum()),
        },
        "summary": {
            "best_holdout_balanced": best_holdout,
            "best_calibration_balanced": best_calibration,
            "reference_best_holdout_balanced": reference_summary.get("best_holdout_balanced"),
            "reference_best_calibration_balanced": reference_summary.get(
                "best_calibration_balanced"
            ),
        },
        "leaderboards": leaderboards,
        "reference_summary": reference_summary,
        "same_surface_alt_impact": same_surface_alt_impact,
        "candidate_results": candidate_results,
        "detailed_results": detailed_results,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "review_markdown": review_markdown,
                "reference_holdout_json": (
                    reference_holdout_json
                    if reference_holdout_json and reference_holdout_json.exists()
                    else None
                ),
            },
            code_paths={
                "holdout_eval": SCRIPT_DIR / "srs_learner_difficulty_holdout_eval_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def generate_candidates(*, candidate_family: str = "v1") -> tuple[SourceArbitrationCandidate, ...]:
    if candidate_family == "v1":
        return generate_v1_candidates()
    if candidate_family == "v2":
        return generate_v2_candidates()
    if candidate_family == "ordinary_refine":
        return generate_ordinary_refine_candidates()
    if candidate_family == "same_surface_alt":
        return generate_same_surface_alt_candidates()
    if candidate_family == "same_surface_attenuate":
        return generate_same_surface_attenuate_candidates()
    if candidate_family == "same_surface_combo":
        return generate_same_surface_combo_candidates()
    if candidate_family == "gairaigo_source_refine":
        return generate_gairaigo_source_refine_candidates()
    if candidate_family == "jlpt_guard_refine":
        return generate_jlpt_guard_refine_candidates()
    if candidate_family == "jlpt_exact_ped_refine":
        return generate_jlpt_exact_ped_refine_candidates()
    if candidate_family == "jlpt_exact_surface_inheritance_sweep":
        return generate_jlpt_exact_surface_inheritance_sweep_candidates()
    raise ValueError(f"Unsupported candidate family: {candidate_family}")


def generate_v1_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    ped_modes = ("min", "mean")
    native_modes = ("frequency", "mean", "min")
    base_specs = (
        ("native", (1.0,)),
        ("ped_override", (1.0,)),
        ("ped_native_min", (1.0,)),
        ("weighted", (1.0, 2.0, 4.0)),
    )
    tail_specs = (
        ("base", 0.55, 0.90),
        ("base", 0.65, 0.95),
        ("frequency", 0.65, 0.95),
    )
    burden_deltas = (0.0, 0.05, 0.10, 0.15)
    entity_deltas = (0.0, 0.05, 0.10)
    topic_deltas = (0.0, 0.05)
    for ped_mode in ped_modes:
        for native_mode in native_modes:
            for base_mode, strengths in base_specs:
                for ped_strength in strengths:
                    for tail_source, tail_lower, tail_upper in tail_specs:
                        for burden_mode in ("max", "mean"):
                            for burden_delta in burden_deltas:
                                for entity_delta in entity_deltas:
                                    for entity_gate_mode in ("weak", "weak_rarity"):
                                        for topic_delta in topic_deltas:
                                            for topic_gate_mode in ("rarity", "weak_rarity"):
                                                params = {
                                                    "p": ped_mode,
                                                    "n": native_mode,
                                                    "b": base_mode,
                                                    "ps": ped_strength,
                                                    "ts": tail_source,
                                                    "tl": tail_lower,
                                                    "tu": tail_upper,
                                                    "bm": burden_mode,
                                                    "bd": burden_delta,
                                                    "ed": entity_delta,
                                                    "eg": entity_gate_mode,
                                                    "td": topic_delta,
                                                    "tg": topic_gate_mode,
                                                }
                                                candidates.append(
                                                    SourceArbitrationCandidate(
                                                        candidate_id=_candidate_id(params),
                                                        candidate_family="v1",
                                                        ped_mode=ped_mode,
                                                        native_mode=native_mode,
                                                        base_mode=base_mode,
                                                        ped_strength=ped_strength,
                                                        tail_source=tail_source,
                                                        tail_lower=tail_lower,
                                                        tail_upper=tail_upper,
                                                        burden_mode=burden_mode,
                                                        burden_delta=burden_delta,
                                                        entity_delta=entity_delta,
                                                        entity_gate_mode=entity_gate_mode,
                                                        topic_delta=topic_delta,
                                                        topic_gate_mode=topic_gate_mode,
                                                        ordinary_cap=0.0,
                                                        ordinary_cap_mode="none",
                                                        ordinary_cap_strength=1.0,
                                                        ordinary_gate_mode="max",
                                                        reading_guard_delta=0.0,
                                                        tail_floor=0.0,
                                                        tail_floor_mode="none",
                                                        same_surface_floor=0.0,
                                                        same_surface_floor_mode="none",
                                                        same_surface_source_attenuation=0.0,
                                                        same_surface_source_attenuation_mode="none",
                                                    )
                                                )
    return tuple(candidates)


def generate_v2_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    ped_modes = ("min", "mean")
    native_modes = ("mean",)
    base_specs = (
        ("ped_native_min", (1.0,)),
        ("weighted", (2.0, 4.0)),
    )
    tail_specs = (
        ("base", 0.55, 0.90),
        ("base", 0.65, 0.95),
    )
    burden_deltas = (0.0, 0.05, 0.10)
    entity_deltas = (0.0, 0.05)
    topic_deltas = (0.0, 0.05)
    ordinary_caps = (0.0, 0.35, 0.45, 0.55)
    reading_guard_deltas = (0.0, 0.05, 0.10, 0.15)
    tail_floor_specs = (
        ("none", 0.0),
        ("rare", 0.75),
        ("rare", 0.85),
    )
    for ped_mode in ped_modes:
        for native_mode in native_modes:
            for base_mode, strengths in base_specs:
                for ped_strength in strengths:
                    for tail_source, tail_lower, tail_upper in tail_specs:
                        for burden_mode in ("max", "mean"):
                            for burden_delta in burden_deltas:
                                for entity_delta in entity_deltas:
                                    for entity_gate_mode in ("weak", "weak_rarity"):
                                        for topic_delta in topic_deltas:
                                            for topic_gate_mode in ("rarity", "weak_rarity"):
                                                for ordinary_cap in ordinary_caps:
                                                    for reading_delta in reading_guard_deltas:
                                                        for (
                                                            tail_floor_mode,
                                                            tail_floor,
                                                        ) in tail_floor_specs:
                                                            params = {
                                                                "p": ped_mode,
                                                                "n": native_mode,
                                                                "b": base_mode,
                                                                "ps": ped_strength,
                                                                "ts": tail_source,
                                                                "tl": tail_lower,
                                                                "tu": tail_upper,
                                                                "bm": burden_mode,
                                                                "bd": burden_delta,
                                                                "ed": entity_delta,
                                                                "eg": entity_gate_mode,
                                                                "td": topic_delta,
                                                                "tg": topic_gate_mode,
                                                                "oc": ordinary_cap,
                                                                "rg": reading_delta,
                                                                "tf": tail_floor,
                                                                "tfm": tail_floor_mode,
                                                            }
                                                            candidates.append(
                                                                SourceArbitrationCandidate(
                                                                    candidate_id=_candidate_id(
                                                                        params
                                                                    ),
                                                                    candidate_family="v2",
                                                                    ped_mode=ped_mode,
                                                                    native_mode=native_mode,
                                                                    base_mode=base_mode,
                                                                    ped_strength=ped_strength,
                                                                    tail_source=tail_source,
                                                                    tail_lower=tail_lower,
                                                                    tail_upper=tail_upper,
                                                                    burden_mode=burden_mode,
                                                                    burden_delta=burden_delta,
                                                                    entity_delta=entity_delta,
                                                                    entity_gate_mode=entity_gate_mode,
                                                                    topic_delta=topic_delta,
                                                                    topic_gate_mode=topic_gate_mode,
                                                                    ordinary_cap=ordinary_cap,
                                                                    ordinary_cap_mode=(
                                                                        "hard"
                                                                        if ordinary_cap > 0.0
                                                                        else "none"
                                                                    ),
                                                                    ordinary_cap_strength=1.0,
                                                                    ordinary_gate_mode="max",
                                                                    reading_guard_delta=reading_delta,
                                                                    tail_floor=tail_floor,
                                                                    tail_floor_mode=tail_floor_mode,
                                                                    same_surface_floor=0.0,
                                                                    same_surface_floor_mode="none",
                                                                    same_surface_source_attenuation=0.0,
                                                                    same_surface_source_attenuation_mode="none",
                                                                )
                                                            )
    return tuple(candidates)


def generate_ordinary_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    cap_specs = (
        ("hard", 1.0),
        ("soft", 0.35),
        ("soft", 0.55),
        ("soft", 0.75),
    )
    for ped_mode in ("min", "mean"):
        for tail_lower, tail_upper in ((0.50, 0.85), (0.55, 0.90), (0.60, 0.90), (0.65, 0.95)):
            for burden_delta in (0.03, 0.05, 0.07, 0.10):
                for ordinary_cap in (0.42, 0.46, 0.50, 0.54, 0.56, 0.58, 0.62, 0.66):
                    for ordinary_gate_mode in (
                        "max",
                        "mean",
                        "frequency",
                        "priority",
                        "freq_priority",
                        "pedagogical",
                    ):
                        for cap_mode, cap_strength in cap_specs:
                            params = {
                                "p": ped_mode,
                                "n": "mean",
                                "b": "ped_native_min",
                                "ps": 1.0,
                                "ts": "base",
                                "tl": tail_lower,
                                "tu": tail_upper,
                                "bm": "mean",
                                "bd": burden_delta,
                                "ed": 0.0,
                                "eg": "weak",
                                "td": 0.0,
                                "tg": "rarity",
                                "oc": ordinary_cap,
                                "ocm": cap_mode,
                                "ocs": cap_strength,
                                "og": ordinary_gate_mode,
                                "rg": 0.0,
                                "tf": 0.0,
                                "tfm": "none",
                            }
                            candidates.append(
                                SourceArbitrationCandidate(
                                    candidate_id=_candidate_id(params),
                                    candidate_family="ordinary_refine",
                                    ped_mode=ped_mode,
                                    native_mode="mean",
                                    base_mode="ped_native_min",
                                    ped_strength=1.0,
                                    tail_source="base",
                                    tail_lower=tail_lower,
                                    tail_upper=tail_upper,
                                    burden_mode="mean",
                                    burden_delta=burden_delta,
                                    entity_delta=0.0,
                                    entity_gate_mode="weak",
                                    topic_delta=0.0,
                                    topic_gate_mode="rarity",
                                    ordinary_cap=ordinary_cap,
                                    ordinary_cap_mode=cap_mode,
                                    ordinary_cap_strength=cap_strength,
                                    ordinary_gate_mode=ordinary_gate_mode,
                                    reading_guard_delta=0.0,
                                    tail_floor=0.0,
                                    tail_floor_mode="none",
                                    same_surface_floor=0.0,
                                    same_surface_floor_mode="none",
                                    same_surface_source_attenuation=0.0,
                                    same_surface_source_attenuation_mode="none",
                                )
                            )
    return tuple(candidates)


def generate_same_surface_alt_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    floor_specs = [("none", 0.0)]
    for mode in ("source_rank_gap", "rare_source_rank_gap"):
        for floor in (0.28, 0.38, 0.50, 0.62, 0.74, 0.84):
            floor_specs.append((mode, floor))
    for tail_lower, tail_upper in ((0.50, 0.85), (0.55, 0.90)):
        for burden_delta in (0.03, 0.05, 0.07):
            for ordinary_cap in (0.54, 0.56, 0.58, 0.62):
                for ordinary_gate_mode in ("mean", "freq_priority"):
                    for same_surface_floor_mode, same_surface_floor in floor_specs:
                        params = {
                            "p": "min",
                            "n": "mean",
                            "b": "ped_native_min",
                            "ps": 1.0,
                            "ts": "base",
                            "tl": tail_lower,
                            "tu": tail_upper,
                            "bm": "mean",
                            "bd": burden_delta,
                            "ed": 0.0,
                            "eg": "weak",
                            "td": 0.0,
                            "tg": "rarity",
                            "oc": ordinary_cap,
                            "ocm": "hard",
                            "ocs": 1.0,
                            "og": ordinary_gate_mode,
                            "rg": 0.0,
                            "tf": 0.0,
                            "tfm": "none",
                            "ssf": same_surface_floor,
                            "ssfm": same_surface_floor_mode,
                        }
                        candidates.append(
                            SourceArbitrationCandidate(
                                candidate_id=_candidate_id(params),
                                candidate_family="same_surface_alt",
                                ped_mode="min",
                                native_mode="mean",
                                base_mode="ped_native_min",
                                ped_strength=1.0,
                                tail_source="base",
                                tail_lower=tail_lower,
                                tail_upper=tail_upper,
                                burden_mode="mean",
                                burden_delta=burden_delta,
                                entity_delta=0.0,
                                entity_gate_mode="weak",
                                topic_delta=0.0,
                                topic_gate_mode="rarity",
                                ordinary_cap=ordinary_cap,
                                ordinary_cap_mode="hard",
                                ordinary_cap_strength=1.0,
                                ordinary_gate_mode=ordinary_gate_mode,
                                reading_guard_delta=0.0,
                                tail_floor=0.0,
                                tail_floor_mode="none",
                                same_surface_floor=same_surface_floor,
                                same_surface_floor_mode=same_surface_floor_mode,
                                same_surface_source_attenuation=0.0,
                                same_surface_source_attenuation_mode="none",
                            )
                        )
    return tuple(candidates)


def generate_same_surface_attenuate_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    attenuation_specs = [("none", 0.0)]
    for mode in (
        "ped_pollution",
        "ped_rare_pollution",
        "native_pollution",
        "native_rare_pollution",
        "all_pollution",
        "all_rare_pollution",
    ):
        for strength in (0.25, 0.50, 0.75, 1.0):
            attenuation_specs.append((mode, strength))
    for tail_lower, tail_upper in ((0.50, 0.85), (0.55, 0.90)):
        for burden_delta in (0.03, 0.05, 0.07):
            for ordinary_cap in (0.54, 0.56, 0.58, 0.62):
                for ordinary_gate_mode in ("mean", "freq_priority"):
                    for attenuation_mode, attenuation_strength in attenuation_specs:
                        params = {
                            "p": "min",
                            "n": "mean",
                            "b": "ped_native_min",
                            "ps": 1.0,
                            "ts": "base",
                            "tl": tail_lower,
                            "tu": tail_upper,
                            "bm": "mean",
                            "bd": burden_delta,
                            "ed": 0.0,
                            "eg": "weak",
                            "td": 0.0,
                            "tg": "rarity",
                            "oc": ordinary_cap,
                            "ocm": "hard",
                            "ocs": 1.0,
                            "og": ordinary_gate_mode,
                            "rg": 0.0,
                            "tf": 0.0,
                            "tfm": "none",
                            "ssf": 0.0,
                            "ssfm": "none",
                            "ssa": attenuation_strength,
                            "ssam": attenuation_mode,
                        }
                        candidates.append(
                            SourceArbitrationCandidate(
                                candidate_id=_candidate_id(params),
                                candidate_family="same_surface_attenuate",
                                ped_mode="min",
                                native_mode="mean",
                                base_mode="ped_native_min",
                                ped_strength=1.0,
                                tail_source="base",
                                tail_lower=tail_lower,
                                tail_upper=tail_upper,
                                burden_mode="mean",
                                burden_delta=burden_delta,
                                entity_delta=0.0,
                                entity_gate_mode="weak",
                                topic_delta=0.0,
                                topic_gate_mode="rarity",
                                ordinary_cap=ordinary_cap,
                                ordinary_cap_mode="hard",
                                ordinary_cap_strength=1.0,
                                ordinary_gate_mode=ordinary_gate_mode,
                                reading_guard_delta=0.0,
                                tail_floor=0.0,
                                tail_floor_mode="none",
                                same_surface_floor=0.0,
                                same_surface_floor_mode="none",
                                same_surface_source_attenuation=attenuation_strength,
                                same_surface_source_attenuation_mode=attenuation_mode,
                            )
                        )
    return tuple(candidates)


def generate_same_surface_combo_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    attenuation_specs = [
        ("none", 0.0),
        ("ped_rare_pollution", 0.25),
        ("ped_rare_pollution", 0.50),
        ("ped_rare_pollution", 0.75),
        ("ped_rare_pollution", 1.0),
        ("native_rare_pollution", 0.25),
        ("native_rare_pollution", 0.50),
        ("native_rare_pollution", 0.75),
        ("native_rare_pollution", 1.0),
        ("all_rare_pollution", 0.25),
        ("all_rare_pollution", 0.50),
        ("all_rare_pollution", 0.75),
        ("ped_pollution", 0.25),
        ("ped_pollution", 0.50),
        ("native_pollution", 0.25),
        ("native_pollution", 0.50),
        ("all_pollution", 0.25),
    ]
    floor_specs = [
        ("none", 0.0),
        ("rare_source_rank_gap", 0.16),
        ("rare_source_rank_gap", 0.22),
        ("rare_source_rank_gap", 0.28),
        ("rare_source_rank_gap", 0.34),
        ("source_rank_gap", 0.16),
        ("source_rank_gap", 0.22),
        ("source_rank_gap", 0.28),
    ]
    for tail_lower, tail_upper in ((0.50, 0.85), (0.55, 0.90)):
        for burden_delta in (0.03, 0.05, 0.07):
            for ordinary_cap in (0.54, 0.56, 0.58, 0.62):
                for ordinary_gate_mode in ("mean", "freq_priority"):
                    for attenuation_mode, attenuation_strength in attenuation_specs:
                        for floor_mode, floor in floor_specs:
                            params = {
                                "p": "min",
                                "n": "mean",
                                "b": "ped_native_min",
                                "ps": 1.0,
                                "ts": "base",
                                "tl": tail_lower,
                                "tu": tail_upper,
                                "bm": "mean",
                                "bd": burden_delta,
                                "ed": 0.0,
                                "eg": "weak",
                                "td": 0.0,
                                "tg": "rarity",
                                "oc": ordinary_cap,
                                "ocm": "hard",
                                "ocs": 1.0,
                                "og": ordinary_gate_mode,
                                "rg": 0.0,
                                "tf": 0.0,
                                "tfm": "none",
                                "ssf": floor,
                                "ssfm": floor_mode,
                                "ssa": attenuation_strength,
                                "ssam": attenuation_mode,
                            }
                            candidates.append(
                                SourceArbitrationCandidate(
                                    candidate_id=_candidate_id(params),
                                    candidate_family="same_surface_combo",
                                    ped_mode="min",
                                    native_mode="mean",
                                    base_mode="ped_native_min",
                                    ped_strength=1.0,
                                    tail_source="base",
                                    tail_lower=tail_lower,
                                    tail_upper=tail_upper,
                                    burden_mode="mean",
                                    burden_delta=burden_delta,
                                    entity_delta=0.0,
                                    entity_gate_mode="weak",
                                    topic_delta=0.0,
                                    topic_gate_mode="rarity",
                                    ordinary_cap=ordinary_cap,
                                    ordinary_cap_mode="hard",
                                    ordinary_cap_strength=1.0,
                                    ordinary_gate_mode=ordinary_gate_mode,
                                    reading_guard_delta=0.0,
                                    tail_floor=0.0,
                                    tail_floor_mode="none",
                                    same_surface_floor=floor,
                                    same_surface_floor_mode=floor_mode,
                                    same_surface_source_attenuation=attenuation_strength,
                                    same_surface_source_attenuation_mode=attenuation_mode,
                                )
                            )
    return tuple(candidates)


def generate_gairaigo_source_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    source_specs = [("none", 0.0)]
    for gate_mode in (
        "marked",
        "marked_rarity",
        "marked_weak_rarity",
        "marked_gloss_guard",
        "marked_soft_gloss_guard",
        "domain",
        "non_english",
        "non_english_or_domain",
    ):
        for delta in (0.03, 0.05, 0.08, 0.12, 0.16):
            source_specs.append((gate_mode, delta))
    ease_specs = [("none", 0.0)]
    for ease_mode in ("english_freq", "english_any"):
        for delta in (0.01, 0.02, 0.04):
            ease_specs.append((ease_mode, delta))
    for source_gate_mode, source_delta in source_specs:
        for english_ease_mode, english_ease_delta in ease_specs:
            params = {
                "p": "min",
                "n": "mean",
                "b": "ped_native_min",
                "ps": 1.0,
                "ts": "base",
                "tl": 0.50,
                "tu": 0.85,
                "bm": "mean",
                "bd": 0.05,
                "ed": 0.0,
                "eg": "weak",
                "td": 0.0,
                "tg": "rarity",
                "oc": 0.58,
                "ocm": "hard",
                "ocs": 1.0,
                "og": "mean",
                "rg": 0.0,
                "tf": 0.0,
                "tfm": "none",
                "ssf": 0.34,
                "ssfm": "rare_source_rank_gap",
                "ssa": 0.0,
                "ssam": "none",
                "gsd": source_delta,
                "gsg": source_gate_mode,
                "ged": english_ease_delta,
                "gem": english_ease_mode,
            }
            candidates.append(
                SourceArbitrationCandidate(
                    candidate_id=_candidate_id(params),
                    candidate_family="gairaigo_source_refine",
                    ped_mode="min",
                    native_mode="mean",
                    base_mode="ped_native_min",
                    ped_strength=1.0,
                    tail_source="base",
                    tail_lower=0.50,
                    tail_upper=0.85,
                    burden_mode="mean",
                    burden_delta=0.05,
                    entity_delta=0.0,
                    entity_gate_mode="weak",
                    topic_delta=0.0,
                    topic_gate_mode="rarity",
                    ordinary_cap=0.58,
                    ordinary_cap_mode="hard",
                    ordinary_cap_strength=1.0,
                    ordinary_gate_mode="mean",
                    reading_guard_delta=0.0,
                    tail_floor=0.0,
                    tail_floor_mode="none",
                    same_surface_floor=0.34,
                    same_surface_floor_mode="rare_source_rank_gap",
                    same_surface_source_attenuation=0.0,
                    same_surface_source_attenuation_mode="none",
                    gairaigo_source_delta=source_delta,
                    gairaigo_source_gate_mode=source_gate_mode,
                    gairaigo_english_ease_delta=english_ease_delta,
                    gairaigo_english_ease_mode=english_ease_mode,
                )
            )
    return tuple(candidates)


def generate_jlpt_guard_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    bound_specs = [("none", 0.0, 1.0)]
    for margin in (0.12, 0.18, 0.25, 0.35):
        bound_specs.append(("upper_hard", margin, 1.0))
        for strength in (0.50, 0.75, 1.0):
            bound_specs.append(("upper_soft", margin, strength))
    for margin in (0.25, 0.35):
        for strength in (0.50, 0.75):
            bound_specs.append(("band_soft", margin, strength))
    for block_jlpt_raise in (False, True):
        for bound_mode, bound_margin, bound_strength in bound_specs:
            params = {
                "p": "min",
                "n": "mean",
                "b": "ped_native_min",
                "ps": 1.0,
                "ts": "base",
                "tl": 0.50,
                "tu": 0.85,
                "bm": "mean",
                "bd": 0.05,
                "ed": 0.0,
                "eg": "weak",
                "td": 0.0,
                "tg": "rarity",
                "oc": 0.58,
                "ocm": "hard",
                "ocs": 1.0,
                "og": "mean",
                "rg": 0.0,
                "tf": 0.0,
                "tfm": "none",
                "ssf": 0.34,
                "ssfm": "rare_source_rank_gap",
                "ssa": 0.0,
                "ssam": "none",
                "gsd": 0.05,
                "gsg": "marked_rarity",
                "ged": 0.04,
                "gem": "english_freq",
                "gjb": int(block_jlpt_raise),
                "jbm": bound_mode,
                "jmar": bound_margin,
                "jbs": bound_strength,
            }
            candidates.append(
                SourceArbitrationCandidate(
                    candidate_id=_candidate_id(params),
                    candidate_family="jlpt_guard_refine",
                    ped_mode="min",
                    native_mode="mean",
                    base_mode="ped_native_min",
                    ped_strength=1.0,
                    tail_source="base",
                    tail_lower=0.50,
                    tail_upper=0.85,
                    burden_mode="mean",
                    burden_delta=0.05,
                    entity_delta=0.0,
                    entity_gate_mode="weak",
                    topic_delta=0.0,
                    topic_gate_mode="rarity",
                    ordinary_cap=0.58,
                    ordinary_cap_mode="hard",
                    ordinary_cap_strength=1.0,
                    ordinary_gate_mode="mean",
                    reading_guard_delta=0.0,
                    tail_floor=0.0,
                    tail_floor_mode="none",
                    same_surface_floor=0.34,
                    same_surface_floor_mode="rare_source_rank_gap",
                    same_surface_source_attenuation=0.0,
                    same_surface_source_attenuation_mode="none",
                    gairaigo_source_delta=0.05,
                    gairaigo_source_gate_mode="marked_rarity",
                    gairaigo_english_ease_delta=0.04,
                    gairaigo_english_ease_mode="english_freq",
                    gairaigo_jlpt_raise_block=block_jlpt_raise,
                    jlpt_bound_mode=bound_mode,
                    jlpt_bound_margin=bound_margin,
                    jlpt_bound_strength=bound_strength,
                )
            )
    return tuple(candidates)


def generate_jlpt_exact_ped_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    floor_specs = [
        ("rare_source_rank_gap", 0.34),
        ("pedagogical_family_only_rare_pollution", 0.22),
        ("pedagogical_family_only_rare_pollution", 0.28),
        ("pedagogical_family_only_rare_pollution", 0.34),
        ("pedagogical_family_only_rare_pollution", 0.42),
        ("pedagogical_family_only_rare_pollution", 0.50),
        ("pedagogical_family_only_rare_pollution", 0.62),
    ]
    for jlpt_ped_mode in ("broad", "exact_preferred"):
        for same_surface_floor_mode, same_surface_floor in floor_specs:
            params = {
                "p": "min",
                "n": "mean",
                "b": "ped_native_min",
                "ps": 1.0,
                "ts": "base",
                "tl": 0.50,
                "tu": 0.85,
                "bm": "mean",
                "bd": 0.05,
                "ed": 0.0,
                "eg": "weak",
                "td": 0.0,
                "tg": "rarity",
                "oc": 0.58,
                "ocm": "hard",
                "ocs": 1.0,
                "og": "mean",
                "rg": 0.0,
                "tf": 0.0,
                "tfm": "none",
                "ssf": same_surface_floor,
                "ssfm": same_surface_floor_mode,
                "ssa": 0.0,
                "ssam": "none",
                "jpm": jlpt_ped_mode,
                "gsd": 0.05,
                "gsg": "marked_rarity",
                "ged": 0.04,
                "gem": "english_freq",
                "gjb": 0,
                "jbm": "none",
                "jmar": 0.0,
                "jbs": 1.0,
            }
            candidates.append(
                SourceArbitrationCandidate(
                    candidate_id=_candidate_id(params),
                    candidate_family="jlpt_exact_ped_refine",
                    ped_mode="min",
                    native_mode="mean",
                    base_mode="ped_native_min",
                    ped_strength=1.0,
                    tail_source="base",
                    tail_lower=0.50,
                    tail_upper=0.85,
                    burden_mode="mean",
                    burden_delta=0.05,
                    entity_delta=0.0,
                    entity_gate_mode="weak",
                    topic_delta=0.0,
                    topic_gate_mode="rarity",
                    ordinary_cap=0.58,
                    ordinary_cap_mode="hard",
                    ordinary_cap_strength=1.0,
                    ordinary_gate_mode="mean",
                    reading_guard_delta=0.0,
                    tail_floor=0.0,
                    tail_floor_mode="none",
                    same_surface_floor=same_surface_floor,
                    same_surface_floor_mode=same_surface_floor_mode,
                    same_surface_source_attenuation=0.0,
                    same_surface_source_attenuation_mode="none",
                    jlpt_ped_mode=jlpt_ped_mode,
                    gairaigo_source_delta=0.05,
                    gairaigo_source_gate_mode="marked_rarity",
                    gairaigo_english_ease_delta=0.04,
                    gairaigo_english_ease_mode="english_freq",
                    gairaigo_jlpt_raise_block=False,
                    jlpt_bound_mode="none",
                    jlpt_bound_margin=0.0,
                    jlpt_bound_strength=1.0,
                )
            )
    return tuple(candidates)


def generate_jlpt_exact_surface_inheritance_sweep_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    exact_specs = [("none", 0.0, 0.0)]
    exact_specs.extend(
        (gate_mode, blend, min_gap)
        for gate_mode in (
            "all_exact_harder",
            "same_surface_alt",
            "same_surface_rare_pollution",
        )
        for blend in (0.25, 0.50, 0.75, 1.0)
        for min_gap in (0.0, 0.08, 0.14, 0.22)
    )
    inherited_specs = [("none", 0.0)]
    inherited_specs.extend(
        (mode, penalty)
        for mode in (
            "family_only",
            "same_surface_family_only",
            "same_surface_rare_pollution_family_only",
        )
        for penalty in (0.04, 0.08, 0.14, 0.22, 0.34)
    )
    old_floor_values = (0.0, 0.24, 0.34, 0.50)
    family_floor_values = (0.0, 0.24, 0.34, 0.42, 0.50, 0.62)
    for exact_gate_mode, exact_blend, exact_min_gap in exact_specs:
        for inherited_mode, inherited_penalty in inherited_specs:
            for old_floor in old_floor_values:
                same_surface_floor_mode = "rare_source_rank_gap" if old_floor > 0.0 else "none"
                for family_floor in family_floor_values:
                    secondary_floor_mode = (
                        "pedagogical_family_only_rare_pollution" if family_floor > 0.0 else "none"
                    )
                    params = {
                        "p": "min",
                        "n": "mean",
                        "b": "ped_native_min",
                        "ps": 1.0,
                        "ts": "base",
                        "tl": 0.50,
                        "tu": 0.85,
                        "bm": "mean",
                        "bd": 0.05,
                        "ed": 0.0,
                        "eg": "weak",
                        "td": 0.0,
                        "tg": "rarity",
                        "oc": 0.58,
                        "ocm": "hard",
                        "ocs": 1.0,
                        "og": "mean",
                        "rg": 0.0,
                        "tf": 0.0,
                        "tfm": "none",
                        "ssf": old_floor,
                        "ssfm": same_surface_floor_mode,
                        "s2f": family_floor,
                        "s2fm": secondary_floor_mode,
                        "ssa": 0.0,
                        "ssam": "none",
                        "jpm": "effective",
                        "jeb": exact_blend,
                        "jeg": exact_gate_mode,
                        "jemg": exact_min_gap,
                        "jip": inherited_penalty,
                        "jipm": inherited_mode,
                        "gsd": 0.05,
                        "gsg": "marked_rarity",
                        "ged": 0.04,
                        "gem": "english_freq",
                        "gjb": 0,
                        "jbm": "none",
                        "jmar": 0.0,
                        "jbs": 1.0,
                    }
                    candidates.append(
                        SourceArbitrationCandidate(
                            candidate_id=_candidate_id(params),
                            candidate_family="jlpt_exact_surface_inheritance_sweep",
                            ped_mode="min",
                            native_mode="mean",
                            base_mode="ped_native_min",
                            ped_strength=1.0,
                            tail_source="base",
                            tail_lower=0.50,
                            tail_upper=0.85,
                            burden_mode="mean",
                            burden_delta=0.05,
                            entity_delta=0.0,
                            entity_gate_mode="weak",
                            topic_delta=0.0,
                            topic_gate_mode="rarity",
                            ordinary_cap=0.58,
                            ordinary_cap_mode="hard",
                            ordinary_cap_strength=1.0,
                            ordinary_gate_mode="mean",
                            reading_guard_delta=0.0,
                            tail_floor=0.0,
                            tail_floor_mode="none",
                            same_surface_floor=old_floor,
                            same_surface_floor_mode=same_surface_floor_mode,
                            same_surface_source_attenuation=0.0,
                            same_surface_source_attenuation_mode="none",
                            jlpt_ped_mode="effective",
                            jlpt_exact_blend=exact_blend,
                            jlpt_exact_blend_gate_mode=exact_gate_mode,
                            jlpt_exact_min_gap=exact_min_gap,
                            jlpt_inherited_penalty=inherited_penalty,
                            jlpt_inherited_penalty_mode=inherited_mode,
                            same_surface_secondary_floor=family_floor,
                            same_surface_secondary_floor_mode=secondary_floor_mode,
                            gairaigo_source_delta=0.05,
                            gairaigo_source_gate_mode="marked_rarity",
                            gairaigo_english_ease_delta=0.04,
                            gairaigo_english_ease_mode="english_freq",
                            gairaigo_jlpt_raise_block=False,
                            jlpt_bound_mode="none",
                            jlpt_bound_margin=0.0,
                            jlpt_bound_strength=1.0,
                        )
                    )
    return tuple(candidates)


def normalized_scores_for_candidate(
    candidate: SourceArbitrationCandidate,
    view: ComponentView,
    *,
    parts: Mapping[str, object],
) -> object:
    raw = raw_scores_for_candidate(candidate, view, parts=parts)
    normalized = _target_curve_normalize(raw, target_positions=view.target_positions)
    return jlpt_bounded_score(candidate, normalized, parts=parts)


def raw_scores_for_candidate(
    candidate: SourceArbitrationCandidate,
    view: ComponentView,
    *,
    parts: Mapping[str, object],
) -> object:
    ped = pedagogical_values_for_candidate(candidate, parts=parts)
    native = parts[f"native_{candidate.native_mode}"]
    ped_conf = parts["ped_conf"]
    native_conf = parts["native_conf"]
    ped, native = attenuated_same_surface_source_values(
        candidate,
        ped=ped,
        native=native,
        parts=parts,
    )
    base = base_spine(
        candidate,
        ped=ped,
        native=native,
        ped_conf=ped_conf,
        native_conf=native_conf,
    )
    tail_signal = base if candidate.tail_source == "base" else view.frequency
    tail_gate = _ramp(tail_signal, lower=candidate.tail_lower, upper=candidate.tail_upper)
    burden = parts[f"burden_{candidate.burden_mode}"]
    raw = base + (float(candidate.burden_delta) * tail_gate * np.nan_to_num(burden, nan=0.0))
    raw += entity_adjustment(candidate, parts=parts, frequency=view.frequency)
    raw += topic_adjustment(candidate, parts=parts, frequency=view.frequency)
    raw = ordinary_protected_score(candidate, raw, parts=parts)
    raw += gairaigo_source_adjustment(candidate, parts=parts, frequency=view.frequency)
    raw = same_surface_alt_reading_floor_score(candidate, raw, parts=parts)
    raw += reading_guard_adjustment(candidate, parts=parts, frequency=view.frequency)
    raw = tail_floor_score(candidate, raw, parts=parts)
    return np.clip(np.nan_to_num(raw, nan=0.0), 0.0, 1.0).astype(np.float32)


def pedagogical_values_for_candidate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.jlpt_ped_mode == "broad":
        return parts[f"ped_{candidate.ped_mode}"]
    if candidate.jlpt_ped_mode == "exact_preferred":
        return parts[f"ped_exact_preferred_{candidate.ped_mode}"]
    if candidate.jlpt_ped_mode == "effective":
        jlpt = jlpt_values_for_candidate(candidate, parts=parts)
        return _nan_reduce(
            (jlpt, parts["lesson_vocab_difficulty"]),
            mode=candidate.ped_mode,
            fallback=np.nan,
        )
    raise ValueError(f"Unsupported JLPT pedagogical mode: {candidate.jlpt_ped_mode}")


def jlpt_values_for_candidate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    broad = np.asarray(parts["jlpt_vocab_difficulty"], dtype=np.float32)
    effective = broad.copy()
    if candidate.jlpt_exact_blend > 0.0 and candidate.jlpt_exact_blend_gate_mode != "none":
        exact = np.asarray(parts["jlpt_vocab_exact_difficulty"], dtype=np.float32)
        gap = exact - broad
        finite = (
            np.isfinite(broad)
            & np.isfinite(exact)
            & (np.asarray(parts["jlpt_vocab_exact_known"], dtype=np.float32) > 0.0)
            & (gap > 0.0)
            & (gap >= float(candidate.jlpt_exact_min_gap))
        )
        gate = _jlpt_exact_blend_gate(candidate, parts=parts)
        adjustment = float(candidate.jlpt_exact_blend) * np.maximum(gap, 0.0) * gate
        effective = np.where(finite, broad + adjustment, effective).astype(np.float32)
    if candidate.jlpt_inherited_penalty > 0.0 and candidate.jlpt_inherited_penalty_mode != "none":
        gate = _jlpt_inherited_penalty_gate(candidate, parts=parts)
        penalty = float(candidate.jlpt_inherited_penalty) * np.clip(gate, 0.0, 1.0)
        effective = np.where(
            np.isfinite(effective),
            np.minimum(1.0, effective + penalty),
            effective,
        ).astype(np.float32)
    return effective


def _jlpt_exact_blend_gate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    mode = candidate.jlpt_exact_blend_gate_mode
    if mode == "all_exact_harder":
        return np.ones_like(np.asarray(parts["jlpt_vocab_difficulty"], dtype=np.float32))
    if mode == "same_surface_alt":
        return (np.asarray(parts["same_surface_alt_count"], dtype=np.float32) > 0.0).astype(
            np.float32
        )
    if mode == "same_surface_rare_pollution":
        return np.asarray(parts["same_surface_rare_pollution_risk"], dtype=np.float32)
    raise ValueError(f"Unsupported JLPT exact blend gate mode: {mode}")


def _jlpt_inherited_penalty_gate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    family_only = np.asarray(parts["jlpt_vocab_family_only_known"], dtype=np.float32)
    mode = candidate.jlpt_inherited_penalty_mode
    if mode == "family_only":
        return family_only
    if mode == "same_surface_family_only":
        return family_only * (
            np.asarray(parts["same_surface_alt_count"], dtype=np.float32) > 0.0
        ).astype(np.float32)
    if mode == "same_surface_rare_pollution_family_only":
        return family_only * np.asarray(
            parts["same_surface_rare_pollution_risk"],
            dtype=np.float32,
        )
    raise ValueError(f"Unsupported JLPT inherited penalty mode: {mode}")


def attenuated_same_surface_source_values(
    candidate: SourceArbitrationCandidate,
    *,
    ped: object,
    native: object,
    parts: Mapping[str, object],
) -> tuple[object, object]:
    if (
        candidate.same_surface_source_attenuation <= 0.0
        or candidate.same_surface_source_attenuation_mode == "none"
    ):
        return ped, native
    mode_specs = {
        "ped_pollution": ("ped", "same_surface_pollution_risk"),
        "ped_rare_pollution": ("ped", "same_surface_rare_pollution_risk"),
        "native_pollution": ("native", "same_surface_pollution_risk"),
        "native_rare_pollution": ("native", "same_surface_rare_pollution_risk"),
        "all_pollution": ("all", "same_surface_pollution_risk"),
        "all_rare_pollution": ("all", "same_surface_rare_pollution_risk"),
    }
    spec = mode_specs.get(candidate.same_surface_source_attenuation_mode)
    if spec is None:
        raise ValueError(
            "Unsupported same-surface source attenuation mode: "
            f"{candidate.same_surface_source_attenuation_mode}"
        )
    target, risk_key = spec
    strength = np.clip(
        np.asarray(parts[risk_key], dtype=np.float32)
        * float(candidate.same_surface_source_attenuation),
        0.0,
        1.0,
    )
    ped_values = _attenuate_difficulty_values(ped, strength) if target in {"ped", "all"} else ped
    native_values = (
        _attenuate_difficulty_values(native, strength) if target in {"native", "all"} else native
    )
    return ped_values, native_values


def _attenuate_difficulty_values(values: object, strength: object) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    attenuation = np.asarray(strength, dtype=np.float32)
    adjusted = parsed * (1.0 - attenuation) + attenuation
    return np.where(np.isfinite(parsed), adjusted, parsed).astype(np.float32)


def family_parts(view: ComponentView) -> dict[str, object]:
    frequency = np.nan_to_num(view.frequency, nan=0.0).astype(np.float32)
    jlpt = view.value("jlpt_vocab_difficulty")
    jlpt_exact = view.value("jlpt_vocab_exact_difficulty", fill=np.nan)
    jlpt_exact_known_for_ped = view.value("jlpt_vocab_exact_known", fill=0.0)
    jlpt_exact_preferred = np.where(
        (np.asarray(jlpt_exact_known_for_ped, dtype=np.float32) > 0.0)
        & np.isfinite(np.asarray(jlpt_exact, dtype=np.float32)),
        np.asarray(jlpt_exact, dtype=np.float32),
        np.asarray(jlpt, dtype=np.float32),
    ).astype(np.float32)
    lesson = view.value("lesson_vocab_difficulty")
    jlpt_known = view.value("jlpt_vocab_known", fill=0.0)
    lesson_known = view.value("lesson_vocab_known", fill=0.0)
    tubelex = view.value("tubelex_frequency")
    jmdict_priority = view.value("jmdict_priority")
    ped_min = _nan_reduce((jlpt, lesson), mode="min", fallback=np.nan)
    ped_mean = _nan_reduce((jlpt, lesson), mode="mean", fallback=np.nan)
    ped_exact_preferred_min = _nan_reduce(
        (jlpt_exact_preferred, lesson),
        mode="min",
        fallback=np.nan,
    )
    ped_exact_preferred_mean = _nan_reduce(
        (jlpt_exact_preferred, lesson),
        mode="mean",
        fallback=np.nan,
    )
    native_mean = _nan_reduce((frequency, tubelex, jmdict_priority), mode="mean", fallback=0.0)
    native_min = _nan_reduce((frequency, tubelex, jmdict_priority), mode="min", fallback=0.0)
    ped_conf = _nan_reduce(
        (
            jlpt_known,
            lesson_known,
        ),
        mode="max",
        fallback=0.0,
    )
    native_conf = _nan_reduce(
        (
            view.value("frequency_source_known", fill=0.0),
            view.value("jmdict_priority_known", fill=0.0),
            view.value("tubelex_frequency_known", fill=0.0),
        ),
        mode="max",
        fallback=0.0,
    )
    ordinary_protection = view.value("ordinary_vocab_protection", fill=np.nan)
    frequency_ease = view.value("frequency_ease", fill=np.nan)
    jmdict_priority_commonness = 1.0 - np.nan_to_num(jmdict_priority, nan=1.0)
    ped_ease = 1.0 - np.nan_to_num(ped_min, nan=1.0)
    pedagogical_ease = _nan_reduce(
        (
            ped_ease,
            view.value("jlpt_vocab_beginner_core", fill=np.nan),
            view.value("lesson_vocab_beginner_core", fill=np.nan),
        ),
        mode="max",
        fallback=0.0,
    )
    ordinary_protection = _nan_reduce(
        (ordinary_protection, frequency_ease, jmdict_priority_commonness),
        mode="max",
        fallback=0.0,
    )
    ordinary_mean = _nan_reduce(
        (
            ordinary_protection,
            frequency_ease,
            jmdict_priority_commonness,
            pedagogical_ease,
        ),
        mode="mean",
        fallback=0.0,
    )
    ordinary_freq_priority = _nan_reduce(
        (frequency_ease, jmdict_priority_commonness),
        mode="mean",
        fallback=0.0,
    )
    weak_ordinary = np.clip(1.0 - ordinary_protection, 0.0, 1.0).astype(np.float32)
    orthographic = _nan_reduce(
        (
            view.value("kanji_burden"),
            view.value("max_written_form_burden"),
            view.value("kanji_curriculum_missing_risk"),
            view.value("non_standard_reading_risk"),
            view.value("rare_non_standard_reading_risk"),
            view.value("rare_wago_obscure_written_risk"),
            view.value("written_wago_tail_risk"),
        ),
        mode="max",
        fallback=0.0,
    )
    lexical = _nan_reduce(
        (
            view.value("jmdict_ambiguity_score"),
            view.value("jmdict_reading_complexity_score"),
            view.value("jmdict_restriction_complexity_score"),
            view.value("common_jmdict_ambiguity_score"),
            view.value("common_reading_complexity_score"),
            view.value("common_restriction_complexity_score"),
        ),
        mode="max",
        fallback=0.0,
    )
    burden_max = _nan_reduce((orthographic, lexical), mode="max", fallback=0.0)
    burden_mean = _nan_reduce((orthographic, lexical), mode="mean", fallback=0.0)
    reading_risk = _nan_reduce(
        (
            view.value("jmdict_reading_form_marked_risk"),
            view.value("jmdict_reading_form_marked_flag"),
            view.value("jmdict_reading_restricted_risk"),
            view.value("jmdict_reading_restricted_flag"),
            view.value("non_standard_reading_risk"),
            view.value("rare_non_standard_reading_risk"),
            view.value("rare_wago_non_standard_reading_risk"),
            view.value("kanjidic_nanori_reading_risk"),
            view.value("kanjidic_nanori_reading_count_score"),
        ),
        mode="max",
        fallback=0.0,
    )
    reading_form_source_strength = _nan_reduce(
        tuple(view.value(name) for name in READING_FORM_SOURCE_SIGNALS),
        mode="max",
        fallback=0.0,
    )
    rare_reading_form_strength = _nan_reduce(
        tuple(view.value(name) for name in RARE_READING_FORM_SIGNALS),
        mode="max",
        fallback=0.0,
    )
    reading_inheritance_risk = np.asarray(reading_risk, dtype=np.float32) * np.asarray(
        ordinary_protection, dtype=np.float32
    )
    same_surface_parts = same_surface_alternate_reading_parts(
        view,
        source_strength=reading_form_source_strength,
        rare_strength=rare_reading_form_strength,
        sibling_commonness=ordinary_mean,
    )
    jlpt_surface_known = view.value("jlpt_vocab_surface_known", fill=0.0)
    jlpt_exact_signal_available = 1.0 if "jlpt_vocab_exact_known" in view.name_to_index else 0.0
    jlpt_family_only_known = (
        np.asarray(jlpt_surface_known, dtype=np.float32)
        * np.clip(1.0 - np.asarray(jlpt_exact_known_for_ped, dtype=np.float32), 0.0, 1.0)
        * jlpt_exact_signal_available
    ).astype(np.float32)
    pedagogical_family_only_known = np.maximum(
        jlpt_family_only_known,
        view.value("lesson_vocab_known", fill=0.0),
    ).astype(np.float32)
    same_surface_pedagogical_family_only_risk = (
        np.asarray(same_surface_parts["same_surface_rare_pollution_risk"], dtype=np.float32)
        * pedagogical_family_only_known
    ).astype(np.float32)
    tail_floor_guard = _nan_reduce(
        (
            view.value("frequency_unranked_rare_risk"),
            view.value("frequency_unranked_tail80_risk"),
            view.value("frequency_unranked_tail90_risk"),
            view.value("rare_wago_tail_risk"),
            view.value("rare_wago_obscure_written_risk"),
            view.value("rare_wago_missing_curriculum_shape_risk"),
            view.value("rare_wago_marked_usage_risk"),
            view.value("written_wago_tail_risk"),
            view.value("jmdict_marked_usage_risk"),
        ),
        mode="max",
        fallback=0.0,
    )
    raw_entity = _nan_reduce(
        (
            view.value("named_entity_overlap"),
            view.value("jmnedict_name_overlap"),
            view.value("proper_place_entity_overlap"),
            view.value("proper_country_entity_overlap"),
            view.value("proper_org_entity_overlap"),
            view.value("proper_noun_pos_flag"),
            view.value("problem_class_proper_flag"),
            view.value("wtype_proper_flag"),
            view.value("proper_acronym_entity_risk"),
        ),
        mode="max",
        fallback=0.0,
    )
    topic_raw = _nan_reduce(
        (
            view.value("jmdict_news_or_policy_field_flag"),
            view.value("jmdict_field_marked_flag"),
            view.value("jmdict_dialect_flag"),
            view.value("jmdict_register_marked_flag"),
            view.value("jmdict_abbreviation_flag"),
            view.value("jmdict_organization_misc_flag"),
            view.value("acronym_topic_only_risk"),
            view.value("acronym_default_suppress_risk"),
        ),
        mode="max",
        fallback=0.0,
    )
    gairaigo = view.value("wtype_gairaigo_risk", fill=0.0)
    gairaigo_non_english = view.value("gairaigo_non_english_source_risk", fill=0.0)
    gairaigo_domain = view.value("gairaigo_domain_source_risk", fill=0.0)
    gairaigo_marked = view.value("gairaigo_marked_source_risk", fill=0.0)
    gairaigo_english_ease = view.value("gairaigo_english_source_ease", fill=0.0)
    jlpt_exact_known = view.value("jlpt_vocab_exact_known", fill=np.nan)
    jlpt_exact_known = np.nan_to_num(jlpt_exact_known, nan=jlpt_known).astype(np.float32)
    jlpt_difficulty = view.value("jlpt_vocab_difficulty", fill=np.nan)
    jlpt_exact_difficulty = view.value("jlpt_vocab_exact_difficulty", fill=np.nan)
    gairaigo_english_gloss_ease = view.value(
        "gairaigo_english_gloss_frequency_ease",
        fill=0.0,
    )
    gairaigo_english_freq_ease = _nan_reduce(
        (
            view.value("gairaigo_english_source_ease", fill=np.nan),
            view.value("jmdict_english_source_frequency_ease", fill=np.nan),
        ),
        mode="min",
        fallback=0.0,
    )
    gairaigo_non_english_or_domain = np.maximum(
        np.asarray(gairaigo_non_english, dtype=np.float32),
        np.asarray(gairaigo_domain, dtype=np.float32),
    ).astype(np.float32)
    gairaigo_rarity_gate = _ramp(frequency, lower=0.35, upper=0.75)
    gairaigo_weak_rarity_gate = np.maximum(
        gairaigo_rarity_gate,
        np.asarray(weak_ordinary, dtype=np.float32),
    ).astype(np.float32)
    gloss_guard = np.clip(
        1.0 - np.asarray(gairaigo_english_gloss_ease, dtype=np.float32),
        0.0,
        1.0,
    )
    soft_gloss_guard = np.clip(
        1.0 - (0.50 * np.asarray(gairaigo_english_gloss_ease, dtype=np.float32)),
        0.0,
        1.0,
    )
    any_english_ease = np.maximum(
        np.asarray(gairaigo_english_ease, dtype=np.float32),
        np.asarray(gairaigo_english_gloss_ease, dtype=np.float32),
    ).astype(np.float32)
    return {
        "ped_min": ped_min,
        "ped_mean": ped_mean,
        "ped_exact_preferred_min": ped_exact_preferred_min,
        "ped_exact_preferred_mean": ped_exact_preferred_mean,
        "lesson_vocab_difficulty": lesson,
        "lesson_vocab_known": lesson_known,
        "native_frequency": frequency,
        "native_mean": native_mean,
        "native_min": native_min,
        "ped_conf": ped_conf,
        "native_conf": native_conf,
        "ordinary_protection": ordinary_protection,
        "ordinary_gate_max": ordinary_protection,
        "ordinary_gate_mean": ordinary_mean,
        "ordinary_gate_frequency": np.nan_to_num(frequency_ease, nan=0.0).astype(np.float32),
        "ordinary_gate_priority": jmdict_priority_commonness.astype(np.float32),
        "ordinary_gate_freq_priority": ordinary_freq_priority,
        "ordinary_gate_pedagogical": pedagogical_ease,
        "weak_ordinary": weak_ordinary,
        "burden_max": burden_max,
        "burden_mean": burden_mean,
        "reading_inheritance_risk": reading_inheritance_risk,
        "reading_form_source_strength": reading_form_source_strength,
        "rare_reading_form_strength": rare_reading_form_strength,
        **same_surface_parts,
        "tail_floor_guard": tail_floor_guard,
        "raw_entity": raw_entity,
        "topic_raw": topic_raw,
        "candidate_deprioritized": view.value("candidate_deprioritized_vocab_risk", fill=0.0),
        "jlpt_vocab_known": jlpt_known,
        "jlpt_vocab_surface_known": jlpt_surface_known,
        "jlpt_vocab_exact_known": jlpt_exact_known,
        "jlpt_vocab_family_only_known": jlpt_family_only_known,
        "pedagogical_family_only_known": pedagogical_family_only_known,
        "jlpt_vocab_difficulty": jlpt_difficulty,
        "jlpt_vocab_exact_difficulty": jlpt_exact_difficulty,
        "jlpt_vocab_exact_gap": (
            np.nan_to_num(jlpt_exact_difficulty - jlpt_difficulty, nan=0.0)
        ).astype(np.float32),
        "same_surface_pedagogical_family_only_risk": (same_surface_pedagogical_family_only_risk),
        "gairaigo_source_marked": gairaigo_marked,
        "gairaigo_source_marked_rarity": (
            np.asarray(gairaigo_marked, dtype=np.float32) * gairaigo_rarity_gate
        ).astype(np.float32),
        "gairaigo_source_marked_weak_rarity": (
            np.asarray(gairaigo_marked, dtype=np.float32) * gairaigo_weak_rarity_gate
        ).astype(np.float32),
        "gairaigo_source_marked_gloss_guard": (
            np.asarray(gairaigo_marked, dtype=np.float32) * gairaigo_rarity_gate * gloss_guard
        ).astype(np.float32),
        "gairaigo_source_marked_soft_gloss_guard": (
            np.asarray(gairaigo_marked, dtype=np.float32) * gairaigo_rarity_gate * soft_gloss_guard
        ).astype(np.float32),
        "gairaigo_source_domain": gairaigo_domain,
        "gairaigo_source_non_english": gairaigo_non_english,
        "gairaigo_source_non_english_or_domain": gairaigo_non_english_or_domain,
        "gairaigo_english_source_ease": gairaigo_english_ease,
        "gairaigo_english_any_ease": any_english_ease,
        "gairaigo_english_gloss_frequency_ease": gairaigo_english_gloss_ease,
        "gairaigo_english_source_frequency_ease": (
            np.asarray(gairaigo, dtype=np.float32)
            * np.asarray(gairaigo_english_freq_ease, dtype=np.float32)
        ).astype(np.float32),
    }


def same_surface_alternate_reading_parts(
    view: ComponentView,
    *,
    source_strength: object,
    rare_strength: object,
    sibling_commonness: object,
) -> dict[str, object]:
    count = len(view.frequency)
    alt_count = np.zeros(count, dtype=np.float32)
    rank_disadvantage = np.zeros(count, dtype=np.float32)
    unranked_vs_ranked = np.zeros(count, dtype=np.float32)
    sibling_common_gate = np.zeros(count, dtype=np.float32)

    groups: dict[str, list[int]] = {}
    for index, lemma in enumerate(view.lemmas):
        groups.setdefault(str(lemma), []).append(index)

    readings = [str(value) for value in view.readings]
    ranks = np.asarray(view.core_ranks, dtype=np.float32)
    sibling_common_values = np.nan_to_num(np.asarray(sibling_commonness, dtype=np.float32), nan=0.0)
    states = [str(value) for value in view.candidate_states]
    for group in groups.values():
        if len(group) <= 1:
            continue
        for index in group:
            siblings = [
                sibling
                for sibling in group
                if sibling != index and readings[sibling] != readings[index]
            ]
            if not siblings:
                continue
            alt_count[index] = float(len({readings[sibling] for sibling in siblings}))
            finite_sibling_ranks = [
                float(ranks[sibling]) for sibling in siblings if np.isfinite(ranks[sibling])
            ]
            best_sibling_rank = min(finite_sibling_ranks) if finite_sibling_ranks else None
            if best_sibling_rank is not None:
                current_rank = float(ranks[index]) if np.isfinite(ranks[index]) else None
                if current_rank is None:
                    unranked_vs_ranked[index] = 1.0
                    rank_disadvantage[index] = 1.0
                elif current_rank > best_sibling_rank:
                    ratio = max(1.0, current_rank / max(best_sibling_rank, 1.0))
                    rank_disadvantage[index] = min(1.0, float(np.log(ratio) / np.log(8.0)))
            best_sibling_commonness = max(
                float(sibling_common_values[sibling]) for sibling in siblings
            )
            rank_commonness = (
                1.0 if best_sibling_rank is not None and best_sibling_rank <= 8000.0 else 0.0
            )
            sibling_common_gate[index] = max(best_sibling_commonness, rank_commonness)

    normal_vocab = np.asarray(
        [1.0 if state == "normal_vocab" else 0.0 for state in states],
        dtype=np.float32,
    )
    source_gate = _ramp(source_strength, lower=0.45, upper=0.80)
    rank_gate = np.maximum(
        unranked_vs_ranked,
        _ramp(rank_disadvantage, lower=0.20, upper=0.80),
    )
    common_gate = _ramp(sibling_common_gate, lower=0.20, upper=0.65)
    alt_gate = (alt_count > 0.0).astype(np.float32)
    source_rank_gap_risk = (normal_vocab * alt_gate * source_gate * rank_gate * common_gate).astype(
        np.float32
    )
    rare_gate = np.maximum(unranked_vs_ranked, _ramp(rare_strength, lower=0.20, upper=0.50))
    rare_source_rank_gap_risk = (source_rank_gap_risk * rare_gate).astype(np.float32)
    exact_commonness = same_surface_exact_commonness(view)
    exact_weakness = _ramp(1.0 - exact_commonness, lower=0.25, upper=0.75)
    pollution_risk = (source_rank_gap_risk * exact_weakness).astype(np.float32)
    rare_pollution_risk = (rare_source_rank_gap_risk * exact_weakness).astype(np.float32)
    return {
        "same_surface_alt_count": alt_count,
        "same_surface_rank_disadvantage": rank_disadvantage,
        "same_surface_unranked_vs_ranked": unranked_vs_ranked,
        "same_surface_sibling_common_gate": sibling_common_gate,
        "same_surface_exact_commonness": exact_commonness,
        "same_surface_exact_weakness": exact_weakness,
        "same_surface_source_rank_gap_risk": source_rank_gap_risk,
        "same_surface_rare_source_rank_gap_risk": rare_source_rank_gap_risk,
        "same_surface_pollution_risk": pollution_risk,
        "same_surface_rare_pollution_risk": rare_pollution_risk,
    }


def same_surface_exact_commonness(view: ComponentView) -> object:
    frequency_ease = np.clip(1.0 - np.asarray(view.frequency, dtype=np.float32), 0.0, 1.0)
    ranks = np.asarray(view.core_ranks, dtype=np.float32)
    finite = np.isfinite(ranks)
    rank_ease = np.zeros(len(frequency_ease), dtype=np.float32)
    rank_ease[finite] = 1.0 - _ramp(ranks[finite], lower=1000.0, upper=12000.0)
    return np.maximum(frequency_ease, rank_ease).astype(np.float32)


def base_spine(
    candidate: SourceArbitrationCandidate,
    *,
    ped: object,
    native: object,
    ped_conf: object,
    native_conf: object,
) -> object:
    native_values = np.nan_to_num(native, nan=0.0).astype(np.float32)
    ped_values = np.asarray(ped, dtype=np.float32)
    ped_known = np.asarray(ped_conf, dtype=np.float32) > 0.0
    if candidate.base_mode == "native":
        return native_values
    if candidate.base_mode == "ped_override":
        return np.where(ped_known, np.nan_to_num(ped_values, nan=0.0), native_values)
    if candidate.base_mode == "ped_native_min":
        ped_safe = np.nan_to_num(ped_values, nan=1.0)
        return np.where(ped_known, np.minimum(ped_safe, native_values), native_values)
    if candidate.base_mode == "weighted":
        ped_weight = np.asarray(ped_conf, dtype=np.float32) * float(candidate.ped_strength)
        native_weight = np.asarray(native_conf, dtype=np.float32)
        denominator = ped_weight + native_weight
        numerator = np.nan_to_num(ped_values, nan=0.0) * ped_weight + native_values * native_weight
        return np.divide(numerator, denominator, out=native_values.copy(), where=denominator > 0.0)
    raise ValueError(f"Unsupported base mode: {candidate.base_mode}")


def entity_adjustment(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
    frequency: object,
) -> object:
    if candidate.entity_delta <= 0.0:
        return np.zeros_like(np.asarray(frequency, dtype=np.float32))
    weak = np.asarray(parts["weak_ordinary"], dtype=np.float32)
    deprioritized = np.asarray(parts["candidate_deprioritized"], dtype=np.float32)
    gate = np.maximum(weak, deprioritized)
    if candidate.entity_gate_mode == "weak_rarity":
        gate = gate * _ramp(frequency, lower=0.65, upper=0.95)
    raw_entity = np.asarray(parts["raw_entity"], dtype=np.float32)
    return float(candidate.entity_delta) * raw_entity * gate


def topic_adjustment(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
    frequency: object,
) -> object:
    if candidate.topic_delta <= 0.0:
        return np.zeros_like(np.asarray(frequency, dtype=np.float32))
    rarity = _ramp(frequency, lower=0.55, upper=0.90)
    if candidate.topic_gate_mode == "weak_rarity":
        gate = np.maximum(rarity, np.asarray(parts["weak_ordinary"], dtype=np.float32))
    else:
        gate = rarity
    return float(candidate.topic_delta) * np.asarray(parts["topic_raw"], dtype=np.float32) * gate


def gairaigo_source_adjustment(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
    frequency: object,
) -> object:
    adjustment = np.zeros_like(np.asarray(frequency, dtype=np.float32))
    if candidate.gairaigo_source_delta > 0.0:
        risk_key_by_mode = {
            "marked": "gairaigo_source_marked",
            "marked_rarity": "gairaigo_source_marked_rarity",
            "marked_weak_rarity": "gairaigo_source_marked_weak_rarity",
            "marked_gloss_guard": "gairaigo_source_marked_gloss_guard",
            "marked_soft_gloss_guard": "gairaigo_source_marked_soft_gloss_guard",
            "domain": "gairaigo_source_domain",
            "non_english": "gairaigo_source_non_english",
            "non_english_or_domain": "gairaigo_source_non_english_or_domain",
        }
        if candidate.gairaigo_source_gate_mode != "none":
            risk_key = risk_key_by_mode.get(candidate.gairaigo_source_gate_mode)
            if risk_key is None:
                raise ValueError(
                    f"Unsupported gairaigo source gate mode: {candidate.gairaigo_source_gate_mode}"
                )
            source_gate = np.asarray(parts[risk_key], dtype=np.float32)
            if candidate.gairaigo_jlpt_raise_block:
                source_gate = source_gate * np.clip(
                    1.0 - np.asarray(parts["jlpt_vocab_exact_known"], dtype=np.float32),
                    0.0,
                    1.0,
                )
            adjustment += float(candidate.gairaigo_source_delta) * source_gate
    if candidate.gairaigo_english_ease_delta > 0.0:
        ease_key_by_mode = {
            "english_any": "gairaigo_english_any_ease",
            "english_freq": "gairaigo_english_source_frequency_ease",
        }
        if candidate.gairaigo_english_ease_mode != "none":
            ease_key = ease_key_by_mode.get(candidate.gairaigo_english_ease_mode)
            if ease_key is None:
                raise ValueError(
                    "Unsupported gairaigo English ease mode: "
                    f"{candidate.gairaigo_english_ease_mode}"
                )
            adjustment -= float(candidate.gairaigo_english_ease_delta) * np.asarray(
                parts[ease_key], dtype=np.float32
            )
    return adjustment.astype(np.float32)


def jlpt_bounded_score(
    candidate: SourceArbitrationCandidate,
    scores: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.jlpt_bound_mode == "none":
        return scores
    values = np.asarray(scores, dtype=np.float32)
    known = np.asarray(parts["jlpt_vocab_exact_known"], dtype=np.float32) > 0.5
    if not known.any():
        return values
    anchor = np.asarray(parts["jlpt_vocab_exact_difficulty"], dtype=np.float32)
    valid = known & np.isfinite(anchor)
    if not valid.any():
        return values
    margin = float(candidate.jlpt_bound_margin)
    strength = float(candidate.jlpt_bound_strength)
    lower = np.clip(anchor - margin, 0.0, 1.0)
    upper = np.clip(anchor + margin, 0.0, 1.0)
    adjusted = values.copy()
    if candidate.jlpt_bound_mode == "upper_hard":
        adjusted[valid] = np.minimum(adjusted[valid], upper[valid])
    elif candidate.jlpt_bound_mode == "upper_soft":
        over = np.maximum(adjusted[valid] - upper[valid], 0.0)
        adjusted[valid] = adjusted[valid] - (strength * over)
    elif candidate.jlpt_bound_mode == "band_soft":
        over = np.maximum(adjusted[valid] - upper[valid], 0.0)
        under = np.maximum(lower[valid] - adjusted[valid], 0.0)
        adjusted[valid] = adjusted[valid] - (strength * over) + (strength * under)
    else:
        raise ValueError(f"Unsupported JLPT bound mode: {candidate.jlpt_bound_mode}")
    return np.clip(adjusted, 0.0, 1.0).astype(np.float32)


def ordinary_protected_score(
    candidate: SourceArbitrationCandidate,
    raw: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.ordinary_cap <= 0.0 or candidate.ordinary_cap_mode == "none":
        return raw
    gate_key = f"ordinary_gate_{candidate.ordinary_gate_mode}"
    if gate_key not in parts:
        raise ValueError(f"Unsupported ordinary gate mode: {candidate.ordinary_gate_mode}")
    ordinary = np.asarray(parts[gate_key], dtype=np.float32)
    reading = np.asarray(parts["reading_inheritance_risk"], dtype=np.float32)
    tail = np.asarray(parts["tail_floor_guard"], dtype=np.float32)
    exception = np.maximum(reading, tail)
    gate = ordinary * np.clip(1.0 - exception, 0.0, 1.0)
    cap = float(candidate.ordinary_cap) + (1.0 - float(candidate.ordinary_cap)) * (1.0 - gate)
    raw_values = np.asarray(raw, dtype=np.float32)
    if candidate.ordinary_cap_mode == "hard":
        return np.minimum(raw_values, cap).astype(np.float32)
    if candidate.ordinary_cap_mode == "soft":
        over_cap = np.maximum(raw_values - cap, 0.0)
        strength = float(candidate.ordinary_cap_strength)
        return (raw_values - (strength * over_cap)).astype(np.float32)
    raise ValueError(f"Unsupported ordinary cap mode: {candidate.ordinary_cap_mode}")


def same_surface_alt_reading_floor_score(
    candidate: SourceArbitrationCandidate,
    raw: object,
    *,
    parts: Mapping[str, object],
) -> object:
    adjusted = np.asarray(raw, dtype=np.float32)
    if candidate.same_surface_floor > 0.0 and candidate.same_surface_floor_mode != "none":
        adjusted = _same_surface_floor_score(
            adjusted,
            floor=candidate.same_surface_floor,
            mode=candidate.same_surface_floor_mode,
            parts=parts,
        )
    if (
        candidate.same_surface_secondary_floor > 0.0
        and candidate.same_surface_secondary_floor_mode != "none"
    ):
        adjusted = _same_surface_floor_score(
            adjusted,
            floor=candidate.same_surface_secondary_floor,
            mode=candidate.same_surface_secondary_floor_mode,
            parts=parts,
        )
    return adjusted.astype(np.float32)


def _same_surface_floor_score(
    raw: object,
    *,
    floor: float,
    mode: str,
    parts: Mapping[str, object],
) -> object:
    risk_key_by_mode = {
        "source_rank_gap": "same_surface_source_rank_gap_risk",
        "rare_source_rank_gap": "same_surface_rare_source_rank_gap_risk",
        "pedagogical_family_only_rare_pollution": ("same_surface_pedagogical_family_only_risk"),
    }
    risk_key = risk_key_by_mode.get(mode)
    if risk_key is None:
        raise ValueError(f"Unsupported same-surface floor mode: {mode}")
    risk = np.asarray(parts[risk_key], dtype=np.float32)
    floor_values = float(floor) * np.clip(risk, 0.0, 1.0)
    return np.maximum(np.asarray(raw, dtype=np.float32), floor_values).astype(np.float32)


def reading_guard_adjustment(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
    frequency: object,
) -> object:
    if candidate.reading_guard_delta <= 0.0:
        return np.zeros_like(np.asarray(frequency, dtype=np.float32))
    reading = np.asarray(parts["reading_inheritance_risk"], dtype=np.float32)
    return float(candidate.reading_guard_delta) * reading


def tail_floor_score(
    candidate: SourceArbitrationCandidate,
    raw: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.tail_floor <= 0.0 or candidate.tail_floor_mode == "none":
        return raw
    if candidate.tail_floor_mode != "rare":
        raise ValueError(f"Unsupported tail floor mode: {candidate.tail_floor_mode}")
    guard = np.asarray(parts["tail_floor_guard"], dtype=np.float32)
    floor = float(candidate.tail_floor) * guard
    return np.maximum(np.asarray(raw, dtype=np.float32), floor).astype(np.float32)


def result_for_candidate(
    candidate: SourceArbitrationCandidate,
    *,
    normalized: object,
    component: object,
    view: ComponentView,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    include_details: bool,
    detail_limit: int,
    band_sample_size: int,
) -> dict[str, object]:
    calibration_metrics = metrics_for_context(normalized, calibration_context)
    holdout_metrics = metrics_for_context(normalized, holdout_context)
    row = {
        "candidate_id": candidate.candidate_id,
        "params": candidate_params(candidate),
        "calibration": {
            "scores": calibration_metrics["scores"],
            "metrics": _summary_metrics(calibration_metrics),
        },
        "holdout": {
            "scores": holdout_metrics["scores"],
            "metrics": _summary_metrics(holdout_metrics),
        },
        "generalization_delta": _rounded(
            _optional_float(holdout_metrics["scores"].get("balanced_score"))
            - _optional_float(calibration_metrics["scores"].get("balanced_score"))
            if _optional_float(holdout_metrics["scores"].get("balanced_score")) is not None
            and _optional_float(calibration_metrics["scores"].get("balanced_score")) is not None
            else None
        ),
    }
    if include_details:
        row["details"] = {
            "band_samples": _band_samples(
                normalized,
                component=component,
                segment_ids=np.zeros(len(view.frequency), dtype=np.int64),
                expert_ids=(candidate.candidate_id,),
                per_band=band_sample_size,
            ),
            "largest_movements_vs_frequency": largest_movements_vs_frequency(
                normalized,
                view=view,
                limit=detail_limit,
            ),
            "calibration_errors": detail_rows(
                normalized,
                calibration_context,
                limit=detail_limit,
            ),
            "holdout_errors": detail_rows(
                normalized,
                holdout_context,
                limit=detail_limit,
            ),
            "calibration_wrong_pairwise_examples": calibration_metrics["pairwise_order"][
                "wrong_examples"
            ][:detail_limit],
            "holdout_wrong_pairwise_examples": holdout_metrics["pairwise_order"]["wrong_examples"][
                :detail_limit
            ],
            "segment_misses": {
                "calibration": {
                    key: value["misses"]
                    for key, value in calibration_metrics["segments"].items()
                    if value.get("misses")
                },
                "holdout": {
                    key: value["misses"]
                    for key, value in holdout_metrics["segments"].items()
                    if value.get("misses")
                },
            },
        }
    return row


def metrics_for_context(normalized: object, context: Mapping[str, object]) -> dict[str, object]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    valid = indices >= 0
    observed[valid] = np.asarray(normalized, dtype=np.float32)[indices[valid]]
    return _difficulty_metrics(
        expected_values=context["expected_values"],
        observed_values=observed,
        expected_bands=context["expected_bands"],
        expected_candidate_states=context.get("expected_candidate_states"),
        observed_candidate_states=context.get("observed_candidate_states"),
        labels=context["labels"],
    )


def build_leaderboards(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> dict[str, list[dict[str, object]]]:
    return {
        "calibration_balanced": leaderboard(
            rows, dataset="calibration", score_key="balanced_score", limit=limit
        ),
        "holdout_balanced": leaderboard(
            rows, dataset="holdout", score_key="balanced_score", limit=limit
        ),
        "holdout_pairwise": leaderboard(
            rows, dataset="holdout", score_key="pairwise_order_score", limit=limit
        ),
        "holdout_mae": leaderboard(
            rows, dataset="holdout", score_key="numeric_mae_score", limit=limit
        ),
        "holdout_guardrail": leaderboard(
            guardrail_rows(rows),
            dataset="holdout",
            score_key="balanced_score",
            limit=limit,
        ),
        "least_overfit": sorted(
            [
                compact_result(row)
                for row in rows
                if _score(row, "calibration", "balanced_score") is not None
                and _score(row, "holdout", "balanced_score") is not None
            ],
            key=lambda row: (
                abs(float(row.get("generalization_delta") or 0.0)),
                -float(_mapping(row.get("holdout_scores")).get("balanced_score") or 0.0),
            ),
        )[:limit],
    }


def same_surface_alt_impact_report(
    *,
    candidate_family: str,
    candidate_results: Sequence[Mapping[str, object]],
    candidate_by_id: Mapping[str, SourceArbitrationCandidate],
    view: ComponentView,
    parts: Mapping[str, object],
    component: object,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
) -> dict[str, object]:
    if candidate_family not in {
        "same_surface_alt",
        "same_surface_attenuate",
        "same_surface_combo",
        "jlpt_exact_surface_inheritance_sweep",
    }:
        return {}
    effect_free_rows = [
        row
        for row in candidate_results
        if _is_effect_free_baseline_params(_mapping(row.get("params")))
    ]
    no_floor_rows = [
        row
        for row in candidate_results
        if not _has_same_surface_floor_effect(_mapping(row.get("params")))
        and _mapping(row.get("params")).get("same_surface_source_attenuation_mode") == "none"
    ]
    if not effect_free_rows:
        return {"available": False, "reason": "no no-floor baseline candidate found"}
    baseline_row = leaderboard(
        effect_free_rows,
        dataset="holdout",
        score_key="balanced_score",
        limit=1,
    )[0]
    no_floor_by_key = {
        _same_surface_match_key(candidate_by_id[str(row.get("candidate_id") or "")]): str(
            row.get("candidate_id") or ""
        )
        for row in no_floor_rows
        if str(row.get("candidate_id") or "") in candidate_by_id
    }
    candidate_ids = [
        str(baseline_row.get("candidate_id") or ""),
        str(
            _mapping(
                leaderboard(
                    candidate_results,
                    dataset="holdout",
                    score_key="balanced_score",
                    limit=1,
                )[0]
            ).get("candidate_id")
            or ""
        ),
        str(
            _mapping(
                leaderboard(
                    candidate_results,
                    dataset="calibration",
                    score_key="balanced_score",
                    limit=1,
                )[0]
            ).get("candidate_id")
            or ""
        ),
        _top_non_noop_candidate_id(
            candidate_results,
            dataset="holdout",
            score_key="balanced_score",
        ),
        _top_non_noop_candidate_id(
            candidate_results,
            dataset="holdout",
            score_key="pairwise_order_score",
        ),
    ]
    candidate_ids = [candidate_id for candidate_id in dict.fromkeys(candidate_ids) if candidate_id]
    baseline_id = str(baseline_row.get("candidate_id") or "")
    scores = {
        candidate_id: _scores_for_candidate_id(
            candidate_id,
            candidate_by_id=candidate_by_id,
            view=view,
            parts=parts,
        )
        for candidate_id in candidate_ids
        if candidate_id in candidate_by_id
    }
    matched_baseline_ids = {
        candidate_id: (
            no_floor_by_key.get(
                _same_surface_match_key(candidate_by_id[candidate_id]),
                baseline_id,
            )
            if _has_same_surface_floor_effect(candidate_params(candidate_by_id[candidate_id]))
            else baseline_id
        )
        for candidate_id in candidate_ids
        if candidate_id in candidate_by_id
    }
    for matched_baseline_id in set(matched_baseline_ids.values()):
        if matched_baseline_id and matched_baseline_id not in scores:
            scores[matched_baseline_id] = _scores_for_candidate_id(
                matched_baseline_id,
                candidate_by_id=candidate_by_id,
                view=view,
                parts=parts,
            )
    baseline_scores = scores.get(baseline_id)
    if baseline_scores is None:
        return {"available": False, "reason": "baseline score array unavailable"}
    impacts = [
        _same_surface_candidate_impact(
            candidate_id,
            scores=np.asarray(scores[candidate_id], dtype=np.float32),
            baseline_scores=np.asarray(
                scores[matched_baseline_ids[candidate_id]], dtype=np.float32
            ),
            baseline_candidate_id=matched_baseline_ids[candidate_id],
            view=view,
            parts=parts,
            limit=12,
            labeled_contexts={
                "calibration": calibration_context,
                "holdout": holdout_context,
            },
        )
        for candidate_id in candidate_ids
        if candidate_id != baseline_id and candidate_id in scores
    ]
    return {
        "available": True,
        "baseline_candidate_id": baseline_id,
        "baseline_holdout_scores": _mapping(baseline_row.get("holdout_scores")),
        "risk_population": {
            "source_rank_gap_positive": int(
                (
                    np.asarray(parts["same_surface_source_rank_gap_risk"], dtype=np.float32) > 0.0
                ).sum()
            ),
            "rare_source_rank_gap_positive": int(
                (
                    np.asarray(
                        parts["same_surface_rare_source_rank_gap_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
            ),
            "pollution_positive": int(
                (np.asarray(parts["same_surface_pollution_risk"], dtype=np.float32) > 0.0).sum()
            ),
            "rare_pollution_positive": int(
                (
                    np.asarray(
                        parts["same_surface_rare_pollution_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
            ),
            "pedagogical_family_only_rare_pollution_positive": int(
                (
                    np.asarray(
                        parts["same_surface_pedagogical_family_only_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
            ),
            "jlpt_family_only_positive": int(
                (np.asarray(parts["jlpt_vocab_family_only_known"], dtype=np.float32) > 0.0).sum()
            ),
        },
        "candidate_impacts": impacts,
        "focus_rows": _same_surface_focus_rows(
            candidate_ids=candidate_ids,
            scores=scores,
            view=view,
            parts=parts,
        ),
        "component_matrix_row_count": int(len(component["lemmas"])),
    }


def _is_effect_free_baseline_params(params: Mapping[str, object]) -> bool:
    return (
        not _has_same_surface_floor_effect(params)
        and params.get("same_surface_source_attenuation_mode") == "none"
        and (_optional_float(params.get("jlpt_exact_blend")) or 0.0) <= 0.0
        and (_optional_float(params.get("jlpt_inherited_penalty")) or 0.0) <= 0.0
    )


def _has_same_surface_floor_effect(params: Mapping[str, object]) -> bool:
    return (
        params.get("same_surface_floor_mode") != "none"
        or params.get("same_surface_secondary_floor_mode") != "none"
    )


def _scores_for_candidate_id(
    candidate_id: str,
    *,
    candidate_by_id: Mapping[str, SourceArbitrationCandidate],
    view: ComponentView,
    parts: Mapping[str, object],
) -> object:
    candidate = candidate_by_id[candidate_id]
    return normalized_scores_for_candidate(candidate, view, parts=parts)


def _top_non_noop_candidate_id(
    rows: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    score_key: str,
) -> str:
    for row in leaderboard(rows, dataset=dataset, score_key=score_key, limit=len(rows)):
        params = _mapping(row.get("params"))
        if (
            _has_same_surface_floor_effect(params)
            or params.get("same_surface_source_attenuation_mode") != "none"
            or (_optional_float(params.get("jlpt_exact_blend")) or 0.0) > 0.0
            or (_optional_float(params.get("jlpt_inherited_penalty")) or 0.0) > 0.0
        ):
            return str(row.get("candidate_id") or "")
    return ""


def _same_surface_match_key(candidate: SourceArbitrationCandidate) -> tuple[object, ...]:
    return (
        candidate.ped_mode,
        candidate.native_mode,
        candidate.base_mode,
        candidate.ped_strength,
        candidate.tail_source,
        candidate.tail_lower,
        candidate.tail_upper,
        candidate.burden_mode,
        candidate.burden_delta,
        candidate.entity_delta,
        candidate.entity_gate_mode,
        candidate.topic_delta,
        candidate.topic_gate_mode,
        candidate.ordinary_cap,
        candidate.ordinary_cap_mode,
        candidate.ordinary_cap_strength,
        candidate.ordinary_gate_mode,
        candidate.reading_guard_delta,
        candidate.tail_floor,
        candidate.tail_floor_mode,
        candidate.same_surface_source_attenuation,
        candidate.same_surface_source_attenuation_mode,
        candidate.jlpt_ped_mode,
        candidate.jlpt_exact_blend,
        candidate.jlpt_exact_blend_gate_mode,
        candidate.jlpt_exact_min_gap,
        candidate.jlpt_inherited_penalty,
        candidate.jlpt_inherited_penalty_mode,
        candidate.gairaigo_source_delta,
        candidate.gairaigo_source_gate_mode,
        candidate.gairaigo_english_ease_delta,
        candidate.gairaigo_english_ease_mode,
        candidate.gairaigo_jlpt_raise_block,
        candidate.jlpt_bound_mode,
        candidate.jlpt_bound_margin,
        candidate.jlpt_bound_strength,
    )


def _same_surface_candidate_impact(
    candidate_id: str,
    *,
    scores: np.ndarray,
    baseline_scores: np.ndarray,
    baseline_candidate_id: str,
    view: ComponentView,
    parts: Mapping[str, object],
    limit: int,
    labeled_contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    delta = scores - baseline_scores
    positive = delta > 1e-6
    negative = delta < -1e-6
    thresholds = (0.005, 0.02, 0.05, 0.10, 0.20)
    top_positive_indices = np.argsort(-delta, kind="stable")[: max(limit * 4, limit)]
    top_negative_indices = np.argsort(delta, kind="stable")[: max(limit * 4, limit)]
    top_positive_rows = [
        _same_surface_delta_row(
            int(index),
            values=scores,
            baseline_values=baseline_scores,
            parts=parts,
            view=view,
        )
        for index in top_positive_indices
        if delta[index] > 1e-6
    ][:limit]
    top_negative_rows = [
        _same_surface_delta_row(
            int(index),
            values=scores,
            baseline_values=baseline_scores,
            parts=parts,
            view=view,
        )
        for index in top_negative_indices
        if delta[index] < -1e-6
    ][:limit]
    return {
        "candidate_id": candidate_id,
        "baseline_candidate_id": baseline_candidate_id,
        "changed_count": int(positive.sum()),
        "changed_count_by_delta": {
            f"gt_{threshold:g}": int((delta > threshold).sum()) for threshold in thresholds
        },
        "negative_shift_count": int(negative.sum()),
        "negative_shift_count_by_delta": {
            f"lt_-{threshold:g}": int((delta < -threshold).sum()) for threshold in thresholds
        },
        "max_delta": _rounded(float(delta.max()) if len(delta) else None),
        "max_negative_delta": _rounded(float(delta.min()) if len(delta) else None),
        "mean_positive_delta": _rounded(float(delta[positive].mean()) if positive.any() else 0.0),
        "mean_negative_delta": _rounded(float(delta[negative].mean()) if negative.any() else 0.0),
        "top_positive_delta_rows": top_positive_rows,
        "top_negative_delta_rows": top_negative_rows,
        "labeled_regression_rows": {
            name: _labeled_regression_rows(
                scores=scores,
                baseline_scores=baseline_scores,
                context=context,
                view=view,
                parts=parts,
                limit=limit,
            )
            for name, context in labeled_contexts.items()
        },
    }


def _labeled_regression_rows(
    *,
    scores: np.ndarray,
    baseline_scores: np.ndarray,
    context: Mapping[str, object],
    view: ComponentView,
    parts: Mapping[str, object],
    limit: int,
) -> list[dict[str, object]]:
    component_indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected_values = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    valid = (component_indices >= 0) & np.isfinite(expected_values)
    if not valid.any():
        return []
    valid_positions = np.flatnonzero(valid)
    valid_indices = component_indices[valid_positions]
    baseline_observed = baseline_scores[valid_indices]
    candidate_observed = scores[valid_indices]
    baseline_errors = np.abs(baseline_observed - expected_values[valid_positions])
    candidate_errors = np.abs(candidate_observed - expected_values[valid_positions])
    error_delta = candidate_errors - baseline_errors
    order = valid_positions[np.argsort(-error_delta, kind="stable")]
    rows: list[dict[str, object]] = []
    for position in order:
        if len(rows) >= limit:
            break
        index = int(component_indices[position])
        regression = float(error_delta[np.where(valid_positions == position)[0][0]])
        if regression <= 1e-6:
            continue
        row = _same_surface_signal_row(index, view=view, parts=parts)
        row.update(
            {
                "review_label": labels[position],
                "expected": _rounded(float(expected_values[position])),
                "baseline": _rounded(float(baseline_scores[index])),
                "candidate": _rounded(float(scores[index])),
                "baseline_error": _rounded(
                    float(abs(baseline_scores[index] - expected_values[position]))
                ),
                "candidate_error": _rounded(float(abs(scores[index] - expected_values[position]))),
                "error_delta": _rounded(regression),
            }
        )
        rows.append(row)
    return rows


def _same_surface_focus_rows(
    *,
    candidate_ids: Sequence[str],
    scores: Mapping[str, object],
    view: ComponentView,
    parts: Mapping[str, object],
) -> list[dict[str, object]]:
    lookup = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings))
    }
    rows = []
    for lemma, reading in SAME_SURFACE_FOCUS_ROWS:
        index = lookup.get((lemma, reading))
        if index is None:
            rows.append({"label": f"{lemma}/{reading}", "missing": True})
            continue
        row = _same_surface_signal_row(index, view=view, parts=parts)
        row["scores"] = {
            candidate_id: _rounded(float(np.asarray(scores[candidate_id])[index]))
            for candidate_id in candidate_ids
            if candidate_id in scores
        }
        rows.append(row)
    return rows


def _same_surface_delta_row(
    index: int,
    *,
    values: np.ndarray,
    baseline_values: np.ndarray,
    parts: Mapping[str, object],
    view: ComponentView,
) -> dict[str, object]:
    row = _same_surface_signal_row(index, view=view, parts=parts)
    row.update(
        {
            "baseline": _rounded(float(baseline_values[index])),
            "candidate": _rounded(float(values[index])),
            "delta": _rounded(float(values[index] - baseline_values[index])),
        }
    )
    return row


def _same_surface_signal_row(
    index: int,
    *,
    view: ComponentView,
    parts: Mapping[str, object],
) -> dict[str, object]:
    return {
        "lemma": str(view.lemmas[index]),
        "reading": str(view.readings[index]),
        "label": f"{view.lemmas[index]}/{view.readings[index]}",
        "candidate_state": str(view.candidate_states[index]),
        "core_rank": _rounded(
            float(view.core_ranks[index]) if np.isfinite(view.core_ranks[index]) else None
        ),
        "same_surface_alt_count": _rounded(float(parts["same_surface_alt_count"][index])),
        "same_surface_rank_disadvantage": _rounded(
            float(parts["same_surface_rank_disadvantage"][index])
        ),
        "same_surface_unranked_vs_ranked": bool(
            float(parts["same_surface_unranked_vs_ranked"][index]) > 0.0
        ),
        "same_surface_source_rank_gap_risk": _rounded(
            float(parts["same_surface_source_rank_gap_risk"][index])
        ),
        "same_surface_rare_source_rank_gap_risk": _rounded(
            float(parts["same_surface_rare_source_rank_gap_risk"][index])
        ),
        "same_surface_exact_commonness": _rounded(
            float(parts["same_surface_exact_commonness"][index])
        ),
        "same_surface_exact_weakness": _rounded(float(parts["same_surface_exact_weakness"][index])),
        "same_surface_pollution_risk": _rounded(float(parts["same_surface_pollution_risk"][index])),
        "same_surface_rare_pollution_risk": _rounded(
            float(parts["same_surface_rare_pollution_risk"][index])
        ),
        "same_surface_pedagogical_family_only_risk": _rounded(
            float(parts["same_surface_pedagogical_family_only_risk"][index])
        ),
        "jlpt_vocab_known": _rounded(float(parts["jlpt_vocab_known"][index])),
        "jlpt_vocab_surface_known": _rounded(float(parts["jlpt_vocab_surface_known"][index])),
        "jlpt_vocab_exact_known": _rounded(float(parts["jlpt_vocab_exact_known"][index])),
        "jlpt_vocab_family_only_known": _rounded(
            float(parts["jlpt_vocab_family_only_known"][index])
        ),
        "jlpt_vocab_difficulty": _rounded(
            float(parts["jlpt_vocab_difficulty"][index])
            if np.isfinite(float(parts["jlpt_vocab_difficulty"][index]))
            else None
        ),
        "jlpt_vocab_exact_difficulty": _rounded(
            float(parts["jlpt_vocab_exact_difficulty"][index])
            if np.isfinite(float(parts["jlpt_vocab_exact_difficulty"][index]))
            else None
        ),
        "jlpt_vocab_exact_gap": _rounded(float(parts["jlpt_vocab_exact_gap"][index])),
        "lesson_vocab_known": _rounded(float(parts["lesson_vocab_known"][index])),
        "pedagogical_family_only_known": _rounded(
            float(parts["pedagogical_family_only_known"][index])
        ),
        "reading_form_source_strength": _rounded(
            float(parts["reading_form_source_strength"][index])
        ),
        "rare_reading_form_strength": _rounded(float(parts["rare_reading_form_strength"][index])),
    }


def guardrail_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    filtered = []
    for row in rows:
        holdout = _mapping(_mapping(row.get("holdout")).get("scores"))
        if (_optional_float(holdout.get("pairwise_order_score")) or 0.0) < GUARDRAIL_PAIRWISE_MIN:
            continue
        if (
            _optional_float(holdout.get("beginner_core_score")) or 0.0
        ) < GUARDRAIL_BEGINNER_CORE_MIN:
            continue
        if (_optional_float(holdout.get("high_tail_score")) or 0.0) < GUARDRAIL_HIGH_TAIL_MIN:
            continue
        filtered.append(row)
    return filtered


def leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    score_key: str,
    limit: int,
) -> list[dict[str, object]]:
    sortable = [row for row in rows if _score(row, dataset, score_key) is not None]
    return [
        compact_result(row)
        for row in sorted(
            sortable,
            key=lambda row: float(_score(row, dataset, score_key) or -1.0),
            reverse=True,
        )[:limit]
    ]


def compact_result(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "candidate_id": row.get("candidate_id"),
        "params": row.get("params"),
        "calibration_scores": _mapping(_mapping(row.get("calibration")).get("scores")),
        "holdout_scores": _mapping(_mapping(row.get("holdout")).get("scores")),
        "generalization_delta": row.get("generalization_delta"),
    }


def largest_movements_vs_frequency(
    normalized: object,
    *,
    view: ComponentView,
    limit: int,
) -> dict[str, list[dict[str, object]]]:
    values = np.asarray(normalized, dtype=np.float32)
    frequency = np.asarray(view.frequency, dtype=np.float32)
    delta = values - frequency
    finite = np.isfinite(values) & np.isfinite(frequency)
    indices = np.where(finite)[0]

    def row(index: int) -> dict[str, object]:
        return {
            "lemma": str(view.lemmas[index]),
            "reading": str(view.readings[index]),
            "candidate_identity_key": str(view.identities[index]),
            "model_value": _rounded(float(values[index])),
            "frequency_value": _rounded(float(frequency[index])),
            "delta": _rounded(float(delta[index])),
        }

    earlier = indices[np.argsort(delta[indices], kind="stable")[:limit]]
    later = indices[np.argsort(-delta[indices], kind="stable")[:limit]]
    return {
        "moved_earlier": [row(int(index)) for index in earlier],
        "moved_later": [row(int(index)) for index in later],
    }


def detail_rows(
    normalized: object,
    context: Mapping[str, object],
    *,
    limit: int,
) -> list[dict[str, object]]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    values = np.asarray(normalized, dtype=np.float32)
    rows = []
    for index, component_index in enumerate(indices):
        if component_index < 0 or not np.isfinite(expected[index]):
            continue
        observed = float(values[component_index])
        rows.append(
            {
                "label": labels[index],
                "expected": _rounded(float(expected[index])),
                "observed": _rounded(observed),
                "absolute_error": _rounded(abs(observed - float(expected[index]))),
                "direction": "too_low" if observed < expected[index] else "too_high",
            }
        )
    return sorted(rows, key=lambda row: float(row["absolute_error"] or 0.0), reverse=True)[:limit]


def load_reference_summary(path: Path | None) -> dict[str, object]:
    if path is None or not path.is_file():
        return {"available": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    leaderboards = _mapping(payload.get("leaderboards"))
    holdout_balanced = _sequence_dicts(leaderboards.get("holdout_balanced"))
    calibration_balanced = _sequence_dicts(leaderboards.get("calibration_balanced"))
    return {
        "available": True,
        "path": _repo_or_home_path(path),
        "best_holdout_balanced": (
            _reference_row(holdout_balanced[0], dataset="holdout") if holdout_balanced else None
        ),
        "best_calibration_balanced": (
            _reference_row(calibration_balanced[0], dataset="calibration")
            if calibration_balanced
            else None
        ),
    }


def _reference_row(row: Mapping[str, object], *, dataset: str) -> dict[str, object]:
    scores = {
        "balanced_score": row.get("balanced"),
        "bucket_accuracy_score": row.get("bucket_accuracy"),
        "pairwise_order_score": row.get("pairwise_accuracy"),
        "rank_correlation_score": row.get("spearman"),
        "beginner_core_score": row.get("beginner_core"),
        "high_tail_score": row.get("high_tail"),
    }
    mae = _optional_float(row.get("mae"))
    if mae is not None:
        scores["numeric_mae_score"] = _rounded(1.0 - mae)
    result = {
        "candidate_id": row.get("candidate_id"),
        "source": row.get("source"),
        "calibration_scores": {},
        "holdout_scores": {},
        "generalization_delta": None,
    }
    if dataset == "holdout":
        result["holdout_scores"] = scores
    else:
        result["calibration_scores"] = scores
    return result


def candidate_params(candidate: SourceArbitrationCandidate) -> dict[str, object]:
    return {
        "candidate_family": candidate.candidate_family,
        "ped_mode": candidate.ped_mode,
        "native_mode": candidate.native_mode,
        "base_mode": candidate.base_mode,
        "ped_strength": _rounded(candidate.ped_strength),
        "tail_source": candidate.tail_source,
        "tail_lower": _rounded(candidate.tail_lower),
        "tail_upper": _rounded(candidate.tail_upper),
        "burden_mode": candidate.burden_mode,
        "burden_delta": _rounded(candidate.burden_delta),
        "entity_delta": _rounded(candidate.entity_delta),
        "entity_gate_mode": candidate.entity_gate_mode,
        "topic_delta": _rounded(candidate.topic_delta),
        "topic_gate_mode": candidate.topic_gate_mode,
        "ordinary_cap": _rounded(candidate.ordinary_cap),
        "ordinary_cap_mode": candidate.ordinary_cap_mode,
        "ordinary_cap_strength": _rounded(candidate.ordinary_cap_strength),
        "ordinary_gate_mode": candidate.ordinary_gate_mode,
        "reading_guard_delta": _rounded(candidate.reading_guard_delta),
        "tail_floor": _rounded(candidate.tail_floor),
        "tail_floor_mode": candidate.tail_floor_mode,
        "same_surface_floor": _rounded(candidate.same_surface_floor),
        "same_surface_floor_mode": candidate.same_surface_floor_mode,
        "same_surface_source_attenuation": _rounded(candidate.same_surface_source_attenuation),
        "same_surface_source_attenuation_mode": (candidate.same_surface_source_attenuation_mode),
        "jlpt_ped_mode": candidate.jlpt_ped_mode,
        "jlpt_exact_blend": _rounded(candidate.jlpt_exact_blend),
        "jlpt_exact_blend_gate_mode": candidate.jlpt_exact_blend_gate_mode,
        "jlpt_exact_min_gap": _rounded(candidate.jlpt_exact_min_gap),
        "jlpt_inherited_penalty": _rounded(candidate.jlpt_inherited_penalty),
        "jlpt_inherited_penalty_mode": candidate.jlpt_inherited_penalty_mode,
        "same_surface_secondary_floor": _rounded(candidate.same_surface_secondary_floor),
        "same_surface_secondary_floor_mode": (candidate.same_surface_secondary_floor_mode),
        "gairaigo_source_delta": _rounded(candidate.gairaigo_source_delta),
        "gairaigo_source_gate_mode": candidate.gairaigo_source_gate_mode,
        "gairaigo_english_ease_delta": _rounded(candidate.gairaigo_english_ease_delta),
        "gairaigo_english_ease_mode": candidate.gairaigo_english_ease_mode,
        "gairaigo_jlpt_raise_block": candidate.gairaigo_jlpt_raise_block,
        "jlpt_bound_mode": candidate.jlpt_bound_mode,
        "jlpt_bound_margin": _rounded(candidate.jlpt_bound_margin),
        "jlpt_bound_strength": _rounded(candidate.jlpt_bound_strength),
    }


def _candidate_id(params: Mapping[str, object]) -> str:
    parts = []
    keys = (
        "p",
        "n",
        "b",
        "ps",
        "ts",
        "tl",
        "tu",
        "bm",
        "bd",
        "ed",
        "eg",
        "td",
        "tg",
        "oc",
        "ocm",
        "ocs",
        "og",
        "rg",
        "tf",
        "tfm",
        "ssf",
        "ssfm",
        "s2f",
        "s2fm",
        "ssa",
        "ssam",
        "jpm",
        "jeb",
        "jeg",
        "jemg",
        "jip",
        "jipm",
        "gsd",
        "gsg",
        "ged",
        "gem",
        "gjb",
        "jbm",
        "jmar",
        "jbs",
    )
    for key in keys:
        if key not in params:
            continue
        value = params[key]
        if isinstance(value, float):
            value = f"{value:g}".replace(".", "p")
        parts.append(f"{key}{value}")
    return "srcarb_" + "_".join(parts)


def _nan_reduce(
    arrays: Sequence[object],
    *,
    mode: str,
    fallback: float,
) -> object:
    if not arrays:
        raise ValueError("Expected at least one array.")
    stack = np.stack([np.asarray(array, dtype=np.float32) for array in arrays], axis=0)
    finite = np.isfinite(stack)
    count = finite.sum(axis=0)
    if mode == "mean":
        total = np.where(finite, stack, 0.0).sum(axis=0)
        return np.divide(
            total,
            count,
            out=np.full(stack.shape[1], fallback, dtype=np.float32),
            where=count > 0,
        ).astype(np.float32)
    if mode == "max":
        reduced = np.where(finite, stack, -np.inf).max(axis=0)
    elif mode == "min":
        reduced = np.where(finite, stack, np.inf).min(axis=0)
    else:
        raise ValueError(f"Unsupported reduce mode: {mode}")
    return np.where(count > 0, reduced, fallback).astype(np.float32)


def _ramp(values: object, *, lower: float, upper: float) -> object:
    if upper <= lower:
        return np.zeros_like(np.asarray(values, dtype=np.float32))
    parsed = np.nan_to_num(np.asarray(values, dtype=np.float32), nan=0.0)
    return np.clip((parsed - float(lower)) / (float(upper) - float(lower)), 0.0, 1.0)


def _score(row: Mapping[str, object], dataset: str, score_key: str) -> float | None:
    return _optional_float(_mapping(_mapping(row.get(dataset)).get("scores")).get(score_key))


def _detailed_candidate_ids(
    leaderboards: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[str, ...]:
    ids: list[str] = []
    for key in (
        "holdout_balanced",
        "holdout_guardrail",
        "calibration_balanced",
        "holdout_pairwise",
        "holdout_mae",
    ):
        for row in leaderboards.get(key, ())[:5]:
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id:
                ids.append(candidate_id)
    return tuple(dict.fromkeys(ids))


def _sequence_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Source-Arbitration Learner-Difficulty Search",
        "",
        "Status: generated sidecar experiment",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Method",
        "",
        _escape(_mapping(report.get("method")).get("shape")),
        "",
        "## Inputs",
        "",
        f"- Component matrix: `{_escape(inputs.get('component_matrix'))}`",
        f"- Calibration matrix: `{_escape(inputs.get('calibration_matrix'))}`",
        f"- Holdout review: `{_escape(inputs.get('review_markdown'))}`",
        f"- Component count: `{_escape(inputs.get('component_count'))}`",
        f"- Candidate count: `{_escape(inputs.get('candidate_count'))}`",
        "",
        "## Best Candidates",
        "",
        "| View | Candidate | Calibration balanced | Holdout balanced | Holdout pairwise | Holdout MAE score | Delta |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, row in (
        ("Best holdout", _mapping(summary.get("best_holdout_balanced"))),
        ("Best calibration", _mapping(summary.get("best_calibration_balanced"))),
        ("Reference holdout", _mapping(summary.get("reference_best_holdout_balanced"))),
    ):
        lines.append(_summary_row(label, row))
    lines.extend(["", "## Holdout Leaderboard", ""])
    lines.extend(
        _leaderboard_markdown(_mapping(report.get("leaderboards")).get("holdout_balanced"))
    )
    lines.extend(["", "## Guardrail Leaderboard", ""])
    lines.append(
        "Requires holdout pairwise >= "
        f"`{GUARDRAIL_PAIRWISE_MIN}`, beginner-core >= "
        f"`{GUARDRAIL_BEGINNER_CORE_MIN}`, and high-tail >= `{GUARDRAIL_HIGH_TAIL_MIN}`."
    )
    lines.extend([""])
    lines.extend(
        _leaderboard_markdown(_mapping(report.get("leaderboards")).get("holdout_guardrail"))
    )
    lines.extend(["", "## Calibration Leaderboard", ""])
    lines.extend(
        _leaderboard_markdown(_mapping(report.get("leaderboards")).get("calibration_balanced"))
    )
    impact_lines = _same_surface_impact_markdown(report.get("same_surface_alt_impact"))
    if impact_lines:
        lines.extend(["", "## Same-Surface Alternate-Reading Impact", ""])
        lines.extend(impact_lines)
    lines.extend(["", "## Detailed Samples", ""])
    for row in _sequence_dicts(report.get("detailed_results"))[:3]:
        lines.extend(_detailed_markdown(row))
    return "\n".join(lines).rstrip() + "\n"


def _summary_row(label: str, row: Mapping[str, object]) -> str:
    calibration = _mapping(row.get("calibration_scores"))
    holdout = _mapping(row.get("holdout_scores"))
    return (
        f"| {_escape(label)} | `{_escape(row.get('candidate_id'))}` | "
        f"{_escape(calibration.get('balanced_score'))} | "
        f"{_escape(holdout.get('balanced_score'))} | "
        f"{_escape(holdout.get('pairwise_order_score'))} | "
        f"{_escape(holdout.get('numeric_mae_score'))} | "
        f"{_escape(row.get('generalization_delta'))} |"
    )


def _leaderboard_markdown(value: object) -> list[str]:
    rows = _sequence_dicts(value)
    lines = [
        "| Rank | Candidate | Calibration balanced | Holdout balanced | Pairwise | Params |",
        "| ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for rank, row in enumerate(rows[:20], start=1):
        calibration = _mapping(row.get("calibration_scores"))
        holdout = _mapping(row.get("holdout_scores"))
        params = _mapping(row.get("params"))
        lines.append(
            f"| {rank} | `{_escape(row.get('candidate_id'))}` | "
            f"{_escape(calibration.get('balanced_score'))} | "
            f"{_escape(holdout.get('balanced_score'))} | "
            f"{_escape(holdout.get('pairwise_order_score'))} | "
            f"`{_escape(_compact_params(params))}` |"
        )
    return lines


def _same_surface_impact_markdown(value: object) -> list[str]:
    impact = _mapping(value)
    if not impact.get("available"):
        return []
    baseline_id = str(impact.get("baseline_candidate_id") or "")
    candidate_impacts = _sequence_dicts(impact.get("candidate_impacts"))
    candidate_ids = [baseline_id] + [
        str(row.get("candidate_id") or "") for row in candidate_impacts
    ]
    candidate_ids = [candidate_id for candidate_id in dict.fromkeys(candidate_ids) if candidate_id]
    score_labels = {
        baseline_id: "Baseline",
    }
    for index, candidate_id in enumerate(candidate_ids[1:], start=1):
        score_labels[candidate_id] = f"Candidate {index}"
    population = _mapping(impact.get("risk_population"))
    lines = [
        f"- Baseline no-floor candidate: `{_escape(baseline_id)}`",
        f"- Source-rank-gap risk rows: `{_escape(population.get('source_rank_gap_positive'))}`",
        f"- Rare-source-rank-gap risk rows: `{_escape(population.get('rare_source_rank_gap_positive'))}`",
        f"- Pollution-risk rows after exact-commonness guard: `{_escape(population.get('pollution_positive'))}`",
        f"- Rare-pollution-risk rows after exact-commonness guard: `{_escape(population.get('rare_pollution_positive'))}`",
        "",
        "| Role | Candidate | Matched baseline | Up | Down | Up >0.02 | Down >0.02 | Max up | Max down |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(candidate_impacts, start=1):
        counts = _mapping(row.get("changed_count_by_delta"))
        negative_counts = _mapping(row.get("negative_shift_count_by_delta"))
        lines.append(
            f"| Candidate {index} | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('baseline_candidate_id'))}` | "
            f"{_escape(row.get('changed_count'))} | "
            f"{_escape(row.get('negative_shift_count'))} | "
            f"{_escape(counts.get('gt_0.02'))} | "
            f"{_escape(negative_counts.get('lt_-0.02'))} | "
            f"{_escape(row.get('max_delta'))} | "
            f"{_escape(row.get('max_negative_delta'))} |"
        )
    for index, row in enumerate(candidate_impacts, start=1):
        lines.extend(_same_surface_regression_sample_markdown(index, row))
    lines.extend(["", "Focus rows:", ""])
    lines.append(_same_surface_focus_header(score_labels, candidate_ids))
    lines.append(_same_surface_focus_rule(candidate_ids))
    for row in _sequence_dicts(impact.get("focus_rows")):
        lines.append(
            _same_surface_focus_row(row, score_labels=score_labels, candidate_ids=candidate_ids)
        )
    return lines


def _same_surface_focus_header(
    score_labels: Mapping[str, str],
    candidate_ids: Sequence[str],
) -> str:
    score_columns = " | ".join(
        _escape(score_labels[candidate_id]) for candidate_id in candidate_ids
    )
    return (
        "| Row | "
        f"{score_columns} | Pollution | Rare pollution | Exact common | "
        "Source risk | Rank gap | Source strength |"
    )


def _same_surface_focus_rule(candidate_ids: Sequence[str]) -> str:
    score_rules = " | ".join("---:" for _candidate_id in candidate_ids)
    return f"| --- | {score_rules} | ---: | ---: | ---: | ---: | ---: | ---: |"


def _same_surface_focus_row(
    row: Mapping[str, object],
    *,
    score_labels: Mapping[str, str],
    candidate_ids: Sequence[str],
) -> str:
    scores = _mapping(row.get("scores"))
    score_values = " | ".join(
        _escape(scores.get(candidate_id))
        for candidate_id in candidate_ids
        if candidate_id in score_labels
    )
    return (
        f"| `{_escape(row.get('label'))}` | {score_values} | "
        f"{_escape(row.get('same_surface_pollution_risk'))} | "
        f"{_escape(row.get('same_surface_rare_pollution_risk'))} | "
        f"{_escape(row.get('same_surface_exact_commonness'))} | "
        f"{_escape(row.get('same_surface_source_rank_gap_risk'))} | "
        f"{_escape(row.get('same_surface_rank_disadvantage'))} | "
        f"{_escape(row.get('reading_form_source_strength'))} |"
    )


def _same_surface_regression_sample_markdown(
    index: int,
    row: Mapping[str, object],
) -> list[str]:
    lines = ["", f"Candidate {index} regression/shift samples:", ""]
    regressions = _mapping(row.get("labeled_regression_rows"))
    for dataset in ("holdout", "calibration"):
        samples = _sequence_dicts(regressions.get(dataset))[:8]
        lines.extend([f"{dataset.title()} labeled rows whose absolute error got worse:", ""])
        if not samples:
            lines.extend(["None.", ""])
            continue
        lines.extend(
            [
                "| Row | Expected | Baseline | Candidate | Error delta | Source risk | Exact common |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for sample in samples:
            lines.append(
                f"| `{_escape(sample.get('review_label') or sample.get('label'))}` | "
                f"{_escape(sample.get('expected'))} | "
                f"{_escape(sample.get('baseline'))} | "
                f"{_escape(sample.get('candidate'))} | "
                f"{_escape(sample.get('error_delta'))} | "
                f"{_escape(sample.get('same_surface_source_rank_gap_risk'))} | "
                f"{_escape(sample.get('same_surface_exact_commonness'))} |"
            )
        lines.append("")
    negative_samples = _sequence_dicts(row.get("top_negative_delta_rows"))[:8]
    lines.extend(
        [
            "Largest full-matrix negative score shifts (qualitative only; unlabeled rows are not automatically regressions):",
            "",
        ]
    )
    if not negative_samples:
        lines.extend(["None.", ""])
        return lines
    lines.extend(
        [
            "| Row | Baseline | Candidate | Delta | Source risk | Exact common |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for sample in negative_samples:
        lines.append(
            f"| `{_escape(sample.get('label'))}` | "
            f"{_escape(sample.get('baseline'))} | "
            f"{_escape(sample.get('candidate'))} | "
            f"{_escape(sample.get('delta'))} | "
            f"{_escape(sample.get('same_surface_source_rank_gap_risk'))} | "
            f"{_escape(sample.get('same_surface_exact_commonness'))} |"
        )
    return lines


def _detailed_markdown(row: Mapping[str, object]) -> list[str]:
    details = _mapping(row.get("details"))
    lines = [
        f"### `{_escape(row.get('candidate_id'))}`",
        "",
        f"- Calibration balanced: `{_escape(_score(row, 'calibration', 'balanced_score'))}`",
        f"- Holdout balanced: `{_escape(_score(row, 'holdout', 'balanced_score'))}`",
        f"- Generalization delta: `{_escape(row.get('generalization_delta'))}`",
        "",
        "Largest holdout errors:",
        "",
        "| Label | Expected | Observed | Error | Direction |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for error in _sequence_dicts(details.get("holdout_errors"))[:8]:
        lines.append(
            f"| {_escape(error.get('label'))} | {_escape(error.get('expected'))} | "
            f"{_escape(error.get('observed'))} | {_escape(error.get('absolute_error'))} | "
            f"{_escape(error.get('direction'))} |"
        )
    movements = _mapping(details.get("largest_movements_vs_frequency"))
    lines.extend(["", "Moved earlier vs frequency:", ""])
    lines.extend(_movement_table(movements.get("moved_earlier")))
    lines.extend(["", "Moved later vs frequency:", ""])
    lines.extend(_movement_table(movements.get("moved_later")))
    return lines


def _movement_table(value: object) -> list[str]:
    lines = [
        "| Word | Model | Frequency | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in _sequence_dicts(value)[:8]:
        word = (
            f"{row.get('lemma')}/{row.get('reading')}" if row.get("reading") else row.get("lemma")
        )
        lines.append(
            f"| {_escape(word)} | {_escape(row.get('model_value'))} | "
            f"{_escape(row.get('frequency_value'))} | {_escape(row.get('delta'))} |"
        )
    return lines


def _compact_params(params: Mapping[str, object]) -> str:
    keys = (
        "ped_mode",
        "native_mode",
        "base_mode",
        "ped_strength",
        "tail_source",
        "tail_lower",
        "tail_upper",
        "burden_mode",
        "burden_delta",
        "entity_delta",
        "entity_gate_mode",
        "topic_delta",
        "topic_gate_mode",
        "ordinary_cap",
        "ordinary_cap_mode",
        "ordinary_cap_strength",
        "ordinary_gate_mode",
        "reading_guard_delta",
        "tail_floor",
        "tail_floor_mode",
        "same_surface_floor",
        "same_surface_floor_mode",
        "same_surface_source_attenuation",
        "same_surface_source_attenuation_mode",
        "gairaigo_source_delta",
        "gairaigo_source_gate_mode",
        "gairaigo_english_ease_delta",
        "gairaigo_english_ease_mode",
        "gairaigo_jlpt_raise_block",
        "jlpt_bound_mode",
        "jlpt_bound_margin",
        "jlpt_bound_strength",
    )
    return ",".join(f"{key}={params.get(key)}" for key in keys)


if __name__ == "__main__":
    raise SystemExit(main())
