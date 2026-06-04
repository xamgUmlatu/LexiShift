from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.auto_refresh import (  # noqa: E402
    SrsAutoRefreshPairState,
    SrsAutoRefreshPolicy,
    SrsAutoRefreshState,
    plan_auto_refresh,
    record_auto_refresh_attempt,
)
from lexishift_core.srs.signal_queue import SrsSignalEvent  # noqa: E402


def _event(index: int, rating: str, *, ts: datetime) -> SrsSignalEvent:
    return SrsSignalEvent(
        event_type="feedback",
        pair="en-ja",
        lemma=f"lemma{index}",
        source_type="extension",
        rating=rating,
        ts=ts.isoformat(),
    )


class TestSrsAutoRefresh(unittest.TestCase):
    def test_plan_requires_feedback_and_good_easy_thresholds(self) -> None:
        now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        events = [
            _event(index, rating, ts=now - timedelta(minutes=index))
            for index, rating in enumerate(
                ["good", "easy", "good", "good", "hard", "again", "easy", "good"]
            )
        ]

        decision = plan_auto_refresh(events, pair="en-ja", now=now)

        self.assertTrue(decision.eligible)
        self.assertEqual(decision.reason_code, "eligible")
        self.assertEqual(decision.feedback_count, 8)
        self.assertEqual(decision.good_easy_count, 6)
        self.assertEqual(decision.required_feedback_events, 8)
        self.assertEqual(decision.required_good_easy_events, 6)

    def test_same_day_repeat_requires_higher_good_easy_since_last_attempt(self) -> None:
        now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        last_attempt = now - timedelta(hours=2)
        state = SrsAutoRefreshPairState(last_attempted_at=last_attempt.isoformat())
        events = [
            _event(index, rating, ts=last_attempt + timedelta(minutes=index + 1))
            for index, rating in enumerate(
                ["good", "easy", "good", "good", "hard", "again", "easy", "good"]
            )
        ]
        policy = SrsAutoRefreshPolicy(cooldown_minutes=90)

        decision = plan_auto_refresh(events, pair="en-ja", state=state, policy=policy, now=now)

        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason_code, "insufficient_good_easy")
        self.assertTrue(decision.attempted_today)
        self.assertEqual(decision.good_easy_count, 6)
        self.assertEqual(decision.required_good_easy_events, 12)

    def test_cooldown_blocks_even_when_thresholds_are_met(self) -> None:
        now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        last_attempt = now - timedelta(minutes=30)
        state = SrsAutoRefreshPairState(last_attempted_at=last_attempt.isoformat())
        events = [
            _event(index, "easy", ts=last_attempt + timedelta(minutes=index + 1))
            for index in range(14)
        ]

        decision = plan_auto_refresh(events, pair="en-ja", state=state, now=now)

        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason_code, "cooldown_active")
        self.assertEqual(decision.cooldown_remaining_minutes, 60)

    def test_record_attempt_updates_attempt_window_without_erasing_prior_apply(self) -> None:
        now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        applied_state = record_auto_refresh_attempt(
            state=record_auto_refresh_attempt(
                state=SrsAutoRefreshState(),
                pair="en-ja",
                now=now - timedelta(hours=3),
                applied=True,
                reason_code="normal",
            ),
            pair="en-ja",
            now=now,
            applied=False,
            reason_code="capacity_exhausted",
        )

        pair_state = dict(applied_state.pairs)["en-ja"]
        self.assertEqual(pair_state.attempt_count, 2)
        self.assertEqual(pair_state.applied_count, 1)
        self.assertEqual(pair_state.last_result_reason, "capacity_exhausted")
        self.assertNotEqual(pair_state.last_applied_at, pair_state.last_attempted_at)


if __name__ == "__main__":
    unittest.main()
