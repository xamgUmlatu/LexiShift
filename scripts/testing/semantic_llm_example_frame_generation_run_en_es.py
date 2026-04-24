#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_llm_prompt_bakeoff_en_es import (  # noqa: E402
    _append_journal_event,
    _assert_live_safety_guards,
    _build_request_outcome_event,
    _build_request_started_event,
    _build_responses_client,
    _bundle_ref,
    _display_path,
    _execute_prompt_request,
    _prepare_live_journal,
    _ReplayResponsesClient,
    _slug,
)
from semantic_llm_example_frame_generation_plan_en_es import (  # noqa: E402
    DEFAULT_CHARS_PER_TOKEN,
    DEFAULT_EXPECTED_OUTPUT_TOKENS,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_JSON_OUT as DEFAULT_PLAN_JSON,
)
from semantic_llm_prompt_downstream_en_es import _load_json  # noqa: E402


DEFAULT_BATCH_DIR = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_run_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_run_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute or replay the no-spend example-frame missing-row generation plan, "
            "preserving raw responses plus raw/normalized semantic evidence batches."
        )
    )
    parser.add_argument("--plan-json", type=Path, default=DEFAULT_PLAN_JSON)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument(
        "--request-id",
        action="append",
        default=[],
        help="Optional request_id filter. Repeat to execute only a subset of planned rows.",
    )
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--chars-per-token", type=float, default=DEFAULT_CHARS_PER_TOKEN)
    parser.add_argument(
        "--expected-output-tokens", type=int, default=DEFAULT_EXPECTED_OUTPUT_TOKENS
    )
    parser.add_argument(
        "--require-selected-request-count",
        type=int,
        default=0,
        help="Live safety guard: fail unless selected request count matches this exact number.",
    )
    parser.add_argument("--input-rate-per-1m", type=float, default=None)
    parser.add_argument("--output-rate-per-1m", type=float, default=None)
    parser.add_argument("--max-estimated-cost-usd", type=float, default=None)
    parser.add_argument("--max-estimated-cost-ceiling-usd", type=float, default=None)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--replay-json", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_example_frame_generation_run_bundle(
    *,
    plan_payload: Mapping[str, object],
    responses_client: Any,
    batch_dir: Path,
    execution_mode: str = "live",
    replay_source: str = "",
    request_ids: Sequence[str] | None = None,
    max_requests: int = 0,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    generated_at: str | None = None,
    run_id: str = "",
    resume: bool = False,
) -> dict[str, object]:
    resolved_execution_mode = str(execution_mode or "").strip().lower() or "live"
    if resolved_execution_mode not in {"live", "replay"}:
        raise ValueError("execution_mode must be `live` or `replay`.")
    resolved_run_id = str(run_id or "").strip()
    if generated_at is None:
        generated_at = _utc_now()

    selected_request_rows = _select_request_rows(
        plan_payload.get("request_rows"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
    pair = str(plan_payload.get("pair") or "").strip() or "en-es"
    prompt_version = str(plan_payload.get("prompt_version") or "").strip()
    source_id = str(plan_payload.get("source_id") or "").strip() or "llm_example_frame_missing_rows"
    batch_id = _build_batch_id(
        pair=pair,
        generated_at=generated_at,
        execution_mode=resolved_execution_mode,
        run_id=resolved_run_id,
    )
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
            spec_slot={"roles": _string_list(request_row.get("roles"))},
            prompt_version=prompt_version,
            stage="example_frame_missing_rows",
            responses_client=responses_client,
            max_output_tokens=max_output_tokens,
            raw_response_ref=_bundle_ref(raw_response_bundle_path, request_id),
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
        pair=pair,
        source_id=source_id,
        prompt_version=prompt_version,
        execution_mode=resolved_execution_mode,
        replay_source=replay_source,
        generated_at=generated_at,
        selected_model_id=str(plan_payload.get("selected_model_id") or "").strip(),
        selected_temperature=float(plan_payload.get("selected_temperature") or 0.0),
        requests=raw_request_rows,
    )
    aggregate_cost = _aggregate_cost_metadata(raw_request_rows)
    intake_batch = None
    normalized_batch = None
    if intake_items:
        intake_batch = {
            "schema_version": 1,
            "batch_id": batch_id,
            "pair": pair,
            "source_type": "llm",
            "source_id": source_id,
            "source_family": "silver_llm_generation",
            "roles": _merge_request_roles(selected_request_rows),
            "generated_at": generated_at,
            "ingested_at": generated_at,
            "review_state": "unreviewed",
            "model_id": str(plan_payload.get("selected_model_id") or "").strip(),
            "prompt_version": prompt_version,
            "temperature": float(plan_payload.get("selected_temperature") or 0.0),
            "cost_metadata": aggregate_cost,
            "provenance": {
                "generation_plan_batch_id": str(plan_payload.get("base_batch_id") or "").strip(),
                "required_family_source": str(
                    plan_payload.get("required_family_source") or ""
                ).strip(),
                "execution_mode": resolved_execution_mode,
                "raw_response_bundle_ref": _display_path(raw_response_bundle_path),
            },
            "items": intake_items,
        }
        if replay_source:
            intake_batch["provenance"]["replay_source"] = replay_source
        normalized_batch = normalize_llm_intake_batch(intake_batch)

    summary = _build_summary(
        selected_request_count=len(selected_request_rows),
        request_outcomes=request_outcomes,
        normalized_batch=normalized_batch,
        aggregate_cost=aggregate_cost,
    )
    report = {
        "schema_version": 1,
        "status": _resolve_status(summary),
        "pair": pair,
        "generated_at": generated_at,
        "execution_mode": resolved_execution_mode,
        "replay_source": replay_source,
        "batch_id": batch_id,
        "source_id": source_id,
        "prompt_version": prompt_version,
        "selected_model_id": str(plan_payload.get("selected_model_id") or "").strip(),
        "selected_temperature": float(plan_payload.get("selected_temperature") or 0.0),
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


def write_example_frame_generation_run_bundle(
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
    markdown_out.write_text(render_example_frame_generation_run_markdown(report), encoding="utf-8")


def build_example_frame_execution_safety_report(
    *,
    plan_payload: Mapping[str, object],
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
    selected_request_rows = _select_request_rows(
        plan_payload.get("request_rows"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
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
        "source_id": str(plan_payload.get("source_id") or "").strip(),
        "prompt_version": str(plan_payload.get("prompt_version") or "").strip(),
        "selected_model_id": str(plan_payload.get("selected_model_id") or "").strip(),
        "summary": summary,
        "request_rows": request_rows,
    }


def render_example_frame_generation_run_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), Mapping) else {}
    lines = [
        "# en-es LLM Example-Frame Generation Run",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Execution mode: `{report.get('execution_mode', '')}`",
        f"- Batch id: `{report.get('batch_id', '')}`",
        f"- Source id: `{report.get('source_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Selected requests: `{summary.get('selected_request_count', 0)}`",
        f"- Accepted items: `{summary.get('accepted_item_count', 0)}`",
        f"- API errors: `{summary.get('api_error_count', 0)}`",
        f"- Invalid outputs: `{summary.get('invalid_output_count', 0)}`",
        f"- Normalized rows: `{summary.get('normalized_row_count', 0)}`",
        f"- Input tokens: `{summary.get('input_tokens', 0)}`",
        f"- Output tokens: `{summary.get('output_tokens', 0)}`",
        "",
        "## Artifacts",
        "",
        f"- Journal: `{artifacts.get('journal_jsonl', 'n/a')}`",
        f"- Raw responses: `{artifacts.get('raw_response_bundle_json', 'n/a')}`",
        f"- Intake batch: `{artifacts.get('intake_batch_json', 'n/a')}`",
        f"- Normalized batch: `{artifacts.get('normalized_batch_json', 'n/a')}`",
        "",
        "## Request Outcomes",
        "",
        "| Request | Target | Family | Status | Output |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report.get("request_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('request_id', '')}`",
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('status', '')}`",
                    _render_request_outcome(row),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _select_request_rows(
    value: object,
    *,
    request_ids: Sequence[str] | None,
    max_requests: int,
) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("plan request_rows must be an array of objects")
    rows = [dict(row) for row in value if isinstance(row, Mapping)]
    requested_ids = {str(item).strip() for item in (request_ids or ()) if str(item).strip()}
    selected = (
        [row for row in rows if str(row.get("request_id") or "").strip() in requested_ids]
        if requested_ids
        else rows
    )
    if max_requests > 0:
        selected = selected[:max_requests]
    if not selected:
        raise ValueError("No example-frame requests selected for execution.")
    return selected


def _build_raw_response_bundle(
    *,
    batch_id: str,
    pair: str,
    source_id: str,
    prompt_version: str,
    execution_mode: str,
    replay_source: str,
    generated_at: str,
    selected_model_id: str,
    selected_temperature: float,
    requests: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": pair,
        "source_id": source_id,
        "prompt_version": prompt_version,
        "execution_mode": execution_mode,
        "replay_source": replay_source,
        "generated_at": generated_at,
        "selected_model_id": selected_model_id,
        "selected_temperature": selected_temperature,
        "request_count": len(requests),
        "requests": [dict(row) for row in requests],
    }


def _aggregate_cost_metadata(request_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    completed_count = 0
    for row in request_rows:
        usage = row.get("usage")
        usage_map = usage if isinstance(usage, Mapping) else {}
        if usage_map:
            completed_count += 1
        input_tokens += int(usage_map.get("input_tokens") or 0)
        output_tokens += int(usage_map.get("output_tokens") or 0)
        output_details = usage_map.get("output_tokens_details")
        output_details_map = output_details if isinstance(output_details, Mapping) else {}
        reasoning_tokens += int(output_details_map.get("reasoning_tokens") or 0)
    return {
        "request_count": len(request_rows),
        "requests_with_usage": completed_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
    }


def _build_summary(
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


def _resolve_status(summary: Mapping[str, object]) -> str:
    selected = int(summary.get("selected_request_count") or 0)
    accepted = int(summary.get("accepted_item_count") or 0)
    if accepted == 0:
        return "error"
    if accepted < selected:
        return "partial"
    return "ok"


def _merge_request_roles(rows: Sequence[Mapping[str, object]]) -> list[str]:
    merged: list[str] = []
    for row in rows:
        for role in _string_list(row.get("roles")):
            if role not in merged:
                merged.append(role)
    return merged or ["discrimination"]


def _string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _render_request_outcome(row: Mapping[str, object]) -> str:
    status = str(row.get("status") or "").strip()
    if status == "accepted":
        return _truncate_markdown_cell(str(row.get("evidence_text") or "").strip())
    return _truncate_markdown_cell(str(row.get("error_message") or "n/a").strip())


def _truncate_markdown_cell(value: str, *, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text.replace("|", "\\|") or "n/a"
    return (text[: limit - 3].rstrip() + "...").replace("|", "\\|")


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
    return f"{pair}:example-frame-missing-rows:{run_component}{suffix}"


def _as_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError("expected path value")
    return Path(text)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    if args.execute_live and args.replay_json is not None:
        raise SystemExit("Use either --execute-live or --replay-json, not both.")
    if args.resume and args.replay_json is not None:
        raise SystemExit("Replay runs do not support --resume.")

    generated_at = _utc_now()
    plan_payload = _load_json(args.plan_json)

    execution_mode = "live"
    replay_source = ""
    if args.replay_json is not None:
        responses_client = _ReplayResponsesClient(_load_json(args.replay_json))
        execution_mode = "replay"
        replay_source = _display_path(args.replay_json)
    elif not args.execute_live:
        raise SystemExit(
            "Refusing to spend API budget without --execute-live. "
            "Run with --replay-json for no-spend rehearsal."
        )
    else:
        safety_report = build_example_frame_execution_safety_report(
            plan_payload=plan_payload,
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

    bundle = build_example_frame_generation_run_bundle(
        plan_payload=plan_payload,
        responses_client=responses_client,
        batch_dir=args.batch_dir,
        execution_mode=execution_mode,
        replay_source=replay_source,
        request_ids=args.request_id,
        max_requests=args.max_requests,
        max_output_tokens=args.max_output_tokens,
        generated_at=generated_at,
        run_id=args.run_id,
        resume=args.resume,
    )
    write_example_frame_generation_run_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
    )
    report = bundle["report"]
    print(f"Wrote summary JSON to {args.json_out}")
    print(f"Wrote summary Markdown to {args.markdown_out}")
    print(f"Batch status: {report['status']}")
    print(f"Accepted items: {report['summary']['accepted_item_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
