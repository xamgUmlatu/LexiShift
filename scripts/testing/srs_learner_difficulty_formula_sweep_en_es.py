#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
    build_report as build_formula_probe_report,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"
)
DEFAULT_MANUAL_CORRECTIONS_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_manual_corrections_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_formula_sweep_en_es_latest.md"
)
PRIMARY_STATE = "normal_vocab"
BASELINE_VARIANTS = (
    "zipf_frequency_only",
    "learner_source_zipf_medium",
)


@dataclass(frozen=True)
class FormulaCandidate:
    candidate_id: str
    description: str
    base_component: str
    up_weights: Mapping[str, float]
    down_weights: Mapping[str, float]
    up_cap: float | None
    down_cap: float | None
    profile: Mapping[str, object]
    post_down_weights: Mapping[str, float] = field(default_factory=dict)
    post_down_cap: float | None = None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an en-es learner-difficulty formula sweep over existing probe "
            "components. This is a sidecar diagnostic; it does not change production "
            "ranking or runtime behavior."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument(
        "--manual-corrections-json", type=Path, default=DEFAULT_MANUAL_CORRECTIONS_JSON
    )
    parser.add_argument(
        "--apply-manual-corrections",
        action="store_true",
        help="Apply the sidecar manual correction layer before metric evaluation.",
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--force-rebuild-probe", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    formula_report = load_or_build_formula_report(
        formula_probe_json=Path(args.formula_probe_json).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_probe),
    )
    report = build_report(
        formula_report=formula_report,
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        corrections_payload=(
            _load_json(Path(args.manual_corrections_json).expanduser())
            if bool(args.apply_manual_corrections)
            else {}
        ),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
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


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = _load_json(formula_probe_json)
        if payload.get("rows"):
            return payload
    return build_formula_probe_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )


def build_report(
    *,
    formula_report: Mapping[str, object],
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    corrections_payload: Mapping[str, object] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    rows_by_lemma = {str(row.get("lemma") or "").lower(): row for row in formula_rows}
    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    corrections_by_lemma = _corrections_by_lemma(_as_mapping(corrections_payload))
    candidates = list(generate_candidates())

    baseline_records = [
        _existing_variant_record(
            variant_id=variant_id,
            rows_by_lemma=rows_by_lemma,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            corrections_by_lemma=corrections_by_lemma,
        )
        for variant_id in BASELINE_VARIANTS
        if any(variant_id in _as_mapping(row.get("variant_scores")) for row in formula_rows[:10])
    ]
    baseline_by_id = {str(record.get("candidate_id")): record for record in baseline_records}
    current_best = baseline_by_id.get("learner_source_zipf_medium") or baseline_records[0]

    records = [
        _candidate_record(
            candidate=candidate,
            rows_by_lemma=rows_by_lemma,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            baseline_record=current_best,
            corrections_by_lemma=corrections_by_lemma,
        )
        for candidate in candidates
    ]
    calibration_top = sorted(records, key=_calibration_sort_key, reverse=True)[:30]
    holdout_guarded_top = sorted(records, key=_holdout_guarded_sort_key, reverse=True)[:30]
    stable_top = sorted(records, key=_stable_sort_key, reverse=True)[:30]
    selected = _unique_records(
        calibration_top[:5] + holdout_guarded_top[:5] + stable_top[:5],
        key="candidate_id",
    )
    selected_details = [
        _with_change_samples(
            record,
            formula_rows=formula_rows,
            candidate=_candidate_by_id(candidates, str(record.get("candidate_id"))),
            baseline_variant_id="learner_source_zipf_medium",
            sample_limit=12,
        )
        for record in selected
    ]

    best_calibration = calibration_top[0] if calibration_top else {}
    best_guarded = holdout_guarded_top[0] if holdout_guarded_top else {}
    best_stable = stable_top[0] if stable_top else {}
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_formula_sweep_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "formula_source": "srs_learner_difficulty_formula_probe_en_es components",
            "candidate_count": len(candidates),
            "selection_warning": (
                "Calibration is the primary selection split. Holdout metrics are reported "
                "to detect overfitting; candidates should not be promoted solely because "
                "they lead on holdout."
            ),
            "base_components": sorted({candidate.base_component for candidate in candidates}),
            "baseline_variants": list(BASELINE_VARIANTS),
            "manual_corrections_applied": bool(corrections_by_lemma),
            "manual_correction_count": len(corrections_by_lemma),
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
            "manual_correction_status": _as_mapping(corrections_payload).get("status"),
        },
        "summary": {
            "current_best_baseline": _compact_record(current_best),
            "best_calibration_candidate": _compact_record(best_calibration),
            "best_holdout_guarded_candidate": _compact_record(best_guarded),
            "best_stable_candidate": _compact_record(best_stable),
        },
        "baseline_records": baseline_records,
        "leaderboards": {
            "calibration_top": calibration_top,
            "holdout_guarded_top": holdout_guarded_top,
            "stable_top": stable_top,
        },
        "selected_candidate_details": selected_details,
        "limitations": [
            "The calibration and holdout sets are still small; tiny metric deltas should be treated as directional evidence, not final proof.",
            "This sweep only recombines already-materialized components. Beyond optional wordfreq commonness, it does not ingest external regional, register, morphology, or learner-list evidence.",
            "The strongest remaining errors may need new signal families, not just scalar tuning.",
            "When manual corrections are enabled, candidate scores are corrected after formula scoring, matching the final-ranking correction layer.",
        ],
    }


