from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence


ACTIVE_SLOT = "active_evidence_expansion"
SHADOW_SLOT = "shadow_or_competitor_evidence_probe"
NO_WINNER_SLOT = "no_winner_context_probe"


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _issue(subject: str, severity: str, message: str) -> dict[str, object]:
    return {"subject": subject, "severity": severity, "message": message}


def _coverage_rows(
    *,
    requests_by_id: Mapping[str, Mapping[str, object]],
    expected_request_ids: frozenset[str],
    admitted_items: Sequence[Mapping[str, object]],
    response_results: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    admitted_counts = Counter(str(item.get("request_id") or "") for item in admitted_items)
    no_competitor_marker_request_ids = {
        str(response.get("request_id") or "")
        for response in response_results
        if bool(response.get("no_competitor_marker"))
    }
    rows: list[dict[str, object]] = []
    for request_id in sorted(expected_request_ids):
        request = requests_by_id.get(request_id)
        if request is None:
            rows.append(
                {
                    "request_id": request_id,
                    "family_id": "",
                    "pilot_arm": "",
                    "slot_type": "",
                    "expected_item_count": 0,
                    "admitted_item_count": 0,
                    "waived_item_count": 0,
                    "shortfall_count": 0,
                }
            )
            continue
        expected = int(request.get("requested_items") or 0)
        admitted = admitted_counts.get(request_id, 0)
        waived = expected if request_id in no_competitor_marker_request_ids else 0
        rows.append(
            {
                "request_id": request_id,
                "family_id": str(request.get("family_id") or ""),
                "pilot_arm": str(request.get("pilot_arm") or ""),
                "slot_type": str(request.get("slot_type") or ""),
                "trigger": str(request.get("trigger") or ""),
                "expected_item_count": expected,
                "admitted_item_count": admitted,
                "waived_item_count": waived,
                "shortfall_count": max(0, expected - admitted - waived),
            }
        )
    return rows


def _alignment_summary(
    *,
    requests_by_id: Mapping[str, Mapping[str, object]],
    expected_request_ids: frozenset[str],
    responses: Sequence[Mapping[str, object]],
    response_results: Sequence[Mapping[str, object]],
    generated_responses_present: bool,
) -> dict[str, object]:
    response_request_ids = {
        str(response.get("request_id") or "").strip()
        for response in responses
        if str(response.get("request_id") or "").strip()
    }
    matched = expected_request_ids & response_request_ids
    missing = sorted(expected_request_ids - response_request_ids)
    unexpected = sorted(response_request_ids - set(requests_by_id))
    duplicate_count = sum(
        1
        for row in response_results
        if "duplicate_response_request_id" in _as_sequence(row.get("response_rejection_reasons"))
    )
    if not generated_responses_present:
        return {
            "expected_request_count": len(expected_request_ids),
            "response_request_count": 0,
            "matched_expected_request_count": 0,
            "missing_expected_request_ids": [],
            "unexpected_response_request_ids": [],
            "duplicate_response_request_count": 0,
            "issues": [],
        }
    issues = []
    if missing:
        issues.append(
            _issue(
                "missing_expected_request_ids",
                "error",
                f"{len(missing)} expected generated responses are missing.",
            )
        )
    if unexpected:
        issues.append(
            _issue(
                "unexpected_response_request_ids",
                "error",
                f"{len(unexpected)} generated responses are outside the request packet.",
            )
        )
    if duplicate_count:
        issues.append(
            _issue(
                "duplicate_response_request_ids",
                "error",
                f"{duplicate_count} duplicate generated responses were found.",
            )
        )
    return {
        "expected_request_count": len(expected_request_ids),
        "response_request_count": len(response_request_ids),
        "matched_expected_request_count": len(matched),
        "missing_expected_request_ids": missing,
        "unexpected_response_request_ids": unexpected,
        "duplicate_response_request_count": duplicate_count,
        "issues": issues,
    }


def _summary(
    *,
    request_rows: Sequence[Mapping[str, object]],
    expected_request_ids: frozenset[str],
    generated_responses: Sequence[Mapping[str, object]],
    admitted_items: Sequence[Mapping[str, object]],
    rejected_items: Sequence[Mapping[str, object]],
    response_level_errors: Sequence[Mapping[str, object]],
    coverage_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    request_by_id = {str(row.get("request_id") or ""): row for row in request_rows}
    selected_requests = [
        request_by_id[request_id]
        for request_id in expected_request_ids
        if request_id in request_by_id
    ]
    coverage_by_request_id = {str(row.get("request_id") or ""): row for row in coverage_rows}
    by_arm = _dimension_summary(
        selected_requests=selected_requests,
        admitted_items=admitted_items,
        rejected_items=rejected_items,
        coverage_by_request_id=coverage_by_request_id,
        dimension="pilot_arm",
    )
    by_slot_type = _dimension_summary(
        selected_requests=selected_requests,
        admitted_items=admitted_items,
        rejected_items=rejected_items,
        coverage_by_request_id=coverage_by_request_id,
        dimension="slot_type",
    )
    return {
        "total_request_packet_count": len(request_rows),
        "expected_request_count": len(expected_request_ids),
        "generated_response_count": len(generated_responses),
        "response_level_error_count": len(response_level_errors),
        "expected_item_count": sum(
            int(row.get("requested_items") or 0) for row in selected_requests
        ),
        "admitted_item_count": len(admitted_items),
        "rejected_item_count": len(rejected_items),
        "coverage_shortfall_count": sum(
            int(row.get("shortfall_count") or 0) for row in coverage_rows
        ),
        "coverage_waived_item_count": sum(
            int(row.get("waived_item_count") or 0) for row in coverage_rows
        ),
        "by_arm": by_arm,
        "by_slot_type": by_slot_type,
    }


def _dimension_summary(
    *,
    selected_requests: Sequence[Mapping[str, object]],
    admitted_items: Sequence[Mapping[str, object]],
    rejected_items: Sequence[Mapping[str, object]],
    coverage_by_request_id: Mapping[str, Mapping[str, object]],
    dimension: str,
) -> dict[str, dict[str, int]]:
    expected_request_counts = Counter(str(row.get(dimension) or "") for row in selected_requests)
    expected_item_counts = Counter(
        {
            value: sum(
                int(row.get("requested_items") or 0)
                for row in selected_requests
                if str(row.get(dimension) or "") == value
            )
            for value in expected_request_counts
        }
    )
    admitted_counts = Counter(str(row.get(dimension) or "") for row in admitted_items)
    rejected_counts = Counter(str(row.get(dimension) or "") for row in rejected_items)
    shortfall_counts: Counter[str] = Counter()
    waived_counts: Counter[str] = Counter()
    for request in selected_requests:
        value = str(request.get(dimension) or "")
        coverage = coverage_by_request_id.get(str(request.get("request_id") or ""))
        waived_counts[value] += int(_as_mapping(coverage).get("waived_item_count") or 0)
        shortfall_counts[value] += int(_as_mapping(coverage).get("shortfall_count") or 0)
    keys = sorted(
        set(expected_request_counts)
        | set(expected_item_counts)
        | set(admitted_counts)
        | set(rejected_counts)
        | set(waived_counts)
        | set(shortfall_counts)
    )
    return {
        key: {
            "expected_request_count": expected_request_counts.get(key, 0),
            "expected_item_count": expected_item_counts.get(key, 0),
            "admitted_item_count": admitted_counts.get(key, 0),
            "rejected_item_count": rejected_counts.get(key, 0),
            "waived_item_count": waived_counts.get(key, 0),
            "shortfall_count": shortfall_counts.get(key, 0),
        }
        for key in keys
    }


def _rejection_reasons(
    *,
    response_results: Sequence[Mapping[str, object]],
    rejected_items: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    reasons: Counter[str] = Counter()
    for response in response_results:
        reasons.update(
            str(reason) for reason in _as_sequence(response.get("response_rejection_reasons"))
        )
    for item in rejected_items:
        reasons.update(str(reason) for reason in _as_sequence(item.get("rejection_reasons")))
    return dict(sorted(reasons.items()))


def _status(
    *,
    request_issues: Sequence[Mapping[str, object]],
    generated_responses_present: bool,
    response_level_errors: Sequence[Mapping[str, object]],
    rejected_items: Sequence[Mapping[str, object]],
    coverage_shortfalls: Sequence[Mapping[str, object]],
    alignment_errors: Sequence[Mapping[str, object]],
) -> str:
    if request_issues:
        return "review"
    if not generated_responses_present:
        return "ok"
    if response_level_errors or rejected_items or coverage_shortfalls or alignment_errors:
        return "review"
    return "ok"


def _decision(
    *,
    status: str,
    generated_responses_present: bool,
    response_level_errors: Sequence[Mapping[str, object]],
    rejected_items: Sequence[Mapping[str, object]],
    coverage_shortfalls: Sequence[Mapping[str, object]],
    alignment_errors: Sequence[Mapping[str, object]],
) -> str:
    if status != "ok":
        if response_level_errors or alignment_errors:
            return "generated_responses_need_repair"
        if rejected_items:
            return "generated_items_need_repair"
        if coverage_shortfalls:
            return "generated_item_coverage_incomplete"
        return "generation_request_packet_needs_repair"
    if not generated_responses_present:
        return "ready_for_generated_response_admission"
    return "generated_items_admitted_for_pilot_rescoring"


def _next_steps(
    *,
    generated_responses_present: bool,
    request_issues: Sequence[Mapping[str, object]],
    response_level_errors: Sequence[Mapping[str, object]],
    rejected_items: Sequence[Mapping[str, object]],
    coverage_shortfalls: Sequence[Mapping[str, object]],
    alignment_errors: Sequence[Mapping[str, object]],
) -> list[str]:
    if request_issues:
        return [
            "Repair and rerender the generation request packet before any LLM spend.",
            "Do not admit generated outputs against a non-ok request packet.",
        ]
    if not generated_responses_present:
        return [
            "Review the request packet, then run the bounded LLM generation batch.",
            "Run this admission harness on the generated response objects before rescoring.",
            "Keep high, middle, and low arms under the same response and admission contract.",
        ]
    if response_level_errors or alignment_errors:
        return [
            "Repair request_id, family_id, slot_id, slot_type, and target_lemma alignment.",
            "Regenerate only the failed request objects rather than changing the pilot design.",
        ]
    if rejected_items:
        return [
            "Discard or regenerate rejected generated sentences before rescoring.",
            "Keep rejection reasons with the batch so failure classes remain auditable.",
        ]
    if coverage_shortfalls:
        return [
            "Generate only the missing item counts for the listed request cells.",
            "Do not compare arm improvement until expected item coverage is complete.",
        ]
    return [
        "Run the downstream evidence-application/rescoring harness on admitted generated items.",
        "Compare improvement by high_need, middle_control, and low_control arms.",
        "Treat this as heuristic validation, not runtime promotion.",
    ]
