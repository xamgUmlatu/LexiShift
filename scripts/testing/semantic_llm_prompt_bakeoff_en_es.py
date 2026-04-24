#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
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


DEFAULT_BATCH_DIR = (
    PROJECT_ROOT / "docs" / "test_outputs" / "experiments" / "semantic_llm_prompt_batches"
)
DEFAULT_BAKEOFF_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_bakeoff_latest.json"
)
DEFAULT_BAKEOFF_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_bakeoff_latest.md"
)
DEFAULT_REPLAY_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_replay_latest.json"
)
DEFAULT_REPLAY_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_replay_latest.md"
)
DEFAULT_CONFIRMATION_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_confirmation_latest.json"
)
DEFAULT_CONFIRMATION_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_confirmation_latest.md"
)
DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_EXPECTED_OUTPUT_TOKENS = 90
DEFAULT_MAX_OUTPUT_TOKENS = 300

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_ALLOWED_MODEL_ITEM_KEYS = frozenset(
    {
        "evidence_text",
        "confidence",
    }
)


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


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object.")
    return dict(payload)


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
                    f"Journal { _display_path(journal_path) } contains malformed JSON on line {line_number}: {exc}"
                ) from exc
            if not isinstance(event, Mapping):
                raise ValueError(
                    f"Journal { _display_path(journal_path) } contains a non-object event on line {line_number}."
                )
            event_batch_id = str(event.get("batch_id") or "").strip()
            if event_batch_id:
                if not batch_id:
                    batch_id = event_batch_id
                elif batch_id != event_batch_id:
                    raise ValueError(
                        f"Journal { _display_path(journal_path) } mixes batch ids {batch_id!r} and {event_batch_id!r}."
                    )
            event_type = str(event.get("event_type") or "").strip()
            request_id = str(event.get("request_id") or "").strip()
            if event_type == "request_started":
                if request_id:
                    started_request_ids.append(request_id)
                continue
            if event_type != "request_outcome":
                raise ValueError(
                    f"Journal { _display_path(journal_path) } contains unknown event_type {event_type!r} on line {line_number}."
                )
            if not request_id:
                raise ValueError(
                    f"Journal { _display_path(journal_path) } contains an outcome without request_id on line {line_number}."
                )
            if request_id in outcomes_by_request_id:
                raise ValueError(
                    f"Journal { _display_path(journal_path) } contains duplicate outcomes for request {request_id!r}."
                )
            raw_request_row = event.get("raw_request_row")
            summary_row = event.get("summary_row")
            intake_item = event.get("intake_item")
            if not isinstance(raw_request_row, Mapping) or not isinstance(summary_row, Mapping):
                raise ValueError(
                    f"Journal { _display_path(journal_path) } is missing raw_request_row or summary_row for {request_id!r}."
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


def _select_request_rows(
    value: object,
    *,
    request_ids: Sequence[str] | None,
    max_requests: int,
) -> list[dict[str, object]]:
    rows = _mapping_rows(value, "request rows")
    selected = rows
    requested_ids = {str(item).strip() for item in (request_ids or []) if str(item).strip()}
    if requested_ids:
        selected = [
            row for row in rows if str(row.get("request_id") or "").strip() in requested_ids
        ]
    if max_requests > 0:
        selected = selected[:max_requests]
    if not selected:
        raise ValueError("No prompt requests selected for execution.")
    return selected


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


def _build_intake_item(
    *,
    parsed_payload: object,
    request_row: Mapping[str, object],
    spec_slot: Mapping[str, object],
    raw_response_ref: str,
) -> tuple[dict[str, object], str]:
    if not isinstance(parsed_payload, Mapping):
        raise ValueError("model output must be a JSON object")
    items = parsed_payload.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ValueError("model output must contain `items` as an array")
    if len(items) != 1:
        raise ValueError("model output must contain exactly one item")
    item = items[0]
    if not isinstance(item, Mapping):
        raise ValueError("model output item must be an object")

    unexpected_keys = sorted(set(item.keys()) - _ALLOWED_MODEL_ITEM_KEYS)
    if unexpected_keys:
        raise ValueError(f"unexpected item keys: {unexpected_keys!r}")

    expected = request_row.get("expected_row_preview")
    if not isinstance(expected, Mapping):
        raise ValueError("request row is missing `expected_row_preview`")
    expected_metadata = _coerce_mapping(expected.get("metadata"))
    evidence_text = str(item.get("evidence_text") or "").strip()
    if not evidence_text:
        raise ValueError("evidence_text must be a non-empty string")
    intake_item = {
        "row_id": str(expected.get("row_id") or "").strip(),
        "relation_type": str(expected.get("relation_type") or "").strip(),
        "trigger": str(expected.get("trigger") or "").strip(),
        "active_target": str(expected.get("active_target") or "").strip(),
        "candidate_target": str(expected.get("candidate_target") or "").strip(),
        "candidate_pos": str(expected.get("candidate_pos") or "").strip(),
        "prompt_slot": str(expected.get("prompt_slot") or "").strip(),
        "input_ref": str(expected.get("input_ref") or "").strip(),
        "metadata": expected_metadata,
        "evidence_text": evidence_text,
    }
    confidence = item.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)):
            raise ValueError("confidence must be numeric when present")
        numeric_confidence = float(confidence)
        if numeric_confidence < 0 or numeric_confidence > 1:
            raise ValueError("confidence must be between 0 and 1 when present")
        intake_item["confidence"] = numeric_confidence
    intake_item["roles"] = _string_list(spec_slot.get("roles"))
    intake_item["pair"] = str(request_row.get("request_id") or "").split(":")[0]
    intake_item["active_sense_hint"] = _sense_hint(
        target_key=str(expected_metadata.get("active_sense_id") or "").strip(),
        canonical_pos="",
        note="fixed_shadow_active",
    )
    intake_item["candidate_sense_hint"] = _sense_hint(
        target_key=str(expected_metadata.get("candidate_sense_id") or "").strip(),
        canonical_pos=str(expected.get("candidate_pos") or "").strip(),
        note="fixed_shadow_candidate",
    )
    intake_item["raw_response_ref"] = raw_response_ref
    intake_item["review_state"] = "unreviewed"
    intake_item["promotion_state"] = "proposed"
    intake_item["runtime_publishable"] = False
    return intake_item, evidence_text


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


