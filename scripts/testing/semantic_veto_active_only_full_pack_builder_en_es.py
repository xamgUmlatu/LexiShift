#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_source_packaging"

DEFAULT_BASE_INVENTORY = (
    EXPERIMENT_ROOT
    / "en-es-active-only-combined-product-scope-v1-inventory-replay-latest_semantic_inventory.json"
)
DEFAULT_BASE_NORMALIZED_EVIDENCE = (
    EXPERIMENT_ROOT / "en-es-active-only-combined-product-scope-v1-normalized_evidence.json"
)
DEFAULT_ADD_NORMALIZED_EVIDENCE = (
    EXPERIMENT_ROOT / "en-es-active-only-full-v1-tranche-001_normalized_evidence.json"
)
DEFAULT_PACK_ID = "en-es-active-only-combined-full-v1-tranche-001"
DEFAULT_COMBINED_NORMALIZED_OUT = EXPERIMENT_ROOT / f"{DEFAULT_PACK_ID}-normalized_evidence.json"
DEFAULT_SEMANTIC_INVENTORY_OUT = EXPERIMENT_ROOT / f"{DEFAULT_PACK_ID}_semantic_inventory.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / f"semantic_veto_{DEFAULT_PACK_ID}_pack_builder_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / f"semantic_veto_{DEFAULT_PACK_ID}_pack_builder_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a product-shaped active-only semantic inventory pack by merging "
            "new normalized anchor-cue evidence into an existing en-es semantic inventory."
        )
    )
    parser.add_argument("--base-inventory", type=Path, default=DEFAULT_BASE_INVENTORY)
    parser.add_argument(
        "--base-normalized-evidence",
        type=Path,
        default=DEFAULT_BASE_NORMALIZED_EVIDENCE,
    )
    parser.add_argument(
        "--add-normalized-evidence",
        type=Path,
        action="append",
        default=[],
        help="Additional normalized active-only evidence batch. May be repeated.",
    )
    parser.add_argument("--pack-id", default=DEFAULT_PACK_ID)
    parser.add_argument(
        "--combined-normalized-out", type=Path, default=DEFAULT_COMBINED_NORMALIZED_OUT
    )
    parser.add_argument(
        "--semantic-inventory-out", type=Path, default=DEFAULT_SEMANTIC_INVENTORY_OUT
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    add_paths = args.add_normalized_evidence or [DEFAULT_ADD_NORMALIZED_EVIDENCE]
    report = build_active_only_full_pack_report(
        base_inventory_payload=_load_json(args.base_inventory),
        base_normalized_payload=_load_json(args.base_normalized_evidence),
        add_normalized_payloads=[_load_json(path) for path in add_paths],
        base_inventory_path=args.base_inventory,
        base_normalized_path=args.base_normalized_evidence,
        add_normalized_paths=add_paths,
        pack_id=str(args.pack_id),
    )
    _write_json(args.combined_normalized_out, _as_mapping(report.get("combined_normalized_batch")))
    _write_json(args.semantic_inventory_out, _as_mapping(report.get("semantic_inventory")))
    output_report = dict(report)
    output_report.pop("combined_normalized_batch", None)
    output_report.pop("semantic_inventory", None)
    output_report["artifacts"] = {
        "combined_normalized_evidence": _repo_path(args.combined_normalized_out),
        "semantic_inventory": _repo_path(args.semantic_inventory_out),
    }
    _write_json(args.json_out, output_report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_active_only_full_pack_markdown(output_report), encoding="utf-8"
    )
    print(f"Wrote combined normalized evidence to {args.combined_normalized_out}")
    print(f"Wrote semantic inventory to {args.semantic_inventory_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and output_report["status"] != "ok":
        return 1
    return 0


def build_active_only_full_pack_report(
    *,
    base_inventory_payload: Mapping[str, object],
    base_normalized_payload: Mapping[str, object],
    add_normalized_payloads: Sequence[Mapping[str, object]],
    base_inventory_path: Path | None = None,
    base_normalized_path: Path | None = None,
    add_normalized_paths: Sequence[Path] = (),
    pack_id: str = DEFAULT_PACK_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    base_rows = _normalized_rows(base_normalized_payload)
    add_rows = [row for payload in add_normalized_payloads for row in _normalized_rows(payload)]
    combined_rows, duplicate_rows = _dedupe_rows((*base_rows, *add_rows))
    semantic_inventory = deepcopy(dict(base_inventory_payload))
    semantic_inventory["pair"] = "en-es"
    semantic_inventory["profile_id"] = "semantic_pack_builder"
    semantic_inventory["generated_at"] = generated_at
    semantic_inventory.setdefault("phrase_sets", {})
    merge_summary = _merge_anchor_cues_into_inventory(
        semantic_inventory=semantic_inventory,
        add_rows=add_rows,
    )
    component_batches = _component_batches(base_normalized_payload, add_normalized_payloads)
    semantic_inventory["lineage"] = _build_full_pack_lineage(
        pack_id=pack_id,
        generated_at=generated_at,
        base_inventory_path=base_inventory_path,
        base_normalized_path=base_normalized_path,
        add_normalized_paths=add_normalized_paths,
        component_batches=component_batches,
    )
    combined_batch = _combined_batch(
        base_payload=base_normalized_payload,
        rows=combined_rows,
        pack_id=pack_id,
        generated_at=generated_at,
        component_batches=component_batches,
    )
    summary = {
        "base_normalized_row_count": len(base_rows),
        "add_normalized_row_count": len(add_rows),
        "combined_normalized_row_count": len(combined_rows),
        "duplicate_row_count": len(duplicate_rows),
        **merge_summary,
        "trigger_count": len(_as_mapping(semantic_inventory.get("triggers"))),
        "sense_count": len(_as_mapping(semantic_inventory.get("senses"))),
        "competition_set_count": len(_as_mapping(semantic_inventory.get("competition_sets"))),
    }
    issues: list[str] = []
    if not add_rows:
        issues.append("no_additional_normalized_rows")
    if not merge_summary["new_family_count"] and not merge_summary["existing_family_append_count"]:
        issues.append("no_rows_merged_into_semantic_inventory")
    status = "ok" if not issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "active_only_full_pack_ready_for_named_install"
            if status == "ok"
            else "active_only_full_pack_needs_review"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "pack_id": str(pack_id or "").strip() or DEFAULT_PACK_ID,
        "inputs": {
            "base_inventory_path": _repo_path(base_inventory_path),
            "base_normalized_evidence_path": _repo_path(base_normalized_path),
            "add_normalized_evidence_paths": [_repo_path(path) for path in add_normalized_paths],
        },
        "methodology": {
            "runtime_policy_change": "none",
            "merge_scope": "append active-only anchor cues, preserve existing shadows and phrase sets",
            "new_family_policy": "create active-only competition set when trigger-target pair is absent",
            "existing_family_policy": "append generated evidence to existing active sense by trigger-target key",
            "runtime_publishable_rows": "kept false in source evidence; semantic inventory is the runtime materialization layer",
        },
        "summary": summary,
        "component_batches": component_batches,
        "new_family_samples": merge_summary["new_family_samples"],
        "existing_family_append_samples": merge_summary["existing_family_append_samples"],
        "duplicate_samples": duplicate_rows[:10],
        "combined_normalized_batch": combined_batch,
        "semantic_inventory": semantic_inventory,
        "issues": issues,
    }


def render_active_only_full_pack_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    artifacts = _as_mapping(report.get("artifacts"))
    lines = [
        "# en-es Active-Only Full Semantic Pack Builder",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Pack id: `{report.get('pack_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Base rows: `{summary.get('base_normalized_row_count', 0)}`",
        f"- Added rows: `{summary.get('add_normalized_row_count', 0)}`",
        f"- Combined rows: `{summary.get('combined_normalized_row_count', 0)}`",
        f"- New active-only families: `{summary.get('new_family_count', 0)}`",
        f"- Existing families appended: `{summary.get('existing_family_append_count', 0)}`",
        f"- Duplicate rows skipped: `{summary.get('duplicate_row_count', 0)}`",
        f"- Inventory triggers/senses/competition sets: `{summary.get('trigger_count', 0)}` / "
        f"`{summary.get('sense_count', 0)}` / `{summary.get('competition_set_count', 0)}`",
        "",
        "## Artifacts",
        "",
        f"- Combined normalized evidence: `{artifacts.get('combined_normalized_evidence', '')}`",
        f"- Semantic inventory: `{artifacts.get('semantic_inventory', '')}`",
        "",
        "## Component Batches",
        "",
        "| Batch | Source | Rows | Families |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in _mapping_rows(report.get("component_batches")):
        lines.append(
            f"| `{row.get('batch_id', '')}` | `{row.get('source_id', '')}` | "
            f"{row.get('row_count', 0)} | {row.get('family_count', 0)} |"
        )
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{item}`" for item in report.get("issues", ()))
    return "\n".join(lines) + "\n"


def _merge_anchor_cues_into_inventory(
    *,
    semantic_inventory: dict[str, object],
    add_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    triggers = _ensure_mapping(semantic_inventory, "triggers")
    senses = _ensure_mapping(semantic_inventory, "senses")
    competition_sets = _ensure_mapping(semantic_inventory, "competition_sets")
    existing_by_key = _existing_trigger_target_index(
        triggers=triggers,
        senses=senses,
        competition_sets=competition_sets,
    )
    rows_by_family: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in add_rows:
        if str(row.get("relation_type") or "") != "anchor_cue":
            continue
        family_id = _family_id(row)
        if family_id:
            rows_by_family[family_id].append(row)

    new_family_count = 0
    existing_family_append_count = 0
    appended_row_count = 0
    new_family_samples: list[dict[str, object]] = []
    existing_family_append_samples: list[dict[str, object]] = []
    for family_id, family_rows in sorted(rows_by_family.items()):
        first = family_rows[0]
        trigger = _text(first.get("trigger")) or _text(first.get("normalized_trigger"))
        target = _text(first.get("active_target")) or _text(first.get("candidate_target"))
        if not trigger or not target:
            continue
        key = (_normalize(trigger), _normalize(target))
        evidence_parts = [
            _text(row.get("evidence_text"))
            for row in family_rows
            if _text(row.get("evidence_text"))
        ]
        if not evidence_parts:
            continue
        existing = existing_by_key.get(key)
        if existing:
            _append_generated_evidence(
                senses=senses,
                active_sense_id=str(existing.get("active_sense_id") or ""),
                evidence_parts=evidence_parts,
            )
            existing_family_append_count += 1
            appended_row_count += len(evidence_parts)
            if len(existing_family_append_samples) < 10:
                existing_family_append_samples.append(
                    {
                        "family_id": family_id,
                        "trigger": trigger,
                        "target": target,
                        "appended_row_count": len(evidence_parts),
                    }
                )
            continue
        trigger_id = f"{family_id}:trigger"
        active_sense_id = f"{family_id}:active"
        competition_set_id = f"{family_id}:competition:active-only-pack"
        triggers[trigger_id] = {
            "trigger_id": trigger_id,
            "source_phrase": trigger,
            "normalized_source_phrase": _normalize(trigger),
            "token_count": max(1, len(trigger.split())),
        }
        senses[active_sense_id] = {
            "sense_id": active_sense_id,
            "target_lemma": target,
            "sense_label": _sense_label(first, trigger=trigger, target=target),
            "evidence_views": _active_evidence_views(
                first, trigger=trigger, target=target, evidence_parts=evidence_parts
            ),
            "provider": "semantic_veto_active_only_full_pack",
            "locator": {
                "provider": "semantic_veto_active_only_full_pack",
                "locator_kind": "source_target_family",
                "opaque_id": family_id,
            },
        }
        competition_sets[competition_set_id] = {
            "competition_set_id": competition_set_id,
            "trigger_id": trigger_id,
            "status": "ready",
            "active_sense_id": active_sense_id,
            "shadow_sense_ids": [],
            "selection_mode": "active_only",
            "selection_policy_version": "active_only_anchor_cue_v1",
        }
        existing_by_key[key] = {
            "active_sense_id": active_sense_id,
            "competition_set_id": competition_set_id,
            "trigger_id": trigger_id,
        }
        new_family_count += 1
        appended_row_count += len(evidence_parts)
        if len(new_family_samples) < 10:
            new_family_samples.append(
                {
                    "family_id": family_id,
                    "trigger": trigger,
                    "target": target,
                    "evidence_row_count": len(evidence_parts),
                }
            )
    return {
        "new_family_count": new_family_count,
        "existing_family_append_count": existing_family_append_count,
        "merged_evidence_row_count": appended_row_count,
        "new_family_samples": new_family_samples,
        "existing_family_append_samples": existing_family_append_samples,
    }


def _existing_trigger_target_index(
    *,
    triggers: Mapping[str, object],
    senses: Mapping[str, object],
    competition_sets: Mapping[str, object],
) -> dict[tuple[str, str], dict[str, str]]:
    index: dict[tuple[str, str], dict[str, str]] = {}
    for competition_set_id, raw_set in competition_sets.items():
        competition_set = _as_mapping(raw_set)
        trigger = _as_mapping(triggers.get(_text(competition_set.get("trigger_id"))))
        active_sense_id = _text(competition_set.get("active_sense_id"))
        active_sense = _as_mapping(senses.get(active_sense_id))
        source_phrase = _text(trigger.get("source_phrase"))
        target = _text(active_sense.get("target_lemma"))
        if source_phrase and target:
            index[(_normalize(source_phrase), _normalize(target))] = {
                "active_sense_id": active_sense_id,
                "competition_set_id": str(competition_set_id),
                "trigger_id": _text(competition_set.get("trigger_id")),
            }
    return index


def _append_generated_evidence(
    *,
    senses: Mapping[str, object],
    active_sense_id: str,
    evidence_parts: Sequence[str],
) -> None:
    active_sense = senses.get(active_sense_id)
    if not isinstance(active_sense, dict):
        return
    evidence_views = active_sense.setdefault("evidence_views", {})
    if not isinstance(evidence_views, dict):
        return
    existing = _text(evidence_views.get("all_evidence_text"))
    appended = " | ".join(f"generated evidence: {part}" for part in evidence_parts)
    evidence_views["all_evidence_text"] = f"{existing} | {appended}" if existing else appended


def _active_evidence_views(
    row: Mapping[str, object],
    *,
    trigger: str,
    target: str,
    evidence_parts: Sequence[str],
) -> dict[str, str]:
    sense_label = _sense_label(row, trigger=trigger, target=target)
    generated_text = " | ".join(f"generated evidence: {part}" for part in evidence_parts)
    return {
        "sense_label": sense_label,
        "sense_gloss_bundle": sense_label,
        "all_evidence_text": f"{sense_label} | {generated_text}" if generated_text else sense_label,
    }


def _sense_label(row: Mapping[str, object], *, trigger: str, target: str) -> str:
    for key in ("active_sense_hint", "candidate_sense_hint"):
        hint = _as_mapping(row.get(key))
        label = _text(hint.get("sense_label"))
        if label:
            return label
    return f"{trigger} -> {target}"


def _build_full_pack_lineage(
    *,
    pack_id: str,
    generated_at: str,
    base_inventory_path: Path | None,
    base_normalized_path: Path | None,
    add_normalized_paths: Sequence[Path],
    component_batches: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "lineage_kind": "active_only_full_pack_builder",
        "pack_id": str(pack_id or "").strip() or DEFAULT_PACK_ID,
        "generated_at": generated_at,
        "base_inventory_path": _repo_path(base_inventory_path),
        "base_normalized_evidence_path": _repo_path(base_normalized_path),
        "add_normalized_evidence_paths": [_repo_path(path) for path in add_normalized_paths],
        "source_batches": [
            str(row.get("batch_id") or "").strip()
            for row in component_batches
            if str(row.get("batch_id") or "").strip()
        ],
        "component_batches": [dict(row) for row in component_batches],
    }


def _combined_batch(
    *,
    base_payload: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    pack_id: str,
    generated_at: str,
    component_batches: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_composite_v1",
        "batch_id": f"en-es:semantic-veto:{pack_id}",
        "pair": "en-es",
        "source_type": "internal",
        "source_id": pack_id,
        "source_family": "internal_rulegen_artifact",
        "roles": sorted({role for row in rows for role in _text_sequence(row.get("roles"))}),
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "mixed",
        "prompt_version": "semantic-veto-active-only-composite-v1",
        "row_count": len(rows),
        "source_batches": [
            str(row.get("batch_id") or "").strip()
            for row in component_batches
            if str(row.get("batch_id") or "").strip()
        ],
        "rows": [dict(row) for row in rows],
        "provenance": {
            "base_batch_id": _text(base_payload.get("batch_id")),
            "component_batches": [dict(row) for row in component_batches],
        },
    }


def _component_batches(
    base_payload: Mapping[str, object],
    add_payloads: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    batches = [base_payload, *add_payloads]
    return [
        {
            "batch_id": _text(payload.get("batch_id")),
            "source_id": _text(payload.get("source_id")),
            "source_type": _text(payload.get("source_type")),
            "source_family": _text(payload.get("source_family")),
            "row_count": len(_normalized_rows(payload)),
            "family_count": len(
                {_family_id(row) for row in _normalized_rows(payload) if _family_id(row)}
            ),
        }
        for payload in batches
    ]


def _dedupe_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    seen: set[tuple[str, str, str, str]] = set()
    accepted: list[dict[str, object]] = []
    duplicates: list[dict[str, object]] = []
    for row in rows:
        key = (
            _family_id(row),
            _normalize(_text(row.get("trigger"))),
            _normalize(_text(row.get("active_target")) or _text(row.get("candidate_target"))),
            _normalize(_text(row.get("evidence_text"))),
        )
        if key in seen:
            duplicates.append(
                {
                    "family_id": key[0],
                    "trigger": key[1],
                    "target": key[2],
                    "evidence_text": _text(row.get("evidence_text")),
                }
            )
            continue
        seen.add(key)
        accepted.append(dict(row))
    return accepted, duplicates


def _normalized_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    return _mapping_rows(payload.get("rows"))


def _family_id(row: Mapping[str, object]) -> str:
    return _text(_as_mapping(row.get("metadata")).get("family_id"))


def _ensure_mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.setdefault(key, {})
    if not isinstance(value, dict):
        payload[key] = {}
        return payload[key]  # type: ignore[return-value]
    return value


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Mapping):
        iterable = value.values()
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        iterable = value
    else:
        return []
    return [row for row in iterable if isinstance(row, Mapping)]


def _text_sequence(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_text(item) for item in value if _text(item)]
    return []


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


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
