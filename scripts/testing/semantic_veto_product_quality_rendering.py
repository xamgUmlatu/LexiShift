from __future__ import annotations

from typing import Mapping


def render_product_quality_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    overall = _as_mapping(summary.get("overall"))
    decision_rationale = _as_sequence(summary.get("decision_rationale"))
    pair = str(report.get("pair") or "").strip() or "unknown-pair"
    lines = [
        f"# {pair} Semantic Veto Product Quality",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Policy: `{_as_mapping(report.get('policy')).get('path', '')}`",
        f"- Cases: `{summary.get('case_count', 0)}`",
        f"- Measured lane types: `{', '.join(_as_sequence(summary.get('measured_lane_types')))}`",
        f"- Planned unmeasured lane types: "
        f"`{', '.join(_as_sequence(summary.get('planned_unmeasured_lane_types')))}`",
        "",
        "## Overall Product Metrics",
        "",
        _metric_table([overall]),
        "",
        "## Baselines",
        "",
        _baseline_table(overall),
        "",
        "## Lanes",
        "",
        _lane_table(report.get("lanes")),
        "",
        "## Suite Breakdowns",
        "",
        _metric_table(report.get("suite_breakdowns")),
        "",
        "## Failure Rows",
        "",
        _failure_table(report.get("failure_rows")),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in decision_rationale)
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _metric_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        checks = _as_mapping(row.get("target_checks"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("scope_id") or "overall")),
                    str(row.get("case_count", 0)),
                    str(row.get("positive_case_count", 0)),
                    str(row.get("negative_case_count", 0)),
                    str(row.get("positive_allow_count", 0)),
                    _format_percent(row.get("positive_allow_rate")),
                    str(row.get("negative_abstain_count", 0)),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("negative_allow_count", 0)),
                    str(row.get("utility_score", 0)),
                    _escape_md(str(checks.get("target_status") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _baseline_table(metrics: Mapping[str, object]) -> str:
    baselines = _as_mapping(metrics.get("baselines"))
    rows = [
        _as_mapping(baselines.get("lexical_allow_all")),
        _as_mapping(baselines.get("abstain_all")),
    ]
    lines = [
        "| Baseline | Utility | Utility/case | Positive allow rate | Negative abstain rate | Delta current utility |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    current = _safe_float(metrics.get("utility_score"))
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("baseline_id") or "")),
                    str(row.get("utility_score", 0)),
                    str(row.get("utility_per_case", 0)),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(_round4(current - _safe_float(row.get("utility_score")))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _lane_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No lanes configured._"
    lines = [
        "| Lane | Type | Cases | Pos allow rate | Neg abstain rate | Utility | Target | Interpretation |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        metrics = _as_mapping(row.get("metrics"))
        checks = _as_mapping(metrics.get("target_checks"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("lane_id") or "")),
                    _escape_md(str(row.get("lane_type") or "")),
                    str(metrics.get("case_count", 0)),
                    _format_percent(metrics.get("positive_allow_rate")),
                    _format_percent(metrics.get("negative_abstain_rate")),
                    str(metrics.get("utility_score", 0)),
                    _escape_md(str(checks.get("target_status") or "")),
                    _escape_md(str(row.get("interpretation") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No product failures in measured lanes._"
    lines = [
        "| Case | Suite | Trigger | Outcome | Error | Sentence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("case_id") or "")),
                    _escape_md(str(row.get("suite_id") or "")),
                    _escape_md(str(row.get("trigger") or "")),
                    _escape_md(str(row.get("product_outcome") or "")),
                    _escape_md(str(row.get("error_type") or "")),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _round4(value: float) -> float:
    return round(float(value), 4)


def _format_percent(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_safe_float(value) * 100:.1f}%"


def _escape_md(value: str) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
