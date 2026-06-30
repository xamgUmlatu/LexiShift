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
    DEFAULT_AOZORA_SQLITE,
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    _aozora_feature_arrays,
    _component_signal_arrays,
    _current_scores,
    _label_context,
    _load_json,
    _regression_profile_table,
    _resolve_path,
    _sample_table,
    _selected_candidate_metadata,
    _smoothstep_array,
    _tail_variant_terms,
    _variant_result,
    _variant_samples,
    ComponentView,
    _view_with_target_curve_override,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_source_void_tiebreak_bakeoff_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_source_void_tiebreak_bakeoff_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Try a capped second-pass source-void tiebreaker for advanced en-ja "
            "difficulty scores. This is a sidecar diagnostic and does not change "
            "accepted scorer behavior."
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
    parser.add_argument("--aozora-sqlite", type=Path, default=DEFAULT_AOZORA_SQLITE)
    parser.add_argument("--top-variant-count", type=int, default=16)
    parser.add_argument("--sample-per-band", type=int, default=10)
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
        aozora_sqlite=_resolve_path(args.aozora_sqlite),
        top_variant_count=max(1, int(args.top_variant_count)),
        sample_per_band=max(1, int(args.sample_per_band)),
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
    aozora_sqlite: Path,
    top_variant_count: int,
    sample_per_band: int,
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
    labels = _label_context(
        view=view,
        current_scores=current_scores,
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    aozora = _aozora_feature_arrays(view=view, aozora_sqlite=aozora_sqlite)
    component_signals = _component_signal_arrays(view)
    evidence = _tiebreak_evidence(
        current_scores=current_scores,
        target_positions=np.asarray(view.target_positions, dtype=np.float32),
        aozora=aozora,
        component_signals=component_signals,
    )
    baseline = _variant_result(
        variant={
            "variant_id": "current",
            "description": "Current accepted sidecar candidate; no source-void tiebreak.",
        },
        scores=current_scores,
        current_scores=current_scores,
        labels=labels,
    )
    baseline.update(
        _movement_summary(scores=current_scores, current_scores=current_scores, variant={})
    )
    rows = [baseline]
    variants = _tiebreak_variant_specs()
    for variant in variants:
        scores = _apply_tiebreak_variant(
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
        row.update(_movement_summary(scores=scores, current_scores=current_scores, variant=variant))
        rows.append(row)
    ranked = sorted(
        rows[1:],
        key=lambda row: (
            _optional_float(row.get("selection_score")) or -999.0,
            -(_optional_float(_mapping(row.get("tail60")).get("mae_delta_vs_current")) or 999.0),
            -(_optional_float(_mapping(row.get("tail80")).get("mae_delta_vs_current")) or 999.0),
            -int(row.get("label_regressed_count_0p01") or 0),
        ),
        reverse=True,
    )
    top_rows = ranked[:top_variant_count]
    top_graded_rows = [
        row for row in ranked if str(row.get("strength_mode") or "") == "graded_log"
    ][:top_variant_count]
    legacy_control_rows = [
        row for row in ranked if str(row.get("strength_mode") or "") == "legacy_attestation"
    ][: min(top_variant_count, 8)]
    no_regression_rows = [
        row for row in ranked if int(row.get("label_regressed_count_0p01") or 0) == 0
    ][: min(top_variant_count, 10)]
    aggressive_rows = _aggressive_rows(ranked, limit=8)
    sample_variant_ids = {
        str(row.get("variant_id") or "")
        for row in [
            *top_rows[:4],
            *top_graded_rows[:4],
            *legacy_control_rows[:4],
            *no_regression_rows[:4],
            *aggressive_rows[:4],
        ]
        if row.get("variant_id")
    }
    variant_by_id = {str(row["variant_id"]): row for row in variants}
    samples = {
        variant_id: _variant_samples(
            variant_id=variant_id,
            scores=_apply_tiebreak_variant(
                current_scores=current_scores,
                evidence=evidence,
                variant=variant_by_id[variant_id],
            ),
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            per_band=sample_per_band,
        )
        for variant_id in sample_variant_ids
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
                "Advanced-tail second-pass tiebreaker. The base scorer remains "
                "unchanged; this only tests small capped movement that separates "
                "credible corpus attestation from words absent across broad sources."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "formula": (
                "score = current + eligible(current >= score_floor) * "
                "smoothstep(gate_lower, gate_upper, current)^gate_power * max_move "
                "* (void_weight * source_void - attested_weight * "
                "credible_attestation), clipped to +/- max_move. "
                "legacy controls use the earlier saturated Aozora attestation; "
                "graded variants recompute Aozora strength from token/work counts, "
                "optional per-work token capping, author dispersion, confidence, "
                "a combine mode, and strength curvature before applying exact/lemma "
                "match quality and optional context gates. "
                "No target-curve normalization is applied."
            ),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "aozora_sqlite": _repo_or_home_path(aozora_sqlite),
            "component_count": int(len(current_scores)),
            "score_floor": 0.80,
            "score_floor_component_count": int((current_scores >= 0.80).sum()),
            "label_count": len(labels["rows"]),
            "variant_count": len(variants),
        },
        "baseline": baseline,
        "top_variants": top_rows,
        "top_graded_variants": top_graded_rows,
        "legacy_control_variants": legacy_control_rows,
        "no_regression_variants": no_regression_rows,
        "aggressive_variants": aggressive_rows,
        "variant_samples": samples,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "source_arbitration_json": source_arbitration_json,
                "component_matrix": component_matrix,
                "calibration_json": calibration_json,
                "holdout_json": holdout_json,
                "validation_json": validation_json,
                "aozora_sqlite": aozora_sqlite,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "aozora_tail_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja.py"
                ),
                "aozora_source_void_tiebreak_bakeoff": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _tiebreak_evidence(
    *,
    current_scores: np.ndarray,
    target_positions: np.ndarray,
    aozora: Mapping[str, Any],
    component_signals: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    features = _mapping(aozora.get("features"))
    terms = _tail_variant_terms(
        current_scores=current_scores,
        target_positions=target_positions,
        aozora=aozora,
        component_signals=component_signals,
        variant={
            "variant_id": "evidence_probe",
            "gate_lower": 0.80,
            "gate_upper": 0.94,
            "attestation_lower": 0.02,
            "old_raise": 0.0,
            "missing_raise": 0.04,
            "old_discount": 1.0,
            "lower_dirty_block": 0.0,
            "raise_taper_start": 1.01,
            "raise_taper_strength": 0.0,
            "old_access_block": 0.0,
            "rank_blend": 1.0,
        },
    )
    match_status = np.asarray(aozora.get("match_status"), dtype=str)
    old_literary_risk = np.asarray(features.get("old_literary_risk_context"), dtype=np.float32)
    hard_context = np.asarray(features.get("hard_work_exposure"), dtype=np.float32)
    accessible_context = np.maximum(
        np.asarray(features.get("accessible_work_exposure"), dtype=np.float32),
        np.asarray(features.get("modern_child_accessible_context"), dtype=np.float32),
    )
    return {
        **terms,
        "token_count": np.asarray(aozora.get("token_count"), dtype=np.float32),
        "work_count": np.asarray(aozora.get("work_count"), dtype=np.float32),
        "author_count": np.asarray(aozora.get("author_count"), dtype=np.float32),
        "confidence": np.asarray(features.get("context_confidence"), dtype=np.float32),
        "exact_match": (match_status == "exact_reading").astype(np.float32),
        "lemma_fallback_match": (match_status == "lemma_only_fallback").astype(np.float32),
        "old_literary_risk": np.clip(old_literary_risk, 0.0, 1.0),
        "hard_context": np.clip(hard_context, 0.0, 1.0),
        "accessible_context": np.clip(accessible_context, 0.0, 1.0),
    }


def _tiebreak_variant_specs() -> list[dict[str, Any]]:
    variants = []
    seen: set[str] = set()
    for accessible_bonus_weight in (0.00, 0.25):
        _append_tiebreak_variant(
            variants,
            seen,
            strength_mode="legacy_attestation",
            gate_lower=0.88,
            gate_upper=0.98,
            score_floor=0.80,
            gate_power=2.0,
            max_move=0.035,
            attested_weight=1.25,
            void_weight=0.00,
            old_brake_weight=0.00,
            hard_brake_weight=0.00,
            accessible_bonus_weight=accessible_bonus_weight,
            dirty_block=0.00,
            lemma_fallback_weight=0.50,
        )
    for gate_lower, gate_upper in ((0.88, 0.98),):
        for gate_power in (2.0,):
            for max_move in (0.012, 0.026, 0.035, 0.050):
                for attested_weight in (1.00, 1.25):
                    for void_weight in (0.00,):
                        for old_brake_weight in (0.00, 0.50):
                            for hard_brake_weight in (0.00,):
                                for accessible_bonus_weight in (0.00, 0.25):
                                    for dirty_block in (0.00,):
                                        for lemma_fallback_weight in (0.50,):
                                            for token_reference in (300.0, 1000.0, 3000.0):
                                                for work_reference in (30.0, 80.0, 200.0):
                                                    for combine_mode in (
                                                        "mean",
                                                        "geomean",
                                                        "work_heavy",
                                                    ):
                                                        for strength_power in (0.75, 1.00):
                                                            for per_work_token_cap in (
                                                                0.0,
                                                                2.0,
                                                                4.0,
                                                                8.0,
                                                                16.0,
                                                            ):
                                                                for author_dispersion_weight in (
                                                                    0.0,
                                                                    0.35,
                                                                    0.65,
                                                                ):
                                                                    _append_tiebreak_variant(
                                                                        variants,
                                                                        seen,
                                                                        strength_mode="graded_log",
                                                                        gate_lower=gate_lower,
                                                                        gate_upper=gate_upper,
                                                                        score_floor=0.80,
                                                                        gate_power=gate_power,
                                                                        max_move=max_move,
                                                                        attested_weight=attested_weight,
                                                                        void_weight=void_weight,
                                                                        old_brake_weight=old_brake_weight,
                                                                        hard_brake_weight=hard_brake_weight,
                                                                        accessible_bonus_weight=accessible_bonus_weight,
                                                                        dirty_block=dirty_block,
                                                                        lemma_fallback_weight=lemma_fallback_weight,
                                                                        token_reference=token_reference,
                                                                        work_reference=work_reference,
                                                                        combine_mode=combine_mode,
                                                                        strength_power=strength_power,
                                                                        per_work_token_cap=per_work_token_cap,
                                                                        author_dispersion_weight=author_dispersion_weight,
                                                                    )
    return variants


def _append_tiebreak_variant(
    variants: list[dict[str, Any]],
    seen: set[str],
    *,
    strength_mode: str,
    gate_lower: float,
    gate_upper: float,
    score_floor: float,
    gate_power: float,
    max_move: float,
    attested_weight: float,
    void_weight: float,
    old_brake_weight: float,
    hard_brake_weight: float,
    accessible_bonus_weight: float,
    dirty_block: float,
    lemma_fallback_weight: float,
    token_reference: float = 0.0,
    work_reference: float = 0.0,
    combine_mode: str = "",
    strength_power: float = 1.0,
    per_work_token_cap: float = 0.0,
    author_dispersion_weight: float = 0.0,
) -> None:
    prefix = "aozlegacy" if strength_mode == "legacy_attestation" else "aozgraded"
    variant_id = (
        f"{prefix}_gl{_id_float(gate_lower)}_gu{_id_float(gate_upper)}"
        f"_sf{_id_float(score_floor)}_gp{_id_float(gate_power)}"
        f"_mv{_id_float(max_move)}"
        f"_aw{_id_float(attested_weight)}_vw{_id_float(void_weight)}"
        f"_ob{_id_float(old_brake_weight)}_hb{_id_float(hard_brake_weight)}"
        f"_ab{_id_float(accessible_bonus_weight)}_db{_id_float(dirty_block)}"
        f"_lf{_id_float(lemma_fallback_weight)}"
    )
    if strength_mode == "graded_log":
        variant_id += (
            f"_tr{_id_float(token_reference)}_wr{_id_float(work_reference)}"
            f"_cm{combine_mode}_sp{_id_float(strength_power)}"
            f"_pwc{_id_float(per_work_token_cap)}_adw{_id_float(author_dispersion_weight)}"
        )
    if variant_id in seen:
        return
    seen.add(variant_id)
    variants.append(
        {
            "variant_id": variant_id,
            "description": (
                "Capped advanced-tail source-void tiebreaker: slight credit for "
                "credible exact/optional lemma Aozora attestation. Legacy controls "
                "use saturated attestation; graded variants preserve more variation "
                "from token/work counts."
            ),
            "strength_mode": strength_mode,
            "gate_lower": gate_lower,
            "gate_upper": gate_upper,
            "score_floor": score_floor,
            "gate_power": gate_power,
            "max_move": max_move,
            "attested_weight": attested_weight,
            "void_weight": void_weight,
            "old_brake_weight": old_brake_weight,
            "hard_brake_weight": hard_brake_weight,
            "accessible_bonus_weight": accessible_bonus_weight,
            "dirty_block": dirty_block,
            "lemma_fallback_weight": lemma_fallback_weight,
            "token_reference": token_reference,
            "work_reference": work_reference,
            "combine_mode": combine_mode,
            "strength_power": strength_power,
            "per_work_token_cap": per_work_token_cap,
            "author_dispersion_weight": author_dispersion_weight,
        }
    )


def _apply_tiebreak_variant(
    *,
    current_scores: np.ndarray,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    base_tail_gate = _smoothstep_array(
        float(variant["gate_lower"]),
        float(variant["gate_upper"]),
        np.asarray(current_scores, dtype=np.float32),
    )
    eligible = (
        np.asarray(current_scores, dtype=np.float32) >= float(variant["score_floor"])
    ).astype(np.float32)
    tail_gate = eligible * np.power(base_tail_gate, float(variant["gate_power"]))
    match_quality = np.clip(
        np.asarray(evidence["exact_match"], dtype=np.float32)
        + float(variant["lemma_fallback_weight"])
        * np.asarray(evidence["lemma_fallback_match"], dtype=np.float32),
        0.0,
        1.0,
    )
    old_gate = np.clip(
        1.0
        - float(variant["old_brake_weight"])
        * np.asarray(evidence["old_literary_risk"], dtype=np.float32),
        0.0,
        1.0,
    )
    hard_gate = np.clip(
        1.0
        - float(variant["hard_brake_weight"])
        * np.asarray(evidence["hard_context"], dtype=np.float32),
        0.0,
        1.0,
    )
    dirty_gate = np.clip(
        1.0 - float(variant["dirty_block"]) * np.asarray(evidence["dirty_risk"], dtype=np.float32),
        0.0,
        1.0,
    )
    accessible_bonus = np.clip(
        1.0
        + float(variant["accessible_bonus_weight"])
        * np.asarray(evidence["accessible_context"], dtype=np.float32),
        1.0,
        1.25,
    )
    aozora_strength = _aozora_strength(evidence=evidence, variant=variant)
    attested = np.clip(
        aozora_strength * match_quality * old_gate * hard_gate * dirty_gate * accessible_bonus,
        0.0,
        1.0,
    )
    effective_void = np.clip(
        (1.0 - aozora_strength * match_quality)
        * (1.0 - np.asarray(evidence["known_elsewhere"], dtype=np.float32))
        * np.asarray(evidence["low_cross_source"], dtype=np.float32),
        0.0,
        1.0,
    )
    signal = (
        float(variant["void_weight"]) * effective_void
        - float(variant["attested_weight"]) * attested
    )
    max_move = float(variant["max_move"])
    delta = np.clip(tail_gate * max_move * signal, -max_move, max_move)
    return np.asarray(np.clip(current_scores + delta, 0.0, 1.0), dtype=np.float32)


def _aozora_strength(
    *,
    evidence: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    if str(variant.get("strength_mode") or "") == "legacy_attestation":
        return np.asarray(evidence["attestation"], dtype=np.float32)
    token_reference = max(1.0, float(variant.get("token_reference") or 1000.0))
    work_reference = max(1.0, float(variant.get("work_reference") or 80.0))
    token_count = np.asarray(evidence["token_count"], dtype=np.float32)
    work_count = np.asarray(evidence["work_count"], dtype=np.float32)
    per_work_token_cap = float(variant.get("per_work_token_cap") or 0.0)
    if per_work_token_cap > 0.0:
        effective_token_count = np.minimum(
            token_count,
            work_count * per_work_token_cap,
        )
    else:
        effective_token_count = token_count
    token_strength = np.clip(
        np.log1p(effective_token_count) / np.log1p(token_reference),
        0.0,
        1.0,
    )
    work_strength = np.clip(
        np.log1p(work_count) / np.log1p(work_reference),
        0.0,
        1.0,
    )
    combine_mode = str(variant.get("combine_mode") or "mean")
    if combine_mode == "geomean":
        corpus_strength = np.sqrt(token_strength * work_strength)
    elif combine_mode == "work_heavy":
        corpus_strength = 0.35 * token_strength + 0.65 * work_strength
    else:
        corpus_strength = 0.5 * token_strength + 0.5 * work_strength
    author_strength = np.clip(
        np.log1p(np.asarray(evidence["author_count"], dtype=np.float32)) / np.log1p(12.0),
        0.0,
        1.0,
    )
    author_dispersion_weight = float(variant.get("author_dispersion_weight") or 0.0)
    if author_dispersion_weight > 0.0:
        author_gate = (1.0 - author_dispersion_weight) + author_dispersion_weight * author_strength
        corpus_strength = np.asarray(corpus_strength * author_gate, dtype=np.float32)
    confidence = np.clip(np.asarray(evidence["confidence"], dtype=np.float32), 0.0, 1.0)
    raw_strength = np.clip(confidence * corpus_strength, 0.0, 1.0)
    return np.asarray(
        np.power(raw_strength, float(variant.get("strength_power") or 1.0)),
        dtype=np.float32,
    )


def _movement_summary(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    variant: Mapping[str, Any],
) -> dict[str, Any]:
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    abs_delta = np.abs(delta)
    moved_mask = abs_delta > 0.0005
    moved_count = int(moved_mask.sum())
    max_move = float(variant.get("max_move") or 0.0)
    cap_mask = moved_mask & (abs_delta >= max(0.0, max_move - 1e-5))
    if moved_count == 0:
        return {
            "moved_count": 0,
            "mean_abs_delta": 0.0,
            "p90_abs_delta": 0.0,
            "cap_saturation_count": 0,
            "cap_saturation_rate": 0.0,
        }
    moved_abs = abs_delta[moved_mask]
    return {
        "moved_count": moved_count,
        "mean_abs_delta": _rounded_float(float(moved_abs.mean())),
        "p90_abs_delta": _rounded_float(float(np.quantile(moved_abs, 0.90))),
        "cap_saturation_count": int(cap_mask.sum()),
        "cap_saturation_rate": _rounded_float(float(cap_mask.sum()) / float(moved_count)),
    }


def _aggressive_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    changed = [
        row
        for row in rows
        if int(row.get("label_improved_count_0p01") or 0)
        + int(row.get("label_regressed_count_0p01") or 0)
        > 0
    ]
    return sorted(
        changed,
        key=lambda row: (
            -(_optional_float(_mapping(row.get("tail60")).get("mae_delta_vs_current")) or 999.0),
            -(_optional_float(_mapping(row.get("tail80")).get("mae_delta_vs_current")) or 999.0),
            int(row.get("label_improved_count_0p01") or 0)
            - int(row.get("label_regressed_count_0p01") or 0),
        ),
        reverse=True,
    )[:limit]


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Aozora Source-Void Tiebreak Bakeoff",
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
        "## Baseline",
        "",
        _tiebreak_metric_table([_mapping(report.get("baseline"))]),
        "",
        "## Top Variants",
        "",
        _tiebreak_metric_table(report.get("top_variants") or []),
        "",
        "## Top Graded Variants",
        "",
        _tiebreak_metric_table(report.get("top_graded_variants") or []),
        "",
        "## Legacy Control Variants",
        "",
        _tiebreak_metric_table(report.get("legacy_control_variants") or []),
        "",
        "## No-Regression Variants",
        "",
        _tiebreak_metric_table(report.get("no_regression_variants") or []),
        "",
        "## Aggressive Variants",
        "",
        _tiebreak_metric_table(report.get("aggressive_variants") or []),
        "",
        _regression_profile_table(report.get("aggressive_variants") or []),
        "",
        "## Qualitative Samples",
        "",
    ]
    for variant_id, samples in _mapping(report.get("variant_samples")).items():
        sample_row = _mapping(samples)
        lines.extend(
            [
                f"### `{_escape(variant_id)}`",
                "",
                "Largest down moves:",
                "",
                _sample_table(sample_row.get("largest_down_moves") or []),
                "",
                "Largest up moves:",
                "",
                _sample_table(sample_row.get("largest_up_moves") or []),
                "",
            ]
        )
    lines.extend(
        [
            "## Caveats",
            "",
            "- This pass is intentionally tiny and capped; it is a tiebreaker, not a replacement model.",
            "- No target-curve normalization is applied, so movement is easier to attribute than in the Aozora tail transform.",
            "- Aozora attestation still means book/literary attestation, not direct learner frequency.",
            "",
        ]
    )
    return "\n".join(lines)


def _tiebreak_metric_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Variant | Select | MAE | Pairwise | Tail60 dMAE | Tail80 dMAE | Begin dMAE | Improve | Regress | Moved | Cap% | MeanAbsΔ | Params |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = _mapping(row.get("all_summary"))
        tail60 = _mapping(row.get("tail60"))
        tail80 = _mapping(row.get("tail80"))
        beginner = _mapping(row.get("beginner"))
        params = ", ".join(
            f"{key}={_fmt(row.get(key))}"
            for key in (
                "strength_mode",
                "gate_lower",
                "gate_upper",
                "score_floor",
                "gate_power",
                "max_move",
                "attested_weight",
                "void_weight",
                "old_brake_weight",
                "hard_brake_weight",
                "accessible_bonus_weight",
                "dirty_block",
                "lemma_fallback_weight",
                "token_reference",
                "work_reference",
                "combine_mode",
                "strength_power",
                "per_work_token_cap",
                "author_dispersion_weight",
            )
            if key in row
        )
        cells = [
            str(row.get("variant_id") or ""),
            _fmt(row.get("selection_score")),
            _fmt(summary.get("mae")),
            _fmt(summary.get("pairwise_accuracy")),
            _fmt(tail60.get("mae_delta_vs_current")),
            _fmt(tail80.get("mae_delta_vs_current")),
            _fmt(beginner.get("mae_delta_vs_current")),
            str(row.get("label_improved_count_0p01") or 0),
            str(row.get("label_regressed_count_0p01") or 0),
            str(row.get("moved_count") or 0),
            _fmt(row.get("cap_saturation_rate")),
            _fmt(row.get("mean_abs_delta")),
            params,
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _rounded_float(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _fmt(value: Any) -> str:
    if isinstance(value, str):
        return value
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _id_float(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", "")


if __name__ == "__main__":
    raise SystemExit(main())
