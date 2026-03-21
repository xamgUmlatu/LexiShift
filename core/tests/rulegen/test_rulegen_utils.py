from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.generation import RuleCandidate  # noqa: E402
from lexishift_core.rulegen.utils import (  # noqa: E402
    BasicStringNormalizer,
    LeadingEnglishInfinitiveNormalizer,
    sanitize_dictionary_gloss,
)


class TestRulegenUtils(unittest.TestCase):
    def test_basic_string_normalizer_trims_space_after_punctuation_strip(self) -> None:
        normalizer = BasicStringNormalizer()
        candidate = RuleCandidate(
            source_phrase="Appearing (",
            replacement="様",
            language_pair="en-ja",
            source_dict="jmdict",
        )
        normalized = normalizer.normalize(candidate)
        self.assertEqual(normalized.source_phrase, "appearing")

    def test_sanitize_dictionary_gloss_removes_trailing_annotation(self) -> None:
        self.assertEqual(sanitize_dictionary_gloss("hour (noun)."), "hour")

    def test_sanitize_dictionary_gloss_unwraps_outer_quotes(self) -> None:
        self.assertEqual(sanitize_dictionary_gloss('"looking"'), "looking")

    def test_leading_english_infinitive_normalizer_strips_to_prefix(self) -> None:
        normalizer = LeadingEnglishInfinitiveNormalizer()
        candidate = RuleCandidate(
            source_phrase="to do",
            replacement="為る",
            language_pair="en-ja",
            source_dict="jmdict",
            metadata={"reverse_check_source_norm": "to do"},
        )
        normalized = normalizer.normalize(candidate)
        self.assertEqual(normalized.source_phrase, "do")
        self.assertEqual(normalized.metadata["reverse_check_source_norm"], "to do")

    def test_leading_english_infinitive_normalizer_keeps_non_infinitive_phrase(self) -> None:
        normalizer = LeadingEnglishInfinitiveNormalizer()
        candidate = RuleCandidate(
            source_phrase="perform",
            replacement="為る",
            language_pair="en-ja",
            source_dict="jmdict",
        )
        normalized = normalizer.normalize(candidate)
        self.assertEqual(normalized.source_phrase, "perform")


if __name__ == "__main__":
    unittest.main()
