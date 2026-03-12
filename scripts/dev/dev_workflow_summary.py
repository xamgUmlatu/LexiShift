#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def _passed_command_count(payload: dict[str, Any]) -> tuple[int, int]:
    commands = payload.get("commands")
    if not isinstance(commands, list):
        return 0, 0
    total = 0
    passed = 0
    for item in commands:
        if not isinstance(item, dict):
            continue
        total += 1
        if _command_status_exit_code(item) == 0:
            passed += 1
    return passed, total


def _command_status_exit_code(item: dict[str, Any]) -> int:
    exit_code = int(item.get("exit_code") or 0)
    if exit_code != 0:
        return exit_code
    return int(item.get("artifact_verification_exit_code") or 0)


def _first_failed_command(payload: dict[str, Any]) -> str | None:
    commands = payload.get("commands")
    if not isinstance(commands, list):
        return None
    for item in commands:
        if not isinstance(item, dict):
            continue
        if _command_status_exit_code(item) != 0:
            label = str(item.get("label") or "").strip()
            return label or None
    return None


def _extract_lint_error_count(text: str) -> int | None:
    match = re.search(r"Found\s+(\d+)\s+errors?\.", text)
    if not match:
        return None
    return int(match.group(1))


def _extract_reformat_count(text: str) -> int | None:
    match = re.search(r"(\d+)\s+files?\s+would be reformatted", text)
    if not match:
        return None
    return int(match.group(1))


def _bool_status(exit_code: int) -> str:
    return "PASS" if exit_code == 0 else "FAIL"


def _render_check_section(payload: dict[str, Any]) -> list[str]:
    passed, total = _passed_command_count(payload)
    overall_exit_code = int(payload.get("overall_exit_code") or 0)
    lines = [
        "## Repo Safety",
        f"- Status: {_bool_status(overall_exit_code)}",
        f"- Commands passed: {passed}/{total}",
    ]
    failed = _first_failed_command(payload)
    if failed:
        lines.append(f"- First failed command: `{failed}`")
    return lines


def _render_changed_section(payload: dict[str, Any]) -> list[str]:
    style = payload.get("style")
    style_status = ""
    lint_errors: int | None = None
    reformats: int | None = None
    if isinstance(style, dict):
        style_status = str(style.get("status") or "").strip()
        lint_errors = _extract_lint_error_count(str(style.get("lint_summary") or ""))
        reformats = _extract_reformat_count(str(style.get("format_summary") or ""))
    status = "PASS"
    if style_status == "advisory-fail":
        status = "PASS (advisory style debt)"
    project_health = payload.get("project_health")
    project_health_status = "unknown"
    if isinstance(project_health, dict):
        project_health_status = _bool_status(int(project_health.get("exit_code") or 0))
    changed_python_files = payload.get("changed_python_files")
    changed_python_count = (
        len(changed_python_files) if isinstance(changed_python_files, list) else 0
    )
    lines = [
        "## Changed Scope",
        f"- Status: {status}",
        f"- Scope: `{payload.get('scope', 'unknown')}` (`{payload.get('base_ref', '')}`)",
        f"- Changed files: {int(payload.get('changed_files_count') or 0)}",
        f"- Substantive changed files: {int(payload.get('substantive_changed_files_count') or 0)}",
        f"- Project health: {project_health_status}",
        f"- Changed Python files: {changed_python_count}",
    ]
    if style_status:
        style_line = f"- Style: `{style_status}`"
        details: list[str] = []
        if lint_errors is not None:
            details.append(f"{lint_errors} lint errors")
        if reformats is not None:
            details.append(f"{reformats} files need formatting")
        if details:
            style_line += f" ({', '.join(details)})"
        lines.append(style_line)
    betterdiscord = payload.get("betterdiscord_freshness")
    if isinstance(betterdiscord, dict):
        required = bool(betterdiscord.get("required"))
        if required:
            lines.append(
                f"- BetterDiscord freshness: {_bool_status(int(betterdiscord.get('exit_code') or 0))}"
            )
        else:
            lines.append("- BetterDiscord freshness: skipped")
    feature_state = payload.get("feature_state")
    if isinstance(feature_state, dict):
        if bool(feature_state.get("required")):
            compare_ref = str(feature_state.get("compare_ref") or "unknown")
            exit_code = int(feature_state.get("exit_code") or 0)
            lines.append(
                f"- Feature-state audit: required (`{compare_ref}`), {_bool_status(exit_code)}"
            )
        else:
            lines.append("- Feature-state audit: not required")
    windows_parity = payload.get("windows_parity")
    if isinstance(windows_parity, dict):
        if bool(windows_parity.get("required")):
            exit_code = int(windows_parity.get("exit_code") or 0)
            lines.append(f"- Windows parity: required, {_bool_status(exit_code)}")
        else:
            lines.append("- Windows parity: not required")
    rulegen = payload.get("rulegen_quality")
    if isinstance(rulegen, dict):
        if bool(rulegen.get("required")):
            mode = str(rulegen.get("mode") or "unknown")
            exit_code = int(rulegen.get("exit_code") or 0)
            inference_basis = str(rulegen.get("inference_basis") or "").strip()
            line = f"- Rulegen quality: required (`{mode}`), {_bool_status(exit_code)}"
            if inference_basis:
                line += f" via `{inference_basis}`"
            lines.append(line)
        else:
            lines.append("- Rulegen quality: not required")
    return lines


