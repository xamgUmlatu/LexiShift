from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_DISCARDED,
    SrsItem,
    SrsSettings,
    SrsStore,
)
from lexishift_core.srs.admission_refresh import (  # noqa: E402
    AdmissionRefreshPolicy,
    admission_refresh_result_to_dict,
    apply_admission_refresh,
    plan_admission_refresh,
    preview_browsing_admission_refresh,
)
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BrowsingSignalAggregate,
    BrowsingSignalStore,
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
    def test_plan_caps_capacity_by_active_items_not_due_only(self) -> None:
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)
        future_due = (now + timedelta(days=7)).isoformat()
        store = SrsStore(
            items=tuple(
                SrsItem(
                    item_id=f"en-ja:existing{index}",
                    lemma=f"existing{index}",
                    language_pair="en-ja",
                    source_type="initial_set",
                    next_due=future_due,
                )
                for index in range(3)
            ),
            version=1,
        )
        settings = SrsSettings(max_active_items=3, max_new_items_per_day=4)
        decision = plan_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            events=[],
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
            now=now,
        )

        self.assertEqual(decision.active_count, 3)
        self.assertEqual(decision.due_count, 0)
        self.assertEqual(decision.capacity_budget, 0)
        self.assertEqual(decision.base_admission_budget, 0)
        self.assertEqual(decision.admission_budget, 0)
        self.assertEqual(decision.reason_code, "capacity_exhausted")
        self.assertEqual(decision.active_zero_exposure_zero_feedback, 3)
        self.assertEqual(decision.active_zero_exposure_zero_feedback_age_unknown, 3)
        self.assertEqual(decision.active_stale_zero_exposure_zero_feedback, 0)

    def test_plan_can_scope_capacity_to_active_inventory_ids(self) -> None:
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)
        future_due = (now + timedelta(days=7)).isoformat()
        store = SrsStore(
            items=tuple(
                SrsItem(
                    item_id=f"en-ja:existing{index}",
                    lemma=f"existing{index}",
                    language_pair="en-ja",
                    source_type="initial_set",
                    next_due=future_due,
                )
                for index in range(3)
            ),
            version=1,
        )

        decision = plan_admission_refresh(
            store=store,
            settings=SrsSettings(max_active_items=3, max_new_items_per_day=4),
            pair="en-ja",
            events=[],
            policy=AdmissionRefreshPolicy(
                feedback_window_size=100,
                active_item_ids=("en-ja:existing0", "en-ja:existing2"),
            ),
            now=now,
        )

        self.assertEqual(decision.active_count, 2)
        self.assertEqual(decision.due_count, 0)
        self.assertEqual(decision.capacity_budget, 1)
        self.assertEqual(decision.base_admission_budget, 1)
        self.assertEqual(decision.admission_budget, 1)
        self.assertEqual(decision.reason_code, "normal")
        self.assertEqual(decision.active_zero_exposure_zero_feedback, 2)

    def test_plan_reports_stale_unseen_active_capacity_pressure(self) -> None:
        now = datetime(2026, 5, 26, tzinfo=timezone.utc)
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:stale",
                    lemma="stale",
                    language_pair="en-ja",
                    source_type="initial_set",
                    admitted_at=(now - timedelta(days=9)).isoformat(),
                ),
                SrsItem(
                    item_id="en-ja:fresh",
                    lemma="fresh",
                    language_pair="en-ja",
                    source_type="initial_set",
                    admitted_at=(now - timedelta(days=1)).isoformat(),
                ),
                SrsItem(
                    item_id="en-ja:legacy",
                    lemma="legacy",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-ja:seen",
                    lemma="seen",
                    language_pair="en-ja",
                    source_type="initial_set",
                    admitted_at=(now - timedelta(days=12)).isoformat(),
                    exposures=2,
                ),
            ),
            version=1,
        )
        decision = plan_admission_refresh(
            store=store,
            settings=SrsSettings(max_active_items=4, max_new_items_per_day=4),
            pair="en-ja",
            events=[],
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
            now=now,
        )

        self.assertEqual(decision.reason_code, "capacity_exhausted")
        self.assertEqual(decision.active_zero_exposure_zero_feedback, 3)
        self.assertEqual(decision.active_zero_exposure_zero_feedback_age_unknown, 1)
        self.assertEqual(decision.active_stale_zero_exposure_zero_feedback, 1)
        self.assertEqual(decision.stale_active_age_days, 7)
        self.assertIn("stale, unseen, and unreviewed", " ".join(decision.notes))
        payload = admission_refresh_result_to_dict(
            apply_admission_refresh(
                store=store,
                settings=SrsSettings(max_active_items=4, max_new_items_per_day=4),
                pair="en-ja",
                candidates=_build_candidates(),
                events=[],
                policy=AdmissionRefreshPolicy(feedback_window_size=100),
                now=now,
            )[1]
        )
        self.assertEqual(payload["active_stale_zero_exposure_zero_feedback"], 1)
        self.assertEqual(payload["active_zero_exposure_zero_feedback_age_unknown"], 1)

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
        now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
        updated_store, result = apply_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            candidates=_build_candidates(),
            events=events,
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
            now=now,
        )
        self.assertTrue(result.applied)
        self.assertEqual(result.admitted_count, 2)
        lemmas = {item.lemma for item in updated_store.items if item.language_pair == "en-ja"}
        self.assertIn("beta", lemmas)
        self.assertIn("gamma", lemmas)
        self.assertNotIn("delta", lemmas)
        beta = next(item for item in updated_store.items if item.lemma == "beta")
        self.assertEqual(beta.admitted_at, "2026-05-26T12:00:00Z")

    def test_apply_refresh_tracks_pos_diagnostics_with_allowed_pos(self) -> None:
        store = SrsStore(items=tuple(), version=1)
        settings = SrsSettings(max_active_items=10, max_new_items_per_day=1)
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
        candidates = [
            SelectorCandidate(
                lemma="alpha",
                language_pair="en-ja",
                base_freq=0.95,
                confidence=0.95,
                source_type="frequency_list",
                pos="noun",
            ),
            SelectorCandidate(
                lemma="beta",
                language_pair="en-ja",
                base_freq=0.90,
                confidence=0.90,
                source_type="frequency_list",
                pos="verb",
            ),
            SelectorCandidate(
                lemma="gamma",
                language_pair="en-ja",
                base_freq=0.50,
                confidence=0.50,
                source_type="frequency_list",
                metadata={"pos_mapped": False},
            ),
        ]

        updated_store, result = apply_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            candidates=candidates,
            events=events,
            policy=AdmissionRefreshPolicy(
                feedback_window_size=100,
                allowed_pos={"noun"},
            ),
        )

        self.assertTrue(result.applied)
        self.assertEqual(result.admitted_count, 1)
        self.assertEqual(result.selected_lemmas, ("alpha",))
        self.assertEqual(result.diagnostics.filtered_by_pos, 1)
        self.assertEqual(result.diagnostics.unknown_pos_seen, 1)
        self.assertEqual(result.diagnostics.candidate_pool_effective, 2)
        self.assertEqual(result.diagnostics.admitted_by_pos_bucket.get("noun"), 1)
        self.assertEqual(tuple(result.diagnostics.allowed_pos), ("noun",))
        lemmas = {item.lemma for item in updated_store.items if item.language_pair == "en-ja"}
        self.assertIn("alpha", lemmas)
        self.assertNotIn("beta", lemmas)

    def test_apply_refresh_skips_lifecycle_blocked_lemmas(self) -> None:
        store = SrsStore(items=tuple(), version=1)
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
            policy=AdmissionRefreshPolicy(
                feedback_window_size=100,
                blocked_lemmas={"alpha", "gamma"},
            ),
        )

        self.assertTrue(result.applied)
        self.assertEqual(result.selected_lemmas, ("beta", "delta"))
        self.assertEqual(result.diagnostics.blocked_by_lifecycle, 2)
        self.assertEqual(tuple(result.diagnostics.blocked_lemmas), ("alpha", "gamma"))
        lemmas = {item.lemma for item in updated_store.items if item.language_pair == "en-ja"}
        self.assertNotIn("alpha", lemmas)
        self.assertNotIn("gamma", lemmas)
        self.assertIn("beta", lemmas)
        self.assertIn("delta", lemmas)
        payload = admission_refresh_result_to_dict(result)
        self.assertEqual(payload["diagnostics"]["blocked_by_lifecycle"], 2)
        self.assertEqual(payload["diagnostics"]["blocked_lemmas"], ["alpha", "gamma"])

    def test_apply_refresh_skips_inactive_store_lifecycle_items(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    lifecycle_state=SRS_LIFECYCLE_DISCARDED,
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
        self.assertEqual(result.selected_lemmas, ("beta", "gamma"))
        self.assertEqual(result.diagnostics.blocked_by_lifecycle, 1)
        self.assertEqual(tuple(result.diagnostics.blocked_lemmas), ("alpha",))
        alpha = next(item for item in updated_store.items if item.lemma == "alpha")
        self.assertEqual(alpha.lifecycle_state, SRS_LIFECYCLE_DISCARDED)

    def test_browsing_refresh_preview_does_not_change_actual_selection(self) -> None:
        store = SrsStore(items=tuple(), version=1)
        settings = SrsSettings(max_active_items=10, max_new_items_per_day=4)
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
        candidates = [
            SelectorCandidate(
                lemma="beta",
                language_pair="en-ja",
                base_freq=0.95,
                confidence=0.95,
            ),
            SelectorCandidate(
                lemma="gamma",
                language_pair="en-ja",
                base_freq=0.90,
                confidence=0.90,
            ),
            SelectorCandidate(
                lemma="delta",
                language_pair="en-ja",
                base_freq=0.30,
                confidence=0.90,
            ),
            SelectorCandidate(
                lemma="epsilon",
                language_pair="en-ja",
                base_freq=0.25,
                confidence=0.90,
            ),
            SelectorCandidate(
                lemma="theta",
                language_pair="en-ja",
                base_freq=0.85,
                confidence=0.90,
            ),
            SelectorCandidate(
                lemma="zeta",
                language_pair="en-ja",
                base_freq=0.80,
                confidence=0.90,
            ),
        ]
        browsing_store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "delta": BrowsingSignalAggregate(
                    target_lemma="delta",
                    target_hit_count=100.0,
                ),
                "epsilon": BrowsingSignalAggregate(
                    target_lemma="epsilon",
                    target_hit_count=100.0,
                ),
            },
        )

        updated_store, result = apply_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            candidates=candidates,
            events=events,
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
        )
        preview = preview_browsing_admission_refresh(
            store=store,
            settings=settings,
            pair="en-ja",
            candidates=candidates,
            events=events,
            browsing_store=browsing_store,
            policy=AdmissionRefreshPolicy(feedback_window_size=100),
        )

        self.assertEqual(result.selected_lemmas, ("beta", "gamma", "theta", "zeta"))
        self.assertEqual(
            {item.lemma for item in updated_store.items if item.language_pair == "en-ja"},
            {"beta", "gamma", "theta", "zeta"},
        )
        self.assertFalse(preview["applied_to_actual_admission"])
        self.assertFalse(preview["runtime_srs_mutation"])
        self.assertEqual(preview["neutral_selected_lemmas"], ("beta", "gamma", "theta", "zeta"))
        self.assertIn(
            "delta",
            preview["simulations"]["strong"]["selected_lemmas"],
        )


if __name__ == "__main__":
    unittest.main()
