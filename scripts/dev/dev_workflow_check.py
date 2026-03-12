#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_TAIL_LINE_LIMIT = 20


def _tail_lines(text: str, *, limit: int = OUTPUT_TAIL_LINE_LIMIT) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if len(lines) <= limit:
        return lines
    return lines[-limit:]


def _run(command: list[str]) -> dict[str, Any]:
    print(f"+ {shlex.join(command)}", flush=True)
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
    payload: dict[str, Any] = {
        "exit_code": int(result.returncode),
    }
    stdout_tail = _tail_lines(result.stdout or "")
    stderr_tail = _tail_lines(result.stderr or "")
    if stdout_tail:
        payload["stdout_tail"] = stdout_tail
    if stderr_tail:
        payload["stderr_tail"] = stderr_tail
    return payload


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


def build_commands() -> list[tuple[str, list[str]]]:
    return [
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
                "scripts/dev/feature_state_audit.py",
                "scripts/dev/ci_report_gate.py",
                "scripts/testing/rulegen_pair_audit_cycle.py",
                "scripts/testing/rulegen_auto_audit.py",
                "scripts/testing/rulegen_benchmark_summary.py",
                "scripts/testing/rulegen_benchmark_triage_summary.py",
                "scripts/testing/rulegen_quality_gate_summary.py",
                "scripts/testing/srs_quality_harness.py",
                "scripts/testing/srs_quality_summary.py",
                "scripts/dev/dev_workflow_check.py",
                "scripts/dev/dev_workflow_build.py",
                "scripts/dev/dev_workflow_changed_check.py",
                "scripts/dev/dev_workflow_summary.py",
                "scripts/dev/dev_workflow_style_check.py",
                "scripts/dev/dev_workflow_style_summary.py",
                "scripts/dev/windows_parity_audit.py",
                "scripts/dev/windows_parity_summary.py",
            ],
        ),
        (
            "feature_state_audit",
            [sys.executable, "scripts/dev/feature_state_audit.py", "--compare-ref", "HEAD"],
        ),
        (
            "windows_parity_audit",
            [sys.executable, "scripts/dev/windows_parity_audit.py", "--strict"],
        ),
        (
            "repo_style_strict",
            [sys.executable, "scripts/dev/dev_workflow_style_check.py", "--strict"],
        ),
        ("project_health_advisory", ["node", "scripts/dev/check_project_health.js", "--advisory"]),
    ]


def main() -> None:
    args = parse_args()
    commands = build_commands()
    results: list[dict[str, object]] = []
    overall_exit_code = 0
    for label, command in commands:
        command_result = _run(command)
        exit_code = int(command_result["exit_code"])
        result_entry: dict[str, object] = {
            "label": label,
            "command": command,
            "exit_code": exit_code,
        }
        stdout_tail = command_result.get("stdout_tail")
        stderr_tail = command_result.get("stderr_tail")
        if isinstance(stdout_tail, list) and stdout_tail:
            result_entry["stdout_tail"] = stdout_tail
        if isinstance(stderr_tail, list) and stderr_tail:
            result_entry["stderr_tail"] = stderr_tail
        results.append(result_entry)
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
