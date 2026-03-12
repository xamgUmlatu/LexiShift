#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def _first_failed_command(payload: dict[str, Any]) -> dict[str, Any] | None:
    commands = payload.get("commands")
    if not isinstance(commands, list):
        return None
    for item in commands:
        if not isinstance(item, dict):
            continue
        exit_code = int(item.get("artifact_verification_exit_code") or item.get("exit_code") or 0)
        if exit_code != 0:
            return item
    return None


def _gate_check(path: Path) -> tuple[bool, str]:
    payload = _load_json(path)
    exit_code = int(payload.get("overall_exit_code") or 0)
    message = f"check_report overall_exit_code={exit_code}"
    failed = _first_failed_command(payload)
    if failed:
        message += f" first_failed_command={failed.get('label')}"
    return exit_code == 0, message


def _gate_build(path: Path) -> tuple[bool, str]:
    payload = _load_json(path)
    exit_code = int(payload.get("overall_exit_code") or 0)
    message = f"build_report overall_exit_code={exit_code}"
    failed = _first_failed_command(payload)
    if failed:
        message += f" first_failed_command={failed.get('label')}"
        missing = failed.get("missing_artifacts")
        if isinstance(missing, list) and missing:
            message += f" missing_artifacts={len(missing)}"
    return exit_code == 0, message


def _gate_windows_parity(path: Path) -> tuple[bool, str]:
    payload = _load_json(path)
    status = str(payload.get("status") or "UNKNOWN")
    return status == "PASS", f"windows_parity status={status}"


def _gate_rulegen_quality(path: Path) -> tuple[bool, str]:
    payload = _load_json(path)
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return False, "rulegen_quality summary_missing"
    should_fail = bool(summary.get("should_fail"))
    status = str(summary.get("status") or "UNKNOWN")
    return not should_fail, f"rulegen_quality status={status} should_fail={should_fail}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail CI jobs from JSON report artifacts after summaries/artifacts are written."
    )
    parser.add_argument("--check-json", type=Path)
    parser.add_argument("--build-json", type=Path)
    parser.add_argument("--windows-parity-json", type=Path)
    parser.add_argument("--rulegen-gate-json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evaluations: list[tuple[bool, str]] = []

    if args.check_json:
        evaluations.append(_gate_check(args.check_json))
    if args.build_json:
        evaluations.append(_gate_build(args.build_json))
    if args.windows_parity_json:
        evaluations.append(_gate_windows_parity(args.windows_parity_json))
    if args.rulegen_gate_json:
        evaluations.append(_gate_rulegen_quality(args.rulegen_gate_json))

    if not evaluations:
        raise SystemExit("No report inputs provided.")

    failures = [message for ok, message in evaluations if not ok]
    for ok, message in evaluations:
        prefix = "PASS" if ok else "FAIL"
        print(f"[{prefix}] {message}")
        if not ok and os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::error title=CI report gate::{message}")

    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
