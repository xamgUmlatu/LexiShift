from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsItem, SrsSettings, SrsStore  # noqa: E402
from lexishift_core.srs.admission_refresh import (  # noqa: E402
    AdmissionRefreshPolicy,
    apply_admission_refresh,
    plan_admission_refresh,
)
from lexishift_core.srs.selector import SelectorCandidate  # noqa: E402
from lexishift_core.srs.signal_queue import SrsSignalEvent  # noqa: E402


def _build_candidates() -> list[SelectorCandidate]:
    return [
        SelectorCandidate(
            lemma="alpha",
            language_pair="en-ja",
            base_freq=0.95,
            confidence=0.95,
            source_type="frequency_list",
        ),
        SelectorCandidate(
            lemma="beta",
            language_pair="en-ja",
            base_freq=0.90,
            confidence=0.90,
            source_type="frequency_list",
        ),
        SelectorCandidate(
            lemma="gamma",
            language_pair="en-ja",
            base_freq=0.80,
            confidence=0.80,
            source_type="frequency_list",
        ),
        SelectorCandidate(
            lemma="delta",
            language_pair="en-ja",
            base_freq=0.70,
            confidence=0.70,
            source_type="frequency_list",
        ),
    ]


class TestSrsAdmissionRefresh(unittest.TestCase):
    def test_plan_reduces_budget_for_mid_retention(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:existing",
                    lemma="existing",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
            ),
            version=1,
        )
        settings = SrsSettings(max_active_items=10, max_new_items_per_day=6)
        events = []
        ratings = ["good", "good", "good", "good", "easy", "good", "hard", "hard", "again", "again"]
        for index, rating in enumerate(ratings):
            events.append(
                SrsSignalEvent(
                    event_type="feedback",
                    pair="en-ja",
                    lemma=f"lemma{index}",
                    source_type="extension",
                    rating=rating,
                )
            )
        decision = plan_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            events=events,
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
        )
        self.assertEqual(decision.base_admission_budget, 6)
        self.assertEqual(decision.admission_budget, 3)
        self.assertEqual(decision.reason_code, "retention_mid")

    def test_plan_stops_budget_for_low_retention(self) -> None:
        store = SrsStore(items=tuple(), version=1)
        settings = SrsSettings(max_active_items=10, max_new_items_per_day=6)
        events = []
        ratings = ["again", "hard"] * 6
        for index, rating in enumerate(ratings):
            events.append(
                SrsSignalEvent(
                    event_type="feedback",
                    pair="en-ja",
                    lemma=f"lemma{index}",
                    source_type="extension",
                    rating=rating,
                )
            )
        decision = plan_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            events=events,
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
        )
        self.assertEqual(decision.base_admission_budget, 6)
        self.assertEqual(decision.admission_budget, 0)
        self.assertEqual(decision.reason_code, "retention_low")

    def test_apply_refresh_admits_up_to_budget(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
            ),
            version=1,
        )
        settings = SrsSettings(max_active_items=10, max_new_items_per_day=2)
        events = [
            SrsSignalEvent(
                event_type="feedback",
                pair="en-ja",
                lemma=f"lemma{index}",
                source_type="extension",
                rating="good",
            )
            for index in range(10)
        ]
        updated_store, result = apply_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            candidates=_build_candidates(),
            events=events,
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
        )
        self.assertTrue(result.applied)
        self.assertEqual(result.admitted_count, 2)
        lemmas = {item.lemma for item in updated_store.items if item.language_pair == "en-ja"}
        self.assertIn("beta", lemmas)
        self.assertIn("gamma", lemmas)
        self.assertNotIn("delta", lemmas)


if __name__ == "__main__":
    unittest.main()
