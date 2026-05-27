#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# SRS Admission Calibration - en-es",
        "",
        f"- Status: {summary.get('status')}",
        f"- Findings: pass={summary.get('pass_count')} warn={summary.get('warn_count')} fail={summary.get('fail_count')}",
        f"- Admission budget: {summary.get('admission_budget')}",
        f"- Top-k window: {summary.get('top_k_window')}",
        f"- Weighted seeds: {', '.join(str(seed) for seed in dict(report.get('parameters') or {}).get('weighted_seeds', []))}",
        f"- Source rows: {dict(report.get('source_summary') or {}).get('row_count')}",
        "",
        "## How To Read",
        "",
        "- Ranked share is the deterministic topic-matching share of the preview admission batch.",
        "- Full-pool weighted share samples from the whole candidate pool and is diagnostic only.",
        "- Top-k weighted share samples from the ranked window, preserving variety without using the whole pool.",
        "- Reserved lane share uses the real profile-bootstrap policy with topic slots plus general slots.",
        "- Reserved lane expected count is derived from topic strength, lane cap, and ranked-window topic capacity.",
        "- These values are calibration diagnostics, not hard product guarantees.",
        "",
        "## Ranked Admission Batch Shares",
        "",
        "| Scenario | Active topics | Topic share | Topic count | Avg difficulty | Avg readiness | Top lemmas |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report.get("ranked_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            f"{row.get('name')} | "
            f"{_join(row.get('active_topics'))} | "
            f"{_format_float(row.get('selected_topic_share'))} | "
            f"{row.get('selected_topic_count')} | "
            f"{_format_float(row.get('average_difficulty'))} | "
            f"{_format_float(row.get('average_readiness'))} | "
            f"{_join(list(row.get('top_lemmas') or [])[:8])} |"
        )
    lines.extend(
        [
            "",
            "## Weighted Admission Batch Shares",
            "",
            "| Scenario | Mean topic share | Range | Mean topic count | Frequent lemmas |",
            "| --- | ---: | --- | ---: | --- |",
        ]
    )
    for row in report.get("weighted_rows", ()):
        if not isinstance(row, Mapping):
            continue
        frequent = [
            f"{item.get('lemma')}({item.get('count')})"
            for item in row.get("top_lemma_frequency", ())
            if isinstance(item, Mapping)
        ]
        lines.append(
            "| "
            f"{row.get('name')} | "
            f"{_format_float(row.get('mean_selected_topic_share'))} | "
            f"{_format_float(row.get('min_selected_topic_share'))}-"
            f"{_format_float(row.get('max_selected_topic_share'))} | "
            f"{_format_float(row.get('mean_selected_topic_count'))} | "
            f"{_join(frequent[:8])} |"
        )
    lines.extend(
        [
            "",
            "## Top-K Weighted Admission Shares",
            "",
            "| Scenario | Mean topic share | Range | Mean topic count | Frequent lemmas |",
            "| --- | ---: | --- | ---: | --- |",
        ]
    )
    for row in report.get("top_k_weighted_rows", ()):
        if not isinstance(row, Mapping):
            continue
        frequent = [
            f"{item.get('lemma')}({item.get('count')})"
            for item in row.get("top_lemma_frequency", ())
            if isinstance(item, Mapping)
        ]
        lines.append(
            "| "
            f"{row.get('name')} | "
            f"{_format_float(row.get('mean_selected_topic_share'))} | "
            f"{_format_float(row.get('min_selected_topic_share'))}-"
            f"{_format_float(row.get('max_selected_topic_share'))} | "
            f"{_format_float(row.get('mean_selected_topic_count'))} | "
            f"{_join(frequent[:8])} |"
        )
    lines.extend(
        [
            "",
            "## Reserved Topic-Lane Policy",
            "",
            "| Scenario | Active topics | Topic share | Topic count | Expected | Window topic candidates | Status | Top lemmas |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in report.get("topic_lane_rows", ()):
        if not isinstance(row, Mapping):
            continue
        expectation = dict(row.get("topic_lane_policy_expectation") or {})
        lines.append(
            "| "
            f"{row.get('name')} | "
            f"{_join(row.get('active_topics'))} | "
            f"{_format_float(row.get('selected_topic_share'))} | "
            f"{row.get('selected_topic_count')} | "
            f"{expectation.get('expected_topic_count', 0)} | "
            f"{expectation.get('window_topic_candidates', 0)} | "
            f"{expectation.get('status', 'missing')} | "
            f"{_join(list(row.get('top_lemmas') or [])[:8])} |"
        )
    lines.extend(["", "## Topic Support", ""])
    for row in report.get("ranked_rows", ()):
        if not isinstance(row, Mapping) or not row.get("active_topic_support"):
            continue
        lines.append(f"### {row.get('name')}")
        for topic in row.get("active_topic_support", ()):
            if not isinstance(topic, Mapping):
                continue
            lines.append(
                "- "
                f"{topic.get('topic')}: candidates={topic.get('candidate_count')}, "
                f"support_mass={_format_float(topic.get('support_mass'))}, "
                f"examples={_join(topic.get('top_examples'))}"
            )
        lines.append("")
    lines.extend(["## Findings", ""])
    for finding in report.get("findings", ()):
        if isinstance(finding, Mapping):
            lines.append(
                f"- {finding.get('level')}: `{finding.get('code')}` - {finding.get('message')}"
            )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: Mapping[str, Any], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")


def _format_float(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_safe_float(value):.3f}"


def _join(values: object) -> str:
    if not isinstance(values, Sequence) or isinstance(values, str):
        return "none"
    rendered = [str(value) for value in values if str(value).strip()]
    return ", ".join(rendered) if rendered else "none"


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed == parsed else 0.0
