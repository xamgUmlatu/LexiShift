#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from functools import lru_cache
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
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _band_samples,
    _calibration_context,
    _difficulty_band,
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
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
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
    ("而して", "しこうして"),
    ("スウェーデン", "すうぇーでん"),
    ("ブラシ", "ぶらし"),
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
BASE_FAMILY_FUNCTION_POS_PREFIXES = ("助詞", "助動詞", "補助記号", "空白")


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
    same_surface_gradient_low_floor: float = 0.0
    same_surface_gradient_high_floor: float = 0.0
    same_surface_gradient_mode: str = "none"
    same_surface_gradient_curve: str = "linear"
    same_surface_gradient_commonness_cap: float = 0.0
    same_surface_gradient_lesson_rescue: float = 0.0
    same_surface_gradient_marked_boost: float = 0.0
    gairaigo_source_delta: float = 0.0
    gairaigo_source_gate_mode: str = "none"
    gairaigo_english_ease_delta: float = 0.0
    gairaigo_english_ease_mode: str = "none"
    gairaigo_jlpt_raise_block: bool = False
    jlpt_bound_mode: str = "none"
    jlpt_bound_margin: float = 0.0
    jlpt_bound_strength: float = 1.0
    cross_corpus_rescue_cap: float = 0.0
    cross_corpus_rescue_mode: str = "none"
    cross_corpus_rescue_strength: float = 1.0
    cross_corpus_rescue_bccwj_lower: float = 0.88
    cross_corpus_rescue_bccwj_upper: float = 0.96
    cross_corpus_rescue_tubelex_lower: float = 0.70
    cross_corpus_rescue_tubelex_upper: float = 0.88
    cross_corpus_rescue_curve: str = "linear"
    cross_corpus_rescue_gate_mode: str = "no_ped_normal"
    cross_corpus_rescue_boost_strength: float = 0.0
    cross_corpus_rescue_boost_bccwj_lower: float = 0.92
    cross_corpus_rescue_boost_bccwj_upper: float = 0.97
    cross_corpus_rescue_boost_tubelex_lower: float = 0.76
    cross_corpus_rescue_boost_tubelex_upper: float = 0.86
    cross_corpus_rescue_burden_lower: float = 0.88
    cross_corpus_rescue_burden_upper: float = 0.98
    cross_corpus_rescue_single_kanji_lower: float = 0.68
    cross_corpus_rescue_single_kanji_upper: float = 0.90
    jmdict_priority_guard_mode: str = "none"
    jmdict_priority_guard_strength: float = 0.0
    jmdict_priority_guard_ordinary_strength: float = 0.0
    jmdict_priority_guard_curve: str = "linear"
    jmdict_priority_guard_ped_rescue: float = 1.0
    jmdict_priority_source: str = "legacy"
    jmdict_pair_safe_blend: float = 1.0
    pair_leak_ped_gate_mode: str = "none"
    pair_leak_ped_adjustment_mode: str = "none"
    pair_leak_ped_strength: float = 0.0
    pair_leak_ped_floor: float = 0.0
    pair_leak_ped_curve: str = "linear"
    ordinary_gate_curve: str = "linear"
    ordinary_exception_mode: str = "current"
    ordinary_exception_curve: str = "linear"
    base_family_rescue_margin: float = 0.0
    base_family_rescue_strength: float = 0.0
    base_family_rescue_gate_mode: str = "none"
    base_family_rescue_gap_lower: float = 0.08
    base_family_rescue_gap_upper: float = 0.30


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
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON_OUT)
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
        "--target-curve-override",
        choices=("component", "warp_p60_g155"),
        default="component",
        help=(
            "Optional monotone target-score remap applied after raw candidate "
            "ranking. component preserves the curve baked into the component matrix; "
            "warp_p60_g155 keeps positions <=0.60 unchanged and smoothly stretches "
            "the upper tail with gamma=1.55."
        ),
    )
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
            "same_surface_exact_protected_floor_refine",
            "same_surface_gradient_floor_refine",
            "cross_corpus_common_rescue_refine",
            "cross_corpus_typed_rescue_refine",
            "jmdict_priority_guard_refine",
            "jmdict_pair_priority_source_refine",
            "fixed_data_current_ablation",
            "pair_leak_ped_trust_refine",
            "ordinary_cap_corrected_data_refine",
            "base_family_rescue_refine",
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
            "secondary same-surface floors; same_surface_exact_protected_floor_refine "
            "tests stricter family-only floors that explicitly exempt effective "
            "exact JLPT rows; same_surface_gradient_floor_refine tests a "
            "continuous version of that exact-protected floor using exact "
            "commonness, marked-reading evidence, and lesson-known rescue; "
            "cross_corpus_common_rescue_refine tests a no-pedagogical-anchor "
            "ordinary-vocabulary pull-down gated by BCCWJ and Tubelex commonness; "
            "cross_corpus_typed_rescue_refine adds non-kango, typed ordinary-shape, "
            "marked-usage, and high-kanji-burden guards around the same signal; "
            "jmdict_priority_guard_refine tests conditional JMDict priority "
            "trust around the current typed rescue winner; "
            "jmdict_pair_priority_source_refine tests replacing or raising "
            "entry-level JMDict priority with exact surface-reading pair priority; "
            "fixed_data_current_ablation removes active current-model compensation "
            "nodes on the corrected pair-priority matrix; pair_leak_ped_trust_refine "
            "tests reducing broad pedagogical trust when exact pair evidence says "
            "the easy source is inherited; ordinary_cap_corrected_data_refine "
            "resweeps the ordinary/easy cap operator against corrected pair-priority "
            "signals with pair-safe ordinary evidence and hard-evidence vetoes; "
            "base_family_rescue_refine adds the accepted single-content-token "
            "dictionary-base rescue on top of the frozen acceptance candidate."
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
        calibration_json=_resolve_path(args.calibration_json),
        review_markdown=_resolve_path(args.review_markdown),
        holdout_json=_resolve_path(args.holdout_json),
        reference_holdout_json=_resolve_path(args.reference_holdout_json)
        if args.reference_holdout_json
        else None,
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        detail_limit=max(1, int(args.detail_limit)),
        band_sample_size=max(1, int(args.band_sample_size)),
        candidate_family=str(args.candidate_family),
        target_curve_override=str(args.target_curve_override),
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
    reference_holdout_json: Path | None,
    leaderboard_limit: int = 20,
    detail_limit: int = 20,
    band_sample_size: int = 6,
    candidate_family: str = "v1",
    target_curve_override: str = "component",
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    view = _view_with_target_curve_override(
        ComponentView.from_npz(component),
        target_curve_override=target_curve_override,
    )
    calibration_context = _refresh_context_expected_from_label_json(
        _calibration_context(calibration, component),
        calibration_json,
    )
    holdout_rows = _load_holdout_rows(holdout_json, fallback_markdown=review_markdown)
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
            "target_curve_override": target_curve_override,
            "target_curve": _target_curve_override_metadata(
                view.target_positions,
                target_curve_override=target_curve_override,
            ),
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
            "calibration_json": _repo_or_home_path(calibration_json),
            "review_markdown": _repo_or_home_path(review_markdown),
            "holdout_json": _repo_or_home_path(holdout_json),
            "reference_holdout_json": (
                _repo_or_home_path(reference_holdout_json)
                if reference_holdout_json and reference_holdout_json.exists()
                else None
            ),
            "component_count": len(view.frequency),
            "signal_count": len(view.names),
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
                "calibration_json": calibration_json,
                "review_markdown": review_markdown,
                "holdout_json": holdout_json,
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


def _view_with_target_curve_override(
    view: ComponentView,
    *,
    target_curve_override: str,
) -> ComponentView:
    if target_curve_override == "component":
        return view
    if target_curve_override == "warp_p60_g155":
        return replace(
            view,
            target_positions=_warp_upper_tail_positions(
                view.target_positions,
                pivot=0.60,
                gamma=1.55,
            ),
        )
    raise ValueError(f"Unsupported target curve override: {target_curve_override}")


def _warp_upper_tail_positions(values: object, *, pivot: float, gamma: float) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    warped = parsed.copy()
    mask = warped > float(pivot)
    scaled = (warped[mask] - float(pivot)) / (1.0 - float(pivot))
    warped[mask] = float(pivot) + ((1.0 - float(pivot)) * (1.0 - np.power(1.0 - scaled, gamma)))
    return np.clip(warped, 0.0, 1.0).astype(np.float32)


def _target_curve_override_metadata(
    target_positions: object,
    *,
    target_curve_override: str,
) -> dict[str, object]:
    values = np.asarray(target_positions, dtype=np.float32)
    return {
        "override": target_curve_override,
        "decile_counts": _target_curve_band_counts(values, width=0.10),
        "half_band_counts": _target_curve_band_counts(values, width=0.05),
    }


def _target_curve_band_counts(values: object, *, width: float) -> list[dict[str, object]]:
    parsed = np.asarray(values, dtype=np.float32)
    total = int(len(parsed))
    rows: list[dict[str, object]] = []
    units = round(1.0 / width)
    for index in range(units):
        start = round(index * width, 6)
        end = round((index + 1) * width, 6)
        if index == units - 1:
            mask = (parsed >= start) & (parsed <= end)
        else:
            mask = (parsed >= start) & (parsed < end)
        count = int(mask.sum())
        rows.append(
            {
                "band": f"{start:.2f}-{end:.2f}",
                "count": count,
                "percent": _rounded(count / total) if total else None,
            }
        )
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


def _split_label(label: str) -> tuple[str, str]:
    if "/" not in label:
        return label, ""
    lemma, reading = label.rsplit("/", 1)
    return lemma, reading


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
    if candidate_family == "same_surface_exact_protected_floor_refine":
        return generate_same_surface_exact_protected_floor_refine_candidates()
    if candidate_family == "same_surface_gradient_floor_refine":
        return generate_same_surface_gradient_floor_refine_candidates()
    if candidate_family == "cross_corpus_common_rescue_refine":
        return generate_cross_corpus_common_rescue_refine_candidates()
    if candidate_family == "cross_corpus_typed_rescue_refine":
        return generate_cross_corpus_typed_rescue_refine_candidates()
    if candidate_family == "jmdict_priority_guard_refine":
        return generate_jmdict_priority_guard_refine_candidates()
    if candidate_family == "jmdict_pair_priority_source_refine":
        return generate_jmdict_pair_priority_source_refine_candidates()
    if candidate_family == "fixed_data_current_ablation":
        return generate_fixed_data_current_ablation_candidates()
    if candidate_family == "pair_leak_ped_trust_refine":
        return generate_pair_leak_ped_trust_refine_candidates()
    if candidate_family == "ordinary_cap_corrected_data_refine":
        return generate_ordinary_cap_corrected_data_refine_candidates()
    if candidate_family == "base_family_rescue_refine":
        return generate_base_family_rescue_refine_candidates()
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


def generate_same_surface_exact_protected_floor_refine_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    floor_specs = (
        ("pedagogical_family_only_rare_pollution", 0.42),
        ("pedagogical_family_only_rare_pollution", 0.50),
        ("pedagogical_family_only_rare_pollution", 0.62),
        ("pedagogical_family_only_rare_pollution_unprotected_exact", 0.42),
        ("pedagogical_family_only_rare_pollution_unprotected_exact", 0.50),
        ("pedagogical_family_only_rare_pollution_unprotected_exact", 0.62),
        ("pedagogical_family_only_rare_pollution_unprotected_exact", 0.74),
    )
    for secondary_floor_mode, secondary_floor in floor_specs:
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
            "ssf": 0.0,
            "ssfm": "none",
            "s2f": secondary_floor,
            "s2fm": secondary_floor_mode,
            "ssa": 0.0,
            "ssam": "none",
            "jpm": "effective",
            "jeb": 0.0,
            "jeg": "none",
            "jemg": 0.0,
            "jip": 0.0,
            "jipm": "none",
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
                candidate_family="same_surface_exact_protected_floor_refine",
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
                same_surface_floor=0.0,
                same_surface_floor_mode="none",
                same_surface_source_attenuation=0.0,
                same_surface_source_attenuation_mode="none",
                jlpt_ped_mode="effective",
                jlpt_exact_blend=0.0,
                jlpt_exact_blend_gate_mode="none",
                jlpt_exact_min_gap=0.0,
                jlpt_inherited_penalty=0.0,
                jlpt_inherited_penalty_mode="none",
                same_surface_secondary_floor=secondary_floor,
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


def generate_base_family_rescue_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    frozen = next(
        candidate
        for candidate in generate_same_surface_exact_protected_floor_refine_candidates()
        if candidate.same_surface_secondary_floor == 0.42
        and candidate.same_surface_secondary_floor_mode
        == "pedagogical_family_only_rare_pollution_unprotected_exact"
    )
    variants = [
        (0.0, 0.0, "none"),
        (0.06, 1.0, "score_gap"),
    ]
    candidates: list[SourceArbitrationCandidate] = []
    for margin, strength, gate_mode in variants:
        suffix = (
            "_bfrm0_bfrs0_bfrgnone"
            if strength <= 0.0 or gate_mode == "none"
            else "_bfrm0p06_bfrs1_bfrgscore_gap"
        )
        candidates.append(
            replace(
                frozen,
                candidate_id=f"{frozen.candidate_id}{suffix}",
                candidate_family="base_family_rescue_refine",
                base_family_rescue_margin=margin,
                base_family_rescue_strength=strength,
                base_family_rescue_gate_mode=gate_mode,
                base_family_rescue_gap_lower=0.08,
                base_family_rescue_gap_upper=0.30,
            )
        )
    return tuple(candidates)


