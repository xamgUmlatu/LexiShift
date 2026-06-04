#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prompt_bakeoff_en_es import _load_json, _select_request_rows  # noqa: E402
from semantic_llm_prompt_reporting import render_prompt_cost_estimate_markdown  # noqa: E402
from semantic_llm_prompt_smoke import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_FAMILY_INVENTORY_JSON,
    DEFAULT_PROMPT_SPEC_JSON,
    DEFAULT_QUEUE_JSON,
    DEFAULT_SLOT_MANIFEST_JSON,
    build_prompt_smoke_report,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402

DEFAULT_COST_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_cost_estimate_latest.json"
)
DEFAULT_COST_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_cost_estimate_latest.md"
)
DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_EXPECTED_OUTPUT_TOKENS = 90
DEFAULT_MAX_OUTPUT_TOKENS = 300


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate token volume and optional spend for the frozen en-es prompt bakeoff slice "
            "without making any live API calls."
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
        help="Bakeoff stage to estimate.",
    )
    parser.add_argument(
        "--request-id",
        action="append",
        default=[],
        help="Optional request_id filter. Repeat to estimate only a subset of rendered requests.",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=0,
        help="Optional cap on the number of rendered requests after filtering.",
    )
    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=DEFAULT_CHARS_PER_TOKEN,
        help="Heuristic characters-per-token ratio used for input-token estimation.",
    )
    parser.add_argument(
        "--expected-output-tokens",
        type=int,
        default=DEFAULT_EXPECTED_OUTPUT_TOKENS,
        help="Expected output token count per request for the first-pass estimate.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=DEFAULT_MAX_OUTPUT_TOKENS,
        help="Output token ceiling per request.",
    )
    parser.add_argument(
        "--input-rate-per-1m",
        type=float,
        default=None,
        help="Optional pricing input rate per 1M tokens; omit to render token estimates only.",
    )
    parser.add_argument(
        "--output-rate-per-1m",
        type=float,
        default=None,
        help="Optional pricing output rate per 1M tokens; omit to render token estimates only.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_COST_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_COST_MARKDOWN_OUT)
    return parser.parse_args()


def build_prompt_cost_estimate_report(
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
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
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

    estimated_rows: list[dict[str, object]] = []
    total_input_tokens = 0
    for row in selected_request_rows:
        request_text = "\n".join(
            [
                str(row.get("system_prompt") or "").strip(),
                str(row.get("user_prompt") or "").strip(),
            ]
        ).strip()
        estimated_input_tokens = math.ceil(len(request_text) / chars_per_token)
        total_input_tokens += estimated_input_tokens
        estimated_rows.append(
            {
                "request_id": str(row.get("request_id") or "").strip(),
                "prompt_slot": str(row.get("prompt_slot") or "").strip(),
                "family_id": str(row.get("family_id") or "").strip(),
                "estimated_input_tokens": estimated_input_tokens,
                "expected_output_tokens": expected_output_tokens,
                "max_output_tokens": max_output_tokens,
            }
        )

    summary: dict[str, object] = {
        "selected_request_count": len(estimated_rows),
        "estimated_input_tokens": total_input_tokens,
        "expected_output_tokens": expected_output_tokens * len(estimated_rows),
        "max_output_tokens": max_output_tokens * len(estimated_rows),
    }
    rate_info: dict[str, object] = {}
    if input_rate_per_1m is not None and output_rate_per_1m is not None:
        rate_info = {
            "input_rate_per_1m": input_rate_per_1m,
            "output_rate_per_1m": output_rate_per_1m,
        }
        summary["estimated_cost_expected"] = round(
            (total_input_tokens / 1_000_000.0) * input_rate_per_1m
            + ((expected_output_tokens * len(estimated_rows)) / 1_000_000.0) * output_rate_per_1m,
            6,
        )
        summary["estimated_cost_ceiling"] = round(
            (total_input_tokens / 1_000_000.0) * input_rate_per_1m
            + ((max_output_tokens * len(estimated_rows)) / 1_000_000.0) * output_rate_per_1m,
            6,
        )

    report = {
        "schema_version": 1,
        "status": "ok",
        "generated_at": generated_at,
        "pair": str(smoke_report.get("pair") or "en-es"),
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "prompt_spec_id": str(prompt_spec_payload.get("spec_id") or "").strip(),
        "prompt_version": str(prompt_spec_payload.get("prompt_version") or "").strip(),
        "stage": stage,
        "selected_model_id": str(stage_config.get("model_id") or "").strip(),
        "input_token_heuristic": f"ceil(characters / {chars_per_token})",
        "summary": summary,
        "rate_info": rate_info,
        "request_rows": estimated_rows,
    }
    return report


def main() -> int:
    args = _parse_args()
    report = build_prompt_cost_estimate_report(
        queue_payload=_load_json(args.queue_json),
        slot_manifest_payload=_load_json(args.slot_manifest_json),
        family_inventory_payload=_load_json(args.family_inventory_json),
        prompt_spec_payload=_load_json(args.prompt_spec_json),
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        stage=args.stage,
        request_ids=args.request_id,
        max_requests=args.max_requests,
        chars_per_token=args.chars_per_token,
        expected_output_tokens=args.expected_output_tokens,
        max_output_tokens=args.max_output_tokens,
        input_rate_per_1m=args.input_rate_per_1m,
        output_rate_per_1m=args.output_rate_per_1m,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_prompt_cost_estimate_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
