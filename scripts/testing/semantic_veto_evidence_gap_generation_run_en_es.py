#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_llm_prompt_bakeoff_en_es import (  # noqa: E402
    _assert_live_safety_guards,
    _build_responses_client,
    _display_path,
    _ReplayResponsesClient,
)
from semantic_veto_evidence_gap_generation_run_core import (  # noqa: E402
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL_ID,
    DEFAULT_TEMPERATURE,
    build_evidence_gap_generation_run_bundle as build_evidence_gap_generation_run_bundle,
    write_evidence_gap_generation_run_bundle as write_evidence_gap_generation_run_bundle,
    _load_json,
    _utc_now,
)
from semantic_veto_evidence_gap_generation_run_rendering import (  # noqa: E402
    render_evidence_gap_generation_run_markdown as render_evidence_gap_generation_run_markdown,
)
from semantic_veto_evidence_gap_generation_run_safety import (  # noqa: E402
    DEFAULT_CHARS_PER_TOKEN,
    DEFAULT_EXPECTED_OUTPUT_TOKENS,
    build_evidence_gap_generation_execution_safety_report as build_evidence_gap_generation_execution_safety_report,
)


DEFAULT_REQUEST_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_evidence_gap_generation_requests_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_evidence_gap_generation_run_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_evidence_gap_generation_run_en_es_latest.md"
)
DEFAULT_GENERATED_RESPONSES_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_evidence_gap_generated_responses_en_es_latest.json"
)
DEFAULT_BATCH_DIR = (
    PROJECT_ROOT / "docs" / "test_outputs" / "experiments" / "semantic_veto_evidence_gap_batches"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute or replay a bounded generation run for the en-es semantic-veto "
            "evidence-gap pilot. Live runs require explicit cardinality and spend guards."
        )
    )
    parser.add_argument("--request-json", type=Path, default=DEFAULT_REQUEST_JSON)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--request-id", action="append", default=[])
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument(
        "--omit-temperature",
        action="store_true",
        help=(
            "Do not send a temperature parameter to the Responses API. "
            "Use this for models that reject sampling controls."
        ),
    )
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
    parser.add_argument("--retry-invalid-outputs", action="store_true")
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--generated-responses-out", type=Path, default=DEFAULT_GENERATED_RESPONSES_OUT
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.execute_live and args.replay_json is not None:
        raise SystemExit("Use either --execute-live or --replay-json, not both.")
    if args.resume and args.replay_json is not None:
        raise SystemExit("Replay runs do not support --resume.")

    generated_at = _utc_now()
    request_payload = dict(_load_json(args.request_json))
    request_payload["_request_json_path"] = _display_path(args.request_json)
    if args.replay_json is not None:
        responses_client = _ReplayResponsesClient(_load_json(args.replay_json))
        execution_mode = "replay"
        replay_source = _display_path(args.replay_json)
    elif args.execute_live:
        safety_report = build_evidence_gap_generation_execution_safety_report(
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
        execution_mode = "live"
        replay_source = ""
    else:
        raise SystemExit(
            "Refusing to spend API budget without --execute-live. "
            "Use --replay-json for a no-spend rehearsal."
        )

    bundle = build_evidence_gap_generation_run_bundle(
        request_payload=request_payload,
        responses_client=responses_client,
        batch_dir=args.batch_dir,
        model_id=args.model_id,
        temperature=None if args.omit_temperature else args.temperature,
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
    write_evidence_gap_generation_run_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        generated_responses_out=args.generated_responses_out,
    )
    report = bundle["report"]
    print(f"Wrote summary JSON to {args.json_out}")
    print(f"Wrote summary Markdown to {args.markdown_out}")
    print(f"Wrote generated responses JSON to {args.generated_responses_out}")
    print(f"Batch status: {report['status']}")
    print(f"Accepted responses: {report['summary']['accepted_response_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
