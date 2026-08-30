from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_manual_semantic_lexicon_en_de import build_report, render_markdown  # noqa: E402


class SrsTopicManualSemanticLexiconEnDeTests(unittest.TestCase):
    def test_build_report_matches_german_corpus_forms_and_reports_unmatched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lexicon = root / "lexicon.json"
            frequency = root / "frequency.sqlite"
            _write_frequency_db(frequency, ("baum", "spiel", "geld"))
            _write_json(
                lexicon,
                {
                    "schema_version": 1,
                    "language_pair": "en-de",
                    "collections": [
                        {
                            "id": "plants",
                            "target_family": "plants_nature",
                            "promotion_eligible": True,
                            "membership": 1.0,
                            "confidence": 0.98,
                            "entries": ["Baum", "Phantomwald"],
                        },
                        {
                            "id": "games",
                            "target_family": "games",
                            "promotion_eligible": True,
                            "membership": 1.0,
                            "confidence": 0.98,
                            "entries": ["Spiel"],
                        },
                    ],
                },
            )

            report = build_report(
                lexicon_json=lexicon,
                frequency_db=frequency,
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["row_count"], 2)
        self.assertEqual(report["summary"]["unique_lemma_count"], 2)
        self.assertEqual(report["summary"]["unmatched_entry_count"], 1)
        self.assertEqual(
            report["summary"]["runtime_effective_counts_by_topic"],
            {"games": 1, "plants_nature": 1},
        )
        row = next(item for item in report["rows"] if item["lemma"] == "baum")
        self.assertEqual(row["confidence_label"], "strong")
        self.assertEqual(row["source_channel"], "product_owned_manual_semantic_lexicon")
        self.assertEqual(row["membership"], 1.0)
        self.assertEqual(row["provenance"]["original_lemma"], "Baum")
        markdown = render_markdown(report)
        self.assertIn("Manual Semantic Topic Lexicon", markdown)
        self.assertIn("Phantomwald", markdown)

    def test_duplicate_lemma_topic_rows_merge_collection_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lexicon = root / "lexicon.json"
            frequency = root / "frequency.sqlite"
            _write_frequency_db(frequency, ("spiel",))
            _write_json(
                lexicon,
                {
                    "schema_version": 1,
                    "language_pair": "en-de",
                    "collections": [
                        {
                            "id": "games_a",
                            "target_family": "games",
                            "promotion_eligible": True,
                            "entries": ["Spiel"],
                        },
                        {
                            "id": "games_b",
                            "target_family": "games",
                            "promotion_eligible": True,
                            "entries": ["spiel"],
                        },
                    ],
                },
            )

            report = build_report(
                lexicon_json=lexicon,
                frequency_db=frequency,
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["summary"]["row_count"], 1)
        self.assertEqual(report["summary"]["duplicate_row_count"], 1)
        self.assertEqual(
            set(report["rows"][0]["provenance"]["collection_ids"]),
            {"games_a", "games_b"},
        )


def _write_frequency_db(path: Path, lemmas: tuple[str, ...]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos
            ) VALUES (?, ?, ?, ?)
            """,
            (
                (lemma, float(index + 1), float(100 - index), "SUB:NOM:SIN:NEU")
                for index, lemma in enumerate(lemmas)
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
