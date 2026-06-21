from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.japanese_learner_signals import (  # noqa: E402
    JmdictLexicalRecord,
    JmdictPriorityRecord,
    JmnedictNameRecord,
    build_japanese_learner_signal_bundle,
)


class TestJapaneseAcronymSignals(unittest.TestCase):
    def test_exact_shared_acronym_recommends_default_suppression(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＰＤＦ",
            reading="ピーディーエフ",
            raw_pos="名詞-普通名詞-一般",
            wtype="記号",
            source_frequency_profile={"rank_min": 17619, "pmw_max": 2.29},
            jmdict_lexical_index={
                "ＰＤＦ": JmdictLexicalRecord(
                    pos_values=("noun",),
                    gloss_values=("PDF",),
                )
            },
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["normalized_ascii_surface"], "PDF")
        self.assertEqual(signal["recommended_acronym_class"], "shared_exact_acronym")
        self.assertEqual(signal["recommended_candidate_state"], "suppressed_default")
        self.assertEqual(signal["reading_spellout_confidence"], 1.0)
        self.assertEqual(signal["identity_gloss_confidence"], 1.0)
        self.assertIn("exact_acronym_gloss", signal["reasons"])

    def test_japanese_specific_acronym_is_not_blindly_suppressed(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＣＭ",
            reading="シーエム",
            raw_pos="名詞-普通名詞-一般",
            wtype="記号",
            source_frequency_profile={"rank_min": 3265, "pmw_max": 24.78},
            jmdict_priority_index={
                "ＣＭ": JmdictPriorityRecord(
                    direct_tags=("spec1",),
                    entry_tags=("spec1",),
                    priority_score=1.0,
                    priority_band="primary",
                )
            },
            jmdict_lexical_index={
                "ＣＭ": JmdictLexicalRecord(
                    pos_values=("noun",),
                    gloss_values=(
                        "commercial (on radio, TV, etc.)",
                        "commercial message",
                    ),
                )
            },
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["recommended_acronym_class"], "japanese_specific_acronym")
        self.assertEqual(signal["recommended_candidate_state"], "normal_vocab")
        self.assertGreaterEqual(signal["recommended_admission_suitability"], 0.7)
        self.assertIn("japanese_specific_usage", signal["reasons"])
        self.assertIn("real_usage_signal", signal["reasons"])

    def test_domain_acronym_recommends_topic_only(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＭＲＩ",
            reading="エムアールアイ",
            raw_pos="名詞-普通名詞-一般",
            wtype="記号",
            source_frequency_profile={"rank_min": 14147, "domain_rank_spread": 18000},
            jmdict_lexical_index={
                "ＭＲＩ": JmdictLexicalRecord(
                    pos_values=("noun",),
                    field_values=("medicine",),
                    gloss_values=("MRI",),
                )
            },
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["recommended_acronym_class"], "domain_acronym")
        self.assertEqual(signal["recommended_candidate_state"], "topic_only")
        self.assertEqual(signal["field_domain_confidence"], 1.0)
        self.assertIn("jmdict_domain_field", signal["reasons"])

    def test_initialism_expansion_requires_matching_gloss_initials(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＡＢＣ",
            reading="エービーシー",
            raw_pos="名詞-普通名詞-一般",
            wtype="記号",
            jmdict_lexical_index={
                "ＡＢＣ": JmdictLexicalRecord(
                    pos_values=("noun",),
                    gloss_values=("not a meaningful expansion",),
                )
            },
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["expanded_gloss_confidence"], 0.0)
        self.assertEqual(signal["english_initialism_expansion_confidence"], 0.0)
        self.assertNotIn("expanded_english_gloss", signal["reasons"])

    def test_initialism_expansion_matches_gloss_initials(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＭＲＩ",
            reading="エムアールアイ",
            raw_pos="名詞-普通名詞-一般",
            wtype="記号",
            jmdict_lexical_index={
                "ＭＲＩ": JmdictLexicalRecord(
                    pos_values=("noun",),
                    gloss_values=("magnetic resonance imaging",),
                )
            },
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["identity_gloss_confidence"], 0.0)
        self.assertEqual(signal["expanded_gloss_confidence"], 1.0)
        self.assertEqual(signal["english_initialism_expansion_confidence"], 1.0)
        self.assertIn("expanded_english_gloss", signal["reasons"])

    def test_distribution_skew_alone_does_not_make_domain_acronym(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＡＢＣ",
            reading="エービーシー",
            raw_pos="名詞-普通名詞-一般",
            wtype="記号",
            source_frequency_profile={
                "domain_rank_known_count": 12,
                "domain_rank_spread": 100000,
            },
        )

        signal = bundle["ja_acronym"]
        self.assertGreaterEqual(signal["domain_concentration"], 0.9)
        self.assertEqual(signal["recommended_acronym_class"], "unknown_acronym_like")
        self.assertEqual(signal["recommended_candidate_state"], "deprioritized_vocab")

    def test_jmnedict_organization_acronym_uses_proper_name_lane(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="ＮＨＫ",
            reading="エヌエイチケー",
            raw_pos="名詞-固有名詞-一般",
            wtype="固",
            source_frequency_profile={"rank_min": 2899, "pmw_max": 28.93},
            jmnedict_name_index={
                "ＮＨＫ": JmnedictNameRecord(
                    surfaces=("ＮＨＫ",),
                    readings=("エヌエイチケー",),
                    name_types=("organization name",),
                    name_type_groups=("organization_or_product_name",),
                    translation_count=3,
                    name_signal_score=0.85,
                )
            },
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["recommended_acronym_class"], "proper_name_acronym")
        self.assertEqual(signal["recommended_candidate_state"], "deprioritized_vocab")
        self.assertGreaterEqual(signal["proper_name_risk"], 0.85)
        self.assertIn("proper_name_signal", signal["reasons"])

    def test_mixed_code_term_is_classified_separately_from_acronyms(self) -> None:
        bundle = build_japanese_learner_signal_bundle(
            lemma="Ｘ線",
            reading="エックスせん",
            raw_pos="名詞-普通名詞-一般",
            wtype="混",
        )

        signal = bundle["ja_acronym"]
        self.assertEqual(signal["recommended_acronym_class"], "mixed_code_term")
        self.assertEqual(signal["recommended_candidate_state"], "deprioritized_vocab")
        self.assertEqual(signal["mixed_code_confidence"], 1.0)
        self.assertIn("mixed_code_surface", signal["reasons"])

    def test_normal_japanese_word_has_no_acronym_signal(self) -> None:
        bundle = build_japanese_learner_signal_bundle(lemma="猫", reading="ネコ")

        self.assertIn("japanese_script", bundle)
        self.assertNotIn("ja_acronym", bundle)


if __name__ == "__main__":
    unittest.main()
