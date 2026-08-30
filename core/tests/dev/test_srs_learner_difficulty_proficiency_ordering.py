from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    ComponentContext,
    LabelContext,
    _frontier_window_metrics,
    _lane_metrics,
    _normalized_values_for_trace_record,
    _placement_metrics,
)


class TestSrsLearnerDifficultyProficiencyOrdering(unittest.TestCase):
    def test_lane_metrics_separate_exact_default_and_normal_vocab(self) -> None:
        context = _label_context(
            expected_values=[0.1, np.nan, 0.5, 0.9],
            expected_states=[
                "normal_vocab",
                "grammar_item",
                "deprioritized_vocab",
                "normal_vocab",
            ],
            observed_states=[
                "normal_vocab",
                "normal_vocab",
                "deprioritized_vocab",
                "suppressed_default",
            ],
        )

        metrics = _lane_metrics(context)

        self.assertEqual(metrics["evaluated_count"], 4)
        self.assertEqual(metrics["exact_state_accuracy"], 0.5)
        self.assertEqual(metrics["default_accept_accuracy"], 0.5)
        self.assertEqual(metrics["normal_vocab_precision"], 0.5)
        self.assertEqual(metrics["normal_vocab_recall"], 0.5)
        self.assertEqual(metrics["normal_vocab_f1"], 0.5)

    def test_placement_metrics_can_score_normal_vocab_only(self) -> None:
        context = _label_context(
            expected_values=[0.1, 0.3, 0.9],
            expected_states=["normal_vocab", "grammar_item", "normal_vocab"],
            observed_states=["normal_vocab", "grammar_item", "normal_vocab"],
        )
        observed = np.array([0.11, 0.95, 0.89], dtype=np.float32)

        metrics = _placement_metrics(
            context,
            observed,
            expected_states=frozenset({"normal_vocab"}),
            detail_limit=5,
        )

        self.assertEqual(metrics["detail"]["difficulty_value"]["evaluated_count"], 2)
        self.assertEqual(metrics["metrics"]["mae"], 0.01)
        self.assertEqual(metrics["scores"]["pairwise_order_score"], 1.0)

    def test_frontier_window_scores_predicted_items_near_target(self) -> None:
        context = _label_context(
            expected_values=[0.1, 0.45, 0.5, 0.9],
            expected_states=[
                "normal_vocab",
                "normal_vocab",
                "normal_vocab",
                "normal_vocab",
            ],
            observed_states=[
                "normal_vocab",
                "normal_vocab",
                "normal_vocab",
                "normal_vocab",
            ],
        )
        observed = np.array([0.12, 0.46, 0.52, 0.2], dtype=np.float32)

        metrics = _frontier_window_metrics(
            context,
            observed,
            proficiency_points=(0.45,),
            challenge_offset=0.0,
            sigma=0.12,
            top_k=2,
        )

        window = metrics["windows"][0]
        self.assertEqual(window["top_k_overlap_rate"], 1.0)
        self.assertEqual(window["near_target_rate"], 1.0)
        self.assertEqual(metrics["average_window_score"], 1.0)

    def test_trace_record_normalization_uses_weights_and_target_curve(self) -> None:
        context = ComponentContext(
            component_names=("frequency", "kanji_grade"),
            component_values=np.array(
                [
                    [0.1, 0.8],
                    [0.6, 0.2],
                    [0.3, 0.4],
                ],
                dtype=np.float32,
            ),
            component_present=np.ones((3, 2), dtype=bool),
            current_values=np.array([0.3, 0.2, 0.1], dtype=np.float32),
            frequency_values=np.array([0.1, 0.6, 0.3], dtype=np.float32),
            jlpt_vocab_levels=np.array([np.nan, np.nan, np.nan], dtype=np.float32),
            target_curve_positions=np.array([0.05, 0.5, 0.95], dtype=np.float32),
            candidate_identity_keys=("a", "b", "c"),
            lemmas=("a", "b", "c"),
            readings=("", "", ""),
            candidate_states=("normal_vocab", "normal_vocab", "normal_vocab"),
        )
        record = {
            "variant_id": "weighted",
            "weights": {"frequency": 0.5, "kanji_grade": 0.5},
            "transforms": {},
        }

        normalized = _normalized_values_for_trace_record(record, context)

        self.assertAlmostEqual(float(normalized[0]), 0.95)
        self.assertAlmostEqual(float(normalized[1]), 0.5)
        self.assertAlmostEqual(float(normalized[2]), 0.05)


def _label_context(
    *,
    expected_values: list[float],
    expected_states: list[str],
    observed_states: list[str],
) -> LabelContext:
    count = len(expected_values)
    return LabelContext(
        context_id="test",
        labels=tuple(f"row{index}" for index in range(count)),
        lemmas=tuple(f"row{index}" for index in range(count)),
        readings=tuple("" for _ in range(count)),
        component_indices=np.arange(count, dtype=np.int64),
        expected_values=np.array(expected_values, dtype=np.float32),
        expected_bands=tuple("beginner" for _ in range(count)),
        expected_candidate_states=np.array(expected_states, dtype="<U64"),
        observed_candidate_states=np.array(observed_states, dtype="<U64"),
        missing_rows=(),
    )


if __name__ == "__main__":
    unittest.main()
