#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Mapping, Sequence

_DEFAULT_MIN_BUCKET_ROWS = 3
_DEFAULT_EXCLUDED_FEATURE_DIMENSIONS = frozenset({"feature_promoted_target_count"})


def render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _render_row_suffix(row: Mapping[str, object]) -> str:
    suffix_parts: list[str] = []
    miss_classification = str(row.get("miss_classification") or "").strip()
    if miss_classification:
        suffix_parts.append(f"miss={miss_classification}")
    case_ids = row.get("case_ids")
    if isinstance(case_ids, Sequence) and not isinstance(case_ids, (str, bytes)) and case_ids:
        suffix_parts.append(f"cases={list(case_ids)}")
    slice_tags = row.get("slice_tags")
    if isinstance(slice_tags, Sequence) and not isinstance(slice_tags, (str, bytes)) and slice_tags:
        suffix_parts.append(f"tags={list(slice_tags)}")
    return (" " + " ".join(suffix_parts)) if suffix_parts else ""


def _render_metric_block(label: str, result: Mapping[str, object]) -> list[str]:
    gold_summary = (
        result.get("gold_summary") if isinstance(result.get("gold_summary"), Mapping) else {}
    )
    veto_summary = (
        result.get("veto_summary") if isinstance(result.get("veto_summary"), Mapping) else {}
    )
    lines = [
        f"### {label}",
        f"- Experiment: `{result.get('experiment_id', '')}`",
        f"- Label: `{result.get('label', '')}`",
        f"- Seed mode / policy: `{result.get('seed_mode', '')}` / `{result.get('policy', '')}`",
        f"- Trigger filter min: `{result.get('trigger_support_score_min', '')}`",
        f"- Shadow support min / max promoted: `{result.get('support_score_min', '')}` / `{result.get('support_score_max_promoted', '')}`",
        f"- Semantic-bridge aux text / examples: `{bool(result.get('semantic_bridge_include_aux_text'))}` / `{bool(result.get('semantic_bridge_include_examples'))}`",
        f"- Gold precision / recall / F1: `{render_rate(gold_summary.get('candidate_precision'))}` / `{render_rate(gold_summary.get('candidate_recall'))}` / `{render_rate(gold_summary.get('candidate_f1'))}`",
        f"- Veto accuracy / abstain recall / harmful allow / overblocking: `{render_rate(veto_summary.get('overall_accuracy'))}` / `{render_rate(veto_summary.get('abstain_recall'))}` / `{render_rate(veto_summary.get('harmful_allow_rate'))}` / `{render_rate(veto_summary.get('overblocking_rate'))}`",
        f"- Veto counts: `false_abstain={veto_summary.get('false_abstain_count', 0)}`, `harmful_allow={veto_summary.get('harmful_allow_count', 0)}`",
    ]
    trigger_support_weights = result.get("trigger_support_weights")
    if isinstance(trigger_support_weights, Mapping) and trigger_support_weights:
        lines.append(
            "- Trigger support weights: "
            f"`{json.dumps(trigger_support_weights, sort_keys=True, ensure_ascii=False)}`"
        )
    shadow_support_weights = result.get("shadow_support_weights")
    if isinstance(shadow_support_weights, Mapping) and shadow_support_weights:
        lines.append(
            "- Shadow support weights: "
            f"`{json.dumps(shadow_support_weights, sort_keys=True, ensure_ascii=False)}`"
        )
    lines.extend(
        _render_generalization_split_lines(result.get("veto_generalization_split_summary"))
    )
    return lines


