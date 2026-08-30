from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_source_quality_guardrail_audit_en_ja import (  # noqa: E402
    GuardrailSpec,
    guardrail_mask,
    guardrail_report,
)


class TestSrsLearnerDifficultySourceQualityGuardrail(unittest.TestCase):
    def test_guardrail_mask_requires_all_terms_and_one_any_term(self) -> None:
        spec = GuardrailSpec(
            "reading_form_source_review",
            "source_fix_review",
            "Rare rows with suspect reading or form evidence.",
            all_terms=("frequency_tail90",),
            any_terms=("reading_or_form_suspect_any", "dictionary_non_ladder_any"),
            threshold=0.7,
        )

        mask = guardrail_mask(
            spec,
            {
                "frequency_tail90": np.asarray([0.8, 0.8, 0.6, 0.9], dtype=np.float32),
                "reading_or_form_suspect_any": np.asarray([0.9, 0.1, 0.9, 0.1], dtype=np.float32),
                "dictionary_non_ladder_any": np.asarray([0.0, 0.8, 0.8, 0.1], dtype=np.float32),
            },
        )

        self.assertEqual(mask.tolist(), [True, True, False, False])

    def test_guardrail_report_separates_recall_from_scalar_collateral(self) -> None:
        spec = GuardrailSpec(
            "test_guardrail",
            "review",
            "Synthetic test guardrail.",
        )
        component = {
            "candidate_states": np.asarray(["normal_vocab", "normal_vocab", "normal_vocab"]),
            "problem_classes": np.asarray(["normal_vocab", "normal_vocab", "normal_vocab"]),
        }
        labeled_rows = [
            {
                "dataset_id": "stitch_validation",
                "label": "bad/ばっど",
                "component_index": 0,
                "target": "non_scalar",
                "treatment": "omit",
                "expected_problem_class": "source_reading_mismatch",
            },
            {
                "dataset_id": "stitch_validation",
                "label": "good/ぐっど",
                "component_index": 1,
                "target": "scalar_vocab",
                "treatment": "vocab",
                "expected_problem_class": "normal_vocab",
                "expected_learner_difficulty": 0.2,
            },
            {
                "dataset_id": "calibration",
                "label": "other/あざー",
                "component_index": 2,
                "target": "scalar_vocab",
                "treatment": "vocab",
                "expected_problem_class": "normal_vocab",
            },
        ]

        report = guardrail_report(
            spec,
            mask=np.asarray([True, True, False], dtype=bool),
            labeled_rows=labeled_rows,
            component=component,
            signals={"frequency": np.asarray([0.9, 0.2, 0.4], dtype=np.float32)},
            detail_limit=4,
        )

        self.assertEqual(report["validation_non_scalar_caught"], 1)
        self.assertEqual(report["validation_non_scalar_total"], 1)
        self.assertEqual(report["validation_non_scalar_recall"], 1.0)
        self.assertEqual(report["validation_scalar_collateral"], 1)
        self.assertEqual(report["all_scalar_collateral"], 1)
        self.assertEqual(report["validation_precision_proxy"], 0.5)
        self.assertEqual(report["caught_by_dataset_target"]["stitch_validation"]["non_scalar"], 1)
        self.assertEqual(report["caught_by_dataset_target"]["stitch_validation"]["scalar_vocab"], 1)


if __name__ == "__main__":
    unittest.main()
