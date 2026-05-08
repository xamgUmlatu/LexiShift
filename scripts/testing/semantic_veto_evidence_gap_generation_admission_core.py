from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_product_quality_en_es import _repo_path  # noqa: E402
from semantic_veto_evidence_gap_generation_admission_summary import (  # noqa: E402
    _alignment_summary,
    _coverage_rows,
    _decision,
    _next_steps,
    _rejection_reasons,
    _status,
    _summary,
)
from semantic_veto_evidence_gap_generation_admission_checks import (  # noqa: E402
    _contains_loose_lemma,
    _contains_negative_judgment,
    _contains_runtime_trigger,
    _has_label_leakage,
    _has_no_winner_context_anchor,
    _has_weak_no_winner_container,
    _normalize_no_winner_context_class,
)


ACTIVE_SLOT = "active_evidence_expansion"
SHADOW_SLOT = "shadow_or_competitor_evidence_probe"
NO_WINNER_SLOT = "no_winner_context_probe"
REQUEST_KIND = "semantic_veto_evidence_gap_generation"
SLOT_TYPE_ORDER = (ACTIVE_SLOT, SHADOW_SLOT, NO_WINNER_SLOT)
SLOT_ITEM_REQUIRED_FIELDS = {
    ACTIVE_SLOT: ("sentence", "evidence_note"),
    SHADOW_SLOT: ("sentence", "evidence_note", "active_mismatch_note"),
    NO_WINNER_SLOT: ("sentence", "no_winner_context_class", "runtime_trigger_note"),
}
SHADOW_CONTRAST_FIELDS = ("competitor_sense_label", "active_sense_contrast")
ALLOWED_NO_WINNER_CONTEXT_CLASSES = frozenset(
    {
        "proper_name_or_title",
        "code_or_identifier",
        "quoted_or_mentioned_word",
        "unrelated_named_entity",
        "source_language_meta_use",
        "ui_label",
    }
)


