#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ParityCheck:
    key: str
    title: str
    status: str
    summary: str
    evidence: list[str]


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assess_windows_data_paths(
    helper_paths_text: str, main_paths_text: str, bootstrap_text: str
) -> ParityCheck:
    conditions = [
        "APPDATA" in helper_paths_text,
        "QStandardPaths.AppDataLocation" in main_paths_text,
        'AppData" / "Roaming"' in bootstrap_text or "AppData" in bootstrap_text,
    ]
    status = "PASS" if all(conditions) else "FAIL"
    summary = (
        "Windows AppData / Roaming path handling exists in helper and GUI startup paths."
        if status == "PASS"
        else "Windows data-path handling is missing from one or more startup/path modules."
    )
    return ParityCheck(
        key="windows_data_paths",
        title="Windows Data Paths",
        status=status,
        summary=summary,
        evidence=[
            "core/lexishift_core/helper/paths.py",
            "apps/gui/src/main_paths.py",
            "apps/gui/src/__main__.py",
        ],
    )


def assess_windows_shell_integration(
    helper_os_text: str, main_text: str, utils_paths_text: str
) -> ParityCheck:
    conditions = [
        "os.startfile" in helper_os_text,
        '["explorer", "/select,"' in main_text,
        '["explorer", "/select,"' in utils_paths_text,
    ]
    status = "PASS" if all(conditions) else "FAIL"
    summary = (
        "Windows shell integration exists for open/reveal path actions."
        if status == "PASS"
        else "Windows shell integration is incomplete for open/reveal path actions."
    )
    return ParityCheck(
        key="windows_shell_integration",
        title="Windows Shell Integration",
        status=status,
        summary=summary,
        evidence=[
            "core/lexishift_core/helper/os.py",
            "apps/gui/src/main.py",
            "apps/gui/src/utils_paths.py",
        ],
    )


def assess_windows_installer_support(installer_text: str, iss_exists: bool) -> ParityCheck:
    conditions = [
        "_build_windows_installer" in installer_text,
        "_sign_windows_installer" in installer_text,
        iss_exists,
    ]
    status = "PASS" if all(conditions) else "FAIL"
    summary = (
        "Windows installer scaffolding exists via Inno Setup and signing hooks."
        if status == "PASS"
        else "Windows installer scaffolding is incomplete."
    )
    return ParityCheck(
        key="windows_installer_support",
        title="Windows Installer Scaffolding",
        status=status,
        summary=summary,
        evidence=[
            "scripts/build/installer.py",
            "apps/gui/packaging/installer_windows.iss",
        ],
    )


def assess_windows_helper_packaging(spec_text: str) -> ParityCheck:
    helper_defined = "helper_a = Analysis(" in spec_text
    platform_branch = spec_text.rsplit('if sys.platform == "darwin":', 1)[-1]
    spec_after_else = platform_branch.split("else:", 1)[-1] if "else:" in platform_branch else ""
    windows_else = "coll = COLLECT(" in spec_after_else
    windows_helper_branch = any(
        marker in spec_after_else
        for marker in ("helper_a = Analysis(", "helper_pyz = PYZ(", "helper_app = BUNDLE(")
    )
    if helper_defined and windows_else and not windows_helper_branch:
        status = "FAIL"
        summary = (
            "PyInstaller packaging only builds the helper app in the macOS branch; "
            "Windows packaging currently emits the main app only."
        )
    else:
        status = "PASS"
        summary = "PyInstaller packaging includes Windows helper parity."
    return ParityCheck(
        key="windows_helper_packaging",
        title="Windows Helper Packaging",
        status=status,
        summary=summary,
        evidence=["apps/gui/packaging/pyinstaller.spec"],
    )


def assess_windows_bundle_validation(validator_text: str) -> ParityCheck:
    has_windows_branch = ".exe" in validator_text or "win32" in validator_text.lower()
    mac_only_shapes = ".app" in validator_text and "Info.plist" in validator_text
    if mac_only_shapes and not has_windows_branch:
        status = "FAIL"
        summary = (
            "Build output validation is macOS-only today; there is no Windows dist/exe validator."
        )
    else:
        status = "PASS"
        summary = "Build output validation includes Windows checks."
    return ParityCheck(
        key="windows_bundle_validation",
        title="Windows Build Validation",
        status=status,
        summary=summary,
        evidence=["scripts/build/validate_app_bundle.py"],
    )


