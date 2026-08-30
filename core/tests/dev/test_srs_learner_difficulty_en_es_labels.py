from __future__ import annotations

import json
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
CALIBRATION_PATH = (
    REPO_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
HOLDOUT_PATH = REPO_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"


class SrsLearnerDifficultyEnEsLabelTests(unittest.TestCase):
    def test_calibration_and_holdout_labels_are_reviewed_and_split(self) -> None:
        calibration = _load(CALIBRATION_PATH)
        holdout = _load(HOLDOUT_PATH)

        self.assertEqual(calibration["language_pair"], "en-es")
        self.assertEqual(holdout["language_pair"], "en-es")
        self.assertEqual(len(calibration["labels"]), 106)
        self.assertEqual(len(holdout["labels"]), 53)

        calibration_numbers = {row["review_number"] for row in calibration["labels"]}
        holdout_numbers = {row["review_number"] for row in holdout["labels"]}
        self.assertFalse(calibration_numbers & holdout_numbers)
        self.assertEqual(calibration_numbers | holdout_numbers, set(range(1, 160)))
        self.assertTrue(all(number % 3 != 0 for number in calibration_numbers))
        self.assertTrue(all(number % 3 == 0 for number in holdout_numbers))

    def test_labels_have_sweep_ready_numeric_targets_and_policy_metadata(self) -> None:
        rows = _load(CALIBRATION_PATH)["labels"] + _load(HOLDOUT_PATH)["labels"]

        for row in rows:
            with self.subTest(lemma=row.get("lemma"), review_number=row.get("review_number")):
                self.assertIsInstance(row.get("lemma"), str)
                self.assertTrue(row["lemma"])
                self.assertEqual(row.get("expected_presentation_mode"), "vocab")
                self.assertIn(
                    row.get("expected_candidate_state"),
                    {"normal_vocab", "deprioritized_vocab"},
                )
                self.assertIsInstance(row.get("expected_problem_class"), str)
                self.assertTrue(row["expected_problem_class"])
                score = row.get("expected_learner_difficulty")
                self.assertIsInstance(score, (int, float))
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)
                self.assertIsInstance(row.get("review_flags"), list)
                self.assertIsInstance(row.get("review_confidence"), (int, float))
                self.assertGreaterEqual(row["review_confidence"], 0.0)
                self.assertLessEqual(row["review_confidence"], 1.0)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
