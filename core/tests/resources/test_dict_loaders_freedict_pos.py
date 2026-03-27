from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import (  # noqa: E402
    load_freedict_gloss_base_forms,
    load_freedict_sqlite_gloss_records_ordered,
    load_freedict_tei_gloss_records_ordered,
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


if __name__ == "__main__":
    unittest.main()
