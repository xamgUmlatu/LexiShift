from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_DISCARDED,
    SrsItem,
    SrsSettings,
    SrsStore,
)
from lexishift_core.srs.growth import (  # noqa: E402
    SrsGrowthConfig,
    normalize_coverage_scalar,
    plan_srs_growth,
    apply_growth_plan,
)
from lexishift_core.srs.selector import (  # noqa: E402
    SELECTION_POLICY_RESERVED_TOPIC_LANE,
    SelectorCandidate,
    SelectorConfig,
    SelectorWeights,
)


class TestSrsGrowth(unittest.TestCase):
    def test_normalize_coverage_scalar(self) -> None:
        self.assertAlmostEqual(normalize_coverage_scalar(0.35), 0.35)
        self.assertAlmostEqual(normalize_coverage_scalar(35.0), 0.35)
        self.assertAlmostEqual(normalize_coverage_scalar(0.0), 0.0)
        self.assertAlmostEqual(normalize_coverage_scalar(120.0), 1.0)

    def test_plan_growth_with_limits(self) -> None:
        candidates = [
            SelectorCandidate(lemma="alpha", language_pair="en-ja", base_freq=0.9),
            SelectorCandidate(lemma="beta", language_pair="en-ja", base_freq=0.8),
            SelectorCandidate(lemma="gamma", language_pair="en-ja", base_freq=0.7),
            SelectorCandidate(lemma="delta", language_pair="en-ja", base_freq=0.6),
        ]
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="frequency_list",
                ),
            ),
            version=1,
        )
        settings = SrsSettings(coverage_scalar=0.5, max_new_items_per_day=2)

        plan = plan_srs_growth(candidates, store=store, settings=settings, allowed_pairs=["en-ja"])
        self.assertEqual(plan.pool_size, 4)
        self.assertEqual(plan.existing_count, 1)
        self.assertEqual(plan.target_size, 2)
        self.assertEqual(plan.add_count, 1)
        self.assertEqual(len(plan.selected), 1)
        self.assertEqual(plan.selected[0].lemma, "beta")

    def test_apply_growth_plan(self) -> None:
        candidates = [
            SelectorCandidate(
                lemma="alpha",
                language_pair="en-ja",
                base_freq=0.9,
                metadata={
                    "word_package": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "alpha",
                        "reading": "alpha",
                        "script_forms": {"surface": "alpha"},
                        "source": {"provider": "seed"},
                    }
                },
            ),
            SelectorCandidate(lemma="beta", language_pair="en-ja", base_freq=0.8),
        ]
        store = SrsStore(items=tuple(), version=1)
        settings = SrsSettings(coverage_scalar=1.0, max_new_items_per_day=5)
        plan = plan_srs_growth(candidates, store=store, settings=settings, allowed_pairs=["en-ja"])
        now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
        updated = apply_growth_plan(store, plan, now=now)

        self.assertEqual(len(updated.items), 2)
        ids = {item.item_id for item in updated.items}
        self.assertIn("en-ja:alpha", ids)
        self.assertIn("en-ja:beta", ids)
        alpha = next(item for item in updated.items if item.lemma == "alpha")
        self.assertIsNotNone(alpha.word_package)
        self.assertEqual(alpha.admitted_at, "2026-05-26T12:00:00Z")

    def test_plan_growth_respects_allowed_pos(self) -> None:
        candidates = [
            SelectorCandidate(lemma="alpha", language_pair="en-ja", base_freq=0.9, pos="noun"),
            SelectorCandidate(lemma="beta", language_pair="en-ja", base_freq=0.8, pos="verb"),
        ]
        store = SrsStore(items=tuple(), version=1)
        settings = SrsSettings(coverage_scalar=1.0, max_new_items_per_day=5)

        plan = plan_srs_growth(
            candidates,
            store=store,
            settings=settings,
            allowed_pairs=["en-ja"],
            allowed_pos={"noun"},
        )
        self.assertEqual(plan.pool_size, 2)
        self.assertEqual(plan.filtered_size, 1)
        self.assertEqual(len(plan.selected), 1)
        self.assertEqual(plan.selected[0].lemma, "alpha")

    def test_plan_growth_excludes_inactive_lifecycle_items_without_counting_capacity(
        self,
    ) -> None:
        candidates = [
            SelectorCandidate(lemma="alpha", language_pair="en-ja", base_freq=0.9),
            SelectorCandidate(lemma="beta", language_pair="en-ja", base_freq=0.8),
            SelectorCandidate(lemma="gamma", language_pair="en-ja", base_freq=0.7),
        ]
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="frequency_list",
                    lifecycle_state=SRS_LIFECYCLE_DISCARDED,
                ),
            ),
            version=1,
        )
        settings = SrsSettings(coverage_scalar=1.0, max_new_items_per_day=5)

        plan = plan_srs_growth(candidates, store=store, settings=settings, allowed_pairs=["en-ja"])

        self.assertEqual(plan.existing_count, 0)
        self.assertEqual(plan.filtered_size, 2)
        self.assertEqual(tuple(candidate.lemma for candidate in plan.selected), ("beta", "gamma"))

    def test_plan_growth_respects_reserved_topic_lane_selection_policy(self) -> None:
        candidates = [
            SelectorCandidate(lemma="alpha", language_pair="en-ja", base_freq=0.99),
            SelectorCandidate(lemma="beta", language_pair="en-ja", base_freq=0.98),
            SelectorCandidate(lemma="gamma", language_pair="en-ja", base_freq=0.97),
            SelectorCandidate(
                lemma="animal",
                language_pair="en-ja",
                base_freq=0.40,
                topic_bias=1.0,
            ),
        ]
        store = SrsStore(items=tuple(), version=1)
        settings = SrsSettings(coverage_scalar=1.0, max_new_items_per_day=2)

        plan = plan_srs_growth(
            candidates,
            store=store,
            settings=settings,
            config=SrsGrowthConfig(
                max_new_items=2,
                selector_config=SelectorConfig(
                    selection_policy=SELECTION_POLICY_RESERVED_TOPIC_LANE,
                    weights=SelectorWeights(base_freq=1.0, topic_bias=0.01),
                    topic_lane_max_share=0.5,
                    topic_lane_min_window=4,
                ),
            ),
            allowed_pairs=["en-ja"],
        )

        self.assertEqual(tuple(candidate.lemma for candidate in plan.selected), ("animal", "alpha"))


if __name__ == "__main__":
    unittest.main()
