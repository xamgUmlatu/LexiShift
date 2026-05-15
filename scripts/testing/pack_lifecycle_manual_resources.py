from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence

from lexishift_core.helper.installed_packs import MANIFEST_FILENAME


def audit_manual_resource_settings(settings_path: Path) -> dict[str, object]:
    path = Path(settings_path).expanduser().resolve(strict=False)
    data_root = path.parent
    payload, errors = _load_json_object(path)
    synonyms = _as_mapping(payload.get("synonyms")) if payload else {}
    rows: list[dict[str, object]] = []
    if synonyms:
        _append_manual_path_map(
            rows,
            field_name="language_pack_paths",
            family="language",
            values=_as_mapping(synonyms.get("language_pack_paths")),
            data_root=data_root,
            disposition="manual_or_secondary_compatibility",
        )
        _append_manual_path_map(
            rows,
            field_name="frequency_pack_paths",
            family="frequency",
            values=_as_mapping(synonyms.get("frequency_pack_paths")),
            data_root=data_root,
            disposition="manual_frequency_override",
        )
        _append_manual_path_map(
            rows,
            field_name="embedding_pack_paths",
            family="embedding",
            values=_as_mapping(synonyms.get("embedding_pack_paths")),
            data_root=data_root,
            disposition="manual_embedding_override",
        )
        _append_embedding_pair_paths(rows, synonyms=synonyms, data_root=data_root)
        _append_legacy_secondary_aliases(rows, synonyms=synonyms, data_root=data_root)
    review_count = sum(1 for row in rows if row["issues"])
    status = "ok"
    if errors:
        status = "error"
    elif review_count:
        status = "review"
    return {
        "settings_path": str(path),
        "settings_exists": path.exists(),
        "settings_errors": errors,
        "status": status,
        "managed_language_pack_ids": _text_values(synonyms.get("managed_language_pack_ids")),
        "managed_frequency_pack_ids": _text_values(synonyms.get("managed_frequency_pack_ids")),
        "embedding_pair_pack_ids": _embedding_pair_pack_ids(synonyms),
        "manual_path_count": len(rows),
        "manual_path_review_count": review_count,
        "manual_path_missing_count": sum(
            1 for row in rows if "manual_path_missing" in row["issues"]
        ),
        "managed_artifact_manual_path_count": sum(
            1 for row in rows if "app_managed_artifact_in_manual_settings" in row["issues"]
        ),
        "manual_paths": rows,
    }


def _append_manual_path_map(
    rows: list[dict[str, object]],
    *,
    field_name: str,
    family: str,
    values: Mapping[str, object],
    data_root: Path,
    disposition: str,
) -> None:
    for key, raw_path in sorted(values.items()):
        key_text = str(key or "").strip()
        path_text = str(raw_path or "").strip()
        if not key_text or not path_text:
            continue
        rows.append(
            _manual_path_row(
                field_name=field_name,
                family=family,
                key=key_text,
                raw_path=path_text,
                data_root=data_root,
                disposition=disposition,
            )
        )


def _append_embedding_pair_paths(
    rows: list[dict[str, object]],
    *,
    synonyms: Mapping[str, object],
    data_root: Path,
) -> None:
    for pair_key, values in sorted(_as_mapping(synonyms.get("embedding_pair_paths")).items()):
        pair_text = str(pair_key or "").strip()
        if not pair_text:
            continue
        for index, raw_path in enumerate(_sequence(values)):
            path_text = str(raw_path or "").strip()
            if not path_text:
                continue
            rows.append(
                _manual_path_row(
                    field_name="embedding_pair_paths",
                    family="embedding",
                    key=f"{pair_text}[{index}]",
                    raw_path=path_text,
                    data_root=data_root,
                    disposition="manual_pair_embedding_override",
                )
            )


def _append_legacy_secondary_aliases(
    rows: list[dict[str, object]],
    *,
    synonyms: Mapping[str, object],
    data_root: Path,
) -> None:
    for field_name, pack_id in (("wordnet_dir", "wordnet-en"), ("moby_path", "moby-en")):
        path_text = str(synonyms.get(field_name) or "").strip()
        if not path_text:
            continue
        rows.append(
            _manual_path_row(
                field_name=field_name,
                family="language",
                key=pack_id,
                raw_path=path_text,
                data_root=data_root,
                disposition="legacy_secondary_compatibility_alias",
            )
        )


