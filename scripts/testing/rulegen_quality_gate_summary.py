#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def render_summary(
    payload: dict[str, Any],
    *,
    title: str = "Rulegen Quality Gate",
    max_findings: int = 10,
) -> str:
    summary = payload.get("summary")
    findings = payload.get("findings")
    if not isinstance(summary, dict):
        raise SystemExit("Gate JSON does not contain a 'summary' object.")
    if not isinstance(findings, list):
        raise SystemExit("Gate JSON does not contain a 'findings' list.")

    status = str(summary.get("status") or "UNKNOWN")
    pass_count = int(summary.get("pass_count") or 0)
    warn_count = int(summary.get("warn_count") or 0)
    fail_count = int(summary.get("fail_count") or 0)

    lines = [
        f"# {title}",
        "",
        f"- Status: {status}",
        f"- Findings: pass={pass_count} warn={warn_count} fail={fail_count}",
        f"- Fail on warn: {'yes' if bool(payload.get('fail_on_warn')) else 'no'}",
        f"- Strict saturation: {'yes' if bool(payload.get('strict_saturation')) else 'no'}",
        f"- Benchmark JSON: `{payload.get('benchmark_json', '')}`",
        f"- Policy JSON: `{payload.get('policy_json', '')}`",
    ]
    pair_scope = str(payload.get("pair_scope") or "").strip()
    if pair_scope:
        lines.append(f"- Pair scope: `{pair_scope}`")

    actionable = [
        item
        for item in findings
        if isinstance(item, dict) and str(item.get("level") or "") in {"FAIL", "WARN"}
    ]
    if actionable:
        lines.extend(["", "## Actionable Findings"])
        for index, item in enumerate(actionable[:max_findings], start=1):
            level = str(item.get("level") or "")
            code = str(item.get("code") or "")
            message = str(item.get("message") or "")
            lines.append(f"{index}. [{level}] `{code}`: {message}")
            details = str(item.get("details") or "").strip()
            if details:
                for detail_line in details.splitlines():
                    lines.append(f"   - {detail_line}")
    else:
        lines.extend(["", "## Actionable Findings", "None."])

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Markdown summaries from rulegen quality gate JSON."
    )
    parser.add_argument(
        "--gate-json", type=Path, required=True, help="Path to rulegen quality gate JSON."
    )
    parser.add_argument("--title", default="Rulegen Quality Gate", help="Summary title.")
    parser.add_argument(
        "--max-findings",
        type=int,
        default=10,
        help="Maximum number of FAIL/WARN findings to include.",
    )
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(
        _load_json(args.gate_json),
        title=str(args.title),
        max_findings=int(args.max_findings),
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
