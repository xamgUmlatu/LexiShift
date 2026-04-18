from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from lexishift_core.resources.dict_gloss_metadata import build_auxiliary_gloss_metadata
from lexishift_core.resources.dict_loaders import FreedictGlossRecord
from lexishift_core.resources.dict_sqlite_support import (
    load_auxiliary_sqlite_gloss_base_forms,
    load_auxiliary_sqlite_gloss_records_ordered,
    load_auxiliary_sqlite_headwords,
    sqlite_has_column,
    sqlite_has_table,
)
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss


class TestDictSqliteSupport(unittest.TestCase):
    def test_support_helpers_detect_auxiliary_schema_and_load_basic_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE sense_glosses ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT"
                    ")"
                )
                conn.executemany(
                    "INSERT INTO sense_glosses (headword, headword_lc, translation) "
                    "VALUES (?, ?, ?)",
                    (
                        ("Casa", "casa", " House! "),
                        ("Casa", "casa", "homes"),
                    ),
                )
                conn.commit()

                self.assertTrue(sqlite_has_table(conn, "sense_glosses"))
                self.assertTrue(sqlite_has_column(conn, "sense_glosses", "translation"))
                self.assertFalse(sqlite_has_column(conn, "sense_glosses", "examples_json"))
                self.assertEqual(load_auxiliary_sqlite_headwords(conn), ("Casa",))
                self.assertEqual(
                    load_auxiliary_sqlite_gloss_base_forms(
                        conn,
                        sanitize_gloss=sanitize_dictionary_gloss,
                    ),
                    {"house", "homes"},
                )
            finally:
                conn.close()

    def test_record_loader_backfills_missing_pos_without_losing_first_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE sense_glosses ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT, "
                    "translation_lc TEXT, "
                    "pos TEXT, "
                    "entry_ord INTEGER, "
                    "sense_ord INTEGER, "
                    "gloss_ord INTEGER, "
                    "raw_glosses_json TEXT, "
                    "examples_json TEXT, "
                    "tags_json TEXT, "
                    "topics_json TEXT, "
                    "categories_json TEXT, "
                    "form_of_json TEXT, "
                    "alt_of_json TEXT"
                    ")"
                )
                conn.execute(
                    "CREATE TABLE entry_meta ("
                    "entry_ord INTEGER, "
                    "pos_title TEXT, "
                    "tags_json TEXT, "
                    "categories_json TEXT"
                    ")"
                )
                conn.execute(
                    "CREATE TABLE translation_meta ("
                    "entry_ord INTEGER, "
                    "sense_ord INTEGER, "
                    "gloss_ord INTEGER, "
                    "sense_text TEXT, "
                    "english_text TEXT, "
                    "note_text TEXT, "
                    "roman_text TEXT, "
                    "tags_json TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entry_meta (entry_ord, pos_title, tags_json, categories_json) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        1,
                        "noun-title",
                        json.dumps(["masculine"]),
                        json.dumps(["employment"]),
                    ),
                )
                conn.execute(
                    "INSERT INTO translation_meta "
                    "(entry_ord, sense_ord, gloss_ord, sense_text, english_text, note_text, roman_text, tags_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        1,
                        0,
                        0,
                        "cargo sense",
                        "office",
                        "role note",
                        "cargo",
                        json.dumps(["formal"]),
                    ),
                )
                conn.executemany(
                    "INSERT INTO sense_glosses "
                    "(headword, headword_lc, translation, translation_lc, pos, entry_ord, sense_ord, gloss_ord, raw_glosses_json, examples_json, tags_json, topics_json, categories_json, form_of_json, alt_of_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        (
                            "cargo",
                            "cargo",
                            "office",
                            "office",
                            "",
                            1,
                            0,
                            0,
                            json.dumps(["professional office"]),
                            json.dumps([{"text": "cargo example"}]),
                            json.dumps(["formal"]),
                            json.dumps(["employment"]),
                            None,
                            None,
                            None,
                        ),
                        (
                            "cargo",
                            "cargo",
                            "office",
                            "office",
                            "noun",
                            1,
                            0,
                            1,
                            json.dumps(["duplicate office"]),
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                        ),
                    ),
                )
                conn.commit()

                records = load_auxiliary_sqlite_gloss_records_ordered(
                    conn,
                    headwords=("cargo",),
                    record_factory=FreedictGlossRecord,
                    metadata_builder=build_auxiliary_gloss_metadata,
                )
            finally:
                conn.close()

        self.assertEqual(list(records.keys()), ["cargo"])
        self.assertEqual(len(records["cargo"]), 1)
        record = records["cargo"][0]
        self.assertEqual(record.translation, "office")
        self.assertEqual(record.pos_raw, "noun")
        self.assertEqual(record.metadata["entry_pos_title"], "noun-title")
        self.assertEqual(record.metadata["translation_note_text"], "role note")
        self.assertEqual(record.metadata["sense_raw_glosses"], ["professional office"])
        self.assertEqual(record.metadata["sense_examples"], [{"text": "cargo example"}])


if __name__ == "__main__":
    unittest.main()
