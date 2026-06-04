from __future__ import annotations

from typing import Mapping, Sequence


def render_semantic_veto_llm_pilot_admission_markdown(
    report: Mapping[str, object],
) -> str:
    pilot = _as_mapping(report.get("pilot"))
    candidate = _as_mapping(report.get("candidate"))
    planning = _as_mapping(report.get("planning_summary"))
    admission = _as_mapping(report.get("admission_summary"))
    alignment = _as_mapping(report.get("request_alignment"))
    split = _as_mapping(report.get("split_summary"))
    lines = [
        "# en-es Semantic Veto LLM Pilot Admission",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Plan: `{pilot.get('plan_path', '')}`",
        f"- Generation requests: `{pilot.get('generation_requests_path', '')}`",
        f"- Generated rows: `{pilot.get('generated_rows_path', '')}`",
        f"- Candidate: `{candidate.get('candidate_id', '')}`",
        f"- Runtime policy change: `{candidate.get('runtime_policy_change', '')}`",
        "",
        "## Strict Flow",
        "",
        _strict_flow_table(report),
        "",
        "## Plan Summary",
        "",
        f"- Pilot families: `{planning.get('family_count', 0)}`",
        f"- Planned rows: `{planning.get('planned_row_count', 0)}`",
        f"- Planned rows by type: `{_inline_counts(planning.get('planned_rows_by_type'))}`",
        f"- Generation strata axes: `{_inline_list(planning.get('generation_strata_axes'))}`",
        "",
        "## Admission Summary",
        "",
        f"- Generated rows present: `{admission.get('generated_rows_present', False)}`",
        f"- Generated rows: `{admission.get('generated_row_count', 0)}`",
        f"- Admitted rows: `{admission.get('admitted_row_count', 0)}`",
        f"- Rejected rows: `{admission.get('rejected_row_count', 0)}`",
        f"- Accepted rows by type: `{_inline_counts(admission.get('admitted_rows_by_type'))}`",
        "",
        "## Request Alignment",
        "",
        f"- Request packet present: `{alignment.get('request_packet_present', False)}`",
        f"- Expected rows: `{alignment.get('expected_row_count', 0)}`",
        f"- Matched rows: `{alignment.get('matched_expected_row_count', 0)}`",
        f"- Missing expected rows: `{len(_as_sequence(alignment.get('missing_expected_row_ids')))}`",
        f"- Unexpected generated rows: `{len(_as_sequence(alignment.get('unexpected_row_ids')))}`",
        "",
        "## Split Summary",
        "",
        f"- Discovery rows: `{split.get('discovery_count', 0)}`",
        f"- Locked-eval rows: `{split.get('locked_eval_count', 0)}`",
        "- Threshold tuning on locked eval: `false`",
        "",
        "## Family Coverage",
        "",
        _coverage_table(report.get("family_coverage")),
        "",
        "## Rejections",
        "",
        _rejection_table(report.get("rejected_rows")),
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _next_steps(
    *,
    generated_rows_present: bool,
    plan_issues: Sequence[Mapping[str, object]],
    rejected_rows: Sequence[Mapping[str, object]],
    coverage_shortfalls: Sequence[Mapping[str, object]],
    request_alignment_issues: Sequence[Mapping[str, object]],
) -> list[str]:
    if plan_issues:
        return [
            "Repair the pilot plan before generating rows.",
            "Do not spend LLM budget until the no-spend preflight is clean.",
        ]
    if not generated_rows_present:
        return [
            "Generate the bounded pilot rows for the configured families and strata.",
            "Run this admission harness on the generated payload before scoring anything.",
            "Keep discovery rows separate from locked-eval rows when choosing thresholds.",
        ]
    if rejected_rows:
        return [
            "Repair or discard rejected rows before scoring the generated batch.",
            "Regenerate only the missing family/type cells instead of replacing the whole pilot.",
        ]
    if request_alignment_issues:
        return [
            "Repair the generated batch so row_ids match the frozen request packet.",
            "Do not score rows that were not produced from the approved request packet.",
        ]
    if coverage_shortfalls:
        return [
            "Generate shortfall rows for the listed family/type cells.",
            "Do not treat the pilot as complete until planned coverage is admitted.",
        ]
    return [
        "Score admitted discovery and locked-eval rows with the frozen veto-only candidate.",
        "Compare product metrics against the current candidate-selection and stress lanes.",
        "Expand breadth only if locked-eval metrics stay near the product acceptance target.",
    ]


def _limitations(*, generated_rows_present: bool) -> list[str]:
    limitations = [
        "research-only lane",
        "runtime policy remains unchanged",
        "generated rows are evaluation data, not source evidence",
        "locked-eval rows cannot be used for threshold selection",
    ]
    if not generated_rows_present:
        limitations.append("no generated rows have been admitted or scored yet")
    return limitations


def _public_row(
    *,
    row: Mapping[str, object],
    admission_status: str,
) -> dict[str, object]:
    return {
        "admission_status": admission_status,
        "row_id": str(row.get("row_id") or "").strip(),
        "family_id": str(row.get("family_id") or "").strip(),
        "trigger": str(row.get("trigger") or "").strip(),
        "candidate_replacement": str(row.get("candidate_replacement") or "").strip(),
        "sentence": str(row.get("sentence") or "").strip(),
        "gold_decision": str(row.get("gold_decision") or "").strip(),
        "gold_type": str(row.get("gold_type") or "").strip(),
        "active_sense": str(row.get("active_sense") or "").strip(),
        "negative_sense": str(row.get("negative_sense") or "").strip(),
        "no_winner_reason": str(row.get("no_winner_reason") or "").strip(),
        "gold_reason": str(row.get("gold_reason") or "").strip(),
        "pos": str(row.get("pos") or "").strip(),
        "generator_id": str(row.get("generator_id") or "").strip(),
        "prompt_id": str(row.get("prompt_id") or "").strip(),
        "difficulty_tags": [str(value) for value in row.get("difficulty_tags") or ()],
    }


def _strict_flow_table(report: Mapping[str, object]) -> str:
    flow = _as_mapping(report.get("strict_flow"))
    rows = [
        ("Runtime policy change", flow.get("runtime_policy_change")),
        ("Source evidence promotion", flow.get("source_evidence_promotion")),
        (
            "Locked-eval threshold tuning",
            flow.get("threshold_tuning_allowed_on_locked_eval"),
        ),
        ("Required flow steps", len(_as_sequence(flow.get("required_flow_steps")))),
        ("Required admission filters", len(_as_sequence(flow.get("required_admission_filters")))),
    ]
    lines = ["| Check | Value |", "| --- | --- |"]
    for label, value in rows:
        lines.append(f"| {_escape_md(str(label))} | `{_escape_md(str(value))}` |")
    return "\n".join(lines)


def _coverage_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Family | Trigger | Type | Planned | Admitted | Shortfall |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        if int(row.get("shortfall_count") or 0) <= 0 and int(row.get("admitted_count") or 0) == 0:
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('family_id') or ''))}`",
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_type') or ''))}`",
                    str(row.get("planned_count") or 0),
                    str(row.get("admitted_count") or 0),
                    str(row.get("shortfall_count") or 0),
                ]
            )
            + " |"
        )
    if len(lines) == 2:
        lines.append("| _No generated rows admitted yet._ |  |  |  |  |  |")
    return "\n".join(lines)


def _rejection_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Row | Family | Type | Reasons |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows[:30]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('row_id') or ''))}`",
                    f"`{_escape_md(str(row.get('family_id') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_type') or ''))}`",
                    _escape_md(_inline_list(row.get("rejection_reasons"))),
                ]
            )
            + " |"
        )
    if not rows:
        lines.append("| _None._ |  |  |  |")
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


def _inline_counts(value: object) -> str:
    mapping = _as_mapping(value)
    return ", ".join(f"{key}: {mapping[key]}" for key in sorted(mapping)) or "none"


def _inline_list(value: object) -> str:
    values = [str(item) for item in _as_sequence(value) if str(item)]
    return ", ".join(values) or "none"


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
