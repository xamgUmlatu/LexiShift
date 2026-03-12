#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def _render_status(payload: dict[str, Any]) -> str:
    lint_exit_code = int(payload.get("lint_exit_code") or 0)
    format_exit_code = int(payload.get("format_exit_code") or 0)
    strict = bool(payload.get("strict"))
    if lint_exit_code == 0 and format_exit_code == 0:
        return "PASS"
    if strict:
        return "FAIL"
    return "PASS (advisory debt)"


def _format_summary_line(payload: dict[str, Any]) -> str | None:
    summary = str(payload.get("format_summary") or "").strip()
    if not summary:
        return None
    return summary.splitlines()[-1]


def render_summary(payload: dict[str, Any], *, title: str = "Repo Style Debt") -> str:
    lines = [
        f"# {title}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Ruff Style Debt",
        f"- Status: {_render_status(payload)}",
        f"- Lint exit code: {int(payload.get('lint_exit_code') or 0)}",
        f"- Format exit code: {int(payload.get('format_exit_code') or 0)}",
    ]
    lint_statistics = payload.get("lint_statistics")
    if isinstance(lint_statistics, list) and lint_statistics:
        lines.append("- Top lint counts:")
        for item in lint_statistics[:5]:
            if not isinstance(item, dict):
                continue
            count = int(item.get("count") or 0)
            code = str(item.get("code") or "").strip() or "<unknown>"
            label = str(item.get("label") or "").strip()
            if label:
                lines.append(f"  - {count} `{code}` {label}")
            else:
                lines.append(f"  - {count} `{code}`")
    format_summary_line = _format_summary_line(payload)
    if format_summary_line:
        lines.append(f"- Format summary: {format_summary_line}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Markdown summaries from repo-wide style check JSON reports."
    )
    parser.add_argument(
        "--style-json", type=Path, required=True, help="Path to a style JSON report."
    )
    parser.add_argument("--title", default="Repo Style Debt", help="Summary title.")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(_load_json(args.style_json), title=str(args.title))
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
