from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_shadow_inventory import (
    DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    DEFAULT_FREQUENCY_REPRESENTATIVE_TOP_K,
    DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
    DEFAULT_SUPPORT_SCORE_MIN,
    BenchmarkShadowTarget,
    SHADOW_PROMOTION_POLICIES,
    promote_shadow_candidates_for_policy,
    promote_shadow_candidates_with_support_score,
    SUPPORT_SCORE_POLICY,
)
from lexishift_core.rulegen.semantic_shadow_support import (
    DEFAULT_FREQUENCY_SIMILARITY_TAU,
    DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
)

REFERENCE_SHADOW_POLICY_MODES = ("none", "gold_overlap_oracle")


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
    policy_reports: dict[str, object] = {}
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
                    active_profile_fallback=active_profile_fallback,
                    support_score_min=support_score_min,
                    support_score_max_promoted=support_score_max_promoted,
                    support_frequency_representative_bonus=support_frequency_representative_bonus,
                    support_frequency_representative_top_k=support_frequency_representative_top_k,
                    support_frequency_similarity_weight=support_frequency_similarity_weight,
                    support_frequency_similarity_tau=support_frequency_similarity_tau,
                    support_representative_pruning_mode=support_representative_pruning_mode,
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

    _finalize_candidate_pool_summary(candidate_pool_summary)
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
    policy_reports: dict[str, object] = {}
    for policy in requested_policies:
        policy_reports[policy] = _empty_veto_policy_report()

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
                    active_profile_fallback=active_profile_fallback,
                    support_score_min=support_score_min,
                    support_score_max_promoted=support_score_max_promoted,
                    support_frequency_representative_bonus=support_frequency_representative_bonus,
                    support_frequency_representative_top_k=support_frequency_representative_top_k,
                    support_frequency_similarity_weight=support_frequency_similarity_weight,
                    support_frequency_similarity_tau=support_frequency_similarity_tau,
                    support_representative_pruning_mode=support_representative_pruning_mode,
                )
                _accumulate_veto_policy_row(
                    report=policy_reports[policy],
                    target=target,
                    trigger=trigger,
                    active_candidate_count=len(active_candidates),
                    gold_shadow_targets=gold_shadow_targets,
                    mined_shadow_targets=mined_shadow_targets,
                    promoted_targets=promoted_targets,
                    row_metadata=(
                        row_metadata_by_key.get((target, trigger))
                        if isinstance(row_metadata_by_key, Mapping)
                        else None
                    ),
                )

    for policy_report in policy_reports.values():
        if isinstance(policy_report, Mapping):
            _finalize_veto_policy_report(policy_report)

    _finalize_candidate_pool_summary(candidate_pool_summary)
    return {
        "schema_version": 1,
        "status": "ok",
        "candidate_pool_summary": candidate_pool_summary,
        "policies": policy_reports,
    }


