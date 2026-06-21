from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_q15_review_pack_en_ja import (  # noqa: E402
    _evenly_spaced_indices,
    _window_indices,
)


class TestSrsLearnerDifficultyQ15ReviewPack(unittest.TestCase):
    def test_window_indices_are_sorted_by_difficulty(self) -> None:
        values = np.array([0.28, 0.21, 0.35, 0.24, 0.20], dtype=np.float32)

        indices = _window_indices(values, start=0.20, end=0.30)

        self.assertEqual(indices.tolist(), [4, 1, 3, 0])

    def test_evenly_spaced_indices_samples_without_padding(self) -> None:
        indices = np.array([10, 11, 12, 13, 14, 15], dtype=np.int64)

        self.assertEqual(_evenly_spaced_indices(indices, sample_count=3), [10, 12, 15])
        self.assertEqual(_evenly_spaced_indices(indices[:2], sample_count=3), [10, 11])


if __name__ == "__main__":
    unittest.main()
