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
PROJECT_HEALTH_BASELINE = (
    PROJECT_ROOT / "docs" / "test_outputs" / "project_health" / "project_health_baseline.json"
)
BETTERDISCORD_PATH_HINTS: tuple[str, ...] = (
    "apps/betterdiscord-plugin/src/",
    "apps/chrome-extension/content/processing/tokenizer.js",
    "apps/chrome-extension/content/processing/matcher.js",
    "apps/chrome-extension/shared/language/language_prefs.js",
    "apps/betterdiscord-plugin/build_plugin.js",
)
RULEGEN_META_ONLY_PATHS: tuple[str, ...] = (
    "scripts/testing/rulegen_pair_audit_cycle.py",
    "scripts/testing/rulegen_auto_audit.py",
    "docs/developer/",
)
RULEGEN_QUALITY_PATH_HINTS: tuple[str, ...] = (
    "core/lexishift_core/rulegen/",
    "core/lexishift_core/pos/",
    "core/lexishift_core/resources/dict_loaders.py",
    "core/lexishift_core/helper/rulegen.py",
    "core/lexishift_core/helper/use_cases/rulegen_job.py",
    "core/tests/rulegen/",
    "docs/rulegen/",
    "docs/test_inputs/rulegen_",
    "scripts/testing/rulegen_benchmark.py",
    "scripts/testing/rulegen_quality_gate.py",
    "scripts/testing/rulegen_quality_gate_",
    "scripts/testing/rulegen_benchmark_triage.py",
)


def _print_command(command: list[str]) -> None:
    print(f"+ {shlex.join(command)}", flush=True)


def _run(command: list[str], *, strict: bool = True) -> int:
    _print_command(command)
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if strict and result.returncode != 0:
        raise SystemExit(result.returncode)
    return int(result.returncode)


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


def _collect_changed_files(base_ref: str | None, scope: str) -> list[str]:
    changed: set[str] = set()
    git_commands: list[list[str]] = []
    if scope == "branch" and base_ref:
        git_commands.append(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"]
        )
    if scope in {"branch", "local"}:
        git_commands.extend(
            [
                ["git", "diff", "--name-only", "--diff-filter=ACMR"],
                ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
                ["git", "ls-files", "--others", "--exclude-standard"],
            ]
        )
    elif scope == "staged":
        git_commands.append(["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"])
    for command in git_commands:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            continue
        for raw_line in result.stdout.splitlines():
            normalized = raw_line.replace("\\", "/").strip()
            if normalized:
                changed.add(normalized)
    return sorted(changed)


def _changed_python_files(changed_files: list[str]) -> list[str]:
    return [
        path for path in changed_files if path.endswith(".py") and (PROJECT_ROOT / path).exists()
    ]


def _needs_betterdiscord_freshness(changed_files: list[str]) -> bool:
    return any(
        path.replace("\\", "/").startswith(BETTERDISCORD_PATH_HINTS)
        or path.replace("\\", "/") in BETTERDISCORD_PATH_HINTS
        for path in changed_files
    )


def _needs_rulegen_quality(changed_files: list[str]) -> bool:
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized.startswith(RULEGEN_META_ONLY_PATHS):
            continue
        if normalized.startswith(RULEGEN_QUALITY_PATH_HINTS):
            return True
    return False


