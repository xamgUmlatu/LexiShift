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

from ruff_support import resolve_ruff


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


def _write_json_report(path: Path | None, payload: dict[str, object]) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"json_out: {path}")


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

    ruff = resolve_ruff()
    payload = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "strict": bool(args.strict),
        "status": "unavailable",
        "ruff_source": ruff.source,
        "ruff_detail": ruff.detail,
    }

    if not ruff.available:
        payload.update(
            {
                "lint_exit_code": 127,
                "format_exit_code": 127,
                "lint_statistics": [],
                "lint_summary": "",
                "format_summary": "",
            }
        )
        _write_json_report(args.json_out, payload)
        print("ruff_status: unavailable")
        print(f"ruff_detail: {ruff.detail}")
        print("style_status: unavailable")
        if args.strict:
            raise SystemExit(1)
        return

    lint_cmd = ruff.command("check", ".", "--statistics")
    format_cmd = ruff.command("format", ".", "--check")

    lint_result = _run_capture(lint_cmd)
    format_result = _run_capture(format_cmd)

    lint_statistics = _parse_ruff_statistics(lint_result.stdout or "")
    payload.update(
        {
            "lint_exit_code": int(lint_result.returncode),
            "format_exit_code": int(format_result.returncode),
            "lint_statistics": lint_statistics,
            "lint_summary": (lint_result.stdout or "").strip(),
            "format_summary": (format_result.stdout or "").strip(),
        }
    )

    if lint_result.returncode == 0 and format_result.returncode == 0:
        payload["status"] = "clean"
        _write_json_report(args.json_out, payload)
        print("style_status: clean")
        return

    payload["status"] = "advisory-fail"
    _write_json_report(args.json_out, payload)

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
