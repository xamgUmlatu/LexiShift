from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_acceptance_review_pack_en_ja import (  # noqa: E402
    _band_indices,
    disagreement_rows,
)


class TestSrsLearnerDifficultyAcceptanceReviewPack(unittest.TestCase):
    def test_band_indices_sort_and_keep_upper_endpoint_only_for_final_band(self) -> None:
        values = np.array([0.28, 0.1, 0.199, 0.2, 1.0], dtype=np.float32)

        self.assertEqual(_band_indices(values, start=0.1, end=0.2).tolist(), [1, 2])
        self.assertEqual(_band_indices(values, start=0.9, end=1.0).tolist(), [4])

    def test_disagreement_rows_orders_by_selected_delta(self) -> None:
        component = {
            "lemmas": np.array(["a", "b", "c"]),
            "readings": np.array(["aa", "bb", "cc"]),
            "candidate_states": np.array(["normal_vocab"] * 3),
            "problem_classes": np.array(["normal_vocab"] * 3),
            "core_ranks": np.array([1.0, 2.0, 3.0], dtype=np.float32),
        }
        score_arrays = {
            "v1": np.array([0.2, 0.8, 0.4], dtype=np.float32),
            "ordinary_cap": np.array([0.2, 0.8, 0.4], dtype=np.float32),
            "stitch": np.array([0.5, 0.81, 0.9], dtype=np.float32),
        }

        rows = disagreement_rows(
            anchor=score_arrays["ordinary_cap"],
            other=score_arrays["stitch"],
            component=component,
            score_arrays=score_arrays,
            direction="other_higher",
            limit=3,
        )

        self.assertEqual([row["lemma"] for row in rows], ["c", "a"])
        self.assertEqual(rows[0]["selected_delta"], 0.5)


if __name__ == "__main__":
    unittest.main()
