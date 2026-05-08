from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import math
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _mapping_rows,
    _repo_path,
    _safe_float,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402
from semantic_veto_translation_ambiguity_heuristic_common import (  # noqa: E402
    _brier,
    _first_dim,
    _lift,
    _mean,
    _normalize_slice_dimensions,
    _optional_float,
    _pairs,
    _rate,
    _round4,
    _sequence,
    _split,
    _spearman,
    _utc_now,
)


DEFAULT_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_SCORE_SURFACE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repaired_full_score_surface_en_es_latest.json"
)
DEFAULT_SRS_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_translation_ambiguity_heuristic_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_translation_ambiguity_heuristic_en_es_latest.md"
)
TOP_K = 8
SWEEP_FEATURE_IDS = (
    "source_exposure_risk",
    "wordnet_polysemy_risk",
    "translation_fanout_risk",
    "evidence_overlap_risk",
    "case_mix_risk",
    "inventory_source_risk",
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


@dataclass(frozen=True)
class InventorySourceProfile:
    source: str
    source_zipf_band_en: str
    source_zipf_frequency_en: float | None
    target_count: int
    target_band_count: int
    target_frequency_spread: float
    uniform_translation_entropy: float


def build_translation_ambiguity_heuristic_report(
    *,
    dataset_payload: Mapping[str, object],
    score_surface_payload: Mapping[str, object],
    srs_bridge_payload: Mapping[str, object],
    wordnet_index: WordNetIndex | None = None,
    dataset_path: Path | None = None,
    score_surface_path: Path | None = None,
    srs_bridge_path: Path | None = None,
    wordnet_dir: Path | None = None,
    top_k: int = TOP_K,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    inventory_profiles = _inventory_source_profiles(
        _mapping_rows(srs_bridge_payload.get("full_source_target_pairs"))
    )
    family_metadata = _family_metadata(
        dataset_payload=dataset_payload,
        inventory_profiles=inventory_profiles,
        wordnet_index=wordnet_index,
    )
    observations = _family_observations(
        rows=_mapping_rows(score_surface_payload.get("row_results")),
        family_metadata=family_metadata,
    )
    formula_rows = _formula_rows(observations)
    comparison_rows = _comparison_rows(
        formula_rows=formula_rows, observations=observations, top_k=top_k
    )
    best_by_scope = _best_by_scope(comparison_rows)
    top_need_rows = _top_need_rows(
        formula_rows=formula_rows, observations=observations, top_k=top_k
    )
    signal_summary = _signal_summary(comparison_rows)

    issues: list[str] = []
    if not inventory_profiles:
        issues.append("srs_bridge_has_no_full_source_target_pairs")
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
            "translation_ambiguity_heuristic_bakeoff_established"
            if status == "ok"
            else "translation_ambiguity_heuristic_bakeoff_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": str(dataset_payload.get("dataset_id") or ""),
            "dataset_manual_review_state": str(dataset_payload.get("manual_review_state") or ""),
            "score_surface_path": _repo_path(score_surface_path),
            "score_surface_decision": str(score_surface_payload.get("decision") or ""),
            "srs_bridge_path": _repo_path(srs_bridge_path),
            "srs_bridge_decision": str(srs_bridge_payload.get("decision") or ""),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(
                getattr(wordnet_index, "source_file_count", 0) if wordnet_index else 0
            ),
        },
        "methodology": {
            "purpose": (
                "Test whether inventory-available ambiguity, evidence-separability, "
                "and exposure features can rank source-target families by observed "
                "semantic-veto failure rate."
            ),
            "runtime_policy_change": "none",
            "unit_of_analysis": "source_target_family_x_scorer",
            "formula_features": list(SWEEP_FEATURE_IDS),
            "forbidden_formula_features": sorted(FORBIDDEN_FORMULA_FEATURES),
            "internal_split": (
                "stable family_id hash modulo 4; one bucket is locked-eval proxy and "
                "three buckets are discovery proxy. This is a leakage guard, not a "
                "future heldout set."
            ),
            "promotion_boundary": (
                "A strong result can nominate an LLM data-allocation hypothesis; it "
                "cannot prove product quality or change runtime scoring."
            ),
        },
        "summary": {
            "issues": issues,
            "inventory_source_count": len(inventory_profiles),
            "family_count": len(family_metadata),
            "observation_count": len(observations),
            "scorer_count": len({row["scorer_id"] for row in observations}),
            "fixed_formula_count": len(_fixed_formula_weights()),
            "sweep_formula_count": len(_sweep_formula_weights()),
            "comparison_row_count": len(comparison_rows),
            "top_k": int(top_k),
            "split_counts": dict(sorted(Counter(row["split"] for row in observations).items())),
            "signal_summary": signal_summary,
            "best_by_scope": best_by_scope,
        },
        "e2e_checks": {
            "dataset_is_user_approved": str(dataset_payload.get("manual_review_state") or "")
            == "approved_by_user",
            "inventory_profiles_available": bool(inventory_profiles),
            "score_surface_rows_available": bool(observations),
            "formula_features_do_not_use_gold_or_prediction_labels": set(
                SWEEP_FEATURE_IDS
            ).isdisjoint(FORBIDDEN_FORMULA_FEATURES),
            "internal_split_has_discovery_and_locked_proxy": (
                any(row.get("split") == "discovery_proxy" for row in observations)
                and any(row.get("split") == "locked_eval_proxy" for row in observations)
            ),
        },
        "formula_definitions": _formula_definitions(),
        "comparison_rows": comparison_rows,
        "top_need_rows": top_need_rows,
        "observations": observations,
        "limitations": [
            "only_49_user_approved_repaired_families_so_correlations_are_fragile",
            "translation_entropy_is_uniform_over_current_rule_targets_not_true_usage_entropy",
            "evidence_overlap_uses_static_evidence_text_not_runtime_contexts",
            "internal_locked_eval_proxy_is_not_a_future_heldout_set",
            "strong_allocator_claims_require_a_control_bearing_llm_or_context_pilot",
        ],
        "next_steps": [
            "Promote only formulas that show positive discovery and locked-proxy correlation.",
            "If no formula is strong, use top/middle/low controls in the next LLM data pilot.",
            "Replace uniform translation entropy with observed translation/context entropy when data exists.",
        ],
    }