def _build_inventory_lookup(
    inventory: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    lookup: dict[tuple[str, str], Mapping[str, object]] = {}
    targets = inventory.get("targets")
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        return lookup
    for target_row in targets:
        if not isinstance(target_row, Mapping):
            continue
        target = str(target_row.get("target") or "").strip()
        if not target:
            continue
        trigger_entries = target_row.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            continue
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            trigger = str(trigger_entry.get("trigger") or "").strip()
            if trigger:
                lookup[(target, trigger)] = trigger_entry
    return lookup


def _empty_policy_report() -> dict[str, object]:
    return {
        "summary": {
            "trigger_rows_total": 0,
            "gold_trigger_rows": 0,
            "trigger_rows_with_active_candidates": 0,
            "promoted_trigger_rows": 0,
            "candidate_true_positive_count": 0,
            "candidate_false_positive_count": 0,
            "candidate_false_negative_count": 0,
            "gold_trigger_rows_hit": 0,
            "gold_trigger_rows_exact_match": 0,
            "gold_trigger_rows_underblocked": 0,
            "gold_trigger_rows_partial": 0,
            "top1_gold_trigger_rows_hit": 0,
            "no_gold_trigger_rows": 0,
            "no_gold_trigger_rows_overblocked": 0,
        },
        "sample_underblocked_rows": [],
        "sample_overblocked_rows": [],
        "sample_partial_rows": [],
    }


def _empty_veto_policy_report() -> dict[str, object]:
    return {
        "summary": _empty_veto_summary(),
        "slice_summaries": {},
        "sample_harmful_allow_rows": [],
        "sample_false_abstain_rows": [],
    }


def _empty_veto_summary() -> dict[str, object]:
    return {
        "trigger_rows_total": 0,
        "trigger_rows_with_active_candidates": 0,
        "ambiguous_trigger_rows": 0,
        "clear_trigger_rows": 0,
        "abstain_rows": 0,
        "allow_rows": 0,
        "true_abstain_count": 0,
        "harmful_allow_count": 0,
        "true_allow_count": 0,
        "false_abstain_count": 0,
    }


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _resolve_promoted_targets_for_policy(
    *,
    policy: str,
    gold_shadow_targets: set[str],
    shadow_candidates: Sequence[object],
    active_candidates: Sequence[object],
    active_profile_fallback: Mapping[str, object] | None,
    support_score_min: float,
    support_score_max_promoted: int,
    support_frequency_representative_bonus: float,
    support_frequency_representative_top_k: int,
    support_frequency_similarity_weight: float,
    support_frequency_similarity_tau: float,
    support_representative_pruning_mode: str,
) -> list[str]:
    if policy == "none":
        return []
    if policy == "gold_overlap_oracle":
        return sorted(gold_shadow_targets)
    if policy == SUPPORT_SCORE_POLICY:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            active_profile_fallback=active_profile_fallback,
            min_score=support_score_min,
            max_promoted_shadows=support_score_max_promoted,
            policy=policy,
            frequency_representative_bonus=support_frequency_representative_bonus,
            frequency_representative_top_k=support_frequency_representative_top_k,
            frequency_similarity_weight=support_frequency_similarity_weight,
            frequency_similarity_tau=support_frequency_similarity_tau,
            representative_pruning_mode=support_representative_pruning_mode,
        )
        return [
            str(candidate.get("target") or "").strip()
            for candidate in promoted
            if isinstance(candidate, Mapping) and str(candidate.get("target") or "").strip()
        ]
    promoted = promote_shadow_candidates_for_policy(
        shadow_candidates=shadow_candidates,
        active_candidates=active_candidates,
        policy=policy,
    )
    return [
        str(candidate.get("target") or "").strip()
        for candidate in promoted
        if isinstance(candidate, Mapping) and str(candidate.get("target") or "").strip()
    ]


def _accumulate_policy_row(
    *,
    report: Mapping[str, object],
    target: str,
    trigger: str,
    active_candidate_count: int,
    gold_shadow_targets: set[str],
    mined_shadow_targets: set[str],
    promoted_targets: Sequence[str],
) -> None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return
    promoted_target_set = {value for value in promoted_targets if value}
    true_positive_targets = promoted_target_set & gold_shadow_targets
    false_positive_targets = promoted_target_set - gold_shadow_targets
    false_negative_targets = gold_shadow_targets - promoted_target_set

    summary["trigger_rows_total"] += 1
    if active_candidate_count:
        summary["trigger_rows_with_active_candidates"] += 1
    if promoted_target_set:
        summary["promoted_trigger_rows"] += 1
    summary["candidate_true_positive_count"] += len(true_positive_targets)
    summary["candidate_false_positive_count"] += len(false_positive_targets)
    summary["candidate_false_negative_count"] += len(false_negative_targets)

    row_payload = {
        "target": target,
        "trigger": trigger,
        "active_candidate_count": active_candidate_count,
        "gold_shadow_targets": sorted(gold_shadow_targets),
        "mined_shadow_targets": sorted(mined_shadow_targets),
        "promoted_targets": list(promoted_targets),
    }
    if gold_shadow_targets:
        summary["gold_trigger_rows"] += 1
        if true_positive_targets:
            summary["gold_trigger_rows_hit"] += 1
        else:
            summary["gold_trigger_rows_underblocked"] += 1
            _append_sample(report.get("sample_underblocked_rows"), row_payload)
        if promoted_targets and promoted_targets[0] in gold_shadow_targets:
            summary["top1_gold_trigger_rows_hit"] += 1
        if promoted_target_set == gold_shadow_targets:
            summary["gold_trigger_rows_exact_match"] += 1
        elif true_positive_targets:
            summary["gold_trigger_rows_partial"] += 1
            _append_sample(
                report.get("sample_partial_rows"),
                {
                    **row_payload,
                    "missing_gold_targets": sorted(false_negative_targets),
                    "extra_promoted_targets": sorted(false_positive_targets),
                },
            )
    else:
        summary["no_gold_trigger_rows"] += 1
        if promoted_target_set:
            summary["no_gold_trigger_rows_overblocked"] += 1
            _append_sample(report.get("sample_overblocked_rows"), row_payload)


