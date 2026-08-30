#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_aozora_tail_bakeoff_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    _current_scores,
    _label_context,
    _load_json,
    _selected_candidate_metadata,
    _variant_result,
    ComponentView,
    _view_with_target_curve_override,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    family_parts,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_early_exact_support_gate_bakeoff_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_early_exact_support_gate_bakeoff_en_ja_latest.md"
)
FOCUS_ROWS = (
    ("明い", "あかい"),
    ("端", "はな"),
    ("端", "たん"),
    ("長", "おさ"),
    ("前", "ぜん"),
    ("辛い", "つらい"),
    ("料理", "りょうり"),
    ("ドア", "どあ"),
    ("殺す", "ころす"),
    ("初め", "はじめ"),
    ("ひく", "ひく"),
    ("ぼたん", "ぼたん"),
    ("冬休み", "ふゆやすみ"),
    ("春休み", "はるやすみ"),
    ("主", "おも"),
    ("仏", "ぶつ"),
    ("競輪", "けいりん"),
    ("碧", "へき"),
    ("応え", "いらえ"),
    ("良人", "りょうじん"),
    ("女", "め"),
    ("紅", "くれない"),
    ("分かり", "わかり"),
    ("御手洗", "みたらし"),
    ("早く", "はやく"),
    ("バックパック", "ばっくぱっく"),
    ("髪型", "かみがた"),
    ("卵焼き", "たまごやき"),
    ("鬼ごっこ", "おにごっこ"),
    ("香る", "かおる"),
    ("居", "い"),
    ("本に", "ほんに"),
    ("暑", "しょ"),
    ("狭", "せ"),
    ("若", "わか"),
    ("聞き", "きき"),
    ("猶", "なお"),
    ("矢張り", "やはり"),
    ("良い", "よい"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sidecar bakeoff for an early-zone exact-support gate. The pass tries "
            "to demote suspicious easy placements only when exact/common support "
            "is weak and inherited/form-risk evidence is strong."
        )
    )
    parser.add_argument(
        "--source-arbitration-json", type=Path, default=DEFAULT_SOURCE_ARBITRATION_JSON
    )
    parser.add_argument("--component-matrix", type=Path, default=None)
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--candidate-family", default="")
    parser.add_argument(
        "--target-curve-override",
        choices=("component", "warp_p60_g155"),
        default="",
    )
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--top-variant-count", type=int, default=20)
    parser.add_argument("--sample-limit", type=int, default=40)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        source_arbitration_json=_resolve_path(args.source_arbitration_json),
        component_matrix_path=(
            _resolve_path(args.component_matrix) if args.component_matrix else None
        ),
        candidate_id=str(args.candidate_id or ""),
        candidate_family=str(args.candidate_family or ""),
        target_curve_override=str(args.target_curve_override or ""),
        calibration_json=_resolve_path(args.calibration_json),
        holdout_json=_resolve_path(args.holdout_json),
        validation_json=_resolve_path(args.validation_json),
        top_variant_count=max(1, int(args.top_variant_count)),
        sample_limit=max(1, int(args.sample_limit)),
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
    source_arbitration_json: Path,
    component_matrix_path: Path | None,
    candidate_id: str,
    candidate_family: str,
    target_curve_override: str,
    calibration_json: Path,
    holdout_json: Path,
    validation_json: Path,
    top_variant_count: int,
    sample_limit: int,
) -> dict[str, Any]:
    source_report = _load_json(source_arbitration_json)
    selected = _selected_candidate_metadata(
        source_report,
        candidate_id=candidate_id,
        candidate_family=candidate_family,
        target_curve_override=target_curve_override,
        component_matrix_path=component_matrix_path,
    )
    component_matrix = _resolve_path(Path(str(selected["component_matrix"])))
    component = np.load(component_matrix)
    view = _view_with_target_curve_override(
        ComponentView.from_npz(component),
        target_curve_override=str(selected["target_curve_override"]),
    )
    current_scores = _current_scores(view=view, selected=selected)
    parts = family_parts(view)
    labels = _label_context(
        view=view,
        current_scores=current_scores,
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    evidence = _early_gate_evidence(view=view, parts=parts)
    baseline = _variant_result(
        variant={
            "variant_id": "current",
            "description": "Current source-arbitration candidate; no early exact-support gate.",
        },
        scores=current_scores,
        current_scores=current_scores,
        labels=labels,
    )
    baseline.update(_movement_summary(scores=current_scores, current_scores=current_scores))
    rows = [baseline]
    variants = _variant_specs()
    for variant in variants:
        scores = _apply_variant(
            current_scores=current_scores,
            evidence=evidence,
            variant=variant,
        )
        row = _variant_result(
            variant=variant,
            scores=scores,
            current_scores=current_scores,
            labels=labels,
        )
        row.update(_movement_summary(scores=scores, current_scores=current_scores))
        rows.append(row)
    ranked = sorted(
        rows[1:],
        key=lambda row: (
            _optional_float(row.get("selection_score")) or -999.0,
            -int(row.get("label_regressed_count_0p01") or 0),
            int(row.get("label_improved_count_0p01") or 0),
            -(_optional_float(row.get("mean_abs_delta")) or 999.0),
        ),
        reverse=True,
    )
    top_rows = ranked[:top_variant_count]
    no_regression_rows = [
        row for row in ranked if int(row.get("label_regressed_count_0p01") or 0) == 0
    ][:top_variant_count]
    moved_rows = [row for row in ranked if int(row.get("moved_count") or 0) > 0]
    high_impact_rows = sorted(
        moved_rows,
        key=lambda row: (
            -int(row.get("moved_count") or 0),
            int(row.get("label_regressed_count_0p01") or 0),
            -int(row.get("label_improved_count_0p01") or 0),
        ),
    )[: min(top_variant_count, 12)]
    best_by_suspicion_mode = _best_by_suspicion_mode(ranked)
    sample_ids = {
        str(row.get("variant_id") or "")
        for row in [
            *top_rows[:3],
            *no_regression_rows[:3],
            *high_impact_rows[:3],
            *best_by_suspicion_mode,
        ]
        if row.get("variant_id")
    }
    variant_by_id = {str(variant["variant_id"]): variant for variant in variants}
    samples = {
        variant_id: _variant_samples(
            scores=_apply_variant(
                current_scores=current_scores,
                evidence=evidence,
                variant=variant_by_id[variant_id],
            ),
            current_scores=current_scores,
            view=view,
            evidence=evidence,
            limit=sample_limit,
        )
        for variant_id in sample_ids
        if variant_id in variant_by_id
    }
    focus = {
        variant_id: _focus_rows(
            scores=_apply_variant(
                current_scores=current_scores,
                evidence=evidence,
                variant=variant_by_id[variant_id],
            ),
            current_scores=current_scores,
            view=view,
            evidence=evidence,
        )
        for variant_id in sample_ids
        if variant_id in variant_by_id
    }
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Test an early-zone certification gate: easy scores are only raised "
                "when exact support is weak and form/inheritance suspicion is high. "
                "JLPT absence is not used as standalone negative evidence."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "formula": (
                "Standard variants: risk = early_gate(score) * suspicion * "
                "(1 - exact_support). Typed variants start from the conservative "
                "full gate, then add overlay risk = early_gate(score) * "
                "typed_evidence^p * (1 - exact_support) * score_taper, where "
                "typed_evidence requires tail/reading or strong-form "
                "corroboration and direct JLPT/lesson/exact support rescues the row. "
                "Orthographic variants start from the typed clean gate, then add "
                "a bounded kana-preferred written-form overlay when support is "
                "normalized-only or otherwise orthographically weak. All variants "
                "map risk through target_floor and max_raise."
            ),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "component_count": int(len(current_scores)),
            "label_count": len(labels["rows"]),
            "variant_count": len(variants),
        },
        "baseline": baseline,
        "top_variants": top_rows,
        "no_regression_variants": no_regression_rows,
        "high_impact_variants": high_impact_rows,
        "best_by_suspicion_mode": best_by_suspicion_mode,
        "variant_samples": samples,
        "focus_rows": focus,
        "population_summary": _population_summary(evidence=evidence, current_scores=current_scores),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "source_arbitration_json": source_arbitration_json,
                "component_matrix": component_matrix,
                "calibration_json": calibration_json,
                "holdout_json": holdout_json,
                "validation_json": validation_json,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "aozora_tail_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja.py"
                ),
                "early_exact_support_gate_bakeoff": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _best_by_suspicion_mode(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        mode = str(row.get("suspicion_mode") or "")
        if not mode:
            continue
        current = selected.get(mode)
        if current is None or (_optional_float(row.get("selection_score")) or -999.0) > (
            _optional_float(current.get("selection_score")) or -999.0
        ):
            selected[mode] = dict(row)
    return [selected[key] for key in sorted(selected)]


def _early_gate_evidence(*, view: ComponentView, parts: Mapping[str, Any]) -> dict[str, np.ndarray]:
    exact_commonness = _part(parts, "same_surface_exact_commonness")
    exact_common_gate = _ramp(exact_commonness, lower=0.20, upper=0.55)
    pair_safe_commonness = _part(parts, "jmdict_pair_safe_commonness")
    pair_safe_gate = _ramp(pair_safe_commonness, lower=0.20, upper=0.70)
    exact_jlpt = np.clip(_part(parts, "jlpt_vocab_effective_exact_known"), 0.0, 1.0)
    raw_exact_jlpt = np.clip(_part(parts, "jlpt_vocab_raw_exact_known"), 0.0, 1.0)
    normalized_exact_jlpt = np.clip(_part(parts, "jlpt_vocab_normalized_exact_known"), 0.0, 1.0)
    normalized_only_jlpt = normalized_exact_jlpt * np.clip(1.0 - raw_exact_jlpt, 0.0, 1.0)
    lesson = np.clip(_part(parts, "lesson_vocab_known"), 0.0, 1.0)
    kana_preferred = np.clip(
        view.value("jmdict_kana_preferred_risk", fill=0.0),
        0.0,
        1.0,
    ).astype(np.float32)
    rare_wago_obscure = np.clip(
        view.value("rare_wago_obscure_written_risk", fill=0.0),
        0.0,
        1.0,
    ).astype(np.float32)
    kanji_surface = np.asarray(
        [_contains_cjk(str(lemma)) for lemma in view.lemmas],
        dtype=np.float32,
    )
    family_only = np.clip(_part(parts, "pedagogical_family_only_known"), 0.0, 1.0)
    family_surface = np.clip(_part(parts, "jlpt_vocab_surface_known"), 0.0, 1.0)
    sibling_common = np.clip(_part(parts, "same_surface_sibling_common_gate"), 0.0, 1.0)
    weak_exact = np.clip(1.0 - exact_common_gate, 0.0, 1.0)
    hard_form = np.clip(_part(parts, "same_surface_hard_form_evidence"), 0.0, 1.0)
    soft_form = np.clip(_part(parts, "same_surface_soft_form_evidence"), 0.0, 1.0)
    marked_not_safe = np.clip(
        _part(parts, "jmdict_pair_marked_form_not_safe_risk"),
        0.0,
        1.0,
    )
    reading_inheritance = np.clip(_part(parts, "reading_inheritance_risk"), 0.0, 1.0)
    tail_guard = np.clip(_part(parts, "tail_floor_guard"), 0.0, 1.0)
    same_surface_risks = np.maximum.reduce(
        [
            np.clip(
                _part(parts, "same_surface_pedagogical_family_only_unprotected_exact_risk"),
                0.0,
                1.0,
            ),
            np.clip(_part(parts, "same_surface_priority_pollution_risk"), 0.0, 1.0),
            np.clip(_part(parts, "same_surface_rare_pollution_risk"), 0.0, 1.0),
        ]
    )
    family_support = np.maximum.reduce([family_only, family_surface, sibling_common])
    family_gate = np.maximum(0.35, family_support)
    hard_same_risk = np.maximum.reduce(
        [
            same_surface_risks,
            hard_form,
            marked_not_safe,
        ]
    )
    hard_soft_same_risk = np.maximum.reduce(
        [
            hard_same_risk,
            0.70 * soft_form,
        ]
    )
    full_form_risk = np.maximum.reduce(
        [
            same_surface_risks,
            hard_form,
            0.70 * soft_form,
            marked_not_safe,
            reading_inheritance,
            tail_guard,
        ]
    )
    return {
        "exact_commonness": exact_commonness,
        "exact_common_gate": exact_common_gate,
        "pair_safe_commonness": pair_safe_commonness,
        "pair_safe_gate": pair_safe_gate,
        "jlpt_exact_known": exact_jlpt,
        "jlpt_raw_exact_known": raw_exact_jlpt,
        "jlpt_normalized_exact_known": normalized_exact_jlpt,
        "jlpt_normalized_only_known": normalized_only_jlpt,
        "lesson_known": lesson,
        "kana_preferred": kana_preferred,
        "rare_wago_obscure_written": rare_wago_obscure,
        "kanji_surface": kanji_surface,
        "family_support": family_support,
        "same_surface_risk": same_surface_risks,
        "hard_form": hard_form,
        "soft_form": soft_form,
        "marked_not_safe": marked_not_safe,
        "reading_inheritance": reading_inheritance,
        "tail_guard": tail_guard,
        "weak_exact": weak_exact,
        "suspicion_hard_same": np.asarray(
            weak_exact * hard_same_risk * family_gate, dtype=np.float32
        ),
        "suspicion_hard_soft_same": np.asarray(
            weak_exact * hard_soft_same_risk * family_gate,
            dtype=np.float32,
        ),
        "suspicion_full": np.asarray(weak_exact * full_form_risk * family_gate, dtype=np.float32),
    }


def _variant_specs() -> list[dict[str, Any]]:
    variants = []
    seen: set[str] = set()
    for early_ceiling in (0.30, 0.40, 0.50):
        for floor_low, floor_high in ((0.22, 0.34), (0.28, 0.42), (0.34, 0.52)):
            for max_raise in (0.08, 0.14, 0.24):
                for common_rescue_upper in (0.35, 0.55, 0.75):
                    for pair_safe_weight in (0.0, 0.50):
                        for jlpt_exact_weight in (0.0, 0.50, 1.0):
                            for lesson_weight in (0.50, 1.0):
                                for suspicion_power in (0.75, 1.0, 1.5):
                                    for suspicion_mode in ("hard_same", "hard_soft_same", "full"):
                                        _append_variant(
                                            variants,
                                            seen,
                                            early_ceiling=early_ceiling,
                                            floor_low=floor_low,
                                            floor_high=floor_high,
                                            max_raise=max_raise,
                                            common_rescue_upper=common_rescue_upper,
                                            pair_safe_weight=pair_safe_weight,
                                            jlpt_exact_weight=jlpt_exact_weight,
                                            lesson_weight=lesson_weight,
                                            suspicion_power=suspicion_power,
                                            suspicion_mode=suspicion_mode,
                                        )
    for early_ceiling in (0.40, 0.50, 0.60):
        for floor_low, floor_high in ((0.40, 0.62), (0.48, 0.72), (0.56, 0.84)):
            for max_raise in (0.36, 0.48, 0.64):
                for common_rescue_upper in (0.35, 0.45, 0.55, 0.75):
                    for pair_safe_weight in (0.0, 0.50):
                        for jlpt_exact_weight in (0.50, 1.0):
                            for lesson_weight in (0.50, 1.0):
                                for suspicion_power in (0.50, 0.75, 1.0, 1.5):
                                    _append_variant(
                                        variants,
                                        seen,
                                        early_ceiling=early_ceiling,
                                        floor_low=floor_low,
                                        floor_high=floor_high,
                                        max_raise=max_raise,
                                        common_rescue_upper=common_rescue_upper,
                                        pair_safe_weight=pair_safe_weight,
                                        jlpt_exact_weight=jlpt_exact_weight,
                                        lesson_weight=lesson_weight,
                                        suspicion_power=suspicion_power,
                                        suspicion_mode="full",
                                    )
    for early_ceiling in (0.50, 0.60):
        for floor_low, floor_high in ((0.48, 0.72), (0.56, 0.84)):
            for max_raise in (0.24, 0.36, 0.48):
                for common_rescue_upper in (0.35, 0.45):
                    for lesson_rescue_strength in (0.75, 1.0):
                        for soft_tail_block_strength in (0.75, 1.0):
                            for taper_start, taper_end in (
                                (0.25, 0.45),
                                (0.30, 0.50),
                                (0.35, 0.50),
                                (0.40, 0.55),
                            ):
                                for suspicion_power in (0.50, 0.75, 1.0):
                                    _append_typed_overlay_variant(
                                        variants,
                                        seen,
                                        early_ceiling=early_ceiling,
                                        floor_low=floor_low,
                                        floor_high=floor_high,
                                        max_raise=max_raise,
                                        common_rescue_upper=common_rescue_upper,
                                        lesson_rescue_strength=lesson_rescue_strength,
                                        soft_tail_block_strength=soft_tail_block_strength,
                                        taper_start=taper_start,
                                        taper_end=taper_end,
                                        suspicion_power=suspicion_power,
                                    )
    for early_ceiling in (0.35, 0.50, 0.60):
        for floor_low, floor_high in ((0.30, 0.42), (0.36, 0.50), (0.44, 0.58)):
            for max_raise in (0.08, 0.14, 0.22, 0.32):
                for exact_common_rescue_weight in (0.0, 0.25, 0.50):
                    for taper_start, taper_end in ((0.20, 0.40), (0.30, 0.50), (0.40, 0.60)):
                        for suspicion_power in (0.50, 0.75, 1.0, 1.5):
                            _append_orthographic_overlay_variant(
                                variants,
                                seen,
                                early_ceiling=early_ceiling,
                                floor_low=floor_low,
                                floor_high=floor_high,
                                max_raise=max_raise,
                                exact_common_rescue_weight=exact_common_rescue_weight,
                                taper_start=taper_start,
                                taper_end=taper_end,
                                suspicion_power=suspicion_power,
                            )
    return variants


def _append_variant(
    variants: list[dict[str, Any]],
    seen: set[str],
    *,
    early_ceiling: float,
    floor_low: float,
    floor_high: float,
    max_raise: float,
    common_rescue_upper: float,
    pair_safe_weight: float,
    jlpt_exact_weight: float,
    lesson_weight: float,
    suspicion_power: float,
    suspicion_mode: str,
) -> None:
    variant_id = (
        f"exgate_ec{_id_float(early_ceiling)}"
        f"_fl{_id_float(floor_low)}_fh{_id_float(floor_high)}"
        f"_mr{_id_float(max_raise)}_cru{_id_float(common_rescue_upper)}"
        f"_ps{_id_float(pair_safe_weight)}_jx{_id_float(jlpt_exact_weight)}"
        f"_lw{_id_float(lesson_weight)}_sp{_id_float(suspicion_power)}"
        f"_sm{suspicion_mode}"
    )
    if variant_id in seen:
        return
    seen.add(variant_id)
    variants.append(
        {
            "variant_id": variant_id,
            "description": (
                "Early exact-support certification gate. Raises only early scores "
                "with weak exact commonness and strong inherited/form-risk evidence."
            ),
            "early_ceiling": early_ceiling,
            "floor_low": floor_low,
            "floor_high": floor_high,
            "max_raise": max_raise,
            "common_rescue_upper": common_rescue_upper,
            "pair_safe_weight": pair_safe_weight,
            "jlpt_exact_weight": jlpt_exact_weight,
            "lesson_weight": lesson_weight,
            "suspicion_power": suspicion_power,
            "suspicion_mode": suspicion_mode,
        }
    )


def _append_typed_overlay_variant(
    variants: list[dict[str, Any]],
    seen: set[str],
    *,
    early_ceiling: float,
    floor_low: float,
    floor_high: float,
    max_raise: float,
    common_rescue_upper: float,
    lesson_rescue_strength: float,
    soft_tail_block_strength: float,
    taper_start: float,
    taper_end: float,
    suspicion_power: float,
) -> None:
    variant_id = (
        f"exgate_typed_ec{_id_float(early_ceiling)}"
        f"_fl{_id_float(floor_low)}_fh{_id_float(floor_high)}"
        f"_mr{_id_float(max_raise)}_cru{_id_float(common_rescue_upper)}"
        f"_lr{_id_float(lesson_rescue_strength)}"
        f"_stb{_id_float(soft_tail_block_strength)}"
        f"_ts{_id_float(taper_start)}_te{_id_float(taper_end)}"
        f"_sp{_id_float(suspicion_power)}"
    )
    if variant_id in seen:
        return
    seen.add(variant_id)
    variants.append(
        {
            "variant_id": variant_id,
            "description": (
                "Typed early exact-support overlay. Starts from the conservative "
                "full gate, then adds extra raise only for stronger structural "
                "risk types while rescuing lesson-known reading inheritance and "
                "soft-only tail cases."
            ),
            "early_ceiling": early_ceiling,
            "floor_low": floor_low,
            "floor_high": floor_high,
            "max_raise": max_raise,
            "common_rescue_upper": common_rescue_upper,
            "lesson_rescue_strength": lesson_rescue_strength,
            "soft_tail_block_strength": soft_tail_block_strength,
            "taper_start": taper_start,
            "taper_end": taper_end,
            "suspicion_power": suspicion_power,
            "suspicion_mode": "typed_full_overlay",
        }
    )


def _append_orthographic_overlay_variant(
    variants: list[dict[str, Any]],
    seen: set[str],
    *,
    early_ceiling: float,
    floor_low: float,
    floor_high: float,
    max_raise: float,
    exact_common_rescue_weight: float,
    taper_start: float,
    taper_end: float,
    suspicion_power: float,
) -> None:
    variant_id = (
        f"exgate_orth_ec{_id_float(early_ceiling)}"
        f"_fl{_id_float(floor_low)}_fh{_id_float(floor_high)}"
        f"_mr{_id_float(max_raise)}_xcr{_id_float(exact_common_rescue_weight)}"
        f"_ts{_id_float(taper_start)}_te{_id_float(taper_end)}"
        f"_sp{_id_float(suspicion_power)}"
    )
    if variant_id in seen:
        return
    seen.add(variant_id)
    variants.append(
        {
            "variant_id": variant_id,
            "description": (
                "Orthographic variant overlay. Starts from the typed clean gate, "
                "then adds a bounded raise for kanji written forms that JMdict "
                "marks as kana-preferred, especially when JLPT support is "
                "normalized-only rather than raw exact."
            ),
            "early_ceiling": early_ceiling,
            "floor_low": floor_low,
            "floor_high": floor_high,
            "max_raise": max_raise,
            "exact_common_rescue_weight": exact_common_rescue_weight,
            "taper_start": taper_start,
            "taper_end": taper_end,
            "suspicion_power": suspicion_power,
            "suspicion_mode": "typed_orthographic_overlay",
        }
    )


def _apply_variant(
    *,
    current_scores: np.ndarray,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    if str(variant.get("suspicion_mode") or "") == "typed_full_overlay":
        return _apply_typed_overlay_variant(
            current_scores=current_scores,
            evidence=evidence,
            variant=variant,
        )
    if str(variant.get("suspicion_mode") or "") == "typed_orthographic_overlay":
        return _apply_orthographic_overlay_variant(
            current_scores=current_scores,
            evidence=evidence,
            variant=variant,
        )
    return _apply_standard_variant(
        current_scores=current_scores,
        evidence=evidence,
        variant=variant,
    )


def _apply_standard_variant(
    *,
    current_scores: np.ndarray,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    scores = np.asarray(current_scores, dtype=np.float32)
    early_ceiling = float(variant["early_ceiling"])
    early_gate = np.clip((early_ceiling - scores) / max(early_ceiling, 1e-6), 0.0, 1.0)
    exact_common_gate = _ramp(
        evidence["exact_commonness"],
        lower=0.10,
        upper=float(variant["common_rescue_upper"]),
    )
    exact_support = np.maximum.reduce(
        [
            exact_common_gate,
            float(variant["pair_safe_weight"])
            * np.asarray(evidence["pair_safe_gate"], dtype=np.float32),
            float(variant["jlpt_exact_weight"])
            * np.asarray(evidence["jlpt_exact_known"], dtype=np.float32),
            float(variant["lesson_weight"])
            * np.asarray(evidence["lesson_known"], dtype=np.float32),
        ]
    )
    raw_risk = (
        early_gate
        * np.power(
            np.clip(_suspicion_for_variant(evidence=evidence, variant=variant), 0.0, 1.0),
            float(variant["suspicion_power"]),
        )
        * np.clip(1.0 - exact_support, 0.0, 1.0)
    )
    target_floor = float(variant["floor_low"]) + raw_risk * (
        float(variant["floor_high"]) - float(variant["floor_low"])
    )
    desired_raise = raw_risk * np.maximum(0.0, target_floor - scores)
    raise_delta = np.minimum(desired_raise, float(variant["max_raise"]))
    return np.asarray(np.clip(scores + raise_delta, 0.0, 1.0), dtype=np.float32)


def _apply_typed_overlay_variant(
    *,
    current_scores: np.ndarray,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    scores = np.asarray(current_scores, dtype=np.float32)
    conservative_variant = {
        "early_ceiling": 0.50,
        "floor_low": 0.34,
        "floor_high": 0.52,
        "max_raise": 0.24,
        "common_rescue_upper": 0.75,
        "pair_safe_weight": 0.0,
        "jlpt_exact_weight": 1.0,
        "lesson_weight": 0.50,
        "suspicion_power": 0.75,
        "suspicion_mode": "full",
    }
    base_scores = _apply_standard_variant(
        current_scores=scores,
        evidence=evidence,
        variant=conservative_variant,
    )
    same_surface = np.asarray(evidence["same_surface_risk"], dtype=np.float32)
    hard_form = np.asarray(evidence["hard_form"], dtype=np.float32)
    soft_form = np.asarray(evidence["soft_form"], dtype=np.float32)
    marked_not_safe = np.asarray(evidence["marked_not_safe"], dtype=np.float32)
    reading_inheritance = np.asarray(evidence["reading_inheritance"], dtype=np.float32)
    tail_guard = np.asarray(evidence["tail_guard"], dtype=np.float32)
    lesson_known = np.asarray(evidence["lesson_known"], dtype=np.float32)
    strong_anchor = np.maximum.reduce([same_surface, hard_form, marked_not_safe])
    exact_common_gate = _ramp(
        evidence["exact_commonness"],
        lower=0.10,
        upper=float(variant["common_rescue_upper"]),
    )
    lesson_reading_rescue = _clip01(
        float(variant["lesson_rescue_strength"])
        * lesson_known
        * reading_inheritance
        * (1.0 - np.maximum.reduce([strong_anchor, soft_form]))
    )
    soft_tail_only = _clip01(
        soft_form * (1.0 - np.maximum.reduce([strong_anchor, reading_inheritance]))
    )
    soft_tail_block = _clip01(1.0 - float(variant["soft_tail_block_strength"]) * soft_tail_only)
    reading_component = reading_inheritance * np.maximum(tail_guard, strong_anchor)
    strong_overlay_evidence = np.maximum.reduce(
        [
            reading_component * (1.0 - lesson_reading_rescue),
            tail_guard * (1.0 - soft_form) * (1.0 - lesson_reading_rescue),
            strong_anchor * np.maximum(reading_inheritance, tail_guard),
        ]
    )
    strong_overlay_evidence = _clip01(strong_overlay_evidence * soft_tail_block)
    exact_support = np.maximum.reduce(
        [
            exact_common_gate,
            np.asarray(evidence["jlpt_exact_known"], dtype=np.float32),
            lesson_known,
            lesson_reading_rescue,
        ]
    )
    early_ceiling = float(variant["early_ceiling"])
    early_gate = np.clip((early_ceiling - scores) / max(early_ceiling, 1e-6), 0.0, 1.0)
    taper = _ramp(
        scores,
        lower=float(variant["taper_start"]),
        upper=float(variant["taper_end"]),
    )
    hard_marked = np.maximum(hard_form, marked_not_safe)
    score_taper = _clip01(1.0 - taper * (1.0 - hard_marked))
    raw_risk = (
        early_gate
        * np.power(
            _clip01(strong_overlay_evidence),
            float(variant["suspicion_power"]),
        )
        * _clip01(1.0 - exact_support)
        * score_taper
    )
    target_floor = float(variant["floor_low"]) + raw_risk * (
        float(variant["floor_high"]) - float(variant["floor_low"])
    )
    desired_raise = raw_risk * np.maximum(0.0, target_floor - base_scores)
    raise_delta = np.minimum(desired_raise, float(variant["max_raise"]))
    return np.asarray(np.clip(base_scores + raise_delta, 0.0, 1.0), dtype=np.float32)


def _apply_orthographic_overlay_variant(
    *,
    current_scores: np.ndarray,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    scores = np.asarray(current_scores, dtype=np.float32)
    typed_clean_variant = {
        "early_ceiling": 0.50,
        "floor_low": 0.56,
        "floor_high": 0.84,
        "max_raise": 0.36,
        "common_rescue_upper": 0.45,
        "lesson_rescue_strength": 0.75,
        "soft_tail_block_strength": 0.75,
        "taper_start": 0.25,
        "taper_end": 0.45,
        "suspicion_power": 0.75,
        "suspicion_mode": "typed_full_overlay",
    }
    base_scores = _apply_typed_overlay_variant(
        current_scores=scores,
        evidence=evidence,
        variant=typed_clean_variant,
    )
    raw_jlpt = np.asarray(evidence["jlpt_raw_exact_known"], dtype=np.float32)
    lesson = np.asarray(evidence["lesson_known"], dtype=np.float32)
    direct_support = np.maximum(raw_jlpt, lesson)
    kana_preferred = np.asarray(evidence["kana_preferred"], dtype=np.float32)
    normalized_only = np.asarray(evidence["jlpt_normalized_only_known"], dtype=np.float32)
    rare_wago_obscure = np.asarray(evidence["rare_wago_obscure_written"], dtype=np.float32)
    kanji_surface = np.asarray(evidence["kanji_surface"], dtype=np.float32)
    orthographic_evidence = (
        kanji_surface
        * kana_preferred
        * np.maximum.reduce(
            [
                normalized_only,
                np.sqrt(np.clip(rare_wago_obscure, 0.0, 1.0)),
                0.50 * np.clip(1.0 - direct_support, 0.0, 1.0) * rare_wago_obscure,
            ]
        )
    )
    exact_common_gate = _ramp(
        evidence["exact_commonness"],
        lower=0.20,
        upper=0.70,
    )
    exact_common_rescue = float(variant["exact_common_rescue_weight"]) * exact_common_gate
    early_ceiling = float(variant["early_ceiling"])
    early_gate = np.clip((early_ceiling - scores) / max(early_ceiling, 1e-6), 0.0, 1.0)
    taper = _ramp(
        scores,
        lower=float(variant["taper_start"]),
        upper=float(variant["taper_end"]),
    )
    score_taper = _clip01(1.0 - taper)
    risk = (
        early_gate
        * np.power(_clip01(orthographic_evidence), float(variant["suspicion_power"]))
        * _clip01(1.0 - direct_support)
        * _clip01(1.0 - exact_common_rescue)
        * score_taper
    )
    target_floor = float(variant["floor_low"]) + risk * (
        float(variant["floor_high"]) - float(variant["floor_low"])
    )
    desired_raise = risk * np.maximum(0.0, target_floor - base_scores)
    raise_delta = np.minimum(desired_raise, float(variant["max_raise"]))
    return np.asarray(np.clip(base_scores + raise_delta, 0.0, 1.0), dtype=np.float32)


def _suspicion_for_variant(
    *,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    mode = str(variant.get("suspicion_mode") or "full")
    key_by_mode = {
        "hard_same": "suspicion_hard_same",
        "hard_soft_same": "suspicion_hard_soft_same",
        "full": "suspicion_full",
    }
    key = key_by_mode.get(mode)
    if key is None:
        raise ValueError(f"Unsupported suspicion mode: {mode}")
    return np.asarray(evidence[key], dtype=np.float32)


def _movement_summary(*, scores: np.ndarray, current_scores: np.ndarray) -> dict[str, Any]:
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    moved = np.abs(delta) > 0.0005
    if not moved.any():
        return {
            "moved_count": 0,
            "up_count": 0,
            "mean_abs_delta": 0.0,
            "p90_abs_delta": 0.0,
            "max_delta": 0.0,
        }
    abs_delta = np.abs(delta[moved])
    return {
        "moved_count": int(moved.sum()),
        "up_count": int((delta > 0.0005).sum()),
        "mean_abs_delta": _rounded(float(abs_delta.mean())),
        "p90_abs_delta": _rounded(float(np.quantile(abs_delta, 0.90))),
        "max_delta": _rounded(float(delta.max())),
    }


def _variant_samples(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    evidence: Mapping[str, np.ndarray],
    limit: int,
) -> dict[str, Any]:
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    moved = [int(index) for index in np.argsort(-delta, kind="stable") if delta[index] > 0.001]
    suspicious_early = [
        int(index)
        for index in np.argsort(
            -np.asarray(evidence["suspicion_full"], dtype=np.float32), kind="stable"
        )
        if current_scores[index] < 0.50
    ]
    return {
        "largest_up_moves": [
            _row(index, scores=scores, current_scores=current_scores, view=view, evidence=evidence)
            for index in moved[:limit]
        ],
        "suspicious_early_rows": [
            _row(index, scores=scores, current_scores=current_scores, view=view, evidence=evidence)
            for index in suspicious_early[:limit]
        ],
    }


def _focus_rows(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    evidence: Mapping[str, np.ndarray],
) -> list[dict[str, Any]]:
    lookup = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings))
    }
    output = []
    for key in FOCUS_ROWS:
        index = lookup.get(key)
        if index is None:
            output.append({"lemma": key[0], "reading": key[1], "missing": True})
            continue
        output.append(
            _row(index, scores=scores, current_scores=current_scores, view=view, evidence=evidence)
        )
    return output


def _row(
    index: int,
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    evidence: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    return {
        "lemma": str(view.lemmas[index]),
        "reading": str(view.readings[index]),
        "score": _rounded(float(scores[index])),
        "current": _rounded(float(current_scores[index])),
        "delta": _rounded(float(scores[index] - current_scores[index])),
        "core_rank": (
            _rounded(float(view.core_ranks[index]))
            if np.isfinite(float(view.core_ranks[index]))
            else None
        ),
        "candidate_state": str(view.candidate_states[index]),
        "exact_commonness": _rounded(float(evidence["exact_commonness"][index])),
        "pair_safe_commonness": _rounded(float(evidence["pair_safe_commonness"][index])),
        "jlpt_exact_known": _rounded(float(evidence["jlpt_exact_known"][index])),
        "jlpt_raw_exact_known": _rounded(float(evidence["jlpt_raw_exact_known"][index])),
        "jlpt_normalized_exact_known": _rounded(
            float(evidence["jlpt_normalized_exact_known"][index])
        ),
        "jlpt_normalized_only_known": _rounded(
            float(evidence["jlpt_normalized_only_known"][index])
        ),
        "lesson_known": _rounded(float(evidence["lesson_known"][index])),
        "kana_preferred": _rounded(float(evidence["kana_preferred"][index])),
        "rare_wago_obscure_written": _rounded(float(evidence["rare_wago_obscure_written"][index])),
        "family_support": _rounded(float(evidence["family_support"][index])),
        "same_surface_risk": _rounded(float(evidence["same_surface_risk"][index])),
        "hard_form": _rounded(float(evidence["hard_form"][index])),
        "soft_form": _rounded(float(evidence["soft_form"][index])),
        "reading_inheritance": _rounded(float(evidence["reading_inheritance"][index])),
        "tail_guard": _rounded(float(evidence["tail_guard"][index])),
        "suspicion_hard_same": _rounded(float(evidence["suspicion_hard_same"][index])),
        "suspicion_hard_soft_same": _rounded(float(evidence["suspicion_hard_soft_same"][index])),
        "suspicion_full": _rounded(float(evidence["suspicion_full"][index])),
    }


def _population_summary(
    *,
    evidence: Mapping[str, np.ndarray],
    current_scores: np.ndarray,
) -> dict[str, Any]:
    early = np.asarray(current_scores, dtype=np.float32) < 0.50
    suspicion = np.asarray(evidence["suspicion_full"], dtype=np.float32)
    return {
        "early_under_0p50_count": int(early.sum()),
        "early_suspicion_ge_0p25": int((early & (suspicion >= 0.25)).sum()),
        "early_suspicion_ge_0p50": int((early & (suspicion >= 0.50)).sum()),
        "early_suspicion_ge_0p75": int((early & (suspicion >= 0.75)).sum()),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Early Exact-Support Gate Bakeoff",
        "",
        "## Summary",
        "",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Candidate family: `{_escape(method.get('candidate_family'))}`",
        f"- Target curve: `{_escape(method.get('target_curve_override'))}`",
        f"- Variants tested: `{_escape(_mapping(report.get('inputs')).get('variant_count'))}`",
        f"- Label count: `{_escape(_mapping(report.get('inputs')).get('label_count'))}`",
        "",
        "This is a diagnostic sidecar only. It does not change scorer behavior.",
        "",
        "Formula:",
        "",
        f"`{_escape(method.get('formula'))}`",
        "",
        "Population:",
        "",
        _population_table([_mapping(report.get("population_summary"))]),
        "",
        "## Baseline",
        "",
        _metric_table([_mapping(report.get("baseline"))]),
        "",
        "## Top Variants",
        "",
        _metric_table(report.get("top_variants") or []),
        "",
        "## No-Regression Variants",
        "",
        _metric_table(report.get("no_regression_variants") or []),
        "",
        "## High-Impact Variants",
        "",
        _metric_table(report.get("high_impact_variants") or []),
        "",
        "## Best By Suspicion Mode",
        "",
        _metric_table(report.get("best_by_suspicion_mode") or []),
        "",
        "## Samples",
        "",
    ]
    for variant_id, samples in _mapping(report.get("variant_samples")).items():
        lines.extend(
            [
                f"### `{_escape(variant_id)}`",
                "",
                "Focus rows:",
                "",
                _row_table(_mapping(report.get("focus_rows")).get(variant_id) or []),
                "",
                "Largest upward moves:",
                "",
                _row_table(_mapping(samples).get("largest_up_moves") or []),
                "",
                "Highest suspicious early rows:",
                "",
                _row_table(_mapping(samples).get("suspicious_early_rows") or []),
                "",
            ]
        )
    lines.extend(
        [
            "## Caveats",
            "",
            "- This tests a floor-style demotion only for early scores; already-hard rows are not moved.",
            "- JLPT absence is never direct negative evidence. Exact JLPT presence is only a swept rescue weight.",
            "- Rows with high exact commonness are intended to be rescued even when they are missing from JLPT.",
            "",
        ]
    )
    return "\n".join(lines)


def _metric_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Variant | Select | MAE | Pairwise | Beginner dMAE | Improve | Regress | Moved | MeanAbsDelta | MaxDelta | Params |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = _mapping(row.get("all_summary"))
        beginner = _mapping(row.get("beginner"))
        params = ", ".join(
            f"{key}={_fmt_param(row.get(key))}"
            for key in (
                "early_ceiling",
                "floor_low",
                "floor_high",
                "max_raise",
                "common_rescue_upper",
                "pair_safe_weight",
                "jlpt_exact_weight",
                "lesson_weight",
                "lesson_rescue_strength",
                "soft_tail_block_strength",
                "exact_common_rescue_weight",
                "taper_start",
                "taper_end",
                "suspicion_power",
                "suspicion_mode",
            )
            if key in row
        )
        cells = [
            str(row.get("variant_id") or ""),
            _fmt(row.get("selection_score")),
            _fmt(summary.get("mae")),
            _fmt(summary.get("pairwise_accuracy")),
            _fmt(beginner.get("mae_delta_vs_current")),
            str(row.get("label_improved_count_0p01") or 0),
            str(row.get("label_regressed_count_0p01") or 0),
            str(row.get("moved_count") or 0),
            _fmt(row.get("mean_abs_delta")),
            _fmt(row.get("max_delta")),
            params,
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _population_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Early <0.50 | Susp >=0.25 | Susp >=0.50 | Susp >=0.75 |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        cells = [
            str(row.get("early_under_0p50_count") or 0),
            str(row.get("early_suspicion_ge_0p25") or 0),
            str(row.get("early_suspicion_ge_0p50") or 0),
            str(row.get("early_suspicion_ge_0p75") or 0),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _row_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Word | Current | New | Delta | Rank | Exact | Pair | JLPTx | RawJ | NormOnly | Lesson | KanaPref | RareWago | Family | SameSurf | Hard | Soft | ReadInh | Tail | Full |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        label = (
            f"{row.get('lemma')}/{row.get('reading')}"
            if row.get("reading")
            else str(row.get("lemma") or "")
        )
        cells = [
            label,
            _fmt(row.get("current")),
            _fmt(row.get("score")),
            _fmt(row.get("delta")),
            _fmt(row.get("core_rank")),
            _fmt(row.get("exact_commonness")),
            _fmt(row.get("pair_safe_commonness")),
            _fmt(row.get("jlpt_exact_known")),
            _fmt(row.get("jlpt_raw_exact_known")),
            _fmt(row.get("jlpt_normalized_only_known")),
            _fmt(row.get("lesson_known")),
            _fmt(row.get("kana_preferred")),
            _fmt(row.get("rare_wago_obscure_written")),
            _fmt(row.get("family_support")),
            _fmt(row.get("same_surface_risk")),
            _fmt(row.get("hard_form")),
            _fmt(row.get("soft_form")),
            _fmt(row.get("reading_inheritance")),
            _fmt(row.get("tail_guard")),
            _fmt(row.get("suspicion_full")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _part(parts: Mapping[str, Any], name: str) -> np.ndarray:
    value = parts.get(name)
    if value is None:
        raise KeyError(name)
    return np.nan_to_num(np.asarray(value, dtype=np.float32), nan=0.0)


def _ramp(values: Any, *, lower: float, upper: float) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    if upper <= lower:
        return (array >= upper).astype(np.float32)
    return np.asarray(np.clip((array - lower) / (upper - lower), 0.0, 1.0), dtype=np.float32)


def _clip01(values: Any) -> np.ndarray:
    return np.asarray(np.clip(values, 0.0, 1.0), dtype=np.float32)


def _contains_cjk(value: str) -> bool:
    return any(
        ("\u3400" <= character <= "\u9fff") or ("\uf900" <= character <= "\ufaff")
        for character in value
    )


def _fmt(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _fmt_param(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return str(value or "")
    return f"{parsed:.3f}"


def _id_float(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", "")


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