def _sense_hint(*, target_key: str, canonical_pos: str, note: str) -> dict[str, object]:
    hint = {
        "provider": "sentence_veto_dataset",
        "locator_kind": "sense_id",
        "target_key": target_key,
        "note": note,
    }
    if canonical_pos:
        hint["canonical_pos"] = canonical_pos
    return hint


def _merge_roles(spec_slots: Sequence[Mapping[str, object] | None]) -> list[str]:
    merged: list[str] = []
    for spec_slot in spec_slots:
        if not isinstance(spec_slot, Mapping):
            continue
        for role in _string_list(spec_slot.get("roles")):
            if role not in merged:
                merged.append(role)
    return merged or ["cue_generation"]


def _mapping_rows(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be an array of objects.")
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _coerce_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _bundle_ref(path: Path, request_id: object) -> str:
    return f"{_display_path(path)}#{str(request_id or '').strip()}"


def _slug(value: str) -> str:
    lowered = str(value or "").strip().lower()
    lowered = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode("ascii")
    normalized = _SLUG_RE.sub("-", lowered).strip("-")
    return normalized or "value"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _build_batch_id(
    *,
    pair: str,
    stage: str,
    generated_at: str,
    execution_mode: str,
    run_id: str = "",
) -> str:
    timestamp = generated_at.replace("-", "").replace(":", "").replace("T", "T").replace("Z", "Z")
    run_component = str(run_id or "").strip() or timestamp
    suffix = "" if execution_mode == "live" else f":{execution_mode}"
    return f"{pair}:{stage}:{run_component}{suffix}"


def _as_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError("expected path value")
    return Path(text)


def _resolve_default_summary_paths(stage: str, execution_mode: str) -> tuple[Path, Path]:
    if execution_mode == "replay":
        return DEFAULT_REPLAY_JSON_OUT, DEFAULT_REPLAY_MARKDOWN_OUT
    if stage == "target":
        return DEFAULT_CONFIRMATION_JSON_OUT, DEFAULT_CONFIRMATION_MARKDOWN_OUT
    return DEFAULT_BAKEOFF_JSON_OUT, DEFAULT_BAKEOFF_MARKDOWN_OUT


def build_prompt_execution_safety_report(
    *,
    queue_payload: Mapping[str, object],
    slot_manifest_payload: Mapping[str, object],
    family_inventory_payload: Mapping[str, object],
    prompt_spec_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    stage: str,
    request_ids: Sequence[str] | None = None,
    max_requests: int = 0,
    chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
    expected_output_tokens: int = DEFAULT_EXPECTED_OUTPUT_TOKENS,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    input_rate_per_1m: float | None = None,
    output_rate_per_1m: float | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be > 0")
    if expected_output_tokens < 0 or max_output_tokens < 0:
        raise ValueError("output token estimates must be >= 0")

    smoke_report = build_prompt_smoke_report(
        queue_payload=queue_payload,
        slot_manifest_payload=slot_manifest_payload,
        family_inventory_payload=family_inventory_payload,
        prompt_spec_payload=prompt_spec_payload,
        dataset_payload=dataset_payload,
        stage=stage,
        generated_at=generated_at,
    )
    selected_request_rows = _select_request_rows(
        smoke_report.get("request_rows"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
    stage_defaults = prompt_spec_payload.get("stage_defaults")
    if not isinstance(stage_defaults, Mapping):
        raise ValueError("Prompt spec is missing `stage_defaults`.")
    stage_config = stage_defaults.get(stage)
    if not isinstance(stage_config, Mapping):
        raise ValueError(f"Prompt spec is missing stage defaults for {stage!r}.")

    estimated_input_tokens = 0
    request_rows: list[dict[str, object]] = []
    for row in selected_request_rows:
        request_text = "\n".join(
            [
                str(row.get("system_prompt") or "").strip(),
                str(row.get("user_prompt") or "").strip(),
            ]
        ).strip()
        input_tokens = math.ceil(len(request_text) / chars_per_token)
        estimated_input_tokens += input_tokens
        request_rows.append(
            {
                "request_id": str(row.get("request_id") or "").strip(),
                "prompt_slot": str(row.get("prompt_slot") or "").strip(),
                "family_id": str(row.get("family_id") or "").strip(),
                "estimated_input_tokens": input_tokens,
                "expected_output_tokens": expected_output_tokens,
                "max_output_tokens": max_output_tokens,
            }
        )

    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": generated_at,
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "prompt_spec_id": str(prompt_spec_payload.get("spec_id") or "").strip(),
        "prompt_version": str(prompt_spec_payload.get("prompt_version") or "").strip(),
        "stage": stage,
        "selected_model_id": str(stage_config.get("model_id") or "").strip(),
        "summary": {
            "selected_request_count": len(request_rows),
            "estimated_input_tokens": estimated_input_tokens,
            "expected_output_tokens": expected_output_tokens * len(request_rows),
            "max_output_tokens": max_output_tokens * len(request_rows),
        },
        "request_rows": request_rows,
    }
    if input_rate_per_1m is not None and output_rate_per_1m is not None:
        report["summary"]["estimated_cost_expected"] = round(
            (estimated_input_tokens / 1_000_000.0) * input_rate_per_1m
            + ((expected_output_tokens * len(request_rows)) / 1_000_000.0) * output_rate_per_1m,
            6,
        )
        report["summary"]["estimated_cost_ceiling"] = round(
            (estimated_input_tokens / 1_000_000.0) * input_rate_per_1m
            + ((max_output_tokens * len(request_rows)) / 1_000_000.0) * output_rate_per_1m,
            6,
        )
    return report


def _assert_live_safety_guards(
    *,
    safety_report: Mapping[str, object],
    run_id: str,
    require_selected_request_count: int,
    input_rate_per_1m: float | None,
    output_rate_per_1m: float | None,
    max_estimated_cost_usd: float | None,
    max_estimated_cost_ceiling_usd: float | None,
) -> None:
    summary = safety_report.get("summary")
    if not isinstance(summary, Mapping):
        raise SystemExit("Live safety report is missing summary data.")
    selected_request_count = int(summary.get("selected_request_count") or 0)
    if not str(run_id or "").strip():
        raise SystemExit(
            "Live runs require --run-id so an interrupted run can be resumed safely without guessing."
        )
    if require_selected_request_count <= 0:
        raise SystemExit(
            "Live runs require --require-selected-request-count so the request cardinality is explicitly bounded."
        )
    if selected_request_count != require_selected_request_count:
        raise SystemExit(
            f"Live safety guard failed: selected_request_count={selected_request_count} "
            f"did not match required {require_selected_request_count}."
        )

    rates_provided = input_rate_per_1m is not None and output_rate_per_1m is not None
    if not rates_provided:
        raise SystemExit(
            "Live runs require both --input-rate-per-1m and --output-rate-per-1m "
            "so spend ceilings are explicit."
        )
    if max_estimated_cost_ceiling_usd is None:
        raise SystemExit(
            "Live runs require --max-estimated-cost-ceiling-usd so accidental overspend is blocked."
        )

    estimated_expected = float(summary.get("estimated_cost_expected") or 0.0)
    estimated_ceiling = float(summary.get("estimated_cost_ceiling") or 0.0)
    if max_estimated_cost_usd is not None and estimated_expected > max_estimated_cost_usd:
        raise SystemExit(
            f"Live safety guard failed: estimated expected cost ${estimated_expected:.6f} "
            f"exceeded cap ${max_estimated_cost_usd:.6f}."
        )
    if estimated_ceiling > max_estimated_cost_ceiling_usd:
        raise SystemExit(
            f"Live safety guard failed: estimated ceiling cost ${estimated_ceiling:.6f} "
            f"exceeded cap ${max_estimated_cost_ceiling_usd:.6f}."
        )


def _build_responses_client() -> Any:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set in the current shell. Export it or source ~/.zshrc first."
        )
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("openai is not installed in the current Python environment.") from exc
    return OpenAI().responses


class _ReplayResponse:
    def __init__(
        self,
        *,
        response_id: str,
        output_text: str,
        usage: Mapping[str, object] | None = None,
        status: str = "completed",
    ) -> None:
        self.id = response_id
        self.output_text = output_text
        self._usage = (
            dict(usage)
            if isinstance(usage, Mapping)
            else {
                "input_tokens": 0,
                "output_tokens": 0,
                "output_tokens_details": {"reasoning_tokens": 0},
            }
        )
        self._status = status

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        if mode != "json":
            raise ValueError(f"unexpected model_dump mode {mode!r}")
        return {
            "id": self.id,
            "status": self._status,
            "usage": self._usage,
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": self.output_text}],
                }
            ],
        }


