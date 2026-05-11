from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from semantic_llm_prompt_bakeoff_en_es import _append_journal_event, _display_path


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
            event = json.loads(line)
            if not isinstance(event, Mapping):
                raise ValueError(f"Journal event on line {line_number} is not an object.")
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
                    f"Unknown journal event_type {event_type!r} on line {line_number}."
                )
            raw_request_row = event.get("raw_request_row")
            summary_row = event.get("summary_row")
            generated_response = event.get("generated_response")
            if (
                not request_id
                or not isinstance(raw_request_row, Mapping)
                or not isinstance(summary_row, Mapping)
            ):
                raise ValueError(f"Malformed journal outcome on line {line_number}.")
            if request_id in outcomes_by_request_id:
                existing = outcomes_by_request_id[request_id]
                existing_status = str(_as_mapping(existing.get("summary_row")).get("status") or "")
                if existing_status == "accepted":
                    raise ValueError(f"Duplicate journal outcome for {request_id!r}.")
            entry = {
                "raw_request_row": dict(raw_request_row),
                "summary_row": dict(summary_row),
            }
            if isinstance(generated_response, Mapping):
                entry["generated_response"] = dict(generated_response)
            outcomes_by_request_id[request_id] = entry
    ambiguous_request_ids = sorted(
        request_id for request_id in started_request_ids if request_id not in outcomes_by_request_id
    )
    return {
        "batch_id": batch_id,
        "ambiguous_request_ids": ambiguous_request_ids,
        "outcomes_by_request_id": outcomes_by_request_id,
    }


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
        "family_id": str(request_row.get("family_id") or ""),
        "slot_id": str(request_row.get("slot_id") or ""),
        "slot_type": str(request_row.get("slot_type") or ""),
        "model_id": model_id,
    }


