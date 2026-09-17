from __future__ import annotations

import json
from typing import Callable, Mapping

NATIVE_MESSAGE_MAX_BYTES = 1024 * 1024


def encode_message(
    payload: Mapping[str, object],
    error_response: Callable[..., dict],
    log_line: Callable[[str], None],
) -> bytes:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(data) <= NATIVE_MESSAGE_MAX_BYTES:
        return data
    request_id = str(payload.get("id", ""))
    original_size = len(data)
    response = error_response(
        request_id,
        "The helper response was too large for the browser. Please update LexiShift "
        "or reduce the requested preview size.",
        code="response_too_large",
    )
    log_line(f"response_too_large request_id={request_id} bytes={original_size}")
    return json.dumps(response, ensure_ascii=False).encode("utf-8")
