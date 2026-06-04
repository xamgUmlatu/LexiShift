#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_llm_prompt_bakeoff_en_es import (  # noqa: E402
    _append_journal_event,
    _assert_live_safety_guards,
    _build_responses_client,
    _display_path,
    _extract_output_text,
    _ReplayResponsesClient,
    _response_payload,
    _slug,
)
from semantic_veto_llm_pilot_admission_en_es import (  # noqa: E402
    _as_mapping,
    _load_json,
    _mapping_rows,
)
from semantic_veto_llm_pilot_generation_run_support import (  # noqa: E402
    _prepare_generation_journal,
    _request_outcome_event,
    _request_started_event,
    _should_retry_prior_outcome,
    render_generation_run_markdown,
)


DEFAULT_REQUEST_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generation_requests_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generation_run_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generation_run_en_es_latest.md"
)
DEFAULT_GENERATED_ROWS_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generated_rows_en_es_latest.json"
)
DEFAULT_BATCH_DIR = (
    PROJECT_ROOT / "docs" / "test_outputs" / "experiments" / "semantic_veto_llm_pilot_batches"
)
DEFAULT_MODEL_ID = "gpt-5.4-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_EXPECTED_OUTPUT_TOKENS = 160
DEFAULT_MAX_OUTPUT_TOKENS = 500


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute or replay the en-es semantic-veto LLM evaluation pilot request packet, "
            "preserving raw responses, generated rows, and append-only live journals."
        )
    )
    parser.add_argument("--request-json", type=Path, default=DEFAULT_REQUEST_JSON)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--request-id", action="append", default=[])
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--chars-per-token", type=float, default=DEFAULT_CHARS_PER_TOKEN)
    parser.add_argument(
        "--expected-output-tokens", type=int, default=DEFAULT_EXPECTED_OUTPUT_TOKENS
    )
    parser.add_argument("--require-selected-request-count", type=int, default=0)
    parser.add_argument("--input-rate-per-1m", type=float, default=None)
    parser.add_argument("--output-rate-per-1m", type=float, default=None)
    parser.add_argument("--max-estimated-cost-usd", type=float, default=None)
    parser.add_argument("--max-estimated-cost-ceiling-usd", type=float, default=None)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--replay-json", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--retry-invalid-outputs",
        action="store_true",
        help=(
            "With --resume, reuse accepted journal outcomes but retry requests whose prior "
            "outcome was invalid_output."
        ),
    )
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--generated-rows-out", type=Path, default=DEFAULT_GENERATED_ROWS_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.execute_live and args.replay_json is not None:
        raise SystemExit("Use either --execute-live or --replay-json, not both.")
    if args.resume and args.replay_json is not None:
        raise SystemExit("Replay runs do not support --resume.")

    generated_at = _utc_now()
    request_payload = _load_json(args.request_json)
    execution_mode = "live"
    replay_source = ""
    if args.replay_json is not None:
        responses_client = _ReplayResponsesClient(_load_json(args.replay_json))
        execution_mode = "replay"
        replay_source = _display_path(args.replay_json)
    elif not args.execute_live:
        raise SystemExit(
            "Refusing to spend API budget without --execute-live. "
            "Use --replay-json for no-spend rehearsal."
        )
    else:
        safety_report = build_semantic_veto_llm_pilot_execution_safety_report(
            request_payload=request_payload,
            request_ids=args.request_id,
            max_requests=args.max_requests,
            chars_per_token=args.chars_per_token,
            expected_output_tokens=args.expected_output_tokens,
            max_output_tokens=args.max_output_tokens,
            input_rate_per_1m=args.input_rate_per_1m,
            output_rate_per_1m=args.output_rate_per_1m,
            model_id=args.model_id,
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

    bundle = build_semantic_veto_llm_pilot_generation_run_bundle(
        request_payload=request_payload,
        responses_client=responses_client,
        batch_dir=args.batch_dir,
        model_id=args.model_id,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
        execution_mode=execution_mode,
        replay_source=replay_source,
        request_ids=args.request_id,
        max_requests=args.max_requests,
        generated_at=generated_at,
        run_id=args.run_id,
        resume=args.resume,
        retry_invalid_outputs=args.retry_invalid_outputs,
    )
    write_semantic_veto_llm_pilot_generation_run_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        generated_rows_out=args.generated_rows_out,
    )
    report = bundle["report"]
    print(f"Wrote summary JSON to {args.json_out}")
    print(f"Wrote summary Markdown to {args.markdown_out}")
    print(f"Wrote generated rows JSON to {args.generated_rows_out}")
    print(f"Batch status: {report['status']}")
    print(f"Accepted rows: {report['summary']['accepted_row_count']}")
    return 0


