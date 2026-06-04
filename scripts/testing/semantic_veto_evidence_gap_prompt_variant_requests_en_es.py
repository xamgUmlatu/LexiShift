#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SEMANTIC_CASES_ROOT = TEST_INPUTS_ROOT / "semantic_routing_cases"

DEFAULT_SOURCE_REQUEST_JSON = (
    TEST_INPUTS_ROOT / "semantic_veto_evidence_gap_active_only_poc_requests_en_es.json"
)
DEFAULT_DATASET_JSON = SEMANTIC_CASES_ROOT / "en_es_full_family_repaired_full_v1.json"
DEFAULT_PACKET_DIR = TEST_INPUTS_ROOT / "semantic_veto_evidence_gap_prompt_variant_requests_en_es"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_prompt_variant_requests_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_prompt_variant_requests_en_es_latest.md"
)
ACTIVE_SLOT = "active_evidence_expansion"
REQUEST_KIND = "semantic_veto_evidence_gap_generation"
EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM = 170
VARIANTS = (
    {
        "variant_id": "v5_refresh_control",
        "prompt_id": "semantic_veto_evidence_gap_generation_v5_refresh_control",
        "description": "Regenerate the current v5 active-only prompt as a variance control.",
        "pos_rules": False,
        "diversity_rules": False,
        "reuse_source_prompt": True,
    },
    {
        "variant_id": "v6_pos_only",
        "prompt_id": "semantic_veto_evidence_gap_generation_v6_pos_only",
        "description": "Add expected-POS and source-frame instructions while leaving topic diversity mostly unchanged.",
        "pos_rules": True,
        "diversity_rules": False,
        "reuse_source_prompt": False,
    },
    {
        "variant_id": "v6_diversity_only",
        "prompt_id": "semantic_veto_evidence_gap_generation_v6_diversity_only",
        "description": "Add topic/frame diversity instructions without explicit POS-frame requirements.",
        "pos_rules": False,
        "diversity_rules": True,
        "reuse_source_prompt": False,
    },
    {
        "variant_id": "v6_pos_diversity",
        "prompt_id": "semantic_veto_evidence_gap_generation_v6_pos_diversity",
        "description": "Combine expected-POS grammar anchoring with topic/frame diversity instructions.",
        "pos_rules": True,
        "diversity_rules": True,
        "reuse_source_prompt": False,
    },
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render no-spend active-only prompt-variant packets over the same frozen "
            "24-family semantic-veto PoC denominator."
        )
    )
    parser.add_argument("--source-request-json", type=Path, default=DEFAULT_SOURCE_REQUEST_JSON)
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source_payload = _load_json(args.source_request_json)
    dataset_payload = _load_json(args.dataset_json)
    packets = build_prompt_variant_packets(
        source_payload=source_payload,
        dataset_payload=dataset_payload,
    )
    args.packet_dir.mkdir(parents=True, exist_ok=True)
    packet_paths: dict[str, Path] = {}
    for variant_id, packet in packets.items():
        packet_path = args.packet_dir / f"{variant_id}.json"
        packet_path.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        packet_paths[variant_id] = packet_path
    report = build_prompt_variant_manifest(
        packets=packets,
        packet_paths=packet_paths,
        source_path=args.source_request_json,
        dataset_path=args.dataset_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_prompt_variant_manifest_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    print(f"Wrote {len(packet_paths)} request packets to {args.packet_dir}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_prompt_variant_packets(
    *,
    source_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    generated_at: str | None = None,
) -> dict[str, dict[str, object]]:
    generated_at = generated_at or _utc_now()
    source_requests = [
        row
        for row in _mapping_rows(source_payload.get("requests"))
        if str(row.get("slot_type") or "") == ACTIVE_SLOT
    ]
    family_pos = _family_pos_map(dataset_payload)
    packets: dict[str, dict[str, object]] = {}
    for variant in VARIANTS:
        variant_id = str(variant["variant_id"])
        requests = [
            _variant_request(
                request=row,
                variant=variant,
                expected_pos=family_pos.get(str(row.get("family_id") or ""), ""),
            )
            for row in source_requests
        ]
        issues = _validate_packet_requests(requests)
        status = "ok" if not issues else "review"
        packets[variant_id] = {
            "schema_version": 1,
            "status": status,
            "decision": (
                "prompt_variant_request_packet_ready"
                if status == "ok"
                else "prompt_variant_request_packet_needs_review"
            ),
            "generated_at": generated_at,
            "pair": str(source_payload.get("pair") or "en-es"),
            "pilot": {
                "pilot_id": f"{_as_mapping(source_payload.get('pilot')).get('pilot_id')}:prompt_variant:{variant_id}",
                "plan_status": str(
                    _as_mapping(source_payload.get("pilot")).get("plan_status") or ""
                ),
                "request_kind": REQUEST_KIND,
                "prompt_id": str(variant["prompt_id"]),
                "source_prompt_id": str(
                    _as_mapping(source_payload.get("pilot")).get("prompt_id") or ""
                ),
                "prompt_variant_id": variant_id,
                "prompt_variant_description": str(variant["description"]),
            },
            "strict_flow": {
                "runtime_policy_change": "none",
                "llm_call": "none",
                "threshold_tuning": "none",
                "request_packet_role": "active_only_prompt_variant_generation_inputs",
                "same_families_as_active_only_poc": True,
            },
            "summary": _summary(requests),
            "request_checks": {
                "issue_count": len(issues),
                "issues": issues,
                "selected_slot_type": ACTIVE_SLOT,
                "selected_request_count": len(requests),
            },
            "requests": requests,
            "limitations": [
                "no LLM call is made by this script",
                "variant packets preserve the same 24-family active-only denominator",
                "variant results must be admitted and postprocessed before comparison",
                "prompt-side self labels are diagnostic and must be checked mechanically",
            ],
        }
    return packets


def build_prompt_variant_manifest(
    *,
    packets: Mapping[str, Mapping[str, object]],
    packet_paths: Mapping[str, Path],
    source_path: Path | None = None,
    dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    rows = []
    issues = []
    family_sets = []
    for variant in VARIANTS:
        variant_id = str(variant["variant_id"])
        packet = _as_mapping(packets.get(variant_id))
        requests = _mapping_rows(packet.get("requests"))
        family_ids = sorted(str(row.get("family_id") or "") for row in requests)
        family_sets.append(family_ids)
        if str(packet.get("status") or "") != "ok":
            issues.append(
                {
                    "severity": "error",
                    "variant_id": variant_id,
                    "message": "variant packet is not ok",
                }
            )
        rows.append(
            {
                "variant_id": variant_id,
                "prompt_id": str(variant["prompt_id"]),
                "description": str(variant["description"]),
                "packet_path": _repo_path(packet_paths.get(variant_id)),
                "request_count": len(requests),
                "family_count": len(set(family_ids)),
                "expected_generated_item_count": sum(
                    int(row.get("requested_items") or 0) for row in requests
                ),
                "estimated_input_tokens": sum(
                    int(row.get("estimated_input_tokens") or 0) for row in requests
                ),
                "expected_output_token_budget": sum(
                    int(row.get("expected_output_token_budget") or 0) for row in requests
                ),
            }
        )
    if family_sets and any(family_ids != family_sets[0] for family_ids in family_sets):
        issues.append(
            {
                "severity": "error",
                "message": "variant packets do not preserve the same family denominator",
            }
        )
    status = "ok" if not issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "prompt_variant_request_packets_ready"
            if status == "ok"
            else "prompt_variant_request_packets_need_review"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "inputs": {
            "source_request_json": _repo_path(source_path),
            "dataset_json": _repo_path(dataset_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_call": "none",
            "threshold_tuning": "none",
            "same_family_denominator": "all variants use the frozen 24 active-only PoC families",
            "primary_later_comparison": "postprocess no_high_eval_overlap_sentence_only view",
        },
        "summary": {
            "variant_count": len(rows),
            "issue_count": len(issues),
            "issues": issues,
            "request_count_per_variant": rows[0]["request_count"] if rows else 0,
            "total_request_count_if_all_variants_run": sum(
                int(row["request_count"]) for row in rows
            ),
            "total_expected_generated_items_if_all_variants_run": sum(
                int(row["expected_generated_item_count"]) for row in rows
            ),
        },
        "variants": rows,
        "next_steps": [
            "Run each variant packet with the existing generation runner and explicit spend guards.",
            "Admit each variant response bundle against the matching variant request packet.",
            "Run the generated-evidence postprocess report for each variant.",
            "Compare variants on the no_high_eval_overlap_sentence_only view before scaling.",
        ],
    }


def render_prompt_variant_manifest_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Active-Only Prompt Variant Requests",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Variants: `{summary.get('variant_count', 0)}`",
        f"- Requests per variant: `{summary.get('request_count_per_variant', 0)}`",
        f"- Total requests if all variants run: `{summary.get('total_request_count_if_all_variants_run', 0)}`",
        f"- Total expected generated items if all variants run: `{summary.get('total_expected_generated_items_if_all_variants_run', 0)}`",
        "",
        "## Variants",
        "",
        "| Variant | Requests | Families | Items | Input tokens | Output budget | Packet |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("variants")):
        lines.append(
            f"| `{_escape_md(str(row.get('variant_id') or ''))}` | "
            f"{row.get('request_count', 0)} | {row.get('family_count', 0)} | "
            f"{row.get('expected_generated_item_count', 0)} | "
            f"{row.get('estimated_input_tokens', 0)} | "
            f"{row.get('expected_output_token_budget', 0)} | "
            f"`{_escape_md(str(row.get('packet_path') or ''))}` |"
        )
    lines.extend(["", "## Methodology", ""])
    for key, value in _as_mapping(report.get("methodology")).items():
        lines.append(f"- `{_escape_md(str(key))}`: {value}")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _variant_request(
    *,
    request: Mapping[str, object],
    variant: Mapping[str, object],
    expected_pos: str,
) -> dict[str, object]:
    row = deepcopy(dict(request))
    row["prompt_variant_id"] = str(variant["variant_id"])
    row["prompt_id"] = str(variant["prompt_id"])
    row["expected_pos"] = expected_pos
    if bool(variant.get("reuse_source_prompt")):
        row["prompt_text"] = str(request.get("prompt_text") or "")
        row["expected_output_token_budget"] = int(request.get("expected_output_token_budget") or 0)
        row["estimated_input_tokens"] = _estimate_tokens(str(row["prompt_text"]))
        return row
    row["prompt_text"] = _prompt_text(
        request=request,
        variant=variant,
        expected_pos=expected_pos,
    )
    row["estimated_input_tokens"] = _estimate_tokens(str(row["prompt_text"]))
    row["expected_output_token_budget"] = (
        int(row.get("requested_items") or 0) * EXPECTED_OUTPUT_TOKEN_BUDGET_PER_ITEM
    )
    return row


def _prompt_text(
    *,
    request: Mapping[str, object],
    variant: Mapping[str, object],
    expected_pos: str,
) -> str:
    source_phrase = str(request.get("trigger") or "")
    target_lemma = str(request.get("slot_target_lemma") or request.get("active_target_lemma") or "")
    requested_items = int(request.get("requested_items") or 0)
    lines = [
        "Return exactly one JSON object. Preserve request_id, family_id, slot_id, slot_type, source_phrase, and target_lemma exactly as given. Do not include markdown.",
        "Generated English sentences must not contain Spanish target lemmas or Spanish words.",
        "Do not add labels like allow, abstain, active, shadow, replace, or no-winner inside generated sentences.",
        "Every generated sentence must contain source_phrase as an exact standalone browser-replaceable token separated by spaces or ordinary punctuation.",
        "Do not hide source_phrase inside filenames, URLs, code identifiers, hashtags, handles, underscores, camelCase, or compounds.",
        "Do not write definition-style sentences such as 'X means ...', 'X refers to ...', or calendar/translation explanations unless that is ordinary browser text.",
        f"Return exactly {requested_items} item objects.",
        "",
        f"request_id: {request.get('request_id')}",
        f"family_id: {request.get('family_id')}",
        f"slot_id: {request.get('slot_id')}",
        f"slot_type: {request.get('slot_type')}",
        f"source_phrase: {source_phrase}",
        f"target_lemma: {target_lemma}",
        f"active_target_lemma: {request.get('active_target_lemma')}",
        f"expected_pos: {expected_pos or 'unknown'}",
        f"active_evidence_text: {request.get('active_evidence_text')}",
        f"requested_items: {requested_items}",
        "",
        "Required top-level JSON fields and exact values:",
        _top_level_json_skeleton(request=request, target_lemma=target_lemma),
        "",
        "Task: generate concise natural English browser-like evidence examples for the active sense. Each item should make the active target sense clear from ordinary context.",
    ]
    if bool(variant.get("pos_rules")):
        lines.extend(["", _pos_instruction(expected_pos=expected_pos, source_phrase=source_phrase)])
    if bool(variant.get("diversity_rules")):
        lines.extend(
            [
                "",
                "Diversity rules: the requested items must use different surrounding topics and different sentence frames when possible. Do not make both items rely on the same common event frame, time phrase, object, or collocate cluster. Prefer ordinary browser-like contexts over textbook definitions.",
            ]
        )
    lines.extend(
        [
            "",
            "For each item, include sentence, evidence_note, source_pos_frame, topic_frame, and diversity_note.",
            "source_pos_frame should name the grammar frame you intended, such as verb_infinitive, verb_after_modal, noun_determined, adjective_attributive, adverb_modifier, preposition_phrase, or other.",
            "topic_frame should summarize the ordinary real-world topic in a short phrase.",
            "diversity_note should explain how this item differs from the other generated item(s).",
            "Schema: {request_id, family_id, slot_id, slot_type, source_phrase, target_lemma, items:[{sentence, evidence_note, source_pos_frame, topic_frame, diversity_note}]}",
        ]
    )
    return "\n".join(lines)


def _pos_instruction(*, expected_pos: str, source_phrase: str) -> str:
    expected = expected_pos.lower()
    if expected == "verb":
        return (
            "Grammar rule: expected_pos is verb. Make source_phrase unmistakably a verb. "
            f"Prefer frames like 'to {source_phrase}', 'can {source_phrase}', 'will {source_phrase}', or a subject performing the action. "
            f"Avoid noun-like frames such as 'a {source_phrase}', 'the {source_phrase}', or possessive + {source_phrase}."
        )
    if expected == "noun":
        return (
            "Grammar rule: expected_pos is noun. Make source_phrase unmistakably a noun. "
            f"Prefer frames like 'a {source_phrase}', 'the {source_phrase}', or source_phrase as a concrete noun phrase when natural."
        )
    if expected == "adjective":
        return (
            "Grammar rule: expected_pos is adjective. Make source_phrase unmistakably an adjective. "
            "Prefer attributive or predicative adjective frames, such as source_phrase before a noun or after a linking verb."
        )
    if expected == "adverb":
        return "Grammar rule: expected_pos is adverb. Make source_phrase unmistakably an adverb modifying an adjective, verb, or clause."
    if expected == "preposition":
        return "Grammar rule: expected_pos is preposition. Make source_phrase unmistakably a preposition introducing a normal phrase."
    return "Grammar rule: use source_phrase in the same part of speech implied by active_evidence_text and make the grammar unambiguous."


def _top_level_json_skeleton(*, request: Mapping[str, object], target_lemma: str) -> str:
    return json.dumps(
        {
            "request_id": str(request.get("request_id") or ""),
            "family_id": str(request.get("family_id") or ""),
            "slot_id": str(request.get("slot_id") or ""),
            "slot_type": str(request.get("slot_type") or ""),
            "source_phrase": str(request.get("trigger") or ""),
            "target_lemma": target_lemma,
            "items": "...",
        },
        ensure_ascii=False,
    )


def _validate_packet_requests(requests: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if len(requests) != 24:
        issues.append({"severity": "error", "message": "expected exactly 24 active requests"})
    family_ids = [str(row.get("family_id") or "") for row in requests]
    if len(set(family_ids)) != len(requests):
        issues.append({"severity": "error", "message": "expected one request per family"})
    arm_counts = Counter(str(row.get("pilot_arm") or "") for row in requests)
    if dict(arm_counts) != {"high_need": 8, "low_control": 8, "middle_control": 8}:
        issues.append({"severity": "error", "message": f"unbalanced arms: {dict(arm_counts)}"})
    for row in requests:
        request_id = str(row.get("request_id") or "")
        if str(row.get("slot_type") or "") != ACTIVE_SLOT:
            issues.append(
                {"severity": "error", "request_id": request_id, "message": "non-active slot"}
            )
        if not str(row.get("prompt_text") or ""):
            issues.append(
                {"severity": "error", "request_id": request_id, "message": "missing prompt_text"}
            )
        if int(row.get("requested_items") or 0) != 2:
            issues.append(
                {"severity": "error", "request_id": request_id, "message": "expected 2 items"}
            )
    return issues


def _summary(requests: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_arm: dict[str, dict[str, object]] = {}
    for arm in ("high_need", "middle_control", "low_control"):
        rows = [row for row in requests if str(row.get("pilot_arm") or "") == arm]
        by_arm[arm] = {
            "request_count": len(rows),
            "family_count": len({str(row.get("family_id") or "") for row in rows}),
            "expected_item_count": sum(int(row.get("requested_items") or 0) for row in rows),
        }
    return {
        "family_count": len({str(row.get("family_id") or "") for row in requests}),
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
    }


def _family_pos_map(dataset_payload: Mapping[str, object]) -> dict[str, str]:
    return {
        str(family.get("family_id") or ""): str(
            _as_mapping(family.get("active")).get("canonical_pos") or ""
        ).lower()
        for family in _mapping_rows(dataset_payload.get("families"))
    }


def _estimate_tokens(value: str) -> int:
    return max(1, int(len(value) / 4.0) + 1)


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
