from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping, Sequence

from semantic_llm_prompt_bakeoff_common import _display_path


def _prepare_live_journal(
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
    journal_state = _load_journal_state(journal_path)
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


def _load_journal_state(journal_path: Path) -> dict[str, object]:
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
            if request_id in outcomes_by_request_id:
                raise ValueError(
                    f"Journal {_display_path(journal_path)} contains duplicate outcomes for request {request_id!r}."
                )
            raw_request_row = event.get("raw_request_row")
            summary_row = event.get("summary_row")
            intake_item = event.get("intake_item")
            if not isinstance(raw_request_row, Mapping) or not isinstance(summary_row, Mapping):
                raise ValueError(
                    f"Journal {_display_path(journal_path)} is missing raw_request_row or summary_row for {request_id!r}."
                )
            entry = {
                "raw_request_row": dict(raw_request_row),
                "summary_row": dict(summary_row),
            }
            if isinstance(intake_item, Mapping):
                entry["intake_item"] = dict(intake_item)
            outcomes_by_request_id[request_id] = entry
    ambiguous_request_ids = sorted(
        request_id for request_id in started_request_ids if request_id not in outcomes_by_request_id
    )
    return {
        "batch_id": batch_id,
        "ambiguous_request_ids": ambiguous_request_ids,
        "outcomes_by_request_id": outcomes_by_request_id,
    }


def _append_journal_event(*, journal_path: Path, event: Mapping[str, object]) -> None:
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(event), ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _build_request_started_event(
    *,
    batch_id: str,
    generated_at: str,
    request_row: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_type": "request_started",
        "batch_id": batch_id,
        "generated_at": generated_at,
        "request_id": str(request_row.get("request_id") or "").strip(),
        "prompt_slot": str(request_row.get("prompt_slot") or "").strip(),
        "family_id": str(request_row.get("family_id") or "").strip(),
        "model_id": str(request_row.get("model_id") or "").strip(),
    }


def _build_request_outcome_event(
    *,
    batch_id: str,
    generated_at: str,
    request_id: str,
    raw_request_row: Mapping[str, object],
    summary_row: Mapping[str, object],
    intake_item: Mapping[str, object] | None,
) -> dict[str, object]:
    event = {
        "schema_version": 1,
        "event_type": "request_outcome",
        "batch_id": batch_id,
        "generated_at": generated_at,
        "request_id": request_id,
        "raw_request_row": dict(raw_request_row),
        "summary_row": dict(summary_row),
    }
    if isinstance(intake_item, Mapping):
        event["intake_item"] = dict(intake_item)
    return event
