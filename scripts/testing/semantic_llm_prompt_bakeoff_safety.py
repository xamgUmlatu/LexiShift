from __future__ import annotations

import math
import os
from typing import Any, Mapping, Sequence

from semantic_llm_prompt_bakeoff_common import (
    DEFAULT_CHARS_PER_TOKEN,
    DEFAULT_EXPECTED_OUTPUT_TOKENS,
    DEFAULT_MAX_OUTPUT_TOKENS,
    _coerce_mapping,
    _mapping_rows,
    _slug,
    _utc_now,
)
from semantic_llm_prompt_smoke import build_prompt_smoke_report


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
