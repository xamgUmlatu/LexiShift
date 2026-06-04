#!/usr/bin/env python3
from __future__ import annotations

import argparse
import plistlib
from pathlib import Path

MAIN_APP_BUNDLE = "LexiShift.app"
HELPER_APP_BUNDLE = "LexiShift Helper.app"
MAIN_BUNDLE_ID = "com.lexishift.app"
HELPER_BUNDLE_ID = "com.lexishift.helper.agent"
MAIN_WINDOWS_EXE = "LexiShift.exe"
HELPER_WINDOWS_EXE = "LexiShiftHelper.exe"
HOST_WINDOWS_EXE = "lexishift_native_host.exe"
MAIN_WINDOWS_DIR = "LexiShift"
HELPER_WINDOWS_DIR = "LexiShiftHelper"
HOST_WINDOWS_DIR = "LexiShiftNativeHost"


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
        errors.append(
            f"Unexpected bundle identifier for main app: {info.get('CFBundleIdentifier')}"
        )

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
        errors.append(
            f"Unexpected bundle identifier for helper app: {info.get('CFBundleIdentifier')}"
        )

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


def _windows_exe_candidates(dist_path: Path, exe_name: str, *, dir_name: str) -> list[Path]:
    candidates: list[Path] = [
        dist_path / dir_name / exe_name,
        dist_path / exe_name,
    ]
    candidates.extend(sorted(dist_path.glob(f"*/{exe_name}")))
    ordered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(candidate)
    return ordered


def _find_windows_exe(dist_path: Path, exe_name: str, *, dir_name: str) -> Path:
    matches = [
        candidate
        for candidate in _windows_exe_candidates(dist_path, exe_name, dir_name=dir_name)
        if candidate.exists()
    ]
    if len(matches) == 1:
        return matches[0]
    if matches:
        return matches[0]
    raise SystemExit(f"{exe_name} not found in {dist_path}")


def _validate_windows_main_exe(exe_path: Path) -> list[str]:
    errors: list[str] = []
    root = exe_path.parent
    contents_root = root / "_internal" if (root / "_internal").exists() else root
    _check_path(exe_path, "Main executable", errors)
    _check_path(contents_root / "resources", "resources root", errors)
    _check_path(contents_root / "resources" / "i18n", "i18n resources", errors)
    _check_path(contents_root / "resources" / "themes", "themes resources", errors)
    _check_path(contents_root / "resources" / "sample_images", "sample images", errors)
    _check_path(
        contents_root / "resources" / "helper" / "lexishift_native_host.py",
        "native host",
        errors,
    )
    _check_path(
        contents_root / "resources" / "helper" / "lexishift_core",
        "lexishift_core helper",
        errors,
    )
    _check_path(
        contents_root / "resources" / "helper" / "helper_daemon.py",
        "helper daemon",
        errors,
    )
    return errors


def _validate_windows_helper_exe(exe_path: Path) -> list[str]:
    errors: list[str] = []
    root = exe_path.parent
    contents_root = root / "_internal" if (root / "_internal").exists() else root
    _check_path(exe_path, "Helper executable", errors)
    _check_path(contents_root / "resources", "resources root", errors)
    _check_path(contents_root / "resources" / "i18n", "i18n resources", errors)
    _check_path(contents_root / "resources" / "ttbn.ico", "helper icon", errors)
    return errors


def _validate_windows_host_exe(exe_path: Path) -> list[str]:
    errors: list[str] = []
    _check_path(exe_path, "Native host executable", errors)
    return errors


def _validate_single_windows_exe(exe_path: Path) -> int:
    if exe_path.name == MAIN_WINDOWS_EXE:
        errors = _validate_windows_main_exe(exe_path)
    elif exe_path.name == HELPER_WINDOWS_EXE:
        errors = _validate_windows_helper_exe(exe_path)
    elif exe_path.name == HOST_WINDOWS_EXE:
        errors = _validate_windows_host_exe(exe_path)
    else:
        errors = [f"Unknown Windows executable type: {exe_path}"]

    if errors:
        for error in errors:
            _fail(error)
        return 1

    print(f"[validate] OK: {exe_path}")
    return 0


def _validate_macos_dist(dist_path: Path) -> int:
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


def _validate_windows_dist(dist_path: Path) -> int:
    try:
        main_exe = _find_windows_exe(dist_path, MAIN_WINDOWS_EXE, dir_name=MAIN_WINDOWS_DIR)
        helper_exe = _find_windows_exe(
            dist_path,
            HELPER_WINDOWS_EXE,
            dir_name=HELPER_WINDOWS_DIR,
        )
        host_exe = _find_windows_exe(dist_path, HOST_WINDOWS_EXE, dir_name=HOST_WINDOWS_DIR)
    except SystemExit as exc:
        _fail(str(exc))
        return 2

    main_rc = _validate_single_windows_exe(main_exe)
    helper_rc = _validate_single_windows_exe(helper_exe)
    host_rc = _validate_single_windows_exe(host_exe)
    if main_rc != 0 or helper_rc != 0 or host_rc != 0:
        return 1

    print(f"[validate] OK: {dist_path}")
    return 0


def _validate_dist(dist_path: Path) -> int:
    if (dist_path / MAIN_APP_BUNDLE).exists() or (dist_path / HELPER_APP_BUNDLE).exists():
        return _validate_macos_dist(dist_path)
    if any(dist_path.glob("*.exe")) or any(dist_path.glob("*/*.exe")):
        return _validate_windows_dist(dist_path)
    _fail(f"Unrecognized dist layout: {dist_path}")
    return 2


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
        if app_path.suffix.lower() == ".exe":
            return _validate_single_windows_exe(app_path)
        return _validate_single_macos_app(app_path)

    if not args.distpath:
        _fail("Provide --app or --distpath.")
        return 2

    return _validate_dist(Path(args.distpath))


if __name__ == "__main__":
    raise SystemExit(main())
