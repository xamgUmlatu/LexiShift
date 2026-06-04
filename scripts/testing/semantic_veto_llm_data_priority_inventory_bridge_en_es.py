#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from math import log1p
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_llm_data_priority_scan_en_es import FORBIDDEN_RANKING_FIELDS
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _load_json,
    _repo_path,
    _resolve_repo_path,
    _safe_float,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_INVENTORY_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_non_v10_inventory_candidates_wave7_source_class_breadth_v1_latest.json"
)
DEFAULT_PRIORITY_SCAN_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_scan_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_inventory_bridge_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_inventory_bridge_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bridge English-only ambiguous inventory candidates to the semantic-veto LLM "
            "data priority scanner without pretending inventory-only rows are ready for "
            "active/shadow/phrase LLM generation."
        )
    )
    parser.add_argument("--inventory-json", type=Path, default=DEFAULT_INVENTORY_JSON)
    parser.add_argument("--priority-scan-json", type=Path, default=DEFAULT_PRIORITY_SCAN_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_llm_data_priority_inventory_bridge_report(
    *,
    inventory_payload: Mapping[str, object],
    priority_scan_payload: Mapping[str, object],
    inventory_json_path: Path | None = None,
    priority_scan_json_path: Path | None = None,
    top_n: int = 50,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    scan_by_trigger = _priority_scan_rows_by_trigger(priority_scan_payload)
    rows = [
        _inventory_bridge_row(
            candidate=row, scan_rows=scan_by_trigger.get(str(row.get("trigger") or "").lower(), [])
        )
        for row in _mapping_rows(inventory_payload.get("candidates"))
    ]
    rows.sort(
        key=lambda row: (
            _stage_sort_weight(str(row.get("readiness_stage") or "")),
            -_safe_float(row.get("inventory_source_need")),
            str(row.get("trigger") or ""),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["priority_rank"] = index
        row["in_top_n"] = index <= int(top_n)
    issues = _issues(rows)
    status = "review" if issues else "ok"
    report = {
        "schema_version": 1,
        "pair": str(inventory_payload.get("pair") or priority_scan_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "llm_data_priority_inventory_bridge_established"
            if status == "ok"
            else "llm_data_priority_inventory_bridge_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "inventory_json": _repo_path(inventory_json_path),
            "priority_scan_json": _repo_path(priority_scan_json_path),
            "inventory_decision": str(inventory_payload.get("decision") or ""),
            "priority_scan_decision": str(priority_scan_payload.get("decision") or ""),
        },
        "end_state_contract": _end_state_contract(),
        "methodology": {
            "ranking_scope": (
                "English ambiguous inventory candidates plus any already-scored "
                "trigger/target priority rows from the current LLM data priority scan."
            ),
            "inventory_only_rule": (
                "An English-only inventory candidate cannot receive active/shadow/phrase "
                "LLM row budgets until a target/shadow family exists."
            ),
            "ranking_fields": [
                "inventory_score",
                "sense_count",
                "pos_diversity",
                "source_example_count",
                "source_definition_count",
                "existing_scored_trigger_target_need_when_available",
            ],
            "forbidden_ranking_fields": list(FORBIDDEN_RANKING_FIELDS),
        },
        "summary": _summary(rows=rows, top_n=top_n),
        "e2e_checks": {
            "inventory_only_rows_have_no_llm_packet": all(
                not _as_mapping(row.get("llm_packet_from_scored_pairs"))
                for row in rows
                if row.get("readiness_stage") == "needs_translation_target_shadow_family"
            ),
            "scored_rows_link_to_priority_scan": all(
                int(row.get("matched_scored_pair_count") or 0) > 0
                for row in rows
                if row.get("readiness_stage") == "trigger_target_pair_scored"
            ),
            "forbidden_fields_absent_from_bridge_features": all(
                set(_as_mapping(row.get("programmatic_inventory_features"))).isdisjoint(
                    FORBIDDEN_RANKING_FIELDS
                )
                for row in rows
            ),
            "rows_sorted_by_stage_then_need": _is_sorted(rows),
        },
        "priority_rows": rows,
        "top_priority_rows": rows[: int(top_n)],
        "limitations": [
            "inventory_candidates_are_english_headwords_without_spanish_target_families",
            "source_frequency_rank_is_not_yet_joined_for_every_inventory_candidate",
            "inventory_source_need_ranks_family_construction_value_not_runtime_veto_quality",
            "scored_context_llm_packets_are_available_only_for_triggers_already_present_in_the_priority_scan",
        ],
        "next_steps": [
            "Construct Spanish target/shadow families for the top inventory-only rows before LLM evidence generation.",
            "Rerun the LLM data priority scan after those trigger/target pairs have scored contexts.",
            "Keep fallback policy explicit: non-enriched words continue through ordinary replacement or existing cheaper semantic evidence, not automatic abstain.",
        ],
    }
    return report


def render_llm_data_priority_inventory_bridge_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM Data Priority Inventory Bridge",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory candidates: `{summary.get('inventory_candidate_count', 0)}`",
        f"- Target-family missing: `{summary.get('needs_target_family_count', 0)}`",
        f"- Already scored trigger rows: `{summary.get('trigger_target_pair_scored_count', 0)}`",
        "",
        "## End-State Contract",
        "",
        str(_as_mapping(report.get("end_state_contract")).get("goal") or ""),
        "",
        "The top-N list decides who gets expensive enrichment first. It does not decide "
        "that every other word must abstain.",
        "",
        "## Stage Counts",
        "",
        "| Stage | Count |",
        "| --- | ---: |",
    ]
    for stage, count in _as_mapping(summary.get("readiness_stage_counts")).items():
        lines.append(f"| `{stage}` | {count} |")
    lines.extend(
        [
            "",
            "## Top Inventory Bridge Rows",
            "",
            "| Rank | Trigger | Stage | Need | Matched scored pairs | Next action | Scored packet |",
            "| ---: | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("top_priority_rows")):
        packet = _as_mapping(row.get("llm_packet_from_scored_pairs"))
        packet_text = "-"
        if packet:
            packet_text = (
                f"active {packet.get('active_rows', 0)}, shadow {packet.get('shadow_rows', 0)}, "
                f"phrase {packet.get('phrase_rows', 0)}, locked {packet.get('locked_eval_rows', 0)}"
            )
        lines.append(
            f"| {int(row.get('priority_rank') or 0)} | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"`{_escape_md(str(row.get('readiness_stage') or ''))}` | "
            f"{float(row.get('inventory_source_need') or 0.0):.4f} | "
            f"{int(row.get('matched_scored_pair_count') or 0)} | "
            f"`{_escape_md(str(row.get('recommended_next_action') or ''))}` | "
            f"{packet_text} |"
        )
    lines.extend(["", "## Fallback Tiers", ""])
    for tier in _as_mapping(report.get("end_state_contract")).get("fallback_tiers", []):
        lines.append(f"- `{_escape_md(str(tier))}`")
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", []))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", []))
    return "\n".join(lines) + "\n"


def _inventory_bridge_row(
    *,
    candidate: Mapping[str, object],
    scan_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    trigger = str(candidate.get("trigger") or "").strip().lower()
    features = _inventory_features(candidate)
    source_need = _inventory_source_need(features)
    best_scan_row = max(
        scan_rows,
        key=lambda row: _safe_float(row.get("scored_context_llm_data_need")),
        default={},
    )
    if best_scan_row:
        readiness_stage = "trigger_target_pair_scored"
        recommended_next_action = "use_scored_pair_llm_packet_or_refresh_contexts"
    else:
        readiness_stage = "needs_translation_target_shadow_family"
        recommended_next_action = "construct_translation_target_shadow_family"
    return {
        "trigger": trigger,
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "readiness_stage": readiness_stage,
        "inventory_source_need": source_need,
        "programmatic_inventory_features": features,
        "matched_scored_pair_count": len(scan_rows),
        "matched_scored_pairs": [
            {
                "target_lemma": str(row.get("target_lemma") or ""),
                "scored_context_llm_data_need": row.get("scored_context_llm_data_need"),
                "priority_rank": row.get("priority_rank"),
            }
            for row in scan_rows
        ],
        "llm_packet_from_scored_pairs": _as_mapping(best_scan_row.get("recommended_llm_packet")),
        "recommended_next_action": recommended_next_action,
        "fallback_tier_until_enriched": "ordinary_or_existing_semantic_replacement",
        "sample_synsets": list(candidate.get("sample_synsets") or [])[:3],
    }


def _inventory_features(candidate: Mapping[str, object]) -> dict[str, object]:
    pos_counts = _as_mapping(candidate.get("pos_counts"))
    sense_count = _safe_float(candidate.get("sense_count"))
    example_count = _safe_float(candidate.get("source_example_count"))
    definition_count = _safe_float(candidate.get("source_definition_count"))
    source_score = _safe_float(candidate.get("score"))
    features = {
        "inventory_score": _round4(min(1.0, source_score / 16.1)),
        "sense_risk": _round4(min(1.0, log1p(max(0.0, sense_count)) / log1p(40.0))),
        "pos_diversity": _round4(min(1.0, len(pos_counts) / 4.0)),
        "source_example_richness": _round4(min(1.0, example_count / 16.0)),
        "source_definition_richness": _round4(min(1.0, definition_count / 16.0)),
        "has_cross_pos": 1.0 if candidate.get("cross_pos") else 0.0,
        "has_noun_verb": 1.0 if candidate.get("noun_verb") else 0.0,
        "has_same_pos_polysemy": 1.0 if candidate.get("same_pos_polysemy") else 0.0,
    }
    forbidden = set(features).intersection(FORBIDDEN_RANKING_FIELDS)
    if forbidden:
        raise ValueError(f"Forbidden fields leaked into inventory features: {sorted(forbidden)}")
    return features


def _inventory_source_need(features: Mapping[str, object]) -> float:
    value = (
        0.28 * _safe_float(features.get("inventory_score"))
        + 0.24 * _safe_float(features.get("sense_risk"))
        + 0.16 * _safe_float(features.get("pos_diversity"))
        + 0.14 * _safe_float(features.get("source_example_richness"))
        + 0.08 * _safe_float(features.get("source_definition_richness"))
        + 0.06 * _safe_float(features.get("has_noun_verb"))
        + 0.04 * _safe_float(features.get("has_same_pos_polysemy"))
    )
    return _round4(min(1.0, max(0.0, value)))


def _priority_scan_rows_by_trigger(
    priority_scan_payload: Mapping[str, object],
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in _mapping_rows(priority_scan_payload.get("priority_rows")):
        trigger = str(row.get("trigger") or "").strip().lower()
        if trigger:
            grouped[trigger].append(row)
    return dict(grouped)


def _end_state_contract() -> dict[str, object]:
    return {
        "goal": (
            "Build a language-pair data-spend allocator that can identify the top-N "
            "trigger/target families most worth expensive LLM enrichment while leaving "
            "lower-priority words on cheaper evidence or ordinary replacement fallbacks."
        ),
        "priority_unit": "source_trigger_plus_target_replacement_family",
        "pipeline_stages": [
            "english_inventory_headword",
            "translation_target_shadow_family_constructed",
            "scored_context_probe_available",
            "llm_active_shadow_phrase_rows_generated_and_admitted",
            "locked_eval_validated_for_product_quality",
            "runtime_semantic_inventory_available_if_promoted",
        ],
        "fallback_tiers": [
            "llm_enriched_semantic_veto",
            "cheap_existing_semantic_veto_or_source_evidence",
            "ordinary_lexical_replacement_without_expensive_veto",
            "defer_or_review_only_when_rule_quality_or_user_policy_requires_it",
        ],
    }


def _summary(*, rows: Sequence[Mapping[str, object]], top_n: int) -> dict[str, object]:
    stage_counts = Counter(str(row.get("readiness_stage") or "") for row in rows)
    top_rows = list(rows[: int(top_n)])
    return {
        "inventory_candidate_count": len(rows),
        "top_n": int(top_n),
        "readiness_stage_counts": dict(sorted(stage_counts.items())),
        "needs_target_family_count": stage_counts.get("needs_translation_target_shadow_family", 0),
        "trigger_target_pair_scored_count": stage_counts.get("trigger_target_pair_scored", 0),
        "top_inventory_source_need": max(
            (_safe_float(row.get("inventory_source_need")) for row in rows), default=0.0
        ),
        "matched_scored_pair_count_top_n": sum(
            int(row.get("matched_scored_pair_count") or 0) for row in top_rows
        ),
        "target_family_construction_count_top_n": sum(
            1
            for row in top_rows
            if row.get("readiness_stage") == "needs_translation_target_shadow_family"
        ),
        "scored_context_packet_count_top_n": sum(
            1 for row in top_rows if row.get("readiness_stage") == "trigger_target_pair_scored"
        ),
    }


def _issues(rows: Sequence[Mapping[str, object]]) -> list[str]:
    issues = []
    if not rows:
        issues.append("no_inventory_candidates")
    if not _is_sorted(rows):
        issues.append("rows_not_sorted_by_stage_then_need")
    for row in rows:
        if row.get("readiness_stage") == "needs_translation_target_shadow_family" and _as_mapping(
            row.get("llm_packet_from_scored_pairs")
        ):
            issues.append("inventory_only_row_has_llm_packet")
            break
    return issues


def _stage_sort_weight(stage: str) -> int:
    if stage == "trigger_target_pair_scored":
        return 0
    if stage == "needs_translation_target_shadow_family":
        return 1
    return 2


def _is_sorted(rows: Sequence[Mapping[str, object]]) -> bool:
    observed = [
        (
            _stage_sort_weight(str(row.get("readiness_stage") or "")),
            -_safe_float(row.get("inventory_source_need")),
            str(row.get("trigger") or ""),
        )
        for row in rows
    ]
    return observed == sorted(observed)


def _round4(value: float | None) -> float:
    return round(float(value or 0.0), 4)


def write_report(
    report: Mapping[str, object],
    *,
    json_out: Path,
    markdown_out: Path,
) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_llm_data_priority_inventory_bridge_markdown(report), encoding="utf-8"
    )


def main() -> int:
    args = _parse_args()
    inventory_path = _resolve_repo_path(args.inventory_json)
    priority_scan_path = _resolve_repo_path(args.priority_scan_json)
    report = build_llm_data_priority_inventory_bridge_report(
        inventory_payload=_load_json(inventory_path),
        priority_scan_payload=_load_json(priority_scan_path),
        inventory_json_path=inventory_path,
        priority_scan_json_path=priority_scan_path,
        top_n=int(args.top_n),
    )
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    write_report(report, json_out=json_out, markdown_out=markdown_out)
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