def _inventory_source_profiles(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, InventorySourceProfile]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        source = str(row.get("source") or "").strip().lower()
        target = str(row.get("target") or "").strip().lower()
        if source and target:
            grouped[source].append(row)
    max_entropy = max(
        (
            math.log2(len({str(r.get("target") or "").lower() for r in group}))
            for group in grouped.values()
        ),
        default=1.0,
    )
    max_entropy = max(max_entropy, 1.0)
    profiles: dict[str, InventorySourceProfile] = {}
    for source, group in grouped.items():
        targets = {
            str(row.get("target") or "").strip().lower() for row in group if row.get("target")
        }
        source_zipfs = [_optional_float(row.get("source_zipf_frequency_en")) for row in group]
        source_zipfs = [value for value in source_zipfs if value is not None]
        target_zipfs = [_optional_float(row.get("target_zipf_frequency_es")) for row in group]
        target_zipfs = [value for value in target_zipfs if value is not None]
        target_bands = {
            str(row.get("target_zipf_band_es") or "missing") for row in group if row.get("target")
        }
        entropy = math.log2(len(targets)) if targets else 0.0
        profiles[source] = InventorySourceProfile(
            source=source,
            source_zipf_band_en=str(group[0].get("source_zipf_band_en") or "missing"),
            source_zipf_frequency_en=(sum(source_zipfs) / len(source_zipfs))
            if source_zipfs
            else None,
            target_count=len(targets),
            target_band_count=len(target_bands),
            target_frequency_spread=(max(target_zipfs) - min(target_zipfs))
            if len(target_zipfs) > 1
            else 0.0,
            uniform_translation_entropy=entropy / max_entropy,
        )
    return profiles