def _render_build_section(payload: dict[str, Any]) -> list[str]:
    passed, total = _passed_command_count(payload)
    overall_exit_code = int(payload.get("overall_exit_code") or 0)
    skipped = payload.get("skipped_commands")
    skipped_items = skipped if isinstance(skipped, list) else []
    expected_artifact_count = int(payload.get("expected_artifact_count") or 0)
    verified_artifact_count = int(payload.get("verified_artifact_count") or 0)
    status = _bool_status(overall_exit_code)
    if overall_exit_code == 0 and bool(payload.get("ci_safe")) and skipped_items:
        status = "PASS (ci-safe partial)"
    lines = [
        "## Build Safety",
        f"- Status: {status}",
        f"- Platform: `{payload.get('platform', 'unknown')}`",
        f"- Commands passed: {passed}/{total}",
    ]
    if expected_artifact_count > 0:
        lines.append(f"- Verified artifacts: {verified_artifact_count}/{expected_artifact_count}")
    failed = _first_failed_command(payload)
    if failed:
        lines.append(f"- First failed command: `{failed}`")
    if skipped_items:
        for item in skipped_items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip() or "<unknown>"
            reason = str(item.get("reason") or "").strip() or "no reason provided"
            lines.append(f"- Skipped: `{label}` ({reason})")
    return lines


def render_summary(
    *,
    check_payload: dict[str, Any] | None = None,
    changed_payload: dict[str, Any] | None = None,
    build_payload: dict[str, Any] | None = None,
    title: str = "Development Workflow Summary",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
    ]
    if check_payload:
        lines.extend(["", *_render_check_section(check_payload)])
    if changed_payload:
        lines.extend(["", *_render_changed_section(changed_payload)])
    if build_payload:
        lines.extend(["", *_render_build_section(build_payload)])
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Markdown summaries from workflow JSON reports."
    )
    parser.add_argument("--check-json", type=Path, help="Path to a repo safety JSON report.")
    parser.add_argument("--changed-json", type=Path, help="Path to a changed-scope JSON report.")
    parser.add_argument("--build-json", type=Path, help="Path to a build safety JSON report.")
    parser.add_argument("--title", default="Development Workflow Summary", help="Summary title.")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(
        check_payload=_load_json(args.check_json),
        changed_payload=_load_json(args.changed_json),
        build_payload=_load_json(args.build_json),
        title=str(args.title),
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
