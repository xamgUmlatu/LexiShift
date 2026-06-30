from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.seed import (  # noqa: E402
    SeedSelectionConfig,
    build_seed_candidates,
    cleanup_seed_frontier_cache,
    prepare_seed_frontier_cache,
    seed_to_selector_candidates,
    seed_frontier_cache_status,
)
from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV,
    clear_corrected_learner_difficulty_cache,
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


def _build_freq_db_with_surface_policy_rows(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE frequency ("
        "lemma TEXT, core_rank REAL, pmw REAL, pos TEXT, lform TEXT, wtype TEXT, sublemma TEXT)"
    )
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw, pos, lform, wtype, sublemma)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("明い", 1, 1000.0, "形容詞-一般", "アカイ", "ADJ", "明い"),
            ("音", 2, 900.0, "名詞-普通名詞-一般", "オン", "NOUN", "音"),
            ("何処", 3, 800.0, "名詞-普通名詞-一般", "ドコ", "NOUN", "何処"),
            ("何処", 4, 700.0, "名詞-普通名詞-一般", "イズコ", "NOUN", "何処"),
            ("此れ", 5, 600.0, "代名詞", "コレ", "PRON", "此れ"),
            ("為", 6, 500.0, "名詞-普通名詞-副詞可能", "タメ", "NOUN", "為"),
        ],
    )
    conn.commit()
    conn.close()


def _build_acronym_freq_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE frequency ("
        "lemma TEXT, core_rank REAL, pmw REAL, pos TEXT, lform TEXT, wtype TEXT)"
    )
    conn.execute(
        "INSERT INTO frequency (lemma, core_rank, pmw, pos, lform, wtype)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            "ＰＤＦ",
            1,
            1000.0,
            "名詞-普通名詞-一般",
            "ピーディーエフ",
            "記号",
        ),
    )
    conn.commit()
    conn.close()


