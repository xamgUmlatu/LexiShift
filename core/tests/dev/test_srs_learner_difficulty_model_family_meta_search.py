from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_model_family_meta_search_en_ja import (  # noqa: E402
    SplitSpec,
    _exact_candidate_rows,
    _leaf_ids_for_values,
    _passes_baseline_constraints,
    _select_family_candidates,
)
from srs_learner_difficulty_model_family_search_en_ja import ModelCandidate  # noqa: E402


class TestSrsLearnerDifficultyModelFamilyMetaSearch(unittest.TestCase):
    def test_leaf_ids_route_stump_missing_left_or_right(self) -> None:
        values = {"frequency": np.array([0.2, 0.8, np.nan], dtype=np.float32)}
        present = {"frequency": np.array([True, True, False], dtype=bool)}

        missing_left = _leaf_ids_for_values(
            root=SplitSpec("frequency", 0.5, True),
            child_side=None,
            child=None,
            values_by_signal=values,
            present_by_signal=present,
        )
        missing_right = _leaf_ids_for_values(
            root=SplitSpec("frequency", 0.5, False),
            child_side=None,
            child=None,
            values_by_signal=values,
            present_by_signal=present,
        )

        self.assertEqual(list(missing_left), [0, 1, 0])
        self.assertEqual(list(missing_right), [0, 1, 1])

    def test_leaf_ids_route_depth2_child_on_left(self) -> None:
        values = {
            "frequency": np.array([0.2, 0.2, 0.8], dtype=np.float32),
            "rare_wago_tail_risk": np.array([0.1, 0.9, 0.9], dtype=np.float32),
        }
        present = {name: np.array([True, True, True], dtype=bool) for name in values}

        leaves = _leaf_ids_for_values(
            root=SplitSpec("frequency", 0.5, False),
            child_side="left",
            child=SplitSpec("rare_wago_tail_risk", 0.5, False),
            values_by_signal=values,
            present_by_signal=present,
        )

        self.assertEqual(list(leaves), [0, 1, 2])

    def test_baseline_constraints_allow_tolerance(self) -> None:
        baseline = {
            "balanced_score": 0.90,
            "bucket_accuracy_score": 0.80,
            "pairwise_order_score": 0.88,
            "beginner_core_score": 0.97,
            "high_tail_score": 0.70,
            "upper_tail_score": 0.90,
        }
        passing = {
            "balanced_score": 0.91,
            "bucket_accuracy_score": 0.795,
            "pairwise_order_score": 0.875,
            "beginner_core_score": 0.97,
            "high_tail_score": 0.70,
            "upper_tail_score": 0.90,
        }
        failing = {**passing, "high_tail_score": 0.69}

        self.assertTrue(_passes_baseline_constraints(passing, baseline_scores=baseline))
        self.assertFalse(_passes_baseline_constraints(failing, baseline_scores=baseline))

    def test_select_family_candidates_uses_leaderboards_and_exact_top(self) -> None:
        candidates = [ModelCandidate(f"candidate_{index}", "family", "base") for index in range(5)]
        report = {
            "leaderboards": {
                "balanced_score": [
                    {"candidate_id": "candidate_3"},
                    {"candidate_id": "candidate_1"},
                ],
                "reviewed_focus_score": [{"candidate_id": "candidate_4"}],
            },
            "exact_top": [
                {"candidate_id": "candidate_0"},
                {"candidate_id": "candidate_2"},
            ],
        }

        selected = _select_family_candidates(
            report,
            family_candidates=candidates,
            candidate_pool_size=4,
            top_per_leaderboard=2,
        )

        self.assertEqual(
            [candidate.candidate_id for candidate in selected],
            ["candidate_0", "candidate_2", "candidate_3", "candidate_1"],
        )

    def test_exact_candidate_rows_preserve_standalone_anchors(self) -> None:
        root_candidates = [
            {
                "candidate_id": "linear_a",
                "tree": {"root": None},
            },
            {
                "candidate_id": "linear_b",
                "tree": {"root": None},
            },
            {
                "candidate_id": "stump_a",
                "tree": {"root": {"signal": "frequency"}},
            },
        ]
        approximate_candidates = [
            {
                "candidate_id": "tree_a",
                "tree": {"root": {"signal": "kango_mid_signal"}},
            },
            {
                "candidate_id": "linear_b",
                "tree": {"root": None},
            },
        ]

        selected = _exact_candidate_rows(
            root_candidates=root_candidates,
            approximate_candidates=approximate_candidates,
            limit=4,
        )

        self.assertEqual(
            [row["candidate_id"] for row in selected],
            ["linear_a", "linear_b", "stump_a", "tree_a"],
        )


if __name__ == "__main__":
    unittest.main()
