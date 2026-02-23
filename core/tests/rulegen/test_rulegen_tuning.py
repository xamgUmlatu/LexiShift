from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.tuning import (  # noqa: E402
    RulegenTuningOverrides,
    resolve_pair_rulegen_tuning,
    resolve_rulegen_tuning,
    rulegen_tuning_overrides_to_dict,
)


class TestRulegenTuning(unittest.TestCase):
    def test_resolves_pair_defaults_without_overrides(self) -> None:
        defaults = resolve_pair_rulegen_tuning("en-es")
        resolved = resolve_rulegen_tuning("en-es")

        self.assertEqual(resolved.pair, "en-es")
        self.assertAlmostEqual(resolved.confidence_threshold, defaults.confidence_threshold, places=6)
        self.assertEqual(resolved.max_definitions_per_target, defaults.max_definitions_per_target)
        self.assertEqual(resolved.max_rules_per_target, defaults.max_rules_per_target)
        self.assertAlmostEqual(
            resolved.scoring.weights.dict_priority,
            defaults.scoring.weights.dict_priority,
            places=6,
        )
        self.assertTrue(resolved.scoring.pos_match.enabled)

    def test_overrides_replace_pair_defaults(self) -> None:
        resolved = resolve_rulegen_tuning(
            "en-es",
            overrides=RulegenTuningOverrides(
                confidence_threshold=0.25,
                max_definitions_per_target=2,
                max_rules_per_target=5,
                pos_scoring_enabled=False,
                pos_exact_match_bonus=2.0,
                pos_compatible_match_bonus=0.3,
                score_weight_dict_priority=0.9,
                score_weight_pos_match=0.4,
            ),
        )

        self.assertAlmostEqual(resolved.confidence_threshold, 0.25, places=6)
        self.assertEqual(resolved.max_definitions_per_target, 2)
        self.assertEqual(resolved.max_rules_per_target, 5)
        self.assertFalse(resolved.scoring.pos_match.enabled)
        self.assertAlmostEqual(resolved.scoring.pos_match.exact_match_bonus, 2.0, places=6)
        self.assertAlmostEqual(resolved.scoring.pos_match.compatible_match_bonus, 0.3, places=6)
        self.assertAlmostEqual(resolved.scoring.weights.dict_priority, 0.9, places=6)
        self.assertAlmostEqual(resolved.scoring.weights.pos_match, 0.4, places=6)

    def test_non_positive_caps_disable_limiters(self) -> None:
        resolved = resolve_rulegen_tuning(
            "en-es",
            overrides=RulegenTuningOverrides(
                max_definitions_per_target=0,
                max_rules_per_target=0,
            ),
        )
        self.assertIsNone(resolved.max_definitions_per_target)
        self.assertIsNone(resolved.max_rules_per_target)

    def test_overrides_dict_omits_none(self) -> None:
        payload = rulegen_tuning_overrides_to_dict(
            RulegenTuningOverrides(score_weight_pos_match=0.3)
        )
        self.assertEqual(payload, {"score_weight_pos_match": 0.3})


if __name__ == "__main__":
    unittest.main()
