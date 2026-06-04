#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
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
from semantic_veto_repaired_full_band_formula_sweep_core import _weighted_score
from semantic_veto_product_scope_band_grading_rendering import (
    _sample_triggers,
    render_product_scope_band_grading_markdown,
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
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_grading_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_grading_en_es_latest.md"
)

BAND_IDS = ("high_need", "middle_need", "low_need")
CASE_TYPES = ("positive_active", "shadow_negative", "phrase_no_winner")
PRIMARY_TARGET_ID = "base_product_prior"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Grade semantic-veto family heuristics by the product-scope bands they form. "
            "Runtime policy remains unchanged."
        )
    )
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--score-surface-json", type=Path, default=DEFAULT_SCORE_SURFACE_JSON)
    parser.add_argument(
        "--srs-case-mix-prior-json", type=Path, default=DEFAULT_SRS_CASE_MIX_PRIOR_JSON
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n-details", type=int, default=30)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_product_scope_band_grading_report(
        formula_sweep_payload=_load_json(args.formula_sweep_json),
        score_surface_payload=_load_json(args.score_surface_json),
        srs_case_mix_prior_payload=_load_json(args.srs_case_mix_prior_json)
        if args.srs_case_mix_prior_json.exists()
        else {},
        formula_sweep_path=args.formula_sweep_json,
        score_surface_path=args.score_surface_json,
        srs_case_mix_prior_path=args.srs_case_mix_prior_json
        if args.srs_case_mix_prior_json.exists()
        else None,
        top_n_details=args.top_n_details,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_product_scope_band_grading_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_product_scope_band_grading_report(
    *,
    formula_sweep_payload: Mapping[str, object],
    score_surface_payload: Mapping[str, object],
    srs_case_mix_prior_payload: Mapping[str, object] | None = None,
    formula_sweep_path: Path | None = None,
    score_surface_path: Path | None = None,
    srs_case_mix_prior_path: Path | None = None,
    top_n_details: int = 30,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    observations = _mapping_rows(formula_sweep_payload.get("observations"))
    formula_rows = _formula_rows(formula_sweep_payload)
    surface_rows = _mapping_rows(score_surface_payload.get("row_results"))
    targets = _normalization_targets(
        surface_rows=surface_rows,
        srs_case_mix_prior_payload=srs_case_mix_prior_payload or {},
    )
    case_rows_by_key = _case_rows_by_key(surface_rows)
    observation_by_key = {
        (str(row.get("scorer_id") or ""), str(row.get("family_id") or "")): row
        for row in observations
    }
    grade_rows, detail_candidates = _grade_formulas(
        formula_rows=formula_rows,
        observations=observations,
        observation_by_key=observation_by_key,
        case_rows_by_key=case_rows_by_key,
        targets=targets,
    )
    grade_rows.sort(key=_grade_sort_key)
    detailed_scope_ids = {str(row.get("scope_id") or "") for row in grade_rows[:top_n_details]}
    detailed_scope_ids.update(_representative_scope_ids(formula_sweep_payload))
    detail_by_scope = {
        str(row.get("scope_id") or ""): row
        for row in detail_candidates
        if str(row.get("scope_id") or "") in detailed_scope_ids
    }
    detail_rows = [
        detail_by_scope[str(row.get("scope_id") or "")]
        for row in grade_rows
        if str(row.get("scope_id") or "") in detail_by_scope
    ]
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
    if not any(
        row.get("primary_normalized_high_low_failure_delta") is not None for row in grade_rows
    ):
        issues.append("no_primary_normalized_band_grade_available")
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(
            formula_sweep_payload.get("pair") or score_surface_payload.get("pair") or "en-es"
        ),
        "status": status,
        "decision": (
            "product_scope_band_grading_established"
            if status == "ok"
            else "product_scope_band_grading_needs_review"
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
        },
        "methodology": {
            "runtime_policy_change": "none",
            "purpose": (
                "Evaluate each family-level heuristic by the actual low/middle/high "
                "bands it creates, then compare raw band success to success normalized "
                "against explicit case-type target mixes."
            ),
            "band_strategy": (
                "Sort families by predicted need descending, preserve ties, and form "
                "three approximate need bands. One unique score becomes middle; two "
                "unique scores become high/low; three unique scores map directly to "
                "high/middle/low."
            ),
            "primary_grade": (
                "Primary ordering uses the base SRS product prior when available: "
                "high_need measured-only failure rate minus low_need measured-only "
                "failure rate, with ordering and measured-target coverage shown "
                "separately."
            ),
            "normalization_boundary": (
                "If a target case type has no cases in a band, the strict normalized "
                "score is null and the missing target weight is reported. The measured-only "
                "score renormalizes over observed target mass so we do not pretend to "
                "have no-winner evidence when the product-scope suite lacks it."
            ),
        },
        "summary": {
            "issues": issues,
            "observation_count": len(observations),
            "formula_scope_count": len(grade_rows),
            "score_surface_row_count": len(surface_rows),
            "normalization_target_count": len(targets),
            "best_by_primary_band_grade": _public_grade_rows(grade_rows[:15]),
            "representative_comparison": _representative_comparison(
                grade_rows, formula_sweep_payload
            ),
            "case_type_counts_by_scorer": _case_type_counts_by_scorer(surface_rows),
        },
        "e2e_checks": {
            "formula_sweep_observations_available": bool(observations),
            "score_surface_row_results_available": bool(surface_rows),
            "srs_case_mix_prior_loaded": bool(srs_case_mix_prior_payload),
            "base_product_prior_available": any(
                str(target.get("target_id") or "") == PRIMARY_TARGET_ID for target in targets
            ),
            "primary_grade_available": any(
                row.get("primary_normalized_high_low_failure_delta") is not None
                for row in grade_rows
            ),
            "unmeasured_case_mass_visible": any(
                _safe_float(row.get("primary_max_unmeasured_target_weight")) > 0
                for row in grade_rows
            ),
        },
        "normalization_targets": targets,
        "formula_grade_rows": grade_rows,
        "top_formula_band_details": detail_rows,
        "limitations": [
            "product_scope_surface_currently_has_no_phrase_no_winner_rows_so_srs_prior_normalization_is_measured_only_for_that_mass",
            "srs_case_mix_priors_are_static_estimates_not_observed_browser_sentence_labels",
            "49_repaired_families_are_still_small_for_formula_selection",
            "band_grade_is_for_llm_data_allocation_research_not_runtime_policy_promotion",
        ],
        "next_steps": [
            "Use the band grade to choose a small LLM follow-through batch plus low-band controls.",
            "Add or restore product-relevant phrase/no-winner rows before making full SRS-normalized claims.",
            "Re-run this report after any new LLM evidence admission so the allocation heuristic can be falsified.",
        ],
    }


def _formula_rows(payload: Mapping[str, object]) -> list[dict[str, object]]:
    comparison_rows = _mapping_rows(payload.get("comparison_rows"))
    rows = []
    seen: set[tuple[str, str]] = set()
    for row in comparison_rows:
        key = (str(row.get("scorer_id") or ""), str(row.get("formula_id") or ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "scorer_id": key[0],
                "formula_id": key[1],
                "formula_family": str(row.get("formula_family") or ""),
                "scope_id": str(row.get("scope_id") or f"{key[0]}::{key[1]}"),
                "weights": dict(_as_mapping(row.get("weights"))),
                "rank_metrics": {
                    "spearman_rank_correlation": row.get("spearman_rank_correlation"),
                    "discovery_spearman": row.get("discovery_spearman"),
                    "internal_locked_eval_spearman": row.get("internal_locked_eval_spearman"),
                    "top_k_lift": row.get("top_k_lift"),
                    "brier_score": row.get("brier_score"),
                },
            }
        )
    return rows


def _grade_formulas(
    *,
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    observation_by_key: Mapping[tuple[str, str], Mapping[str, object]],
    case_rows_by_key: Mapping[tuple[str, str], Sequence[Mapping[str, object]]],
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
        scored = []
        for observation in observations_by_scorer.get(scorer_id, []):
            scored.append(
                {
                    "family_id": str(observation.get("family_id") or ""),
                    "predicted_need": _weighted_score(
                        _as_mapping(observation.get("features")), weights
                    ),
                }
            )
        bands = _assign_bands(scored)
        band_metrics = []
        for band_id in BAND_IDS:
            family_ids = bands.get(band_id, [])
            rows = [
                row
                for family_id in family_ids
                for row in case_rows_by_key.get((scorer_id, family_id), [])
            ]
            band_metrics.append(
                _band_metrics(
                    band_id=band_id,
                    scorer_id=scorer_id,
                    family_ids=family_ids,
                    rows=rows,
                    observations=observation_by_key,
                    targets=targets,
                )
            )
        primary = _target_grade(band_metrics, PRIMARY_TARGET_ID)
        raw = _raw_grade(band_metrics)
        row = {
            "scope_id": str(formula.get("scope_id") or ""),
            "formula_id": str(formula.get("formula_id") or ""),
            "formula_family": str(formula.get("formula_family") or ""),
            "scorer_id": scorer_id,
            "weights": dict(weights),
            "rank_metrics": dict(_as_mapping(formula.get("rank_metrics"))),
            "band_family_counts": {
                metric["band_id"]: metric.get("family_count") for metric in band_metrics
            },
            "raw_high_low_failure_delta": raw.get("high_low_failure_delta"),
            "raw_order_score": raw.get("order_score"),
            "primary_target_id": PRIMARY_TARGET_ID,
            "primary_normalized_high_low_failure_delta": primary.get("high_low_failure_delta"),
            "primary_normalized_order_score": primary.get("order_score"),
            "primary_min_measured_target_weight": primary.get("min_measured_target_weight"),
            "primary_max_unmeasured_target_weight": primary.get("max_unmeasured_target_weight"),
            "primary_grade_score": primary.get("grade_score"),
        }
        grade_rows.append(row)
        detail_rows.append(
            {
                **row,
                "band_metrics": band_metrics,
            }
        )
    return grade_rows, detail_rows


def _assign_bands(rows: Sequence[Mapping[str, object]]) -> dict[str, list[str]]:
    grouped: dict[float, list[str]] = defaultdict(list)
    for row in rows:
        grouped[round(_safe_float(row.get("predicted_need")), 6)].append(
            str(row.get("family_id") or "")
        )
    scores = sorted(grouped, reverse=True)
    output = {band_id: [] for band_id in BAND_IDS}
    if not scores:
        return output
    if len(scores) == 1:
        output["middle_need"].extend(sorted(grouped[scores[0]]))
        return output
    if len(scores) == 2:
        output["high_need"].extend(sorted(grouped[scores[0]]))
        output["low_need"].extend(sorted(grouped[scores[1]]))
        return output
    if len(scores) == 3:
        for band_id, score in zip(BAND_IDS, scores, strict=True):
            output[band_id].extend(sorted(grouped[score]))
        return output
    total = sum(len(grouped[score]) for score in scores)
    cursor = 0
    for score in scores:
        family_ids = sorted(grouped[score])
        midpoint = (cursor + cursor + len(family_ids) - 1) / 2 / max(total, 1)
        if midpoint < 1 / 3:
            band_id = "high_need"
        elif midpoint < 2 / 3:
            band_id = "middle_need"
        else:
            band_id = "low_need"
        output[band_id].extend(family_ids)
        cursor += len(family_ids)
    return output


def _band_metrics(
    *,
    band_id: str,
    scorer_id: str,
    family_ids: Sequence[str],
    rows: Sequence[Mapping[str, object]],
    observations: Mapping[tuple[str, str], Mapping[str, object]],
    targets: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    case_type_metrics = _case_type_metrics(rows)
    family_failure_rates = [
        _safe_float(observations[(scorer_id, family_id)].get("observed_failure_rate"))
        for family_id in family_ids
        if (scorer_id, family_id) in observations
    ]
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
            _target_normalized_metrics(
                target=target,
                case_type_metrics=case_type_metrics,
            )
            for target in targets
        ],
        "sample_triggers": _sample_triggers(rows),
    }


def _case_type_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[_case_type(row)].append(row)
    metrics: dict[str, dict[str, object]] = {}
    for case_type in CASE_TYPES:
        group = grouped.get(case_type, [])
        failure_count = sum(1 for row in group if _is_failure(row))
        metrics[case_type] = {
            "case_count": len(group),
            "failure_count": failure_count,
            "success_count": len(group) - failure_count,
            "failure_rate": _round4(_rate(failure_count, len(group))),
            "success_rate": _round4(1 - _rate(failure_count, len(group))) if group else None,
        }
    extra_types = sorted(set(grouped) - set(CASE_TYPES))
    for case_type in extra_types:
        group = grouped[case_type]
        failure_count = sum(1 for row in group if _is_failure(row))
        metrics[case_type] = {
            "case_count": len(group),
            "failure_count": failure_count,
            "success_count": len(group) - failure_count,
            "failure_rate": _round4(_rate(failure_count, len(group))),
            "success_rate": _round4(1 - _rate(failure_count, len(group))) if group else None,
        }
    return metrics


def _target_normalized_metrics(
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


def _normalization_targets(
    *,
    surface_rows: Sequence[Mapping[str, object]],
    srs_case_mix_prior_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    targets = [
        {
            "target_id": "global_test_case_mix",
            "description": "The current product-scope test-suite case mix.",
            "case_type_weights": _case_mix(surface_rows),
            "source": "score_surface_row_results",
        },
    ]
    measured_types = [
        case_type for case_type, weight in _case_mix(surface_rows).items() if weight > 0
    ]
    if measured_types:
        weight = 1.0 / len(measured_types)
        targets.append(
            {
                "target_id": "balanced_measured_case_mix",
                "description": "Equal weight over case types present in this score surface.",
                "case_type_weights": {case_type: weight for case_type in measured_types},
                "source": "score_surface_row_results",
            }
        )
    for scenario in _mapping_rows(srs_case_mix_prior_payload.get("scenario_rows")):
        targets.append(
            {
                "target_id": str(scenario.get("scenario_id") or ""),
                "description": str(scenario.get("description") or ""),
                "case_type_weights": _scenario_case_mix(scenario),
                "source": "srs_case_mix_prior",
            }
        )
    return [
        target for target in targets if _normalize_weights(_as_mapping(target["case_type_weights"]))
    ]


def _scenario_case_mix(scenario: Mapping[str, object]) -> dict[str, float]:
    totals = {case_type: 0.0 for case_type in CASE_TYPES}
    for row in _mapping_rows(scenario.get("band_prior_rows")):
        share = _safe_float(row.get("srs_pair_share"))
        totals["positive_active"] += share * _safe_float(row.get("p_positive_active"))
        totals["shadow_negative"] += share * _safe_float(row.get("p_shadow_negative"))
        totals["phrase_no_winner"] += share * _safe_float(row.get("p_phrase_no_winner"))
    return _normalize_weights(totals)


def _case_mix(rows: Sequence[Mapping[str, object]]) -> dict[str, float]:
    counts = Counter(_case_type(row) for row in rows)
    total = sum(counts.values())
    if total <= 0:
        return {}
    return {case_type: counts.get(case_type, 0) / total for case_type in CASE_TYPES}


def _target_grade(
    band_metrics: Sequence[Mapping[str, object]],
    target_id: str,
) -> dict[str, object]:
    by_band = {str(row.get("band_id") or ""): row for row in band_metrics}
    rates = {}
    measured_weights = []
    unmeasured_weights = []
    for band_id in BAND_IDS:
        metrics = _target_metrics(by_band.get(band_id, {}), target_id)
        rate = metrics.get("measured_only_failure_rate")
        rates[band_id] = _safe_float(rate) if rate is not None else None
        measured_weights.append(_safe_float(metrics.get("measured_target_weight")))
        unmeasured_weights.append(_safe_float(metrics.get("unmeasured_target_weight")))
    high_low = (
        _round4(rates["high_need"] - rates["low_need"])
        if rates["high_need"] is not None and rates["low_need"] is not None
        else None
    )
    order_score = _order_score(rates)
    coverage = min(measured_weights) if measured_weights else 0.0
    grade = (
        _round4(max(0.0, _safe_float(high_low)) * _safe_float(order_score) * coverage)
        if high_low is not None
        else None
    )
    return {
        "target_id": target_id,
        "high_low_failure_delta": high_low,
        "order_score": order_score,
        "min_measured_target_weight": _round4(coverage),
        "max_unmeasured_target_weight": _round4(max(unmeasured_weights, default=0.0)),
        "grade_score": grade,
    }


def _raw_grade(band_metrics: Sequence[Mapping[str, object]]) -> dict[str, object]:
    rates = {
        str(row.get("band_id") or ""): _safe_float(row.get("raw_failure_rate"))
        if row.get("raw_failure_rate") is not None
        else None
        for row in band_metrics
    }
    high_low = (
        _round4(rates["high_need"] - rates["low_need"])
        if rates.get("high_need") is not None and rates.get("low_need") is not None
        else None
    )
    return {"high_low_failure_delta": high_low, "order_score": _order_score(rates)}


def _target_metrics(band: Mapping[str, object], target_id: str) -> dict[str, object]:
    for row in _mapping_rows(band.get("target_normalized_metrics")):
        if str(row.get("target_id") or "") == target_id:
            return dict(row)
    return {}


def _order_score(rates: Mapping[str, float | None]) -> float | None:
    comparable = [
        ("high_need", "middle_need"),
        ("middle_need", "low_need"),
        ("high_need", "low_need"),
    ]
    available = [
        (left, right)
        for left, right in comparable
        if rates.get(left) is not None and rates.get(right) is not None
    ]
    if not available:
        return None
    correct = sum(1 for left, right in available if rates[left] >= rates[right])
    return _round4(correct / len(available))


def _case_rows_by_key(
    rows: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], list[Mapping[str, object]]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("scorer_id") or ""), str(row.get("family_id") or ""))].append(row)
    return grouped