def build_evidence_gap_generation_admission_report(
    *,
    generation_requests_payload: Mapping[str, object],
    generation_requests_path: Path | None = None,
    generated_responses_payload: object | None = None,
    generated_responses_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    request_rows = _mapping_rows(generation_requests_payload.get("requests"))
    request_issues = _validate_request_packet(generation_requests_payload, request_rows)
    requests_by_id = {
        str(row.get("request_id") or ""): row
        for row in request_rows
        if str(row.get("request_id") or "")
    }
    generated_responses = _generated_responses(generated_responses_payload)
    generated_responses_present = generated_responses_payload is not None
    selected_request_ids = _selected_request_ids(generated_responses_payload)
    expected_request_ids = selected_request_ids or frozenset(requests_by_id)
    response_results = (
        _admit_responses(
            responses=generated_responses,
            requests_by_id=requests_by_id,
            expected_request_ids=expected_request_ids,
        )
        if generated_responses_present
        else []
    )
    admitted_items = [
        item
        for response in response_results
        for item in _mapping_rows(response.get("admitted_items"))
    ]
    rejected_items = [
        item
        for response in response_results
        for item in _mapping_rows(response.get("rejected_items"))
    ]
    response_level_errors = [
        response
        for response in response_results
        if _as_sequence(response.get("response_rejection_reasons"))
    ]
    coverage_rows = _coverage_rows(
        requests_by_id=requests_by_id,
        expected_request_ids=expected_request_ids,
        admitted_items=admitted_items,
        response_results=response_results,
    )
    coverage_shortfalls = [row for row in coverage_rows if int(row.get("shortfall_count") or 0) > 0]
    alignment = _alignment_summary(
        requests_by_id=requests_by_id,
        expected_request_ids=expected_request_ids,
        responses=generated_responses,
        response_results=response_results,
        generated_responses_present=generated_responses_present,
    )
    alignment_errors = [
        issue
        for issue in _mapping_rows(alignment.get("issues"))
        if issue.get("severity") == "error"
    ]
    status = _status(
        request_issues=request_issues,
        generated_responses_present=generated_responses_present,
        response_level_errors=response_level_errors,
        rejected_items=rejected_items,
        coverage_shortfalls=coverage_shortfalls,
        alignment_errors=alignment_errors,
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": _decision(
            status=status,
            generated_responses_present=generated_responses_present,
            response_level_errors=response_level_errors,
            rejected_items=rejected_items,
            coverage_shortfalls=coverage_shortfalls,
            alignment_errors=alignment_errors,
        ),
        "generated_at": generated_at,
        "pair": str(generation_requests_payload.get("pair") or "en-es"),
        "pilot": {
            "pilot_id": str(
                _as_mapping(generation_requests_payload.get("pilot")).get("pilot_id") or ""
            ),
            "request_kind": REQUEST_KIND,
            "generation_requests_path": _repo_path(generation_requests_path),
            "generated_responses_path": _repo_path(generated_responses_path),
            "generated_responses_present": generated_responses_present,
        },
        "strict_flow": {
            "runtime_policy_change": "none",
            "threshold_tuning": "none",
            "source_evidence_promotion": "none",
            "admission_role": "pre_scoring_generated_response_filter",
            "selected_request_subset_allowed": bool(selected_request_ids),
        },
        "request_packet_checks": {
            "issue_count": len(request_issues),
            "issues": request_issues,
            "request_count": len(request_rows),
            "unique_request_ids": len(requests_by_id) == len(request_rows),
        },
        "summary": _summary(
            request_rows=request_rows,
            expected_request_ids=expected_request_ids,
            generated_responses=generated_responses,
            admitted_items=admitted_items,
            rejected_items=rejected_items,
            response_level_errors=response_level_errors,
            coverage_rows=coverage_rows,
        ),
        "alignment": alignment,
        "coverage": coverage_rows,
        "rejection_reasons": _rejection_reasons(
            response_results=response_results,
            rejected_items=rejected_items,
        ),
        "response_results": response_results,
        "admitted_items": admitted_items,
        "rejected_items": rejected_items,
        "next_steps": _next_steps(
            generated_responses_present=generated_responses_present,
            request_issues=request_issues,
            response_level_errors=response_level_errors,
            rejected_items=rejected_items,
            coverage_shortfalls=coverage_shortfalls,
            alignment_errors=alignment_errors,
        ),
        "limitations": [
            "research-only generated-response admission lane",
            "no LLM call is made by this script",
            "no generated item is source evidence until a later explicit promotion step",
            "no runtime policy or threshold changes are made",
            "semantic correctness of generated text still needs scoring and spot review",
        ],
    }


