from __future__ import annotations

from mmap import ACCESS_READ, mmap
from pathlib import Path
from typing import Iterable, Sequence
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from lexishift_core.resources.dict_loaders import (
    JmdictEntryRecord,
    XML_LANG_KEY,
)
from lexishift_core.resources.jmdict_records import (
    JmdictGlossRecord,
    JmdictReadingRecord,
    JmdictSenseRecord,
)


def load_jmdict_definition_records_for_terms(
    path: Path,
    terms: Sequence[str],
    *,
    languages: Iterable[str] = ("eng", "en"),
) -> tuple[dict[str, list[JmdictEntryRecord]], dict[str, list[str]]]:
    """Load richly structured JMdict entries only for the requested terms.

    Matching entry fragments are located through JMdict's exact ``keb``/``reb``
    text tags and parsed with the file's original embedded DTD. This preserves
    source ordering, entity text, and sense boundaries without retaining a
    second in-memory dictionary.
    """

    entries_by_term: dict[str, list[JmdictEntryRecord]] = {}
    glosses_by_term: dict[str, list[str]] = {}
    requested = {_normalize_term(term) for term in terms if _normalize_term(term)}
    if not requested or not path.exists():
        return entries_by_term, glosses_by_term

    allowed_languages = {str(language).strip().lower() for language in languages}
    entry_elements = _matching_entry_elements(path, requested)
    if not entry_elements:
        return entries_by_term, glosses_by_term
    for elem in entry_elements:
        kanji_forms = _unique_texts(elem.findall("k_ele/keb"))
        kana_forms = _unique_texts(elem.findall("r_ele/reb"))
        matching_terms = _matching_terms((*kanji_forms, *kana_forms), requested)
        if not matching_terms:
            continue

        senses = _collect_senses(elem, allowed_languages=allowed_languages)
        glosses = [gloss.text for sense in senses for gloss in sense.glosses]
        if not glosses:
            continue
        entry = JmdictEntryRecord(
            kanji_forms=tuple(kanji_forms),
            kana_forms=tuple(kana_forms),
            glosses=tuple(glosses),
            pos_values=tuple(_unique_texts(elem.findall("sense/pos"))),
            reading_records=tuple(_collect_reading_records(elem)),
            senses=tuple(senses),
        )
        for term in matching_terms:
            entries_by_term.setdefault(term, []).append(entry)
            bucket = glosses_by_term.setdefault(term, [])
            for gloss in glosses:
                if gloss not in bucket:
                    bucket.append(gloss)
    return entries_by_term, glosses_by_term


def _matching_entry_elements(
    path: Path,
    requested: set[str],
) -> list[ElementTree.Element]:
    try:
        with path.open("rb") as handle, mmap(handle.fileno(), 0, access=ACCESS_READ) as data:
            first_entry = data.find(b"<entry>")
            if first_entry < 0:
                return []
            spans = _matching_entry_spans(
                data,
                requested=requested,
                first_entry=first_entry,
            )
            if not spans:
                return []
            document = (
                data[:first_entry]
                + b"".join(data[start:end] for start, end in spans)
                + b"</JMdict>"
            )
    except (OSError, ValueError):
        return []
    try:
        root = ElementTree.fromstring(document)
    except ElementTree.ParseError:
        return []
    return list(root.findall("entry"))


def _collect_reading_records(elem: ElementTree.Element) -> list[JmdictReadingRecord]:
    records: list[JmdictReadingRecord] = []
    for reading in elem.findall("r_ele"):
        text = _first_node_text(reading.find("reb"))
        if not text:
            continue
        records.append(
            JmdictReadingRecord(
                text=text,
                kanji_restrictions=tuple(_unique_texts(reading.findall("re_restr"))),
                no_kanji=reading.find("re_nokanji") is not None,
            )
        )
    return records


def _matching_entry_spans(
    data: mmap,
    *,
    requested: set[str],
    first_entry: int,
) -> list[tuple[int, int]]:
    entry_open = b"<entry>"
    entry_close = b"</entry>"
    spans: set[tuple[int, int]] = set()
    for term in requested:
        encoded_term = escape(term).encode("utf-8")
        for tag in (b"keb", b"reb"):
            needle = b"<" + tag + b">" + encoded_term + b"</" + tag + b">"
            offset = first_entry
            while (hit := data.find(needle, offset)) >= 0:
                start = data.rfind(entry_open, first_entry, hit + 1)
                close = data.find(entry_close, hit)
                if start >= 0 and close >= 0:
                    spans.add((start, close + len(entry_close)))
                offset = hit + len(needle)
    return sorted(spans)


def _collect_senses(
    elem: ElementTree.Element,
    *,
    allowed_languages: set[str],
) -> list[JmdictSenseRecord]:
    senses: list[JmdictSenseRecord] = []
    for sense in elem.findall("sense"):
        glosses: list[JmdictGlossRecord] = []
        for gloss in sense.findall("gloss"):
            text = (gloss.text or "").strip()
            language = (gloss.get(XML_LANG_KEY) or "eng").strip().lower()
            if not text or (allowed_languages and language not in allowed_languages):
                continue
            glosses.append(
                JmdictGlossRecord(
                    text=text,
                    language=language,
                    gloss_type=(gloss.get("g_type") or "").strip(),
                    gender=(gloss.get("g_gend") or "").strip(),
                    priority_values=tuple(_unique_texts(gloss.findall("pri"))),
                )
            )
        if not glosses:
            continue
        senses.append(
            JmdictSenseRecord(
                glosses=tuple(glosses),
                kanji_restrictions=tuple(_unique_texts(sense.findall("stagk"))),
                reading_restrictions=tuple(_unique_texts(sense.findall("stagr"))),
                pos_values=tuple(_unique_texts(sense.findall("pos"))),
                field_values=tuple(_unique_texts(sense.findall("field"))),
                misc_values=tuple(_unique_texts(sense.findall("misc"))),
                info_values=tuple(_unique_texts(sense.findall("s_inf"))),
                dialect_values=tuple(_unique_texts(sense.findall("dial"))),
                cross_references=tuple(_unique_texts(sense.findall("xref"))),
                antonyms=tuple(_unique_texts(sense.findall("ant"))),
            )
        )
    return senses


def _matching_terms(forms: Sequence[str], requested: set[str]) -> list[str]:
    matches: list[str] = []
    for form in forms:
        if _normalize_term(form) in requested and form not in matches:
            matches.append(form)
    return matches


def _unique_texts(nodes: Iterable[ElementTree.Element]) -> list[str]:
    values: list[str] = []
    for node in nodes:
        text = (node.text or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _first_node_text(node: ElementTree.Element | None) -> str:
    return (node.text or "").strip() if node is not None else ""


def _normalize_term(value: object) -> str:
    return str(value or "").strip().casefold()
