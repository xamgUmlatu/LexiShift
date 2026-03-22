from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
import gzip
import json
from pathlib import Path
import sqlite3
from typing import TextIO


SQLITE_MAGIC = b"SQLite format 3"
DEFAULT_SKIP_SENSE_TAGS = frozenset({"form-of", "alt-of", "inflection-of"})
DEFAULT_SKIP_GLOSS_PREFIXES = (
    "inflection of ",
    "plural of ",
    "alternative form of ",
    "alternative spelling of ",
    "alternative typography of ",
    "misspelling of ",
    "clipping of ",
    "abbreviation of ",
    "acronym of ",
)


def convert_kaikki_glosses_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    source_lang_code: str,
    gloss_language: str = "en",
    source_provider: str = "kaikki",
    source_dump: str = "enwiktionary",
    overwrite: bool = False,
    batch_size: int = 1000,
    skip_sense_tags: Iterable[str] = DEFAULT_SKIP_SENSE_TAGS,
    skip_gloss_prefixes: Iterable[str] = DEFAULT_SKIP_GLOSS_PREFIXES,
) -> dict[str, object]:
    normalized_source_lang = str(source_lang_code or "").strip().lower()
    if not normalized_source_lang:
        raise ValueError("source_lang_code is required")
    conn = _init_db(output_path, overwrite=overwrite)
    entry_meta_batch: list[tuple[object, ...]] = []
    sense_gloss_batch: list[tuple[object, ...]] = []
    translation_meta_batch: list[tuple[object, ...]] = []
    total_records = 0
    selected_records = 0
    inserted_entry_meta = 0
    inserted_sense_rows = 0
    skipped_empty_headword = 0
    skipped_non_matching_lang = 0
    skipped_no_usable_glosses = 0
    line_count = 0
    entry_ord = 0
    skip_tag_set = {str(tag).strip().lower() for tag in skip_sense_tags if str(tag).strip()}
    skip_prefixes = tuple(
        str(prefix).strip().lower() for prefix in skip_gloss_prefixes if str(prefix).strip()
    )

    try:
        with _open_text_jsonl(input_path) as handle:
            for line_count, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                total_records += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on line {line_count}: {exc}") from exc
                if not isinstance(record, dict):
                    continue
                record_lang_code = str(record.get("lang_code") or "").strip().lower()
                if record_lang_code != normalized_source_lang:
                    skipped_non_matching_lang += 1
                    continue
                headword = _normalize_text(record.get("word"))
                if not headword:
                    skipped_empty_headword += 1
                    continue
                headword_lc = headword.lower()
                pos = _normalize_text(record.get("pos"))
                pos_title = _normalize_text(record.get("pos_title"))
                senses = record.get("senses")
                if not isinstance(senses, list):
                    senses = []
                candidate_rows: list[tuple[object, ...]] = []
                for sense_ord, sense in enumerate(senses):
                    if not isinstance(sense, dict):
                        continue
                    if _should_skip_sense(sense, skip_tag_set=skip_tag_set):
                        continue
                    glosses = _normalize_string_list(sense.get("glosses"))
                    raw_glosses = _normalize_string_list(sense.get("raw_glosses"))
                    usable_glosses = glosses or raw_glosses
                    if not usable_glosses:
                        continue
                    raw_glosses_json = _json_or_none(raw_glosses)
                    tags_json = _json_or_none(_normalize_string_list(sense.get("tags")))
                    topics_json = _json_or_none(_normalize_string_list(sense.get("topics")))
                    categories_json = _json_or_none(_normalize_string_list(sense.get("categories")))
                    form_of_json = _json_or_none(_normalize_json_array(sense.get("form_of")))
                    alt_of_json = _json_or_none(_normalize_json_array(sense.get("alt_of")))
                    gloss_ord = 0
                    for gloss in usable_glosses:
                        if _should_skip_gloss(gloss, skip_prefixes=skip_prefixes):
                            continue
                        gloss_text = _normalize_text(gloss)
                        if not gloss_text:
                            continue
                        candidate_rows.append(
                            (
                                sense_ord,
                                gloss_ord,
                                headword,
                                headword_lc,
                                gloss_text,
                                gloss_text.lower(),
                                pos,
                                raw_glosses_json,
                                tags_json,
                                topics_json,
                                categories_json,
                                form_of_json,
                                alt_of_json,
                            )
                        )
                        gloss_ord += 1
                if not candidate_rows:
                    skipped_no_usable_glosses += 1
                    continue
                entry_ord += 1
                selected_records += 1
                entry_meta_batch.append(
                    (
                        entry_ord,
                        headword,
                        headword_lc,
                        _normalize_text(record.get("lang")),
                        record_lang_code,
                        pos,
                        pos_title,
                        _json_or_none(_normalize_string_list(record.get("categories"))),
                        _json_or_none(_normalize_json_array(record.get("forms"))),
                        _json_or_none(_normalize_json_array(record.get("sounds"))),
                        _json_or_none(_normalize_json_array(record.get("synonyms"))),
                        _json_or_none(_normalize_string_list(record.get("tags"))),
                        _normalize_text(record.get("etymology_text")),
                    )
                )
                inserted_entry_meta += 1
                for row in candidate_rows:
                    sense_gloss_batch.append((entry_ord, *row))
                inserted_sense_rows += len(candidate_rows)
                if len(entry_meta_batch) >= batch_size or len(sense_gloss_batch) >= batch_size * 4:
                    _flush_batches(
                        conn,
                        entry_meta_batch,
                        sense_gloss_batch,
                        translation_meta_batch,
                    )
        _flush_batches(conn, entry_meta_batch, sense_gloss_batch, translation_meta_batch)
        _finalize_entries(conn)
        metadata = {
            "converter": "kaikki_glosses_to_sqlite",
            "source_provider": str(source_provider or "").strip().lower() or "kaikki",
            "source_dump": str(source_dump or "").strip().lower() or "enwiktionary",
            "source_lang_code": normalized_source_lang,
            "gloss_language": str(gloss_language or "").strip().lower() or "en",
            "input_path": str(input_path),
            "built_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "line_count": int(line_count),
            "total_records": int(total_records),
            "selected_records": int(selected_records),
            "inserted_entry_meta": int(inserted_entry_meta),
            "inserted_sense_rows": int(inserted_sense_rows),
            "skipped_non_matching_lang": int(skipped_non_matching_lang),
            "skipped_empty_headword": int(skipped_empty_headword),
            "skipped_no_usable_glosses": int(skipped_no_usable_glosses),
            "skip_sense_tags": sorted(skip_tag_set),
            "skip_gloss_prefixes": list(skip_prefixes),
        }
        conn.execute("DELETE FROM meta")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("metadata", json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
        )
        conn.commit()
        return metadata
    finally:
        conn.close()