def _render_generalization_split_lines(summary: object) -> list[str]:
    if not isinstance(summary, Mapping):
        return []
    lines = [
        "- Generalization split coverage: "
        f"`assigned={summary.get('assigned_row_count', 0)}`, "
        f"`unassigned={summary.get('unassigned_row_count', 0)}`",
        "- Tune veto acc / abstain recall / harmful allow / overblocking: "
        f"`{render_rate(_split_metric(summary, 'tune', 'overall_accuracy'))}` / "
        f"`{render_rate(_split_metric(summary, 'tune', 'abstain_recall'))}` / "
        f"`{render_rate(_split_metric(summary, 'tune', 'harmful_allow_rate'))}` / "
        f"`{render_rate(_split_metric(summary, 'tune', 'overblocking_rate'))}`",
        "- Held-out veto acc / abstain recall / harmful allow / overblocking: "
        f"`{render_rate(_split_metric(summary, 'held_out', 'overall_accuracy'))}` / "
        f"`{render_rate(_split_metric(summary, 'held_out', 'abstain_recall'))}` / "
        f"`{render_rate(_split_metric(summary, 'held_out', 'harmful_allow_rate'))}` / "
        f"`{render_rate(_split_metric(summary, 'held_out', 'overblocking_rate'))}`",
        "- Held-out minus tune acc / abstain recall / harmful allow / overblocking: "
        f"`{render_rate(_split_delta_metric(summary, 'overall_accuracy'))}` / "
        f"`{render_rate(_split_delta_metric(summary, 'abstain_recall'))}` / "
        f"`{render_rate(_split_delta_metric(summary, 'harmful_allow_rate'))}` / "
        f"`{render_rate(_split_delta_metric(summary, 'overblocking_rate'))}`",
    ]
    unassigned_samples = summary.get("unassigned_row_samples")
    if (
        isinstance(unassigned_samples, Sequence)
        and not isinstance(unassigned_samples, (str, bytes))
        and unassigned_samples
    ):
        lines.append(
            "- Split-unassigned rows: "
            + "; ".join(
                (
                    f"{sample.get('target', '')}/{sample.get('trigger', '')} "
                    f"families={sample.get('semantic_families', [])}"
                )
                for sample in unassigned_samples[:5]
                if isinstance(sample, Mapping)
            )
        )
    return lines


def _split_metric(summary: object, split_id: str, metric_name: str) -> object:
    if not isinstance(summary, Mapping):
        return None
    splits = summary.get("splits")
    if not isinstance(splits, Mapping):
        return None
    split_payload = splits.get(split_id)
    if not isinstance(split_payload, Mapping):
        return None
    split_summary = split_payload.get("summary")
    if not isinstance(split_summary, Mapping):
        return None
    return split_summary.get(metric_name)


def _split_delta_metric(summary: object, metric_name: str) -> object:
    if not isinstance(summary, Mapping):
        return None
    deltas = summary.get("deltas")
    if not isinstance(deltas, Mapping):
        return None
    gap = deltas.get("held_out_minus_tune")
    if not isinstance(gap, Mapping):
        return None
    return gap.get(metric_name)


