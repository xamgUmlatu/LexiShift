from __future__ import annotations

from collections import Counter, defaultdict
from math import sqrt
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_heuristic_difficulty_surface_common import (
    CASE_TYPES,
    ERROR_OUTCOMES,
    PRIMARY_SELECTION_MODE,
    _as_mapping,
    _mapping_rows,
    _optional_float,
    _optional_ratio,
    _repo_path,
    _round4,
    _safe_ratio,
)
from semantic_veto_product_quality_en_es import _safe_float, score_product_outcome_counts


def _normalized_score_rows(
    *,
    report: Mapping[str, object],
    source_id: str,
    source_path: Path | None,
    authored_by_trigger: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    scorer_id = str(_as_mapping(report.get("config")).get("scorer_id") or source_id).strip()
    rows: list[dict[str, object]] = []
    for row in _mapping_rows(report.get("row_results")):
        trigger = str(row.get("trigger") or "").strip()
        authored = _as_mapping(authored_by_trigger.get(trigger))
        dims = _normalize_slice_dimensions(row.get("slice_dimensions"))
        gold_decision = _normalize_decision(row.get("gold_decision"))
        predicted_decision = _normalize_decision(row.get("predicted_decision"))
        product_outcome = _product_outcome(gold=gold_decision, predicted=predicted_decision)
        active_score = _optional_float(row.get("active_score"))
        shadow_score = _optional_float(row.get("strongest_shadow_score"))
        margin = _optional_float(row.get("margin"))
        if margin is None and active_score is not None and shadow_score is not None:
            margin = active_score - shadow_score
        phrase_score = _optional_float(row.get("phrase_control_score"))
        phrase_score_lead = None
        if phrase_score is not None and active_score is not None and shadow_score is not None:
            phrase_score_lead = phrase_score - max(active_score, shadow_score)
        case_type = _first_dim(dims, "manual_case_type") or _case_type_from_winner(row)
        selection_mode = _first_dim(dims, "selection_mode") or str(
            authored.get("selection_mode") or ""
        )
        source_rank = _optional_float(authored.get("source_rank"))
        source_rank_bin = (
            _first_dim(dims, "source_rank_bin")
            or str(authored.get("source_rank_bin") or "")
            or "missing"
        )
        normalized = {
            "case_id": str(row.get("case_id") or ""),
            "source_report": _repo_path(source_path),
            "source_id": source_id,
            "scorer_id": scorer_id,
            "family_id": str(row.get("family_id") or ""),
            "trigger": trigger,
            "sentence": str(row.get("sentence") or ""),
            "gold_decision": gold_decision,
            "predicted_decision": predicted_decision,
            "gold_winner_type": str(row.get("gold_winner_type") or ""),
            "product_outcome": product_outcome,
            "error_type": _error_type(product_outcome),
            "manual_case_type": case_type,
            "heuristic_group": _first_dim(dims, "heuristic_group")
            or str(authored.get("group_id") or ""),
            "selection_mode": selection_mode,
            "source_rank": source_rank,
            "source_rank_bin": source_rank_bin,
            "source_rank_known": source_rank is not None,
            "polysemy_band": _first_dim(dims, "polysemy_band")
            or str(authored.get("polysemy_band") or "missing"),
            "shadow_contract": _first_dim(dims, "shadow_contract")
            or str(authored.get("shadow_contract") or "missing"),
            "manual_review_state": _first_dim(dims, "manual_review_state"),
            "wordnet_sense_count": int(authored.get("wordnet_sense_count") or 0),
            "wordnet_pos_count": int(authored.get("wordnet_pos_count") or 0),
            "target_lemma": str(authored.get("target_lemma") or ""),
            "expected_veto_difficulty": str(authored.get("expected_veto_difficulty") or ""),
            "active_score": _round4(active_score) if active_score is not None else None,
            "strongest_shadow_score": _round4(shadow_score) if shadow_score is not None else None,
            "margin": _round4(margin) if margin is not None else None,
            "score_margin_bin": _margin_bin(margin),
            "phrase_control_score": _round4(phrase_score) if phrase_score is not None else None,
            "phrase_score_lead": _round4(phrase_score_lead)
            if phrase_score_lead is not None
            else None,
            "phrase_score_lead_bin": _phrase_score_lead_bin(phrase_score_lead),
            "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        }
        rows.append(normalized)
    return rows


def _metrics_for_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    counts = Counter(str(row.get("product_outcome") or "") for row in rows)
    metrics = score_product_outcome_counts(
        outcome_counts=counts,
        weights=weights,
        acceptance=acceptance,
    )
    case_type_counts: dict[str, Counter[str]] = {case_type: Counter() for case_type in CASE_TYPES}
    for row in rows:
        case_type = str(row.get("manual_case_type") or "")
        if case_type in case_type_counts:
            case_type_counts[case_type][str(row.get("product_outcome") or "")] += 1
    positive_count = sum(case_type_counts["positive_active"].values())
    shadow_count = sum(case_type_counts["shadow_negative"].values())
    phrase_count = sum(case_type_counts["phrase_no_winner"].values())
    difficulty_scores = {
        "positive_allow_difficulty": _optional_ratio(
            case_type_counts["positive_active"]["positive_abstain"],
            positive_count,
        ),
        "shadow_negative_difficulty": _optional_ratio(
            case_type_counts["shadow_negative"]["negative_allow"],
            shadow_count,
        ),
        "phrase_no_winner_difficulty": _optional_ratio(
            case_type_counts["phrase_no_winner"]["negative_allow"],
            phrase_count,
        ),
        "overall_veto_difficulty": _weighted_loss_rate(
            outcome_counts=counts,
            weights=weights,
        ),
    }
    metrics["difficulty_scores"] = difficulty_scores
    metrics["case_type_counts"] = {
        case_type: dict(sorted(counts_by_type.items()))
        for case_type, counts_by_type in case_type_counts.items()
    }
    return metrics


def _build_breakdowns(
    *,
    rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    dimensions = (
        "scorer_id",
        "heuristic_group",
        "source_rank_bin",
        "polysemy_band",
        "wordnet_pos_count",
        "shadow_contract",
        "manual_case_type",
        "selection_mode",
        "score_margin_bin",
        "phrase_score_lead_bin",
    )
    breakdowns: dict[str, object] = {}
    for dimension in dimensions:
        breakdowns[_public_dimension_id(dimension)] = _breakdown(
            rows=rows,
            dimension=dimension,
            weights=weights,
            acceptance=acceptance,
        )
    breakdowns["scorer_x_manual_case_type"] = _breakdown(
        rows=rows,
        dimension="scorer_id",
        secondary_dimension="manual_case_type",
        weights=weights,
        acceptance=acceptance,
    )
    breakdowns["scorer_x_heuristic_group"] = _breakdown(
        rows=rows,
        dimension="scorer_id",
        secondary_dimension="heuristic_group",
        weights=weights,
        acceptance=acceptance,
    )
    breakdowns["primary_scorer_x_heuristic_group"] = _breakdown(
        rows=[row for row in rows if row.get("selection_mode") == PRIMARY_SELECTION_MODE],
        dimension="scorer_id",
        secondary_dimension="heuristic_group",
        weights=weights,
        acceptance=acceptance,
    )
    return breakdowns


def _breakdown(
    *,
    rows: Sequence[Mapping[str, object]],
    dimension: str,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
    secondary_dimension: str | None = None,
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str | None], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        value = _dimension_value(row, dimension)
        secondary_value = (
            _dimension_value(row, secondary_dimension) if secondary_dimension else None
        )
        grouped[(value, secondary_value)].append(row)
    result = []
    for (value, secondary_value), group in grouped.items():
        metrics = _metrics_for_rows(group, weights=weights, acceptance=acceptance)
        payload = {
            "dimension": _public_dimension_id(dimension),
            "value": value,
            "case_rows": len(group),
            "metrics": metrics,
        }
        if secondary_dimension:
            payload["secondary_dimension"] = _public_dimension_id(secondary_dimension)
            payload["secondary_value"] = secondary_value
            payload["scope_id"] = f"{value}::{secondary_value}"
        else:
            payload["scope_id"] = value
        result.append(payload)
    result.sort(
        key=lambda row: (
            str(row.get("value") or ""),
            str(row.get("secondary_value") or ""),
        )
    )
    return result


def _failure_concentration(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    dimensions = (
        "manual_case_type",
        "heuristic_group",
        "source_rank_bin",
        "polysemy_band",
        "shadow_contract",
        "selection_mode",
        "score_margin_bin",
    )
    scorer_failure_totals = Counter(
        str(row.get("scorer_id") or "")
        for row in rows
        if str(row.get("product_outcome") or "") in ERROR_OUTCOMES
    )
    concentration_rows = []
    for dimension in dimensions:
        grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
        for row in rows:
            grouped[(str(row.get("scorer_id") or ""), _dimension_value(row, dimension))].append(row)
        for (scorer_id, value), group in grouped.items():
            failures = [
                row for row in group if str(row.get("product_outcome") or "") in ERROR_OUTCOMES
            ]
            if not failures:
                continue
            failure_counts = Counter(str(row.get("product_outcome") or "") for row in failures)
            concentration_rows.append(
                {
                    "dimension": _public_dimension_id(dimension),
                    "value": value,
                    "scorer_id": scorer_id,
                    "case_rows": len(group),
                    "failure_count": len(failures),
                    "failure_rate": _optional_ratio(len(failures), len(group)),
                    "failure_share_of_scorer_failures": _optional_ratio(
                        len(failures),
                        scorer_failure_totals[scorer_id],
                    ),
                    "positive_abstain_count": failure_counts["positive_abstain"],
                    "negative_allow_count": failure_counts["negative_allow"],
                    "sample_case_ids": [str(row.get("case_id") or "") for row in failures[:5]],
                }
            )
    concentration_rows.sort(
        key=lambda row: (
            -int(row.get("failure_count") or 0),
            -_safe_float(row.get("failure_rate")),
            str(row.get("dimension") or ""),
            str(row.get("value") or ""),
        )
    )
    return concentration_rows[:20]


def _formula_bakeoff(
    *,
    rows: Sequence[Mapping[str, object]],
    authored_by_trigger: Mapping[str, Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    observation_rows = _trigger_observation_rows(
        rows=rows,
        weights=weights,
        acceptance=acceptance,
    )
    observations_by_scorer: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in observation_rows:
        observations_by_scorer[str(row.get("scorer_id") or "")].append(row)
    comparison_rows = []
    formula_score_rows = []
    for scorer_id, scorer_observations in sorted(observations_by_scorer.items()):
        for formula_id in ("baseline_frequency_polysemy", "richer_case_shape", "evidence_margin"):
            pairs = []
            score_rows = []
            excluded_missing_rank = 0
            excluded_sentinel = 0
            for observed in scorer_observations:
                trigger = str(observed.get("trigger") or "")
                authored = _as_mapping(authored_by_trigger.get(trigger))
                if str(authored.get("selection_mode") or "") != PRIMARY_SELECTION_MODE:
                    excluded_sentinel += 1
                    continue
                formula_score = _formula_score(
                    formula_id=formula_id,
                    authored=authored,
                    observed=observed,
                )
                if formula_score is None:
                    excluded_missing_rank += 1
                    continue
                observed_difficulty = _as_mapping(
                    _as_mapping(observed.get("metrics")).get("difficulty_scores")
                ).get("overall_veto_difficulty")
                if observed_difficulty is None:
                    continue
                pair = (float(formula_score), float(observed_difficulty))
                pairs.append(pair)
                score_row = {
                    "formula_id": formula_id,
                    "scorer_id": scorer_id,
                    "trigger": trigger,
                    "heuristic_group": str(authored.get("group_id") or ""),
                    "source_rank_bin": str(authored.get("source_rank_bin") or "missing"),
                    "predicted_difficulty": _round4(formula_score),
                    "observed_difficulty": _round4(observed_difficulty),
                    "case_rows": int(observed.get("case_rows") or 0),
                }
                score_rows.append(score_row)
                formula_score_rows.append(score_row)
            comparison_rows.append(
                {
                    "formula_id": formula_id,
                    "scorer_id": scorer_id,
                    "comparison_scope": "primary_only_rank_known",
                    "compared_triggers": len(pairs),
                    "excluded_sentinel_triggers": excluded_sentinel,
                    "excluded_missing_rank_triggers": excluded_missing_rank,
                    "spearman_rank_correlation": _spearman(pairs),
                    "top_predicted": sorted(
                        score_rows,
                        key=lambda row: (
                            -_safe_float(row.get("predicted_difficulty")),
                            -_safe_float(row.get("observed_difficulty")),
                            str(row.get("trigger") or ""),
                        ),
                    )[:6],
                }
            )
    comparison_rows.sort(
        key=lambda row: (
            str(row.get("scorer_id") or ""),
            str(row.get("formula_id") or ""),
        )
    )
    return {
        "comparison_rows": comparison_rows,
        "formula_score_rows": formula_score_rows,
        "formula_definitions": [
            {
                "formula_id": "baseline_frequency_polysemy",
                "inputs": ["source_rank", "wordnet_sense_count", "wordnet_pos_count"],
                "rank_missing_policy": "excluded_from_correlation_not_imputed",
            },
            {
                "formula_id": "richer_case_shape",
                "inputs": [
                    "baseline_frequency_polysemy",
                    "shadow_contract",
                    "case_type_mix",
                ],
                "rank_missing_policy": "excluded_from_correlation_not_imputed",
            },
            {
                "formula_id": "evidence_margin",
                "inputs": [
                    "richer_case_shape",
                    "mean_abs_active_shadow_margin",
                    "phrase_score_lead_when_available",
                ],
                "missing_features": ["phrase_score_lead"],
                "rank_missing_policy": "excluded_from_correlation_not_imputed",
            },
        ],
    }


def _trigger_observation_rows(
    *,
    rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("scorer_id") or ""), str(row.get("trigger") or ""))].append(row)
    result = []
    for (scorer_id, trigger), group in grouped.items():
        metrics = _metrics_for_rows(group, weights=weights, acceptance=acceptance)
        margins = [
            abs(float(row.get("margin")))
            for row in group
            if isinstance(row.get("margin"), (int, float))
        ]
        result.append(
            {
                "scorer_id": scorer_id,
                "trigger": trigger,
                "case_rows": len(group),
                "metrics": metrics,
                "mean_abs_margin": _round4(sum(margins) / len(margins)) if margins else None,
                "near_tie_rate": _optional_ratio(
                    sum(1 for value in margins if value < 0.02),
                    len(margins),
                ),
            }
        )
    return result


def _formula_score(
    *,
    formula_id: str,
    authored: Mapping[str, object],
    observed: Mapping[str, object],
) -> float | None:
    baseline = _baseline_formula_score(authored)
    if baseline is None:
        return None
    if formula_id == "baseline_frequency_polysemy":
        return baseline
    shadow_score = {
        "full": 1.0,
        "limited": 0.65,
        "not_applicable": 0.25,
    }.get(str(authored.get("shadow_contract") or ""), 0.5)
    case_counts = _as_mapping(authored.get("case_type_counts"))
    case_total = sum(int(value or 0) for value in case_counts.values())
    competing_case_share = _safe_ratio(
        int(case_counts.get("shadow_negative") or 0)
        + int(case_counts.get("phrase_no_winner") or 0),
        case_total,
    )
    richer = 0.72 * baseline + 0.18 * shadow_score + 0.10 * competing_case_share
    if formula_id == "richer_case_shape":
        return richer
    mean_abs_margin = observed.get("mean_abs_margin")
    margin_risk = 0.5
    if isinstance(mean_abs_margin, (int, float)):
        margin_risk = 1.0 - min(1.0, float(mean_abs_margin) / 0.1)
    return 0.70 * richer + 0.30 * margin_risk


def _baseline_formula_score(authored: Mapping[str, object]) -> float | None:
    rank = _optional_float(authored.get("source_rank"))
    if rank is None:
        return None
    rank_score = _rank_risk_score(rank)
    sense_score = min(1.0, int(authored.get("wordnet_sense_count") or 0) / 20.0)
    pos_score = min(1.0, max(0, int(authored.get("wordnet_pos_count") or 0) - 1) / 3.0)
    return 0.50 * rank_score + 0.35 * sense_score + 0.15 * pos_score


def _rank_risk_score(rank: float) -> float:
    if rank <= 500:
        return 1.0
    if rank <= 1000:
        return 0.85
    if rank <= 2000:
        return 0.65
    if rank <= 5000:
        return 0.45
    return 0.25


def _case_type_expansion_recommendations(
    *,
    rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row.get("heuristic_group") or ""),
                str(row.get("manual_case_type") or ""),
                str(row.get("shadow_contract") or ""),
            )
        ].append(row)
    recommendations = []
    for (group_id, case_type, shadow_contract), group in sorted(grouped.items()):
        metrics = _metrics_for_rows(group, weights=weights, acceptance=acceptance)
        difficulty = _as_mapping(metrics.get("difficulty_scores"))
        if case_type == "phrase_no_winner":
            phrase_difficulty = difficulty.get("phrase_no_winner_difficulty")
            if _safe_float(phrase_difficulty) >= 0.40 or len(group) < 8:
                recommendations.append(
                    {
                        "cell_id": f"{group_id}:{case_type}:{shadow_contract}",
                        "priority": "P0" if _safe_float(phrase_difficulty) >= 0.60 else "P1",
                        "reason": "phrase_no_winner_underfilled_or_leaking",
                        "recommended_action": "expand_phrase_no_winner_discovery_then_locked_eval",
                        "observed_case_rows": len(group),
                        "observed_difficulty": phrase_difficulty,
                        "manual_discovery_rows": 4,
                        "llm_discovery_rows": 12,
                        "locked_eval_rows": 6,
                        "notes": "This is the current main product-risk cell for high-positive-allow scorers.",
                    }
                )
        elif case_type == "shadow_negative" and shadow_contract != "not_applicable":
            shadow_difficulty = difficulty.get("shadow_negative_difficulty")
            if _safe_float(shadow_difficulty) >= 0.20 or len(group) < 8:
                recommendations.append(
                    {
                        "cell_id": f"{group_id}:{case_type}:{shadow_contract}",
                        "priority": "P1",
                        "reason": "shadow_negative_needs_more_competition_coverage",
                        "recommended_action": "add_shadow_negative_rows_and_review_shadow_evidence",
                        "observed_case_rows": len(group),
                        "observed_difficulty": shadow_difficulty,
                        "manual_discovery_rows": 4,
                        "llm_discovery_rows": 8,
                        "locked_eval_rows": 4,
                        "notes": "Use real alternate senses only.",
                    }
                )
        elif case_type == "positive_active":
            positive_difficulty = difficulty.get("positive_allow_difficulty")
            if _safe_float(positive_difficulty) >= 0.20:
                recommendations.append(
                    {
                        "cell_id": f"{group_id}:{case_type}:{shadow_contract}",
                        "priority": "P2",
                        "reason": "positive_active_false_abstain_cluster",
                        "recommended_action": "review_active_evidence_before_row_expansion",
                        "observed_case_rows": len(group),
                        "observed_difficulty": positive_difficulty,
                        "manual_discovery_rows": 2,
                        "llm_discovery_rows": 6,
                        "locked_eval_rows": 3,
                        "notes": "Prefer source/evidence improvements if margins show near ties.",
                    }
                )
    return recommendations


def _veto_only_summary(payload: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {}
    best = _as_mapping(_as_mapping(payload.get("summary")).get("best_product_rank_row"))
    return {
        "status": str(payload.get("status") or ""),
        "decision": str(payload.get("decision") or ""),
        "positive_allow_rate": best.get("positive_allow_rate"),
        "negative_abstain_rate": best.get("negative_abstain_rate"),
        "utility_score": best.get("utility_score"),
        "target_status": best.get("target_status"),
    }


def _authored_by_trigger(authoring_payload: Mapping[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("trigger") or "").strip(): dict(row)
        for row in _mapping_rows(authoring_payload.get("authored_triggers"))
        if str(row.get("trigger") or "").strip()
    }


def _weighted_loss_rate(
    *,
    outcome_counts: Mapping[str, object],
    weights: Mapping[str, float],
) -> float | None:
    positive_count = int(outcome_counts.get("positive_allow") or 0) + int(
        outcome_counts.get("positive_abstain") or 0
    )
    negative_count = int(outcome_counts.get("negative_abstain") or 0) + int(
        outcome_counts.get("negative_allow") or 0
    )
    max_loss = positive_count * (
        weights.get("positive_allow", 1.0) - weights.get("positive_abstain", -0.4)
    ) + negative_count * (
        weights.get("negative_abstain", 0.8) - weights.get("negative_allow", -0.6)
    )
    if max_loss <= 0:
        return None
    observed_loss = int(outcome_counts.get("positive_abstain") or 0) * (
        weights.get("positive_allow", 1.0) - weights.get("positive_abstain", -0.4)
    ) + int(outcome_counts.get("negative_allow") or 0) * (
        weights.get("negative_abstain", 0.8) - weights.get("negative_allow", -0.6)
    )
    return _round4(max(0.0, min(1.0, observed_loss / max_loss)))


def _product_outcome(*, gold: str, predicted: str) -> str:
    if gold == "replace" and predicted == "replace":
        return "positive_allow"
    if gold == "replace":
        return "positive_abstain"
    if predicted == "replace":
        return "negative_allow"
    return "negative_abstain"


def _error_type(product_outcome: str) -> str:
    if product_outcome == "positive_abstain":
        return "false_abstain"
    if product_outcome == "negative_allow":
        return "harmful_replace"
    return ""


def _normalize_decision(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"replace", "allow", "yes"}:
        return "replace"
    if text in {"abstain", "no_replace", "no-replace", "no", "none"}:
        return "abstain"
    raise ValueError(f"Unknown semantic-veto decision value: {value!r}")


def _case_type_from_winner(row: Mapping[str, object]) -> str:
    winner_type = str(row.get("gold_winner_type") or "").strip()
    if winner_type == "active":
        return "positive_active"
    if winner_type == "shadow":
        return "shadow_negative"
    return "phrase_no_winner"


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, raw_values in value.items():
        if isinstance(raw_values, Sequence) and not isinstance(raw_values, (str, bytes)):
            values = [str(item or "").strip() for item in raw_values if str(item or "").strip()]
        else:
            values = [str(raw_values or "").strip()] if str(raw_values or "").strip() else []
        if values:
            normalized[str(key)] = values
    return normalized


def _first_dim(dimensions: Mapping[str, Sequence[str]], key: str) -> str:
    values = dimensions.get(key)
    if not values:
        return ""
    return str(values[0] or "").strip()


def _dimension_value(row: Mapping[str, object], dimension: str | None) -> str:
    if not dimension:
        return ""
    value = row.get(dimension)
    if value is None or value == "":
        return "missing"
    if dimension == "wordnet_pos_count":
        return f"pos_count:{int(value or 0)}"
    return str(value)


def _public_dimension_id(dimension: str) -> str:
    return {
        "scorer_id": "scorer",
        "heuristic_group": "heuristic_group",
        "source_rank_bin": "source_rank_bin",
        "polysemy_band": "polysemy_band",
        "wordnet_pos_count": "wordnet_pos_count",
        "shadow_contract": "shadow_contract",
        "manual_case_type": "manual_case_type",
        "selection_mode": "selection_mode",
        "score_margin_bin": "score_margin_bin",
        "phrase_score_lead_bin": "phrase_score_lead_bin",
    }.get(dimension, dimension)


def _margin_bin(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < -0.05:
        return "shadow_leads_gt_0.05"
    if value < -0.02:
        return "shadow_leads_0.02_to_0.05"
    if value < 0.02:
        return "near_tie_abs_lt_0.02"
    if value < 0.05:
        return "active_leads_0.02_to_0.05"
    return "active_leads_gt_0.05"


def _phrase_score_lead_bin(value: float | None) -> str:
    if value is None:
        return "missing"
    if value >= 0.05:
        return "phrase_leads_gt_0.05"
    if value >= 0.0:
        return "phrase_near_or_leads"
    return "phrase_below_active_shadow"


def _spearman(pairs: Sequence[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    left_ranks = _rank_values([pair[0] for pair in pairs])
    right_ranks = _rank_values([pair[1] for pair in pairs])
    correlation = _pearson(left_ranks, right_ranks)
    return _round4(correlation) if correlation is not None else None


def _rank_values(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for original_index, _value in indexed[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
    denom_left = sqrt(sum((x - mean_left) ** 2 for x in left))
    denom_right = sqrt(sum((y - mean_right) ** 2 for y in right))
    denominator = denom_left * denom_right
    if denominator == 0:
        return None
    return numerator / denominator
