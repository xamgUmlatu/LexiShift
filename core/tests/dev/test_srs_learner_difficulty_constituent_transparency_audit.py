from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_constituent_transparency_audit_en_ja import (  # noqa: E402
    ConstituentProfile,
    TransparencySpec,
    best_constituent_path,
    constituent_analysis,
    policy_matches,
    surface_features,
)


def profile(
    lemma: str,
    *,
    score: float,
    reading: str | None = None,
    no_priority: float | None = None,
) -> ConstituentProfile:
    return ConstituentProfile(
        lemma=lemma,
        reading=lemma if reading is None else reading,
        index=0,
        knownness=score,
        knownness_no_priority=score if no_priority is None else no_priority,
        source_flags=("test",),
    )


def row_with_transparency(
    *,
    lemma: str = "黒百合",
    primary_pair_status: str = "jmdict_exact",
    transparency: dict[str, object] | None = None,
    **signals: float,
) -> dict[str, object]:
    base_signals = {
        "frequency": 0.95,
        "jlpt_vocab_beginner_core": 0.0,
        "lesson_vocab_beginner_core": 0.0,
        "max_written_form_burden": 0.45,
        "rare_wago_tail_risk": 0.9,
        "wtype_wago_ease": 1.0,
        "named_entity_risk": 0.0,
    }
    base_signals.update(signals)
    return {
        "label": f"{lemma}/reading",
        "lemma": lemma,
        "primary_pair_status": primary_pair_status,
        "signals": base_signals,
        "surface_features": surface_features(lemma),
        "transparency": transparency
        or {
            "coverage_ratio": 1.0,
            "transparency_score": 0.75,
            "guarded_transparency_score": 0.75,
            "reading_compositionality": 1.0,
            "min_knownness": 0.6,
            "auto_downshift_eligible": True,
            "guard_flags": [],
        },
    }


def spec() -> TransparencySpec:
    return TransparencySpec(
        spec_id="test",
        family="low_written",
        ceiling=0.74,
        tail_min=0.75,
        written_max=0.45,
        coverage_min=0.67,
        score_min=0.35,
        min_known_min=0.2,
        reading_min=0.67,
        domain_risk_max=1.01,
        protect_beginner_core=True,
        protect_source_pair_review=True,
        entity_max=0.95,
    )


class TestSrsLearnerDifficultyConstituentTransparencyAudit(unittest.TestCase):
    def test_compound_uses_known_sublemmas_not_full_lemma(self) -> None:
        inventory = {
            "黒百合": profile("黒百合", score=1.0),
            "黒": profile("黒", score=1.0, reading="くろ", no_priority=1.0),
            "百合": profile("百合", score=0.8, reading="ゆり"),
        }

        analysis = constituent_analysis("黒百合", "くろゆり", inventory)

        self.assertEqual(analysis["coverage_ratio"], 1.0)
        self.assertGreater(analysis["transparency_score"], 0.7)
        self.assertEqual(analysis["reading_compositionality"], 1.0)
        chunks = analysis["chunks"]
        self.assertEqual([chunk["surface"] for chunk in chunks], ["黒", "百合"])

    def test_single_character_full_lemma_does_not_self_explain(self) -> None:
        inventory = {"勿": profile("勿", score=1.0, no_priority=1.0)}

        analysis = constituent_analysis("勿", "まな", inventory)

        self.assertEqual(analysis["coverage_ratio"], 0.0)
        self.assertEqual(analysis["chunk_count"], 0)

    def test_derivational_variant_can_explain_nominalized_chunks(self) -> None:
        inventory = {
            "乗る": profile("乗る", score=1.0, reading="のる"),
            "込む": profile("込む", score=0.75, reading="こむ"),
        }

        path = best_constituent_path("乗り込み", inventory)

        self.assertEqual([chunk.surface for chunk in path], ["乗り", "込み"])
        self.assertEqual(
            [chunk.match_type for chunk in path],
            ["derivational_variant", "derivational_variant"],
        )

    def test_reading_compositionality_penalizes_opaque_spelling(self) -> None:
        inventory = {
            "紙": profile("紙", score=1.0, reading="かみ", no_priority=1.0),
            "魚": profile("魚", score=1.0, reading="さかな", no_priority=1.0),
        }

        analysis = constituent_analysis("紙魚", "しみ", inventory)

        self.assertLess(analysis["reading_compositionality"], 0.67)
        self.assertIn("reading_noncompositional", analysis["guard_flags"])
        self.assertFalse(analysis["auto_downshift_eligible"])

    def test_bad_kana_segmentation_blocks_repeated_chunks(self) -> None:
        inventory = {"くい": profile("くい", score=1.0, reading="くい")}

        analysis = constituent_analysis("くいくい", "くいくい", inventory)

        self.assertIn("repeated_kana_chunk", analysis["guard_flags"])
        self.assertIn("short_kana_chunk", analysis["guard_flags"])
        self.assertFalse(analysis["auto_downshift_eligible"])

    def test_policy_requires_constituent_thresholds(self) -> None:
        low_transparency = row_with_transparency(
            transparency={
                "coverage_ratio": 1.0,
                "transparency_score": 0.2,
                "guarded_transparency_score": 0.2,
                "reading_compositionality": 1.0,
                "min_knownness": 0.6,
                "auto_downshift_eligible": True,
                "guard_flags": [],
            }
        )

        self.assertFalse(policy_matches(low_transparency, spec()))

    def test_policy_requires_reading_guard(self) -> None:
        opaque_reading = row_with_transparency(
            transparency={
                "coverage_ratio": 1.0,
                "transparency_score": 0.8,
                "guarded_transparency_score": 0.3,
                "reading_compositionality": 0.5,
                "min_knownness": 1.0,
                "auto_downshift_eligible": False,
                "guard_flags": ["reading_noncompositional"],
            }
        )

        self.assertFalse(policy_matches(opaque_reading, spec()))

    def test_policy_blocks_source_pair_review(self) -> None:
        row = row_with_transparency(primary_pair_status="jmdict_surface_only")

        self.assertFalse(policy_matches(row, spec()))

    def test_matching_row_passes_policy(self) -> None:
        row = row_with_transparency()

        self.assertTrue(policy_matches(row, spec()))


if __name__ == "__main__":
    unittest.main()
