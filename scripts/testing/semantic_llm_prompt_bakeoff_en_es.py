#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_llm_prompt_bakeoff_common import (  # noqa: E402
    DEFAULT_BATCH_DIR,
    DEFAULT_BAKEOFF_JSON_OUT as DEFAULT_BAKEOFF_JSON_OUT,
    DEFAULT_BAKEOFF_MARKDOWN_OUT as DEFAULT_BAKEOFF_MARKDOWN_OUT,
    DEFAULT_CHARS_PER_TOKEN,
    DEFAULT_CONFIRMATION_JSON_OUT as DEFAULT_CONFIRMATION_JSON_OUT,
    DEFAULT_CONFIRMATION_MARKDOWN_OUT as DEFAULT_CONFIRMATION_MARKDOWN_OUT,
    DEFAULT_EXPECTED_OUTPUT_TOKENS,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_REPLAY_JSON_OUT as DEFAULT_REPLAY_JSON_OUT,
    DEFAULT_REPLAY_MARKDOWN_OUT as DEFAULT_REPLAY_MARKDOWN_OUT,
    _as_path as _as_path,
    _build_batch_id as _build_batch_id,
    _bundle_ref as _bundle_ref,
    _coerce_mapping as _coerce_mapping,
    _display_path as _display_path,
    _load_json as _load_json,
    _mapping_rows as _mapping_rows,
    _merge_roles as _merge_roles,
    _resolve_default_summary_paths as _resolve_default_summary_paths,
    _sense_hint as _sense_hint,
    _slug as _slug,
    _string_list as _string_list,
    _utc_now as _utc_now,
)
from semantic_llm_prompt_bakeoff_journal import (  # noqa: E402
    _append_journal_event as _append_journal_event,
    _build_request_outcome_event as _build_request_outcome_event,
    _build_request_started_event as _build_request_started_event,
    _load_journal_state as _load_journal_state,
    _prepare_live_journal as _prepare_live_journal,
)
from semantic_llm_prompt_bakeoff_intake import _build_intake_item  # noqa: E402
from semantic_llm_prompt_bakeoff_safety import (  # noqa: E402
    _assert_live_safety_guards as _assert_live_safety_guards,
    _build_responses_client as _build_responses_client,
    _ReplayResponsesClient as _ReplayResponsesClient,
    _select_request_rows as _select_request_rows,
    build_prompt_execution_safety_report as build_prompt_execution_safety_report,
)
from semantic_llm_prompt_reporting import render_prompt_bakeoff_markdown  # noqa: E402
from semantic_llm_prompt_smoke import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_FAMILY_INVENTORY_JSON,
    DEFAULT_PROMPT_SPEC_JSON,
    DEFAULT_QUEUE_JSON,
    DEFAULT_SLOT_MANIFEST_JSON,
    build_prompt_smoke_report,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen semantic LLM prompt bakeoff on the current en-es queue, "
            "write immutable raw/normalized batch artifacts, and render a stable summary report."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--slot-manifest-json", type=Path, default=DEFAULT_SLOT_MANIFEST_JSON)
    parser.add_argument("--family-inventory-json", type=Path, default=DEFAULT_FAMILY_INVENTORY_JSON)
    parser.add_argument("--prompt-spec-json", type=Path, default=DEFAULT_PROMPT_SPEC_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--stage",
        choices=("proxy", "target"),
        default="proxy",
        help="Bakeoff stage to execute.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="",
        help="Stable operator-chosen run id used for live journaling and safe resume.",
    )
    parser.add_argument(
        "--request-id",
        action="append",
        default=[],
        help="Optional request_id filter. Repeat to execute only a subset of rendered requests.",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=0,
        help="Optional cap on the number of rendered requests to execute after filtering.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=DEFAULT_MAX_OUTPUT_TOKENS,
        help="Upper bound for model-visible output tokens per request.",
    )
    parser.add_argument(
        "--require-selected-request-count",
        type=int,
        default=0,
        help="Live safety guard: fail unless the selected request count matches this exact number.",
    )
    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=DEFAULT_CHARS_PER_TOKEN,
        help="Live safety guard heuristic for input-token estimation.",
    )
    parser.add_argument(
        "--expected-output-tokens",
        type=int,
        default=DEFAULT_EXPECTED_OUTPUT_TOKENS,
        help="Live safety guard expected output tokens per request.",
    )
    parser.add_argument(
        "--input-rate-per-1m",
        type=float,
        default=None,
        help="Live safety guard input pricing rate per 1M tokens.",
    )
    parser.add_argument(
        "--output-rate-per-1m",
        type=float,
        default=None,
        help="Live safety guard output pricing rate per 1M tokens.",
    )
    parser.add_argument(
        "--max-estimated-cost-usd",
        type=float,
        default=None,
        help="Optional live safety guard on expected estimated USD cost.",
    )
    parser.add_argument(
        "--max-estimated-cost-ceiling-usd",
        type=float,
        default=None,
        help="Required live safety guard on estimated ceiling USD cost.",
    )
    parser.add_argument(
        "--execute-live",
        action="store_true",
        help="Actually call the API. Omit this flag for safety; the runner will refuse live spend.",
    )
    parser.add_argument(
        "--replay-json",
        type=Path,
        default=None,
        help=(
            "Optional replay fixture. When set, the runner uses canned responses instead of calling the API "
            "and writes replay-labeled artifacts through the normal bakeoff path."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a previously interrupted live run from its append-only journal.",
    )
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    return parser.parse_args()


def build_prompt_bakeoff_bundle(
    *,
    queue_payload: Mapping[str, object],
    slot_manifest_payload: Mapping[str, object],
    family_inventory_payload: Mapping[str, object],
    prompt_spec_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    stage: str,
    responses_client: Any,
    batch_dir: Path,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    request_ids: Sequence[str] | None = None,
    max_requests: int = 0,
    generated_at: str | None = None,
    execution_mode: str = "live",
    replay_source: str = "",
    run_id: str = "",
    resume: bool = False,
) -> dict[str, object]:
    resolved_stage = str(stage or "").strip().lower() or "proxy"
    if resolved_stage not in {"proxy", "target"}:
        raise ValueError("stage must be `proxy` or `target`.")
    resolved_execution_mode = str(execution_mode or "").strip().lower() or "live"
    if resolved_execution_mode not in {"live", "replay"}:
        raise ValueError("execution_mode must be `live` or `replay`.")
    resolved_run_id = str(run_id or "").strip()
    if generated_at is None:
        generated_at = _utc_now()

    smoke_report = build_prompt_smoke_report(
        queue_payload=queue_payload,
        slot_manifest_payload=slot_manifest_payload,
        family_inventory_payload=family_inventory_payload,
        prompt_spec_payload=prompt_spec_payload,
        dataset_payload=dataset_payload,
        stage=resolved_stage,
        generated_at=generated_at,
    )
    stage_defaults = prompt_spec_payload.get("stage_defaults")
    if not isinstance(stage_defaults, Mapping):
        raise ValueError("Prompt spec is missing `stage_defaults`.")
    stage_config = stage_defaults.get(resolved_stage)
    if not isinstance(stage_config, Mapping):
        raise ValueError(f"Prompt spec is missing stage defaults for {resolved_stage!r}.")
    spec_slots = _mapping_rows(prompt_spec_payload.get("slots"), "prompt spec slots")
    spec_slot_lookup = {
        str(row.get("prompt_slot") or "").strip(): row
        for row in spec_slots
        if str(row.get("prompt_slot") or "").strip()
    }

    selected_request_rows = _select_request_rows(
        smoke_report.get("request_rows"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
    queue_id = str(queue_payload.get("queue_id") or "").strip()
    prompt_spec_id = str(prompt_spec_payload.get("spec_id") or "").strip()
    prompt_version = str(prompt_spec_payload.get("prompt_version") or "").strip()
    batch_id = _build_batch_id(
        pair=str(smoke_report.get("pair") or "en-es"),
        stage=resolved_stage,
        generated_at=generated_at,
        execution_mode=resolved_execution_mode,
        run_id=resolved_run_id,
    )
    if queue_id:
        source_id = (
            f"{queue_id}:{resolved_stage}"
            if resolved_execution_mode == "live"
            else f"{queue_id}:{resolved_stage}:{resolved_execution_mode}"
        )
    else:
        source_id = f"semantic_prompt_bakeoff:{resolved_stage}:{resolved_execution_mode}"

    batch_slug = _slug(batch_id)
    raw_response_bundle_path = batch_dir / f"{batch_slug}_raw_responses.json"
    intake_batch_path = batch_dir / f"{batch_slug}_intake_batch.json"
    normalized_batch_path = batch_dir / f"{batch_slug}_normalized_evidence.json"
    journal_path = batch_dir / f"{batch_slug}_journal.jsonl"

    prior_outcomes: dict[str, dict[str, object]] = {}
    if resolved_execution_mode == "live":
        prior_outcomes = _prepare_live_journal(
            journal_path=journal_path,
            batch_id=batch_id,
            resume=resume,
            selected_request_rows=selected_request_rows,
        )

    raw_request_rows: list[dict[str, object]] = []
    intake_items: list[dict[str, object]] = []
    request_outcomes: list[dict[str, object]] = []
    for request_row in selected_request_rows:
        request_id = str(request_row.get("request_id") or "").strip()
        prior_outcome = prior_outcomes.get(request_id)
        if prior_outcome is not None:
            raw_request_rows.append(dict(prior_outcome["raw_request_row"]))
            request_outcomes.append(dict(prior_outcome["summary_row"]))
            intake_item = prior_outcome.get("intake_item")
            if isinstance(intake_item, Mapping):
                intake_items.append(dict(intake_item))
            continue

        prompt_slot = str(request_row.get("prompt_slot") or "").strip()
        spec_slot = spec_slot_lookup.get(prompt_slot)
        if spec_slot is None:
            raise ValueError(f"Prompt spec is missing slot {prompt_slot!r}.")
        if resolved_execution_mode == "live":
            _append_journal_event(
                journal_path=journal_path,
                event=_build_request_started_event(
                    batch_id=batch_id,
                    generated_at=generated_at,
                    request_row=request_row,
                ),
            )
        outcome = _execute_prompt_request(
            request_row=request_row,
            spec_slot=spec_slot,
            prompt_version=prompt_version,
            stage=resolved_stage,
            responses_client=responses_client,
            max_output_tokens=max_output_tokens,
            raw_response_ref=_bundle_ref(raw_response_bundle_path, request_row.get("request_id")),
        )
        if resolved_execution_mode == "live":
            _append_journal_event(
                journal_path=journal_path,
                event=_build_request_outcome_event(
                    batch_id=batch_id,
                    generated_at=generated_at,
                    request_id=request_id,
                    raw_request_row=outcome["raw_request_row"],
                    summary_row=outcome["summary_row"],
                    intake_item=outcome.get("intake_item"),
                ),
            )
        raw_request_rows.append(outcome["raw_request_row"])
        request_outcomes.append(outcome["summary_row"])
        intake_item = outcome.get("intake_item")
        if isinstance(intake_item, Mapping):
            intake_items.append(dict(intake_item))

    raw_response_bundle = _build_raw_response_bundle(
        batch_id=batch_id,
        pair=str(smoke_report.get("pair") or "en-es"),
        queue_id=queue_id,
        prompt_spec_id=prompt_spec_id,
        prompt_version=prompt_version,
        stage=resolved_stage,
        execution_mode=resolved_execution_mode,
        replay_source=replay_source,
        selected_model_id=str(stage_config.get("model_id") or "").strip(),
        selected_temperature=float(stage_config.get("temperature") or 0.0),
        generated_at=generated_at,
        requests=raw_request_rows,
    )

    aggregate_cost = _aggregate_cost_metadata(raw_request_rows)
    intake_batch = None
    normalized_batch = None
    if intake_items:
        batch_roles = _merge_roles(
            spec_slot_lookup.get(str(row.get("prompt_slot") or "").strip())
            for row in request_outcomes
        )
        intake_batch = {
            "schema_version": 1,
            "batch_id": batch_id,
            "pair": str(smoke_report.get("pair") or "en-es"),
            "source_type": "llm",
            "source_id": source_id,
            "source_family": "silver_llm_generation",
            "roles": batch_roles,
            "generated_at": generated_at,
            "ingested_at": generated_at,
            "review_state": "unreviewed",
            "model_id": str(stage_config.get("model_id") or "").strip(),
            "prompt_version": prompt_version,
            "temperature": float(stage_config.get("temperature") or 0.0),
            "cost_metadata": aggregate_cost,
            "provenance": {
                "queue_id": queue_id,
                "prompt_spec_id": prompt_spec_id,
                "stage": resolved_stage,
                "execution_mode": resolved_execution_mode,
                "raw_response_bundle_ref": _display_path(raw_response_bundle_path),
            },
            "items": intake_items,
        }
        if replay_source:
            intake_batch["provenance"]["replay_source"] = replay_source
        normalized_batch = normalize_llm_intake_batch(intake_batch)

    summary = _build_bakeoff_summary(
        selected_request_count=len(selected_request_rows),
        request_outcomes=request_outcomes,
        normalized_batch=normalized_batch,
        aggregate_cost=aggregate_cost,
    )
    report = {
        "schema_version": 1,
        "status": _resolve_status(summary),
        "pair": str(smoke_report.get("pair") or "en-es"),
        "generated_at": generated_at,
        "queue_id": queue_id,
        "prompt_spec_id": prompt_spec_id,
        "prompt_version": prompt_version,
        "stage": resolved_stage,
        "execution_mode": resolved_execution_mode,
        "replay_source": replay_source,
        "batch_id": batch_id,
        "source_id": source_id,
        "selected_model_id": str(stage_config.get("model_id") or "").strip(),
        "selected_temperature": float(stage_config.get("temperature") or 0.0),
        "summary": summary,
        "artifacts": {
            "journal_jsonl": _display_path(journal_path)
            if resolved_execution_mode == "live"
            else "",
            "raw_response_bundle_json": _display_path(raw_response_bundle_path),
            "intake_batch_json": _display_path(intake_batch_path)
            if intake_batch is not None
            else "",
            "normalized_batch_json": _display_path(normalized_batch_path)
            if normalized_batch is not None
            else "",
        },
        "request_rows": request_outcomes,
    }
    return {
        "report": report,
        "raw_response_bundle": raw_response_bundle,
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "journal_path": journal_path,
        "raw_response_bundle_path": raw_response_bundle_path,
        "intake_batch_path": intake_batch_path,
        "normalized_batch_path": normalized_batch_path,
    }


def write_prompt_bakeoff_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
) -> None:
    report = bundle.get("report")
    raw_response_bundle = bundle.get("raw_response_bundle")
    intake_batch = bundle.get("intake_batch")
    normalized_batch = bundle.get("normalized_batch")
    raw_response_bundle_path = _as_path(bundle.get("raw_response_bundle_path"))
    intake_batch_path = _as_path(bundle.get("intake_batch_path"))
    normalized_batch_path = _as_path(bundle.get("normalized_batch_path"))

    if not isinstance(report, Mapping) or not isinstance(raw_response_bundle, Mapping):
        raise ValueError("bundle must contain report and raw_response_bundle mappings")

    raw_response_bundle_path.parent.mkdir(parents=True, exist_ok=True)
    raw_response_bundle_path.write_text(
        json.dumps(raw_response_bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if isinstance(intake_batch, Mapping):
        intake_batch_path.parent.mkdir(parents=True, exist_ok=True)
        intake_batch_path.write_text(
            json.dumps(intake_batch, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if isinstance(normalized_batch, Mapping):
        normalized_batch_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_batch_path.write_text(
            json.dumps(normalized_batch, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_prompt_bakeoff_markdown(report), encoding="utf-8")


def _execute_prompt_request(
    *,
    request_row: Mapping[str, object],
    spec_slot: Mapping[str, object],
    prompt_version: str,
    stage: str,
    responses_client: Any,
    max_output_tokens: int,
    raw_response_ref: str,
) -> dict[str, object]:
    request_id = str(request_row.get("request_id") or "").strip()
    base_summary = {
        "request_id": request_id,
        "prompt_slot": str(request_row.get("prompt_slot") or "").strip(),
        "family_id": str(request_row.get("family_id") or "").strip(),
        "trigger": str(request_row.get("trigger") or "").strip(),
        "active_target": str(request_row.get("active_target") or "").strip(),
        "candidate_target": str(request_row.get("candidate_target") or "").strip(),
    }
    raw_request_row = {
        **base_summary,
        "model_id": str(request_row.get("model_id") or "").strip(),
        "temperature": float(request_row.get("temperature") or 0.0),
        "system_prompt": str(request_row.get("system_prompt") or "").strip(),
        "user_prompt": str(request_row.get("user_prompt") or "").strip(),
        "status": "pending",
    }
    try:
        response = responses_client.create(
            model=str(request_row.get("model_id") or "").strip(),
            instructions=str(request_row.get("system_prompt") or "").strip(),
            input=str(request_row.get("user_prompt") or "").strip(),
            temperature=float(request_row.get("temperature") or 0.0),
            max_output_tokens=max_output_tokens,
            text={"format": {"type": "json_object"}},
            metadata={
                "request_id": request_id,
                "prompt_slot": str(request_row.get("prompt_slot") or "").strip(),
                "family_id": str(request_row.get("family_id") or "").strip(),
                "stage": stage,
                "prompt_version": prompt_version,
            },
            store=False,
        )
    except Exception as exc:  # pragma: no cover - exercised via fake client in tests
        message = f"{type(exc).__name__}: {exc}"
        raw_request_row["status"] = "api_error"
        raw_request_row["error_message"] = message
        return {
            "raw_request_row": raw_request_row,
            "summary_row": {
                **base_summary,
                "status": "api_error",
                "error_message": message,
            },
        }

    try:
        response_payload = _response_payload(response)
        output_text = _extract_output_text(response, response_payload)
        usage = _coerce_mapping(response_payload.get("usage"))
        response_id = str(response_payload.get("id") or getattr(response, "id", "") or "").strip()
        raw_request_row.update(
            {
                "status": "completed",
                "response_id": response_id,
                "response_status": str(response_payload.get("status") or "").strip(),
                "usage": usage,
                "output_text": output_text,
                "response_json": response_payload,
            }
        )
        parsed_payload = json.loads(output_text)
        intake_item, evidence_text = _build_intake_item(
            parsed_payload=parsed_payload,
            request_row=request_row,
            spec_slot=spec_slot,
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
            },
        }

    return {
        "raw_request_row": raw_request_row,
        "intake_item": intake_item,
        "summary_row": {
            **base_summary,
            "status": "accepted",
            "response_id": response_id,
            "evidence_text": evidence_text,
            "raw_response_ref": raw_response_ref,
            "usage": usage,
        },
    }


def _build_raw_response_bundle(
    *,
    batch_id: str,
    pair: str,
    queue_id: str,
    prompt_spec_id: str,
    prompt_version: str,
    stage: str,
    execution_mode: str,
    replay_source: str,
    selected_model_id: str,
    selected_temperature: float,
    generated_at: str,
    requests: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": pair,
        "queue_id": queue_id,
        "prompt_spec_id": prompt_spec_id,
        "prompt_version": prompt_version,
        "stage": stage,
        "execution_mode": execution_mode,
        "replay_source": replay_source,
        "generated_at": generated_at,
        "selected_model_id": selected_model_id,
        "selected_temperature": selected_temperature,
        "request_count": len(requests),
        "requests": [dict(row) for row in requests],
    }


def _build_bakeoff_summary(
    *,
    selected_request_count: int,
    request_outcomes: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    aggregate_cost: Mapping[str, object],
) -> dict[str, object]:
    api_error_count = 0
    invalid_output_count = 0
    accepted_item_count = 0
    for row in request_outcomes:
        status = str(row.get("status") or "").strip()
        if status == "api_error":
            api_error_count += 1
        elif status == "invalid_output":
            invalid_output_count += 1
        elif status == "accepted":
            accepted_item_count += 1
    normalized_row_count = (
        int(normalized_batch.get("row_count") or 0) if isinstance(normalized_batch, Mapping) else 0
    )
    return {
        "selected_request_count": selected_request_count,
        "accepted_item_count": accepted_item_count,
        "api_error_count": api_error_count,
        "invalid_output_count": invalid_output_count,
        "normalized_row_count": normalized_row_count,
        "input_tokens": int(aggregate_cost.get("input_tokens") or 0),
        "output_tokens": int(aggregate_cost.get("output_tokens") or 0),
        "reasoning_tokens": int(aggregate_cost.get("reasoning_tokens") or 0),
    }


def _aggregate_cost_metadata(request_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    completed_count = 0
    for row in request_rows:
        usage = _coerce_mapping(row.get("usage"))
        if usage:
            completed_count += 1
        input_tokens += int(usage.get("input_tokens") or 0)
        output_tokens += int(usage.get("output_tokens") or 0)
        output_details = _coerce_mapping(usage.get("output_tokens_details"))
        reasoning_tokens += int(output_details.get("reasoning_tokens") or 0)
    return {
        "request_count": len(request_rows),
        "requests_with_usage": completed_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
    }


def _resolve_status(summary: Mapping[str, object]) -> str:
    selected = int(summary.get("selected_request_count") or 0)
    accepted = int(summary.get("accepted_item_count") or 0)
    if accepted == 0:
        return "error"
    if accepted < selected:
        return "partial"
    return "ok"


def _response_payload(response: Any) -> dict[str, object]:
    if hasattr(response, "model_dump"):
        payload = response.model_dump(mode="json")
        if isinstance(payload, Mapping):
            return dict(payload)
    if hasattr(response, "to_dict"):
        payload = response.to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    raise ValueError("response object does not expose a JSON payload")


def _extract_output_text(response: Any, payload: Mapping[str, object]) -> str:
    text = str(getattr(response, "output_text", "") or "").strip()
    if text:
        return text
    output = payload.get("output")
    if isinstance(output, Sequence) and not isinstance(output, (str, bytes)):
        for item in output:
            if not isinstance(item, Mapping):
                continue
            content = item.get("content")
            if not isinstance(content, Sequence) or isinstance(content, (str, bytes)):
                continue
            for block in content:
                if not isinstance(block, Mapping):
                    continue
                block_text = str(block.get("text") or "").strip()
                if block_text:
                    return block_text
    raise ValueError("response payload does not contain output text")


def main() -> int:
    args = _parse_args()
    if args.execute_live and args.replay_json is not None:
        raise SystemExit("Use either --execute-live or --replay-json, not both.")
    if args.resume and args.replay_json is not None:
        raise SystemExit("Replay runs do not support --resume.")

    generated_at = _utc_now()
    queue_payload = _load_json(args.queue_json)
    slot_manifest_payload = _load_json(args.slot_manifest_json)
    family_inventory_payload = _load_json(args.family_inventory_json)
    prompt_spec_payload = _load_json(args.prompt_spec_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)

    execution_mode = "live"
    replay_source = ""
    if args.replay_json is not None:
        responses_client = _ReplayResponsesClient(_load_json(args.replay_json))
        execution_mode = "replay"
        replay_source = _display_path(args.replay_json)
    elif not args.execute_live:
        raise SystemExit(
            "Refusing to spend API budget without --execute-live. "
            "Run scripts/testing/semantic_llm_prompt_preflight_en_es.py first."
        )
    else:
        safety_report = build_prompt_execution_safety_report(
            queue_payload=queue_payload,
            slot_manifest_payload=slot_manifest_payload,
            family_inventory_payload=family_inventory_payload,
            prompt_spec_payload=prompt_spec_payload,
            dataset_payload=dataset_payload,
            stage=args.stage,
            request_ids=args.request_id,
            max_requests=args.max_requests,
            chars_per_token=args.chars_per_token,
            expected_output_tokens=args.expected_output_tokens,
            max_output_tokens=args.max_output_tokens,
            input_rate_per_1m=args.input_rate_per_1m,
            output_rate_per_1m=args.output_rate_per_1m,
            generated_at=generated_at,
        )
        _assert_live_safety_guards(
            safety_report=safety_report,
            run_id=args.run_id,
            require_selected_request_count=args.require_selected_request_count,
            input_rate_per_1m=args.input_rate_per_1m,
            output_rate_per_1m=args.output_rate_per_1m,
            max_estimated_cost_usd=args.max_estimated_cost_usd,
            max_estimated_cost_ceiling_usd=args.max_estimated_cost_ceiling_usd,
        )
        responses_client = _build_responses_client()

    json_out, markdown_out = _resolve_default_summary_paths(args.stage, execution_mode)
    if args.json_out is not None:
        json_out = args.json_out
    if args.markdown_out is not None:
        markdown_out = args.markdown_out

    bundle = build_prompt_bakeoff_bundle(
        queue_payload=queue_payload,
        slot_manifest_payload=slot_manifest_payload,
        family_inventory_payload=family_inventory_payload,
        prompt_spec_payload=prompt_spec_payload,
        dataset_payload=dataset_payload,
        stage=args.stage,
        responses_client=responses_client,
        batch_dir=args.batch_dir,
        max_output_tokens=args.max_output_tokens,
        request_ids=args.request_id,
        max_requests=args.max_requests,
        generated_at=generated_at,
        execution_mode=execution_mode,
        replay_source=replay_source,
        run_id=args.run_id,
        resume=args.resume,
    )
    write_prompt_bakeoff_bundle(bundle=bundle, json_out=json_out, markdown_out=markdown_out)
    report = bundle["report"]
    print(f"Wrote summary JSON to {json_out}")
    print(f"Wrote summary Markdown to {markdown_out}")
    print(f"Batch status: {report['status']}")
    print(f"Accepted items: {report['summary']['accepted_item_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
