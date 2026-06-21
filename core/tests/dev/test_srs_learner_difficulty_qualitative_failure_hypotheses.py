from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_qualitative_failure_hypotheses_en_ja import (  # noqa: E402
    classify_failure,
)


class TestSrsLearnerDifficultyQualitativeFailureHypotheses(unittest.TestCase):
    def test_classifies_rare_gairaigo_too_early(self) -> None:
        row = {
            "direction": "too_low",
            "candidate_state": "normal_vocab",
            "signals": {
                "wtype_gairaigo_risk": 1.0,
                "frequency": 0.9,
            },
        }

        result = classify_failure(row)

        self.assertEqual(result["hypothesis_id"], "rare_or_domain_gairaigo_too_early")
        self.assertEqual(result["fix_direction"], "bounded_upshift")

    def test_classifies_transparent_wago_tail_too_late(self) -> None:
        row = {
            "direction": "too_high",
            "candidate_state": "normal_vocab",
            "signals": {
                "wtype_wago_ease": 1.0,
                "rare_wago_tail_risk": 0.9,
            },
        }

        result = classify_failure(row)

        self.assertEqual(result["hypothesis_id"], "transparent_wago_tail_too_late")
        self.assertEqual(result["computability"], "low_medium")

    def test_routes_non_normal_vocab_before_scalar(self) -> None:
        row = {
            "direction": "too_low",
            "candidate_state": "deprioritized_vocab",
            "signals": {},
        }

        result = classify_failure(row)

        self.assertEqual(result["hypothesis_id"], "admission_or_source_lane")
        self.assertEqual(result["fix_direction"], "route_or_review_before_scalar")


if __name__ == "__main__":
    unittest.main()
