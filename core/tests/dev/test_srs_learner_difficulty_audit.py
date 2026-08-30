from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_audit_en_ja import (  # noqa: E402
    _calibration_metrics,
    _difficulty_band_for_value,
    _select_calibration_seed_row,
)


class TestSrsLearnerDifficultyAuditMetrics(unittest.TestCase):
    def test_difficulty_band_thresholds_match_documented_baseline(self) -> None:
        self.assertEqual(_difficulty_band_for_value(0.10), "beginner")
        self.assertEqual(_difficulty_band_for_value(0.5499), "beginner")
        self.assertEqual(_difficulty_band_for_value(0.55), "intermediate")
        self.assertEqual(_difficulty_band_for_value(0.7999), "intermediate")
        self.assertEqual(_difficulty_band_for_value(0.80), "advanced")
        self.assertEqual(_difficulty_band_for_value(None), "")

    def test_calibration_metrics_separate_classifier_and_difficulty_gaps(self) -> None:
        metrics = _calibration_metrics(
            [
                {
                    "lemma": "猫",
                    "status": "match",
                    "expected_candidate_state": "normal_vocab",
                    "observed_candidate_state": "normal_vocab",
                    "expected_presentation_mode": "vocab",
                    "observed_presentation_mode": "vocab",
                    "expected_problem_class": "normal_vocab",
                    "observed_problem_class": "normal_vocab",
                    "expected_difficulty_band": "beginner",
                    "observed_difficulty_band": "intermediate",
                    "difficulty_status": "mismatch",
                },
                {
                    "lemma": "ね",
                    "status": "match",
                    "expected_candidate_state": "grammar_item",
                    "observed_candidate_state": "grammar_item",
                    "expected_presentation_mode": "grammar",
                    "observed_presentation_mode": "grammar",
                    "expected_problem_class": "particle_or_auxiliary",
                    "observed_problem_class": "particle_or_auxiliary",
                    "expected_difficulty_band": "",
                    "observed_difficulty_band": "beginner",
                    "difficulty_status": "not_labeled",
                },
                {
                    "lemma": "イラク",
                    "status": "mismatch",
                    "expected_candidate_state": "deprioritized_vocab",
                    "observed_candidate_state": "normal_vocab",
                    "expected_presentation_mode": "vocab",
                    "observed_presentation_mode": "vocab",
                    "expected_problem_class": "proper_noun",
                    "observed_problem_class": "normal_vocab",
                    "expected_difficulty_band": "",
                    "observed_difficulty_band": "intermediate",
                    "difficulty_status": "not_labeled",
                },
            ]
        )

        self.assertEqual(metrics["classification"]["row_count"], 3)
        self.assertEqual(metrics["classification"]["match_count"], 2)
        self.assertEqual(metrics["default_vocab_decision"]["false_default_admit"], 0)
        self.assertEqual(metrics["default_vocab_decision"]["false_default_suppress"], 0)
        self.assertEqual(metrics["difficulty_bucket"]["labeled_count"], 1)
        self.assertEqual(metrics["difficulty_bucket"]["mismatch_count"], 1)
        self.assertEqual(metrics["difficulty_bucket"]["accuracy"], 0.0)
        self.assertEqual(metrics["difficulty_value"]["labeled_count"], 0)
        self.assertEqual(
            metrics["candidate_state"]["by_label"]["deprioritized_vocab"]["recall"],
            0.0,
        )
        self.assertEqual(metrics["candidate_state"]["by_label"]["normal_vocab"]["precision"], 0.5)

    def test_calibration_metrics_report_numeric_difficulty_error(self) -> None:
        metrics = _calibration_metrics(
            [
                {
                    "lemma": "猫",
                    "status": "match",
                    "expected_candidate_state": "normal_vocab",
                    "observed_candidate_state": "normal_vocab",
                    "expected_presentation_mode": "vocab",
                    "observed_presentation_mode": "vocab",
                    "expected_problem_class": "normal_vocab",
                    "observed_problem_class": "normal_vocab",
                    "expected_difficulty_band": "beginner",
                    "observed_difficulty_band": "beginner",
                    "expected_learner_difficulty": 0.2,
                    "observed_current_difficulty_proxy": 0.27,
                    "difficulty_absolute_error": 0.07,
                    "difficulty_status": "match",
                },
                {
                    "lemma": "明日",
                    "status": "match",
                    "expected_candidate_state": "normal_vocab",
                    "observed_candidate_state": "normal_vocab",
                    "expected_presentation_mode": "vocab",
                    "observed_presentation_mode": "vocab",
                    "expected_problem_class": "normal_vocab",
                    "observed_problem_class": "normal_vocab",
                    "expected_difficulty_band": "beginner",
                    "observed_difficulty_band": "intermediate",
                    "expected_learner_difficulty": 0.22,
                    "observed_current_difficulty_proxy": 0.57,
                    "difficulty_absolute_error": 0.35,
                    "difficulty_status": "mismatch",
                },
            ]
        )

        self.assertEqual(metrics["difficulty_value"]["labeled_count"], 2)
        self.assertEqual(metrics["difficulty_value"]["evaluated_count"], 2)
        self.assertAlmostEqual(metrics["difficulty_value"]["mae"], 0.21)
        self.assertEqual(metrics["difficulty_value"]["within_0_10"], 1)

    def test_calibration_row_selection_can_target_ambiguous_readings(self) -> None:
        rows = [
            {
                "lemma": "的",
                "reading": "てき",
                "pos": "接尾辞-形状詞的",
                "candidate_state": "grammar_item",
            },
            {
                "lemma": "的",
                "reading": "まと",
                "pos": "名詞-普通名詞-一般",
                "candidate_state": "normal_vocab",
            },
        ]

        selected = _select_calibration_seed_row(
            {"lemma": "的", "expected_reading": "まと", "expected_pos_contains": "名詞"},
            rows,
        )

        self.assertIsNotNone(selected)
        self.assertEqual(selected["reading"], "まと")
        self.assertEqual(selected["candidate_state"], "normal_vocab")


if __name__ == "__main__":
    unittest.main()
