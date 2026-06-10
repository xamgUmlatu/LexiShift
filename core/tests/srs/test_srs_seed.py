from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.seed import (  # noqa: E402
    SeedSelectionConfig,
    build_seed_candidates,
    seed_to_selector_candidates,
)


def _build_freq_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
        [
            ("の", 1, 1000.0),
            ("に", 2, 900.0),
            ("学校", 3, 800.0),
            ("猫", 4, 700.0),
            ("犬", 5, 600.0),
        ],
    )
    conn.commit()
    conn.close()


def _build_freq_db_with_pos(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT)")
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?)",
        [
            ("の", 1, 1000.0, "助詞-格助詞"),
            ("走る", 2, 900.0, "動詞-一般"),
            ("高い", 3, 800.0, "形容詞-一般"),
            ("猫", 4, 700.0, "名詞-普通名詞-一般"),
            ("とても", 5, 600.0, "副詞-一般"),
        ],
    )
    conn.commit()
    conn.close()


def _build_freq_db_with_lform(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE frequency ("
        "lemma TEXT, core_rank REAL, pmw REAL, pos TEXT, lform TEXT, wtype TEXT, sublemma TEXT)"
    )
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw, pos, lform, wtype, sublemma)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("所", 1, 1000.0, "名詞-普通名詞-一般", "トコロ", "NOUN", "所"),
            ("所", 2, 900.0, "名詞-普通名詞-一般", "ショ", "NOUN", "所"),
            ("猫", 3, 800.0, "名詞-普通名詞-一般", "ネコ", "NOUN", "猫"),
        ],
    )
    conn.commit()
    conn.close()


def _build_freq_db_with_spanish_style_columns(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (ID REAL, freq REAL, lemma TEXT, pos TEXT)")
    conn.executemany(
        "INSERT INTO frequency (ID, freq, lemma, pos) VALUES (?, ?, ?, ?)",
        [
            (1, 950.0, "hola", "INTJ"),
            (2, 875.0, "gato", "NOUN"),
            (3, 765.0, "rápido", "ADJ"),
        ],
    )
    conn.commit()
    conn.close()


def _build_spalex_style_freq_db_without_pos_values(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (id REAL, freq REAL, lemma TEXT, pos TEXT)")
    conn.executemany(
        "INSERT INTO frequency (id, freq, lemma, pos) VALUES (?, ?, ?, ?)",
        [
            (1, 1000.0, "gato", ""),
            (2, 900.0, "correr", None),
            (3, 800.0, "rápido", ""),
        ],
    )
    conn.commit()
    conn.close()


def _build_freq_db_with_compact_spanish_tags(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (ID REAL, freq REAL, lemma TEXT, pos TEXT)")
    conn.executemany(
        "INSERT INTO frequency (ID, freq, lemma, pos) VALUES (?, ?, ?, ?)",
        [
            (1, 1000.0, "gato", "n"),
            (2, 900.0, "bonito", "j"),
            (3, 800.0, "correr", "v"),
            (4, 700.0, "rapidamente", "r"),
            (5, 600.0, "hola", "i"),
        ],
    )
    conn.commit()
    conn.close()


def _build_ud_pos_overlay(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE pos_overlay (
          lemma TEXT PRIMARY KEY,
          raw_pos TEXT,
          pos_canonical TEXT,
          pos_bucket TEXT,
          pos_source_profile TEXT,
          pos_matched_rule TEXT,
          confidence REAL,
          source_count INTEGER,
          total_count INTEGER,
          source_provider TEXT,
          overlay_id TEXT
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO pos_overlay (
          lemma, raw_pos, pos_canonical, pos_bucket, pos_source_profile,
          pos_matched_rule, confidence, source_count, total_count,
          source_provider, overlay_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "gato",
                "NOUN",
                "noun",
                "noun",
                "universal-dependencies",
                "ud_upos:NOUN",
                1.0,
                4,
                4,
                "universal-dependencies-ud-ancora",
                "pos-es-ud-ancora-v1",
            ),
            (
                "correr",
                "VERB",
                "verb",
                "verb",
                "universal-dependencies",
                "ud_upos:VERB",
                0.75,
                3,
                4,
                "universal-dependencies-ud-ancora",
                "pos-es-ud-ancora-v1",
            ),
            (
                "rápido",
                "ADJ",
                "adjective",
                "adjective",
                "universal-dependencies",
                "ud_upos:ADJ",
                1.0,
                2,
                2,
                "universal-dependencies-ud-ancora",
                "pos-es-ud-ancora-v1",
            ),
        ],
    )
    conn.commit()
    conn.close()


def _build_freq_db_with_pmw_and_freq(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, freq REAL, pos TEXT)"
    )
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw, freq, pos) VALUES (?, ?, ?, ?, ?)",
        [
            ("alpha", 1.0, 900.0, 10.0, "NOUN"),
            ("beta", 2.0, 450.0, 20.0, "NOUN"),
        ],
    )
    conn.commit()
    conn.close()


