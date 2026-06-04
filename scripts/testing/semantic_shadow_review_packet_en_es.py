#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_POLICY_COMPARE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_policy_compare_en_es_latest.json"
)
DEFAULT_REVIEW_QUEUE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_review_queue_en_es_latest.json"
)
DEFAULT_GAP_QUEUE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_policy_gap_queue_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_review_packet_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_review_packet_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a single en-es shadow-review packet that combines the policy summary, "
            "review queue, and gap queue into one human-facing artifact."
        )
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=DEFAULT_INVENTORY_JSON,
        help="Input semantic shadow inventory JSON artifact.",
    )
    parser.add_argument(
        "--policy-compare-json",
        type=Path,
        default=DEFAULT_POLICY_COMPARE_JSON,
        help="Input shadow policy comparison JSON artifact.",
    )
    parser.add_argument(
        "--review-queue-json",
        type=Path,
        default=DEFAULT_REVIEW_QUEUE_JSON,
        help="Input shadow review queue JSON artifact.",
    )
    parser.add_argument(
        "--gap-queue-json",
        type=Path,
        default=DEFAULT_GAP_QUEUE_JSON,
        help="Input shadow policy gap queue JSON artifact.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def _as_mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _build_inventory_lookup(
    inventory_report: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    inventory = _as_mapping(inventory_report.get("inventory"))
    lookup: dict[tuple[str, str], Mapping[str, object]] = {}
    if inventory is None:
        return lookup
    for target_row in _as_sequence(inventory.get("targets")):
        target_row_map = _as_mapping(target_row)
        if target_row_map is None:
            continue
        target = str(target_row_map.get("target") or "").strip()
        if not target:
            continue
        for trigger_entry in _as_sequence(target_row_map.get("trigger_entries")):
            trigger_entry_map = _as_mapping(trigger_entry)
            if trigger_entry_map is None:
                continue
            trigger = str(trigger_entry_map.get("trigger") or "").strip()
            if trigger:
                lookup[(target, trigger)] = trigger_entry_map
    return lookup


def _first_active_summary(trigger_entry: Mapping[str, object] | None) -> dict[str, object]:
    if trigger_entry is None:
        return {"count": 0, "summary": "missing inventory row"}
    active_candidates = _as_sequence(trigger_entry.get("active_candidates"))
    if not active_candidates:
        return {"count": 0, "summary": "none"}
    first = _as_mapping(active_candidates[0]) or {}
    glosses = _as_sequence(first.get("glosses"))
    gloss = str(glosses[0] if glosses else first.get("sense_label") or "").strip()
    canonical_pos = str(first.get("canonical_pos") or "").strip() or "unknown"
    matched_trigger = str(first.get("matched_trigger") or "").strip()
    summary = f"{canonical_pos}: {gloss}"
    if matched_trigger:
        summary += f" (matched {matched_trigger})"
    return {"count": len(active_candidates), "summary": summary}


def _candidate_reasons(candidate: Mapping[str, object]) -> list[str]:
    return [
        str(item).strip()
        for item in _as_sequence(candidate.get("promotion_reasons"))
        if str(item).strip()
    ]


def _review_recommendation(*, target: str, trigger: str, shadow_target: str) -> str:
    keep_rows = {
        ("coger", "take", "llevar"),
        ("cuadro", "table", "tabla"),
        ("llevar", "take", "coger"),
        ("malla", "net", "red"),
        ("marco", "frame", "cuadro"),
        ("sacar", "remove", "quitar"),
    }
    return "keep" if (target, trigger, shadow_target) in keep_rows else "review"


def _gap_recommendation(*, target: str, trigger: str, shadow_target: str, drop_reason: str) -> str:
    if drop_reason == "cross_pos_without_reviewed_trigger":
        return "drop"
    if (target, trigger, shadow_target) in {
        ("caso", "matter", "punto"),
        ("plaza", "square", "cuadro"),
        ("subir", "rise", "salir"),
    }:
        return "drop_for_now"
    return "drop"


def build_review_packet(
    *,
    inventory_report: Mapping[str, object],
    policy_compare_report: Mapping[str, object],
    review_queue_report: Mapping[str, object],
    gap_queue_report: Mapping[str, object],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    inventory_lookup = _build_inventory_lookup(inventory_report)

    policies = _as_mapping(policy_compare_report.get("policies")) or {}
    policy_snapshot: dict[str, dict[str, int]] = {}
    for name in (
        "same_pos_lenient_v1",
        "benchmark_backed_v1",
        "cross_checked_v1",
        "cross_checked_backoff_missing_active_v1",
    ):
        policy_row = _as_mapping(policies.get(name)) or {}
        summary = _as_mapping(policy_row.get("summary")) or {}
        policy_snapshot[name] = {
            "promoted_trigger_count": int(summary.get("promoted_trigger_count") or 0),
            "promoted_candidate_count": int(summary.get("promoted_candidate_count") or 0),
        }

    review_rows: list[dict[str, object]] = []
    for row in _as_sequence(review_queue_report.get("rows")):
        row_map = _as_mapping(row)
        if row_map is None:
            continue
        target = str(row_map.get("target") or "").strip()
        trigger = str(row_map.get("trigger") or "").strip()
        trigger_entry = inventory_lookup.get((target, trigger))
        active_summary = _first_active_summary(trigger_entry)
        for candidate in _as_sequence(row_map.get("promoted_shadow_candidates")):
            candidate_map = _as_mapping(candidate)
            if candidate_map is None:
                continue
            shadow_target = str(candidate_map.get("target") or "").strip()
            review_rows.append(
                {
                    "target": target,
                    "trigger": trigger,
                    "active_candidate_count": active_summary["count"],
                    "active_summary": active_summary["summary"],
                    "shadow_target": shadow_target,
                    "shadow_pos": str(candidate_map.get("canonical_pos") or "").strip(),
                    "shadow_label": str(candidate_map.get("sense_label") or "").strip(),
                    "promotion_reasons": _candidate_reasons(candidate_map),
                    "recommendation": _review_recommendation(
                        target=target,
                        trigger=trigger,
                        shadow_target=shadow_target,
                    ),
                }
            )

    gap_rows: list[dict[str, object]] = []
    for row in _as_sequence(gap_queue_report.get("rows")):
        row_map = _as_mapping(row)
        if row_map is None:
            continue
        target = str(row_map.get("target") or "").strip()
        trigger = str(row_map.get("trigger") or "").strip()
        shadow_target = str(row_map.get("promoted_target") or "").strip()
        trigger_entry = inventory_lookup.get((target, trigger))
        active_summary = _first_active_summary(trigger_entry)
        gap_rows.append(
            {
                "target": target,
                "trigger": trigger,
                "active_candidate_count": active_summary["count"],
                "active_summary": active_summary["summary"],
                "shadow_target": shadow_target,
                "shadow_pos": str(row_map.get("shadow_pos") or "").strip(),
                "drop_reason": str(row_map.get("drop_reason") or "").strip(),
                "promotion_reasons": [
                    str(item).strip()
                    for item in _as_sequence(row_map.get("promotion_reasons"))
                    if str(item).strip()
                ],
                "recommendation": _gap_recommendation(
                    target=target,
                    trigger=trigger,
                    shadow_target=shadow_target,
                    drop_reason=str(row_map.get("drop_reason") or "").strip(),
                ),
            }
        )

    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "policy_snapshot": policy_snapshot,
        "provisional_runtime_policy": "cross_checked_v1",
        "review_rows": review_rows,
        "gap_rows": gap_rows,
    }


def _render_policy_snapshot(policy_snapshot: Mapping[str, object]) -> list[str]:
    lines = ["## Policy Snapshot"]
    for name in (
        "same_pos_lenient_v1",
        "benchmark_backed_v1",
        "cross_checked_v1",
        "cross_checked_backoff_missing_active_v1",
    ):
        row = _as_mapping(policy_snapshot.get(name)) or {}
        lines.append(
            f"- `{name}`: triggers=`{row.get('promoted_trigger_count', 0)}` "
            f"candidates=`{row.get('promoted_candidate_count', 0)}`"
        )
    return lines


def _render_review_rows(review_rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "## Provisional Keep Rows",
        "| Target | Trigger | Active Support | Shadow | Reasons | Recommendation |",
        "|---|---|---|---|---|---|",
    ]
    if not review_rows:
        lines.append("| none | none | none | none | none | none |")
        return lines
    for row in review_rows:
        reasons = (
            ", ".join(str(item) for item in _as_sequence(row.get("promotion_reasons"))) or "none"
        )
        lines.append(
            f"| `{row.get('target', '')}` | `{row.get('trigger', '')}` | "
            f"`{row.get('active_summary', '')}` | `{row.get('shadow_target', '')}` | "
            f"`{reasons}` | `{row.get('recommendation', '')}` |"
        )
    return lines


def _render_gap_rows(gap_rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "## Provisional Drop Rows",
        "| Target | Trigger | Active Support | Shadow | Drop Reason | Recommendation |",
        "|---|---|---|---|---|---|",
    ]
    if not gap_rows:
        lines.append("| none | none | none | none | none | none |")
        return lines
    for row in gap_rows:
        lines.append(
            f"| `{row.get('target', '')}` | `{row.get('trigger', '')}` | "
            f"`{row.get('active_summary', '')}` | `{row.get('shadow_target', '')}` | "
            f"`{row.get('drop_reason', '')}` | `{row.get('recommendation', '')}` |"
        )
    return lines


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Review Packet",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Provisional runtime policy: `{report.get('provisional_runtime_policy', '')}`",
        "",
        "## How To Read This Packet",
        "- `Active Support` is what the active target currently has for that English trigger from forward pack evidence.",
        "- `Shadow` is the competing Spanish target that the current shadow miner would test against.",
        "- `Provisional Keep Rows` are the surviving blockers under the current strict policy.",
        "- `Provisional Drop Rows` are rows that a looser benchmark-backed policy would allow, but the strict policy currently drops.",
        "",
    ]
    lines.extend(_render_policy_snapshot(_as_mapping(report.get("policy_snapshot")) or {}))
    lines.extend([""])
    lines.extend(
        _render_review_rows(
            [_as_mapping(row) or {} for row in _as_sequence(report.get("review_rows"))]
        )
    )
    lines.extend([""])
    lines.extend(
        _render_gap_rows([_as_mapping(row) or {} for row in _as_sequence(report.get("gap_rows"))])
    )
    lines.extend(
        [
            "",
            "## Current Recommendation",
            "- Keep the `Provisional Keep Rows` in the `en-es` blocker set.",
            "- Keep the `Provisional Drop Rows` dropped for now.",
            "- Treat missing active evidence as a reason to stay conservative, not to widen the policy.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    inventory_report = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    policy_compare_report = json.loads(args.policy_compare_json.read_text(encoding="utf-8"))
    review_queue_report = json.loads(args.review_queue_json.read_text(encoding="utf-8"))
    gap_queue_report = json.loads(args.gap_queue_json.read_text(encoding="utf-8"))
    report = build_review_packet(
        inventory_report=inventory_report,
        policy_compare_report=policy_compare_report,
        review_queue_report=review_queue_report,
        gap_queue_report=gap_queue_report,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
