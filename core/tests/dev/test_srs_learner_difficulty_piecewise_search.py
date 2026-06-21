from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _segment_ids,
    _target_curve_normalize,
)


class TestSrsLearnerDifficultyPiecewiseSearch(unittest.TestCase):
    def test_segment_ids_use_frequency_boundaries(self) -> None:
        values = np.array([0.05, 0.35, 0.45, 0.70, 0.90], dtype=np.float32)

        segments = _segment_ids(values, (0.45, 0.85))

        self.assertEqual(list(segments), [0, 0, 1, 1, 2])

    def test_target_curve_normalize_assigns_positions_by_raw_order(self) -> None:
        raw = np.array([0.8, 0.2, 0.5], dtype=np.float32)
        positions = np.array([0.1, 0.5, 0.9], dtype=np.float32)

        normalized = _target_curve_normalize(raw, target_positions=positions)

        self.assertAlmostEqual(float(normalized[1]), 0.1)
        self.assertAlmostEqual(float(normalized[2]), 0.5)
        self.assertAlmostEqual(float(normalized[0]), 0.9)

    def test_difficulty_metrics_score_numeric_order_and_segments(self) -> None:
        expected = np.array([0.05, 0.35, 0.92, np.nan], dtype=np.float32)
        observed = np.array([0.06, 0.40, 0.91, 0.3], dtype=np.float32)

        metrics = _difficulty_metrics(
            expected_values=expected,
            observed_values=observed,
            expected_bands=("beginner", "beginner", "advanced", ""),
            labels=("名前/なまえ", "料理/りょうり", "韜晦/とうかい", "七百/ななひゃく"),
        )

        self.assertEqual(metrics["difficulty_value"]["evaluated_count"], 3)
        self.assertEqual(metrics["difficulty_bucket"]["accuracy"], 1.0)
        self.assertEqual(metrics["pairwise_order"]["accuracy"], 1.0)
        self.assertEqual(metrics["segments"]["beginner_core"]["pass_count"], 1)
        self.assertEqual(metrics["segments"]["upper_tail"]["pass_count"], 1)

    def test_difficulty_metrics_score_default_decision_from_candidate_states(self) -> None:
        expected = np.array([0.05, 0.35, 0.92], dtype=np.float32)
        observed = np.array([0.06, 0.40, 0.91], dtype=np.float32)

        metrics = _difficulty_metrics(
            expected_values=expected,
            observed_values=observed,
            expected_bands=("beginner", "beginner", "advanced"),
            expected_candidate_states=(
                "normal_vocab",
                "grammar_item",
                "normal_vocab",
            ),
            observed_candidate_states=(
                "normal_vocab",
                "normal_vocab",
                "grammar_item",
            ),
            labels=("名前/なまえ", "的/てき", "韜晦/とうかい"),
        )

        default_decision = metrics["default_vocab_decision"]
        self.assertEqual(default_decision["evaluated_count"], 3)
        self.assertEqual(default_decision["true_default_accept"], 1)
        self.assertEqual(default_decision["false_default_admit"], 1)
        self.assertEqual(default_decision["false_default_suppress"], 1)
        self.assertAlmostEqual(default_decision["accuracy"], 1 / 3, places=6)
        self.assertAlmostEqual(metrics["scores"]["default_decision_score"], 1 / 3, places=6)


if __name__ == "__main__":
    unittest.main()
