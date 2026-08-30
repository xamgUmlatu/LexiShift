from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
from typing import Mapping

from lexishift_core.helper.installed_packs import (
    installed_pack_root,
    load_installed_pack_manifest,
    resolve_installed_pack_artifact,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import (
    LOOKUP_DICTIONARY_METADATA_FILENAME,
    YOMITAN_IMPORTER_VERSION,
    InstalledLookupDictionary,
    YomitanDictionaryImportError,
    YomitanDictionaryImportResult,
    _installed_dictionary_from_metadata,
    _read_dictionary_metadata,
)


@dataclass(frozen=True)
class InstalledLookupDictionaryHealth:
    dictionary: InstalledLookupDictionary
    status: str
    reason: str
    detail: str
    disk_usage_bytes: int

    @property
    def healthy(self) -> bool:
        return self.status == "healthy"


def inspect_installed_lookup_dictionary_health(
    dictionaries_dir: Path,
) -> tuple[InstalledLookupDictionaryHealth, ...]:
    """Inspect managed dictionaries without hashing archives or scanning all rows."""
    base = Path(dictionaries_dir)
    if not base.exists() or not base.is_dir():
        return ()
    try:
        roots = sorted(
            (path for path in base.iterdir() if path.is_dir() and not path.name.startswith(".")),
            key=lambda path: path.name,
        )
    except OSError:
        return ()
    return tuple(inspect_lookup_dictionary_root(base, root) for root in roots)


def inspect_lookup_dictionary_root(
    dictionaries_dir: Path,
    root: Path,
) -> InstalledLookupDictionaryHealth:
    pack_id = root.name
    if root.is_symlink():
        return InstalledLookupDictionaryHealth(
            dictionary=_installed_dictionary_from_metadata({"pack_id": pack_id, "title": pack_id}),
            status="incompatible",
            reason="managed_root_symlink",
            detail="Managed dictionary directories cannot be symbolic links.",
            disk_usage_bytes=0,
        )
    metadata_path = root / LOOKUP_DICTIONARY_METADATA_FILENAME
    metadata: Mapping[str, object] = {}
    metadata_issue: tuple[str, str, str] | None = None
    try:
        raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if isinstance(raw_metadata, Mapping):
            metadata = raw_metadata
        else:
            metadata_issue = (
                "corrupt",
                "metadata_invalid",
                "dictionary.json does not contain a JSON object.",
            )
    except FileNotFoundError:
        metadata_issue = (
            "missing",
            "metadata_missing",
            "dictionary.json is missing.",
        )
    except (OSError, json.JSONDecodeError) as exc:
        metadata_issue = (
            "corrupt",
            "metadata_invalid",
            f"dictionary.json could not be read: {exc}",
        )
    dictionary = _installed_dictionary_from_metadata(
        {"pack_id": pack_id, "title": pack_id, **metadata}
    )
    disk_usage = _lookup_dictionary_known_file_usage(root)
    if metadata_issue is not None:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status=metadata_issue[0],
            reason=metadata_issue[1],
            detail=metadata_issue[2],
            disk_usage_bytes=disk_usage,
        )
    if dictionary.pack_id != pack_id:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="corrupt",
            reason="metadata_pack_id_mismatch",
            detail="dictionary.json does not match its managed directory.",
            disk_usage_bytes=disk_usage,
        )
    if dictionary.provider != "yomitan" or dictionary.format != 3:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="incompatible",
            reason="metadata_incompatible",
            detail="Dictionary provider or format is not supported by this importer.",
            disk_usage_bytes=disk_usage,
        )
    try:
        importer_version = int(str(metadata.get("importer_version", 0)))
    except (TypeError, ValueError):
        importer_version = 0
    if importer_version > YOMITAN_IMPORTER_VERSION:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="incompatible",
            reason="importer_too_new",
            detail="Dictionary was created by a newer LexiShift importer.",
            disk_usage_bytes=disk_usage,
        )

    try:
        manifest = load_installed_pack_manifest(dictionaries_dir, pack_id)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="corrupt",
            reason="manifest_invalid",
            detail=f"manifest.json could not be read: {exc}",
            disk_usage_bytes=disk_usage,
        )
    if manifest is None:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="missing",
            reason="manifest_missing",
            detail="manifest.json is missing.",
            disk_usage_bytes=disk_usage,
        )
    if (
        manifest.pack_id != pack_id
        or manifest.pack_kind != "lookup_dictionary"
        or manifest.provider != "yomitan"
        or manifest.artifact_kind != "sqlite"
    ):
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="incompatible",
            reason="manifest_incompatible",
            detail="manifest.json does not describe a supported lookup dictionary.",
            disk_usage_bytes=disk_usage,
        )
    artifact_path = root / manifest.artifact_relpath
    try:
        resolved_root = root.resolve()
        resolved_artifact = artifact_path.resolve()
        resolved_artifact.relative_to(resolved_root)
    except (OSError, ValueError):
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="incompatible",
            reason="artifact_path_unsafe",
            detail="The dictionary artifact path escapes its managed directory.",
            disk_usage_bytes=disk_usage,
        )
    if not resolved_artifact.exists() or not resolved_artifact.is_file():
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="missing",
            reason="artifact_missing",
            detail="The imported SQLite dictionary is missing.",
            disk_usage_bytes=disk_usage,
        )
    sqlite_issue = _lookup_dictionary_sqlite_issue(resolved_artifact, pack_id)
    if sqlite_issue is not None:
        return InstalledLookupDictionaryHealth(
            dictionary=dictionary,
            status="corrupt",
            reason=sqlite_issue[0],
            detail=sqlite_issue[1],
            disk_usage_bytes=disk_usage,
        )
    return InstalledLookupDictionaryHealth(
        dictionary=dictionary,
        status="healthy",
        reason="healthy",
        detail="Dictionary metadata, manifest, and SQLite index are readable.",
        disk_usage_bytes=disk_usage,
    )


