from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Sequence
from xml.sax.saxutils import escape


def write_jmdict_fixture(path: Path, *, entries: Sequence[tuple[str, str]]) -> Path:
    payload_entries: list[str] = []
    for headword, gloss in entries:
        payload_entries.append(
            "<entry>"
            f"<k_ele><keb>{escape(headword)}</keb></k_ele>"
            f"<r_ele><reb>{escape(headword)}</reb></r_ele>"
            f"<sense><gloss>{escape(gloss)}</gloss></sense>"
            "</entry>"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<JMdict>" + "".join(payload_entries) + "</JMdict>", encoding="utf-8")
    return path


def write_freedict_tei_fixture(
    path: Path,
    *,
    entries: Sequence[tuple[str, str, str]],
    target_lang: str,
) -> Path:
    payload_entries: list[str] = []
    for headword, translation, pos_raw in entries:
        pos_xml = f"<gramGrp><pos>{escape(pos_raw)}</pos></gramGrp>" if pos_raw else ""
        payload_entries.append(
            "<entry>"
            f"<form><orth>{escape(headword)}</orth></form>"
            f"{pos_xml}"
            "<sense>"
            f"<cit type='trans'><quote xml:lang='{escape(target_lang)}'>{escape(translation)}</quote></cit>"
            "</sense>"
            "</entry>"
        )
    payload = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<TEI xmlns='http://www.tei-c.org/ns/1.0'>"
        "<text><body>" + "".join(payload_entries) + "</body></text></TEI>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return path


def write_translation_dictionary_sqlite_fixture(
    path: Path,
    *,
    entries: Sequence[tuple[str, str, str]],
    metadata_source: str,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TABLE IF EXISTS meta;")
        conn.execute("DROP TABLE IF EXISTS entries;")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
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
        conn.executemany(
            "INSERT INTO entries ("
            "headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    headword,
                    headword.lower(),
                    translation,
                    translation.lower(),
                    index + 1,
                    pos_raw,
                    index + 1,
                    0,
                )
                for index, (headword, translation, pos_raw) in enumerate(entries)
            ],
        )
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("metadata", json.dumps({"source": metadata_source}, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()
    return path
