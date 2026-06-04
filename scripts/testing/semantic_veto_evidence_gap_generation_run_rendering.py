from __future__ import annotations

from typing import Mapping

from semantic_veto_evidence_gap_generation_run_core import _as_mapping, _mapping_rows


def render_evidence_gap_generation_run_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    admission = _as_mapping(report.get("admission_preview"))
    artifacts = _as_mapping(report.get("artifacts"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Generation Run",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Execution mode: `{report.get('execution_mode', '')}`",
        f"- Batch id: `{report.get('batch_id', '')}`",
        f"- Pilot id: `{report.get('pilot_id', '')}`",
        f"- Prompt id: `{report.get('prompt_id', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Selected requests: `{summary.get('selected_request_count', 0)}`",
        f"- Accepted responses: `{summary.get('accepted_response_count', 0)}`",
        f"- Accepted generated items: `{summary.get('accepted_generated_item_count', 0)}`",
        f"- API errors: `{summary.get('api_error_count', 0)}`",
        f"- Invalid outputs: `{summary.get('invalid_output_count', 0)}`",
        f"- Input tokens: `{summary.get('input_tokens', 0)}`",
        f"- Output tokens: `{summary.get('output_tokens', 0)}`",
        f"- Accepted responses by arm: `{_inline_counts(summary.get('accepted_responses_by_arm'))}`",
        f"- Accepted items by slot: `{_inline_counts(summary.get('accepted_items_by_slot_type'))}`",
        "",
        "## Admission Preview",
        "",
        f"- Admission status: `{admission.get('status', '')}`",
        f"- Admission decision: `{admission.get('decision', '')}`",
        f"- Admitted items: `{admission.get('admitted_item_count', 0)}`",
        f"- Rejected items: `{admission.get('rejected_item_count', 0)}`",
        f"- Waived items: `{admission.get('coverage_waived_item_count', 0)}`",
        f"- Coverage shortfall: `{admission.get('coverage_shortfall_count', 0)}`",
        "",
        "## Artifacts",
        "",
        f"- Run manifest: `{artifacts.get('run_manifest_json', 'n/a')}`",
        f"- Request queue: `{artifacts.get('request_queue_jsonl', 'n/a')}`",
        f"- Journal: `{artifacts.get('journal_jsonl', 'n/a')}`",
        f"- Raw responses JSONL: `{artifacts.get('raw_responses_jsonl', 'n/a')}`",
        f"- Failures JSONL: `{artifacts.get('failures_jsonl', 'n/a')}`",
        f"- Raw response bundle: `{artifacts.get('raw_response_bundle_json', 'n/a')}`",
        f"- Generated responses: `{artifacts.get('generated_responses_json', 'n/a')}`",
        "",
        "## Request Outcomes",
        "",
        "| Request | Arm | Slot | Status | Items | Output / Error |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("request_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('request_id') or ''))}`",
                    f"`{_escape_md(str(row.get('pilot_arm') or ''))}`",
                    f"`{_escape_md(str(row.get('slot_type') or ''))}`",
                    f"`{_escape_md(str(row.get('status') or ''))}`",
                    str(row.get("item_count") or 0),
                    _escape_md(_row_output(row)),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _first_sentence(response: Mapping[str, object]) -> str:
    items = _mapping_rows(response.get("items"))
    if not items:
        return ""
    return str(items[0].get("sentence") or "")


def _row_output(row: Mapping[str, object]) -> str:
    if str(row.get("status") or "") == "accepted":
        return _truncate(str(row.get("first_sentence") or ""))
    return _truncate(str(row.get("error_message") or "n/a"))


def _truncate(value: str, *, limit: int = 140) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text or "n/a"
    return text[: limit - 3].rstrip() + "..."


def _inline_counts(value: object) -> str:
    mapping = _as_mapping(value)
    return ", ".join(f"{key}: {mapping[key]}" for key in sorted(mapping)) or "none"


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
