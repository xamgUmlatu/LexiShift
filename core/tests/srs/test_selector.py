from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.selector import (  # noqa: E402
    SelectorCandidate,
    SelectorConfig,
    SelectorWeights,
    resolve_selection_mass,
    score_candidate,
)


class TestSelectorReadinessMultiplier(unittest.TestCase):
    def test_score_candidate_applies_readiness_metadata(self) -> None:
        scored = score_candidate(
            SelectorCandidate(
                lemma="basic",
                language_pair="en-ja",
                base_freq=0.80,
                metadata={"readiness_multiplier": 0.25},
            ),
            SelectorConfig(
                weights=SelectorWeights(
                    base_freq=1.0,
                    topic_bias=0.0,
                    scarcity_bonus=0.0,
                    user_pref=0.0,
                    confidence=0.0,
                    difficulty_target=0.0,
                )
            ),
        )

        self.assertAlmostEqual(scored.breakdown.weighted_sum, 0.80, places=6)
        self.assertAlmostEqual(scored.breakdown.final_score, 0.20, places=6)
        self.assertIn("readiness_gate", scored.breakdown.penalties)

    def test_selection_mass_applies_readiness_to_frequency_baseline(self) -> None:
        config = SelectorConfig(
            weights=SelectorWeights(
                base_freq=1.0,
                topic_bias=0.0,
                scarcity_bonus=0.0,
                user_pref=0.0,
                confidence=0.0,
                difficulty_target=0.0,
            ),
            sampling_baseline_alpha=0.5,
            sampling_min_mass=0.001,
        )
        scored = score_candidate(
            SelectorCandidate(
                lemma="basic",
                language_pair="en-ja",
                base_freq=1.0,
                metadata={"readiness_multiplier": 0.01},
            ),
            config,
        )

        self.assertAlmostEqual(resolve_selection_mass(scored, config), 0.01, places=6)


if __name__ == "__main__":
    unittest.main()
