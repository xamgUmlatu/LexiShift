from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_gairaigo_curve_sweep_en_ja import (  # noqa: E402
    CURRENT_SPEC_ID,
    current_curve_spec,
    guarded_gairaigo_curve,
    protected_common_loanword,
    shaped_tail_value,
)


class TestSrsLearnerDifficultyGairaigoCurveSweep(unittest.TestCase):
    def test_current_spec_id_matches_current_curve(self) -> None:
        self.assertEqual(current_curve_spec().spec_id, CURRENT_SPEC_ID)

    def test_tail_shapes_are_monotone_but_differently_aggressive(self) -> None:
        linear = shaped_tail_value(0.90, lower=0.80, shape="linear")
        square = shaped_tail_value(0.90, lower=0.80, shape="square")
        sqrt = shaped_tail_value(0.90, lower=0.80, shape="sqrt")

        self.assertAlmostEqual(linear, 0.5)
        self.assertAlmostEqual(square, 0.25)
        self.assertGreater(sqrt, linear)

    def test_common_loanword_protection_blocks_curve(self) -> None:
        spec = current_curve_spec()
        row = {
            "core_rank": 5000.0,
            "signals": {
                "frequency": 0.9,
                "frequency_unranked_risk": 0.0,
                "bccwj_domain_rank_coverage": 0.8,
                "jlpt_vocab_difficulty": 0.0,
                "jlpt_vocab_beginner_core": 0.0,
                "lesson_vocab_beginner_core": 0.0,
            },
        }

        self.assertTrue(protected_common_loanword(row, spec=spec))

    def test_current_ranked_tail_curve_matches_prior_floor(self) -> None:
        row = {
            "expected": 0.66,
            "anchor_observed": 0.315782,
            "is_gairaigo": True,
            "core_rank": 17861.0,
            "signals": {
                "frequency": 0.89971,
                "frequency_unranked_risk": 0.0,
                "bccwj_domain_rank_coverage": 0.75,
                "jlpt_vocab_difficulty": 0.0,
                "jlpt_vocab_beginner_core": 0.0,
                "lesson_vocab_beginner_core": 0.0,
            },
        }

        result = guarded_gairaigo_curve(row, current_curve_spec())

        self.assertTrue(result["changed"])
        self.assertEqual(result["policy_reason"], "ranked_tail_floor")
        self.assertEqual(result["adjusted_observed"], 0.479594)

    def test_floor_does_not_move_already_high_rows(self) -> None:
        row = {
            "expected": 0.52,
            "anchor_observed": 0.7,
            "is_gairaigo": True,
            "core_rank": 23544.0,
            "signals": {
                "frequency": 0.95,
                "frequency_unranked_risk": 0.0,
                "bccwj_domain_rank_coverage": 0.6,
                "jlpt_vocab_difficulty": 0.0,
                "jlpt_vocab_beginner_core": 0.0,
                "lesson_vocab_beginner_core": 0.0,
            },
        }

        result = guarded_gairaigo_curve(row, current_curve_spec())

        self.assertFalse(result["changed"])
        self.assertEqual(result["adjusted_observed"], 0.7)


if __name__ == "__main__":
    unittest.main()
