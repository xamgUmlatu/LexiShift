#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

from ruff_support import resolve_ruff


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_HEALTH_BASELINE = (
    PROJECT_ROOT / "docs" / "test_outputs" / "project_health" / "project_health_baseline.json"
)
JSON_NORMALIZED_EXTENSIONS: tuple[str, ...] = (".json",)
WHITESPACE_NORMALIZED_TEXT_EXTENSIONS: tuple[str, ...] = (".md", ".txt", ".rst")
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
WINDOWS_PARITY_PATH_HINTS: tuple[str, ...] = (
    "apps/gui/packaging/pyinstaller.spec",
    "apps/gui/packaging/installer_windows.iss",
    "apps/gui/src/frozen_layout.py",
    "apps/gui/src/helper_installer.py",
    "apps/gui/src/helper_ui.py",
    "apps/gui/src/helper_tray.py",
    "scripts/build/installer.py",
    "scripts/build/validate_app_bundle.py",
    "scripts/dev/dev_workflow_build.py",
    "scripts/dev/windows_parity_audit.py",
    "scripts/dev/windows_parity_summary.py",
    "docs/developer/windows_gui_parity_workstream.md",
)
DOC_REFERENCE_TRIGGER_HINTS: tuple[str, ...] = (
    "AGENTS.md",
    "README.md",
    "docs/",
    "scripts/",
    "apps/",
    "core/",
    ".github/",
    "scripts/README.md",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements-build.txt",
    ".pre-commit-config.yaml",
)
FEATURE_STATE_MATRIX_PATH = "docs/developer/feature_state_matrix.md"


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


def _collect_changed_files(
    base_ref: str | None,
    scope: str,
    *,
    ignore_whitespace: bool = False,
) -> list[str]:
    changed: set[str] = set()
    git_commands: list[list[str]] = []
    diff_prefix = ["git", "diff"]
    if ignore_whitespace:
        diff_prefix.append("-w")
    if scope == "branch" and base_ref:
        git_commands.append(
            [*diff_prefix, "--name-only", "--diff-filter=ACMRD", f"{base_ref}...HEAD"]
        )
    if scope in {"branch", "local"}:
        git_commands.extend(
            [
                [*diff_prefix, "--name-only", "--diff-filter=ACMRD"],
                [*diff_prefix, "--name-only", "--cached", "--diff-filter=ACMRD"],
                ["git", "ls-files", "--others", "--exclude-standard"],
            ]
        )
    elif scope == "staged":
        git_commands.append([*diff_prefix, "--name-only", "--cached", "--diff-filter=ACMRD"])
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


def _matching_paths(
    changed_files: list[str],
    hints: tuple[str, ...],
    *,
    exclude_prefixes: tuple[str, ...] = (),
) -> list[str]:
    matched: list[str] = []
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if any(normalized.startswith(hint) or normalized == hint for hint in hints):
            matched.append(normalized)
    return matched


def _run_git_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _git_merge_base(base_ref: str | None) -> str | None:
    if not base_ref:
        return None
    result = _run_git_capture(["git", "merge-base", base_ref, "HEAD"])
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _git_tracked_file_text(revision: str, path: str) -> str | None:
    result = _run_git_capture(["git", "show", f"{revision}:{path}"])
    if result.returncode != 0:
        return None
    return result.stdout


def _git_index_file_text(path: str) -> str | None:
    result = _run_git_capture(["git", "show", f":{path}"])
    if result.returncode != 0:
        return None
    return result.stdout


def _python_semantics_signature(source: str) -> str | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def _python_change_is_substantive(base_source: str | None, current_source: str | None) -> bool:
    if base_source is None or current_source is None:
        return True
    base_signature = _python_semantics_signature(base_source)
    current_signature = _python_semantics_signature(current_source)
    if base_signature is None or current_signature is None:
        return True
    return base_signature != current_signature


def _json_change_is_substantive(base_source: str | None, current_source: str | None) -> bool:
    if base_source is None or current_source is None:
        return True
    try:
        base_json = json.loads(base_source)
        current_json = json.loads(current_source)
    except json.JSONDecodeError:
        return True
    return base_json != current_json


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _text_change_is_substantive(base_source: str | None, current_source: str | None) -> bool:
    if base_source is None or current_source is None:
        return True
    return _collapse_whitespace(base_source) != _collapse_whitespace(current_source)


