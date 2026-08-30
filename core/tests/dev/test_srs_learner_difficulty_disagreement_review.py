from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_disagreement_review_en_ja import (  # noqa: E402
    _band_label,
    _direction,
    _label_subset_summary,
    _sample_spread_rows,
    _signal_group_summary,
    _tags_for_row,
)


class TestSrsLearnerDifficultyDisagreementReview(unittest.TestCase):
    def test_direction_uses_new_minus_old_delta(self) -> None:
        self.assertEqual(_direction(-0.2), "new_easier")
        self.assertEqual(_direction(0.2), "new_harder")
        self.assertEqual(_direction(0.0), "equal")

    def test_band_label_clamps_unit_interval(self) -> None:
        self.assertEqual(_band_label(0.0, 0.25), "0.00-0.25")
        self.assertEqual(_band_label(0.26, 0.25), "0.25-0.50")
        self.assertEqual(_band_label(1.0, 0.25), "0.75-1.00")
        self.assertEqual(_band_label(1.4, 0.25), "0.75-1.00")

    def test_label_subset_summary_counts_closer_models(self) -> None:
        summary = _label_subset_summary(
            [
                {"old_abs_error": 0.1, "new_abs_error": 0.2, "closer_model": "old"},
                {"old_abs_error": 0.3, "new_abs_error": 0.1, "closer_model": "new"},
                {"old_abs_error": 0.2, "new_abs_error": 0.2, "closer_model": "tie"},
            ]
        )

        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["old_closer_count"], 1)
        self.assertEqual(summary["new_closer_count"], 1)
        self.assertEqual(summary["tie_count"], 1)
        self.assertAlmostEqual(summary["old_mean_abs_error"], 0.2)

    def test_tags_for_row_exposes_lane_and_signal_structure(self) -> None:
        tags = _tags_for_row(
            {
                "candidate_state": "deprioritized_vocab",
                "problem_class": "proper_noun",
                "jlpt_vocab_level": 5,
                "signal_groups": {
                    "entity_or_acronym": 0.8,
                    "rare_native": 0.7,
                    "written_burden": 0.6,
                },
            }
        )

        self.assertIn("deprioritized_lane", tags)
        self.assertIn("proper_noun", tags)
        self.assertIn("entity_or_acronym", tags)
        self.assertIn("rare_native", tags)
        self.assertIn("written_burden", tags)
        self.assertIn("beginner_jlpt", tags)

    def test_signal_group_summary_reports_high_share(self) -> None:
        summary = _signal_group_summary(
            [
                {"signal_groups": {"rare_native": 0.8}},
                {"signal_groups": {"rare_native": 0.2}},
            ]
        )

        self.assertEqual(summary["rare_native"]["high_count"], 1)
        self.assertAlmostEqual(summary["rare_native"]["high_share"], 0.5)

    def test_sample_spread_rows_spreads_by_new_score(self) -> None:
        rows = [
            {"lemma": str(index), "new_score": index / 10, "abs_delta": 0.2} for index in range(10)
        ]

        samples = _sample_spread_rows(rows, sample_count=4)

        self.assertEqual([row["lemma"] for row in samples], ["1", "3", "6", "8"])


if __name__ == "__main__":
    unittest.main()
