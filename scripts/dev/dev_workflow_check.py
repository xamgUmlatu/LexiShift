#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(command: list[str]) -> int:
    print(f"+ {shlex.join(command)}", flush=True)
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return int(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the stable non-mutating repository safety checks."
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    commands = [
        ("unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "core/tests"]),
        ("mypy", [sys.executable, "-m", "mypy", "core/lexishift_core"]),
        (
            "betterdiscord_freshness",
            ["node", "apps/betterdiscord-plugin/build_plugin.js", "--check"],
        ),
        (
            "workflow_py_compile",
            [
                sys.executable,
                "-m",
                "py_compile",
                "scripts/testing/rulegen_pair_audit_cycle.py",
                "scripts/testing/rulegen_auto_audit.py",
                "scripts/testing/rulegen_quality_gate_summary.py",
                "scripts/dev/dev_workflow_check.py",
                "scripts/dev/dev_workflow_build.py",
                "scripts/dev/dev_workflow_changed_check.py",
                "scripts/dev/dev_workflow_summary.py",
                "scripts/dev/dev_workflow_style_check.py",
            ],
        ),
        ("project_health_advisory", ["node", "scripts/dev/check_project_health.js", "--advisory"]),
    ]
    results: list[dict[str, object]] = []
    overall_exit_code = 0
    for label, command in commands:
        exit_code = _run(command)
        results.append(
            {
                "label": label,
                "command": command,
                "exit_code": exit_code,
            }
        )
        if exit_code != 0:
            overall_exit_code = exit_code
            break

    payload = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_exit_code": overall_exit_code,
        "commands": results,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json_out: {args.json_out}")

    if overall_exit_code != 0:
        raise SystemExit(overall_exit_code)


if __name__ == "__main__":
    main()
