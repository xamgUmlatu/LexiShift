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

from srs_topic_signal_inventory_en_es import build_report, render_markdown  # noqa: E402


class SrsTopicSignalInventoryTests(unittest.TestCase):
    def test_inventories_trusted_topics_and_review_only_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                candidates=(("fixture", frequency_db),),
                kaikki_forward_db=kaikki_db,
                top_n=4,
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            audit = report["audits"][0]
            self.assertEqual(audit["combined_coverage"]["trusted_profile_row_count"], 2)
            self.assertEqual(audit["combined_coverage"]["review_only_signal_row_count"], 4)
            self.assertEqual(audit["channel_coverage"]["sense_topics"]["row_count"], 2)
            self.assertEqual(audit["channel_coverage"]["sense_tags"]["row_count"], 2)
            product_topics = {row["topic"]: row for row in audit["product_topic_examples"]}
            self.assertEqual(product_topics["medicine"]["trusted_count"], 1)
            self.assertEqual(product_topics["literature"]["trusted_count"], 1)

            markdown = render_markdown(report)
            self.assertIn("SRS Topic Signal Inventory", markdown)
            self.assertIn("SAT and TOEFL", markdown)

    def test_missing_frequency_db_marks_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kaikki_db = Path(tmp) / "kaikki.sqlite"
            _write_kaikki_db(kaikki_db)

            report = build_report(
                candidates=(("missing", Path(tmp) / "missing.sqlite"),),
                kaikki_forward_db=kaikki_db,
                top_n=4,
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "review")
            self.assertIn("candidate_missing:missing", report["summary"]["issues"])


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma) VALUES (?, ?, ?)",
            [
                (1, 100.0, "salud"),
                (2, 90.0, "novela"),
                (3, 80.0, "perro"),
                (4, 70.0, "mesa"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entry_meta (headword_lc TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "headword_lc TEXT, topics_json TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.executemany(
            "INSERT INTO entry_meta (headword_lc, tags_json, categories_json) VALUES (?, ?, ?)",
            [
                ("salud", '["feminine"]', '["Spanish nouns"]'),
                ("perro", '["colloquial"]', '["Spanish animal terms"]'),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(headword_lc, topics_json, tags_json, categories_json) VALUES (?, ?, ?, ?)",
            [
                ("salud", '["medicine"]', '["formal"]', '["Health"]'),
                ("novela", '["literature"]', "[]", '["Spanish literature"]'),
                ("mesa", "[]", '["regional"]', "[]"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