def generate_candidates() -> tuple[FormulaCandidate, ...]:
    bases = ("zipf_base", "spalex_blend")
    learner_profiles: list[tuple[str, Mapping[str, float], float | None, str]] = [
        ("no_ls", {}, None, "no learner-source rescue"),
    ]
    learner_components = (
        ("learner_core_gap_zipf_confident", "lsz", "confidence-only Zipf learner gap"),
        ("learner_core_gap_blend_confident", "lsb", "confidence-only blend learner gap"),
        ("learner_core_gap_zipf_quality", "lszq", "quality-gated Zipf learner gap"),
        ("learner_core_gap_blend_quality", "lsbq", "quality-gated blend learner gap"),
        ("learner_core_gap_zipf_strict", "lszs", "strict Zipf learner gap"),
        ("learner_core_gap_blend_strict", "lsbs", "strict blend learner gap"),
    )
    for component, stem, label in learner_components:
        for weight in (0.45, 0.60, 0.75, 0.80, 0.90, 1.05):
            for cap in (0.08, 0.12, 0.16, 0.18, 0.22):
                learner_profiles.append(
                    (
                        f"{stem}_w{_slug(weight)}_c{_slug(cap)}",
                        {component: weight},
                        cap,
                        f"{label} weight {weight:.2f}, cap {cap:.2f}",
                    )
                )
    cognate_profiles = (
        ("no_cog", {}, None, "no cognate rescue"),
        ("cog_l", {"cognate_rescue": 0.06}, 0.04, "light cognate rescue"),
        ("cog_m", {"cognate_rescue": 0.10}, 0.06, "medium cognate rescue"),
        ("cog_tail", {"rare_cognate_tail_rescue": 0.10}, 0.06, "tail-gated cognate rescue"),
    )
    wordfreq_profiles = (
        ("no_wf", {}, None, "no optional wordfreq rescue"),
        (
            "wf_l",
            {"wordfreq_source_rescue": 0.10},
            0.040,
            "light multi-source wordfreq rescue",
        ),
        (
            "wf_m",
            {"wordfreq_source_rescue": 0.18},
            0.070,
            "medium multi-source wordfreq rescue",
        ),
        (
            "wf_tail_l",
            {"wordfreq_tail_rescue": 0.28},
            0.080,
            "light tail-gated wordfreq rescue",
        ),
        (
            "wf_tail_m",
            {"wordfreq_tail_rescue": 0.42},
            0.120,
            "medium tail-gated wordfreq rescue",
        ),
        (
            "wf_reg_l",
            {"wordfreq_regional_rescue": 0.45},
            0.110,
            "regional/colloquial wordfreq rescue",
        ),
        (
            "lex_micro",
            {"lexcom_learner_rescue": 0.10},
            0.025,
            "micro LexComSpaL2 learner-complexity rescue",
        ),
        (
            "lex_mid_l",
            {"lexcom_rescue_after030": 0.45},
            0.060,
            "light LexComSpaL2 rescue after the early-core range",
        ),
        (
            "lex_mid_m",
            {"lexcom_rescue_after040": 0.65},
            0.080,
            "medium LexComSpaL2 rescue after the core range",
        ),
        (
            "lex_tail_l",
            {"lexcom_tail_rescue": 0.85},
            0.100,
            "tail-gated LexComSpaL2 learner-complexity rescue",
        ),
    )
    guard_profiles = (
        ("no_guard", {}, None, "no upward guard"),
        (
            "pos_l",
            {
                "pos_function_risk": 0.035,
                "pos_other_risk": 0.030,
                "admission_suitability_risk": 0.040,
            },
            0.055,
            "light POS/admission guard",
        ),
        (
            "dict_l",
            {
                "gated_dict_marked_usage_risk": 0.070,
                "dict_variant_risk": 0.060,
                "tail_dict_ambiguity": 0.035,
                "weak_form_risk": 0.020,
            },
            0.085,
            "light dictionary/register guard",
        ),
        (
            "tail_l",
            {
                "gated_dict_marked_usage_risk": 0.095,
                "tail_variant_risk": 0.090,
                "tail_dict_ambiguity": 0.060,
                "weak_form_risk": 0.025,
            },
            0.105,
            "tail-sensitive dictionary guard",
        ),
        (
            "broad_abs_l",
            {
                "learner_broad_absence_tail65": 0.060,
            },
            0.050,
            "light tail-only guard for absence from broad learner dictionary",
        ),
        (
            "broad_abs_t50",
            {
                "learner_broad_absence_tail50": 0.045,
            },
            0.045,
            "light lower-threshold guard for absence from broad learner dictionary",
        ),
        (
            "broad_abs_t80",
            {
                "learner_broad_absence_tail80": 0.090,
            },
            0.050,
            "narrow upper-tail guard for absence from broad learner dictionary",
        ),
        (
            "ue_floor_l",
            {
                "unsupported_ease_floor050": 1.000,
            },
            0.050,
            "light unsupported-ease floor for easy rows lacking broad learner support",
        ),
        (
            "ue_content_m",
            {
                "unsupported_ease_floor050": 0.800,
                "unsupported_ease_content_floor050": 1.000,
            },
            0.090,
            "medium unsupported-ease floor biased toward normal content words",
        ),
        (
            "ue_struct_l",
            {
                "unsupported_ease_structural_floor060": 1.100,
            },
            0.080,
            "light unsupported-ease floor requiring independent structural suspicion",
        ),
        (
            "ue_marked_l",
            {
                "unsupported_ease_marked_floor060": 1.250,
            },
            0.080,
            "light unsupported-ease floor requiring dictionary/register/form suspicion",
        ),
        (
            "ue_marked_m",
            {
                "unsupported_ease_marked_floor060": 1.650,
            },
            0.120,
            "medium unsupported-ease floor requiring dictionary/register/form suspicion",
        ),
        (
            "ue_usage_l",
            {
                "unsupported_ease_usage_floor060": 1.250,
            },
            0.080,
            "light unsupported-ease floor requiring usage/register/form suspicion without domain-topic evidence",
        ),
        (
            "ue_usage_m",
            {
                "unsupported_ease_usage_floor060": 1.650,
            },
            0.120,
            "medium unsupported-ease floor requiring usage/register/form suspicion without domain-topic evidence",
        ),
        (
            "ue_struct_m",
            {
                "unsupported_ease_floor040": 0.800,
                "unsupported_ease_structural_floor060": 1.450,
            },
            0.120,
            "medium unsupported-ease floor with structural suspicion and conservative base floor",
        ),
        (
            "ue_combo_m",
            {
                "unsupported_ease_floor050": 0.650,
                "unsupported_ease_content_floor050": 0.700,
                "unsupported_ease_structural_floor060": 1.200,
            },
            0.120,
            "combined unsupported-ease floor over plain, content, and structural gates",
        ),
        (
            "dict_detail_l",
            {
                "tail_rare_dated_register": 0.065,
                "tail_domain_specificity": 0.035,
                "dict_register_sensitive_score": 0.020,
            },
            0.075,
            "light structured Kaikki register/domain guard",
        ),
        (
            "lex_caution_l",
            {
                "lexcom_learner_caution": 0.120,
            },
            0.060,
            "light LexComSpaL2 learner-complexity caution",
        ),
        (
            "combo_l",
            {
                "pos_function_risk": 0.025,
                "pos_other_risk": 0.025,
                "admission_suitability_risk": 0.030,
                "gated_dict_marked_usage_risk": 0.060,
                "dict_variant_risk": 0.055,
                "tail_dict_ambiguity": 0.035,
                "tail_rare_dated_register": 0.030,
                "tail_domain_specificity": 0.020,
                "weak_form_risk": 0.020,
                "learner_broad_absence_tail65": 0.035,
                "unsupported_ease_usage_floor060": 1.000,
            },
            0.100,
            "combined light POS, dictionary, broad-absence, and usage-only unsupported-ease guard",
        ),
        (
            "combo_m",
            {
                "pos_function_risk": 0.040,
                "pos_other_risk": 0.035,
                "admission_suitability_risk": 0.045,
                "gated_dict_marked_usage_risk": 0.090,
                "dict_variant_risk": 0.080,
                "tail_dict_ambiguity": 0.055,
                "tail_rare_dated_register": 0.045,
                "tail_domain_specificity": 0.030,
                "weak_form_risk": 0.030,
                "learner_broad_absence_tail65": 0.050,
                "unsupported_ease_usage_floor060": 1.250,
            },
            0.130,
            "combined medium POS, dictionary, broad-absence, and usage-only unsupported-ease guard",
        ),
    )
    result: list[FormulaCandidate] = []
    seen: set[str] = set()

    def add_candidate(
        *,
        base: str,
        learner: tuple[str, Mapping[str, float], float | None, str],
        cognate: tuple[str, Mapping[str, float], float | None, str],
        wordfreq: tuple[str, Mapping[str, float], float | None, str],
        guard: tuple[str, Mapping[str, float], float | None, str],
    ) -> None:
        learner_id, learner_down, learner_cap, learner_desc = learner
        cognate_id, cognate_down, cognate_cap, cognate_desc = cognate
        wordfreq_id, wordfreq_down, wordfreq_cap, wordfreq_desc = wordfreq
        guard_id, up_weights, up_cap, guard_desc = guard
        down_weights = dict(learner_down)
        down_weights.update(cognate_down)
        down_caps = [cap for cap in (learner_cap, cognate_cap) if cap is not None]
        down_cap = round(sum(down_caps), 6) if down_caps else None
        candidate_id = f"{base}__{learner_id}__{cognate_id}__{wordfreq_id}__{guard_id}"
        if candidate_id in seen:
            return
        seen.add(candidate_id)
        result.append(
            FormulaCandidate(
                candidate_id=candidate_id,
                description=(
                    f"{base}; {learner_desc}; {cognate_desc}; {wordfreq_desc}; {guard_desc}."
                ),
                base_component=base,
                up_weights=dict(up_weights),
                down_weights=down_weights,
                up_cap=up_cap,
                down_cap=down_cap,
                profile={
                    "base": base,
                    "learner": learner_id,
                    "cognate": cognate_id,
                    "side_source": wordfreq_id,
                    "guard": guard_id,
                },
                post_down_weights=dict(wordfreq_down),
                post_down_cap=wordfreq_cap,
            )
        )

    no_wordfreq_profile = wordfreq_profiles[0]
    for base in bases:
        for learner in learner_profiles:
            for cognate in cognate_profiles:
                for guard in guard_profiles:
                    add_candidate(
                        base=base,
                        learner=learner,
                        cognate=cognate,
                        wordfreq=no_wordfreq_profile,
                        guard=guard,
                    )

    targeted_learner_ids = {
        "no_ls",
        "lsz_w080_c018",
        "lsb_w075_c016",
        "lsb_w090_c022",
        "lsb_w105_c022",
        "lsbq_w075_c016",
        "lsbq_w090_c022",
        "lsbq_w105_c022",
        "lsbs_w090_c022",
    }
    targeted_cognate_ids = {"no_cog", "cog_l", "cog_m"}
    targeted_guard_ids = {
        "no_guard",
        "dict_l",
        "dict_detail_l",
        "lex_caution_l",
        "ue_usage_l",
        "combo_l",
        "combo_m",
    }
    targeted_learners = [
        profile for profile in learner_profiles if profile[0] in targeted_learner_ids
    ]
    targeted_cognates = [
        profile for profile in cognate_profiles if profile[0] in targeted_cognate_ids
    ]
    targeted_wordfreqs = wordfreq_profiles[1:]
    targeted_guards = [profile for profile in guard_profiles if profile[0] in targeted_guard_ids]
    for base in bases:
        for learner in targeted_learners:
            for cognate in targeted_cognates:
                for wordfreq in targeted_wordfreqs:
                    for guard in targeted_guards:
                        add_candidate(
                            base=base,
                            learner=learner,
                            cognate=cognate,
                            wordfreq=wordfreq,
                            guard=guard,
                        )
    return tuple(result)


