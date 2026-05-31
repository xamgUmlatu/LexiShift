from __future__ import annotations

from pathlib import Path
from typing import Mapping

MACOS_MAIN_BUNDLE_ID = "com.lexishift.app"
MAIN_APP_BUNDLE_NAME = "LexiShift.app"
MAIN_WINDOWS_DIR_NAME = "LexiShift"
MAIN_WINDOWS_EXE_NAME = "LexiShift.exe"


def resource_settings_launch_command(
    payload: Mapping[str, object] | None,
    *,
    script_dir: Path,
    project_root: Path,
    executable: str,
    environ: Mapping[str, str],
    platform: str,
    frozen: bool,
    open_resource_settings_flag: str,
    resource_pair_flag: str,
) -> tuple[list[str], str]:
    resource_args = _resource_pair_arg(payload or {}, resource_pair_flag=resource_pair_flag)
    env_python = environ.get("LEXISHIFT_GUI_PYTHON")
    env_entry = environ.get("LEXISHIFT_GUI_ENTRY")
    if env_entry:
        return [
            env_python or executable,
            str(Path(env_entry).expanduser()),
            open_resource_settings_flag,
            *resource_args,
        ], "env_gui_entry"

    if platform == "darwin":
        resolved_bundle = _resolve_macos_launch_bundle(script_dir)
        if resolved_bundle is not None:
            main_bundle, launch_mode = resolved_bundle
            return [
                "open",
                str(main_bundle),
                "--args",
                open_resource_settings_flag,
                *resource_args,
            ], launch_mode

    dev_entry = project_root / "apps" / "gui" / "src" / "main.py"
    if dev_entry.exists():
        return [
            executable,
            str(dev_entry),
            open_resource_settings_flag,
            *resource_args,
        ], "dev_gui_entry"

    if frozen and platform.startswith("win"):
        main_executable = _resolve_windows_sibling_executable(Path(executable))
        if main_executable is not None:
            return [
                str(main_executable),
                open_resource_settings_flag,
                *resource_args,
            ], "windows_sibling_exe"

    if platform == "darwin":
        return [
            "open",
            "-b",
            MACOS_MAIN_BUNDLE_ID,
            "--args",
            open_resource_settings_flag,
            *resource_args,
        ], "macos_bundle_id"

    raise RuntimeError("LexiShift app launch target could not be resolved.")


def _resource_pair_arg(
    payload: Mapping[str, object],
    *,
    resource_pair_flag: str,
) -> list[str]:
    pair = str(payload.get("pair") or "").strip().lower()
    if not pair:
        return []
    return [resource_pair_flag, pair]


def _resolve_windows_sibling_executable(current_executable: Path) -> Path | None:
    exe_path = current_executable.resolve()
    parent = exe_path.parent
    grandparent = parent.parent
    candidates = [
        parent / MAIN_WINDOWS_EXE_NAME,
        parent / MAIN_WINDOWS_DIR_NAME / MAIN_WINDOWS_EXE_NAME,
        grandparent / MAIN_WINDOWS_DIR_NAME / MAIN_WINDOWS_EXE_NAME,
        grandparent / MAIN_WINDOWS_EXE_NAME,
        *sorted(parent.glob(f"*/{MAIN_WINDOWS_EXE_NAME}")),
        *sorted(grandparent.glob(f"*/{MAIN_WINDOWS_EXE_NAME}")),
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved == exe_path or resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists():
            return candidate
    return None


def _resolve_macos_bundle_from_host_script(script_dir: Path) -> Path | None:
    for parent in script_dir.parents:
        if parent.suffix == ".app":
            return parent
    return None


def _resolve_macos_installed_bundle() -> Path | None:
    for candidate in (
        Path("/Applications") / MAIN_APP_BUNDLE_NAME,
        Path.home() / "Applications" / MAIN_APP_BUNDLE_NAME,
    ):
        if candidate.exists():
            return candidate
    return None


def _resolve_macos_launch_bundle(script_dir: Path) -> tuple[Path, str] | None:
    host_bundle = _resolve_macos_bundle_from_host_script(script_dir)
    if host_bundle is not None:
        return host_bundle, "macos_host_bundle"
    installed_bundle = _resolve_macos_installed_bundle()
    if installed_bundle is not None:
        return installed_bundle, "macos_installed_bundle"
    return None
