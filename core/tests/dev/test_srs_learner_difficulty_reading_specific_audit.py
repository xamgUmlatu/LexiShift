from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_reading_specific_audit_en_ja import (  # noqa: E402
    ReadingFloorSpec,
    adjusted_payload,
    common_nonstandard_false_positive_risk,
    policy_matches,
    segment_memberships,
)


def row_with_signals(
    *,
    primary_pair_status: str = "jmdict_exact",
    **signals: float,
) -> dict[str, object]:
    base_signals = {
        "frequency": 0.9,
        "frequency_unranked_risk": 1.0,
        "jlpt_vocab_beginner_core": 0.0,
        "lesson_vocab_beginner_core": 0.0,
        "jmdict_reading_form_marked_risk": 0.0,
        "jmdict_reading_restricted_risk": 0.0,
        "non_standard_reading_risk": 0.0,
        "rare_non_standard_reading_risk": 0.0,
        "rare_wago_non_standard_reading_risk": 0.0,
        "wtype_wago_ease": 0.0,
        "wtype_kango_risk": 0.0,
    }
    base_signals.update(signals)
    return {
        "label": "row/reading",
        "expected": 0.7,
        "anchor_observed": 0.3,
        "anchor_abs_error": 0.4,
        "expected_band": "intermediate",
        "primary_pair_status": primary_pair_status,
        "core_rank": None,
        "signals": base_signals,
    }


class TestSrsLearnerDifficultyReadingSpecificAudit(unittest.TestCase):
    def test_common_nonstandard_reading_is_flagged_as_false_positive_risk(self) -> None:
        row = row_with_signals(
            frequency=0.5,
            frequency_unranked_risk=0.0,
            non_standard_reading_risk=1.0,
            rare_non_standard_reading_risk=0.0,
            jlpt_vocab_beginner_core=1.0,
        )

        self.assertTrue(common_nonstandard_false_positive_risk(row))
        self.assertIn("common_nonstandard_false_positive_risk", segment_memberships(row))

    def test_rare_unranked_nonstandard_row_matches_floor_policy(self) -> None:
        row = row_with_signals(
            frequency=0.95,
            frequency_unranked_risk=1.0,
            non_standard_reading_risk=1.0,
            rare_non_standard_reading_risk=0.5,
        )
        spec = ReadingFloorSpec(
            spec_id="test",
            family="unranked_nonstandard",
            floor=0.54,
            rare_min=0.25,
            frequency_min=0.8,
            common_frequency_max=0.65,
            common_rank_max=3000.0,
            protect_beginner_core=False,
        )

        self.assertTrue(policy_matches(row, spec))
        adjusted = adjusted_payload(row, spec)
        self.assertTrue(adjusted["changed"])
        self.assertEqual(adjusted["adjusted_observed"], 0.54)

    def test_common_protection_blocks_floor_policy(self) -> None:
        row = row_with_signals(
            frequency=0.45,
            frequency_unranked_risk=0.0,
            non_standard_reading_risk=1.0,
            rare_non_standard_reading_risk=0.0,
        )
        spec = ReadingFloorSpec(
            spec_id="test",
            family="unranked_nonstandard",
            floor=0.54,
            rare_min=0.25,
            frequency_min=0.8,
            common_frequency_max=0.65,
            common_rank_max=3000.0,
            protect_beginner_core=False,
        )

        self.assertFalse(policy_matches(row, spec))

    def test_source_pair_review_blocks_floor_policy(self) -> None:
        row = row_with_signals(
            primary_pair_status="jmdict_surface_only",
            frequency=0.95,
            frequency_unranked_risk=1.0,
            non_standard_reading_risk=1.0,
            rare_non_standard_reading_risk=0.5,
        )
        spec = ReadingFloorSpec(
            spec_id="test",
            family="unranked_nonstandard",
            floor=0.54,
            rare_min=0.25,
            frequency_min=0.8,
            common_frequency_max=0.65,
            common_rank_max=3000.0,
            protect_beginner_core=False,
        )

        self.assertIn("source_pair_review", segment_memberships(row))
        self.assertFalse(policy_matches(row, spec))


if __name__ == "__main__":
    unittest.main()