def generate_same_surface_gradient_floor_refine_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    base_params = _current_source_arbitration_params()

    candidates.append(
        _current_source_arbitration_candidate(
            candidate_family="same_surface_gradient_floor_refine",
            params={**base_params, "s2f": 0.0, "s2fm": "none"},
        )
    )

    hard_floor_specs = (
        ("pedagogical_family_only_rare_pollution_unprotected_exact", 0.42),
        ("pedagogical_family_only_rare_pollution_unprotected_exact", 0.74),
    )
    for secondary_floor_mode, secondary_floor in hard_floor_specs:
        candidates.append(
            _current_source_arbitration_candidate(
                candidate_family="same_surface_gradient_floor_refine",
                params={
                    **base_params,
                    "s2f": secondary_floor,
                    "s2fm": secondary_floor_mode,
                },
                same_surface_secondary_floor=secondary_floor,
                same_surface_secondary_floor_mode=secondary_floor_mode,
            )
        )

    low_floors = (0.0, 0.34, 0.42, 0.50)
    high_floors = (0.42, 0.62, 0.74, 0.86, 0.95)
    commonness_caps = (0.0, 0.08, 0.15, 0.25)
    lesson_rescues = (0.0, 0.35, 0.65)
    marked_boosts = (0.0, 0.35, 0.65, 1.0)
    curves = ("linear", "square", "sqrt", "smoothstep")
    for low_floor in low_floors:
        for high_floor in high_floors:
            if high_floor < low_floor:
                continue
            for commonness_cap in commonness_caps:
                for lesson_rescue in lesson_rescues:
                    for marked_boost in marked_boosts:
                        for curve in curves:
                            params = {
                                **base_params,
                                "sglf": low_floor,
                                "sghf": high_floor,
                                "sgm": "exact_protected_evidence",
                                "sgc": curve,
                                "sgcc": commonness_cap,
                                "sglr": lesson_rescue,
                                "sgmb": marked_boost,
                            }
                            candidates.append(
                                _current_source_arbitration_candidate(
                                    candidate_family="same_surface_gradient_floor_refine",
                                    params=params,
                                    same_surface_gradient_low_floor=low_floor,
                                    same_surface_gradient_high_floor=high_floor,
                                    same_surface_gradient_mode="exact_protected_evidence",
                                    same_surface_gradient_curve=curve,
                                    same_surface_gradient_commonness_cap=commonness_cap,
                                    same_surface_gradient_lesson_rescue=lesson_rescue,
                                    same_surface_gradient_marked_boost=marked_boost,
                                )
                            )
    return tuple(candidates)


def generate_cross_corpus_common_rescue_refine_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    base_params = _current_source_arbitration_params()
    candidates.append(
        _current_source_arbitration_candidate(
            candidate_family="cross_corpus_common_rescue_refine",
            params={**base_params, "ccrc": 0.0, "ccrm": "none"},
        )
    )

    cap_specs = (
        ("hard", 1.0),
        ("soft", 0.35),
        ("soft", 0.55),
        ("soft", 0.75),
        ("soft", 1.0),
    )
    bccwj_bands = (
        (0.80, 0.94),
        (0.84, 0.95),
        (0.88, 0.96),
        (0.90, 0.98),
    )
    tubelex_bands = (
        (0.60, 0.82),
        (0.65, 0.86),
        (0.70, 0.88),
        (0.75, 0.92),
    )
    curves = ("linear", "square", "sqrt", "smoothstep")
    for rescue_cap in (0.34, 0.38, 0.42, 0.46, 0.50, 0.56):
        for rescue_mode, rescue_strength in cap_specs:
            for bccwj_lower, bccwj_upper in bccwj_bands:
                for tubelex_lower, tubelex_upper in tubelex_bands:
                    for curve in curves:
                        params = {
                            **base_params,
                            "ccrc": rescue_cap,
                            "ccrm": rescue_mode,
                            "ccrs": rescue_strength,
                            "ccbl": bccwj_lower,
                            "ccbu": bccwj_upper,
                            "cctl": tubelex_lower,
                            "cctu": tubelex_upper,
                            "cccc": curve,
                            "ccg": "no_ped_normal",
                        }
                        candidates.append(
                            _current_source_arbitration_candidate(
                                candidate_family="cross_corpus_common_rescue_refine",
                                params=params,
                                cross_corpus_rescue_cap=rescue_cap,
                                cross_corpus_rescue_mode=rescue_mode,
                                cross_corpus_rescue_strength=rescue_strength,
                                cross_corpus_rescue_bccwj_lower=bccwj_lower,
                                cross_corpus_rescue_bccwj_upper=bccwj_upper,
                                cross_corpus_rescue_tubelex_lower=tubelex_lower,
                                cross_corpus_rescue_tubelex_upper=tubelex_upper,
                                cross_corpus_rescue_curve=curve,
                                cross_corpus_rescue_gate_mode="no_ped_normal",
                            )
                        )
    return tuple(candidates)


def generate_cross_corpus_typed_rescue_refine_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    base_params = _current_source_arbitration_params()
    candidates.append(
        _current_source_arbitration_candidate(
            candidate_family="cross_corpus_typed_rescue_refine",
            params={**base_params, "ccrc": 0.0, "ccrm": "none"},
        )
    )
    candidates.append(
        _current_source_arbitration_candidate(
            candidate_family="cross_corpus_typed_rescue_refine",
            params={
                **base_params,
                "ccrc": 0.38,
                "ccrm": "hard",
                "ccrs": 1.0,
                "ccbl": 0.84,
                "ccbu": 0.95,
                "cctl": 0.60,
                "cctu": 0.82,
                "cccc": "linear",
                "ccg": "no_ped_normal",
            },
            cross_corpus_rescue_cap=0.38,
            cross_corpus_rescue_mode="hard",
            cross_corpus_rescue_strength=1.0,
            cross_corpus_rescue_bccwj_lower=0.84,
            cross_corpus_rescue_bccwj_upper=0.95,
            cross_corpus_rescue_tubelex_lower=0.60,
            cross_corpus_rescue_tubelex_upper=0.82,
            cross_corpus_rescue_curve="linear",
            cross_corpus_rescue_gate_mode="no_ped_normal",
        )
    )

    cap_specs = (
        ("hard", 1.0),
        ("soft", 0.65),
        ("soft", 1.0),
    )
    bccwj_bands = (
        (0.80, 0.94),
        (0.84, 0.95),
        (0.88, 0.96),
    )
    tubelex_bands = (
        (0.60, 0.82),
        (0.65, 0.86),
        (0.70, 0.88),
    )
    burden_bands = (
        (0.82, 0.94),
        (0.88, 0.98),
    )
    single_kanji_bands = (
        (0.62, 0.88),
        (0.68, 0.90),
    )
    boost_bccwj_bands = (
        (0.90, 0.96),
        (0.92, 0.97),
    )
    boost_tubelex_bands = (
        (0.72, 0.84),
        (0.76, 0.86),
    )
    curves = ("linear", "square", "sqrt")
    boost_strengths = (0.0, 0.65, 0.80, 0.95)
    for rescue_cap in (0.34, 0.38, 0.42, 0.46, 0.50):
        for rescue_mode, rescue_strength in cap_specs:
            for bccwj_lower, bccwj_upper in bccwj_bands:
                for tubelex_lower, tubelex_upper in tubelex_bands:
                    for curve in curves:
                        for burden_lower, burden_upper in burden_bands:
                            for single_lower, single_upper in single_kanji_bands:
                                for boost_strength in boost_strengths:
                                    if boost_strength <= 0.0:
                                        boost_bands = ((0.92, 0.97, 0.76, 0.86),)
                                    else:
                                        boost_bands = tuple(
                                            (
                                                boost_bccwj_lower,
                                                boost_bccwj_upper,
                                                boost_tubelex_lower,
                                                boost_tubelex_upper,
                                            )
                                            for boost_bccwj_lower, boost_bccwj_upper in boost_bccwj_bands
                                            for boost_tubelex_lower, boost_tubelex_upper in boost_tubelex_bands
                                        )
                                    for (
                                        boost_bccwj_lower,
                                        boost_bccwj_upper,
                                        boost_tubelex_lower,
                                        boost_tubelex_upper,
                                    ) in boost_bands:
                                        params = {
                                            **base_params,
                                            "ccrc": rescue_cap,
                                            "ccrm": rescue_mode,
                                            "ccrs": rescue_strength,
                                            "ccbl": bccwj_lower,
                                            "ccbu": bccwj_upper,
                                            "cctl": tubelex_lower,
                                            "cctu": tubelex_upper,
                                            "cccc": curve,
                                            "ccg": "typed_nonkango_life",
                                            "ccbs": boost_strength,
                                            "ccbbl": boost_bccwj_lower,
                                            "ccbbu": boost_bccwj_upper,
                                            "ccbtll": boost_tubelex_lower,
                                            "ccbtu": boost_tubelex_upper,
                                            "ccbrl": burden_lower,
                                            "ccbru": burden_upper,
                                            "ccskl": single_lower,
                                            "ccsku": single_upper,
                                        }
                                        candidates.append(
                                            _current_source_arbitration_candidate(
                                                candidate_family=(
                                                    "cross_corpus_typed_rescue_refine"
                                                ),
                                                params=params,
                                                cross_corpus_rescue_cap=rescue_cap,
                                                cross_corpus_rescue_mode=rescue_mode,
                                                cross_corpus_rescue_strength=rescue_strength,
                                                cross_corpus_rescue_bccwj_lower=bccwj_lower,
                                                cross_corpus_rescue_bccwj_upper=bccwj_upper,
                                                cross_corpus_rescue_tubelex_lower=(tubelex_lower),
                                                cross_corpus_rescue_tubelex_upper=(tubelex_upper),
                                                cross_corpus_rescue_curve=curve,
                                                cross_corpus_rescue_gate_mode=(
                                                    "typed_nonkango_life"
                                                ),
                                                cross_corpus_rescue_boost_strength=(boost_strength),
                                                cross_corpus_rescue_boost_bccwj_lower=(
                                                    boost_bccwj_lower
                                                ),
                                                cross_corpus_rescue_boost_bccwj_upper=(
                                                    boost_bccwj_upper
                                                ),
                                                cross_corpus_rescue_boost_tubelex_lower=(
                                                    boost_tubelex_lower
                                                ),
                                                cross_corpus_rescue_boost_tubelex_upper=(
                                                    boost_tubelex_upper
                                                ),
                                                cross_corpus_rescue_burden_lower=(burden_lower),
                                                cross_corpus_rescue_burden_upper=(burden_upper),
                                                cross_corpus_rescue_single_kanji_lower=(
                                                    single_lower
                                                ),
                                                cross_corpus_rescue_single_kanji_upper=(
                                                    single_upper
                                                ),
                                            )
                                        )
    return tuple(candidates)


def generate_jmdict_priority_guard_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    base_params = _current_source_arbitration_params()
    best_params = {
        **base_params,
        "ccrc": 0.34,
        "ccrm": "soft",
        "ccrs": 1.0,
        "ccbl": 0.80,
        "ccbu": 0.94,
        "cctl": 0.60,
        "cctu": 0.82,
        "cccc": "sqrt",
        "ccg": "typed_nonkango_life",
        "ccbs": 0.80,
        "ccbbl": 0.90,
        "ccbbu": 0.96,
        "ccbtll": 0.72,
        "ccbtu": 0.84,
        "ccbrl": 0.88,
        "ccbru": 0.98,
        "ccskl": 0.62,
        "ccsku": 0.88,
    }

    def add_candidate(
        *,
        params: Mapping[str, object],
        same_surface_floor: float = 0.0,
        same_surface_floor_mode: str = "none",
        guard_mode: str = "none",
        guard_strength: float = 0.0,
        guard_ordinary_strength: float = 0.0,
        guard_curve: str = "linear",
        guard_ped_rescue: float = 1.0,
    ) -> None:
        candidates.append(
            _current_source_arbitration_candidate(
                candidate_family="jmdict_priority_guard_refine",
                params=params,
                cross_corpus_rescue_cap=0.34,
                cross_corpus_rescue_mode="soft",
                cross_corpus_rescue_strength=1.0,
                cross_corpus_rescue_bccwj_lower=0.80,
                cross_corpus_rescue_bccwj_upper=0.94,
                cross_corpus_rescue_tubelex_lower=0.60,
                cross_corpus_rescue_tubelex_upper=0.82,
                cross_corpus_rescue_curve="sqrt",
                cross_corpus_rescue_gate_mode="typed_nonkango_life",
                cross_corpus_rescue_boost_strength=0.80,
                cross_corpus_rescue_boost_bccwj_lower=0.90,
                cross_corpus_rescue_boost_bccwj_upper=0.96,
                cross_corpus_rescue_boost_tubelex_lower=0.72,
                cross_corpus_rescue_boost_tubelex_upper=0.84,
                cross_corpus_rescue_burden_lower=0.88,
                cross_corpus_rescue_burden_upper=0.98,
                cross_corpus_rescue_single_kanji_lower=0.62,
                cross_corpus_rescue_single_kanji_upper=0.88,
                same_surface_secondary_floor=same_surface_floor,
                same_surface_secondary_floor_mode=same_surface_floor_mode,
                jmdict_priority_guard_mode=guard_mode,
                jmdict_priority_guard_strength=guard_strength,
                jmdict_priority_guard_ordinary_strength=guard_ordinary_strength,
                jmdict_priority_guard_curve=guard_curve,
                jmdict_priority_guard_ped_rescue=guard_ped_rescue,
            )
        )

    add_candidate(params={**best_params, "jpgm": "none", "jpgs": 0.0})
    for guard_mode in ("marked", "marked_same_surface", "marked_same_surface_news"):
        for guard_strength in (0.35, 0.55, 0.75, 1.0):
            for guard_ordinary_strength in (0.0, 0.50, 1.0):
                for guard_curve in ("linear", "sqrt", "smoothstep"):
                    floor_specs = [(0.0, "none")]
                    floor_specs.extend(
                        (floor, mode)
                        for floor in (0.62, 0.70, 0.78, 0.84)
                        for mode in (
                            "priority_pollution",
                            "unranked_priority_pollution",
                        )
                    )
                    for same_surface_floor, floor_mode in floor_specs:
                        params = {
                            **best_params,
                            "s2f": same_surface_floor,
                            "s2fm": floor_mode,
                            "jpgm": guard_mode,
                            "jpgs": guard_strength,
                            "jpgos": guard_ordinary_strength,
                            "jpgc": guard_curve,
                            "jpgpr": 1.0,
                        }
                        add_candidate(
                            params=params,
                            same_surface_floor=same_surface_floor,
                            same_surface_floor_mode=floor_mode,
                            guard_mode=guard_mode,
                            guard_strength=guard_strength,
                            guard_ordinary_strength=guard_ordinary_strength,
                            guard_curve=guard_curve,
                            guard_ped_rescue=1.0,
                        )
    return tuple(candidates)