def _representative_scope_ids(payload: Mapping[str, object]) -> set[str]:
    scope_ids = set()
    for row in _mapping_rows(_as_mapping(payload.get("summary")).get("best_by_scope")):
        scope = str(row.get("scope_id") or "")
        if "::" in scope:
            scope_ids.add(scope.split("::", 1)[1] + "::" + str(row.get("formula_id") or ""))
        scope_ids.add(str(row.get("scorer_id") or "") + "::" + str(row.get("formula_id") or ""))
    return scope_ids


def _representative_comparison(
    grade_rows: Sequence[Mapping[str, object]],
    formula_sweep_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    wanted = {
        (str(row.get("scorer_id") or ""), str(row.get("formula_id") or ""))
        for row in _mapping_rows(
            _as_mapping(formula_sweep_payload.get("summary")).get("best_by_scope")
        )
    }
    wanted.update(
        {
            ("best_product_rank_sentence_transformer_a0000_mneg0025", "shadow_coverage_only"),
            ("current_v3_like_sentence_transformer_a0000_m0000", "shadow_coverage_only"),
            ("tfidf_best_by_scorer_tfidf_a0000_mneg0005", "shadow_coverage_only"),
        }
    )
    return _public_grade_rows(
        [
            row
            for row in grade_rows
            if (str(row.get("scorer_id") or ""), str(row.get("formula_id") or "")) in wanted
        ]
    )


def _public_grade_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "formula_id": row.get("formula_id"),
            "formula_family": row.get("formula_family"),
            "scorer_id": row.get("scorer_id"),
            "raw_high_low_failure_delta": row.get("raw_high_low_failure_delta"),
            "raw_order_score": row.get("raw_order_score"),
            "primary_normalized_high_low_failure_delta": row.get(
                "primary_normalized_high_low_failure_delta"
            ),
            "primary_normalized_order_score": row.get("primary_normalized_order_score"),
            "primary_min_measured_target_weight": row.get("primary_min_measured_target_weight"),
            "primary_max_unmeasured_target_weight": row.get("primary_max_unmeasured_target_weight"),
            "primary_grade_score": row.get("primary_grade_score"),
            "band_family_counts": row.get("band_family_counts"),
            "rank_metrics": row.get("rank_metrics"),
            "weights": row.get("weights"),
        }
        for row in rows
    ]