def assess_windows_helper_autostart(helper_installer_text: str, checklist_text: str) -> ParityCheck:
    has_windows_autostart = any(
        marker in helper_installer_text.lower()
        for marker in ("winreg", "schtasks", "startup", "currentversion\\run")
    )
    mac_launch_agent = "launch_agent_path" in helper_installer_text
    checklist_has_macos = "Start helper tray at login on macOS" in checklist_text
    if mac_launch_agent and checklist_has_macos and not has_windows_autostart:
        status = "FAIL"
        summary = (
            "Helper autostart is implemented for macOS LaunchAgent only; "
            "no Windows startup-registration path is tracked in code."
        )
    else:
        status = "PASS"
        summary = "Helper autostart includes a Windows path."
    return ParityCheck(
        key="windows_helper_autostart",
        title="Windows Helper Autostart",
        status=status,
        summary=summary,
        evidence=[
            "apps/gui/src/helper_installer.py",
            "docs/architecture/native_messaging_checklist.md",
        ],
    )


def assess_windows_tray_launch(helper_tray_text: str) -> ParityCheck:
    try:
        open_main_block = helper_tray_text.split("def _open_main_app()", 1)[1].split(
            "\n\nclass HelperTrayController", 1
        )[0]
    except IndexError:
        open_main_block = helper_tray_text
    has_windows_launch = 'SYS.platform.startswith("win")' in open_main_block
    has_macos_launch = 'SYS.platform == "darwin"' in open_main_block
    if has_macos_launch and not has_windows_launch:
        status = "FAIL"
        summary = (
            "Frozen helper tray launch has macOS-specific app-bundle handoff, "
            "but no Windows-specific main-app launch path."
        )
    else:
        status = "PASS"
        summary = "Frozen helper tray launch includes Windows-specific handling."
    return ParityCheck(
        key="windows_tray_launch",
        title="Windows Tray Launch Path",
        status=status,
        summary=summary,
        evidence=["apps/gui/src/helper_tray.py"],
    )


def assess_hosted_windows_validation(ci_text: str) -> ParityCheck:
    has_windows_runner = "runs-on: windows-latest" in ci_text
    status = "PASS" if has_windows_runner else "FAIL"
    summary = (
        "Hosted CI includes a Windows runner for parity reporting."
        if status == "PASS"
        else "Hosted CI has no Windows runner yet for build/parity reporting."
    )
    return ParityCheck(
        key="hosted_windows_validation",
        title="Hosted Windows Validation",
        status=status,
        summary=summary,
        evidence=[".github/workflows/ci.yml"],
    )


def _overall_status(checks: Iterable[ParityCheck]) -> str:
    statuses = [check.status for check in checks]
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def build_audit(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    helper_paths_text = _load_text(project_root / "core" / "lexishift_core" / "helper" / "paths.py")
    main_paths_text = _load_text(project_root / "apps" / "gui" / "src" / "main_paths.py")
    bootstrap_text = _load_text(project_root / "apps" / "gui" / "src" / "__main__.py")
    helper_os_text = _load_text(project_root / "core" / "lexishift_core" / "helper" / "os.py")
    main_text = _load_text(project_root / "apps" / "gui" / "src" / "main.py")
    utils_paths_text = _load_text(project_root / "apps" / "gui" / "src" / "utils_paths.py")
    installer_text = _load_text(project_root / "scripts" / "build" / "installer.py")
    spec_text = _load_text(project_root / "apps" / "gui" / "packaging" / "pyinstaller.spec")
    validator_text = _load_text(project_root / "scripts" / "build" / "validate_app_bundle.py")
    helper_installer_text = _load_text(
        project_root / "apps" / "gui" / "src" / "helper_installer.py"
    )
    checklist_text = _load_text(
        project_root / "docs" / "architecture" / "native_messaging_checklist.md"
    )
    helper_tray_text = _load_text(project_root / "apps" / "gui" / "src" / "helper_tray.py")
    ci_text = _load_text(project_root / ".github" / "workflows" / "ci.yml")

    checks = [
        assess_windows_data_paths(helper_paths_text, main_paths_text, bootstrap_text),
        assess_windows_shell_integration(helper_os_text, main_text, utils_paths_text),
        assess_windows_installer_support(
            installer_text,
            (project_root / "apps" / "gui" / "packaging" / "installer_windows.iss").exists(),
        ),
        assess_windows_helper_packaging(spec_text),
        assess_windows_bundle_validation(validator_text),
        assess_windows_helper_autostart(helper_installer_text, checklist_text),
        assess_windows_tray_launch(helper_tray_text),
        assess_hosted_windows_validation(ci_text),
    ]

    status = _overall_status(checks)
    counts = {
        "pass": sum(1 for check in checks if check.status == "PASS"),
        "warn": sum(1 for check in checks if check.status == "WARN"),
        "fail": sum(1 for check in checks if check.status == "FAIL"),
    }
    return {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "counts": counts,
        "checks": [asdict(check) for check in checks],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the current Windows GUI parity state from code and workflow evidence."
    )
    parser.add_argument("--json-out", type=Path, help="Optional JSON output path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when the audit status is FAIL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_audit()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"json_out: {args.json_out}")
    print(f"status: {payload['status']}")
    counts = payload["counts"]
    print(f"counts: pass={counts['pass']} warn={counts['warn']} fail={counts['fail']}")
    if args.strict and payload["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