def generate_jmdict_pair_priority_source_refine_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    base_params = _current_source_arbitration_params()
    best_params = {
        **base_params,
        "ccrc": 0.34,
        "ccrm": "soft",
        "ccrs": 1.0,
        "ccbl": 0.80,
        "ccbu": 0.94,
        "cctl": 0.60,
        "cctu": 0.82,
        "cccc": "sqrt",
        "ccg": "typed_nonkango_life",
        "ccbs": 0.80,
        "ccbbl": 0.90,
        "ccbbu": 0.96,
        "ccbtll": 0.72,
        "ccbtu": 0.84,
        "ccbrl": 0.88,
        "ccbru": 0.98,
        "ccskl": 0.62,
        "ccsku": 0.88,
    }

    def add_candidate(
        *,
        priority_source: str,
        pair_safe_blend: float = 1.0,
        guard_mode: str = "none",
        guard_strength: float = 0.0,
        guard_ordinary_strength: float = 0.0,
    ) -> None:
        params = {
            **best_params,
            "jpsrc": priority_source,
            "jpsb": pair_safe_blend,
            "jpgm": guard_mode,
            "jpgs": guard_strength,
            "jpgos": guard_ordinary_strength,
        }
        candidates.append(
            _current_source_arbitration_candidate(
                candidate_family="jmdict_pair_priority_source_refine",
                params=params,
                cross_corpus_rescue_cap=0.34,
                cross_corpus_rescue_mode="soft",
                cross_corpus_rescue_strength=1.0,
                cross_corpus_rescue_bccwj_lower=0.80,
                cross_corpus_rescue_bccwj_upper=0.94,
                cross_corpus_rescue_tubelex_lower=0.60,
                cross_corpus_rescue_tubelex_upper=0.82,
                cross_corpus_rescue_curve="sqrt",
                cross_corpus_rescue_gate_mode="typed_nonkango_life",
                cross_corpus_rescue_boost_strength=0.80,
                cross_corpus_rescue_boost_bccwj_lower=0.90,
                cross_corpus_rescue_boost_bccwj_upper=0.96,
                cross_corpus_rescue_boost_tubelex_lower=0.72,
                cross_corpus_rescue_boost_tubelex_upper=0.84,
                cross_corpus_rescue_burden_lower=0.88,
                cross_corpus_rescue_burden_upper=0.98,
                cross_corpus_rescue_single_kanji_lower=0.62,
                cross_corpus_rescue_single_kanji_upper=0.88,
                jmdict_priority_guard_mode=guard_mode,
                jmdict_priority_guard_strength=guard_strength,
                jmdict_priority_guard_ordinary_strength=guard_ordinary_strength,
                jmdict_priority_source=priority_source,
                jmdict_pair_safe_blend=pair_safe_blend,
            )
        )

    add_candidate(priority_source="legacy", pair_safe_blend=0.0)
    for blend in (0.25, 0.50, 0.75, 1.0):
        add_candidate(priority_source="pair_safe_raise", pair_safe_blend=blend)
        add_candidate(priority_source="pair_safe_blend", pair_safe_blend=blend)
    add_candidate(priority_source="pair_safe", pair_safe_blend=1.0)
    for blend in (0.50, 1.0):
        for guard_strength in (0.35, 0.55, 0.75):
            add_candidate(
                priority_source="pair_safe_raise",
                pair_safe_blend=blend,
                guard_mode="marked",
                guard_strength=guard_strength,
                guard_ordinary_strength=0.0,
            )
    return tuple(candidates)


def _typed_rescue_best_params() -> dict[str, object]:
    return {
        **_current_source_arbitration_params(),
        "ccrc": 0.34,
        "ccrm": "soft",
        "ccrs": 1.0,
        "ccbl": 0.80,
        "ccbu": 0.94,
        "cctl": 0.60,
        "cctu": 0.82,
        "cccc": "sqrt",
        "ccg": "typed_nonkango_life",
        "ccbs": 0.80,
        "ccbbl": 0.90,
        "ccbbu": 0.96,
        "ccbtll": 0.72,
        "ccbtu": 0.84,
        "ccbrl": 0.88,
        "ccbru": 0.98,
        "ccskl": 0.62,
        "ccsku": 0.88,
    }


def _typed_rescue_candidate_kwargs() -> dict[str, object]:
    return {
        "cross_corpus_rescue_cap": 0.34,
        "cross_corpus_rescue_mode": "soft",
        "cross_corpus_rescue_strength": 1.0,
        "cross_corpus_rescue_bccwj_lower": 0.80,
        "cross_corpus_rescue_bccwj_upper": 0.94,
        "cross_corpus_rescue_tubelex_lower": 0.60,
        "cross_corpus_rescue_tubelex_upper": 0.82,
        "cross_corpus_rescue_curve": "sqrt",
        "cross_corpus_rescue_gate_mode": "typed_nonkango_life",
        "cross_corpus_rescue_boost_strength": 0.80,
        "cross_corpus_rescue_boost_bccwj_lower": 0.90,
        "cross_corpus_rescue_boost_bccwj_upper": 0.96,
        "cross_corpus_rescue_boost_tubelex_lower": 0.72,
        "cross_corpus_rescue_boost_tubelex_upper": 0.84,
        "cross_corpus_rescue_burden_lower": 0.88,
        "cross_corpus_rescue_burden_upper": 0.98,
        "cross_corpus_rescue_single_kanji_lower": 0.62,
        "cross_corpus_rescue_single_kanji_upper": 0.88,
    }


def generate_fixed_data_current_ablation_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    best_params = _typed_rescue_best_params()
    best_kwargs = _typed_rescue_candidate_kwargs()

    def add_candidate(
        ablation: str,
        *,
        params: Mapping[str, object] | None = None,
        **overrides: object,
    ) -> None:
        merged_params = {**best_params, "ab": ablation}
        if params:
            merged_params.update(params)
        merged_kwargs = {**best_kwargs, **overrides}
        candidates.append(
            _current_source_arbitration_candidate(
                candidate_family="fixed_data_current_ablation",
                params=merged_params,
                **merged_kwargs,
            )
        )

    add_candidate("baseline")
    add_candidate(
        "no_burden",
        params={"bd": 0.0},
        burden_delta=0.0,
    )
    add_candidate(
        "no_ordinary_cap",
        params={"oc": 0.0, "ocm": "none"},
        ordinary_cap=0.0,
        ordinary_cap_mode="none",
    )
    add_candidate(
        "no_gairaigo_source",
        params={"gsd": 0.0},
        gairaigo_source_delta=0.0,
    )
    add_candidate(
        "no_gairaigo_english",
        params={"ged": 0.0},
        gairaigo_english_ease_delta=0.0,
    )
    add_candidate(
        "no_gairaigo_all",
        params={"gsd": 0.0, "ged": 0.0},
        gairaigo_source_delta=0.0,
        gairaigo_english_ease_delta=0.0,
    )
    add_candidate(
        "no_cross_corpus_boost",
        params={"ccbs": 0.0},
        cross_corpus_rescue_boost_strength=0.0,
    )
    add_candidate(
        "no_cross_corpus_rescue",
        params={"ccrc": 0.0, "ccrm": "none", "ccbs": 0.0},
        cross_corpus_rescue_cap=0.0,
        cross_corpus_rescue_mode="none",
        cross_corpus_rescue_boost_strength=0.0,
    )
    add_candidate(
        "no_rescue_family",
        params={"gsd": 0.0, "ged": 0.0, "ccrc": 0.0, "ccrm": "none", "ccbs": 0.0},
        gairaigo_source_delta=0.0,
        gairaigo_english_ease_delta=0.0,
        cross_corpus_rescue_cap=0.0,
        cross_corpus_rescue_mode="none",
        cross_corpus_rescue_boost_strength=0.0,
    )
    add_candidate(
        "pair_jmdict_raise_025",
        params={"jpsrc": "pair_safe_raise", "jpsb": 0.25},
        jmdict_priority_source="pair_safe_raise",
        jmdict_pair_safe_blend=0.25,
    )
    add_candidate(
        "pair_jmdict_raise_050",
        params={"jpsrc": "pair_safe_raise", "jpsb": 0.50},
        jmdict_priority_source="pair_safe_raise",
        jmdict_pair_safe_blend=0.50,
    )
    return tuple(candidates)


def generate_pair_leak_ped_trust_refine_candidates() -> tuple[SourceArbitrationCandidate, ...]:
    candidates: list[SourceArbitrationCandidate] = []
    best_params = _typed_rescue_best_params()
    best_kwargs = _typed_rescue_candidate_kwargs()

    def add_candidate(
        *,
        gate_mode: str,
        adjustment_mode: str,
        strength: float,
        floor: float = 0.0,
        curve: str = "linear",
    ) -> None:
        params = {
            **best_params,
            "plpg": gate_mode,
            "plpm": adjustment_mode,
            "plps": strength,
            "plpf": floor,
            "plpc": curve,
        }
        candidates.append(
            _current_source_arbitration_candidate(
                candidate_family="pair_leak_ped_trust_refine",
                params=params,
                pair_leak_ped_gate_mode=gate_mode,
                pair_leak_ped_adjustment_mode=adjustment_mode,
                pair_leak_ped_strength=strength,
                pair_leak_ped_floor=floor,
                pair_leak_ped_curve=curve,
                **best_kwargs,
            )
        )

    add_candidate(
        gate_mode="none",
        adjustment_mode="none",
        strength=0.0,
    )
    gate_modes = (
        "pair_leak_ped_known",
        "pair_leak_family_only",
        "pair_alt_family_only",
        "pair_missing_family_only",
        "pair_surface_only_family_only",
        "pair_leak_or_same_surface_family",
    )
    curves = ("linear", "sqrt", "smoothstep")
    for gate_mode in gate_modes:
        for curve in curves:
            for strength in (0.06, 0.10, 0.16, 0.24, 0.34):
                add_candidate(
                    gate_mode=gate_mode,
                    adjustment_mode="raise",
                    strength=strength,
                    curve=curve,
                )
            for strength in (0.25, 0.50, 0.75, 1.0):
                add_candidate(
                    gate_mode=gate_mode,
                    adjustment_mode="raise_toward_native",
                    strength=strength,
                    curve=curve,
                )
                add_candidate(
                    gate_mode=gate_mode,
                    adjustment_mode="raise_toward_pair_native",
                    strength=strength,
                    curve=curve,
                )
            for floor in (0.22, 0.34, 0.42, 0.50, 0.62, 0.74):
                add_candidate(
                    gate_mode=gate_mode,
                    adjustment_mode="floor",
                    strength=1.0,
                    floor=floor,
                    curve=curve,
                )
    return tuple(candidates)


def generate_ordinary_cap_corrected_data_refine_candidates() -> tuple[
    SourceArbitrationCandidate, ...
]:
    candidates: list[SourceArbitrationCandidate] = []
    best_params = _typed_rescue_best_params()
    best_kwargs = _typed_rescue_candidate_kwargs()

    def add_candidate(
        *,
        cap_mode: str,
        cap: float,
        strength: float,
        gate_mode: str,
        gate_curve: str,
        exception_mode: str,
        exception_curve: str,
    ) -> None:
        params = {
            **best_params,
            "oc": cap,
            "ocm": cap_mode,
            "ocs": strength,
            "og": gate_mode,
            "ogc": gate_curve,
            "oem": exception_mode,
            "oec": exception_curve,
        }
        candidates.append(
            _current_source_arbitration_candidate(
                candidate_family="ordinary_cap_corrected_data_refine",
                params=params,
                ordinary_cap=cap,
                ordinary_cap_mode=cap_mode,
                ordinary_cap_strength=strength,
                ordinary_gate_mode=gate_mode,
                ordinary_gate_curve=gate_curve,
                ordinary_exception_mode=exception_mode,
                ordinary_exception_curve=exception_curve,
                **best_kwargs,
            )
        )

    add_candidate(
        cap_mode="none",
        cap=0.0,
        strength=0.0,
        gate_mode="mean",
        gate_curve="linear",
        exception_mode="current",
        exception_curve="linear",
    )
    gate_modes = (
        "mean",
        "frequency",
        "freq_priority",
        "pedagogical",
        "pair_safe_priority",
        "freq_pair_safe_priority",
        "pair_safe_mean",
    )
    caps = (0.50, 0.58, 0.66, 0.74, 0.82)
    gate_curves = ("sqrt", "linear", "pow1p5", "square")
    exception_modes = (
        "current",
        "current_pair_leak",
        "marked_tail",
        "broad_hard",
    )
    exception_curves = ("linear", "sqrt")
    for gate_mode in gate_modes:
        for cap in caps:
            for gate_curve in gate_curves:
                for exception_mode in exception_modes:
                    for exception_curve in exception_curves:
                        add_candidate(
                            cap_mode="hard",
                            cap=cap,
                            strength=1.0,
                            gate_mode=gate_mode,
                            gate_curve=gate_curve,
                            exception_mode=exception_mode,
                            exception_curve=exception_curve,
                        )
                        for strength in (0.25, 0.50, 0.75, 1.0):
                            add_candidate(
                                cap_mode="soft",
                                cap=cap,
                                strength=strength,
                                gate_mode=gate_mode,
                                gate_curve=gate_curve,
                                exception_mode=exception_mode,
                                exception_curve=exception_curve,
                            )
    return tuple(candidates)


def _current_source_arbitration_params() -> dict[str, object]:
    return {
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
        "ssf": 0.0,
        "ssfm": "none",
        "s2f": 0.0,
        "s2fm": "none",
        "ssa": 0.0,
        "ssam": "none",
        "jpm": "effective",
        "jeb": 0.0,
        "jeg": "none",
        "jemg": 0.0,
        "jip": 0.0,
        "jipm": "none",
        "gsd": 0.05,
        "gsg": "marked_rarity",
        "ged": 0.04,
        "gem": "english_freq",
        "gjb": 0,
        "jbm": "none",
        "jmar": 0.0,
        "jbs": 1.0,
    }