def _manual_path_row(
    *,
    field_name: str,
    family: str,
    key: str,
    raw_path: str,
    data_root: Path,
    disposition: str,
) -> dict[str, object]:
    path = Path(raw_path).expanduser().resolve(strict=False)
    managed_pack_root = _managed_pack_root_for_path(
        path,
        data_root=data_root,
        family=family,
    )
    issues: list[str] = []
    if not path.exists():
        issues.append("manual_path_missing")
    if managed_pack_root is not None:
        issues.append("app_managed_artifact_in_manual_settings")
    format_supported, expected_format = _manual_path_format_support(
        field_name=field_name,
        family=family,
        key=key,
        path=path,
    )
    if path.exists() and not format_supported:
        issues.append("unsupported_manual_artifact_format")
    return {
        "field_name": field_name,
        "family": family,
        "key": key,
        "path": str(path),
        "path_exists": path.exists(),
        "expected_format": expected_format,
        "format_supported": format_supported,
        "disposition": "migrate_to_managed_pack_id" if managed_pack_root else disposition,
        "managed_pack_root": str(managed_pack_root or ""),
        "issues": issues,
    }


def _managed_pack_root_for_path(path: Path, *, data_root: Path, family: str) -> Path | None:
    base_dir = {
        "language": data_root / "language_packs",
        "frequency": data_root / "frequency_packs",
        "embedding": data_root / "embedding_packs",
    }.get(family)
    if base_dir is None:
        return None
    resolved_base = base_dir.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    try:
        relpath = resolved_path.relative_to(resolved_base)
    except ValueError:
        return None
    if not relpath.parts:
        return None
    pack_root = resolved_base / relpath.parts[0]
    if (pack_root / MANIFEST_FILENAME).is_file():
        return pack_root
    return None


def _manual_path_format_support(
    *,
    field_name: str,
    family: str,
    key: str,
    path: Path,
) -> tuple[bool, str]:
    if field_name == "wordnet_dir" or key == "wordnet-en":
        return path.is_dir(), "WordNet directory"
    if field_name == "moby_path" or key == "moby-en":
        return path.is_file(), "Moby thesaurus text file"
    if family == "frequency":
        return (
            path.is_file() and _is_sqlite_db_file(path) and _sqlite_has_table(path, "frequency"),
            "SQLite database with frequency table",
        )
    if family == "embedding":
        return (
            path.is_file()
            and (_is_sqlite_db_file(path) or path.suffix.lower() in {".vec", ".txt", ".bin"}),
            "SQLite embedding database or .vec/.txt/.bin vector file",
        )
    if family == "language":
        if path.is_dir():
            return True, "directory with pack-specific required files"
        return (
            path.is_file()
            and (_is_sqlite_db_file(path) or path.suffix.lower() in {".tei", ".xml", ".txt"}),
            "SQLite, TEI/XML, or pack-specific text resource",
        )
    return True, "manual compatibility path"


def _load_json_object(path: Path) -> tuple[dict[str, object], list[str]]:
    if not path.exists() or not path.is_file():
        return {}, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"invalid_json:{exc}"]
    if not isinstance(payload, Mapping):
        return {}, ["not_json_object"]
    return dict(payload), []


def _is_sqlite_db_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError:
        return False
    return header.startswith(b"SQLite format 3")


def _sqlite_has_table(path: Path, table_name: str) -> bool:
    if not _is_sqlite_db_file(path):
        return False
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND lower(name) = lower(?) LIMIT 1",
                (table_name,),
            )
            return cursor.fetchone() is not None
    except sqlite3.Error:
        return False


def _text_values(value: object) -> list[str]:
    return [str(item).strip() for item in _sequence(value) if str(item).strip()]


def _embedding_pair_pack_ids(synonyms: Mapping[str, object]) -> dict[str, list[str]]:
    return {
        str(pair_key): _text_values(values)
        for pair_key, values in _as_mapping(synonyms.get("embedding_pair_pack_ids")).items()
        if str(pair_key).strip()
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()
