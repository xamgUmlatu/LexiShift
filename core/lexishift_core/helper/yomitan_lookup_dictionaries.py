from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import tempfile
from typing import Callable, Mapping, Sequence
import zipfile
import zlib

from lexishift_core.helper.installed_packs import (
    installed_pack_root,
    resolve_installed_pack_artifact,
    write_installed_pack_manifest,
)
from lexishift_core.helper.pack_provenance import write_app_managed_pack_provenance
from lexishift_core.helper.yomitan_dictionary_rendering import (
    definition_payloads,
    is_cross_reference_only_glossary,
)
from lexishift_core.lexicon.word_package import normalize_reading


LOOKUP_DICTIONARY_METADATA_FILENAME = "dictionary.json"
YOMITAN_IMPORTER_VERSION = 2
MAX_ARCHIVE_MEMBERS = 20_000
# Large, heavily structured dictionaries can legitimately expand well beyond
# their ZIP size. Keep the limit finite for zip-bomb protection while allowing
# current large Yomitan term dictionaries such as Daijirin Fourth Edition.
MAX_TOTAL_UNCOMPRESSED_BYTES = 4 * 1024 * 1024 * 1024
MAX_INDEX_BYTES = 4 * 1024 * 1024
MAX_TERM_BANK_BYTES = 256 * 1024 * 1024
GLOSSARY_COMPRESSION_MIN_BYTES = 2_048
_GLOSSARY_COMPRESSION_MAGIC = b"LSZ1"
_TERM_BANK_NAME = re.compile(r"term_bank_(\d+)\.json")
_SAFE_PACK_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")


class YomitanDictionaryImportError(ValueError):
    pass


class YomitanDictionaryImportCancelled(RuntimeError):
    pass


@dataclass(frozen=True)
class InstalledLookupDictionary:
    pack_id: str
    title: str
    revision: str
    provider: str
    format: int
    term_count: int
    imported_at_utc: str
    source_filename: str = ""
    author: str = ""
    source_language: str = ""
    target_language: str = ""


@dataclass(frozen=True)
class YomitanDictionaryImportResult:
    dictionary: InstalledLookupDictionary
    artifact_path: Path
    manifest_path: Path
    provenance_path: Path


@dataclass(frozen=True)
class YomitanLookupResult:
    senses: tuple[dict[str, object], ...]
    glosses: tuple[dict[str, object], ...]
    dictionary: dict[str, object]
    dictionary_match: dict[str, object]


