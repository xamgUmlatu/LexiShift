#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


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


DEFAULT_BAND_PLAN = TEST_OUTPUTS_ROOT / (
    "semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es_latest.json"
)
DEFAULT_EXISTING_EVIDENCE = [
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_veto_source_packaging"
    / "en-es-active-only-poc-v5-source-packaging-latest_normalized_evidence.json",
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_veto_source_packaging"
    / (
        "en-es-product-scope-band-grading-v1-active-only-source-packaging-latest"
        "_normalized_evidence.json"
    ),
]
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_scale_tranche_v1_requests_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_scale_tranche_v1_requests_en_es_latest.md"
)
DEFAULT_PILOT_ID = "semantic_veto_active_only_scale_tranche_v1_en_es"
ACTIVE_SLOT = "active_evidence_expansion"
ARM_ORDER = ("high_need", "middle_control", "low_control")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze the next en-es semantic-veto active-only generation tranche from "
            "product-scope families not already covered by packaged active evidence."
        )
    )
    parser.add_argument("--band-plan-json", type=Path, default=DEFAULT_BAND_PLAN)
    parser.add_argument(
        "--existing-evidence-json",
        type=Path,
        action="append",
        default=[],
        help=(
            "Normalized semantic evidence batch to treat as already covered. "
            "May be repeated. Defaults to the current PoC and v1 active-only batches."
        ),
    )
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument("--requested-items", type=int, default=2)
    parser.add_argument("--max-families", type=int, default=0)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    existing_paths = args.existing_evidence_json or list(DEFAULT_EXISTING_EVIDENCE)
    report = build_active_only_scale_tranche_request_report(
        band_plan_payload=_load_json(args.band_plan_json),
        existing_evidence_payloads=[_load_json(path) for path in existing_paths],
        band_plan_path=args.band_plan_json,
        existing_evidence_paths=existing_paths,
        pilot_id=args.pilot_id,
        requested_items=max(1, int(args.requested_items)),
        max_families=max(0, int(args.max_families)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_active_only_scale_tranche_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_active_only_scale_tranche_request_report(
    *,
    band_plan_payload: Mapping[str, object],
    existing_evidence_payloads: Sequence[Mapping[str, object]],
    band_plan_path: Path | None = None,
    existing_evidence_paths: Sequence[Path] = (),
    pilot_id: str = DEFAULT_PILOT_ID,
    requested_items: int = 2,
    max_families: int = 0,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    covered_family_ids = _covered_family_ids(existing_evidence_payloads)
    candidate_rows = [
        dict(row)
        for row in _mapping_rows(band_plan_payload.get("band_family_rows"))
        if str(row.get("family_id") or "").strip()
        and str(row.get("family_id") or "").strip() not in covered_family_ids
    ]
    selected_families = _select_families(
        candidate_rows,
        max_families=max_families,
        requested_items=requested_items,
    )
    requests = [
        _request_from_family(
            family=family,
            pilot_id=pilot_id,
            requested_items=requested_items,
        )
        for family in selected_families
    ]
    issues = _issues(
        band_plan_payload=band_plan_payload,
        covered_family_ids=covered_family_ids,
        selected_families=selected_families,
        requests=requests,
    )
    status = "ok" if not issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "active_only_scale_tranche_request_packet_ready"
            if status == "ok"
            else "active_only_scale_tranche_request_packet_needs_review"
        ),
        "generated_at": generated_at,
        "pair": str(band_plan_payload.get("pair") or "en-es"),
        "pilot": {
            "pilot_id": pilot_id,
            "prompt_id": PROMPT_ID,
            "request_kind": REQUEST_KIND,
            "source_band_plan": _repo_path(band_plan_path),
            "existing_evidence_paths": [_repo_path(path) for path in existing_evidence_paths],
        },
        "strict_flow": {
            "runtime_policy_change": "none",
            "llm_call": "none",
            "request_packet_role": "pre_spend_active_only_generation_inputs",
            "generated_output_role": "candidate_active_anchor_cues",
            "shadow_generation": "excluded",
            "no_winner_generation": "excluded",
            "selection_uses_observed_outcomes": False,
        },
        "selection": {
            "source": "product_scope_band_grading_v1 band_family_rows",
            "covered_family_count": len(covered_family_ids),
            "uncovered_candidate_family_count": len(candidate_rows),
            "selected_family_count": len(selected_families),
            "max_families": int(max_families),
            "selection_order": "arm_order_then_band_rank_then_family_id",
        },
        "summary": _summary(requests=requests, selected_families=selected_families),
        "request_checks": _request_checks(requests=requests),
        "covered_family_ids": sorted(covered_family_ids),
        "selected_families": selected_families,
        "requests": requests,
        "limitations": [
            "active evidence only",
            "request packet makes no LLM call",
            "does not generate shadows or no-winner rows",
            "selected from the current 49-family product-scope denominator only",
            "generated outputs must pass admission, postprocess, packaging, replay, "
            "helper smoke, and page review before broader spend",
        ],
        "next_steps": [
            "Run this active-only request packet with explicit live spend guards.",
            "Admit generated responses structurally before scoring or packaging.",
            "Use the no_high_eval_overlap_sentence_only postprocess view unless it regresses.",
            "Package only admitted active rows as canonical anchor_cue evidence with "
            "tranche-specific provenance.",
        ],
        "issues": issues,
    }


def render_active_only_scale_tranche_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    selection = _as_mapping(report.get("selection"))
    lines = [
        "# en-es Semantic Veto Active-Only Scale Tranche Requests",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Prompt id: `{_as_mapping(report.get('pilot')).get('prompt_id', '')}`",
        f"- Covered families excluded: `{selection.get('covered_family_count', 0)}`",
        f"- Uncovered candidate families: `{selection.get('uncovered_candidate_family_count', 0)}`",
        f"- Selected families: `{selection.get('selected_family_count', 0)}`",
        f"- Requests: `{summary.get('request_count', 0)}`",
        f"- Expected generated items: `{summary.get('expected_generated_item_count', 0)}`",
        f"- Estimated input tokens: `{summary.get('estimated_input_tokens', 0)}`",
        f"- Expected output-token budget: `{summary.get('expected_output_token_budget', 0)}`",
        "",
        "## Arm Summary",
        "",
        "| Arm | Families | Requests | Expected items |",
        "| --- | ---: | ---: | ---: |",
    ]
    for arm in ARM_ORDER:
        row = _as_mapping(_as_mapping(summary.get("requests_by_arm")).get(arm))
        lines.append(
            f"| `{arm}` | {row.get('family_count', 0)} | "
            f"{row.get('request_count', 0)} | {row.get('expected_item_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Selected Families",
            "",
            "| Arm | Band rank | Family | Trigger | Target | Predicted need |",
            "| --- | ---: | --- | --- | --- | ---: |",
        ]
    )
    for family in _mapping_rows(report.get("selected_families")):
        lines.append(
            f"| `{family.get('pilot_arm', '')}` | {family.get('band_rank', 0)} | "
            f"`{family.get('family_id', '')}` | `{family.get('trigger', '')}` | "
            f"`{family.get('target_lemma', '')}` | {family.get('predicted_need', 0)} |"
        )
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(
            f"- `{_as_mapping(issue).get('message', issue)}`" for issue in report["issues"]
        )
    return "\n".join(lines) + "\n"


