from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.set_planner import SrsSetPlanRequest, build_srs_set_plan  # noqa: E402


class TestSrsSetPlanner(unittest.TestCase):
    def test_frequency_bootstrap_is_executable(self) -> None:
        plan = build_srs_set_plan(
            SrsSetPlanRequest(
                pair="en-ja",
                strategy="frequency_bootstrap",
                objective="bootstrap",
            )
        )
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.execution_mode, "frequency_bootstrap")
        self.assertEqual(plan.strategy_effective, "frequency_bootstrap")

    def test_profile_bootstrap_falls_back_to_frequency(self) -> None:
        plan = build_srs_set_plan(
            SrsSetPlanRequest(
                pair="en-ja",
                strategy="profile_bootstrap",
                objective="bootstrap",
                profile_context={"interests": ["animals"]},
            )
        )
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.execution_mode, "frequency_bootstrap")
        self.assertEqual(plan.strategy_effective, "frequency_bootstrap")
        self.assertTrue(any("falling back" in note.lower() for note in plan.notes))

    def test_adaptive_refresh_is_planner_only_for_now(self) -> None:
        plan = build_srs_set_plan(
            SrsSetPlanRequest(
                pair="en-ja",
                strategy="adaptive_refresh",
                objective="refresh",
            )
        )
        self.assertFalse(plan.can_execute)
        self.assertEqual(plan.execution_mode, "planner_only")
        self.assertIn("feedback_signals", plan.requires_profile_fields)


if __name__ == "__main__":
    unittest.main()