def _request_outcome_event(
    *,
    batch_id: str,
    generated_at: str,
    request_id: str,
    raw_request_row: Mapping[str, object],
    summary_row: Mapping[str, object],
    generated_response: Mapping[str, object] | None,
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
    if isinstance(generated_response, Mapping):
        event["generated_response"] = dict(generated_response)
    return event


def _prepare_live_run_artifacts(
    *,
    run_manifest_path: Path,
    request_queue_path: Path,
    raw_responses_jsonl_path: Path,
    failures_path: Path,
    batch_id: str,
    pair: str,
    pilot: Mapping[str, object],
    prompt_id: str,
    generated_at: str,
    model_id: str,
    temperature: float | None,
    execution_mode: str,
    replay_source: str,
    request_payload: Mapping[str, object],
    selected_requests: Sequence[Mapping[str, object]],
    resume: bool,
    artifacts: Mapping[str, object],
) -> None:
    selected_request_hash = _stable_json_hash(selected_requests)
    if run_manifest_path.exists() and resume:
        _validate_existing_run_manifest(
            run_manifest_path=run_manifest_path,
            batch_id=batch_id,
            selected_request_hash=selected_request_hash,
        )
    elif run_manifest_path.exists():
        raise ValueError(
            f"Run manifest already exists: {_display_path(run_manifest_path)}. "
            "Use --resume for the same run or choose a new --run-id."
        )

    for path in (request_queue_path, raw_responses_jsonl_path, failures_path):
        if path.exists() and not resume:
            raise ValueError(
                f"Run artifact already exists: {_display_path(path)}. "
                "Use --resume for the same run or choose a new --run-id."
            )

    if not request_queue_path.exists():
        _write_jsonl_atomic(
            request_queue_path,
            _request_queue_events(
                batch_id=batch_id,
                generated_at=generated_at,
                selected_requests=selected_requests,
            ),
        )
    if not run_manifest_path.exists():
        _write_json_atomic(
            run_manifest_path,
            _started_run_manifest(
                batch_id=batch_id,
                pair=pair,
                pilot=pilot,
                prompt_id=prompt_id,
                generated_at=generated_at,
                model_id=model_id,
                temperature=temperature,
                execution_mode=execution_mode,
                replay_source=replay_source,
                request_payload=request_payload,
                selected_requests=selected_requests,
                artifacts=artifacts,
            ),
        )


def _append_live_run_outcome(
    *,
    raw_responses_jsonl_path: Path,
    failures_path: Path,
    batch_id: str,
    generated_at: str,
    request_id: str,
    raw_request_row: Mapping[str, object],
    summary_row: Mapping[str, object],
    generated_response: object,
) -> None:
    response_event = _raw_response_event(
        batch_id=batch_id,
        generated_at=generated_at,
        request_id=request_id,
        raw_request_row=raw_request_row,
        summary_row=summary_row,
        generated_response=generated_response,
    )
    _append_journal_event(journal_path=raw_responses_jsonl_path, event=response_event)
    if str(summary_row.get("status") or "") != "accepted":
        _append_journal_event(
            journal_path=failures_path,
            event=_failure_event(
                batch_id=batch_id,
                generated_at=generated_at,
                request_id=request_id,
                raw_request_row=raw_request_row,
                summary_row=summary_row,
                generated_response=generated_response,
            ),
        )


def _run_artifact_refs(
    *,
    journal_path: Path,
    raw_response_bundle_path: Path,
    generated_responses_path: Path,
    run_manifest_path: Path,
    request_queue_path: Path,
    raw_responses_jsonl_path: Path,
    failures_path: Path,
) -> dict[str, object]:
    return {
        "journal_jsonl": _display_path(journal_path),
        "run_manifest_json": _display_path(run_manifest_path),
        "request_queue_jsonl": _display_path(request_queue_path),
        "raw_responses_jsonl": _display_path(raw_responses_jsonl_path),
        "failures_jsonl": _display_path(failures_path),
        "raw_response_bundle_json": _display_path(raw_response_bundle_path),
        "generated_responses_json": _display_path(generated_responses_path),
    }


def _started_run_manifest(
    *,
    batch_id: str,
    pair: str,
    pilot: Mapping[str, object],
    prompt_id: str,
    generated_at: str,
    model_id: str,
    temperature: float | None,
    execution_mode: str,
    replay_source: str,
    request_payload: Mapping[str, object],
    selected_requests: Sequence[Mapping[str, object]],
    artifacts: Mapping[str, object],
) -> dict[str, object]:
    request_payload_ref = str(request_payload.get("_request_json_path") or "").strip()
    return {
        "schema_version": 1,
        "manifest_kind": "semantic_veto_evidence_gap_generation_run",
        "status": "started",
        "batch_id": batch_id,
        "pair": pair,
        "pilot_id": str(pilot.get("pilot_id") or "").strip(),
        "prompt_id": prompt_id,
        "execution_mode": execution_mode,
        "replay_source": replay_source,
        "generated_at": generated_at,
        "selected_model_id": model_id,
        "selected_temperature": temperature,
        "source_request_packet": request_payload_ref,
        "source_request_packet_hash": _stable_json_hash(request_payload),
        "selected_request_count": len(selected_requests),
        "selected_request_hash": _stable_json_hash(selected_requests),
        "artifacts": dict(artifacts),
    }


def _final_run_manifest(
    *,
    report: Mapping[str, object],
    request_queue_events: Sequence[Mapping[str, object]],
    artifacts: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest_kind": "semantic_veto_evidence_gap_generation_run",
        "status": str(report.get("status") or ""),
        "batch_id": str(report.get("batch_id") or ""),
        "pair": str(report.get("pair") or ""),
        "pilot_id": str(report.get("pilot_id") or ""),
        "prompt_id": str(report.get("prompt_id") or ""),
        "execution_mode": str(report.get("execution_mode") or ""),
        "replay_source": str(report.get("replay_source") or ""),
        "generated_at": str(report.get("generated_at") or ""),
        "selected_model_id": str(report.get("selected_model_id") or ""),
        "selected_temperature": report.get("selected_temperature"),
        "selected_request_count": len(request_queue_events),
        "selected_request_hash": _stable_json_hash(
            [event.get("request_row") for event in request_queue_events]
        ),
        "summary": dict(_as_mapping(report.get("summary"))),
        "artifacts": dict(artifacts),
    }


def _validate_existing_run_manifest(
    *,
    run_manifest_path: Path,
    batch_id: str,
    selected_request_hash: str,
) -> None:
    payload = _load_json(run_manifest_path)
    if str(payload.get("batch_id") or "").strip() != batch_id:
        raise ValueError(
            f"Run manifest {_display_path(run_manifest_path)} does not match batch id {batch_id!r}."
        )
    if str(payload.get("selected_request_hash") or "").strip() != selected_request_hash:
        raise ValueError(
            f"Run manifest {_display_path(run_manifest_path)} does not match current request selection."
        )


def _request_queue_events(
    *,
    batch_id: str,
    generated_at: str,
    selected_requests: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for row in selected_requests:
        events.append(
            {
                "schema_version": 1,
                "event_type": "request_queued",
                "batch_id": batch_id,
                "generated_at": generated_at,
                "request_id": str(row.get("request_id") or "").strip(),
                "request_row": dict(row),
            }
        )
    return events


def _raw_response_events(
    *,
    batch_id: str,
    generated_at: str,
    raw_request_rows: Sequence[Mapping[str, object]],
    request_outcomes: Sequence[Mapping[str, object]],
    generated_responses: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    outcomes_by_id = {str(row.get("request_id") or "").strip(): row for row in request_outcomes}
    generated_by_id = {str(row.get("request_id") or "").strip(): row for row in generated_responses}
    events: list[dict[str, object]] = []
    for row in raw_request_rows:
        request_id = str(row.get("request_id") or "").strip()
        events.append(
            _raw_response_event(
                batch_id=batch_id,
                generated_at=generated_at,
                request_id=request_id,
                raw_request_row=row,
                summary_row=outcomes_by_id.get(request_id, {}),
                generated_response=generated_by_id.get(request_id),
            )
        )
    return events


def _failure_events(
    *,
    batch_id: str,
    generated_at: str,
    raw_request_rows: Sequence[Mapping[str, object]],
    request_outcomes: Sequence[Mapping[str, object]],
    generated_responses: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    raw_by_id = {str(row.get("request_id") or "").strip(): row for row in raw_request_rows}
    generated_by_id = {str(row.get("request_id") or "").strip(): row for row in generated_responses}
    events: list[dict[str, object]] = []
    for row in request_outcomes:
        if str(row.get("status") or "") == "accepted":
            continue
        request_id = str(row.get("request_id") or "").strip()
        events.append(
            _failure_event(
                batch_id=batch_id,
                generated_at=generated_at,
                request_id=request_id,
                raw_request_row=raw_by_id.get(request_id, {}),
                summary_row=row,
                generated_response=generated_by_id.get(request_id),
            )
        )
    return events


def _raw_and_failure_events_from_journal(
    journal_path: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    raw_events: list[dict[str, object]] = []
    failure_events: list[dict[str, object]] = []
    with journal_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            event = json.loads(line)
            if not isinstance(event, Mapping):
                continue
            if str(event.get("event_type") or "") != "request_outcome":
                continue
            raw_request_row = _as_mapping(event.get("raw_request_row"))
            summary_row = _as_mapping(event.get("summary_row"))
            generated_response = event.get("generated_response")
            request_id = str(event.get("request_id") or "").strip()
            batch_id = str(event.get("batch_id") or "").strip()
            generated_at = str(event.get("generated_at") or "").strip()
            raw_events.append(
                _raw_response_event(
                    batch_id=batch_id,
                    generated_at=generated_at,
                    request_id=request_id,
                    raw_request_row=raw_request_row,
                    summary_row=summary_row,
                    generated_response=generated_response,
                )
            )
            if str(summary_row.get("status") or "") != "accepted":
                failure_events.append(
                    _failure_event(
                        batch_id=batch_id,
                        generated_at=generated_at,
                        request_id=request_id,
                        raw_request_row=raw_request_row,
                        summary_row=summary_row,
                        generated_response=generated_response,
                    )
                )
    return raw_events, failure_events


def _raw_response_event(
    *,
    batch_id: str,
    generated_at: str,
    request_id: str,
    raw_request_row: Mapping[str, object],
    summary_row: Mapping[str, object],
    generated_response: object,
) -> dict[str, object]:
    event: dict[str, object] = {
        "schema_version": 1,
        "event_type": "raw_response",
        "batch_id": batch_id,
        "generated_at": generated_at,
        "request_id": request_id,
        "raw_request_row": dict(raw_request_row),
        "summary_row": dict(summary_row),
    }
    if isinstance(generated_response, Mapping):
        event["generated_response"] = dict(generated_response)
    return event


def _failure_event(
    *,
    batch_id: str,
    generated_at: str,
    request_id: str,
    raw_request_row: Mapping[str, object],
    summary_row: Mapping[str, object],
    generated_response: object,
) -> dict[str, object]:
    event = _raw_response_event(
        batch_id=batch_id,
        generated_at=generated_at,
        request_id=request_id,
        raw_request_row=raw_request_row,
        summary_row=summary_row,
        generated_response=generated_response,
    )
    event["event_type"] = "request_failure"
    return event


def _build_batch_id(
    *,
    pair: str,
    generated_at: str,
    execution_mode: str,
    run_id: str = "",
) -> str:
    timestamp = generated_at.replace("-", "").replace(":", "").replace("T", "T")
    run_component = str(run_id or "").strip() or timestamp
    suffix = "" if execution_mode == "live" else f":{execution_mode}"
    return f"{pair}:semantic-veto-evidence-gap-generation:{run_component}{suffix}"


def _bundle_ref(path: Path, request_id: object) -> str:
    return f"{_display_path(path)}#{str(request_id or '').strip()}"


def _as_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError("expected path value")
    return Path(text)


def _load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_json_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    _write_text_atomic(
        path,
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_jsonl_atomic(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    _write_text_atomic(
        path,
        "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
    )


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        _fsync_parent_dir(path)
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()


def _fsync_parent_dir(path: Path) -> None:
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
