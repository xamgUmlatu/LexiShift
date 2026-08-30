from __future__ import annotations

import hashlib
from mmap import ACCESS_READ, mmap
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Iterable, Sequence
from xml.etree import ElementTree
from xml.sax.saxutils import escape, unescape

from lexishift_core.resources.dict_loaders import (
    JmdictEntryRecord,
    XML_LANG_KEY,
)
from lexishift_core.resources.jmdict_records import (
    JmdictGlossRecord,
    JmdictReadingRecord,
    JmdictSenseRecord,
)


JMDICT_DEFINITION_INDEX_VERSION = 1
_FORM_PATTERN = re.compile(rb"<(?:keb|reb)>([^<]+)</(?:keb|reb)>")


def load_jmdict_definition_records_for_terms(
    path: Path,
    terms: Sequence[str],
    *,
    languages: Iterable[str] = ("eng", "en"),
    index_path: Path | None = None,
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
    entry_elements = _matching_entry_elements(path, requested, index_path=index_path)
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
    *,
    index_path: Path | None = None,
) -> list[ElementTree.Element]:
    try:
        with path.open("rb") as handle, mmap(handle.fileno(), 0, access=ACCESS_READ) as data:
            first_entry = data.find(b"<entry>")
            if first_entry < 0:
                return []
            spans = None
            if index_path is not None:
                spans = _indexed_entry_spans(
                    path,
                    index_path=index_path,
                    requested=requested,
                )
            if spans is None:
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


def jmdict_definition_index_path(cache_dir: Path, source_path: Path) -> Path:
    resolved_source = str(Path(source_path).resolve(strict=False))
    source_key = hashlib.sha256(resolved_source.encode("utf-8")).hexdigest()[:16]
    return Path(cache_dir) / f"jmdict-definition-{source_key}.sqlite3"


def _indexed_entry_spans(
    source_path: Path,
    *,
    index_path: Path,
    requested: set[str],
) -> list[tuple[int, int]] | None:
    try:
        source_stat = source_path.stat()
        if not _index_matches_source(index_path, source_path, source_stat):
            _build_definition_index(
                source_path,
                index_path=index_path,
                source_stat=source_stat,
            )
        if not _index_matches_source(index_path, source_path, source_stat):
            return None
        placeholders = ",".join("?" for _value in requested)
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                f"SELECT entry_start, entry_end FROM forms "
                f"WHERE term IN ({placeholders}) ORDER BY entry_start",
                tuple(sorted(requested)),
            ).fetchall()
        return sorted({(int(start), int(end)) for start, end in rows})
    except (OSError, sqlite3.DatabaseError, ValueError):
        return None


def _index_matches_source(
    index_path: Path,
    source_path: Path,
    source_stat: os.stat_result,
) -> bool:
    if not index_path.exists():
        return False
    try:
        with sqlite3.connect(index_path) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        return metadata == {
            "index_version": str(JMDICT_DEFINITION_INDEX_VERSION),
            "source_path": str(source_path.resolve(strict=False)),
            "source_mtime_ns": str(int(source_stat.st_mtime_ns)),
            "source_size": str(int(source_stat.st_size)),
        }
    except (OSError, sqlite3.DatabaseError, ValueError):
        return False


def _build_definition_index(
    source_path: Path,
    *,
    index_path: Path,
    source_stat: os.stat_result,
) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{index_path.name}.",
        suffix=".tmp",
        dir=index_path.parent,
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        with sqlite3.connect(temp_path) as connection:
            connection.executescript(
                "PRAGMA journal_mode=OFF;"
                "PRAGMA synchronous=OFF;"
                "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);"
                "CREATE TABLE forms ("
                "term TEXT NOT NULL, entry_start INTEGER NOT NULL, entry_end INTEGER NOT NULL"
                ");"
            )
            batch: list[tuple[str, int, int]] = []
            with (
                source_path.open("rb") as handle,
                mmap(handle.fileno(), 0, access=ACCESS_READ) as data,
            ):
                entry_start = data.find(b"<entry>")
                while entry_start >= 0:
                    close = data.find(b"</entry>", entry_start)
                    if close < 0:
                        break
                    entry_end = close + len(b"</entry>")
                    seen_terms: set[str] = set()
                    for raw_term in _FORM_PATTERN.findall(data[entry_start:entry_end]):
                        try:
                            term = _normalize_term(unescape(raw_term.decode("utf-8")))
                        except UnicodeDecodeError:
                            continue
                        if not term or term in seen_terms:
                            continue
                        seen_terms.add(term)
                        batch.append((term, entry_start, entry_end))
                    if len(batch) >= 10_000:
                        connection.executemany(
                            "INSERT INTO forms(term, entry_start, entry_end) VALUES (?, ?, ?)",
                            batch,
                        )
                        batch.clear()
                    entry_start = data.find(b"<entry>", entry_end)
            if batch:
                connection.executemany(
                    "INSERT INTO forms(term, entry_start, entry_end) VALUES (?, ?, ?)",
                    batch,
                )
            current_stat = source_path.stat()
            if int(current_stat.st_mtime_ns) != int(source_stat.st_mtime_ns) or int(
                current_stat.st_size
            ) != int(source_stat.st_size):
                raise OSError("JMdict changed while its lookup index was being built.")
            connection.execute("CREATE INDEX forms_term_idx ON forms(term)")
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("index_version", str(JMDICT_DEFINITION_INDEX_VERSION)),
                    ("source_path", str(source_path.resolve(strict=False))),
                    ("source_mtime_ns", str(int(source_stat.st_mtime_ns))),
                    ("source_size", str(int(source_stat.st_size))),
                ),
            )
            connection.commit()
        os.replace(temp_path, index_path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


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
