from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_proficiency_ordering_en_ja import LabelContext  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_stability_en_ja import (  # noqa: E402
    _candidate_stability_report,
    _fold_training_selector_events,
    _fold_stability_summary,
    _stratified_fold_masks,
    _stability_candidates,
    _subset_context,
)


class TestSrsLearnerDifficultyProficiencyOrderingStability(unittest.TestCase):
    def test_stratified_fold_masks_cover_rows_once(self) -> None:
        context = _label_context(
            labels=("a", "b", "c", "d", "e", "f"),
            expected_bands=("low", "low", "mid", "mid", "high", "high"),
            expected_states=("normal_vocab",) * 6,
        )

        masks = _stratified_fold_masks(context, fold_count=3)

        stacked = np.stack(masks, axis=0)
        self.assertTrue(np.all(stacked.sum(axis=0) == 1))
        self.assertEqual([int(mask.sum()) for mask in masks], [2, 2, 2])

    def test_subset_context_preserves_selected_rows_and_missing_rows(self) -> None:
        context = _label_context(
            labels=("a", "b", "c"),
            expected_bands=("low", "mid", "high"),
            expected_states=("normal_vocab", "grammar_item", "normal_vocab"),
        )
        context = LabelContext(
            **{
                **context.__dict__,
                "component_indices": np.array([0, -1, 2], dtype=np.int64),
            }
        )

        subset = _subset_context(
            context,
            np.array([False, True, True], dtype=bool),
            context_id="fold",
        )

        self.assertEqual(subset.labels, ("b", "c"))
        self.assertEqual(list(subset.component_indices), [-1, 2])
        self.assertEqual(subset.missing_rows, ({"label": "b", "row_index": 0},))

    def test_fold_stability_summary_computes_mean_min_and_std(self) -> None:
        summary = _fold_stability_summary(
            [
                _fold_report(score=0.8),
                _fold_report(score=0.6),
                _fold_report(score=1.0),
            ]
        )

        self.assertEqual(summary["mean_score"], 0.8)
        self.assertEqual(summary["min_score"], 0.6)
        self.assertAlmostEqual(float(summary["score_std"]), 0.163299)

    def test_candidate_stability_penalizes_full_calibration_optimism(self) -> None:
        stable = _candidate_report(
            full_score=0.8,
            fold_scores=(0.79, 0.8, 0.81),
        )
        optimistic = _candidate_report(
            full_score=0.95,
            fold_scores=(0.79, 0.8, 0.81),
        )

        self.assertGreater(
            float(stable["stability_selector_score"]),
            float(optimistic["stability_selector_score"]),
        )

    def test_stability_candidates_parse_formula_rows(self) -> None:
        candidates = _stability_candidates(
            {
                "candidate_results": [
                    {
                        "candidate_id": "candidate",
                        "formula_id": "formula",
                        "feature_set_id": "features",
                        "lane_policy": "current",
                        "weights": {"frequency": 0.5, "jmdict_priority": 0.5},
                    }
                ]
            }
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].formula.formula_id, "formula")
        self.assertEqual(candidates[0].formula.weights["frequency"], 0.5)

    def test_fold_training_selector_picks_by_train_score(self) -> None:
        events = _fold_training_selector_events(
            [
                _selector_candidate("a", train=(0.9, 0.2), validation=(0.7, 0.6)),
                _selector_candidate("b", train=(0.1, 0.8), validation=(0.4, 0.9)),
            ]
        )

        self.assertEqual([event["candidate_id"] for event in events], ["a", "b"])
        self.assertEqual([event["validation_score"] for event in events], [0.7, 0.9])


def _candidate_report(
    *,
    full_score: float,
    fold_scores: tuple[float, ...],
) -> dict[str, object]:
    fold_reports = [_fold_report(score=value) for value in fold_scores]
    return _candidate_stability_report(
        _FakeCandidate(full_score),
        fold_reports=fold_reports,
        train_reports=fold_reports,
        reference_summary={"mean_score": 0.5},
    )


class _FakeCandidate:
    lane_policy = "current"
    formula = None

    def __init__(self, full_score: float) -> None:
        self.row = {
            "candidate_id": "candidate",
            "feature_set_id": "features",
            "formula_id": "formula",
            "calibration": {"proficiency_ordering_score": full_score},
            "holdout": {"proficiency_ordering_score": 0.75},
        }


def _fold_report(*, score: float) -> dict[str, object]:
    return {
        "proficiency_ordering_score": score,
        "normal_vocab": {
            "metrics": {"mae": 0.1},
            "scores": {"pairwise_order_score": 0.8},
        },
        "frontier_windows": {"average_window_score": 0.4},
        "lane": {"normal_vocab_f1": 1.0},
    }


def _selector_candidate(
    candidate_id: str,
    *,
    train: tuple[float, ...],
    validation: tuple[float, ...],
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "feature_set_id": "features",
        "lane_policy": "current",
        "train_folds": [{"fold": index + 1, "score": score} for index, score in enumerate(train)],
        "fold_stability": {
            "folds": [{"fold": index + 1, "score": score} for index, score in enumerate(validation)]
        },
        "holdout_score": 0.5,
        "full_calibration_score": 0.6,
        "stability_selector_score": 0.4,
    }


def _label_context(
    *,
    labels: tuple[str, ...],
    expected_bands: tuple[str, ...],
    expected_states: tuple[str, ...],
) -> LabelContext:
    count = len(labels)
    return LabelContext(
        context_id="test",
        labels=labels,
        lemmas=labels,
        readings=tuple("" for _ in labels),
        component_indices=np.arange(count, dtype=np.int64),
        expected_values=np.linspace(0.1, 0.9, count, dtype=np.float32),
        expected_bands=expected_bands,
        expected_candidate_states=np.array(expected_states, dtype="<U64"),
        observed_candidate_states=np.array(expected_states, dtype="<U64"),
        missing_rows=(),
    )


if __name__ == "__main__":
    unittest.main()