def import_yomitan_dictionary_zip(
    archive_path: Path,
    *,
    dictionaries_dir: Path,
    progress: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> YomitanDictionaryImportResult:
    source = Path(archive_path)
    if not source.exists() or not source.is_file():
        raise YomitanDictionaryImportError("Dictionary ZIP does not exist.")
    archive_sha256 = _sha256_file(source)
    target_base = Path(dictionaries_dir)
    target_base.mkdir(parents=True, exist_ok=True)

    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile) as exc:
        raise YomitanDictionaryImportError("The selected file is not a valid ZIP archive.") from exc
    with archive:
        members = _validated_archive_members(archive)
        index_member = members.get("index.json")
        if index_member is None:
            raise YomitanDictionaryImportError("Yomitan dictionary ZIP is missing index.json.")
        index = _read_json_member(archive, index_member, size_limit=MAX_INDEX_BYTES)
        metadata = _validated_index(index)
        bank_members = sorted(
            (
                (int(match.group(1)), member)
                for name, member in members.items()
                if (match := _TERM_BANK_NAME.fullmatch(name)) is not None
            ),
            key=lambda item: item[0],
        )
        if not bank_members:
            raise YomitanDictionaryImportError(
                "Yomitan dictionary ZIP does not contain any term_bank_*.json files."
            )
        pack_id = _pack_id_for_archive(metadata["title"], archive_sha256)
        existing = _existing_import_result(target_base, pack_id, archive_sha256)
        if existing is not None:
            return existing

        temp_base = Path(tempfile.mkdtemp(prefix=".yomitan-import-", dir=target_base))
        temp_pack_root = temp_base / pack_id
        temp_pack_root.mkdir(parents=True, exist_ok=True)
        artifact_path = temp_pack_root / "main.sqlite"
        imported_at = _utc_timestamp()
        term_count = 0
        skipped_term_count = 0
        total_banks = len(bank_members)
        try:
            with sqlite3.connect(str(artifact_path)) as conn:
                _create_dictionary_schema(conn)
                _write_dictionary_metadata(
                    conn,
                    {
                        **metadata,
                        "pack_id": pack_id,
                        "provider": "yomitan",
                        "archive_sha256": archive_sha256,
                        "imported_at_utc": imported_at,
                        "importer_version": YOMITAN_IMPORTER_VERSION,
                        "source_filename": source.name,
                    },
                )
                for processed_banks, (bank_index, member) in enumerate(bank_members, start=1):
                    _raise_if_cancelled(should_cancel)
                    rows = _read_json_member(
                        archive,
                        member,
                        size_limit=MAX_TERM_BANK_BYTES,
                    )
                    if not isinstance(rows, list):
                        raise YomitanDictionaryImportError(
                            f"{member.filename} must contain a JSON array."
                        )
                    inserted_count, skipped_count = _insert_term_rows(
                        conn,
                        rows,
                        bank_index=bank_index,
                        should_cancel=should_cancel,
                    )
                    term_count += inserted_count
                    skipped_term_count += skipped_count
                    if progress is not None:
                        progress(processed_banks, total_banks)
                if term_count <= 0:
                    raise YomitanDictionaryImportError(
                        "Yomitan dictionary did not contain any usable term entries."
                    )
                conn.execute(
                    "INSERT OR REPLACE INTO metadata (key, value_json) VALUES (?, ?)",
                    ("term_count", json.dumps(term_count)),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO metadata (key, value_json) VALUES (?, ?)",
                    ("skipped_term_count", json.dumps(skipped_term_count)),
                )
                conn.commit()

            dictionary_metadata = {
                **metadata,
                "pack_id": pack_id,
                "provider": "yomitan",
                "term_count": term_count,
                "skipped_term_count": skipped_term_count,
                "archive_sha256": archive_sha256,
                "imported_at_utc": imported_at,
                "importer_version": YOMITAN_IMPORTER_VERSION,
                "source_filename": source.name,
                "local_only": True,
            }
            (temp_pack_root / LOOKUP_DICTIONARY_METADATA_FILENAME).write_text(
                json.dumps(dictionary_metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest_path = write_installed_pack_manifest(
                temp_base,
                pack_id=pack_id,
                pack_kind="lookup_dictionary",
                provider="yomitan",
                local_kind="file",
                build_mode="yomitan_zip_to_sqlite",
                artifact_path=artifact_path,
                source_filename=source.name,
                sqlite_filename=artifact_path.name,
                raw_retained=False,
            )
            provenance_path = write_app_managed_pack_provenance(
                pack_root=temp_pack_root,
                pack_id=pack_id,
                pack_kind="lookup_dictionary",
                provider="yomitan",
                source_name=metadata["title"],
                source_url="user-supplied://local",
                license_status="not_redistributable",
                build_mode="yomitan_zip_to_sqlite",
                converter_version=str(YOMITAN_IMPORTER_VERSION),
                parser_profile="yomitan-term-bank-v3",
                parser_config={
                    "rendering": "safe_structured_content_v1",
                    "glossary_storage": "utf8_or_zlib_v1",
                    "media_imported": False,
                },
                artifact_path=artifact_path,
                source_filename=source.name,
                sqlite_filename=artifact_path.name,
                source_version=metadata["revision"],
                raw_artifact_sha256=archive_sha256,
                artifact_metrics={
                    "term_count": term_count,
                    "skipped_term_count": skipped_term_count,
                },
            )
            target_root = installed_pack_root(target_base, pack_id)
            if target_root.exists():
                shutil.rmtree(temp_base)
                existing = _existing_import_result(target_base, pack_id, archive_sha256)
                if existing is not None:
                    return existing
                raise YomitanDictionaryImportError(
                    f"Lookup dictionary destination already exists: {pack_id}"
                )
            os.replace(temp_pack_root, target_root)
            try:
                temp_base.rmdir()
            except OSError:
                pass
            dictionary = _installed_dictionary_from_metadata(dictionary_metadata)
            return YomitanDictionaryImportResult(
                dictionary=dictionary,
                artifact_path=target_root / artifact_path.name,
                manifest_path=target_root / manifest_path.name,
                provenance_path=target_root / provenance_path.name,
            )
        except Exception:
            shutil.rmtree(temp_base, ignore_errors=True)
            raise


def list_installed_lookup_dictionaries(
    dictionaries_dir: Path,
) -> tuple[InstalledLookupDictionary, ...]:
    base = Path(dictionaries_dir)
    if not base.exists() or not base.is_dir():
        return ()
    dictionaries: list[InstalledLookupDictionary] = []
    for metadata_path in sorted(base.glob(f"*/{LOOKUP_DICTIONARY_METADATA_FILENAME}")):
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        pack_id = str(payload.get("pack_id") or metadata_path.parent.name).strip()
        if resolve_installed_pack_artifact(base, pack_id) is None:
            continue
        dictionaries.append(_installed_dictionary_from_metadata(payload))
    return tuple(dictionaries)


def remove_installed_lookup_dictionary(
    dictionaries_dir: Path,
    pack_id: str,
) -> bool:
    normalized_pack_id = str(pack_id or "").strip()
    if _SAFE_PACK_ID.fullmatch(normalized_pack_id) is None:
        raise ValueError("Invalid lookup dictionary pack id.")
    base = Path(dictionaries_dir).resolve()
    target = installed_pack_root(base, normalized_pack_id).resolve()
    if target.parent != base:
        raise ValueError("Lookup dictionary path escapes the managed dictionary directory.")
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True


def lookup_yomitan_dictionary(
    artifact_path: Path,
    *,
    lookup_candidates: Sequence[str],
    surface: str,
    reading: str,
    sense_limit: int,
    gloss_limit: int,
) -> YomitanLookupResult | None:
    path = Path(artifact_path)
    if not path.exists() or not path.is_file():
        return None
    expression_candidates = _unique_normalized(
        (*lookup_candidates, surface, reading),
        japanese_reading=False,
    )
    reading_candidates = _unique_normalized(
        (*lookup_candidates, reading, surface),
        japanese_reading=True,
    )
    if not expression_candidates and not reading_candidates:
        return None
    expression_placeholders = ", ".join("?" for _ in expression_candidates)
    reading_placeholders = ", ".join("?" for _ in reading_candidates)
    conditions: list[str] = []
    parameters: list[str] = []
    if expression_candidates:
        conditions.append(f"expression_norm IN ({expression_placeholders})")
        parameters.extend(expression_candidates)
    if reading_candidates:
        conditions.append(f"reading_norm IN ({reading_placeholders})")
        parameters.extend(reading_candidates)
    expression_priority = "0"
    if expression_candidates:
        expression_priority = (
            f"CASE WHEN expression_norm IN ({expression_placeholders}) THEN 0 ELSE 1 END"
        )
        parameters.extend(expression_candidates)
    query = f"""
        SELECT expression, reading, definition_tags, rules, score,
               glossary_json, sequence, term_tags, bank_order, row_order
        FROM terms
        WHERE {" OR ".join(conditions)}
        ORDER BY {expression_priority}, score DESC, bank_order ASC, row_order ASC
        LIMIT 100
    """
    try:
        with sqlite3.connect(str(path)) as conn:
            rows = conn.execute(query, parameters).fetchall()
            metadata = _read_dictionary_metadata(conn)
    except (OSError, sqlite3.Error, json.JSONDecodeError):
        return None
    if not rows:
        return None

    normalized_surface = _normalize_term(surface)
    normalized_reading = _normalize_japanese_reading(reading)
    exact_reading_rows = [
        row
        for row in rows
        if normalized_reading
        and _normalize_term(row[0]) == normalized_surface
        and _row_supports_reading(row, normalized_reading)
    ]
    exact_surface_rows = [row for row in rows if _normalize_term(row[0]) == normalized_surface]
    reading_rows = [
        row for row in rows if normalized_reading and _row_supports_reading(row, normalized_reading)
    ]
    selected_rows = exact_reading_rows or exact_surface_rows or reading_rows
    if not selected_rows:
        selected_rows = rows

    decoded_rows: list[tuple[Sequence[object], object, bool]] = []
    for row in selected_rows:
        try:
            raw_glossary = _decode_glossary_payload(row[5])
        except (UnicodeDecodeError, json.JSONDecodeError, zlib.error):
            continue
        decoded_rows.append((row, raw_glossary, is_cross_reference_only_glossary(raw_glossary)))
    has_substantive_row = any(
        not cross_reference_only for _, _, cross_reference_only in decoded_rows
    )

    senses: list[dict[str, object]] = []
    glosses: list[dict[str, object]] = []
    for row, raw_glossary, cross_reference_only in decoded_rows:
        if has_substantive_row and cross_reference_only:
            continue
        definitions = definition_payloads(raw_glossary)
        if not definitions:
            continue
        labels = _space_separated_values(row[2], row[7])
        rules = _space_separated_values(row[3])
        sense: dict[str, object] = {
            "glosses": [
                {"text": str(item.get("text") or "")} for item in definitions[:gloss_limit]
            ],
            "source": str(metadata.get("pack_id") or ""),
            "source_kind": "installed_lookup_dictionary",
            "rank": len(senses) + 1,
        }
        structured_content = [
            node
            for item in definitions
            for node in item.get("structured_content", [])
            if isinstance(node, Mapping)
        ]
        if structured_content:
            sense["structured_content"] = structured_content
            if any(bool(item.get("structured_content_truncated")) for item in definitions):
                sense["structured_content_truncated"] = True
        if labels:
            sense["labels"] = labels[:4]
        if rules:
            sense["pos"] = rules
        senses.append(sense)
        for definition in definitions:
            text = str(definition.get("text") or "").strip()
            if not text:
                continue
            if text.casefold() in {str(item.get("text") or "").casefold() for item in glosses}:
                continue
            glosses.append(
                {
                    "text": text,
                    "source": str(metadata.get("pack_id") or ""),
                    "source_kind": "installed_lookup_dictionary",
                }
            )
            if len(glosses) >= gloss_limit:
                break
        if len(senses) >= sense_limit:
            break
    if not senses:
        return None

    matched_expression = str(selected_rows[0][0] or selected_rows[0][1] or "").strip()
    matched_reading = str(selected_rows[0][1] or matched_expression).strip()
    match_quality = "candidate_fallback"
    if exact_reading_rows:
        match_quality = "exact_surface_reading"
    elif _normalize_term(matched_expression) == normalized_surface:
        match_quality = "exact_surface"
    elif reading_rows:
        match_quality = "exact_reading"
    return YomitanLookupResult(
        senses=tuple(senses),
        glosses=tuple(glosses[:gloss_limit]),
        dictionary={
            "pack_id": str(metadata.get("pack_id") or ""),
            "provider": "yomitan",
            "source_kind": "installed_lookup_dictionary",
            "title": str(metadata.get("title") or "").strip(),
            "revision": str(metadata.get("revision") or "").strip(),
        },
        dictionary_match={
            "surface": matched_expression,
            "reading": matched_reading,
            "quality": match_quality,
        },
    )


def _validated_archive_members(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_MEMBERS:
        raise YomitanDictionaryImportError("Dictionary ZIP contains too many files.")
    total_size = 0
    members: dict[str, zipfile.ZipInfo] = {}
    for info in infos:
        name = str(info.filename or "")
        if not name or name.endswith("/"):
            continue
        if info.flag_bits & 0x1:
            raise YomitanDictionaryImportError("Encrypted dictionary ZIPs are not supported.")
        if "\\" in name:
            raise YomitanDictionaryImportError("Dictionary ZIP contains an unsafe file path.")
        pure_path = PurePosixPath(name)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            raise YomitanDictionaryImportError("Dictionary ZIP contains an unsafe file path.")
        if len(pure_path.parts) != 1:
            continue
        if name in members:
            raise YomitanDictionaryImportError(f"Dictionary ZIP contains duplicate {name} files.")
        total_size += max(0, int(info.file_size))
        if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise YomitanDictionaryImportError("Dictionary ZIP expands beyond the supported limit.")
        members[name] = info
    return members


def _validated_index(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise YomitanDictionaryImportError("Yomitan index.json must contain a JSON object.")
    title = str(value.get("title") or "").strip()
    revision = str(value.get("revision") or "").strip()
    format_value = value.get("format", value.get("version"))
    try:
        format_number = int(format_value)
    except (TypeError, ValueError) as exc:
        raise YomitanDictionaryImportError("Yomitan index.json is missing a valid format.") from exc
    if not title or not revision:
        raise YomitanDictionaryImportError("Yomitan index.json requires title and revision.")
    if format_number != 3:
        raise YomitanDictionaryImportError(
            f"Yomitan dictionary format {format_number} is not supported yet; format 3 is required."
        )
    return {
        "title": title,
        "revision": revision,
        "format": format_number,
        "author": str(value.get("author") or "").strip(),
        "url": str(value.get("url") or "").strip(),
        "description": str(value.get("description") or "").strip(),
        "attribution": str(value.get("attribution") or "").strip(),
        "source_language": str(value.get("sourceLanguage") or "").strip().lower(),
        "target_language": str(value.get("targetLanguage") or "").strip().lower(),
    }


def _read_json_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    *,
    size_limit: int,
) -> object:
    if member.file_size > size_limit:
        raise YomitanDictionaryImportError(f"{member.filename} exceeds the supported size limit.")
    try:
        with archive.open(member) as handle:
            payload = handle.read(size_limit + 1)
        if len(payload) > size_limit:
            raise YomitanDictionaryImportError(
                f"{member.filename} exceeds the supported size limit."
            )
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RuntimeError, zipfile.BadZipFile) as exc:
        raise YomitanDictionaryImportError(f"{member.filename} is not valid UTF-8 JSON.") from exc


def _create_dictionary_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = DELETE;
        PRAGMA synchronous = NORMAL;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL
        );
        CREATE TABLE terms (
            id INTEGER PRIMARY KEY,
            expression TEXT NOT NULL,
            expression_norm TEXT NOT NULL,
            reading TEXT NOT NULL,
            reading_norm TEXT NOT NULL,
            definition_tags TEXT,
            rules TEXT NOT NULL,
            score REAL NOT NULL,
            glossary_json TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            term_tags TEXT NOT NULL,
            bank_order INTEGER NOT NULL,
            row_order INTEGER NOT NULL
        );
        CREATE INDEX terms_expression_idx
            ON terms(expression_norm, reading_norm, score DESC);
        CREATE INDEX terms_reading_idx
            ON terms(reading_norm, expression_norm, score DESC);
        """
    )


def _write_dictionary_metadata(conn: sqlite3.Connection, metadata: Mapping[str, object]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO metadata (key, value_json) VALUES (?, ?)",
        ((str(key), json.dumps(value, ensure_ascii=False)) for key, value in metadata.items()),
    )


def _insert_term_rows(
    conn: sqlite3.Connection,
    rows: Sequence[object],
    *,
    bank_index: int,
    should_cancel: Callable[[], bool] | None,
) -> tuple[int, int]:
    prepared: list[tuple[object, ...]] = []
    skipped_count = 0
    for row_order, raw_row in enumerate(rows):
        if row_order % 500 == 0:
            _raise_if_cancelled(should_cancel)
        if not isinstance(raw_row, list) or len(raw_row) != 8:
            raise YomitanDictionaryImportError(
                f"term_bank_{bank_index}.json row {row_order + 1} must have 8 fields."
            )
        expression = str(raw_row[0] or "").strip()
        reading = str(raw_row[1] or "").strip()
        if not expression and not reading:
            skipped_count += 1
            continue
        if not isinstance(raw_row[5], list):
            raise YomitanDictionaryImportError(
                f"term_bank_{bank_index}.json row {row_order + 1} is malformed."
            )
        try:
            score = float(raw_row[4])
            sequence = int(raw_row[6])
        except (TypeError, ValueError) as exc:
            raise YomitanDictionaryImportError(
                f"term_bank_{bank_index}.json row {row_order + 1} has invalid numeric fields."
            ) from exc
        prepared.append(
            (
                expression,
                _normalize_term(expression),
                reading,
                _normalize_japanese_reading(reading or expression),
                str(raw_row[2] or "").strip(),
                str(raw_row[3] or "").strip(),
                score,
                _encode_glossary_payload(raw_row[5]),
                sequence,
                str(raw_row[7] or "").strip(),
                bank_index,
                row_order,
            )
        )
    conn.executemany(
        """
        INSERT INTO terms (
            expression, expression_norm, reading, reading_norm,
            definition_tags, rules, score, glossary_json, sequence,
            term_tags, bank_order, row_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        prepared,
    )
    return len(prepared), skipped_count


def _encode_glossary_payload(value: object) -> str | sqlite3.Binary:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    payload = text.encode("utf-8")
    if len(payload) < GLOSSARY_COMPRESSION_MIN_BYTES:
        return text
    compressed = zlib.compress(payload)
    if len(compressed) + len(_GLOSSARY_COMPRESSION_MAGIC) >= len(payload):
        return text
    return sqlite3.Binary(_GLOSSARY_COMPRESSION_MAGIC + compressed)


def _decode_glossary_payload(value: object) -> object:
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, bytes):
        payload = value
        if payload.startswith(_GLOSSARY_COMPRESSION_MAGIC):
            payload = zlib.decompress(payload[len(_GLOSSARY_COMPRESSION_MAGIC) :])
        return json.loads(payload.decode("utf-8"))
    return json.loads(str(value or "[]"))


