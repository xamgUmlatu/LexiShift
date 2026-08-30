from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_model_family_search_en_ja import (  # noqa: E402
    BoostSpec,
    Expert,
    FinalAdjustmentSpec,
    FinalFloorSpec,
    FloorSpec,
    ModelCandidate,
    SoftMixSpec,
    _apply_boost,
    _apply_floor,
    _apply_soft_mix,
    _candidate_family_counts,
    _candidate_final_scores,
    _candidate_raw_scores,
    _iter_model_candidates,
    _ramp,
    _reviewed_focus_metrics,
    _signal_arrays,
    _target_cure_context,
    _target_cure_metrics,
)


class TestSrsLearnerDifficultyModelFamilySearch(unittest.TestCase):
    def test_floor_activates_only_after_signal_threshold(self) -> None:
        raw = np.array([0.20, 0.30, 0.40], dtype=np.float32)
        signal_arrays = {
            "frequency": np.array([0.20, 0.30, 0.40], dtype=np.float32),
            "kango_mid_signal": np.array([0.10, 0.50, 1.00], dtype=np.float32),
        }

        values = _apply_floor(
            raw,
            FloorSpec("floor", "kango_mid_signal", 0.35, 0.40, 0.70),
            signal_arrays=signal_arrays,
        )

        self.assertAlmostEqual(float(values[0]), 0.20)
        self.assertGreater(float(values[1]), 0.40)
        self.assertAlmostEqual(float(values[2]), 0.70, places=5)

    def test_boost_uses_remaining_headroom(self) -> None:
        raw = np.array([0.20, 0.80], dtype=np.float32)
        signal_arrays = {
            "frequency": np.array([0.20, 0.80], dtype=np.float32),
            "rare_wago_tail_risk": np.array([0.50, 1.00], dtype=np.float32),
        }

        values = _apply_boost(
            raw,
            BoostSpec("boost", "rare_wago_tail_risk", 0.50, 0.50),
            signal_arrays=signal_arrays,
        )

        self.assertAlmostEqual(float(values[0]), 0.20)
        self.assertAlmostEqual(float(values[1]), 0.90, places=5)

    def test_soft_mix_blends_toward_other_expert(self) -> None:
        raw_by_expert = {
            "base": np.array([0.20, 0.20, 0.20], dtype=np.float32),
            "other": np.array([0.80, 0.80, 0.80], dtype=np.float32),
        }
        signal_arrays = {
            "frequency": np.array([0.00, 0.50, 1.00], dtype=np.float32),
            "kango_mid_signal": np.array([0.00, 0.50, 1.00], dtype=np.float32),
        }

        values = _apply_soft_mix(
            raw_by_expert["base"],
            SoftMixSpec("soft", "other", "kango_mid_signal", 0.50, 1.00),
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )

        self.assertAlmostEqual(float(values[0]), 0.20)
        self.assertAlmostEqual(float(values[1]), 0.20)
        self.assertAlmostEqual(float(values[2]), 0.80)

    def test_candidate_raw_scores_applies_floor_boost_and_soft_mix(self) -> None:
        raw_by_expert = {
            "base": np.array([0.20, 0.20], dtype=np.float32),
            "other": np.array([0.60, 0.60], dtype=np.float32),
        }
        signal_arrays = {
            "frequency": np.array([0.20, 0.20], dtype=np.float32),
            "kango_mid_signal": np.array([0.00, 1.00], dtype=np.float32),
            "rare_wago_tail_risk": np.array([0.00, 1.00], dtype=np.float32),
        }
        candidate = ModelCandidate(
            candidate_id="candidate",
            family="combined",
            base_expert_id="base",
            floors=(FloorSpec("floor", "kango_mid_signal", 0.50, 0.40, 0.70),),
            boosts=(BoostSpec("boost", "rare_wago_tail_risk", 0.50, 0.10),),
            soft_mix=SoftMixSpec("soft", "other", "rare_wago_tail_risk", 0.50, 0.50),
        )

        values = _candidate_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            signal_arrays=signal_arrays,
        )

        self.assertAlmostEqual(float(values[0]), 0.20)
        self.assertGreater(float(values[1]), 0.60)

    def test_candidate_final_scores_applies_post_normalization_floor(self) -> None:
        signal_arrays = {
            "frequency": np.array([0.20, 0.90], dtype=np.float32),
            "missing_frequency_rank_risk": np.array([0.00, 1.00], dtype=np.float32),
        }
        candidate = ModelCandidate(
            candidate_id="candidate",
            family="final_floor",
            base_expert_id="base",
            final_floors=(
                FinalFloorSpec(
                    "final_floor",
                    "missing_frequency_rank_risk",
                    0.50,
                    0.75,
                    0.75,
                ),
            ),
        )

        values = _candidate_final_scores(
            candidate,
            np.array([0.20, 0.40], dtype=np.float32),
            signal_arrays=signal_arrays,
        )

        self.assertAlmostEqual(float(values[0]), 0.20)
        self.assertAlmostEqual(float(values[1]), 0.75)

    def test_candidate_final_scores_applies_soft_adjustments(self) -> None:
        signal_arrays = {
            "frequency": np.array([0.20, 0.90], dtype=np.float32),
            "missing_frequency_rank_risk": np.array([0.00, 1.00], dtype=np.float32),
        }
        partial = ModelCandidate(
            candidate_id="partial",
            family="partial_final_floor",
            base_expert_id="base",
            final_adjustments=(
                FinalAdjustmentSpec(
                    "partial",
                    "partial_final_floor",
                    "missing_frequency_rank_risk",
                    0.50,
                    0.50,
                    floor=0.80,
                ),
            ),
        )
        tail = ModelCandidate(
            candidate_id="tail",
            family="final_tail_boost",
            base_expert_id="base",
            final_adjustments=(
                FinalAdjustmentSpec(
                    "tail",
                    "final_tail_boost",
                    "missing_frequency_rank_risk",
                    0.50,
                    0.25,
                ),
            ),
        )

        partial_values = _candidate_final_scores(
            partial,
            np.array([0.20, 0.40], dtype=np.float32),
            signal_arrays=signal_arrays,
        )
        tail_values = _candidate_final_scores(
            tail,
            np.array([0.20, 0.40], dtype=np.float32),
            signal_arrays=signal_arrays,
        )

        self.assertAlmostEqual(float(partial_values[0]), 0.20)
        self.assertAlmostEqual(float(partial_values[1]), 0.60)
        self.assertAlmostEqual(float(tail_values[0]), 0.20)
        self.assertAlmostEqual(float(tail_values[1]), 0.55)

    def test_ramp_clamps_to_unit_interval(self) -> None:
        values = _ramp(
            np.array([0.00, 0.50, 1.00], dtype=np.float32),
            lower=0.25,
            upper=0.75,
        )

        self.assertEqual([round(float(value), 2) for value in values], [0.0, 0.5, 1.0])

    def test_candidate_family_counts(self) -> None:
        counts = _candidate_family_counts(
            [
                ModelCandidate("a", "linear", "base"),
                ModelCandidate("b", "linear", "base"),
                ModelCandidate("c", "floor", "base"),
            ]
        )

        self.assertEqual(counts, {"linear": 2, "floor": 1})

    def test_refined_softening_candidate_mode_keeps_search_bounded(self) -> None:
        experts = [
            Expert(variant_id, {}, None, {})
            for variant_id in (
                "grid_s10_cnone_000237",
                "grid_s10_cnone_000238",
                "grid_s10_cnone_000206",
                "grid_s10_cnone_000240",
                "grid_s10_cnone_000171",
            )
        ]

        candidates = list(
            _iter_model_candidates(
                experts=experts,
                max_candidates=100000,
                candidate_mode="missingness-softening-refined",
            )
        )
        families = {candidate.family for candidate in candidates}
        base_ids = {candidate.base_expert_id for candidate in candidates}
        final_adjustment_signals = {
            adjustment.signal
            for candidate in candidates
            for adjustment in candidate.final_adjustments
        }

        self.assertEqual(
            families,
            {
                "softening_refined_base",
                "partial_final_floor_refined",
                "final_tail_boost_refined",
            },
        )
        self.assertEqual(
            base_ids,
            {
                "grid_s10_cnone_000237",
                "grid_s10_cnone_000238",
                "grid_s10_cnone_000206",
                "grid_s10_cnone_000240",
            },
        )
        self.assertIn(
            "missing_frequency_source_evidence_risk",
            final_adjustment_signals,
        )
        self.assertIn(
            "missing_frequency_priority_or_kanji_risk",
            final_adjustment_signals,
        )
        self.assertNotIn("rare_wago_tail_risk", final_adjustment_signals)

    def test_signal_arrays_synthesizes_missingness_signals(self) -> None:
        component = {
            "component_names": np.array(
                [
                    "frequency_unranked_risk",
                    "jmdict_priority",
                    "jlpt_vocab_difficulty",
                    "lesson_vocab_difficulty",
                ]
            ),
            "component_values": np.array(
                [
                    [1.00, 1.00, 0.00, 0.00],
                    [0.00, 0.20, 0.30, 0.00],
                ],
                dtype=np.float32,
            ),
            "component_present": np.array(
                [
                    [True, True, False, False],
                    [True, True, True, False],
                ],
                dtype=bool,
            ),
            "frequency_values": np.array([0.99, 0.20], dtype=np.float32),
        }

        arrays = _signal_arrays(component)

        self.assertEqual(
            [float(value) for value in arrays["missing_frequency_rank_risk"]],
            [1.0, 0.0],
        )
        self.assertEqual(
            [float(value) for value in arrays["missing_jmdict_priority_risk"]],
            [1.0, 0.0],
        )
        self.assertEqual(
            [float(value) for value in arrays["missing_pedagogical_vocab_risk"]],
            [1.0, 0.0],
        )
        self.assertEqual(
            [float(value) for value in arrays["missing_frequency_and_priority_risk"]],
            [1.0, 0.0],
        )
        self.assertEqual(
            [float(value) for value in arrays["missing_frequency_source_evidence_risk"]],
            [1.0, 0.0],
        )

    def test_reviewed_focus_metrics_only_scores_reviewed_labels(self) -> None:
        metrics = _reviewed_focus_metrics(
            expected_values=np.array([0.10, 0.80, 0.90], dtype=np.float32),
            observed_values=np.array([0.20, 0.70, 0.00], dtype=np.float32),
            labels=["猫/ねこ", "侘び/わび", "not-reviewed"],
        )

        self.assertEqual(metrics["count"], 2)
        self.assertAlmostEqual(float(metrics["mae"]), 0.10, places=5)
        self.assertAlmostEqual(float(metrics["score"]), 0.90, places=5)

    def test_target_cure_metrics_include_watch_items(self) -> None:
        component = {
            "component_names": np.array(["frequency_unranked_floor99_risk"]),
            "component_values": np.array([[0.99], [0.00]], dtype=np.float32),
            "component_present": np.array([[True], [True]], dtype=bool),
            "frequency_values": np.array([0.99, 0.05], dtype=np.float32),
            "lemmas": np.array(["水虻", "猫"]),
            "readings": np.array(["みずあぶ", "ねこ"]),
        }
        calibration_context = {
            "component_indices": np.array([1], dtype=np.int64),
            "expected_values": np.array([0.05], dtype=np.float32),
            "expected_bands": ["beginner"],
            "labels": ["猫/ねこ"],
        }
        target_cure_context = _target_cure_context(
            component=component,
            calibration_context=calibration_context,
        )

        metrics = _target_cure_metrics(
            np.array([0.90, 0.06], dtype=np.float32),
            target_cure_context=target_cure_context,
            include_rows=True,
        )

        self.assertEqual(metrics["pass_count"], 2)
        self.assertEqual(metrics["count"], 2)
        self.assertAlmostEqual(float(metrics["pass_rate"]), 1.0)
        rows = {row["label"]: row for row in metrics["rows"]}
        self.assertTrue(rows["水虻/みずあぶ"]["pass"])
        self.assertTrue(rows["猫/ねこ"]["pass"])


if __name__ == "__main__":
    unittest.main()
