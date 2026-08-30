from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_bounded_hybrid_stability_en_ja import (  # noqa: E402
    _fold_training_selection_frequency,
    _fold_training_selector_events,
    _is_narrow_policy,
    _policy_family,
    _scope_for_policy,
)


class TestSrsLearnerDifficultyBoundedHybridStability(unittest.TestCase):
    def test_scope_for_policy_separates_global_targeted_and_narrow(self) -> None:
        self.assertEqual(
            _scope_for_policy("global_delta_blend__s035__c008__clip", {"changed_count": 70000}),
            "all",
        )
        self.assertEqual(
            _scope_for_policy("rare_tail_lift__t050__s100__c008__clip", {"changed_count": 30000}),
            "targeted",
        )
        self.assertEqual(
            _scope_for_policy("rare_tail_lift__t050__s100__c008__clip", {"changed_count": 20000}),
            "narrow",
        )

    def test_is_narrow_policy_requires_targeted_and_changed_count_limit(self) -> None:
        self.assertFalse(
            _is_narrow_policy(
                {
                    "candidate_id": "global_delta_blend__x",
                    "correction_summary": {"changed_count": 1},
                }
            )
        )
        self.assertTrue(
            _is_narrow_policy(
                {
                    "candidate_id": "written_downshift_small__x",
                    "correction_summary": {"changed_count": 25000},
                }
            )
        )
        self.assertFalse(
            _is_narrow_policy(
                {
                    "candidate_id": "written_downshift_small__x",
                    "correction_summary": {"changed_count": 25001},
                }
            )
        )

    def test_policy_family_uses_prefix_before_parameters(self) -> None:
        self.assertEqual(
            _policy_family("rare_lift_written_small_downshift__t050__s100__c016__rerank"),
            "rare_lift_written_small_downshift",
        )
        self.assertEqual(_policy_family("old_anchor_clip"), "old_anchor_clip")

    def test_fold_training_selector_picks_by_train_score(self) -> None:
        events = _fold_training_selector_events(
            [
                _candidate("a", train=(0.9, 0.2), validation=(0.7, 0.6), holdout=0.5),
                _candidate("b", train=(0.1, 0.8), validation=(0.4, 0.9), holdout=0.6),
            ]
        )

        self.assertEqual([event["candidate_id"] for event in events], ["a", "b"])
        self.assertEqual([event["validation_score"] for event in events], [0.7, 0.9])
        self.assertEqual([event["holdout_score"] for event in events], [0.5, 0.6])

    def test_selection_frequency_groups_selected_candidates(self) -> None:
        frequency = _fold_training_selection_frequency(
            [
                {
                    "fold": 1,
                    "candidate_id": "a",
                    "policy_family": "rare",
                    "scope": "narrow",
                    "validation_score": 0.8,
                    "train_score": 0.9,
                    "holdout_score": 0.7,
                },
                {
                    "fold": 2,
                    "candidate_id": "a",
                    "policy_family": "rare",
                    "scope": "narrow",
                    "validation_score": 0.6,
                    "train_score": 0.7,
                    "holdout_score": 0.7,
                },
            ]
        )

        self.assertEqual(frequency[0]["candidate_id"], "a")
        self.assertEqual(frequency[0]["selected_fold_count"], 2)
        self.assertEqual(frequency[0]["mean_validation_score"], 0.7)
        self.assertEqual(frequency[0]["mean_holdout_score"], 0.7)


def _candidate(
    candidate_id: str,
    *,
    train: tuple[float, ...],
    validation: tuple[float, ...],
    holdout: float,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "policy_family": "family",
        "scope": "scope",
        "train_folds": [{"fold": index + 1, "score": score} for index, score in enumerate(train)],
        "fold_stability": {
            "folds": [
                {
                    "fold": index + 1,
                    "score": score,
                    "normal_vocab_pairwise": 0.8,
                    "window_quality": 0.4,
                }
                for index, score in enumerate(validation)
            ]
        },
        "holdout_score": holdout,
        "full_calibration_score": 0.6,
        "stability_selector_score": 0.5,
    }


if __name__ == "__main__":
    unittest.main()
