from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_transparent_wago_audit_en_ja import (  # noqa: E402
    WagoCeilingSpec,
    adjusted_payload,
    policy_matches,
    segment_memberships,
    surface_features,
)


def row_with_signals(
    *,
    lemma: str = "乗り込み",
    primary_pair_status: str = "jmdict_exact",
    expected: float = 0.48,
    observed: float = 0.88,
    **signals: float,
) -> dict[str, object]:
    base_signals = {
        "frequency": 0.95,
        "jlpt_vocab_beginner_core": 0.0,
        "lesson_vocab_beginner_core": 0.0,
        "max_written_form_burden": 0.5,
        "rare_wago_tail_risk": 0.9,
        "rare_wago_obscure_written_risk": 0.7,
        "wtype_wago_ease": 1.0,
        "named_entity_risk": 0.0,
    }
    base_signals.update(signals)
    return {
        "label": f"{lemma}/reading",
        "lemma": lemma,
        "expected": expected,
        "expected_band": "intermediate",
        "anchor_observed": observed,
        "anchor_abs_error": abs(observed - expected),
        "anchor_direction": "too_high" if observed > expected else "too_low",
        "primary_pair_status": primary_pair_status,
        "core_rank": 20000.0,
        "signals": base_signals,
        "surface_features": surface_features(lemma),
    }


class TestSrsLearnerDifficultyTransparentWagoAudit(unittest.TestCase):
    def test_surface_features_detect_mixed_kanji_hiragana(self) -> None:
        features = surface_features("乗り込み")

        self.assertTrue(features["mixed_kanji_hiragana"])
        self.assertFalse(features["kanji_only"])
        self.assertEqual(features["kanji_count"], 2)
        self.assertEqual(features["hiragana_count"], 2)

    def test_mixed_surface_wago_tail_matches_ceiling_policy(self) -> None:
        row = row_with_signals()
        spec = WagoCeilingSpec(
            spec_id="test",
            family="mixed_surface",
            ceiling=0.62,
            tail_min=0.75,
            written_max=0.55,
            rank_max=25000.0,
            obscure_max=0.9,
            protect_beginner_core=True,
            protect_source_pair_review=True,
            entity_max=0.95,
        )

        self.assertTrue(policy_matches(row, spec))
        self.assertIn("transparent_wago_failure", segment_memberships(row))
        adjusted = adjusted_payload(row, spec)
        self.assertTrue(adjusted["changed"])
        self.assertEqual(adjusted["adjusted_observed"], 0.62)

    def test_source_pair_review_blocks_ceiling_policy(self) -> None:
        row = row_with_signals(primary_pair_status="jmdict_surface_only")
        spec = WagoCeilingSpec(
            spec_id="test",
            family="mixed_surface",
            ceiling=0.62,
            tail_min=0.75,
            written_max=0.55,
            rank_max=25000.0,
            obscure_max=0.9,
            protect_beginner_core=True,
            protect_source_pair_review=True,
            entity_max=0.95,
        )

        self.assertIn("source_pair_review", segment_memberships(row))
        self.assertFalse(policy_matches(row, spec))

    def test_beginner_core_protection_blocks_ceiling_policy(self) -> None:
        row = row_with_signals(jlpt_vocab_beginner_core=1.0)
        spec = WagoCeilingSpec(
            spec_id="test",
            family="mixed_surface",
            ceiling=0.62,
            tail_min=0.75,
            written_max=0.55,
            rank_max=25000.0,
            obscure_max=0.9,
            protect_beginner_core=True,
            protect_source_pair_review=True,
            entity_max=0.95,
        )

        self.assertFalse(policy_matches(row, spec))


if __name__ == "__main__":
    unittest.main()
