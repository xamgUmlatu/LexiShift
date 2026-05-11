#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha1
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_evidence_gap_generation_requests_en_es import (  # noqa: E402
    EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM,
    PROMPT_ID,
    REQUEST_KIND,
    _estimate_tokens,
    _prompt_text,
)
from semantic_veto_active_only_full_generation_plan_rendering import (  # noqa: E402
    render_active_only_full_generation_plan_markdown,
)
from semantic_veto_active_only_full_generation_plan_support import (  # noqa: E402
    ZIPF_BAND_ORDER,
    annotate_source_target_review,
    coverage_breakdown,
    coverage_key,
    coverage_matrix,
    source_target_review_decisions,
    source_target_review_excludes,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
    _safe_float,
)


DEFAULT_SRS_ZIPF_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_EXISTING_EVIDENCE_JSON = [
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_veto_source_packaging"
    / "en-es-active-only-combined-product-scope-v1-normalized_evidence.json"
]
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_full_generation_plan_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_full_generation_plan_en_es_latest.md"
)
DEFAULT_SOURCE_TARGET_REVIEW_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_veto_active_only_generation_source_target_review_en_es.json"
)
DEFAULT_PILOT_ID = "semantic_veto_active_only_full_en_es_v1"
ACTIVE_SLOT = "active_evidence_expansion"
DEFAULT_REQUESTED_ITEMS = 2
DEFAULT_TRANCHE_SIZE = 50
DEFAULT_REQUEST_FAMILY_LIMIT = 50
ZIPF_BAND_WEIGHTS = {
    "zipf_5_plus_very_common": 1.0,
    "zipf_4_to_5_common": 0.8,
    "zipf_3_to_4_mid": 0.55,
    "zipf_below_3_rare": 0.35,
    "missing": 0.25,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a no-spend en-es active-only LLM generation coverage plan from the "
            "full SRS-admissible source-target denominator."
        )
    )
    parser.add_argument("--srs-zipf-bridge-json", type=Path, default=DEFAULT_SRS_ZIPF_BRIDGE_JSON)
    parser.add_argument(
        "--existing-evidence-json",
        type=Path,
        action="append",
        default=[],
        help=(
            "Normalized semantic evidence batch to count as active-only coverage. "
            "May be repeated. Defaults to the combined active-only product-smoke pack."
        ),
    )
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument("--requested-items", type=int, default=DEFAULT_REQUESTED_ITEMS)
    parser.add_argument("--tranche-size", type=int, default=DEFAULT_TRANCHE_SIZE)
    parser.add_argument(
        "--request-family-limit",
        type=int,
        default=DEFAULT_REQUEST_FAMILY_LIMIT,
        help=(
            "How many uncovered families to include in the runnable request packet. "
            "Use 0 only when intentionally preparing a full all-at-once packet."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--source-target-review-json",
        type=Path,
        default=DEFAULT_SOURCE_TARGET_REVIEW_JSON,
        help=(
            "Optional pre-spend source-target review manifest. When present, the "
            "runnable request packet includes only rows explicitly approved by the manifest."
        ),
    )
    parser.add_argument(
        "--ignore-source-target-review",
        action="store_true",
        help="Ignore the default/manual source-target review manifest.",
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    existing_paths = args.existing_evidence_json or list(DEFAULT_EXISTING_EVIDENCE_JSON)
    report = build_active_only_full_generation_plan_report(
        srs_zipf_bridge_payload=_load_json(_resolve_repo_path(args.srs_zipf_bridge_json)),
        existing_evidence_payloads=[
            _load_json(_resolve_repo_path(path)) for path in existing_paths
        ],
        srs_zipf_bridge_path=args.srs_zipf_bridge_json,
        existing_evidence_paths=existing_paths,
        source_target_review_payload=(
            _load_json(_resolve_repo_path(args.source_target_review_json))
            if not args.ignore_source_target_review
            and args.source_target_review_json
            and _resolve_repo_path(args.source_target_review_json).exists()
            else None
        ),
        source_target_review_path=(
            args.source_target_review_json
            if not args.ignore_source_target_review
            and args.source_target_review_json
            and _resolve_repo_path(args.source_target_review_json).exists()
            else None
        ),
        pilot_id=str(args.pilot_id),
        requested_items=max(1, int(args.requested_items)),
        tranche_size=max(1, int(args.tranche_size)),
        request_family_limit=max(0, int(args.request_family_limit)),
    )
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    write_report(report, json_out=json_out, markdown_out=markdown_out)
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


def build_active_only_full_generation_plan_report(
    *,
    srs_zipf_bridge_payload: Mapping[str, object],
    existing_evidence_payloads: Sequence[Mapping[str, object]],
    srs_zipf_bridge_path: Path | None = None,
    existing_evidence_paths: Sequence[Path] = (),
    source_target_review_payload: Mapping[str, object] | None = None,
    source_target_review_path: Path | None = None,
    pilot_id: str = DEFAULT_PILOT_ID,
    requested_items: int = DEFAULT_REQUESTED_ITEMS,
    tranche_size: int = DEFAULT_TRANCHE_SIZE,
    request_family_limit: int = DEFAULT_REQUEST_FAMILY_LIMIT,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    denominator_rows = _denominator_rows(srs_zipf_bridge_payload)
    covered_by_key = _active_evidence_coverage(existing_evidence_payloads)
    review_decisions = source_target_review_decisions(source_target_review_payload)
    source_target_review_active = source_target_review_payload is not None
    denominator_keys = {str(row["coverage_key"]) for row in denominator_rows}
    covered_denominator_keys = denominator_keys.intersection(covered_by_key)
    uncovered_rows = [
        _generation_family_row(row)
        for row in denominator_rows
        if str(row["coverage_key"]) not in covered_denominator_keys
    ]
    uncovered_rows = [
        annotate_source_target_review(row, review_decisions=review_decisions)
        for row in uncovered_rows
    ]
    uncovered_rows.sort(key=_uncovered_sort_key)
    for rank, row in enumerate(uncovered_rows, start=1):
        row["global_need_rank"] = rank
        row["arm_rank"] = _arm_rank(row, uncovered_rows)
        row["planned_generation_slots"] = [
            {
                "slot_id": f"{row['family_id']}:{ACTIVE_SLOT}",
                "slot_type": ACTIVE_SLOT,
                "target_lemma": row["target"],
                "requested_items": int(requested_items),
                "purpose": "generate active anchor cues for the intended source-target sense",
            }
        ]

    generation_queue_rows = [
        row for row in uncovered_rows if not source_target_review_excludes(row)
    ]
    selected_pool_rows = list(generation_queue_rows)
    if source_target_review_active:
        selected_pool_rows = [
            row
            for row in generation_queue_rows
            if str(row.get("source_target_review_status") or "") == "approved"
        ]
    selected_rows = list(selected_pool_rows)
    if request_family_limit:
        selected_rows = selected_rows[: int(request_family_limit)]
    requests = [
        _request_from_family(
            family=row,
            pilot_id=pilot_id,
            requested_items=requested_items,
        )
        for row in selected_rows
    ]
    tranches = _tranche_plan(
        uncovered_rows=generation_queue_rows,
        pilot_id=pilot_id,
        tranche_size=tranche_size,
        requested_items=requested_items,
    )
    evidence_outside_denominator = sorted(set(covered_by_key).difference(denominator_keys))
    issues = _issues(
        denominator_rows=denominator_rows,
        uncovered_rows=uncovered_rows,
        requests=requests,
        request_family_limit=request_family_limit,
        srs_zipf_bridge_payload=srs_zipf_bridge_payload,
        source_target_review_active=source_target_review_active,
        selected_rows=selected_rows,
    )
    status = "ok" if not issues else "review"
    decision = (
        "active_only_full_generation_plan_ready"
        if status == "ok"
        else "active_only_full_generation_plan_needs_review"
    )
    if denominator_rows and not uncovered_rows:
        decision = "active_only_full_generation_already_covered"
    next_steps = [
        "Run the first request tranche only, with --max-requests and --require-selected-request-count matching the selected request count.",
        "Run postprocess, admission, source packaging, inventory replay, helper smoke, and live-page scan on that tranche before continuing.",
        "Append admitted rows to the product-smoke active-only pack only after replay shows the same soft-assist behavior.",
        "Generate shadows only for high-need or observed-harm families after active-only coverage has been measured.",
    ]
    if not requests and uncovered_rows:
        next_steps = [
            "Expand the source-target review manifest for the next uncovered tranche before any paid generation.",
            "Rerun this planner with the updated review manifest and require a nonzero selected request count before calling the live generation harness.",
            "Keep the current combined pack as the product-smoke control while the next tranche is reviewed.",
        ]
    return {
        "schema_version": 1,
        "pair": str(srs_zipf_bridge_payload.get("pair") or "en-es"),
        "status": status,
        "decision": decision,
        "generated_at": generated_at,
        "pilot": {
            "pilot_id": pilot_id,
            "prompt_id": PROMPT_ID,
            "request_kind": REQUEST_KIND,
            "requested_items_per_request": requested_items,
        },
        "inputs": {
            "srs_zipf_bridge_json": _repo_path(srs_zipf_bridge_path),
            "srs_zipf_bridge_decision": str(srs_zipf_bridge_payload.get("decision") or ""),
            "existing_evidence_paths": [_repo_path(path) for path in existing_evidence_paths],
            "source_target_review_json": _repo_path(source_target_review_path),
            "source_target_review_decision": str(
                _as_mapping(source_target_review_payload).get("decision") or ""
            ),
        },
        "strict_flow": {
            "runtime_policy_change": "none",
            "llm_call": "none",
            "request_packet_role": "pre_spend_active_only_generation_inputs",
            "source_target_review": (
                "approved_rows_only" if source_target_review_active else "not_applied"
            ),
            "shadow_generation": "excluded_until_active_only_coverage_is_measured",
            "phrase_no_winner_generation": "excluded_until_active_only_coverage_is_measured",
            "request_packet_scope": (
                "first_tranche_only" if request_family_limit else "all_uncovered_families"
            ),
            "selection_uses_observed_outcomes": False,
        },
        "methodology": {
            "denominator": (
                "full_source_target_pairs from the SRS Zipf bridge; this is the current "
                "installed en-es SRS-admissible source-target rule universe, not every "
                "dictionary entry."
            ),
            "coverage_match": (
                "existing active-only evidence rows are matched to denominator rows by "
                "normalized English trigger plus normalized Spanish target."
            ),
            "ordering_policy": (
                "exposure-first queue order from source and target Zipf bands; this is "
                "cost triage, not a promoted veto-difficulty proof."
            ),
            "active_prompt_policy": (
                "uncovered source-target rows receive active_evidence_expansion requests "
                "using the existing v7 prompt contract with target-labeled sense hints."
            ),
        },
        "summary": _summary(
            denominator_rows=denominator_rows,
            covered_by_key=covered_by_key,
            covered_denominator_keys=covered_denominator_keys,
            evidence_outside_denominator=evidence_outside_denominator,
            requests=requests,
            tranches=tranches,
            source_target_review_active=source_target_review_active,
            source_target_review_decisions=review_decisions,
            uncovered_rows=uncovered_rows,
            generation_queue_rows=generation_queue_rows,
        ),
        "coverage_by_source_band": coverage_breakdown(
            denominator_rows=denominator_rows,
            covered_denominator_keys=covered_denominator_keys,
            group_key="source_zipf_band_en",
            label="source_band",
        ),
        "coverage_by_target_band": coverage_breakdown(
            denominator_rows=denominator_rows,
            covered_denominator_keys=covered_denominator_keys,
            group_key="target_zipf_band_es",
            label="target_band",
        ),
        "coverage_matrix": coverage_matrix(
            denominator_rows=denominator_rows,
            covered_denominator_keys=covered_denominator_keys,
        ),
        "tranche_plan": tranches,
        "all_uncovered_families": uncovered_rows,
        "selected_request_families": selected_rows,
        "requests": requests,
        "evidence_outside_denominator_keys": evidence_outside_denominator[:100],
        "e2e_checks": _e2e_checks(
            denominator_rows=denominator_rows,
            covered_denominator_keys=covered_denominator_keys,
            selected_rows=selected_rows,
            requests=requests,
        ),
        "limitations": [
            "full denominator is current installed SRS rulegen output, not all possible en-es words",
            "active-only rows do not add repaired shadows or phrase/no-winner controls",
            "Zipf ordering is an exposure queue, not proof of veto difficulty",
            "source-target-only rows have weaker sense hints than manually reviewed families",
            "manual pre-spend source-target review covers only rows present in the review manifest",
            "live generation must be run in small resumable tranches with explicit spend guards",
        ],
        "next_steps": next_steps,
        "issues": issues,
    }


def _denominator_rows(payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows_by_key: dict[str, dict[str, object]] = {}
    for row in _mapping_rows(payload.get("full_source_target_pairs")):
        source = str(row.get("source") or "").strip()
        target = str(row.get("target") or "").strip()
        if not source or not target:
            continue
        key = coverage_key(source=source, target=target)
        if key in rows_by_key:
            continue
        rows_by_key[key] = {
            "source": source,
            "target": target,
            "coverage_key": key,
            "source_zipf_frequency_en": row.get("source_zipf_frequency_en"),
            "source_zipf_band_en": str(row.get("source_zipf_band_en") or "missing"),
            "target_zipf_frequency_es": row.get("target_zipf_frequency_es"),
            "target_zipf_band_es": str(row.get("target_zipf_band_es") or "missing"),
        }
    return [rows_by_key[key] for key in sorted(rows_by_key)]


def _active_evidence_coverage(
    payloads: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    covered: dict[str, dict[str, object]] = {}
    for payload in payloads:
        for row in _mapping_rows(payload.get("rows")):
            if str(row.get("relation_type") or "") not in {"", "anchor_cue"}:
                continue
            source = str(row.get("normalized_trigger") or row.get("trigger") or "").strip()
            target = str(
                row.get("normalized_active_target")
                or row.get("active_target")
                or row.get("normalized_candidate_target")
                or row.get("candidate_target")
                or ""
            ).strip()
            if not source or not target:
                continue
            key = coverage_key(source=source, target=target)
            entry = covered.setdefault(
                key,
                {
                    "source": source,
                    "target": target,
                    "row_count": 0,
                    "family_ids": set(),
                },
            )
            entry["row_count"] = int(entry["row_count"]) + 1
            family_id = str(_as_mapping(row.get("metadata")).get("family_id") or "").strip()
            if family_id:
                entry["family_ids"].add(family_id)  # type: ignore[union-attr]
    normalized: dict[str, dict[str, object]] = {}
    for key, value in covered.items():
        normalized[key] = {
            **value,
            "family_ids": sorted(value["family_ids"]),  # type: ignore[index]
        }
    return normalized


def _generation_family_row(row: Mapping[str, object]) -> dict[str, object]:
    source = str(row.get("source") or "")
    target = str(row.get("target") or "")
    score = _priority_score(row)
    return {
        **dict(row),
        "family_id": _family_id(source=source, target=target),
        "trigger": source,
        "active": {
            "target_lemma": target,
            "evidence_text": _active_evidence_hint(source=source, target=target),
        },
        "shadows": [],
        "target_lemma": target,
        "pilot_arm": _priority_tier(score),
        "priority_tier": _priority_tier(score),
        "active_only_generation_need_score": score,
        "predicted_need": score,
    }


def _request_from_family(
    *,
    family: Mapping[str, object],
    pilot_id: str,
    requested_items: int,
) -> dict[str, object]:
    active = _as_mapping(family.get("active"))
    request = {
        "request_id": f"{pilot_id}:{family.get('family_id')}:{ACTIVE_SLOT}",
        "request_kind": REQUEST_KIND,
        "prompt_id": PROMPT_ID,
        "pilot_id": pilot_id,
        "family_id": str(family.get("family_id") or ""),
        "pilot_arm": str(family.get("pilot_arm") or ""),
        "arm_rank": int(family.get("arm_rank") or 0),
        "global_need_rank": int(family.get("global_need_rank") or 0),
        "predicted_need": family.get("predicted_need"),
        "trigger": str(family.get("trigger") or ""),
        "active_target_lemma": str(active.get("target_lemma") or family.get("target") or ""),
        "active_evidence_text": str(active.get("evidence_text") or ""),
        "known_shadow_targets": [],
        "slot_id": f"{family.get('family_id')}:{ACTIVE_SLOT}",
        "slot_type": ACTIVE_SLOT,
        "slot_target_lemma": str(active.get("target_lemma") or family.get("target") or ""),
        "requested_items": int(requested_items),
        "purpose": "generate active anchor cues for the intended source-target sense",
    }
    request["prompt_text"] = _prompt_text(request)
    request["estimated_input_tokens"] = _estimate_tokens(str(request["prompt_text"]))
    request["expected_output_token_budget"] = (
        int(request["requested_items"]) * EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM
    )
    return request


def _tranche_plan(
    *,
    uncovered_rows: Sequence[Mapping[str, object]],
    pilot_id: str,
    tranche_size: int,
    requested_items: int,
) -> list[dict[str, object]]:
    tranches = []
    for index in range(0, len(uncovered_rows), int(tranche_size)):
        chunk = list(uncovered_rows[index : index + int(tranche_size)])
        requests = [
            _request_from_family(
                family=row,
                pilot_id=pilot_id,
                requested_items=requested_items,
            )
            for row in chunk
        ]
        tranche_index = len(tranches) + 1
        tranches.append(
            {
                "tranche_id": f"en-es-active-only-full-v1-tranche-{tranche_index:03d}",
                "start_global_need_rank": chunk[0].get("global_need_rank") if chunk else 0,
                "end_global_need_rank": chunk[-1].get("global_need_rank") if chunk else 0,
                "family_count": len(chunk),
                "request_count": len(requests),
                "expected_generated_item_count": len(chunk) * int(requested_items),
                "estimated_input_tokens": sum(
                    int(request.get("estimated_input_tokens") or 0) for request in requests
                ),
                "expected_output_token_budget": sum(
                    int(request.get("expected_output_token_budget") or 0) for request in requests
                ),
                "priority_tier_counts": dict(
                    sorted(Counter(str(row.get("priority_tier") or "") for row in chunk).items())
                ),
                "source_band_counts": dict(
                    sorted(
                        Counter(str(row.get("source_zipf_band_en") or "") for row in chunk).items()
                    )
                ),
                "target_band_counts": dict(
                    sorted(
                        Counter(str(row.get("target_zipf_band_es") or "") for row in chunk).items()
                    )
                ),
            }
        )
    return tranches


def _summary(
    *,
    denominator_rows: Sequence[Mapping[str, object]],
    covered_by_key: Mapping[str, Mapping[str, object]],
    covered_denominator_keys: set[str],
    uncovered_rows: Sequence[Mapping[str, object]],
    generation_queue_rows: Sequence[Mapping[str, object]],
    evidence_outside_denominator: Sequence[str],
    requests: Sequence[Mapping[str, object]],
    tranches: Sequence[Mapping[str, object]],
    source_target_review_active: bool,
    source_target_review_decisions: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    review_status_counts = Counter(
        str(row.get("source_target_review_status") or "not_reviewed") for row in uncovered_rows
    )
    return {
        "denominator_family_count": len(denominator_rows),
        "denominator_source_trigger_count": len(
            {str(row.get("source") or "") for row in denominator_rows}
        ),
        "denominator_target_count": len({str(row.get("target") or "") for row in denominator_rows}),
        "covered_evidence_key_count": len(covered_by_key),
        "covered_denominator_family_count": len(covered_denominator_keys),
        "covered_denominator_family_share": _ratio(
            len(covered_denominator_keys), len(denominator_rows)
        ),
        "uncovered_family_count": len(uncovered_rows),
        "generation_queue_family_count": len(generation_queue_rows),
        "evidence_outside_denominator_key_count": len(evidence_outside_denominator),
        "selected_request_family_count": len({request.get("family_id") for request in requests}),
        "selected_request_count": len(requests),
        "selected_expected_generated_item_count": sum(
            int(request.get("requested_items") or 0) for request in requests
        ),
        "selected_estimated_input_tokens": sum(
            int(request.get("estimated_input_tokens") or 0) for request in requests
        ),
        "selected_expected_output_token_budget": sum(
            int(request.get("expected_output_token_budget") or 0) for request in requests
        ),
        "full_expected_generated_item_count": sum(
            int(row.get("planned_generation_slots", [{}])[0].get("requested_items") or 0)
            for row in generation_queue_rows
        ),
        "tranche_count": len(tranches),
        "uncovered_priority_tier_counts": dict(
            sorted(Counter(str(row.get("priority_tier") or "") for row in uncovered_rows).items())
        ),
        "source_target_review_active": bool(source_target_review_active),
        "source_target_review_decision_count": len(source_target_review_decisions),
        "source_target_review_status_counts": dict(sorted(review_status_counts.items())),
    }


def _e2e_checks(
    *,
    denominator_rows: Sequence[Mapping[str, object]],
    covered_denominator_keys: set[str],
    selected_rows: Sequence[Mapping[str, object]],
    requests: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    selected_keys = {str(row.get("coverage_key") or "") for row in selected_rows}
    request_family_ids = [str(row.get("family_id") or "") for row in requests]
    return {
        "denominator_present": bool(denominator_rows),
        "selected_rows_do_not_overlap_existing_coverage": selected_keys.isdisjoint(
            covered_denominator_keys
        ),
        "request_ids_unique": len({str(row.get("request_id") or "") for row in requests})
        == len(requests),
        "request_family_ids_unique": len(set(request_family_ids)) == len(request_family_ids),
        "all_requests_active_only": all(
            str(row.get("slot_type") or "") == ACTIVE_SLOT for row in requests
        ),
        "all_requests_have_prompt_text": all(
            str(row.get("prompt_text") or "").strip() for row in requests
        ),
        "all_requests_have_target": all(
            str(row.get("active_target_lemma") or "").strip() for row in requests
        ),
        "selected_rows_review_approved_or_review_inactive": all(
            str(row.get("source_target_review_status") or "") in {"", "approved"}
            for row in selected_rows
        ),
    }


def _issues(
    *,
    denominator_rows: Sequence[Mapping[str, object]],
    uncovered_rows: Sequence[Mapping[str, object]],
    requests: Sequence[Mapping[str, object]],
    request_family_limit: int,
    srs_zipf_bridge_payload: Mapping[str, object],
    source_target_review_active: bool,
    selected_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    issues = []
    if str(srs_zipf_bridge_payload.get("decision") or "") != "srs_zipf_bridge_established":
        issues.append("srs_zipf_bridge_not_established")
    if not denominator_rows:
        issues.append("full_source_target_denominator_missing")
    if uncovered_rows and not requests:
        issues.append("uncovered_rows_exist_but_no_requests_selected")
    if request_family_limit == 0 and len(requests) > DEFAULT_TRANCHE_SIZE:
        issues.append("all_uncovered_requests_emitted_review_before_live_spend")
    if any(str(request.get("slot_type") or "") != ACTIVE_SLOT for request in requests):
        issues.append("non_active_request_emitted")
    if source_target_review_active and any(
        str(row.get("source_target_review_status") or "") != "approved" for row in selected_rows
    ):
        issues.append("selected_request_rows_not_source_target_review_approved")
    return issues


def _priority_score(row: Mapping[str, object]) -> float:
    source_weight = ZIPF_BAND_WEIGHTS.get(str(row.get("source_zipf_band_en") or "missing"), 0.25)
    target_weight = ZIPF_BAND_WEIGHTS.get(str(row.get("target_zipf_band_es") or "missing"), 0.25)
    common_bonus = 0.08 if source_weight >= 0.8 and target_weight >= 0.8 else 0.0
    score = min(1.0, (0.57 * source_weight) + (0.35 * target_weight) + common_bonus)
    return round(score, 4)


def _priority_tier(score: float) -> str:
    if score >= 0.85:
        return "P0_exposure_first"
    if score >= 0.65:
        return "P1_exposure_first"
    if score >= 0.45:
        return "P2_exposure_first"
    return "P3_exposure_first"


def _uncovered_sort_key(row: Mapping[str, object]) -> tuple[float, int, int, str, str]:
    return (
        -_safe_float(row.get("active_only_generation_need_score")),
        _band_order(str(row.get("source_zipf_band_en") or "")),
        _band_order(str(row.get("target_zipf_band_es") or "")),
        str(row.get("source") or ""),
        str(row.get("target") or ""),
    )


def _arm_rank(row: Mapping[str, object], rows: Sequence[Mapping[str, object]]) -> int:
    tier = str(row.get("priority_tier") or "")
    source = str(row.get("source") or "")
    target = str(row.get("target") or "")
    tier_rows = [item for item in rows if str(item.get("priority_tier") or "") == tier]
    for index, item in enumerate(tier_rows, start=1):
        if str(item.get("source") or "") == source and str(item.get("target") or "") == target:
            return index
    return 0


def _band_order(value: str) -> int:
    return ZIPF_BAND_ORDER.index(value) if value in ZIPF_BAND_ORDER else len(ZIPF_BAND_ORDER)


def _family_id(*, source: str, target: str) -> str:
    digest = sha1(coverage_key(source=source, target=target).encode("utf-8")).hexdigest()[:8]
    return f"en-es:srs-source-target:{_slug(source)}:{_slug(target)}:{digest}"


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "term"


def _active_evidence_hint(*, source: str, target: str) -> str:
    return (
        f"Use {source!r} in natural English contexts where the intended Spanish "
        f"replacement is {target!r}. The sentence should make that source-target sense "
        "clear without using the Spanish word."
    )


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_report(
    report: Mapping[str, object],
    *,
    json_out: Path,
    markdown_out: Path,
) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(
        render_active_only_full_generation_plan_markdown(report), encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
