#!/usr/bin/env python3
from __future__ import annotations

import argparse
import plistlib
import sys
from pathlib import Path


def _fail(msg: str) -> None:
    print(f"[validate] {msg}")


def _check_path(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing {label}: {path}")


def _load_info_plist(info_path: Path) -> dict:
    try:
        with info_path.open("rb") as handle:
            return plistlib.load(handle)
    except Exception:
        return {}


def _validate_macos_app(app_path: Path) -> int:
    errors: list[str] = []
    contents = app_path / "Contents"
    resources = contents / "Resources"
    macos_dir = contents / "MacOS"
    info_path = contents / "Info.plist"

    _check_path(contents, "Contents dir", errors)
    _check_path(resources, "Resources dir", errors)
    _check_path(info_path, "Info.plist", errors)

    info = _load_info_plist(info_path)
    exe_name = info.get("CFBundleExecutable")
    if exe_name:
        _check_path(macos_dir / exe_name, f"Executable {exe_name}", errors)
    else:
        errors.append("Missing CFBundleExecutable in Info.plist")

    icon_name = info.get("CFBundleIconFile", "")
    if icon_name:
        _check_path(resources / icon_name, f"App icon {icon_name}", errors)

    # App resources
    resource_root = resources / "resources"
    _check_path(resource_root, "resources root", errors)
    _check_path(resource_root / "i18n", "i18n resources", errors)
    _check_path(resource_root / "themes", "themes resources", errors)
    _check_path(resource_root / "sample_images", "sample images", errors)
    _check_path(resource_root / "helper" / "lexishift_native_host.py", "native host", errors)
    _check_path(resource_root / "helper" / "lexishift_core", "lexishift_core helper", errors)
    _check_path(resource_root / "helper" / "helper_daemon.py", "helper daemon", errors)

    if errors:
        for error in errors:
            _fail(error)
        return 1

    print(f"[validate] OK: {app_path}")
    return 0


def _find_macos_app(dist_path: Path) -> Path | None:
    apps = sorted(dist_path.glob("*.app"))
    return apps[0] if apps else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LexiShift app bundle output.")
    parser.add_argument("--app", help="Path to .app bundle.")
    parser.add_argument("--distpath", help="Dist folder containing the .app.")
    args = parser.parse_args()

    app_path: Path | None = Path(args.app) if args.app else None
    if app_path is None:
        if not args.distpath:
            _fail("Provide --app or --distpath.")
            return 2
        app_path = _find_macos_app(Path(args.distpath))

    if app_path is None:
        _fail("No .app bundle found.")
        return 2

    if not app_path.exists():
        _fail(f"App not found: {app_path}")
        return 2

    return _validate_macos_app(app_path)


if __name__ == "__main__":
    raise SystemExit(main())
