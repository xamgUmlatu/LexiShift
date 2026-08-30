from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_reviewed_focus_eval_en_ja import (  # noqa: E402
    _admission_policy_summary,
    _route_metrics,
    _topic_score_summary,
    _worst_numeric_rows,
)


class TestSrsLearnerDifficultyReviewedFocusEval(unittest.TestCase):
    def test_admission_policy_summary_counts_topic_rows_observed_as_normal_vocab(
        self,
    ) -> None:
        rows = [
            {
                "label": "導体/どうたい",
                "treatment": "topic_only",
                "observed_candidate_state": "normal_vocab",
                "observed_problem_class": "normal_vocab",
            },
            {
                "label": "藍瓶/あいがめ",
                "treatment": "topic_only",
                "observed_candidate_state": "deprioritized_vocab",
                "observed_problem_class": "topic_or_entity_specific",
            },
            {
                "label": "鋸歯/のこば",
                "treatment": "source_fix",
                "observed_candidate_state": "normal_vocab",
            },
        ]

        summary = _admission_policy_summary(rows)

        self.assertEqual(summary["topic_only_count"], 2)
        self.assertEqual(summary["topic_only_observed_normal_vocab_count"], 1)
        self.assertEqual(summary["source_fix_observed_normal_vocab_count"], 1)
        self.assertEqual(summary["topic_only_observed_normal_vocab_rate"], 0.5)

    def test_route_metrics_separate_numeric_and_policy_rows(self) -> None:
        rows = [
            {
                "label": "火曜/かよう",
                "review_route": "possible_overhard_general_vocab",
                "treatment": "vocab",
                "expected_learner_difficulty": 0.14,
            },
            {
                "label": "導体/どうたい",
                "review_route": "tail_topic_or_omit_review",
                "treatment": "topic_only",
                "observed_candidate_state": "normal_vocab",
            },
            {
                "label": "内戦/ないせん",
                "review_route": "tail_topic_or_omit_review",
                "treatment": "vocab",
                "expected_learner_difficulty": 0.58,
            },
        ]
        metrics = {
            row["route"]: row for row in _route_metrics(rows, np.asarray([0.24, 0.60, 0.68]))
        }

        self.assertEqual(metrics["possible_overhard_general_vocab"]["numeric_count"], 1)
        self.assertEqual(metrics["possible_overhard_general_vocab"]["numeric_mae"], 0.1)
        self.assertEqual(metrics["tail_topic_or_omit_review"]["numeric_count"], 1)
        self.assertEqual(metrics["tail_topic_or_omit_review"]["policy_count"], 1)
        self.assertEqual(
            metrics["tail_topic_or_omit_review"]["topic_only_observed_normal_vocab_count"],
            1,
        )

    def test_topic_score_summary_ignores_numeric_vocab_rows(self) -> None:
        rows = [
            {"treatment": "vocab"},
            {"treatment": "topic_only"},
            {"treatment": "source_fix"},
        ]
        summary = _topic_score_summary(rows, np.asarray([0.1, 0.4, 0.9]))

        self.assertEqual(summary["evaluated_count"], 2)
        self.assertEqual(summary["below_0_80"], 1)
        self.assertEqual(summary["at_or_above_0_80"], 1)

    def test_worst_numeric_rows_reports_signed_delta(self) -> None:
        rows = [
            {
                "label": "火曜/かよう",
                "review_route": "possible_overhard_general_vocab",
                "treatment": "vocab",
                "expected_learner_difficulty": 0.14,
            }
        ]
        worst = _worst_numeric_rows(rows, np.asarray([0.44]), limit=1)

        self.assertEqual(worst[0]["label"], "火曜/かよう")
        self.assertEqual(worst[0]["delta_observed_minus_expected"], 0.3)
        self.assertEqual(worst[0]["abs_error"], 0.3)


if __name__ == "__main__":
    unittest.main()
