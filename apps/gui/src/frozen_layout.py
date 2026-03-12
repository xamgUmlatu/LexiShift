from __future__ import annotations

from pathlib import Path


MAIN_APP_BUNDLE_NAME = "LexiShift.app"
MAIN_WINDOWS_DIR_NAME = "LexiShift"
MAIN_WINDOWS_EXE_NAME = "LexiShift.exe"
HELPER_APP_BUNDLE_NAME = "LexiShift Helper.app"
HELPER_WINDOWS_DIR_NAME = "LexiShiftHelper"
HELPER_WINDOWS_EXE_NAME = "LexiShiftHelper.exe"


def resolve_macos_sibling_bundle(current_executable: Path, bundle_name: str) -> Path | None:
    exe_path = current_executable.resolve()
    if exe_path.parent.name != "MacOS" or exe_path.parent.parent.name != "Contents":
        return None
    current_bundle = exe_path.parent.parent.parent
    if current_bundle.suffix != ".app":
        return None
    candidate = current_bundle.with_name(bundle_name)
    return candidate if candidate.exists() else None


def resolve_windows_sibling_executable(
    current_executable: Path,
    *,
    preferred_dir_name: str,
    exe_name: str,
) -> Path | None:
    exe_path = current_executable.resolve()
    parent = exe_path.parent
    grandparent = parent.parent
    candidates = [
        parent / exe_name,
        parent / preferred_dir_name / exe_name,
        grandparent / preferred_dir_name / exe_name,
        grandparent / exe_name,
        *sorted(parent.glob(f"*/{exe_name}")),
        *sorted(grandparent.glob(f"*/{exe_name}")),
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
