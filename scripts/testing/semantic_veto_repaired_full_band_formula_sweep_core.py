from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _mapping_rows,
    _repo_path,
    _safe_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_SCORE_SURFACE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repaired_full_score_surface_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_repaired_full_band_formula_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_repaired_full_band_formula_sweep_en_es_latest.md"
)
FORBIDDEN_FORMULA_FEATURES = {
    "observed_failure_rate",
    "winner_accuracy",
    "product_outcome",
    "predicted_decision",
    "gold_decision",
    "failure_count",
    "case_count",
}
FEATURE_IDS = (
    "source_exposure_risk",
    "source_polysemy_risk",
    "source_pos_risk",
    "translation_competitor_risk",
    "case_mix_risk",
)
TOP_K = 8


def build_repaired_full_band_formula_sweep_report(
    *,
    dataset_payload: Mapping[str, object],
    score_surface_payload: Mapping[str, object],
    dataset_path: Path | None = None,
    score_surface_path: Path | None = None,
    top_k: int = TOP_K,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    family_metadata = _family_metadata(dataset_payload)
    observations = _family_observations(
        rows=_mapping_rows(score_surface_payload.get("row_results")),
        family_metadata=family_metadata,
    )
    formula_rows = _formula_rows(observations)
    fixed_formula_rows = [
        row for row in formula_rows if str(row.get("formula_family") or "") != "sweep_linear"
    ]
    sweep_formula_rows = [
        row for row in formula_rows if str(row.get("formula_family") or "") == "sweep_linear"
    ]
    comparison_rows = _comparison_rows(
        formula_rows=formula_rows, observations=observations, top_k=top_k
    )
    best_by_scope = _best_by_scope(comparison_rows)
    selected_sweep_rows = _selected_sweep_rows(
        comparison_rows=comparison_rows,
        formula_rows=sweep_formula_rows,
        observations=observations,
        top_k=top_k,
    )
    top_need_rows = _top_need_rows(
        formula_rows=[*fixed_formula_rows, *selected_sweep_rows],
        observations=observations,
        top_k=top_k,
    )
    issues: list[str] = []
    if not family_metadata:
        issues.append("dataset_has_no_families")
    if not observations:
        issues.append("score_surface_has_no_family_observations")
    if str(dataset_payload.get("manual_review_state") or "") != "approved_by_user":
        issues.append("dataset_not_marked_approved_by_user")
    if not any(row.get("split") == "discovery_proxy" for row in observations):
        issues.append("no_discovery_proxy_observations")
    if not any(row.get("split") == "locked_eval_proxy" for row in observations):
        issues.append("no_locked_eval_proxy_observations")

    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or score_surface_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "repaired_full_band_formula_sweep_established"
            if status == "ok"
            else "repaired_full_band_formula_sweep_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": str(dataset_payload.get("dataset_id") or ""),
            "dataset_manual_review_state": str(dataset_payload.get("manual_review_state") or ""),
            "score_surface_path": _repo_path(score_surface_path),
            "score_surface_decision": str(score_surface_payload.get("decision") or ""),
        },
        "methodology": {
            "purpose": (
                "Compare programmatic family-level heuristics for ranking the source-target "
                "families most likely to benefit from LLM-generated semantic evidence."
            ),
            "unit_of_analysis": "source_target_family",
            "runtime_policy_change": "none",
            "formula_features": list(FEATURE_IDS),
            "forbidden_formula_features": sorted(FORBIDDEN_FORMULA_FEATURES),
            "internal_split": (
                "stable family_id hash modulo 4; one bucket is locked-eval proxy and "
                "three buckets are discovery proxy. This guards against selecting a "
                "formula entirely on the same families it is judged on, but it is not a "
                "real future heldout set."
            ),
            "promotion_boundary": (
                "This can choose the next LLM data-allocation hypothesis; it cannot "
                "prove product quality or promote runtime scoring."
            ),
        },
        "summary": {
            "issues": issues,
            "family_count": len(family_metadata),
            "observation_count": len(observations),
            "scorer_count": len({row["scorer_id"] for row in observations}),
            "fixed_formula_count": len({row["formula_id"] for row in fixed_formula_rows}),
            "sweep_formula_count": len({row["formula_id"] for row in sweep_formula_rows}),
            "comparison_row_count": len(comparison_rows),
            "top_k": int(top_k),
            "split_counts": dict(sorted(Counter(row["split"] for row in observations).items())),
            "best_by_scope": best_by_scope,
        },
        "e2e_checks": {
            "dataset_is_user_approved": str(dataset_payload.get("manual_review_state") or "")
            == "approved_by_user",
            "score_surface_rows_available": bool(observations),
            "family_metadata_available_for_all_observations": all(
                bool(row.get("target_lemma")) for row in observations
            ),
            "formula_features_do_not_use_gold_or_prediction_labels": set(FEATURE_IDS).isdisjoint(
                FORBIDDEN_FORMULA_FEATURES
            ),
            "internal_split_has_discovery_and_locked_proxy": (
                any(row.get("split") == "discovery_proxy" for row in observations)
                and any(row.get("split") == "locked_eval_proxy" for row in observations)
            ),
            "sweep_selected_rows_available": bool(selected_sweep_rows),
        },
        "formula_definitions": _formula_definitions(),
        "comparison_rows": comparison_rows,
        "selected_sweep_formula_rows": selected_sweep_rows,
        "top_need_rows": top_need_rows,
        "observations": observations,
        "limitations": [
            "only_49_user_approved_repaired_families_so_correlation_is_still_fragile",
            "zipf_values_are_bands_not_exact_frequency_ranks_in_this_lane",
            "internal_locked_eval_proxy_is_not_a_future_heldout_set",
            "shadow_coverage_is_available_for_this_dataset_but_needs_full_inventory_equivalent",
            "ranking_quality_must_be_rechecked_after_llm_evidence_generation",
        ],
        "next_steps": [
            "Use the best stable formula family to choose a small top-N LLM evidence pilot.",
            "Include low-ranked controls in that pilot so the ranking can be falsified.",
            "Do not tune runtime thresholds from this report alone.",
        ],
    }