def _accumulate_veto_policy_row(
    *,
    report: Mapping[str, object],
    target: str,
    trigger: str,
    active_candidate_count: int,
    gold_shadow_targets: set[str],
    mined_shadow_targets: set[str],
    promoted_targets: Sequence[str],
    row_metadata: Mapping[str, object] | None = None,
) -> None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return
    promoted_target_set = {value for value in promoted_targets if value}
    should_abstain = bool(gold_shadow_targets)
    did_abstain = bool(promoted_target_set)

    row_payload = {
        "target": target,
        "trigger": trigger,
        "active_candidate_count": active_candidate_count,
        "gold_shadow_targets": sorted(gold_shadow_targets),
        "mined_shadow_targets": sorted(mined_shadow_targets),
        "promoted_targets": list(promoted_targets),
    }
    normalized_metadata = _normalize_veto_row_metadata(row_metadata)
    if normalized_metadata:
        row_payload.update(normalized_metadata)

    _accumulate_veto_summary_counts(
        summary=summary,
        active_candidate_count=active_candidate_count,
        should_abstain=should_abstain,
        did_abstain=did_abstain,
    )

    if should_abstain:
        if not did_abstain:
            _append_sample(report.get("sample_harmful_allow_rows"), row_payload)
    elif did_abstain:
        _append_sample(report.get("sample_false_abstain_rows"), row_payload)

    _accumulate_veto_slice_summaries(
        report=report,
        row_metadata=normalized_metadata,
        active_candidate_count=active_candidate_count,
        should_abstain=should_abstain,
        did_abstain=did_abstain,
    )


