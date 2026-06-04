from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_formula_weight_surface_en_es import (  # noqa: E402
    build_formula_weight_surface_report,
    render_formula_weight_surface_markdown,
)


class SemanticVetoFormulaWeightSurfaceTests(unittest.TestCase):
    def test_surface_report_probes_maxima_curves_and_pairwise_shape(self) -> None:
        report = build_formula_weight_surface_report(
            manifest=_manifest(),
            difficulty_surface_payload=_difficulty_surface_payload(),
            policy_payload=_policy(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "formula_weight_surface_established")
        self.assertEqual(report["summary"]["cell_count"], 3)
        self.assertEqual(report["summary"]["sweep_count"], 1)

        sweep = report["sweep_reports"][0]
        self.assertEqual(sweep["sweep_id"], "linear_test_weight_sweep")
        self.assertGreater(sweep["sampled_candidate_count"], 1)
        self.assertIn("sampled_maximum", sweep)
        self.assertIn(
            sweep["surface_shape"],
            {"sharp_sampled_peak", "sharp_or_unstable", "moderate_peak", "broad_plateau"},
        )
        self.assertTrue(sweep["feature_curve_summaries"])
        self.assertTrue(sweep["pairwise_curve_summaries"])

        first_curve = sweep["feature_curve_summaries"][0]
        self.assertIn("best_alpha", first_curve)
        self.assertTrue(first_curve["points"])

        markdown = render_formula_weight_surface_markdown(report)
        self.assertIn("Formula Weight Surface", markdown)
        self.assertIn("Sweep Maxima", markdown)
        self.assertIn("Pairwise Probes", markdown)


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cell_grouping": [
            "scorer_id",
            "selection_mode",
            "heuristic_group",
            "manual_case_type",
            "shadow_contract",
            "source_rank_bin",
            "polysemy_band",
        ],
        "parameter_sweeps": [
            {
                "sweep_id": "linear_test_weight_sweep",
                "formula_class": "linear_weighted_sum",
                "sample_count": 8,
                "seed": "linear_test_weight_sweep_v1",
                "composition": "linear",
                "features": [
                    "rank_risk",
                    "rank_missing_rate",
                    "sense_risk",
                    "case_type_prior",
                    "coverage_gap",
                    "fixability",
                ],
            }
        ],
        "internal_split": {
            "method": "stable_hash_cell_id",
            "modulo": 3,
            "locked_eval_remainders": [0],
        },
        "data_help_priority": {
            "top_k": 4,
            "underfilled_target_rows": 4,
        },
    }


def _policy() -> dict[str, object]:
    return {
        "pair": "en-es",
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _difficulty_surface_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "case_traces": [
            _row(
                "phrase:001",
                "pre_outcome",
                "core_low_polysemy_control",
                "phrase_no_winner",
                "not_applicable",
                "1-500",
                "low_1_to_3",
                "negative_allow",
                "yes",
                175.0,
                1,
                1,
                0.01,
                0.04,
                "Yes, that was close.",
            ),
            _row(
                "positive:001",
                "pre_outcome",
                "missing_rank_probe",
                "positive_active",
                "full",
                "missing",
                "high_10_plus",
                "positive_abstain",
                "check",
                None,
                18,
                2,
                -0.01,
                0.02,
                "Please check the box.",
            ),
            _row(
                "positive:002",
                "pre_outcome",
                "missing_rank_probe",
                "positive_active",
                "full",
                "missing",
                "high_10_plus",
                "positive_allow",
                "check",
                None,
                18,
                2,
                0.04,
                0.07,
                "They ran a quick check.",
            ),
            _row(
                "sentinel:001",
                "outcome_informed_sentinel",
                "measured_missing_rank_high_failure_sentinel",
                "phrase_no_winner",
                "full",
                "missing",
                "high_10_plus",
                "negative_allow",
                "order",
                None,
                24,
                2,
                0.0,
                0.05,
                "Order, please.",
            ),
        ],
    }


def _row(
    case_id: str,
    selection_mode: str,
    heuristic_group: str,
    manual_case_type: str,
    shadow_contract: str,
    rank_bin: str,
    polysemy_band: str,
    product_outcome: str,
    trigger: str,
    rank: float | None,
    sense_count: int,
    pos_count: int,
    margin: float,
    active_score: float,
    sentence: str,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "scorer_id": "sentence_transformer_cosine",
        "selection_mode": selection_mode,
        "heuristic_group": heuristic_group,
        "manual_case_type": manual_case_type,
        "shadow_contract": shadow_contract,
        "source_rank_bin": rank_bin,
        "polysemy_band": polysemy_band,
        "product_outcome": product_outcome,
        "trigger": trigger,
        "source_rank": rank,
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
        "margin": margin,
        "active_score": active_score,
        "phrase_score_lead": None,
        "sentence": sentence,
    }


if __name__ == "__main__":
    unittest.main()
