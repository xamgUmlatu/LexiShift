from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsItem, SrsStore  # noqa: E402
from lexishift_core.srs_store_ops import record_exposure, record_feedback  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
