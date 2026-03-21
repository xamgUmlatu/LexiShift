from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import (  # noqa: E402
    SrsItem,
    SrsSchedulerSettings,
    SrsSettings,
    SrsStore,
    srs_settings_from_dict,
    srs_settings_to_dict,
    srs_store_from_dict,
    srs_store_to_dict,
)


class TestSrsStore(unittest.TestCase):
    def test_srs_settings_roundtrip_with_scheduler(self) -> None:
        settings = SrsSettings(
            max_active_items=24,
            scheduler=SrsSchedulerSettings(
                algorithm="fsrs",
                desired_retention=0.87,
                learning_steps_minutes=(1, 10),
                relearning_steps_minutes=(10,),
                maximum_interval_days=3650,
                enable_fuzzing=False,
                parameters=(0.212, 1.2931),
            ),
        )

        payload = srs_settings_to_dict(settings)
        restored = srs_settings_from_dict(payload)

        self.assertEqual(restored.scheduler.algorithm, "fsrs")
        self.assertAlmostEqual(restored.scheduler.desired_retention, 0.87, places=6)
        self.assertEqual(tuple(restored.scheduler.learning_steps_minutes), (1, 10))
        self.assertEqual(tuple(restored.scheduler.relearning_steps_minutes), (10,))
        self.assertEqual(restored.scheduler.maximum_interval_days, 3650)
        self.assertEqual(tuple(restored.scheduler.parameters or ()), (0.212, 1.2931))

    def test_srs_store_roundtrip_with_word_package(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:所",
                    lemma="所",
                    language_pair="en-ja",
                    source_type="initial_set",
                    scheduler_state="review",
                    scheduler_step=None,
                    last_review="2026-02-04T10:00:00+00:00",
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
        self.assertEqual(restored.items[0].scheduler_state, "review")
        self.assertEqual(restored.items[0].last_review, "2026-02-04T10:00:00+00:00")

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
