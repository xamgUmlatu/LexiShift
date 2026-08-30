from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_bounded_hybrid_search_en_ja import (  # noqa: E402
    CorrectionPolicy,
    _group_mask,
    apply_policy,
    generate_correction_policies,
)


class TestSrsLearnerDifficultyBoundedHybridSearch(unittest.TestCase):
    def test_generate_correction_policies_has_references_and_real_policies(self) -> None:
        policy_ids = {policy.policy_id for policy in generate_correction_policies()}

        self.assertIn("old_anchor_clip", policy_ids)
        self.assertIn("old_anchor_rerank", policy_ids)
        self.assertTrue(any(policy_id.startswith("rare_tail_lift") for policy_id in policy_ids))
        self.assertEqual(len(policy_ids), len(generate_correction_policies()))

    def test_group_mask_supports_and_or_and_all(self) -> None:
        groups = {
            "rare_native": np.asarray([0.9, 0.2, 0.9], dtype=np.float32),
            "frequency_tail": np.asarray([0.8, 0.9, 0.2], dtype=np.float32),
        }

        both = _group_mask(
            groups,
            ("rare_native", "frequency_tail"),
            threshold=0.5,
            length=3,
        )
        either = _group_mask(
            groups,
            ("rare_native|frequency_tail",),
            threshold=0.5,
            length=3,
        )
        all_rows = _group_mask(groups, ("all",), threshold=0.0, length=3)

        self.assertEqual(both.tolist(), [True, False, False])
        self.assertEqual(either.tolist(), [True, True, True])
        self.assertEqual(all_rows.tolist(), [True, True, True])

    def test_apply_policy_only_changes_masked_normal_vocab_positive_rows(self) -> None:
        policy = CorrectionPolicy(
            policy_id="test",
            description="test",
            positive_groups=("rare_native", "frequency_tail"),
            negative_groups=(),
            positive_threshold=0.5,
            negative_threshold=1.1,
            scale=1.0,
            cap=0.08,
            normalization="clip",
        )
        old = np.asarray([0.2, 0.4, 0.6, 0.8], dtype=np.float32)
        new = np.asarray([0.5, 0.7, 0.1, 0.9], dtype=np.float32)
        groups = {
            "rare_native": np.asarray([0.9, 0.9, 0.9, 0.9], dtype=np.float32),
            "frequency_tail": np.asarray([0.9, 0.1, 0.9, 0.9], dtype=np.float32),
        }
        states = ("normal_vocab", "normal_vocab", "normal_vocab", "deprioritized_vocab")

        hybrid, summary = apply_policy(
            policy,
            old_values=old,
            new_values=new,
            signal_groups=groups,
            candidate_states=states,
            target_positions=old,
        )

        self.assertAlmostEqual(float(hybrid[0]), 0.28, places=6)
        self.assertAlmostEqual(float(hybrid[1]), 0.4, places=6)
        self.assertAlmostEqual(float(hybrid[2]), 0.6, places=6)
        self.assertAlmostEqual(float(hybrid[3]), 0.8, places=6)
        self.assertEqual(summary["changed_count"], 1)
        self.assertEqual(summary["positive_changed_count"], 1)

    def test_apply_policy_rerank_preserves_target_positions(self) -> None:
        policy = CorrectionPolicy(
            policy_id="test",
            description="test",
            positive_groups=("all",),
            negative_groups=(),
            positive_threshold=0.0,
            negative_threshold=1.1,
            scale=1.0,
            cap=0.5,
            normalization="rerank",
        )
        target_positions = np.asarray([0.1, 0.2, 0.3], dtype=np.float32)

        hybrid, _summary = apply_policy(
            policy,
            old_values=np.asarray([0.3, 0.2, 0.1], dtype=np.float32),
            new_values=np.asarray([0.8, 0.2, 0.1], dtype=np.float32),
            signal_groups={"all": np.ones(3, dtype=np.float32)},
            candidate_states=("normal_vocab", "normal_vocab", "normal_vocab"),
            target_positions=target_positions,
        )

        self.assertEqual(sorted(round(float(value), 6) for value in hybrid), [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