def _current_source_arbitration_candidate(
    *,
    candidate_family: str,
    params: Mapping[str, object],
    same_surface_secondary_floor: float = 0.0,
    same_surface_secondary_floor_mode: str = "none",
    same_surface_gradient_low_floor: float = 0.0,
    same_surface_gradient_high_floor: float = 0.0,
    same_surface_gradient_mode: str = "none",
    same_surface_gradient_curve: str = "linear",
    same_surface_gradient_commonness_cap: float = 0.0,
    same_surface_gradient_lesson_rescue: float = 0.0,
    same_surface_gradient_marked_boost: float = 0.0,
    cross_corpus_rescue_cap: float = 0.0,
    cross_corpus_rescue_mode: str = "none",
    cross_corpus_rescue_strength: float = 1.0,
    cross_corpus_rescue_bccwj_lower: float = 0.88,
    cross_corpus_rescue_bccwj_upper: float = 0.96,
    cross_corpus_rescue_tubelex_lower: float = 0.70,
    cross_corpus_rescue_tubelex_upper: float = 0.88,
    cross_corpus_rescue_curve: str = "linear",
    cross_corpus_rescue_gate_mode: str = "no_ped_normal",
    cross_corpus_rescue_boost_strength: float = 0.0,
    cross_corpus_rescue_boost_bccwj_lower: float = 0.92,
    cross_corpus_rescue_boost_bccwj_upper: float = 0.97,
    cross_corpus_rescue_boost_tubelex_lower: float = 0.76,
    cross_corpus_rescue_boost_tubelex_upper: float = 0.86,
    cross_corpus_rescue_burden_lower: float = 0.88,
    cross_corpus_rescue_burden_upper: float = 0.98,
    cross_corpus_rescue_single_kanji_lower: float = 0.68,
    cross_corpus_rescue_single_kanji_upper: float = 0.90,
    jmdict_priority_guard_mode: str = "none",
    jmdict_priority_guard_strength: float = 0.0,
    jmdict_priority_guard_ordinary_strength: float = 0.0,
    jmdict_priority_guard_curve: str = "linear",
    jmdict_priority_guard_ped_rescue: float = 1.0,
    jmdict_priority_source: str = "legacy",
    jmdict_pair_safe_blend: float = 1.0,
    burden_delta: float = 0.05,
    ordinary_cap: float = 0.58,
    ordinary_cap_mode: str = "hard",
    ordinary_cap_strength: float = 1.0,
    ordinary_gate_mode: str = "mean",
    ordinary_gate_curve: str = "linear",
    ordinary_exception_mode: str = "current",
    ordinary_exception_curve: str = "linear",
    gairaigo_source_delta: float = 0.05,
    gairaigo_source_gate_mode: str = "marked_rarity",
    gairaigo_english_ease_delta: float = 0.04,
    gairaigo_english_ease_mode: str = "english_freq",
    pair_leak_ped_gate_mode: str = "none",
    pair_leak_ped_adjustment_mode: str = "none",
    pair_leak_ped_strength: float = 0.0,
    pair_leak_ped_floor: float = 0.0,
    pair_leak_ped_curve: str = "linear",
) -> SourceArbitrationCandidate:
    return SourceArbitrationCandidate(
        candidate_id=_candidate_id(params),
        candidate_family=candidate_family,
        ped_mode="min",
        native_mode="mean",
        base_mode="ped_native_min",
        ped_strength=1.0,
        tail_source="base",
        tail_lower=0.50,
        tail_upper=0.85,
        burden_mode="mean",
        burden_delta=burden_delta,
        entity_delta=0.0,
        entity_gate_mode="weak",
        topic_delta=0.0,
        topic_gate_mode="rarity",
        ordinary_cap=ordinary_cap,
        ordinary_cap_mode=ordinary_cap_mode,
        ordinary_cap_strength=ordinary_cap_strength,
        ordinary_gate_mode=ordinary_gate_mode,
        reading_guard_delta=0.0,
        tail_floor=0.0,
        tail_floor_mode="none",
        same_surface_floor=0.0,
        same_surface_floor_mode="none",
        same_surface_source_attenuation=0.0,
        same_surface_source_attenuation_mode="none",
        jlpt_ped_mode="effective",
        jlpt_exact_blend=0.0,
        jlpt_exact_blend_gate_mode="none",
        jlpt_exact_min_gap=0.0,
        jlpt_inherited_penalty=0.0,
        jlpt_inherited_penalty_mode="none",
        same_surface_secondary_floor=same_surface_secondary_floor,
        same_surface_secondary_floor_mode=same_surface_secondary_floor_mode,
        same_surface_gradient_low_floor=same_surface_gradient_low_floor,
        same_surface_gradient_high_floor=same_surface_gradient_high_floor,
        same_surface_gradient_mode=same_surface_gradient_mode,
        same_surface_gradient_curve=same_surface_gradient_curve,
        same_surface_gradient_commonness_cap=same_surface_gradient_commonness_cap,
        same_surface_gradient_lesson_rescue=same_surface_gradient_lesson_rescue,
        same_surface_gradient_marked_boost=same_surface_gradient_marked_boost,
        gairaigo_source_delta=gairaigo_source_delta,
        gairaigo_source_gate_mode=gairaigo_source_gate_mode,
        gairaigo_english_ease_delta=gairaigo_english_ease_delta,
        gairaigo_english_ease_mode=gairaigo_english_ease_mode,
        gairaigo_jlpt_raise_block=False,
        jlpt_bound_mode="none",
        jlpt_bound_margin=0.0,
        jlpt_bound_strength=1.0,
        cross_corpus_rescue_cap=cross_corpus_rescue_cap,
        cross_corpus_rescue_mode=cross_corpus_rescue_mode,
        cross_corpus_rescue_strength=cross_corpus_rescue_strength,
        cross_corpus_rescue_bccwj_lower=cross_corpus_rescue_bccwj_lower,
        cross_corpus_rescue_bccwj_upper=cross_corpus_rescue_bccwj_upper,
        cross_corpus_rescue_tubelex_lower=cross_corpus_rescue_tubelex_lower,
        cross_corpus_rescue_tubelex_upper=cross_corpus_rescue_tubelex_upper,
        cross_corpus_rescue_curve=cross_corpus_rescue_curve,
        cross_corpus_rescue_gate_mode=cross_corpus_rescue_gate_mode,
        cross_corpus_rescue_boost_strength=cross_corpus_rescue_boost_strength,
        cross_corpus_rescue_boost_bccwj_lower=cross_corpus_rescue_boost_bccwj_lower,
        cross_corpus_rescue_boost_bccwj_upper=cross_corpus_rescue_boost_bccwj_upper,
        cross_corpus_rescue_boost_tubelex_lower=(cross_corpus_rescue_boost_tubelex_lower),
        cross_corpus_rescue_boost_tubelex_upper=(cross_corpus_rescue_boost_tubelex_upper),
        cross_corpus_rescue_burden_lower=cross_corpus_rescue_burden_lower,
        cross_corpus_rescue_burden_upper=cross_corpus_rescue_burden_upper,
        cross_corpus_rescue_single_kanji_lower=(cross_corpus_rescue_single_kanji_lower),
        cross_corpus_rescue_single_kanji_upper=(cross_corpus_rescue_single_kanji_upper),
        jmdict_priority_guard_mode=jmdict_priority_guard_mode,
        jmdict_priority_guard_strength=jmdict_priority_guard_strength,
        jmdict_priority_guard_ordinary_strength=jmdict_priority_guard_ordinary_strength,
        jmdict_priority_guard_curve=jmdict_priority_guard_curve,
        jmdict_priority_guard_ped_rescue=jmdict_priority_guard_ped_rescue,
        jmdict_priority_source=jmdict_priority_source,
        jmdict_pair_safe_blend=jmdict_pair_safe_blend,
        pair_leak_ped_gate_mode=pair_leak_ped_gate_mode,
        pair_leak_ped_adjustment_mode=pair_leak_ped_adjustment_mode,
        pair_leak_ped_strength=pair_leak_ped_strength,
        pair_leak_ped_floor=pair_leak_ped_floor,
        pair_leak_ped_curve=pair_leak_ped_curve,
        ordinary_gate_curve=ordinary_gate_curve,
        ordinary_exception_mode=ordinary_exception_mode,
        ordinary_exception_curve=ordinary_exception_curve,
    )


def normalized_scores_for_candidate(
    candidate: SourceArbitrationCandidate,
    view: ComponentView,
    *,
    parts: Mapping[str, object],
) -> object:
    raw = raw_scores_for_candidate(candidate, view, parts=parts)
    normalized = _target_curve_normalize(raw, target_positions=view.target_positions)
    normalized = base_family_rescue_score(candidate, normalized, view=view)
    return jlpt_bounded_score(candidate, normalized, parts=parts)


def raw_scores_for_candidate(
    candidate: SourceArbitrationCandidate,
    view: ComponentView,
    *,
    parts: Mapping[str, object],
) -> object:
    ped = pedagogical_values_for_candidate(candidate, parts=parts)
    native = native_values_for_candidate(candidate, parts=parts)
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
    raw = cross_corpus_common_rescue_score(candidate, raw, parts=parts)
    raw = same_surface_alt_reading_floor_score(candidate, raw, parts=parts)
    raw += reading_guard_adjustment(candidate, parts=parts, frequency=view.frequency)
    raw = tail_floor_score(candidate, raw, parts=parts)
    return np.clip(np.nan_to_num(raw, nan=0.0), 0.0, 1.0).astype(np.float32)


def native_values_for_candidate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.jmdict_priority_source == "legacy" and (
        candidate.jmdict_priority_guard_strength <= 0.0
        or candidate.jmdict_priority_guard_mode == "none"
    ):
        return parts[f"native_{candidate.native_mode}"]
    if (
        candidate.jmdict_priority_guard_strength <= 0.0
        or candidate.jmdict_priority_guard_mode == "none"
    ):
        jmdict_priority = selected_jmdict_priority_difficulty(
            candidate,
            parts=parts,
        )
    else:
        jmdict_priority = guarded_jmdict_priority_difficulty(candidate, parts=parts)
    frequency = np.asarray(parts["native_frequency"], dtype=np.float32)
    tubelex = np.asarray(parts["tubelex_frequency"], dtype=np.float32)
    return _nan_reduce(
        (frequency, tubelex, jmdict_priority),
        mode=candidate.native_mode,
        fallback=0.0,
    )


