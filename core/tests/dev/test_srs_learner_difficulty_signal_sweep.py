from __future__ import annotations

import lzma
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    FormulaVariant,
    PiecewiseFormulaSection,
    _calibration_only_sweep,
    _component_matrix_payload,
    _expand_formula_variant_jlpt_transforms,
    _iter_grid_variants,
    _pairwise_order_metrics,
    _parse_grid_caps,
    _parse_weight_mapping_csv,
    _rank_correlation_metrics,
    _success_metrics_for_calibration,
    _build_target_curve_scoring_context,
    _normalization_population_rows,
    _row_with_tubelex_frequency,
    _target_curve_raw_scores_for_variant,
    _variant_values_by_identity,
    _within_grid_weight_bounds,
    difficulty_components,
    estimate_variant_difficulty,
    load_tubelex_frequency_index,
    np as sweep_np,
    variant_difficulty_diagnostics,
)


class TestSrsLearnerDifficultySignalSweep(unittest.TestCase):
    def test_difficulty_components_extract_jmdict_and_kanjidic2_signals(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.8,
                "wtype": "漢",
                "pos": "名詞-普通名詞-サ変可能",
                "learner_signals": {
                    "japanese_script": {"script_complexity_score": 0.33},
                    "jmdict_priority": {"priority_score": 0.75},
                    "jmdict_lexical": {
                        "non_vocab_signal_score": 0.9,
                        "lexical_class_groups": ["affix_or_counter"],
                    },
                    "jmnedict_name": {"name_signal_score": 0.85},
                    "kanjidic2": {
                        "kanji_grade_difficulty_proxy": 0.34,
                        "freq_rank_mean": 105,
                        "old_jlpt_hardest_level": 2,
                        "stroke_count_mean": 8,
                    },
                    "kanjivg": {
                        "visual_complexity_proxy_mean": 0.42,
                    },
                },
            }
        )

        self.assertEqual(components["frequency"], 0.8)
        self.assertEqual(components["frequency_value_known"], 1.0)
        self.assertEqual(components["frequency_rank_known"], 0.0)
        self.assertEqual(components["script_complexity"], 0.33)
        self.assertEqual(components["jmdict_priority"], 0.25)
        self.assertEqual(components["jmdict_priority_known"], 1.0)
        self.assertEqual(components["jmdict_lexical_known"], 1.0)
        self.assertEqual(components["lexical_source_known"], 1.0)
        self.assertEqual(components["jmdict_non_vocab_raw_class_score"], 0.9)
        self.assertEqual(components["jmdict_affix_counter_class"], 1.0)
        self.assertAlmostEqual(components["jmdict_non_ladder_entry_risk"] or 0.0, 0.225)
        self.assertAlmostEqual(components["jmdict_non_vocab_risk"] or 0.0, 0.225)
        self.assertEqual(components["jmnedict_name_risk"], 0.85)
        self.assertEqual(components["jmnedict_name_overlap"], 0.85)
        self.assertEqual(components["jmnedict_name_known"], 1.0)
        self.assertEqual(components["kanji_grade"], 0.34)
        self.assertEqual(components["kanjidic2_known"], 1.0)
        self.assertAlmostEqual(components["old_jlpt_kanji"], 0.70)
        self.assertAlmostEqual(components["stroke_count"], 0.30)
        self.assertAlmostEqual(components["kanjivg_visual_complexity"] or 0.0, 0.42)
        self.assertEqual(components["kanjivg_known"], 1.0)
        self.assertEqual(components["orthographic_source_known"], 1.0)
        self.assertEqual(components["pedagogical_source_known"], 0.0)
        self.assertGreater(components["source_coverage_count"] or 0.0, 0.0)
        self.assertGreater(components["kanji_curriculum_burden"] or 0.0, 0.0)
        self.assertGreater(components["kanji_shape_burden"] or 0.0, 0.0)
        self.assertGreater(components["max_kanji_shape_burden"] or 0.0, 0.0)
        self.assertGreater(components["kanji_frequency_rank"] or 0.0, 0.0)
        self.assertEqual(components["wtype_kango_risk"], 1.0)
        self.assertEqual(components["wtype_wago_ease"], 0.0)
        self.assertEqual(components["wtype_non_wago_risk"], 1.0)
        self.assertEqual(components["pos_sahen_noun_risk"], 1.0)
        self.assertEqual(components["pos_common_noun_gate"], 1.0)
        self.assertAlmostEqual(components["kango_old_jlpt_kanji"] or 0.0, 0.70)
        self.assertAlmostEqual(components["kango_kanji_grade"] or 0.0, 0.34)
        self.assertAlmostEqual(components["sahen_kango_risk"] or 0.0, 1.0)
        self.assertGreater(components["kanji_burden"] or 0.0, 0.0)
        self.assertGreater(components["kango_kanji_burden"] or 0.0, 0.0)
        self.assertGreater(components["kango_common_priority_risk"] or 0.0, 0.0)
        self.assertGreater(components["kango_uncommon_kanji_burden"] or 0.0, 0.0)
        self.assertEqual(components["jmdict_marked_usage_flag"], 0.0)
        self.assertEqual(components["jmdict_marked_usage_risk"], 0.0)
        self.assertEqual(components["sahen_kango_ease_gate"], 1.0)

    def test_difficulty_components_extract_jlpt_exact_match_signals(self) -> None:
        exact = difficulty_components(
            {
                "learner_signals": {
                    "jlpt_vocabulary": {
                        "difficulty_score": 0.08,
                        "beginner_core_score": 1.0,
                        "exact_difficulty_score": 0.08,
                        "exact_beginner_core_score": 1.0,
                        "exact_match": True,
                        "surface_match": True,
                        "reading_match": True,
                    },
                },
            }
        )
        inherited = difficulty_components(
            {
                "learner_signals": {
                    "jlpt_vocabulary": {
                        "difficulty_score": 0.08,
                        "beginner_core_score": 1.0,
                        "exact_match": False,
                        "surface_match": True,
                        "reading_match": False,
                    },
                },
            }
        )

        self.assertEqual(exact["jlpt_vocab_known"], 1.0)
        self.assertEqual(exact["jlpt_vocab_exact_known"], 1.0)
        self.assertEqual(exact["jlpt_vocab_surface_known"], 1.0)
        self.assertEqual(exact["jlpt_vocab_reading_known"], 1.0)
        self.assertAlmostEqual(exact["jlpt_vocab_exact_difficulty"] or 0.0, 0.08)
        self.assertAlmostEqual(exact["jlpt_vocab_exact_beginner_core"] or 0.0, 1.0)
        self.assertEqual(inherited["jlpt_vocab_known"], 1.0)
        self.assertEqual(inherited["jlpt_vocab_exact_known"], 0.0)
        self.assertEqual(inherited["jlpt_vocab_surface_known"], 1.0)
        self.assertEqual(inherited["jlpt_vocab_reading_known"], 0.0)
        self.assertIsNone(inherited["jlpt_vocab_exact_difficulty"])

    def test_tubelex_frequency_sidecar_adds_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tubelex-ja-lemma-pos.tsv.xz"
            _write_tubelex_fixture(
                path,
                [
                    ("の", 10000, 100, 50, "助詞-格助詞"),
                    ("銀行", 5000, 80, 40, "名詞-普通名詞-一般"),
                    ("銀行", 50, 10, 5, "動詞-一般"),
                ],
            )
            index = load_tubelex_frequency_index(path)

            row = _row_with_tubelex_frequency(
                _seed_row(
                    "bank-v",
                    "銀行",
                    "ぎんこう",
                    0.90,
                    pos="動詞-一般",
                ),
                index,
            )
            profile = row["tubelex_frequency_profile"]
            components = difficulty_components(row)

        self.assertEqual(profile["match_kind"], "word_pos_exact")
        self.assertEqual(profile["pos"], "動詞-一般")
        self.assertIn("tubelex_frequency", row["learner_signal_sources"])
        self.assertIsNotNone(components["tubelex_frequency"])
        self.assertEqual(components["tubelex_frequency_known"], 1.0)
        self.assertIsNotNone(components["tubelex_rank_difficulty"])
        self.assertIsNotNone(components["tubelex_count_difficulty"])
        self.assertIsNotNone(components["tubelex_dispersion_difficulty"])
        self.assertGreater(components["tubelex_spoken_rescue"] or 0.0, 0.0)
        self.assertGreater(components["tubelex_bccwj_gap_abs"] or 0.0, 0.0)
        self.assertLessEqual(
            components["tubelex_bccwj_min_frequency"] or 0.0,
            components["tubelex_bccwj_mean_frequency"] or 0.0,
        )
        self.assertLessEqual(
            components["tubelex_bccwj_mean_frequency"] or 0.0,
            components["tubelex_bccwj_max_frequency"] or 0.0,
        )
        self.assertIsNotNone(components["tubelex_bccwj_agreement_hard"])

    def test_tubelex_frequency_sidecar_falls_back_to_word_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tubelex-ja.tsv.xz"
            _write_tubelex_fixture(
                path,
                [
                    ("料理", 1000, 80, 50, ""),
                ],
            )
            index = load_tubelex_frequency_index(path)

            row = _row_with_tubelex_frequency(
                _seed_row("cooking", "料理", "りょうり", 0.40, pos="名詞-普通名詞-一般"),
                index,
            )

        self.assertEqual(row["tubelex_frequency_profile"]["match_kind"], "word")
        self.assertEqual(row["tubelex_frequency_profile"]["word"], "料理")

    def test_difficulty_components_detect_missing_kanji_curriculum_metadata(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.98,
                "wtype": "和",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                    "jmdict_lexical": {"lexical_class_groups": ["marked_usage"]},
                    "japanese_script": {"script_complexity_score": 0.12},
                    "kanjidic2": {
                        "known_kanji_count": 1,
                        "curriculum_signal_known_count": 0,
                        "stroke_count_mean": 12,
                        "stroke_count_max": 12,
                    },
                    "kanjivg": {
                        "visual_complexity_proxy_mean": 0.54,
                        "visual_complexity_proxy_max": 0.54,
                    },
                },
            }
        )

        self.assertEqual(components["kanji_curriculum_missing_risk"], 1.0)
        self.assertGreater(components["rare_wago_missing_curriculum_risk"] or 0.0, 0.95)
        self.assertGreater(
            components["rare_wago_missing_curriculum_shape_risk"] or 0.0,
            0.50,
        )
        self.assertGreater(components["rare_wago_obscure_written_risk"] or 0.0, 0.95)

    def test_difficulty_components_track_unranked_frequency_risk(self) -> None:
        ranked = difficulty_components(
            {
                "core_rank": 123,
                "frequency_difficulty_proxy": 0.96,
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                },
            }
        )
        unranked = difficulty_components(
            {
                "core_rank": None,
                "frequency_difficulty_proxy": 0.96,
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                },
            }
        )
        high_priority_unranked = difficulty_components(
            {
                "core_rank": None,
                "frequency_difficulty_proxy": 0.96,
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                },
            }
        )
        low_frequency_unranked = difficulty_components(
            {
                "core_rank": None,
                "frequency_difficulty_proxy": 0.30,
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                },
            }
        )
        unknown_rank = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.96,
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                },
            }
        )

        self.assertEqual(ranked["frequency_unranked_risk"], 0.0)
        self.assertEqual(ranked["frequency_unranked_rare_risk"], 0.0)
        self.assertAlmostEqual(ranked["frequency_power2"] or 0.0, 0.9216)
        self.assertAlmostEqual(ranked["frequency_power3"] or 0.0, 0.884736)
        self.assertAlmostEqual(ranked["frequency_tail80"] or 0.0, 0.8)
        self.assertEqual(ranked["frequency_unranked_floor80_risk"], 0.0)
        self.assertEqual(unranked["frequency_unranked_risk"], 1.0)
        self.assertAlmostEqual(unranked["frequency_unranked_rare_risk"] or 0.0, 0.96)
        self.assertAlmostEqual(
            unranked["frequency_unranked_priority_risk"] or 0.0,
            0.96,
        )
        self.assertGreater(unranked["frequency_unranked_tail_risk"] or 0.0, 0.70)
        self.assertAlmostEqual(unranked["frequency_unranked_power2_risk"] or 0.0, 0.9216)
        self.assertAlmostEqual(
            unranked["frequency_unranked_power3_risk"] or 0.0,
            0.884736,
        )
        self.assertAlmostEqual(unranked["frequency_unranked_floor60_risk"] or 0.0, 0.96)
        self.assertAlmostEqual(unranked["frequency_unranked_floor70_risk"] or 0.0, 0.96)
        self.assertAlmostEqual(unranked["frequency_unranked_floor80_risk"] or 0.0, 0.96)
        self.assertAlmostEqual(unranked["frequency_unranked_floor90_risk"] or 0.0, 0.96)
        self.assertAlmostEqual(unranked["frequency_unranked_floor95_risk"] or 0.0, 0.96)
        self.assertAlmostEqual(unranked["frequency_unranked_floor99_risk"] or 0.0, 0.99)
        self.assertAlmostEqual(
            low_frequency_unranked["frequency_unranked_floor60_risk"] or 0.0,
            0.60,
        )
        self.assertAlmostEqual(
            low_frequency_unranked["frequency_unranked_floor70_risk"] or 0.0,
            0.70,
        )
        self.assertAlmostEqual(
            low_frequency_unranked["frequency_unranked_floor80_risk"] or 0.0,
            0.80,
        )
        self.assertAlmostEqual(
            low_frequency_unranked["frequency_unranked_floor90_risk"] or 0.0,
            0.90,
        )
        self.assertAlmostEqual(
            low_frequency_unranked["frequency_unranked_floor95_risk"] or 0.0,
            0.95,
        )
        self.assertAlmostEqual(
            low_frequency_unranked["frequency_unranked_floor99_risk"] or 0.0,
            0.99,
        )
        self.assertEqual(high_priority_unranked["frequency_unranked_risk"], 1.0)
        self.assertLess(
            high_priority_unranked["frequency_unranked_priority_risk"] or 0.0,
            0.40,
        )
        self.assertIsNone(unknown_rank["frequency_unranked_risk"])
        self.assertIsNone(unknown_rank["frequency_unranked_floor60_risk"])
        self.assertIsNone(unknown_rank["frequency_unranked_floor80_risk"])

    def test_difficulty_components_keep_covered_kanji_curriculum_missing_risk_low(
        self,
    ) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.60,
                "wtype": "和",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                    "kanjidic2": {
                        "known_kanji_count": 1,
                        "curriculum_signal_known_count": 1,
                        "kanji_grade_difficulty_proxy": 0.70,
                        "freq_rank_mean": 1702,
                        "old_jlpt_hardest_level": 2,
                        "stroke_count_mean": 11,
                    },
                    "kanjivg": {"visual_complexity_proxy_mean": 0.48},
                },
            }
        )

        self.assertEqual(components["kanji_curriculum_missing_risk"], 0.0)
        self.assertEqual(components["rare_wago_missing_curriculum_risk"], 0.0)

    def test_difficulty_components_extract_wago_and_plain_verb_gates(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.1,
                "wtype": "和",
                "pos": "動詞-一般",
                "learner_signals": {
                    "kanjidic2": {
                        "kanji_grade_difficulty_proxy": 0.70,
                        "old_jlpt_hardest_level": 1,
                    },
                    "kanjivg": {"visual_complexity_proxy_mean": 0.80},
                },
            }
        )

        self.assertEqual(components["wtype_kango_risk"], 0.0)
        self.assertEqual(components["wtype_wago_ease"], 1.0)
        self.assertEqual(components["wtype_non_wago_risk"], 0.0)
        self.assertEqual(components["pos_plain_verb_gate"], 1.0)
        self.assertEqual(components["pos_sahen_noun_risk"], 0.0)
        self.assertEqual(components["kango_old_jlpt_kanji"], 0.0)
        self.assertEqual(components["wago_kanji_grade"], 0.70)
        self.assertEqual(components["wago_visual_complexity"], 0.80)
        self.assertEqual(components["kango_kanji_burden"], 0.0)
        self.assertGreater(components["wago_kanji_burden"] or 0.0, 0.0)
        self.assertIsNone(components["rare_wago_risk"])

    def test_difficulty_components_track_rare_wago_written_risk(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.95,
                "wtype": "和",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                    "jmdict_lexical": {"lexical_class_groups": ["marked_usage"]},
                    "japanese_script": {"script_complexity_score": 0.12},
                    "kanjidic2": {"stroke_count_mean": 10, "stroke_count_max": 16},
                    "kanjivg": {
                        "visual_complexity_proxy_mean": 0.60,
                        "visual_complexity_proxy_max": 0.80,
                    },
                },
            }
        )

        self.assertGreater(components["rare_wago_risk"] or 0.0, 0.90)
        self.assertGreater(components["rare_wago_written_risk"] or 0.0, 0.30)
        self.assertEqual(components["jmdict_marked_usage_risk"], 1.0)
        self.assertGreater(components["max_kanji_burden"] or 0.0, 0.70)
        self.assertGreater(components["rare_wago_max_kanji_burden"] or 0.0, 0.70)
        self.assertGreater(components["rare_wago_marked_usage_risk"] or 0.0, 0.90)
        self.assertGreater(components["rare_wago_obscure_written_risk"] or 0.0, 0.90)
        self.assertGreater(components["rare_wago_tail_risk"] or 0.0, 0.40)
        self.assertGreater(components["written_wago_tail_risk"] or 0.0, 0.30)

    def test_difficulty_components_dampen_high_priority_marked_wago_risk(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.80,
                "wtype": "和",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                    "jmdict_lexical": {"lexical_class_groups": ["marked_usage"]},
                    "kanjidic2": {
                        "kanji_grade_difficulty_proxy": 0.34,
                        "stroke_count_mean": 6,
                        "stroke_count_max": 6,
                    },
                    "kanjivg": {
                        "visual_complexity_proxy_mean": 0.52,
                        "visual_complexity_proxy_max": 0.52,
                    },
                },
            }
        )

        self.assertEqual(components["jmdict_marked_usage_risk"], 1.0)
        self.assertLess(components["rare_wago_marked_usage_risk"] or 0.0, 0.30)
        self.assertLess(components["rare_wago_obscure_written_risk"] or 0.0, 0.30)
        self.assertLess(components["rare_wago_tail_risk"] or 0.0, 0.01)

    def test_difficulty_components_keep_common_wago_obscure_written_risk_low(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.30,
                "wtype": "和",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                    "japanese_script": {"script_complexity_score": 0.12},
                    "kanjidic2": {
                        "kanji_grade_difficulty_proxy": 0.34,
                        "stroke_count_mean": 6,
                        "stroke_count_max": 6,
                    },
                    "kanjivg": {
                        "visual_complexity_proxy_mean": 0.52,
                        "visual_complexity_proxy_max": 0.52,
                    },
                },
            }
        )

        self.assertLess(components["rare_wago_risk"] or 0.0, 0.20)
        self.assertLess(components["rare_wago_obscure_written_risk"] or 0.0, 0.12)
        self.assertLess(components["written_wago_tail_risk"] or 0.0, 0.01)

    def test_difficulty_components_track_kango_mid_signal(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.60,
                "wtype": "漢",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                    "kanjidic2": {
                        "kanji_grade_difficulty_proxy": 0.50,
                        "freq_rank_mean": 1200,
                        "old_jlpt_hardest_level": 2,
                        "stroke_count_mean": 12,
                    },
                    "kanjivg": {"visual_complexity_proxy_mean": 0.55},
                },
            }
        )

        self.assertGreater(components["kango_mid_signal"] or 0.0, 0.30)

    def test_difficulty_components_match_standard_kanjidic2_compound_reading(
        self,
    ) -> None:
        components = difficulty_components(
            {
                "lemma": "研究",
                "reading": "けんきゅう",
                "frequency_difficulty_proxy": 0.40,
                "wtype": "漢",
                "pos": "名詞-普通名詞-サ変可能",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                    "kanjidic2": {
                        "character_readings": [
                            {"kanji": "研", "on_readings": ["ケン"], "kun_readings": []},
                            {"kanji": "究", "on_readings": ["キュウ"], "kun_readings": []},
                        ]
                    },
                },
            }
        )

        self.assertEqual(components["non_standard_reading_risk"], 0.0)
        self.assertEqual(components["rare_non_standard_reading_risk"], 0.0)

    def test_difficulty_components_raise_rare_non_standard_reading_risk(self) -> None:
        components = difficulty_components(
            {
                "lemma": "猯",
                "reading": "まみ",
                "frequency_difficulty_proxy": 0.98,
                "wtype": "和",
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.0},
                    "kanjidic2": {
                        "character_readings": [
                            {
                                "kanji": "猯",
                                "on_readings": ["タン"],
                                "kun_readings": ["いのしし"],
                            }
                        ]
                    },
                },
            }
        )

        self.assertEqual(components["non_standard_reading_risk"], 1.0)
        self.assertGreater(components["rare_non_standard_reading_risk"] or 0.0, 0.94)
        self.assertGreater(
            components["rare_wago_non_standard_reading_risk"] or 0.0,
            0.94,
        )

    def test_difficulty_components_dampen_common_irregular_reading_risk(self) -> None:
        components = difficulty_components(
            {
                "lemma": "今日",
                "reading": "きょう",
                "frequency_difficulty_proxy": 0.05,
                "wtype": "和",
                "pos": "名詞-普通名詞-副詞可能",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 1.0},
                    "kanjidic2": {
                        "character_readings": [
                            {
                                "kanji": "今",
                                "on_readings": ["コン", "キン"],
                                "kun_readings": ["いま"],
                            },
                            {
                                "kanji": "日",
                                "on_readings": ["ニチ", "ジツ"],
                                "kun_readings": ["ひ", "か"],
                            },
                        ]
                    },
                },
            }
        )

        self.assertEqual(components["non_standard_reading_risk"], 1.0)
        self.assertEqual(components["rare_non_standard_reading_risk"], 0.0)

    def test_difficulty_components_extract_acronym_signals(self) -> None:
        components = difficulty_components(
            {
                "frequency_difficulty_proxy": 0.95,
                "learner_signals": {
                    "ja_acronym": {
                        "surface_confidence": 1.0,
                        "mixed_code_confidence": 0.0,
                        "reading_spellout_confidence": 1.0,
                        "identity_gloss_confidence": 1.0,
                        "expanded_gloss_confidence": 0.0,
                        "japanese_specific_usage_confidence": 0.0,
                        "domain_concentration": 0.2,
                        "field_domain_confidence": 0.0,
                        "proper_name_risk": 0.0,
                        "real_usage_confidence": 0.8,
                        "recommended_acronym_class": "shared_exact_acronym",
                        "recommended_candidate_state": "suppressed_default",
                    }
                },
            }
        )

        self.assertEqual(components["acronym_surface_confidence"], 1.0)
        self.assertEqual(components["acronym_spellout_reading"], 1.0)
        self.assertEqual(components["acronym_identity_gloss"], 1.0)
        self.assertEqual(components["acronym_domain_concentration"], 0.2)
        self.assertEqual(components["acronym_real_usage_confidence"], 0.8)
        self.assertEqual(components["acronym_default_suppress_risk"], 1.0)
        self.assertEqual(components["acronym_topic_only_risk"], 0.0)
        self.assertEqual(components["acronym_shared_exact_risk"], 1.0)
        self.assertEqual(components["acronym_japanese_specific_gate"], 0.0)
        self.assertEqual(components["proper_acronym_entity_risk"], 0.0)

    def test_difficulty_components_extract_news_entity_signals(self) -> None:
        components = difficulty_components(
            {
                "candidate_state": "deprioritized_vocab",
                "problem_class": "proper_noun",
                "frequency_difficulty_proxy": 0.7,
                "pos": "名詞-固有名詞-地名-国",
                "learner_signals": {
                    "jmdict_priority": {
                        "direct_tags": ["news1"],
                        "entry_tags": ["news1", "gai1"],
                        "priority_score": 0.9,
                    },
                    "jmdict_lexical": {
                        "misc_values": ["abbreviation"],
                        "field_values": ["politics"],
                        "lexical_class_groups": ["misc_marked"],
                    },
                    "jmnedict_name": {
                        "name_signal_score": 0.75,
                        "name_type_groups": ["place_name"],
                    },
                },
            }
        )

        self.assertEqual(components["jmdict_news_priority_risk"], 1.0)
        self.assertEqual(components["jmdict_foreign_priority_risk"], 1.0)
        self.assertEqual(components["jmdict_foreign_priority_commonness"], 1.0)
        self.assertEqual(components["jmdict_abbreviation_flag"], 1.0)
        self.assertEqual(components["jmdict_abbreviation_risk"], 1.0)
        self.assertEqual(components["jmdict_news_or_policy_field_flag"], 1.0)
        self.assertEqual(components["jmdict_news_or_policy_domain_risk"], 1.0)
        self.assertEqual(components["jmnedict_place_name_risk"], 1.0)
        self.assertEqual(components["proper_noun_pos_risk"], 1.0)
        self.assertEqual(components["proper_noun_pos_flag"], 1.0)
        self.assertEqual(components["proper_country_pos_risk"], 1.0)
        self.assertEqual(components["proper_country_pos_flag"], 1.0)
        self.assertEqual(components["proper_country_entity_overlap"], 1.0)
        self.assertEqual(components["proper_country_entity_risk"], 1.0)
        self.assertEqual(components["named_entity_overlap"], 1.0)
        self.assertEqual(components["named_entity_risk"], 1.0)
        self.assertEqual(components["ordinary_ladder_entity_suppression_risk"], 1.0)
        self.assertEqual(components["news_or_policy_topic_risk"], 1.0)
        self.assertAlmostEqual(components["news_or_policy_frequency_risk"] or 0.0, 0.7)
        self.assertEqual(components["news_named_entity_risk"], 1.0)
        self.assertAlmostEqual(components["named_entity_frequency_risk"] or 0.0, 0.7)
        self.assertAlmostEqual(components["news_named_frequency_risk"] or 0.0, 0.7)
        self.assertEqual(components["news_abbreviation_entity_risk"], 1.0)
        self.assertEqual(components["geopolitical_entity_risk"], 1.0)
        self.assertAlmostEqual(components["geopolitical_frequency_risk"] or 0.0, 0.7)
        self.assertEqual(components["candidate_deprioritized_named_entity_risk"], 1.0)
        self.assertAlmostEqual(
            components["candidate_deprioritized_named_frequency_risk"] or 0.0,
            0.7,
        )

    def test_news_priority_tag_does_not_create_topic_risk(self) -> None:
        components = difficulty_components(
            {
                "candidate_state": "normal_vocab",
                "frequency_difficulty_proxy": 0.2,
                "learner_signals": {
                    "jmdict_priority": {
                        "direct_tags": ["news1"],
                        "entry_tags": ["news1"],
                        "priority_score": 0.95,
                    },
                    "jmdict_lexical": {
                        "field_values": [],
                        "lexical_class_groups": ["ordinary_lexeme"],
                    },
                },
            }
        )

        self.assertEqual(components["jmdict_news_priority_risk"], 1.0)
        self.assertEqual(components["jmdict_news_priority_commonness"], 1.0)
        self.assertIsNone(components["news_or_policy_topic_risk"])
        self.assertIsNone(components["news_or_policy_frequency_risk"])

    def test_common_entity_overlap_is_not_full_entity_suppression_risk(self) -> None:
        components = difficulty_components(
            {
                "candidate_state": "normal_vocab",
                "problem_class": "proper_noun",
                "frequency_difficulty_proxy": 0.14,
                "pos": "名詞-固有名詞-地名-国",
                "learner_signals": {
                    "jmdict_priority": {"priority_score": 0.90},
                    "jmnedict_name": {
                        "name_signal_score": 1.0,
                        "name_type_groups": ["place_name"],
                    },
                },
            }
        )

        self.assertEqual(components["proper_country_pos_flag"], 1.0)
        self.assertEqual(components["proper_country_entity_overlap"], 1.0)
        self.assertEqual(components["named_entity_overlap"], 1.0)
        self.assertAlmostEqual(components["ordinary_vocab_protection"] or 0.0, 0.90)
        self.assertAlmostEqual(components["entity_suppression_gate"] or 0.0, 0.10)
        self.assertAlmostEqual(components["named_entity_risk"] or 0.0, 0.10)
        self.assertAlmostEqual(
            components["ordinary_ladder_entity_suppression_risk"] or 0.0,
            0.10,
        )

    def test_difficulty_components_extract_common_ambiguity_and_register_gates(
        self,
    ) -> None:
        components = difficulty_components(
            {
                "lemma": "生",
                "reading": "せい",
                "frequency_difficulty_proxy": 0.10,
                "wtype": "漢",
                "pos": "名詞-普通名詞-一般",
                "source_frequency_profile": {
                    "domain_rank_known_count": 12,
                    "domain_rank_spread": 50000,
                },
                "learner_signals": {
                    "jmdict_lexical": {
                        "pos_values": ["noun", "prefix"],
                        "field_values": ["biology"],
                        "lexical_class_groups": [
                            "register_marked",
                            "reading_restricted",
                            "sense_restricted",
                        ],
                        "entry_count": 3,
                        "kanji_form_count": 1,
                        "reading_form_count": 4,
                        "form_count": 5,
                        "sense_count": 9,
                        "gloss_count": 12,
                        "sense_restriction_count": 1,
                        "reading_restriction_count": 1,
                    },
                    "japanese_script": {"script_complexity_score": 0.45},
                    "kanjidic2": {"stroke_count_mean": 8, "stroke_count_max": 8},
                    "kanjivg": {
                        "visual_complexity_proxy_mean": 0.35,
                        "visual_complexity_proxy_max": 0.35,
                    },
                },
            }
        )

        self.assertAlmostEqual(components["frequency_ease"] or 0.0, 0.90)
        self.assertGreater(components["jmdict_entry_count"] or 0.0, 0.0)
        self.assertGreater(components["jmdict_pos_count"] or 0.0, 0.0)
        self.assertGreater(components["jmdict_reading_form_count"] or 0.0, 0.0)
        self.assertEqual(components["jmdict_register_marked_flag"], 1.0)
        self.assertEqual(components["jmdict_field_marked_flag"], 1.0)
        self.assertGreater(components["jmdict_ambiguity_risk"] or 0.0, 0.0)
        self.assertGreater(components["jmdict_ambiguity_score"] or 0.0, 0.0)
        self.assertGreater(components["jmdict_reading_complexity_risk"] or 0.0, 0.0)
        self.assertGreater(
            components["jmdict_reading_complexity_score"] or 0.0,
            0.0,
        )
        self.assertGreater(
            components["jmdict_restriction_complexity_risk"] or 0.0,
            0.0,
        )
        self.assertGreater(
            components["jmdict_restriction_complexity_score"] or 0.0,
            0.0,
        )
        self.assertGreater(components["common_jmdict_ambiguity_risk"] or 0.0, 0.0)
        self.assertGreater(components["common_jmdict_ambiguity_score"] or 0.0, 0.0)
        self.assertGreater(components["common_reading_complexity_risk"] or 0.0, 0.0)
        self.assertEqual(components["jmdict_field_marked_risk"], 1.0)
        self.assertGreater(components["bccwj_domain_profile_variability"] or 0.0, 0.0)
        self.assertGreater(components["bccwj_domain_profile_risk"] or 0.0, 0.0)
        self.assertEqual(components["bccwj_domain_rank_known"], 1.0)
        self.assertGreater(components["common_register_domain_risk"] or 0.0, 0.0)
        self.assertGreater(components["common_register_domain_score"] or 0.0, 0.0)
        self.assertGreater(
            components["common_kango_complexity_risk"] or 0.0,
            0.0,
        )
        self.assertGreater(
            components["common_kango_complexity_score"] or 0.0,
            0.0,
        )

    def test_difficulty_components_extract_lesson_name_contamination_signal(self) -> None:
        components = difficulty_components(
            {
                "candidate_state": "normal_vocab",
                "problem_class": "normal_vocab",
                "frequency_difficulty_proxy": 0.8,
                "pos": "名詞-普通名詞-一般",
                "learner_signals": {
                    "lesson_vocabulary": {"difficulty_score": 0.1},
                    "jmnedict_name": {
                        "name_signal_score": 1.0,
                        "name_type_groups": ["person_name"],
                    },
                },
            }
        )

        self.assertEqual(components["jmnedict_person_name_risk"], 1.0)
        self.assertEqual(components["jmnedict_person_name_overlap"], 1.0)
        self.assertEqual(components["named_entity_overlap"], 1.0)
        self.assertAlmostEqual(components["named_entity_risk"] or 0.0, 0.8)
        self.assertEqual(components["lesson_name_contamination_risk"], 1.0)
        self.assertAlmostEqual(
            components["lesson_name_contamination_frequency_risk"] or 0.0,
            0.8,
        )

    def test_capped_variant_limits_shift_from_frequency(self) -> None:
        row = {
            "frequency_difficulty_proxy": 0.9,
            "learner_signals": {
                "jmdict_priority": {"priority_score": 1.0},
            },
        }
        uncapped = FormulaVariant(
            variant_id="uncapped",
            description="",
            weights={"frequency": 0.5, "jmdict_priority": 0.5},
        )
        capped = FormulaVariant(
            variant_id="capped",
            description="",
            weights={"frequency": 0.5, "jmdict_priority": 0.5},
            max_shift_from_frequency=0.1,
        )

        self.assertAlmostEqual(estimate_variant_difficulty(row, uncapped), 0.45)
        self.assertAlmostEqual(estimate_variant_difficulty(row, capped), 0.8)

    def test_piecewise_variant_blends_sections_by_frequency_anchor(self) -> None:
        row = {
            "frequency_difficulty_proxy": 0.2,
            "learner_signals": {
                "jmdict_priority": {"priority_score": 0.0},
                "kanjidic2": {"stroke_count_mean": 20},
            },
        }
        variant = FormulaVariant(
            variant_id="piecewise",
            description="",
            weights={},
            piecewise_sections=(
                PiecewiseFormulaSection(
                    section_id="early",
                    center=0.0,
                    radius=0.5,
                    weights={"frequency": 1.0},
                ),
                PiecewiseFormulaSection(
                    section_id="late",
                    center=0.5,
                    radius=0.5,
                    weights={"jmdict_priority": 1.0},
                ),
            ),
        )

        self.assertAlmostEqual(estimate_variant_difficulty(row, variant), 0.52)
        diagnostics = variant_difficulty_diagnostics(row, variant)
        self.assertEqual(diagnostics["mode"], "piecewise")
        sections = diagnostics["sections"]
        self.assertEqual([section["section_id"] for section in sections], ["early", "late"])
        self.assertAlmostEqual(float(sections[0]["influence"]), 0.6)
        self.assertAlmostEqual(float(sections[1]["influence"]), 0.4)

    def test_grid_variants_generate_normalized_weight_compositions(self) -> None:
        variants = list(
            _iter_grid_variants(
                signals=("frequency", "kanji_grade", "stroke_count"),
                step=0.5,
                caps=(None, 0.1),
            )
        )

        self.assertEqual(len(variants), 12)
        self.assertEqual(variants[0].variant_id, "grid_s02_cnone_000001")
        self.assertEqual(variants[-1].max_shift_from_frequency, 0.1)
        for variant in variants:
            self.assertAlmostEqual(sum(variant.weights.values()), 1.0)
            self.assertLessEqual(set(variant.weights), {"frequency", "kanji_grade", "stroke_count"})

    def test_parse_grid_caps_accepts_uncapped_and_numeric_values(self) -> None:
        self.assertEqual(_parse_grid_caps("none,0.05,uncapped,0.1"), (None, 0.05, None, 0.1))

    def test_grid_variants_can_filter_to_local_neighborhood(self) -> None:
        variants = list(
            _iter_grid_variants(
                signals=("frequency", "jmdict_priority", "old_jlpt_kanji"),
                step=0.25,
                caps=(None,),
                center={"frequency": 0.5, "jmdict_priority": 0.25, "old_jlpt_kanji": 0.25},
                radius=0.0,
            )
        )

        self.assertEqual(len(variants), 1)
        self.assertEqual(
            variants[0].weights,
            {"frequency": 0.5, "jmdict_priority": 0.25, "old_jlpt_kanji": 0.25},
        )

    def test_grid_weight_bounds_filter_variants(self) -> None:
        self.assertTrue(
            _within_grid_weight_bounds(
                {"frequency": 0.3, "old_jlpt_kanji": 0.6},
                signals=("frequency", "old_jlpt_kanji"),
                min_weights={"frequency": 0.2},
                max_weights={"old_jlpt_kanji": 0.7},
            )
        )
        self.assertFalse(
            _within_grid_weight_bounds(
                {"frequency": 0.1, "old_jlpt_kanji": 0.9},
                signals=("frequency", "old_jlpt_kanji"),
                min_weights={"frequency": 0.2},
                max_weights={"old_jlpt_kanji": 0.7},
            )
        )

    def test_parse_weight_mapping_csv(self) -> None:
        self.assertEqual(
            _parse_weight_mapping_csv("frequency=0.3,jmdict_priority=0.6"),
            {"frequency": 0.3, "jmdict_priority": 0.6},
        )

    def test_pairwise_order_metrics_reward_relative_difficulty_order(self) -> None:
        rows = [
            _calibration_row("名前", 0.02, 0.05),
            _calibration_row("料理", 0.34, 0.36),
            _calibration_row("韜晦", 0.93, 0.20),
        ]

        metrics = _pairwise_order_metrics(rows)

        self.assertEqual(metrics["comparable_count"], 3)
        self.assertEqual(metrics["correct_count"], 2)
        self.assertEqual(metrics["wrong_count"], 1)
        self.assertAlmostEqual(float(metrics["accuracy"]), 2 / 3, places=6)
        self.assertEqual(
            metrics["wrong_examples"][0]["expected_easier"],
            "料理 / りょうり",
        )

    def test_rank_correlation_metrics_use_numeric_targets(self) -> None:
        good_rows = [
            _calibration_row("名前", 0.02, 0.04),
            _calibration_row("料理", 0.34, 0.30),
            _calibration_row("韜晦", 0.93, 0.90),
        ]
        bad_rows = [
            _calibration_row("名前", 0.02, 0.90),
            _calibration_row("料理", 0.34, 0.30),
            _calibration_row("韜晦", 0.93, 0.04),
        ]

        good = _rank_correlation_metrics(good_rows)
        bad = _rank_correlation_metrics(bad_rows)

        self.assertAlmostEqual(float(good["spearman"]), 1.0)
        self.assertAlmostEqual(float(bad["spearman"]), -1.0)

    def test_success_metrics_include_independent_sweep_scores(self) -> None:
        rows = [
            _calibration_row("名前", 0.02, 0.05),
            _calibration_row("料理", 0.34, 0.36),
            _calibration_row("韜晦", 0.93, 0.90),
            _calibration_row("雷霆", 0.98, 0.95),
        ]
        metrics = _success_metrics_for_calibration(
            rows,
            calibration_metrics={
                "difficulty_bucket": {"accuracy": 0.75},
                "difficulty_value": {"mae": 0.05},
                "default_vocab_decision": {"accuracy": 1.0},
            },
        )

        scores = metrics["scores"]
        segments = metrics["segments"]
        self.assertGreater(float(scores["balanced_score"]), 0.90)
        self.assertEqual(segments["beginner_core"]["pass_count"], 1)
        self.assertEqual(segments["high_tail"]["pass_count"], 1)
        self.assertGreater(
            float(metrics["separation"]["mean_gap"]),
            0.80,
        )

    def test_target_curve_values_use_deduped_vocab_population(self) -> None:
        rows = [
            _seed_row("a", "名前", "なまえ", 0.10, core_rank=1),
            _seed_row("b", "料理", "りょうり", 0.50, core_rank=2),
            _seed_row("c", "韜晦", "とうかい", 0.90, core_rank=3),
            _seed_row(
                "ignored",
                "ね",
                "ね",
                0.20,
                candidate_state="grammar_item",
                core_rank=4,
            ),
        ]
        population = _normalization_population_rows(rows)
        context = _build_target_curve_scoring_context(
            population,
            component_names=("frequency",),
            target_band_weights=(0.5, 0.5),
            band_width=0.5,
        )
        values = _variant_values_by_identity(
            FormulaVariant(
                variant_id="frequency_only",
                description="",
                weights={"frequency": 1.0},
            ),
            seed_by_identity={str(row["candidate_identity_key"]): row for row in rows},
            identities=("a", "b", "c", "ignored"),
            normalization_population_rows=population,
            target_curve_context=context,
            score_normalization="target_curve",
            target_band_weights=(0.5, 0.5),
            band_width=0.5,
        )

        self.assertEqual(len(population), 3)
        self.assertAlmostEqual(values["a"], 0.125)
        self.assertAlmostEqual(values["b"], 0.375)
        self.assertAlmostEqual(values["c"], 0.75)
        self.assertAlmostEqual(values["ignored"], 0.20)

    def test_jlpt_vocab_curve_override_changes_raw_component_value(self) -> None:
        row = _seed_row(
            "a",
            "影響",
            "えいきょう",
            0.60,
            learner_signals={
                "jlpt_vocabulary": {
                    "difficulty_score": 0.65,
                    "easiest_level": 2,
                },
            },
        )
        variant = FormulaVariant(
            variant_id="jlpt_override",
            description="",
            weights={"jlpt_vocab_difficulty": 1.0},
            jlpt_vocab_curve={5: 0.05, 4: 0.18, 3: 0.34, 2: 0.52, 1: 0.82},
        )

        diagnostics = variant_difficulty_diagnostics(row, variant)

        self.assertAlmostEqual(estimate_variant_difficulty(row, variant), 0.52)
        self.assertEqual(
            diagnostics["transforms"]["jlpt_vocab_curve"],
            {"N5": 0.05, "N4": 0.18, "N3": 0.34, "N2": 0.52, "N1": 0.82},
        )
        self.assertAlmostEqual(
            diagnostics["base_component_values"]["jlpt_vocab_difficulty"],
            0.65,
        )
        self.assertAlmostEqual(
            diagnostics["component_values"]["jlpt_vocab_difficulty"],
            0.52,
        )

    def test_jlpt_kanji_dampening_pulls_kanji_burden_toward_vocab_anchor(self) -> None:
        row = _seed_row(
            "a",
            "影響",
            "えいきょう",
            0.60,
            learner_signals={
                "jlpt_vocabulary": {
                    "difficulty_score": 0.46,
                    "easiest_level": 2,
                },
                "kanjidic2": {
                    "old_jlpt_hardest_level": 1,
                },
            },
        )
        variant = FormulaVariant(
            variant_id="kanji_dampened",
            description="",
            weights={"old_jlpt_kanji": 1.0},
            jlpt_kanji_dampening_strength=0.5,
        )

        diagnostics = variant_difficulty_diagnostics(row, variant)

        self.assertAlmostEqual(
            diagnostics["base_component_values"]["old_jlpt_kanji"],
            0.90,
        )
        self.assertAlmostEqual(
            diagnostics["component_values"]["old_jlpt_kanji"],
            0.68,
        )
        self.assertAlmostEqual(estimate_variant_difficulty(row, variant), 0.68)
        self.assertEqual(
            diagnostics["transforms"]["jlpt_kanji_dampening_strength"],
            0.5,
        )

    def test_target_curve_context_scores_transformed_jlpt_components(self) -> None:
        if sweep_np is None:
            self.skipTest("NumPy is required for target-curve transform tests.")
        rows = [
            _seed_row(
                "a",
                "名前",
                "なまえ",
                0.20,
                core_rank=1,
                learner_signals={
                    "jlpt_vocabulary": {
                        "difficulty_score": 0.40,
                        "easiest_level": 5,
                    },
                },
            ),
            _seed_row(
                "b",
                "技術",
                "ぎじゅつ",
                0.40,
                core_rank=2,
                learner_signals={
                    "jlpt_vocabulary": {
                        "difficulty_score": 0.30,
                        "easiest_level": 2,
                    },
                },
            ),
        ]
        context = _build_target_curve_scoring_context(
            _normalization_population_rows(rows),
            component_names=("jlpt_vocab_difficulty",),
            target_band_weights=(1.0,),
            band_width=1.0,
        )
        assert context is not None
        base_raw = _target_curve_raw_scores_for_variant(
            FormulaVariant(
                variant_id="base",
                description="",
                weights={"jlpt_vocab_difficulty": 1.0},
            ),
            context,
        )
        transformed_raw = _target_curve_raw_scores_for_variant(
            FormulaVariant(
                variant_id="curve",
                description="",
                weights={"jlpt_vocab_difficulty": 1.0},
                jlpt_vocab_curve={5: 0.05, 4: 0.20, 3: 0.40, 2: 0.70, 1: 0.90},
            ),
            context,
        )

        self.assertEqual([round(float(value), 2) for value in base_raw], [0.40, 0.30])
        self.assertEqual(
            [round(float(value), 2) for value in transformed_raw],
            [0.05, 0.70],
        )

    def test_current_value_variant_is_not_multiplied_by_jlpt_transform_grid(self) -> None:
        expanded = list(
            _expand_formula_variant_jlpt_transforms(
                FormulaVariant(
                    variant_id="current",
                    description="",
                    weights={},
                    use_current_value=True,
                ),
                jlpt_vocab_curves=(
                    {5: 0.05, 4: 0.18, 3: 0.34, 2: 0.52, 1: 0.82},
                    {5: 0.08, 4: 0.22, 3: 0.42, 2: 0.65, 1: 0.85},
                ),
                jlpt_kanji_dampening_strengths=(0.0, 0.5, 1.0),
            )
        )

        self.assertEqual(len(expanded), 1)
        self.assertEqual(expanded[0].variant_id, "current")

    def test_calibration_only_sweep_can_emit_compact_trace_and_matrix(self) -> None:
        if sweep_np is None:
            self.skipTest("NumPy is required for matrix artifact tests.")
        seed_rows = [
            _seed_row("a", "名前", "なまえ", 0.10, core_rank=1),
            _seed_row("b", "韜晦", "とうかい", 0.90, core_rank=2),
        ]
        calibration_rows = [
            _calibration_row("名前", 0.05, 0.10, identity="a"),
            _calibration_row("韜晦", 0.90, 0.90, identity="b"),
        ]
        variants = [
            FormulaVariant(
                variant_id="frequency_only",
                description="",
                weights={"frequency": 1.0},
            ),
            FormulaVariant(
                variant_id="priority_fallback",
                description="",
                weights={"jmdict_priority": 1.0},
            ),
        ]

        retained, summary, trace, matrix = _calibration_only_sweep(
            variants=variants,
            seed_rows=seed_rows,
            normalization_population_rows=_normalization_population_rows(seed_rows),
            target_curve_context=None,
            calibration_rows=calibration_rows,
            score_normalization="raw",
            target_band_weights=(1.0,),
            band_width=1.0,
            leaderboard_limit=2,
            retain_variant_limit=2,
            include_compact_trace=True,
            include_calibration_matrix=True,
        )

        self.assertEqual(summary["evaluated_variant_count"], 2)
        self.assertEqual(len(retained), 2)
        self.assertIsNotNone(trace)
        self.assertIsNotNone(matrix)
        assert trace is not None
        assert matrix is not None
        self.assertEqual(len(trace["variant_records"]), 2)
        self.assertEqual(matrix["observed_values"].shape, (2, 2))
        self.assertAlmostEqual(float(matrix["observed_values"][0, 0]), 0.10)
        self.assertAlmostEqual(float(matrix["observed_values"][0, 1]), 0.90)

    def test_component_matrix_payload_preserves_row_and_component_axes(self) -> None:
        if sweep_np is None:
            self.skipTest("NumPy is required for matrix artifact tests.")
        seed_rows = [
            _seed_row("a", "名前", "なまえ", 0.10, core_rank=1, wtype="和"),
            _seed_row("b", "料理", "りょうり", 0.50, core_rank=2, wtype="漢"),
        ]
        population = _normalization_population_rows(seed_rows)

        payload = _component_matrix_payload(
            population,
            component_names=("frequency", "kanji_grade"),
            target_band_weights=(0.5, 0.5),
            band_width=0.5,
            target_curve_context=None,
        )

        component_names = list(payload["component_names"])
        self.assertIn("frequency", component_names)
        self.assertIn("kanji_grade", component_names)
        self.assertIn("wtype_kango_risk", component_names)
        self.assertIn("wtype_wago_ease", component_names)
        self.assertEqual(payload["component_values"].shape[0], 2)
        self.assertEqual(payload["component_values"].shape[1], len(component_names))
        self.assertEqual(payload["component_present"].shape, payload["component_values"].shape)
        self.assertEqual(list(payload["candidate_identity_keys"]), ["a", "b"])
        kango_index = component_names.index("wtype_kango_risk")
        wago_index = component_names.index("wtype_wago_ease")
        self.assertEqual(float(payload["component_values"][0, kango_index]), 0.0)
        self.assertEqual(float(payload["component_values"][1, kango_index]), 1.0)
        self.assertEqual(float(payload["component_values"][0, wago_index]), 1.0)
        self.assertEqual(float(payload["component_values"][1, wago_index]), 0.0)