def _family_metadata(
    *,
    dataset_payload: Mapping[str, object],
    inventory_profiles: Mapping[str, InventorySourceProfile],
    wordnet_index: WordNetIndex | None,
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    max_target_frequency_spread = max(
        (profile.target_frequency_spread for profile in inventory_profiles.values()),
        default=1.0,
    )
    max_target_frequency_spread = max(max_target_frequency_spread, 1.0)
    for family in _mapping_rows(dataset_payload.get("families")):
        cases = _mapping_rows(family.get("cases"))
        dims = _normalize_slice_dimensions(cases[0].get("slice_dimensions") if cases else {})
        active = _as_mapping(family.get("active"))
        shadows = _mapping_rows(family.get("shadows"))
        trigger = str(family.get("trigger") or "").strip()
        source_key = trigger.lower()
        inventory = inventory_profiles.get(source_key)
        wordnet = _wordnet_profile(source_key, wordnet_index)
        active_evidence = _evidence_text(active)
        shadow_evidence = [_evidence_text(shadow) for shadow in shadows]
        target_count = inventory.target_count if inventory else 1
        target_frequency_spread = inventory.target_frequency_spread if inventory else 0.0
        result[str(family.get("family_id") or "")] = {
            "family_id": str(family.get("family_id") or ""),
            "trigger": trigger,
            "target_lemma": str(active.get("target_lemma") or ""),
            "source_zipf_band_en": (
                inventory.source_zipf_band_en
                if inventory
                else _first_dim(dims, "source_zipf_band_en") or "missing"
            ),
            "source_zipf_frequency_en": inventory.source_zipf_frequency_en if inventory else None,
            "target_zipf_band_es": _first_dim(dims, "target_zipf_band_es") or "missing",
            "polysemy_band": _first_dim(dims, "polysemy_band") or "missing",
            "pos_shape": _first_dim(dims, "pos_shape") or "missing",
            "translation_fanout": target_count,
            "translation_entropy": inventory.uniform_translation_entropy if inventory else 0.0,
            "target_band_count": inventory.target_band_count if inventory else 1,
            "target_frequency_spread": target_frequency_spread / max_target_frequency_spread,
            "wordnet_sense_count": int(wordnet.get("wordnet_sense_count") or 0),
            "wordnet_pos_count": int(wordnet.get("wordnet_pos_count") or 0),
            "shadow_count": len(shadows),
            "active_evidence_token_count": len(_tokens(active_evidence)),
            "mean_shadow_evidence_token_count": _mean(
                len(_tokens(text)) for text in shadow_evidence
            ),
            "max_active_shadow_token_jaccard": _max_jaccard(active_evidence, shadow_evidence),
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
                "positive_case_count": sum(row.get("gold_decision") == "replace" for row in group),
                "negative_case_count": sum(row.get("gold_decision") == "abstain" for row in group),
                "false_abstain_count": errors["false_abstain"],
                "harmful_replace_count": errors["harmful_replace"],
                "failure_count": failure_count,
                "observed_failure_rate": _rate(failure_count, len(group)),
                "features": _features(metadata),
                "feature_context": {
                    "source_zipf_band_en": str(metadata.get("source_zipf_band_en") or "missing"),
                    "source_zipf_frequency_en": metadata.get("source_zipf_frequency_en"),
                    "translation_fanout": int(metadata.get("translation_fanout") or 0),
                    "translation_entropy": _round4(
                        _safe_float(metadata.get("translation_entropy"))
                    ),
                    "target_band_count": int(metadata.get("target_band_count") or 0),
                    "target_frequency_spread": _round4(
                        _safe_float(metadata.get("target_frequency_spread"))
                    ),
                    "wordnet_sense_count": int(metadata.get("wordnet_sense_count") or 0),
                    "wordnet_pos_count": int(metadata.get("wordnet_pos_count") or 0),
                    "shadow_count": int(metadata.get("shadow_count") or 0),
                    "max_active_shadow_token_jaccard": _round4(
                        _safe_float(metadata.get("max_active_shadow_token_jaccard"))
                    ),
                },
            }
        )
    return observations


