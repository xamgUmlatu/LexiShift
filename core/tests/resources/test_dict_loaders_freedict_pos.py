from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import (  # noqa: E402
    load_freedict_gloss_base_forms,
    load_freedict_headwords,
    load_freedict_sqlite_gloss_records_ordered,
    load_freedict_tei_gloss_records_ordered,
    load_translation_gloss_records_by_translation_ordered,
    load_translation_gloss_base_forms,
    load_translation_headwords,
)
from lexishift_core.resources.freedict_sqlite import (  # noqa: E402
    convert_freedict_tei_to_sqlite,
)


class TestFreedictPosLoaders(unittest.TestCase):
    def test_tei_loader_returns_ordered_translations_with_pos(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <gramGrp><pos>noun</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.tei"
            path.write_text(payload, encoding="utf-8")
            records = load_freedict_tei_gloss_records_ordered(path, target_lang="en")
        self.assertIn("Haus", records)
        self.assertEqual([entry.translation for entry in records["Haus"]], ["house", "home"])
        self.assertEqual(records["Haus"][0].pos_raw, "noun")

    def test_tei_loader_can_filter_by_headword_subset(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <gramGrp><pos>noun</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>Baum</orth></form>
        <gramGrp><pos>noun</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="en">tree</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.tei"
            path.write_text(payload, encoding="utf-8")
            records = load_freedict_tei_gloss_records_ordered(
                path,
                target_lang="en",
                headwords=("haus",),
            )
        self.assertIn("Haus", records)
        self.assertNotIn("Baum", records)

    def test_tei_base_form_loader_collects_sanitized_glosses(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en"> House! </quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.tei"
            path.write_text(payload, encoding="utf-8")
            base_forms = load_freedict_gloss_base_forms(path, target_lang="en")
        self.assertEqual(base_forms, {"house", "home"})

    def test_tei_headword_loader_preserves_raw_infinitive_spellings(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>To Remove</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">quitar</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>House</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">casa</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-spa.tei"
            path.write_text(payload, encoding="utf-8")
            headwords = load_freedict_headwords(path)
        self.assertEqual(headwords, ("To Remove", "House"))

    def test_convert_freedict_tei_to_sqlite_preserves_order_and_pos(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <gramGrp><pos>noun</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>laufen</orth></form>
        <gramGrp><pos>verb</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="en">run</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            tei_path = Path(tmp) / "deu-eng.tei"
            sqlite_path = Path(tmp) / "freedict-de-en.sqlite"
            tei_path.write_text(payload, encoding="utf-8")
            metadata = convert_freedict_tei_to_sqlite(
                tei_path,
                sqlite_path,
                target_lang="en",
                overwrite=True,
            )
            records = load_freedict_sqlite_gloss_records_ordered(sqlite_path)
        self.assertEqual(metadata["pair_count"], 3)
        self.assertIn("Haus", records)
        self.assertEqual([entry.translation for entry in records["Haus"]], ["house", "home"])
        self.assertEqual(records["Haus"][0].pos_raw, "noun")
        self.assertEqual(records["Haus"][0].metadata.get("rank"), 1)
        self.assertEqual(records["Haus"][0].metadata.get("entry_ord"), 1)
        self.assertEqual(records["Haus"][0].metadata.get("gloss_ord"), 0)
        self.assertEqual(records["Haus"][1].metadata.get("rank"), 2)
        self.assertEqual(records["Haus"][1].metadata.get("entry_ord"), 1)
        self.assertEqual(records["Haus"][1].metadata.get("gloss_ord"), 1)
        self.assertEqual(records["laufen"][0].translation, "run")
        self.assertEqual(records["laufen"][0].pos_raw, "verb")
        self.assertEqual(records["laufen"][0].metadata.get("rank"), 1)
        self.assertEqual(records["laufen"][0].metadata.get("entry_ord"), 2)
        self.assertEqual(records["laufen"][0].metadata.get("gloss_ord"), 0)

    def test_sqlite_loader_backfills_missing_pos_for_duplicate_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE entries ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT, "
                    "rank INTEGER, "
                    "pos TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("Haus", "haus", "house", 1, ""),
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("Haus", "haus", "house", 2, "noun"),
                )
                conn.commit()
            finally:
                conn.close()
            records = load_freedict_sqlite_gloss_records_ordered(path)
        self.assertIn("Haus", records)
        self.assertEqual(len(records["Haus"]), 1)
        self.assertEqual(records["Haus"][0].translation, "house")
        self.assertEqual(records["Haus"][0].pos_raw, "noun")

    def test_sqlite_loader_can_filter_by_headword_subset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE entries ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT, "
                    "rank INTEGER, "
                    "pos TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("Haus", "haus", "house", 1, "noun"),
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("Baum", "baum", "tree", 1, "noun"),
                )
                conn.commit()
            finally:
                conn.close()
            records = load_freedict_sqlite_gloss_records_ordered(path, headwords=("haus",))
        self.assertIn("Haus", records)
        self.assertNotIn("Baum", records)

    def test_translation_loader_can_group_rows_by_translation_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-spa.sqlite"
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
                    "INSERT INTO sense_glosses "
                    "(headword, headword_lc, translation, translation_lc, pos, entry_ord, sense_ord, gloss_ord, raw_glosses_json, examples_json, tags_json, topics_json, categories_json, form_of_json, alt_of_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "function",
                        "function",
                        "cargo",
                        "cargo",
                        "noun",
                        1,
                        0,
                        0,
                        json.dumps(["professional or official position"]),
                        None,
                        json.dumps(["masculine"]),
                        None,
                        json.dumps(["en:Employment"]),
                        None,
                        None,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            records = load_translation_gloss_records_by_translation_ordered(
                path,
                translations=("cargo",),
            )

        self.assertIn("cargo", records)
        self.assertEqual(len(records["cargo"]), 1)
        self.assertEqual(records["cargo"][0].translation, "function")
        self.assertEqual(records["cargo"][0].pos_raw, "noun")
        self.assertEqual(
            records["cargo"][0].metadata.get("sense_raw_glosses"),
            ["professional or official position"],
        )

    def test_auxiliary_sqlite_loaders_accept_legacy_tables_without_examples_json(self) -> None:
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
                    "tags_json TEXT, "
                    "topics_json TEXT, "
                    "categories_json TEXT, "
                    "form_of_json TEXT, "
                    "alt_of_json TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO sense_glosses "
                    "(headword, headword_lc, translation, translation_lc, pos, entry_ord, sense_ord, gloss_ord, raw_glosses_json, tags_json, topics_json, categories_json, form_of_json, alt_of_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "cargo",
                        "cargo",
                        "office",
                        "office",
                        "noun",
                        1,
                        0,
                        0,
                        json.dumps(["professional office or role"]),
                        None,
                        None,
                        None,
                        None,
                        None,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            records_by_headword = load_freedict_sqlite_gloss_records_ordered(path)
            records_by_translation = load_translation_gloss_records_by_translation_ordered(
                path,
                translations=("office",),
            )

        self.assertIn("cargo", records_by_headword)
        self.assertEqual(records_by_headword["cargo"][0].translation, "office")
        self.assertNotIn("sense_examples", records_by_headword["cargo"][0].metadata)
        self.assertIn("office", records_by_translation)
        self.assertEqual(records_by_translation["office"][0].translation, "cargo")

    def test_sqlite_base_form_loader_collects_sanitized_glosses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE entries ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT, "
                    "rank INTEGER, "
                    "pos TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("Haus", "haus", " House! ", 1, "noun"),
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("Haus", "haus", "homes", 2, "noun"),
                )
                conn.commit()
            finally:
                conn.close()
            base_forms = load_freedict_gloss_base_forms(path, target_lang="en")
        self.assertEqual(base_forms, {"house", "homes"})

    def test_sqlite_headword_loader_preserves_raw_infinitive_spellings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-spa.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE entries ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT, "
                    "rank INTEGER, "
                    "pos TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("To Remove", "to remove", "quitar", 1, "verb"),
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, rank, pos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("House", "house", "casa", 2, "noun"),
                )
                conn.commit()
            finally:
                conn.close()
            headwords = load_freedict_headwords(path)
        self.assertEqual(headwords, ("House", "To Remove"))

    def test_translation_gloss_base_forms_uses_persistent_path_cache(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en"> House! </quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.tei"
            path.write_text(payload, encoding="utf-8")
            first = load_translation_gloss_base_forms(path, target_lang="en")
            with patch(
                "lexishift_core.resources.dict_loaders.load_freedict_gloss_base_forms",
                side_effect=AssertionError("translation gloss base-form cache should be warm"),
            ):
                second = load_translation_gloss_base_forms(path, target_lang="en")
        self.assertEqual(first, {"house"})
        self.assertEqual(second, {"house"})

    def test_translation_headwords_uses_persistent_path_cache(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>To Remove</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">quitar</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-spa.tei"
            path.write_text(payload, encoding="utf-8")
            first = load_translation_headwords(path)
            with patch(
                "lexishift_core.resources.dict_loaders.load_freedict_headwords",
                side_effect=AssertionError("translation headword cache should be warm"),
            ):
                second = load_translation_headwords(path)
        self.assertEqual(first, ("To Remove",))
        self.assertEqual(second, ("To Remove",))


if __name__ == "__main__":
    unittest.main()
