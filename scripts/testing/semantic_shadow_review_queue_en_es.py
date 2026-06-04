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
    DEFAULT_SHADOW_PROMOTION_POLICY,
    SHADOW_PROMOTION_POLICIES,
    promote_shadow_candidates_for_policy,
)


DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_review_queue_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_review_queue_en_es_latest.md"
)
DEFAULT_FOCUS_TARGETS = (
    "marco",
    "cuadro",
    "sacar",
    "quitar",
    "coger",
    "llevar",
    "malla",
    "red",
    "banco",
    "pelota",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a focused en-es shadow review queue for selected benchmark targets under a "
            "named shadow promotion policy."
        )
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=DEFAULT_INVENTORY_JSON,
        help="Input semantic shadow inventory JSON artifact.",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="cross_checked_v1",
        choices=SHADOW_PROMOTION_POLICIES,
        help="Promotion policy to inspect.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Optional target filter. Repeat to include multiple targets.",
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


def _normalize_target_list(values: Sequence[object]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def build_review_queue(
    *,
    inventory_report: Mapping[str, object],
    policy: str,
    focus_targets: Sequence[str],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    inventory = inventory_report.get("inventory")
    if not isinstance(inventory, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "inventory_unavailable",
            "inventory_status": str(inventory_report.get("status") or "unknown"),
            "policy": policy,
            "focus_targets": list(focus_targets),
            "rows": [],
        }

    selected_targets = set(_normalize_target_list(focus_targets))
    rows: list[dict[str, object]] = []
    for target_row in inventory.get("targets", ()):
        if not isinstance(target_row, Mapping):
            continue
        target = str(target_row.get("target") or "").strip()
        if selected_targets and target not in selected_targets:
            continue
        trigger_entries = target_row.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            continue
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            promoted = promote_shadow_candidates_for_policy(
                shadow_candidates=trigger_entry.get("shadow_candidates", ()),
                active_candidates=trigger_entry.get("active_candidates", ()),
                policy=policy,
            )
            if not promoted:
                continue
            rows.append(
                {
                    "target": target,
                    "trigger": str(trigger_entry.get("trigger") or "").strip(),
                    "active_candidates": list(trigger_entry.get("active_candidates", ())),
                    "promoted_shadow_candidates": promoted,
                }
            )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "inventory_status": str(inventory_report.get("status") or "unknown"),
        "policy": policy,
        "focus_targets": list(focus_targets),
        "row_count": len(rows),
        "rows": rows,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Review Queue",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory status: `{report.get('inventory_status', 'unknown')}`",
        f"- Policy: `{report.get('policy', DEFAULT_SHADOW_PROMOTION_POLICY)}`",
        f"- Rows: `{report.get('row_count', 0)}`",
    ]
    focus_targets = report.get("focus_targets")
    if isinstance(focus_targets, Sequence) and not isinstance(focus_targets, (str, bytes)):
        lines.append(f"- Focus targets: `{', '.join(str(item) for item in focus_targets)}`")
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"
    lines.extend(["", "## Queue"])
    if not rows:
        lines.append("- No promoted rows for the selected policy/targets.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        promoted = row.get("promoted_shadow_candidates")
        if not isinstance(promoted, Sequence) or isinstance(promoted, (str, bytes)):
            continue
        shadow_bits = []
        for candidate in promoted:
            if not isinstance(candidate, Mapping):
                continue
            target = str(candidate.get("target") or "").strip()
            reasons = ", ".join(candidate.get("promotion_reasons", ())) or "none"
            shadow_bits.append(f"{target} [{reasons}]")
        lines.append(
            f"- `{row.get('target', '')}` / `{row.get('trigger', '')}` -> `{'; '.join(shadow_bits)}`"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    focus_targets = _normalize_target_list(args.target or DEFAULT_FOCUS_TARGETS)
    report = build_review_queue(
        inventory_report=payload,
        policy=args.policy,
        focus_targets=focus_targets,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
