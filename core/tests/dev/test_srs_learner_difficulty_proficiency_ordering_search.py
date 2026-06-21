from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    ComponentContext,
    LabelContext,
)
from srs_learner_difficulty_proficiency_ordering_search_en_ja import (  # noqa: E402
    LanePolicy,
    LaneRule,
    _apply_lane_policy_to_states,
    _context_with_observed_states,
    _guardrail_report,
    generate_formula_candidates,
)


class TestSrsLearnerDifficultyProficiencyOrderingSearch(unittest.TestCase):
    def test_formula_generator_uses_available_source_signals(self) -> None:
        candidates = generate_formula_candidates(
            component_names=(
                "frequency",
                "jmdict_priority",
                "jlpt_vocab_difficulty",
                "lesson_vocab_difficulty",
                "written_form_burden",
                "kango_mid_signal",
            ),
            grid_units=2,
            max_shifts=(None,),
        )

        self.assertTrue(candidates)
        for candidate in candidates:
            self.assertIn("frequency", candidate.weights)
            self.assertAlmostEqual(sum(candidate.weights.values()), 1.0)
            self.assertFalse(candidate.missing_features)

    def test_lane_policy_demotes_only_normal_vocab_with_present_risk(self) -> None:
        context = _component_context(
            states=("normal_vocab", "deprioritized_vocab", "normal_vocab"),
            risks=[0.9, 0.9, 0.1],
        )
        policy = LanePolicy(
            "test",
            "test policy",
            (
                LaneRule(
                    "deprioritized_vocab",
                    ("proper_acronym_entity_risk",),
                    0.8,
                ),
            ),
        )

        states, diagnostics = _apply_lane_policy_to_states(context, policy)

        self.assertEqual(
            list(states),
            ["deprioritized_vocab", "deprioritized_vocab", "normal_vocab"],
        )
        self.assertEqual(diagnostics["changed_count"], 1)

    def test_context_with_observed_states_maps_component_indices(self) -> None:
        context = LabelContext(
            context_id="test",
            labels=("a", "b", "missing"),
            lemmas=("a", "b", "missing"),
            readings=("", "", ""),
            component_indices=np.array([1, 0, -1], dtype=np.int64),
            expected_values=np.array([0.1, 0.2, 0.3], dtype=np.float32),
            expected_bands=("beginner", "beginner", "beginner"),
            expected_candidate_states=np.array(
                ["normal_vocab", "normal_vocab", "normal_vocab"],
                dtype="<U64",
            ),
            observed_candidate_states=np.array(["", "", ""], dtype="<U64"),
            missing_rows=(),
        )

        mapped = _context_with_observed_states(
            context,
            np.array(["normal_vocab", "suppressed_default"], dtype="<U64"),
        )

        self.assertEqual(
            list(mapped.observed_candidate_states),
            ["suppressed_default", "normal_vocab", ""],
        )

    def test_guardrail_report_compares_against_reference_with_tolerance(self) -> None:
        candidate = _dataset_report(score=0.88, pairwise=0.79, window=0.42, lane_f1=0.97)
        reference = _dataset_report(score=0.87, pairwise=0.80, window=0.44, lane_f1=0.99)

        report = _guardrail_report(candidate, reference)

        self.assertTrue(report["passes"])
        self.assertTrue(report["checks"]["normal_vocab_pairwise_within_002"]["passes"])


def _component_context(*, states: tuple[str, ...], risks: list[float]) -> ComponentContext:
    return ComponentContext(
        component_names=("frequency", "proper_acronym_entity_risk"),
        component_values=np.array(
            [[0.1, risk] for risk in risks],
            dtype=np.float32,
        ),
        component_present=np.ones((len(states), 2), dtype=bool),
        current_values=np.zeros(len(states), dtype=np.float32),
        frequency_values=np.zeros(len(states), dtype=np.float32),
        jlpt_vocab_levels=np.full(len(states), np.nan, dtype=np.float32),
        target_curve_positions=np.linspace(0.0, 1.0, len(states), dtype=np.float32),
        candidate_identity_keys=tuple(f"row{index}" for index in range(len(states))),
        lemmas=tuple(f"row{index}" for index in range(len(states))),
        readings=tuple("" for _ in states),
        candidate_states=states,
    )


def _dataset_report(
    *,
    score: float,
    pairwise: float,
    window: float,
    lane_f1: float,
) -> dict[str, object]:
    return {
        "proficiency_ordering_score": score,
        "normal_vocab": {
            "scores": {"pairwise_order_score": pairwise},
            "metrics": {},
        },
        "frontier_windows": {"average_window_score": window},
        "lane": {
            "normal_vocab_f1": lane_f1,
            "default_accept_accuracy": 0.98,
        },
    }


if __name__ == "__main__":
    unittest.main()
