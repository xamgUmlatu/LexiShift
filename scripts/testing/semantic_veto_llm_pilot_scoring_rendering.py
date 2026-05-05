from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _as_mapping, _escape_md, _format_percent


def render_semantic_veto_llm_pilot_scoring_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    overall = _as_mapping(summary.get("overall"))
    target = _as_mapping(overall.get("target_checks"))
    lines = [
        "# en-es Semantic Veto LLM Pilot Scoring",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Admitted rows: `{summary.get('admitted_row_count', 0)}`",
        f"- Scored cases: `{summary.get('scored_case_count', 0)}`",
        f"- Scoreable families: `{summary.get('scoreable_family_count', 0)}` / `{summary.get('family_count', 0)}`",
        f"- Product target: `{target.get('target_status', '')}`",
        f"- Positive allow / negative abstain: `{_format_percent(overall.get('positive_allow_rate'))}` / `{_format_percent(overall.get('negative_abstain_rate'))}`",
        f"- Utility: `{overall.get('utility_score', '')}`",
        "",
        "## Candidate",
        "",
        _mapping_table(report.get("candidate")),
        "",
        "## Strict Flow Checks",
        "",
        _mapping_table(report.get("strict_flow")),
        "",
        "## Source Evidence",
        "",
        _mapping_table(report.get("source_evidence")),
        "",
        "## Leakage Checks",
        "",
        _mapping_table(report.get("leakage_checks")),
        "",
        "## Split Breakdown",
        "",
        _metrics_table(report.get("split_breakdowns"), "split"),
        "",
        "## Gold Type Breakdown",
        "",
        _metrics_table(report.get("gold_type_breakdowns"), "gold_type"),
        "",
        "## Family Coverage",
        "",
        _coverage_table(report.get("coverage_rows")),
        "",
        "## Failure Rows",
        "",
        _failure_table(report.get("failure_rows")),
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _mapping_table(value: object) -> str:
    mapping = _as_mapping(value)
    if not mapping:
        return "_No values._"
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, raw_value in mapping.items():
        if isinstance(raw_value, (list, tuple)):
            rendered = ", ".join(str(item) for item in raw_value)
        else:
            rendered = str(raw_value)
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _metrics_table(value: object, label: str) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        f"| {label} | Cases | Pos allow | Neg abstain | Pos allow rate | Neg abstain rate | Utility | Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        target = _as_mapping(row.get("target_checks"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("scope_id") or "")),
                    str(row.get("case_count", 0)),
                    str(row.get("positive_allow_count", 0)),
                    str(row.get("negative_abstain_count", 0)),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("utility_score", "")),
                    _escape_md(str(target.get("target_status") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _coverage_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No coverage rows._"
    lines = [
        "| Family | Pilot rows | Active | Shadow | Phrase | Scoreable | Missing |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("family_id") or "")),
                    str(row.get("pilot_row_count", 0)),
                    str(row.get("active_example_count", 0)),
                    str(row.get("shadow_example_count", 0)),
                    str(row.get("phrase_control_example_count", 0)),
                    "yes" if bool(row.get("scoreable")) else "no",
                    _escape_md(
                        ", ".join(str(v) for v in _as_sequence(row.get("missing_requirements")))
                    ),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No failure rows._"
    lines = [
        "| Case | Split | Gold | Trigger | Outcome | Reason | Active | Shadow | Phrase | Sentence |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:36]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("case_id") or "")),
                    _escape_md(str(row.get("split") or "")),
                    _escape_md(str(row.get("gold_type") or "")),
                    _escape_md(str(row.get("trigger") or "")),
                    _escape_md(str(row.get("product_outcome") or "")),
                    _escape_md(str(row.get("veto_reason") or "")),
                    str(row.get("active_score", "")),
                    str(row.get("strongest_shadow_score", "")),
                    str(row.get("phrase_control_score", "")),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []
