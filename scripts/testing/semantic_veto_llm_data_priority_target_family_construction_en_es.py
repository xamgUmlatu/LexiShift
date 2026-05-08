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
CORE_ROOT = PROJECT_ROOT / "core"
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_non_v10_wave_builder_en_es import (  # noqa: E402
    build_non_v10_wave_draft_report,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _repo_path,
    _resolve_repo_path,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_BRIDGE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_inventory_bridge_en_es_latest.json"
)
DEFAULT_INVENTORY_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_non_v10_inventory_candidates_wave7_source_class_breadth_v1_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_llm_data_priority_target_family_construction_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_target_family_construction_en_es_latest.md"
)
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_llm_data_priority"
DEFAULT_DATASET_OUT = DEFAULT_DRAFT_ROOT / "en_es_target_family_construction_queue_v1_dataset.json"
DEFAULT_QUEUE_OUT = DEFAULT_DRAFT_ROOT / "en_es_target_family_construction_queue_v1.json"
DEFAULT_QUEUE_ID = "semantic_veto_llm_data_priority_target_family_construction_en_es_v1"
DEFAULT_MAX_SENSE_COUNT = 40


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construct a stage-gated Spanish target/shadow family queue for the "
            "inventory-only rows surfaced by the semantic-veto LLM data priority bridge."
        )
    )
    parser.add_argument("--bridge-json", type=Path, default=DEFAULT_BRIDGE_JSON)
    parser.add_argument("--inventory-json", type=Path, default=DEFAULT_INVENTORY_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wiktionary-en-es-sqlite", type=Path, default=None)
    parser.add_argument("--wiktionary-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--freedict-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument("--construction-limit", type=int, default=0)
    parser.add_argument("--max-sense-count", type=int, default=DEFAULT_MAX_SENSE_COUNT)
    parser.add_argument("--queue-id", default=DEFAULT_QUEUE_ID)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--queue-out", type=Path, default=DEFAULT_QUEUE_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_target_family_construction_report(
    *,
    bridge_payload: Mapping[str, object],
    inventory_payload: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None = None,
    freedict_es_en_sqlite: Path | None = None,
    wordnet_index: WordNetIndex | None = None,
    bridge_json_path: Path | None = None,
    inventory_json_path: Path | None = None,
    construction_limit: int = 0,
    max_sense_count: int = DEFAULT_MAX_SENSE_COUNT,
    queue_id: str = DEFAULT_QUEUE_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    candidate_by_id, candidate_by_trigger = _candidate_indexes(inventory_payload)
    bridge_rows = _construction_bridge_rows(
        bridge_payload=bridge_payload,
        construction_limit=construction_limit,
    )
    attempts: list[dict[str, object]] = []
    source_ready_families: list[dict[str, object]] = []
    weak_families: list[dict[str, object]] = []
    for construction_rank, bridge_row in enumerate(bridge_rows, start=1):
        candidate = _candidate_for_bridge_row(
            bridge_row,
            candidate_by_id=candidate_by_id,
            candidate_by_trigger=candidate_by_trigger,
        )
        attempt = _attempt_target_family_construction(
            bridge_row=bridge_row,
            inventory_candidate=candidate,
            construction_rank=construction_rank,
            wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
            wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
            freedict_es_en_sqlite=freedict_es_en_sqlite,
            wordnet_index=wordnet_index,
            max_sense_count=max_sense_count,
            queue_id=queue_id,
            generated_at=generated_at,
        )
        attempts.append(attempt)
        family = _as_mapping(attempt.get("selected_family"))
        if not family:
            continue
        if attempt.get("source_ready_for_scored_probe"):
            source_ready_families.append(dict(family))
        else:
            weak_families.append(dict(family))
    draft_dataset = _draft_dataset(
        source_ready_families,
        inventory_payload=inventory_payload,
        queue_id=queue_id,
        generated_at=generated_at,
    )
    construction_queue = _construction_queue(
        attempts,
        dataset=draft_dataset,
        queue_id=queue_id,
        generated_at=generated_at,
    )
    checks = _checks(attempts=attempts, source_ready_families=source_ready_families)
    issues = [key for key, value in checks.items() if not value]
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(bridge_payload.get("pair") or inventory_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "target_family_construction_queue_established"
            if status == "ok"
            else "target_family_construction_queue_needs_review"
        ),
        "generated_at": generated_at,
        "queue_id": queue_id,
        "inputs": {
            "bridge_json": _repo_path(bridge_json_path),
            "inventory_json": _repo_path(inventory_json_path),
            "bridge_decision": str(bridge_payload.get("decision") or ""),
            "inventory_decision": str(inventory_payload.get("decision") or ""),
        },
        "methodology": {
            "goal": (
                "Move top inventory-only rows one stage forward by constructing Spanish "
                "target/shadow family drafts before any LLM active/shadow/phrase row spend."
            ),
            "attempt_scope": (
                "Rows from the bridge that are in the bridge top-N and still have "
                "readiness_stage=needs_translation_target_shadow_family."
            ),
            "strategy_order": [strategy["strategy_id"] for strategy in _strategy_specs()],
            "source_ready_definition": (
                "A row is source-ready for scored probe only when a strict supported "
                "strategy constructs a distinct visible active/shadow family. Diagnostic "
                "translation-only drafts are retained for review but excluded from the "
                "source-ready dataset."
            ),
            "llm_spend": "none",
        },
        "summary": _summary(attempts=attempts, source_ready_families=source_ready_families),
        "e2e_checks": checks,
        "construction_attempts": attempts,
        "source_ready_families": source_ready_families,
        "weak_diagnostic_families": weak_families,
        "draft_dataset": draft_dataset,
        "construction_queue": construction_queue,
        "limitations": [
            "constructed_families_are_drafts_and_need_review_before_locked_eval_claims",
            "source_ready_here_means_ready_for_scored_probe_not_runtime_promotion",
            "diagnostic_translation_only_families_are_not_scored_probe_inputs",
            "no_active_shadow_phrase_llm_rows_are_generated_by_this_harness",
        ],
        "next_steps": [
            "Review the source-ready target/shadow family drafts for visible-target and sense quality.",
            "Run scored context probes only for reviewed source-ready families.",
            "Return reviewed probe rows to the LLM data priority scan before spending on active/shadow/phrase examples.",
        ],
    }


def render_target_family_construction_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM Data Priority Target-Family Construction",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Attempts: `{summary.get('attempted_inventory_only_count', 0)}`",
        f"- Source-ready family drafts: `{summary.get('source_ready_family_count', 0)}`",
        f"- Weak diagnostic family drafts: `{summary.get('weak_diagnostic_family_count', 0)}`",
        f"- Blocked rows: `{summary.get('blocked_count', 0)}`",
        "",
        "## Goal",
        "",
        str(_as_mapping(report.get("methodology")).get("goal") or ""),
        "",
        "This report still does not generate active/shadow/phrase LLM rows. It only "
        "moves rows from English-only inventory toward reviewed en-es target families.",
        "",
        "## Stage Counts",
        "",
        "| Stage | Count |",
        "| --- | ---: |",
    ]
    for stage, count in _as_mapping(summary.get("readiness_stage_counts")).items():
        lines.append(f"| `{_escape_md(stage)}` | {count} |")
    lines.extend(
        [
            "",
            "## Construction Attempts",
            "",
            "| Rank | Trigger | Bridge rank | Stage | Strategy | Active | Shadows | Reason |",
            "| ---: | --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("construction_attempts")):
        active = _as_mapping(row.get("active"))
        shadows = [
            f"{shadow.get('target_lemma', '')} ({shadow.get('canonical_pos', '')})"
            for shadow in _mapping_rows(row.get("shadows"))
        ]
        lines.append(
            f"| {int(row.get('construction_rank') or 0)} | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"{int(row.get('bridge_priority_rank') or 0)} | "
            f"`{_escape_md(str(row.get('readiness_stage') or ''))}` | "
            f"`{_escape_md(str(row.get('selected_strategy') or '-'))}` | "
            f"`{_escape_md(_target_label(active))}` | "
            f"`{_escape_md(', '.join(shadows) or '-')}` | "
            f"`{_escape_md(str(row.get('reason') or ''))}` |"
        )
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _construction_bridge_rows(
    *, bridge_payload: Mapping[str, object], construction_limit: int
) -> list[Mapping[str, object]]:
    rows = [
        row
        for row in _mapping_rows(bridge_payload.get("priority_rows"))
        if row.get("readiness_stage") == "needs_translation_target_shadow_family"
        and bool(row.get("in_top_n"))
    ]
    rows.sort(key=lambda row: int(row.get("priority_rank") or 999999))
    if construction_limit > 0:
        return rows[: int(construction_limit)]
    return rows


def _candidate_indexes(
    inventory_payload: Mapping[str, object],
) -> tuple[dict[str, Mapping[str, object]], dict[str, Mapping[str, object]]]:
    by_id: dict[str, Mapping[str, object]] = {}
    by_trigger: dict[str, Mapping[str, object]] = {}
    for row in _mapping_rows(inventory_payload.get("candidates")):
        candidate_id = str(row.get("candidate_id") or "").strip()
        trigger = str(row.get("trigger") or "").strip().lower()
        if candidate_id:
            by_id[candidate_id] = row
        if trigger:
            by_trigger[trigger] = row
    return by_id, by_trigger


def _candidate_for_bridge_row(
    bridge_row: Mapping[str, object],
    *,
    candidate_by_id: Mapping[str, Mapping[str, object]],
    candidate_by_trigger: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object] | None:
    candidate_id = str(bridge_row.get("candidate_id") or "").strip()
    trigger = str(bridge_row.get("trigger") or "").strip().lower()
    return candidate_by_id.get(candidate_id) or candidate_by_trigger.get(trigger)


def _attempt_target_family_construction(
    *,
    bridge_row: Mapping[str, object],
    inventory_candidate: Mapping[str, object] | None,
    construction_rank: int,
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None,
    freedict_es_en_sqlite: Path | None,
    wordnet_index: WordNetIndex | None,
    max_sense_count: int,
    queue_id: str,
    generated_at: str,
) -> dict[str, object]:
    trigger = str(bridge_row.get("trigger") or "").strip().lower()
    base = {
        "construction_rank": construction_rank,
        "bridge_priority_rank": int(bridge_row.get("priority_rank") or 0),
        "trigger": trigger,
        "candidate_id": str(bridge_row.get("candidate_id") or ""),
        "bridge_inventory_source_need": float(bridge_row.get("inventory_source_need") or 0.0),
        "source_ready_for_scored_probe": False,
        "selected_family": {},
        "active": {},
        "shadows": [],
        "probe_results": [],
    }
    if inventory_candidate is None:
        return {
            **base,
            "readiness_stage": "construction_blocked",
            "selected_strategy": "",
            "reason": "inventory_candidate_missing",
        }
    probe_results = []
    selected_probe: Mapping[str, object] | None = None
    for strategy in _strategy_specs():
        probe = _run_strategy_probe(
            strategy=strategy,
            inventory_candidate=inventory_candidate,
            wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
            wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
            freedict_es_en_sqlite=freedict_es_en_sqlite,
            wordnet_index=wordnet_index,
            max_sense_count=max_sense_count,
            queue_id=queue_id,
            generated_at=generated_at,
        )
        probe_results.append(probe)
        if selected_probe is None and probe.get("selected_family"):
            selected_probe = probe
    if selected_probe is None:
        reason = _first_probe_reason(probe_results) or "no_strategy_constructed_family"
        return {
            **base,
            "readiness_stage": "construction_blocked",
            "selected_strategy": "",
            "reason": reason,
            "probe_results": probe_results,
        }
    selected_family = dict(_as_mapping(selected_probe.get("selected_family")))
    selected_strategy = str(selected_probe.get("strategy_id") or "")
    source_ready = bool(selected_probe.get("source_ready_for_scored_probe"))
    readiness_stage = (
        "source_supported_family_draft_needs_review"
        if source_ready
        else "weak_family_draft_needs_source_support"
    )
    family_metadata = dict(_as_mapping(selected_family.get("metadata")))
    family_metadata["llm_data_priority_target_family_construction"] = {
        "construction_rank": construction_rank,
        "bridge_priority_rank": int(bridge_row.get("priority_rank") or 0),
        "selected_strategy": selected_strategy,
        "readiness_stage": readiness_stage,
        "source_ready_for_scored_probe": source_ready,
    }
    selected_family["metadata"] = family_metadata
    return {
        **base,
        "readiness_stage": readiness_stage,
        "selected_strategy": selected_strategy,
        "reason": str(selected_probe.get("reason") or ""),
        "source_ready_for_scored_probe": source_ready,
        "selected_family": selected_family,
        "active": dict(_as_mapping(selected_family.get("active"))),
        "shadows": [
            dict(shadow)
            for shadow in _mapping_rows(selected_family.get("shadows"))
            if isinstance(shadow, Mapping)
        ],
        "probe_results": probe_results,
    }


def _strategy_specs() -> list[dict[str, object]]:
    return [
        {
            "strategy_id": "noun_verb_supported_source_linked",
            "family_pos_strategy": "noun_verb",
            "require_translation_support": True,
            "use_wordnet_index": True,
            "source_ready_for_scored_probe": True,
        },
        {
            "strategy_id": "any_cross_pos_supported_source_linked",
            "family_pos_strategy": "any_cross_pos",
            "require_translation_support": True,
            "use_wordnet_index": True,
            "source_ready_for_scored_probe": True,
        },
        {
            "strategy_id": "any_cross_pos_wordnet_forward_only",
            "family_pos_strategy": "any_cross_pos",
            "require_translation_support": False,
            "use_wordnet_index": True,
            "source_ready_for_scored_probe": False,
        },
        {
            "strategy_id": "any_cross_pos_translation_only_diagnostic",
            "family_pos_strategy": "any_cross_pos",
            "require_translation_support": False,
            "use_wordnet_index": False,
            "source_ready_for_scored_probe": False,
        },
    ]


def _run_strategy_probe(
    *,
    strategy: Mapping[str, object],
    inventory_candidate: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None,
    freedict_es_en_sqlite: Path | None,
    wordnet_index: WordNetIndex | None,
    max_sense_count: int,
    queue_id: str,
    generated_at: str,
) -> dict[str, object]:
    strategy_id = str(strategy.get("strategy_id") or "")
    probe_wordnet_index = wordnet_index if strategy.get("use_wordnet_index") else None
    report = build_non_v10_wave_draft_report(
        candidate_payload={
            "schema_version": 1,
            "inventory_id": "semantic_veto_llm_data_priority_inventory_bridge",
            "candidates": [dict(inventory_candidate)],
        },
        wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
        wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
        freedict_es_en_sqlite=freedict_es_en_sqlite,
        wordnet_index=probe_wordnet_index,
        wave_id=queue_id,
        wave_size=1,
        max_sense_count=max_sense_count,
        require_translation_support=bool(strategy.get("require_translation_support")),
        family_pos_strategy=str(strategy.get("family_pos_strategy") or "noun_verb"),
        generated_at=generated_at,
    )
    selected = [
        row for row in _mapping_rows(report.get("selected_families")) if isinstance(row, Mapping)
    ]
    reason = "constructed_family" if selected else _skip_reason(report)
    return {
        "strategy_id": strategy_id,
        "constructed": bool(selected),
        "decision": str(report.get("decision") or ""),
        "reason": reason,
        "source_ready_for_scored_probe": (
            bool(selected) and bool(strategy.get("source_ready_for_scored_probe"))
        ),
        "family_pos_strategy": str(strategy.get("family_pos_strategy") or ""),
        "require_translation_support": bool(strategy.get("require_translation_support")),
        "use_wordnet_index": bool(strategy.get("use_wordnet_index")),
        "selected_family": dict(selected[0]) if selected else {},
    }


def _skip_reason(report: Mapping[str, object]) -> str:
    for row in _mapping_rows(report.get("skipped_candidates")):
        reason = str(row.get("reason") or "").strip()
        if reason:
            return reason
    return str(_as_mapping(report.get("readiness")).get("reason") or "")


def _first_probe_reason(probe_results: Sequence[Mapping[str, object]]) -> str:
    for probe in probe_results:
        reason = str(probe.get("reason") or "").strip()
        if reason:
            return reason
    return ""


def _summary(
    *,
    attempts: Sequence[Mapping[str, object]],
    source_ready_families: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    stage_counts = Counter(str(row.get("readiness_stage") or "") for row in attempts)
    strategy_counts = Counter(
        str(row.get("selected_strategy") or "none")
        for row in attempts
        if row.get("selected_strategy")
    )
    return {
        "attempted_inventory_only_count": len(attempts),
        "source_ready_family_count": len(source_ready_families),
        "weak_diagnostic_family_count": stage_counts.get(
            "weak_family_draft_needs_source_support", 0
        ),
        "blocked_count": stage_counts.get("construction_blocked", 0),
        "readiness_stage_counts": dict(sorted(stage_counts.items())),
        "selected_strategy_counts": dict(sorted(strategy_counts.items())),
        "top_bridge_priority_rank": min(
            (int(row.get("bridge_priority_rank") or 0) for row in attempts), default=0
        ),
        "last_bridge_priority_rank": max(
            (int(row.get("bridge_priority_rank") or 0) for row in attempts), default=0
        ),
    }


def _draft_dataset(
    families: Sequence[Mapping[str, object]],
    *,
    inventory_payload: Mapping[str, object],
    queue_id: str,
    generated_at: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": f"en_es_{queue_id}",
        "generated_at": generated_at,
        "description": (
            "Source-ready draft target/shadow families constructed from the LLM "
            "data-priority inventory bridge. These require review before scored "
            "context probes and are not active/shadow/phrase LLM rows."
        ),
        "source_candidate_inventory_id": str(inventory_payload.get("inventory_id") or ""),
        "review_state": "draft_target_shadow_families_need_review",
        "families": [
            {
                "family_id": str(family.get("family_id") or ""),
                "trigger": str(family.get("trigger") or ""),
                "active": dict(_as_mapping(family.get("active"))),
                "shadows": [dict(shadow) for shadow in _mapping_rows(family.get("shadows"))],
                "cases": [dict(case) for case in _mapping_rows(family.get("cases"))],
                "metadata": dict(_as_mapping(family.get("metadata"))),
            }
            for family in families
        ],
    }


def _construction_queue(
    attempts: Sequence[Mapping[str, object]],
    *,
    dataset: Mapping[str, object],
    queue_id: str,
    generated_at: str,
) -> dict[str, object]:
    rows = []
    for row in attempts:
        rows.append(
            {
                "construction_rank": int(row.get("construction_rank") or 0),
                "bridge_priority_rank": int(row.get("bridge_priority_rank") or 0),
                "trigger": str(row.get("trigger") or ""),
                "family_id": str(_as_mapping(row.get("selected_family")).get("family_id") or ""),
                "readiness_stage": str(row.get("readiness_stage") or ""),
                "selected_strategy": str(row.get("selected_strategy") or ""),
                "source_ready_for_scored_probe": bool(row.get("source_ready_for_scored_probe")),
                "review_state": (
                    "draft_target_shadow_family_needs_review"
                    if row.get("selected_family")
                    else "construction_blocked"
                ),
                "next_action": _queue_next_action(row),
            }
        )
    return {
        "schema_version": 1,
        "queue_id": queue_id,
        "pair": "en-es",
        "generated_at": generated_at,
        "dataset_id": str(dataset.get("dataset_id") or ""),
        "rows": rows,
    }


def _queue_next_action(row: Mapping[str, object]) -> str:
    stage = str(row.get("readiness_stage") or "")
    if stage == "source_supported_family_draft_needs_review":
        return "review_family_then_score_probe_contexts"
    if stage == "weak_family_draft_needs_source_support":
        return "add_reverse_or_source_support_before_scored_probe"
    return "inspect_translation_gap_or_skip_for_now"


def _checks(
    *,
    attempts: Sequence[Mapping[str, object]],
    source_ready_families: Sequence[Mapping[str, object]],
) -> dict[str, bool]:
    return {
        "attempts_are_bridge_inventory_only_rows": all(
            int(row.get("bridge_priority_rank") or 0) > 0 for row in attempts
        ),
        "no_llm_packets_emitted": all("recommended_llm_packet" not in row for row in attempts),
        "source_ready_rows_have_source_supported_strategy": all(
            str(row.get("selected_strategy") or "").endswith("source_linked")
            for row in attempts
            if row.get("source_ready_for_scored_probe")
        ),
        "weak_rows_not_marked_source_ready": all(
            not row.get("source_ready_for_scored_probe")
            for row in attempts
            if row.get("readiness_stage") == "weak_family_draft_needs_source_support"
        ),
        "selected_families_have_distinct_visible_targets": all(
            _family_has_distinct_visible_targets(family) for family in source_ready_families
        ),
    }


def _family_has_distinct_visible_targets(family: Mapping[str, object]) -> bool:
    active_target = str(_as_mapping(family.get("active")).get("target_lemma") or "").lower()
    shadow_targets = [
        str(shadow.get("target_lemma") or "").lower()
        for shadow in _mapping_rows(family.get("shadows"))
    ]
    return bool(active_target) and all(
        target and target != active_target for target in shadow_targets
    )


def _target_label(row: Mapping[str, object]) -> str:
    if not row:
        return "-"
    return f"{row.get('target_lemma', '')} ({row.get('canonical_pos', '')})"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(
    report: Mapping[str, object],
    *,
    json_out: Path,
    markdown_out: Path,
    dataset_out: Path,
    queue_out: Path,
) -> None:
    _write_json(json_out, report)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_target_family_construction_markdown(report), encoding="utf-8")
    _write_json(dataset_out, _as_mapping(report.get("draft_dataset")))
    _write_json(queue_out, _as_mapping(report.get("construction_queue")))


def main() -> int:
    args = _parse_args()
    data_root = _resolve_repo_path(args.data_root)
    wiktionary_en_es = args.wiktionary_en_es_sqlite or (
        data_root / "language_packs" / "wiktionary-en-es.sqlite"
    )
    wiktionary_es_en = args.wiktionary_es_en_sqlite or (
        data_root / "language_packs" / "wiktionary-es-en.sqlite"
    )
    freedict_es_en = args.freedict_es_en_sqlite or (
        data_root / "language_packs" / "freedict-es-en" / "main.sqlite"
    )
    wordnet_dir = args.wordnet_dir or (data_root / "language_packs" / "english-wordnet-2025-json")
    wordnet_index = WordNetIndex.load(wordnet_dir) if wordnet_dir.exists() else None
    bridge_path = _resolve_repo_path(args.bridge_json)
    inventory_path = _resolve_repo_path(args.inventory_json)
    report = build_target_family_construction_report(
        bridge_payload=_load_json(bridge_path),
        inventory_payload=_load_json(inventory_path),
        wiktionary_en_es_sqlite=wiktionary_en_es,
        wiktionary_es_en_sqlite=wiktionary_es_en if wiktionary_es_en.exists() else None,
        freedict_es_en_sqlite=freedict_es_en if freedict_es_en.exists() else None,
        wordnet_index=wordnet_index,
        bridge_json_path=bridge_path,
        inventory_json_path=inventory_path,
        construction_limit=int(args.construction_limit),
        max_sense_count=int(args.max_sense_count),
        queue_id=str(args.queue_id),
    )
    write_report(
        report,
        json_out=_resolve_repo_path(args.json_out),
        markdown_out=_resolve_repo_path(args.markdown_out),
        dataset_out=_resolve_repo_path(args.dataset_out),
        queue_out=_resolve_repo_path(args.queue_out),
    )
    print(f"Wrote JSON artifact to {_resolve_repo_path(args.json_out)}")
    print(f"Wrote Markdown artifact to {_resolve_repo_path(args.markdown_out)}")
    print(f"Wrote dataset artifact to {_resolve_repo_path(args.dataset_out)}")
    print(f"Wrote queue artifact to {_resolve_repo_path(args.queue_out)}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
