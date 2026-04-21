from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
from typing import Optional, Sequence


def resolve_workspace_host_script() -> Optional[Path]:
    override = str(os.environ.get("LEXISHIFT_HELPER_HOST", "") or "").strip()
    if override:
        return Path(override).expanduser()
    env_repo_root = str(os.environ.get("LEXISHIFT_REPO_ROOT", "") or "").strip()
    candidates: list[Path] = []
    if env_repo_root:
        candidates.append(Path(env_repo_root).expanduser())
    try:
        candidates.append(Path.cwd())
    except OSError:
        pass
    try:
        candidates.append(Path(sys.executable).resolve())
    except OSError:
        candidates.append(Path(sys.executable))
    candidates.append(Path(__file__).resolve())
    for candidate in candidates:
        for current in (candidate, *candidate.parents):
            marker = current / "core" / "lexishift_core" / "__init__.py"
            if marker.exists():
                return current / "scripts" / "helper" / "lexishift_native_host.py"
    return None


def normalize_extension_ids(extension_ids: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in extension_ids:
        extension_id = str(value or "").strip()
        if not extension_id or extension_id in normalized:
            continue
        normalized.append(extension_id)
    return tuple(normalized)


def origin_for_extension_id(extension_id: str) -> str:
    return f"chrome-extension://{extension_id}/"


def extension_id_from_origin(origin: object) -> Optional[str]:
    origin_text = str(origin or "").strip()
    prefix = "chrome-extension://"
    if not origin_text.startswith(prefix):
        return None
    suffix = origin_text[len(prefix) :]
    extension_id = suffix.rstrip("/")
    return extension_id or None


def hash_file(path: Path) -> Optional[str]:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def hash_directory(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_dir():
        return None
    digest = hashlib.sha256()
    try:
        for file_path in sorted(child for child in path.rglob("*") if child.is_file()):
            relative = file_path.relative_to(path).as_posix().encode("utf-8")
            digest.update(relative)
            file_digest = hash_file(file_path)
            if file_digest is None:
                return None
            digest.update(file_digest.encode("ascii"))
        return digest.hexdigest()
    except OSError:
        return None


def stable_bundled_host_path(
    data_root: Path,
    *,
    is_windows: bool,
    windows_host_executable_name: str,
) -> Path:
    if is_windows:
        return data_root / "helper" / "native_host" / windows_host_executable_name
    return data_root / "helper" / "lexishift_native_host.py"


def stable_bundled_core_path(data_root: Path) -> Path:
    return data_root / "helper" / "lexishift_core"


def resolve_host_path_for_mode(
    host_mode: str,
    *,
    host_override_path: Optional[str],
    default_host_resolver,
    workspace_host_resolver,
) -> Optional[Path]:
    override = str(host_override_path or "").strip()
    if host_mode == "custom":
        return Path(override).expanduser() if override else None
    if host_mode == "workspace":
        if override:
            return Path(override).expanduser()
        return workspace_host_resolver()
    if host_mode == "bundled":
        return default_host_resolver()
    if override:
        return Path(override).expanduser()
    return default_host_resolver()
