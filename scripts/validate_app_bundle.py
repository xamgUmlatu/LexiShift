#!/usr/bin/env python3
from __future__ import annotations

import argparse
import plistlib
from pathlib import Path

MAIN_APP_BUNDLE = "LexiShift.app"
HELPER_APP_BUNDLE = "LexiShift Helper.app"
MAIN_BUNDLE_ID = "com.lexishift.app"
HELPER_BUNDLE_ID = "com.lexishift.helper.agent"


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


def _validate_macos_main_app(app_path: Path) -> list[str]:
    errors: list[str] = []
    contents = app_path / "Contents"
    resources = contents / "Resources"
    macos_dir = contents / "MacOS"
    info_path = contents / "Info.plist"

    _check_path(contents, "Contents dir", errors)
    _check_path(resources, "Resources dir", errors)
    _check_path(info_path, "Info.plist", errors)

    info = _load_info_plist(info_path)
    if info.get("CFBundleIdentifier") != MAIN_BUNDLE_ID:
        errors.append(f"Unexpected bundle identifier for main app: {info.get('CFBundleIdentifier')}")

    exe_name = info.get("CFBundleExecutable")
    if exe_name:
        _check_path(macos_dir / exe_name, f"Executable {exe_name}", errors)
    else:
        errors.append("Missing CFBundleExecutable in Info.plist")

    icon_name = info.get("CFBundleIconFile", "")
    if icon_name:
        _check_path(resources / icon_name, f"App icon {icon_name}", errors)

    resource_root = resources / "resources"
    _check_path(resource_root, "resources root", errors)
    _check_path(resource_root / "i18n", "i18n resources", errors)
    _check_path(resource_root / "themes", "themes resources", errors)
    _check_path(resource_root / "sample_images", "sample images", errors)
    _check_path(resource_root / "helper" / "lexishift_native_host.py", "native host", errors)
    _check_path(resource_root / "helper" / "lexishift_core", "lexishift_core helper", errors)
    _check_path(resource_root / "helper" / "helper_daemon.py", "helper daemon", errors)
    return errors


def _validate_macos_helper_app(app_path: Path) -> list[str]:
    errors: list[str] = []
    contents = app_path / "Contents"
    resources = contents / "Resources"
    macos_dir = contents / "MacOS"
    info_path = contents / "Info.plist"

    _check_path(contents, "Contents dir", errors)
    _check_path(resources, "Resources dir", errors)
    _check_path(info_path, "Info.plist", errors)

    info = _load_info_plist(info_path)
    if info.get("CFBundleIdentifier") != HELPER_BUNDLE_ID:
        errors.append(f"Unexpected bundle identifier for helper app: {info.get('CFBundleIdentifier')}")

    exe_name = info.get("CFBundleExecutable")
    if exe_name:
        _check_path(macos_dir / exe_name, f"Executable {exe_name}", errors)
    else:
        errors.append("Missing CFBundleExecutable in helper Info.plist")

    icon_name = info.get("CFBundleIconFile", "")
    if icon_name:
        _check_path(resources / icon_name, f"Helper icon {icon_name}", errors)

    lsui_element = str(info.get("LSUIElement", "")).lower()
    if lsui_element not in {"1", "true", "yes"}:
        errors.append("Helper app must be an agent app (LSUIElement=true).")

    _check_path(resources / "resources" / "ttbn.icns", "helper bundled icon", errors)
    return errors


def _validate_single_macos_app(app_path: Path) -> int:
    info = _load_info_plist(app_path / "Contents" / "Info.plist")
    bundle_id = info.get("CFBundleIdentifier")

    if bundle_id == MAIN_BUNDLE_ID or app_path.name == MAIN_APP_BUNDLE:
        errors = _validate_macos_main_app(app_path)
    elif bundle_id == HELPER_BUNDLE_ID or app_path.name == HELPER_APP_BUNDLE:
        errors = _validate_macos_helper_app(app_path)
    else:
        errors = [f"Unknown app bundle type: {app_path} (bundle id: {bundle_id})"]

    if errors:
        for error in errors:
            _fail(error)
        return 1

    print(f"[validate] OK: {app_path}")
    return 0


def _validate_dist(dist_path: Path) -> int:
    main_app = dist_path / MAIN_APP_BUNDLE
    helper_app = dist_path / HELPER_APP_BUNDLE

    if not main_app.exists():
        _fail(f"Main app not found: {main_app}")
        return 2
    if not helper_app.exists():
        _fail(f"Helper app not found: {helper_app}")
        return 2

    main_rc = _validate_single_macos_app(main_app)
    helper_rc = _validate_single_macos_app(helper_app)
    if main_rc != 0 or helper_rc != 0:
        return 1

    print(f"[validate] OK: {dist_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LexiShift app bundle output.")
    parser.add_argument("--app", help="Path to .app bundle.")
    parser.add_argument("--distpath", help="Dist folder containing app bundles.")
    args = parser.parse_args()

    app_path: Path | None = Path(args.app) if args.app else None
    if app_path is not None:
        if not app_path.exists():
            _fail(f"App not found: {app_path}")
            return 2
        return _validate_single_macos_app(app_path)

    if not args.distpath:
        _fail("Provide --app or --distpath.")
        return 2

    return _validate_dist(Path(args.distpath))


if __name__ == "__main__":
    raise SystemExit(main())
