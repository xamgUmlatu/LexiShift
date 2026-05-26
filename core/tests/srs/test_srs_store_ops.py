from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_ACTIVE,
    SRS_LIFECYCLE_DISCARDED,
    SrsItem,
    SrsStore,
)
from lexishift_core.srs.store_ops import (  # noqa: E402
    mark_item_lifecycle,
    record_exposure,
    record_feedback,
)


class TestSrsStoreOps(unittest.TestCase):
    def test_record_exposure(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="frequency_list",
                    exposures=1,
                ),
            ),
            version=1,
        )
        now = datetime(2026, 2, 3, 12, 0, tzinfo=timezone.utc)
        updated = record_exposure(store, language_pair="en-ja", lemma="alpha", now=now)
        item = updated.items[0]
        self.assertEqual(item.exposures, 2)
        self.assertIsNotNone(item.last_seen)

    def test_record_feedback_updates_history(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="frequency_list",
                ),
            ),
            version=1,
        )
        now = datetime(2026, 2, 3, 12, 0, tzinfo=timezone.utc)
        updated = record_feedback(
            store,
            language_pair="en-ja",
            lemma="beta",
            rating="good",
            now=now,
        )
        item = updated.items[0]
        self.assertEqual(len(item.history), 1)
        self.assertIsNotNone(item.next_due)

    def test_mark_item_lifecycle_updates_existing_item(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="frequency_list",
                ),
            ),
            version=1,
        )
        now = datetime(2026, 5, 26, 0, 0, tzinfo=timezone.utc)

        updated_store, updated_item = mark_item_lifecycle(
            store,
            language_pair="en-ja",
            lemma="beta",
            lifecycle_state=SRS_LIFECYCLE_DISCARDED,
            reason="user_blocked",
            now=now,
        )

        self.assertIsNotNone(updated_item)
        self.assertEqual(updated_store.items[0].lifecycle_state, SRS_LIFECYCLE_DISCARDED)
        self.assertEqual(updated_store.items[0].lifecycle_reason, "user_blocked")
        self.assertEqual(updated_store.items[0].lifecycle_updated_at, "2026-05-26T00:00:00Z")

    def test_mark_item_lifecycle_active_clears_reason(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="frequency_list",
                    lifecycle_state=SRS_LIFECYCLE_DISCARDED,
                    lifecycle_reason="user_blocked",
                ),
            ),
            version=1,
        )

        updated_store, updated_item = mark_item_lifecycle(
            store,
            language_pair="en-ja",
            lemma="beta",
            lifecycle_state=SRS_LIFECYCLE_ACTIVE,
            reason="ignored",
        )

        self.assertIsNotNone(updated_item)
        self.assertEqual(updated_store.items[0].lifecycle_state, SRS_LIFECYCLE_ACTIVE)
        self.assertIsNone(updated_store.items[0].lifecycle_reason)

    def test_record_exposure_preserves_existing_word_package(self) -> None:
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
        now = datetime(2026, 2, 3, 12, 0, tzinfo=timezone.utc)
        updated = record_exposure(store, language_pair="en-ja", lemma="所", now=now)
        item = updated.items[0]
        self.assertIsNotNone(item.word_package)
        self.assertEqual(item.word_package["reading"], "ところ")


if __name__ == "__main__":
    unittest.main()
