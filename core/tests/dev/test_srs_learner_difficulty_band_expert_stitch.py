from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_band_expert_stitch_en_ja import (  # noqa: E402
    DifficultyBandSpec,
    _band_expert_rankings,
    _calibration_observed,
    _selected_expert_ids,
)


class TestSrsLearnerDifficultyBandExpertStitch(unittest.TestCase):
    def test_guarded_expert_stays_explicit_when_no_candidate_passes_guard(self) -> None:
        bands = (DifficultyBandSpec("0.00-0.50", 0.0, 0.5),)
        expected = np.array([0.20, 0.30], dtype=np.float32)
        observed = np.array(
            [
                [0.21, 0.31],
                [0.22, 0.32],
            ],
            dtype=np.float32,
        )
        variant_ids = ("local_best", "local_second")
        variant_records = {
            "local_best": {
                "scores": {
                    "balanced_score": 0.95,
                    "pairwise_order_score": 0.95,
                    "beginner_core_score": 1.0,
                    "upper_tail_score": 1.0,
                    "high_tail_score": 0.60,
                    "default_decision_score": 1.0,
                }
            },
            "local_second": {
                "scores": {
                    "balanced_score": 0.94,
                    "pairwise_order_score": 0.94,
                    "beginner_core_score": 1.0,
                    "upper_tail_score": 1.0,
                    "high_tail_score": 0.65,
                    "default_decision_score": 1.0,
                }
            },
        }
        guard = {
            "balanced_score_min": 0.90,
            "pairwise_order_score_min": 0.90,
            "beginner_core_score_min": 0.95,
            "upper_tail_score_min": 0.80,
            "high_tail_score_min": 0.70,
            "default_decision_score_min": 1.0,
        }

        rankings = _band_expert_rankings(
            expert_bands=bands,
            expected_values=expected,
            observed_matrix=observed,
            variant_ids=variant_ids,
            variant_records=variant_records,
            top_experts_per_band=2,
            guard=guard,
        )

        self.assertIsNone(rankings[0]["best_guarded"])
        self.assertEqual(rankings[0]["top_guarded"], [])
        self.assertEqual(_selected_expert_ids(rankings, "best_guarded", "base"), ("base",))
        self.assertEqual(rankings[0]["best_unconstrained"]["variant_id"], "local_best")

    def test_calibration_observed_uses_matrix_fallback_for_component_missing_rows(self) -> None:
        normalized = np.array([0.10, 0.20, 0.30], dtype=np.float32)
        fallback = np.array([0.91, 0.82, 0.73, 0.64], dtype=np.float32)
        calibration_context = {
            "component_indices": np.array([0, -1, 2, -1], dtype=np.int64),
        }

        observed = _calibration_observed(
            normalized,
            calibration_context,
            fallback_values=fallback,
        )

        self.assertEqual([round(float(value), 2) for value in observed], [0.10, 0.82, 0.30, 0.64])


if __name__ == "__main__":
    unittest.main()
