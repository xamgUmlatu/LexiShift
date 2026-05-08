from __future__ import annotations

from typing import Mapping

from semantic_veto_evidence_gap_generation_admission_core import (
    _as_mapping,
    _as_sequence,
    _mapping_rows,
)


def render_evidence_gap_generation_admission_markdown(report: Mapping[str, object]) -> str:
    pilot = _as_mapping(report.get("pilot"))
    summary = _as_mapping(report.get("summary"))
    alignment = _as_mapping(report.get("alignment"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Generation Admission",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Requests: `{pilot.get('generation_requests_path', '')}`",
        f"- Generated responses: `{pilot.get('generated_responses_path', '')}`",
        f"- Generated responses present: `{pilot.get('generated_responses_present', False)}`",
        "",
        "## Summary",
        "",
        f"- Expected requests: `{summary.get('expected_request_count', 0)}`",
        f"- Generated responses: `{summary.get('generated_response_count', 0)}`",
        f"- Expected items: `{summary.get('expected_item_count', 0)}`",
        f"- Admitted items: `{summary.get('admitted_item_count', 0)}`",
        f"- Rejected items: `{summary.get('rejected_item_count', 0)}`",
        f"- Waived items: `{summary.get('coverage_waived_item_count', 0)}`",
        f"- Coverage shortfall: `{summary.get('coverage_shortfall_count', 0)}`",
        "",
        "## Alignment",
        "",
        f"- Matched expected requests: `{alignment.get('matched_expected_request_count', 0)}`",
        f"- Missing expected requests: `{len(_as_sequence(alignment.get('missing_expected_request_ids')))}`",
        f"- Unexpected response requests: `{len(_as_sequence(alignment.get('unexpected_response_request_ids')))}`",
        "",
        "## Arm Summary",
        "",
        "| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm, row in _as_mapping(summary.get("by_arm")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(arm))}` | {row_map.get('expected_request_count', 0)} | "
            f"{row_map.get('expected_item_count', 0)} | {row_map.get('admitted_item_count', 0)} | "
            f"{row_map.get('rejected_item_count', 0)} | {row_map.get('waived_item_count', 0)} | "
            f"{row_map.get('shortfall_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Slot Summary",
            "",
            "| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for slot_type, row in _as_mapping(summary.get("by_slot_type")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(slot_type))}` | {row_map.get('expected_request_count', 0)} | "
            f"{row_map.get('expected_item_count', 0)} | {row_map.get('admitted_item_count', 0)} | "
            f"{row_map.get('rejected_item_count', 0)} | {row_map.get('waived_item_count', 0)} | "
            f"{row_map.get('shortfall_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Rejection Reasons",
            "",
            _rejection_table(report.get("rejection_reasons")),
            "",
            "## Coverage Samples",
            "",
            _coverage_table(report.get("coverage")),
            "",
            "## Next Steps",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _coverage_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No coverage rows._"
    lines = [
        "| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    visible = [
        row
        for row in rows
        if int(row.get("shortfall_count") or 0) > 0
        or int(row.get("waived_item_count") or 0) > 0
        or int(row.get("admitted_item_count") or 0) > 0
    ][:24]
    if not visible:
        visible = rows[:12]
    for row in visible:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('request_id') or ''))}`",
                    f"`{_escape_md(str(row.get('pilot_arm') or ''))}`",
                    f"`{_escape_md(str(row.get('slot_type') or ''))}`",
                    str(row.get("expected_item_count") or 0),
                    str(row.get("admitted_item_count") or 0),
                    str(row.get("waived_item_count") or 0),
                    str(row.get("shortfall_count") or 0),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _rejection_table(value: object) -> str:
    rows = _as_mapping(value)
    if not rows:
        return "_None._"
    lines = ["| Reason | Count |", "| --- | ---: |"]
    for reason, count in sorted(rows.items()):
        lines.append(f"| `{_escape_md(str(reason))}` | {count} |")
    return "\n".join(lines)


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