def selected_jmdict_priority_difficulty(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    legacy = np.asarray(parts["jmdict_priority"], dtype=np.float32)
    pair_safe_raw = np.asarray(
        parts.get("jmdict_pair_safe_priority", legacy),
        dtype=np.float32,
    )
    pair_safe = np.where(np.isfinite(pair_safe_raw), pair_safe_raw, legacy).astype(np.float32)
    source = candidate.jmdict_priority_source
    blend = np.clip(float(candidate.jmdict_pair_safe_blend), 0.0, 1.0)
    if source == "legacy":
        return legacy
    if source == "pair_safe":
        return pair_safe
    if source == "pair_safe_blend":
        return np.clip(legacy + (blend * (pair_safe - legacy)), 0.0, 1.0).astype(np.float32)
    if source == "pair_safe_raise":
        return np.clip(legacy + (blend * np.maximum(pair_safe - legacy, 0.0)), 0.0, 1.0).astype(
            np.float32
        )
    raise ValueError(f"Unsupported JMDict priority source: {source}")


def base_family_rescue_score(
    candidate: SourceArbitrationCandidate,
    normalized: object,
    *,
    view: ComponentView,
) -> object:
    if (
        candidate.base_family_rescue_margin <= 0.0
        or candidate.base_family_rescue_strength <= 0.0
        or candidate.base_family_rescue_gate_mode == "none"
    ):
        return normalized
    if candidate.base_family_rescue_gate_mode != "score_gap":
        raise ValueError(
            f"Unsupported base-family rescue gate mode: {candidate.base_family_rescue_gate_mode}"
        )

    source_scores = np.asarray(normalized, dtype=np.float32)
    adjusted = source_scores.copy()
    best_by_lemma = _best_score_by_lemma(view.lemmas, source_scores)
    for index, lemma_value in enumerate(view.lemmas):
        lemma = str(lemma_value)
        base = _base_family_dictionary_form(lemma)
        if not base or base == lemma:
            continue
        base_score = best_by_lemma.get(base)
        if base_score is None or not np.isfinite(base_score):
            continue
        score = float(source_scores[index])
        gap = score - float(base_score)
        gate = _ramp_scalar(
            gap,
            lower=float(candidate.base_family_rescue_gap_lower),
            upper=float(candidate.base_family_rescue_gap_upper),
        )
        if gate <= 0.0:
            continue
        target = min(1.0, max(0.0, float(base_score) + candidate.base_family_rescue_margin))
        over_target = max(0.0, score - target)
        adjusted[index] = score - (
            float(candidate.base_family_rescue_strength) * gate * over_target
        )
    return np.clip(adjusted, 0.0, 1.0).astype(np.float32)


def _best_score_by_lemma(lemmas: object, scores: object) -> dict[str, float]:
    parsed_scores = np.asarray(scores, dtype=np.float32)
    best: dict[str, float] = {}
    for lemma_value, score_value in zip(lemmas, parsed_scores, strict=False):
        if not np.isfinite(float(score_value)):
            continue
        lemma = str(lemma_value)
        score = float(score_value)
        previous = best.get(lemma)
        if previous is None or score < previous:
            best[lemma] = score
    return best


@lru_cache(maxsize=100000)
def _base_family_dictionary_form(surface: str) -> str | None:
    try:
        sudachi, mode = _sudachi_base_family_analyzer()
        tokens = sudachi.tokenize(surface, mode)
    except Exception:
        return None
    content = [
        token
        for token in tokens
        if not "-".join(part for part in token.part_of_speech() if part != "*").startswith(
            BASE_FAMILY_FUNCTION_POS_PREFIXES
        )
    ]
    if len(content) != 1:
        return None
    base = str(content[0].dictionary_form())
    if not base or base == surface:
        return None
    return base


@lru_cache(maxsize=1)
def _sudachi_base_family_analyzer() -> tuple[object, object]:
    from sudachipy import dictionary, tokenizer

    return dictionary.Dictionary().create(), tokenizer.Tokenizer.SplitMode.C


def selected_jmdict_priority_commonness(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    selected = selected_jmdict_priority_difficulty(candidate, parts=parts)
    return np.clip(
        1.0 - np.asarray(selected, dtype=np.float32),
        0.0,
        1.0,
    ).astype(np.float32)


def selected_ordinary_gate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    gate_key = f"ordinary_gate_{candidate.ordinary_gate_mode}"
    if candidate.jmdict_priority_source == "legacy" and gate_key in parts:
        return parts[gate_key]
    frequency_ease = np.asarray(parts["ordinary_gate_frequency"], dtype=np.float32)
    priority_commonness = np.asarray(
        selected_jmdict_priority_commonness(candidate, parts=parts),
        dtype=np.float32,
    )
    pair_safe_priority_commonness = np.asarray(
        parts["ordinary_gate_pair_safe_priority"],
        dtype=np.float32,
    )
    pedagogical_ease = np.asarray(parts["ordinary_gate_pedagogical"], dtype=np.float32)
    ordinary_signal = np.asarray(
        parts.get("ordinary_vocab_protection_raw", parts["ordinary_protection"]),
        dtype=np.float32,
    )
    pair_safe_priority_commonness = np.asarray(
        parts["ordinary_gate_pair_safe_priority"],
        dtype=np.float32,
    )
    ordinary_max = _nan_reduce(
        (ordinary_signal, frequency_ease, priority_commonness),
        mode="max",
        fallback=0.0,
    )
    pair_safe_max = _nan_reduce(
        (ordinary_signal, frequency_ease, pair_safe_priority_commonness),
        mode="max",
        fallback=0.0,
    )
    if candidate.ordinary_gate_mode == "max":
        return ordinary_max
    if candidate.ordinary_gate_mode == "mean":
        return _nan_reduce(
            (ordinary_max, frequency_ease, priority_commonness, pedagogical_ease),
            mode="mean",
            fallback=0.0,
        )
    if candidate.ordinary_gate_mode == "frequency":
        return frequency_ease
    if candidate.ordinary_gate_mode == "priority":
        return priority_commonness
    if candidate.ordinary_gate_mode == "freq_priority":
        return _nan_reduce(
            (frequency_ease, priority_commonness),
            mode="mean",
            fallback=0.0,
        )
    if candidate.ordinary_gate_mode == "pedagogical":
        return pedagogical_ease
    if candidate.ordinary_gate_mode == "pair_safe_priority":
        return pair_safe_priority_commonness
    if candidate.ordinary_gate_mode == "freq_pair_safe_priority":
        return _nan_reduce(
            (frequency_ease, pair_safe_priority_commonness),
            mode="mean",
            fallback=0.0,
        )
    if candidate.ordinary_gate_mode == "pair_safe_mean":
        return _nan_reduce(
            (pair_safe_max, frequency_ease, pair_safe_priority_commonness, pedagogical_ease),
            mode="mean",
            fallback=0.0,
        )
    raise ValueError(f"Unsupported ordinary gate mode: {candidate.ordinary_gate_mode}")


def source_uses_pair_safe_priority(candidate: SourceArbitrationCandidate) -> bool:
    return (
        candidate.jmdict_priority_source != "legacy"
        and float(candidate.jmdict_pair_safe_blend) > 0.0
    )


def source_replaces_legacy_ordinary_gate(candidate: SourceArbitrationCandidate) -> bool:
    return source_uses_pair_safe_priority(candidate)


def legacy_jmdict_priority_is_effectively_selected(
    candidate: SourceArbitrationCandidate,
) -> bool:
    return not source_uses_pair_safe_priority(candidate)


def guarded_jmdict_priority_difficulty(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    jmdict_priority = np.asarray(
        selected_jmdict_priority_difficulty(candidate, parts=parts),
        dtype=np.float32,
    )
    guard = jmdict_priority_guard_gate(candidate, parts=parts)
    corpus_difficulty = _nan_reduce(
        (
            parts["native_frequency"],
            parts["tubelex_frequency"],
        ),
        mode="mean",
        fallback=1.0,
    )
    target = np.maximum(jmdict_priority, corpus_difficulty).astype(np.float32)
    adjustment = (
        float(candidate.jmdict_priority_guard_strength)
        * guard
        * np.maximum(target - jmdict_priority, 0.0)
    )
    return np.clip(jmdict_priority + adjustment, 0.0, 1.0).astype(np.float32)


def jmdict_priority_guard_gate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    mode = candidate.jmdict_priority_guard_mode
    if mode == "none":
        return np.zeros_like(np.asarray(parts["jmdict_priority"], dtype=np.float32))
    hard_form = np.asarray(parts["same_surface_hard_form_evidence"], dtype=np.float32)
    soft_form = np.asarray(parts["same_surface_soft_form_evidence"], dtype=np.float32)
    rare_reading = np.asarray(parts["rare_reading_form_strength"], dtype=np.float32)
    marked_form = _nan_reduce(
        (hard_form, 0.65 * soft_form, rare_reading),
        mode="max",
        fallback=0.0,
    )
    same_surface = np.asarray(parts["same_surface_priority_pollution_risk"], dtype=np.float32)
    formal_news = np.asarray(parts["jmdict_priority_formal_news_blocker"], dtype=np.float32)
    pair_leak = np.asarray(parts["jmdict_pair_priority_leak_risk"], dtype=np.float32)
    if mode == "marked":
        gate = _nan_reduce((marked_form, pair_leak), mode="max", fallback=0.0)
    elif mode == "marked_same_surface":
        gate = _nan_reduce((marked_form, same_surface, pair_leak), mode="max", fallback=0.0)
    elif mode == "marked_same_surface_news":
        gate = _nan_reduce(
            (marked_form, same_surface, formal_news, pair_leak),
            mode="max",
            fallback=0.0,
        )
    else:
        raise ValueError(f"Unsupported JMDict priority guard mode: {mode}")
    pedagogical_ease = np.asarray(parts["ordinary_gate_pedagogical"], dtype=np.float32)
    rescued_gate = gate * np.clip(
        1.0 - (float(candidate.jmdict_priority_guard_ped_rescue) * pedagogical_ease),
        0.0,
        1.0,
    )
    return _priority_guard_curve(
        rescued_gate,
        curve=candidate.jmdict_priority_guard_curve,
    )


def _priority_guard_curve(values: object, *, curve: str) -> object:
    clipped = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    if curve == "linear":
        return clipped
    if curve == "square":
        return np.square(clipped).astype(np.float32)
    if curve == "sqrt":
        return np.sqrt(clipped).astype(np.float32)
    if curve == "smoothstep":
        return (clipped * clipped * (3.0 - (2.0 * clipped))).astype(np.float32)
    raise ValueError(f"Unsupported JMDict priority guard curve: {curve}")


def pedagogical_values_for_candidate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.jlpt_ped_mode == "broad":
        ped = parts[f"ped_{candidate.ped_mode}"]
    elif candidate.jlpt_ped_mode == "exact_preferred":
        ped = parts[f"ped_exact_preferred_{candidate.ped_mode}"]
    elif candidate.jlpt_ped_mode == "effective":
        jlpt = jlpt_values_for_candidate(candidate, parts=parts)
        ped = _nan_reduce(
            (jlpt, parts["lesson_vocab_difficulty"]),
            mode=candidate.ped_mode,
            fallback=np.nan,
        )
    else:
        raise ValueError(f"Unsupported JLPT pedagogical mode: {candidate.jlpt_ped_mode}")
    return pair_leak_adjusted_pedagogical_values(candidate, ped, parts=parts)


def pair_leak_adjusted_pedagogical_values(
    candidate: SourceArbitrationCandidate,
    ped: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if (
        candidate.pair_leak_ped_adjustment_mode == "none"
        or candidate.pair_leak_ped_gate_mode == "none"
        or candidate.pair_leak_ped_strength <= 0.0
    ):
        return ped
    ped_values = np.asarray(ped, dtype=np.float32)
    finite = np.isfinite(ped_values)
    gate = _priority_guard_curve(
        pair_leak_pedagogical_gate(candidate, parts=parts),
        curve=candidate.pair_leak_ped_curve,
    )
    strength = np.clip(float(candidate.pair_leak_ped_strength) * gate, 0.0, 1.0)
    mode = candidate.pair_leak_ped_adjustment_mode
    if mode == "raise":
        adjusted = ped_values + strength
    elif mode == "floor":
        target = np.maximum(ped_values, float(candidate.pair_leak_ped_floor))
        adjusted = ped_values + (strength * np.maximum(target - ped_values, 0.0))
    elif mode in {"raise_toward_native", "raise_toward_pair_native"}:
        if mode == "raise_toward_native":
            target = np.asarray(parts["native_mean"], dtype=np.float32)
        else:
            target = pair_safe_native_target(parts)
        adjusted = ped_values + (strength * np.maximum(target - ped_values, 0.0))
    else:
        raise ValueError(f"Unsupported pair-leak pedagogical adjustment mode: {mode}")
    return np.where(finite, np.clip(adjusted, 0.0, 1.0), ped_values).astype(np.float32)


def pair_leak_pedagogical_gate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    pair_leak = np.asarray(parts["jmdict_pair_priority_leak_risk"], dtype=np.float32)
    missing = np.asarray(parts["jmdict_pair_missing_reading_risk"], dtype=np.float32)
    marked_not_safe = np.asarray(
        parts["jmdict_pair_marked_form_not_safe_risk"],
        dtype=np.float32,
    )
    surface_only = np.asarray(
        parts["jmdict_pair_surface_only_multi_reading_risk"],
        dtype=np.float32,
    )
    family_only = np.asarray(parts["pedagogical_family_only_known"], dtype=np.float32)
    ped_known = np.asarray(parts["ped_conf"], dtype=np.float32)
    same_surface_family = np.asarray(
        parts["same_surface_pedagogical_family_only_risk"],
        dtype=np.float32,
    )
    alt_pair_risk = _nan_reduce(
        (missing, marked_not_safe, surface_only),
        mode="max",
        fallback=0.0,
    )
    mode = candidate.pair_leak_ped_gate_mode
    if mode == "pair_leak_ped_known":
        gate = pair_leak * ped_known
    elif mode == "pair_leak_family_only":
        gate = pair_leak * family_only
    elif mode == "pair_alt_family_only":
        gate = alt_pair_risk * family_only
    elif mode == "pair_missing_family_only":
        gate = missing * family_only
    elif mode == "pair_surface_only_family_only":
        gate = surface_only * family_only
    elif mode == "pair_leak_or_same_surface_family":
        gate = _nan_reduce(
            (pair_leak * family_only, same_surface_family),
            mode="max",
            fallback=0.0,
        )
    else:
        raise ValueError(
            f"Unsupported pair-leak pedagogical gate mode: {candidate.pair_leak_ped_gate_mode}"
        )
    return np.clip(gate, 0.0, 1.0).astype(np.float32)


def pair_safe_native_target(parts: Mapping[str, object]) -> object:
    pair_safe_priority = np.asarray(parts["jmdict_pair_safe_priority"], dtype=np.float32)
    legacy_priority = np.asarray(parts["jmdict_priority"], dtype=np.float32)
    pair_safe_or_legacy = np.where(
        np.isfinite(pair_safe_priority),
        pair_safe_priority,
        legacy_priority,
    ).astype(np.float32)
    return _nan_reduce(
        (
            parts["native_frequency"],
            parts["tubelex_frequency"],
            pair_safe_or_legacy,
        ),
        mode="mean",
        fallback=0.0,
    )


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


def _is_cjk_ideograph(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def family_parts(view: ComponentView) -> dict[str, object]:
    frequency = np.nan_to_num(view.frequency, nan=0.0).astype(np.float32)
    surface_kanji_count = np.asarray(
        [
            sum(1 for character in str(lemma) if _is_cjk_ideograph(character))
            for lemma in view.lemmas
        ],
        dtype=np.float32,
    )
    jlpt = view.value("jlpt_vocab_difficulty")
    jlpt_exact = view.value("jlpt_vocab_effective_exact_difficulty", fill=np.nan)
    if "jlpt_vocab_effective_exact_difficulty" not in view.name_to_index:
        jlpt_exact = view.value("jlpt_vocab_exact_difficulty", fill=np.nan)
    jlpt_exact_known_for_ped = view.value("jlpt_vocab_effective_exact_known", fill=0.0)
    if "jlpt_vocab_effective_exact_known" not in view.name_to_index:
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
    tubelex_count_difficulty = view.value("tubelex_count_difficulty", fill=np.nan)
    tubelex_known = view.value("tubelex_frequency_known", fill=0.0)
    jmdict_priority = view.value("jmdict_priority")
    jmdict_pair_safe_priority = view.value("jmdict_pair_safe_priority", fill=np.nan)
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
    ordinary_signal = view.value("ordinary_vocab_protection", fill=np.nan)
    frequency_ease = view.value("frequency_ease", fill=np.nan)
    jmdict_priority_commonness = 1.0 - np.nan_to_num(jmdict_priority, nan=1.0)
    jmdict_pair_safe_commonness = np.nan_to_num(
        view.value("jmdict_pair_safe_commonness", fill=np.nan),
        nan=0.0,
    ).astype(np.float32)
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
        (ordinary_signal, frequency_ease, jmdict_priority_commonness),
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
    ordinary_freq_pair_safe_priority = _nan_reduce(
        (frequency_ease, jmdict_pair_safe_commonness),
        mode="mean",
        fallback=0.0,
    )
    ordinary_pair_safe_mean = _nan_reduce(
        (
            np.nan_to_num(ordinary_signal, nan=0.0),
            frequency_ease,
            jmdict_pair_safe_commonness,
            pedagogical_ease,
        ),
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
    jlpt_exact_signal_available = (
        1.0
        if (
            "jlpt_vocab_effective_exact_known" in view.name_to_index
            or "jlpt_vocab_exact_known" in view.name_to_index
        )
        else 0.0
    )
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
    same_surface_pedagogical_family_only_unprotected_exact_risk = (
        np.asarray(same_surface_parts["same_surface_rare_pollution_risk"], dtype=np.float32)
        * pedagogical_family_only_known
        * np.clip(1.0 - np.asarray(jlpt_exact_known_for_ped, dtype=np.float32), 0.0, 1.0)
    ).astype(np.float32)
    same_surface_hard_form_evidence = _nan_reduce(
        (
            view.value("jmdict_reading_form_marked_risk", fill=0.0),
            view.value("jmdict_reading_form_marked_flag", fill=0.0),
            view.value("jmdict_reading_restricted_risk", fill=0.0),
            view.value("jmdict_reading_restricted_flag", fill=0.0),
            view.value("jmdict_search_only_form_risk", fill=0.0),
        ),
        mode="max",
        fallback=0.0,
    )
    same_surface_soft_form_evidence = _nan_reduce(
        (
            view.value("jmdict_kana_preferred_risk", fill=0.0),
            view.value("jmdict_marked_usage_risk", fill=0.0),
            view.value("jmdict_kanji_form_marked_risk", fill=0.0),
            view.value("jmdict_no_kanji_reading_risk", fill=0.0),
        ),
        mode="max",
        fallback=0.0,
    )
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
    kango = view.value("wtype_kango_risk", fill=0.0)
    wago_ease = view.value("wtype_wago_ease", fill=0.0)
    mixed = view.value("wtype_mixed_risk", fill=0.0)
    rescue_kanji_burden = _nan_reduce(
        (
            view.value("kanji_burden", fill=np.nan),
            view.value("max_written_form_burden", fill=np.nan),
            view.value("rare_wago_max_kanji_burden", fill=np.nan),
            view.value("kango_uncommon_kanji_burden", fill=np.nan),
        ),
        mode="max",
        fallback=0.0,
    )
    rescue_marked_usage = _nan_reduce(
        (
            view.value("jmdict_marked_usage_risk", fill=np.nan),
            view.value("rare_wago_marked_usage_risk", fill=np.nan),
            view.value("jmdict_register_marked_risk", fill=np.nan),
        ),
        mode="max",
        fallback=0.0,
    )
    gairaigo_non_english = view.value("gairaigo_non_english_source_risk", fill=0.0)
    gairaigo_domain = view.value("gairaigo_domain_source_risk", fill=0.0)
    gairaigo_marked = view.value("gairaigo_marked_source_risk", fill=0.0)
    gairaigo_english_ease = view.value("gairaigo_english_source_ease", fill=0.0)
    jlpt_raw_exact_known = view.value("jlpt_vocab_exact_known", fill=0.0)
    jlpt_exact_known = view.value("jlpt_vocab_effective_exact_known", fill=np.nan)
    if "jlpt_vocab_effective_exact_known" not in view.name_to_index:
        jlpt_exact_known = view.value("jlpt_vocab_exact_known", fill=np.nan)
    jlpt_exact_known = np.nan_to_num(jlpt_exact_known, nan=jlpt_known).astype(np.float32)
    jlpt_difficulty = view.value("jlpt_vocab_difficulty", fill=np.nan)
    jlpt_exact_difficulty = view.value("jlpt_vocab_effective_exact_difficulty", fill=np.nan)
    if "jlpt_vocab_effective_exact_difficulty" not in view.name_to_index:
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
    jmdict_news_priority_commonness = view.value(
        "jmdict_news_priority_commonness",
        fill=0.0,
    )
    formal_news_blocker = (
        np.asarray(jmdict_news_priority_commonness, dtype=np.float32)
        * np.asarray(kango, dtype=np.float32)
        * np.sqrt(
            np.clip(_ramp(frequency, lower=0.82, upper=0.96), 0.0, 1.0)
            * np.clip(
                _ramp(tubelex_count_difficulty, lower=0.74, upper=0.90),
                0.0,
                1.0,
            )
        )
    ).astype(np.float32)
    return {
        "ped_min": ped_min,
        "ped_mean": ped_mean,
        "ped_exact_preferred_min": ped_exact_preferred_min,
        "ped_exact_preferred_mean": ped_exact_preferred_mean,
        "lesson_vocab_difficulty": lesson,
        "lesson_vocab_known": lesson_known,
        "native_frequency": frequency,
        "tubelex_frequency": tubelex,
        "tubelex_count_difficulty": tubelex_count_difficulty,
        "tubelex_frequency_known": tubelex_known,
        "jmdict_priority": jmdict_priority,
        "jmdict_priority_commonness": jmdict_priority_commonness,
        "jmdict_pair_safe_priority": jmdict_pair_safe_priority,
        "jmdict_pair_safe_commonness": jmdict_pair_safe_commonness,
        "jmdict_pair_priority_leak_risk": view.value(
            "jmdict_pair_priority_leak_risk",
            fill=0.0,
        ),
        "jmdict_pair_missing_reading_risk": view.value(
            "jmdict_pair_missing_reading_risk",
            fill=0.0,
        ),
        "jmdict_pair_marked_form_not_safe_risk": view.value(
            "jmdict_pair_marked_form_not_safe_risk",
            fill=0.0,
        ),
        "jmdict_pair_surface_only_multi_reading_risk": view.value(
            "jmdict_pair_surface_only_multi_reading_risk",
            fill=0.0,
        ),
        "jmdict_priority_formal_news_blocker": formal_news_blocker,
        "cross_corpus_rescue_surface_single_kanji": (surface_kanji_count == 1.0).astype(np.float32),
        "cross_corpus_rescue_kanji_burden": rescue_kanji_burden,
        "cross_corpus_rescue_max_written_form_burden": view.value(
            "max_written_form_burden",
            fill=0.0,
        ),
        "cross_corpus_rescue_marked_usage": rescue_marked_usage,
        "pos_common_noun_gate": view.value("pos_common_noun_gate", fill=0.0),
        "pos_plain_verb_gate": view.value("pos_plain_verb_gate", fill=0.0),
        "pos_adjective_gate": view.value("pos_adjective_gate", fill=0.0),
        "wtype_kango_risk": kango,
        "wtype_wago_ease": wago_ease,
        "wtype_mixed_risk": mixed,
        "wtype_gairaigo_risk": gairaigo,
        "native_mean": native_mean,
        "native_min": native_min,
        "ped_conf": ped_conf,
        "native_conf": native_conf,
        "ordinary_vocab_protection_raw": np.nan_to_num(
            ordinary_signal,
            nan=0.0,
        ).astype(np.float32),
        "ordinary_protection": ordinary_protection,
        "ordinary_gate_max": ordinary_protection,
        "ordinary_gate_mean": ordinary_mean,
        "ordinary_gate_frequency": np.nan_to_num(frequency_ease, nan=0.0).astype(np.float32),
        "ordinary_gate_priority": jmdict_priority_commonness.astype(np.float32),
        "ordinary_gate_pair_safe_priority": jmdict_pair_safe_commonness.astype(np.float32),
        "ordinary_gate_freq_priority": ordinary_freq_priority,
        "ordinary_gate_freq_pair_safe_priority": ordinary_freq_pair_safe_priority,
        "ordinary_gate_pair_safe_mean": ordinary_pair_safe_mean,
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
        "acronym_signal_known": view.value("acronym_signal_known", fill=0.0),
        "jlpt_vocab_known": jlpt_known,
        "jlpt_vocab_surface_known": jlpt_surface_known,
        "jlpt_vocab_exact_known": jlpt_exact_known,
        "jlpt_vocab_raw_exact_known": jlpt_raw_exact_known,
        "jlpt_vocab_normalized_exact_known": view.value(
            "jlpt_vocab_normalized_exact_known",
            fill=0.0,
        ),
        "jlpt_vocab_effective_exact_known": jlpt_exact_known,
        "jlpt_vocab_family_only_known": jlpt_family_only_known,
        "pedagogical_family_only_known": pedagogical_family_only_known,
        "jlpt_vocab_difficulty": jlpt_difficulty,
        "jlpt_vocab_exact_difficulty": jlpt_exact_difficulty,
        "jlpt_vocab_exact_gap": (
            np.nan_to_num(jlpt_exact_difficulty - jlpt_difficulty, nan=0.0)
        ).astype(np.float32),
        "same_surface_pedagogical_family_only_risk": (same_surface_pedagogical_family_only_risk),
        "same_surface_pedagogical_family_only_unprotected_exact_risk": (
            same_surface_pedagogical_family_only_unprotected_exact_risk
        ),
        "same_surface_hard_form_evidence": same_surface_hard_form_evidence,
        "same_surface_soft_form_evidence": same_surface_soft_form_evidence,
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
    exact_commonness = same_surface_exact_commonness(view)
    exact_weakness = _ramp(1.0 - exact_commonness, lower=0.25, upper=0.75)
    source_rank_gap_risk = (normal_vocab * alt_gate * source_gate * rank_gate * common_gate).astype(
        np.float32
    )
    priority_pollution_risk = (
        normal_vocab * alt_gate * rank_gate * common_gate * exact_weakness
    ).astype(np.float32)
    unranked_priority_pollution_risk = (priority_pollution_risk * unranked_vs_ranked).astype(
        np.float32
    )
    rare_gate = np.maximum(unranked_vs_ranked, _ramp(rare_strength, lower=0.20, upper=0.50))
    rare_source_rank_gap_risk = (source_rank_gap_risk * rare_gate).astype(np.float32)
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
        "same_surface_priority_pollution_risk": priority_pollution_risk,
        "same_surface_unranked_priority_pollution_risk": (unranked_priority_pollution_risk),
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
    ordinary = np.asarray(selected_ordinary_gate(candidate, parts=parts), dtype=np.float32)
    ordinary = guarded_ordinary_gate(candidate, ordinary, parts=parts)
    ordinary = _ordinary_cap_curve(
        ordinary,
        curve=candidate.ordinary_gate_curve,
    )
    exception = _ordinary_cap_curve(
        ordinary_cap_exception_gate(candidate, parts=parts),
        curve=candidate.ordinary_exception_curve,
    )
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


def ordinary_cap_exception_gate(
    candidate: SourceArbitrationCandidate,
    *,
    parts: Mapping[str, object],
) -> object:
    reading = np.asarray(parts["reading_inheritance_risk"], dtype=np.float32)
    tail = np.asarray(parts["tail_floor_guard"], dtype=np.float32)
    current = np.maximum(reading, tail).astype(np.float32)
    mode = candidate.ordinary_exception_mode
    if mode == "current":
        return current
    pair_leak = np.asarray(parts["jmdict_pair_priority_leak_risk"], dtype=np.float32)
    if mode == "current_pair_leak":
        return np.maximum(current, pair_leak).astype(np.float32)
    marked_tail = _nan_reduce(
        (
            tail,
            parts["same_surface_hard_form_evidence"],
            0.65 * np.asarray(parts["same_surface_soft_form_evidence"], dtype=np.float32),
            parts["rare_reading_form_strength"],
            parts["cross_corpus_rescue_marked_usage"],
        ),
        mode="max",
        fallback=0.0,
    )
    if mode == "marked_tail":
        return marked_tail
    if mode == "broad_hard":
        kanji_burden = _ramp(
            np.asarray(parts["cross_corpus_rescue_kanji_burden"], dtype=np.float32),
            lower=0.78,
            upper=0.94,
        )
        return _nan_reduce(
            (
                current,
                pair_leak,
                marked_tail,
                parts["jmdict_pair_missing_reading_risk"],
                parts["jmdict_pair_marked_form_not_safe_risk"],
                parts["jmdict_pair_surface_only_multi_reading_risk"],
                kanji_burden,
            ),
            mode="max",
            fallback=0.0,
        )
    raise ValueError(f"Unsupported ordinary exception mode: {mode}")


def _ordinary_cap_curve(values: object, *, curve: str) -> object:
    clipped = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    if curve == "linear":
        return clipped
    if curve == "sqrt":
        return np.sqrt(clipped).astype(np.float32)
    if curve == "pow1p5":
        return np.power(clipped, 1.5).astype(np.float32)
    if curve == "square":
        return np.square(clipped).astype(np.float32)
    if curve == "smoothstep":
        return (clipped * clipped * (3.0 - (2.0 * clipped))).astype(np.float32)
    raise ValueError(f"Unsupported ordinary cap curve: {curve}")


def guarded_ordinary_gate(
    candidate: SourceArbitrationCandidate,
    ordinary: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if (
        candidate.jmdict_priority_guard_ordinary_strength <= 0.0
        or candidate.jmdict_priority_guard_mode == "none"
    ):
        return ordinary
    gate = jmdict_priority_guard_gate(candidate, parts=parts)
    priority_commonness = np.asarray(
        selected_jmdict_priority_commonness(candidate, parts=parts),
        dtype=np.float32,
    )
    pair_safe_priority_commonness = np.asarray(
        parts["ordinary_gate_pair_safe_priority"],
        dtype=np.float32,
    )
    guarded_priority = priority_commonness * np.clip(
        1.0 - (float(candidate.jmdict_priority_guard_ordinary_strength) * gate),
        0.0,
        1.0,
    )
    frequency_ease = np.asarray(parts["ordinary_gate_frequency"], dtype=np.float32)
    pedagogical_ease = np.asarray(parts["ordinary_gate_pedagogical"], dtype=np.float32)
    guarded_max = _nan_reduce(
        (frequency_ease, guarded_priority, pedagogical_ease),
        mode="max",
        fallback=0.0,
    )
    guarded_pair_safe_max = _nan_reduce(
        (frequency_ease, pair_safe_priority_commonness, pedagogical_ease),
        mode="max",
        fallback=0.0,
    )
    if candidate.ordinary_gate_mode == "max":
        return guarded_max
    if candidate.ordinary_gate_mode == "mean":
        return _nan_reduce(
            (guarded_max, frequency_ease, guarded_priority, pedagogical_ease),
            mode="mean",
            fallback=0.0,
        )
    if candidate.ordinary_gate_mode == "frequency":
        return frequency_ease
    if candidate.ordinary_gate_mode == "priority":
        return guarded_priority
    if candidate.ordinary_gate_mode == "freq_priority":
        return _nan_reduce(
            (frequency_ease, guarded_priority),
            mode="mean",
            fallback=0.0,
        )
    if candidate.ordinary_gate_mode == "pedagogical":
        return pedagogical_ease
    if candidate.ordinary_gate_mode == "pair_safe_priority":
        return pair_safe_priority_commonness
    if candidate.ordinary_gate_mode == "freq_pair_safe_priority":
        return _nan_reduce(
            (frequency_ease, pair_safe_priority_commonness),
            mode="mean",
            fallback=0.0,
        )
    if candidate.ordinary_gate_mode == "pair_safe_mean":
        return _nan_reduce(
            (
                guarded_pair_safe_max,
                frequency_ease,
                pair_safe_priority_commonness,
                pedagogical_ease,
            ),
            mode="mean",
            fallback=0.0,
        )
    return ordinary


def cross_corpus_common_rescue_score(
    candidate: SourceArbitrationCandidate,
    raw: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.cross_corpus_rescue_cap <= 0.0 or candidate.cross_corpus_rescue_mode == "none":
        return raw
    bccwj = np.asarray(parts["native_frequency"], dtype=np.float32)
    tubelex = np.asarray(parts["tubelex_count_difficulty"], dtype=np.float32)
    tubelex_known = np.asarray(parts["tubelex_frequency_known"], dtype=np.float32)
    bccwj_gate = 1.0 - _ramp(
        bccwj,
        lower=float(candidate.cross_corpus_rescue_bccwj_lower),
        upper=float(candidate.cross_corpus_rescue_bccwj_upper),
    )
    tubelex_gate = 1.0 - _ramp(
        np.nan_to_num(tubelex, nan=1.0),
        lower=float(candidate.cross_corpus_rescue_tubelex_lower),
        upper=float(candidate.cross_corpus_rescue_tubelex_upper),
    )
    commonness_gate = np.sqrt(
        np.clip(bccwj_gate, 0.0, 1.0) * np.clip(tubelex_gate, 0.0, 1.0)
    ).astype(np.float32)

    pedagogical_known = np.maximum(
        np.asarray(parts["jlpt_vocab_known"], dtype=np.float32),
        np.asarray(parts["lesson_vocab_known"], dtype=np.float32),
    )
    no_pedagogical_gate = np.clip(1.0 - pedagogical_known, 0.0, 1.0)
    normal_gate = np.clip(
        1.0 - np.asarray(parts["candidate_deprioritized"], dtype=np.float32),
        0.0,
        1.0,
    )
    non_acronym_gate = np.clip(
        1.0 - np.asarray(parts["acronym_signal_known"], dtype=np.float32),
        0.0,
        1.0,
    )
    normal_rescue_gate = (
        no_pedagogical_gate * normal_gate * non_acronym_gate * np.clip(tubelex_known, 0.0, 1.0)
    ).astype(np.float32)
    broad_gate = (commonness_gate * normal_rescue_gate).astype(np.float32)
    if candidate.cross_corpus_rescue_gate_mode == "no_ped_normal":
        gate = broad_gate
    elif candidate.cross_corpus_rescue_gate_mode == "typed_nonkango_life":
        gate = _cross_corpus_typed_rescue_gate(
            candidate,
            broad_gate=broad_gate,
            normal_rescue_gate=normal_rescue_gate,
            parts=parts,
        )
    else:
        raise ValueError(
            f"Unsupported cross-corpus rescue gate mode: {candidate.cross_corpus_rescue_gate_mode}"
        )
    gate = _cross_corpus_rescue_curve(gate, curve=candidate.cross_corpus_rescue_curve)

    cap = float(candidate.cross_corpus_rescue_cap) + (
        (1.0 - float(candidate.cross_corpus_rescue_cap)) * (1.0 - gate)
    )
    raw_values = np.asarray(raw, dtype=np.float32)
    over_cap = np.maximum(raw_values - cap, 0.0)
    if candidate.cross_corpus_rescue_mode == "hard":
        return np.minimum(raw_values, cap).astype(np.float32)
    if candidate.cross_corpus_rescue_mode == "soft":
        return (raw_values - (float(candidate.cross_corpus_rescue_strength) * over_cap)).astype(
            np.float32
        )
    raise ValueError(f"Unsupported cross-corpus rescue mode: {candidate.cross_corpus_rescue_mode}")


def _cross_corpus_typed_rescue_gate(
    candidate: SourceArbitrationCandidate,
    *,
    broad_gate: object,
    normal_rescue_gate: object,
    parts: Mapping[str, object],
) -> object:
    kango_gate = np.clip(
        1.0 - np.asarray(parts["wtype_kango_risk"], dtype=np.float32),
        0.0,
        1.0,
    )
    high_burden_block = np.maximum(
        _ramp(
            np.asarray(parts["cross_corpus_rescue_kanji_burden"], dtype=np.float32),
            lower=float(candidate.cross_corpus_rescue_burden_lower),
            upper=float(candidate.cross_corpus_rescue_burden_upper),
        ),
        np.asarray(parts["cross_corpus_rescue_surface_single_kanji"], dtype=np.float32)
        * _ramp(
            np.asarray(
                parts["cross_corpus_rescue_max_written_form_burden"],
                dtype=np.float32,
            ),
            lower=float(candidate.cross_corpus_rescue_single_kanji_lower),
            upper=float(candidate.cross_corpus_rescue_single_kanji_upper),
        ),
    )
    safe_shape_gate = (kango_gate * np.clip(1.0 - high_burden_block, 0.0, 1.0)).astype(np.float32)
    typed_life_gate = _nan_reduce(
        (
            parts["wtype_mixed_risk"],
            parts["wtype_gairaigo_risk"],
            parts["pos_common_noun_gate"],
            parts["pos_plain_verb_gate"],
            parts["pos_adjective_gate"],
        ),
        mode="max",
        fallback=0.0,
    )
    broad_life_gate = _nan_reduce(
        (
            parts["wtype_wago_ease"],
            parts["wtype_mixed_risk"],
            parts["wtype_gairaigo_risk"],
            0.8 * np.asarray(parts["pos_common_noun_gate"], dtype=np.float32),
            0.8 * np.asarray(parts["pos_plain_verb_gate"], dtype=np.float32),
            0.8 * np.asarray(parts["pos_adjective_gate"], dtype=np.float32),
        ),
        mode="max",
        fallback=0.0,
    )
    base_gate = (
        np.asarray(broad_gate, dtype=np.float32)
        * safe_shape_gate
        * np.clip(np.asarray(broad_life_gate, dtype=np.float32), 0.0, 1.0)
    ).astype(np.float32)

    boost_bccwj_gate = 1.0 - _ramp(
        np.asarray(parts["native_frequency"], dtype=np.float32),
        lower=float(candidate.cross_corpus_rescue_boost_bccwj_lower),
        upper=float(candidate.cross_corpus_rescue_boost_bccwj_upper),
    )
    boost_tubelex_gate = 1.0 - _ramp(
        np.nan_to_num(
            np.asarray(parts["tubelex_count_difficulty"], dtype=np.float32),
            nan=1.0,
        ),
        lower=float(candidate.cross_corpus_rescue_boost_tubelex_lower),
        upper=float(candidate.cross_corpus_rescue_boost_tubelex_upper),
    )
    strong_evidence = np.minimum(
        np.clip(boost_bccwj_gate, 0.0, 1.0),
        np.clip(boost_tubelex_gate, 0.0, 1.0),
    )
    marked_gate = np.clip(
        1.0 - np.asarray(parts["cross_corpus_rescue_marked_usage"], dtype=np.float32),
        0.0,
        1.0,
    )
    boost_gate = (
        float(candidate.cross_corpus_rescue_boost_strength)
        * strong_evidence
        * np.asarray(normal_rescue_gate, dtype=np.float32)
        * safe_shape_gate
        * np.clip(np.asarray(typed_life_gate, dtype=np.float32), 0.0, 1.0)
        * marked_gate
    ).astype(np.float32)
    return np.maximum(base_gate, boost_gate).astype(np.float32)


def _cross_corpus_rescue_curve(values: object, *, curve: str) -> object:
    clipped = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    if curve == "linear":
        return clipped
    if curve == "square":
        return np.square(clipped).astype(np.float32)
    if curve == "sqrt":
        return np.sqrt(clipped).astype(np.float32)
    if curve == "smoothstep":
        return (clipped * clipped * (3.0 - (2.0 * clipped))).astype(np.float32)
    raise ValueError(f"Unsupported cross-corpus rescue curve: {curve}")


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
    if (
        candidate.same_surface_gradient_high_floor > 0.0
        and candidate.same_surface_gradient_mode != "none"
    ):
        adjusted = _same_surface_gradient_floor_score(candidate, adjusted, parts=parts)
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
        "pedagogical_family_only_rare_pollution_unprotected_exact": (
            "same_surface_pedagogical_family_only_unprotected_exact_risk"
        ),
        "priority_pollution": "same_surface_priority_pollution_risk",
        "unranked_priority_pollution": "same_surface_unranked_priority_pollution_risk",
    }
    risk_key = risk_key_by_mode.get(mode)
    if risk_key is None:
        raise ValueError(f"Unsupported same-surface floor mode: {mode}")
    risk = np.asarray(parts[risk_key], dtype=np.float32)
    floor_values = float(floor) * np.clip(risk, 0.0, 1.0)
    return np.maximum(np.asarray(raw, dtype=np.float32), floor_values).astype(np.float32)


def _same_surface_gradient_floor_score(
    candidate: SourceArbitrationCandidate,
    raw: object,
    *,
    parts: Mapping[str, object],
) -> object:
    if candidate.same_surface_gradient_mode != "exact_protected_evidence":
        raise ValueError(
            f"Unsupported same-surface gradient mode: {candidate.same_surface_gradient_mode}"
        )
    low_floor = float(candidate.same_surface_gradient_low_floor)
    high_floor = float(candidate.same_surface_gradient_high_floor)
    if high_floor < low_floor:
        raise ValueError(
            "same_surface_gradient_high_floor must be >= same_surface_gradient_low_floor"
        )
    base_risk = np.clip(
        np.asarray(
            parts["same_surface_pedagogical_family_only_unprotected_exact_risk"],
            dtype=np.float32,
        ),
        0.0,
        1.0,
    )
    exact_commonness = np.clip(
        np.asarray(parts["same_surface_exact_commonness"], dtype=np.float32),
        0.0,
        1.0,
    )
    commonness_cap = float(candidate.same_surface_gradient_commonness_cap)
    if commonness_cap <= 0.0:
        exact_rarity_pressure = np.ones_like(exact_commonness, dtype=np.float32)
    else:
        exact_rarity_pressure = 1.0 - _ramp(
            exact_commonness,
            lower=0.0,
            upper=commonness_cap,
        )
    hard_evidence = np.clip(
        np.asarray(parts["same_surface_hard_form_evidence"], dtype=np.float32),
        0.0,
        1.0,
    )
    soft_evidence = np.clip(
        np.asarray(parts["same_surface_soft_form_evidence"], dtype=np.float32),
        0.0,
        1.0,
    )
    marked_pressure = np.maximum(
        hard_evidence,
        float(candidate.same_surface_gradient_marked_boost) * soft_evidence,
    ).astype(np.float32)
    evidence_pressure = np.maximum(exact_rarity_pressure, marked_pressure).astype(np.float32)
    lesson_rescue = (
        float(candidate.same_surface_gradient_lesson_rescue)
        * np.asarray(parts["lesson_vocab_known"], dtype=np.float32)
        * np.clip(1.0 - hard_evidence, 0.0, 1.0)
    )
    severity = base_risk * evidence_pressure * np.clip(1.0 - lesson_rescue, 0.0, 1.0)
    curved_severity = _same_surface_gradient_curve(
        severity,
        curve=candidate.same_surface_gradient_curve,
    )
    floor_values = (low_floor * base_risk) + ((high_floor - low_floor) * curved_severity)
    return np.maximum(np.asarray(raw, dtype=np.float32), floor_values).astype(np.float32)


def _same_surface_gradient_curve(values: object, *, curve: str) -> object:
    clipped = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    if curve == "linear":
        return clipped
    if curve == "square":
        return np.square(clipped).astype(np.float32)
    if curve == "sqrt":
        return np.sqrt(clipped).astype(np.float32)
    if curve == "smoothstep":
        return (clipped * clipped * (3.0 - (2.0 * clipped))).astype(np.float32)
    raise ValueError(f"Unsupported same-surface gradient curve: {curve}")


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
        "same_surface_exact_protected_floor_refine",
        "same_surface_gradient_floor_refine",
        "jmdict_priority_guard_refine",
        "jmdict_pair_priority_source_refine",
        "fixed_data_current_ablation",
        "pair_leak_ped_trust_refine",
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
            "priority_pollution_positive": int(
                (
                    np.asarray(
                        parts["same_surface_priority_pollution_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
            ),
            "unranked_priority_pollution_positive": int(
                (
                    np.asarray(
                        parts["same_surface_unranked_priority_pollution_risk"],
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
            "pedagogical_family_only_unprotected_exact_positive": int(
                (
                    np.asarray(
                        parts["same_surface_pedagogical_family_only_unprotected_exact_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
            ),
            "jlpt_family_only_positive": int(
                (np.asarray(parts["jlpt_vocab_family_only_known"], dtype=np.float32) > 0.0).sum()
            ),
            "same_surface_hard_form_evidence_positive": int(
                (np.asarray(parts["same_surface_hard_form_evidence"], dtype=np.float32) > 0.0).sum()
            ),
            "same_surface_soft_form_evidence_positive": int(
                (np.asarray(parts["same_surface_soft_form_evidence"], dtype=np.float32) > 0.0).sum()
            ),
            "jmdict_pair_priority_leak_positive": int(
                (np.asarray(parts["jmdict_pair_priority_leak_risk"], dtype=np.float32) > 0.0).sum()
            ),
            "jmdict_pair_missing_reading_positive": int(
                (
                    np.asarray(parts["jmdict_pair_missing_reading_risk"], dtype=np.float32) > 0.0
                ).sum()
            ),
            "jmdict_pair_surface_only_multi_reading_positive": int(
                (
                    np.asarray(
                        parts["jmdict_pair_surface_only_multi_reading_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
            ),
            "jmdict_pair_marked_form_not_safe_positive": int(
                (
                    np.asarray(
                        parts["jmdict_pair_marked_form_not_safe_risk"],
                        dtype=np.float32,
                    )
                    > 0.0
                ).sum()
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
        and params.get("jmdict_priority_guard_mode", "none") == "none"
        and (_optional_float(params.get("jmdict_priority_guard_strength")) or 0.0) <= 0.0
        and params.get("jmdict_priority_source", "legacy") == "legacy"
        and params.get("pair_leak_ped_gate_mode", "none") == "none"
        and params.get("pair_leak_ped_adjustment_mode", "none") == "none"
        and (_optional_float(params.get("pair_leak_ped_strength")) or 0.0) <= 0.0
    )


def _has_same_surface_floor_effect(params: Mapping[str, object]) -> bool:
    return (
        params.get("same_surface_floor_mode", "none") != "none"
        or params.get("same_surface_secondary_floor_mode", "none") != "none"
        or params.get("same_surface_gradient_mode", "none") != "none"
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
            or params.get("jmdict_priority_guard_mode", "none") != "none"
            or (_optional_float(params.get("jmdict_priority_guard_strength")) or 0.0) > 0.0
            or params.get("jmdict_priority_source", "legacy") != "legacy"
            or params.get("pair_leak_ped_gate_mode", "none") != "none"
            or params.get("pair_leak_ped_adjustment_mode", "none") != "none"
            or (_optional_float(params.get("pair_leak_ped_strength")) or 0.0) > 0.0
            or params.get("base_family_rescue_gate_mode", "none") != "none"
            or (_optional_float(params.get("base_family_rescue_strength")) or 0.0) > 0.0
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
        candidate.ordinary_gate_curve,
        candidate.ordinary_exception_mode,
        candidate.ordinary_exception_curve,
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
        candidate.jmdict_priority_guard_mode,
        candidate.jmdict_priority_guard_strength,
        candidate.jmdict_priority_guard_ordinary_strength,
        candidate.jmdict_priority_guard_curve,
        candidate.jmdict_priority_guard_ped_rescue,
        candidate.jmdict_priority_source,
        candidate.jmdict_pair_safe_blend,
        candidate.pair_leak_ped_gate_mode,
        candidate.pair_leak_ped_adjustment_mode,
        candidate.pair_leak_ped_strength,
        candidate.pair_leak_ped_floor,
        candidate.pair_leak_ped_curve,
        candidate.base_family_rescue_margin,
        candidate.base_family_rescue_strength,
        candidate.base_family_rescue_gate_mode,
        candidate.base_family_rescue_gap_lower,
        candidate.base_family_rescue_gap_upper,
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
        "same_surface_priority_pollution_risk": _rounded(
            float(parts["same_surface_priority_pollution_risk"][index])
        ),
        "same_surface_unranked_priority_pollution_risk": _rounded(
            float(parts["same_surface_unranked_priority_pollution_risk"][index])
        ),
        "same_surface_pedagogical_family_only_risk": _rounded(
            float(parts["same_surface_pedagogical_family_only_risk"][index])
        ),
        "same_surface_pedagogical_family_only_unprotected_exact_risk": _rounded(
            float(parts["same_surface_pedagogical_family_only_unprotected_exact_risk"][index])
        ),
        "same_surface_hard_form_evidence": _rounded(
            float(parts["same_surface_hard_form_evidence"][index])
        ),
        "same_surface_soft_form_evidence": _rounded(
            float(parts["same_surface_soft_form_evidence"][index])
        ),
        "jmdict_priority": _rounded(float(parts["jmdict_priority"][index])),
        "jmdict_pair_safe_priority": _rounded(
            float(parts["jmdict_pair_safe_priority"][index])
            if np.isfinite(float(parts["jmdict_pair_safe_priority"][index]))
            else None
        ),
        "jmdict_pair_priority_leak_risk": _rounded(
            float(parts["jmdict_pair_priority_leak_risk"][index])
        ),
        "jmdict_pair_missing_reading_risk": _rounded(
            float(parts["jmdict_pair_missing_reading_risk"][index])
        ),
        "jmdict_pair_marked_form_not_safe_risk": _rounded(
            float(parts["jmdict_pair_marked_form_not_safe_risk"][index])
        ),
        "jmdict_pair_surface_only_multi_reading_risk": _rounded(
            float(parts["jmdict_pair_surface_only_multi_reading_risk"][index])
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
        "ordinary_gate_curve": candidate.ordinary_gate_curve,
        "ordinary_exception_mode": candidate.ordinary_exception_mode,
        "ordinary_exception_curve": candidate.ordinary_exception_curve,
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
        "same_surface_gradient_low_floor": _rounded(candidate.same_surface_gradient_low_floor),
        "same_surface_gradient_high_floor": _rounded(candidate.same_surface_gradient_high_floor),
        "same_surface_gradient_mode": candidate.same_surface_gradient_mode,
        "same_surface_gradient_curve": candidate.same_surface_gradient_curve,
        "same_surface_gradient_commonness_cap": _rounded(
            candidate.same_surface_gradient_commonness_cap
        ),
        "same_surface_gradient_lesson_rescue": _rounded(
            candidate.same_surface_gradient_lesson_rescue
        ),
        "same_surface_gradient_marked_boost": _rounded(
            candidate.same_surface_gradient_marked_boost
        ),
        "gairaigo_source_delta": _rounded(candidate.gairaigo_source_delta),
        "gairaigo_source_gate_mode": candidate.gairaigo_source_gate_mode,
        "gairaigo_english_ease_delta": _rounded(candidate.gairaigo_english_ease_delta),
        "gairaigo_english_ease_mode": candidate.gairaigo_english_ease_mode,
        "gairaigo_jlpt_raise_block": candidate.gairaigo_jlpt_raise_block,
        "jlpt_bound_mode": candidate.jlpt_bound_mode,
        "jlpt_bound_margin": _rounded(candidate.jlpt_bound_margin),
        "jlpt_bound_strength": _rounded(candidate.jlpt_bound_strength),
        "cross_corpus_rescue_cap": _rounded(candidate.cross_corpus_rescue_cap),
        "cross_corpus_rescue_mode": candidate.cross_corpus_rescue_mode,
        "cross_corpus_rescue_strength": _rounded(candidate.cross_corpus_rescue_strength),
        "cross_corpus_rescue_bccwj_lower": _rounded(candidate.cross_corpus_rescue_bccwj_lower),
        "cross_corpus_rescue_bccwj_upper": _rounded(candidate.cross_corpus_rescue_bccwj_upper),
        "cross_corpus_rescue_tubelex_lower": _rounded(candidate.cross_corpus_rescue_tubelex_lower),
        "cross_corpus_rescue_tubelex_upper": _rounded(candidate.cross_corpus_rescue_tubelex_upper),
        "cross_corpus_rescue_curve": candidate.cross_corpus_rescue_curve,
        "cross_corpus_rescue_gate_mode": candidate.cross_corpus_rescue_gate_mode,
        "cross_corpus_rescue_boost_strength": _rounded(
            candidate.cross_corpus_rescue_boost_strength
        ),
        "cross_corpus_rescue_boost_bccwj_lower": _rounded(
            candidate.cross_corpus_rescue_boost_bccwj_lower
        ),
        "cross_corpus_rescue_boost_bccwj_upper": _rounded(
            candidate.cross_corpus_rescue_boost_bccwj_upper
        ),
        "cross_corpus_rescue_boost_tubelex_lower": _rounded(
            candidate.cross_corpus_rescue_boost_tubelex_lower
        ),
        "cross_corpus_rescue_boost_tubelex_upper": _rounded(
            candidate.cross_corpus_rescue_boost_tubelex_upper
        ),
        "cross_corpus_rescue_burden_lower": _rounded(candidate.cross_corpus_rescue_burden_lower),
        "cross_corpus_rescue_burden_upper": _rounded(candidate.cross_corpus_rescue_burden_upper),
        "cross_corpus_rescue_single_kanji_lower": _rounded(
            candidate.cross_corpus_rescue_single_kanji_lower
        ),
        "cross_corpus_rescue_single_kanji_upper": _rounded(
            candidate.cross_corpus_rescue_single_kanji_upper
        ),
        "jmdict_priority_guard_mode": candidate.jmdict_priority_guard_mode,
        "jmdict_priority_guard_strength": _rounded(candidate.jmdict_priority_guard_strength),
        "jmdict_priority_guard_ordinary_strength": _rounded(
            candidate.jmdict_priority_guard_ordinary_strength
        ),
        "jmdict_priority_guard_curve": candidate.jmdict_priority_guard_curve,
        "jmdict_priority_guard_ped_rescue": _rounded(candidate.jmdict_priority_guard_ped_rescue),
        "jmdict_priority_source": candidate.jmdict_priority_source,
        "jmdict_pair_safe_blend": _rounded(candidate.jmdict_pair_safe_blend),
        "pair_leak_ped_gate_mode": candidate.pair_leak_ped_gate_mode,
        "pair_leak_ped_adjustment_mode": candidate.pair_leak_ped_adjustment_mode,
        "pair_leak_ped_strength": _rounded(candidate.pair_leak_ped_strength),
        "pair_leak_ped_floor": _rounded(candidate.pair_leak_ped_floor),
        "pair_leak_ped_curve": candidate.pair_leak_ped_curve,
        "base_family_rescue_margin": _rounded(candidate.base_family_rescue_margin),
        "base_family_rescue_strength": _rounded(candidate.base_family_rescue_strength),
        "base_family_rescue_gate_mode": candidate.base_family_rescue_gate_mode,
        "base_family_rescue_gap_lower": _rounded(candidate.base_family_rescue_gap_lower),
        "base_family_rescue_gap_upper": _rounded(candidate.base_family_rescue_gap_upper),
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
        "ogc",
        "oem",
        "oec",
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
        "sglf",
        "sghf",
        "sgm",
        "sgc",
        "sgcc",
        "sglr",
        "sgmb",
        "ccrc",
        "ccrm",
        "ccrs",
        "ccbl",
        "ccbu",
        "cctl",
        "cctu",
        "cccc",
        "ccg",
        "ccbs",
        "ccbbl",
        "ccbbu",
        "ccbtll",
        "ccbtu",
        "ccbrl",
        "ccbru",
        "ccskl",
        "ccsku",
        "jpgm",
        "jpgs",
        "jpgos",
        "jpgc",
        "jpgpr",
        "jpsrc",
        "jpsb",
        "plpg",
        "plpm",
        "plps",
        "plpf",
        "plpc",
        "bfrm",
        "bfrs",
        "bfrg",
        "bfrl",
        "bfru",
        "ab",
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


def _ramp_scalar(value: float, *, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.0
    return float(np.clip((float(value) - lower) / (upper - lower), 0.0, 1.0))


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
        f"- Calibration labels: `{_escape(inputs.get('calibration_json'))}`",
        f"- Holdout review: `{_escape(inputs.get('review_markdown'))}`",
        f"- Holdout labels: `{_escape(inputs.get('holdout_json'))}`",
        f"- Component count: `{_escape(inputs.get('component_count'))}`",
        f"- Signal count: `{_escape(inputs.get('signal_count'))}`",
        f"- Candidate count: `{_escape(inputs.get('candidate_count'))}`",
        f"- Target curve override: `{_escape(_mapping(report.get('method')).get('target_curve_override'))}`",
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
        f"- Hard form evidence rows: `{_escape(population.get('same_surface_hard_form_evidence_positive'))}`",
        f"- Soft form evidence rows: `{_escape(population.get('same_surface_soft_form_evidence_positive'))}`",
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
        "Source risk | Rank gap | Source strength | Hard form | Soft form |"
    )


def _same_surface_focus_rule(candidate_ids: Sequence[str]) -> str:
    score_rules = " | ".join("---:" for _candidate_id in candidate_ids)
    return f"| --- | {score_rules} | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"


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
        f"{_escape(row.get('reading_form_source_strength'))} | "
        f"{_escape(row.get('same_surface_hard_form_evidence'))} | "
        f"{_escape(row.get('same_surface_soft_form_evidence'))} |"
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
    lines.extend(["", "Band samples:", ""])
    lines.extend(_band_sample_table(details.get("band_samples")))
    movements = _mapping(details.get("largest_movements_vs_frequency"))
    lines.extend(["", "Moved earlier vs frequency:", ""])
    lines.extend(_movement_table(movements.get("moved_earlier")))
    lines.extend(["", "Moved later vs frequency:", ""])
    lines.extend(_movement_table(movements.get("moved_later")))
    return lines


def _band_sample_table(value: object) -> list[str]:
    lines = [
        "| Band | Count | Samples |",
        "| --- | ---: | --- |",
    ]
    for band in _sequence_dicts(value):
        samples = []
        for sample in _sequence_dicts(band.get("samples")):
            word = (
                f"{sample.get('lemma')}/{sample.get('reading')}"
                if sample.get("reading")
                else str(sample.get("lemma") or "")
            )
            samples.append(f"{word} ({sample.get('difficulty')})")
        lines.append(
            f"| {_escape(band.get('band'))} | {_escape(band.get('count'))} | "
            f"{_escape('; '.join(samples))} |"
        )
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
        "ordinary_gate_curve",
        "ordinary_exception_mode",
        "ordinary_exception_curve",
        "reading_guard_delta",
        "tail_floor",
        "tail_floor_mode",
        "same_surface_floor",
        "same_surface_floor_mode",
        "same_surface_source_attenuation",
        "same_surface_source_attenuation_mode",
        "same_surface_secondary_floor",
        "same_surface_secondary_floor_mode",
        "same_surface_gradient_low_floor",
        "same_surface_gradient_high_floor",
        "same_surface_gradient_mode",
        "same_surface_gradient_curve",
        "same_surface_gradient_commonness_cap",
        "same_surface_gradient_lesson_rescue",
        "same_surface_gradient_marked_boost",
        "gairaigo_source_delta",
        "gairaigo_source_gate_mode",
        "gairaigo_english_ease_delta",
        "gairaigo_english_ease_mode",
        "gairaigo_jlpt_raise_block",
        "jlpt_bound_mode",
        "jlpt_bound_margin",
        "jlpt_bound_strength",
        "jmdict_priority_source",
        "jmdict_pair_safe_blend",
        "pair_leak_ped_gate_mode",
        "pair_leak_ped_adjustment_mode",
        "pair_leak_ped_strength",
        "pair_leak_ped_floor",
        "pair_leak_ped_curve",
    )
    return ",".join(f"{key}={params.get(key)}" for key in keys)


if __name__ == "__main__":
    raise SystemExit(main())
