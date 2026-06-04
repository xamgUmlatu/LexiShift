#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
from semantic_veto_llm_data_priority_target_family_construction_en_es import (  # noqa: E402
    _attempt_target_family_construction,
    _family_has_distinct_visible_targets,
    _target_label,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _repo_path,
    _resolve_repo_path,
)
from semantic_veto_representative_heuristic_band_sampler_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_SAMPLE_JSON,
    FORBIDDEN_SELECTION_FIELDS,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_target_family_construction_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_target_family_construction_en_es_latest.md"
)
DEFAULT_DRAFT_ROOT = (
    TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_representative_target_family"
)
DEFAULT_DATASET_OUT = DEFAULT_DRAFT_ROOT / "en_es_representative_target_family_v1_dataset.json"
DEFAULT_QUEUE_OUT = DEFAULT_DRAFT_ROOT / "en_es_representative_target_family_v1_queue.json"
DEFAULT_QUEUE_ID = "semantic_veto_representative_target_family_construction_en_es_v1"
DEFAULT_MAX_SENSE_COUNT = 40


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construct draft Spanish target/shadow families over the frozen "
            "representative heuristic-band source-trigger sample."
        )
    )
    parser.add_argument("--sample-json", type=Path, default=DEFAULT_SAMPLE_JSON)
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


def build_representative_target_family_construction_report(
    *,
    sample_payload: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None = None,
    freedict_es_en_sqlite: Path | None = None,
    wordnet_index: WordNetIndex | None = None,
    sample_json_path: Path | None = None,
    construction_limit: int = 0,
    max_sense_count: int = DEFAULT_MAX_SENSE_COUNT,
    queue_id: str = DEFAULT_QUEUE_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    sample_rows = _sample_rows(sample_payload, construction_limit=construction_limit)
    attempts: list[dict[str, object]] = []
    source_ready_families: list[dict[str, object]] = []
    weak_families: list[dict[str, object]] = []
    for construction_rank, sample_row in enumerate(sample_rows, start=1):
        bridge_row = _bridge_row_from_sample(sample_row, construction_rank=construction_rank)
        candidate = _candidate_from_sample(sample_row, construction_rank=construction_rank)
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
        attempt = _attach_sample_metadata(attempt, sample_row=sample_row)
        attempts.append(attempt)
        family = _as_mapping(attempt.get("selected_family"))
        if not family:
            continue
        if attempt.get("source_ready_for_scored_probe"):
            source_ready_families.append(dict(family))
        else:
            weak_families.append(dict(family))
    dataset = _draft_dataset(
        source_ready_families,
        sample_payload=sample_payload,
        queue_id=queue_id,
        generated_at=generated_at,
    )
    queue = _construction_queue(
        attempts,
        dataset=dataset,
        queue_id=queue_id,
        generated_at=generated_at,
    )
    checks = _checks(
        attempts=attempts, sample_rows=sample_rows, source_ready_families=source_ready_families
    )
    issues = [key for key, value in checks.items() if not value]
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(sample_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "representative_target_family_construction_queue_established"
            if status == "ok"
            else "representative_target_family_construction_queue_needs_review"
        ),
        "generated_at": generated_at,
        "queue_id": queue_id,
        "inputs": {
            "sample_json": _repo_path(sample_json_path),
            "sample_decision": str(sample_payload.get("decision") or ""),
            "sample_status": str(sample_payload.get("status") or ""),
        },
        "methodology": {
            "goal": (
                "Advance the frozen representative heuristic-band source-trigger sample "
                "toward en-es evaluation by constructing draft Spanish target/shadow "
                "families without changing the sampled trigger set."
            ),
            "attempt_scope": (
                "Rows from sampled_rows in the representative heuristic-band sampler; "
                "no replacement, resorting by outcome, or interesting-word backfill."
            ),
            "source_ready_definition": (
                "A row is source-ready for scored probe only when the shared target-family "
                "builder constructs a distinct visible active/shadow family using a "
                "source-supported strategy."
            ),
            "llm_spend": "none",
        },
        "summary": _summary(
            sample_payload=sample_payload,
            attempts=attempts,
            sample_rows=sample_rows,
            source_ready_families=source_ready_families,
        ),
        "e2e_checks": checks,
        "construction_attempts": attempts,
        "source_ready_families": source_ready_families,
        "weak_diagnostic_families": weak_families,
        "draft_dataset": dataset,
        "construction_queue": queue,
        "limitations": [
            "target_families_are_drafts_and_need_review_before_scored_probe_claims",
            "source_ready_here_means_ready_for_probe_not_runtime_promotion",
            "english_trigger_sampling_is_representative_within_cells_not_browser_token_weighted",
            "blocked_rows_remain_part_of_the_representative_result_and_must_not_be_replaced",
            "no_active_shadow_phrase_llm_rows_are_generated_by_this_harness",
        ],
        "next_steps": [
            "Review source-ready family drafts for visible-target and sense quality.",
            "Score fixed probe contexts for reviewed source-ready families.",
            "Keep blocked and weak rows in denominator when estimating source-coverage difficulty by cell.",
            "Use the blocked-cell map to decide whether to improve source packs or spend LLM budget.",
        ],
    }


