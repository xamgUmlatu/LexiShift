#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_llm_pilot_admission_en_es import (  # noqa: E402
    _as_mapping,
    _load_json,
    _mapping_rows,
    _repo_path,
    _validate_plan,
)


DEFAULT_PLAN = PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_llm_pilot_plan_en_es.json"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generation_requests_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generation_requests_en_es_latest.md"
)
PROMPT_ID = "semantic_veto_eval_sentence_pilot_v1"
REQUEST_KIND = "semantic_veto_eval_sentence"
GOLD_TYPE_ORDER = ("positive_active", "shadow_negative", "phrase_no_winner")
STRATA_AXIS_ORDER = (
    "word_order",
    "trigger_position",
    "context_distance",
    "morphology",
    "register",
    "difficulty",
)
EXPECTED_OUTPUT_TOKEN_BUDGET_PER_REQUEST = 120


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render the no-spend generation request packet for the en-es semantic-veto "
            "LLM evaluation pilot."
        )
    )
    parser.add_argument("--plan-json", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_semantic_veto_llm_pilot_generation_request_report(
        plan_payload=_load_json(args.plan_json),
        plan_path=args.plan_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_semantic_veto_llm_pilot_generation_request_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_semantic_veto_llm_pilot_generation_request_report(
    *,
    plan_payload: Mapping[str, object],
    plan_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    plan_issues = _validate_plan(plan_payload)
    requests = [] if plan_issues else _build_requests(plan_payload)
    planned_count = _planned_row_count(plan_payload)
    request_checks = _request_checks(
        plan_payload=plan_payload,
        requests=requests,
        planned_count=planned_count,
    )
    request_issues = [
        issue for issue in request_checks["issues"] if str(issue.get("severity") or "") == "error"
    ]
    status = "ok" if not plan_issues and not request_issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "ready_for_llm_batch_execution" if status == "ok" else "request_packet_needs_repair"
        ),
        "generated_at": generated_at,
        "pair": str(plan_payload.get("pair") or ""),
        "pilot": {
            "plan_path": _repo_path(plan_path),
            "pilot_id": str(plan_payload.get("pilot_id") or ""),
            "plan_status": str(plan_payload.get("status") or ""),
            "request_kind": REQUEST_KIND,
            "prompt_id": PROMPT_ID,
        },
        "candidate": dict(_as_mapping(plan_payload.get("candidate"))),
        "strict_flow": {
            "runtime_policy_change": str(
                _as_mapping(plan_payload.get("candidate")).get("runtime_policy_change") or ""
            ),
            "source_evidence_promotion": str(
                _as_mapping(plan_payload.get("candidate")).get("source_evidence_promotion") or ""
            ),
            "request_packet_role": "pre_spend_generation_inputs",
            "generated_row_role": "evaluation_data_only",
        },
        "plan_checks": {
            "issue_count": len(plan_issues),
            "issues": plan_issues,
        },
        "request_checks": request_checks,
        "summary": _summary(
            requests=requests,
            planned_count=planned_count,
            plan_payload=plan_payload,
        ),
        "prompt_contract": _prompt_contract(plan_payload),
        "requests": requests,
        "next_steps": _next_steps(status=status),
        "limitations": [
            "no LLM call is made by this script",
            "request packet is not generated data",
            "generated rows must pass admission before scoring",
            "locked-eval rows cannot be used for threshold selection",
            "runtime policy remains unchanged",
        ],
    }


def render_semantic_veto_llm_pilot_generation_request_markdown(
    report: Mapping[str, object],
) -> str:
    pilot = _as_mapping(report.get("pilot"))
    candidate = _as_mapping(report.get("candidate"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM Pilot Generation Requests",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Plan: `{pilot.get('plan_path', '')}`",
        f"- Prompt id: `{pilot.get('prompt_id', '')}`",
        f"- Candidate: `{candidate.get('candidate_id', '')}`",
        f"- Runtime policy change: `{candidate.get('runtime_policy_change', '')}`",
        "",
        "## Summary",
        "",
        f"- Planned rows: `{summary.get('planned_request_count', 0)}`",
        f"- Requests rendered: `{summary.get('request_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Requests by type: `{_inline_counts(summary.get('requests_by_gold_type'))}`",
        f"- Estimated input tokens: `{summary.get('estimated_input_tokens', 0)}`",
        f"- Expected output-token budget: `{summary.get('expected_output_token_budget', 0)}`",
        "",
        "## Contract",
        "",
        "- Output must be one JSON object per request.",
        "- Output sentence must contain the English trigger.",
        "- Output sentence must not contain the Spanish candidate replacement.",
        "- Output sentence must not contain labels such as allow, abstain, or gold decision.",
        "- Generated rows are evaluation data only.",
        "",
        "## Request Samples",
        "",
        _request_table(report.get("requests")),
        "",
        "## Strata Coverage",
        "",
        _strata_table(summary.get("requests_by_strata")),
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _build_requests(plan: Mapping[str, object]) -> list[dict[str, object]]:
    pilot_id = str(plan.get("pilot_id") or "").strip()
    candidate = _as_mapping(plan.get("candidate"))
    strata = _as_mapping(plan.get("generation_strata"))
    decision_by_gold_type = _as_mapping(
        _as_mapping(plan.get("row_contract")).get("decision_by_gold_type")
    )
    requests: list[dict[str, object]] = []
    ordinal = 0
    for family in _mapping_rows(plan.get("pilot_families")):
        planned_rows = _as_mapping(family.get("planned_rows"))
        for gold_type in GOLD_TYPE_ORDER:
            planned_count = int(planned_rows.get(gold_type) or 0)
            for within_type_index in range(1, planned_count + 1):
                ordinal += 1
                strata_values = _strata_values(strata=strata, ordinal=ordinal)
                expected_row_id = _expected_row_id(
                    family_id=str(family.get("family_id") or ""),
                    gold_type=gold_type,
                    index=within_type_index,
                )
                request = {
                    "request_id": f"{pilot_id}:{expected_row_id}",
                    "request_kind": REQUEST_KIND,
                    "prompt_id": PROMPT_ID,
                    "expected_row_id": expected_row_id,
                    "family_id": str(family.get("family_id") or ""),
                    "trigger": str(family.get("trigger") or ""),
                    "candidate_replacement": str(family.get("candidate_replacement") or ""),
                    "active_sense": str(family.get("active_sense") or ""),
                    "pos": str(family.get("pos") or ""),
                    "gold_type": gold_type,
                    "gold_decision": str(decision_by_gold_type.get(gold_type) or ""),
                    "candidate_id": str(candidate.get("candidate_id") or ""),
                    "strata": strata_values,
                    "prompt_text": _prompt_text(
                        family=family,
                        gold_type=gold_type,
                        gold_decision=str(decision_by_gold_type.get(gold_type) or ""),
                        expected_row_id=expected_row_id,
                        strata_values=strata_values,
                    ),
                }
                request["estimated_input_tokens"] = _estimate_tokens(str(request["prompt_text"]))
                request["expected_output_token_budget"] = EXPECTED_OUTPUT_TOKEN_BUDGET_PER_REQUEST
                requests.append(request)
    return requests


def _prompt_text(
    *,
    family: Mapping[str, object],
    gold_type: str,
    gold_decision: str,
    expected_row_id: str,
    strata_values: Mapping[str, object],
) -> str:
    trigger = str(family.get("trigger") or "")
    candidate_replacement = str(family.get("candidate_replacement") or "")
    active_sense = str(family.get("active_sense") or "")
    pos = str(family.get("pos") or "")
    family_id = str(family.get("family_id") or "")
    type_instruction = _type_instruction(gold_type=gold_type, active_sense=active_sense)
    return "\n".join(
        [
            "Create one natural English browser sentence for LexiShift semantic-veto evaluation.",
            "",
            "Return exactly one JSON object and no prose outside JSON.",
            "",
            "Family:",
            f"- family_id: {family_id}",
            f"- trigger: {trigger}",
            f"- candidate_replacement: {candidate_replacement}",
            f"- active_sense: {active_sense}",
            f"- pos: {pos}",
            f"- gold_type: {gold_type}",
            f"- gold_decision: {gold_decision}",
            "",
            "Sentence requirements:",
            f"- The sentence must contain the English trigger word or phrase: {trigger}",
            f"- The sentence must not contain the Spanish candidate replacement: {candidate_replacement}",
            "- The sentence must not contain the labels allow, abstain, gold decision, or candidate replacement.",
            "- The sentence must be ordinary English that could appear in a browser page.",
            "- The sentence must end with punctuation.",
            f"- Use this target stratum: {_strata_inline(strata_values)}",
            "",
            "Semantic target:",
            type_instruction,
            "",
            "JSON schema:",
            "{",
            f'  "row_id": "{expected_row_id}",',
            f'  "family_id": "{family_id}",',
            f'  "trigger": "{trigger}",',
            f'  "candidate_replacement": "{candidate_replacement}",',
            '  "sentence": "...",',
            f'  "gold_decision": "{gold_decision}",',
            f'  "gold_type": "{gold_type}",',
            f'  "active_sense": "{active_sense}",',
            '  "negative_sense": "... only for shadow_negative, else empty string",',
            '  "no_winner_reason": "... only for phrase_no_winner, else empty string",',
            '  "gold_reason": "one short reason based only on the sentence meaning",',
            f'  "pos": "{pos}",',
            '  "generator_id": "operator-filled-model-id",',
            f'  "prompt_id": "{PROMPT_ID}",',
            '  "difficulty_tags": ["..."]',
            "}",
        ]
    )


def _type_instruction(*, gold_type: str, active_sense: str) -> str:
    if gold_type == "positive_active":
        return (
            "Make the trigger clearly mean the active sense "
            f"({active_sense}), so the candidate replacement should be shown."
        )
    if gold_type == "shadow_negative":
        return (
            "Make the trigger clearly mean a different concrete sense, not "
            f"the active sense ({active_sense}), so the candidate replacement should be hidden. "
            "Fill negative_sense with that different sense."
        )
    return (
        "Use the trigger inside an idiom, lexicalized phrase, or phrase-like expression where "
        "the candidate replacement should be hidden because neither the active sense nor one "
        "ordinary alternate noun sense is the right explanation. Fill no_winner_reason."
    )


def _request_checks(
    *,
    plan_payload: Mapping[str, object],
    requests: list[Mapping[str, object]],
    planned_count: int,
) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    if len(requests) != planned_count:
        issues.append(
            {
                "subject": "request_count",
                "severity": "error",
                "message": f"Rendered {len(requests)} requests for {planned_count} planned rows.",
            }
        )
    duplicate_request_ids = _duplicates(str(row.get("request_id") or "") for row in requests)
    duplicate_row_ids = _duplicates(str(row.get("expected_row_id") or "") for row in requests)
    for request_id in duplicate_request_ids:
        issues.append(
            {
                "subject": request_id,
                "severity": "error",
                "message": "Duplicate request_id.",
            }
        )
    for row_id in duplicate_row_ids:
        issues.append(
            {
                "subject": row_id,
                "severity": "error",
                "message": "Duplicate expected_row_id.",
            }
        )
    request_counts = Counter(
        (str(row.get("family_id") or ""), str(row.get("gold_type") or "")) for row in requests
    )
    for family in _mapping_rows(plan_payload.get("pilot_families")):
        family_id = str(family.get("family_id") or "")
        planned_rows = _as_mapping(family.get("planned_rows"))
        for gold_type in GOLD_TYPE_ORDER:
            expected_count = int(planned_rows.get(gold_type) or 0)
            actual_count = request_counts.get((family_id, gold_type), 0)
            if actual_count != expected_count:
                issues.append(
                    {
                        "subject": f"{family_id}:{gold_type}",
                        "severity": "error",
                        "message": (
                            f"Rendered {actual_count} requests for {expected_count} planned rows."
                        ),
                    }
                )
    return {
        "issue_count": len(issues),
        "issues": issues,
        "request_count_matches_plan": len(requests) == planned_count,
        "unique_request_ids": not duplicate_request_ids,
        "unique_expected_row_ids": not duplicate_row_ids,
    }


def _summary(
    *,
    requests: list[Mapping[str, object]],
    planned_count: int,
    plan_payload: Mapping[str, object],
) -> dict[str, object]:
    strata_counts = {
        axis: dict(
            sorted(
                Counter(
                    str(_as_mapping(row.get("strata")).get(axis) or "") for row in requests
                ).items()
            )
        )
        for axis in STRATA_AXIS_ORDER
    }
    return {
        "planned_request_count": planned_count,
        "request_count": len(requests),
        "family_count": len(_mapping_rows(plan_payload.get("pilot_families"))),
        "requests_by_gold_type": dict(
            sorted(Counter(str(row.get("gold_type") or "") for row in requests).items())
        ),
        "requests_by_family": dict(
            sorted(Counter(str(row.get("family_id") or "") for row in requests).items())
        ),
        "requests_by_strata": strata_counts,
        "estimated_input_tokens": sum(
            int(row.get("estimated_input_tokens") or 0) for row in requests
        ),
        "expected_output_token_budget": sum(
            int(row.get("expected_output_token_budget") or 0) for row in requests
        ),
    }


def _prompt_contract(plan_payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "prompt_id": PROMPT_ID,
        "request_kind": REQUEST_KIND,
        "row_contract": dict(_as_mapping(plan_payload.get("row_contract"))),
        "admission_filters": [
            str(row.get("filter_id") or "")
            for row in _mapping_rows(plan_payload.get("admission_filters"))
        ],
        "output_role": "evaluation_data_only",
    }


def _next_steps(*, status: str) -> list[str]:
    if status != "ok":
        return [
            "Repair the request packet before any LLM execution.",
            "Rerun this harness with --fail-on-review before generation.",
        ]
    return [
        "Execute the request packet as a bounded LLM batch only when spend is approved.",
        "Preserve raw responses and normalize them into the row contract without editing labels after seeing scores.",
        "Run semantic_veto_llm_pilot_admission_en_es.py on the generated rows.",
        "Score admitted discovery and locked-eval rows separately with the frozen veto-only candidate.",
    ]


def _planned_row_count(plan_payload: Mapping[str, object]) -> int:
    total = 0
    for family in _mapping_rows(plan_payload.get("pilot_families")):
        planned_rows = _as_mapping(family.get("planned_rows"))
        total += sum(int(planned_rows.get(gold_type) or 0) for gold_type in GOLD_TYPE_ORDER)
    return total


def _strata_values(*, strata: Mapping[str, object], ordinal: int) -> dict[str, object]:
    values: dict[str, object] = {}
    for axis_index, axis in enumerate(STRATA_AXIS_ORDER):
        axis_values = _as_sequence(strata.get(axis))
        if not axis_values:
            values[axis] = ""
            continue
        values[axis] = str(axis_values[(ordinal + axis_index - 1) % len(axis_values)])
    return values


def _expected_row_id(*, family_id: str, gold_type: str, index: int) -> str:
    family_slug = re.sub(r"[^a-z0-9]+", "_", family_id.lower()).strip("_")
    return f"pilotrow:{family_slug}:{gold_type}:{index:03d}"


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def _duplicates(values: object) -> list[str]:
    counts = Counter(str(value) for value in values if str(value))
    return sorted(value for value, count in counts.items() if count > 1)


def _strata_inline(strata_values: Mapping[str, object]) -> str:
    return ", ".join(f"{axis}={strata_values.get(axis, '')}" for axis in STRATA_AXIS_ORDER)


def _inline_counts(value: object) -> str:
    mapping = _as_mapping(value)
    return ", ".join(f"{key}: {mapping[key]}" for key in sorted(mapping)) or "none"


def _request_table(value: object) -> str:
    rows = _as_sequence(value)
    lines = [
        "| Request | Family | Type | Decision | Strata |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows[:18]:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('expected_row_id') or ''))}`",
                    f"`{_escape_md(str(row.get('family_id') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_type') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_decision') or ''))}`",
                    _escape_md(_strata_inline(_as_mapping(row.get("strata")))),
                ]
            )
            + " |"
        )
    if len(rows) > 18:
        lines.append(f"| _{len(rows) - 18} more requests omitted from preview._ |  |  |  |  |")
    if len(lines) == 2:
        lines.append("| _No requests rendered._ |  |  |  |  |")
    return "\n".join(lines)


def _strata_table(value: object) -> str:
    mapping = _as_mapping(value)
    lines = ["| Axis | Counts |", "| --- | --- |"]
    for axis in STRATA_AXIS_ORDER:
        lines.append(f"| `{axis}` | {_escape_md(_inline_counts(mapping.get(axis)))} |")
    return "\n".join(lines)


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
