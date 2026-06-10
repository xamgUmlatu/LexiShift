from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional


MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True)
class InstalledPackManifest:
    pack_id: str
    pack_kind: str
    provider: str
    local_kind: str
    build_mode: str
    artifact_relpath: str
    artifact_kind: str
    installed_at_utc: str
    source_filename: str | None = None
    sqlite_filename: str | None = None
    required_files: tuple[str, ...] = ()
    raw_retained: bool = False


def installed_pack_root(base_dir: Path, pack_id: str) -> Path:
    return Path(base_dir) / str(pack_id or "").strip()


def installed_pack_manifest_path(base_dir: Path, pack_id: str) -> Path:
    return installed_pack_root(base_dir, pack_id) / MANIFEST_FILENAME


def load_installed_pack_manifest(
    base_dir: Path,
    pack_id: str,
) -> Optional[InstalledPackManifest]:
    manifest_path = installed_pack_manifest_path(base_dir, pack_id)
    if not manifest_path.exists() or not manifest_path.is_file():
        return None
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_files = tuple(str(name) for name in data.get("required_files", ()))
    return InstalledPackManifest(
        pack_id=str(data.get("pack_id", pack_id)),
        pack_kind=str(data.get("pack_kind", "language")),
        provider=str(data.get("provider", "")),
        local_kind=str(data.get("local_kind", "file")),
        build_mode=str(data.get("build_mode", "download_only")),
        artifact_relpath=str(data.get("artifact_relpath", ".")),
        artifact_kind=str(data.get("artifact_kind", "file")),
        installed_at_utc=str(data.get("installed_at_utc", "")),
        source_filename=_optional_text(data.get("source_filename")),
        sqlite_filename=_optional_text(data.get("sqlite_filename")),
        required_files=required_files,
        raw_retained=bool(data.get("raw_retained", False)),
    )


def resolve_installed_pack_artifact(
    base_dir: Path,
    pack_id: str,
) -> Optional[Path]:
    manifest = load_installed_pack_manifest(base_dir, pack_id)
    if manifest is None:
        return None
    pack_root = installed_pack_root(base_dir, pack_id)
    artifact = _resolve_manifest_artifact_path(pack_root, manifest.artifact_relpath)
    if artifact.exists():
        return artifact
    return None


def load_installed_pack_manifest_for_artifact(path: Path) -> Optional[InstalledPackManifest]:
    candidate = Path(path)
    pack_root = candidate if candidate.is_dir() else candidate.parent
    manifest_path = pack_root / MANIFEST_FILENAME
    if not manifest_path.exists() or not manifest_path.is_file():
        return None
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_files = tuple(str(name) for name in data.get("required_files", ()))
    return InstalledPackManifest(
        pack_id=str(data.get("pack_id", pack_root.name)),
        pack_kind=str(data.get("pack_kind", "language")),
        provider=str(data.get("provider", "")),
        local_kind=str(data.get("local_kind", "file")),
        build_mode=str(data.get("build_mode", "download_only")),
        artifact_relpath=str(data.get("artifact_relpath", ".")),
        artifact_kind=str(data.get("artifact_kind", "file")),
        installed_at_utc=str(data.get("installed_at_utc", "")),
        source_filename=_optional_text(data.get("source_filename")),
        sqlite_filename=_optional_text(data.get("sqlite_filename")),
        required_files=required_files,
        raw_retained=bool(data.get("raw_retained", False)),
    )


def write_installed_pack_manifest(
    base_dir: Path,
    *,
    pack_id: str,
    pack_kind: str,
    provider: str,
    local_kind: str,
    build_mode: str,
    artifact_path: Path,
    source_filename: str | None = None,
    sqlite_filename: str | None = None,
    required_files: tuple[str, ...] = (),
    raw_retained: bool = False,
) -> Path:
    pack_root = installed_pack_root(base_dir, pack_id)
    pack_root.mkdir(parents=True, exist_ok=True)
    artifact_relpath = _artifact_relpath(pack_root, Path(artifact_path))
    artifact_kind = _infer_artifact_kind(Path(artifact_path))
    manifest = InstalledPackManifest(
        pack_id=str(pack_id),
        pack_kind=str(pack_kind),
        provider=str(provider),
        local_kind=str(local_kind),
        build_mode=str(build_mode),
        artifact_relpath=artifact_relpath,
        artifact_kind=artifact_kind,
        installed_at_utc=_utc_timestamp(),
        source_filename=_optional_text(source_filename),
        sqlite_filename=_optional_text(sqlite_filename),
        required_files=tuple(str(name) for name in required_files),
        raw_retained=bool(raw_retained),
    )
    manifest_path = installed_pack_manifest_path(base_dir, pack_id)
    manifest_path.write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _artifact_relpath(pack_root: Path, artifact_path: Path) -> str:
    resolved_root = pack_root.resolve()
    resolved_artifact = artifact_path.resolve()
    if resolved_artifact == resolved_root:
        return "."
    try:
        return resolved_artifact.relative_to(resolved_root).as_posix()
    except ValueError:
        return artifact_path.name


def _resolve_manifest_artifact_path(pack_root: Path, artifact_relpath: str) -> Path:
    relpath = str(artifact_relpath or ".").strip() or "."
    if relpath == ".":
        return pack_root
    return pack_root / relpath


def _infer_artifact_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        return "sqlite"
    return "file"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "InstalledPackManifest",
    "installed_pack_manifest_path",
    "installed_pack_root",
    "load_installed_pack_manifest",
    "load_installed_pack_manifest_for_artifact",
    "resolve_installed_pack_artifact",
    "write_installed_pack_manifest",
]
