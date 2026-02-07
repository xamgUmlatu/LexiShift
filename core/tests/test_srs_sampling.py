from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsItem, SrsStore  # noqa: E402
from lexishift_core.srs_sampling import (  # noqa: E402
    SAMPLE_STRATEGY_UNIFORM,
    sample_store_items,
)


def _store_for_sampling() -> SrsStore:
    return SrsStore(
        items=(
            SrsItem(
                item_id="en-ja:alpha",
                lemma="alpha",
                language_pair="en-ja",
                source_type="initial_set",
                difficulty=0.9,
                stability=0.8,
                next_due="2026-02-01T00:00:00Z",
            ),
            SrsItem(
                item_id="en-ja:beta",
                lemma="beta",
                language_pair="en-ja",
                source_type="initial_set",
                difficulty=0.3,
                stability=2.0,
                next_due="2026-03-01T00:00:00Z",
            ),
            SrsItem(
                item_id="en-ja:gamma",
                lemma="gamma",
                language_pair="en-ja",
                source_type="initial_set",
                difficulty=0.5,
                stability=1.0,
                next_due=None,
            ),
            SrsItem(
                item_id="en-en:other",
                lemma="other",
                language_pair="en-en",
                source_type="initial_set",
            ),
        ),
        version=1,
    )


class TestSrsSampling(unittest.TestCase):
    def test_weighted_sampling_returns_pair_scoped_unique_items(self) -> None:
        result = sample_store_items(
            _store_for_sampling(),
            pair="en-ja",
            sample_count=3,
            strategy="weighted_priority",
            seed=7,
        )
        self.assertEqual(result.total_items_for_pair, 3)
        self.assertEqual(result.sample_count_effective, 3)
        self.assertEqual(len(set(result.sampled_lemmas)), 3)
        self.assertTrue(all(lemma in {"alpha", "beta", "gamma"} for lemma in result.sampled_lemmas))

    def test_uniform_strategy_is_respected(self) -> None:
        result = sample_store_items(
            _store_for_sampling(),
            pair="en-ja",
            sample_count=2,
            strategy=SAMPLE_STRATEGY_UNIFORM,
            seed=3,
        )
        self.assertEqual(result.strategy_effective, SAMPLE_STRATEGY_UNIFORM)
        self.assertEqual(result.sample_count_effective, 2)

    def test_invalid_strategy_and_count_fallback(self) -> None:
        result = sample_store_items(
            _store_for_sampling(),
            pair="en-ja",
            sample_count=9999,
            strategy="unknown_strategy",
            seed=1,
        )
        self.assertEqual(result.strategy_effective, "weighted_priority")
        self.assertEqual(result.sample_count_requested, 200)
        self.assertTrue(any("Unknown sample strategy" in note for note in result.notes))
        self.assertTrue(any("sample_count clamped" in note for note in result.notes))


if __name__ == "__main__":
    unittest.main()