def _candidate_record(
    *,
    candidate: FormulaCandidate,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    baseline_record: Mapping[str, object],
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    record = {
        "candidate_id": candidate.candidate_id,
        "description": candidate.description,
        "profile": dict(candidate.profile),
        "base_component": candidate.base_component,
        "up_weights": dict(candidate.up_weights),
        "down_weights": dict(candidate.down_weights),
        "post_down_weights": dict(candidate.post_down_weights),
        "up_cap": candidate.up_cap,
        "down_cap": candidate.down_cap,
        "post_down_cap": candidate.post_down_cap,
        "calibration_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=True,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "holdout_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=True,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "calibration_all_numeric": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "holdout_all_numeric": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
            corrections_by_lemma=corrections_by_lemma,
        ),
    }
    record["score_deltas_vs_current_best"] = _score_deltas(record, baseline_record)
    return record


def _existing_variant_record(
    *,
    variant_id: str,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    candidate = FormulaCandidate(
        candidate_id=variant_id,
        description=f"Existing fixed probe variant `{variant_id}`.",
        base_component="existing_variant_score",
        up_weights={},
        down_weights={},
        up_cap=None,
        down_cap=None,
        profile={"existing_variant": variant_id},
    )
    return {
        "candidate_id": variant_id,
        "description": candidate.description,
        "profile": dict(candidate.profile),
        "base_component": candidate.base_component,
        "up_weights": {},
        "down_weights": {},
        "post_down_weights": {},
        "up_cap": None,
        "down_cap": None,
        "post_down_cap": None,
        "calibration_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=True,
            existing_variant_id=variant_id,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "holdout_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=True,
            existing_variant_id=variant_id,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "calibration_all_numeric": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
            existing_variant_id=variant_id,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "holdout_all_numeric": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
            existing_variant_id=variant_id,
            corrections_by_lemma=corrections_by_lemma,
        ),
    }


