from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.candidate_classification import (  # noqa: E402
    classify_srs_candidate,
)


class TestCandidateClassification(unittest.TestCase):
    def test_suppresses_compositional_ja_numerals_from_default_vocab(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="七百",
            raw_pos="名詞-数詞",
        )

        self.assertEqual(classification.candidate_state, "suppressed_default")
        self.assertEqual(classification.presentation_mode, "suppress")
        self.assertEqual(classification.problem_class, "numeral_or_counter")
        self.assertEqual(classification.confidence, "high")
        self.assertAlmostEqual(classification.admission_suitability, 0.0, places=6)

    def test_classifies_simple_ja_numerals_as_pattern_items(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="一",
            raw_pos="名詞-数詞",
        )

        self.assertEqual(classification.candidate_state, "pattern_item")
        self.assertEqual(classification.presentation_mode, "pattern")
        self.assertEqual(classification.problem_class, "numeral_or_counter")
        self.assertAlmostEqual(classification.admission_suitability, 0.02, places=6)

    def test_classifies_ja_particles_as_grammar_items(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="ね",
            raw_pos="助詞-終助詞",
        )

        self.assertEqual(classification.candidate_state, "grammar_item")
        self.assertEqual(classification.presentation_mode, "grammar")
        self.assertEqual(classification.problem_class, "particle_or_auxiliary")
        self.assertAlmostEqual(classification.admission_suitability, 0.02, places=6)

    def test_classifies_exact_ja_function_surfaces_as_grammar_items(self) -> None:
        for lemma in ("で", "が", "より", "そして", "及び"):
            with self.subTest(lemma=lemma):
                classification = classify_srs_candidate(
                    language_pair="en-ja",
                    lemma=lemma,
                    raw_pos="名詞-普通名詞-一般",
                )

                self.assertEqual(classification.candidate_state, "grammar_item")
                self.assertEqual(classification.presentation_mode, "grammar")
                self.assertEqual(classification.problem_class, "particle_or_auxiliary")
                self.assertEqual(classification.confidence, "high")
                self.assertIn("ja_exact_function_item", classification.reasons)
                self.assertAlmostEqual(
                    classification.admission_suitability,
                    0.02,
                    places=6,
                )

    def test_classifies_core_ja_country_names_as_normal_vocab(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="中国",
            raw_pos="名詞-固有名詞-地名-国",
        )

        self.assertEqual(classification.candidate_state, "normal_vocab")
        self.assertEqual(classification.presentation_mode, "vocab")
        self.assertEqual(classification.problem_class, "proper_noun")
        self.assertAlmostEqual(classification.admission_suitability, 0.85, places=6)

    def test_classifies_non_core_ja_proper_nouns_as_deprioritized_vocab(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="イラク",
            raw_pos="名詞-固有名詞-地名-国",
        )

        self.assertEqual(classification.candidate_state, "deprioritized_vocab")
        self.assertEqual(classification.presentation_mode, "vocab")
        self.assertEqual(classification.problem_class, "proper_noun")
        self.assertAlmostEqual(classification.admission_suitability, 0.25, places=6)

    def test_applies_source_backed_acronym_recommendation(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="ＰＤＦ",
            raw_pos="名詞-普通名詞-一般",
            learner_signals={
                "ja_acronym": {
                    "recommended_acronym_class": "shared_exact_acronym",
                    "recommended_candidate_state": "suppressed_default",
                    "recommended_admission_suitability": 0.0,
                }
            },
        )

        self.assertEqual(classification.candidate_state, "suppressed_default")
        self.assertEqual(classification.presentation_mode, "suppress")
        self.assertEqual(classification.problem_class, "acronym_or_code")
        self.assertEqual(classification.confidence, "high")
        self.assertAlmostEqual(classification.admission_suitability, 0.0, places=6)
        self.assertIn(
            "ja_acronym_recommended_state:suppressed_default",
            classification.reasons,
        )

    def test_can_disable_source_backed_acronym_recommendation(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-ja",
            lemma="ＰＤＦ",
            raw_pos="名詞-普通名詞-一般",
            learner_signals={
                "ja_acronym": {
                    "recommended_acronym_class": "shared_exact_acronym",
                    "recommended_candidate_state": "suppressed_default",
                    "recommended_admission_suitability": 0.0,
                }
            },
            apply_learner_signal_recommendations=False,
        )

        self.assertEqual(classification.candidate_state, "normal_vocab")
        self.assertEqual(classification.presentation_mode, "vocab")
        self.assertEqual(classification.problem_class, "normal_vocab")

    def test_en_de_content_words_default_to_normal_vocab(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-de",
            lemma="Haus",
            raw_pos="SUB:NOM:SIN:NEU",
        )

        self.assertEqual(classification.candidate_state, "normal_vocab")
        self.assertEqual(classification.presentation_mode, "vocab")
        self.assertEqual(classification.problem_class, "normal_vocab")
        self.assertAlmostEqual(classification.admission_suitability, 1.0, places=6)

    def test_en_de_abbreviation_pos_is_deprioritized(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-de",
            lemma="st",
            raw_pos="ABK:SANKT:SUB",
        )

        self.assertEqual(classification.candidate_state, "deprioritized_vocab")
        self.assertEqual(classification.presentation_mode, "vocab")
        self.assertEqual(classification.problem_class, "acronym_or_code")
        self.assertEqual(classification.confidence, "high")
        self.assertIn("de_pos_abbreviation_or_code", classification.reasons)
        self.assertAlmostEqual(classification.admission_suitability, 0.2, places=6)

    def test_en_de_function_pos_only_is_grammar_item(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-de",
            lemma="der",
            raw_pos="ART:DEF|PRO:REL",
        )

        self.assertEqual(classification.candidate_state, "grammar_item")
        self.assertEqual(classification.presentation_mode, "grammar")
        self.assertEqual(classification.problem_class, "particle_or_auxiliary")
        self.assertEqual(classification.confidence, "high")
        self.assertIn("de_function_pos_only", classification.reasons)
        self.assertAlmostEqual(classification.admission_suitability, 0.08, places=6)

    def test_en_de_bound_standalone_fragment_is_grammar_item(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-de",
            lemma="dar",
            raw_pos="",
        )

        self.assertEqual(classification.candidate_state, "grammar_item")
        self.assertEqual(classification.presentation_mode, "grammar")
        self.assertEqual(classification.problem_class, "prefix_or_suffix")
        self.assertEqual(classification.confidence, "high")
        self.assertIn("de_bound_standalone_fragment", classification.reasons)
        self.assertAlmostEqual(classification.admission_suitability, 0.03, places=6)

    def test_en_de_exact_contractions_are_grammar_items_without_pos(self) -> None:
        classification = classify_srs_candidate(
            language_pair="en-de",
            lemma="zur",
            raw_pos="",
        )

        self.assertEqual(classification.candidate_state, "grammar_item")
        self.assertEqual(classification.presentation_mode, "grammar")
        self.assertEqual(classification.problem_class, "particle_or_auxiliary")
        self.assertEqual(classification.confidence, "high")
        self.assertIn("de_exact_grammar_item", classification.reasons)
        self.assertAlmostEqual(classification.admission_suitability, 0.08, places=6)

    def test_en_de_mixed_content_and_function_pos_stays_normal_vocab(self) -> None:
        for lemma, raw_pos in (
            (
                "freuen",
                "SUB:AKK:SIN:NEU:INF|VER:INF:SFT",
            ),
            (
                "bisschen",
                "PRO:IND:AKK:SIN:ALG:B/S|SUB:AKK:SIN:NEU",
            ),
        ):
            with self.subTest(lemma=lemma):
                classification = classify_srs_candidate(
                    language_pair="en-de",
                    lemma=lemma,
                    raw_pos=raw_pos,
                )

                self.assertEqual(classification.candidate_state, "normal_vocab")
                self.assertEqual(classification.presentation_mode, "vocab")
                self.assertEqual(classification.problem_class, "normal_vocab")


if __name__ == "__main__":
    unittest.main()