def replace_unhealthy_installed_dictionary(
    *,
    dictionaries_dir: Path,
    pack_id: str,
    staged_result: YomitanDictionaryImportResult,
) -> YomitanDictionaryImportResult:
    base = Path(dictionaries_dir).resolve()
    target_root = installed_pack_root(base, pack_id)
    if target_root.is_symlink() or target_root.resolve().parent != base:
        raise YomitanDictionaryImportError(
            "The installed dictionary path is unsafe and cannot be repaired automatically."
        )
    current_health = inspect_lookup_dictionary_root(base, target_root)
    if current_health.healthy:
        raise YomitanDictionaryImportError(
            f"Lookup dictionary destination already exists: {pack_id}"
        )
    staged_root = staged_result.artifact_path.parent
    staged_health = inspect_lookup_dictionary_root(staged_root.parent, staged_root)
    if not staged_health.healthy:
        raise YomitanDictionaryImportError(
            "The rebuilt dictionary did not pass validation and was not installed."
        )
    replacement_paths = (
        staged_result.artifact_path,
        staged_root / LOOKUP_DICTIONARY_METADATA_FILENAME,
        staged_result.manifest_path,
        staged_result.provenance_path,
    )
    if any(not path.is_file() for path in replacement_paths):
        raise YomitanDictionaryImportError(
            "The rebuilt dictionary is incomplete and was not installed."
        )
    target_root.mkdir(parents=True, exist_ok=True)
    for source_path in replacement_paths:
        os.replace(source_path, target_root / source_path.name)
    return YomitanDictionaryImportResult(
        dictionary=staged_result.dictionary,
        artifact_path=target_root / staged_result.artifact_path.name,
        manifest_path=target_root / staged_result.manifest_path.name,
        provenance_path=target_root / staged_result.provenance_path.name,
    )


def existing_import_result(
    *,
    dictionaries_dir: Path,
    pack_id: str,
    archive_sha256: str,
) -> YomitanDictionaryImportResult | None:
    root = installed_pack_root(dictionaries_dir, pack_id)
    metadata_path = root / LOOKUP_DICTIONARY_METADATA_FILENAME
    try:
        artifact_path = resolve_installed_pack_artifact(dictionaries_dir, pack_id)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if artifact_path is None or not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, Mapping) or metadata.get("archive_sha256") != archive_sha256:
        return None
    if not inspect_lookup_dictionary_root(Path(dictionaries_dir), root).healthy:
        return None
    return YomitanDictionaryImportResult(
        dictionary=_installed_dictionary_from_metadata(metadata),
        artifact_path=artifact_path,
        manifest_path=root / "manifest.json",
        provenance_path=root / "provenance.json",
    )


def _lookup_dictionary_sqlite_issue(
    artifact_path: Path,
    pack_id: str,
) -> tuple[str, str] | None:
    try:
        uri = artifact_path.resolve().as_uri() + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True, timeout=0.25) as conn:
            tables = {
                str(row[0])
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name IN ('metadata', 'terms')"
                )
            }
            if tables != {"metadata", "terms"}:
                return "database_schema_missing", "Required SQLite tables are missing."
            indexes = {
                str(row[0])
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index' "
                    "AND name IN ('terms_expression_idx', 'terms_reading_idx')"
                )
            }
            if indexes != {"terms_expression_idx", "terms_reading_idx"}:
                return "database_index_missing", "Required SQLite indexes are missing."
            metadata = _read_dictionary_metadata(conn)
            if str(metadata.get("pack_id") or "") != pack_id:
                return "database_pack_id_mismatch", "SQLite metadata has the wrong pack ID."
            if conn.execute("SELECT 1 FROM terms LIMIT 1").fetchone() is None:
                return "database_empty", "SQLite dictionary contains no readable terms."
    except (OSError, sqlite3.Error, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return "database_unreadable", f"SQLite dictionary could not be read: {exc}"
    return None


def _lookup_dictionary_known_file_usage(root: Path) -> int:
    total = 0
    try:
        for path in root.iterdir():
            if path.is_file():
                total += path.stat().st_size
    except OSError:
        pass
    return total


__all__ = [
    "InstalledLookupDictionaryHealth",
    "inspect_installed_lookup_dictionary_health",
]