def _features(metadata: Mapping[str, object]) -> dict[str, float]:
    fanout = int(metadata.get("translation_fanout") or 1)
    sense_count = int(metadata.get("wordnet_sense_count") or 0)
    pos_count = int(metadata.get("wordnet_pos_count") or 0)
    active_tokens = _safe_float(metadata.get("active_evidence_token_count"))
    shadow_tokens = _safe_float(metadata.get("mean_shadow_evidence_token_count"))
    coverage = min(1.0, (active_tokens + shadow_tokens) / 32.0)
    source_zipf = metadata.get("source_zipf_frequency_en")
    return {
        "source_exposure_risk": _source_exposure_risk(
            source_zipf, str(metadata.get("source_zipf_band_en") or "missing")
        ),
        "translation_fanout_risk": min(1.0, math.log1p(max(0, fanout - 1)) / math.log1p(5)),
        "translation_entropy_risk": _safe_float(metadata.get("translation_entropy")),
        "target_diversity_risk": min(
            1.0,
            0.55 * min(1.0, max(0, int(metadata.get("target_band_count") or 1) - 1) / 3.0)
            + 0.45 * _safe_float(metadata.get("target_frequency_spread")),
        ),
        "wordnet_sense_risk": min(1.0, max(0, sense_count - 1) / 14.0) if sense_count else 0.35,
        "wordnet_pos_risk": min(1.0, max(0, pos_count - 1) / 3.0) if pos_count else 0.25,
        "evidence_overlap_risk": _safe_float(metadata.get("max_active_shadow_token_jaccard")),
        "evidence_gap_risk": 1.0 - coverage,
        "shadow_competition_risk": min(1.0, 0.20 + 0.25 * int(metadata.get("shadow_count") or 0)),
        "source_surface_risk": _source_surface_risk(
            source=str(metadata.get("trigger") or ""),
            source_band=str(metadata.get("source_zipf_band_en") or "missing"),
        ),
    }