def _evaluate_labels(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    candidate: FormulaCandidate,
    primary_only: bool,
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
    existing_variant_id: str | None = None,
) -> dict[str, object]:
    selected = [
        label
        for label in labels
        if _safe_float(label.get("expected_learner_difficulty")) is not None
        and (not primary_only or str(label.get("expected_candidate_state") or "") == PRIMARY_STATE)
    ]
    expected_values = []
    observed_values = []
    expected_bands = []
    label_names = []
    expected_states = []
    observed_states = []
    row_pairs = []
    missing = []
    for label in selected:
        lemma = str(label.get("lemma") or "")
        row = rows_by_lemma.get(lemma.lower())
        observed = None
        if row is not None:
            if existing_variant_id:
                observed = _safe_float(
                    _as_mapping(row.get("variant_scores")).get(existing_variant_id)
                )
            else:
                observed = _score_formula(candidate, row)
            if observed is not None:
                observed = _apply_correction(
                    observed,
                    corrections_by_lemma.get(lemma.lower(), {}),
                )
        if observed is None:
            missing.append(lemma)
            observed = float("nan")
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(observed)
        expected_bands.append(str(label.get("expected_difficulty_band") or ""))
        label_names.append(lemma)
        expected_states.append(str(label.get("expected_candidate_state") or ""))
        observed_states.append(str(_as_mapping(row).get("candidate_state") or ""))
        row_pairs.append((label, row, observed))
    metrics = _difficulty_metrics(
        expected_values=np.asarray(expected_values, dtype=np.float32),
        observed_values=np.asarray(observed_values, dtype=np.float32),
        expected_bands=expected_bands,
        labels=label_names,
        expected_candidate_states=np.asarray(expected_states, dtype="<U64"),
        observed_candidate_states=np.asarray(observed_states, dtype="<U64"),
    )
    return {
        "label_count": len(selected),
        "missing_count": len(missing),
        "missing": missing[:20],
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
        "largest_errors": _largest_errors(row_pairs, limit=20),
    }


