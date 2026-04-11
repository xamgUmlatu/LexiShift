#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Mapping, Sequence


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
    return lines


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
