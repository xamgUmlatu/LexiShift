#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_spec_values(spec_path: Path) -> dict[str, str]:
    data = spec_path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for key in ("APP_NAME", "APP_PRODUCT_NAME", "APP_BUNDLE_ID"):
        match = re.search(rf"^{key}\\s*=\\s*\"([^\"]+)\"", data, re.MULTILINE)
        if match:
            values[key] = match.group(1)
    version_match = re.search(r"CFBundleShortVersionString\"\\s*:\\s*\"([^\"]+)\"", data)
    if version_match:
        values["APP_VERSION"] = version_match.group(1)
    return values


def _run_build_gui(
    repo_root: Path, spec_path: Path, dist_dir: Path, build_dir: Path, *, validate: bool
) -> None:
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "build_gui_app.py"),
        "--spec",
        str(spec_path),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
    ]
    if validate:
        cmd.append("--validate")
    result = subprocess.run(cmd, check=False, cwd=str(repo_root))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _find_app_bundle(dist_dir: Path) -> Path:
    apps = sorted(dist_dir.glob("*.app"))
    if not apps:
        raise SystemExit(f"No .app bundle found in {dist_dir}")
    return apps[0]


def _build_dmg(*, app_path: Path, output_dir: Path, volume_name: str, dmg_name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    dmg_path = output_dir / f"{dmg_name}.dmg"
    with tempfile.TemporaryDirectory(prefix="lexishift_dmg_") as staging:
        stage_dir = Path(staging)
        shutil.copytree(app_path, stage_dir / app_path.name)
        apps_link = stage_dir / "Applications"
        try:
            apps_link.symlink_to("/Applications")
        except OSError:
            pass
        cmd = [
            "hdiutil",
            "create",
            "-volname",
            volume_name,
            "-srcfolder",
            str(stage_dir),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ]
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    return dmg_path


def _find_windows_exe(dist_dir: Path) -> tuple[Path, Path]:
    candidates = sorted(dist_dir.glob("*.exe"))
    if candidates:
        return candidates[0], dist_dir
    for child in dist_dir.iterdir():
        if not child.is_dir():
            continue
        sub_candidates = sorted(child.glob("*.exe"))
        if sub_candidates:
            return sub_candidates[0], child
    raise SystemExit(f"No .exe found in {dist_dir}")


def _sign_macos_app(app_path: Path, identity: str) -> None:
    cmd = [
        "codesign",
        "--deep",
        "--force",
        "--options",
        "runtime",
        "--sign",
        identity,
        str(app_path),
    ]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _notarize_macos(dmg_path: Path, apple_id: str, team_id: str, password: str) -> None:
    submit_cmd = [
        "xcrun",
        "notarytool",
        "submit",
        str(dmg_path),
        "--apple-id",
        apple_id,
        "--team-id",
        team_id,
        "--password",
        password,
        "--wait",
    ]
    result = subprocess.run(submit_cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    staple_cmd = ["xcrun", "stapler", "staple", str(dmg_path)]
    result = subprocess.run(staple_cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _ensure_iscc() -> str:
    exe = shutil.which("iscc")
    if not exe:
        raise SystemExit(
            "Inno Setup compiler (iscc) not found in PATH.\n"
            "Install Inno Setup and ensure iscc.exe is available on PATH."
        )
    return exe


def _build_windows_installer(
    *,
    repo_root: Path,
    dist_dir: Path,
    output_dir: Path,
    app_name: str,
    app_version: str,
) -> Path:
    exe_path, content_dir = _find_windows_exe(dist_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    iscc = _ensure_iscc()
    iss_path = repo_root / "apps" / "gui" / "packaging" / "installer_windows.iss"
    cmd = [
        iscc,
        f"/DAppName={app_name}",
        f"/DAppVersion={app_version}",
        f"/DAppExeName={exe_path.name}",
        f"/DDistDir={str(content_dir)}",
        f"/DOutputDir={str(output_dir)}",
        str(iss_path),
    ]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return output_dir


def _find_installer_exe(output_dir: Path) -> Path:
    candidates = sorted(output_dir.glob("*.exe"))
    if candidates:
        return candidates[0]
    raise SystemExit(f"No installer .exe found in {output_dir}")


def _sign_windows_installer(
    installer_path: Path,
    *,
    pfx_path: str,
    pfx_password: str,
    signtool: str,
    timestamp_url: str,
) -> None:
    cmd = [
        signtool,
        "sign",
        "/f",
        pfx_path,
        "/p",
        pfx_password,
        "/tr",
        timestamp_url,
        "/td",
        "sha256",
        "/fd",
        "sha256",
        str(installer_path),
    ]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    repo_root = _resolve_repo_root()
    default_spec = repo_root / "apps" / "gui" / "packaging" / "pyinstaller.spec"
    default_dist = repo_root / "apps" / "gui" / "dist"
    default_build = repo_root / "apps" / "gui" / "build"
    default_output = repo_root / "apps" / "gui" / "dist" / "installers"

    parser = argparse.ArgumentParser(description="Build platform installers for LexiShift.")
    parser.add_argument("--spec", default=str(default_spec), help="Path to the PyInstaller spec file.")
    parser.add_argument("--dist", default=str(default_dist), help="PyInstaller dist directory.")
    parser.add_argument("--build", default=str(default_build), help="PyInstaller build directory.")
    parser.add_argument("--out", default=str(default_output), help="Installer output directory.")
    parser.add_argument("--skip-build", action="store_true", help="Skip PyInstaller build step.")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the built app bundle after PyInstaller.",
    )
    parser.add_argument("--app-name", default="LexiShift", help="Installer display name.")
    parser.add_argument("--app-version", default="0.1.0", help="Installer version.")
    parser.add_argument("--dmg-name", default="LexiShift", help="DMG file base name (macOS).")
    parser.add_argument(
        "--mac-sign-identity",
        default=os.environ.get("LEXISHIFT_MAC_SIGN_IDENTITY", ""),
        help="macOS code signing identity (Developer ID Application).",
    )
    parser.add_argument(
        "--notarize",
        action="store_true",
        help="Submit the DMG for notarization (requires Apple credentials).",
    )
    parser.add_argument(
        "--apple-id",
        default=os.environ.get("LEXISHIFT_APPLE_ID", ""),
        help="Apple ID for notarization.",
    )
    parser.add_argument(
        "--team-id",
        default=os.environ.get("LEXISHIFT_TEAM_ID", ""),
        help="Apple Team ID for notarization.",
    )
    parser.add_argument(
        "--notary-password",
        default=os.environ.get("LEXISHIFT_NOTARY_PASSWORD", ""),
        help="App-specific password or notarization keychain item.",
    )
    parser.add_argument(
        "--win-sign-pfx",
        default=os.environ.get("LEXISHIFT_WIN_PFX", ""),
        help="Path to Windows code signing .pfx file.",
    )
    parser.add_argument(
        "--win-sign-password",
        default=os.environ.get("LEXISHIFT_WIN_PFX_PASSWORD", ""),
        help="Password for the Windows .pfx file.",
    )
    parser.add_argument(
        "--win-signtool",
        default=os.environ.get("LEXISHIFT_SIGNTOOL", "signtool"),
        help="Path to signtool.exe (Windows SDK).",
    )
    parser.add_argument(
        "--timestamp-url",
        default=os.environ.get("LEXISHIFT_TIMESTAMP_URL", "http://timestamp.digicert.com"),
        help="Timestamp server URL for Windows signing.",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec).expanduser().resolve()
    dist_dir = Path(args.dist).expanduser().resolve()
    build_dir = Path(args.build).expanduser().resolve()
    output_dir = Path(args.out).expanduser().resolve()

    values = _load_spec_values(spec_path) if spec_path.exists() else {}
    app_name = values.get("APP_PRODUCT_NAME") or values.get("APP_NAME") or args.app_name
    app_version = values.get("APP_VERSION") or args.app_version

    if not args.skip_build:
        _run_build_gui(repo_root, spec_path, dist_dir, build_dir, validate=args.validate)

    system = platform.system().lower()
    if system == "darwin":
        app_path = _find_app_bundle(dist_dir)
        if args.mac_sign_identity:
            _sign_macos_app(app_path, args.mac_sign_identity)
        dmg_path = _build_dmg(
            app_path=app_path,
            output_dir=output_dir,
            volume_name=app_name,
            dmg_name=args.dmg_name,
        )
        if args.notarize:
            if not (args.apple_id and args.team_id and args.notary_password):
                raise SystemExit("Notarization requires --apple-id, --team-id, and --notary-password.")
            _notarize_macos(dmg_path, args.apple_id, args.team_id, args.notary_password)
        print(f"DMG created: {dmg_path}")
        return 0
    if system.startswith("win"):
        _build_windows_installer(
            repo_root=repo_root,
            dist_dir=dist_dir,
            output_dir=output_dir,
            app_name=app_name,
            app_version=app_version,
        )
        if args.win_sign_pfx:
            if not args.win_sign_password:
                raise SystemExit("Windows signing requires --win-sign-password.")
            installer = _find_installer_exe(output_dir)
            _sign_windows_installer(
                installer,
                pfx_path=args.win_sign_pfx,
                pfx_password=args.win_sign_password,
                signtool=args.win_signtool,
                timestamp_url=args.timestamp_url,
            )
        print(f"Installer created in: {output_dir}")
        return 0

    raise SystemExit("Unsupported platform. Run this on macOS or Windows.")


if __name__ == "__main__":
    raise SystemExit(main())