def convert_kaikki_translations_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    source_lang_code: str,
    target_lang_code: str,
    translation_language: str = "",
    source_provider: str = "kaikki",
    source_dump: str = "enwiktionary",
    overwrite: bool = False,
    batch_size: int = 1000,
) -> dict[str, object]:
    normalized_source_lang = str(source_lang_code or "").strip().lower()
    if not normalized_source_lang:
        raise ValueError("source_lang_code is required")
    normalized_target_lang = str(target_lang_code or "").strip().lower()
    if not normalized_target_lang:
        raise ValueError("target_lang_code is required")
    conn = _init_db(output_path, overwrite=overwrite)
    entry_meta_batch: list[tuple[object, ...]] = []
    sense_gloss_batch: list[tuple[object, ...]] = []
    translation_meta_batch: list[tuple[object, ...]] = []
    total_records = 0
    selected_records = 0
    inserted_entry_meta = 0
    inserted_sense_rows = 0
    inserted_translation_meta = 0
    skipped_empty_headword = 0
    skipped_non_matching_lang = 0
    skipped_no_usable_translations = 0
    line_count = 0
    entry_ord = 0

    try:
        with _open_text_jsonl(input_path) as handle:
            for line_count, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                total_records += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on line {line_count}: {exc}") from exc
                if not isinstance(record, dict):
                    continue
                record_lang_code = str(record.get("lang_code") or "").strip().lower()
                if record_lang_code != normalized_source_lang:
                    skipped_non_matching_lang += 1
                    continue
                headword = _normalize_text(record.get("word"))
                if not headword:
                    skipped_empty_headword += 1
                    continue
                headword_lc = headword.lower()
                pos = _normalize_text(record.get("pos"))
                pos_title = _normalize_text(record.get("pos_title"))
                translations = record.get("translations")
                if not isinstance(translations, list):
                    translations = []
                candidate_rows: list[tuple[object, ...]] = []
                translation_meta_rows: list[tuple[object, ...]] = []
                sense_ord_by_key: dict[str, int] = {}
                gloss_ord_by_sense: dict[int, int] = {}
                next_sense_ord = 0
                for translation in translations:
                    if not isinstance(translation, dict):
                        continue
                    translation_lang_code = _normalize_translation_lang_code(translation)
                    if translation_lang_code != normalized_target_lang:
                        continue
                    translation_text = _normalize_text(translation.get("word"))
                    if not translation_text:
                        continue
                    sense_text = _normalize_text(translation.get("sense"))
                    english_text = _normalize_text(translation.get("english"))
                    sense_fragments: list[str] = []
                    for fragment in (sense_text, english_text):
                        if fragment and fragment not in sense_fragments:
                            sense_fragments.append(fragment)
                    sense_key = " | ".join(sense_fragments).lower()
                    if sense_key:
                        sense_ord = sense_ord_by_key.get(sense_key)
                        if sense_ord is None:
                            sense_ord = next_sense_ord
                            sense_ord_by_key[sense_key] = sense_ord
                            next_sense_ord += 1
                    else:
                        sense_ord = next_sense_ord
                        next_sense_ord += 1
                    gloss_ord = gloss_ord_by_sense.get(sense_ord, 0)
                    gloss_ord_by_sense[sense_ord] = gloss_ord + 1
                    tags_json = _json_or_none(_normalize_string_list(translation.get("tags")))
                    raw_glosses_json = _json_or_none(sense_fragments)
                    candidate_rows.append(
                        (
                            sense_ord,
                            gloss_ord,
                            headword,
                            headword_lc,
                            translation_text,
                            translation_text.lower(),
                            pos,
                            raw_glosses_json,
                            tags_json,
                            None,
                            None,
                            None,
                            None,
                        )
                    )
                    translation_meta_rows.append(
                        (
                            sense_ord,
                            gloss_ord,
                            sense_text or None,
                            english_text or None,
                            _normalize_text(translation.get("note")) or None,
                            _normalize_text(translation.get("roman")) or None,
                            tags_json,
                            _normalize_text(translation.get("code")) or None,
                            _normalize_text(translation.get("lang")) or None,
                            translation_lang_code or None,
                        )
                    )
                if not candidate_rows:
                    skipped_no_usable_translations += 1
                    continue
                entry_ord += 1
                selected_records += 1
                entry_meta_batch.append(
                    (
                        entry_ord,
                        headword,
                        headword_lc,
                        _normalize_text(record.get("lang")),
                        record_lang_code,
                        pos,
                        pos_title,
                        _json_or_none(_normalize_string_list(record.get("categories"))),
                        _json_or_none(_normalize_json_array(record.get("forms"))),
                        _json_or_none(_normalize_json_array(record.get("sounds"))),
                        _json_or_none(_normalize_json_array(record.get("synonyms"))),
                        _json_or_none(_normalize_string_list(record.get("tags"))),
                        _normalize_text(record.get("etymology_text")),
                    )
                )
                inserted_entry_meta += 1
                for row in candidate_rows:
                    sense_gloss_batch.append((entry_ord, *row))
                inserted_sense_rows += len(candidate_rows)
                for row in translation_meta_rows:
                    translation_meta_batch.append((entry_ord, *row))
                inserted_translation_meta += len(translation_meta_rows)
                if len(entry_meta_batch) >= batch_size or len(sense_gloss_batch) >= batch_size * 4:
                    _flush_batches(
                        conn,
                        entry_meta_batch,
                        sense_gloss_batch,
                        translation_meta_batch,
                    )
        _flush_batches(conn, entry_meta_batch, sense_gloss_batch, translation_meta_batch)
        _finalize_entries(conn)
        metadata = {
            "converter": "kaikki_translations_to_sqlite",
            "source_provider": str(source_provider or "").strip().lower() or "kaikki",
            "source_dump": str(source_dump or "").strip().lower() or "enwiktionary",
            "source_lang_code": normalized_source_lang,
            "target_lang_code": normalized_target_lang,
            "translation_language": str(translation_language or "").strip().lower()
            or normalized_target_lang,
            "input_path": str(input_path),
            "built_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "line_count": int(line_count),
            "total_records": int(total_records),
            "selected_records": int(selected_records),
            "inserted_entry_meta": int(inserted_entry_meta),
            "inserted_sense_rows": int(inserted_sense_rows),
            "inserted_translation_meta": int(inserted_translation_meta),
            "skipped_non_matching_lang": int(skipped_non_matching_lang),
            "skipped_empty_headword": int(skipped_empty_headword),
            "skipped_no_usable_translations": int(skipped_no_usable_translations),
        }
        conn.execute("DELETE FROM meta")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("metadata", json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
        )
        conn.commit()
        return metadata
    finally:
        conn.close()


