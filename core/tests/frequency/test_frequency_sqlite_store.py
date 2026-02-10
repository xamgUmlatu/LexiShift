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

from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore  # noqa: E402


class TestSqliteFrequencyStore(unittest.TestCase):
    def test_iter_top_by_rank_pushes_null_ranks_last(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "freq.sqlite"
            conn = sqlite3.connect(db_path)
            conn.execute(
                "CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)"
            )
            conn.executemany(
                "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
                [
                    ("null_high", None, 999.0),
                    ("rank_2", 2.0, 10.0),
                    ("rank_1", 1.0, 20.0),
                    ("null_low", None, 1.0),
                ],
            )
            conn.commit()
            conn.close()

            store = SqliteFrequencyStore(
                SqliteFrequencyConfig(path=db_path, table="frequency")
            )
            try:
                rows = list(store.iter_top_by_rank(limit=4))
            finally:
                store.close()

            lemmas = [row["lemma"] for row in rows]
            self.assertEqual(lemmas, ["rank_1", "rank_2", "null_high", "null_low"])


if __name__ == "__main__":
    unittest.main()
