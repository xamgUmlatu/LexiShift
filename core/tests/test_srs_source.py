from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.source import (  # noqa: E402
    SOURCE_EXTENSION,
    SOURCE_INITIAL_SET,
    SOURCE_UNKNOWN,
    merge_source_types,
    normalize_source_type,
)


class TestSrsSource(unittest.TestCase):
    def test_normalize_source_type_known_values(self) -> None:
        self.assertEqual(normalize_source_type(" extension "), SOURCE_EXTENSION)
        self.assertEqual(normalize_source_type(None), SOURCE_UNKNOWN)

    def test_normalize_source_type_unknown_values_are_preserved(self) -> None:
        self.assertEqual(normalize_source_type("profile_model"), "profile_model")

    def test_merge_source_types_preserves_order_and_deduplicates(self) -> None:
        merged = merge_source_types(["initial_set", "initial_set", "USER_STREAM", "", None, "curated"])
        self.assertEqual(merged, (SOURCE_INITIAL_SET, "user_stream", SOURCE_UNKNOWN, "curated"))


if __name__ == "__main__":
    unittest.main()