def _score_formula(candidate: FormulaCandidate, row: Mapping[str, object]) -> float:
    components = _as_mapping(row.get("components"))
    base = _safe_float(components.get(candidate.base_component))
    if base is None:
        base = _safe_float(components.get("spalex_blend")) or 0.0
    up_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in candidate.up_weights.items()
    )
    down_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in candidate.down_weights.items()
    )
    post_down_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in candidate.post_down_weights.items()
    )
    up = min(up_raw, candidate.up_cap) if candidate.up_cap is not None else up_raw
    down = min(down_raw, candidate.down_cap) if candidate.down_cap is not None else down_raw
    post_down = (
        min(post_down_raw, candidate.post_down_cap)
        if candidate.post_down_cap is not None
        else post_down_raw
    )
    return _round_float(_clamp01(base + up - down - post_down))


def _apply_correction(score: float, correction: Mapping[str, object]) -> float:
    if not _is_active_correction(correction):
        return _clamp01(score)
    override = _safe_float(correction.get("score_override"))
    floor = _safe_float(correction.get("min_score"))
    if override is not None:
        return _clamp01(override)
    if floor is not None:
        return _clamp01(max(score, floor))
    return _clamp01(score)


def _corrections_by_lemma(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for raw in _as_sequence(payload.get("corrections")):
        row = _as_mapping(raw)
        lemma = str(row.get("lemma") or row.get("surface") or "").strip().lower()
        if lemma and _is_active_correction(row):
            result[lemma] = row
    return result


def _is_active_correction(correction: Mapping[str, object]) -> bool:
    status = str(correction.get("status") or "active").strip().lower()
    return bool(correction) and status in {"active", "accepted"}


def _score_deltas(
    record: Mapping[str, object],
    baseline_record: Mapping[str, object],
) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for split in (
        "calibration_primary",
        "holdout_primary",
        "calibration_all_numeric",
        "holdout_all_numeric",
    ):
        current = _score_at(record, split, "balanced_score")
        baseline = _score_at(baseline_record, split, "balanced_score")
        result[f"{split}_balanced"] = (
            _round_float(current - baseline)
            if current is not None and baseline is not None
            else None
        )
    return result


def _with_change_samples(
    record: Mapping[str, object],
    *,
    formula_rows: Sequence[Mapping[str, object]],
    candidate: FormulaCandidate | None,
    baseline_variant_id: str,
    sample_limit: int,
) -> dict[str, object]:
    if candidate is None:
        return dict(record)
    rows = []
    for row in formula_rows:
        scores = _as_mapping(row.get("variant_scores"))
        baseline = _safe_float(scores.get(baseline_variant_id))
        score = _score_formula(candidate, row)
        if baseline is None:
            continue
        rows.append(
            {
                "lemma": row.get("lemma"),
                "score": score,
                "baseline_score": _round_float(baseline),
                "delta": _round_float(score - baseline),
                "spalex_rank": row.get("spalex_rank"),
                "pos": row.get("pos"),
                "pos_bucket": row.get("pos_bucket"),
                "translations": row.get("translations"),
                "signals": _salient_signals(_as_mapping(row.get("components"))),
            }
        )
    largest_raises = sorted(
        rows, key=lambda row: _safe_float(row.get("delta")) or 0.0, reverse=True
    )[:sample_limit]
    largest_lowers = sorted(rows, key=lambda row: _safe_float(row.get("delta")) or 0.0)[
        :sample_limit
    ]
    detailed = dict(record)
    detailed["change_samples_vs_current_best"] = {
        "largest_raises": largest_raises,
        "largest_lowers": largest_lowers,
    }
    detailed["band_samples"] = _band_samples(rows, sample_limit=sample_limit)
    return detailed


def _largest_errors(
    row_pairs: Sequence[tuple[Mapping[str, object], Mapping[str, object] | None, float]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    errors = []
    for label, row, observed in row_pairs:
        expected = _safe_float(label.get("expected_learner_difficulty"))
        if expected is None or not np.isfinite(observed):
            continue
        errors.append(
            {
                "lemma": label.get("lemma"),
                "expected": _round_float(expected),
                "observed": _round_float(observed),
                "abs_error": _round_float(abs(observed - expected)),
                "expected_candidate_state": label.get("expected_candidate_state"),
                "source_spalex_rank": label.get("source_spalex_rank"),
                "pos": _as_mapping(row).get("pos") if row is not None else None,
            }
        )
    return sorted(errors, key=lambda item: _safe_float(item.get("abs_error")) or -1, reverse=True)[
        :limit
    ]


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _as_mapping(report.get("inputs"))
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Learner Difficulty Formula Sweep",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Inputs",
        "",
        f"- Formula probe: `{inputs.get('formula_probe_decision')}`",
        f"- Formula top N: `{inputs.get('formula_probe_top_n')}`",
        f"- Calibration labels: `{inputs.get('calibration_count')}`",
        f"- Holdout labels: `{inputs.get('holdout_count')}`",
        f"- Candidates swept: `{method.get('candidate_count')}`",
        f"- Manual corrections applied: `{method.get('manual_corrections_applied')}`",
        f"- Manual correction rows: `{method.get('manual_correction_count')}`",
        "",
        "## Summary",
        "",
        "| Selection | Candidate | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | Cal Pairwise | Holdout Pairwise |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (
        ("current_best_baseline", "current baseline"),
        ("best_calibration_candidate", "best calibration"),
        ("best_holdout_guarded_candidate", "best holdout-guarded"),
        ("best_stable_candidate", "best stable"),
    ):
        lines.append(_summary_row(label, _as_mapping(summary.get(key))))
    lines.extend(
        [
            "",
            "Selection note: calibration remains the selection split; holdout is reported as an overfitting check.",
            "",
        ]
    )
    leaderboards = _as_mapping(report.get("leaderboards"))
    for key, title in (
        ("calibration_top", "Calibration Top"),
        ("holdout_guarded_top", "Holdout-Guarded Top"),
        ("stable_top", "Stable Top"),
    ):
        lines.extend(
            [
                f"## {title}",
                "",
                "| Candidate | Cal Balanced | Holdout Balanced | Cal Δ | Holdout Δ | Cal MAE | Holdout MAE | Shape |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in _as_sequence(leaderboards.get(key))[:12]:
            lines.append(_leaderboard_row(_as_mapping(row)))
        lines.append("")

    for raw in _as_sequence(report.get("selected_candidate_details"))[:8]:
        row = _as_mapping(raw)
        lines.extend(_candidate_detail_lines(row))

    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.append("## Limitations")
        lines.append("")
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _candidate_detail_lines(row: Mapping[str, object]) -> list[str]:
    lines = [
        f"## `{row.get('candidate_id')}`",
        "",
        str(row.get("description") or ""),
        "",
        "| Split | Rows | Balanced | MAE | Bucket | Pairwise | High Tail |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (
        ("calibration_primary", "calibration primary"),
        ("holdout_primary", "holdout primary"),
        ("calibration_all_numeric", "calibration all numeric"),
        ("holdout_all_numeric", "holdout all numeric"),
    ):
        item = _as_mapping(row.get(key))
        compact = _compact_eval(item)
        lines.append(
            f"| {label} | {compact.get('count', '')} | {_fmt(compact.get('balanced_score'))} | "
            f"{_fmt(compact.get('mae'))} | {_fmt(compact.get('bucket_accuracy'))} | "
            f"{_fmt(compact.get('pairwise_accuracy'))} | {_fmt(compact.get('high_tail_score'))} |"
        )
    lines.append("")
    lines.extend(
        [
            "### Largest Primary Errors",
            "",
            "| Split | Lemma | Expected | Observed | Abs Error |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for split, label in (("calibration_primary", "cal"), ("holdout_primary", "holdout")):
        for error in _as_sequence(_as_mapping(row.get(split)).get("largest_errors"))[:8]:
            item = _as_mapping(error)
            lines.append(
                f"| {label} | `{_escape(item.get('lemma'))}` | {_fmt(item.get('expected'))} | "
                f"{_fmt(item.get('observed'))} | {_fmt(item.get('abs_error'))} |"
            )
    lines.append("")
    changes = _as_mapping(row.get("change_samples_vs_current_best"))
    for key, title in (
        ("largest_lowers", "Largest Lowers vs Current Best"),
        ("largest_raises", "Largest Raises vs Current Best"),
    ):
        rows = _as_sequence(changes.get(key))
        if not rows:
            continue
        lines.extend(
            [
                f"### {title}",
                "",
                "| Lemma | Score | Current Best | Delta | Rank | POS | Signals |",
                "| --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for item_raw in rows:
            item = _as_mapping(item_raw)
            lines.append(
                f"| `{_escape(item.get('lemma'))}` | {_fmt(item.get('score'))} | "
                f"{_fmt(item.get('baseline_score'))} | {_fmt_signed(item.get('delta'))} | "
                f"{_fmt_rank(item.get('spalex_rank'))} | `{_escape(item.get('pos'))}` | "
                f"{_signal_text(item)} |"
            )
        lines.append("")
    band_samples = _as_sequence(row.get("band_samples"))
    if band_samples:
        lines.extend(["### Band Samples", ""])
        for band_raw in band_samples:
            band = _as_mapping(band_raw)
            rows = _as_sequence(band.get("rows"))
            if not rows:
                continue
            lines.extend(
                [
                    f"Band `{band.get('band')}` (`{band.get('count')}` rows)",
                    "",
                    "| Lemma | Score | Current Best | Delta | Rank | POS | Translations |",
                    "| --- | ---: | ---: | ---: | ---: | --- | --- |",
                ]
            )
            for item_raw in rows:
                item = _as_mapping(item_raw)
                translations = ", ".join(str(t) for t in _as_sequence(item.get("translations"))[:3])
                lines.append(
                    f"| `{_escape(item.get('lemma'))}` | {_fmt(item.get('score'))} | "
                    f"{_fmt(item.get('baseline_score'))} | {_fmt_signed(item.get('delta'))} | "
                    f"{_fmt_rank(item.get('spalex_rank'))} | `{_escape(item.get('pos'))}` | "
                    f"{_escape(translations) or '-'} |"
                )
            lines.append("")
    return lines


def _summary_row(label: str, row: Mapping[str, object]) -> str:
    if not row:
        return f"| {label} | - |  |  |  |  |  |  |"
    return (
        f"| {label} | `{row.get('candidate_id')}` | {_fmt(row.get('calibration_balanced'))} | "
        f"{_fmt(row.get('holdout_balanced'))} | {_fmt(row.get('calibration_mae'))} | "
        f"{_fmt(row.get('holdout_mae'))} | {_fmt(row.get('calibration_pairwise'))} | "
        f"{_fmt(row.get('holdout_pairwise'))} |"
    )


def _leaderboard_row(row: Mapping[str, object]) -> str:
    deltas = _as_mapping(row.get("score_deltas_vs_current_best"))
    profile = _as_mapping(row.get("profile"))
    shape = "/".join(
        str(profile.get(key) or "")
        for key in ("base", "learner", "cognate", "side_source", "guard")
    )
    return (
        f"| `{row.get('candidate_id')}` | {_fmt(_score_at(row, 'calibration_primary', 'balanced_score'))} | "
        f"{_fmt(_score_at(row, 'holdout_primary', 'balanced_score'))} | "
        f"{_fmt_signed(deltas.get('calibration_primary_balanced'))} | "
        f"{_fmt_signed(deltas.get('holdout_primary_balanced'))} | "
        f"{_fmt(_metric_at(row, 'calibration_primary', 'mae'))} | "
        f"{_fmt(_metric_at(row, 'holdout_primary', 'mae'))} | {_escape(shape)} |"
    )


def _band_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_limit: int,
    band_width: float = 0.10,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index in range(int(round(1.0 / band_width))):
        low = round(index * band_width, 6)
        high = round((index + 1) * band_width, 6)
        center = (low + high) / 2.0
        band_rows = [
            row
            for row in rows
            if (_safe_float(row.get("score")) or 0.0) >= low
            and (
                (_safe_float(row.get("score")) or 0.0) < high
                or (
                    index == int(round(1.0 / band_width)) - 1
                    and (_safe_float(row.get("score")) or 0.0) <= 1.0
                )
            )
        ]
        selected = sorted(
            band_rows,
            key=lambda row: (
                abs((_safe_float(row.get("score")) or 0.0) - center),
                _safe_float(row.get("spalex_rank")) or 0.0,
            ),
        )[:sample_limit]
        result.append(
            {
                "band": f"{low:.2f}-{high:.2f}",
                "count": len(band_rows),
                "rows": selected,
            }
        )
    return result


def _compact_record(row: Mapping[str, object]) -> dict[str, object]:
    if not row:
        return {}
    return {
        "candidate_id": row.get("candidate_id"),
        "profile": row.get("profile"),
        "calibration_balanced": _score_at(row, "calibration_primary", "balanced_score"),
        "holdout_balanced": _score_at(row, "holdout_primary", "balanced_score"),
        "calibration_mae": _metric_at(row, "calibration_primary", "mae"),
        "holdout_mae": _metric_at(row, "holdout_primary", "mae"),
        "calibration_pairwise": _metric_at(row, "calibration_primary", "pairwise_accuracy"),
        "holdout_pairwise": _metric_at(row, "holdout_primary", "pairwise_accuracy"),
    }


def _compact_eval(value: object) -> dict[str, object]:
    item = _as_mapping(value)
    scores = _as_mapping(item.get("scores"))
    metrics = _as_mapping(item.get("metrics"))
    return {
        "count": item.get("label_count"),
        "balanced_score": scores.get("balanced_score"),
        "mae": metrics.get("mae"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "high_tail_score": scores.get("high_tail_score"),
        "missing_count": item.get("missing_count"),
    }


def _calibration_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _score_at(row, "holdout_primary", "balanced_score") or -1.0,
        _metric_at(row, "calibration_primary", "pairwise_accuracy") or -1.0,
        -(_metric_at(row, "calibration_primary", "mae") or 999.0),
    )


def _holdout_guarded_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        min(
            _score_at(row, "calibration_primary", "balanced_score") or -1.0,
            _score_at(row, "holdout_primary", "balanced_score") or -1.0,
        ),
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _metric_at(row, "holdout_primary", "pairwise_accuracy") or -1.0,
        -(_metric_at(row, "holdout_primary", "mae") or 999.0),
    )


def _stable_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _score_at(row, "calibration_primary", "balanced_score") or -1.0
    holdout = _score_at(row, "holdout_primary", "balanced_score") or -1.0
    gap = abs(cal - holdout)
    mean_score = (cal + holdout) / 2.0
    return (mean_score - gap * 0.35, min(cal, holdout), -gap)


def _candidate_by_id(
    candidates: Sequence[FormulaCandidate],
    candidate_id: str,
) -> FormulaCandidate | None:
    candidate_id = _candidate_id_alias(candidate_id)
    for candidate in candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    return None


def _candidate_id_alias(candidate_id: str) -> str:
    parts = candidate_id.split("__")
    if len(parts) == 4:
        base, learner, cognate, guard = parts
        return f"{base}__{learner}__{cognate}__no_wf__{guard}"
    return candidate_id


def _unique_records(
    records: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> list[Mapping[str, object]]:
    result = []
    seen = set()
    for record in records:
        value = str(record.get(key) or "")
        if value in seen:
            continue
        seen.add(value)
        result.append(record)
    return result


def _salient_signals(components: Mapping[str, object]) -> list[dict[str, object]]:
    keys = (
        "pos_function_risk",
        "pos_other_risk",
        "admission_suitability_risk",
        "gated_dict_marked_usage_risk",
        "dict_region_tag_count_score",
        "dict_domain_topic_count_score",
        "dict_register_colloquial_score",
        "dict_register_sensitive_score",
        "dict_register_rare_dated_score",
        "tail_domain_specificity",
        "tail_rare_dated_register",
        "dict_variant_risk",
        "tail_variant_risk",
        "tail_dict_ambiguity",
        "weak_form_risk",
        "cognate_rescue",
        "rare_cognate_tail_rescue",
        "wordfreq_commonness",
        "wordfreq_source_rescue",
        "wordfreq_tail_rescue",
        "wordfreq_regional_rescue",
        "wordfreq_source_caution",
        "wordfreq_tail_caution",
        "lexcom_complexity",
        "lexcom_learner_rescue",
        "lexcom_rescue_after020",
        "lexcom_rescue_after030",
        "lexcom_rescue_after040",
        "lexcom_tail_rescue",
        "lexcom_learner_caution",
        "lexcom_tail_caution",
        "learner_core_gap_zipf_confident",
        "learner_core_gap_blend_confident",
        "learner_core_confidence",
        "learner_broad_absence_tail50",
        "learner_broad_absence_tail65",
        "learner_broad_absence_tail80",
        "positive_ease_support",
        "unsupported_ease50",
        "unsupported_ease65",
        "unsupported_ease_content",
        "unsupported_ease_marked",
        "unsupported_ease_usage",
        "unsupported_ease_structural",
        "unsupported_ease_floor040",
        "unsupported_ease_floor050",
        "unsupported_ease_content_floor050",
        "unsupported_ease_marked_floor060",
        "unsupported_ease_usage_floor060",
        "unsupported_ease_structural_floor060",
    )
    rows = [
        {"component": key, "value": _round_float(components.get(key))}
        for key in keys
        if (_safe_float(components.get(key)) or 0.0) > 0.01
    ]
    return sorted(rows, key=lambda row: float(row["value"]), reverse=True)[:6]


def _signal_text(row: Mapping[str, object]) -> str:
    signals = []
    for raw in _as_sequence(row.get("signals")):
        item = _as_mapping(raw)
        signals.append(f"{item.get('component')}={_fmt(item.get('value'))}")
    return _escape(", ".join(signals) or "-")


def _score_at(row: Mapping[str, object], eval_key: str, score_key: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("scores")).get(score_key))


def _metric_at(row: Mapping[str, object], eval_key: str, metric_key: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("metrics")).get(metric_key))


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _fmt_signed(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:+.3f}"


def _fmt_rank(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.0f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _slug(value: float) -> str:
    return f"{value:.2f}".replace(".", "")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