def build_semantic_veto_llm_pilot_generation_run_bundle(
    *,
    request_payload: Mapping[str, object],
    responses_client: Any,
    batch_dir: Path,
    model_id: str = DEFAULT_MODEL_ID,
    temperature: float = DEFAULT_TEMPERATURE,
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
    if generated_at is None:
        generated_at = _utc_now()
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
    generated_rows_path = batch_dir / f"{batch_slug}_generated_rows.json"
    journal_path = batch_dir / f"{batch_slug}_journal.jsonl"

    prior_outcomes: dict[str, dict[str, object]] = {}
    if resolved_execution_mode == "live":
        prior_outcomes = _prepare_generation_journal(
            journal_path=journal_path,
            batch_id=batch_id,
            resume=resume,
            selected_request_rows=selected_requests,
        )

    raw_request_rows: list[dict[str, object]] = []
    generated_rows: list[dict[str, object]] = []
    request_outcomes: list[dict[str, object]] = []
    for request_row in selected_requests:
        request_id = str(request_row.get("request_id") or "").strip()
        prior_outcome = prior_outcomes.get(request_id)
        if prior_outcome is not None and not _should_retry_prior_outcome(
            prior_outcome=prior_outcome,
            retry_invalid_outputs=retry_invalid_outputs,
        ):
            raw_request_rows.append(dict(prior_outcome["raw_request_row"]))
            request_outcomes.append(dict(prior_outcome["summary_row"]))
            generated_row = prior_outcome.get("generated_row")
            if isinstance(generated_row, Mapping):
                generated_rows.append(dict(generated_row))
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
                    generated_row=outcome.get("generated_row"),
                ),
            )
        raw_request_rows.append(outcome["raw_request_row"])
        request_outcomes.append(outcome["summary_row"])
        generated_row = outcome.get("generated_row")
        if isinstance(generated_row, Mapping):
            generated_rows.append(dict(generated_row))

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
    generated_rows_payload = {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": pair,
        "pilot_id": str(pilot.get("pilot_id") or "").strip(),
        "prompt_id": prompt_id,
        "generated_at": generated_at,
        "model_id": model_id,
        "execution_mode": resolved_execution_mode,
        "source_request_packet": str(pilot.get("plan_path") or "").strip(),
        "raw_response_bundle_ref": _display_path(raw_response_bundle_path),
        "selected_request_ids": [
            str(row.get("request_id") or "").strip() for row in selected_requests
        ],
        "selected_expected_row_ids": [
            str(row.get("expected_row_id") or "").strip() for row in selected_requests
        ],
        "rows": generated_rows,
    }
    summary = _summary(
        selected_request_count=len(selected_requests),
        request_outcomes=request_outcomes,
        raw_request_rows=raw_request_rows,
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
        "artifacts": {
            "journal_jsonl": _display_path(journal_path)
            if resolved_execution_mode == "live"
            else "",
            "raw_response_bundle_json": _display_path(raw_response_bundle_path),
            "generated_rows_json": _display_path(generated_rows_path),
        },
        "request_rows": request_outcomes,
    }
    return {
        "report": report,
        "raw_response_bundle": raw_response_bundle,
        "generated_rows_payload": generated_rows_payload,
        "journal_path": journal_path,
        "raw_response_bundle_path": raw_response_bundle_path,
        "generated_rows_path": generated_rows_path,
    }