def _validate_request_packet(
    payload: Mapping[str, object],
    request_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if int(payload.get("schema_version") or 0) != 1:
        issues.append(_issue("schema_version", "error", "Expected request schema_version 1."))
    if str(payload.get("status") or "") != "ok":
        issues.append(_issue("status", "error", "Generation request packet is not ok."))
    pilot = _as_mapping(payload.get("pilot"))
    if str(pilot.get("request_kind") or "") != REQUEST_KIND:
        issues.append(_issue("request_kind", "error", "Unexpected request kind."))
    request_ids = [str(row.get("request_id") or "") for row in request_rows]
    if not request_rows:
        issues.append(_issue("requests", "error", "No generation requests found."))
    if len(set(request_ids)) != len(request_ids):
        issues.append(_issue("request_id", "error", "Duplicate request ids in packet."))
    for row in request_rows:
        request_id = str(row.get("request_id") or "")
        for field in (
            "family_id",
            "slot_id",
            "slot_type",
            "trigger",
            "active_target_lemma",
            "requested_items",
        ):
            if not str(row.get(field) or "").strip():
                issues.append(_issue(request_id, "error", f"Request lacks {field}."))
        if str(row.get("slot_type") or "") not in SLOT_TYPE_ORDER:
            issues.append(_issue(request_id, "error", "Request has unsupported slot_type."))
        if int(row.get("requested_items") or 0) <= 0:
            issues.append(_issue(request_id, "error", "Request has no requested items."))
    return issues


def _admit_responses(
    *,
    responses: Sequence[Mapping[str, object]],
    requests_by_id: Mapping[str, Mapping[str, object]],
    expected_request_ids: frozenset[str],
) -> list[dict[str, object]]:
    seen_response_request_ids: set[str] = set()
    seen_sentences: set[str] = set()
    results: list[dict[str, object]] = []
    for response in responses:
        request_id = str(response.get("request_id") or "").strip()
        request = requests_by_id.get(request_id)
        response_reasons = _response_rejection_reasons(
            response=response,
            request=request,
            expected_request_ids=expected_request_ids,
            seen_response_request_ids=seen_response_request_ids,
        )
        if request_id:
            seen_response_request_ids.add(request_id)
        admitted_items: list[dict[str, object]] = []
        rejected_items: list[dict[str, object]] = []
        if request is not None and not response_reasons:
            for index, item in enumerate(_mapping_rows(response.get("items")), start=1):
                public_item, reasons = _admit_item(
                    item=item,
                    item_index=index,
                    response=response,
                    request=request,
                    seen_sentences=seen_sentences,
                )
                if reasons:
                    public_item["admission_status"] = "rejected"
                    public_item["rejection_reasons"] = sorted(set(reasons))
                    rejected_items.append(public_item)
                else:
                    public_item["admission_status"] = "admitted"
                    public_item["rejection_reasons"] = []
                    admitted_items.append(public_item)
        results.append(
            {
                "request_id": request_id,
                "family_id": str(response.get("family_id") or ""),
                "slot_id": str(response.get("slot_id") or ""),
                "slot_type": str(response.get("slot_type") or ""),
                "response_rejection_reasons": sorted(set(response_reasons)),
                "item_count": len(_mapping_rows(response.get("items"))),
                "admitted_item_count": len(admitted_items),
                "rejected_item_count": len(rejected_items),
                "no_competitor_marker": _is_no_competitor_marker(response=response, request=request)
                if request is not None
                else False,
                "admitted_items": admitted_items,
                "rejected_items": rejected_items,
            }
        )
    return results


def _response_rejection_reasons(
    *,
    response: Mapping[str, object],
    request: Mapping[str, object] | None,
    expected_request_ids: frozenset[str],
    seen_response_request_ids: set[str],
) -> list[str]:
    reasons: list[str] = []
    request_id = str(response.get("request_id") or "").strip()
    if not request_id:
        reasons.append("missing_request_id")
    elif request_id not in expected_request_ids:
        reasons.append("unexpected_request_id")
    if request_id in seen_response_request_ids:
        reasons.append("duplicate_response_request_id")
    if request is None:
        reasons.append("unknown_request_id")
        return reasons
    for field in ("family_id", "slot_id", "slot_type", "source_phrase", "target_lemma", "items"):
        if field not in response:
            reasons.append(f"missing_response_field:{field}")
    field_pairs = {
        "family_id": "family_id",
        "slot_id": "slot_id",
        "slot_type": "slot_type",
        "source_phrase": "trigger",
    }
    for response_field, request_field in field_pairs.items():
        response_value = _normalize_text(str(response.get(response_field) or ""))
        request_value = _normalize_text(str(request.get(request_field) or ""))
        if response_value != request_value:
            reasons.append(f"request_mismatch:{response_field}")
    slot_type = str(request.get("slot_type") or "")
    response_target = str(response.get("target_lemma") or "").strip()
    proposed_target = str(response.get("proposed_competitor_target_lemma") or "").strip()
    slot_target = str(request.get("slot_target_lemma") or "").strip()
    active_target = str(request.get("active_target_lemma") or "").strip()
    no_competitor_marker = _is_no_competitor_marker(response=response, request=request)
    if slot_type == ACTIVE_SLOT and _normalize_text(response_target) != _normalize_text(
        slot_target
    ):
        reasons.append("request_mismatch:target_lemma")
    if slot_type == NO_WINNER_SLOT and response_target:
        reasons.append("no_winner_target_lemma_must_be_blank")
    if (
        slot_type == SHADOW_SLOT
        and not no_competitor_marker
        and not (
            response_target or str(response.get("proposed_competitor_target_lemma") or "").strip()
        )
    ):
        reasons.append("missing_competitor_target_lemma")
    if slot_type == SHADOW_SLOT and not no_competitor_marker:
        for field in SHADOW_CONTRAST_FIELDS:
            if not str(response.get(field) or "").strip():
                reasons.append(f"missing_response_field:{field}")
        if proposed_target and _normalize_text(proposed_target) == _normalize_text(active_target):
            reasons.append("proposed_competitor_reuses_active_target_lemma")
        if (
            response_target
            and proposed_target
            and _normalize_text(response_target) != _normalize_text(proposed_target)
        ):
            reasons.append("conflicting_competitor_target_lemmas")
        if (
            slot_target
            and proposed_target
            and _normalize_text(proposed_target) != _normalize_text(slot_target)
        ):
            reasons.append("request_mismatch:proposed_competitor_target_lemma")
    if slot_type == SHADOW_SLOT and no_competitor_marker and _mapping_rows(response.get("items")):
        reasons.append("no_competitor_marker_must_have_empty_items")
    if slot_type == SHADOW_SLOT and response_target and slot_target:
        if _normalize_text(response_target) != _normalize_text(slot_target):
            reasons.append("request_mismatch:target_lemma")
    if slot_type in {SHADOW_SLOT, NO_WINNER_SLOT} and _normalize_text(
        response_target
    ) == _normalize_text(active_target):
        reasons.append("non_active_slot_reuses_active_target_lemma")
    if not isinstance(response.get("items"), Sequence) or isinstance(
        response.get("items"), (str, bytes)
    ):
        reasons.append("items_not_list")
    elif not _mapping_rows(response.get("items")) and not no_competitor_marker:
        reasons.append("items_empty")
    return reasons


def _admit_item(
    *,
    item: Mapping[str, object],
    item_index: int,
    response: Mapping[str, object],
    request: Mapping[str, object],
    seen_sentences: set[str],
) -> tuple[dict[str, object], list[str]]:
    slot_type = str(request.get("slot_type") or "")
    sentence = str(item.get("sentence") or "").strip()
    normalized_sentence = _normalize_text(sentence)
    reasons: list[str] = []
    required_fields = SLOT_ITEM_REQUIRED_FIELDS.get(slot_type, ("sentence", "evidence_note"))
    for field in required_fields:
        if not str(item.get(field) or "").strip():
            reasons.append(f"missing_item_field:{field}")
    if item_index > int(request.get("requested_items") or 0):
        reasons.append("exceeds_requested_item_count")
    if sentence and not _contains_runtime_trigger(sentence, str(request.get("trigger") or "")):
        reasons.append("source_phrase_missing_or_not_runtime_like")
    if slot_type == NO_WINNER_SLOT:
        context_class = _normalize_no_winner_context_class(
            str(item.get("no_winner_context_class") or "")
        )
        if context_class and context_class not in ALLOWED_NO_WINNER_CONTEXT_CLASSES:
            reasons.append("invalid_no_winner_context_class")
        if sentence and _has_weak_no_winner_container(sentence):
            reasons.append("weak_no_winner_technical_container")
        if (
            sentence
            and context_class
            and not _has_no_winner_context_anchor(
                sentence=sentence,
                context_class=context_class,
            )
        ):
            reasons.append("no_winner_context_lacks_visible_nontranslation_anchor")
    if slot_type == SHADOW_SLOT and sentence:
        mismatch_note = str(item.get("active_mismatch_note") or "")
        if not _contains_loose_lemma(
            mismatch_note,
            str(request.get("active_target_lemma") or ""),
        ):
            reasons.append("active_mismatch_note_missing_active_target_lemma")
        competitor_target = (
            str(response.get("target_lemma") or "").strip()
            or str(response.get("proposed_competitor_target_lemma") or "").strip()
        )
        if (
            competitor_target
            and _contains_loose_lemma(mismatch_note, competitor_target)
            and _contains_negative_judgment(mismatch_note)
        ):
            reasons.append("active_mismatch_note_declares_competitor_wrong")
    if normalized_sentence in seen_sentences and normalized_sentence:
        reasons.append("duplicate_sentence")
    if normalized_sentence:
        seen_sentences.add(normalized_sentence)
    if sentence and _has_label_leakage(sentence, source_phrase=str(request.get("trigger") or "")):
        reasons.append("label_leakage_in_sentence")
    for lemma in _blocked_target_lemmas(response=response, request=request):
        if sentence and _contains_runtime_trigger(sentence, lemma):
            reasons.append("spanish_target_lemma_in_sentence")
            break
    public_item = _public_item(
        item=item,
        item_index=item_index,
        response=response,
        request=request,
    )
    return public_item, reasons


def _public_item(
    *,
    item: Mapping[str, object],
    item_index: int,
    response: Mapping[str, object],
    request: Mapping[str, object],
) -> dict[str, object]:
    request_id = str(response.get("request_id") or "")
    item_id = f"{request_id}:item:{item_index:03d}"
    return {
        "item_id": item_id,
        "request_id": request_id,
        "family_id": str(request.get("family_id") or ""),
        "pilot_arm": str(request.get("pilot_arm") or ""),
        "arm_rank": int(request.get("arm_rank") or 0),
        "global_need_rank": int(request.get("global_need_rank") or 0),
        "predicted_need": request.get("predicted_need"),
        "slot_id": str(request.get("slot_id") or ""),
        "slot_type": str(request.get("slot_type") or ""),
        "source_phrase": str(request.get("trigger") or ""),
        "active_target_lemma": str(request.get("active_target_lemma") or ""),
        "target_lemma": str(response.get("target_lemma") or ""),
        "proposed_competitor_target_lemma": str(
            response.get("proposed_competitor_target_lemma") or ""
        ),
        "competitor_sense_label": str(response.get("competitor_sense_label") or "").strip(),
        "active_sense_contrast": str(response.get("active_sense_contrast") or "").strip(),
        "sentence": str(item.get("sentence") or "").strip(),
        "evidence_note": str(item.get("evidence_note") or "").strip(),
        "active_mismatch_note": str(item.get("active_mismatch_note") or "").strip(),
        "no_winner_context_class": _normalize_no_winner_context_class(
            str(item.get("no_winner_context_class") or "")
        ),
        "no_winner_reason": str(item.get("no_winner_reason") or "").strip(),
        "runtime_trigger_note": str(item.get("runtime_trigger_note") or "").strip(),
    }


def _is_no_competitor_marker(
    *,
    response: Mapping[str, object],
    request: Mapping[str, object],
) -> bool:
    if str(request.get("slot_type") or "") != SHADOW_SLOT:
        return False
    if not bool(response.get("unable_to_find_distinct_competitor")):
        return False
    return bool(str(response.get("no_distinct_competitor_reason") or "").strip())


def _generated_responses(payload: object | None) -> list[Mapping[str, object]]:
    if payload is None:
        return []
    if isinstance(payload, Mapping):
        if "responses" in payload:
            return _mapping_rows(payload.get("responses"))
        if "response_objects" in payload:
            return _mapping_rows(payload.get("response_objects"))
        if "request_id" in payload and "items" in payload:
            return [payload]
        return []
    return _mapping_rows(payload)


def _selected_request_ids(payload: object | None) -> frozenset[str] | None:
    if not isinstance(payload, Mapping):
        return None
    selected = payload.get("selected_request_ids")
    if not isinstance(selected, Sequence) or isinstance(selected, (str, bytes)):
        return None
    values = frozenset(str(value).strip() for value in selected if str(value).strip())
    return values or None


def _blocked_target_lemmas(
    *,
    response: Mapping[str, object],
    request: Mapping[str, object],
) -> list[str]:
    values: list[str] = []
    values.append(str(request.get("active_target_lemma") or ""))
    values.append(str(request.get("slot_target_lemma") or ""))
    values.append(str(response.get("target_lemma") or ""))
    values.append(str(response.get("proposed_competitor_target_lemma") or ""))
    values.extend(str(value) for value in request.get("known_shadow_targets") or ())
    return sorted({value.strip() for value in values if value and value.strip()})


def _issue(subject: str, severity: str, message: str) -> dict[str, object]:
    return {"subject": subject, "severity": severity, "message": message}


def _load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
