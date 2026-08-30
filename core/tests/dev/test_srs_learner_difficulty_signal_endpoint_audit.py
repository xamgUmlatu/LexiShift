from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_signal_endpoint_audit_en_ja import (  # noqa: E402
    MatrixContext,
    _component_values_by_jlpt_level,
    _high_endpoint_common_core_examples,
    _signal_concerns,
    _supporting_signal_report,
    _value_stats,
)


class TestSrsLearnerDifficultySignalEndpointAudit(unittest.TestCase):
    def test_value_stats_detects_binary_distribution(self) -> None:
        stats = _value_stats(np.asarray([0.0, 0.0, 1.0]), row_count=4)

        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["coverage_rate"], 0.75)
        self.assertTrue(stats["binary_like"])
        self.assertEqual(stats["zero_rate_within_present"], 0.666667)

    def test_high_endpoint_common_core_examples_filters_core_normal_vocab(self) -> None:
        report = {
            "endpoint_examples": {
                "high": [
                    {
                        "label": "事/こと",
                        "value": 1.0,
                        "core_rank": 18.0,
                        "candidate_state": "normal_vocab",
                    },
                    {
                        "label": "遙か/はるか",
                        "value": 1.0,
                        "core_rank": 900.0,
                        "candidate_state": "normal_vocab",
                    },
                ]
            }
        }

        matches = _high_endpoint_common_core_examples(report)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["label"], "事/こと")

    def test_signal_concerns_flags_topic_endpoint_core_vocab(self) -> None:
        report = {
            "name": "news_or_policy_topic_risk",
            "signal_kind": "risk",
            "roles": ["topic_register_policy"],
            "stats": {
                "coverage_rate": 1.0,
                "unique_count": 2,
                "min": 0.0,
                "max": 1.0,
                "binary_like": True,
                "zero_rate_within_present": 0.5,
                "one_rate_within_present": 0.5,
            },
            "endpoint_examples": {
                "high": [
                    {
                        "label": "事/こと",
                        "value": 1.0,
                        "core_rank": 18.0,
                        "candidate_state": "normal_vocab",
                    }
                ]
            },
        }

        categories = {
            concern["category"]
            for concern in _signal_concerns(
                report,
                active_names={"news_or_policy_topic_risk"},
            )
        }

        self.assertIn("topic_endpoint_hits_core_vocab", categories)

    def test_component_values_by_jlpt_level_uses_matrix_levels(self) -> None:
        context = _small_context(
            component_names=("jlpt_vocab_difficulty",),
            values=np.asarray([[0.08], [0.42], [0.85]], dtype=float),
            present=np.asarray([[True], [True], [True]], dtype=bool),
            jlpt_levels=np.asarray([5.0, 3.0, 1.0], dtype=float),
        )

        by_level = _component_values_by_jlpt_level("jlpt_vocab_difficulty", context)

        self.assertEqual(by_level["5"], [0.08])
        self.assertEqual(by_level["3"], [0.42])
        self.assertEqual(by_level["1"], [0.85])

    def test_supporting_jlpt_gate_is_derived_from_easiest_level_matrix(self) -> None:
        context = _small_context(
            component_names=("frequency",),
            values=np.asarray([[0.1], [0.2], [0.3]], dtype=float),
            present=np.asarray([[True], [True], [True]], dtype=bool),
            jlpt_levels=np.asarray([5.0, 3.0, np.nan], dtype=float),
        )

        report = _supporting_signal_report(
            {"name": "jlpt_vocab_is_n3", "roles": ["pedagogical_anchor"]},
            context=context,
            example_limit=2,
        )

        self.assertEqual(report["status"], "derived_from_easiest_level_matrix_field")
        self.assertEqual(report["stats"]["count"], 2)
        self.assertEqual(report["stats"]["one_rate_within_present"], 0.5)


def _small_context(
    *,
    component_names: tuple[str, ...],
    values: object,
    present: object,
    jlpt_levels: object,
) -> MatrixContext:
    row_count = int(np.asarray(values).shape[0])
    return MatrixContext(
        component_names=component_names,
        component_values=values,
        component_present=present,
        lemmas=tuple(f"語{index}" for index in range(row_count)),
        readings=tuple(f"ご{index}" for index in range(row_count)),
        candidate_states=tuple("normal_vocab" for _ in range(row_count)),
        problem_classes=tuple("normal_vocab" for _ in range(row_count)),
        core_ranks=np.arange(1, row_count + 1, dtype=float),
        frequency_values=np.linspace(0.1, 0.3, row_count),
        jlpt_vocab_levels=jlpt_levels,
        current_values=np.linspace(0.1, 0.3, row_count),
        target_curve_positions=np.linspace(0.0, 1.0, row_count),
    )


if __name__ == "__main__":
    unittest.main()
