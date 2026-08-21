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

from srs_learner_difficulty_external_source_audit_en_de import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyExternalSourceAuditEnDeTests(unittest.TestCase):
    def test_build_report_combines_modern_child_and_optional_corpus_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_db = Path(tmp) / "freq.sqlite"
            _write_frequency_db(frequency_db)

            report = build_report(
                frequency_db=frequency_db,
                top_n=6,
                sample_limit=5,
                generated_at="2026-07-06T00:00:00+00:00",
                fetch_network=False,
                include_wordfreq=False,
                source_texts={
                    "olastor_opensubtitles_cistem": (
                        "word,freq\nhaus,1000\ncomputer,100\nabendessen,5\n"
                    ),
                    "klexikon_child_encyclopedia_titles": (
                        '[{"title":"Haus"},{"title":"Mond"},{"title":"Computer"}]'
                    ),
                    "german_commons_sample": (
                        '{"text":"Das Haus und der Computer stehen im modernen Alltag."}\n'
                        '{"text":"Ein Mond ist am Himmel."}\n'
                    ),
                    "german_commons_manifest": (
                        '{"cardData":{"license":["odc-by"],"configs":[{"config_name":"web"}]}}'
                    ),
                },
            )

        self.assertEqual(report["status"], "ok")
        overlay = report["external_source_by_lemma"]
        self.assertIn("Haus", overlay)
        self.assertIn("Computer", overlay)
        self.assertIn("Mond", overlay)
        haus = overlay["Haus"]
        self.assertTrue(haus["modern_source_known"])
        self.assertTrue(haus["child_source_known"])
        self.assertIn("olastor_opensubtitles_cistem", haus["source_ids"])
        self.assertIn("klexikon_child_encyclopedia_titles", haus["source_ids"])
        mond = overlay["Mond"]
        self.assertTrue(mond["child_source_known"])
        self.assertIn("german_commons_sample", mond["source_ids"])
        coverage = report["candidate_coverage"]
        self.assertEqual(coverage["candidate_count"], 6)
        self.assertGreaterEqual(coverage["matched_candidate_count"], 3)
        markdown = render_markdown(report)
        self.assertIn("External Difficulty Source Audit", markdown)
        self.assertIn("olastor_opensubtitles_cistem", markdown)
        self.assertIn("klexikon_child_encyclopedia_titles", markdown)


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
                ("Haus", 1.0, 1000.0, "SUB:NOM:SIN:NEU"),
                ("Computer", 2.0, 800.0, "SUB:NOM:SIN:MAS"),
                ("Mond", 3.0, 200.0, "SUB:NOM:SIN:MAS"),
                ("Abendessen", 4.0, 80.0, "SUB:NOM:SIN:NEU"),
                ("gehen", 5.0, 60.0, "VER:INF:NON"),
                ("zufall", 6.0, 10.0, "SUB:NOM:SIN:MAS"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