def is_sqlite_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            return handle.read(16).startswith(SQLITE_MAGIC)
    except OSError:
        return False


def _init_db(output_path: Path, *, overwrite: bool) -> sqlite3.Connection:
    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output_path}")
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
    conn.execute(
        "CREATE TABLE entry_meta ("
        "entry_ord INTEGER PRIMARY KEY, "
        "headword TEXT NOT NULL, "
        "headword_lc TEXT NOT NULL, "
        "lang TEXT, "
        "lang_code TEXT, "
        "pos TEXT, "
        "pos_title TEXT, "
        "categories_json TEXT, "
        "forms_json TEXT, "
        "sounds_json TEXT, "
        "synonyms_json TEXT, "
        "tags_json TEXT, "
        "etymology_text TEXT"
        ");"
    )
    conn.execute(
        "CREATE TABLE sense_glosses ("
        "entry_ord INTEGER NOT NULL, "
        "sense_ord INTEGER NOT NULL, "
        "gloss_ord INTEGER NOT NULL, "
        "headword TEXT NOT NULL, "
        "headword_lc TEXT NOT NULL, "
        "translation TEXT NOT NULL, "
        "translation_lc TEXT NOT NULL, "
        "pos TEXT, "
        "raw_glosses_json TEXT, "
        "tags_json TEXT, "
        "topics_json TEXT, "
        "categories_json TEXT, "
        "form_of_json TEXT, "
        "alt_of_json TEXT, "
        "PRIMARY KEY (entry_ord, sense_ord, gloss_ord)"
        ");"
    )
    conn.execute(
        "CREATE TABLE translation_meta ("
        "entry_ord INTEGER NOT NULL, "
        "sense_ord INTEGER NOT NULL, "
        "gloss_ord INTEGER NOT NULL, "
        "sense_text TEXT, "
        "english_text TEXT, "
        "note_text TEXT, "
        "roman_text TEXT, "
        "tags_json TEXT, "
        "code TEXT, "
        "lang TEXT, "
        "lang_code TEXT, "
        "PRIMARY KEY (entry_ord, sense_ord, gloss_ord)"
        ");"
    )
    conn.execute("CREATE INDEX idx_entry_meta_headword_lc ON entry_meta(headword_lc);")
    conn.execute("CREATE INDEX idx_sense_glosses_headword_lc ON sense_glosses(headword_lc);")
    conn.execute(
        "CREATE INDEX idx_sense_glosses_pair ON sense_glosses(headword_lc, translation_lc);"
    )
    conn.execute("CREATE INDEX idx_translation_meta_entry_ord ON translation_meta(entry_ord);")
    return conn


