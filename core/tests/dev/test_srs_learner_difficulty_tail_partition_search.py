from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_tail_partition_search_en_ja import (  # noqa: E402
    _false_tail_adjusted_score,
    _hard_partition_normalize,
    _tail_mask,
    _tail_partition_diagnostics,
)


class TestSrsLearnerDifficultyTailPartitionSearch(unittest.TestCase):
    def test_tail_mask_selects_top_quantile_by_raw_score(self) -> None:
        raw = np.array([0.20, 0.80, 0.10, 0.95, 0.50], dtype=np.float32)

        mask = _tail_mask(raw, 0.40)

        self.assertEqual(mask.tolist(), [False, True, False, True, False])

    def test_hard_partition_assigns_every_row_once(self) -> None:
        base_raw = np.array([0.10, 0.20, 0.90, 0.40, 0.50], dtype=np.float32)
        tail_raw = np.array([0.00, 1.00, 0.30, 0.80, 0.70], dtype=np.float32)
        tail_mask = np.array([False, True, False, True, False])
        positions = np.array([0.00, 0.25, 0.50, 0.75, 1.00], dtype=np.float32)

        normalized = _hard_partition_normalize(
            base_raw,
            tail_raw,
            tail_mask=tail_mask,
            target_positions=positions,
        )

        self.assertEqual(sorted(float(value) for value in normalized), positions.tolist())
        self.assertAlmostEqual(float(normalized[0]), 0.00)
        self.assertAlmostEqual(float(normalized[4]), 0.25)
        self.assertAlmostEqual(float(normalized[2]), 0.50)
        self.assertAlmostEqual(float(normalized[3]), 0.75)
        self.assertAlmostEqual(float(normalized[1]), 1.00)

    def test_tail_partition_diagnostics_define_precision_recall_and_false_tail(self) -> None:
        tail_mask = np.array([False, True, False, True, True], dtype=bool)
        context = {
            "component_indices": np.array([0, 1, 2, 3, 4, -1], dtype=np.int64),
            "expected_values": np.array(
                [0.10, 0.90, 0.95, 0.75, 0.88, 0.99],
                dtype=np.float32,
            ),
            "labels": [
                "easy/a",
                "upper/b",
                "high/c",
                "mid/d",
                "upper/e",
                "missing/f",
            ],
        }

        diagnostics = _tail_partition_diagnostics(tail_mask, calibration_context=context)

        self.assertEqual(diagnostics["selected_calibration_count"], 3)
        self.assertEqual(diagnostics["upper_tail_label_count"], 3)
        self.assertEqual(diagnostics["upper_tail_hit_count"], 2)
        self.assertEqual(diagnostics["upper_tail_recall"], 0.666667)
        self.assertEqual(diagnostics["upper_tail_precision"], 0.666667)
        self.assertEqual(diagnostics["high_tail_label_count"], 1)
        self.assertEqual(diagnostics["high_tail_hit_count"], 0)
        self.assertEqual(diagnostics["false_tail_under_0_80_count"], 1)
        self.assertEqual(diagnostics["false_tail_under_0_80_rate"], 0.333333)

    def test_false_tail_adjusted_score_penalizes_selected_mid_tail_rows(self) -> None:
        score = _false_tail_adjusted_score(
            {"balanced_score": 0.920372},
            {"false_tail_under_0_80_rate": 0.115385},
            0.10,
        )

        self.assertEqual(score, 0.908833)


if __name__ == "__main__":
    unittest.main()
