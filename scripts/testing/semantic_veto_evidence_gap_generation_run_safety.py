from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Mapping, Sequence

from semantic_veto_evidence_gap_generation_run_core import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL_ID,
    _select_request_rows,
)


DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_EXPECTED_OUTPUT_TOKENS = 180


def build_evidence_gap_generation_execution_safety_report(
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
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be > 0")
    generated_at = generated_at or _utc_now()
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
                "family_id": str(row.get("family_id") or ""),
                "pilot_arm": str(row.get("pilot_arm") or ""),
                "slot_type": str(row.get("slot_type") or ""),
                "requested_items": int(row.get("requested_items") or 0),
                "estimated_input_tokens": input_tokens,
                "expected_output_tokens": expected_output_tokens,
                "max_output_tokens": max_output_tokens,
            }
        )
    summary = _safety_summary(
        request_rows=request_rows,
        estimated_input_tokens=estimated_input_tokens,
        expected_output_tokens=expected_output_tokens,
        max_output_tokens=max_output_tokens,
        input_rate_per_1m=input_rate_per_1m,
        output_rate_per_1m=output_rate_per_1m,
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "selected_model_id": model_id,
        "summary": summary,
        "request_rows": request_rows,
    }


def _safety_summary(
    *,
    request_rows: Sequence[Mapping[str, object]],
    estimated_input_tokens: int,
    expected_output_tokens: int,
    max_output_tokens: int,
    input_rate_per_1m: float | None,
    output_rate_per_1m: float | None,
) -> dict[str, object]:
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
    return summary


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