def _write_json_report(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
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
            "Run changed-scope workflow checks and show whether heavier quality loops are required."
        )
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref used for changed-scope checks (default: origin/main).",
    )
    parser.add_argument(
        "--scope",
        choices=("branch", "local", "staged"),
        default="branch",
        help="Changed-file scope: branch diff + local changes, local working tree only, or staged only.",
    )
    parser.add_argument(
        "--strict-style",
        action="store_true",
        help="Fail when changed Python files do not pass Ruff lint/format checks.",
    )
    parser.add_argument(
        "--run-rulegen-quality",
        action="store_true",
        help="Run the inferred rulegen quality loop instead of only printing the dry-run command.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    changed_files = _collect_changed_files(args.base_ref, args.scope)
    payload: dict[str, object] = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": args.scope,
        "base_ref": args.base_ref,
        "strict_style": bool(args.strict_style),
        "run_rulegen_quality": bool(args.run_rulegen_quality),
        "changed_files_count": len(changed_files),
        "changed_files_sample": changed_files[:10],
    }
    print(f"scope: {args.scope}")
    print(f"changed_files_count: {len(changed_files)}")
    if changed_files:
        print("changed_files_sample:")
        for path in changed_files[:10]:
            print(f"  - {path}")

    project_health_command = [
        "node",
        "scripts/dev/check_project_health.js",
        "--changed-only",
        "--baseline-json",
        str(PROJECT_HEALTH_BASELINE),
        "--fail-on-new",
        "--fail-on-regressions",
    ] + (
        ["--base-ref", str(args.base_ref)]
        if args.scope == "branch"
        else ["--staged"]
        if args.scope == "staged"
        else []
    )
    project_health_exit_code = _run(project_health_command, strict=False)
    payload["project_health"] = {
        "command": project_health_command,
        "exit_code": project_health_exit_code,
    }
    if project_health_exit_code != 0:
        _write_json_report(args.json_out, payload)
        raise SystemExit(project_health_exit_code)

    changed_python_files = _changed_python_files(changed_files)
    payload["changed_python_files"] = changed_python_files
    if changed_python_files:
        print(f"changed_python_files: {len(changed_python_files)}")
        lint_command = [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--statistics",
            *changed_python_files,
        ]
        format_command = [sys.executable, "-m", "ruff", "format", "--check", *changed_python_files]
        lint_result = _run_capture(lint_command)
        format_result = _run_capture(format_command)
        style_clean = lint_result.returncode == 0 and format_result.returncode == 0
        payload["style"] = {
            "lint_command": lint_command,
            "lint_exit_code": int(lint_result.returncode),
            "lint_summary": (lint_result.stdout or "").strip(),
            "format_command": format_command,
            "format_exit_code": int(format_result.returncode),
            "format_summary": (format_result.stdout or "").strip(),
            "status": "clean" if style_clean else "advisory-fail",
        }
        if args.strict_style and (lint_result.returncode != 0 or format_result.returncode != 0):
            _write_json_report(args.json_out, payload)
            raise SystemExit(1)
        if not style_clean:
            print("changed_style_status: advisory-fail")
        else:
            print("changed_style_status: clean")
    else:
        print("changed_python_files: 0")
        payload["style"] = {"status": "skipped"}

    if _needs_betterdiscord_freshness(changed_files):
        betterdiscord_command = ["node", "apps/betterdiscord-plugin/build_plugin.js", "--check"]
        betterdiscord_exit_code = _run(betterdiscord_command, strict=False)
        payload["betterdiscord_freshness"] = {
            "required": True,
            "command": betterdiscord_command,
            "exit_code": betterdiscord_exit_code,
        }
        if betterdiscord_exit_code != 0:
            _write_json_report(args.json_out, payload)
            raise SystemExit(betterdiscord_exit_code)
    else:
        print("betterdiscord_freshness_check: skipped")
        payload["betterdiscord_freshness"] = {"required": False, "status": "skipped"}

    if _needs_rulegen_quality(changed_files):
        print("rulegen_quality_required: yes")
        command = [
            sys.executable,
            "scripts/testing/rulegen_auto_audit.py",
        ]
        if args.scope == "branch":
            command.extend(["--base-ref", str(args.base_ref)])
        elif args.scope == "local":
            command.extend(["--base-ref", ""])
        if args.run_rulegen_quality:
            command.append("--strict-gate")
            rulegen_exit_code = _run(command, strict=False)
            payload["rulegen_quality"] = {
                "required": True,
                "mode": "run",
                "command": command,
                "exit_code": rulegen_exit_code,
            }
            if rulegen_exit_code != 0:
                _write_json_report(args.json_out, payload)
                raise SystemExit(rulegen_exit_code)
        else:
            command.append("--dry-run")
            rulegen_exit_code = _run(command, strict=False)
            payload["rulegen_quality"] = {
                "required": True,
                "mode": "dry-run",
                "command": command,
                "exit_code": rulegen_exit_code,
            }
    else:
        print("rulegen_quality_required: no")
        payload["rulegen_quality"] = {"required": False, "status": "not-needed"}

    _write_json_report(args.json_out, payload)


if __name__ == "__main__":
    main()