class TestSrsSeedStopwords(unittest.TestCase):
    def test_stopwords_json_list_filters_lemmas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db(db_path)
            stopwords_path = root / "stopwords-ja.json"
            stopwords_path.write_text(
                json.dumps(["の", "に"], ensure_ascii=False),
                encoding="utf-8",
            )

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=10,
                    require_jmdict=False,
                    stopwords_path=stopwords_path,
                ),
            )

            lemmas = [item.lemma for item in selected]
            self.assertEqual(lemmas, ["学校", "猫", "犬"])

    def test_invalid_stopwords_object_format_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db(db_path)
            stopwords_path = root / "stopwords-ja.json"
            stopwords_path.write_text(
                json.dumps({"words": ["の", "に"]}, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                build_seed_candidates(
                    frequency_db=db_path,
                    config=SeedSelectionConfig(
                        language_pair="en-ja",
                        top_n=10,
                        require_jmdict=False,
                        stopwords_path=stopwords_path,
                    ),
                )

    def test_pos_weighting_prioritizes_nouns_then_adjectives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db_with_pos(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=10,
                    require_jmdict=False,
                ),
            )

            lemmas = [item.lemma for item in selected]
            self.assertEqual(lemmas[:3], ["猫", "高い", "走る"])
            self.assertEqual(selected[0].pos_bucket, "noun")
            self.assertGreater(selected[0].admission_weight, selected[1].admission_weight)
            self.assertGreater(selected[1].admission_weight, selected[2].admission_weight)

    def test_seed_metadata_source_defaults_to_frequency_db_stem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq-de-default.sqlite"
            _build_freq_db(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-de",
                    top_n=2,
                    require_jmdict=False,
                ),
            )

            self.assertTrue(selected)
            self.assertEqual(selected[0].metadata["source"], "freq-de-default")

    def test_seed_metadata_source_can_be_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-de",
                    top_n=2,
                    require_jmdict=False,
                    source_label="leipzig_2023_1m",
                ),
            )

            self.assertTrue(selected)
            self.assertEqual(selected[0].metadata["source"], "leipzig_2023_1m")

    def test_seed_word_package_uses_frequency_reading_and_selector_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db_with_lform(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=2,
                    require_jmdict=False,
                ),
            )

            self.assertEqual([item.lemma for item in selected], ["所", "所"])
            first_package = selected[0].word_package
            self.assertIsNotNone(first_package)
            self.assertEqual(first_package["surface"], "所")
            self.assertEqual(first_package["reading"], "ところ")
            self.assertEqual(first_package["script_forms"]["kana"], "ところ")
            self.assertEqual(first_package["script_forms"]["romaji"], "tokoro")

            selector_candidates = seed_to_selector_candidates(selected)
            self.assertIn("word_package", selector_candidates[0].metadata)
            selector_package = selector_candidates[0].metadata["word_package"]
            self.assertEqual(selector_package["reading"], "ところ")

    def test_seed_falls_back_to_spanish_style_rank_and_frequency_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq-es.sqlite"
            _build_freq_db_with_spanish_style_columns(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-es",
                    top_n=3,
                    require_jmdict=False,
                    sort_by_admission_weight=False,
                ),
            )

            lemmas = [item.lemma for item in selected]
            self.assertEqual(lemmas, ["hola", "gato", "rápido"])
            self.assertEqual(str(selected[0].metadata["rank_column"]).lower(), "id")
            self.assertEqual(str(selected[0].metadata["pmw_column"]).lower(), "freq")
            self.assertAlmostEqual(float(selected[0].pmw or 0.0), 950.0)

    def test_seed_uses_canonical_pos_for_compact_spanish_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq-es.sqlite"
            _build_freq_db_with_compact_spanish_tags(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-es",
                    top_n=5,
                    require_jmdict=False,
                ),
            )

            by_lemma = {item.lemma: item for item in selected}
            self.assertEqual(by_lemma["gato"].pos_bucket, "noun")
            self.assertEqual(by_lemma["bonito"].pos_bucket, "adjective")
            self.assertEqual(by_lemma["correr"].pos_bucket, "verb")
            self.assertEqual(by_lemma["rapidamente"].pos_bucket, "adverb")
            self.assertEqual(by_lemma["hola"].pos_bucket, "other")

            gato = by_lemma["gato"]
            self.assertEqual(gato.pos_raw, "n")
            self.assertEqual(gato.pos_canonical, "noun")
            self.assertTrue(gato.pos_mapped)
            self.assertEqual(gato.metadata["pos_raw"], "n")
            self.assertEqual(gato.metadata["pos_canonical"], "noun")

            package = gato.word_package
            self.assertIsNotNone(package)
            self.assertEqual(package.get("pos"), "n")
            self.assertEqual(package.get("pos_raw"), "n")
            self.assertEqual(package.get("pos_canonical"), "noun")

            selector_candidates = seed_to_selector_candidates(selected)
            selector_by_lemma = {item.lemma: item for item in selector_candidates}
            self.assertEqual(selector_by_lemma["gato"].pos, "noun")
            self.assertEqual(selector_by_lemma["gato"].metadata["pos_raw"], "n")
            self.assertEqual(selector_by_lemma["gato"].metadata["pos_canonical"], "noun")

    def test_seed_uses_pos_overlay_when_frequency_pos_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq-es-spalex-v1.sqlite"
            overlay_path = root / "pos-es-ud-ancora-v1.sqlite"
            _build_spalex_style_freq_db_without_pos_values(db_path)
            _build_ud_pos_overlay(overlay_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-es",
                    top_n=3,
                    require_jmdict=False,
                    pos_overlay_path=overlay_path,
                ),
            )

            by_lemma = {item.lemma: item for item in selected}
            self.assertEqual(by_lemma["gato"].pos_raw, "NOUN")
            self.assertEqual(by_lemma["gato"].pos_canonical, "noun")
            self.assertEqual(by_lemma["gato"].pos_bucket, "noun")
            self.assertEqual(by_lemma["gato"].metadata["pos_source_kind"], "pos_overlay")
            self.assertEqual(
                by_lemma["gato"].metadata["pos_source_profile"],
                "universal-dependencies",
            )
            self.assertEqual(by_lemma["gato"].metadata["frequency_pos_raw"], "")
            self.assertEqual(
                by_lemma["gato"].metadata["pos_overlay_id"],
                "pos-es-ud-ancora-v1",
            )
            self.assertAlmostEqual(
                float(by_lemma["correr"].metadata["pos_overlay_confidence"]),
                0.75,
            )

    def test_seed_keeps_frequency_pos_over_pos_overlay_when_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq-es-cde.sqlite"
            overlay_path = root / "pos-es-ud-ancora-v1.sqlite"
            _build_freq_db_with_compact_spanish_tags(db_path)
            _build_ud_pos_overlay(overlay_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-es",
                    top_n=5,
                    require_jmdict=False,
                    pos_overlay_path=overlay_path,
                ),
            )

            by_lemma = {item.lemma: item for item in selected}
            self.assertEqual(by_lemma["gato"].pos_raw, "n")
            self.assertEqual(by_lemma["gato"].metadata["pos_source_kind"], "frequency")
            self.assertNotIn("pos_overlay_id", by_lemma["gato"].metadata)

    def test_seed_prefers_pmw_when_pmw_and_freq_are_both_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db_with_pmw_and_freq(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=2,
                    require_jmdict=False,
                    sort_by_admission_weight=False,
                ),
            )

            self.assertTrue(selected)
            self.assertEqual(str(selected[0].metadata["pmw_column"]).lower(), "pmw")
            self.assertAlmostEqual(float(selected[0].pmw or 0.0), 900.0)


if __name__ == "__main__":
    unittest.main()
