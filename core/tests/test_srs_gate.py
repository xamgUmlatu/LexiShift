from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import RuleMetadata, VocabRule
from lexishift_core.srs import SrsItem
from lexishift_core.srs_gate import select_rules_for_practice


class TestSrsGate(unittest.TestCase):
    def test_filters_by_pair_and_lemma(self) -> None:
        rules = [
            VocabRule(
                source_phrase="twilight",
                replacement="gloaming",
                metadata=RuleMetadata(language_pair="en-en"),
            ),
            VocabRule(
                source_phrase="abendrot",
                replacement="gloaming",
                metadata=RuleMetadata(language_pair="de-en"),
            ),
        ]
        items = [
            SrsItem(
                item_id="en-en:gloaming",
                lemma="gloaming",
                language_pair="en-en",
                source_type="frequency",
            )
        ]
        filtered = select_rules_for_practice(rules, items)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].metadata.language_pair, "en-en")

    def test_unpaired_rules_optional(self) -> None:
        rules = [VocabRule(source_phrase="twilight", replacement="gloaming")]
        items = [
            SrsItem(
                item_id="en-en:gloaming",
                lemma="gloaming",
                language_pair="en-en",
                source_type="frequency",
            )
        ]
        filtered = select_rules_for_practice(rules, items)
        self.assertEqual(filtered, [])
        filtered = select_rules_for_practice(rules, items, include_unpaired_rules=True)
        self.assertEqual(len(filtered), 1)


if __name__ == "__main__":
    unittest.main()
