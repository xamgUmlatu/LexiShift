from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import load_jmdict_glosses_and_script_forms  # noqa: E402
from lexishift_core.resources.japanese_learner_signals import (  # noqa: E402
    build_japanese_learner_signal_bundle,
    load_japanese_lesson_vocabulary_index,
    load_jmdict_lexical_index,
    load_jmdict_priority_index,
    load_jmnedict_name_index,
    load_jlpt_vocabulary_index,
    load_kanjidic2_character_index,
    load_kanjivg_character_index,
)
from lexishift_core.resources.japanese_script import kana_to_romaji  # noqa: E402
from lexishift_core.rulegen.pairs.en_ja import (  # noqa: E402
    EnJaRulegenConfig,
    generate_en_ja_results,
)


def _write_sample_jmdict(path: Path) -> None:
    payload = (
        "<JMdict>"
        "<entry>"
        "<k_ele><keb>猫</keb></k_ele>"
        "<r_ele><reb>ねこ</reb></r_ele>"
        "<sense><gloss xml:lang='eng'>cat</gloss></sense>"
        "</entry>"
        "</JMdict>"
    )
    path.write_text(payload, encoding="utf-8")


def _write_tokoro_jmdict(path: Path) -> None:
    payload = (
        "<JMdict>"
        "<entry>"
        "<k_ele><keb>所</keb></k_ele>"
        "<r_ele><reb>ところ</reb></r_ele>"
        "<sense><gloss xml:lang='eng'>place</gloss></sense>"
        "</entry>"
        "</JMdict>"
    )
    path.write_text(payload, encoding="utf-8")


