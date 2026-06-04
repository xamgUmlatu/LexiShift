#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_triage_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_triage_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize promotion-signal quality from the latest en-es semantic shadow "
            "inventory artifact."
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


def _reason_bucket(reasons: Sequence[object]) -> str:
    normalized = tuple(str(reason or "").strip() for reason in reasons if str(reason or "").strip())
    normalized_set = set(normalized)
    if not normalized_set:
        return "no_signal"
    if normalized_set == {"same_pos_as_active"}:
        return "same_pos_only"
    return "benchmark_aligned"


def _top_candidate_bucket(trigger_entry: Mapping[str, object]) -> str:
    promoted = trigger_entry.get("promoted_shadow_candidates")
    if not isinstance(promoted, Sequence) or isinstance(promoted, (str, bytes)) or not promoted:
        return "no_promotion"
    first = promoted[0]
    if not isinstance(first, Mapping):
        return "no_signal"
    return _reason_bucket(first.get("promotion_reasons", ()))


def _collect_top_example(
    *,
    target: str,
    trigger_entry: Mapping[str, object],
) -> dict[str, object] | None:
    promoted = trigger_entry.get("promoted_shadow_candidates")
    if not isinstance(promoted, Sequence) or isinstance(promoted, (str, bytes)) or not promoted:
        return None
    first = promoted[0]
    if not isinstance(first, Mapping):
        return None
    return {
        "target": target,
        "trigger": str(trigger_entry.get("trigger") or "").strip(),
        "promoted_target": str(first.get("target") or "").strip(),
        "sense_label": str(first.get("sense_label") or "").strip(),
        "canonical_pos": str(first.get("canonical_pos") or "").strip(),
        "reason_bucket": _reason_bucket(first.get("promotion_reasons", ())),
        "promotion_reasons": [
            str(reason or "").strip()
            for reason in first.get("promotion_reasons", ())
            if str(reason or "").strip()
        ],
        "reviewed_trigger_support": bool(first.get("reviewed_trigger_support")),
        "benchmark_target_present": bool(first.get("benchmark_target_present")),
        "same_pos_as_active": bool(first.get("same_pos_as_active")),
    }


def build_triage_report(inventory_report: Mapping[str, object]) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    inventory = inventory_report.get("inventory")
    if not isinstance(inventory, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "inventory_unavailable",
            "inventory_status": str(inventory_report.get("status") or "unknown"),
            "summary": {},
            "top1_bucket_counts": {},
            "candidate_bucket_counts": {},
            "targets_with_no_signal_top1": [],
            "examples": {
                "benchmark_aligned_top1": [],
                "same_pos_only_top1": [],
                "no_signal_top1": [],
            },
        }

    top1_bucket_counts: Counter[str] = Counter()
    candidate_bucket_counts: Counter[str] = Counter()
    targets_with_no_signal_top1: defaultdict[str, int] = defaultdict(int)
    example_rows: dict[str, list[dict[str, object]]] = {
        "benchmark_aligned_top1": [],
        "same_pos_only_top1": [],
        "no_signal_top1": [],
    }
    trigger_count = 0
    promoted_trigger_count = 0
    promoted_candidate_count = 0
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
            trigger_count += 1
            bucket = _top_candidate_bucket(trigger_entry)
            top1_bucket_counts[bucket] += 1
            if bucket != "no_promotion":
                promoted_trigger_count += 1
                example = _collect_top_example(target=target, trigger_entry=trigger_entry)
                if example is not None:
                    if (
                        bucket == "benchmark_aligned"
                        and len(example_rows["benchmark_aligned_top1"]) < 20
                    ):
                        example_rows["benchmark_aligned_top1"].append(example)
                    elif bucket == "same_pos_only" and len(example_rows["same_pos_only_top1"]) < 20:
                        example_rows["same_pos_only_top1"].append(example)
                    elif bucket == "no_signal":
                        targets_with_no_signal_top1[target] += 1
                        if len(example_rows["no_signal_top1"]) < 25:
                            example_rows["no_signal_top1"].append(example)

            promoted = trigger_entry.get("promoted_shadow_candidates")
            if not isinstance(promoted, Sequence) or isinstance(promoted, (str, bytes)):
                continue
            for candidate in promoted:
                if not isinstance(candidate, Mapping):
                    continue
                promoted_candidate_count += 1
                candidate_bucket_counts[_reason_bucket(candidate.get("promotion_reasons", ()))] += 1

    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "inventory_status": str(inventory_report.get("status") or "unknown"),
        "summary": {
            "trigger_count": trigger_count,
            "promoted_trigger_count": promoted_trigger_count,
            "promoted_candidate_count": promoted_candidate_count,
        },
        "top1_bucket_counts": dict(top1_bucket_counts),
        "candidate_bucket_counts": dict(candidate_bucket_counts),
        "targets_with_no_signal_top1": [
            {"target": target, "count": count}
            for target, count in sorted(
                targets_with_no_signal_top1.items(),
                key=lambda item: (-item[1], item[0]),
            )[:20]
        ],
        "examples": example_rows,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic Shadow Inventory Triage",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory status: `{report.get('inventory_status', 'unknown')}`",
    ]
    summary = report.get("summary")
    if isinstance(summary, Mapping):
        lines.extend(
            [
                f"- Triggers scanned: `{summary.get('trigger_count', 0)}`",
                f"- Triggers with any promotion: `{summary.get('promoted_trigger_count', 0)}`",
                f"- Promoted candidate rows: `{summary.get('promoted_candidate_count', 0)}`",
            ]
        )
    top1_bucket_counts = report.get("top1_bucket_counts")
    if isinstance(top1_bucket_counts, Mapping):
        lines.extend(["", "## Top-1 Promotion Buckets"])
        for key in ("benchmark_aligned", "same_pos_only", "no_signal", "no_promotion"):
            lines.append(f"- `{key}`: `{top1_bucket_counts.get(key, 0)}`")
    candidate_bucket_counts = report.get("candidate_bucket_counts")
    if isinstance(candidate_bucket_counts, Mapping):
        lines.extend(["", "## Candidate Bucket Counts"])
        for key in ("benchmark_aligned", "same_pos_only", "no_signal"):
            lines.append(f"- `{key}`: `{candidate_bucket_counts.get(key, 0)}`")
    targets_with_no_signal_top1 = report.get("targets_with_no_signal_top1")
    if isinstance(targets_with_no_signal_top1, Sequence) and not isinstance(
        targets_with_no_signal_top1, (str, bytes)
    ):
        lines.extend(["", "## Targets With No-Signal Top-1 Promotions"])
        if targets_with_no_signal_top1:
            for row in targets_with_no_signal_top1:
                if not isinstance(row, Mapping):
                    continue
                lines.append(f"- `{row.get('target', '')}`: `{row.get('count', 0)}`")
        else:
            lines.append("- None")
    examples = report.get("examples")
    if isinstance(examples, Mapping):
        for key, title in (
            ("benchmark_aligned_top1", "Benchmark-Aligned Top-1 Examples"),
            ("same_pos_only_top1", "Same-POS-Only Top-1 Examples"),
            ("no_signal_top1", "No-Signal Top-1 Examples"),
        ):
            rows = examples.get(key)
            if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
                continue
            lines.extend(["", f"## {title}"])
            if not rows:
                lines.append("- None")
                continue
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                reasons = ", ".join(row.get("promotion_reasons", ())) or "none"
                lines.append(
                    f"- `{row.get('target', '')}` / `{row.get('trigger', '')}` -> "
                    f"`{row.get('promoted_target', '')}` (`{reasons}`)"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    report = build_triage_report(payload)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
