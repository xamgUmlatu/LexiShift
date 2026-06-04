from __future__ import annotations

from typing import Mapping, MutableMapping, Sequence, cast

from lexishift_core.rulegen.semantic_shadow_evaluation_helpers import (
    _accumulate_policy_row,
    _accumulate_veto_policy_row,
    _as_sequence,
    _build_inventory_lookup,
    _empty_policy_report,
    _empty_veto_policy_report,
    _finalize_candidate_pool_summary,
    _finalize_policy_report,
    _finalize_veto_policy_report,
    _resolve_promoted_targets_for_policy,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (
    DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    DEFAULT_FREQUENCY_REPRESENTATIVE_TOP_K,
    DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
    DEFAULT_SUPPORT_SCORE_MIN,
    BenchmarkShadowTarget,
    SHADOW_PROMOTION_POLICIES,
)
from lexishift_core.rulegen.semantic_shadow_support import (
    DEFAULT_FREQUENCY_SIMILARITY_TAU,
    DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
)

REFERENCE_SHADOW_POLICY_MODES = ("none", "gold_overlap_oracle")

__all__ = (
    "REFERENCE_SHADOW_POLICY_MODES",
    "_resolve_promoted_targets_for_policy",
    "build_benchmark_trigger_overlap_gold",
    "evaluate_shadow_inventory_against_benchmark_overlap_gold",
    "evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold",
)


def build_benchmark_trigger_overlap_gold(
    benchmark_targets: Sequence[BenchmarkShadowTarget],
) -> dict[tuple[str, str], tuple[str, ...]]:
    trigger_to_targets: dict[str, list[str]] = {}
    for benchmark_target in benchmark_targets:
        target = str(benchmark_target.target or "").strip()
        if not target:
            continue
        for trigger in benchmark_target.reviewed_triggers:
            normalized_trigger = str(trigger or "").strip()
            if not normalized_trigger:
                continue
            bucket = trigger_to_targets.setdefault(normalized_trigger, [])
            if target not in bucket:
                bucket.append(target)

    gold_rows: dict[tuple[str, str], tuple[str, ...]] = {}
    for benchmark_target in benchmark_targets:
        target = str(benchmark_target.target or "").strip()
        if not target:
            continue
        for trigger in benchmark_target.reviewed_triggers:
            normalized_trigger = str(trigger or "").strip()
            if not normalized_trigger:
                continue
            gold_rows[(target, normalized_trigger)] = tuple(
                sorted(
                    candidate_target
                    for candidate_target in trigger_to_targets.get(normalized_trigger, ())
                    if candidate_target != target
                )
            )
    return gold_rows


def evaluate_shadow_inventory_against_benchmark_overlap_gold(
    *,
    inventory: Mapping[str, object],
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    policies: Sequence[str] = SHADOW_PROMOTION_POLICIES + REFERENCE_SHADOW_POLICY_MODES,
    support_score_min: float = DEFAULT_SUPPORT_SCORE_MIN,
    support_score_max_promoted: int = DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
    support_frequency_representative_bonus: float = DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    support_frequency_representative_top_k: int = DEFAULT_FREQUENCY_REPRESENTATIVE_TOP_K,
    support_frequency_similarity_weight: float = DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
    support_frequency_similarity_tau: float = DEFAULT_FREQUENCY_SIMILARITY_TAU,
    support_representative_pruning_mode: str = DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    support_score_weights: Mapping[str, object] | None = None,
) -> dict[str, object]:
    gold_rows = build_benchmark_trigger_overlap_gold(benchmark_targets)
    inventory_lookup = _build_inventory_lookup(inventory)
    requested_policies = tuple(
        policy
        for policy in policies
        if policy in SHADOW_PROMOTION_POLICIES or policy in REFERENCE_SHADOW_POLICY_MODES
    )
    candidate_pool_summary = {
        "trigger_rows_total": 0,
        "trigger_rows_with_inventory_entry": 0,
        "gold_trigger_rows": 0,
        "gold_trigger_rows_with_inventory_entry": 0,
        "gold_trigger_rows_with_active_candidates": 0,
        "gold_trigger_rows_with_mined_overlap": 0,
        "gold_trigger_rows_with_exact_mined_set": 0,
    }
    policy_reports: dict[str, dict[str, object]] = {}
    for policy in requested_policies:
        policy_reports[policy] = _empty_policy_report()

    if not isinstance(inventory.get("targets"), Sequence) or isinstance(
        inventory.get("targets"), (str, bytes)
    ):
        return {
            "schema_version": 1,
            "status": "inventory_unavailable",
            "candidate_pool_summary": candidate_pool_summary,
            "policies": policy_reports,
        }

    for benchmark_target in benchmark_targets:
        target = str(benchmark_target.target or "").strip()
        if not target:
            continue
        for trigger in benchmark_target.reviewed_triggers:
            if not trigger:
                continue
            trigger_entry = inventory_lookup.get((target, trigger), {})
            active_candidates = _as_sequence(trigger_entry.get("active_candidates"))
            active_profile_fallback = trigger_entry.get("active_profile_fallback")
            active_profile_fallback_mapping = (
                active_profile_fallback if isinstance(active_profile_fallback, Mapping) else None
            )
            shadow_candidates = _as_sequence(trigger_entry.get("shadow_candidates"))
            gold_shadow_targets = set(gold_rows.get((target, trigger), ()))
            mined_shadow_targets = {
                str(candidate.get("target") or "").strip()
                for candidate in shadow_candidates
                if isinstance(candidate, Mapping) and str(candidate.get("target") or "").strip()
            }

            candidate_pool_summary["trigger_rows_total"] += 1
            if trigger_entry:
                candidate_pool_summary["trigger_rows_with_inventory_entry"] += 1
            if gold_shadow_targets:
                candidate_pool_summary["gold_trigger_rows"] += 1
                if trigger_entry:
                    candidate_pool_summary["gold_trigger_rows_with_inventory_entry"] += 1
                if active_candidates:
                    candidate_pool_summary["gold_trigger_rows_with_active_candidates"] += 1
                if mined_shadow_targets & gold_shadow_targets:
                    candidate_pool_summary["gold_trigger_rows_with_mined_overlap"] += 1
                if mined_shadow_targets == gold_shadow_targets:
                    candidate_pool_summary["gold_trigger_rows_with_exact_mined_set"] += 1

            for policy in requested_policies:
                promoted_targets = _resolve_promoted_targets_for_policy(
                    policy=policy,
                    gold_shadow_targets=gold_shadow_targets,
                    shadow_candidates=shadow_candidates,
                    active_candidates=active_candidates,
                    active_profile_fallback=active_profile_fallback_mapping,
                    support_score_min=support_score_min,
                    support_score_max_promoted=support_score_max_promoted,
                    support_frequency_representative_bonus=support_frequency_representative_bonus,
                    support_frequency_representative_top_k=support_frequency_representative_top_k,
                    support_frequency_similarity_weight=support_frequency_similarity_weight,
                    support_frequency_similarity_tau=support_frequency_similarity_tau,
                    support_representative_pruning_mode=support_representative_pruning_mode,
                    support_score_weights=support_score_weights,
                )
                _accumulate_policy_row(
                    report=policy_reports[policy],
                    target=target,
                    trigger=trigger,
                    active_candidate_count=len(active_candidates),
                    gold_shadow_targets=gold_shadow_targets,
                    mined_shadow_targets=mined_shadow_targets,
                    promoted_targets=promoted_targets,
                )

    for policy_report in policy_reports.values():
        if isinstance(policy_report, Mapping):
            _finalize_policy_report(policy_report)

    _finalize_candidate_pool_summary(cast(MutableMapping[str, object], candidate_pool_summary))
    return {
        "schema_version": 1,
        "status": "ok",
        "candidate_pool_summary": candidate_pool_summary,
        "policies": policy_reports,
    }


def evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
    *,
    inventory: Mapping[str, object],
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    row_metadata_by_key: Mapping[tuple[str, str], Mapping[str, object]] | None = None,
    policies: Sequence[str] = SHADOW_PROMOTION_POLICIES + REFERENCE_SHADOW_POLICY_MODES,
    support_score_min: float = DEFAULT_SUPPORT_SCORE_MIN,
    support_score_max_promoted: int = DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
    support_frequency_representative_bonus: float = DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    support_frequency_representative_top_k: int = DEFAULT_FREQUENCY_REPRESENTATIVE_TOP_K,
    support_frequency_similarity_weight: float = DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
    support_frequency_similarity_tau: float = DEFAULT_FREQUENCY_SIMILARITY_TAU,
    support_representative_pruning_mode: str = DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    support_score_weights: Mapping[str, object] | None = None,
    include_row_results: bool = False,
) -> dict[str, object]:
    gold_rows = build_benchmark_trigger_overlap_gold(benchmark_targets)
    inventory_lookup = _build_inventory_lookup(inventory)
    requested_policies = tuple(
        policy
        for policy in policies
        if policy in SHADOW_PROMOTION_POLICIES or policy in REFERENCE_SHADOW_POLICY_MODES
    )
    candidate_pool_summary = {
        "trigger_rows_total": 0,
        "trigger_rows_with_inventory_entry": 0,
        "gold_trigger_rows": 0,
        "gold_trigger_rows_with_inventory_entry": 0,
        "gold_trigger_rows_with_active_candidates": 0,
        "gold_trigger_rows_with_mined_overlap": 0,
        "gold_trigger_rows_with_exact_mined_set": 0,
    }
    policy_reports: dict[str, dict[str, object]] = {}
    for policy in requested_policies:
        policy_reports[policy] = _empty_veto_policy_report(include_row_results=include_row_results)

    if not isinstance(inventory.get("targets"), Sequence) or isinstance(
        inventory.get("targets"), (str, bytes)
    ):
        return {
            "schema_version": 1,
            "status": "inventory_unavailable",
            "candidate_pool_summary": candidate_pool_summary,
            "policies": policy_reports,
        }

    for benchmark_target in benchmark_targets:
        target = str(benchmark_target.target or "").strip()
        if not target:
            continue
        for trigger in benchmark_target.reviewed_triggers:
            if not trigger:
                continue
            trigger_entry = inventory_lookup.get((target, trigger), {})
            active_candidates = _as_sequence(trigger_entry.get("active_candidates"))
            active_profile_fallback = trigger_entry.get("active_profile_fallback")
            active_profile_fallback_mapping = (
                active_profile_fallback if isinstance(active_profile_fallback, Mapping) else None
            )
            shadow_candidates = _as_sequence(trigger_entry.get("shadow_candidates"))
            gold_shadow_targets = set(gold_rows.get((target, trigger), ()))
            mined_shadow_targets = {
                str(candidate.get("target") or "").strip()
                for candidate in shadow_candidates
                if isinstance(candidate, Mapping) and str(candidate.get("target") or "").strip()
            }

            candidate_pool_summary["trigger_rows_total"] += 1
            if trigger_entry:
                candidate_pool_summary["trigger_rows_with_inventory_entry"] += 1
            if gold_shadow_targets:
                candidate_pool_summary["gold_trigger_rows"] += 1
                if trigger_entry:
                    candidate_pool_summary["gold_trigger_rows_with_inventory_entry"] += 1
                if active_candidates:
                    candidate_pool_summary["gold_trigger_rows_with_active_candidates"] += 1
                if mined_shadow_targets & gold_shadow_targets:
                    candidate_pool_summary["gold_trigger_rows_with_mined_overlap"] += 1
                if mined_shadow_targets == gold_shadow_targets:
                    candidate_pool_summary["gold_trigger_rows_with_exact_mined_set"] += 1

            for policy in requested_policies:
                promoted_targets = _resolve_promoted_targets_for_policy(
                    policy=policy,
                    gold_shadow_targets=gold_shadow_targets,
                    shadow_candidates=shadow_candidates,
                    active_candidates=active_candidates,
                    active_profile_fallback=active_profile_fallback_mapping,
                    support_score_min=support_score_min,
                    support_score_max_promoted=support_score_max_promoted,
                    support_frequency_representative_bonus=support_frequency_representative_bonus,
                    support_frequency_representative_top_k=support_frequency_representative_top_k,
                    support_frequency_similarity_weight=support_frequency_similarity_weight,
                    support_frequency_similarity_tau=support_frequency_similarity_tau,
                    support_representative_pruning_mode=support_representative_pruning_mode,
                    support_score_weights=support_score_weights,
                )
                _accumulate_veto_policy_row(
                    report=policy_reports[policy],
                    target=target,
                    trigger=trigger,
                    inventory_entry_present=bool(trigger_entry),
                    active_candidates=active_candidates,
                    active_profile_fallback=active_profile_fallback_mapping,
                    shadow_candidates=shadow_candidates,
                    active_candidate_count=len(active_candidates),
                    gold_shadow_targets=gold_shadow_targets,
                    mined_shadow_targets=mined_shadow_targets,
                    promoted_targets=promoted_targets,
                    row_metadata=(
                        row_metadata_by_key.get((target, trigger))
                        if isinstance(row_metadata_by_key, Mapping)
                        else None
                    ),
                    include_row_results=include_row_results,
                )

    for policy_report in policy_reports.values():
        if isinstance(policy_report, Mapping):
            _finalize_veto_policy_report(policy_report)

    _finalize_candidate_pool_summary(cast(MutableMapping[str, object], candidate_pool_summary))
    return {
        "schema_version": 1,
        "status": "ok",
        "candidate_pool_summary": candidate_pool_summary,
        "policies": policy_reports,
    }
