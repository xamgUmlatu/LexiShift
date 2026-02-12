from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import (  # noqa: E402
    SrsItem,
    SrsStore,
    srs_store_from_dict,
    srs_store_to_dict,
)


class TestSrsStore(unittest.TestCase):
    def test_srs_store_roundtrip_with_word_package(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:所",
                    lemma="所",
                    language_pair="en-ja",
                    source_type="initial_set",
                    word_package={
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "所",
                        "reading": "ところ",
                        "script_forms": {
                            "kanji": "所",
                            "kana": "ところ",
                            "romaji": "tokoro",
                        },
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                ),
            ),
            version=1,
        )

        payload = srs_store_to_dict(store)
        restored = srs_store_from_dict(payload)

        self.assertEqual(len(restored.items), 1)
        self.assertIsNotNone(restored.items[0].word_package)
        self.assertEqual(restored.items[0].word_package["reading"], "ところ")
        self.assertEqual(restored.items[0].word_package["script_forms"]["romaji"], "tokoro")

    def test_legacy_srs_store_without_word_package_still_loads(self) -> None:
        legacy = {
            "version": 1,
            "items": [
                {
                    "item_id": "en-ja:猫",
                    "lemma": "猫",
                    "language_pair": "en-ja",
                    "source_type": "initial_set",
                    "exposures": 3,
                    "srs_history": [{"ts": "2026-02-10T00:00:00Z", "rating": "good"}],
                }
            ],
        }

        restored = srs_store_from_dict(legacy)

        self.assertEqual(len(restored.items), 1)
        self.assertEqual(restored.items[0].lemma, "猫")
        self.assertIsNone(restored.items[0].word_package)
        self.assertEqual(restored.items[0].exposures, 3)


if __name__ == "__main__":
    unittest.main()