class _ReplayResponsesClient:
    def __init__(self, replay_payload: Mapping[str, object]) -> None:
        request_rows = _mapping_rows(replay_payload.get("requests"), "replay requests")
        self._requests_by_id = {
            str(row.get("request_id") or "").strip(): row
            for row in request_rows
            if str(row.get("request_id") or "").strip()
        }
        self._seen_request_ids: set[str] = set()

    def create(self, **kwargs: object) -> object:
        metadata = kwargs.get("metadata")
        metadata_map = metadata if isinstance(metadata, Mapping) else {}
        request_id = str(metadata_map.get("request_id") or "").strip()
        if not request_id:
            raise RuntimeError("Replay request is missing metadata.request_id.")
        if request_id in self._seen_request_ids:
            raise RuntimeError(f"Replay request {request_id!r} was already consumed.")
        self._seen_request_ids.add(request_id)

        replay_row = self._requests_by_id.get(request_id)
        if replay_row is None:
            raise RuntimeError(f"No replay response configured for request {request_id!r}.")

        error_type = str(replay_row.get("error_type") or "").strip()
        error_message = str(replay_row.get("error_message") or "").strip()
        if error_type or error_message:
            raise _build_replay_exception(error_type=error_type, error_message=error_message)

        output_text = str(replay_row.get("output_text") or "").strip()
        if not output_text:
            raise RuntimeError(
                f"Replay response for request {request_id!r} is missing output_text."
            )
        return _ReplayResponse(
            response_id=str(replay_row.get("response_id") or f"replay_{_slug(request_id)}").strip(),
            output_text=output_text,
            usage=_coerce_mapping(replay_row.get("usage")),
            status=str(replay_row.get("response_status") or "completed").strip() or "completed",
        )


def _build_replay_exception(*, error_type: str, error_message: str) -> Exception:
    normalized_type = error_type.strip()
    normalized_message = error_message.strip() or "Replay error"
    builtins_map = {
        "RuntimeError": RuntimeError,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "AssertionError": AssertionError,
    }
    exc_cls = builtins_map.get(normalized_type, RuntimeError)
    return exc_cls(normalized_message)


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