def _read_dictionary_metadata(conn: sqlite3.Connection) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for key, value_json in conn.execute("SELECT key, value_json FROM metadata"):
        metadata[str(key)] = json.loads(str(value_json))
    return metadata


def _row_supports_reading(row: Sequence[object], reading: str) -> bool:
    row_reading = _normalize_japanese_reading(row[1] or row[0])
    return row_reading == reading


def _space_separated_values(*values: object) -> list[str]:
    result: list[str] = []
    for value in values:
        for item in str(value or "").split():
            if item and item not in result:
                result.append(item)
    return result


def _pack_id_for_archive(title: str, archive_sha256: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(title or "").casefold()).strip("-")
    slug = (slug or "dictionary")[:48].rstrip("-")
    return f"yomitan-{slug}-{archive_sha256[:12]}"


def _existing_import_result(
    dictionaries_dir: Path,
    pack_id: str,
    archive_sha256: str,
) -> YomitanDictionaryImportResult | None:
    root = installed_pack_root(dictionaries_dir, pack_id)
    metadata_path = root / LOOKUP_DICTIONARY_METADATA_FILENAME
    artifact_path = resolve_installed_pack_artifact(dictionaries_dir, pack_id)
    if artifact_path is None or not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, Mapping) or metadata.get("archive_sha256") != archive_sha256:
        return None
    return YomitanDictionaryImportResult(
        dictionary=_installed_dictionary_from_metadata(metadata),
        artifact_path=artifact_path,
        manifest_path=root / "manifest.json",
        provenance_path=root / "provenance.json",
    )


