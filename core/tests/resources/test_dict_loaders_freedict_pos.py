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

    def test_sqlite_loader_backfills_missing_pos_for_duplicate_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.sqlite"
            with sqlite3.connect(path) as conn:
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
            records = load_freedict_sqlite_gloss_records_ordered(path)
        self.assertIn("Haus", records)
        self.assertEqual(len(records["Haus"]), 1)
        self.assertEqual(records["Haus"][0].translation, "house")
        self.assertEqual(records["Haus"][0].pos_raw, "noun")


if __name__ == "__main__":
    unittest.main()