def build_candidate_feature_bucket_risk_report(
    *,
    candidate_result: Mapping[str, object],
    row_comparison: Mapping[str, object],
    min_bucket_rows: int = _DEFAULT_MIN_BUCKET_ROWS,
    excluded_feature_dimensions: Sequence[str] = _DEFAULT_EXCLUDED_FEATURE_DIMENSIONS,
) -> dict[str, object]:
    candidate_rows = candidate_result.get("veto_row_results")
    if not isinstance(candidate_rows, Sequence) or isinstance(candidate_rows, (str, bytes)):
        return {
            "minimum_bucket_rows": max(1, int(min_bucket_rows)),
            "excluded_feature_dimensions": sorted(
                str(value).strip() for value in excluded_feature_dimensions if str(value).strip()
            ),
            "harmful_allow_bucket_rows": [],
            "false_abstain_bucket_rows": [],
        }

    excluded_dimensions = {
        str(value).strip() for value in excluded_feature_dimensions if str(value).strip()
    }
    persistent_harmful_allow_keys = _collect_row_key_set(
        row_comparison.get("persistent_harmful_allow_rows")
    )
    persistent_false_abstain_keys = _collect_row_key_set(
        row_comparison.get("persistent_false_abstain_rows")
    )
    bucket_stats: dict[str, dict[str, object]] = {}
    for row in candidate_rows:
        if not isinstance(row, Mapping):
            continue
        target = str(row.get("target") or "").strip()
        trigger = str(row.get("trigger") or "").strip()
        if not target or not trigger:
            continue
        row_key = (target, trigger)
        outcome = str(row.get("outcome") or "").strip()
        should_abstain = bool(row.get("should_abstain"))
        miss_classification = str(row.get("miss_classification") or "").strip()
        for slice_key in _iter_feature_slice_keys_from_row(
            row,
            excluded_feature_dimensions=excluded_dimensions,
        ):
            stats = bucket_stats.setdefault(
                slice_key,
                {
                    "slice_key": slice_key,
                    "trigger_rows_total": 0,
                    "ambiguous_trigger_rows": 0,
                    "clear_trigger_rows": 0,
                    "true_abstain_count": 0,
                    "harmful_allow_count": 0,
                    "true_allow_count": 0,
                    "false_abstain_count": 0,
                    "persistent_harmful_allow_count": 0,
                    "persistent_false_abstain_count": 0,
                    "harmful_allow_miss_counts": {
                        "seed_missing": 0,
                        "candidate_missing": 0,
                        "promotion_miss": 0,
                    },
                },
            )
            stats["trigger_rows_total"] += 1
            if should_abstain:
                stats["ambiguous_trigger_rows"] += 1
                if outcome == "true_abstain":
                    stats["true_abstain_count"] += 1
                elif outcome == "harmful_allow":
                    stats["harmful_allow_count"] += 1
                    if row_key in persistent_harmful_allow_keys:
                        stats["persistent_harmful_allow_count"] += 1
                    miss_counts = stats["harmful_allow_miss_counts"]
                    if isinstance(miss_counts, dict) and miss_classification in miss_counts:
                        miss_counts[miss_classification] += 1
            else:
                stats["clear_trigger_rows"] += 1
                if outcome == "true_allow":
                    stats["true_allow_count"] += 1
                elif outcome == "false_abstain":
                    stats["false_abstain_count"] += 1
                    if row_key in persistent_false_abstain_keys:
                        stats["persistent_false_abstain_count"] += 1

    veto_summary = (
        candidate_result.get("veto_summary")
        if isinstance(candidate_result.get("veto_summary"), Mapping)
        else {}
    )
    global_harmful_allow_rate = veto_summary.get("harmful_allow_rate")
    global_false_abstain_rate = veto_summary.get("overblocking_rate")
    harmful_allow_bucket_rows: list[dict[str, object]] = []
    false_abstain_bucket_rows: list[dict[str, object]] = []
    for stats in bucket_stats.values():
        if not isinstance(stats, dict):
            continue
        harmful_allow_rate = _safe_rate(
            int(stats.get("harmful_allow_count") or 0),
            int(stats.get("ambiguous_trigger_rows") or 0),
        )
        false_abstain_rate = _safe_rate(
            int(stats.get("false_abstain_count") or 0),
            int(stats.get("clear_trigger_rows") or 0),
        )
        total_rows = int(stats.get("trigger_rows_total") or 0)
        overall_accuracy = _safe_rate(
            int(stats.get("true_abstain_count") or 0) + int(stats.get("true_allow_count") or 0),
            total_rows,
        )
        finalized = {
            **stats,
            "harmful_allow_rate": harmful_allow_rate,
            "false_abstain_rate": false_abstain_rate,
            "overall_accuracy": overall_accuracy,
            "harmful_allow_rate_lift": _delta(harmful_allow_rate, global_harmful_allow_rate),
            "false_abstain_rate_lift": _delta(false_abstain_rate, global_false_abstain_rate),
        }
        if (
            int(finalized.get("ambiguous_trigger_rows") or 0) >= max(1, int(min_bucket_rows))
            and int(finalized.get("harmful_allow_count") or 0) > 0
        ):
            harmful_allow_bucket_rows.append(finalized)
        if (
            int(finalized.get("clear_trigger_rows") or 0) >= max(1, int(min_bucket_rows))
            and int(finalized.get("false_abstain_count") or 0) > 0
        ):
            false_abstain_bucket_rows.append(finalized)

    harmful_allow_bucket_rows.sort(
        key=lambda row: (
            int(row.get("persistent_harmful_allow_count") or 0),
            float(row.get("harmful_allow_rate_lift") or 0.0),
            int(row.get("harmful_allow_count") or 0),
            int(row.get("ambiguous_trigger_rows") or 0),
        ),
        reverse=True,
    )
    false_abstain_bucket_rows.sort(
        key=lambda row: (
            int(row.get("persistent_false_abstain_count") or 0),
            float(row.get("false_abstain_rate_lift") or 0.0),
            int(row.get("false_abstain_count") or 0),
            int(row.get("clear_trigger_rows") or 0),
        ),
        reverse=True,
    )
    return {
        "minimum_bucket_rows": max(1, int(min_bucket_rows)),
        "excluded_feature_dimensions": sorted(excluded_dimensions),
        "harmful_allow_bucket_rows": harmful_allow_bucket_rows,
        "false_abstain_bucket_rows": false_abstain_bucket_rows,
    }


