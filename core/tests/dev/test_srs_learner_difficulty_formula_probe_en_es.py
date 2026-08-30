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

from srs_learner_difficulty_formula_probe_en_es import build_report  # noqa: E402


class SrsLearnerDifficultyFormulaProbeEnEsTests(unittest.TestCase):
    def test_builds_source_backed_components_and_variant_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            pos_overlay = root / "pos.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            english_db = root / "english.sqlite"
            _write_frequency_db(frequency_db)
            _write_pos_overlay(pos_overlay)
            _write_kaikki_db(kaikki_db)
            _write_english_db(english_db)

            report = build_report(
                frequency_db=frequency_db,
                pos_overlay_path=pos_overlay,
                kaikki_forward_db=kaikki_db,
                english_frequency_db=english_db,
                learner_source_json=None,
                lexcomspal2_tsv=None,
                wordfreq_enabled=False,
                top_n=6,
                sample_limit=3,
                generated_at="2026-07-05T00:00:00+00:00",
                include_rows=True,
            )

            self.assertEqual(report["status"], "ok")
            rows = {str(row["lemma"]): row for row in report["rows"]}

            self.assertEqual(rows["que"]["components"]["pos_function_risk"], 1.0)
            self.assertGreater(rows["arcaísmo"]["components"]["gated_dict_marked_usage_risk"], 0.0)
            self.assertGreater(rows["arcaísmo"]["components"]["tail_rare_dated_register"], 0.0)
            self.assertGreater(rows["hospital"]["components"]["cognate_rescue"], 0.40)
            self.assertLess(rows["empresa"]["components"]["cognate_rescue"], 0.05)

            que_scores = rows["que"]["variant_scores"]
            hospital_scores = rows["hospital"]["variant_scores"]
            self.assertGreater(
                que_scores["transfer_all_light"],
                que_scores["spalex_blend_frequency"],
            )
            self.assertLess(
                hospital_scores["transfer_all_light"],
                hospital_scores["spalex_blend_frequency"],
            )

            transfer = next(
                row for row in report["variants"] if row["variant_id"] == "transfer_all_light"
            )
            self.assertIn("raised_count", transfer["summary"])
            self.assertTrue(transfer["band_samples"])

    def test_cognate_rescue_requires_pos_compatible_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            pos_overlay = root / "pos.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            english_db = root / "english.sqlite"
            _write_frequency_db(frequency_db)
            _write_pos_overlay(pos_overlay)
            _write_kaikki_db(kaikki_db)
            _write_english_db(english_db)

            report = build_report(
                frequency_db=frequency_db,
                pos_overlay_path=pos_overlay,
                kaikki_forward_db=kaikki_db,
                english_frequency_db=english_db,
                learner_source_json=None,
                lexcomspal2_tsv=None,
                wordfreq_enabled=False,
                top_n=6,
                sample_limit=3,
                generated_at="2026-07-05T00:00:00+00:00",
                include_rows=True,
            )

            rows = {str(row["lemma"]): row for row in report["rows"]}
            self.assertEqual(rows["son"]["pos"], "verb")
            self.assertEqual(rows["son"]["components"]["cognate_rescue"], 0.0)

    def test_learner_source_overlay_can_bound_lower_known_core_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            pos_overlay = root / "pos.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            english_db = root / "english.sqlite"
            learner_json = root / "learner_sources.json"
            _write_frequency_db(frequency_db)
            _write_pos_overlay(pos_overlay)
            _write_kaikki_db(kaikki_db)
            _write_english_db(english_db)
            learner_json.write_text(
                "{"
                '"status":"ok",'
                '"source_summary":{"sources":['
                '{"source_id":"openlingo_mit_spanish_dictionary","decision":"included_sidecar"}'
                "]},"
                '"source_overlay":{'
                '"hospital":{'
                '"term":"hospital",'
                '"source_ids":["openlingo_mit_spanish_dictionary"],'
                '"source_count":1,'
                '"learner_core_score":0.12,'
                '"confidence":0.80'
                "}"
                "}"
                "}",
                encoding="utf-8",
            )

            report = build_report(
                frequency_db=frequency_db,
                pos_overlay_path=pos_overlay,
                kaikki_forward_db=kaikki_db,
                english_frequency_db=english_db,
                learner_source_json=learner_json,
                lexcomspal2_tsv=None,
                wordfreq_enabled=False,
                top_n=6,
                sample_limit=3,
                generated_at="2026-07-05T00:00:00+00:00",
                include_rows=True,
            )

            rows = {str(row["lemma"]): row for row in report["rows"]}
            hospital = rows["hospital"]
            empresa = rows["empresa"]
            self.assertGreater(
                hospital["components"]["learner_core_gap_zipf_confident"],
                0.0,
            )
            self.assertGreater(
                hospital["components"]["learner_core_gap_zipf_quality"],
                0.0,
            )
            self.assertGreater(
                hospital["components"]["learner_independent_vocab_support"],
                0.0,
            )
            self.assertEqual(hospital["components"]["learner_broad_source_known"], 1.0)
            self.assertEqual(hospital["components"]["unsupported_ease65"], 0.0)
            self.assertEqual(empresa["components"]["learner_broad_source_absent"], 1.0)
            self.assertGreater(empresa["components"]["unsupported_ease_content"], 0.0)
            self.assertGreater(
                empresa["variant_scores"]["unsupported_ease_probe"],
                empresa["variant_scores"]["spalex_blend_frequency"],
            )
            self.assertLess(
                hospital["variant_scores"]["learner_source_zipf_light"],
                hospital["variant_scores"]["zipf_frequency_only"],
            )

    def test_wordfreq_overlay_materializes_multisource_rescue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            pos_overlay = root / "pos.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            english_db = root / "english.sqlite"
            _write_frequency_db(frequency_db)
            _write_pos_overlay(pos_overlay)
            _write_kaikki_db(kaikki_db)
            _write_english_db(english_db)

            report = build_report(
                frequency_db=frequency_db,
                pos_overlay_path=pos_overlay,
                kaikki_forward_db=kaikki_db,
                english_frequency_db=english_db,
                learner_source_json=None,
                lexcomspal2_tsv=None,
                wordfreq_zipf_by_lemma={"arcaísmo": 3.5},
                top_n=6,
                sample_limit=3,
                generated_at="2026-07-05T00:00:00+00:00",
                include_rows=True,
            )

            rows = {str(row["lemma"]): row for row in report["rows"]}
            arcaismo = rows["arcaísmo"]
            self.assertEqual(arcaismo["components"]["wordfreq_known"], 1.0)
            self.assertGreater(arcaismo["components"]["wordfreq_source_rescue"], 0.0)
            self.assertGreater(arcaismo["components"]["wordfreq_tail_rescue"], 0.0)
            self.assertLess(
                arcaismo["variant_scores"]["wordfreq_rescue_probe"],
                arcaismo["variant_scores"]["spalex_blend_frequency"],
            )
            self.assertEqual(report["wordfreq_signal"]["rows_with_zipf"], 1)

    def test_lexcom_overlay_materializes_learner_complexity_rescue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            pos_overlay = root / "pos.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            english_db = root / "english.sqlite"
            lexcom_tsv = root / "lexcom.tsv"
            _write_frequency_db(frequency_db)
            _write_pos_overlay(pos_overlay)
            _write_kaikki_db(kaikki_db)
            _write_english_db(english_db)
            lexcom_tsv.write_text(
                "id\tcorpus\tsentence\ttoken\tcomplexity\tannotations\n"
                "1\thealth\tfixture\tarcaísmo\t"
                "{'PL1': 0.20, 'PL2': 0.10, 'PL3': 0.05, 'overall': 0.12}\t{}\n",
                encoding="utf-8",
            )

            report = build_report(
                frequency_db=frequency_db,
                pos_overlay_path=pos_overlay,
                kaikki_forward_db=kaikki_db,
                english_frequency_db=english_db,
                learner_source_json=None,
                lexcomspal2_tsv=lexcom_tsv,
                wordfreq_enabled=False,
                top_n=6,
                sample_limit=3,
                generated_at="2026-07-05T00:00:00+00:00",
                include_rows=True,
            )

            rows = {str(row["lemma"]): row for row in report["rows"]}
            arcaismo = rows["arcaísmo"]
            self.assertEqual(arcaismo["components"]["lexcom_known"], 1.0)
            self.assertEqual(arcaismo["components"]["lexcom_complexity"], 0.12)
            self.assertGreater(arcaismo["components"]["lexcom_learner_rescue"], 0.0)
            self.assertLess(
                arcaismo["variant_scores"]["lexcom_complexity_probe"],
                arcaismo["variant_scores"]["spalex_blend_frequency"],
            )
            self.assertEqual(report["lexcom_signal"]["source_token_count"], 1)


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
        rows = [
            (
                1,
                600.0,
                600.0,
                "que",
                "",
                "spalex",
                1,
                600.0,
                1,
                600.0,
                6.5,
                2.2,
                99.0,
                "",
                "",
                "",
                "",
            ),
            (
                2,
                500.0,
                500.0,
                "hospital",
                "",
                "spalex",
                2,
                500.0,
                2,
                500.0,
                6.0,
                2.0,
                98.0,
                "",
                "",
                "",
                "",
            ),
            (
                3,
                400.0,
                400.0,
                "empresa",
                "",
                "spalex",
                3,
                400.0,
                3,
                400.0,
                5.8,
                1.9,
                97.0,
                "",
                "",
                "",
                "",
            ),
            (
                4,
                300.0,
                300.0,
                "son",
                "",
                "spalex",
                4,
                300.0,
                4,
                300.0,
                5.5,
                1.7,
                95.0,
                "",
                "",
                "",
                "",
            ),
            (
                5,
                200.0,
                200.0,
                "rápidamente",
                "",
                "spalex",
                5,
                200.0,
                5,
                200.0,
                5.0,
                1.2,
                90.0,
                "",
                "",
                "",
                "",
            ),
            (
                6,
                100.0,
                100.0,
                "arcaísmo",
                "",
                "spalex",
                6,
                100.0,
                6,
                100.0,
                4.0,
                0.2,
                60.0,
                "",
                "",
                "",
                "",
            ),
        ]
        conn.executemany(
            "INSERT INTO frequency ("
            "id, pmw, freq, lemma, pos, source_family, source_rank, source_frequency, "
            "spalex_rank, spalex_freq, spalex_zipf, spalex_prevalence_total, "
            "spalex_percent_total, pos_source, pos_canonical, topics, topic_source"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
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
        rows = [
            (
                "que",
                "PRON",
                "pronoun",
                "other",
                "fixture",
                "upos:pron",
                1.0,
                1,
                1,
                "fixture",
                "fixture-pos",
            ),
            (
                "hospital",
                "NOUN",
                "noun",
                "noun",
                "fixture",
                "upos:noun",
                1.0,
                1,
                1,
                "fixture",
                "fixture-pos",
            ),
            (
                "empresa",
                "NOUN",
                "noun",
                "noun",
                "fixture",
                "upos:noun",
                1.0,
                1,
                1,
                "fixture",
                "fixture-pos",
            ),
            (
                "son",
                "VERB",
                "verb",
                "verb",
                "fixture",
                "upos:verb",
                1.0,
                1,
                1,
                "fixture",
                "fixture-pos",
            ),
            (
                "rápidamente",
                "ADV",
                "adverb",
                "adverb",
                "fixture",
                "upos:adv",
                1.0,
                1,
                1,
                "fixture",
                "fixture-pos",
            ),
            (
                "arcaísmo",
                "NOUN",
                "noun",
                "noun",
                "fixture",
                "upos:noun",
                1.0,
                1,
                1,
                "fixture",
                "fixture-pos",
            ),
        ]
        conn.executemany(
            "INSERT INTO pos_overlay ("
            "lemma, raw_pos, pos_canonical, pos_bucket, pos_source_profile, "
            "pos_matched_rule, confidence, source_count, total_count, source_provider, overlay_id"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
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
                (1, "que", "que", "pron", "Pronoun", "[]", "[]", "[]", "[]", "[]", ""),
                (2, "hospital", "hospital", "noun", "Noun", "[]", "[]", "[]", "[]", "[]", ""),
                (3, "empresa", "empresa", "noun", "Noun", "[]", "[]", "[]", "[]", "[]", ""),
                (4, "son", "son", "verb", "Verb", "[]", "[]", "[]", "[]", "[]", ""),
                (
                    5,
                    "rápidamente",
                    "rápidamente",
                    "adv",
                    "Adverb",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "",
                ),
                (6, "arcaísmo", "arcaísmo", "noun", "Noun", "[]", "[]", "[]", "[]", '["rare"]', ""),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses ("
            "entry_ord, sense_ord, gloss_ord, headword, headword_lc, translation, "
            "translation_lc, pos, tags_json, topics_json, categories_json, form_of_json, "
            "alt_of_json"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 0, 0, "que", "que", "that", "that", "pron", "[]", "[]", "[]", "[]", "[]"),
                (
                    2,
                    0,
                    0,
                    "hospital",
                    "hospital",
                    "hospital",
                    "hospital",
                    "noun",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                ),
                (
                    3,
                    0,
                    0,
                    "empresa",
                    "empresa",
                    "company",
                    "company",
                    "noun",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                ),
                (4, 0, 0, "son", "son", "son", "son", "noun", "[]", "[]", "[]", "[]", "[]"),
                (4, 1, 0, "son", "son", "are", "are", "verb", "[]", "[]", "[]", "[]", "[]"),
                (
                    5,
                    0,
                    0,
                    "rápidamente",
                    "rápidamente",
                    "quickly",
                    "quickly",
                    "adv",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                ),
                (
                    6,
                    0,
                    0,
                    "arcaísmo",
                    "arcaísmo",
                    "archaism",
                    "archaism",
                    "noun",
                    '["rare"]',
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_english_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?)",
            [
                ("hospital", 10.0, 1000.0, None),
                ("company", 20.0, 800.0, None),
                ("son", 30.0, 700.0, None),
                ("are", 5.0, 1200.0, None),
                ("archaism", 5000.0, 1.0, None),
                ("quickly", 1000.0, 10.0, None),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
