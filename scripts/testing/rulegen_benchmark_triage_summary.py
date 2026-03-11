#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


MAX_ITEMS = 10


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def render_summary(
    payload: dict[str, Any],
    *,
    title: str = "Rulegen Benchmark Triage",
    max_items: int = MAX_ITEMS,
) -> str:
    items = payload.get("items")
    if not isinstance(items, list):
        raise SystemExit("Triage JSON does not contain an 'items' list.")

    benchmark_json = str(payload.get("benchmark_json") or "")
    pairs_processed = int(payload.get("pairs_processed") or 0)
    failing_or_review_count = int(payload.get("failing_or_review_count") or 0)

    status_counts = Counter()
    pair_counts = Counter()
    actionable: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "UNKNOWN")
        pair = str(item.get("pair") or "<unknown>")
        status_counts[status] += 1
        pair_counts[pair] += 1
        actionable.append(item)

    lines = [
        f"# {title}",
        "",
        f"- Benchmark JSON: `{benchmark_json}`" if benchmark_json else "- Benchmark JSON: unknown",
        f"- Pairs processed: {pairs_processed}",
        f"- Actionable items: {failing_or_review_count}",
        f"- FAIL items: {status_counts.get('FAIL', 0)}",
        f"- REVIEW items: {status_counts.get('REVIEW', 0)}",
        "",
    ]

    if pair_counts:
        lines.append("## Items By Pair")
        lines.append("")
        for pair, count in sorted(pair_counts.items()):
            lines.append(f"- `{pair}`: {count}")
        lines.append("")

    lines.append("## Actionable Cases")
    if not actionable:
        lines.extend(["", "None.", ""])
        return "\n".join(lines)

    lines.append("")
    for index, item in enumerate(actionable[: max(1, int(max_items))], start=1):
        pair = str(item.get("pair") or "")
        case_id = str(item.get("case_id") or "")
        target = str(item.get("target") or "")
        status = str(item.get("status") or "")
        reasons = item.get("reasons")
        reasons_text = (
            ", ".join(str(reason) for reason in reasons) if isinstance(reasons, list) else ""
        )
        top1 = str(item.get("top1_source") or "")
        lines.append(f"{index}. [{status}] `{pair}` `{case_id}` target=`{target}`")
        if reasons_text:
            lines.append(f"   - Reasons: {reasons_text}")
        if top1:
            lines.append(f"   - Observed top1: `{top1}`")

    if len(actionable) > max(1, int(max_items)):
        lines.append(f"{max_items + 1}. Additional items omitted: {len(actionable) - max_items}")

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Markdown summaries from rulegen benchmark triage JSON."
    )
    parser.add_argument("--triage-json", type=Path, required=True, help="Path to triage JSON.")
    parser.add_argument("--title", default="Rulegen Benchmark Triage", help="Summary title.")
    parser.add_argument(
        "--max-items",
        type=int,
        default=MAX_ITEMS,
        help="Maximum number of actionable items to include.",
    )
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(
        _load_json(args.triage_json),
        title=str(args.title),
        max_items=max(1, int(args.max_items)),
    )
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown, encoding="utf-8")
        print(f"markdown_out: {args.markdown_out}")
    if args.append_to:
        args.append_to.parent.mkdir(parents=True, exist_ok=True)
        with args.append_to.open("a", encoding="utf-8") as handle:
            handle.write(markdown)
            if not markdown.endswith("\n"):
                handle.write("\n")
        print(f"append_to: {args.append_to}")
    print(markdown, end="" if markdown.endswith("\n") else "\n")


if __name__ == "__main__":
    main()