def _collect_row_key_set(rows: object) -> set[tuple[str, str]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return set()
    resolved: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        target = str(row.get("target") or "").strip()
        trigger = str(row.get("trigger") or "").strip()
        if target and trigger:
            resolved.add((target, trigger))
    return resolved


def _iter_feature_slice_keys_from_row(
    row: Mapping[str, object],
    *,
    excluded_feature_dimensions: set[str],
) -> list[str]:
    raw_feature_dimensions = row.get("feature_dimensions")
    if not isinstance(raw_feature_dimensions, Mapping):
        return []
    slice_keys: list[str] = []
    for name, raw_values in raw_feature_dimensions.items():
        dimension_name = str(name or "").strip()
        if not dimension_name or dimension_name in excluded_feature_dimensions:
            continue
        if not isinstance(raw_values, Sequence) or isinstance(raw_values, (str, bytes)):
            continue
        for value in raw_values:
            normalized_value = str(value or "").strip()
            if not normalized_value:
                continue
            slice_key = f"feature:{dimension_name}:{normalized_value}"
            if slice_key not in slice_keys:
                slice_keys.append(slice_key)
    return slice_keys


def _delta(value: object, baseline: object) -> float | None:
    if not isinstance(value, (float, int)) or not isinstance(baseline, (float, int)):
        return None
    return float(value) - float(baseline)


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def _render_miss_mix(row: Mapping[str, object]) -> str:
    miss_counts = row.get("harmful_allow_miss_counts")
    if not isinstance(miss_counts, Mapping):
        return "n/a"
    return (
        f"seed={int(miss_counts.get('seed_missing') or 0)} "
        f"cand={int(miss_counts.get('candidate_missing') or 0)} "
        f"promo={int(miss_counts.get('promotion_miss') or 0)}"
    )


def render_experiment_compare_markdown(report: Mapping[str, object]) -> str:
    control = report.get("control") if isinstance(report.get("control"), Mapping) else {}
    candidate = report.get("candidate") if isinstance(report.get("candidate"), Mapping) else {}
    row_comparison = (
        report.get("row_comparison") if isinstance(report.get("row_comparison"), Mapping) else {}
    )
    comparison_summary = (
        row_comparison.get("summary") if isinstance(row_comparison.get("summary"), Mapping) else {}
    )
    slice_rows = report.get("slice_delta_rows")
    if not isinstance(slice_rows, Sequence) or isinstance(slice_rows, (str, bytes)):
        slice_rows = []
    candidate_feature_bucket_risk = (
        report.get("candidate_feature_bucket_risk")
        if isinstance(report.get("candidate_feature_bucket_risk"), Mapping)
        else {}
    )
    beneficial_ambiguous = [
        row
        for row in slice_rows
        if isinstance(row, Mapping)
        and int(row.get("ambiguous_trigger_rows") or 0) > 0
        and (
            int(row.get("control_harmful_allow_count") or 0)
            - int(row.get("candidate_harmful_allow_count") or 0)
        )
        > 0
    ]
    beneficial_ambiguous = sorted(
        beneficial_ambiguous,
        key=lambda row: (
            int(row.get("control_harmful_allow_count") or 0)
            - int(row.get("candidate_harmful_allow_count") or 0),
            float(row.get("delta_abstain_recall") or 0.0),
            int(row.get("trigger_rows_total") or 0),
        ),
        reverse=True,
    )
    regressive_clear = [
        row
        for row in slice_rows
        if isinstance(row, Mapping)
        and int(row.get("clear_trigger_rows") or 0) > 0
        and (
            int(row.get("candidate_false_abstain_count") or 0)
            - int(row.get("control_false_abstain_count") or 0)
        )
        > 0
    ]
    regressive_clear = sorted(
        regressive_clear,
        key=lambda row: (
            int(row.get("candidate_false_abstain_count") or 0)
            - int(row.get("control_false_abstain_count") or 0),
            float(row.get("delta_overblocking_rate") or 0.0),
            int(row.get("trigger_rows_total") or 0),
        ),
        reverse=True,
    )

    lines = [
        "# en-es Semantic Shadow Experiment Compare",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Generalization split manifest: `{report.get('generalization_splits_manifest_path', '')}`",
        f"- Frontier read: `{report.get('frontier_read', '')}`",
        "- Meaning: compare the current control row against a candidate row and measure exact row-level fixes, regressions, and slice deltas.",
        "",
        "## Overall",
        f"- Row outcomes: `improved={comparison_summary.get('improved_rows', 0)}`, `regressed={comparison_summary.get('regressed_rows', 0)}`, `stable_correct={comparison_summary.get('stable_correct_rows', 0)}`, `stable_incorrect={comparison_summary.get('stable_incorrect_rows', 0)}`",
        f"- Ambiguous-row changes: `fixed_harmful_allow={comparison_summary.get('fixed_harmful_allow_rows', 0)}`, `persistent_harmful_allow={comparison_summary.get('persistent_harmful_allow_rows', 0)}`",
        f"- Clear-row changes: `introduced_false_abstain={comparison_summary.get('introduced_false_abstain_rows', 0)}`, `persistent_false_abstain={comparison_summary.get('persistent_false_abstain_rows', 0)}`",
        "",
        "## Experiments",
        "",
    ]
    lines.extend(_render_metric_block("Control", control))
    lines.extend([""])
    lines.extend(_render_metric_block("Candidate", candidate))
    lines.extend(
        [
            "",
            "## Deltas",
            f"- Gold precision delta: `{render_rate(report.get('gold_precision_delta'))}`",
            f"- Gold recall delta: `{render_rate(report.get('gold_recall_delta'))}`",
            f"- Veto accuracy delta: `{render_rate(report.get('veto_accuracy_delta'))}`",
            f"- Abstain recall delta: `{render_rate(report.get('abstain_recall_delta'))}`",
            f"- Harmful allow delta: `{render_rate(report.get('harmful_allow_delta'))}`",
            f"- Overblocking delta: `{render_rate(report.get('overblocking_delta'))}`",
        ]
    )

    if beneficial_ambiguous:
        lines.extend(
            [
                "",
                "## Best Ambiguous Slice Gains",
                "| Slice | Rows | Harmful Allow Count | Abstain Recall Delta | Accuracy Delta |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in beneficial_ambiguous[:10]:
            control_harmful = int(row.get("control_harmful_allow_count") or 0)
            candidate_harmful = int(row.get("candidate_harmful_allow_count") or 0)
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("slice_key", "")),
                        str(row.get("trigger_rows_total", "")),
                        f"{control_harmful} -> {candidate_harmful}",
                        render_rate(row.get("delta_abstain_recall")),
                        render_rate(row.get("delta_overall_accuracy")),
                    ]
                )
                + " |"
            )

    if regressive_clear:
        lines.extend(
            [
                "",
                "## Clear-Slice Regressions",
                "| Slice | Rows | False Abstain Count | Overblocking Delta | Accuracy Delta |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in regressive_clear[:10]:
            control_false = int(row.get("control_false_abstain_count") or 0)
            candidate_false = int(row.get("candidate_false_abstain_count") or 0)
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("slice_key", "")),
                        str(row.get("trigger_rows_total", "")),
                        f"{control_false} -> {candidate_false}",
                        render_rate(row.get("delta_overblocking_rate")),
                        render_rate(row.get("delta_overall_accuracy")),
                    ]
                )
                + " |"
            )

    harmful_allow_bucket_rows = candidate_feature_bucket_risk.get("harmful_allow_bucket_rows")
    if not isinstance(harmful_allow_bucket_rows, Sequence) or isinstance(
        harmful_allow_bucket_rows, (str, bytes)
    ):
        harmful_allow_bucket_rows = []
    false_abstain_bucket_rows = candidate_feature_bucket_risk.get("false_abstain_bucket_rows")
    if not isinstance(false_abstain_bucket_rows, Sequence) or isinstance(
        false_abstain_bucket_rows, (str, bytes)
    ):
        false_abstain_bucket_rows = []
    if harmful_allow_bucket_rows or false_abstain_bucket_rows:
        lines.extend(
            [
                "",
                "## Automatic Bucket Read",
                "- Meaning: candidate-side automatic feature buckets ranked by error concentration; this is a diagnostic read, not yet a routing policy.",
                f"- Minimum bucket rows shown: `{candidate_feature_bucket_risk.get('minimum_bucket_rows', '')}`",
                f"- Excluded downstream buckets: `{list(candidate_feature_bucket_risk.get('excluded_feature_dimensions', []))}`",
            ]
        )
    if harmful_allow_bucket_rows:
        lines.extend(
            [
                "",
                "### Harmful-Allow Buckets",
                "| Bucket | Ambiguous Rows | Harmful Allow | Persistent | Rate | Lift Vs Global | Miss Mix |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in harmful_allow_bucket_rows[:12]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("slice_key", "")),
                        str(row.get("ambiguous_trigger_rows", "")),
                        str(row.get("harmful_allow_count", "")),
                        str(row.get("persistent_harmful_allow_count", "")),
                        render_rate(row.get("harmful_allow_rate")),
                        render_rate(row.get("harmful_allow_rate_lift")),
                        _render_miss_mix(row),
                    ]
                )
                + " |"
            )
    if false_abstain_bucket_rows:
        lines.extend(
            [
                "",
                "### False-Abstain Buckets",
                "| Bucket | Clear Rows | False Abstain | Persistent | Rate | Lift Vs Global |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in false_abstain_bucket_rows[:12]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("slice_key", "")),
                        str(row.get("clear_trigger_rows", "")),
                        str(row.get("false_abstain_count", "")),
                        str(row.get("persistent_false_abstain_count", "")),
                        render_rate(row.get("false_abstain_rate")),
                        render_rate(row.get("false_abstain_rate_lift")),
                    ]
                )
                + " |"
            )

    for title, field_name, limit in (
        ("Fixed Harmful-Allow Rows", "fixed_harmful_allow_rows", 10),
        ("Introduced False-Abstain Rows", "introduced_false_abstain_rows", 10),
        ("Persistent Harmful-Allow Rows", "persistent_harmful_allow_rows", 10),
        ("Regressed Rows", "regressed_rows", 10),
    ):
        rows = row_comparison.get(field_name)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            continue
        lines.extend(["", f"## {title}"])
        if not rows:
            lines.append("- None")
            continue
        for row in rows[:limit]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('target', '')}` / `{row.get('trigger', '')}` "
                f"control={row.get('control_outcome', '')} candidate={row.get('candidate_outcome', '')} "
                f"control_promoted={row.get('control_promoted_targets', [])} "
                f"candidate_promoted={row.get('candidate_promoted_targets', [])}"
                f"{_render_row_suffix(row)}"
            )
    return "\n".join(lines) + "\n"
