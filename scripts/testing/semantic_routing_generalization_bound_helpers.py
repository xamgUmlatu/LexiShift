from __future__ import annotations

import math
import random
from typing import Callable, Mapping, Sequence

from semantic_routing_generalization_bound_splits import (
    build_metric_views,
    partition_rows_by_split,
)


def safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    bounded_quantile = min(max(float(quantile), 0.0), 1.0)
    sorted_values = sorted(float(value) for value in values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = bounded_quantile * (len(sorted_values) - 1)
    lower_index = int(math.floor(rank))
    upper_index = int(math.ceil(rank))
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    fraction = rank - lower_index
    return lower_value + ((upper_value - lower_value) * fraction)


def summarize_sentence_veto_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    cases_total = len(rows)
    gold_replace_cases = 0
    gold_abstain_cases = 0
    predicted_replace_cases = 0
    true_replace_count = 0
    true_abstain_count = 0
    harmful_replace_count = 0
    false_abstain_count = 0
    winner_labeled_cases = 0
    winner_correct_count = 0
    shadow_winner_labeled_cases = 0
    shadow_winner_correct_count = 0

    for row in rows:
        gold_decision = str(row.get("gold_decision") or "").strip().lower()
        predicted_decision = str(row.get("predicted_decision") or "").strip().lower()
        gold_winner = str(row.get("gold_winner") or "").strip()
        predicted_winner = str(row.get("predicted_winner") or "").strip()
        gold_winner_type = str(row.get("gold_winner_type") or "").strip().lower()

        if gold_decision == "replace":
            gold_replace_cases += 1
        else:
            gold_abstain_cases += 1
        if predicted_decision == "replace":
            predicted_replace_cases += 1
        if predicted_decision == "replace" and gold_decision == "replace":
            true_replace_count += 1
        elif predicted_decision == "replace":
            harmful_replace_count += 1
        elif gold_decision == "replace":
            false_abstain_count += 1
        else:
            true_abstain_count += 1

        if gold_winner_type in {"active", "shadow"}:
            winner_labeled_cases += 1
            if predicted_winner and predicted_winner == gold_winner:
                winner_correct_count += 1
        if gold_winner_type == "shadow":
            shadow_winner_labeled_cases += 1
            if predicted_winner and predicted_winner == gold_winner:
                shadow_winner_correct_count += 1

    return {
        "cases_total": cases_total,
        "gold_replace_cases": gold_replace_cases,
        "gold_abstain_cases": gold_abstain_cases,
        "predicted_replace_cases": predicted_replace_cases,
        "true_replace_count": true_replace_count,
        "true_abstain_count": true_abstain_count,
        "harmful_replace_count": harmful_replace_count,
        "false_abstain_count": false_abstain_count,
        "winner_labeled_cases": winner_labeled_cases,
        "shadow_winner_labeled_cases": shadow_winner_labeled_cases,
        "decision_accuracy": safe_rate(true_replace_count + true_abstain_count, cases_total),
        "replace_precision": safe_rate(true_replace_count, predicted_replace_cases),
        "replace_recall": safe_rate(true_replace_count, gold_replace_cases),
        "harmful_replace_rate": safe_rate(harmful_replace_count, gold_abstain_cases),
        "false_abstain_rate": safe_rate(false_abstain_count, gold_replace_cases),
        "winner_accuracy": safe_rate(winner_correct_count, winner_labeled_cases),
        "shadow_winner_accuracy": safe_rate(
            shadow_winner_correct_count,
            shadow_winner_labeled_cases,
        ),
    }


def summarize_sentence_veto_ladder_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    cases_total = len(rows)
    gold_replace_cases = 0
    gold_abstain_cases = 0
    replace_count = 0
    soft_affordance_count = 0
    hard_true_positive_count = 0
    hard_false_positive_count = 0
    soft_true_positive_count = 0
    soft_false_positive_count = 0
    remaining_missed_replace_count = 0

    for row in rows:
        gold_decision = str(row.get("gold_decision") or "").strip().lower()
        ladder_decision = str(row.get("ladder_decision") or "").strip().lower()

        if gold_decision == "replace":
            gold_replace_cases += 1
        else:
            gold_abstain_cases += 1

        if ladder_decision == "replace":
            replace_count += 1
            if gold_decision == "replace":
                hard_true_positive_count += 1
            else:
                hard_false_positive_count += 1
        elif ladder_decision == "soft_affordance":
            soft_affordance_count += 1
            if gold_decision == "replace":
                soft_true_positive_count += 1
            else:
                soft_false_positive_count += 1
        elif gold_decision == "replace":
            remaining_missed_replace_count += 1

    surfaced_count = replace_count + soft_affordance_count
    surfaced_true_positive_count = hard_true_positive_count + soft_true_positive_count

    return {
        "cases_total": cases_total,
        "gold_replace_cases": gold_replace_cases,
        "gold_abstain_cases": gold_abstain_cases,
        "replace_count": replace_count,
        "soft_affordance_count": soft_affordance_count,
        "hard_true_positive_count": hard_true_positive_count,
        "hard_false_positive_count": hard_false_positive_count,
        "soft_true_positive_count": soft_true_positive_count,
        "soft_false_positive_count": soft_false_positive_count,
        "remaining_missed_replace_count": remaining_missed_replace_count,
        "hard_replace_recall": safe_rate(hard_true_positive_count, gold_replace_cases),
        "hard_replace_precision": safe_rate(hard_true_positive_count, replace_count),
        "hard_harmful_replace_rate": safe_rate(hard_false_positive_count, gold_abstain_cases),
        "replace_or_soft_recall": safe_rate(surfaced_true_positive_count, gold_replace_cases),
        "soft_precision": safe_rate(soft_true_positive_count, soft_affordance_count),
        "soft_noise_rate": safe_rate(soft_false_positive_count, gold_abstain_cases),
        "surfaced_precision": safe_rate(surfaced_true_positive_count, surfaced_count),
        "remaining_missed_replace_rate": safe_rate(
            remaining_missed_replace_count, gold_replace_cases
        ),
    }


def summarize_veto_proxy_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    trigger_rows_total = len(rows)
    ambiguous_trigger_rows = 0
    clear_trigger_rows = 0
    allow_rows = 0
    abstain_rows = 0
    true_abstain_count = 0
    harmful_allow_count = 0
    true_allow_count = 0
    false_abstain_count = 0

    for row in rows:
        should_abstain = bool(row.get("should_abstain"))
        did_abstain = bool(row.get("did_abstain"))
        if should_abstain:
            ambiguous_trigger_rows += 1
        else:
            clear_trigger_rows += 1
        if did_abstain:
            abstain_rows += 1
        else:
            allow_rows += 1
        outcome = str(row.get("outcome") or "").strip()
        if outcome == "true_abstain":
            true_abstain_count += 1
        elif outcome == "harmful_allow":
            harmful_allow_count += 1
        elif outcome == "true_allow":
            true_allow_count += 1
        elif outcome == "false_abstain":
            false_abstain_count += 1

    return {
        "trigger_rows_total": trigger_rows_total,
        "ambiguous_trigger_rows": ambiguous_trigger_rows,
        "clear_trigger_rows": clear_trigger_rows,
        "allow_rows": allow_rows,
        "abstain_rows": abstain_rows,
        "true_abstain_count": true_abstain_count,
        "harmful_allow_count": harmful_allow_count,
        "true_allow_count": true_allow_count,
        "false_abstain_count": false_abstain_count,
        "overall_accuracy": safe_rate(true_abstain_count + true_allow_count, trigger_rows_total),
        "abstain_recall": safe_rate(true_abstain_count, ambiguous_trigger_rows),
        "harmful_allow_rate": safe_rate(harmful_allow_count, ambiguous_trigger_rows),
        "allow_precision": safe_rate(true_allow_count, allow_rows),
        "allow_rate": safe_rate(allow_rows, trigger_rows_total),
        "abstain_rate": safe_rate(abstain_rows, trigger_rows_total),
        "overblocking_rate": safe_rate(false_abstain_count, clear_trigger_rows),
    }


def group_rows_by_cluster(
    rows: Sequence[Mapping[str, object]],
    *,
    cluster_key_name: str,
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        cluster_value = str(row.get(cluster_key_name) or "").strip() or "<missing>"
        grouped.setdefault(cluster_value, []).append(row)
    return grouped


def build_cluster_summaries(
    grouped_rows: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cluster_id, cluster_rows in grouped_rows.items():
        summary = summarize_rows(cluster_rows)
        rows.append(
            {
                "cluster_id": str(cluster_id),
                "row_count": len(cluster_rows),
                "summary": summary,
            }
        )
    return sorted(rows, key=lambda item: (-int(item.get("row_count") or 0), item["cluster_id"]))


def bootstrap_cluster_metrics(
    grouped_rows: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_names: Sequence[str],
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
) -> dict[str, dict[str, object]]:
    cluster_samples = [list(rows) for rows in grouped_rows.values() if rows]
    if not cluster_samples:
        return {}
    lower_quantile = (1.0 - confidence_level) / 2.0
    upper_quantile = 1.0 - lower_quantile
    rng = random.Random(int(random_seed))
    sampled_values: dict[str, list[float]] = {metric: [] for metric in metric_names}
    for _ in range(max(1, int(bootstrap_iterations))):
        sampled_rows: list[Mapping[str, object]] = []
        for _cluster_index in range(len(cluster_samples)):
            sampled_rows.extend(rng.choice(cluster_samples))
        summary = summarize_rows(sampled_rows)
        for metric_name in metric_names:
            value = summary.get(metric_name)
            if isinstance(value, (int, float)):
                sampled_values[metric_name].append(float(value))
    intervals: dict[str, dict[str, object]] = {}
    for metric_name in metric_names:
        values = sampled_values.get(metric_name, [])
        intervals[metric_name] = {
            "lower": percentile(values, lower_quantile),
            "upper": percentile(values, upper_quantile),
            "sample_count": len(values),
        }
    return intervals


def leave_one_cluster_out_metrics(
    grouped_rows: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_names: Sequence[str],
    metric_directions: Mapping[str, str],
) -> dict[str, object]:
    cluster_ids = [str(cluster_id) for cluster_id in grouped_rows.keys()]
    if len(cluster_ids) <= 1:
        return {"rows": [], "metrics": {}}

    rows: list[dict[str, object]] = []
    metric_values: dict[str, list[tuple[str, float]]] = {metric: [] for metric in metric_names}
    for omitted_cluster_id in cluster_ids:
        sampled_rows: list[Mapping[str, object]] = []
        for cluster_id, cluster_rows in grouped_rows.items():
            if str(cluster_id) == omitted_cluster_id:
                continue
            sampled_rows.extend(cluster_rows)
        summary = summarize_rows(sampled_rows)
        rows.append(
            {
                "omitted_cluster_id": omitted_cluster_id,
                "row_count": len(sampled_rows),
                "summary": summary,
            }
        )
        for metric_name in metric_names:
            value = summary.get(metric_name)
            if isinstance(value, (int, float)):
                metric_values[metric_name].append((omitted_cluster_id, float(value)))

    metric_report: dict[str, object] = {}
    for metric_name in metric_names:
        values = metric_values.get(metric_name, [])
        if not values:
            metric_report[metric_name] = {
                "min": None,
                "max": None,
                "worst_case": None,
                "worst_case_omitted_cluster_id": "",
            }
            continue
        minimum = min(value for _, value in values)
        maximum = max(value for _, value in values)
        direction = str(metric_directions.get(metric_name) or "higher")
        if direction == "lower":
            worst_cluster_id, worst_case = max(values, key=lambda item: item[1])
        else:
            worst_cluster_id, worst_case = min(values, key=lambda item: item[1])
        metric_report[metric_name] = {
            "min": minimum,
            "max": maximum,
            "worst_case": worst_case,
            "worst_case_omitted_cluster_id": worst_cluster_id,
        }
    return {
        "rows": rows,
        "metrics": metric_report,
    }


def build_surface_bound(
    *,
    label: str,
    rows: Sequence[Mapping[str, object]],
    cluster_key_name: str,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_directions: Mapping[str, str],
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
    config: Mapping[str, object] | None = None,
) -> dict[str, object]:
    point_summary = summarize_rows(rows)
    grouped_rows = group_rows_by_cluster(rows, cluster_key_name=cluster_key_name)
    cluster_summaries = build_cluster_summaries(grouped_rows, summarize_rows=summarize_rows)
    bootstrap_intervals = bootstrap_cluster_metrics(
        grouped_rows,
        summarize_rows=summarize_rows,
        metric_names=tuple(metric_directions.keys()),
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
        confidence_level=confidence_level,
    )
    leave_one_cluster_out = leave_one_cluster_out_metrics(
        grouped_rows,
        summarize_rows=summarize_rows,
        metric_names=tuple(metric_directions.keys()),
        metric_directions=metric_directions,
    )
    metric_views = build_metric_views(
        point_summary=point_summary,
        bootstrap_intervals=bootstrap_intervals,
        leave_one_cluster_out=leave_one_cluster_out,
        metric_directions=metric_directions,
        confidence_level=confidence_level,
    )
    return {
        "label": label,
        "config": dict(config or {}),
        "cluster_key_name": cluster_key_name,
        "cluster_count": len(grouped_rows),
        "summary": point_summary,
        "metric_views": metric_views,
        "cluster_summaries": cluster_summaries,
        "leave_one_cluster_out_rows": leave_one_cluster_out.get("rows", []),
    }


def extend_with_split_surfaces(
    surfaces: list[dict[str, object]],
    *,
    label: str,
    rows: Sequence[Mapping[str, object]],
    cluster_key_name: str,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_directions: Mapping[str, str],
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
    config: Mapping[str, object],
    split_ids: Sequence[str],
    split_lookup: Mapping[str, str],
    resolve_split_id: Callable[[Mapping[str, object], Mapping[str, str]], str],
) -> None:
    split_rows, _unassigned_rows = partition_rows_by_split(
        rows,
        split_ids=split_ids,
        split_lookup=split_lookup,
        resolve_split_id=resolve_split_id,
    )
    for index, split_id in enumerate(split_ids):
        subset_rows = tuple(split_rows.get(str(split_id), ()))
        if not subset_rows:
            continue
        surfaces.append(
            build_surface_bound(
                label=f"{label} [{split_id}]",
                rows=subset_rows,
                cluster_key_name=cluster_key_name,
                summarize_rows=summarize_rows,
                metric_directions=metric_directions,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + index + 100,
                confidence_level=confidence_level,
                config={**dict(config), "subset_id": str(split_id)},
            )
        )
