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
from lexishift_core.rulegen.semantic_shadow_frequency import (  # noqa: E402
    ShadowFrequencyLookup,
    enrich_candidate_frequency_details,
)


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (lemma TEXT, freq REAL, id REAL)")
    conn.executemany(
        "INSERT INTO frequency (lemma, freq, id) VALUES (?, ?, ?)",
        [
            ("cargo", 90.0, 2.0),
            ("camello", 5.0, 50.0),
            ("trabajo", 120.0, 1.0),
        ],
    )
    conn.commit()
    conn.close()


class TestSemanticShadowFrequency(unittest.TestCase):
    def test_lookup_build_details_uses_freq_and_rank(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "freq-es.sqlite"
            _write_frequency_db(db_path)
            store = SqliteFrequencyStore(SqliteFrequencyConfig(path=db_path))
            lookup = ShadowFrequencyLookup(
                pair="en-es",
                pack_id="freq-es-cde",
                provider="freq-es-cde",
                value_column="freq",
                rank_column="id",
                max_value=120.0,
                max_rank=50.0,
                _store=store,
            )
            try:
                cargo = lookup.build_details("cargo")
                missing = lookup.build_details("desconocido")
            finally:
                lookup.close()

        self.assertTrue(cargo["target_frequency_present"])
        self.assertEqual(cargo["target_frequency_value"], 90.0)
        self.assertEqual(cargo["target_frequency_rank"], 2.0)
        self.assertGreater(float(cargo["target_frequency_score"]), 0.0)
        self.assertFalse(missing["target_frequency_present"])
        self.assertEqual(float(missing["target_frequency_score"]), 0.0)

    def test_enrich_candidate_frequency_details_updates_target_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "freq-es.sqlite"
            _write_frequency_db(db_path)
            store = SqliteFrequencyStore(SqliteFrequencyConfig(path=db_path))
            lookup = ShadowFrequencyLookup(
                pair="en-es",
                pack_id="freq-es-cde",
                provider="freq-es-cde",
                value_column="freq",
                rank_column="id",
                max_value=120.0,
                max_rank=50.0,
                _store=store,
            )
            candidate = {"target": "trabajo"}
            try:
                enrich_candidate_frequency_details(candidate=candidate, frequency_lookup=lookup)
            finally:
                lookup.close()

        self.assertTrue(candidate["target_frequency_present"])
        self.assertEqual(candidate["target_frequency_value"], 120.0)
        self.assertEqual(candidate["target_frequency_rank"], 1.0)
        self.assertGreater(float(candidate["target_frequency_score"]), 0.0)


if __name__ == "__main__":
    unittest.main()
