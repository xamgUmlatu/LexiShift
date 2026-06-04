from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsHistoryEntry, SrsItem, SrsStore  # noqa: E402
from lexishift_core.srs.active_rotation import (  # noqa: E402
    active_rotation_release_result_to_dict,
    is_active_rotation_release_candidate,
    plan_active_rotation_release,
)


def _history(now: datetime, count: int) -> tuple[SrsHistoryEntry, ...]:
    return tuple(
        SrsHistoryEntry(ts=(now - timedelta(days=count - index)).isoformat(), rating="good")
        for index in range(count)
    )


class TestSrsActiveRotation(unittest.TestCase):
    def test_release_candidate_requires_review_history_and_far_future_due_date(self) -> None:
        now = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
        candidate = SrsItem(
            item_id="en-ja:alpha",
            lemma="alpha",
            language_pair="en-ja",
            source_type="initial_set",
            scheduler_state="review",
            next_due=(now + timedelta(days=14)).isoformat(),
            history=_history(now, 4),
        )
        still_learning = SrsItem(
            item_id="en-ja:beta",
            lemma="beta",
            language_pair="en-ja",
            source_type="initial_set",
            scheduler_state="learning",
            next_due=(now + timedelta(days=14)).isoformat(),
            history=_history(now, 4),
        )
        due_soon = SrsItem(
            item_id="en-ja:gamma",
            lemma="gamma",
            language_pair="en-ja",
            source_type="initial_set",
            scheduler_state="review",
            next_due=(now + timedelta(days=2)).isoformat(),
            history=_history(now, 4),
        )

        self.assertTrue(is_active_rotation_release_candidate(candidate, now=now))
        self.assertFalse(is_active_rotation_release_candidate(still_learning, now=now))
        self.assertFalse(is_active_rotation_release_candidate(due_soon, now=now))

    def test_plan_parks_release_candidates_without_removing_store_records(self) -> None:
        now = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    scheduler_state="review",
                    next_due=(now + timedelta(days=14)).isoformat(),
                    history=_history(now, 4),
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                    scheduler_state="review",
                    next_due=(now + timedelta(days=1)).isoformat(),
                    history=_history(now, 4),
                ),
            ),
            version=1,
        )

        result = plan_active_rotation_release(
            store=store,
            pair="en-ja",
            active_item_ids=("en-ja:alpha", "en-ja:beta"),
            now=now,
        )

        self.assertEqual(tuple(result.released_item_ids), ("en-ja:alpha",))
        self.assertEqual(tuple(result.released_lemmas), ("alpha",))
        self.assertEqual(tuple(result.active_item_ids_after), ("en-ja:beta",))
        self.assertEqual({item.lemma for item in store.items}, {"alpha", "beta"})
        payload = active_rotation_release_result_to_dict(result)
        self.assertEqual(payload["released_count"], 1)
        self.assertEqual(payload["active_count_after"], 1)


if __name__ == "__main__":
    unittest.main()
