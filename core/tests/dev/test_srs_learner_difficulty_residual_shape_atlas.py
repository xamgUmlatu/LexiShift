from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_residual_shape_atlas_en_ja import (  # noqa: E402
    BaseBand,
    CompositeCell,
    ShapeCell,
    _apply_composite_deltas,
    _cell_mask,
    _dedupe_reports_by_mask,
    _parse_base_bands,
    _stable_selector_score,
)
from srs_learner_difficulty_structured_failure_groups_en_ja import (  # noqa: E402
    GroupSpec,
)


class TestSrsLearnerDifficultyResidualShapeAtlas(unittest.TestCase):
    def test_cell_mask_uses_half_open_bands_except_last(self) -> None:
        group = GroupSpec("all", "test", ())
        old_values = np.asarray([0.19, 0.20, 0.39, 0.40, 1.0], dtype=np.float32)
        group_mask = np.asarray([True, True, True, True, True])

        first = ShapeCell(
            cell_id="first",
            group=group,
            base_band=BaseBand("0p20_0p40", 0.20, 0.40),
        )
        last = ShapeCell(
            cell_id="last",
            group=group,
            base_band=BaseBand("0p40_1p00", 0.40, 1.00, is_last=True),
        )

        self.assertEqual(
            _cell_mask(first, group_mask, old_values).tolist(),
            [
                False,
                True,
                True,
                False,
                False,
            ],
        )
        self.assertEqual(
            _cell_mask(last, group_mask, old_values).tolist(),
            [
                False,
                False,
                False,
                True,
                True,
            ],
        )

    def test_composite_deltas_stack_but_clip_total_shift(self) -> None:
        values = np.asarray([0.50, 0.50, 0.50], dtype=np.float32)
        cells = (
            CompositeCell(
                "raise_left",
                0.15,
                np.asarray([True, True, False]),
            ),
            CompositeCell(
                "raise_edges",
                0.15,
                np.asarray([True, False, True]),
            ),
            CompositeCell(
                "lower_middle",
                -0.10,
                np.asarray([False, True, False]),
            ),
        )

        adjusted, summary = _apply_composite_deltas(values, cells, max_total_abs=0.20)

        self.assertTrue(np.allclose(adjusted, [0.70, 0.55, 0.65]))
        self.assertEqual(summary["touched_count"], 3)
        self.assertEqual(summary["overlap_count"], 2)
        self.assertEqual(summary["positive_shift_count"], 3)

    def test_parse_base_bands_marks_only_final_band_inclusive(self) -> None:
        bands = _parse_base_bands("0.00:0.50,0.50:1.00")

        self.assertFalse(bands[0].is_last)
        self.assertTrue(bands[1].is_last)
        self.assertEqual(bands[0].band_id, "0p00_0p50")

    def test_stable_selector_score_requires_validation_and_mae_safety(self) -> None:
        row = {
            "eligible": True,
            "full_vocab_count": 500,
            "fold_summary": {
                "mean_validation_score_delta": 0.02,
                "min_validation_score_delta": 0.0,
                "mean_validation_normal_vocab_mae_reduction": 0.01,
                "valid_fold_count": 5,
            },
        }
        unsafe = {
            **row,
            "fold_summary": {
                **row["fold_summary"],
                "mean_validation_normal_vocab_mae_reduction": -0.01,
            },
        }

        self.assertIsNotNone(_stable_selector_score(row))
        self.assertIsNone(_stable_selector_score(unsafe))

    def test_dedupe_reports_by_mask_removes_equivalent_threshold_aliases(self) -> None:
        rows = ({"cell_id": "a"}, {"cell_id": "b"}, {"cell_id": "c"})
        cell_masks = {
            "a": np.asarray([True, False, True]),
            "b": np.asarray([True, False, True]),
            "c": np.asarray([False, True, True]),
        }

        deduped = _dedupe_reports_by_mask(rows, cell_masks)

        self.assertEqual([row["cell_id"] for row in deduped], ["a", "c"])


if __name__ == "__main__":
    unittest.main()
