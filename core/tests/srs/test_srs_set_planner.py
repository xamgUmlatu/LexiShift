from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
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

    def test_profile_bootstrap_is_executable_with_diagnostics(
        self,
    ) -> None:
        plan = build_srs_set_plan(
            SrsSetPlanRequest(
                pair="en-ja",
                strategy="profile_bootstrap",
                objective="bootstrap",
                profile_context={"interests": ["animals"]},
            )
        )
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.execution_mode, "profile_bootstrap")
        self.assertEqual(plan.strategy_effective, "profile_bootstrap")
        self.assertIn("difficulty_preferences", plan.requires_profile_fields)
        self.assertTrue(any("profile-aware candidate scoring" in note for note in plan.notes))
        self.assertIn("profile_bootstrap", plan.diagnostics)
        context = plan.diagnostics["profile_bootstrap"]["context"]
        self.assertEqual(context["active_signals"], ["interests"])
        self.assertEqual(
            context["missing_signals"],
            ["proficiency", "challenge_preference"],
        )

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

    def test_profile_growth_rebalance_is_executable(self) -> None:
        plan = build_srs_set_plan(
            SrsSetPlanRequest(
                pair="en-ja",
                strategy="profile_growth",
                objective="rebalance",
                profile_context={"interests": ["animals"]},
            )
        )
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.execution_mode, "rebalance_preview")
        self.assertEqual(plan.strategy_effective, "profile_growth")
        self.assertEqual(plan.objective, "rebalance")
        self.assertIn("empirical_trends", plan.requires_profile_fields)

    def test_profile_growth_refresh_is_executable(self) -> None:
        plan = build_srs_set_plan(
            SrsSetPlanRequest(
                pair="en-ja",
                strategy="profile_growth",
                objective="refresh",
                profile_context={"interests": ["animals"]},
            )
        )
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.execution_mode, "profile_growth")
        self.assertEqual(plan.strategy_effective, "profile_growth")
        self.assertEqual(plan.objective, "refresh")
        self.assertTrue(any("ongoing refresh/growth admission" in note for note in plan.notes))


if __name__ == "__main__":
    unittest.main()
