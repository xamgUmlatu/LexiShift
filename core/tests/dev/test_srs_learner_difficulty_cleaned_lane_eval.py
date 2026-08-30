from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_cleaned_lane_eval_en_ja import (  # noqa: E402
    dataset_report,
)


class TestSrsLearnerDifficultyCleanedLaneEval(unittest.TestCase):
    def test_dataset_report_splits_scalar_rows_by_jmdict_exact_status(self) -> None:
        rows = [
            {
                "lemma": "黒",
                "reading": "くろ",
                "label": "黒/くろ",
                "target": "scalar_vocab",
                "expected_learner_difficulty": 0.1,
                "primary_pair_status": "jmdict_exact",
                "gate_recommendation": "source_pair_ok_for_vocab_lane",
            },
            {
                "lemma": "厚口",
                "reading": "あつくち",
                "label": "厚口/あつくち",
                "target": "scalar_vocab",
                "expected_learner_difficulty": 0.6,
                "primary_pair_status": "jmdict_surface_only",
                "gate_recommendation": "source_pair_review",
                "jmdict_status": "surface_only",
                "jmnedict_status": "no_evidence",
            },
            {
                "lemma": "枚",
                "reading": "ばい",
                "label": "枚/ばい",
                "target": "source_mismatch_review",
                "primary_pair_status": "jmdict_surface_and_reading_unpaired",
                "gate_recommendation": "source_pair_review",
            },
        ]
        lookup = {("黒", "くろ"): 0, ("厚口", "あつくち"): 1, ("枚", "ばい"): 2}
        score_arrays = {
            "v1": np.asarray([0.1, 0.7, 0.4], dtype=np.float32),
            "ordinary_cap": np.asarray([0.2, 0.6, 0.4], dtype=np.float32),
            "stitch": np.asarray([0.1, 0.5, 0.4], dtype=np.float32),
        }

        report = dataset_report(
            rows,
            lookup=lookup,
            score_arrays=score_arrays,
            detail_limit=4,
        )

        self.assertEqual(report["pair_scalar_count"], 2)
        self.assertEqual(report["cleaned_jmdict_exact_count"], 1)
        self.assertEqual(report["excluded_non_jmdict_exact_count"], 1)
        self.assertEqual(report["scopes"]["all_pair_scalar"]["count"], 2)
        self.assertEqual(report["scopes"]["cleaned_jmdict_exact"]["count"], 1)
        self.assertEqual(report["scopes"]["excluded_non_jmdict_exact"]["count"], 1)
        self.assertEqual(report["excluded_rows"][0]["label"], "厚口/あつくち")


if __name__ == "__main__":
    unittest.main()
