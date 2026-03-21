from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsItem
from lexishift_core.srs.scheduler import (
    RATING_GOOD,
    apply_feedback,
    get_item_retrievability,
    select_active_items,
)


class TestSrsScheduler(unittest.TestCase):
    def test_select_active_items_due_and_pair_filter(self) -> None:
        now = datetime(2026, 2, 2, 12, 0, tzinfo=timezone.utc)
        items = [
            SrsItem(
                item_id="en-en:alpha",
                lemma="alpha",
                language_pair="en-en",
                source_type="frequency",
                next_due=(now - timedelta(days=1)).isoformat(),
            ),
            SrsItem(
                item_id="de-de:beta",
                lemma="beta",
                language_pair="de-de",
                source_type="frequency",
                next_due=(now + timedelta(days=1)).isoformat(),
            ),
            SrsItem(
                item_id="en-en:gamma",
                lemma="gamma",
                language_pair="en-en",
                source_type="frequency",
                next_due=None,
            ),
        ]
        due = select_active_items(items, now=now, max_active=10, allowed_pairs=["en-en"])
        ids = [item.item_id for item in due]
        self.assertIn("en-en:alpha", ids)
        self.assertIn("en-en:gamma", ids)
        self.assertNotIn("de-de:beta", ids)

    def test_apply_feedback_sets_due(self) -> None:
        now = datetime(2026, 2, 2, 12, 0, tzinfo=timezone.utc)
        item = SrsItem(
            item_id="en-en:gloaming",
            lemma="gloaming",
            language_pair="en-en",
            source_type="frequency",
        )
        updated = apply_feedback(item, RATING_GOOD, now=now)
        self.assertIsNotNone(updated.next_due)
        self.assertIsNotNone(updated.last_seen)
        self.assertIsNotNone(updated.last_review)
        self.assertEqual(updated.scheduler_state, "learning")
        self.assertEqual(updated.scheduler_step, 1)
        self.assertEqual(len(updated.history), 1)

    def test_get_item_retrievability_uses_fsrs_state(self) -> None:
        now = datetime(2026, 2, 2, 12, 0, tzinfo=timezone.utc)
        item = SrsItem(
            item_id="en-en:gloaming",
            lemma="gloaming",
            language_pair="en-en",
            source_type="frequency",
        )
        reviewed = apply_feedback(item, RATING_GOOD, now=now)

        retrievability = get_item_retrievability(reviewed, now=now + timedelta(minutes=1))

        self.assertIsNotNone(retrievability)
        self.assertGreaterEqual(float(retrievability or 0.0), 0.0)
        self.assertLessEqual(float(retrievability or 1.0), 1.0)


if __name__ == "__main__":
    unittest.main()
