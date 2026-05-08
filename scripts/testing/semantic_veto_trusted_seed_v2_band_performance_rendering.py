from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
)


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_signed_percent(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:+.1f}%"


def _comparison_table(value: object) -> str:
    comparison = _as_mapping(value)
    if not bool(comparison.get("available")):
        return "_No prior comparison report found._"
    rows = _mapping_rows(comparison.get("overall_deltas"))
    if not rows:
        return "_No comparable scorer rows._"
    headers = [
        "scorer",
        "current cases",
        "prior cases",
        "decision delta",
        "positive allow delta",
        "shadow abstain delta",
        "phrase abstain delta",
        "harmful delta",
        "false abstain delta",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [
            str(row.get("scorer_id") or ""),
            str(row.get("current_cases") or 0),
            str(row.get("prior_cases") or 0),
            _format_signed_percent(row.get("decision_accuracy_delta")),
            _format_signed_percent(row.get("positive_allow_rate_delta")),
            _format_signed_percent(row.get("shadow_negative_abstain_rate_delta")),
            _format_signed_percent(row.get("phrase_no_winner_abstain_rate_delta")),
            _format_signed_int(row.get("harmful_replace_count_delta")),
            _format_signed_int(row.get("false_abstain_count_delta")),
        ]
        lines.append("| " + " | ".join(_escape_md(value) for value in values) + " |")
    boundary = str(comparison.get("comparison_boundary") or "")
    return "\n".join([*lines, "", boundary])


def _metrics_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    dimension_keys = [
        key
        for key in (
            "scorer_id",
            "source_zipf_band_en",
            "manual_case_type",
            "target_zipf_band_es",
            "polysemy_band",
            "pos_shape",
            "approval_id",
            "trusted_seed_v2_status",
            "no_winner_subtype",
        )
        if any(key in row for row in rows)
    ]
    headers = [
        *dimension_keys,
        "cases",
        "decision",
        "precision",
        "positive allow",
        "shadow abstain",
        "phrase abstain",
        "harmful",
        "false abstain",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [
            *[str(row.get(key) or "") for key in dimension_keys],
            str(row.get("cases") or 0),
            _format_percent(row.get("decision_accuracy")),
            _format_percent(row.get("replace_precision")),
            _format_percent(row.get("positive_allow_rate")),
            _format_percent(row.get("shadow_negative_abstain_rate")),
            _format_percent(row.get("phrase_no_winner_abstain_rate")),
            f"{_format_percent(row.get('harmful_replace_rate'))} ({row.get('harmful_replace_count', 0)})",
            f"{_format_percent(row.get('false_abstain_rate'))} ({row.get('false_abstain_count', 0)})",
        ]
        lines.append("| " + " | ".join(_escape_md(value) for value in values) + " |")
    return "\n".join(lines)


def _failure_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No failures._"
    headers = [
        "scorer",
        "dimension",
        "value",
        "cases",
        "errors",
        "error rate",
        "harmful",
        "false abstain",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [
            str(row.get("scorer_id") or ""),
            str(row.get("dimension") or ""),
            str(row.get("value") or ""),
            str(row.get("cases") or 0),
            str(row.get("error_count") or 0),
            _format_percent(row.get("error_rate")),
            str(row.get("harmful_replace_count") or 0),
            str(row.get("false_abstain_count") or 0),
        ]
        lines.append("| " + " | ".join(_escape_md(value) for value in values) + " |")
    return "\n".join(lines)


def render_trusted_seed_v2_band_performance_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    breakdowns = _as_mapping(report.get("breakdowns"))
    answer = _as_mapping(report.get("answer_to_band_question"))
    lines = [
        "# en-es Semantic Veto Trusted Seed v2 Band Performance",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Unique cases: `{summary.get('unique_case_count', 0)}`",
        f"- Unique families: `{summary.get('unique_family_count', 0)}`",
        "",
        "## Answer To The Band Question",
        "",
        f"- Claim strength: `{answer.get('claim_strength', '')}`",
        f"- Main signal: {answer.get('main_signal', '')}",
        f"- Main caution: {answer.get('main_caution', '')}",
        "",
        "## Overall By Scorer",
        "",
        _metrics_table(summary.get("overall_by_scorer")),
        "",
        "## Source Band",
        "",
        _metrics_table(breakdowns.get("scorer_x_source_band")),
        "",
        "## Source Band By Case Type",
        "",
        _metrics_table(breakdowns.get("scorer_x_source_band_x_case_type")),
        "",
        "## Case Type",
        "",
        _metrics_table(breakdowns.get("scorer_x_case_type")),
        "",
        "## Approval Source",
        "",
        _metrics_table(breakdowns.get("scorer_x_approval")),
        "",
        "## Trusted Seed v2 Status",
        "",
        _metrics_table(breakdowns.get("scorer_x_trusted_seed_v2_status")),
        "",
        "## Prior Draft Comparison",
        "",
        _comparison_table(report.get("prior_comparison")),
        "",
        "## Failure Concentration",
        "",
        _failure_table(report.get("failure_concentration")),
        "",
        "## Sample Warnings",
        "",
    ]
    warnings = summary.get("sample_warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _format_signed_int(value: object) -> str:
    try:
        return f"{int(value):+d}"
    except (TypeError, ValueError):
        return "n/a"
