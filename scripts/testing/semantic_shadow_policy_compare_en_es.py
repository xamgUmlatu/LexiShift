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
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    SHADOW_PROMOTION_POLICIES,
    promote_shadow_candidates_for_policy,
)


DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_policy_compare_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_policy_compare_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare en-es shadow promotion policies against the latest inventory artifact."
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


def _reason_bucket(reasons: Sequence[object]) -> str:
    normalized = tuple(str(reason or "").strip() for reason in reasons if str(reason or "").strip())
    normalized_set = set(normalized)
    if not normalized_set:
        return "no_signal"
    if normalized_set == {"same_pos_as_active"}:
        return "same_pos_only"
    return "benchmark_aligned"


def build_policy_comparison_report(inventory_report: Mapping[str, object]) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    inventory = inventory_report.get("inventory")
    if not isinstance(inventory, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "inventory_unavailable",
            "inventory_status": str(inventory_report.get("status") or "unknown"),
            "policies": {},
        }

    policies: dict[str, object] = {}
    targets = inventory.get("targets", ())
    for policy in SHADOW_PROMOTION_POLICIES:
        top1_bucket_counts: Counter[str] = Counter()
        promoted_candidate_count = 0
        promoted_trigger_count = 0
        sample_rows: list[dict[str, object]] = []
        for target_row in targets:
            if not isinstance(target_row, Mapping):
                continue
            target = str(target_row.get("target") or "").strip()
            trigger_entries = target_row.get("trigger_entries")
            if not isinstance(trigger_entries, Sequence) or isinstance(
                trigger_entries, (str, bytes)
            ):
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
                promoted = promote_shadow_candidates_for_policy(
                    shadow_candidates=shadow_candidates,
                    active_candidates=active_candidates,
                    policy=policy,
                )
                if not promoted:
                    top1_bucket_counts["no_promotion"] += 1
                    continue
                promoted_trigger_count += 1
                promoted_candidate_count += len(promoted)
                bucket = _reason_bucket(promoted[0].get("promotion_reasons", ()))
                top1_bucket_counts[bucket] += 1
                if len(sample_rows) < 20:
                    sample_rows.append(
                        {
                            "target": target,
                            "trigger": str(trigger_entry.get("trigger") or "").strip(),
                            "promoted_target": str(promoted[0].get("target") or "").strip(),
                            "promotion_reasons": list(promoted[0].get("promotion_reasons", ())),
                            "reason_bucket": bucket,
                        }
                    )
        policies[policy] = {
            "summary": {
                "promoted_trigger_count": promoted_trigger_count,
                "promoted_candidate_count": promoted_candidate_count,
            },
            "top1_bucket_counts": dict(top1_bucket_counts),
            "sample_rows": sample_rows,
        }
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "inventory_status": str(inventory_report.get("status") or "unknown"),
        "inventory_promotion_policy": str(inventory.get("promotion_policy") or ""),
        "policies": policies,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Promotion Policy Comparison",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory status: `{report.get('inventory_status', 'unknown')}`",
        f"- Inventory default policy: `{report.get('inventory_promotion_policy', '')}`",
    ]
    policies = report.get("policies")
    if not isinstance(policies, Mapping):
        return "\n".join(lines) + "\n"
    for policy in SHADOW_PROMOTION_POLICIES:
        payload = policies.get(policy)
        if not isinstance(payload, Mapping):
            continue
        summary = payload.get("summary")
        top1_bucket_counts = payload.get("top1_bucket_counts")
        lines.extend(["", f"## {policy}"])
        if isinstance(summary, Mapping):
            lines.extend(
                [
                    f"- Promoted triggers: `{summary.get('promoted_trigger_count', 0)}`",
                    f"- Promoted candidate rows: `{summary.get('promoted_candidate_count', 0)}`",
                ]
            )
        if isinstance(top1_bucket_counts, Mapping):
            for key in ("benchmark_aligned", "same_pos_only", "no_signal", "no_promotion"):
                lines.append(f"- `{key}`: `{top1_bucket_counts.get(key, 0)}`")
        sample_rows = payload.get("sample_rows")
        if isinstance(sample_rows, Sequence) and not isinstance(sample_rows, (str, bytes)):
            lines.append("- Samples:")
            for row in sample_rows[:8]:
                if not isinstance(row, Mapping):
                    continue
                reasons = ", ".join(row.get("promotion_reasons", ())) or "none"
                lines.append(
                    f"  - `{row.get('target', '')}` / `{row.get('trigger', '')}` -> "
                    f"`{row.get('promoted_target', '')}` (`{reasons}`)"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    report = build_policy_comparison_report(payload)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
