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


if __name__ == "__main__":
    unittest.main()
