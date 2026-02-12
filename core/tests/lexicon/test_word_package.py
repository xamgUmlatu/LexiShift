from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.lexicon.word_package import (  # noqa: E402
    build_word_package,
    normalize_word_package,
)


class TestWordPackage(unittest.TestCase):
    def test_build_word_package_normalizes_japanese_reading(self) -> None:
        package = build_word_package(
            language_pair="en-ja",
            surface="所",
            reading="トコロ",
            source_provider="freq-ja-bccwj",
        )
        self.assertIsNotNone(package)
        self.assertEqual(package["language_tag"], "ja")
        self.assertEqual(package["reading"], "ところ")
        self.assertEqual(package["script_forms"]["romaji"], "tokoro")

    def test_normalize_word_package_requires_core_fields(self) -> None:
        package = normalize_word_package(
            {
                "version": 1,
                "language_tag": "ja",
                "surface": "所",
                "reading": "ところ",
                "script_forms": {"kanji": "所", "kana": "ところ", "romaji": "tokoro"},
                "source": {"provider": "freq-ja-bccwj"},
            }
        )
        self.assertIsNotNone(package)
        self.assertEqual(package["source"]["provider"], "freq-ja-bccwj")

        invalid = normalize_word_package({"surface": "所"})
        self.assertIsNone(invalid)


if __name__ == "__main__":
    unittest.main()
