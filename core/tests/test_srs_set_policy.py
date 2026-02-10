from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.set_policy import (  # noqa: E402
    DEFAULT_BOOTSTRAP_TOP_N,
    DEFAULT_INITIAL_ACTIVE_COUNT,
    resolve_set_sizing_policy,
)


class TestSrsSetPolicy(unittest.TestCase):
    def test_defaults_when_values_missing(self) -> None:
        policy = resolve_set_sizing_policy(
            bootstrap_top_n=None,
            initial_active_count=None,
            max_active_items_hint=None,
        )
        self.assertEqual(policy.bootstrap_top_n_effective, DEFAULT_BOOTSTRAP_TOP_N)
        self.assertEqual(policy.initial_active_count_effective, DEFAULT_INITIAL_ACTIVE_COUNT)
        self.assertIsNone(policy.max_active_items_hint)
        self.assertTrue(any("bootstrap_top_n missing/invalid" in note for note in policy.notes))
        self.assertTrue(any("initial_active_count missing/invalid" in note for note in policy.notes))

    def test_initial_active_defaults_to_hint_when_available(self) -> None:
        policy = resolve_set_sizing_policy(
            bootstrap_top_n=1200,
            initial_active_count=None,
            max_active_items_hint=55,
        )
        self.assertEqual(policy.bootstrap_top_n_effective, 1200)
        self.assertEqual(policy.max_active_items_hint, 55)
        self.assertEqual(policy.initial_active_count_effective, 55)

    def test_clamps_values_and_initial_never_exceeds_bootstrap(self) -> None:
        policy = resolve_set_sizing_policy(
            bootstrap_top_n=100,
            initial_active_count=9999,
            max_active_items_hint=9999,
        )
        self.assertEqual(policy.bootstrap_top_n_effective, 200)
        self.assertEqual(policy.max_active_items_hint, 5000)
        self.assertEqual(policy.initial_active_count_effective, 200)
        self.assertTrue(any("bootstrap_top_n clamped" in note for note in policy.notes))
        self.assertTrue(any("initial_active_count clamped" in note for note in policy.notes))
        self.assertTrue(
            any(
                "initial_active_count exceeded bootstrap_top_n" in note
                for note in policy.notes
            )
        )

    def test_invalid_inputs_fall_back_to_defaults(self) -> None:
        policy = resolve_set_sizing_policy(
            bootstrap_top_n="not-a-number",
            initial_active_count="invalid",
            max_active_items_hint=0,
        )
        self.assertEqual(policy.bootstrap_top_n_effective, DEFAULT_BOOTSTRAP_TOP_N)
        self.assertEqual(policy.initial_active_count_effective, DEFAULT_INITIAL_ACTIVE_COUNT)
        self.assertIsNone(policy.max_active_items_hint)


if __name__ == "__main__":
    unittest.main()