def _flush_batches(
    conn: sqlite3.Connection,
    entry_meta_batch: list[tuple[object, ...]],
    sense_gloss_batch: list[tuple[object, ...]],
    translation_meta_batch: list[tuple[object, ...]],
) -> None:
    if entry_meta_batch:
        conn.executemany(
            "INSERT INTO entry_meta ("
            "entry_ord, headword, headword_lc, lang, lang_code, pos, pos_title, "
            "categories_json, forms_json, sounds_json, synonyms_json, tags_json, etymology_text"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            entry_meta_batch,
        )
        entry_meta_batch.clear()
    if sense_gloss_batch:
        conn.executemany(
            "INSERT INTO sense_glosses ("
            "entry_ord, sense_ord, gloss_ord, headword, headword_lc, translation, "
            "translation_lc, pos, raw_glosses_json, tags_json, topics_json, "
            "categories_json, form_of_json, alt_of_json"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sense_gloss_batch,
        )
        sense_gloss_batch.clear()
    if translation_meta_batch:
        conn.executemany(
            "INSERT INTO translation_meta ("
            "entry_ord, sense_ord, gloss_ord, sense_text, english_text, note_text, "
            "roman_text, tags_json, code, lang, lang_code"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            translation_meta_batch,
        )
        translation_meta_batch.clear()
    conn.commit()