def _covered_family_ids(payloads: Sequence[Mapping[str, object]]) -> set[str]:
    family_ids: set[str] = set()
    for payload in payloads:
        for row in _mapping_rows(payload.get("rows")):
            family_id = str(_as_mapping(row.get("metadata")).get("family_id") or "").strip()
            if family_id:
                family_ids.add(family_id)
    return family_ids


def _select_families(
    candidate_rows: Sequence[Mapping[str, object]],
    *,
    max_families: int,
    requested_items: int,
) -> list[dict[str, object]]:
    sorted_rows = sorted(
        (dict(row) for row in candidate_rows),
        key=lambda row: (
            ARM_ORDER.index(str(row.get("pilot_arm") or "low_control"))
            if str(row.get("pilot_arm") or "") in ARM_ORDER
            else len(ARM_ORDER),
            int(row.get("band_rank") or 0),
            str(row.get("family_id") or ""),
        ),
    )
    if max_families:
        sorted_rows = sorted_rows[:max_families]
    selected = []
    for global_rank, row in enumerate(sorted_rows, start=1):
        selected.append(
            {
                **row,
                "global_tranche_rank": global_rank,
                "planned_generation_slots": [
                    {
                        "slot_id": f"{row.get('family_id')}:{ACTIVE_SLOT}",
                        "slot_type": ACTIVE_SLOT,
                        "target_lemma": str(row.get("target_lemma") or ""),
                        "requested_items": int(requested_items),
                        "purpose": (
                            "generate active anchor cues for the intended source-target sense"
                        ),
                    }
                ],
            }
        )
    return selected


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
        "arm_rank": int(family.get("band_rank") or 0),
        "global_need_rank": int(family.get("global_tranche_rank") or 0),
        "predicted_need": family.get("predicted_need"),
        "trigger": str(family.get("trigger") or ""),
        "active_target_lemma": str(active.get("target_lemma") or family.get("target_lemma") or ""),
        "active_evidence_text": str(active.get("evidence_text") or ""),
        "known_shadow_targets": [
            str(shadow.get("target_lemma") or "")
            for shadow in _mapping_rows(family.get("shadows"))
            if str(shadow.get("target_lemma") or "")
        ],
        "slot_id": f"{family.get('family_id')}:{ACTIVE_SLOT}",
        "slot_type": ACTIVE_SLOT,
        "slot_target_lemma": str(active.get("target_lemma") or family.get("target_lemma") or ""),
        "requested_items": int(requested_items),
        "purpose": "generate active anchor cues for the intended source-target sense",
    }
    request["prompt_text"] = _prompt_text(request)
    request["estimated_input_tokens"] = _estimate_tokens(str(request["prompt_text"]))
    request["expected_output_token_budget"] = (
        int(request["requested_items"]) * EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM
    )
    return request