def _current_file_text(path: str, scope: str) -> str | None:
    if scope == "staged":
        return _git_index_file_text(path)
    file_path = PROJECT_ROOT / path
    if not file_path.exists():
        return None
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _collect_substantive_changed_files(
    base_ref: str | None,
    scope: str,
    changed_files: list[str],
) -> list[str]:
    non_whitespace_changed = set(_collect_changed_files(base_ref, scope, ignore_whitespace=True))
    tracked_base_revision = "HEAD"
    if scope == "branch":
        tracked_base_revision = _git_merge_base(base_ref) or "HEAD"
    substantive: set[str] = set()
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized.endswith(".py"):
            base_source = _git_tracked_file_text(tracked_base_revision, normalized)
            current_source = _current_file_text(normalized, scope)
            is_substantive = _python_change_is_substantive(base_source, current_source)
        elif normalized.endswith(JSON_NORMALIZED_EXTENSIONS):
            base_source = _git_tracked_file_text(tracked_base_revision, normalized)
            current_source = _current_file_text(normalized, scope)
            is_substantive = _json_change_is_substantive(base_source, current_source)
        elif normalized.endswith(WHITESPACE_NORMALIZED_TEXT_EXTENSIONS):
            base_source = _git_tracked_file_text(tracked_base_revision, normalized)
            current_source = _current_file_text(normalized, scope)
            is_substantive = _text_change_is_substantive(base_source, current_source)
        else:
            is_substantive = normalized in non_whitespace_changed
        if is_substantive:
            substantive.add(normalized)
    return sorted(substantive)


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


def _needs_windows_parity(changed_files: list[str]) -> bool:
    return any(
        path.replace("\\", "/").startswith(WINDOWS_PARITY_PATH_HINTS)
        or path.replace("\\", "/") in WINDOWS_PARITY_PATH_HINTS
        for path in changed_files
    )


def _needs_feature_state_audit(changed_files: list[str]) -> bool:
    return any(path.replace("\\", "/") == FEATURE_STATE_MATRIX_PATH for path in changed_files)