def _build_freq_db_with_bccwj_profile_columns(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE frequency ("
        "lemma TEXT, core_rank REAL, pmw REAL, "
        "pb_rank REAL, pb_pmw REAL, ow_rank REAL, ow_pmw REAL, "
        "pb_fixed_rank REAL, pb_variable_rank REAL)"
    )
    conn.executemany(
        "INSERT INTO frequency ("
        "lemma, core_rank, pmw, pb_rank, pb_pmw, ow_rank, ow_pmw, "
        "pb_fixed_rank, pb_variable_rank"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("猫", 1, 1000.0, 3, 300.0, 30, 30.0, 4, 24),
            ("犬", 2, 900.0, None, None, 20, 40.0, None, None),
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
    def test_missing_top_n_reads_full_seed_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=None,
                    require_jmdict=False,
                ),
            )

            lemmas = [item.lemma for item in selected]
            self.assertEqual(lemmas, ["の", "に", "学校", "猫", "犬"])

    def test_en_ja_seed_metadata_includes_optional_learner_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db_with_lform(db_path)
            jmdict_path = root / "JMdict_e"
            jmdict_path.write_text(
                (
                    "<JMdict>"
                    "<entry>"
                    "<k_ele><keb>猫</keb><ke_pri>ichi1</ke_pri><ke_pri>nf08</ke_pri></k_ele>"
                    "<r_ele><reb>ねこ</reb></r_ele>"
                    "<sense><gloss xml:lang='eng'>cat</gloss></sense>"
                    "</entry>"
                    "</JMdict>"
                ),
                encoding="utf-8",
            )
            kanjidic2_path = root / "kanjidic2.xml"
            kanjidic2_path.write_text(
                (
                    "<kanjidic2>"
                    "<character><literal>猫</literal>"
                    "<misc><grade>8</grade><stroke_count>11</stroke_count>"
                    "<freq>1702</freq><jlpt>2</jlpt></misc>"
                    "</character>"
                    "</kanjidic2>"
                ),
                encoding="utf-8",
            )
            jmnedict_path = root / "JMnedict.xml"
            jmnedict_path.write_text(
                (
                    "<JMnedict>"
                    "<entry><ent_seq>1</ent_seq>"
                    "<k_ele><keb>猫</keb></k_ele>"
                    "<r_ele><reb>ねこ</reb></r_ele>"
                    "<trans><name_type>character</name_type>"
                    "<trans_det>Neko</trans_det></trans>"
                    "</entry>"
                    "</JMnedict>"
                ),
                encoding="utf-8",
            )
            kanjivg_path = root / "kanjivg.xml"
            kanjivg_path.write_text(
                (
                    "<kanjivg xmlns:kvg='http://kanjivg.tagaini.net'>"
                    "<kanji id='kvg:kanji_732b'>"
                    "<g id='kvg:732b' kvg:element='猫'>"
                    "<g id='kvg:732b-g1' kvg:element='犭'>"
                    "<path id='kvg:732b-s1' d='M1 1'/>"
                    "</g>"
                    "<g id='kvg:732b-g2' kvg:element='苗'>"
                    "<path id='kvg:732b-s2' d='M2 2'/>"
                    "</g>"
                    "</g>"
                    "</kanji>"
                    "</kanjivg>"
                ),
                encoding="utf-8",
            )
            jlpt_vocabulary_path = root / "JLPT_vocab_ALL.csv"
            jlpt_vocabulary_path.write_text(
                "Kanji,Reading,Level\n猫,ねこ,5\n",
                encoding="utf-8",
            )
            lesson_vocabulary_path = root / "sbsjapanese1-ja" / "EPUB"
            lesson_vocabulary_path.mkdir(parents=True)
            (lesson_vocabulary_path / "chapter-001-slug.xhtml").write_text(
                (
                    "<html><body><h2>Vocabulary</h2><table>"
                    "<tr><th>Audio</th><th>Hiragana</th><th>Romanization</th>"
                    "<th>Kanji</th><th>English translation</th></tr>"
                    "<tr><td></td><td>ねこ</td><td>neko</td><td>猫</td><td>cat</td></tr>"
                    "</table></body></html>"
                ),
                encoding="utf-8",
            )

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=None,
                    require_jmdict=True,
                    jmdict_path=jmdict_path,
                    jmnedict_path=jmnedict_path,
                    kanjidic2_path=kanjidic2_path,
                    kanjivg_path=kanjivg_path,
                    jlpt_vocabulary_path=jlpt_vocabulary_path,
                    lesson_vocabulary_path=lesson_vocabulary_path,
                ),
            )

            self.assertEqual([item.lemma for item in selected], ["猫"])
            self.assertEqual(selected[0].word_package["lform_raw"], "ネコ")
            self.assertEqual(selected[0].word_package["reading"], "ねこ")
            signals = selected[0].metadata["learner_signals"]
            self.assertEqual(
                signals["sources"],
                [
                    "japanese_script",
                    "jmdict_priority",
                    "jmdict_lexical",
                    "jlpt_vocabulary",
                    "lesson_vocabulary",
                    "jmnedict_name",
                    "kanjidic2",
                    "kanjivg",
                ],
            )
            self.assertEqual(signals["jmdict_priority"]["priority_band"], "primary")
            self.assertEqual(
                signals["jmdict_priority"]["matched_pair"]["match_type"],
                "exact",
            )
            self.assertEqual(
                signals["jmdict_priority"]["matched_pair"]["safe_priority_score"],
                1.0,
            )
            self.assertEqual(signals["jmdict_lexical"]["sense_count"], 1)
            self.assertEqual(
                signals["jmnedict_name"]["name_type_groups"],
                ["creative_work_or_character_name"],
            )
            self.assertEqual(signals["kanjidic2"]["grade_max"], 8)
            self.assertEqual(signals["kanjivg"]["component_count_max"], 2)
            self.assertEqual(signals["kanjivg"]["path_count_max"], 2)
            self.assertEqual(signals["jlpt_vocabulary"]["easiest_level"], 5)
            self.assertEqual(signals["lesson_vocabulary"]["earliest_lesson"], 1)
            self.assertEqual(signals["lesson_vocabulary"]["romanizations"], ["neko"])
            self.assertEqual(signals["lesson_vocabulary"]["glosses"], ["cat"])

    def test_en_ja_seed_applies_exact_display_form_surface_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            corrected_path = root / "corrected.csv"
            _build_freq_db_with_surface_policy_rows(db_path)
            corrected_path.write_text(
                (
                    "rank,lemma,reading,score,band,correction_types,display_form,"
                    "admission_override\n"
                    "1,明い,あかい,0.22,0.20-0.25,display_only,あかい,normal_vocab\n"
                    '2,音,おん,0.35,0.35-0.40,"score_floor,restricted_admission",'
                    "おん,compound_or_on_reading\n"
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: str(corrected_path)},
            ):
                clear_corrected_learner_difficulty_cache()
                selected = build_seed_candidates(
                    frequency_db=db_path,
                    config=SeedSelectionConfig(
                        language_pair="en-ja",
                        top_n=None,
                        require_jmdict=False,
                        sort_by_admission_weight=False,
                    ),
                )
                clear_corrected_learner_difficulty_cache()

        lemmas = [item.lemma for item in selected]
        self.assertEqual(lemmas, ["あかい", "音", "どこ", "何処", "これ", "ため"])

        by_lemma = {item.lemma: item for item in selected}
        self.assertEqual(by_lemma["あかい"].metadata["source_surface_original"], "明い")
        self.assertEqual(by_lemma["あかい"].word_package["script_forms"]["kanji"], "明い")
        self.assertEqual(by_lemma["あかい"].word_package["script_forms"]["kana"], "あかい")
        self.assertEqual(by_lemma["あかい"].word_package["reading"], "あかい")
        self.assertEqual(by_lemma["音"].word_package["reading"], "おん")
        self.assertNotIn("おん", lemmas)

    def test_en_ja_seed_classification_applies_acronym_learner_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_acronym_freq_db(db_path)
            jmdict_path = root / "JMdict_e"
            jmdict_path.write_text(
                (
                    "<JMdict>"
                    "<entry>"
                    "<k_ele><keb>ＰＤＦ</keb></k_ele>"
                    "<r_ele><reb>ピーディーエフ</reb></r_ele>"
                    "<sense><gloss xml:lang='eng'>PDF</gloss></sense>"
                    "</entry>"
                    "</JMdict>"
                ),
                encoding="utf-8",
            )

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=None,
                    require_jmdict=True,
                    jmdict_path=jmdict_path,
                ),
            )

            self.assertEqual([item.lemma for item in selected], ["ＰＤＦ"])
            self.assertEqual(selected[0].candidate_state, "suppressed_default")
            self.assertEqual(selected[0].presentation_mode, "suppress")
            self.assertEqual(selected[0].problem_class, "acronym_or_code")
            self.assertAlmostEqual(selected[0].admission_suitability, 0.0, places=6)
            self.assertEqual(
                selected[0].metadata["learner_signals"]["ja_acronym"][
                    "recommended_candidate_state"
                ],
                "suppressed_default",
            )
            self.assertEqual(
                selected[0].metadata["candidate_state"],
                "suppressed_default",
            )

    def test_en_ja_seed_classification_can_disable_acronym_learner_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_acronym_freq_db(db_path)
            jmdict_path = root / "JMdict_e"
            jmdict_path.write_text(
                (
                    "<JMdict>"
                    "<entry>"
                    "<k_ele><keb>ＰＤＦ</keb></k_ele>"
                    "<r_ele><reb>ピーディーエフ</reb></r_ele>"
                    "<sense><gloss xml:lang='eng'>PDF</gloss></sense>"
                    "</entry>"
                    "</JMdict>"
                ),
                encoding="utf-8",
            )

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=None,
                    require_jmdict=True,
                    jmdict_path=jmdict_path,
                    apply_learner_signal_classification=False,
                ),
            )

            self.assertEqual(selected[0].candidate_state, "normal_vocab")
            self.assertEqual(selected[0].presentation_mode, "vocab")
            self.assertEqual(selected[0].problem_class, "normal_vocab")

    def test_seed_metadata_includes_compact_source_frequency_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            _build_freq_db_with_bccwj_profile_columns(db_path)

            selected = build_seed_candidates(
                frequency_db=db_path,
                config=SeedSelectionConfig(
                    language_pair="en-ja",
                    top_n=1,
                    require_jmdict=False,
                    sort_by_admission_weight=False,
                ),
            )

            self.assertEqual([item.lemma for item in selected], ["猫"])
            profile = selected[0].metadata["source_frequency_profile"]
            self.assertEqual(profile["known_column_count"], 8)
            self.assertEqual(profile["domain_rank_known_count"], 4)
            self.assertEqual(profile["domain_rank_min"], 3)
            self.assertEqual(profile["domain_rank_max"], 30)
            self.assertEqual(profile["fixed_rank_mean"], 4)
            self.assertEqual(profile["variable_rank_mean"], 24)
            self.assertEqual(profile["fixed_variable_rank_delta"], 20)

    def test_seed_frontier_cache_hit_skips_frequency_db_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            cache_dir = root / "cache"
            _build_freq_db_with_lform(db_path)
            config = SeedSelectionConfig(
                language_pair="en-ja",
                top_n=3,
                require_jmdict=False,
                cache_dir=cache_dir,
            )

            first = build_seed_candidates(frequency_db=db_path, config=config)
            cache_files = list(cache_dir.rglob("*.jsonl"))
            self.assertEqual(len(cache_files), 1)

            with patch(
                "lexishift_core.srs.seed.SqliteFrequencyStore",
                side_effect=AssertionError("cache miss attempted to reopen frequency DB"),
            ):
                second = build_seed_candidates(frequency_db=db_path, config=config)

            self.assertEqual([item.lemma for item in second], [item.lemma for item in first])
            self.assertEqual(second[0].word_package, first[0].word_package)
            self.assertEqual(second[0].metadata, first[0].metadata)

    def test_seed_frontier_cache_invalidates_when_frequency_db_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            cache_dir = root / "cache"
            _build_freq_db(db_path)
            config = SeedSelectionConfig(
                language_pair="en-ja",
                top_n=None,
                require_jmdict=False,
                cache_dir=cache_dir,
            )

            first = build_seed_candidates(frequency_db=db_path, config=config)
            self.assertNotIn("山", [item.lemma for item in first])

            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
                    ("山", 0.5, 2000.0),
                )
                conn.commit()
            stat = db_path.stat()
            os.utime(db_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

            second = build_seed_candidates(frequency_db=db_path, config=config)

            self.assertIn("山", [item.lemma for item in second])
            self.assertGreaterEqual(len(list(cache_dir.rglob("*.jsonl"))), 2)

    def test_seed_frontier_cache_corrupt_file_falls_back_to_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            cache_dir = root / "cache"
            _build_freq_db(db_path)
            config = SeedSelectionConfig(
                language_pair="en-ja",
                top_n=3,
                require_jmdict=False,
                cache_dir=cache_dir,
            )

            first = build_seed_candidates(frequency_db=db_path, config=config)
            cache_file = next(cache_dir.rglob("*.jsonl"))
            cache_file.write_text("not-json\n", encoding="utf-8")

            second = build_seed_candidates(frequency_db=db_path, config=config)

            self.assertEqual([item.lemma for item in second], [item.lemma for item in first])

    def test_seed_frontier_cache_preserves_zero_admission_suitability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            cache_dir = root / "cache"
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT)"
                )
                conn.execute(
                    "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?)",
                    ("。", 1, 1000.0, "補助記号-句点"),
                )
                conn.commit()
            config = SeedSelectionConfig(
                language_pair="en-ja",
                top_n=1,
                require_jmdict=False,
                cache_dir=cache_dir,
            )

            first = build_seed_candidates(frequency_db=db_path, config=config)
            self.assertEqual(first[0].admission_suitability, 0.0)

            with patch(
                "lexishift_core.srs.seed.SqliteFrequencyStore",
                side_effect=AssertionError("cache miss attempted to reopen frequency DB"),
            ):
                second = build_seed_candidates(frequency_db=db_path, config=config)

            self.assertEqual(second[0].admission_suitability, 0.0)

    def test_seed_frontier_cache_status_prepare_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "freq.sqlite"
            cache_dir = root / "cache"
            _build_freq_db(db_path)
            config = SeedSelectionConfig(
                language_pair="en-ja",
                top_n=None,
                require_jmdict=False,
                cache_dir=cache_dir,
            )

            missing = seed_frontier_cache_status(frequency_db=db_path, config=config)
            self.assertEqual(missing["status"], "missing")

            prepared = prepare_seed_frontier_cache(frequency_db=db_path, config=config)
            self.assertEqual(prepared["status"], "ready")
            self.assertEqual(prepared["seed_count"], 5)

            stale_file = cache_dir / "en-ja" / "old.jsonl"
            stale_file.write_text('{"kind":"old"}\n', encoding="utf-8")
            cleanup = cleanup_seed_frontier_cache(
                cache_dir=cache_dir,
                pair="en-ja",
                active_cache_path=Path(str(prepared["cache_path"])),
            )
            self.assertEqual(cleanup["deleted_cache_count"], 1)
            self.assertFalse(stale_file.exists())

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

            self.assertEqual([item.lemma for item in selected], ["ところ", "所"])
            self.assertNotEqual(selected[0].identity_key, selected[1].identity_key)
            first_package = selected[0].word_package
            self.assertIsNotNone(first_package)
            self.assertEqual(first_package["surface"], "ところ")
            self.assertEqual(first_package["reading"], "ところ")
            self.assertEqual(first_package["script_forms"]["kanji"], "所")
            self.assertEqual(first_package["script_forms"]["kana"], "ところ")
            self.assertEqual(first_package["script_forms"]["romaji"], "tokoro")

            selector_candidates = seed_to_selector_candidates(selected)
            self.assertEqual(
                selector_candidates[0].metadata["candidate_identity_key"],
                selected[0].identity_key,
            )
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