def _installed_dictionary_from_metadata(
    metadata: Mapping[str, object],
) -> InstalledLookupDictionary:
    return InstalledLookupDictionary(
        pack_id=str(metadata.get("pack_id") or "").strip(),
        title=str(metadata.get("title") or "").strip(),
        revision=str(metadata.get("revision") or "").strip(),
        provider=str(metadata.get("provider") or "yomitan").strip(),
        format=_safe_int(metadata.get("format"), default=3),
        term_count=_safe_int(metadata.get("term_count"), default=0),
        imported_at_utc=str(metadata.get("imported_at_utc") or "").strip(),
        source_filename=str(metadata.get("source_filename") or "").strip(),
        author=str(metadata.get("author") or "").strip(),
        source_language=str(metadata.get("source_language") or "").strip(),
        target_language=str(metadata.get("target_language") or "").strip(),
    )


def _raise_if_cancelled(should_cancel: Callable[[], bool] | None) -> None:
    if should_cancel is not None and should_cancel():
        raise YomitanDictionaryImportCancelled("Dictionary import was cancelled.")


def _unique_normalized(
    values: Sequence[object],
    *,
    japanese_reading: bool,
) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        text = _normalize_japanese_reading(value) if japanese_reading else _normalize_term(value)
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def _normalize_term(value: object) -> str:
    return str(value or "").strip().casefold()


def _normalize_japanese_reading(value: object) -> str:
    return normalize_reading(value, language_tag="ja").casefold()


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _safe_int(value: object, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "InstalledLookupDictionary",
    "YomitanDictionaryImportCancelled",
    "YomitanDictionaryImportError",
    "YomitanDictionaryImportResult",
    "YomitanLookupResult",
    "import_yomitan_dictionary_zip",
    "list_installed_lookup_dictionaries",
    "lookup_yomitan_dictionary",
    "remove_installed_lookup_dictionary",
]
