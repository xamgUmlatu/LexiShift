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


def render_summary(payload: dict[str, Any], title: str = "Windows GUI Parity Audit") -> str:
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    lines = [
        f"# {title}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"- Status: {payload.get('status', 'unknown')}",
        (
            "- Counts: "
            f"PASS={int(counts.get('pass') or 0)} "
            f"WARN={int(counts.get('warn') or 0)} "
            f"FAIL={int(counts.get('fail') or 0)}"
        ),
    ]

    checks = payload.get("checks")
    if isinstance(checks, list):
        lines.extend(["", "## Checks"])
        for item in checks:
            if not isinstance(item, dict):
                continue
            title_text = str(item.get("title") or item.get("key") or "Unknown Check")
            status = str(item.get("status") or "unknown")
            summary = str(item.get("summary") or "").strip()
            lines.append(f"- `{status}` {title_text}: {summary}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Markdown summary from a Windows parity audit JSON report."
    )
    parser.add_argument("--audit-json", type=Path, required=True, help="Path to the audit JSON.")
    parser.add_argument("--title", default="Windows GUI Parity Audit", help="Summary title.")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument("--append-to", type=Path, help="Optional path to append the summary to.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(_load_json(args.audit_json), title=str(args.title))
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
