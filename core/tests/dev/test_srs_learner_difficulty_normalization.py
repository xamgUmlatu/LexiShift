from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_normalization import (  # noqa: E402
    difficulty_bands,
    normalize_rows_by_target_curve,
    target_band_counts,
)


class TestSrsLearnerDifficultyNormalization(unittest.TestCase):
    def test_target_band_counts_use_largest_remainder(self) -> None:
        self.assertEqual(target_band_counts(10, (0.5, 0.25, 0.25)), [5, 3, 2])
        self.assertEqual(sum(target_band_counts(101, (1, 2, 3))), 101)

    def test_normalize_rows_by_target_curve_assigns_monotonic_band_positions(self) -> None:
        rows = [
            {"lemma": "a", "raw": 0.4, "core_rank": 3},
            {"lemma": "b", "raw": 0.1, "core_rank": 1},
            {"lemma": "c", "raw": 0.2, "core_rank": 2},
            {"lemma": "d", "raw": 0.9, "core_rank": 4},
        ]

        normalized, metadata = normalize_rows_by_target_curve(
            rows,
            score_key="raw",
            output_key="difficulty",
            band_weights=(0.25, 0.25, 0.25, 0.25),
            band_width=0.25,
        )

        self.assertEqual([row["lemma"] for row in normalized], ["b", "c", "a", "d"])
        self.assertEqual([row["difficulty_band"] for row in normalized], difficulty_band_labels())
        self.assertEqual(metadata["normalization"], "target_curve")
        self.assertEqual([row["assigned_count"] for row in metadata["band_counts"]], [1, 1, 1, 1])


def difficulty_band_labels() -> list[str]:
    return [band.label for band in difficulty_bands(0.25)]


if __name__ == "__main__":
    unittest.main()
