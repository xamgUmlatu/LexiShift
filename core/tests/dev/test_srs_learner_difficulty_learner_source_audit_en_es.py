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

from srs_learner_difficulty_learner_source_audit_en_es import (  # noqa: E402
    build_report,
    parse_espanjapeli_words,
    parse_openlingo_a1_spanish,
    parse_openlingo_spanish_dictionary,
    parse_wiktionary_spanish1000,
)


class SrsLearnerDifficultyLearnerSourceAuditEnEsTests(unittest.TestCase):
    def test_parses_safe_source_shapes(self) -> None:
        wiki_hits = parse_wiktionary_spanish1000(
            """
{| class="wikitable"
|-
! rank
! word
! occurrences (ppm)
! lemma forms
|-
|1.
|[[es#Spanish|es]]
|16620
|[[ser#Spanish|ser]]
|-
|500.
|[[hospital#Spanish|hospital]]
|42
|[[hospital#Spanish|hospital]]
|}
"""
        )
        espanjapeli_hits = parse_espanjapeli_words(
            """
{ spanish: 'el hospital', english: 'hospital', finnish: 'sairaala' },
{ spanish: 'la comida', english: 'food', frequency: { rank: 483, cefrLevel: 'A1' } },
"""
        )
        openlingo_hits = parse_openlingo_a1_spanish(
            """
- "familia" = "family"
sentence: "Steve tiene una familia."
srsWords: "familia ciudad"
"""
        )
        openlingo_dict_hits = parse_openlingo_spanish_dictionary(
            """
[
  {"word":"hoy","useful_for_flashcard":true,"cefr_level":"A1","word_frequency":113},
  {"word":"hoy","useful_for_flashcard":true,"cefr_level":"A1","word_frequency":113},
  {"word":"relajado","useful_for_flashcard":true,"cefr_level":"B1","word_frequency":8599},
  {"word":"skip","useful_for_flashcard":false,"cefr_level":"A1","word_frequency":1}
]
"""
        )

        wiki_terms = {hit.source_term for hit in wiki_hits}
        self.assertIn("ser", wiki_terms)
        self.assertIn("hospital", wiki_terms)
        self.assertTrue(any(hit.rank == 500 for hit in wiki_hits))
        self.assertTrue(any(hit.source_term == "el hospital" for hit in espanjapeli_hits))
        self.assertTrue(any(hit.level == "A1" for hit in espanjapeli_hits))
        self.assertEqual({hit.level for hit in openlingo_hits}, {"A1"})
        self.assertEqual(len([hit for hit in openlingo_dict_hits if hit.source_term == "hoy"]), 1)
        self.assertTrue(any(hit.level == "B1" for hit in openlingo_dict_hits))
        self.assertFalse(any(hit.source_term == "skip" for hit in openlingo_dict_hits))

    def test_builds_overlay_and_candidate_coverage_from_provided_texts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            _write_frequency_db(frequency_db)

            report = build_report(
                frequency_db=frequency_db,
                top_n=5,
                sample_limit=4,
                generated_at="2026-07-05T00:00:00+00:00",
                source_texts={
                    "wiktionary_spanish1000": """
|-
|1.
|[[es#Spanish|es]]
|16620
|[[ser#Spanish|ser]]
|-
|500.
|[[hospital#Spanish|hospital]]
|42
|[[hospital#Spanish|hospital]]
""",
                    "espanjapeli_mit_words": "{ spanish: 'el agua', english: 'water' }",
                    "openlingo_mit_a1_spanish": '- "familia" = "family"',
                    "openlingo_mit_spanish_dictionary": (
                        '[{"word":"hoy","useful_for_flashcard":true,'
                        '"cefr_level":"A1","word_frequency":113},'
                        '{"word":"enseñar","useful_for_flashcard":true,'
                        '"cefr_level":"A1","word_frequency":2274}]'
                    ),
                },
            )

            self.assertEqual(report["status"], "ok")
            overlay = report["source_overlay"]
            self.assertIn("hospital", overlay)
            self.assertIn("agua", overlay)
            self.assertIn("hoy", overlay)
            self.assertIn("enseñar", overlay)
            self.assertNotIn("ensenar", overlay)
            coverage = report["candidate_coverage"]
            self.assertEqual(coverage["candidate_count"], 5)
            self.assertGreaterEqual(coverage["matched_candidate_count"], 3)
            matched_lemmas = {row["lemma"] for row in coverage["highest_score_matched_samples"]}
            self.assertNotIn("ensenar", matched_lemmas)


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE frequency ("
            "id REAL, pmw REAL, freq REAL, lemma TEXT, pos TEXT, source_family TEXT, "
            "source_rank REAL, source_frequency REAL, spalex_rank REAL, spalex_freq REAL, "
            "spalex_zipf REAL, spalex_prevalence_total REAL, spalex_percent_total REAL)"
        )
        rows = [
            (1, 600.0, 600.0, "ser", "v", "spalex", 1, 600.0, 1, 600.0, 6.5, 99.0, 2.2),
            (2, 500.0, 500.0, "hospital", "n", "spalex", 2, 500.0, 2, 500.0, 6.0, 98.0, 2.0),
            (3, 400.0, 400.0, "agua", "n", "spalex", 3, 400.0, 3, 400.0, 5.8, 97.0, 1.9),
            (4, 300.0, 300.0, "familia", "n", "spalex", 4, 300.0, 4, 300.0, 5.5, 95.0, 1.7),
            (5, 250.0, 250.0, "ensenar", "v", "spalex", 5, 250.0, 5, 250.0, 5.3, 90.0, 1.5),
        ]
        conn.executemany(
            "INSERT INTO frequency ("
            "id, pmw, freq, lemma, pos, source_family, source_rank, source_frequency, "
            "spalex_rank, spalex_freq, spalex_zipf, spalex_prevalence_total, "
            "spalex_percent_total"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