class TestJapaneseScriptForms(unittest.TestCase):
    def test_kana_to_romaji_transliterates_hiragana_and_katakana(self) -> None:
        self.assertEqual(kana_to_romaji("ねこ"), "neko")
        self.assertEqual(kana_to_romaji("キャット"), "kyatto")

    def test_jmdict_loader_extracts_script_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_sample_jmdict(path)
            mapping, forms = load_jmdict_glosses_and_script_forms(path)

        self.assertIn("cat", mapping["猫"])
        self.assertIn("cat", mapping["ねこ"])
        self.assertEqual(forms["猫"]["kanji"], "猫")
        self.assertEqual(forms["猫"]["kana"], "ねこ")
        self.assertEqual(forms["猫"]["romaji"], "neko")
        self.assertEqual(forms["ねこ"]["kanji"], "猫")

    def test_jmdict_priority_loader_extracts_form_priority_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            payload = (
                "<JMdict>"
                "<entry>"
                "<k_ele><keb>猫</keb><ke_pri>ichi1</ke_pri><ke_pri>nf08</ke_pri></k_ele>"
                "<r_ele><reb>ねこ</reb><re_pri>news2</re_pri></r_ele>"
                "<sense><gloss xml:lang='eng'>cat</gloss></sense>"
                "</entry>"
                "</JMdict>"
            )
            path.write_text(payload, encoding="utf-8")

            index = load_jmdict_priority_index(path)

        self.assertEqual(index["猫"].priority_band, "primary")
        self.assertEqual(index["猫"].priority_score, 1.0)
        self.assertEqual(index["猫"].nf_min, 8)
        self.assertIn("ichi1", index["猫"].direct_tags)
        self.assertIn("news2", index["ねこ"].direct_tags)

    def test_jmdict_lexical_loader_extracts_pos_misc_signal_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            payload = (
                "<JMdict>"
                "<entry>"
                "<k_ele><keb>七百</keb></k_ele>"
                "<r_ele><reb>ななひゃく</reb></r_ele>"
                "<sense><pos>numeric</pos><gloss xml:lang='eng'>seven hundred</gloss></sense>"
                "</entry>"
                "<entry>"
                "<k_ele><keb>的</keb></k_ele>"
                "<k_ele><ke_inf>rarely used kanji form</ke_inf></k_ele>"
                "<r_ele><reb>てき</reb><re_inf>word containing irregular kana usage</re_inf>"
                "<re_restr>的</re_restr><re_nokanji/></r_ele>"
                "<sense><pos>suffix</pos><misc>dated term</misc>"
                "<dial>Kansai-ben</dial><stagk>的</stagk><s_inf>formal only</s_inf>"
                "<lsource xml:lang='eng' ls_type='part'>tic</lsource>"
                "<xref>形式的</xref><gloss xml:lang='eng'>-ical</gloss></sense>"
                "</entry>"
                "<entry>"
                "<k_ele><keb>的</keb></k_ele>"
                "<r_ele><reb>まと</reb></r_ele>"
                "<sense><pos>noun</pos><gloss xml:lang='eng'>target</gloss></sense>"
                "</entry>"
                "</JMdict>"
            )
            path.write_text(payload, encoding="utf-8")

            index = load_jmdict_lexical_index(path)
            bundle = build_japanese_learner_signal_bundle(
                lemma="七百",
                jmdict_lexical_index=index,
            )

        self.assertIn("numeric", index["七百"].lexical_class_groups)
        self.assertEqual(index["七百"].non_vocab_signal_score, 0.9)
        self.assertIn("affix_or_counter", index["的"].lexical_class_groups)
        self.assertIn("marked_usage", index["的"].lexical_class_groups)
        self.assertIn("dialect_marked", index["的"].lexical_class_groups)
        self.assertIn("loanword_source", index["的"].lexical_class_groups)
        self.assertIn("kanji_form_marked", index["的"].lexical_class_groups)
        self.assertIn("reading_form_marked", index["的"].lexical_class_groups)
        self.assertIn("sense_restricted", index["的"].lexical_class_groups)
        self.assertIn("reading_restricted", index["的"].lexical_class_groups)
        self.assertIn("no_kanji_reading", index["的"].lexical_class_groups)
        self.assertEqual(index["的"].dial_values, ("kansai-ben",))
        self.assertIn("eng", index["的"].source_language_values)
        self.assertIn("type:part", index["的"].source_language_values)
        self.assertEqual(index["的"].entry_count, 2)
        self.assertEqual(index["的"].kanji_form_count, 1)
        self.assertEqual(index["的"].reading_form_count, 2)
        self.assertEqual(index["的"].form_count, 3)
        self.assertEqual(index["的"].sense_info_count, 1)
        self.assertEqual(index["的"].xref_count, 1)
        self.assertEqual(bundle["sources"], ["japanese_script", "jmdict_lexical"])
        self.assertEqual(bundle["japanese_script"]["script_shape"], "kanji_only")
        self.assertEqual(bundle["jmdict_lexical"]["non_vocab_signal_score"], 0.9)

    def test_kanjidic2_loader_and_signal_bundle_extract_kanji_level_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kanjidic2.xml"
            payload = (
                "<kanjidic2>"
                "<character>"
                "<literal>猫</literal>"
                '<radical><rad_value rad_type="classical">94</rad_value></radical>'
                "<misc><grade>8</grade><stroke_count>11</stroke_count>"
                '<variant var_type="jis208">1-20-13</variant>'
                "<rad_name>けものへん</rad_name><freq>1702</freq><jlpt>2</jlpt></misc>"
                '<dic_number><dic_ref dr_type="heisig">1919</dic_ref></dic_number>'
                '<query_code><q_code qc_type="skip">1-3-8</q_code></query_code>'
                "<reading_meaning><rmgroup>"
                '<reading r_type="ja_on">ビョウ</reading>'
                '<reading r_type="ja_kun">ねこ</reading>'
                "<meaning>cat</meaning></rmgroup><nanori>ね</nanori></reading_meaning>"
                "</character>"
                "</kanjidic2>"
            )
            path.write_text(payload, encoding="utf-8")

            index = load_kanjidic2_character_index(path)
            bundle = build_japanese_learner_signal_bundle(
                lemma="猫",
                kanjidic2_character_index=index,
            )

        self.assertEqual(index["猫"].grade, 8)
        self.assertEqual(bundle["sources"], ["japanese_script", "kanjidic2"])
        self.assertEqual(bundle["kanjidic2"]["grade_max"], 8)
        self.assertEqual(bundle["kanjidic2"]["stroke_count_max"], 11)
        self.assertEqual(bundle["kanjidic2"]["old_jlpt_hardest_level"], 2)
        self.assertEqual(bundle["kanjidic2"]["on_readings"], ["ビョウ"])
        self.assertEqual(bundle["kanjidic2"]["kun_readings"], ["ねこ"])
        self.assertEqual(bundle["kanjidic2"]["nanori_reading_count"], 1)
        self.assertEqual(bundle["kanjidic2"]["meaning_count"], 1)
        self.assertEqual(bundle["kanjidic2"]["variant_type_count"], 1)
        self.assertEqual(bundle["kanjidic2"]["query_code_type_values"], ["skip"])
        self.assertEqual(
            bundle["kanjidic2"]["character_readings"],
            [
                {
                    "kanji": "猫",
                    "on_readings": ["ビョウ"],
                    "kun_readings": ["ねこ"],
                    "nanori_readings": ["ね"],
                }
            ],
        )

    def test_jmnedict_loader_and_signal_bundle_extract_name_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMnedict.xml"
            payload = (
                "<JMnedict>"
                "<entry>"
                "<ent_seq>1</ent_seq>"
                "<k_ele><keb>山田</keb></k_ele>"
                "<r_ele><reb>やまだ</reb></r_ele>"
                "<trans><name_type>family or surname</name_type>"
                "<trans_det>Yamada</trans_det></trans>"
                "</entry>"
                "</JMnedict>"
            )
            path.write_text(payload, encoding="utf-8")

            index = load_jmnedict_name_index(path)
            bundle = build_japanese_learner_signal_bundle(
                lemma="山田",
                jmnedict_name_index=index,
            )

        self.assertIn("person_name", index["山田"].name_type_groups)
        self.assertEqual(index["山田"].name_signal_score, 1.0)
        self.assertEqual(bundle["sources"], ["japanese_script", "jmnedict_name"])
        self.assertEqual(bundle["jmnedict_name"]["name_signal_score"], 1.0)

    def test_kanjivg_loader_and_signal_bundle_extract_visual_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kanjivg.xml"
            payload = (
                "<kanjivg xmlns:kvg='http://kanjivg.tagaini.net'>"
                "<kanji id='kvg:kanji_732b'>"
                "<g id='kvg:732b' kvg:element='猫' kvg:radical='general'>"
                "<g id='kvg:732b-g1' kvg:element='犭' kvg:position='left'>"
                "<path id='kvg:732b-s1' d='M1 1'/>"
                "<path id='kvg:732b-s2' d='M2 2'/>"
                "</g>"
                "<g id='kvg:732b-g2' kvg:element='苗' kvg:phon='苗' kvg:variant='true'>"
                "<g id='kvg:732b-g3' kvg:element='艹'>"
                "<path id='kvg:732b-s3' d='M3 3'/>"
                "</g>"
                "<path id='kvg:732b-s4' d='M4 4'/>"
                "</g>"
                "</g>"
                "</kanji>"
                "</kanjivg>"
            )
            path.write_text(payload, encoding="utf-8")

            index = load_kanjivg_character_index(path)
            bundle = build_japanese_learner_signal_bundle(
                lemma="猫",
                kanjivg_character_index=index,
            )

        self.assertEqual(index["猫"].path_count, 4)
        self.assertEqual(index["猫"].component_count, 3)
        self.assertEqual(index["猫"].max_group_depth, 3)
        self.assertEqual(index["猫"].variant_count, 1)
        self.assertEqual(index["猫"].position_values, ("left",))
        self.assertEqual(index["猫"].phonetic_elements, ("苗",))
        self.assertEqual(bundle["sources"], ["japanese_script", "kanjivg"])
        self.assertEqual(bundle["kanjivg"]["path_count_max"], 4)
        self.assertIn("苗", bundle["kanjivg"]["component_elements_sample"])
        self.assertEqual(bundle["kanjivg"]["variant_count"], 1)
        self.assertEqual(bundle["kanjivg"]["phonetic_component_count"], 1)

    def test_jlpt_vocabulary_loader_and_signal_bundle_extract_level_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JLPT_vocab_ALL.csv"
            path.write_text(
                (
                    "Kanji,Reading,Level\n"
                    "猫,ねこ,5\n"
                    "技術,ぎじゅつ,2\n"
                    "外国,がいこく,5\n"
                    "コーヒー,コーヒー,5\n"
                ),
                encoding="utf-8",
            )

            index = load_jlpt_vocabulary_index(path)
            bundle = build_japanese_learner_signal_bundle(
                lemma="猫",
                reading="ねこ",
                jlpt_vocabulary_index=index,
            )
            inherited = build_japanese_learner_signal_bundle(
                lemma="外国",
                reading="とつくに",
                jlpt_vocabulary_index=index,
            )
            katakana_reading = build_japanese_learner_signal_bundle(
                lemma="コーヒー",
                reading="こーひー",
                jlpt_vocabulary_index=index,
            )

        self.assertEqual(index["猫"].levels, (5,))
        self.assertEqual(index["ねこ"].readings, ("ねこ",))
        self.assertIn("猫\tねこ\t5", index["猫"].entries)
        self.assertEqual(bundle["sources"], ["japanese_script", "jlpt_vocabulary"])
        self.assertEqual(bundle["jlpt_vocabulary"]["easiest_level"], 5)
        self.assertEqual(bundle["jlpt_vocabulary"]["difficulty_score"], 0.08)
        self.assertEqual(bundle["jlpt_vocabulary"]["beginner_core_score"], 1.0)
        self.assertTrue(bundle["jlpt_vocabulary"]["exact_match"])
        self.assertEqual(bundle["jlpt_vocabulary"]["match_type"], "exact")
        self.assertEqual(bundle["jlpt_vocabulary"]["exact_easiest_level"], 5)
        self.assertTrue(inherited["jlpt_vocabulary"]["surface_match"])
        self.assertFalse(inherited["jlpt_vocabulary"]["exact_match"])
        self.assertEqual(inherited["jlpt_vocabulary"]["match_type"], "surface")
        self.assertIsNone(inherited["jlpt_vocabulary"]["exact_easiest_level"])
        self.assertIsNone(inherited["jlpt_vocabulary"]["exact_difficulty_score"])
        self.assertTrue(katakana_reading["jlpt_vocabulary"]["exact_match"])
        self.assertTrue(katakana_reading["jlpt_vocabulary"]["reading_match"])

    def test_lesson_vocabulary_loader_extracts_pressbooks_vocab_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epub_dir = Path(tmp) / "EPUB"
            epub_dir.mkdir()
            path = epub_dir / "chapter-001-slug.xhtml"
            path.write_text(
                (
                    "<html><body><h1>Module 1.1 Vocabulary</h1><table>"
                    "<tr><th>Audio</th><th>Hiragana</th><th>Romanization</th>"
                    "<th>Kanji</th><th>English translation</th></tr>"
                    "<tr><td></td><td>せんせい</td><td>sensei</td><td>先生</td>"
                    "<td>teacher</td></tr>"
                    "<tr><td></td><td>ねこ</td><td>neko</td><td></td><td>cat</td></tr>"
                    "</table></body></html>"
                ),
                encoding="utf-8",
            )

            index = load_japanese_lesson_vocabulary_index(Path(tmp))
            bundle = build_japanese_learner_signal_bundle(
                lemma="先生",
                lesson_vocabulary_index=index,
            )

        self.assertEqual(index["先生"].lesson_indices, (1,))
        self.assertEqual(index["せんせい"].surfaces, ("先生",))
        self.assertEqual(index["ねこ"].surfaces, ("ねこ",))
        self.assertEqual(index["先生"].romanizations, ("sensei",))
        self.assertEqual(index["先生"].glosses, ("teacher",))
        self.assertEqual(index["先生"].lesson_titles, ("Module 1.1 Vocabulary",))
        self.assertEqual(bundle["sources"], ["japanese_script", "lesson_vocabulary"])
        self.assertEqual(bundle["lesson_vocabulary"]["earliest_lesson"], 1)
        self.assertEqual(bundle["lesson_vocabulary"]["difficulty_score"], 0.02)

    def test_japanese_script_signal_detects_mixed_script_shape(self) -> None:
        bundle = build_japanese_learner_signal_bundle(lemma="申し込む")

        self.assertEqual(bundle["sources"], ["japanese_script"])
        self.assertEqual(bundle["japanese_script"]["script_shape"], "mixed_japanese")
        self.assertEqual(bundle["japanese_script"]["kanji_count"], 2)
        self.assertEqual(bundle["japanese_script"]["hiragana_count"], 2)

    def test_en_ja_rulegen_metadata_includes_script_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_sample_jmdict(path)
            results = generate_en_ja_results(
                ("猫",),
                config=EnJaRulegenConfig(
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "猫": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "猫",
                            "reading": "ねこ",
                            "script_forms": {
                                "kanji": "猫",
                                "kana": "ねこ",
                                "romaji": "neko",
                            },
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                ),
            )

        self.assertGreater(len(results), 0)
        metadata = results[0].rule.metadata
        self.assertIsNotNone(metadata)
        self.assertIsNotNone(metadata.script_forms)
        self.assertIsNotNone(metadata.word_package)
        self.assertEqual(metadata.script_forms["kanji"], "猫")
        self.assertEqual(metadata.script_forms["kana"], "ねこ")
        self.assertEqual(metadata.script_forms["romaji"], "neko")
        self.assertEqual(metadata.word_package["script_forms"]["kana"], "ねこ")

    def test_en_ja_rulegen_requires_word_package_for_japanese_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_sample_jmdict(path)
            results = generate_en_ja_results(
                ("猫",),
                config=EnJaRulegenConfig(
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={},
                ),
            )

        self.assertEqual(results, [])

    def test_en_ja_rulegen_filters_by_reading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            payload = (
                "<JMdict>"
                "<entry>"
                "<k_ele><keb>時</keb></k_ele>"
                "<r_ele><reb>とき</reb></r_ele>"
                "<sense><gloss xml:lang='eng'>time</gloss></sense>"
                "</entry>"
                "<entry>"
                "<k_ele><keb>時</keb></k_ele>"
                "<r_ele><reb>じ</reb></r_ele>"
                "<sense><gloss xml:lang='eng'>o'clock</gloss></sense>"
                "</entry>"
                "</JMdict>"
            )
            path.write_text(payload, encoding="utf-8")
            results = generate_en_ja_results(
                ("時",),
                config=EnJaRulegenConfig(
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "時": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "時",
                            "reading": "とき",
                            "script_forms": {
                                "kanji": "時",
                                "kana": "とき",
                                "romaji": "toki",
                            },
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                ),
            )

        self.assertEqual([result.rule.source_phrase for result in results], ["time"])

    def test_en_ja_rulegen_prefers_word_package_script_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_tokoro_jmdict(path)
            results = generate_en_ja_results(
                ("所",),
                config=EnJaRulegenConfig(
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "所": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "所",
                            "reading": "ところ",
                            "script_forms": {
                                "kanji": "所",
                                "kana": "ところ",
                                "romaji": "tokoro_freq",
                            },
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                ),
            )

        self.assertGreater(len(results), 0)
        metadata = results[0].rule.metadata
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.script_forms["kana"], "ところ")
        self.assertEqual(metadata.script_forms["romaji"], "tokoro_freq")
        self.assertIsNotNone(metadata.word_package)
        self.assertEqual(metadata.word_package["reading"], "ところ")

    def test_en_ja_rulegen_falls_back_to_jmdict_when_package_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_tokoro_jmdict(path)
            results = generate_en_ja_results(
                ("所",),
                config=EnJaRulegenConfig(
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "所": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "所",
                            "reading": "ところ",
                            "script_forms": {"kanji": "所"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                ),
            )

        self.assertGreater(len(results), 0)
        metadata = results[0].rule.metadata
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.script_forms["kana"], "ところ")
        self.assertIsNotNone(metadata.word_package)
        self.assertEqual(metadata.word_package["script_forms"]["kana"], "ところ")


if __name__ == "__main__":
    unittest.main()
