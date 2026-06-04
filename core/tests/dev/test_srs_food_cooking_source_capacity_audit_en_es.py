from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_food_cooking_source_capacity_audit_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsFoodCookingSourceCapacityAuditTests(unittest.TestCase):
    def test_capacity_audit_separates_full_source_from_current_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                frequency_db=frequency_db,
                kaikki_forward_db=kaikki_db,
                top_n=10,
                generated_at="2026-05-19T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["source_capacity"]["candidate_count"], 4)
            self.assertEqual(report["current_frontier"]["candidate_count"], 2)
            self.assertEqual(report["current_frontier"]["outside_current_candidate_count"], 2)

            probes = {row["lemma"]: row for row in report["common_food_probe_rows"]}
            self.assertTrue(probes["pan"]["in_current_frequency_frontier"])
            self.assertTrue(probes["pan"]["has_current_policy_signal"])
            self.assertFalse(probes["arroz"]["in_current_frequency_frontier"])
            self.assertTrue(probes["arroz"]["has_current_policy_signal"])

            markdown = render_markdown(report)
            self.assertIn("Food/Cooking Source Capacity Audit", markdown)
            self.assertIn("Outside current frontier", markdown)


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma) VALUES (?, ?, ?)",
            [
                (1, 100.0, "pan"),
                (2, 90.0, "té"),
                (3, 80.0, "mesa"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entry_meta ("
            "entry_ord INTEGER, headword_lc TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "entry_ord INTEGER, sense_ord INTEGER, gloss_ord INTEGER, headword_lc TEXT, "
            "pos TEXT, translation TEXT, raw_glosses_json TEXT, tags_json TEXT, "
            "topics_json TEXT, categories_json TEXT)"
        )
        conn.executemany(
            "INSERT INTO entry_meta "
            "(entry_ord, headword_lc, tags_json, categories_json) VALUES (?, ?, ?, ?)",
            [
                (1, "pan", "[]", "[]"),
                (2, "té", "[]", '["es:Beverages"]'),
                (3, "arroz", "[]", '["es:Foods"]'),
                (4, "agua", "[]", '["es:Beverages"]'),
                (5, "mesa", "[]", "[]"),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(entry_ord, sense_ord, gloss_ord, headword_lc, pos, translation, "
            "raw_glosses_json, tags_json, topics_json, categories_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 0, 0, "pan", "noun", "bread", "[]", "[]", "[]", "[]"),
                (2, 0, 0, "té", "noun", "tea", "[]", "[]", "[]", "[]"),
                (3, 0, 0, "arroz", "noun", "rice", "[]", "[]", "[]", '["es:Foods"]'),
                (4, 0, 0, "agua", "noun", "water", "[]", "[]", "[]", '["es:Beverages"]'),
                (5, 0, 0, "mesa", "noun", "table", "[]", "[]", "[]", "[]"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
