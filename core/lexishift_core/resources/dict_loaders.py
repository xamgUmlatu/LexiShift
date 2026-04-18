from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
from typing import Iterable, Mapping, Optional
from xml.etree import ElementTree

from lexishift_core.resources.japanese_script import (
    contains_kana,
    contains_kanji,
    kana_to_romaji,
)
from lexishift_core.resources.dict_gloss_metadata import build_auxiliary_gloss_metadata
from lexishift_core.resources.dict_sqlite_support import (
    load_auxiliary_sqlite_gloss_base_forms as _load_auxiliary_sqlite_gloss_base_forms,
    load_auxiliary_sqlite_gloss_records_ordered as _load_auxiliary_sqlite_gloss_records_ordered,
    load_auxiliary_sqlite_headwords as _load_auxiliary_sqlite_headwords,
    sqlite_has_table as _sqlite_has_table,
)
from lexishift_core.resources.path_cache import load_or_compute_path_json_value
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
class TranslationGlossRecord:
    translation: str
    pos_raw: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


FreedictGlossRecord = TranslationGlossRecord


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


def load_freedict_sqlite_headwords(path: Path) -> tuple[str, ...]:
    if not path.exists() or not path.is_file():
        return ()
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(path)
        try:
            if _sqlite_has_table(conn, "sense_glosses"):
                return _load_auxiliary_sqlite_headwords(conn)
            has_entries = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries' LIMIT 1"
            ).fetchone()
            if not has_entries:
                return ()
            cursor = conn.execute("SELECT headword FROM entries ORDER BY headword_lc, headword")
            try:
                return _collect_sqlite_headwords(cursor)
            finally:
                cursor.close()
        finally:
            conn.close()
    except sqlite3.Error:
        return ()


def load_freedict_sqlite_gloss_base_forms(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(path)
        try:
            if _sqlite_has_table(conn, "sense_glosses"):
                return _load_auxiliary_sqlite_gloss_base_forms(
                    conn,
                    sanitize_gloss=sanitize_dictionary_gloss,
                )
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
                    record_factory=FreedictGlossRecord,
                    metadata_builder=build_auxiliary_gloss_metadata,
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


def _collect_sqlite_gloss_base_forms(cursor: sqlite3.Cursor) -> set[str]:
    base_forms: set[str] = set()
    for (translation,) in cursor:
        normalized = sanitize_dictionary_gloss(translation).lower()
        if normalized:
            base_forms.add(normalized)
    return base_forms


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


def load_freedict_tei_headwords(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return ()
    ordered: list[str] = []
    seen: set[str] = set()
    for _event, elem in context:
        if elem.tag != f"{{{TEI_NS['tei']}}}entry":
            continue
        for orth in elem.findall("tei:form/tei:orth", TEI_NS):
            text = (orth.text or "").strip()
            if not text:
                continue
            normalized = text.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(text)
        elem.clear()
    return tuple(ordered)


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


def load_freedict_headwords(path: Path) -> tuple[str, ...]:
    if _is_sqlite_file(path):
        return load_freedict_sqlite_headwords(path)
    return load_freedict_tei_headwords(path)


def load_translation_gloss_base_forms(
    path: Path,
    *,
    target_lang: str,
) -> set[str]:
    normalized_target_lang = str(target_lang or "").strip().lower()
    return load_or_compute_path_json_value(
        path,
        namespace="translation_pack_metadata",
        key={
            "kind": "gloss_base_forms",
            "target_lang": normalized_target_lang,
        },
        compute=lambda: load_freedict_gloss_base_forms(path, target_lang=normalized_target_lang),
        serialize=lambda values: sorted(
            {str(value or "").strip().lower() for value in values if str(value or "").strip()}
        ),
        deserialize=lambda payload: {
            str(value or "").strip().lower() for value in payload if str(value or "").strip()
        },
    )


def load_translation_gloss_records_ordered(
    path: Path,
    *,
    target_lang: str,
    headwords: Optional[Iterable[str]] = None,
) -> dict[str, list[TranslationGlossRecord]]:
    return load_freedict_gloss_records_ordered(
        path,
        target_lang=target_lang,
        headwords=headwords,
    )


def load_translation_gloss_records_by_translation_ordered(
    path: Path,
    *,
    translations: Optional[Iterable[str]] = None,
) -> dict[str, list[TranslationGlossRecord]]:
    normalized_translations = _normalize_headword_filter(translations)
    if _is_sqlite_file(path):
        from lexishift_core.resources.dict_translation_grouped_loader import (
            load_sqlite_gloss_records_by_translation_ordered,
        )

        conn = sqlite3.connect(path)
        try:
            return load_sqlite_gloss_records_by_translation_ordered(
                conn,
                translations=normalized_translations,
            )
        finally:
            conn.close()
    return {}


def load_translation_headwords(path: Path) -> tuple[str, ...]:
    return load_or_compute_path_json_value(
        path,
        namespace="translation_pack_metadata",
        key={"kind": "headwords"},
        compute=lambda: load_freedict_headwords(path),
        serialize=lambda values: [
            str(value or "").strip() for value in values if str(value or "").strip()
        ],
        deserialize=lambda payload: tuple(
            str(value or "").strip() for value in payload if str(value or "").strip()
        ),
    )


def _is_sqlite_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            return handle.read(16).startswith(b"SQLite format 3")
    except OSError:
        return False