def write_semantic_veto_llm_pilot_generation_run_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
    generated_rows_out: Path,
) -> None:
    report = bundle.get("report")
    raw_response_bundle = bundle.get("raw_response_bundle")
    generated_rows_payload = bundle.get("generated_rows_payload")
    raw_response_bundle_path = _as_path(bundle.get("raw_response_bundle_path"))
    generated_rows_path = _as_path(bundle.get("generated_rows_path"))
    if not isinstance(report, Mapping) or not isinstance(raw_response_bundle, Mapping):
        raise ValueError("bundle must contain report and raw_response_bundle mappings")
    if not isinstance(generated_rows_payload, Mapping):
        raise ValueError("bundle must contain generated_rows_payload mapping")

    raw_response_bundle_path.parent.mkdir(parents=True, exist_ok=True)
    raw_response_bundle_path.write_text(
        json.dumps(raw_response_bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    generated_rows_path.parent.mkdir(parents=True, exist_ok=True)
    generated_rows_path.write_text(
        json.dumps(generated_rows_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    generated_rows_out.parent.mkdir(parents=True, exist_ok=True)
    generated_rows_out.write_text(
        json.dumps(generated_rows_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_generation_run_markdown(report), encoding="utf-8")


def build_semantic_veto_llm_pilot_execution_safety_report(
    *,
    request_payload: Mapping[str, object],
    request_ids: Sequence[str] | None = None,
    max_requests: int = 0,
    chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
    expected_output_tokens: int = DEFAULT_EXPECTED_OUTPUT_TOKENS,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    input_rate_per_1m: float | None = None,
    output_rate_per_1m: float | None = None,
    model_id: str = DEFAULT_MODEL_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be > 0")
    selected_requests = _select_request_rows(
        request_payload.get("requests"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
    request_rows: list[dict[str, object]] = []
    estimated_input_tokens = 0
    for row in selected_requests:
        input_tokens = math.ceil(len(str(row.get("prompt_text") or "")) / chars_per_token)
        estimated_input_tokens += input_tokens
        request_rows.append(
            {
                "request_id": str(row.get("request_id") or ""),
                "expected_row_id": str(row.get("expected_row_id") or ""),
                "family_id": str(row.get("family_id") or ""),
                "gold_type": str(row.get("gold_type") or ""),
                "estimated_input_tokens": input_tokens,
                "expected_output_tokens": expected_output_tokens,
                "max_output_tokens": max_output_tokens,
            }
        )
    summary: dict[str, object] = {
        "selected_request_count": len(request_rows),
        "estimated_input_tokens": estimated_input_tokens,
        "expected_output_tokens": expected_output_tokens * len(request_rows),
        "max_output_tokens": max_output_tokens * len(request_rows),
    }
    if input_rate_per_1m is not None and output_rate_per_1m is not None:
        summary["estimated_cost_expected"] = round(
            (estimated_input_tokens / 1_000_000.0) * input_rate_per_1m
            + ((expected_output_tokens * len(request_rows)) / 1_000_000.0) * output_rate_per_1m,
            6,
        )
        summary["estimated_cost_ceiling"] = round(
            (estimated_input_tokens / 1_000_000.0) * input_rate_per_1m
            + ((max_output_tokens * len(request_rows)) / 1_000_000.0) * output_rate_per_1m,
            6,
        )
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "selected_model_id": model_id,
        "summary": summary,
        "request_rows": request_rows,
    }


def _execute_generation_request(
    *,
    request_row: Mapping[str, object],
    responses_client: Any,
    model_id: str,
    temperature: float,
    max_output_tokens: int,
    prompt_id: str,
    raw_response_ref: str,
) -> dict[str, object]:
    request_id = str(request_row.get("request_id") or "").strip()
    expected_row_id = str(request_row.get("expected_row_id") or "").strip()
    base_summary = {
        "request_id": request_id,
        "row_id": expected_row_id,
        "family_id": str(request_row.get("family_id") or "").strip(),
        "trigger": str(request_row.get("trigger") or "").strip(),
        "candidate_replacement": str(request_row.get("candidate_replacement") or "").strip(),
        "gold_type": str(request_row.get("gold_type") or "").strip(),
        "gold_decision": str(request_row.get("gold_decision") or "").strip(),
    }
    raw_request_row = {
        **base_summary,
        "model_id": model_id,
        "temperature": temperature,
        "prompt_text": str(request_row.get("prompt_text") or "").strip(),
        "status": "pending",
    }
    try:
        response = responses_client.create(
            model=model_id,
            input=str(request_row.get("prompt_text") or "").strip(),
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            text={"format": {"type": "json_object"}},
            metadata={
                "request_id": request_id,
                "expected_row_id": expected_row_id,
                "family_id": str(request_row.get("family_id") or ""),
                "prompt_id": prompt_id,
            },
            store=False,
        )
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
        generated_row = _build_generated_row(
            parsed_payload=parsed_payload,
            request_row=request_row,
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
            },
        }
    return {
        "raw_request_row": raw_request_row,
        "generated_row": generated_row,
        "summary_row": {
            **base_summary,
            "status": "accepted",
            "response_id": response_id,
            "sentence": str(generated_row.get("sentence") or ""),
            "raw_response_ref": raw_response_ref,
            "usage": dict(usage),
        },
    }


def _build_generated_row(
    *,
    parsed_payload: object,
    request_row: Mapping[str, object],
    prompt_id: str,
    raw_response_ref: str,
) -> dict[str, object]:
    if not isinstance(parsed_payload, Mapping):
        raise ValueError("model output must be a JSON object")
    required_fields = [
        "row_id",
        "family_id",
        "trigger",
        "candidate_replacement",
        "sentence",
        "gold_decision",
        "gold_type",
        "active_sense",
        "gold_reason",
        "pos",
        "generator_id",
        "prompt_id",
    ]
    missing = [field for field in required_fields if not str(parsed_payload.get(field) or "")]
    if missing:
        raise ValueError(f"model output missing required fields: {missing}")
    row_id = str(parsed_payload.get("row_id") or "").strip()
    expected_row_id = str(request_row.get("expected_row_id") or "").strip()
    if row_id != expected_row_id:
        raise ValueError(f"row_id {row_id!r} did not match expected {expected_row_id!r}")
    checks = {
        "family_id": str(request_row.get("family_id") or ""),
        "trigger": str(request_row.get("trigger") or ""),
        "candidate_replacement": str(request_row.get("candidate_replacement") or ""),
        "gold_decision": str(request_row.get("gold_decision") or ""),
        "gold_type": str(request_row.get("gold_type") or ""),
        "active_sense": str(request_row.get("active_sense") or ""),
        "pos": str(request_row.get("pos") or ""),
    }
    for key, expected in checks.items():
        if str(parsed_payload.get(key) or "").strip() != expected:
            raise ValueError(f"{key} did not match request packet")
    row = {key: parsed_payload.get(key) for key in required_fields}
    row["negative_sense"] = str(parsed_payload.get("negative_sense") or "").strip()
    row["no_winner_reason"] = str(parsed_payload.get("no_winner_reason") or "").strip()
    difficulty_tags = parsed_payload.get("difficulty_tags")
    row["difficulty_tags"] = (
        [str(value) for value in difficulty_tags]
        if isinstance(difficulty_tags, Sequence) and not isinstance(difficulty_tags, (str, bytes))
        else []
    )
    row["generator_id"] = str(row.get("generator_id") or "").strip() or "unknown-model"
    row["prompt_id"] = str(row.get("prompt_id") or "").strip() or prompt_id
    row["raw_response_ref"] = raw_response_ref
    row["source_request_id"] = str(request_row.get("request_id") or "").strip()
    return row


def _select_request_rows(
    value: object,
    *,
    request_ids: Sequence[str] | None,
    max_requests: int,
) -> list[dict[str, object]]:
    rows = _mapping_rows(value)
    requested_ids = {str(item).strip() for item in (request_ids or ()) if str(item).strip()}
    selected = (
        [row for row in rows if str(row.get("request_id") or "").strip() in requested_ids]
        if requested_ids
        else rows
    )
    if max_requests > 0:
        selected = selected[:max_requests]
    if not selected:
        raise ValueError("No semantic-veto LLM pilot requests selected.")
    return selected


def _summary(
    *,
    selected_request_count: int,
    request_outcomes: Sequence[Mapping[str, object]],
    raw_request_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    status_counts = Counter(str(row.get("status") or "") for row in request_outcomes)
    usage = _aggregate_usage(raw_request_rows)
    accepted_rows = [row for row in request_outcomes if str(row.get("status") or "") == "accepted"]
    return {
        "selected_request_count": selected_request_count,
        "accepted_row_count": status_counts.get("accepted", 0),
        "api_error_count": status_counts.get("api_error", 0),
        "invalid_output_count": status_counts.get("invalid_output", 0),
        "accepted_rows_by_gold_type": dict(
            sorted(Counter(str(row.get("gold_type") or "") for row in accepted_rows).items())
        ),
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "reasoning_tokens": int(usage.get("reasoning_tokens") or 0),
    }


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


def _status(summary: Mapping[str, object]) -> str:
    selected = int(summary.get("selected_request_count") or 0)
    accepted = int(summary.get("accepted_row_count") or 0)
    if accepted == 0:
        return "error"
    if accepted < selected:
        return "partial"
    return "ok"


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
    return f"{pair}:semantic-veto-llm-pilot:{run_component}{suffix}"


def _bundle_ref(path: Path, request_id: object) -> str:
    return f"{_display_path(path)}#{str(request_id or '').strip()}"


def _as_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError("expected path value")
    return Path(text)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
