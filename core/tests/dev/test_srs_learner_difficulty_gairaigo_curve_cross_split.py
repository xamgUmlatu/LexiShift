from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_gairaigo_curve_cross_split_en_ja import (  # noqa: E402
    compare_curve_results,
    interpretation,
    rows_for_dataset,
)
from srs_learner_difficulty_qualitative_failure_hypotheses_en_ja import (  # noqa: E402
    MatrixView,
)


class TestSrsLearnerDifficultyGairaigoCurveCrossSplit(unittest.TestCase):
    def test_rows_for_dataset_attaches_anchor_and_gairaigo_signal(self) -> None:
        matrix = MatrixView(
            lemmas=["ダイオード"],
            readings=["だいおーど"],
            candidate_states=["normal_vocab"],
            problem_classes=["normal_vocab"],
            core_ranks=np.asarray([17861.0], dtype=np.float32),
            component_names=["frequency", "wtype_gairaigo_risk"],
            component_values=np.asarray([[0.9, 1.0]], dtype=np.float32),
        )
        rows = [
            {
                "dataset_id": "holdout",
                "target": "scalar_vocab",
                "label": "ダイオード/だいおーど",
                "lemma": "ダイオード",
                "reading": "だいおーど",
                "expected_learner_difficulty": 0.66,
                "primary_pair_status": "jmdict_exact",
            }
        ]

        result = rows_for_dataset(
            rows,
            lookup={("ダイオード", "だいおーど"): 0},
            matrix=matrix,
            anchor_scores=np.asarray([0.32], dtype=np.float32),
        )

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["is_gairaigo"])
        self.assertEqual(result[0]["anchor_direction"], "too_low")
        self.assertEqual(result[0]["anchor_observed"], 0.32)

    def test_compare_curve_results_reports_best_minus_current(self) -> None:
        current = {
            "metrics": {
                "all_rows": {"delta": {"mae_reduction": 0.01}},
                "gairaigo_rows": {"delta": {"mae_reduction": 0.02, "pairwise_delta": 0.03}},
            },
            "counts": {"changed_regressions": 0},
        }
        best = {
            "metrics": {
                "all_rows": {"delta": {"mae_reduction": 0.04}},
                "gairaigo_rows": {"delta": {"mae_reduction": 0.07, "pairwise_delta": 0.08}},
            },
            "counts": {"changed_regressions": 1},
        }

        result = compare_curve_results(best, current)

        self.assertEqual(result["all_mae_reduction_delta"], 0.03)
        self.assertEqual(result["gairaigo_mae_reduction_delta"], 0.05)
        self.assertEqual(result["gairaigo_pairwise_delta_delta"], 0.05)
        self.assertEqual(result["regression_delta"], 1)

    def test_interpretation_blocks_promotion_without_holdout_gairaigo(self) -> None:
        result = interpretation(
            {
                "calibration": {
                    "has_gairaigo_evidence": False,
                    "current_gairaigo_mae_reduction": 0.0,
                    "best_gairaigo_mae_reduction": 0.0,
                    "best_changed_regressions": 0,
                },
                "holdout": {
                    "has_gairaigo_evidence": False,
                    "current_gairaigo_mae_reduction": 0.0,
                    "best_gairaigo_mae_reduction": 0.0,
                    "best_changed_regressions": 0,
                },
                "stitch_validation": {
                    "has_gairaigo_evidence": True,
                    "current_gairaigo_mae_reduction": 0.03,
                    "best_gairaigo_mae_reduction": 0.05,
                    "best_changed_regressions": 0,
                },
            }
        )

        self.assertIsNone(result["validation_best_holdout_nonnegative"])
        self.assertIsNone(result["validation_best_improves_calibration_gairaigo"])
        self.assertEqual(
            result["promotion_readiness"],
            "not_promotable_no_holdout_gairaigo_coverage",
        )
        self.assertEqual(
            result["missing_cross_split_gairaigo_evidence"],
            ["calibration", "holdout"],
        )


if __name__ == "__main__":
    unittest.main()
