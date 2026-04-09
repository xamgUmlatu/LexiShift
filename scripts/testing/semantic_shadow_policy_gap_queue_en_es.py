#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    promote_shadow_candidates_for_policy,
)


DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_policy_gap_queue_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_policy_gap_queue_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a focused review queue for rows that survive benchmark-backed shadow "
            "promotion but are dropped by the stricter cross-checked policy."
        )
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=DEFAULT_INVENTORY_JSON,
        help="Input semantic shadow inventory JSON artifact.",
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


def _infer_drop_reason(
    *,
    active_candidates: Sequence[Mapping[str, object]],
    promoted_shadow: Mapping[str, object],
) -> str:
    active_pos_values = {
        str(candidate.get("canonical_pos") or "").strip().lower()
        for candidate in active_candidates
        if isinstance(candidate, Mapping) and str(candidate.get("canonical_pos") or "").strip()
    }
    shadow_pos = str(promoted_shadow.get("canonical_pos") or "").strip().lower()
    reviewed_trigger_support = bool(promoted_shadow.get("reviewed_trigger_support"))
    if reviewed_trigger_support:
        return "unexpected_drop"
    if not active_pos_values:
        return "missing_active_pos"
    if shadow_pos and shadow_pos not in active_pos_values:
        return "cross_pos_without_reviewed_trigger"
    return "benchmark_only_without_reviewed_trigger"


def build_gap_queue(inventory_report: Mapping[str, object]) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    inventory = inventory_report.get("inventory")
    if not isinstance(inventory, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "inventory_unavailable",
            "inventory_status": str(inventory_report.get("status") or "unknown"),
            "row_count": 0,
            "rows": [],
        }

    rows: list[dict[str, object]] = []
    for target_row in inventory.get("targets", ()):
        if not isinstance(target_row, Mapping):
            continue
        target = str(target_row.get("target") or "").strip()
        trigger_entries = target_row.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            continue
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            active_candidates = trigger_entry.get("active_candidates")
            shadow_candidates = trigger_entry.get("shadow_candidates")
            if not isinstance(active_candidates, Sequence) or isinstance(
                active_candidates, (str, bytes)
            ):
                active_candidates = ()
            if not isinstance(shadow_candidates, Sequence) or isinstance(
                shadow_candidates, (str, bytes)
            ):
                shadow_candidates = ()
            benchmark_backed = promote_shadow_candidates_for_policy(
                shadow_candidates=shadow_candidates,
                active_candidates=active_candidates,
                policy="benchmark_backed_v1",
            )
            cross_checked = promote_shadow_candidates_for_policy(
                shadow_candidates=shadow_candidates,
                active_candidates=active_candidates,
                policy="cross_checked_v1",
            )
            if not benchmark_backed or cross_checked:
                continue
            first = benchmark_backed[0]
            rows.append(
                {
                    "target": target,
                    "trigger": str(trigger_entry.get("trigger") or "").strip(),
                    "promoted_target": str(first.get("target") or "").strip(),
                    "promotion_reasons": list(first.get("promotion_reasons", ())),
                    "drop_reason": _infer_drop_reason(
                        active_candidates=active_candidates,
                        promoted_shadow=first,
                    ),
                    "active_pos_values": [
                        str(candidate.get("canonical_pos") or "").strip()
                        for candidate in active_candidates
                        if isinstance(candidate, Mapping)
                        and str(candidate.get("canonical_pos") or "").strip()
                    ],
                    "shadow_pos": str(first.get("canonical_pos") or "").strip(),
                }
            )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "inventory_status": str(inventory_report.get("status") or "unknown"),
        "row_count": len(rows),
        "rows": rows,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Policy Gap Queue",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory status: `{report.get('inventory_status', 'unknown')}`",
        f"- Rows: `{report.get('row_count', 0)}`",
    ]
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"
    lines.extend(["", "## Queue"])
    if not rows:
        lines.append("- No benchmark-backed rows are uniquely dropped by `cross_checked_v1`.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        reasons = ", ".join(row.get("promotion_reasons", ())) or "none"
        active_pos = ", ".join(row.get("active_pos_values", ())) or "none"
        lines.append(
            f"- `{row.get('target', '')}` / `{row.get('trigger', '')}` -> "
            f"`{row.get('promoted_target', '')}` (`{reasons}`) | "
            f"drop=`{row.get('drop_reason', '')}` | active_pos=`{active_pos}` | "
            f"shadow_pos=`{row.get('shadow_pos', '')}`"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    report = build_gap_queue(payload)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
