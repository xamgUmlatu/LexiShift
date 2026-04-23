#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Mapping, Sequence


def render_prompt_smoke_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    slot_rows = _coerce_rows(report.get("slot_rows"))
    sample_requests = _coerce_rows(report.get("sample_requests"))

    lines = [
        "# en-es Semantic LLM Prompt Smoke",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Prompt spec: `{report.get('prompt_spec_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Stage: `{report.get('stage', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Temperature: `{report.get('selected_temperature', '')}`",
        "",
        "## Summary",
        "",
        f"- Active slots: `{summary.get('active_slot_count', 0)}`",
        f"- Prompt requests: `{summary.get('request_count', 0)}`",
        f"- Target families covered: `{summary.get('target_family_count', 0)}`",
        f"- Negative controls held out of prompting: `{summary.get('negative_control_count', 0)}`",
        "",
        "## Slot Matrix",
        "",
        "| Slot | Status | Target Families | Requests | Notes |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in slot_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('status', '')}`",
                    str(int(row.get("target_family_count") or 0)),
                    str(int(row.get("request_count") or 0)),
                    _render_notes(row.get("notes")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Sample Requests",
            "",
        ]
    )
    for row in sample_requests:
        lines.extend(
            [
                f"### `{row.get('request_id', '')}`",
                "",
                f"- Slot: `{row.get('prompt_slot', '')}`",
                f"- Family: `{row.get('family_id', '')}`",
                f"- Trigger: `{row.get('trigger', '')}`",
                f"- Active -> Candidate: `{row.get('active_target', '')}` -> `{row.get('candidate_target', '')}`",
                f"- Model: `{row.get('model_id', '')}` @ temperature `{row.get('temperature', '')}`",
                "",
                "System prompt:",
                "",
                "```text",
                str(row.get("system_prompt") or "").strip(),
                "```",
                "",
                "User prompt:",
                "",
                "```text",
                str(row.get("user_prompt") or "").strip(),
                "```",
                "",
                "Expected row preview:",
                "",
                "```json",
                _render_json_preview(row.get("expected_row_preview")),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _coerce_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _render_notes(value: object) -> str:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        notes = [str(item).strip() for item in value if str(item).strip()]
        return "<br>".join(notes) if notes else "n/a"
    text = str(value or "").strip()
    return text or "n/a"


def _render_json_preview(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) if isinstance(value, Mapping) else "{}"
