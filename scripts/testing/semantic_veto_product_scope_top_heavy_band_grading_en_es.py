#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float,
)
from semantic_veto_product_scope_band_grading_en_es import (
    BAND_IDS,
    CASE_TYPES,
    PRIMARY_TARGET_ID,
    _case_type,
    _formula_rows,
    _is_failure,
    _normalize_weights,
    _normalization_targets,
    _rate,
    _raw_grade,
    _target_grade,
    _target_metrics,
)
from semantic_veto_repaired_full_band_formula_sweep_core import _weighted_score
from semantic_veto_product_scope_top_heavy_support import (
    _accepted_candidate,
    _accepted_takeaway,
    _best_by_ranking_mode,
    _best_by_strategy,
    _combined_metrics,
    _matches_candidate,
    _public_top_heavy_rows,
    _ranking_mode_definitions,
    _mean_float,
    _round4,
    _sample_ranked_triggers,
    _top_heavy_sort_key,
    _utc_now,
    render_top_heavy_band_grading_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_FORMULA_SWEEP_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_formula_sweep_en_es_latest.json"
)
DEFAULT_SCORE_SURFACE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_selected_candidate_surface_en_es_latest.json"
)
DEFAULT_SRS_CASE_MIX_PRIOR_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_srs_case_mix_prior_en_es_latest.json"
)
DEFAULT_ACCEPTANCE_AUDIT_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_product_scope_band_grading_acceptance_audit_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_top_heavy_band_grading_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_top_heavy_band_grading_en_es_latest.md"
)

RANKING_MODE_IDS = (
    "algorithm_need",
    "source_exposure_product",
    "source_exposure_blend_25",
    "source_exposure_blend_50",
)


@dataclass(frozen=True)
class BandStrategy:
    strategy_id: str
    high_fraction: float
    middle_fraction: float
    description: str


