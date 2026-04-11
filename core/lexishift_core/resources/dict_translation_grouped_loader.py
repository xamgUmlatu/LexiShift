from __future__ import annotations

import sqlite3
from typing import Sequence


def load_sqlite_gloss_records_by_translation_ordered(
    conn: sqlite3.Connection,
    *,
    translations: Sequence[str] | None = None,
) -> dict[str, list[object]]:
    from lexishift_core.resources.dict_loaders import (
        FreedictGlossRecord,
        _sqlite_has_column,
        _sqlite_has_table,
    )
    from lexishift_core.resources.dict_gloss_metadata import build_auxiliary_gloss_metadata

    mapping: dict[str, list[object]] = {}
    headword_index_by_translation: dict[str, dict[str, int]] = {}
    has_entry_meta = _sqlite_has_table(conn, "entry_meta")
    has_translation_meta = _sqlite_has_table(conn, "translation_meta")
    has_examples_json = _sqlite_has_column(conn, "sense_glosses", "examples_json")
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
    if translations is not None:
        if not translations:
            return mapping
        placeholders = ", ".join("?" for _ in translations)
        where_clause = f"WHERE sg.translation_lc IN ({placeholders})"
        parameters = tuple(translations)
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
        ORDER BY sg.translation_lc, sg.headword_lc, sg.entry_ord, sg.sense_ord, sg.gloss_ord, sg.headword
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
            metadata = build_auxiliary_gloss_metadata(
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
            )
            bucket = mapping.setdefault(translation_text, [])
            index_by_headword = headword_index_by_translation.setdefault(translation_text, {})
            existing_index = index_by_headword.get(headword_text)
            normalized_pos_raw = str(pos_raw or "").strip()
            if existing_index is None:
                bucket.append(
                    FreedictGlossRecord(
                        translation=headword_text,
                        pos_raw=normalized_pos_raw,
                        metadata=metadata,
                    )
                )
                index_by_headword[headword_text] = len(bucket) - 1
                continue
            existing = bucket[existing_index]
            if existing.pos_raw or not normalized_pos_raw:
                continue
            bucket[existing_index] = FreedictGlossRecord(
                translation=headword_text,
                pos_raw=normalized_pos_raw,
                metadata=existing.metadata or metadata,
            )
    finally:
        cursor.close()
    return mapping
