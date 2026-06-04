from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_llm_prompt_bakeoff_en_es import (  # noqa: E402
    _append_journal_event,
    _display_path,
    _extract_output_text,
    _response_payload,
    _slug,
)
from semantic_veto_evidence_gap_generation_admission_en_es import (  # noqa: E402
    build_evidence_gap_generation_admission_report,
)
from semantic_veto_llm_pilot_generation_run_support import (  # noqa: E402
    _should_retry_prior_outcome,
)
from semantic_veto_evidence_gap_generation_run_artifacts import (  # noqa: E402
    _append_live_run_outcome,
    _as_path,
    _build_batch_id,
    _bundle_ref,
    _failure_events,
    _final_run_manifest,
    _mapping_rows,
    _prepare_generation_journal,
    _prepare_live_run_artifacts,
    _raw_and_failure_events_from_journal,
    _raw_response_events,
    _request_outcome_event,
    _request_queue_events,
    _request_started_event,
    _run_artifact_refs,
    _write_json_atomic,
    _write_jsonl_atomic,
    _write_text_atomic,
)


DEFAULT_MODEL_ID = "gpt-5.4-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_OUTPUT_TOKENS = 700


def build_evidence_gap_generation_run_bundle(
    *,
    request_payload: Mapping[str, object],
    responses_client: Any,
    batch_dir: Path,
    model_id: str = DEFAULT_MODEL_ID,
    temperature: float | None = DEFAULT_TEMPERATURE,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    execution_mode: str = "live",
    replay_source: str = "",
    request_ids: Sequence[str] | None = None,
    max_requests: int = 0,
    generated_at: str | None = None,
    run_id: str = "",
    resume: bool = False,
    retry_invalid_outputs: bool = False,
) -> dict[str, object]:
    resolved_execution_mode = str(execution_mode or "").strip().lower() or "live"
    if resolved_execution_mode not in {"live", "replay"}:
        raise ValueError("execution_mode must be `live` or `replay`.")
    generated_at = generated_at or _utc_now()
    selected_requests = _select_request_rows(
        request_payload.get("requests"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
    pilot = _as_mapping(request_payload.get("pilot"))
    pair = str(request_payload.get("pair") or "en-es").strip() or "en-es"
    prompt_id = str(pilot.get("prompt_id") or "").strip()
    batch_id = _build_batch_id(
        pair=pair,
        generated_at=generated_at,
        execution_mode=resolved_execution_mode,
        run_id=run_id,
    )
    batch_slug = _slug(batch_id)
    raw_response_bundle_path = batch_dir / f"{batch_slug}_raw_responses.json"
    generated_responses_path = batch_dir / f"{batch_slug}_generated_responses.json"
    journal_path = batch_dir / f"{batch_slug}_journal.jsonl"
    run_manifest_path = batch_dir / f"{batch_slug}_run_manifest.json"
    request_queue_path = batch_dir / f"{batch_slug}_request_queue.jsonl"
    raw_responses_jsonl_path = batch_dir / f"{batch_slug}_raw_responses.jsonl"
    failures_path = batch_dir / f"{batch_slug}_failures.jsonl"

    prior_outcomes: dict[str, dict[str, object]] = {}
    if resolved_execution_mode == "live":
        prior_outcomes = _prepare_generation_journal(
            journal_path=journal_path,
            batch_id=batch_id,
            resume=resume,
            selected_request_rows=selected_requests,
        )
        _prepare_live_run_artifacts(
            run_manifest_path=run_manifest_path,
            request_queue_path=request_queue_path,
            raw_responses_jsonl_path=raw_responses_jsonl_path,
            failures_path=failures_path,
            batch_id=batch_id,
            pair=pair,
            pilot=pilot,
            prompt_id=prompt_id,
            generated_at=generated_at,
            model_id=model_id,
            temperature=temperature,
            execution_mode=resolved_execution_mode,
            replay_source=replay_source,
            request_payload=request_payload,
            selected_requests=selected_requests,
            resume=resume,
            artifacts=_run_artifact_refs(
                journal_path=journal_path,
                raw_response_bundle_path=raw_response_bundle_path,
                generated_responses_path=generated_responses_path,
                run_manifest_path=run_manifest_path,
                request_queue_path=request_queue_path,
                raw_responses_jsonl_path=raw_responses_jsonl_path,
                failures_path=failures_path,
            ),
        )

    raw_request_rows: list[dict[str, object]] = []
    request_outcomes: list[dict[str, object]] = []
    generated_responses: list[dict[str, object]] = []
    for request_row in selected_requests:
        request_id = str(request_row.get("request_id") or "").strip()
        prior_outcome = prior_outcomes.get(request_id)
        if prior_outcome is not None and not _should_retry_prior_outcome(
            prior_outcome=prior_outcome,
            retry_invalid_outputs=retry_invalid_outputs,
        ):
            raw_request_rows.append(dict(prior_outcome["raw_request_row"]))
            request_outcomes.append(dict(prior_outcome["summary_row"]))
            generated_response = prior_outcome.get("generated_response")
            if isinstance(generated_response, Mapping):
                generated_responses.append(dict(generated_response))
            continue

        if resolved_execution_mode == "live":
            _append_journal_event(
                journal_path=journal_path,
                event=_request_started_event(
                    batch_id=batch_id,
                    generated_at=generated_at,
                    request_row=request_row,
                    model_id=model_id,
                ),
            )
        outcome = _execute_generation_request(
            request_row=request_row,
            responses_client=responses_client,
            model_id=model_id,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            prompt_id=prompt_id,
            raw_response_ref=_bundle_ref(raw_response_bundle_path, request_id),
        )
        if resolved_execution_mode == "live":
            _append_journal_event(
                journal_path=journal_path,
                event=_request_outcome_event(
                    batch_id=batch_id,
                    generated_at=generated_at,
                    request_id=request_id,
                    raw_request_row=outcome["raw_request_row"],
                    summary_row=outcome["summary_row"],
                    generated_response=outcome.get("generated_response"),
                ),
            )
            _append_live_run_outcome(
                raw_responses_jsonl_path=raw_responses_jsonl_path,
                failures_path=failures_path,
                batch_id=batch_id,
                generated_at=generated_at,
                request_id=request_id,
                raw_request_row=outcome["raw_request_row"],
                summary_row=outcome["summary_row"],
                generated_response=outcome.get("generated_response"),
            )
        raw_request_rows.append(outcome["raw_request_row"])
        request_outcomes.append(outcome["summary_row"])
        generated_response = outcome.get("generated_response")
        if isinstance(generated_response, Mapping):
            generated_responses.append(dict(generated_response))

    raw_response_bundle = {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": pair,
        "pilot_id": str(pilot.get("pilot_id") or "").strip(),
        "prompt_id": prompt_id,
        "execution_mode": resolved_execution_mode,
        "replay_source": replay_source,
        "generated_at": generated_at,
        "selected_model_id": model_id,
        "selected_temperature": temperature,
        "request_count": len(raw_request_rows),
        "requests": raw_request_rows,
    }
    generated_responses_payload = {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": pair,
        "pilot_id": str(pilot.get("pilot_id") or "").strip(),
        "prompt_id": prompt_id,
        "generated_at": generated_at,
        "model_id": model_id,
        "execution_mode": resolved_execution_mode,
        "source_request_packet": str(request_payload.get("_request_json_path") or "").strip(),
        "raw_response_bundle_ref": _display_path(raw_response_bundle_path),
        "selected_request_ids": [
            str(row.get("request_id") or "").strip() for row in selected_requests
        ],
        "responses": generated_responses,
    }
    admission_preview = build_evidence_gap_generation_admission_report(
        generation_requests_payload=request_payload,
        generated_responses_payload=generated_responses_payload,
        generated_at=generated_at,
    )
    summary = _summary(
        selected_request_count=len(selected_requests),
        request_outcomes=request_outcomes,
        raw_request_rows=raw_request_rows,
        admission_preview=admission_preview,
    )
    report = {
        "schema_version": 1,
        "status": _status(summary),
        "pair": pair,
        "generated_at": generated_at,
        "execution_mode": resolved_execution_mode,
        "replay_source": replay_source,
        "batch_id": batch_id,
        "pilot_id": str(pilot.get("pilot_id") or "").strip(),
        "prompt_id": prompt_id,
        "selected_model_id": model_id,
        "selected_temperature": temperature,
        "summary": summary,
        "admission_preview": {
            "status": admission_preview["status"],
            "decision": admission_preview["decision"],
            "admitted_item_count": _as_mapping(admission_preview.get("summary")).get(
                "admitted_item_count", 0
            ),
            "rejected_item_count": _as_mapping(admission_preview.get("summary")).get(
                "rejected_item_count", 0
            ),
            "coverage_shortfall_count": _as_mapping(admission_preview.get("summary")).get(
                "coverage_shortfall_count", 0
            ),
            "coverage_waived_item_count": _as_mapping(admission_preview.get("summary")).get(
                "coverage_waived_item_count", 0
            ),
        },
        "artifacts": {
            "journal_jsonl": _display_path(journal_path)
            if resolved_execution_mode == "live"
            else "",
            "run_manifest_json": _display_path(run_manifest_path),
            "request_queue_jsonl": _display_path(request_queue_path),
            "raw_responses_jsonl": _display_path(raw_responses_jsonl_path),
            "failures_jsonl": _display_path(failures_path),
            "raw_response_bundle_json": _display_path(raw_response_bundle_path),
            "generated_responses_json": _display_path(generated_responses_path),
        },
        "request_rows": request_outcomes,
    }
    return {
        "report": report,
        "raw_response_bundle": raw_response_bundle,
        "generated_responses_payload": generated_responses_payload,
        "journal_path": journal_path,
        "raw_response_bundle_path": raw_response_bundle_path,
        "generated_responses_path": generated_responses_path,
        "run_manifest_path": run_manifest_path,
        "request_queue_path": request_queue_path,
        "raw_responses_jsonl_path": raw_responses_jsonl_path,
        "failures_path": failures_path,
        "request_queue_events": _request_queue_events(
            batch_id=batch_id,
            generated_at=generated_at,
            selected_requests=selected_requests,
        ),
    }


def write_evidence_gap_generation_run_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
    generated_responses_out: Path,
) -> None:
    report = _as_mapping(bundle.get("report"))
    raw_response_bundle = _as_mapping(bundle.get("raw_response_bundle"))
    generated_responses_payload = _as_mapping(bundle.get("generated_responses_payload"))
    journal_path = _as_path(bundle.get("journal_path"))
    raw_response_bundle_path = _as_path(bundle.get("raw_response_bundle_path"))
    generated_responses_path = _as_path(bundle.get("generated_responses_path"))
    run_manifest_path = _as_path(bundle.get("run_manifest_path"))
    request_queue_path = _as_path(bundle.get("request_queue_path"))
    raw_responses_jsonl_path = _as_path(bundle.get("raw_responses_jsonl_path"))
    failures_path = _as_path(bundle.get("failures_path"))
    request_queue_events = _mapping_rows(bundle.get("request_queue_events"))

    _write_json_atomic(raw_response_bundle_path, raw_response_bundle)
    _write_json_atomic(generated_responses_path, generated_responses_payload)
    _write_json_atomic(generated_responses_out, generated_responses_payload)
    _write_json_atomic(json_out, report)
    _write_jsonl_atomic(request_queue_path, request_queue_events)
    if str(report.get("execution_mode") or "") == "live" and journal_path.exists():
        raw_response_events, failure_events = _raw_and_failure_events_from_journal(journal_path)
    else:
        raw_response_events = _raw_response_events(
            batch_id=str(report.get("batch_id") or ""),
            generated_at=str(report.get("generated_at") or ""),
            raw_request_rows=_mapping_rows(raw_response_bundle.get("requests")),
            request_outcomes=_mapping_rows(report.get("request_rows")),
            generated_responses=_mapping_rows(generated_responses_payload.get("responses")),
        )
        failure_events = _failure_events(
            batch_id=str(report.get("batch_id") or ""),
            generated_at=str(report.get("generated_at") or ""),
            raw_request_rows=_mapping_rows(raw_response_bundle.get("requests")),
            request_outcomes=_mapping_rows(report.get("request_rows")),
            generated_responses=_mapping_rows(generated_responses_payload.get("responses")),
        )
    _write_jsonl_atomic(raw_responses_jsonl_path, raw_response_events)
    _write_jsonl_atomic(failures_path, failure_events)
    _write_json_atomic(
        run_manifest_path,
        _final_run_manifest(
            report=report,
            request_queue_events=request_queue_events,
            artifacts=_as_mapping(report.get("artifacts")),
        ),
    )
    from semantic_veto_evidence_gap_generation_run_rendering import (
        render_evidence_gap_generation_run_markdown,
    )

    _write_text_atomic(markdown_out, render_evidence_gap_generation_run_markdown(report))


def _execute_generation_request(
    *,
    request_row: Mapping[str, object],
    responses_client: Any,
    model_id: str,
    temperature: float | None,
    max_output_tokens: int,
    prompt_id: str,
    raw_response_ref: str,
) -> dict[str, object]:
    request_id = str(request_row.get("request_id") or "").strip()
    base_summary = {
        "request_id": request_id,
        "family_id": str(request_row.get("family_id") or "").strip(),
        "pilot_arm": str(request_row.get("pilot_arm") or "").strip(),
        "slot_id": str(request_row.get("slot_id") or "").strip(),
        "slot_type": str(request_row.get("slot_type") or "").strip(),
        "requested_items": int(request_row.get("requested_items") or 0),
    }
    raw_request_row = {
        **base_summary,
        "model_id": model_id,
        "temperature": temperature,
        "prompt_text": str(request_row.get("prompt_text") or "").strip(),
        "status": "pending",
    }
    try:
        create_kwargs: dict[str, object] = {
            "model": model_id,
            "input": str(request_row.get("prompt_text") or "").strip(),
            "max_output_tokens": max_output_tokens,
            "text": {"format": {"type": "json_object"}},
            "metadata": {
                "request_id": request_id,
                "family_id": str(request_row.get("family_id") or ""),
                "slot_id": str(request_row.get("slot_id") or ""),
                "prompt_id": prompt_id,
            },
            "store": False,
        }
        if temperature is not None:
            create_kwargs["temperature"] = temperature
        response = responses_client.create(**create_kwargs)
    except Exception as exc:  # pragma: no cover - exercised by fake clients
        message = f"{type(exc).__name__}: {exc}"
        raw_request_row["status"] = "api_error"
        raw_request_row["error_message"] = message
        return {
            "raw_request_row": raw_request_row,
            "summary_row": {
                **base_summary,
                "status": "api_error",
                "error_message": message,
                "item_count": 0,
            },
        }

    response_id = ""
    output_text = ""
    usage: Mapping[str, object] = {}
    try:
        response_payload = _response_payload(response)
        output_text = _extract_output_text(response, response_payload)
        usage = _as_mapping(response_payload.get("usage"))
        response_id = str(response_payload.get("id") or getattr(response, "id", "") or "").strip()
        raw_request_row.update(
            {
                "status": "completed",
                "response_id": response_id,
                "response_status": str(response_payload.get("status") or "").strip(),
                "usage": dict(usage),
                "output_text": output_text,
                "response_json": response_payload,
            }
        )
        parsed_payload = json.loads(output_text)
        generated_response = _build_generated_response(
            parsed_payload=parsed_payload,
            request_row=request_row,
            model_id=model_id,
            prompt_id=prompt_id,
            raw_response_ref=raw_response_ref,
        )
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        raw_request_row["status"] = "invalid_output"
        raw_request_row["error_message"] = message
        return {
            "raw_request_row": raw_request_row,
            "summary_row": {
                **base_summary,
                "status": "invalid_output",
                "response_id": response_id,
                "output_text": output_text,
                "error_message": message,
                "item_count": 0,
            },
        }
    return {
        "raw_request_row": raw_request_row,
        "generated_response": generated_response,
        "summary_row": {
            **base_summary,
            "status": "accepted",
            "response_id": response_id,
            "item_count": len(_mapping_rows(generated_response.get("items"))),
            "first_sentence": _first_sentence(generated_response),
            "raw_response_ref": raw_response_ref,
            "usage": dict(usage),
        },
    }


def _build_generated_response(
    *,
    parsed_payload: object,
    request_row: Mapping[str, object],
    model_id: str,
    prompt_id: str,
    raw_response_ref: str,
) -> dict[str, object]:
    if not isinstance(parsed_payload, Mapping):
        raise ValueError("model output must be a JSON object")
    parsed_payload = dict(parsed_payload)
    normalization_notes: list[str] = []
    if (
        not str(parsed_payload.get("source_phrase") or "").strip()
        and str(request_row.get("trigger") or "").strip()
    ):
        parsed_payload["source_phrase"] = str(request_row.get("trigger") or "").strip()
        normalization_notes.append("source_phrase_filled_from_request_trigger")
    required_fields = [
        "request_id",
        "family_id",
        "slot_id",
        "slot_type",
        "source_phrase",
        "target_lemma",
        "items",
    ]
    missing = [field for field in required_fields if field not in parsed_payload]
    if missing:
        raise ValueError(f"model output missing required fields: {missing}")
    checks = {
        "request_id": str(request_row.get("request_id") or ""),
        "family_id": str(request_row.get("family_id") or ""),
        "slot_id": str(request_row.get("slot_id") or ""),
        "slot_type": str(request_row.get("slot_type") or ""),
        "source_phrase": str(request_row.get("trigger") or ""),
    }
    for key, expected in checks.items():
        if str(parsed_payload.get(key) or "").strip() != expected:
            raise ValueError(f"{key} did not match request packet")
    items = _mapping_rows(parsed_payload.get("items"))
    no_competitor_marker = _is_no_competitor_marker(parsed_payload, request_row=request_row)
    if not items and not no_competitor_marker:
        raise ValueError("model output items must contain at least one object")
    response = {key: parsed_payload.get(key) for key in required_fields}
    response["items"] = [dict(item) for item in items]
    response["proposed_competitor_target_lemma"] = str(
        parsed_payload.get("proposed_competitor_target_lemma") or ""
    ).strip()
    response["competitor_sense_label"] = str(
        parsed_payload.get("competitor_sense_label") or ""
    ).strip()
    response["active_sense_contrast"] = str(
        parsed_payload.get("active_sense_contrast") or ""
    ).strip()
    response["unable_to_find_distinct_competitor"] = bool(
        parsed_payload.get("unable_to_find_distinct_competitor")
    )
    response["no_distinct_competitor_reason"] = str(
        parsed_payload.get("no_distinct_competitor_reason") or ""
    ).strip()
    response["generator_id"] = model_id
    response["prompt_id"] = prompt_id
    response["raw_response_ref"] = raw_response_ref
    if normalization_notes:
        response["normalization_notes"] = normalization_notes
    return response


def _first_sentence(response: Mapping[str, object]) -> str:
    for item in _mapping_rows(response.get("items")):
        for key in (
            "sentence",
            "active_context_sentence_1",
            "shadow_or_competitor_context_sentence_1",
            "no_winner_context_sentence_1",
        ):
            value = str(item.get(key) or "").strip()
            if value:
                return value
    return ""


def _is_no_competitor_marker(
    payload: Mapping[str, object],
    *,
    request_row: Mapping[str, object],
) -> bool:
    if str(request_row.get("slot_type") or "") != "shadow_or_competitor_evidence_probe":
        return False
    if not bool(payload.get("unable_to_find_distinct_competitor")):
        return False
    return bool(str(payload.get("no_distinct_competitor_reason") or "").strip())


def _select_request_rows(
    value: object,
    *,
    request_ids: Sequence[str] | None,
    max_requests: int,
) -> list[dict[str, object]]:
    rows = [dict(row) for row in _mapping_rows(value)]
    requested_ids = {str(item).strip() for item in (request_ids or ()) if str(item).strip()}
    selected = (
        [row for row in rows if str(row.get("request_id") or "").strip() in requested_ids]
        if requested_ids
        else rows
    )
    if max_requests > 0:
        selected = selected[:max_requests]
    if not selected:
        raise ValueError("No semantic-veto evidence-gap generation requests selected.")
    return selected


def _summary(
    *,
    selected_request_count: int,
    request_outcomes: Sequence[Mapping[str, object]],
    raw_request_rows: Sequence[Mapping[str, object]],
    admission_preview: Mapping[str, object],
) -> dict[str, object]:
    status_counts = Counter(str(row.get("status") or "") for row in request_outcomes)
    accepted_rows = [row for row in request_outcomes if str(row.get("status") or "") == "accepted"]
    usage = _aggregate_usage(raw_request_rows)
    admission_summary = _as_mapping(admission_preview.get("summary"))
    return {
        "selected_request_count": selected_request_count,
        "accepted_response_count": status_counts.get("accepted", 0),
        "accepted_generated_item_count": sum(
            int(row.get("item_count") or 0) for row in accepted_rows
        ),
        "api_error_count": status_counts.get("api_error", 0),
        "invalid_output_count": status_counts.get("invalid_output", 0),
        "accepted_responses_by_arm": dict(
            sorted(Counter(str(row.get("pilot_arm") or "") for row in accepted_rows).items())
        ),
        "accepted_responses_by_slot_type": dict(
            sorted(Counter(str(row.get("slot_type") or "") for row in accepted_rows).items())
        ),
        "accepted_items_by_slot_type": dict(
            sorted(
                Counter(
                    {
                        slot_type: sum(
                            int(row.get("item_count") or 0)
                            for row in accepted_rows
                            if str(row.get("slot_type") or "") == slot_type
                        )
                        for slot_type in {str(row.get("slot_type") or "") for row in accepted_rows}
                    }
                ).items()
            )
        ),
        "admission_status": str(admission_preview.get("status") or ""),
        "admitted_item_count": int(admission_summary.get("admitted_item_count") or 0),
        "rejected_item_count": int(admission_summary.get("rejected_item_count") or 0),
        "coverage_waived_item_count": int(admission_summary.get("coverage_waived_item_count") or 0),
        "coverage_shortfall_count": int(admission_summary.get("coverage_shortfall_count") or 0),
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "reasoning_tokens": int(usage.get("reasoning_tokens") or 0),
    }


def _status(summary: Mapping[str, object]) -> str:
    selected = int(summary.get("selected_request_count") or 0)
    accepted = int(summary.get("accepted_response_count") or 0)
    if accepted == 0:
        return "error"
    if accepted < selected:
        return "partial"
    return "ok"


def _aggregate_usage(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    for row in rows:
        usage = _as_mapping(row.get("usage"))
        input_tokens += int(usage.get("input_tokens") or 0)
        output_tokens += int(usage.get("output_tokens") or 0)
        output_details = _as_mapping(usage.get("output_tokens_details"))
        reasoning_tokens += int(output_details.get("reasoning_tokens") or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