def _family_metadata(dataset: Mapping[str, object]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for family in _mapping_rows(dataset.get("families")):
        cases = _mapping_rows(family.get("cases"))
        dims = _normalize_slice_dimensions(cases[0].get("slice_dimensions") if cases else {})
        active = _as_mapping(family.get("active"))
        result[str(family.get("family_id") or "")] = {
            "family_id": str(family.get("family_id") or ""),
            "trigger": str(family.get("trigger") or ""),
            "target_lemma": str(active.get("target_lemma") or ""),
            "source_zipf_band_en": _first_dim(dims, "source_zipf_band_en") or "missing",
            "target_zipf_band_es": _first_dim(dims, "target_zipf_band_es") or "missing",
            "polysemy_band": _first_dim(dims, "polysemy_band") or "missing",
            "pos_shape": _first_dim(dims, "pos_shape") or "missing",
            "shadow_count": len(_mapping_rows(family.get("shadows"))),
            "case_count": len(cases),
        }
    return result


def _family_observations(
    *,
    rows: Sequence[Mapping[str, object]],
    family_metadata: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("scorer_id") or ""), str(row.get("family_id") or ""))].append(row)
    observations = []
    for (scorer_id, family_id), group in sorted(grouped.items()):
        metadata = _as_mapping(family_metadata.get(family_id))
        features = _features(metadata)
        errors = Counter(str(row.get("error_type") or "") for row in group)
        failure_count = errors["false_abstain"] + errors["harmful_replace"]
        observations.append(
            {
                "observation_id": f"{scorer_id}::{family_id}",
                "scorer_id": scorer_id,
                "family_id": family_id,
                "trigger": str(metadata.get("trigger") or group[0].get("trigger") or ""),
                "target_lemma": str(metadata.get("target_lemma") or ""),
                "split": _split(family_id),
                "case_count": len(group),
                "positive_case_count": sum(
                    1 for row in group if row.get("gold_decision") == "replace"
                ),
                "negative_case_count": sum(
                    1 for row in group if row.get("gold_decision") == "abstain"
                ),
                "false_abstain_count": errors["false_abstain"],
                "harmful_replace_count": errors["harmful_replace"],
                "failure_count": failure_count,
                "observed_failure_rate": _rate(failure_count, len(group)),
                "features": features,
                "feature_context": {
                    "source_zipf_band_en": str(metadata.get("source_zipf_band_en") or "missing"),
                    "target_zipf_band_es": str(metadata.get("target_zipf_band_es") or "missing"),
                    "polysemy_band": str(metadata.get("polysemy_band") or "missing"),
                    "pos_shape": str(metadata.get("pos_shape") or "missing"),
                    "shadow_count": int(metadata.get("shadow_count") or 0),
                },
            }
        )
    return observations