def _calibration_row(
    lemma: str,
    expected: float,
    observed: float,
    *,
    reading: str = "",
    identity: str = "",
) -> dict[str, object]:
    readings = {
        "名前": "なまえ",
        "料理": "りょうり",
        "韜晦": "とうかい",
        "雷霆": "らいてい",
    }
    return {
        "lemma": lemma,
        "reading": reading or readings.get(lemma, ""),
        "candidate_identity_key": identity,
        "status": "match",
        "expected_candidate_state": "normal_vocab",
        "observed_candidate_state": "normal_vocab",
        "expected_presentation_mode": "vocab",
        "observed_presentation_mode": "vocab",
        "expected_problem_class": "normal_vocab",
        "observed_problem_class": "normal_vocab",
        "expected_difficulty_band": "beginner" if expected < 0.55 else "advanced",
        "expected_learner_difficulty": expected,
        "observed_current_difficulty_proxy": observed,
        "observed_difficulty_band": "beginner" if observed < 0.55 else "advanced",
        "difficulty_status": "match",
    }


def _write_tubelex_fixture(
    path: Path,
    rows: list[tuple[str, int, int, int, str]],
) -> None:
    with lzma.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write("word\tcount\tvideos\tchannels\tpos\n")
        for word, count, videos, channels, pos in rows:
            handle.write(f"{word}\t{count}\t{videos}\t{channels}\t{pos}\n")


def _seed_row(
    identity: str,
    lemma: str,
    reading: str,
    frequency_difficulty: float,
    *,
    candidate_state: str = "normal_vocab",
    problem_class: str = "normal_vocab",
    core_rank: int | None = 10,
    wtype: str = "",
    pos: str = "",
    learner_signals: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "candidate_identity_key": identity,
        "lemma": lemma,
        "reading": reading,
        "candidate_state": candidate_state,
        "problem_class": problem_class,
        "core_rank": core_rank,
        "frequency_difficulty_proxy": frequency_difficulty,
        "wtype": wtype,
        "pos": pos,
        "learner_signals": learner_signals or {},
    }


if __name__ == "__main__":
    unittest.main()
