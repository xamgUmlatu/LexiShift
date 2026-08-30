from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import struct
import sys
from typing import Callable, Optional, Sequence


WORKSPACE_WRAPPER_NAME = "lexishift_native_host_workspace.sh"


def probe_native_host(host_path: Path, *, timeout_seconds: float = 20.0) -> tuple[bool, str]:
    request = json.dumps(
        {"id": "native-host-smoke", "type": "hello", "version": 1, "payload": {}}
    ).encode("utf-8")
    framed_request = struct.pack("<I", len(request)) + request
    try:
        completed = subprocess.run(
            [str(host_path)],
            input=framed_request,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env={
                **os.environ,
                "HOME": os.environ.get("HOME", str(Path.home())),
                "PATH": os.environ.get("PATH", ""),
            },
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    output = completed.stdout or b""
    if completed.returncode != 0:
        detail = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
        return False, detail or f"native host exited with code {completed.returncode}"
    if len(output) < 4:
        return False, "native host returned no framed response"
    response_length = struct.unpack("<I", output[:4])[0]
    response_bytes = output[4 : 4 + response_length]
    if len(response_bytes) != response_length:
        return False, "native host returned an incomplete framed response"
    try:
        response = json.loads(response_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"native host returned invalid JSON: {exc}"
    if not isinstance(response, dict) or response.get("ok") is not True:
        return False, f"native host smoke request failed: {response!r}"
    data = response.get("data")
    if not isinstance(data, dict) or int(data.get("protocol_version", 0) or 0) < 1:
        return False, "native host hello response is missing its protocol version"
    return True, ""


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


def workspace_host_wrapper_path(data_root: Path) -> Path:
    return data_root / "helper" / WORKSPACE_WRAPPER_NAME


def workspace_repo_root(host_script: Path) -> Path:
    return host_script.resolve().parents[2]


def workspace_python_candidates(host_script: Path) -> list[Path]:
    candidates: list[Path] = []
    override = str(os.environ.get("LEXISHIFT_PYTHON", "") or "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    repo_root = workspace_repo_root(host_script)
    candidates.append(repo_root / ".venv" / "bin" / "python")
    candidates.append(repo_root / ".venv" / "bin" / "python3")
    if not getattr(sys, "frozen", False):
        try:
            candidates.append(Path(sys.executable).resolve())
        except OSError:
            candidates.append(Path(sys.executable))
    normalized: list[Path] = []
    for candidate in candidates:
        if candidate in normalized:
            continue
        normalized.append(candidate)
    return normalized


def probe_workspace_python(python_path: Path, host_script: Path) -> tuple[bool, str]:
    repo_root = workspace_repo_root(host_script)
    command = [
        str(python_path),
        "-c",
        (
            "from pathlib import Path; import sys; "
            f"root = Path({repo_root.as_posix()!r}); "
            "sys.path.insert(0, str(root / 'core')); "
            "import lexishift_core.helper.engine"
        ),
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env={
                "HOME": os.environ.get("HOME", str(Path.home())),
                "PATH": os.environ.get("PATH", ""),
            },
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ""
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    detail = stderr or stdout or f"exit={result.returncode}"
    return False, detail


def resolve_workspace_python(
    host_script: Path,
    *,
    validate: bool,
    log: Optional[Callable[[str], None]] = None,
) -> Optional[Path]:
    logger = log or (lambda _message: None)
    for candidate in workspace_python_candidates(host_script):
        if not candidate.exists():
            continue
        if validate:
            ok, detail = probe_workspace_python(candidate, host_script)
            if not ok:
                logger(f"[Helper] Workspace python probe rejected {candidate}: {detail}")
                continue
        return candidate
    return None


def build_workspace_wrapper_script(host_script: Path, python_path: Path) -> str:
    repo_root = workspace_repo_root(host_script)
    return "\n".join(
        [
            "#!/bin/sh",
            f"export LEXISHIFT_REPO_ROOT={shlex.quote(str(repo_root))}",
            f'exec {shlex.quote(str(python_path))} {shlex.quote(str(host_script))} "$@"',
            "",
        ]
    )


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
