#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MAX_PAIRS = 12


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def render_summary(
    payload: dict[str, Any],
    *,
    title: str = "Rulegen Benchmark",
    max_pairs: int = MAX_PAIRS,
) -> str:
    pairs_payload = payload.get("pairs")
    sweep = payload.get("sweep")
    if not isinstance(pairs_payload, dict):
        raise SystemExit("Benchmark JSON does not contain a 'pairs' object.")
    if not isinstance(sweep, dict):
        raise SystemExit("Benchmark JSON does not contain a 'sweep' object.")

    generated_at = str(payload.get("generated_at") or "")
    dataset_path = str(payload.get("dataset_path") or "")
    profile_id = str(payload.get("profile_id") or "")
    configuration_count = int(sweep.get("configuration_count") or 0)
    pair_filter = sweep.get("pair_filter")
    pair_filter_text = (
        ", ".join(pair_filter) if isinstance(pair_filter, list) and pair_filter else "all"
    )

    lines = [
        f"# {title}",
        "",
        f"- Generated at: `{generated_at}`" if generated_at else "- Generated at: unknown",
        f"- Dataset: `{dataset_path}`" if dataset_path else "- Dataset: unknown",
        f"- Profile ID: `{profile_id}`" if profile_id else "- Profile ID: unknown",
        f"- Pair filter: `{pair_filter_text}`",
        f"- Configurations per pair: {configuration_count}",
        f"- Pairs reported: {len(pairs_payload)}",
        "",
    ]

    if not pairs_payload:
        lines.append("No benchmark pairs found.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "## Best Runs",
            "",
            "| Pair | Case Count | Run Count | Objective | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Config |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )

    sorted_pairs = sorted((str(pair), value) for pair, value in pairs_payload.items())
    for pair, pair_payload in sorted_pairs[: max(1, int(max_pairs))]:
        if not isinstance(pair_payload, dict):
            continue
        best_run = pair_payload.get("best_run")
        if not isinstance(best_run, dict):
            lines.append(f"| {pair} | 0 | 0 | - | - | - | - | - | - | missing best run |")
            continue
        summary = best_run.get("summary")
        if not isinstance(summary, dict):
            lines.append(f"| {pair} | 0 | 0 | - | - | - | - | - | - | missing summary |")
            continue
        config_label = str(best_run.get("config_label") or "")
        lines.append(
            "| "
            f"{pair} | "
            f"{int(pair_payload.get('case_count') or 0)} | "
            f"{int(pair_payload.get('run_count') or 0)} | "
            f"{float(summary.get('objective_score') or 0.0):.3f} | "
            f"{float(summary.get('top1_accuracy') or 0.0):.2%} | "
            f"{float(summary.get('top3_recall') or 0.0):.2%} | "
            f"{float(summary.get('forbidden_top1_rate') or 0.0):.2%} | "
            f"{float(summary.get('forbidden_any_rate') or 0.0):.2%} | "
            f"{float(summary.get('avg_rules_per_target') or 0.0):.2f} | "
            f"`{config_label}` |"
        )

    if len(sorted_pairs) > max(1, int(max_pairs)):
        lines.append("")
        lines.append(
            f"Showing first {max_pairs} pairs out of {len(sorted_pairs)}. Use `--max-pairs` to expand the table."
        )

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Markdown summaries from rulegen benchmark JSON."
    )
    parser.add_argument(
        "--benchmark-json", type=Path, required=True, help="Path to rulegen benchmark JSON."
    )
    parser.add_argument("--title", default="Rulegen Benchmark", help="Summary title.")
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=MAX_PAIRS,
        help="Maximum number of pair rows to include.",
    )
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(
        _load_json(args.benchmark_json),
        title=str(args.title),
        max_pairs=max(1, int(args.max_pairs)),
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