def _normalize_veto_row_metadata(row_metadata: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(row_metadata, Mapping):
        return {}
    normalized: dict[str, object] = {}
    case_ids = _normalize_string_list(row_metadata.get("case_ids"))
    if case_ids:
        normalized["case_ids"] = case_ids
    tiers = _normalize_string_list(row_metadata.get("tiers"))
    if tiers:
        normalized["tiers"] = tiers
    slice_tags = _normalize_string_list(row_metadata.get("slice_tags"))
    if slice_tags:
        normalized["slice_tags"] = slice_tags
    raw_dimensions = row_metadata.get("slice_dimensions")
    normalized_dimensions: dict[str, list[str]] = {}
    for tier in tiers:
        normalized_dimensions.setdefault("tier", []).append(tier)
    if isinstance(raw_dimensions, Mapping):
        for name, raw_values in raw_dimensions.items():
            values = _normalize_string_list(raw_values)
            if values:
                dimension_name = str(name).strip()
                if not dimension_name:
                    continue
                bucket = normalized_dimensions.setdefault(dimension_name, [])
                for value in values:
                    if value not in bucket:
                        bucket.append(value)
    if normalized_dimensions:
        normalized["slice_dimensions"] = normalized_dimensions
    return normalized


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _accumulate_veto_summary_counts(
    *,
    summary: dict[str, object],
    active_candidate_count: int,
    should_abstain: bool,
    did_abstain: bool,
) -> None:
    summary["trigger_rows_total"] += 1
    if active_candidate_count:
        summary["trigger_rows_with_active_candidates"] += 1
    if did_abstain:
        summary["abstain_rows"] += 1
    else:
        summary["allow_rows"] += 1
    if should_abstain:
        summary["ambiguous_trigger_rows"] += 1
        if did_abstain:
            summary["true_abstain_count"] += 1
        else:
            summary["harmful_allow_count"] += 1
    else:
        summary["clear_trigger_rows"] += 1
        if did_abstain:
            summary["false_abstain_count"] += 1
        else:
            summary["true_allow_count"] += 1


def _iter_veto_slice_keys(row_metadata: Mapping[str, object]) -> list[str]:
    slice_keys: list[str] = []
    for tag in _normalize_string_list(row_metadata.get("slice_tags")):
        slice_key = f"tag:{tag}"
        if slice_key not in slice_keys:
            slice_keys.append(slice_key)
    raw_dimensions = row_metadata.get("slice_dimensions")
    if isinstance(raw_dimensions, Mapping):
        for name, raw_values in raw_dimensions.items():
            dimension_name = str(name or "").strip()
            if not dimension_name:
                continue
            for value in _normalize_string_list(raw_values):
                slice_key = f"dimension:{dimension_name}:{value}"
                if slice_key not in slice_keys:
                    slice_keys.append(slice_key)
    return slice_keys


def _accumulate_veto_slice_summaries(
    *,
    report: Mapping[str, object],
    row_metadata: Mapping[str, object],
    active_candidate_count: int,
    should_abstain: bool,
    did_abstain: bool,
) -> None:
    if not row_metadata:
        return
    slice_summaries = report.get("slice_summaries")
    if not isinstance(slice_summaries, dict):
        return
    for slice_key in _iter_veto_slice_keys(row_metadata):
        summary = slice_summaries.get(slice_key)
        if not isinstance(summary, dict):
            summary = _empty_veto_summary()
            slice_summaries[slice_key] = summary
        _accumulate_veto_summary_counts(
            summary=summary,
            active_candidate_count=active_candidate_count,
            should_abstain=should_abstain,
            did_abstain=did_abstain,
        )


def _append_sample(container: object, payload: Mapping[str, object], *, limit: int = 12) -> None:
    if not isinstance(container, list):
        return
    if len(container) < limit:
        container.append(dict(payload))


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _finalize_policy_report(report: Mapping[str, object]) -> None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return
    tp = int(summary.get("candidate_true_positive_count") or 0)
    fp = int(summary.get("candidate_false_positive_count") or 0)
    fn = int(summary.get("candidate_false_negative_count") or 0)
    gold_rows = int(summary.get("gold_trigger_rows") or 0)
    no_gold_rows = int(summary.get("no_gold_trigger_rows") or 0)

    summary["candidate_precision"] = _safe_rate(tp, tp + fp)
    summary["candidate_recall"] = _safe_rate(tp, tp + fn)
    precision = summary.get("candidate_precision")
    recall = summary.get("candidate_recall")
    if isinstance(precision, float) and isinstance(recall, float) and (precision + recall) > 0:
        summary["candidate_f1"] = 2 * precision * recall / (precision + recall)
    else:
        summary["candidate_f1"] = None
    summary["gold_trigger_hit_rate"] = _safe_rate(
        int(summary.get("gold_trigger_rows_hit") or 0),
        gold_rows,
    )
    summary["gold_trigger_exact_match_rate"] = _safe_rate(
        int(summary.get("gold_trigger_rows_exact_match") or 0),
        gold_rows,
    )
    summary["top1_gold_trigger_hit_rate"] = _safe_rate(
        int(summary.get("top1_gold_trigger_rows_hit") or 0),
        gold_rows,
    )
    summary["underblocking_rate"] = _safe_rate(
        int(summary.get("gold_trigger_rows_underblocked") or 0),
        gold_rows,
    )
    summary["overblocking_rate"] = _safe_rate(
        int(summary.get("no_gold_trigger_rows_overblocked") or 0),
        no_gold_rows,
    )


def _finalize_veto_policy_report(report: Mapping[str, object]) -> None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return
    _finalize_veto_summary(summary)
    slice_summaries = report.get("slice_summaries")
    if isinstance(slice_summaries, dict):
        for slice_summary in slice_summaries.values():
            if isinstance(slice_summary, dict):
                _finalize_veto_summary(slice_summary)


def _finalize_veto_summary(summary: Mapping[str, object]) -> None:
    trigger_rows = int(summary.get("trigger_rows_total") or 0)
    ambiguous_rows = int(summary.get("ambiguous_trigger_rows") or 0)
    clear_rows = int(summary.get("clear_trigger_rows") or 0)
    allow_rows = int(summary.get("allow_rows") or 0)
    abstain_rows = int(summary.get("abstain_rows") or 0)
    true_abstain = int(summary.get("true_abstain_count") or 0)
    harmful_allow = int(summary.get("harmful_allow_count") or 0)
    true_allow = int(summary.get("true_allow_count") or 0)
    false_abstain = int(summary.get("false_abstain_count") or 0)

    summary["abstain_recall"] = _safe_rate(true_abstain, ambiguous_rows)
    summary["harmful_allow_rate"] = _safe_rate(harmful_allow, ambiguous_rows)
    summary["allow_precision"] = _safe_rate(true_allow, allow_rows)
    summary["allow_rate"] = _safe_rate(allow_rows, trigger_rows)
    summary["abstain_rate"] = _safe_rate(abstain_rows, trigger_rows)
    summary["overblocking_rate"] = _safe_rate(false_abstain, clear_rows)
    summary["overall_accuracy"] = _safe_rate(true_abstain + true_allow, trigger_rows)


def _finalize_candidate_pool_summary(summary: Mapping[str, object]) -> None:
    trigger_rows = int(summary.get("trigger_rows_total") or 0)
    gold_rows = int(summary.get("gold_trigger_rows") or 0)
    summary["inventory_entry_coverage_rate"] = _safe_rate(
        int(summary.get("trigger_rows_with_inventory_entry") or 0),
        trigger_rows,
    )
    summary["gold_trigger_inventory_coverage_rate"] = _safe_rate(
        int(summary.get("gold_trigger_rows_with_inventory_entry") or 0),
        gold_rows,
    )
    summary["candidate_pool_trigger_recall"] = _safe_rate(
        int(summary.get("gold_trigger_rows_with_mined_overlap") or 0),
        gold_rows,
    )
    summary["candidate_pool_exact_match_rate"] = _safe_rate(
        int(summary.get("gold_trigger_rows_with_exact_mined_set") or 0),
        gold_rows,
    )
    summary["gold_trigger_active_support_rate"] = _safe_rate(
        int(summary.get("gold_trigger_rows_with_active_candidates") or 0),
        gold_rows,
    )
