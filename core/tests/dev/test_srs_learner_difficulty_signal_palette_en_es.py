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

from srs_learner_difficulty_signal_palette_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultySignalPaletteEnEsTests(unittest.TestCase):
    def test_inventories_frequency_pos_dictionary_topic_and_form_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            pos_overlay = root / "pos.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            _write_frequency_db(frequency_db)
            _write_pos_overlay(pos_overlay)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                frequency_db=frequency_db,
                pos_overlay_path=pos_overlay,
                kaikki_forward_db=kaikki_db,
                learner_source_json=None,
                top_n=5,
                sample_limit=5,
                generated_at="2026-07-04T00:00:00+00:00",
                include_rows=True,
            )

            self.assertEqual(report["status"], "ok")
            coverage = report["coverage"]
            self.assertEqual(coverage["dictionary_entry_count"], 3)
            self.assertEqual(coverage["dictionary_sense_count"], 3)
            self.assertEqual(coverage["dictionary_topic_count"], 2)
            self.assertEqual(coverage["form_diacritic_count"], 2)
            self.assertEqual(coverage["pos_bucket_counts"]["noun"], 4)

            raw_columns = {row["column"]: row for row in coverage["raw_frequency_columns"]}
            self.assertTrue(raw_columns["spalex_zipf"]["present"])
            self.assertEqual(raw_columns["spalex_zipf"]["non_null_count"], 5)
            self.assertTrue(raw_columns["spalex_prevalence_total"]["present"])

            samples = report["samples"]["rank_order"]
            rows_by_lemma = {row["lemma"]: row for row in samples}
            self.assertEqual(len(report["signal_rows"]), 5)
            self.assertEqual(rows_by_lemma["clínica"]["pos_source_kind"], "pos_overlay")
            self.assertTrue(rows_by_lemma["clínica"]["form"]["has_diacritic"])
            self.assertEqual(rows_by_lemma["salud"]["topics"], ["health", "medicine"])
            self.assertEqual(rows_by_lemma["salud"]["dictionary"]["sense_count"], 1)
            self.assertGreater(rows_by_lemma["salud"]["dictionary"]["region_tag_count"], 0)
            self.assertTrue(rows_by_lemma["salud"]["dictionary"]["register_colloquial_flag"])
            self.assertIn("medicine", rows_by_lemma["salud"]["dictionary"]["domain_terms"])
            self.assertTrue(rows_by_lemma["arcaísmo"]["dictionary"]["marked_usage_flag"])
            self.assertTrue(rows_by_lemma["arcaísmo"]["dictionary"]["register_rare_dated_flag"])

            markdown = render_markdown(report)
            self.assertIn("en-es Learner Difficulty Signal Palette", markdown)
            self.assertIn("SPALEX Zipf", markdown)
            self.assertIn("Dictionary Metadata", markdown)

    def test_missing_frequency_db_marks_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.sqlite"

            report = build_report(
                frequency_db=missing,
                learner_source_json=None,
                top_n=5,
                generated_at="2026-07-04T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "review")
            self.assertIn("frequency_db_missing", report["summary"]["issues"])

    def test_joins_optional_learner_source_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            learner_json = root / "learner_sources.json"
            _write_frequency_db(frequency_db)
            learner_json.write_text(
                "{"
                '"status":"ok",'
                '"source_overlay":{'
                '"salud":{'
                '"term":"salud",'
                '"source_ids":["fixture_beginner"],'
                '"source_count":1,'
                '"learner_core_score":0.12,'
                '"confidence":0.75'
                "},"
                '"clinica":{'
                '"term":"clinica",'
                '"source_ids":["fixture_beginner"],'
                '"source_count":1,'
                '"learner_core_score":0.12,'
                '"confidence":0.75'
                "}"
                "}"
                "}",
                encoding="utf-8",
            )

            report = build_report(
                frequency_db=frequency_db,
                learner_source_json=learner_json,
                top_n=5,
                sample_limit=5,
                generated_at="2026-07-04T00:00:00+00:00",
                include_rows=True,
            )

            coverage = report["coverage"]
            self.assertEqual(coverage["learner_source_count"], 1)
            rows = {row["lemma"]: row for row in report["signal_rows"]}
            self.assertEqual(rows["salud"]["learner_source"]["learner_core_score"], 0.12)
            self.assertFalse(rows["clínica"]["learner_source"])


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE frequency ("
            "id REAL, pmw REAL, freq REAL, lemma TEXT, pos TEXT, source_family TEXT, "
            "source_rank REAL, source_frequency REAL, spalex_rank REAL, spalex_freq REAL, "
            "spalex_zipf REAL, spalex_prevalence_total REAL, spalex_percent_total REAL, "
            "pos_source TEXT, pos_canonical TEXT, topics TEXT, topic_source TEXT)"
        )
        conn.executemany(
            "INSERT INTO frequency ("
            "id, pmw, freq, lemma, pos, source_family, source_rank, source_frequency, "
            "spalex_rank, spalex_freq, spalex_zipf, spalex_prevalence_total, "
            "spalex_percent_total, pos_source, pos_canonical, topics, topic_source"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    1,
                    500.0,
                    500.0,
                    "salud",
                    "n",
                    "spalex",
                    1,
                    500.0,
                    1,
                    500.0,
                    6.1,
                    95.0,
                    0.4,
                    "wiktionary",
                    "noun",
                    "medicine,health",
                    "fixture",
                ),
                (
                    2,
                    400.0,
                    400.0,
                    "clínica",
                    "",
                    "spalex",
                    2,
                    400.0,
                    2,
                    400.0,
                    5.8,
                    88.0,
                    0.3,
                    "",
                    "",
                    "medicine",
                    "fixture",
                ),
                (
                    3,
                    300.0,
                    300.0,
                    "hablar",
                    "v",
                    "spalex",
                    3,
                    300.0,
                    3,
                    300.0,
                    5.5,
                    80.0,
                    0.2,
                    "wiktionary",
                    "verb",
                    "",
                    "",
                ),
                (
                    4,
                    200.0,
                    200.0,
                    "banco",
                    "n",
                    "spalex",
                    4,
                    200.0,
                    4,
                    200.0,
                    5.2,
                    70.0,
                    0.1,
                    "wiktionary",
                    "noun",
                    "finance",
                    "fixture",
                ),
                (
                    5,
                    100.0,
                    100.0,
                    "arcaísmo",
                    "",
                    "spalex",
                    5,
                    100.0,
                    5,
                    100.0,
                    4.0,
                    20.0,
                    0.01,
                    "",
                    "",
                    "",
                    "",
                ),
            ],
        )
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES ('metadata', '{\"pack_id\":\"fixture\"}')"
        )
        conn.commit()
    finally:
        conn.close()