def _finalize_entries(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE entries ("
        "headword TEXT NOT NULL, "
        "headword_lc TEXT NOT NULL, "
        "translation TEXT NOT NULL, "
        "translation_lc TEXT NOT NULL, "
        "rank INTEGER NOT NULL, "
        "pos TEXT, "
        "entry_ord INTEGER NOT NULL, "
        "gloss_ord INTEGER NOT NULL, "
        "PRIMARY KEY (headword_lc, translation_lc)"
        ");"
    )
    conn.execute(
        """
        WITH pair_first AS (
            SELECT
                headword,
                headword_lc,
                translation,
                translation_lc,
                pos,
                entry_ord,
                sense_ord,
                gloss_ord,
                ROW_NUMBER() OVER (
                    PARTITION BY headword_lc, translation_lc
                    ORDER BY entry_ord, sense_ord, gloss_ord, translation, headword
                ) AS pair_rownum
            FROM sense_glosses
        ),
        dedup AS (
            SELECT
                headword,
                headword_lc,
                translation,
                translation_lc,
                entry_ord,
                sense_ord,
                gloss_ord
            FROM pair_first
            WHERE pair_rownum = 1
        ),
        pos_agg AS (
            SELECT
                headword_lc,
                translation_lc,
                REPLACE(group_concat(DISTINCT pos), ',', '|') AS pos
            FROM sense_glosses
            WHERE TRIM(COALESCE(pos, '')) <> ''
            GROUP BY headword_lc, translation_lc
        ),
        ranked AS (
            SELECT
                dedup.headword AS headword,
                dedup.headword_lc AS headword_lc,
                dedup.translation AS translation,
                dedup.translation_lc AS translation_lc,
                ROW_NUMBER() OVER (
                    PARTITION BY dedup.headword_lc
                    ORDER BY
                        dedup.entry_ord,
                        dedup.sense_ord,
                        dedup.gloss_ord,
                        dedup.translation_lc,
                        dedup.headword
                ) AS rank,
                COALESCE(pos_agg.pos, '') AS pos,
                dedup.entry_ord AS entry_ord,
                dedup.gloss_ord AS gloss_ord
            FROM dedup
            LEFT JOIN pos_agg
                ON pos_agg.headword_lc = dedup.headword_lc
               AND pos_agg.translation_lc = dedup.translation_lc
        )
        INSERT INTO entries (
            headword,
            headword_lc,
            translation,
            translation_lc,
            rank,
            pos,
            entry_ord,
            gloss_ord
        )
        SELECT
            headword,
            headword_lc,
            translation,
            translation_lc,
            rank,
            pos,
            entry_ord,
            gloss_ord
        FROM ranked
        ORDER BY headword_lc, rank, headword
        """
    )
    conn.execute("CREATE INDEX idx_entries_headword ON entries(headword);")
    conn.execute("CREATE INDEX idx_entries_headword_lc_rank ON entries(headword_lc, rank);")
    conn.execute("CREATE INDEX idx_entries_translation_lc ON entries(translation_lc);")
    conn.commit()


@contextmanager
def _open_text_jsonl(path: Path) -> Iterator[TextIO]:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            yield handle
        return
    with path.open("r", encoding="utf-8") as handle:
        yield handle


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = _normalize_text(item)
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_json_array(value: object) -> list[dict[str, object] | str]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, object] | str] = []
    for item in value:
        if isinstance(item, dict):
            cleaned = _normalize_json_object(item)
            if cleaned:
                normalized.append(cleaned)
            continue
        text = _normalize_text(item)
        if text:
            normalized.append(text)
    return normalized


def _normalize_json_object(value: dict[object, object]) -> dict[str, object]:
    cleaned: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        key = _normalize_text(raw_key)
        if not key:
            continue
        if isinstance(raw_value, str):
            text = _normalize_text(raw_value)
            if text:
                cleaned[key] = text
            continue
        if isinstance(raw_value, list):
            items = _normalize_json_array(raw_value)
            if items:
                cleaned[key] = items
            continue
        if isinstance(raw_value, dict):
            child = _normalize_json_object(raw_value)
            if child:
                cleaned[key] = child
            continue
        if raw_value is not None:
            cleaned[key] = raw_value
    return cleaned


def _json_or_none(value: object) -> str | None:
    if value in (None, "", [], {}):
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_translation_lang_code(translation: dict[object, object]) -> str:
    return _normalize_text(translation.get("lang_code") or translation.get("code")).lower()


def _should_skip_sense(sense: dict[object, object], *, skip_tag_set: set[str]) -> bool:
    tags = {
        str(tag).strip().lower()
        for tag in _normalize_string_list(sense.get("tags"))
        if str(tag).strip()
    }
    if tags & skip_tag_set:
        return True
    form_of = sense.get("form_of")
    if isinstance(form_of, list) and form_of:
        return True
    alt_of = sense.get("alt_of")
    if isinstance(alt_of, list) and alt_of:
        return True
    return False


def _should_skip_gloss(gloss: object, *, skip_prefixes: tuple[str, ...]) -> bool:
    text = _normalize_text(gloss).lower()
    if not text:
        return True
    return any(text.startswith(prefix) for prefix in skip_prefixes)


__all__ = [
    "DEFAULT_SKIP_GLOSS_PREFIXES",
    "DEFAULT_SKIP_SENSE_TAGS",
    "convert_kaikki_glosses_to_sqlite",
    "convert_kaikki_translations_to_sqlite",
    "is_sqlite_file",
]
