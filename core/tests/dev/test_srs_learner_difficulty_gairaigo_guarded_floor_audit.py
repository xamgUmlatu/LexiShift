from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_gairaigo_guarded_floor_audit_en_ja import (  # noqa: E402
    guarded_gairaigo_floor,
)


class TestSrsLearnerDifficultyGairaigoGuardedFloorAudit(unittest.TestCase):
    def test_non_gairaigo_is_unchanged(self) -> None:
        row = {
            "expected": 0.6,
            "anchor_observed": 0.2,
            "is_gairaigo": False,
            "signals": {},
        }

        result = guarded_gairaigo_floor(row)

        self.assertFalse(result["changed"])
        self.assertEqual(result["adjusted_observed"], 0.2)

    def test_common_loanword_protection_blocks_floor(self) -> None:
        row = {
            "expected": 0.3,
            "anchor_observed": 0.2,
            "is_gairaigo": True,
            "core_rank": 5000.0,
            "signals": {
                "frequency": 0.9,
                "frequency_tail80": 0.5,
                "frequency_unranked_risk": 0.0,
                "bccwj_domain_rank_coverage": 0.8,
                "jlpt_vocab_difficulty": 0.0,
                "jlpt_vocab_beginner_core": 0.0,
                "lesson_vocab_beginner_core": 0.0,
            },
        }

        result = guarded_gairaigo_floor(row)

        self.assertFalse(result["changed"])
        self.assertEqual(result["policy_reason"], "protected_common_loanword")

    def test_ranked_tail_floor_lifts_unprotected_row(self) -> None:
        row = {
            "expected": 0.6,
            "anchor_observed": 0.2,
            "is_gairaigo": True,
            "core_rank": 20000.0,
            "signals": {
                "frequency": 0.9,
                "frequency_tail80": 0.5,
                "frequency_unranked_risk": 0.0,
                "bccwj_domain_rank_coverage": 0.8,
                "jlpt_vocab_difficulty": 0.0,
                "jlpt_vocab_beginner_core": 0.0,
                "lesson_vocab_beginner_core": 0.0,
            },
        }

        result = guarded_gairaigo_floor(row)

        self.assertTrue(result["changed"])
        self.assertEqual(result["policy_reason"], "ranked_tail80_floor")
        self.assertEqual(result["adjusted_observed"], 0.48)


if __name__ == "__main__":
    unittest.main()
