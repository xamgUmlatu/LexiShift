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

from lexishift_core.resources.synonyms import SynonymGenerator, SynonymSources  # noqa: E402


class TestSynonymTranslationPacks(unittest.TestCase):
    def test_synonym_generator_reads_freedict_sqlite_translation_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "freedict-de-en.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE entries ("
                    "headword TEXT NOT NULL, "
                    "headword_lc TEXT NOT NULL, "
                    "translation TEXT NOT NULL, "
                    "translation_lc TEXT NOT NULL, "
                    "rank INTEGER NOT NULL, "
                    "pos TEXT, "
                    "entry_ord INTEGER NOT NULL, "
                    "gloss_ord INTEGER NOT NULL"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("Haus", "haus", "house", "house", 1, "noun", 1, 0),
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("Haus", "haus", "home", "home", 2, "noun", 1, 1),
                )
                conn.commit()
            finally:
                conn.close()

            generator = SynonymGenerator(SynonymSources(freedict_de_en_path=path))
            synonyms = generator.synonyms_for("Haus")

        self.assertEqual(synonyms, ["home", "house"])


if __name__ == "__main__":
    unittest.main()
