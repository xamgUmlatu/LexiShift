#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(Path(__file__).resolve().parent),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
)


DEFAULT_PLAN_JSON = TEST_INPUTS_ROOT / "semantic_veto_evidence_gap_control_pilot_plan_en_es.json"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_requests_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_requests_en_es_latest.md"
)
PROMPT_ID = "semantic_veto_evidence_gap_generation_v7_shadow_target_correctness"
REQUEST_KIND = "semantic_veto_evidence_gap_generation"
EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM = 140
SLOT_TYPE_ORDER = (
    "active_evidence_expansion",
    "shadow_or_competitor_evidence_probe",
    "no_winner_context_probe",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render the no-spend generation request packet for the evidence-gap "
            "control pilot. This makes no LLM call and changes no runtime policy."
        )
    )
    parser.add_argument("--plan-json", type=Path, default=DEFAULT_PLAN_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_evidence_gap_generation_request_report(
        plan_payload=_load_json(args.plan_json),
        plan_path=args.plan_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_evidence_gap_generation_request_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_evidence_gap_generation_request_report(
    *,
    plan_payload: Mapping[str, object],
    plan_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    plan_issues = _validate_plan(plan_payload)
    requests = [] if plan_issues else _build_requests(plan_payload)
    request_checks = _request_checks(plan_payload=plan_payload, requests=requests)
    request_errors = [
        issue for issue in request_checks["issues"] if str(issue.get("severity") or "") == "error"
    ]
    status = "ok" if not plan_issues and not request_errors else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "evidence_gap_generation_request_packet_ready"
            if status == "ok"
            else "evidence_gap_generation_request_packet_needs_repair"
        ),
        "generated_at": generated_at,
        "pair": str(plan_payload.get("pair") or "en-es"),
        "pilot": {
            "plan_path": _repo_path(plan_path),
            "pilot_id": str(plan_payload.get("pilot_id") or ""),
            "plan_status": str(plan_payload.get("status") or ""),
            "request_kind": REQUEST_KIND,
            "prompt_id": PROMPT_ID,
        },
        "strict_flow": {
            "runtime_policy_change": "none",
            "llm_call": "none",
            "request_packet_role": "pre_spend_generation_inputs",
            "generated_output_role": "candidate_evidence_or_context_data",
            "selection_uses_observed_outcomes": _as_mapping(plan_payload.get("selection")).get(
                "selection_uses_observed_outcomes"
            ),
        },
        "summary": _summary(plan_payload=plan_payload, requests=requests),
        "plan_checks": {
            "issue_count": len(plan_issues),
            "issues": plan_issues,
        },
        "request_checks": request_checks,
        "response_contract": _response_contract(),
        "requests": requests,
        "limitations": [
            "no LLM call is made by this script",
            "request packet is not generated data",
            "generated output must be admitted and reviewed before scoring claims",
            "the same request schema is used for high, middle, and low arms",
            "runtime policy and scorer thresholds remain unchanged",
        ],
        "next_steps": [
            "Review the prompt packet before spending.",
            "Run the same generation contract for high_need, middle_control, and low_control arms.",
            "Admit generated outputs with slot-id and family-id checks before any downstream scoring.",
            "Compare improvement by arm; do not tune thresholds from this generation packet.",
        ],
    }


def render_evidence_gap_generation_request_markdown(report: Mapping[str, object]) -> str:
    pilot = _as_mapping(report.get("pilot"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Generation Requests",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Plan: `{pilot.get('plan_path', '')}`",
        f"- Prompt id: `{pilot.get('prompt_id', '')}`",
        f"- Requests rendered: `{summary.get('request_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Expected generated items: `{summary.get('expected_generated_item_count', 0)}`",
        f"- Expected output-token budget: `{summary.get('expected_output_token_budget', 0)}`",
        "",
        "## Contract",
        "",
        "- No runtime policy change.",
        "- No threshold tuning from generated outputs.",
        "- Use the same slot contract for high, middle, and low arms.",
        "- Each response must be JSON and must preserve request_id, family_id, slot_id, and slot_type.",
        "- Generated English contexts must contain the English source phrase and must not contain Spanish target lemmas.",
        "",
        "## Arm Summary",
        "",
        "| Arm | Requests | Families | Expected items |",
        "| --- | ---: | ---: | ---: |",
    ]
    for arm, row in _as_mapping(summary.get("requests_by_arm")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(arm))}` | {row_map.get('request_count', 0)} | "
            f"{row_map.get('family_count', 0)} | {row_map.get('expected_item_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Slot Summary",
            "",
            "| Slot type | Requests | Expected items |",
            "| --- | ---: | ---: |",
        ]
    )
    for slot_type, row in _as_mapping(summary.get("requests_by_slot_type")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(slot_type))}` | {row_map.get('request_count', 0)} | "
            f"{row_map.get('expected_item_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Request Samples",
            "",
            _request_table(report.get("requests")),
            "",
            "## Guardrails",
            "",
            "| Check | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in _as_mapping(report.get("request_checks")).items():
        if key != "issues":
            lines.append(f"| `{_escape_md(str(key))}` | `{value}` |")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _build_requests(plan: Mapping[str, object]) -> list[dict[str, object]]:
    pilot_id = str(plan.get("pilot_id") or "").strip()
    requests: list[dict[str, object]] = []
    for family in _mapping_rows(plan.get("pilot_families")):
        for slot in _mapping_rows(family.get("planned_generation_slots")):
            request = {
                "request_id": f"{pilot_id}:{slot.get('slot_id')}",
                "request_kind": REQUEST_KIND,
                "prompt_id": PROMPT_ID,
                "pilot_id": pilot_id,
                "family_id": str(family.get("family_id") or ""),
                "pilot_arm": str(family.get("pilot_arm") or ""),
                "arm_rank": int(family.get("arm_rank") or 0),
                "global_need_rank": int(family.get("global_need_rank") or 0),
                "predicted_need": family.get("predicted_need"),
                "trigger": str(family.get("trigger") or ""),
                "active_target_lemma": str(
                    _as_mapping(family.get("active")).get("target_lemma") or ""
                ),
                "active_evidence_text": str(
                    _as_mapping(family.get("active")).get("evidence_text") or ""
                ),
                "known_shadow_targets": [
                    str(shadow.get("target_lemma") or "")
                    for shadow in _mapping_rows(family.get("shadows"))
                    if str(shadow.get("target_lemma") or "")
                ],
                "slot_id": str(slot.get("slot_id") or ""),
                "slot_type": str(slot.get("slot_type") or ""),
                "slot_target_lemma": str(slot.get("target_lemma") or ""),
                "requested_items": int(slot.get("requested_items") or 0),
                "purpose": str(slot.get("purpose") or ""),
            }
            request["prompt_text"] = _prompt_text(request)
            request["estimated_input_tokens"] = _estimate_tokens(str(request["prompt_text"]))
            request["expected_output_token_budget"] = (
                int(request["requested_items"]) * EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM
            )
            requests.append(request)
    return requests


def _prompt_text(request: Mapping[str, object]) -> str:
    slot_type = str(request.get("slot_type") or "")
    common = (
        "Return exactly one JSON object. Preserve request_id, family_id, slot_id, "
        "slot_type, source_phrase, and target_lemma exactly as given. Do not include "
        "markdown. Generated English sentences must not contain Spanish target lemmas. "
        "Do not add labels like allow, abstain, active, shadow, or no-winner inside "
        "generated sentences. Every generated sentence must contain source_phrase as an "
        "exact standalone browser-replaceable token separated by spaces or ordinary "
        "punctuation. Do not hide source_phrase inside filenames, URLs, code identifiers, "
        "hashtags, handles, underscores, camelCase, or compounds. Return exactly "
        "requested_items item objects unless you are returning the explicit "
        "unable_to_find_distinct_competitor marker.\n\n"
        f"request_id: {request.get('request_id')}\n"
        f"family_id: {request.get('family_id')}\n"
        f"slot_id: {request.get('slot_id')}\n"
        f"slot_type: {slot_type}\n"
        f"source_phrase: {request.get('trigger')}\n"
        f"target_lemma: {request.get('slot_target_lemma')}\n"
        f"active_target_lemma: {request.get('active_target_lemma')}\n"
        f"active_evidence_text: {request.get('active_evidence_text')}\n"
        f"known_shadow_targets: {', '.join(request.get('known_shadow_targets', [])) or '-'}\n"
        f"requested_items: {request.get('requested_items')}\n\n"
        "Required top-level JSON fields and exact values:\n"
        f"{_top_level_json_skeleton(request)}\n\n"
    )
    if slot_type == "active_evidence_expansion":
        task = (
            "Task: generate concise English evidence examples for the active sense. "
            "Each item should be a natural sentence containing the source_phrase and "
            "making the active target sense clear from context."
        )
        schema = (
            "Schema: {request_id, family_id, slot_id, slot_type, source_phrase, "
            "target_lemma, items:[{sentence, evidence_note}]}"
        )
    elif slot_type == "shadow_or_competitor_evidence_probe":
        task = (
            "Task: generate competitor-sense evidence. First decide whether source_phrase "
            "has a clearly different English sense from the active target sense. Distinct "
            "means the active_target_lemma would be wrong in that sentence and a bilingual "
            "dictionary would reasonably choose another Spanish lemma. If slot target_lemma "
            "is provided, every generated sentence must make that target_lemma the correct "
            "Spanish replacement. Never generate a sentence where target_lemma or "
            "proposed_competitor_target_lemma would be wrong. If the provided target_lemma "
            "does not seem like a valid distinct competitor for source_phrase, return "
            "unable_to_find_distinct_competitor:true with empty items and explain why. If "
            "blank, propose one plausible Spanish competitor target only when it meets "
            "that distinct-sense test. Do not use near-synonyms, stylistic variants, "
            "grammatical meta-examples, or examples that still fit active_evidence_text. "
            "If no clearly distinct competitor exists, return "
            "unable_to_find_distinct_competitor:true with empty items and explain why. "
            "When generating items, include a competitor_sense_label and "
            "active_sense_contrast at the response level. If target_lemma is provided, "
            "leave proposed_competitor_target_lemma blank or set it to exactly the same "
            "target_lemma; do not propose a different lemma. For each item, include "
            "active_mismatch_note that starts with active_target_lemma exactly and explains "
            "why that active target is wrong in the generated sentence. Do not say the "
            "competitor target is wrong. Example: if active_target_lemma is razonable and "
            "target_lemma is correcto, write `razonable is wrong here because ...`, never "
            "`correcto is wrong here because ...`. Before returning, verify each item: "
            "target_lemma/proposed_competitor_target_lemma must be correct for the sentence, "
            "and active_target_lemma must be incorrect."
        )
        schema = (
            "Schema: {request_id, family_id, slot_id, slot_type, source_phrase, "
            "target_lemma, proposed_competitor_target_lemma, "
            "competitor_sense_label, active_sense_contrast, "
            "unable_to_find_distinct_competitor, no_distinct_competitor_reason, "
            "items:[{sentence, evidence_note, active_mismatch_note}]}"
        )
    elif slot_type == "no_winner_context_probe":
        task = (
            "Task: generate browser-like English contexts where source_phrase appears as a "
            "standalone replaceable token, but neither the active Spanish target nor any "
            "known competitor target should be inserted. Each item must set "
            "no_winner_context_class to exactly one of proper_name_or_title, "
            "code_or_identifier, quoted_or_mentioned_word, unrelated_named_entity, "
            "source_language_meta_use, or ui_label. The sentence must contain a visible "
            "anchor for that class: called/named/title/song/album/book for "
            "proper_name_or_title; code/identifier/project/label/file/SKU for "
            "code_or_identifier; word/term/spelled/phrase/quoted for "
            "quoted_or_mentioned_word; company/brand/restaurant/team/product for "
            "unrelated_named_entity; English/translation/vocabulary/dictionary for "
            "source_language_meta_use; or menu/label/button/tab/toolbar for ui_label. "
            "Avoid page titles, visible headings, table labels, search-result fragments, "
            "filenames, file paths, URLs, underscores, embedded-token examples, and "
            "ordinary sentences that simply use the active target sense. Do not use weak "
            "containers like `dashboard`, `file named`, `listed`, `internal project code`, "
            "`placeholder`, or `example sentence`. Each item must explain both why the "
            "replacement should not happen and why the English source token is still a "
            "runtime-like standalone match."
        )
        schema = (
            "Schema: {request_id, family_id, slot_id, slot_type, source_phrase, "
            'target_lemma:"", items:[{sentence, no_winner_context_class, '
            "no_winner_reason, runtime_trigger_note}]}"
        )
    else:
        task = "Task: explain why this slot_type is unsupported."
        schema = "Schema: {request_id, family_id, slot_id, slot_type, error}"
    return common + task + "\n" + schema


def _top_level_json_skeleton(request: Mapping[str, object]) -> str:
    return json.dumps(
        {
            "request_id": str(request.get("request_id") or ""),
            "family_id": str(request.get("family_id") or ""),
            "slot_id": str(request.get("slot_id") or ""),
            "slot_type": str(request.get("slot_type") or ""),
            "source_phrase": str(request.get("trigger") or ""),
            "target_lemma": str(request.get("slot_target_lemma") or ""),
            "items": "...",
        },
        ensure_ascii=False,
    )


def _validate_plan(plan: Mapping[str, object]) -> list[dict[str, object]]:
    issues = []
    families = _mapping_rows(plan.get("pilot_families"))
    if not families:
        issues.append({"severity": "error", "message": "pilot_families is empty"})
    if _as_mapping(plan.get("selection")).get("selection_uses_observed_outcomes") not in (
        False,
        "False",
    ):
        issues.append({"severity": "error", "message": "selection must not use observed outcomes"})
    expected_slot_types = tuple(
        _as_mapping(plan.get("generation_contract")).get("slot_types") or ()
    )
    if tuple(expected_slot_types) != SLOT_TYPE_ORDER:
        issues.append(
            {
                "severity": "error",
                "message": "generation_contract slot_types does not match expected fair pilot contract",
            }
        )
    for family in families:
        slots = _mapping_rows(family.get("planned_generation_slots"))
        slot_types = tuple(str(slot.get("slot_type") or "") for slot in slots)
        if slot_types != SLOT_TYPE_ORDER:
            issues.append(
                {
                    "severity": "error",
                    "message": f"{family.get('family_id')} has invalid slot type order",
                }
            )
    return issues


def _request_checks(
    *,
    plan_payload: Mapping[str, object],
    requests: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    request_ids = [str(request.get("request_id") or "") for request in requests]
    slot_ids = [str(request.get("slot_id") or "") for request in requests]
    families = _mapping_rows(plan_payload.get("pilot_families"))
    expected_request_count = sum(
        len(_mapping_rows(family.get("planned_generation_slots"))) for family in families
    )
    arm_slot_counts = Counter(
        (str(request.get("pilot_arm") or ""), str(request.get("slot_type") or ""))
        for request in requests
    )
    issues = []
    if len(requests) != expected_request_count:
        issues.append(
            {"severity": "error", "message": "request count does not match planned slots"}
        )
    if len(set(request_ids)) != len(request_ids):
        issues.append({"severity": "error", "message": "duplicate request ids"})
    if len(set(slot_ids)) != len(slot_ids):
        issues.append({"severity": "error", "message": "duplicate slot ids"})
    for arm in ("high_need", "middle_control", "low_control"):
        counts = [arm_slot_counts[(arm, slot_type)] for slot_type in SLOT_TYPE_ORDER]
        if len(set(counts)) != 1:
            issues.append({"severity": "error", "message": f"uneven slot counts for {arm}"})
    return {
        "issues": issues,
        "request_count_matches_planned_slots": len(requests) == expected_request_count,
        "unique_request_ids": len(set(request_ids)) == len(request_ids),
        "unique_slot_ids": len(set(slot_ids)) == len(slot_ids),
        "all_requests_have_prompt_text": all(
            bool(request.get("prompt_text")) for request in requests
        ),
        "all_requests_have_positive_requested_items": all(
            int(request.get("requested_items") or 0) > 0 for request in requests
        ),
        "same_slot_counts_per_arm": not any(
            str(issue.get("message") or "").startswith("uneven slot counts") for issue in issues
        ),
    }


def _summary(
    *,
    plan_payload: Mapping[str, object],
    requests: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    families = _mapping_rows(plan_payload.get("pilot_families"))
    by_arm: dict[str, dict[str, object]] = {}
    for arm in ("high_need", "middle_control", "low_control"):
        arm_requests = [request for request in requests if request.get("pilot_arm") == arm]
        by_arm[arm] = {
            "request_count": len(arm_requests),
            "family_count": len({request.get("family_id") for request in arm_requests}),
            "expected_item_count": sum(
                int(request.get("requested_items") or 0) for request in arm_requests
            ),
        }
    by_slot_type: dict[str, dict[str, object]] = {}
    for slot_type in SLOT_TYPE_ORDER:
        slot_requests = [request for request in requests if request.get("slot_type") == slot_type]
        by_slot_type[slot_type] = {
            "request_count": len(slot_requests),
            "expected_item_count": sum(
                int(request.get("requested_items") or 0) for request in slot_requests
            ),
        }
    return {
        "family_count": len(families),
        "request_count": len(requests),
        "expected_generated_item_count": sum(
            int(request.get("requested_items") or 0) for request in requests
        ),
        "estimated_input_tokens": sum(
            int(request.get("estimated_input_tokens") or 0) for request in requests
        ),
        "expected_output_token_budget": sum(
            int(request.get("expected_output_token_budget") or 0) for request in requests
        ),
        "requests_by_arm": by_arm,
        "requests_by_slot_type": by_slot_type,
    }


def _response_contract() -> dict[str, object]:
    return {
        "required_top_level_fields": [
            "request_id",
            "family_id",
            "slot_id",
            "slot_type",
            "source_phrase",
            "target_lemma",
            "items",
        ],
        "item_contract": {
            "active_evidence_expansion": ["sentence", "evidence_note"],
            "shadow_or_competitor_evidence_probe": [
                "sentence",
                "evidence_note",
                "active_mismatch_note",
                "response-level competitor_sense_label",
                "response-level active_sense_contrast",
                "or unable_to_find_distinct_competitor with no_distinct_competitor_reason",
            ],
            "no_winner_context_probe": [
                "sentence",
                "no_winner_context_class",
                "no_winner_reason",
                "runtime_trigger_note",
            ],
        },
        "admission_requirements": [
            "request_id must match the request packet",
            "slot_id must match the request packet",
            "English sentence must contain the source phrase",
            "source phrase must be an exact standalone browser-replaceable token",
            "no-winner examples must not rely on filename, URL, code, or underscore containers",
            "no-winner examples must declare an allowed context class and visibly match it",
            "shadow examples must include a contrast note against the active sense",
            "English sentence must not contain Spanish target lemmas",
            "label leakage words must be absent from generated sentences",
        ],
    }


def _request_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)[:12]
    if not rows:
        return "_No requests._"
    headers = ["arm", "rank", "trigger", "slot", "items", "prompt chars"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('pilot_arm') or ''))}`",
                    str(row.get("arm_rank") or ""),
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('slot_type') or ''))}`",
                    str(row.get("requested_items") or 0),
                    str(len(str(row.get("prompt_text") or ""))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
