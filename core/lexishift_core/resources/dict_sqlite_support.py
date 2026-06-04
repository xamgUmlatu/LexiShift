from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Callable, Iterator, Mapping, Optional, Sequence, TypeVar


_RecordT = TypeVar("_RecordT")


@dataclass(frozen=True)
class _AuxiliarySqliteGlossRow:
    headword: str
    translation: str
    pos_raw: str
    metadata: Mapping[str, object]


def sqlite_has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return bool(row)


def sqlite_has_column(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    normalized_column = str(column_name or "").strip()
    if not normalized_column:
        return False
    try:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    except sqlite3.Error:
        return False
    return any(str(row[1] or "").strip() == normalized_column for row in rows if len(row) > 1)


def load_auxiliary_sqlite_gloss_records_ordered(
    conn: sqlite3.Connection,
    *,
    headwords: Optional[Sequence[str]] = None,
    record_factory: Callable[..., _RecordT],
    metadata_builder,
) -> dict[str, list[_RecordT]]:
    mapping: dict[str, list[_RecordT]] = {}
    translation_index_by_headword: dict[str, dict[str, int]] = {}
    if headwords is not None:
        if not headwords:
            return mapping
    for row in _iter_auxiliary_sqlite_gloss_rows_ordered(
        conn,
        filter_column="sg.headword_lc",
        filter_values=headwords,
        order_by=(
            "sg.headword_lc, sg.entry_ord, sg.sense_ord, sg.gloss_ord, sg.translation, sg.headword"
        ),
        metadata_builder=metadata_builder,
    ):
        bucket = mapping.setdefault(row.headword, [])
        index_by_translation = translation_index_by_headword.setdefault(
            row.headword,
            {},
        )
        existing_index = index_by_translation.get(row.translation)
        if existing_index is None:
            bucket.append(
                record_factory(
                    translation=row.translation,
                    pos_raw=row.pos_raw,
                    metadata=row.metadata,
                )
            )
            index_by_translation[row.translation] = len(bucket) - 1
            continue
        existing = bucket[existing_index]
        if getattr(existing, "pos_raw", "") or not row.pos_raw:
            continue
        bucket[existing_index] = record_factory(
            translation=row.translation,
            pos_raw=row.pos_raw,
            metadata=getattr(existing, "metadata", None) or row.metadata,
        )
    return mapping


def load_auxiliary_sqlite_gloss_records_by_translation_ordered(
    conn: sqlite3.Connection,
    *,
    translations: Optional[Sequence[str]] = None,
    record_factory: Callable[..., _RecordT],
    metadata_builder,
) -> dict[str, list[_RecordT]]:
    mapping: dict[str, list[_RecordT]] = {}
    headword_index_by_translation: dict[str, dict[str, int]] = {}
    if translations is not None:
        if not translations:
            return mapping
    for row in _iter_auxiliary_sqlite_gloss_rows_ordered(
        conn,
        filter_column="sg.translation_lc",
        filter_values=translations,
        order_by=(
            "sg.translation_lc, sg.headword_lc, sg.entry_ord, "
            "sg.sense_ord, sg.gloss_ord, sg.headword"
        ),
        metadata_builder=metadata_builder,
    ):
        bucket = mapping.setdefault(row.translation, [])
        index_by_headword = headword_index_by_translation.setdefault(
            row.translation,
            {},
        )
        existing_index = index_by_headword.get(row.headword)
        if existing_index is None:
            bucket.append(
                record_factory(
                    translation=row.headword,
                    pos_raw=row.pos_raw,
                    metadata=row.metadata,
                )
            )
            index_by_headword[row.headword] = len(bucket) - 1
            continue
        existing = bucket[existing_index]
        if getattr(existing, "pos_raw", "") or not row.pos_raw:
            continue
        bucket[existing_index] = record_factory(
            translation=row.headword,
            pos_raw=row.pos_raw,
            metadata=getattr(existing, "metadata", None) or row.metadata,
        )
    return mapping


def _iter_auxiliary_sqlite_gloss_rows_ordered(
    conn: sqlite3.Connection,
    *,
    filter_column: str,
    filter_values: Optional[Sequence[str]],
    order_by: str,
    metadata_builder,
) -> Iterator[_AuxiliarySqliteGlossRow]:
    has_entry_meta = sqlite_has_table(conn, "entry_meta")
    has_translation_meta = sqlite_has_table(conn, "translation_meta")
    has_examples_json = sqlite_has_column(conn, "sense_glosses", "examples_json")
    entry_meta_join = (
        "LEFT JOIN entry_meta em ON em.entry_ord = sg.entry_ord" if has_entry_meta else ""
    )
    translation_meta_join = (
        "LEFT JOIN translation_meta tm "
        "ON tm.entry_ord = sg.entry_ord AND tm.sense_ord = sg.sense_ord AND tm.gloss_ord = sg.gloss_ord"
        if has_translation_meta
        else ""
    )
    where_clause = ""
    parameters: tuple[object, ...] = ()
    if filter_values is not None:
        if not filter_values:
            return
        placeholders = ", ".join("?" for _ in filter_values)
        where_clause = f"WHERE {filter_column} IN ({placeholders})"
        parameters = tuple(filter_values)
    cursor = conn.execute(
        f"""
        SELECT
            sg.headword,
            sg.translation,
            sg.pos,
            sg.entry_ord,
            sg.sense_ord,
            sg.gloss_ord,
            sg.raw_glosses_json,
            {"sg.examples_json" if has_examples_json else "NULL"} AS examples_json,
            sg.tags_json,
            sg.topics_json,
            sg.categories_json,
            sg.form_of_json,
            sg.alt_of_json,
            {"em.pos_title" if has_entry_meta else "NULL"} AS entry_pos_title,
            {"em.tags_json" if has_entry_meta else "NULL"} AS entry_tags_json,
            {"em.categories_json" if has_entry_meta else "NULL"} AS entry_categories_json,
            {"tm.sense_text" if has_translation_meta else "NULL"} AS translation_sense_text,
            {"tm.english_text" if has_translation_meta else "NULL"} AS translation_english_text,
            {"tm.note_text" if has_translation_meta else "NULL"} AS translation_note_text,
            {"tm.roman_text" if has_translation_meta else "NULL"} AS translation_roman_text,
            {"tm.tags_json" if has_translation_meta else "NULL"} AS translation_tags_json
        FROM sense_glosses sg
        {entry_meta_join}
        {translation_meta_join}
        {where_clause}
        ORDER BY {order_by}
        """,
        parameters,
    )
    try:
        for row in cursor:
            (
                headword,
                translation,
                pos_raw,
                entry_ord,
                sense_ord,
                gloss_ord,
                raw_glosses_json,
                sense_examples_json,
                sense_tags_json,
                sense_topics_json,
                sense_categories_json,
                form_of_json,
                alt_of_json,
                entry_pos_title,
                entry_tags_json,
                entry_categories_json,
                translation_sense_text,
                translation_english_text,
                translation_note_text,
                translation_roman_text,
                translation_tags_json,
            ) = row
            headword_text = str(headword or "").strip()
            translation_text = str(translation or "").strip()
            if not headword_text or not translation_text:
                continue
            yield _AuxiliarySqliteGlossRow(
                headword=headword_text,
                translation=translation_text,
                pos_raw=str(pos_raw or "").strip(),
                metadata=metadata_builder(
                    entry_ord=entry_ord,
                    sense_ord=sense_ord,
                    gloss_ord=gloss_ord,
                    raw_glosses_json=raw_glosses_json,
                    sense_examples_json=sense_examples_json,
                    sense_tags_json=sense_tags_json,
                    sense_topics_json=sense_topics_json,
                    sense_categories_json=sense_categories_json,
                    form_of_json=form_of_json,
                    alt_of_json=alt_of_json,
                    entry_pos_title=entry_pos_title,
                    entry_tags_json=entry_tags_json,
                    entry_categories_json=entry_categories_json,
                    translation_sense_text=translation_sense_text,
                    translation_english_text=translation_english_text,
                    translation_note_text=translation_note_text,
                    translation_roman_text=translation_roman_text,
                    translation_tags_json=translation_tags_json,
                ),
            )
    finally:
        cursor.close()


def load_auxiliary_sqlite_headwords(conn: sqlite3.Connection) -> tuple[str, ...]:
    cursor = conn.execute("SELECT headword FROM sense_glosses ORDER BY headword_lc, headword")
    try:
        return _collect_sqlite_headwords(cursor)
    finally:
        cursor.close()


def load_auxiliary_sqlite_gloss_base_forms(conn: sqlite3.Connection, *, sanitize_gloss) -> set[str]:
    cursor = conn.execute("SELECT translation FROM sense_glosses")
    try:
        return _collect_sqlite_gloss_base_forms(cursor, sanitize_gloss=sanitize_gloss)
    finally:
        cursor.close()


def _collect_sqlite_headwords(cursor: sqlite3.Cursor) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for (headword,) in cursor:
        text = str(headword or "").strip()
        if not text:
            continue
        normalized = text.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(text)
    return tuple(ordered)


def _collect_sqlite_gloss_base_forms(cursor: sqlite3.Cursor, *, sanitize_gloss) -> set[str]:
    base_forms: set[str] = set()
    for (translation,) in cursor:
        normalized = sanitize_gloss(translation).lower()
        if normalized:
            base_forms.add(normalized)
    return base_forms