BAND_STRATEGIES = (
    BandStrategy(
        "equal_tertiles_33_33_34",
        1 / 3,
        1 / 3,
        "Control: approximate equal thirds by predicted need.",
    ),
    BandStrategy(
        "top_05_next_15_rest",
        0.05,
        0.15,
        "Very concentrated product hypothesis: top 5%, next 15%, rest.",
    ),
    BandStrategy(
        "top_10_next_20_rest",
        0.10,
        0.20,
        "Concentrated product hypothesis: top 10%, next 20%, rest.",
    ),
    BandStrategy(
        "top_15_next_25_rest",
        0.15,
        0.25,
        "Moderately concentrated product hypothesis: top 15%, next 25%, rest.",
    ),
    BandStrategy(
        "top_20_next_30_rest",
        0.20,
        0.30,
        "Broad top-heavy product hypothesis: top 20%, next 30%, rest.",
    ),
    BandStrategy(
        "top_25_next_25_rest",
        0.25,
        0.25,
        "Wide high-priority hypothesis: top 25%, next 25%, rest.",
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare equal-tertile semantic-veto LLM allocation bands against top-heavy "
            "and source-exposure-weighted allocation views. Runtime policy remains unchanged."
        )
    )
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--score-surface-json", type=Path, default=DEFAULT_SCORE_SURFACE_JSON)
    parser.add_argument(
        "--srs-case-mix-prior-json", type=Path, default=DEFAULT_SRS_CASE_MIX_PRIOR_JSON
    )
    parser.add_argument("--acceptance-audit-json", type=Path, default=DEFAULT_ACCEPTANCE_AUDIT_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n-details", type=int, default=75)
    parser.add_argument(
        "--formula-scope-limit",
        type=int,
        default=2000,
        help=(
            "Evaluate the first N formula scopes from the existing formula sweep ordering, "
            "plus the accepted candidate. Use 0 for an exhaustive matrix."
        ),
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    acceptance_audit_payload = (
        _load_json(args.acceptance_audit_json) if args.acceptance_audit_json.exists() else {}
    )
    report = build_top_heavy_band_grading_report(
        formula_sweep_payload=_load_json(args.formula_sweep_json),
        score_surface_payload=_load_json(args.score_surface_json),
        srs_case_mix_prior_payload=_load_json(args.srs_case_mix_prior_json)
        if args.srs_case_mix_prior_json.exists()
        else {},
        acceptance_audit_payload=acceptance_audit_payload,
        formula_sweep_path=args.formula_sweep_json,
        score_surface_path=args.score_surface_json,
        srs_case_mix_prior_path=args.srs_case_mix_prior_json
        if args.srs_case_mix_prior_json.exists()
        else None,
        acceptance_audit_path=args.acceptance_audit_json
        if args.acceptance_audit_json.exists()
        else None,
        top_n_details=args.top_n_details,
        formula_scope_limit=args.formula_scope_limit,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_top_heavy_band_grading_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_top_heavy_band_grading_report(
    *,
    formula_sweep_payload: Mapping[str, object],
    score_surface_payload: Mapping[str, object],
    srs_case_mix_prior_payload: Mapping[str, object] | None = None,
    acceptance_audit_payload: Mapping[str, object] | None = None,
    formula_sweep_path: Path | None = None,
    score_surface_path: Path | None = None,
    srs_case_mix_prior_path: Path | None = None,
    acceptance_audit_path: Path | None = None,
    top_n_details: int = 75,
    formula_scope_limit: int = 2000,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    observations = _mapping_rows(formula_sweep_payload.get("observations"))
    all_formula_rows = _formula_rows(formula_sweep_payload)
    surface_rows = _mapping_rows(score_surface_payload.get("row_results"))
    targets = _normalization_targets(
        surface_rows=surface_rows,
        srs_case_mix_prior_payload=srs_case_mix_prior_payload or {},
    )
    family_case_metrics_by_key = _family_case_metrics_by_key(surface_rows)
    observation_by_key = {
        (str(row.get("scorer_id") or ""), str(row.get("family_id") or "")): row
        for row in observations
    }
    candidate = _accepted_candidate(acceptance_audit_payload or {})
    formula_rows = _limited_formula_rows(
        all_formula_rows,
        candidate=candidate,
        formula_scope_limit=formula_scope_limit,
    )
    grade_rows, detail_candidates = _grade_top_heavy_formulas(
        formula_rows=formula_rows,
        observations=observations,
        observation_by_key=observation_by_key,
        family_case_metrics_by_key=family_case_metrics_by_key,
        targets=targets,
    )
    grade_rows.sort(key=_top_heavy_sort_key)
    detail_ids = {str(row.get("scope_id") or "") for row in grade_rows[:top_n_details]}
    if candidate:
        detail_ids.update(
            str(row.get("scope_id") or "")
            for row in grade_rows
            if _matches_candidate(row, candidate)
        )
    detail_by_scope = {
        str(row.get("scope_id") or ""): row
        for row in detail_candidates
        if str(row.get("scope_id") or "") in detail_ids
    }
    detail_rows = [
        detail_by_scope[str(row.get("scope_id") or "")]
        for row in grade_rows
        if str(row.get("scope_id") or "") in detail_by_scope
    ]
    accepted_rows = [row for row in grade_rows if candidate and _matches_candidate(row, candidate)]
    accepted_takeaway = _accepted_takeaway(accepted_rows)
    issues = []
    if not observations:
        issues.append("formula_sweep_has_no_observations")
    if not formula_rows:
        issues.append("formula_sweep_has_no_formula_rows")
    if not surface_rows:
        issues.append("score_surface_has_no_row_results")
    if not targets:
        issues.append("normalization_targets_missing")
    if not any(str(target.get("target_id") or "") == PRIMARY_TARGET_ID for target in targets):
        issues.append("base_product_prior_missing")
    if not any(row.get("top_heavy_grade_score") is not None for row in grade_rows):
        issues.append("no_top_heavy_grade_available")
    if candidate and not accepted_rows:
        issues.append("accepted_candidate_not_found_in_top_heavy_rows")
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(
            formula_sweep_payload.get("pair") or score_surface_payload.get("pair") or "en-es"
        ),
        "status": status,
        "decision": (
            "product_scope_top_heavy_band_grading_established"
            if status == "ok"
            else "product_scope_top_heavy_band_grading_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "formula_sweep_path": _repo_path(formula_sweep_path),
            "formula_sweep_decision": str(formula_sweep_payload.get("decision") or ""),
            "score_surface_path": _repo_path(score_surface_path),
            "score_surface_decision": str(score_surface_payload.get("decision") or ""),
            "srs_case_mix_prior_path": _repo_path(srs_case_mix_prior_path),
            "srs_case_mix_prior_decision": str(
                (srs_case_mix_prior_payload or {}).get("decision") or ""
            ),
            "acceptance_audit_path": _repo_path(acceptance_audit_path),
            "acceptance_audit_decision": str(
                (acceptance_audit_payload or {}).get("decision") or ""
            ),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_spend": "none",
            "purpose": (
                "Check whether semantic-veto evidence need is better represented by a "
                "concentrated top slice than by equal thirds, and whether source-exposure "
                "weighting surfaces product-important daily-language families."
            ),
            "unit_of_analysis": "source_target_family",
            "candidate_pool_policy": (
                "Default run evaluates the strongest formula scopes from the existing "
                "formula sweep ordering plus the accepted candidate. Pass "
                "--formula-scope-limit 0 for an exhaustive formula matrix."
            ),
            "band_strategy": (
                "Sort families by ranking score, preserve ties, then apply explicit "
                "top-heavy cut fractions. Equal tertiles are kept as the control."
            ),
            "ranking_modes": _ranking_mode_definitions(),
            "primary_grade": (
                "Primary ordering uses base_product_prior measured-only failure. "
                "The top-heavy grade emphasizes high_need minus rest failure rate, "
                "then multiplies by monotonic high>=middle>=low order and measured "
                "target coverage."
            ),
            "normalization_boundary": (
                "This still uses the repaired product-scope case surface, so missing "
                "case-type mass is reported and not silently imputed."
            ),
        },
        "summary": {
            "issues": issues,
            "observation_count": len(observations),
            "source_formula_scope_count": len(all_formula_rows),
            "evaluated_formula_scope_count": len(formula_rows),
            "strategy_scope_count": len(grade_rows),
            "score_surface_row_count": len(surface_rows),
            "normalization_target_count": len(targets),
            "band_strategy_count": len(BAND_STRATEGIES),
            "ranking_mode_count": len(RANKING_MODE_IDS),
            "formula_scope_limit": int(formula_scope_limit),
            "accepted_candidate": candidate,
            "accepted_candidate_takeaway": accepted_takeaway,
            "best_by_top_heavy_grade": _public_top_heavy_rows(grade_rows[:20]),
            "best_by_strategy": _best_by_strategy(grade_rows),
            "best_by_ranking_mode": _best_by_ranking_mode(grade_rows),
            "accepted_candidate_strategy_rows": _public_top_heavy_rows(accepted_rows),
        },
        "e2e_checks": {
            "formula_sweep_observations_available": bool(observations),
            "score_surface_row_results_available": bool(surface_rows),
            "base_product_prior_available": any(
                str(target.get("target_id") or "") == PRIMARY_TARGET_ID for target in targets
            ),
            "equal_tertile_control_included": any(
                strategy.strategy_id == "equal_tertiles_33_33_34" for strategy in BAND_STRATEGIES
            ),
            "top_heavy_strategies_included": any(
                strategy.strategy_id != "equal_tertiles_33_33_34" for strategy in BAND_STRATEGIES
            ),
            "source_exposure_ranking_modes_included": any(
                mode != "algorithm_need" for mode in RANKING_MODE_IDS
            ),
            "accepted_candidate_available": bool(candidate),
            "accepted_candidate_rows_available": bool(accepted_rows),
        },
        "normalization_targets": targets,
        "band_strategies": [
            {
                "strategy_id": strategy.strategy_id,
                "high_fraction": strategy.high_fraction,
                "middle_fraction": strategy.middle_fraction,
                "low_fraction": max(0.0, 1.0 - strategy.high_fraction - strategy.middle_fraction),
                "description": strategy.description,
            }
            for strategy in BAND_STRATEGIES
        ],
        "ranking_modes": _ranking_mode_definitions(),
        "top_strategy_grade_details": detail_rows,
        "limitations": [
            "top_heavy_report_reuses_49_repaired_families_so_small_slice_results_are_fragile",
            "source_exposure_is_a_zipf_band_proxy_not_observed_browser_impression_frequency",
            "scores_are_allocation_rankings_not_calibrated_failure_probabilities",
            "product_scope_surface_currently_has_no_phrase_no_winner_rows",
            "this report can guide the next LLM allocation hypothesis but cannot promote runtime policy",
        ],
        "next_steps": [
            "Compare accepted-candidate equal-tertile rows against top-heavy source-exposure rows.",
            "If top-heavy rows concentrate failure and generated-evidence lift, use top-N budget curves for allocation instead of thirds.",
            "Keep low and middle controls in the next generation batch so the concentrated-ranking hypothesis remains falsifiable.",
        ],
    }


def _grade_top_heavy_formulas(
    *,
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    observation_by_key: Mapping[tuple[str, str], Mapping[str, object]],
    family_case_metrics_by_key: Mapping[tuple[str, str], Mapping[str, Mapping[str, object]]],
    targets: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    observations_by_scorer: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for observation in observations:
        observations_by_scorer[str(observation.get("scorer_id") or "")].append(observation)
    grade_rows: list[dict[str, object]] = []
    detail_rows: list[dict[str, object]] = []
    for formula in formula_rows:
        scorer_id = str(formula.get("scorer_id") or "")
        weights = _as_mapping(formula.get("weights"))
        base_scored = []
        for observation in observations_by_scorer.get(scorer_id, []):
            features = _as_mapping(observation.get("features"))
            base_scored.append(
                {
                    "family_id": str(observation.get("family_id") or ""),
                    "trigger": str(observation.get("trigger") or ""),
                    "target_lemma": str(observation.get("target_lemma") or ""),
                    "algorithm_need": _weighted_score(features, weights),
                    "source_exposure": _safe_float(features.get("source_zipf_risk")),
                }
            )
        for ranking_mode_id in RANKING_MODE_IDS:
            ranked = [
                {
                    **row,
                    "ranking_score": _ranking_score(row, ranking_mode_id),
                }
                for row in base_scored
            ]
            for strategy in BAND_STRATEGIES:
                bands = _assign_fraction_bands(ranked, strategy=strategy)
                band_metrics = []
                for band_id in BAND_IDS:
                    family_ids = bands.get(band_id, [])
                    band_metrics.append(
                        _band_metrics_fast(
                            band_id=band_id,
                            scorer_id=scorer_id,
                            family_ids=family_ids,
                            observations=observation_by_key,
                            family_case_metrics=family_case_metrics_by_key,
                            targets=targets,
                        )
                    )
                rest_metrics = _merge_band_metrics(
                    "rest_need",
                    [
                        metric
                        for metric in band_metrics
                        if str(metric.get("band_id") or "") in {"middle_need", "low_need"}
                    ],
                    targets,
                )
                primary = _target_grade(band_metrics, PRIMARY_TARGET_ID)
                raw = _raw_grade(band_metrics)
                top_heavy = _top_heavy_grade(band_metrics, rest_metrics, PRIMARY_TARGET_ID)
                row = {
                    "scope_id": "::".join(
                        [
                            scorer_id,
                            str(formula.get("formula_id") or ""),
                            ranking_mode_id,
                            strategy.strategy_id,
                        ]
                    ),
                    "formula_id": str(formula.get("formula_id") or ""),
                    "formula_family": str(formula.get("formula_family") or ""),
                    "scorer_id": scorer_id,
                    "ranking_mode_id": ranking_mode_id,
                    "band_strategy_id": strategy.strategy_id,
                    "weights": dict(weights),
                    "rank_metrics": dict(_as_mapping(formula.get("rank_metrics"))),
                    "band_family_counts": {
                        metric["band_id"]: metric.get("family_count") for metric in band_metrics
                    },
                    "high_family_share": _round4(
                        _safe_float(_as_mapping(band_metrics[0]).get("family_count"))
                        / max(1, len(base_scored))
                    ),
                    "raw_high_low_failure_delta": raw.get("high_low_failure_delta"),
                    "raw_order_score": raw.get("order_score"),
                    "primary_target_id": PRIMARY_TARGET_ID,
                    "primary_normalized_high_low_failure_delta": primary.get(
                        "high_low_failure_delta"
                    ),
                    "primary_normalized_order_score": primary.get("order_score"),
                    "primary_min_measured_target_weight": primary.get("min_measured_target_weight"),
                    "primary_max_unmeasured_target_weight": primary.get(
                        "max_unmeasured_target_weight"
                    ),
                    "primary_high_failure_rate": top_heavy.get("high_failure_rate"),
                    "primary_rest_failure_rate": top_heavy.get("rest_failure_rate"),
                    "primary_all_failure_rate": top_heavy.get("all_failure_rate"),
                    "primary_high_rest_failure_delta": top_heavy.get("high_rest_delta"),
                    "primary_high_failure_lift": top_heavy.get("high_failure_lift"),
                    "top_heavy_grade_score": top_heavy.get("grade_score"),
                    "high_sample_triggers": _sample_ranked_triggers(
                        ranked, bands.get("high_need", [])
                    ),
                    "low_sample_triggers": _sample_ranked_triggers(
                        ranked, bands.get("low_need", [])
                    ),
                }
                grade_rows.append(row)
                detail_rows.append(row)
    return grade_rows, detail_rows


def _limited_formula_rows(
    formula_rows: Sequence[Mapping[str, object]],
    *,
    candidate: Mapping[str, object],
    formula_scope_limit: int,
) -> list[Mapping[str, object]]:
    if formula_scope_limit <= 0:
        return list(formula_rows)
    selected = list(formula_rows[:formula_scope_limit])
    seen = {(str(row.get("scorer_id") or ""), str(row.get("formula_id") or "")) for row in selected}
    candidate_key = (
        str(candidate.get("scorer_id") or ""),
        str(candidate.get("formula_id") or ""),
    )
    if candidate_key != ("", "") and candidate_key not in seen:
        for row in formula_rows:
            row_key = (str(row.get("scorer_id") or ""), str(row.get("formula_id") or ""))
            if row_key == candidate_key:
                selected.append(row)
                break
    return selected


def _assign_fraction_bands(
    rows: Sequence[Mapping[str, object]], *, strategy: BandStrategy
) -> dict[str, list[str]]:
    grouped: dict[float, list[str]] = defaultdict(list)
    for row in rows:
        grouped[round(_safe_float(row.get("ranking_score")), 6)].append(
            str(row.get("family_id") or "")
        )
    scores = sorted(grouped, reverse=True)
    output = {band_id: [] for band_id in BAND_IDS}
    if not scores:
        return output
    total = sum(len(grouped[score]) for score in scores)
    cursor = 0
    middle_cut = min(1.0, strategy.high_fraction + strategy.middle_fraction)
    for score in scores:
        family_ids = sorted(grouped[score])
        midpoint = (cursor + cursor + len(family_ids) - 1) / 2 / max(total, 1)
        if midpoint < strategy.high_fraction:
            band_id = "high_need"
        elif midpoint < middle_cut:
            band_id = "middle_need"
        else:
            band_id = "low_need"
        output[band_id].extend(family_ids)
        cursor += len(family_ids)
    return output


def _family_case_metrics_by_key(
    surface_rows: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], dict[str, dict[str, object]]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in surface_rows:
        key = (str(row.get("scorer_id") or ""), str(row.get("family_id") or ""))
        case_type = _case_type(row)
        metrics = grouped[key].setdefault(
            case_type,
            {"case_count": 0, "failure_count": 0, "success_count": 0},
        )
        metrics["case_count"] = int(metrics.get("case_count") or 0) + 1
        if _is_failure(row):
            metrics["failure_count"] = int(metrics.get("failure_count") or 0) + 1
        else:
            metrics["success_count"] = int(metrics.get("success_count") or 0) + 1
    for case_metrics in grouped.values():
        for case_type in CASE_TYPES:
            case_metrics.setdefault(
                case_type,
                {"case_count": 0, "failure_count": 0, "success_count": 0},
            )
        for metrics in case_metrics.values():
            case_count = int(metrics.get("case_count") or 0)
            failure_count = int(metrics.get("failure_count") or 0)
            metrics["failure_rate"] = _round4(_rate(failure_count, case_count))
            metrics["success_rate"] = (
                _round4(1 - _rate(failure_count, case_count)) if case_count else None
            )
    return grouped


def _band_metrics_fast(
    *,
    band_id: str,
    scorer_id: str,
    family_ids: Sequence[str],
    observations: Mapping[tuple[str, str], Mapping[str, object]],
    family_case_metrics: Mapping[tuple[str, str], Mapping[str, Mapping[str, object]]],
    targets: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    case_type_metrics = {
        case_type: {"case_count": 0, "failure_count": 0, "success_count": 0}
        for case_type in CASE_TYPES
    }
    family_failure_rates = []
    for family_id in family_ids:
        observation = observations.get((scorer_id, family_id))
        if observation:
            family_failure_rates.append(_safe_float(observation.get("observed_failure_rate")))
        for case_type, metrics in _as_mapping(
            family_case_metrics.get((scorer_id, family_id))
        ).items():
            if case_type not in case_type_metrics:
                case_type_metrics[str(case_type)] = {
                    "case_count": 0,
                    "failure_count": 0,
                    "success_count": 0,
                }
            target = case_type_metrics[str(case_type)]
            target["case_count"] = int(target.get("case_count") or 0) + int(
                _as_mapping(metrics).get("case_count") or 0
            )
            target["failure_count"] = int(target.get("failure_count") or 0) + int(
                _as_mapping(metrics).get("failure_count") or 0
            )
            target["success_count"] = int(target.get("success_count") or 0) + int(
                _as_mapping(metrics).get("success_count") or 0
            )
    for metrics in case_type_metrics.values():
        case_count = int(metrics.get("case_count") or 0)
        failure_count = int(metrics.get("failure_count") or 0)
        metrics["failure_rate"] = _round4(_rate(failure_count, case_count))
        metrics["success_rate"] = (
            _round4(1 - _rate(failure_count, case_count)) if case_count else None
        )
    total_count = sum(int(metric.get("case_count") or 0) for metric in case_type_metrics.values())
    failure_count = sum(
        int(metric.get("failure_count") or 0) for metric in case_type_metrics.values()
    )
    return {
        "band_id": band_id,
        "family_count": len(family_ids),
        "case_count": total_count,
        "failure_count": failure_count,
        "raw_failure_rate": _round4(_rate(failure_count, total_count)),
        "raw_success_rate": _round4(1 - _rate(failure_count, total_count)) if total_count else None,
        "mean_family_observed_failure_rate": _round4(_mean_float(family_failure_rates)),
        "case_type_metrics": case_type_metrics,
        "target_normalized_metrics": [
            _target_normalized_metrics_fast(
                target=target,
                case_type_metrics=case_type_metrics,
            )
            for target in targets
        ],
        "sample_triggers": [],
    }


def _merge_band_metrics(
    band_id: str,
    band_metrics: Sequence[Mapping[str, object]],
    targets: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    case_type_metrics = {
        case_type: {"case_count": 0, "failure_count": 0, "success_count": 0}
        for case_type in CASE_TYPES
    }
    family_count = 0
    for band in band_metrics:
        family_count += int(band.get("family_count") or 0)
        for case_type, metrics in _as_mapping(band.get("case_type_metrics")).items():
            if case_type not in case_type_metrics:
                case_type_metrics[str(case_type)] = {
                    "case_count": 0,
                    "failure_count": 0,
                    "success_count": 0,
                }
            target = case_type_metrics[str(case_type)]
            target["case_count"] = int(target.get("case_count") or 0) + int(
                _as_mapping(metrics).get("case_count") or 0
            )
            target["failure_count"] = int(target.get("failure_count") or 0) + int(
                _as_mapping(metrics).get("failure_count") or 0
            )
            target["success_count"] = int(target.get("success_count") or 0) + int(
                _as_mapping(metrics).get("success_count") or 0
            )
    for metrics in case_type_metrics.values():
        case_count = int(metrics.get("case_count") or 0)
        failure_count = int(metrics.get("failure_count") or 0)
        metrics["failure_rate"] = _round4(_rate(failure_count, case_count))
        metrics["success_rate"] = (
            _round4(1 - _rate(failure_count, case_count)) if case_count else None
        )
    total_count = sum(int(metric.get("case_count") or 0) for metric in case_type_metrics.values())
    failure_count = sum(
        int(metric.get("failure_count") or 0) for metric in case_type_metrics.values()
    )
    return {
        "band_id": band_id,
        "family_count": family_count,
        "case_count": total_count,
        "failure_count": failure_count,
        "raw_failure_rate": _round4(_rate(failure_count, total_count)),
        "raw_success_rate": _round4(1 - _rate(failure_count, total_count)) if total_count else None,
        "mean_family_observed_failure_rate": None,
        "case_type_metrics": case_type_metrics,
        "target_normalized_metrics": [
            _target_normalized_metrics_fast(
                target=target,
                case_type_metrics=case_type_metrics,
            )
            for target in targets
        ],
        "sample_triggers": [],
    }


def _target_normalized_metrics_fast(
    *,
    target: Mapping[str, object],
    case_type_metrics: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    weights = _normalize_weights(_as_mapping(target.get("case_type_weights")))
    measured_weight = 0.0
    unmeasured_weight = 0.0
    measured_failure = 0.0
    missing_case_types = []
    for case_type, weight in weights.items():
        metrics = _as_mapping(case_type_metrics.get(case_type))
        case_count = int(metrics.get("case_count") or 0)
        rate = metrics.get("failure_rate")
        if case_count > 0 and rate is not None:
            measured_weight += weight
            measured_failure += weight * _safe_float(rate)
        else:
            unmeasured_weight += weight
            missing_case_types.append(case_type)
    measured_only = measured_failure / measured_weight if measured_weight else None
    strict = measured_failure if unmeasured_weight <= 0.00001 else None
    return {
        "target_id": str(target.get("target_id") or ""),
        "measured_target_weight": _round4(measured_weight),
        "unmeasured_target_weight": _round4(unmeasured_weight),
        "missing_case_types": missing_case_types,
        "measured_only_failure_rate": _round4(measured_only),
        "measured_only_success_rate": _round4(1 - measured_only)
        if measured_only is not None
        else None,
        "strict_failure_rate": _round4(strict),
        "strict_success_rate": _round4(1 - strict) if strict is not None else None,
    }


def _ranking_score(row: Mapping[str, object], ranking_mode_id: str) -> float:
    need = _safe_float(row.get("algorithm_need"))
    exposure = _safe_float(row.get("source_exposure"))
    if ranking_mode_id == "algorithm_need":
        return need
    if ranking_mode_id == "source_exposure_product":
        return need * exposure
    if ranking_mode_id == "source_exposure_blend_25":
        return 0.75 * need + 0.25 * exposure
    if ranking_mode_id == "source_exposure_blend_50":
        return 0.50 * need + 0.50 * exposure
    return need


def _top_heavy_grade(
    band_metrics: Sequence[Mapping[str, object]],
    rest_metrics: Mapping[str, object],
    target_id: str,
) -> dict[str, object]:
    by_band = {str(row.get("band_id") or ""): row for row in band_metrics}
    high = _safe_float(
        _target_metrics(by_band.get("high_need", {}), target_id).get("measured_only_failure_rate")
    )
    rest = _safe_float(_target_metrics(rest_metrics, target_id).get("measured_only_failure_rate"))
    all_metrics = _combined_metrics([*band_metrics], target_id)
    all_rate = _safe_float(all_metrics.get("measured_only_failure_rate"))
    primary = _target_grade(band_metrics, target_id)
    high_rest_delta = _round4(high - rest) if high is not None and rest is not None else None
    lift = _round4(high / all_rate) if all_rate and high is not None else None
    grade = (
        _round4(
            max(0.0, _safe_float(high_rest_delta))
            * _safe_float(primary.get("order_score"))
            * _safe_float(primary.get("min_measured_target_weight"))
        )
        if high_rest_delta is not None
        else None
    )
    return {
        "high_failure_rate": _round4(high),
        "rest_failure_rate": _round4(rest),
        "all_failure_rate": _round4(all_rate),
        "high_rest_delta": high_rest_delta,
        "high_failure_lift": lift,
        "grade_score": grade,
    }


if __name__ == "__main__":
    raise SystemExit(main())
