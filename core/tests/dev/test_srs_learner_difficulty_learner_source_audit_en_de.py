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

from srs_learner_difficulty_learner_source_audit_en_de import (  # noqa: E402
    build_report,
    parse_goethe_a1_wordlist_text,
    parse_odenet_basiswortschatz,
    parse_openlingo_german_dictionary,
    parse_sprachomat_goethe_stems,
)


class SrsLearnerDifficultyLearnerSourceAuditEnDeTests(unittest.TestCase):
    def test_parses_openlingo_and_sprachomat_source_shapes(self) -> None:
        openlingo_hits = parse_openlingo_german_dictionary(
            """
[
  {"word":"sein","useful_for_flashcard":true,"cefr_level":"A1","word_frequency":6},
  {"word":"die Katze","useful_for_flashcard":true,"cefr_level":"A1","word_frequency":700},
  {"word":"Bundesverfassungsgericht","useful_for_flashcard":true,"cefr_level":"C1","word_frequency":18000},
  {"word":"skip","useful_for_flashcard":false,"cefr_level":"A1","word_frequency":1}
]
"""
        )
        stem_hits = parse_sprachomat_goethe_stems(
            '"","level","stem"\n"1","B1","abbieg"\n"2","A2","abe"\n"3","A1","kauf"\n'
        )
        odenet_hits = parse_odenet_basiswortschatz(
            """
<LexicalResource xmlns:dc="http://purl.org/dc/elements/1.1/">
<Lexicon id="odenet">
<LexicalEntry id="w1"><Lemma writtenForm="Kernspaltung" partOfSpeech="n"/></LexicalEntry>
<LexicalEntry id="w2" dc:type="Basiswortschatz" confidenceScore="1.0"><Lemma writtenForm="Kurs" partOfSpeech="n"/></LexicalEntry>
<LexicalEntry id="w3" dc:type="Basiswortschatz" confidenceScore="0.6"><Lemma writtenForm="gut" partOfSpeech="a"/></LexicalEntry>
</Lexicon>
</LexicalResource>
"""
        )

        openlingo_terms = {hit.source_term for hit in openlingo_hits}
        odenet_terms = {hit.source_term for hit in odenet_hits}
        self.assertIn("sein", openlingo_terms)
        self.assertIn("die Katze", openlingo_terms)
        self.assertIn("Bundesverfassungsgericht", openlingo_terms)
        self.assertFalse(any(hit.source_term == "skip" for hit in openlingo_hits))
        self.assertTrue(any(hit.level == "C1" for hit in openlingo_hits))
        self.assertTrue(any(hit.source_term == "abbieg" for hit in stem_hits))
        self.assertFalse(any(hit.source_term == "abe" for hit in stem_hits))
        self.assertTrue(all(hit.match_type == "stem_prefix" for hit in stem_hits))
        self.assertIn("Kurs", odenet_terms)
        self.assertIn("gut", odenet_terms)
        self.assertNotIn("Kernspaltung", odenet_terms)
        self.assertTrue(all(hit.source_id == "odenet_basiswortschatz" for hit in odenet_hits))

    def test_parses_official_goethe_a1_wordlist_text_conservatively(self) -> None:
        hits = parse_goethe_a1_wordlist_text(
            """
VS_02_280312 Seite 9
A
ab Ab morgen muss ich arbeiten.
die Adresse,-en Können Sie mir seine Adresse sagen?
Wir müssen noch meinen Bruder abholen.
(sich) anziehen Ich muss mich noch anziehen.
das Haus, -ä, er In welchem Haus wohnst du?
"""
        )
        terms = {hit.source_term for hit in hits}
        self.assertIn("ab", terms)
        self.assertIn("Adresse", terms)
        self.assertIn("anziehen", terms)
        self.assertIn("Haus", terms)
        self.assertNotIn("Wir", terms)
        self.assertTrue(all(hit.source_id == "goethe_official_a1_wordlist" for hit in hits))

    def test_builds_candidate_overlay_from_exact_and_stem_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_db = Path(tmp) / "freq.sqlite"
            _write_frequency_db(frequency_db)

            report = build_report(
                frequency_db=frequency_db,
                top_n=8,
                sample_limit=5,
                generated_at="2026-07-06T00:00:00+00:00",
                source_texts={
                    "openlingo_mit_german_dictionary": """
[
  {"word":"sein","useful_for_flashcard":true,"cefr_level":"A1","word_frequency":6},
  {"word":"Katze","useful_for_flashcard":true,"cefr_level":"A1","word_frequency":700},
  {"word":"Bundesverfassungsgericht","useful_for_flashcard":true,"cefr_level":"C1","word_frequency":18000}
]
""",
                    "sprachomat_goethe_a1a2b1_stems": (
                        '"","level","stem"\n"1","B1","abbieg"\n"2","A1","kauf"\n'
                    ),
                    "goethe_official_a1_wordlist": (
                        "ab Ab morgen muss ich arbeiten.\n"
                        "das Haus, -ä, er In welchem Haus wohnst du?\n"
                    ),
                    "odenet_basiswortschatz": """
<LexicalResource xmlns:dc="http://purl.org/dc/elements/1.1/">
<Lexicon id="odenet">
<LexicalEntry id="w1" dc:type="Basiswortschatz" confidenceScore="1.0"><Lemma writtenForm="Kurs" partOfSpeech="n"/></LexicalEntry>
<LexicalEntry id="w2" dc:type="Basiswortschatz" confidenceScore="1.0"><Lemma writtenForm="gut" partOfSpeech="a"/></LexicalEntry>
</Lexicon>
</LexicalResource>
""",
                },
            )

        self.assertEqual(report["status"], "ok")
        overlay = report["source_overlay"]
        self.assertIn("sein", overlay)
        self.assertIn("katze", {key.lower() for key in overlay})
        self.assertIn("abbiegen", overlay)
        self.assertIn("kaufen", overlay)
        self.assertIn("Kurs", overlay)
        self.assertIn("Bundesverfassungsgericht", overlay)
        self.assertEqual(report["candidate_coverage"]["candidate_count"], 8)
        self.assertGreaterEqual(report["candidate_coverage"]["matched_candidate_count"], 5)
        abbiegen = overlay["abbiegen"]
        self.assertIn("sprachomat_goethe_a1a2b1_stems", abbiegen["source_ids"])
        self.assertEqual(abbiegen["min_level"], "B1")
        kurs = overlay["Kurs"]
        self.assertIn("odenet_basiswortschatz", kurs["source_ids"])
        self.assertAlmostEqual(kurs["learner_core_score"], 0.18)
        sein = overlay["sein"]
        self.assertIn("openlingo_mit_german_dictionary", sein["source_ids"])


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
                ("sein", 1.0, 1000.0, "VER:INF:NON"),
                ("katze", 2.0, 100.0, "SUB:NOM:SIN:FEM"),
                ("abbiegen", 3.0, 80.0, "VER:INF:NON"),
                ("kaufen", 4.0, 70.0, "VER:INF:NON"),
                ("Bundesverfassungsgericht", 5.0, 20.0, "SUB:NOM:SIN:NEU"),
                ("Kurs", 6.0, 15.0, "SUB:NOM:SIN:MAS"),
                ("gut", 7.0, 12.0, "ADJ:POS"),
                ("zufall", 8.0, 10.0, "SUB:NOM:SIN:MAS"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