def _grade_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float, str]:
    return (
        -_safe_float(row.get("primary_grade_score")),
        -_safe_float(row.get("primary_normalized_high_low_failure_delta")),
        -_safe_float(row.get("primary_normalized_order_score")),
        _safe_float(row.get("primary_max_unmeasured_target_weight")),
        str(row.get("scope_id") or ""),
    )


def _case_type(row: Mapping[str, object]) -> str:
    dims = _as_mapping(row.get("slice_dimensions"))
    values = dims.get("manual_case_type")
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, str) and values:
        return values
    if str(row.get("gold_decision") or "") == "replace":
        return "positive_active"
    winner_type = str(row.get("gold_winner_type") or "")
    if winner_type == "shadow":
        return "shadow_negative"
    if str(row.get("gold_decision") or "") == "abstain":
        return "phrase_no_winner"
    return "unknown"


def _is_failure(row: Mapping[str, object]) -> bool:
    error = str(row.get("error_type") or "")
    if error in {"false_abstain", "harmful_replace"}:
        return True
    gold = str(row.get("gold_decision") or "")
    predicted = str(row.get("predicted_decision") or "")
    return (gold == "replace" and predicted == "abstain") or (
        gold == "abstain" and predicted == "replace"
    )


def _case_type_counts_by_scorer(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get("scorer_id") or "")][_case_type(row)] += 1
    return {scorer: dict(sorted(counts.items())) for scorer, counts in sorted(grouped.items())}


def _normalize_weights(weights: Mapping[str, object]) -> dict[str, float]:
    values = {
        case_type: max(0.0, _safe_float(weights.get(case_type)))
        for case_type in CASE_TYPES
        if _safe_float(weights.get(case_type)) > 0
    }
    total = sum(values.values())
    if total <= 0:
        return {}
    return {case_type: value / total for case_type, value in values.items()}


def _mean_float(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _rate(numerator: int | float, denominator: int | float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