def _write_pos_overlay(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE pos_overlay ("
            "lemma TEXT, raw_pos TEXT, pos_canonical TEXT, pos_bucket TEXT, "
            "pos_source_profile TEXT, pos_matched_rule TEXT, confidence REAL, "
            "source_count INTEGER, total_count INTEGER, source_provider TEXT, overlay_id TEXT)"
        )
        conn.executemany(
            "INSERT INTO pos_overlay ("
            "lemma, raw_pos, pos_canonical, pos_bucket, pos_source_profile, "
            "pos_matched_rule, confidence, source_count, total_count, source_provider, overlay_id"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "clínica",
                    "NOUN",
                    "noun",
                    "noun",
                    "universal-dependencies",
                    "upos:noun",
                    0.95,
                    19,
                    20,
                    "universal-dependencies-ud-ancora",
                    "pos-es-ud-ancora-v1",
                ),
                (
                    "arcaísmo",
                    "NOUN",
                    "noun",
                    "noun",
                    "universal-dependencies",
                    "upos:noun",
                    0.9,
                    9,
                    10,
                    "universal-dependencies-ud-ancora",
                    "pos-es-ud-ancora-v1",
                ),
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
            "entry_ord INTEGER PRIMARY KEY, headword TEXT, headword_lc TEXT, pos TEXT, "
            "pos_title TEXT, categories_json TEXT, forms_json TEXT, sounds_json TEXT, "
            "synonyms_json TEXT, tags_json TEXT, etymology_text TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "entry_ord INTEGER, sense_ord INTEGER, gloss_ord INTEGER, headword TEXT, "
            "headword_lc TEXT, translation TEXT, translation_lc TEXT, pos TEXT, "
            "tags_json TEXT, topics_json TEXT, categories_json TEXT, form_of_json TEXT, "
            "alt_of_json TEXT)"
        )
        conn.executemany(
            "INSERT INTO entry_meta ("
            "entry_ord, headword, headword_lc, pos, pos_title, categories_json, "
            "forms_json, sounds_json, synonyms_json, tags_json, etymology_text"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    1,
                    "salud",
                    "salud",
                    "noun",
                    "Noun",
                    '["Spanish nouns"]',
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "",
                ),
                (
                    2,
                    "clínica",
                    "clínica",
                    "noun",
                    "Noun",
                    '["Medicine"]',
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "",
                ),
                (
                    3,
                    "arcaísmo",
                    "arcaísmo",
                    "noun",
                    "Noun",
                    '["Spanish lemmas"]',
                    "[]",
                    "[]",
                    "[]",
                    '["rare"]',
                    "From Greek.",
                ),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses ("
            "entry_ord, sense_ord, gloss_ord, headword, headword_lc, translation, "
            "translation_lc, pos, tags_json, topics_json, categories_json, form_of_json, "
            "alt_of_json"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    1,
                    0,
                    0,
                    "salud",
                    "salud",
                    "health",
                    "health",
                    "noun",
                    '["Mexico","colloquial"]',
                    '["medicine"]',
                    '["Health","Mexican Spanish","Spanish colloquialisms"]',
                    "[]",
                    "[]",
                ),
                (
                    2,
                    0,
                    0,
                    "clínica",
                    "clínica",
                    "clinic",
                    "clinic",
                    "noun",
                    "[]",
                    '["medicine"]',
                    '["Medicine"]',
                    "[]",
                    "[]",
                ),
                (
                    3,
                    0,
                    0,
                    "arcaísmo",
                    "arcaísmo",
                    "archaism",
                    "archaism",
                    "noun",
                    '["rare"]',
                    "[]",
                    '["Linguistics","Spanish terms with rare senses"]',
                    "[]",
                    "[]",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
