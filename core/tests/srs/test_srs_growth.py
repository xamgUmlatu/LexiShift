from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsItem, SrsSettings, SrsStore  # noqa: E402
from lexishift_core.srs.growth import (  # noqa: E402
    normalize_coverage_scalar,
    plan_srs_growth,
    apply_growth_plan,
)
from lexishift_core.srs.selector import SelectorCandidate  # noqa: E402


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
        updated = apply_growth_plan(store, plan)

        self.assertEqual(len(updated.items), 2)
        ids = {item.item_id for item in updated.items}
        self.assertIn("en-ja:alpha", ids)
        self.assertIn("en-ja:beta", ids)
        alpha = next(item for item in updated.items if item.lemma == "alpha")
        self.assertIsNotNone(alpha.word_package)


if __name__ == "__main__":
    unittest.main()
