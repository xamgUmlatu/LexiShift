from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import sqlite3
from typing import Iterable, Mapping, Optional, Sequence
from xml.etree import ElementTree

from lexishift_core.resources.japanese_script import (
    contains_kana,
    contains_kanji,
    kana_to_romaji,
)
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss


XML_LANG_KEY = "{http://www.w3.org/XML/1998/namespace}lang"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


@dataclass(frozen=True)
class JmdictEntryRecord:
    kanji_forms: tuple[str, ...]
    kana_forms: tuple[str, ...]
    glosses: tuple[str, ...]
    pos_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class FreedictGlossRecord:
    translation: str
    pos_raw: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


def load_jmdict_glosses(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> dict[str, set[str]]:
    ordered, _forms = load_jmdict_glosses_and_script_forms(
        path,
        languages=languages,
        include_kana=include_kana,
        include_kanji=include_kanji,
    )
    return {key: set(values) for key, values in ordered.items()}


def load_jmdict_glosses_ordered(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> dict[str, list[str]]:
    mapping, _forms = load_jmdict_glosses_and_script_forms(
        path,
        languages=languages,
        include_kana=include_kana,
        include_kanji=include_kanji,
    )
    return mapping


def _collect_glosses(
    *,
    elem: ElementTree.Element,
    allowed_languages: set[str],
) -> list[str]:
    glosses: list[str] = []
    for gloss in elem.findall("sense/gloss"):
        text = (gloss.text or "").strip()
        if not text:
            continue
        lang = gloss.get(XML_LANG_KEY)
        if lang and allowed_languages and lang.lower() not in allowed_languages:
            continue
        glosses.append(text)
    return glosses


def _collect_forms(*, elem: ElementTree.Element, tag_path: str) -> list[str]:
    forms: list[str] = []
    for entry in elem.findall(tag_path):
        text = (entry.text or "").strip()
        if not text:
            continue
        if text not in forms:
            forms.append(text)
    return forms


def _collect_unique_texts(nodes: Iterable[ElementTree.Element]) -> list[str]:
    values: list[str] = []
    for node in nodes:
        text = (node.text or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _collect_jmdict_pos_values(*, elem: ElementTree.Element) -> list[str]:
    pos_values: list[str] = []
    for pos in elem.findall("sense/pos"):
        text = (pos.text or "").strip()
        if text and text not in pos_values:
            pos_values.append(text)
    return pos_values


def _build_script_forms(
    *,
    term: str,
    canonical_kanji: str,
    canonical_kana: str,
) -> dict[str, str]:
    forms: dict[str, str] = {}
    if canonical_kanji:
        forms["kanji"] = canonical_kanji
    if canonical_kana:
        forms["kana"] = canonical_kana
    if not forms.get("kanji") and contains_kanji(term):
        forms["kanji"] = term
    if not forms.get("kana") and contains_kana(term):
        forms["kana"] = term
    kana_value = forms.get("kana", "")
    if kana_value:
        romaji = kana_to_romaji(kana_value)
        if romaji:
            forms["romaji"] = romaji
    return forms


def load_jmdict_glosses_and_script_forms(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> tuple[dict[str, list[str]], dict[str, dict[str, str]]]:
    _entries, mapping, forms_by_term = load_jmdict_entry_index_glosses_and_script_forms(
        path,
        languages=languages,
        include_kana=include_kana,
        include_kanji=include_kanji,
    )
    return mapping, forms_by_term


def load_jmdict_entry_index(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> dict[str, list[JmdictEntryRecord]]:
    entries_by_term, _mapping, _forms = load_jmdict_entry_index_glosses_and_script_forms(
        path,
        languages=languages,
        include_kana=include_kana,
        include_kanji=include_kanji,
    )
    return entries_by_term


def load_jmdict_entry_index_glosses_and_script_forms(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> tuple[dict[str, list[JmdictEntryRecord]], dict[str, list[str]], dict[str, dict[str, str]]]:
    entries_by_term: dict[str, list[JmdictEntryRecord]] = {}
    mapping: dict[str, list[str]] = {}
    forms_by_term: dict[str, dict[str, str]] = {}
    if not path.exists():
        return entries_by_term, mapping, forms_by_term
    allowed = {lang.lower() for lang in languages} if languages else set()
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return entries_by_term, mapping, forms_by_term
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        glosses = _collect_glosses(elem=elem, allowed_languages=allowed)
        if not glosses:
            elem.clear()
            continue
        kanji_forms = _collect_forms(elem=elem, tag_path="k_ele/keb")
        kana_forms = _collect_forms(elem=elem, tag_path="r_ele/reb")
        pos_values = _collect_jmdict_pos_values(elem=elem)
        canonical_kanji = kanji_forms[0] if kanji_forms else ""
        canonical_kana = kana_forms[0] if kana_forms else ""
        terms: list[str] = []
        if include_kanji:
            terms.extend(kanji_forms)
        if include_kana:
            terms.extend(kana_forms)
        entry_record = JmdictEntryRecord(
            kanji_forms=tuple(kanji_forms),
            kana_forms=tuple(kana_forms),
            glosses=tuple(glosses),
            pos_values=tuple(pos_values),
        )
        for term in terms:
            entry_bucket = entries_by_term.setdefault(term, [])
            entry_bucket.append(entry_record)
            bucket = mapping.setdefault(term, [])
            for gloss in glosses:
                if gloss not in bucket:
                    bucket.append(gloss)
            entry_forms = _build_script_forms(
                term=term,
                canonical_kanji=canonical_kanji,
                canonical_kana=canonical_kana,
            )
            existing = forms_by_term.setdefault(term, {})
            for script, value in entry_forms.items():
                if script not in existing and value:
                    existing[script] = value
        elem.clear()
    return entries_by_term, mapping, forms_by_term


def load_jmdict_lemmas(
    path: Path,
    *,
    include_kana: bool = True,
    include_kanji: bool = True,
) -> set[str]:
    lemmas: set[str] = set()
    if not path.exists():
        return lemmas
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return lemmas
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        if include_kanji:
            for keb in elem.findall("k_ele/keb"):
                if keb.text and keb.text.strip():
                    lemmas.add(keb.text.strip())
        if include_kana:
            for reb in elem.findall("r_ele/reb"):
                if reb.text and reb.text.strip():
                    lemmas.add(reb.text.strip())
        elem.clear()
    return lemmas


def load_freedict_tei_glosses_ordered(
    path: Path,
    *,
    target_lang: str,
) -> dict[str, list[str]]:
    records = load_freedict_tei_gloss_records_ordered(path, target_lang=target_lang)
    return {
        headword: [record.translation for record in entries]
        for headword, entries in records.items()
    }


def load_freedict_tei_gloss_records_ordered(
    path: Path,
    *,
    target_lang: str,
    headwords: Optional[Iterable[str]] = None,
) -> dict[str, list[FreedictGlossRecord]]:
    if not path.exists():
        return {}
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return {}
    headword_filter = _normalize_headword_filter(headwords)
    if headword_filter is not None and not headword_filter:
        return {}
    records: dict[str, list[FreedictGlossRecord]] = {}
    translation_index_by_headword: dict[str, dict[str, int]] = {}
    for _event, elem in context:
        if elem.tag != f"{{{TEI_NS['tei']}}}entry":
            continue
        headwords: list[str] = []
        for orth in elem.findall("tei:form/tei:orth", TEI_NS):
            text = (orth.text or "").strip()
            if text and text not in headwords:
                headwords.append(text)
        if not headwords:
            elem.clear()
            continue
        if headword_filter is not None and not any(
            headword.lower() in headword_filter for headword in headwords
        ):
            elem.clear()
            continue
        translations: list[str] = []
        for quote in elem.findall(".//tei:cit[@type='trans']/tei:quote", TEI_NS):
            text = (quote.text or "").strip()
            if not text:
                continue
            lang = (quote.get(XML_LANG_KEY) or "").strip().lower()
            if lang and lang != target_lang.lower():
                continue
            if text not in translations:
                translations.append(text)
        pos_values = _collect_unique_texts(elem.findall(".//tei:gramGrp/tei:pos", TEI_NS))
        pos_raw = "|".join(pos_values)
        if translations:
            for headword in headwords:
                bucket = records.setdefault(headword, [])
                index_by_translation = translation_index_by_headword.setdefault(headword, {})
                for translation in translations:
                    existing_index = index_by_translation.get(translation)
                    if existing_index is None:
                        bucket.append(FreedictGlossRecord(translation=translation, pos_raw=pos_raw))
                        index_by_translation[translation] = len(bucket) - 1
                        continue
                    if not bucket[existing_index].pos_raw and pos_raw:
                        bucket[existing_index] = FreedictGlossRecord(
                            translation=translation,
                            pos_raw=pos_raw,
                        )
        elem.clear()
    return records


def load_freedict_sqlite_glosses_ordered(path: Path) -> dict[str, list[str]]:
    records = load_freedict_sqlite_gloss_records_ordered(path)
    return {
        headword: [record.translation for record in entries]
        for headword, entries in records.items()
    }


def load_freedict_sqlite_gloss_base_forms(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(path)
        try:
            if _sqlite_has_table(conn, "sense_glosses"):
                return _load_auxiliary_sqlite_gloss_base_forms(conn)
            has_entries = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries' LIMIT 1"
            ).fetchone()
            if not has_entries:
                return set()
            cursor = conn.execute("SELECT translation FROM entries")
            try:
                return _collect_sqlite_gloss_base_forms(cursor)
            finally:
                cursor.close()
        finally:
            conn.close()
    except sqlite3.Error:
        return set()


def load_freedict_sqlite_gloss_records_ordered(
    path: Path,
    *,
    headwords: Optional[Iterable[str]] = None,
) -> dict[str, list[FreedictGlossRecord]]:
    mapping: dict[str, list[FreedictGlossRecord]] = {}
    translation_index_by_headword: dict[str, dict[str, int]] = {}
    if not path.exists() or not path.is_file():
        return mapping
    headword_filter = _normalize_headword_filter(headwords)
    if headword_filter is not None and not headword_filter:
        return mapping
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(path)
        try:
            if _sqlite_has_table(conn, "sense_glosses"):
                return _load_auxiliary_sqlite_gloss_records_ordered(
                    conn,
                    headwords=headword_filter,
                )
            has_entries = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries' LIMIT 1"
            ).fetchone()
            if not has_entries:
                return mapping
            query = "SELECT headword, translation, pos FROM entries"
            parameters: tuple[object, ...] = ()
            if headword_filter is not None:
                placeholders = ", ".join("?" for _ in headword_filter)
                query += f" WHERE headword_lc IN ({placeholders})"
                parameters = tuple(headword_filter)
            query += " ORDER BY headword_lc, rank, headword"
            cursor = conn.execute(query, parameters)
            try:
                for headword, translation, pos_raw in cursor:
                    headword_text = str(headword or "").strip()
                    translation_text = str(translation or "").strip()
                    if not headword_text or not translation_text:
                        continue
                    bucket = mapping.setdefault(headword_text, [])
                    index_by_translation = translation_index_by_headword.setdefault(
                        headword_text,
                        {},
                    )
                    existing_index = index_by_translation.get(translation_text)
                    normalized_pos_raw = str(pos_raw or "").strip()
                    if existing_index is None:
                        bucket.append(
                            FreedictGlossRecord(
                                translation=translation_text,
                                pos_raw=normalized_pos_raw,
                            )
                        )
                        index_by_translation[translation_text] = len(bucket) - 1
                        continue
                    if not bucket[existing_index].pos_raw and normalized_pos_raw:
                        bucket[existing_index] = FreedictGlossRecord(
                            translation=translation_text,
                            pos_raw=normalized_pos_raw,
                        )
            finally:
                cursor.close()
        finally:
            conn.close()
    except sqlite3.Error:
        return {}
    return mapping


def _sqlite_has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return bool(row)


def _load_auxiliary_sqlite_gloss_records_ordered(
    conn: sqlite3.Connection,
    *,
    headwords: Optional[Sequence[str]] = None,
) -> dict[str, list[FreedictGlossRecord]]:
    mapping: dict[str, list[FreedictGlossRecord]] = {}
    translation_index_by_headword: dict[str, dict[str, int]] = {}
    has_entry_meta = _sqlite_has_table(conn, "entry_meta")
    has_translation_meta = _sqlite_has_table(conn, "translation_meta")
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
    if headwords is not None:
        if not headwords:
            return mapping
        placeholders = ", ".join("?" for _ in headwords)
        where_clause = f"WHERE sg.headword_lc IN ({placeholders})"
        parameters = tuple(headwords)
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
        ORDER BY sg.headword_lc, sg.entry_ord, sg.sense_ord, sg.gloss_ord, sg.translation, sg.headword
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
            metadata = _build_auxiliary_gloss_metadata(
                entry_ord=entry_ord,
                sense_ord=sense_ord,
                gloss_ord=gloss_ord,
                raw_glosses_json=raw_glosses_json,
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
            bucket = mapping.setdefault(headword_text, [])
            index_by_translation = translation_index_by_headword.setdefault(
                headword_text,
                {},
            )
            existing_index = index_by_translation.get(translation_text)
            normalized_pos_raw = str(pos_raw or "").strip()
            if existing_index is None:
                bucket.append(
                    FreedictGlossRecord(
                        translation=translation_text,
                        pos_raw=normalized_pos_raw,
                        metadata=metadata,
                    )
                )
                index_by_translation[translation_text] = len(bucket) - 1
                continue
            existing = bucket[existing_index]
            if existing.pos_raw or not normalized_pos_raw:
                continue
            bucket[existing_index] = FreedictGlossRecord(
                translation=translation_text,
                pos_raw=normalized_pos_raw,
                metadata=existing.metadata or metadata,
            )
    finally:
        cursor.close()
    return mapping


def _load_auxiliary_sqlite_gloss_base_forms(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.execute("SELECT translation FROM sense_glosses")
    try:
        return _collect_sqlite_gloss_base_forms(cursor)
    finally:
        cursor.close()


def _collect_sqlite_gloss_base_forms(cursor: sqlite3.Cursor) -> set[str]:
    base_forms: set[str] = set()
    for (translation,) in cursor:
        normalized = sanitize_dictionary_gloss(translation).lower()
        if normalized:
            base_forms.add(normalized)
    return base_forms


def _build_auxiliary_gloss_metadata(
    *,
    entry_ord: object,
    sense_ord: object,
    gloss_ord: object,
    raw_glosses_json: object,
    sense_tags_json: object,
    sense_topics_json: object,
    sense_categories_json: object,
    form_of_json: object,
    alt_of_json: object,
    entry_pos_title: object,
    entry_tags_json: object,
    entry_categories_json: object,
    translation_sense_text: object,
    translation_english_text: object,
    translation_note_text: object,
    translation_roman_text: object,
    translation_tags_json: object,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    _set_int_metadata(metadata, "entry_ord", entry_ord)
    _set_int_metadata(metadata, "sense_ord", sense_ord)
    _set_int_metadata(metadata, "gloss_ord", gloss_ord)
    _set_text_metadata(metadata, "entry_pos_title", entry_pos_title)
    _set_text_metadata(metadata, "translation_sense_text", translation_sense_text)
    _set_text_metadata(metadata, "translation_english_text", translation_english_text)
    _set_text_metadata(metadata, "translation_note_text", translation_note_text)
    _set_text_metadata(metadata, "translation_roman_text", translation_roman_text)
    _set_json_metadata(metadata, "entry_tags", entry_tags_json)
    _set_json_metadata(metadata, "entry_categories", entry_categories_json)
    _set_json_metadata(metadata, "sense_raw_glosses", raw_glosses_json)
    _set_json_metadata(metadata, "sense_tags", sense_tags_json)
    _set_json_metadata(metadata, "sense_topics", sense_topics_json)
    _set_json_metadata(metadata, "sense_categories", sense_categories_json)
    _set_json_metadata(metadata, "sense_form_of", form_of_json)
    _set_json_metadata(metadata, "sense_alt_of", alt_of_json)
    _set_json_metadata(metadata, "translation_tags", translation_tags_json)
    return metadata


def _set_text_metadata(metadata: dict[str, object], key: str, value: object) -> None:
    text = str(value or "").strip()
    if text:
        metadata[key] = text


def _set_int_metadata(metadata: dict[str, object], key: str, value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        metadata[key] = value
        return
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return
        try:
            metadata[key] = int(text)
        except ValueError:
            return


def _set_json_metadata(metadata: dict[str, object], key: str, value: object) -> None:
    parsed = _parse_json_column(value)
    if parsed in (None, "", [], {}):
        return
    metadata[key] = parsed


def _parse_json_column(value: object) -> object:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def load_freedict_glosses_ordered(
    path: Path,
    *,
    target_lang: str,
) -> dict[str, list[str]]:
    records = load_freedict_gloss_records_ordered(path, target_lang=target_lang)
    return {
        headword: [record.translation for record in entries]
        for headword, entries in records.items()
    }


def load_freedict_gloss_base_forms(
    path: Path,
    *,
    target_lang: str,
) -> set[str]:
    if _is_sqlite_file(path):
        return load_freedict_sqlite_gloss_base_forms(path)
    return load_freedict_tei_gloss_base_forms(path, target_lang=target_lang)


def load_freedict_tei_gloss_base_forms(
    path: Path,
    *,
    target_lang: str,
) -> set[str]:
    if not path.exists():
        return set()
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return set()
    base_forms: set[str] = set()
    for _event, elem in context:
        if elem.tag != f"{{{TEI_NS['tei']}}}entry":
            continue
        for quote in elem.findall(".//tei:cit[@type='trans']/tei:quote", TEI_NS):
            text = (quote.text or "").strip()
            if not text:
                continue
            lang = (quote.get(XML_LANG_KEY) or "").strip().lower()
            if lang and lang != target_lang.lower():
                continue
            normalized = sanitize_dictionary_gloss(text).lower()
            if normalized:
                base_forms.add(normalized)
        elem.clear()
    return base_forms


def load_freedict_gloss_records_ordered(
    path: Path,
    *,
    target_lang: str,
    headwords: Optional[Iterable[str]] = None,
) -> dict[str, list[FreedictGlossRecord]]:
    if _is_sqlite_file(path):
        return load_freedict_sqlite_gloss_records_ordered(path, headwords=headwords)
    return load_freedict_tei_gloss_records_ordered(
        path,
        target_lang=target_lang,
        headwords=headwords,
    )


def _normalize_headword_filter(
    headwords: Optional[Iterable[str]],
) -> Optional[tuple[str, ...]]:
    if headwords is None:
        return None
    normalized = tuple(
        sorted(
            {
                str(headword or "").strip().lower()
                for headword in headwords
                if str(headword or "").strip()
            }
        )
    )
    return normalized


def _is_sqlite_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            return handle.read(16).startswith(b"SQLite format 3")
    except OSError:
        return False
