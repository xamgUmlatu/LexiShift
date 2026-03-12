#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shlex
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ExpectedArtifact:
    label: str
    path: Path
    kind: str


def _run(command: list[str]) -> int:
    print(f"+ {shlex.join(command)}", flush=True)
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return int(result.returncode)


def _supports_gui_build_validate() -> bool:
    return platform.system() in {"Darwin", "Windows"}


def _find_windows_artifact_paths(project_root: Path) -> list[ExpectedArtifact]:
    dist_root = project_root / "apps" / "gui" / "dist"
    main_direct = dist_root / "LexiShift.exe"
    helper_direct = dist_root / "LexiShiftHelper.exe"
    if main_direct.exists() and helper_direct.exists():
        return [
            ExpectedArtifact("gui_main_windows_exe", main_direct, "file"),
            ExpectedArtifact("gui_helper_windows_exe", helper_direct, "file"),
        ]

    nested_specs: list[ExpectedArtifact] = []
    nested_candidates = {
        "gui_main_windows_exe": sorted(dist_root.glob("*/LexiShift.exe")),
        "gui_helper_windows_exe": sorted(dist_root.glob("*/LexiShiftHelper.exe")),
    }
    for label, matches in nested_candidates.items():
        if matches:
            nested_specs.append(ExpectedArtifact(label, matches[0], "file"))
    return nested_specs


def _artifact_specs(
    label: str, *, project_root: Path, platform_name: str
) -> list[ExpectedArtifact]:
    if label == "betterdiscord_build":
        return [
            ExpectedArtifact(
                label="betterdiscord_bundle",
                path=project_root / "apps" / "betterdiscord-plugin" / "LexiShift.plugin.js",
                kind="file",
            )
        ]
    if label == "gui_build_validate" and platform_name == "Darwin":
        main_app = project_root / "apps" / "gui" / "dist" / "LexiShift.app"
        helper_app = project_root / "apps" / "gui" / "dist" / "LexiShift Helper.app"
        return [
            ExpectedArtifact("gui_main_app_bundle", main_app, "directory"),
            ExpectedArtifact("gui_helper_app_bundle", helper_app, "directory"),
            ExpectedArtifact("gui_main_info_plist", main_app / "Contents" / "Info.plist", "file"),
            ExpectedArtifact(
                "gui_helper_info_plist",
                helper_app / "Contents" / "Info.plist",
                "file",
            ),
        ]
    if label == "gui_build_validate" and platform_name == "Windows":
        return _find_windows_artifact_paths(project_root)
    return []


def _artifact_record(spec: ExpectedArtifact) -> dict[str, object]:
    exists = spec.path.exists()
    payload: dict[str, object] = {
        "label": spec.label,
        "path": str(spec.path),
        "kind": spec.kind,
        "exists": exists,
    }
    if exists and spec.path.is_file():
        payload["size_bytes"] = spec.path.stat().st_size
    elif exists and spec.path.is_dir():
        payload["entry_count"] = sum(1 for _ in spec.path.iterdir())
    return payload


def collect_artifact_records(
    label: str, *, project_root: Path = PROJECT_ROOT, platform_name: str | None = None
) -> list[dict[str, object]]:
    resolved_platform = platform_name or platform.system()
    return [
        _artifact_record(spec)
        for spec in _artifact_specs(
            label,
            project_root=project_root,
            platform_name=resolved_platform,
        )
    ]


def _missing_artifact_paths(artifacts: list[dict[str, object]]) -> list[str]:
    return [str(item["path"]) for item in artifacts if not bool(item.get("exists"))]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run local build safeties for repo surfaces that already have stable build paths."
        )
    )
    parser.add_argument(
        "--skip-bd",
        action="store_true",
        help="Skip BetterDiscord plugin build.",
    )
    parser.add_argument(
        "--skip-gui",
        action="store_true",
        help="Skip GUI PyInstaller build + validate.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    parser.add_argument(
        "--ci-safe",
        action="store_true",
        help="Skip build surfaces that are intentionally unsupported on the current CI host.",
    )
    args = parser.parse_args()

    commands: list[tuple[str, list[str]]] = []
    skipped_commands: list[dict[str, object]] = []
    if not args.skip_bd:
        commands.append(
            ("betterdiscord_build", ["node", "apps/betterdiscord-plugin/build_plugin.js"])
        )
    if not args.skip_gui:
        if args.ci_safe and not _supports_gui_build_validate():
            skipped_commands.append(
                {
                    "label": "gui_build_validate",
                    "reason": "macOS app-bundle validation is not supported on this host",
                }
            )
        else:
            commands.append(
                ("gui_build_validate", [sys.executable, "scripts/build/gui_app.py", "--validate"])
            )

    results: list[dict[str, object]] = []
    all_artifacts: list[dict[str, object]] = []
    overall_exit_code = 0
    for label, command in commands:
        exit_code = _run(command)
        result_entry: dict[str, object] = {
            "label": label,
            "command": command,
            "exit_code": exit_code,
        }
        if exit_code == 0:
            artifacts = collect_artifact_records(label)
            if artifacts:
                result_entry["artifacts"] = artifacts
                all_artifacts.extend(artifacts)
                missing_artifacts = _missing_artifact_paths(artifacts)
                if missing_artifacts:
                    result_entry["artifact_verification_exit_code"] = 1
                    result_entry["missing_artifacts"] = missing_artifacts
                    overall_exit_code = 1
                    results.append(result_entry)
                    break
        results.append(result_entry)
        if exit_code != 0:
            overall_exit_code = exit_code
            break

    payload = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_exit_code": overall_exit_code,
        "skip_bd": bool(args.skip_bd),
        "skip_gui": bool(args.skip_gui),
        "ci_safe": bool(args.ci_safe),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "python_executable": sys.executable,
        "host_supports_gui_build_validate": _supports_gui_build_validate(),
        "skipped_commands": skipped_commands,
        "commands": results,
        "artifacts": all_artifacts,
        "expected_artifact_count": len(all_artifacts),
        "verified_artifact_count": sum(1 for item in all_artifacts if bool(item.get("exists"))),
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
