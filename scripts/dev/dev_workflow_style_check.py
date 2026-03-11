#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _print_command(command: list[str]) -> None:
    print(f"+ {shlex.join(command)}", flush=True)


def _run_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    _print_command(command)
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result


def _parse_ruff_statistics(stdout: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    pattern = re.compile(r"^(\d+)\s+([A-Za-z0-9_-]+)(?:\s+(.*))?$")
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Found "):
            continue
        match = pattern.match(line)
        if not match:
            continue
        count = int(match.group(1))
        code = str(match.group(2))
        label = str(match.group(3) or "").strip()
        items.append(
            {
                "count": count,
                "code": code,
                "label": label,
            }
        )
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run advisory repo-wide style checks separately from the default green safety loop."
        )
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if lint or format checks fail.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    lint_cmd = [sys.executable, "-m", "ruff", "check", ".", "--statistics"]
    format_cmd = [sys.executable, "-m", "ruff", "format", ".", "--check"]

    lint_result = _run_capture(lint_cmd)
    format_result = _run_capture(format_cmd)

    lint_statistics = _parse_ruff_statistics(lint_result.stdout or "")
    payload = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lint_exit_code": int(lint_result.returncode),
        "format_exit_code": int(format_result.returncode),
        "lint_statistics": lint_statistics,
        "lint_summary": (lint_result.stdout or "").strip(),
        "format_summary": (format_result.stdout or "").strip(),
        "strict": bool(args.strict),
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json_out: {args.json_out}")

    if lint_result.returncode == 0 and format_result.returncode == 0:
        print("style_status: clean")
        return

    top_items = lint_statistics[:5]
    if top_items:
        print("style_top_counts:")
        for item in top_items:
            label = str(item["label"]).strip()
            if label:
                print(f"  - {item['count']} {item['code']} {label}")
            else:
                print(f"  - {item['count']} {item['code']}")

    if format_result.stdout:
        summary_line = format_result.stdout.strip().splitlines()[-1]
        print(f"format_summary_line: {summary_line}")

    if args.strict:
        raise SystemExit(1)

    print("style_status: advisory-fail")


if __name__ == "__main__":
    main()
