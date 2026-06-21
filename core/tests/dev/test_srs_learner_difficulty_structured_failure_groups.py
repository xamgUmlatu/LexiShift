from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_structured_failure_groups_en_ja import (  # noqa: E402
    GroupSpec,
    GroupTerm,
    _bounded_residual_delta,
    _context_group_mask,
    _enrichment,
    _fold_training_selector_events,
    _group_mask,
    _passes_profile,
    _scope_for_count,
)


@dataclass(frozen=True)
class FakeContext:
    component_indices: object
    expected_values: object


class TestSrsLearnerDifficultyStructuredFailureGroups(unittest.TestCase):
    def test_group_mask_applies_min_and_max_terms(self) -> None:
        spec = GroupSpec(
            "middle_kango",
            "test",
            (
                GroupTerm("kango", min_value=0.5),
                GroupTerm("frequency", max_value=0.8),
            ),
        )
        mask = _group_mask(
            spec,
            {
                "kango": np.asarray([0.7, 0.3, 0.9], dtype=np.float32),
                "frequency": np.asarray([0.6, 0.6, 0.95], dtype=np.float32),
            },
        )

        self.assertEqual(mask.tolist(), [True, False, False])

    def test_context_group_mask_projects_component_rows(self) -> None:
        context = FakeContext(
            component_indices=np.asarray([2, -1, 0, 1], dtype=np.int64),
            expected_values=np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float32),
        )

        mask = _context_group_mask(context, np.asarray([True, False, True]))

        self.assertEqual(mask.tolist(), [True, False, True, False])

    def test_bounded_residual_delta_uses_median_and_cap(self) -> None:
        context = FakeContext(
            component_indices=np.asarray([0, 1, 2, 3], dtype=np.int64),
            expected_values=np.asarray([0.9, 0.8, 0.8, 0.1], dtype=np.float32),
        )
        values = np.asarray([0.1, 0.2, 0.3, 0.1], dtype=np.float32)

        delta = _bounded_residual_delta(
            context,
            values,
            np.asarray([True, True, True, False]),
            max_abs=0.3,
            min_support=2,
        )

        self.assertEqual(delta, 0.3)

    def test_enrichment_reports_precision_recall_and_lift(self) -> None:
        metrics = _enrichment(
            selected=np.asarray([True, True, False, False]),
            positive=np.asarray([True, False, True, False]),
        )

        self.assertEqual(metrics["selected_positive_count"], 1)
        self.assertEqual(metrics["positive_count"], 2)
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 0.5)
        self.assertEqual(metrics["lift"], 1.0)

    def test_fold_training_selector_uses_train_delta_per_fold(self) -> None:
        events = _fold_training_selector_events(
            [
                {
                    "group_id": "a",
                    "source": "test",
                    "residual_structure_score": 0.1,
                    "folds": [
                        _fold(1, train=0.02, validation=0.03, holdout=0.04),
                        _fold(2, train=-0.01, validation=0.01, holdout=0.02),
                    ],
                },
                {
                    "group_id": "b",
                    "source": "test",
                    "residual_structure_score": 0.2,
                    "folds": [
                        _fold(1, train=0.01, validation=0.06, holdout=0.07),
                        _fold(2, train=0.04, validation=0.05, holdout=0.06),
                    ],
                },
            ]
        )

        self.assertEqual([event["group_id"] for event in events], ["a", "b"])
        self.assertEqual([event["validation_score_delta"] for event in events], [0.03, 0.05])

    def test_scope_for_count_separates_narrow_medium_and_broad(self) -> None:
        self.assertEqual(_scope_for_count(10_000), "narrow")
        self.assertEqual(_scope_for_count(10_001), "medium")
        self.assertEqual(_scope_for_count(25_001), "broad")

    def test_validation_positive_mae_safe_profile_requires_mae_safety(self) -> None:
        row = {
            "eligible": True,
            "full_vocab_count": 5000,
            "fold_summary": {
                "mean_validation_score_delta": 0.01,
                "min_validation_score_delta": 0.0,
                "mean_validation_normal_vocab_mae_reduction": -0.001,
                "valid_fold_count": 5,
            },
        }

        self.assertTrue(_passes_profile(row, "validation_positive"))
        self.assertFalse(_passes_profile(row, "validation_positive_mae_safe"))


def _fold(
    fold: int,
    *,
    train: float,
    validation: float,
    holdout: float,
) -> dict[str, object]:
    return {
        "fold": fold,
        "delta": 0.1,
        "train_score_delta": train,
        "validation_score_delta": validation,
        "holdout_score_delta": holdout,
    }


if __name__ == "__main__":
    unittest.main()
