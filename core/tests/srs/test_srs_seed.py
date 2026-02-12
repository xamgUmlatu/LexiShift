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


if __name__ == "__main__":
    unittest.main()