def _formula_rows(observations: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    formulas = _fixed_formula_weights()
    formulas.extend(_sweep_formula_weights())
    for observation in observations:
        features = _as_mapping(observation.get("features"))
        for formula_id, family, weights in formulas:
            predicted = _weighted_score(features, weights)
            rows.append(
                {
                    "formula_id": formula_id,
                    "formula_family": family,
                    "scorer_id": observation.get("scorer_id"),
                    "family_id": observation.get("family_id"),
                    "trigger": observation.get("trigger"),
                    "target_lemma": observation.get("target_lemma"),
                    "split": observation.get("split"),
                    "predicted_need": round(predicted, 4),
                    "observed_failure_rate": observation.get("observed_failure_rate"),
                    "failure_count": observation.get("failure_count"),
                    "case_count": observation.get("case_count"),
                    "weights": weights,
                }
            )
    return rows


def _fixed_formula_weights() -> list[tuple[str, str, dict[str, float]]]:
    return [
        ("source_zipf_only", "fixed_single_signal", {"source_zipf_risk": 1.0}),
        ("target_zipf_only", "fixed_single_signal", {"target_zipf_risk": 1.0}),
        ("polysemy_only", "fixed_single_signal", {"polysemy_risk": 1.0}),
        ("pos_shape_only", "fixed_single_signal", {"pos_shape_risk": 1.0}),
        ("shadow_coverage_only", "fixed_single_signal", {"shadow_coverage_risk": 1.0}),
        (
            "linear_equal",
            "fixed_linear",
            {feature: 1.0 / len(FEATURE_IDS) for feature in FEATURE_IDS},
        ),
        (
            "linear_source_polysemy",
            "fixed_linear",
            {
                "source_zipf_risk": 0.40,
                "polysemy_risk": 0.35,
                "pos_shape_risk": 0.15,
                "target_zipf_risk": 0.05,
                "shadow_coverage_risk": 0.05,
            },
        ),
        (
            "linear_polysemy_shadow",
            "fixed_linear",
            {
                "polysemy_risk": 0.35,
                "shadow_coverage_risk": 0.30,
                "pos_shape_risk": 0.20,
                "source_zipf_risk": 0.10,
                "target_zipf_risk": 0.05,
            },
        ),
        (
            "max_signal",
            "fixed_max",
            {feature: 1.0 for feature in FEATURE_IDS},
        ),
        (
            "source_polysemy_interaction",
            "fixed_interaction",
            {
                "source_zipf_risk": 0.25,
                "polysemy_risk": 0.25,
                "pos_shape_risk": 0.10,
                "target_zipf_risk": 0.10,
                "shadow_coverage_risk": 0.10,
                "source_polysemy_product": 0.20,
            },
        ),
    ]


def _sweep_formula_weights() -> list[tuple[str, str, dict[str, float]]]:
    raw_values = (0, 1, 2, 3, 4)
    formulas: list[tuple[str, str, dict[str, float]]] = []
    index = 1
    for source in raw_values:
        for target in raw_values:
            for polysemy in raw_values:
                for pos in raw_values:
                    for shadow in raw_values:
                        total = source + target + polysemy + pos + shadow
                        if total <= 0:
                            continue
                        weights = {
                            "source_zipf_risk": source / total,
                            "target_zipf_risk": target / total,
                            "polysemy_risk": polysemy / total,
                            "pos_shape_risk": pos / total,
                            "shadow_coverage_risk": shadow / total,
                        }
                        formulas.append((f"sweep_linear_{index:04d}", "sweep_linear", weights))
                        index += 1
    return formulas


def _weighted_score(features: Mapping[str, object], weights: Mapping[str, float]) -> float:
    if set(weights) == set(FEATURE_IDS) and all(value == 1.0 for value in weights.values()):
        return max(_safe_float(features.get(feature)) for feature in FEATURE_IDS)
    score = 0.0
    for feature, weight in weights.items():
        if feature == "source_polysemy_product":
            score += (
                float(weight)
                * _safe_float(features.get("source_zipf_risk"))
                * _safe_float(features.get("polysemy_risk"))
            )
        else:
            score += float(weight) * _safe_float(features.get(feature))
    return max(0.0, min(1.0, score))


def _comparison_rows(
    *,
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    observed_by_id = {(row["scorer_id"], row["family_id"]): row for row in observations}
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in formula_rows:
        grouped[(str(row.get("formula_id") or ""), str(row.get("scorer_id") or ""))].append(row)
    rows = []
    for (formula_id, scorer_id), group in grouped.items():
        all_pairs = _pairs(group)
        discovery_pairs = _pairs(row for row in group if row.get("split") == "discovery_proxy")
        locked_pairs = _pairs(row for row in group if row.get("split") == "locked_eval_proxy")
        top_rows = sorted(
            group,
            key=lambda row: (
                -_safe_float(row.get("predicted_need")),
                str(row.get("family_id") or ""),
            ),
        )[:top_k]
        all_observed = [
            _safe_float(observed.get("observed_failure_rate"))
            for observed in observed_by_id.values()
            if observed.get("scorer_id") == scorer_id
        ]
        top_observed = [_safe_float(row.get("observed_failure_rate")) for row in top_rows]
        rows.append(
            {
                "formula_id": formula_id,
                "formula_family": str(group[0].get("formula_family") or ""),
                "scorer_id": scorer_id,
                "scope_id": f"{scorer_id}::{formula_id}",
                "family_count": len(group),
                "spearman_rank_correlation": _round4(_spearman(all_pairs)),
                "discovery_spearman": _round4(_spearman(discovery_pairs)),
                "internal_locked_eval_spearman": _round4(_spearman(locked_pairs)),
                "brier_score": _round4(_brier(all_pairs)),
                "top_k_lift": _round4(_lift(top_observed, all_observed)),
                "top_k_triggers": [
                    f"{row.get('trigger')}->{row.get('target_lemma')}" for row in top_rows
                ],
                "weights": group[0].get("weights"),
            }
        )
    rows.sort(key=_comparison_sort_key)
    return rows


def _best_by_scope(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    best = {}
    for scorer_id in sorted({str(row.get("scorer_id") or "") for row in rows}):
        candidates = [row for row in rows if row.get("scorer_id") == scorer_id]
        if candidates:
            best[f"all_formulas::{scorer_id}"] = sorted(candidates, key=_comparison_sort_key)[0]
        fixed = [
            row for row in candidates if str(row.get("formula_family") or "") != "sweep_linear"
        ]
        if fixed:
            best[f"fixed_formulas::{scorer_id}"] = sorted(fixed, key=_comparison_sort_key)[0]
    return [_public_comparison(scope, row) for scope, row in best.items()]


def _selected_sweep_rows(
    *,
    comparison_rows: Sequence[Mapping[str, object]],
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    selected = []
    for scorer_id in sorted({str(row.get("scorer_id") or "") for row in observations}):
        candidates = [
            row
            for row in comparison_rows
            if row.get("scorer_id") == scorer_id
            and str(row.get("formula_family") or "") == "sweep_linear"
        ]
        if not candidates:
            continue
        best = sorted(candidates, key=_comparison_sort_key)[0]
        best_formula = str(best.get("formula_id") or "")
        for row in formula_rows:
            if row.get("scorer_id") == scorer_id and row.get("formula_id") == best_formula:
                copied = dict(row)
                copied["formula_id"] = f"{best_formula}_selected"
                copied["formula_family"] = "selected_sweep_linear"
                selected.append(copied)
    return selected


def _top_need_rows(
    *,
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    scorer_ids = sorted({str(row.get("scorer_id") or "") for row in observations})
    rows = []
    for scorer_id in scorer_ids:
        scorer_rows = [row for row in formula_rows if row.get("scorer_id") == scorer_id]
        selected_formula_ids = {
            str(row.get("formula_id") or "")
            for row in scorer_rows
            if "selected" in str(row.get("formula_id") or "")
        }
        if selected_formula_ids:
            scorer_rows = [
                row
                for row in scorer_rows
                if str(row.get("formula_id") or "") in selected_formula_ids
            ]
        grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in scorer_rows:
            grouped[str(row.get("family_id") or "")].append(row)
        averaged = []
        for family_rows in grouped.values():
            averaged.append(
                {
                    "scorer_id": scorer_id,
                    "family_id": family_rows[0].get("family_id"),
                    "trigger": family_rows[0].get("trigger"),
                    "target_lemma": family_rows[0].get("target_lemma"),
                    "predicted_need": _round4(
                        sum(_safe_float(row.get("predicted_need")) for row in family_rows)
                        / len(family_rows)
                    ),
                    "observed_failure_rate": family_rows[0].get("observed_failure_rate"),
                    "failure_count": family_rows[0].get("failure_count"),
                    "case_count": family_rows[0].get("case_count"),
                    "formula_ids": sorted(
                        {str(row.get("formula_id") or "") for row in family_rows}
                    ),
                }
            )
        averaged.sort(
            key=lambda row: (
                -_safe_float(row.get("predicted_need")),
                str(row.get("family_id") or ""),
            )
        )
        for rank, row in enumerate(averaged[:top_k], start=1):
            row["priority_rank"] = rank
            rows.append(row)
    return rows


def _features(metadata: Mapping[str, object]) -> dict[str, float]:
    source = str(metadata.get("source_zipf_band_en") or "missing")
    target = str(metadata.get("target_zipf_band_es") or "missing")
    polysemy = str(metadata.get("polysemy_band") or "missing")
    pos_shape = str(metadata.get("pos_shape") or "missing")
    shadow_count = int(metadata.get("shadow_count") or 0)
    return {
        "source_zipf_risk": {
            "zipf_5_plus_very_common": 1.0,
            "zipf_4_to_5_common": 0.75,
            "zipf_3_to_4_mid": 0.45,
            "zipf_below_3_rare": 0.2,
            "missing": 0.5,
        }.get(source, 0.5),
        "target_zipf_risk": {
            "zipf_5_plus_very_common": 0.2,
            "zipf_4_to_5_common": 0.35,
            "zipf_3_to_4_mid": 0.65,
            "zipf_below_3_rare": 0.85,
            "missing": 0.5,
        }.get(target, 0.5),
        "polysemy_risk": {
            "high_10_plus": 1.0,
            "medium_4_to_9": 0.6,
            "low_1_to_3": 0.2,
            "missing": 0.5,
        }.get(polysemy, 0.5),
        "pos_shape_risk": {
            "cross_pos_polysemy": 0.9,
            "same_pos_polysemy": 0.55,
            "single_sense": 0.2,
            "missing": 0.5,
        }.get(pos_shape, 0.5),
        "shadow_coverage_risk": 0.3 if shadow_count == 0 else min(1.0, 0.45 + 0.20 * shadow_count),
    }


def _formula_definitions() -> list[dict[str, object]]:
    return [
        {
            "formula_family": "fixed_single_signal",
            "description": "One feature at a time: source band, target band, polysemy, POS shape, or shadow coverage.",
        },
        {
            "formula_family": "fixed_linear",
            "description": "Hand-authored additive formulas to compare intuitive compositions.",
        },
        {
            "formula_family": "fixed_max",
            "description": "Risk is the largest single warning signal.",
        },
        {
            "formula_family": "fixed_interaction",
            "description": "Additive formula with a source-frequency by polysemy product term.",
        },
        {
            "formula_family": "sweep_linear",
            "description": "Discrete normalized weight sweep across the five family-level signals.",
        },
    ]


def _comparison_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, str]:
    return (
        -_safe_float(row.get("discovery_spearman")),
        -_safe_float(row.get("internal_locked_eval_spearman")),
        -_safe_float(row.get("top_k_lift")),
        str(row.get("formula_id") or ""),
    )


def _public_comparison(scope_id: str, row: Mapping[str, object]) -> dict[str, object]:
    return {
        "scope_id": scope_id,
        "formula_id": row.get("formula_id"),
        "formula_family": row.get("formula_family"),
        "scorer_id": row.get("scorer_id"),
        "family_count": row.get("family_count"),
        "spearman_rank_correlation": row.get("spearman_rank_correlation"),
        "discovery_spearman": row.get("discovery_spearman"),
        "internal_locked_eval_spearman": row.get("internal_locked_eval_spearman"),
        "top_k_lift": row.get("top_k_lift"),
        "brier_score": row.get("brier_score"),
        "top_k_triggers": row.get("top_k_triggers"),
        "weights": row.get("weights"),
    }


def _pairs(rows: Sequence[Mapping[str, object]] | object) -> list[tuple[float, float]]:
    return [
        (_safe_float(row.get("predicted_need")), _safe_float(row.get("observed_failure_rate")))
        for row in rows
        if isinstance(row, Mapping)
    ]


def _spearman(pairs: Sequence[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    left = _ranks([pair[0] for pair in pairs])
    right = _ranks([pair[1] for pair in pairs])
    return _pearson(left, right)


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and order[end][1] == order[index][1]:
            end += 1
        rank = (index + end + 1) / 2.0
        for original, _value in order[index:end]:
            ranks[original] = rank
        index = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right, strict=True))
    denom_left = sum((a - mean_left) ** 2 for a in left)
    denom_right = sum((b - mean_right) ** 2 for b in right)
    if denom_left <= 0 or denom_right <= 0:
        return None
    return numerator / (denom_left * denom_right) ** 0.5


def _brier(pairs: Sequence[tuple[float, float]]) -> float | None:
    if not pairs:
        return None
    return sum((predicted - observed) ** 2 for predicted, observed in pairs) / len(pairs)


def _lift(top_values: Sequence[float], all_values: Sequence[float]) -> float | None:
    if not top_values or not all_values:
        return None
    baseline = sum(all_values) / len(all_values)
    if baseline <= 0:
        return None
    return (sum(top_values) / len(top_values)) / baseline


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for key, raw in _as_mapping(value).items():
        output[str(key)] = [str(item) for item in _sequence(raw) if str(item)]
    return output


def _first_dim(dimensions: Mapping[str, Sequence[str]], key: str) -> str:
    values = dimensions.get(key) or []
    return str(values[0]) if values else ""


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return [value]


def _split(family_id: str) -> str:
    digest = hashlib.sha256(family_id.encode("utf-8")).hexdigest()
    return "locked_eval_proxy" if int(digest[:8], 16) % 4 == 0 else "discovery_proxy"


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