def _needs_doc_reference_check(changed_files: list[str]) -> bool:
    return any(
        path.replace("\\", "/").startswith(DOC_REFERENCE_TRIGGER_HINTS)
        or path.replace("\\", "/") in DOC_REFERENCE_TRIGGER_HINTS
        for path in changed_files
    )


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
    substantive_changed_files = _collect_substantive_changed_files(
        args.base_ref,
        args.scope,
        changed_files,
    )
    changed_python_files = _changed_python_files(changed_files)
    substantive_python_files = _changed_python_files(substantive_changed_files)
    format_only_python_files = sorted(set(changed_python_files) - set(substantive_python_files))
    changed_text_files = [
        path
        for path in changed_files
        if path.endswith(JSON_NORMALIZED_EXTENSIONS + WHITESPACE_NORMALIZED_TEXT_EXTENSIONS)
    ]
    substantive_text_files = [
        path
        for path in substantive_changed_files
        if path.endswith(JSON_NORMALIZED_EXTENSIONS + WHITESPACE_NORMALIZED_TEXT_EXTENSIONS)
    ]
    format_only_text_files = sorted(set(changed_text_files) - set(substantive_text_files))
    payload: dict[str, object] = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": args.scope,
        "base_ref": args.base_ref,
        "strict_style": bool(args.strict_style),
        "run_rulegen_quality": bool(args.run_rulegen_quality),
        "changed_files_count": len(changed_files),
        "changed_files_sample": changed_files[:10],
        "substantive_changed_files_count": len(substantive_changed_files),
        "substantive_changed_files_sample": substantive_changed_files[:10],
        "changed_python_files_count": len(changed_python_files),
        "substantive_python_files_count": len(substantive_python_files),
        "format_only_python_files_count": len(format_only_python_files),
        "format_only_python_files_sample": format_only_python_files[:10],
        "format_only_text_files_count": len(format_only_text_files),
        "format_only_text_files_sample": format_only_text_files[:10],
    }
    print(f"scope: {args.scope}")
    print(f"changed_files_count: {len(changed_files)}")
    if changed_files:
        print("changed_files_sample:")
        for path in changed_files[:10]:
            print(f"  - {path}")
    print(f"substantive_changed_files_count: {len(substantive_changed_files)}")
    if substantive_changed_files:
        print("substantive_changed_files_sample:")
        for path in substantive_changed_files[:10]:
            print(f"  - {path}")
    print(f"format_only_python_files_count: {len(format_only_python_files)}")
    if format_only_python_files:
        print("format_only_python_files_sample:")
        for path in format_only_python_files[:10]:
            print(f"  - {path}")
    print(f"format_only_text_files_count: {len(format_only_text_files)}")
    if format_only_text_files:
        print("format_only_text_files_sample:")
        for path in format_only_text_files[:10]:
            print(f"  - {path}")

    project_health_command = [
        "node",
        "scripts/dev/check_project_health.js",
        "--changed-only",
        "--baseline-json",
        str(PROJECT_HEALTH_BASELINE),
        "--fail-on-new",
        "--fail-on-regressions",
        "--fail-on-new-warnings",
        "--fail-on-warning-regressions",
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

    payload["changed_python_files"] = changed_python_files
    if changed_python_files:
        print(f"changed_python_files: {len(changed_python_files)}")
        ruff = resolve_ruff()
        if not ruff.available:
            payload["style"] = {
                "lint_exit_code": 127,
                "lint_summary": "",
                "format_exit_code": 127,
                "format_summary": "",
                "status": "unavailable",
                "ruff_source": ruff.source,
                "ruff_detail": ruff.detail,
            }
            print("changed_style_status: unavailable")
            print(f"changed_style_detail: {ruff.detail}")
            if args.strict_style:
                _write_json_report(args.json_out, payload)
                raise SystemExit(1)
        else:
            lint_command = ruff.command("check", "--statistics", *changed_python_files)
            format_command = ruff.command("format", "--check", *changed_python_files)
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
                "ruff_source": ruff.source,
                "ruff_detail": ruff.detail,
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

    feature_state_trigger_files = []
    if _needs_feature_state_audit(changed_files):
        feature_state_trigger_files = [
            path for path in changed_files if path == FEATURE_STATE_MATRIX_PATH
        ]
        compare_ref = str(args.base_ref) if args.scope == "branch" else "HEAD"
        feature_state_command = [
            sys.executable,
            "scripts/dev/feature_state_audit.py",
            "--compare-ref",
            compare_ref,
        ]
        feature_state_exit_code = _run(feature_state_command, strict=False)
        payload["feature_state"] = {
            "required": True,
            "compare_ref": compare_ref,
            "trigger_files": feature_state_trigger_files,
            "command": feature_state_command,
            "exit_code": feature_state_exit_code,
        }
        if feature_state_exit_code != 0:
            _write_json_report(args.json_out, payload)
            raise SystemExit(feature_state_exit_code)
    else:
        print("feature_state_audit_required: no")
        payload["feature_state"] = {"required": False, "status": "not-needed"}

    doc_reference_trigger_files = _matching_paths(
        substantive_changed_files,
        DOC_REFERENCE_TRIGGER_HINTS,
    )
    if _needs_doc_reference_check(substantive_changed_files):
        doc_reference_command = [
            sys.executable,
            "scripts/dev/check_doc_references.py",
        ]
        doc_reference_exit_code = _run(doc_reference_command, strict=False)
        payload["doc_references"] = {
            "required": True,
            "trigger_files": doc_reference_trigger_files[:10],
            "command": doc_reference_command,
            "exit_code": doc_reference_exit_code,
        }
        if doc_reference_exit_code != 0:
            _write_json_report(args.json_out, payload)
            raise SystemExit(doc_reference_exit_code)
    else:
        print("doc_reference_check_required: no")
        payload["doc_references"] = {"required": False, "status": "not-needed"}

    betterdiscord_trigger_files = _matching_paths(changed_files, BETTERDISCORD_PATH_HINTS)
    if betterdiscord_trigger_files:
        betterdiscord_command = ["node", "apps/betterdiscord-plugin/build_plugin.js", "--check"]
        betterdiscord_exit_code = _run(betterdiscord_command, strict=False)
        payload["betterdiscord_freshness"] = {
            "required": True,
            "trigger_files": betterdiscord_trigger_files[:10],
            "command": betterdiscord_command,
            "exit_code": betterdiscord_exit_code,
        }
        if betterdiscord_exit_code != 0:
            _write_json_report(args.json_out, payload)
            raise SystemExit(betterdiscord_exit_code)
    else:
        print("betterdiscord_freshness_check: skipped")
        payload["betterdiscord_freshness"] = {"required": False, "status": "skipped"}

    windows_parity_trigger_files = _matching_paths(changed_files, WINDOWS_PARITY_PATH_HINTS)
    if windows_parity_trigger_files:
        windows_parity_command = [sys.executable, "scripts/dev/windows_parity_audit.py", "--strict"]
        windows_parity_exit_code = _run(windows_parity_command, strict=False)
        payload["windows_parity"] = {
            "required": True,
            "trigger_files": windows_parity_trigger_files[:10],
            "command": windows_parity_command,
            "exit_code": windows_parity_exit_code,
        }
        if windows_parity_exit_code != 0:
            _write_json_report(args.json_out, payload)
            raise SystemExit(windows_parity_exit_code)
    else:
        print("windows_parity_required: no")
        payload["windows_parity"] = {"required": False, "status": "not-needed"}

    rulegen_trigger_files = _matching_paths(
        substantive_changed_files,
        RULEGEN_QUALITY_PATH_HINTS,
        exclude_prefixes=RULEGEN_META_ONLY_PATHS,
    )
    if rulegen_trigger_files:
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
                "inference_basis": "substantive_changed_files",
                "trigger_files": rulegen_trigger_files[:10],
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
                "inference_basis": "substantive_changed_files",
                "trigger_files": rulegen_trigger_files[:10],
                "command": command,
                "exit_code": rulegen_exit_code,
            }
    else:
        print("rulegen_quality_required: no")
        payload["rulegen_quality"] = {"required": False, "status": "not-needed"}

    _write_json_report(args.json_out, payload)


if __name__ == "__main__":
    main()
