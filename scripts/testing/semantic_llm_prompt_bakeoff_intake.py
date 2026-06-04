from __future__ import annotations

from typing import Mapping, Sequence

from semantic_llm_prompt_bakeoff_common import _coerce_mapping, _sense_hint, _string_list


_ALLOWED_MODEL_ITEM_KEYS = frozenset(
    {
        "evidence_text",
        "confidence",
    }
)


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