def _formula_rows(observations: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    formulas = [*_fixed_formula_weights(), *_sweep_formula_weights()]
    rows = []
    for observation in observations:
        features = _as_mapping(observation.get("features"))
        for formula_id, family, weights in formulas:
            rows.append(
                {
                    "formula_id": formula_id,
                    "formula_family": family,
                    "scorer_id": observation.get("scorer_id"),
                    "family_id": observation.get("family_id"),
                    "trigger": observation.get("trigger"),
                    "target_lemma": observation.get("target_lemma"),
                    "split": observation.get("split"),
                    "predicted_need": _round4(_weighted_score(features, weights)),
                    "observed_failure_rate": observation.get("observed_failure_rate"),
                    "failure_count": observation.get("failure_count"),
                    "case_count": observation.get("case_count"),
                    "weights": weights,
                }
            )
    return rows


def _fixed_formula_weights() -> list[tuple[str, str, dict[str, float]]]:
    return [
        ("source_exposure_only", "fixed_single_signal", {"source_exposure_risk": 1.0}),
        ("translation_fanout_only", "fixed_single_signal", {"translation_fanout_risk": 1.0}),
        ("translation_entropy_only", "fixed_single_signal", {"translation_entropy_risk": 1.0}),
        ("target_diversity_only", "fixed_single_signal", {"target_diversity_risk": 1.0}),
        ("wordnet_sense_only", "fixed_single_signal", {"wordnet_sense_risk": 1.0}),
        ("wordnet_pos_only", "fixed_single_signal", {"wordnet_pos_risk": 1.0}),
        ("evidence_overlap_only", "fixed_single_signal", {"evidence_overlap_risk": 1.0}),
        ("evidence_gap_only", "fixed_single_signal", {"evidence_gap_risk": 1.0}),
        ("shadow_competition_only", "fixed_single_signal", {"shadow_competition_risk": 1.0}),
        ("source_surface_only", "fixed_single_signal", {"source_surface_risk": 1.0}),
        (
            "translation_ambiguity",
            "fixed_linear",
            {
                "translation_fanout_risk": 0.35,
                "translation_entropy_risk": 0.25,
                "target_diversity_risk": 0.15,
                "wordnet_sense_risk": 0.15,
                "wordnet_pos_risk": 0.10,
            },
        ),
        (
            "semantic_separability",
            "fixed_linear",
            {
                "evidence_overlap_risk": 0.45,
                "shadow_competition_risk": 0.25,
                "wordnet_pos_risk": 0.15,
                "evidence_gap_risk": 0.15,
            },
        ),
        (
            "expected_llm_value",
            "fixed_linear",
            {
                "source_exposure_risk": 0.30,
                "translation_fanout_risk": 0.20,
                "evidence_overlap_risk": 0.20,
                "wordnet_sense_risk": 0.15,
                "source_surface_risk": 0.15,
            },
        ),
        (
            "fixability_candidate",
            "fixed_linear",
            {
                "evidence_gap_risk": 0.30,
                "evidence_overlap_risk": 0.25,
                "shadow_competition_risk": 0.25,
                "translation_fanout_risk": 0.20,
            },
        ),
        ("max_preoutcome_signal", "fixed_max", {feature: 1.0 for feature in SWEEP_FEATURE_IDS}),
    ]


def _sweep_formula_weights() -> list[tuple[str, str, dict[str, float]]]:
    formulas: list[tuple[str, str, dict[str, float]]] = []
    index = 1
    for values in itertools.product((0, 1, 2, 3), repeat=len(SWEEP_FEATURE_IDS)):
        total = sum(values)
        if total <= 0:
            continue
        weights = {
            feature: value / total
            for feature, value in zip(SWEEP_FEATURE_IDS, values, strict=True)
            if value
        }
        formulas.append((f"sweep_linear_{index:05d}", "sweep_linear", weights))
        index += 1
    return formulas


def _weighted_score(features: Mapping[str, object], weights: Mapping[str, float]) -> float:
    if set(weights) == set(SWEEP_FEATURE_IDS) and all(value == 1.0 for value in weights.values()):
        return max(_safe_float(features.get(feature)) for feature in SWEEP_FEATURE_IDS)
    score = 0.0
    for feature, weight in weights.items():
        score += float(weight) * _safe_float(features.get(feature))
    return max(0.0, min(1.0, score))


def _comparison_rows(
    *,
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    observed_by_scorer = defaultdict(list)
    for observation in observations:
        observed_by_scorer[str(observation.get("scorer_id") or "")].append(
            _safe_float(observation.get("observed_failure_rate"))
        )
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in formula_rows:
        grouped[(str(row.get("formula_id") or ""), str(row.get("scorer_id") or ""))].append(row)
    rows = []
    for (formula_id, scorer_id), group in grouped.items():
        top_rows = sorted(
            group,
            key=lambda row: (
                -_safe_float(row.get("predicted_need")),
                str(row.get("family_id") or ""),
            ),
        )[:top_k]
        top_observed = [_safe_float(row.get("observed_failure_rate")) for row in top_rows]
        rows.append(
            {
                "formula_id": formula_id,
                "formula_family": str(group[0].get("formula_family") or ""),
                "scorer_id": scorer_id,
                "scope_id": f"{scorer_id}::{formula_id}",
                "family_count": len(group),
                "spearman_rank_correlation": _round4(_spearman(_pairs(group))),
                "discovery_spearman": _round4(
                    _spearman(_pairs(row for row in group if row.get("split") == "discovery_proxy"))
                ),
                "internal_locked_eval_spearman": _round4(
                    _spearman(
                        _pairs(row for row in group if row.get("split") == "locked_eval_proxy")
                    )
                ),
                "top_k_lift": _round4(_lift(top_observed, observed_by_scorer[scorer_id])),
                "brier_score": _round4(_brier(_pairs(group))),
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


def _signal_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    stable = [
        row
        for row in rows
        if _safe_float(row.get("discovery_spearman")) > 0
        and _safe_float(row.get("internal_locked_eval_spearman")) > 0
    ]
    best = sorted(stable, key=_comparison_sort_key)[0] if stable else {}
    locked = _safe_float(best.get("internal_locked_eval_spearman")) if best else 0.0
    lift = _safe_float(best.get("top_k_lift")) if best else 0.0
    return {
        "stable_positive_formula_count": len(stable),
        "best_stable_formula_id": str(best.get("formula_id") or "none"),
        "best_stable_formula_family": str(best.get("formula_family") or "none"),
        "best_stable_scorer_id": str(best.get("scorer_id") or "none"),
        "best_stable_discovery_spearman": best.get("discovery_spearman"),
        "best_stable_locked_spearman": best.get("internal_locked_eval_spearman"),
        "best_stable_top_k_lift": best.get("top_k_lift"),
        "strong_allocator_found": locked >= 0.25 and lift >= 1.20,
    }


def _top_need_rows(
    *,
    formula_rows: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    rows = []
    for scorer_id in sorted({str(row.get("scorer_id") or "") for row in observations}):
        scorer_formulas = [row for row in formula_rows if row.get("scorer_id") == scorer_id]
        comparison = _comparison_rows(
            formula_rows=scorer_formulas,
            observations=[row for row in observations if row.get("scorer_id") == scorer_id],
            top_k=top_k,
        )
        stable = [
            row
            for row in comparison
            if _safe_float(row.get("discovery_spearman")) > 0
            and _safe_float(row.get("internal_locked_eval_spearman")) > 0
        ]
        selected = (stable or comparison)[0]
        formula_id = str(selected.get("formula_id") or "")
        selected_rows = [row for row in scorer_formulas if row.get("formula_id") == formula_id]
        selected_rows = sorted(
            selected_rows,
            key=lambda row: (
                -_safe_float(row.get("predicted_need")),
                str(row.get("family_id") or ""),
            ),
        )[:top_k]
        for rank, row in enumerate(selected_rows, start=1):
            rows.append(
                {
                    "scorer_id": scorer_id,
                    "priority_rank": rank,
                    "trigger": row.get("trigger"),
                    "target_lemma": row.get("target_lemma"),
                    "predicted_need": row.get("predicted_need"),
                    "observed_failure_rate": row.get("observed_failure_rate"),
                    "failure_count": row.get("failure_count"),
                    "case_count": row.get("case_count"),
                    "formula_id": formula_id,
                    "formula_family": selected.get("formula_family"),
                }
            )
    return rows


def _formula_definitions() -> list[dict[str, str]]:
    return [
        {
            "formula_family": "fixed_single_signal",
            "description": "One signal at a time: exposure, translation fanout/entropy, WordNet ambiguity, evidence overlap/gap, shadow competition, or surface no-winner risk.",
        },
        {
            "formula_family": "fixed_linear",
            "description": "Hand-authored formulas for translation ambiguity, semantic separability, expected LLM value, and fixability.",
        },
        {
            "formula_family": "fixed_max",
            "description": "Risk is the largest inventory-available warning signal.",
        },
        {
            "formula_family": "sweep_linear",
            "description": "Discrete normalized weight sweep over exposure, fanout, WordNet, evidence-overlap, shadow, and surface-risk features.",
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


def _evidence_text(sense: Mapping[str, object]) -> str:
    views = _as_mapping(_as_mapping(sense).get("evidence_views"))
    return str(
        views.get("all_evidence_text")
        or views.get("sense_gloss_bundle")
        or views.get("gloss_text")
        or views.get("sense_label")
        or ""
    )


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if token not in {"the", "a", "an", "to", "or", "and", "of", "in"}
    }


def _max_jaccard(active_evidence: str, shadow_evidence: Sequence[str]) -> float:
    active_tokens = _tokens(active_evidence)
    if not active_tokens:
        return 0.0
    scores = []
    for text in shadow_evidence:
        shadow_tokens = _tokens(text)
        if not shadow_tokens:
            continue
        scores.append(len(active_tokens & shadow_tokens) / len(active_tokens | shadow_tokens))
    return max(scores, default=0.0)


def _source_exposure_risk(zipf: object, band: str) -> float:
    value = _optional_float(zipf)
    if value is not None:
        return max(0.0, min(1.0, (value - 2.0) / 4.0))
    return {
        "zipf_5_plus_very_common": 0.95,
        "zipf_4_to_5_common": 0.70,
        "zipf_3_to_4_mid": 0.45,
        "zipf_below_3_rare": 0.20,
        "missing": 0.45,
    }.get(band, 0.45)


def _source_surface_risk(*, source: str, source_band: str) -> float:
    token = str(source or "").strip()
    band_risk = {
        "zipf_5_plus_very_common": 1.0,
        "zipf_4_to_5_common": 0.65,
        "zipf_3_to_4_mid": 0.35,
        "zipf_below_3_rare": 0.15,
        "missing": 0.45,
    }.get(source_band, 0.45)
    short_risk = 0.7 if len(token) <= 3 else 0.4 if len(token) <= 5 else 0.1
    artifact_risk = 0.0
    if not re.fullmatch(r"[A-Za-z]+", token):
        artifact_risk = 0.8
    elif len(token) >= 14:
        artifact_risk = 0.35
    elif re.search(r"(site|work|man|woman|journalist|language)$", token.lower()):
        artifact_risk = 0.25
    return round(0.60 * band_risk + 0.25 * short_risk + 0.15 * artifact_risk, 4)


def _wordnet_profile(source: str, wordnet_index: WordNetIndex | None) -> dict[str, int]:
    if wordnet_index is None:
        return {}
    entry = wordnet_index.entries_by_word.get(str(source or "").strip().lower())
    if not isinstance(entry, Mapping):
        return {}
    sense_count = 0
    pos_count = 0
    for section in entry.values():
        if not isinstance(section, Mapping):
            continue
        senses = _sequence(section.get("sense"))
        count = sum(1 for item in senses if isinstance(item, Mapping))
        if count:
            sense_count += count
            pos_count += 1
    return {
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
    }
