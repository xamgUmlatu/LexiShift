#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping, Sequence


def render_margin_policy_sweep_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    recommendation = _as_mapping(report.get("recommendation"))
    configured = _as_mapping(report.get("configured_lane"))
    lines = [
        "# en-es Semantic Source Margin Policy Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Base dataset: `{report.get('base_dataset_id', '')}`",
        f"- Evidence batch: `{report.get('evidence_batch_id', '')}`",
        f"- Recommended min margin: `{_format_optional_margin(summary.get('recommended_min_margin'))}`",
        f"- Recommended phrase margin: `{_format_optional_margin(summary.get('recommended_phrase_prototype_margin'))}`",
        f"- Passing policies: `{_format_policy_list(recommendation.get('passing_policies'))}`",
        "",
        "## Configured Lane",
        "",
    ]
    for key, value in configured.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            f"- Decision: `{recommendation.get('decision', '')}`",
            f"- Reason: `{recommendation.get('reason', '')}`",
            f"- Next step: {recommendation.get('next_step', '')}",
            "",
            "## Rows",
            "",
            _row_table(report.get("rows", ())),
            "",
            "## Blockers By Margin",
            "",
            _blocker_table(recommendation.get("blockers_by_margin")),
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _row_table(rows: object) -> str:
    materialized = [row for row in rows if isinstance(row, Mapping)]
    if not materialized:
        return "No rows."
    lines = [
        "| Suite | Type | Margin | Phrase Margin | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('suite_id', '')}`",
                    f"`{row.get('suite_type', '')}`",
                    f"`{_format_margin(row.get('min_margin'))}`",
                    f"`{_format_margin(row.get('phrase_prototype_margin'))}`",
                    f"`{str(bool(row.get('passes'))).lower()}`",
                    str(row.get("case_count", 0)),
                    str(row.get("harmful_replace_count", 0)),
                    str(row.get("false_abstain_count", 0)),
                    _pct(row.get("replace_recall")),
                    _pct(row.get("decision_accuracy")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _blocker_table(blockers_by_margin: object) -> str:
    if not isinstance(blockers_by_margin, Mapping) or not blockers_by_margin:
        return "No blockers."
    lines = [
        "| Policy | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for policy, blockers in blockers_by_margin.items():
        if not isinstance(blockers, Sequence) or isinstance(blockers, (str, bytes)):
            continue
        for blocker in blockers:
            if not isinstance(blocker, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{policy}`",
                        f"`{blocker.get('suite_id', '')}`",
                        str(blocker.get("harmful_replace_count", 0)),
                        str(blocker.get("false_abstain_count", 0)),
                        _case_id_cell(blocker.get("harmful_replace_case_ids")),
                        _case_id_cell(blocker.get("false_abstain_case_ids")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) if len(lines) > 2 else "No blockers."


def _case_id_cell(value: object) -> str:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return "`none`"
    text = ", ".join(str(item) for item in value if str(item))
    return f"`{text or 'none'}`"


def _format_optional_margin(value: object) -> str:
    if value is None:
        return "none"
    return _format_margin(value)


def _format_policy_list(values: object) -> str:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return "none"
    policies = [policy for policy in values if isinstance(policy, Mapping)]
    return (
        ", ".join(
            _format_policy_key(
                float(policy.get("min_margin") or 0.0),
                float(policy.get("phrase_prototype_margin") or 0.0),
            )
            for policy in policies
        )
        or "none"
    )


def _format_policy_key(min_margin: float, phrase_prototype_margin: float) -> str:
    return f"m={_format_margin(min_margin)};phrase={_format_margin(phrase_prototype_margin)}"


def _format_margin(value: object) -> str:
    return f"{float(value):.3f}".rstrip("0").rstrip(".") if value is not None else "none"


def _pct(value: object) -> str:
    return f"{float(value or 0.0) * 100:.1f}%"


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