def _issues(
    *,
    band_plan_payload: Mapping[str, object],
    covered_family_ids: set[str],
    selected_families: Sequence[Mapping[str, object]],
    requests: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    issues = []
    if int(band_plan_payload.get("schema_version") or 0) != 1:
        issues.append(_issue("band_plan", "error", "Band plan must be schema_version=1."))
    if not selected_families:
        issues.append(_issue("selection", "error", "No uncovered families selected."))
    selected_ids = [str(family.get("family_id") or "") for family in selected_families]
    if len(set(selected_ids)) != len(selected_ids):
        issues.append(_issue("selection", "error", "Selected families are not unique."))
    overlap = sorted(family_id for family_id in selected_ids if family_id in covered_family_ids)
    if overlap:
        issues.append(
            _issue("selection", "error", "Selected families overlap existing active evidence.")
        )
    if any(str(request.get("slot_type") or "") != ACTIVE_SLOT for request in requests):
        issues.append(_issue("requests", "error", "Non-active request entered packet."))
    if len({str(request.get("request_id") or "") for request in requests}) != len(requests):
        issues.append(_issue("requests", "error", "Request ids are not unique."))
    if not all(str(request.get("prompt_text") or "").strip() for request in requests):
        issues.append(_issue("requests", "error", "Every request must have prompt_text."))
    return issues


def _request_checks(requests: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "request_count": len(requests),
        "unique_request_ids": len({str(row.get("request_id") or "") for row in requests})
        == len(requests),
        "all_active_only": all(str(row.get("slot_type") or "") == ACTIVE_SLOT for row in requests),
        "all_have_prompt_text": all(str(row.get("prompt_text") or "").strip() for row in requests),
        "all_have_positive_requested_items": all(
            int(row.get("requested_items") or 0) > 0 for row in requests
        ),
    }


def _summary(
    *,
    requests: Sequence[Mapping[str, object]],
    selected_families: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    by_arm = {}
    for arm in ARM_ORDER:
        arm_requests = [row for row in requests if str(row.get("pilot_arm") or "") == arm]
        by_arm[arm] = {
            "family_count": len({row.get("family_id") for row in arm_requests}),
            "request_count": len(arm_requests),
            "expected_item_count": sum(
                int(row.get("requested_items") or 0) for row in arm_requests
            ),
        }
    return {
        "family_count": len(selected_families),
        "request_count": len(requests),
        "expected_generated_item_count": sum(
            int(row.get("requested_items") or 0) for row in requests
        ),
        "estimated_input_tokens": sum(
            int(row.get("estimated_input_tokens") or 0) for row in requests
        ),
        "expected_output_token_budget": sum(
            int(row.get("expected_output_token_budget") or 0) for row in requests
        ),
        "requests_by_arm": by_arm,
        "requests_by_slot_type": {
            ACTIVE_SLOT: {
                "request_count": len(requests),
                "expected_item_count": sum(
                    int(row.get("requested_items") or 0) for row in requests
                ),
            }
        },
        "selected_family_counts_by_arm": dict(
            sorted(Counter(str(row.get("pilot_arm") or "") for row in selected_families).items())
        ),
    }


def _issue(scope: str, severity: str, message: str) -> dict[str, object]:
    return {"scope": scope, "severity": severity, "message": message}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return value


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
