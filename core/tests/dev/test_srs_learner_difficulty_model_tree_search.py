from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_model_tree_search_en_ja import (  # noqa: E402
    SplitSpec,
    TreeCandidate,
    _append_global_experts,
    _calibration_detail_rows,
    _fast_difficulty_summary,
    _filter_expert_records,
    _flat_calibration_rows,
    _format_manual_thresholds,
    _leaf_summary,
    _limit_split_specs,
    _parse_manual_thresholds,
    _split_mask,
    _top_tree_rows,
)


class TestSrsLearnerDifficultyModelTreeSearch(unittest.TestCase):
    def test_manual_threshold_round_trip(self) -> None:
        parsed = _parse_manual_thresholds("frequency:0.35,0.45;kanji_grade:0.7")

        self.assertEqual(parsed["frequency"], (0.35, 0.45))
        self.assertEqual(parsed["kanji_grade"], (0.7,))
        self.assertEqual(
            _format_manual_thresholds({"frequency": (0.35, 0.45)}),
            "frequency:0.35,0.45",
        )

    def test_split_mask_can_route_missing_values_left_or_right(self) -> None:
        values = {"frequency": np.array([0.20, 0.80, np.nan], dtype=np.float32)}
        present = {"frequency": np.array([True, True, False], dtype=bool)}

        missing_left = _split_mask(
            SplitSpec("frequency", 0.45, True),
            split_values=values,
            split_present=present,
        )
        missing_right = _split_mask(
            SplitSpec("frequency", 0.45, False),
            split_values=values,
            split_present=present,
        )

        self.assertEqual(list(missing_left), [True, False, True])
        self.assertEqual(list(missing_right), [True, False, False])

    def test_limit_split_specs_keeps_existing_order(self) -> None:
        specs = [
            SplitSpec("frequency", 0.25, False),
            SplitSpec("frequency", 0.50, False),
            SplitSpec("rare_wago_risk", 0.75, True),
        ]

        self.assertEqual(_limit_split_specs(specs, 0), specs)
        self.assertEqual(_limit_split_specs(specs, 2), specs[:2])

    def test_global_experts_are_kept_after_leaf_specialists(self) -> None:
        merged = _append_global_experts(
            ("leaf_a", "leaf_b"),
            ("global_a", "leaf_a", "global_b"),
        )

        self.assertEqual(merged, ["leaf_a", "leaf_b", "global_a", "global_b"])

    def test_filter_expert_records_excludes_nonzero_signal_weights(self) -> None:
        records = [
            {"variant_id": "safe", "weights": {"frequency": 0.8, "old_jlpt_kanji": 0.2}},
            {
                "variant_id": "visual",
                "weights": {"frequency": 0.8, "kanjivg_visual_complexity": 0.2},
            },
            {
                "variant_id": "zero_visual",
                "weights": {"frequency": 1.0, "kanjivg_visual_complexity": 0.0},
            },
        ]

        filtered = _filter_expert_records(
            records,
            exclude_signals=("kanjivg_visual_complexity",),
        )

        self.assertEqual([row["variant_id"] for row in filtered], ["safe", "zero_visual"])

    def test_top_tree_rows_deduplicates_candidate_ids(self) -> None:
        rows = [
            {"candidate_id": "same", "scores": {"balanced_score": 0.5}},
            {"candidate_id": "same", "scores": {"balanced_score": 0.7}},
            {"candidate_id": "other", "scores": {"balanced_score": 0.6}},
        ]

        top = _top_tree_rows(rows, limit=10)

        self.assertEqual([row["candidate_id"] for row in top], ["same", "other"])
        self.assertEqual(top[0]["scores"]["balanced_score"], 0.7)

    def test_fast_difficulty_summary_rewards_bucket_and_order(self) -> None:
        context = {
            "expected_values": np.array([0.05, 0.35, 0.95], dtype=np.float32),
            "expected_finite": np.array([True, True, True], dtype=bool),
            "expected_bucket_ids": np.array([0, 0, 2], dtype=np.int8),
            "beginner_core_mask": np.array([True, False, False], dtype=bool),
            "beginner_broad_mask": np.array([True, True, False], dtype=bool),
            "upper_tail_mask": np.array([False, False, True], dtype=bool),
            "high_tail_mask": np.array([False, False, True], dtype=bool),
            "pair_left": np.array([0, 0, 1], dtype=np.int64),
            "pair_right": np.array([1, 2, 2], dtype=np.int64),
            "pair_expected_gap": np.array([0.30, 0.90, 0.60], dtype=np.float32),
        }

        scores, metrics = _fast_difficulty_summary(
            np.array([0.06, 0.40, 0.92], dtype=np.float32),
            calibration_context=context,
        )

        self.assertEqual(metrics["bucket_accuracy"], 1.0)
        self.assertEqual(metrics["pairwise_accuracy"], 1.0)
        self.assertGreater(float(scores["balanced_score"]), 0.90)

    def test_calibration_detail_rows_capture_status_leaf_and_signals(self) -> None:
        component = {
            "component_names": np.array(["frequency", "kanji_grade"]),
            "component_values": np.array(
                [
                    [0.10, 0.20],
                    [0.90, 0.80],
                ],
                dtype=np.float32,
            ),
            "component_present": np.array(
                [
                    [True, True],
                    [True, False],
                ],
                dtype=bool,
            ),
            "frequency_values": np.array([0.10, 0.90], dtype=np.float32),
            "candidate_states": np.array(["normal_vocab", "deprioritized_vocab"]),
            "problem_classes": np.array(["normal_vocab", "proper_noun"]),
            "core_ranks": np.array([10.0, 200.0], dtype=np.float32),
        }
        calibration_context = {
            "component_indices": np.array([0, 1, -1], dtype=np.int64),
            "expected_values": np.array([0.05, 0.90, np.nan], dtype=np.float32),
            "expected_bands": ["beginner", "advanced", ""],
            "identity_keys": ["id-0", "id-1", "id-2"],
            "lemmas": ["猫", "詭弁", "第"],
            "readings": ["ねこ", "きべん", ""],
            "labels": ["猫/ねこ", "詭弁/きべん", "第"],
        }
        candidate = TreeCandidate(
            candidate_id="candidate",
            root=None,
            child_side=None,
            child=None,
            expert_ids=("expert_a",),
        )

        rows = _calibration_detail_rows(
            candidate=candidate,
            normalized=np.array([0.06, 0.70], dtype=np.float32),
            leaf_ids=np.array([0, 0], dtype=np.int64),
            component=component,
            calibration_context=calibration_context,
        )

        self.assertEqual(
            [row["difficulty_status"] for row in rows], ["match", "mismatch", "not_labeled"]
        )
        self.assertEqual(rows[1]["direction"], "too_low")
        self.assertEqual(rows[1]["observed_band"], "intermediate")
        self.assertEqual(rows[1]["expert_id"], "expert_a")
        self.assertIsNone(rows[1]["signals"]["kanji_grade"])

        leaf_summary = _leaf_summary(
            np.array([0, 0], dtype=np.int64),
            ("expert_a",),
            normalized=np.array([0.06, 0.70], dtype=np.float32),
            component=component,
            calibration_rows=rows,
        )
        self.assertEqual(leaf_summary[0]["calibration_status_counts"], {"match": 1, "mismatch": 1})
        self.assertEqual(leaf_summary[0]["candidate_state_counts"]["normal_vocab"], 1)

        flat = _flat_calibration_rows(
            {
                "exact_top": [
                    {
                        "candidate_id": "candidate",
                        "calibration_rows": rows,
                    }
                ]
            }
        )
        self.assertEqual(flat[0]["candidate_id"], "candidate")
        self.assertEqual(flat[0]["signal_kanji_grade"], 0.2)


if __name__ == "__main__":
    unittest.main()
