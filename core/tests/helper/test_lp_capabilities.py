from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    known_pairs,
    selectable_srs_pairs,
    supported_rulegen_pairs,
)


class TestLpCapabilities(unittest.TestCase):
    def test_supported_rulegen_pairs_use_capability_registry(self) -> None:
        pairs = supported_rulegen_pairs()
        self.assertEqual(pairs, ("en-ja", "en-de"))

    def test_srs_selectable_pairs_include_current_gui_pairs(self) -> None:
        pairs = selectable_srs_pairs()
        self.assertIn("en-ja", pairs)
        self.assertIn("en-en", pairs)
        self.assertIn("ja-ja", pairs)
        self.assertIn("en-de", pairs)
        self.assertIn("de-de", pairs)
        self.assertIn("de-en", pairs)

    def test_known_pairs_contains_all_declared_capabilities(self) -> None:
        pairs = known_pairs()
        self.assertIn("en-zh", pairs)
        self.assertIn("en-de", pairs)
        self.assertIn("de-en", pairs)


if __name__ == "__main__":
    unittest.main()
