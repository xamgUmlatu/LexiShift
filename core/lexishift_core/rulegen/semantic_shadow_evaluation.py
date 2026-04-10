from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_shadow_inventory import (
    BenchmarkShadowTarget,
    SHADOW_PROMOTION_POLICIES,
    promote_shadow_candidates_for_policy,
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
) -> dict[str, object]:
    gold_rows = build_benchmark_trigger_overlap_gold(benchmark_targets)
    requested_policies = tuple(
        policy
        for policy in policies
        if policy in SHADOW_PROMOTION_POLICIES or policy in REFERENCE_SHADOW_POLICY_MODES
    )
    candidate_pool_summary = {
        "trigger_rows_total": 0,
        "gold_trigger_rows": 0,
        "gold_trigger_rows_with_active_candidates": 0,
        "gold_trigger_rows_with_mined_overlap": 0,
        "gold_trigger_rows_with_exact_mined_set": 0,
    }
    policy_reports: dict[str, object] = {}
    for policy in requested_policies:
        policy_reports[policy] = _empty_policy_report()

    targets = inventory.get("targets")
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        return {
            "schema_version": 1,
            "status": "inventory_unavailable",
            "candidate_pool_summary": candidate_pool_summary,
            "policies": policy_reports,
        }

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
            if not trigger:
                continue
            active_candidates = _as_sequence(trigger_entry.get("active_candidates"))
            shadow_candidates = _as_sequence(trigger_entry.get("shadow_candidates"))
            gold_shadow_targets = set(gold_rows.get((target, trigger), ()))
            mined_shadow_targets = {
                str(candidate.get("target") or "").strip()
                for candidate in shadow_candidates
                if isinstance(candidate, Mapping) and str(candidate.get("target") or "").strip()
            }

            candidate_pool_summary["trigger_rows_total"] += 1
            if gold_shadow_targets:
                candidate_pool_summary["gold_trigger_rows"] += 1
                if active_candidates:
                    candidate_pool_summary["gold_trigger_rows_with_active_candidates"] += 1
                if mined_shadow_targets & gold_shadow_targets:
                    candidate_pool_summary["gold_trigger_rows_with_mined_overlap"] += 1
                if mined_shadow_targets == gold_shadow_targets:
                    candidate_pool_summary["gold_trigger_rows_with_exact_mined_set"] += 1

            for policy in requested_policies:
                if policy == "none":
                    promoted_targets: list[str] = []
                elif policy == "gold_overlap_oracle":
                    promoted_targets = sorted(gold_shadow_targets)
                else:
                    promoted = promote_shadow_candidates_for_policy(
                        shadow_candidates=shadow_candidates,
                        active_candidates=active_candidates,
                        policy=policy,
                    )
                    promoted_targets = [
                        str(candidate.get("target") or "").strip()
                        for candidate in promoted
                        if isinstance(candidate, Mapping)
                        and str(candidate.get("target") or "").strip()
                    ]
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


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


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


def _finalize_candidate_pool_summary(summary: Mapping[str, object]) -> None:
    gold_rows = int(summary.get("gold_trigger_rows") or 0)
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
