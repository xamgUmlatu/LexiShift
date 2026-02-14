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

    def test_iter_top_by_rank_does_not_fail_when_pmw_column_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "freq.sqlite"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, freq REAL)")
            conn.executemany(
                "INSERT INTO frequency (lemma, core_rank, freq) VALUES (?, ?, ?)",
                [
                    ("rank_2", 2.0, 10.0),
                    ("rank_1", 1.0, 20.0),
                ],
            )
            conn.commit()
            conn.close()

            store = SqliteFrequencyStore(
                SqliteFrequencyConfig(path=db_path, table="frequency")
            )
            try:
                rows = list(store.iter_top_by_rank(limit=2))
            finally:
                store.close()

            lemmas = [row["lemma"] for row in rows]
            self.assertEqual(lemmas, ["rank_1", "rank_2"])

    def test_max_value_falls_back_from_pmw_to_freq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "freq.sqlite"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, freq REAL)")
            conn.executemany(
                "INSERT INTO frequency (lemma, core_rank, freq) VALUES (?, ?, ?)",
                [
                    ("alpha", 1.0, 5.0),
                    ("beta", 2.0, 3.0),
                ],
            )
            conn.commit()
            conn.close()

            store = SqliteFrequencyStore(
                SqliteFrequencyConfig(path=db_path, table="frequency")
            )
            try:
                value = store.max_value("pmw")
            finally:
                store.close()

            self.assertEqual(value, 5.0)

    def test_iter_top_by_rank_falls_back_from_core_rank_to_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "freq.sqlite"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE frequency (lemma TEXT, ID REAL, freq REAL)")
            conn.executemany(
                "INSERT INTO frequency (lemma, ID, freq) VALUES (?, ?, ?)",
                [
                    ("rank_2", 2.0, 10.0),
                    ("rank_1", 1.0, 20.0),
                ],
            )
            conn.commit()
            conn.close()

            store = SqliteFrequencyStore(
                SqliteFrequencyConfig(path=db_path, table="frequency")
            )
            try:
                rows = list(store.iter_top_by_rank(limit=2))
            finally:
                store.close()

            lemmas = [row["lemma"] for row in rows]
            self.assertEqual(lemmas, ["rank_1", "rank_2"])


if __name__ == "__main__":
    unittest.main()
