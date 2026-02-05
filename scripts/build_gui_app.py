#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Sequence, Tuple


def _resolve_repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "PyInstaller is not available. Install it in your current environment:\n"
            "  python -m pip install pyinstaller"
        ) from exc


def _build_command(
    spec_path: str,
    *,
    clean: bool,
    noconfirm: bool,
    distpath: str,
    workpath: str,
    extra: Sequence[str],
) -> list[str]:
    cmd = [sys.executable, "-m", "PyInstaller"]
    if clean:
        cmd.append("--clean")
    if noconfirm:
        cmd.append("--noconfirm")
    cmd.extend(["--distpath", distpath, "--workpath", workpath])
    cmd.append(spec_path)
    cmd.extend(extra)
    return cmd


def _default_paths(repo_root: str) -> Tuple[str, str, str]:
    default_spec = os.path.join(repo_root, "apps", "gui", "packaging", "pyinstaller.spec")
    default_dist = os.path.join(repo_root, "apps", "gui", "dist")
    default_build = os.path.join(repo_root, "apps", "gui", "build")
    return default_spec, default_dist, default_build


def _clean_output_dirs(dist_path: str, work_path: str) -> None:
    for path in (dist_path, work_path):
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)


def _detect_build_mode(spec_path: str) -> str:
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        return "onedir" if "COLLECT(" in content else "onefile"
    except Exception:
        return "unknown"


def _find_macos_app(dist_path: str) -> Path:
    dist_dir = Path(dist_path)
    apps = sorted(dist_dir.glob("*.app"))
    if not apps:
        raise SystemExit(f"No .app bundle found in {dist_dir}")
    return apps[0]


def _install_macos_app(app_path: Path, install_dir: Path) -> Path:
    install_dir.mkdir(parents=True, exist_ok=True)
    target = install_dir / app_path.name
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(app_path, target, symlinks=True)
    return target


def _run_validation(repo_root: str, app_path: Path | None, dist_path: str) -> None:
    script = Path(repo_root) / "scripts" / "validate_app_bundle.py"
    cmd = [sys.executable, str(script)]
    if app_path is not None:
        cmd.extend(["--app", str(app_path)])
    else:
        cmd.extend(["--distpath", dist_path])
    result = subprocess.run(cmd, check=False, cwd=repo_root)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    repo_root = _resolve_repo_root()
    default_spec, default_dist, default_build = _default_paths(repo_root)

    parser = argparse.ArgumentParser(description="Build the LexiShift desktop app.")
    parser.add_argument(
        "--spec",
        default=str(default_spec),
        help="Path to the PyInstaller .spec file.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Clean PyInstaller build cache (default).",
    )
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Do not clean PyInstaller build cache.",
    )
    parser.add_argument(
        "--noconfirm",
        action="store_true",
        default=True,
        help="Overwrite output directory without asking (default).",
    )
    parser.add_argument(
        "--confirm",
        dest="noconfirm",
        action="store_false",
        help="Ask before overwriting output directory.",
    )
    parser.add_argument(
        "--distpath",
        default=str(default_dist),
        help="Output directory for built artifacts.",
    )
    parser.add_argument(
        "--workpath",
        default=str(default_build),
        help="Build/work directory for PyInstaller.",
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        default=True,
        help="Remove dist/work directories before building (default).",
    )
    parser.add_argument(
        "--no-clean-output",
        dest="clean_output",
        action="store_false",
        help="Keep existing dist/work directories.",
    )
    parser.add_argument(
        "pyinstaller_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed through to PyInstaller.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the built app bundle for required resources.",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the built app bundle (macOS only).",
    )
    parser.add_argument(
        "--install-dir",
        default="/Applications",
        help="Install directory for macOS app bundle (default: /Applications).",
    )

    args = parser.parse_args()
    spec_path = os.path.abspath(os.path.expanduser(args.spec))
    dist_path = os.path.abspath(os.path.expanduser(args.distpath))
    work_path = os.path.abspath(os.path.expanduser(args.workpath))

    if not os.path.exists(spec_path):
        raise SystemExit(f"Spec file not found: {spec_path}")

    _ensure_pyinstaller()

    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.executable}")
    print(f"Spec: {spec_path}")
    print(f"Dist: {dist_path}")
    print(f"Work: {work_path}")

    mode = _detect_build_mode(spec_path)
    print(f"Build Mode: {mode.upper()}")
    if mode == "onefile":
        print("  -> Warning: One-file builds have slower startup times.")
        print("  -> To fix: Edit the .spec file to use COLLECT() for a one-dir build.")

    if args.clean_output:
        print("Cleaning dist/work directories...")
        _clean_output_dirs(dist_path, work_path)

    cmd = _build_command(
        spec_path,
        clean=args.clean,
        noconfirm=args.noconfirm,
        distpath=dist_path,
        workpath=work_path,
        extra=args.pyinstaller_args,
    )
    print("Running:", " ".join(cmd))

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("LEXISHIFT_REPO_ROOT", repo_root)
    env.setdefault("LEXISHIFT_SPEC_PATH", spec_path)

    result = subprocess.run(cmd, env=env, check=False, cwd=repo_root)
    if result.returncode != 0:
        return int(result.returncode)

    app_path: Path | None = None
    if platform.system() == "Darwin":
        app_path = _find_macos_app(dist_path)

    if args.validate:
        _run_validation(repo_root, app_path, dist_path)

    if args.install:
        if platform.system() != "Darwin":
            print("Install step skipped: --install is only supported on macOS.")
        elif app_path is not None:
            install_target = _install_macos_app(app_path, Path(args.install_dir))
            print(f"Installed to: {install_target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
