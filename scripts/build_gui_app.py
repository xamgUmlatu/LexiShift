#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
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
        "pyinstaller_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed through to PyInstaller.",
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
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
