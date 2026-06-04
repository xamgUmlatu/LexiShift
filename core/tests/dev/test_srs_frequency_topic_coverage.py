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

from srs_frequency_topic_coverage import build_report  # noqa: E402


class TestSrsFrequencyTopicCoverage(unittest.TestCase):
    def test_build_report_detects_present_topic_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "synthetic.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("CREATE TABLE frequency (rank REAL, lemma TEXT, topics TEXT)")
                conn.executemany(
                    "INSERT INTO frequency (rank, lemma, topics) VALUES (?, ?, ?)",
                    [
                        (1, "dog", "animals"),
                        (2, "cat", "animals,pets"),
                        (3, "money", ""),
                    ],
                )
                conn.commit()
            finally:
                conn.close()

            report = build_report([db_path], frontier_limit=2)
            summary = report["summary"]
            self.assertEqual(summary["fail_count"], 0)
            self.assertEqual(summary["warn_count"], 0)
            audit = report["audits"][0]
            self.assertEqual(audit["table_name"], "frequency")
            self.assertEqual(audit["topic_columns_present"], ["topics"])
            self.assertEqual(audit["any_topic_rows"], 2)
            frontier = audit["frontier"]
            self.assertEqual(frontier["row_count"], 2)
            self.assertEqual(frontier["rows_with_raw_topics"], 2)
            self.assertEqual(frontier["rows_with_canonical_topics"], 2)
            self.assertEqual(frontier["resolved_rank_column"], "rank")

    def test_build_report_tracks_canonical_frontier_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "synthetic.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("CREATE TABLE frequency (rank REAL, lemma TEXT, sense_topics TEXT)")
                conn.executemany(
                    "INSERT INTO frequency (rank, lemma, sense_topics) VALUES (?, ?, ?)",
                    [
                        (1, "poker", '["card-games"]'),
                        (2, "dog", '["pets"]'),
                        (3, "money", '["business"]'),
                    ],
                )
                conn.commit()
            finally:
                conn.close()

            report = build_report([db_path], frontier_limit=3)
            frontier = report["audits"][0]["frontier"]
            canonical_topics = {
                entry["topic"]: entry["count"] for entry in frontier["top_canonical_topics"]
            }

            self.assertEqual(frontier["rows_with_canonical_topics"], 3)
            self.assertIn("games", canonical_topics)
            self.assertIn("animals", canonical_topics)
            self.assertIn("finance", canonical_topics)


if __name__ == "__main__":
    unittest.main()
