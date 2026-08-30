#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _escape,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    _calibration_context,
    _load_holdout_rows,
    _refresh_context_expected_from_label_json,
    _view_with_target_curve_override,
    family_parts,
    generate_candidates,
    holdout_context_from_rows,
    metrics_for_context,
    normalized_scores_for_candidate,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)


PAIR = "en-ja"
DATA_ROOT = Path.home() / "Library" / "Application Support" / "LexiShift" / "LexiShift"
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
DEFAULT_ACCEPTANCE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_acceptance_first60_en_ja_latest.json"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_VALIDATION_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_stitch_validation_labels_en_ja.json"
)
DEFAULT_HOLDOUT_REVIEW_MARKDOWN = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_holdout_review_en_ja.md"
)
DEFAULT_WORKING_SET_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_litmus_working_set_en_ja_latest.json"
)
DEFAULT_BCCWJ_SQLITE = DATA_ROOT / "frequency_packs" / "freq-ja-bccwj" / "main.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_targeted_signal_bakeoff_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_targeted_signal_bakeoff_en_ja_latest.md"
)
ASCIIISH_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 .'+/_-]*$")
FUNCTION_POS_PREFIXES = ("助詞", "助動詞", "補助記号", "空白")
FIRST60_CUTOFF = 0.70


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sidecar bakeoff for three targeted en-ja difficulty improvements: "
            "base/family rescue, gairaigo source ease, and domain/marked bucket caps."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--acceptance-json", type=Path, default=DEFAULT_ACCEPTANCE_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument(
        "--holdout-review-markdown",
        type=Path,
        default=DEFAULT_HOLDOUT_REVIEW_MARKDOWN,
    )
    parser.add_argument("--working-set-json", type=Path, default=DEFAULT_WORKING_SET_JSON)
    parser.add_argument("--bccwj-sqlite", type=Path, default=DEFAULT_BCCWJ_SQLITE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        acceptance_json_path=_resolve_path(args.acceptance_json),
        calibration_json_path=_resolve_path(args.calibration_json),
        holdout_json_path=_resolve_path(args.holdout_json),
        validation_json_path=_resolve_path(args.validation_json),
        holdout_review_markdown_path=_resolve_path(args.holdout_review_markdown),
        working_set_json_path=_resolve_path(args.working_set_json),
        bccwj_sqlite_path=_resolve_path(args.bccwj_sqlite),
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
    acceptance_json_path: Path,
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
    holdout_review_markdown_path: Path,
    working_set_json_path: Path,
    bccwj_sqlite_path: Path,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    view = _view_with_target_curve_override(
        ComponentView.from_npz(component),
        target_curve_override="warp_p60_g155",
    )
    parts = family_parts(view)
    baseline_candidate_id = _acceptance_candidate_id(acceptance_json_path)
    baseline_candidate = _baseline_candidate(baseline_candidate_id)
    baseline_scores = np.asarray(
        normalized_scores_for_candidate(baseline_candidate, view, parts=parts),
        dtype=np.float32,
    )
    contexts = _contexts(
        component=component,
        calibration=calibration,
        baseline_scores=baseline_scores,
        calibration_json_path=calibration_json_path,
        holdout_json_path=holdout_json_path,
        validation_json_path=validation_json_path,
        holdout_review_markdown_path=holdout_review_markdown_path,
    )
    signals = build_targeted_signals(
        view=view,
        baseline_scores=baseline_scores,
        bccwj_sqlite_path=bccwj_sqlite_path,
    )
    variants = generate_variants()
    evaluated = []
    for variant in variants:
        scores = apply_variant(baseline_scores, signals=signals, variant=variant)
        evaluated.append(
            variant_result(
                variant,
                scores=scores,
                baseline_scores=baseline_scores,
                contexts=contexts,
                view=view,
                signals=signals,
                working_set_json_path=working_set_json_path,
            )
        )
    sorted_results = sorted(
        evaluated,
        key=lambda result: (
            _metric(result, "holdout", "balanced_score"),
            _metric(result, "first60_all_labels", "numeric_mae_score"),
            _metric(result, "all_labels", "numeric_mae_score"),
        ),
        reverse=True,
    )
    baseline_result = next(result for result in evaluated if result["variant_id"] == "baseline")
    best_result = sorted_results[0]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "sweeps_run": True,
        "method": {
            "purpose": (
                "Strict sidecar bakeoff for three targeted low-hanging-fruit "
                "hypotheses. The production model is not changed."
            ),
            "baseline_candidate_id": baseline_candidate_id,
            "target_curve_override": "warp_p60_g155",
            "tested_hypotheses": {
                "base_family_rescue": (
                    "If Sudachi reduces an exact surface to a dictionary base and "
                    "that base is scored materially easier, softly cap the surface "
                    "near the base score plus a swept margin."
                ),
                "gairaigo_source_ease": (
                    "If BCCWJ exposes an ASCII source/sublemma for gairaigo, use "
                    "English wordfreq Zipf as a familiarity clue and sweep a small "
                    "downward delta."
                ),
                "domain_marked_bucket": (
                    "If JMDict/component signals indicate domain/register/marked "
                    "usage, sweep a soft upper bucket so advanced terms do not "
                    "automatically saturate near 1.0. The refined modes separate "
                    "strict JMDict-backed domain/marked evidence from the broader "
                    "BCCWJ profile-domain signal."
                ),
            },
            "acceptance_policy": (
                "Accept only variants with a clear diagnostic benefit, no obvious "
                "labeled regression, and no first-60 degradation versus baseline."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "acceptance_json": _repo_or_home_path(acceptance_json_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "validation_json": _repo_or_home_path(validation_json_path),
            "working_set_json": _repo_or_home_path(working_set_json_path),
            "bccwj_sqlite": _repo_or_home_path(bccwj_sqlite_path),
            "component_count": int(len(view.frequency)),
            "variant_count": int(len(variants)),
        },
        "signal_coverage": signal_coverage(signals),
        "summary": {
            "baseline": _summary_row(baseline_result),
            "best": _summary_row(best_result),
            "clear_winners": [
                _summary_row(result)
                for result in sorted_results
                if result.get("recommendation") == "clear_benefit"
            ][:10],
            "near_winners": [
                _summary_row(result)
                for result in sorted_results
                if result.get("recommendation") == "mixed_or_tiny"
            ][:10],
        },
        "leaderboard": [_summary_row(result) for result in sorted_results[:25]],
        "baseline_result": baseline_result,
        "best_result": best_result,
        "variant_results": evaluated,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "acceptance_json": acceptance_json_path,
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "validation_json": validation_json_path,
                "working_set_json": working_set_json_path,
                "bccwj_sqlite": bccwj_sqlite_path,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "targeted_signal_bakeoff": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def build_targeted_signals(
    *,
    view: ComponentView,
    baseline_scores: object,
    bccwj_sqlite_path: Path,
) -> dict[str, object]:
    lemmas = [str(value) for value in view.lemmas]
    sudachi = SudachiBaseAnalyzer()
    base_terms = [sudachi.base_for_surface(lemma) for lemma in lemmas]
    terms = set(lemmas) | {term for term in base_terms if term}
    bccwj = load_bccwj_rows(bccwj_sqlite_path, terms)
    lemma_best_baseline = _best_baseline_by_lemma(lemmas, baseline_scores)

    count = len(lemmas)
    base_score = np.full(count, np.nan, dtype=np.float32)
    base_bccwj_pmw_gain = np.zeros(count, dtype=np.float32)
    base_bccwj_rank_gain = np.zeros(count, dtype=np.float32)
    base_family_gate = np.zeros(count, dtype=np.float32)
    gairaigo_origin_ease = np.zeros(count, dtype=np.float32)
    gairaigo_origin_known = np.zeros(count, dtype=np.float32)
    for index, lemma in enumerate(lemmas):
        base = base_terms[index]
        if base:
            if base in lemma_best_baseline:
                base_score[index] = float(lemma_best_baseline[base])
            exact_row = bccwj.best_by_lemma.get(lemma)
            base_row = bccwj.best_by_lemma.get(base)
            base_bccwj_pmw_gain[index] = _ratio_gain(
                _pmw_value(base_row),
                _pmw_value(exact_row),
            )
            base_bccwj_rank_gain[index] = _ratio_gain(
                _rank_value(exact_row),
                _rank_value(base_row),
            )
            score_gap = (
                float(baseline_scores[index]) - float(base_score[index])
                if np.isfinite(base_score[index])
                else 0.0
            )
            corpus_gate = max(
                _ramp_scalar(base_bccwj_pmw_gain[index], lower=2.0, upper=12.0),
                _ramp_scalar(base_bccwj_rank_gain[index], lower=2.0, upper=8.0),
            )
            score_gate = _ramp_scalar(score_gap, lower=0.08, upper=0.30)
            base_family_gate[index] = max(corpus_gate, score_gate)
        exact_row = bccwj.best_by_lemma.get(lemma)
        if exact_row and str(exact_row.get("wtype") or "") == "外":
            sublemma = str(exact_row.get("sublemma") or "").strip()
            if ASCIIISH_RE.match(sublemma):
                zipf = english_zipf(sublemma)
                if zipf is not None and zipf > 0.0:
                    gairaigo_origin_known[index] = 1.0
                    gairaigo_origin_ease[index] = _ramp_scalar(zipf, lower=2.6, upper=5.0)

    domain_signal = _max_components(
        view,
        (
            "jmdict_field_marked_risk",
            "jmdict_register_domain_risk",
            "jmdict_sense_info_risk",
            "gairaigo_domain_source_risk",
            "bccwj_domain_profile_risk",
        ),
    )
    marked_signal = _max_components(
        view,
        (
            "jmdict_marked_usage_risk",
            "jmdict_register_marked_risk",
            "jmdict_dialect_risk",
            "jmdict_abbreviation_risk",
            "jmdict_search_only_form_risk",
            "rare_wago_marked_usage_risk",
        ),
    )
    exact_ped_known = _max_components(
        view,
        (
            "jlpt_vocab_effective_exact_known",
            "jlpt_vocab_exact_known",
            "lesson_vocab_known",
        ),
    )
    gairaigo_component = np.nan_to_num(
        np.asarray(view.value("wtype_gairaigo_risk", fill=0.0), dtype=np.float32),
        nan=0.0,
    )
    non_english_component = _max_components(
        view,
        (
            "gairaigo_non_english_source_risk",
            "jmdict_non_english_loan_source_flag",
        ),
    )
    jmdict_domain_signal = _max_components(
        view,
        (
            "jmdict_field_marked_risk",
            "jmdict_register_domain_risk",
            "jmdict_sense_info_risk",
            "gairaigo_domain_source_risk",
        ),
    )
    jmdict_marked_signal = _max_components(
        view,
        (
            "jmdict_marked_usage_risk",
            "jmdict_register_marked_risk",
            "jmdict_dialect_risk",
            "jmdict_abbreviation_risk",
            "jmdict_search_only_form_risk",
            "rare_wago_marked_usage_risk",
        ),
    )
    return {
        "base_terms": base_terms,
        "base_score": base_score,
        "base_family_gate": base_family_gate,
        "base_bccwj_pmw_gain": base_bccwj_pmw_gain,
        "base_bccwj_rank_gain": base_bccwj_rank_gain,
        "gairaigo_origin_ease": (
            gairaigo_origin_ease * np.clip(gairaigo_component, 0.0, 1.0)
        ).astype(np.float32),
        "gairaigo_origin_known": gairaigo_origin_known,
        "gairaigo_component": gairaigo_component,
        "gairaigo_non_english": non_english_component,
        "domain_signal": domain_signal,
        "marked_signal": marked_signal,
        "domain_or_marked_signal": np.maximum(domain_signal, marked_signal).astype(np.float32),
        "jmdict_domain_signal": jmdict_domain_signal,
        "jmdict_marked_signal": jmdict_marked_signal,
        "jmdict_domain_or_marked_signal": np.maximum(
            jmdict_domain_signal,
            jmdict_marked_signal,
        ).astype(np.float32),
        "exact_ped_known": exact_ped_known,
    }


class SudachiBaseAnalyzer:
    def __init__(self) -> None:
        from sudachipy import dictionary, tokenizer

        self.tokenizer = dictionary.Dictionary().create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

    def base_for_surface(self, surface: str) -> str | None:
        try:
            tokens = self.tokenizer.tokenize(surface, self.mode)
        except Exception:
            return None
        content = [
            token
            for token in tokens
            if not "-".join(part for part in token.part_of_speech() if part != "*").startswith(
                FUNCTION_POS_PREFIXES
            )
        ]
        if len(content) != 1:
            return None
        base = str(content[0].dictionary_form())
        if not base or base == surface:
            return None
        return base


class BccwjRows:
    def __init__(self, rows: Sequence[Mapping[str, object]]) -> None:
        best_by_lemma: dict[str, Mapping[str, object]] = {}
        for row in rows:
            lemma = str(row.get("lemma") or "")
            if not lemma:
                continue
            current = best_by_lemma.get(lemma)
            if current is None or _sort_rank(row) < _sort_rank(current):
                best_by_lemma[lemma] = row
        self.best_by_lemma = best_by_lemma


def load_bccwj_rows(sqlite_path: Path, terms: set[str]) -> BccwjRows:
    if not sqlite_path.exists():
        return BccwjRows(())
    con = sqlite3.connect(sqlite_path)
    con.row_factory = sqlite3.Row
    rows: list[dict[str, object]] = []
    try:
        for chunk in _chunks(sorted(terms), size=800):
            placeholders = ",".join("?" for _ in chunk)
            query = f"""
                SELECT rank, lemma, sublemma, wtype, pmw, core_rank, core_pmw
                FROM frequency
                WHERE lemma IN ({placeholders})
            """
            for row in con.execute(query, chunk):
                rows.append({key: row[key] for key in row.keys()})
    finally:
        con.close()
    return BccwjRows(rows)


def generate_variants() -> list[dict[str, object]]:
    variants: list[dict[str, object]] = [
        {
            "variant_id": "baseline",
            "family_margin": None,
            "family_strength": 0.0,
            "gairaigo_delta": 0.0,
            "gairaigo_mode": "none",
            "domain_cap": None,
            "domain_strength": 0.0,
            "domain_mode": "none",
        }
    ]
    family_specs = [(None, 0.0)]
    family_specs.extend(
        (margin, strength) for margin in (0.06, 0.10, 0.14) for strength in (0.5, 1.0)
    )
    gairaigo_specs = [("none", 0.0)]
    gairaigo_specs.extend(
        (mode, delta)
        for mode in ("ascii_origin", "ascii_origin_english_only")
        for delta in (0.02, 0.04, 0.06, 0.08)
    )
    domain_specs = [("none", None, 0.0)]
    domain_specs.extend(
        (mode, cap, strength)
        for mode in (
            "domain",
            "marked",
            "domain_or_marked",
            "jmdict_domain",
            "jmdict_marked",
            "jmdict_domain_or_marked",
        )
        for cap in (0.82, 0.86, 0.90, 0.94)
        for strength in (0.5, 1.0)
    )
    for family_margin, family_strength in family_specs:
        for gairaigo_mode, gairaigo_delta in gairaigo_specs:
            for domain_mode, domain_cap, domain_strength in domain_specs:
                if family_margin is None and gairaigo_delta <= 0.0 and domain_cap is None:
                    continue
                variant_id = _variant_id(
                    family_margin=family_margin,
                    family_strength=family_strength,
                    gairaigo_mode=gairaigo_mode,
                    gairaigo_delta=gairaigo_delta,
                    domain_mode=domain_mode,
                    domain_cap=domain_cap,
                    domain_strength=domain_strength,
                )
                variants.append(
                    {
                        "variant_id": variant_id,
                        "family_margin": family_margin,
                        "family_strength": family_strength,
                        "gairaigo_delta": gairaigo_delta,
                        "gairaigo_mode": gairaigo_mode,
                        "domain_cap": domain_cap,
                        "domain_strength": domain_strength,
                        "domain_mode": domain_mode,
                    }
                )
    return variants


def apply_variant(
    baseline_scores: object,
    *,
    signals: Mapping[str, object],
    variant: Mapping[str, object],
) -> object:
    scores = np.asarray(baseline_scores, dtype=np.float32).copy()
    family_margin = _optional_float(variant.get("family_margin"))
    family_strength = float(variant.get("family_strength") or 0.0)
    if family_margin is not None and family_strength > 0.0:
        base_score = np.asarray(signals["base_score"], dtype=np.float32)
        gate = np.asarray(signals["base_family_gate"], dtype=np.float32)
        valid = np.isfinite(base_score) & (gate > 0.0)
        target = np.clip(base_score + family_margin, 0.0, 1.0)
        over = np.maximum(scores - target, 0.0)
        scores[valid] = scores[valid] - (family_strength * gate[valid] * over[valid])

    gairaigo_delta = float(variant.get("gairaigo_delta") or 0.0)
    gairaigo_mode = str(variant.get("gairaigo_mode") or "none")
    if gairaigo_delta > 0.0 and gairaigo_mode != "none":
        ease = np.asarray(signals["gairaigo_origin_ease"], dtype=np.float32)
        if gairaigo_mode == "ascii_origin":
            gate = ease
        elif gairaigo_mode == "ascii_origin_english_only":
            gate = ease * np.clip(
                1.0 - np.asarray(signals["gairaigo_non_english"], dtype=np.float32),
                0.0,
                1.0,
            )
        else:
            raise ValueError(f"Unsupported gairaigo mode: {gairaigo_mode}")
        scores = scores - (gairaigo_delta * gate)

    domain_cap = _optional_float(variant.get("domain_cap"))
    domain_strength = float(variant.get("domain_strength") or 0.0)
    domain_mode = str(variant.get("domain_mode") or "none")
    if domain_cap is not None and domain_strength > 0.0 and domain_mode != "none":
        if domain_mode == "domain":
            gate = np.asarray(signals["domain_signal"], dtype=np.float32)
        elif domain_mode == "marked":
            gate = np.asarray(signals["marked_signal"], dtype=np.float32)
        elif domain_mode == "domain_or_marked":
            gate = np.asarray(signals["domain_or_marked_signal"], dtype=np.float32)
        elif domain_mode == "jmdict_domain":
            gate = np.asarray(signals["jmdict_domain_signal"], dtype=np.float32)
        elif domain_mode == "jmdict_marked":
            gate = np.asarray(signals["jmdict_marked_signal"], dtype=np.float32)
        elif domain_mode == "jmdict_domain_or_marked":
            gate = np.asarray(signals["jmdict_domain_or_marked_signal"], dtype=np.float32)
        else:
            raise ValueError(f"Unsupported domain mode: {domain_mode}")
        cap = domain_cap + ((1.0 - domain_cap) * (1.0 - np.clip(gate, 0.0, 1.0)))
        over = np.maximum(scores - cap, 0.0)
        scores = scores - (domain_strength * over)

    return np.clip(scores, 0.0, 1.0).astype(np.float32)


def variant_result(
    variant: Mapping[str, object],
    *,
    scores: object,
    baseline_scores: object,
    contexts: Mapping[str, Mapping[str, object]],
    view: ComponentView,
    signals: Mapping[str, object],
    working_set_json_path: Path,
) -> dict[str, object]:
    dataset_metrics = {
        name: metrics_for_context(scores, context)["scores"] for name, context in contexts.items()
    }
    baseline_metrics = {
        name: metrics_for_context(baseline_scores, context)["scores"]
        for name, context in contexts.items()
    }
    changed = np.abs(
        np.asarray(scores, dtype=np.float32) - np.asarray(baseline_scores, dtype=np.float32)
    )
    changed_mask = changed > 0.00001
    result = {
        **dict(variant),
        "metrics": dataset_metrics,
        "metric_deltas": _metric_deltas(dataset_metrics, baseline_metrics),
        "changed_count": int(changed_mask.sum()),
        "changed_first60_count": int(
            (changed_mask & (np.asarray(baseline_scores, dtype=np.float32) <= FIRST60_CUTOFF)).sum()
        ),
        "max_abs_score_change": _rounded(float(changed.max())) if len(changed) else 0.0,
    }
    result["diagnostics"] = {
        "working_set": working_set_impact(
            scores=scores,
            baseline_scores=baseline_scores,
            view=view,
            working_set_json_path=working_set_json_path,
        ),
        "top_improvements": top_error_deltas(
            scores=scores,
            baseline_scores=baseline_scores,
            context=contexts["all_labels"],
            direction="improved",
            limit=12,
        ),
        "top_regressions": top_error_deltas(
            scores=scores,
            baseline_scores=baseline_scores,
            context=contexts["all_labels"],
            direction="regressed",
            limit=12,
        ),
        "signal_changed_counts": signal_changed_counts(
            changed_mask=changed_mask,
            signals=signals,
        ),
    }
    result["recommendation"] = recommendation(result)
    return result


def recommendation(result: Mapping[str, object]) -> str:
    if result.get("variant_id") == "baseline":
        return "baseline"
    deltas = _mapping(result.get("metric_deltas"))
    holdout_delta = _score_delta(deltas, "holdout", "balanced_score")
    first60_delta = _score_delta(deltas, "first60_all_labels", "numeric_mae_score")
    all_delta = _score_delta(deltas, "all_labels", "numeric_mae_score")
    regressions = _rows(_mapping(result.get("diagnostics")).get("top_regressions"))
    large_regressions = [
        row for row in regressions if float(row.get("error_delta") or 0.0) >= 0.035
    ]
    working_set = _rows(_mapping(result.get("diagnostics")).get("working_set"))
    intended_improvements = [
        row for row in working_set if float(row.get("error_delta") or 0.0) < -0.025
    ]
    if (
        holdout_delta >= -0.0005
        and first60_delta >= -0.0005
        and all_delta >= -0.0005
        and not large_regressions
        and intended_improvements
    ):
        return "clear_benefit"
    if (
        holdout_delta >= -0.002
        and first60_delta >= -0.002
        and all_delta >= -0.002
        and intended_improvements
    ):
        return "mixed_or_tiny"
    return "reject_or_research"


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    baseline = _mapping(summary.get("baseline"))
    best = _mapping(summary.get("best"))
    lines = [
        "# en-ja Targeted Signal Bakeoff",
        "",
        f"- Generated: `{_escape(str(report.get('generated_at')))}`",
        "- Runtime/model behavior changed: `false`",
        f"- Variants tested: `{_escape(str(_mapping(report.get('inputs')).get('variant_count')))}`",
        f"- Baseline: `{_escape(str(_mapping(report.get('method')).get('baseline_candidate_id')))}`",
        "",
        "## Headline",
        "",
        f"- Baseline holdout balanced: `{_fmt_metric(baseline, 'holdout', 'balanced_score')}`",
        f"- Best holdout balanced: `{_fmt_metric(best, 'holdout', 'balanced_score')}`",
        f"- Best recommendation: `{_escape(str(best.get('recommendation')))}`",
        f"- Best variant: `{_escape(str(best.get('variant_id')))}`",
        "",
        "## Signal Coverage",
        "",
        "```json",
        json.dumps(report.get("signal_coverage"), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Leaderboard",
        "",
        "| Variant | Rec | Holdout bal | Δ holdout | First60 MAE score Δ | All-label MAE score Δ | Changed | Changed ≤0.70 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in _rows(report.get("leaderboard"))[:20]:
        lines.append(
            "| "
            f"`{_escape(str(row.get('variant_id')))}` | "
            f"`{_escape(str(row.get('recommendation')))}` | "
            f"{_fmt_metric(row, 'holdout', 'balanced_score')} | "
            f"{_fmt_delta(row, 'holdout', 'balanced_score')} | "
            f"{_fmt_delta(row, 'first60_all_labels', 'numeric_mae_score')} | "
            f"{_fmt_delta(row, 'all_labels', 'numeric_mae_score')} | "
            f"{row.get('changed_count')} | "
            f"{row.get('changed_first60_count')} |"
        )
    lines.extend(
        [
            "",
            "## Best Variant Working Set Impact",
            "",
            "| Row | Expected | Baseline | Candidate | Error Δ | Signals |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _rows(_mapping(report.get("best_result")).get("diagnostics", {})):
        pass
    best_working = _rows(
        _mapping(_mapping(report.get("best_result")).get("diagnostics")).get("working_set")
    )
    for row in best_working:
        lines.append(
            "| "
            f"`{_escape(str(row.get('label')))}` | "
            f"{_fmt_float(row.get('expected'))} | "
            f"{_fmt_float(row.get('baseline_score'))} | "
            f"{_fmt_float(row.get('candidate_score'))} | "
            f"{_fmt_signed(row.get('error_delta'))} | "
            f"{_escape(str(row.get('hint')))} |"
        )
    lines.extend(
        [
            "",
            "## Best Variant Regressions",
            "",
            "| Row | Expected | Baseline | Candidate | Error Δ |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _rows(
        _mapping(_mapping(report.get("best_result")).get("diagnostics")).get("top_regressions")
    )[:12]:
        lines.append(
            "| "
            f"`{_escape(str(row.get('label')))}` | "
            f"{_fmt_float(row.get('expected'))} | "
            f"{_fmt_float(row.get('baseline_score'))} | "
            f"{_fmt_float(row.get('candidate_score'))} | "
            f"{_fmt_signed(row.get('error_delta'))} |"
        )
    lines.extend(
        [
            "",
            "## Clear Winners",
            "",
        ]
    )
    clear_winners = _rows(summary.get("clear_winners"))
    if not clear_winners:
        lines.append("No variant met the strict `clear_benefit` rule.")
    else:
        for row in clear_winners[:10]:
            lines.append(
                "- "
                f"`{_escape(str(row.get('variant_id')))}` "
                f"holdout `{_fmt_metric(row, 'holdout', 'balanced_score')}`, "
                f"first60 Δ `{_fmt_delta(row, 'first60_all_labels', 'numeric_mae_score')}`"
            )
    lines.append("")
    return "\n".join(lines)


def _contexts(
    *,
    component: object,
    calibration: object,
    baseline_scores: object,
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
    holdout_review_markdown_path: Path,
) -> dict[str, Mapping[str, object]]:
    calibration_context = _refresh_context_expected_from_label_json(
        _calibration_context(calibration, component),
        calibration_json_path,
    )
    holdout_context = holdout_context_from_rows(
        _load_holdout_rows(holdout_json_path, fallback_markdown=holdout_review_markdown_path),
        component,
    )
    validation_context = label_context_from_json(validation_json_path, component)
    all_context = concat_contexts(
        {
            "calibration": calibration_context,
            "holdout": holdout_context,
            "stitch_validation": validation_context,
        }
    )
    return {
        "calibration": calibration_context,
        "holdout": holdout_context,
        "stitch_validation": validation_context,
        "all_labels": all_context,
        "first60_all_labels": filter_first60_context(all_context, baseline_scores),
    }


def label_context_from_json(path: Path, component: object) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    lookup = component_lookup(component)
    indices = []
    expected_values = []
    expected_bands = []
    expected_states = []
    observed_states = []
    labels = []
    for label in payload.get("labels") or []:
        if not isinstance(label, Mapping):
            continue
        expected = _optional_float(label.get("expected_learner_difficulty"))
        if expected is None:
            continue
        lemma = str(label.get("lemma") or "")
        reading = str(label.get("expected_reading") or "")
        index = lookup.get((lemma, reading), lookup.get((lemma, ""), -1))
        labels.append(f"{lemma}/{reading}" if reading else lemma)
        indices.append(index)
        expected_values.append(float(expected))
        expected_bands.append(_difficulty_band(float(expected)))
        expected_states.append(str(label.get("expected_candidate_state") or "normal_vocab"))
        observed_states.append(
            str(component["candidate_states"][index]) if index >= 0 else "missing"
        )
    return {
        "component_indices": np.asarray(indices, dtype=np.int64),
        "expected_values": np.asarray(expected_values, dtype=np.float32),
        "expected_bands": expected_bands,
        "expected_candidate_states": expected_states,
        "observed_candidate_states": observed_states,
        "labels": labels,
    }


def concat_contexts(contexts: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    indices = []
    expected_values = []
    expected_bands = []
    expected_states = []
    observed_states = []
    labels = []
    for name, context in contexts.items():
        indices.extend(np.asarray(context["component_indices"], dtype=np.int64).tolist())
        expected_values.extend(np.asarray(context["expected_values"], dtype=np.float32).tolist())
        expected_bands.extend(list(context["expected_bands"]))
        context_expected_states = context.get("expected_candidate_states")
        context_observed_states = context.get("observed_candidate_states")
        expected_states.extend(
            list(context_expected_states) if context_expected_states is not None else []
        )
        observed_states.extend(
            list(context_observed_states) if context_observed_states is not None else []
        )
        labels.extend([f"{name}:{label}" for label in context["labels"]])
    return {
        "component_indices": np.asarray(indices, dtype=np.int64),
        "expected_values": np.asarray(expected_values, dtype=np.float32),
        "expected_bands": expected_bands,
        "expected_candidate_states": expected_states,
        "observed_candidate_states": observed_states,
        "labels": labels,
    }


def filter_first60_context(
    context: Mapping[str, object],
    baseline_scores: object,
) -> dict[str, object]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    baseline = np.full(len(indices), np.nan, dtype=np.float32)
    valid = indices >= 0
    baseline[valid] = np.asarray(baseline_scores, dtype=np.float32)[indices[valid]]
    keep = (expected <= FIRST60_CUTOFF) | (baseline <= FIRST60_CUTOFF)
    positions = np.flatnonzero(keep)
    return {
        "component_indices": indices[positions],
        "expected_values": expected[positions],
        "expected_bands": [context["expected_bands"][int(pos)] for pos in positions],
        "expected_candidate_states": [
            _sequence_value(context.get("expected_candidate_states"), int(pos)) for pos in positions
        ],
        "observed_candidate_states": [
            _sequence_value(context.get("observed_candidate_states"), int(pos)) for pos in positions
        ],
        "labels": [context["labels"][int(pos)] for pos in positions],
    }


def working_set_impact(
    *,
    scores: object,
    baseline_scores: object,
    view: ComponentView,
    working_set_json_path: Path,
) -> list[dict[str, object]]:
    if not working_set_json_path.exists():
        return []
    payload = json.loads(working_set_json_path.read_text(encoding="utf-8"))
    lookup = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings, strict=False))
    }
    rows = []
    for row in payload.get("working_set") or []:
        if not isinstance(row, Mapping) or not row.get("found"):
            continue
        lemma = str(row.get("lemma") or "")
        reading = str(row.get("reading") or "")
        index = lookup.get((lemma, reading))
        if index is None:
            continue
        expected = _optional_float(
            _mapping(row.get("expected_label")).get(
                "expected_learner_difficulty",
                _mapping(row.get("expected_label")).get("expected"),
            )
        )
        baseline = float(np.asarray(baseline_scores, dtype=np.float32)[index])
        candidate = float(np.asarray(scores, dtype=np.float32)[index])
        baseline_error = None if expected is None else abs(baseline - expected)
        candidate_error = None if expected is None else abs(candidate - expected)
        key_summary = _mapping(row.get("key_signal_summary"))
        rows.append(
            {
                "group": row.get("group"),
                "label": f"{lemma}/{reading}",
                "expected": _rounded(expected) if expected is not None else None,
                "baseline_score": _rounded(baseline),
                "candidate_score": _rounded(candidate),
                "score_delta": _rounded(candidate - baseline),
                "error_delta": (
                    _rounded(candidate_error - baseline_error)
                    if baseline_error is not None and candidate_error is not None
                    else None
                ),
                "hint": (
                    f"rarity={_rounded(key_summary.get('rarity_mean'))}; "
                    f"marked={_rounded(key_summary.get('marked_or_form_risk'))}; "
                    f"domain={_rounded(key_summary.get('domain_or_register_risk'))}; "
                    f"gairaigo={_rounded(key_summary.get('gairaigo_or_loan_risk'))}"
                ),
            }
        )
    return rows


def top_error_deltas(
    *,
    scores: object,
    baseline_scores: object,
    context: Mapping[str, object],
    direction: str,
    limit: int,
) -> list[dict[str, object]]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    valid = (indices >= 0) & np.isfinite(expected)
    labels = list(context["labels"])
    baseline_observed = np.asarray(baseline_scores, dtype=np.float32)[indices[valid]]
    candidate_observed = np.asarray(scores, dtype=np.float32)[indices[valid]]
    expected_valid = expected[valid]
    error_delta = np.abs(candidate_observed - expected_valid) - np.abs(
        baseline_observed - expected_valid
    )
    valid_positions = np.flatnonzero(valid)
    if direction == "improved":
        order = np.argsort(error_delta)
    elif direction == "regressed":
        order = np.argsort(-error_delta)
    else:
        raise ValueError(f"Unsupported direction: {direction}")
    rows = []
    for rel_pos in order[:limit]:
        source_pos = int(valid_positions[int(rel_pos)])
        rows.append(
            {
                "label": labels[source_pos],
                "expected": _rounded(float(expected[source_pos])),
                "baseline_score": _rounded(float(baseline_observed[int(rel_pos)])),
                "candidate_score": _rounded(float(candidate_observed[int(rel_pos)])),
                "score_delta": _rounded(
                    float(candidate_observed[int(rel_pos)] - baseline_observed[int(rel_pos)])
                ),
                "error_delta": _rounded(float(error_delta[int(rel_pos)])),
            }
        )
    return rows


def signal_changed_counts(
    *,
    changed_mask: object,
    signals: Mapping[str, object],
) -> dict[str, int]:
    changed = np.asarray(changed_mask, dtype=bool)
    return {
        "base_family_changed": int(
            (changed & (np.asarray(signals["base_family_gate"], dtype=np.float32) > 0.0)).sum()
        ),
        "gairaigo_origin_changed": int(
            (changed & (np.asarray(signals["gairaigo_origin_ease"], dtype=np.float32) > 0.0)).sum()
        ),
        "domain_changed": int(
            (changed & (np.asarray(signals["domain_signal"], dtype=np.float32) > 0.0)).sum()
        ),
        "marked_changed": int(
            (changed & (np.asarray(signals["marked_signal"], dtype=np.float32) > 0.0)).sum()
        ),
        "jmdict_domain_changed": int(
            (changed & (np.asarray(signals["jmdict_domain_signal"], dtype=np.float32) > 0.0)).sum()
        ),
        "jmdict_marked_changed": int(
            (changed & (np.asarray(signals["jmdict_marked_signal"], dtype=np.float32) > 0.0)).sum()
        ),
    }


def signal_coverage(signals: Mapping[str, object]) -> dict[str, int]:
    return {
        "base_family_gate_rows": int(
            (np.asarray(signals["base_family_gate"], dtype=np.float32) > 0.0).sum()
        ),
        "base_family_score_rows": int(np.isfinite(np.asarray(signals["base_score"])).sum()),
        "gairaigo_origin_ease_rows": int(
            (np.asarray(signals["gairaigo_origin_ease"], dtype=np.float32) > 0.0).sum()
        ),
        "gairaigo_origin_known_rows": int(
            (np.asarray(signals["gairaigo_origin_known"], dtype=np.float32) > 0.0).sum()
        ),
        "domain_signal_rows": int(
            (np.asarray(signals["domain_signal"], dtype=np.float32) > 0.0).sum()
        ),
        "marked_signal_rows": int(
            (np.asarray(signals["marked_signal"], dtype=np.float32) > 0.0).sum()
        ),
        "domain_or_marked_rows": int(
            (np.asarray(signals["domain_or_marked_signal"], dtype=np.float32) > 0.0).sum()
        ),
        "jmdict_domain_signal_rows": int(
            (np.asarray(signals["jmdict_domain_signal"], dtype=np.float32) > 0.0).sum()
        ),
        "jmdict_marked_signal_rows": int(
            (np.asarray(signals["jmdict_marked_signal"], dtype=np.float32) > 0.0).sum()
        ),
        "jmdict_domain_or_marked_rows": int(
            (np.asarray(signals["jmdict_domain_or_marked_signal"], dtype=np.float32) > 0.0).sum()
        ),
    }


def _acceptance_candidate_id(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload["inputs"]["candidate_id"])


def _baseline_candidate(candidate_id: str):
    candidate_families = (
        "base_family_rescue_refine",
        "same_surface_exact_protected_floor_refine",
    )
    for family in candidate_families:
        candidates = {
            candidate.candidate_id: candidate
            for candidate in generate_candidates(candidate_family=family)
        }
        if candidate_id in candidates:
            return candidates[candidate_id]
    raise KeyError(f"Acceptance candidate is not in known families: {candidate_id}")


def component_lookup(component: object) -> dict[tuple[str, str], int]:
    lookup: dict[tuple[str, str], int] = {}
    for index, (lemma, reading) in enumerate(
        zip(component["lemmas"], component["readings"], strict=False)
    ):
        lookup.setdefault((str(lemma), str(reading)), index)
        lookup.setdefault((str(lemma), ""), index)
    return lookup


def _best_baseline_by_lemma(
    lemmas: Sequence[str],
    baseline_scores: object,
) -> dict[str, float]:
    scores = np.asarray(baseline_scores, dtype=np.float32)
    best: dict[str, float] = {}
    for lemma, score in zip(lemmas, scores, strict=False):
        if not np.isfinite(score):
            continue
        previous = best.get(lemma)
        if previous is None or float(score) < previous:
            best[lemma] = float(score)
    return best


def _max_components(view: ComponentView, names: Sequence[str]) -> object:
    values = [view.value(name, fill=0.0) for name in names]
    return np.maximum.reduce([np.nan_to_num(value, nan=0.0) for value in values]).astype(np.float32)


def english_zipf(word: str) -> float | None:
    try:
        from wordfreq import zipf_frequency
    except Exception:
        return None
    try:
        value = float(zipf_frequency(word, "en"))
    except Exception:
        return None
    return value if math.isfinite(value) else None


def _ratio_gain(numerator: float | None, denominator: float | None) -> float:
    if numerator is None or denominator is None or denominator <= 0.0:
        return 0.0
    return float(max(0.0, numerator / denominator))


def _pmw_value(row: Mapping[str, object] | None) -> float | None:
    if not row:
        return None
    value = _optional_float(row.get("core_pmw"))
    if value is None or value <= 0.0:
        value = _optional_float(row.get("pmw"))
    return value


def _rank_value(row: Mapping[str, object] | None) -> float | None:
    if not row:
        return None
    value = _optional_float(row.get("core_rank"))
    if value is None or value <= 0.0:
        value = _optional_float(row.get("rank"))
    return value


def _sort_rank(row: Mapping[str, object]) -> tuple[float, float]:
    core = _optional_float(row.get("core_rank"))
    rank = _optional_float(row.get("rank"))
    return (
        core if core is not None and core > 0.0 else math.inf,
        rank if rank is not None and rank > 0.0 else math.inf,
    )


def _chunks(values: Sequence[str], *, size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _ramp_scalar(value: float, *, lower: float, upper: float) -> float:
    if upper <= lower:
        return 1.0 if value >= upper else 0.0
    return float(np.clip((float(value) - lower) / (upper - lower), 0.0, 1.0))


def _metric(result: Mapping[str, object], dataset: str, key: str) -> float:
    return float(_mapping(_mapping(result.get("metrics")).get(dataset)).get(key) or 0.0)


def _metric_deltas(
    metrics: Mapping[str, Mapping[str, object]],
    baseline_metrics: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for dataset, scores in metrics.items():
        baseline = baseline_metrics[dataset]
        out[dataset] = {}
        for key, value in scores.items():
            current = _optional_float(value)
            base = _optional_float(baseline.get(key))
            out[dataset][key] = (
                _rounded(current - base) if current is not None and base is not None else None
            )
    return out


def _score_delta(
    deltas: Mapping[str, object],
    dataset: str,
    key: str,
) -> float:
    return float(_mapping(_mapping(deltas).get(dataset)).get(key) or 0.0)


def _summary_row(result: Mapping[str, object]) -> dict[str, object]:
    return {
        "variant_id": result.get("variant_id"),
        "recommendation": result.get("recommendation"),
        "params": {
            "family_margin": result.get("family_margin"),
            "family_strength": result.get("family_strength"),
            "gairaigo_mode": result.get("gairaigo_mode"),
            "gairaigo_delta": result.get("gairaigo_delta"),
            "domain_mode": result.get("domain_mode"),
            "domain_cap": result.get("domain_cap"),
            "domain_strength": result.get("domain_strength"),
        },
        "metrics": result.get("metrics"),
        "metric_deltas": result.get("metric_deltas"),
        "changed_count": result.get("changed_count"),
        "changed_first60_count": result.get("changed_first60_count"),
        "max_abs_score_change": result.get("max_abs_score_change"),
        "diagnostic_counts": _mapping(
            _mapping(result.get("diagnostics")).get("signal_changed_counts")
        ),
    }


def _variant_id(
    *,
    family_margin: float | None,
    family_strength: float,
    gairaigo_mode: str,
    gairaigo_delta: float,
    domain_mode: str,
    domain_cap: float | None,
    domain_strength: float,
) -> str:
    parts = []
    if family_margin is not None and family_strength > 0.0:
        parts.append(f"fam_m{_compact_num(family_margin)}_s{_compact_num(family_strength)}")
    if gairaigo_delta > 0.0 and gairaigo_mode != "none":
        parts.append(f"gai_{gairaigo_mode}_d{_compact_num(gairaigo_delta)}")
    if domain_cap is not None and domain_strength > 0.0 and domain_mode != "none":
        parts.append(
            f"dom_{domain_mode}_c{_compact_num(domain_cap)}_s{_compact_num(domain_strength)}"
        )
    return "targeted_" + "__".join(parts)


def _compact_num(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def _fmt_metric(row: Mapping[str, object], dataset: str, key: str) -> str:
    return _fmt_float(_mapping(_mapping(row.get("metrics")).get(dataset)).get(key))


def _fmt_delta(row: Mapping[str, object], dataset: str, key: str) -> str:
    return _fmt_signed(_mapping(_mapping(row.get("metric_deltas")).get(dataset)).get(key))


def _fmt_float(value: object) -> str:
    parsed = _optional_float(value)
    return "" if parsed is None else f"{parsed:.6f}".rstrip("0").rstrip(".")


def _fmt_signed(value: object) -> str:
    parsed = _optional_float(value)
    return "" if parsed is None else f"{parsed:+.6f}".rstrip("0").rstrip(".")


def _mapping(value: object) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _rows(value: object) -> list:
    return list(value) if isinstance(value, list | tuple) else []


def _sequence_value(value: object, index: int) -> object:
    if value is None:
        return None
    try:
        return list(value)[index]
    except (IndexError, TypeError):
        return None


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path.expanduser().resolve()
    return (PROJECT_ROOT / path).expanduser().resolve()


if __name__ == "__main__":
    raise SystemExit(main())
