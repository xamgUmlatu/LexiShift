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

from srs_learner_difficulty_wiktionary_metadata_en_de import build_report  # noqa: E402


class SrsLearnerDifficultyWiktionaryMetadataEnDeTests(unittest.TestCase):
    def test_extracts_marked_variant_and_ambiguity_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_db = Path(tmp) / "freq.sqlite"
            _write_frequency_db(frequency_db)
            report = build_report(
                frequency_db=frequency_db,
                top_n=4,
                generated_at="2026-07-06T00:00:00+00:00",
                raw_entries=[
                    {
                        "word": "frei",
                        "lang_code": "de",
                        "pos": "adj",
                        "categories": ["German terms with rare senses"],
                        "senses": [
                            {"glosses": ["free"], "tags": ["rare"]},
                            {"glosses": ["unrestricted"], "topics": ["law"]},
                        ],
                        "forms": [{"form": "freier"}],
                        "sounds": [{"ipa": "x"}],
                    },
                    {
                        "word": "ging",
                        "lang_code": "de",
                        "pos": "verb",
                        "senses": [
                            {
                                "glosses": ["went"],
                                "form_of": [{"word": "gehen"}],
                                "tags": ["colloquial"],
                            }
                        ],
                    },
                    {
                        "word": "haus",
                        "lang_code": "de",
                        "pos": "noun",
                        "senses": [{"glosses": ["house"]}],
                    },
                    {"word": "free", "lang_code": "en", "pos": "adj", "senses": []},
                ],
            )

        self.assertEqual(report["status"], "ok")
        summary = report["summary"]
        self.assertEqual(summary["candidate_count"], 4)
        self.assertEqual(summary["metadata_coverage_count"], 3)
        self.assertEqual(summary["marked_usage_count"], 2)
        self.assertEqual(summary["rare_dated_count"], 1)
        self.assertEqual(summary["colloquial_count"], 1)
        self.assertEqual(summary["form_or_alt_of_count"], 1)
        metadata = report["wiktionary_metadata_by_lemma"]
        self.assertEqual(metadata["frei"]["sense_count"], 2)
        self.assertTrue(metadata["frei"]["rare_dated_flag"])
        self.assertIn("rare", metadata["frei"]["marked_terms"])
        self.assertEqual(metadata["ging"]["form_of_count"], 1)
        self.assertTrue(metadata["ging"]["colloquial_flag"])
        self.assertNotIn("free", metadata)


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT NOT NULL,
                core_rank REAL,
                pmw REAL,
                pos TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?)",
            (
                ("frei", 1.0, 100.0, "ADJ:POS"),
                ("ging", 2.0, 80.0, "VER:PAST"),
                ("haus", 3.0, 70.0, "SUB:NOM:SIN:NEU"),
                ("fehlt", 4.0, 10.0, "VER:FIN"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
