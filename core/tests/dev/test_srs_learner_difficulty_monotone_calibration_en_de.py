from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_monotone_calibration_en_de import (  # noqa: E402
    _pava,
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyMonotoneCalibrationEnDeTests(unittest.TestCase):
    def test_builds_monotone_calibration_report(self) -> None:
        report = build_report(
            signal_rows=[
                _row("haus", 0.05),
                _row("katze", 0.38),
                _row("mittel", 0.62),
                _row("schwer", 0.92),
            ],
            sweep_payload={},
            calibration_payload={
                "labels": [
                    _label("haus", 0.04, "beginner"),
                    _label("katze", 0.12, "beginner"),
                    _label("mittel", 0.55, "intermediate"),
                    _label("schwer", 0.86, "advanced"),
                ]
            },
            holdout_payload={
                "labels": [
                    _label("katze", 0.14, "beginner"),
                    _label("mittel", 0.52, "beginner"),
                    _label("schwer", 0.88, "advanced"),
                ]
            },
            candidate_id="raw_frequency_blend",
            candidate_grid="refined",
            generated_at="2026-07-06T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_de_learner_difficulty_monotone_calibration_ready",
        )
        self.assertFalse(report["production_ranking_changed"])
        self.assertFalse(report["manual_labels_added"])
        self.assertIn("identity", report["summary"])
        self.assertIn("best_calibration_mae_profile", report["summary"])
        self.assertGreater(len(report["profile_records"]), 5)

        markdown = render_markdown(report)
        self.assertIn("Monotone Calibration Bakeoff", markdown)
        self.assertIn("Best Calibration-MAE Mapping", markdown)
        self.assertIn("Profile Bakeoff", markdown)

    def test_pava_returns_non_decreasing_fit(self) -> None:
        fitted = _pava(
            np.asarray([0.1, 0.8, 0.2, 0.9], dtype=np.float64),
            np.ones(4, dtype=np.float64),
        )

        self.assertEqual(len(fitted), 4)
        self.assertTrue(np.all(np.diff(fitted) >= -1e-9))


def _row(lemma: str, score: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "frequency_blend": score,
        "rank_base": score,
        "pmw_base": score,
        "pos_bucket": "noun",
        "core_rank": int(score * 1000),
        "translations": [f"{lemma} translation"],
    }


def _label(lemma: str, expected: float, band: str) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_candidate_state": "normal_vocab",
        "expected_learner_difficulty": expected,
        "expected_difficulty_band": band,
        "review_flags": [],
    }


if __name__ == "__main__":
    unittest.main()
