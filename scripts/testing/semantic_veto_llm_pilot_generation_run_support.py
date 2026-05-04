from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def render_generation_run_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    artifacts = _as_mapping(report.get("artifacts"))
    lines = [
        "# en-es Semantic Veto LLM Pilot Generation Run",
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
        f"- Accepted rows: `{summary.get('accepted_row_count', 0)}`",
        f"- API errors: `{summary.get('api_error_count', 0)}`",
        f"- Invalid outputs: `{summary.get('invalid_output_count', 0)}`",
        f"- Input tokens: `{summary.get('input_tokens', 0)}`",
        f"- Output tokens: `{summary.get('output_tokens', 0)}`",
        f"- Rows by type: `{_inline_counts(summary.get('accepted_rows_by_gold_type'))}`",
        "",
        "## Artifacts",
        "",
        f"- Journal: `{artifacts.get('journal_jsonl', 'n/a')}`",
        f"- Raw responses: `{artifacts.get('raw_response_bundle_json', 'n/a')}`",
        f"- Generated rows: `{artifacts.get('generated_rows_json', 'n/a')}`",
        "",
        "## Request Outcomes",
        "",
        "| Request | Row | Family | Type | Status | Sentence / Error |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in _mapping_rows(report.get("request_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('request_id') or ''))}`",
                    f"`{_escape_md(str(row.get('row_id') or ''))}`",
                    f"`{_escape_md(str(row.get('family_id') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_type') or ''))}`",
                    f"`{_escape_md(str(row.get('status') or ''))}`",
                    _escape_md(_row_output(row)),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _request_started_event(
    *,
    batch_id: str,
    generated_at: str,
    request_row: Mapping[str, object],
    model_id: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_type": "request_started",
        "batch_id": batch_id,
        "generated_at": generated_at,
        "request_id": str(request_row.get("request_id") or ""),
        "expected_row_id": str(request_row.get("expected_row_id") or ""),
        "family_id": str(request_row.get("family_id") or ""),
        "gold_type": str(request_row.get("gold_type") or ""),
        "model_id": model_id,
    }


def _request_outcome_event(
    *,
    batch_id: str,
    generated_at: str,
    request_id: str,
    raw_request_row: Mapping[str, object],
    summary_row: Mapping[str, object],
    generated_row: Mapping[str, object] | None,
) -> dict[str, object]:
    event: dict[str, object] = {
        "schema_version": 1,
        "event_type": "request_outcome",
        "batch_id": batch_id,
        "generated_at": generated_at,
        "request_id": request_id,
        "raw_request_row": dict(raw_request_row),
        "summary_row": dict(summary_row),
    }
    if isinstance(generated_row, Mapping):
        event["generated_row"] = dict(generated_row)
    return event


def _prepare_generation_journal(
    *,
    journal_path: Path,
    batch_id: str,
    resume: bool,
    selected_request_rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    if not journal_path.exists():
        if resume:
            raise ValueError(
                f"Resume requested but journal does not exist: {_display_path(journal_path)}"
            )
        return {}
    if not resume:
        raise ValueError(
            f"Live journal already exists: {_display_path(journal_path)}. "
            "Use --resume to continue this exact run or choose a new --run-id."
        )
    journal_state = _load_generation_journal_state(journal_path)
    if journal_state["batch_id"] and journal_state["batch_id"] != batch_id:
        raise ValueError(
            f"Journal batch id {journal_state['batch_id']!r} did not match current batch id {batch_id!r}."
        )
    if journal_state["ambiguous_request_ids"]:
        ambiguous = ", ".join(sorted(journal_state["ambiguous_request_ids"]))
        raise ValueError(
            "Journal contains started requests without recorded outcomes; refusing resume to avoid "
            f"duplicate spend. Inspect {_display_path(journal_path)} and resolve: {ambiguous}"
        )
    selected_request_ids = {
        str(row.get("request_id") or "").strip()
        for row in selected_request_rows
        if str(row.get("request_id") or "").strip()
    }
    prior_request_ids = set(journal_state["outcomes_by_request_id"].keys())
    extra_request_ids = sorted(prior_request_ids - selected_request_ids)
    if extra_request_ids:
        raise ValueError(
            "Journal contains outcomes for request ids outside the current selection; refusing resume: "
            + ", ".join(extra_request_ids)
        )
    return journal_state["outcomes_by_request_id"]


def _load_generation_journal_state(journal_path: Path) -> dict[str, object]:
    batch_id = ""
    started_request_ids: list[str] = []
    outcomes_by_request_id: dict[str, dict[str, object]] = {}
    with journal_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Journal {_display_path(journal_path)} contains malformed JSON on line {line_number}: {exc}"
                ) from exc
            if not isinstance(event, Mapping):
                raise ValueError(
                    f"Journal {_display_path(journal_path)} contains a non-object event on line {line_number}."
                )
            event_batch_id = str(event.get("batch_id") or "").strip()
            if event_batch_id:
                if not batch_id:
                    batch_id = event_batch_id
                elif batch_id != event_batch_id:
                    raise ValueError(
                        f"Journal {_display_path(journal_path)} mixes batch ids {batch_id!r} and {event_batch_id!r}."
                    )
            event_type = str(event.get("event_type") or "").strip()
            request_id = str(event.get("request_id") or "").strip()
            if event_type == "request_started":
                if request_id:
                    started_request_ids.append(request_id)
                continue
            if event_type != "request_outcome":
                raise ValueError(
                    f"Journal {_display_path(journal_path)} contains unknown event_type {event_type!r} on line {line_number}."
                )
            if not request_id:
                raise ValueError(
                    f"Journal {_display_path(journal_path)} contains an outcome without request_id on line {line_number}."
                )
            raw_request_row = event.get("raw_request_row")
            summary_row = event.get("summary_row")
            generated_row = event.get("generated_row")
            if not isinstance(raw_request_row, Mapping) or not isinstance(summary_row, Mapping):
                raise ValueError(
                    f"Journal {_display_path(journal_path)} is missing raw_request_row or summary_row for {request_id!r}."
                )
            if request_id in outcomes_by_request_id:
                existing = outcomes_by_request_id[request_id]
                existing_status = str(_as_mapping(existing.get("summary_row")).get("status") or "")
                next_status = str(summary_row.get("status") or "")
                if existing_status == "accepted" or next_status != "accepted":
                    raise ValueError(
                        f"Journal {_display_path(journal_path)} contains duplicate outcomes "
                        f"for request {request_id!r}."
                    )
            entry = {
                "raw_request_row": dict(raw_request_row),
                "summary_row": dict(summary_row),
            }
            if isinstance(generated_row, Mapping):
                entry["generated_row"] = dict(generated_row)
            outcomes_by_request_id[request_id] = entry
    ambiguous_request_ids = sorted(
        request_id for request_id in started_request_ids if request_id not in outcomes_by_request_id
    )
    return {
        "batch_id": batch_id,
        "ambiguous_request_ids": ambiguous_request_ids,
        "outcomes_by_request_id": outcomes_by_request_id,
    }


def _should_retry_prior_outcome(
    *,
    prior_outcome: Mapping[str, object],
    retry_invalid_outputs: bool,
) -> bool:
    if not retry_invalid_outputs:
        return False
    summary_row = _as_mapping(prior_outcome.get("summary_row"))
    return str(summary_row.get("status") or "") == "invalid_output"


def _inline_counts(value: object) -> str:
    mapping = _as_mapping(value)
    return ", ".join(f"{key}: {mapping[key]}" for key in sorted(mapping)) or "none"


def _row_output(row: Mapping[str, object]) -> str:
    if str(row.get("status") or "") == "accepted":
        return _truncate(str(row.get("sentence") or ""))
    return _truncate(str(row.get("error_message") or "n/a"))


def _truncate(value: str, *, limit: int = 140) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text or "n/a"
    return text[: limit - 3].rstrip() + "..."


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