def render_representative_target_family_construction_markdown(
    report: Mapping[str, object],
) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Representative Target-Family Construction",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Attempted sampled triggers: `{summary.get('attempted_sample_count', 0)}`",
        f"- Source-ready family drafts: `{summary.get('source_ready_family_count', 0)}`",
        f"- Weak diagnostic family drafts: `{summary.get('weak_diagnostic_family_count', 0)}`",
        f"- Blocked rows: `{summary.get('blocked_count', 0)}`",
        "",
        "## Goal",
        "",
        str(_as_mapping(report.get("methodology")).get("goal") or ""),
        "",
        "This report does not generate LLM rows and does not change runtime policy. "
        "Blocked rows remain part of the representative result instead of being replaced.",
        "",
        "## Stage Counts",
        "",
        "| Stage | Count |",
        "| --- | ---: |",
    ]
    for stage, count in _as_mapping(summary.get("readiness_stage_counts")).items():
        lines.append(f"| `{_escape_md(stage)}` | {count} |")
    lines.extend(["", "## Strategy Counts", "", "| Strategy | Count |", "| --- | ---: |"])
    for strategy, count in _as_mapping(summary.get("selected_strategy_counts")).items():
        lines.append(f"| `{_escape_md(strategy)}` | {count} |")
    lines.extend(["", "## Reason Counts", "", "| Reason | Count |", "| --- | ---: |"])
    for reason, count in _as_mapping(summary.get("reason_counts")).items():
        lines.append(f"| `{_escape_md(reason)}` | {count} |")
    lines.extend(["", "## Cell Coverage", "", _cell_table(summary.get("cell_counts")), ""])
    lines.extend(
        [
            "## Construction Attempts",
            "",
            "| Rank | Trigger | Cell | Stage | Strategy | Active | Shadows | Reason |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("construction_attempts"))[:80]:
        active = _as_mapping(row.get("active"))
        shadows = [
            f"{shadow.get('target_lemma', '')} ({shadow.get('canonical_pos', '')})"
            for shadow in _mapping_rows(row.get("shadows"))
        ]
        lines.append(
            f"| {int(row.get('construction_rank') or 0)} | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"`{_escape_md(str(row.get('cell_id') or ''))}` | "
            f"`{_escape_md(str(row.get('readiness_stage') or ''))}` | "
            f"`{_escape_md(str(row.get('selected_strategy') or '-'))}` | "
            f"`{_escape_md(_target_label(active))}` | "
            f"`{_escape_md(', '.join(shadows) or '-')}` | "
            f"`{_escape_md(str(row.get('reason') or ''))}` |"
        )
    if len(_mapping_rows(report.get("construction_attempts"))) > 80:
        lines.append("| ... | ... | ... | ... | ... | ... | ... | ... |")
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _sample_rows(
    sample_payload: Mapping[str, object], *, construction_limit: int
) -> list[Mapping[str, object]]:
    rows = [
        row
        for row in _mapping_rows(sample_payload.get("sampled_rows"))
        if str(row.get("trigger") or "").strip()
    ]
    if construction_limit > 0:
        return rows[: int(construction_limit)]
    return rows


def _bridge_row_from_sample(
    sample_row: Mapping[str, object], *, construction_rank: int
) -> dict[str, object]:
    return {
        "trigger": str(sample_row.get("trigger") or "").strip().lower(),
        "candidate_id": _candidate_id(sample_row, construction_rank=construction_rank),
        "priority_rank": construction_rank,
        "inventory_source_need": 0.0,
    }


def _candidate_from_sample(
    sample_row: Mapping[str, object], *, construction_rank: int
) -> dict[str, object]:
    return {
        "candidate_id": _candidate_id(sample_row, construction_rank=construction_rank),
        "trigger": str(sample_row.get("trigger") or "").strip().lower(),
        "score": float(sample_row.get("cell_sampling_weight") or 0.0),
        "complexity_band": str(sample_row.get("cell_id") or ""),
        "sense_count": int(sample_row.get("wordnet_sense_count") or 0),
        "source_rank": sample_row.get("source_rank"),
        "source_rank_band": str(sample_row.get("source_rank_band") or ""),
        "polysemy_band": str(sample_row.get("polysemy_band") or ""),
        "pos_shape": str(sample_row.get("pos_shape") or ""),
    }


def _candidate_id(sample_row: Mapping[str, object], *, construction_rank: int) -> str:
    trigger = str(sample_row.get("trigger") or "").strip().lower().replace(" ", "_")
    return f"representative-heuristic-band:{construction_rank}:{trigger}"


def _attach_sample_metadata(
    attempt: Mapping[str, object], *, sample_row: Mapping[str, object]
) -> dict[str, object]:
    result = dict(attempt)
    sample_metadata = _sample_metadata(sample_row)
    result.update(sample_metadata)
    family = dict(_as_mapping(result.get("selected_family")))
    if family:
        metadata = dict(_as_mapping(family.get("metadata")))
        metadata["representative_heuristic_band_sample"] = sample_metadata
        family["metadata"] = metadata
        result["selected_family"] = family
    return result


def _sample_metadata(sample_row: Mapping[str, object]) -> dict[str, object]:
    return {
        "representative_sample_rank": int(sample_row.get("sample_rank_in_cell") or 0),
        "cell_id": str(sample_row.get("cell_id") or ""),
        "cell_eligible_count": int(sample_row.get("cell_eligible_count") or 0),
        "cell_sample_count": int(sample_row.get("cell_sample_count") or 0),
        "cell_sampling_weight": sample_row.get("cell_sampling_weight"),
        "source_rank": sample_row.get("source_rank"),
        "source_rank_band": str(sample_row.get("source_rank_band") or ""),
        "polysemy_band": str(sample_row.get("polysemy_band") or ""),
        "pos_shape": str(sample_row.get("pos_shape") or ""),
        "wordnet_sense_count": int(sample_row.get("wordnet_sense_count") or 0),
        "wordnet_pos_count": int(sample_row.get("wordnet_pos_count") or 0),
    }


def _summary(
    *,
    sample_payload: Mapping[str, object],
    attempts: Sequence[Mapping[str, object]],
    sample_rows: Sequence[Mapping[str, object]],
    source_ready_families: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    stage_counts = Counter(str(row.get("readiness_stage") or "") for row in attempts)
    strategy_counts = Counter(
        str(row.get("selected_strategy") or "none")
        for row in attempts
        if row.get("selected_strategy")
    )
    reason_counts = Counter(str(row.get("reason") or "") for row in attempts)
    cell_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in attempts:
        cell_id = str(row.get("cell_id") or "")
        stage = str(row.get("readiness_stage") or "")
        if cell_id and stage:
            cell_counts[cell_id][stage] += 1
    return {
        "sample_decision": str(sample_payload.get("decision") or ""),
        "sampled_trigger_count": len(_mapping_rows(sample_payload.get("sampled_rows"))),
        "attempted_sample_count": len(attempts),
        "source_ready_family_count": len(source_ready_families),
        "weak_diagnostic_family_count": stage_counts.get(
            "weak_family_draft_needs_source_support", 0
        ),
        "blocked_count": stage_counts.get("construction_blocked", 0),
        "readiness_stage_counts": dict(sorted(stage_counts.items())),
        "selected_strategy_counts": dict(sorted(strategy_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "source_ready_rate": _ratio(len(source_ready_families), len(attempts)),
        "attempted_all_loaded_sample_rows": len(attempts) == len(sample_rows),
        "cell_counts": {
            cell_id: dict(sorted(counts.items())) for cell_id, counts in sorted(cell_counts.items())
        },
    }


def _draft_dataset(
    families: Sequence[Mapping[str, object]],
    *,
    sample_payload: Mapping[str, object],
    queue_id: str,
    generated_at: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": f"en_es_{queue_id}",
        "generated_at": generated_at,
        "description": (
            "Source-ready draft target/shadow families constructed over the frozen "
            "representative heuristic-band source-trigger sample. Families require "
            "review before scored probes and are not LLM active/shadow/phrase rows."
        ),
        "source_sample_decision": str(sample_payload.get("decision") or ""),
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
    return {
        "schema_version": 1,
        "queue_id": queue_id,
        "pair": "en-es",
        "generated_at": generated_at,
        "dataset_id": str(dataset.get("dataset_id") or ""),
        "rows": [
            {
                "construction_rank": int(row.get("construction_rank") or 0),
                "trigger": str(row.get("trigger") or ""),
                "cell_id": str(row.get("cell_id") or ""),
                "family_id": str(_as_mapping(row.get("selected_family")).get("family_id") or ""),
                "readiness_stage": str(row.get("readiness_stage") or ""),
                "selected_strategy": str(row.get("selected_strategy") or ""),
                "source_ready_for_scored_probe": bool(row.get("source_ready_for_scored_probe")),
                "cell_sampling_weight": row.get("cell_sampling_weight"),
                "review_state": (
                    "draft_target_shadow_family_needs_review"
                    if row.get("selected_family")
                    else "construction_blocked"
                ),
                "next_action": _queue_next_action(row),
            }
            for row in attempts
        ],
    }


def _queue_next_action(row: Mapping[str, object]) -> str:
    stage = str(row.get("readiness_stage") or "")
    if stage == "source_supported_family_draft_needs_review":
        return "review_family_then_score_probe_contexts"
    if stage == "weak_family_draft_needs_source_support":
        return "add_reverse_or_source_support_before_scored_probe"
    return "preserve_blocked_row_in_coverage_denominator"


def _checks(
    *,
    attempts: Sequence[Mapping[str, object]],
    sample_rows: Sequence[Mapping[str, object]],
    source_ready_families: Sequence[Mapping[str, object]],
) -> dict[str, bool]:
    attempted_triggers = [str(row.get("trigger") or "") for row in attempts]
    sampled_triggers = [
        str(row.get("trigger") or "").strip().lower()
        for row in sample_rows
        if str(row.get("trigger") or "").strip()
    ]
    forbidden_keys = [
        key for row in sample_rows for key in row if key in FORBIDDEN_SELECTION_FIELDS
    ]
    return {
        "attempts_match_loaded_sample_rows": attempted_triggers == sampled_triggers,
        "all_attempts_have_cell_ids": all(row.get("cell_id") for row in attempts),
        "sample_rows_have_no_outcome_fields": not forbidden_keys,
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
        "source_ready_families_have_distinct_visible_targets": all(
            _family_has_distinct_visible_targets(family) for family in source_ready_families
        ),
    }


def _cell_table(value: object, *, limit: int = 40) -> str:
    rows = []
    for cell_id, counts in _as_mapping(value).items():
        row = {"cell_id": cell_id, **_as_mapping(counts)}
        rows.append(row)
    if not rows:
        return "_No cell counts._"
    lines = [
        "| Cell | Source-ready | Weak | Blocked |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('cell_id') or ''))}`",
                    str(int(row.get("source_supported_family_draft_needs_review") or 0)),
                    str(int(row.get("weak_family_draft_needs_source_support") or 0)),
                    str(int(row.get("construction_blocked") or 0)),
                ]
            )
            + " |"
        )
    if len(rows) > limit:
        lines.append("| ... | ... | ... | ... |")
    return "\n".join(lines)


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


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
    markdown_out.write_text(
        render_representative_target_family_construction_markdown(report),
        encoding="utf-8",
    )
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
    sample_path = _resolve_repo_path(args.sample_json)
    report = build_representative_target_family_construction_report(
        sample_payload=_load_json(sample_path),
        wiktionary_en_es_sqlite=wiktionary_en_es,
        wiktionary_es_en_sqlite=wiktionary_es_en if wiktionary_es_en.exists() else None,
        freedict_es_en_sqlite=freedict_es_en if freedict_es_en.exists() else None,
        wordnet_index=wordnet_index,
        sample_json_path=sample_path,
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
