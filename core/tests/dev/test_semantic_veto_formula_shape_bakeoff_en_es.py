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

from semantic_veto_formula_shape_bakeoff_en_es import (  # noqa: E402
    build_formula_shape_bakeoff_report,
    render_formula_shape_bakeoff_markdown,
)


class SemanticVetoFormulaShapeBakeoffTests(unittest.TestCase):
    def test_formula_shape_bakeoff_preserves_scientific_guardrails(self) -> None:
        report = build_formula_shape_bakeoff_report(
            manifest=_manifest(),
            difficulty_surface_payload=_difficulty_surface_payload(),
            policy_payload=_policy(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "formula_shape_bakeoff_established")
        self.assertEqual(report["summary"]["cell_count"], 4)
        self.assertEqual(report["summary"]["primary_cell_count"], 3)
        self.assertEqual(report["summary"]["sentinel_cell_count"], 1)
        self.assertEqual(report["summary"]["parameter_sweep_count"], 1)
        self.assertTrue(report["e2e_checks"]["missing_rank_cells_preserved"])
        self.assertTrue(report["e2e_checks"]["sentinel_cells_excluded_from_primary"])

        primary_rows = [
            row for row in report["comparison_rows"] if row["scope_id"] == "primary_all_scorers"
        ]
        self.assertTrue(primary_rows)
        self.assertTrue(any(row["formula_id"] == "gated_by_failure_class" for row in primary_rows))
        self.assertTrue(
            any(
                row["formula_id"] == "sweep_linear_test_weight_sweep_selected"
                for row in primary_rows
            )
        )

        sweep = report["parameter_sweep_results"][0]
        self.assertEqual(sweep["sweep_id"], "linear_test_weight_sweep")
        self.assertGreater(sweep["sampled_candidate_count"], 1)
        self.assertIn("selected_weights", sweep)
        self.assertNotIn("selected_score_rows", sweep)

        shuffled = next(
            row
            for row in report["negative_control_rows"]
            if row["formula_id"] == "shuffled_observed_order"
        )
        self.assertEqual(shuffled["cell_count"], report["summary"]["primary_cell_count"])

        top_cells = report["top_priority_cells"]
        self.assertEqual(
            len({row["cell_id"] for row in top_cells}),
            len(top_cells),
        )
        self.assertTrue(any(row["supporting_formulas"] for row in top_cells))

        markdown = render_formula_shape_bakeoff_markdown(report)
        self.assertIn("Formula-Shape Bakeoff", markdown)
        self.assertIn("Negative Controls", markdown)
        self.assertIn("Top Data-Help Cells", markdown)


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
        "formula_rows": [
            {"formula_id": "linear_baseline", "formula_class": "linear_weighted_sum"},
            {"formula_id": "gated_by_failure_class", "formula_class": "gated_formula"},
            {"formula_id": "rank_aggregation", "formula_class": "rank_aggregation"},
        ],
        "negative_controls": [
            {"control_id": "random_seeded"},
            {"control_id": "source_rank_only"},
            {"control_id": "shuffled_observed_order"},
        ],
        "parameter_sweeps": [
            {
                "sweep_id": "linear_test_weight_sweep",
                "formula_class": "linear_weighted_sum",
                "sample_count": 8,
                "seed": "linear_test_weight_sweep_v1",
                "composition": "linear",
                "selection_scope": "primary_discovery_all_scorers",
                "selection_metric_order": [
                    "spearman_rank_correlation",
                    "top_k_lift",
                    "negative_brier_score",
                ],
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
            "formula": (
                "exposure_weight * product_impact_weight * uncertainty_weight * "
                "predicted_failure_risk * fixability_weight * coverage_gap_weight"
            ),
            "manual_rows_by_priority": {"P0": 4, "P1": 3, "P2": 2},
            "llm_rows_by_priority": {"P0": 12, "P1": 8, "P2": 4},
            "locked_eval_rows_by_priority": {"P0": 6, "P1": 4, "P2": 2},
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
        "decision": "heuristic_difficulty_surface_established",
        "case_traces": [
            _row(
                "phrase:001",
                "sentence_transformer_cosine",
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
                "sentence_transformer_cosine",
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
                "sentence_transformer_cosine",
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
                "shadow:001",
                "sentence_transformer_cosine",
                "pre_outcome",
                "core_high_polysemy",
                "shadow_negative",
                "full",
                "1-500",
                "high_10_plus",
                "negative_abstain",
                "man",
                95.0,
                12,
                2,
                -0.08,
                0.03,
                "Volunteers man the phones.",
            ),
            _row(
                "sentinel:001",
                "sentence_transformer_cosine",
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
    scorer_id: str,
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
        "scorer_id": scorer_id,
        "source_id": scorer_id,
        "selection_mode": selection_mode,
        "heuristic_group": heuristic_group,
        "manual_case_type": manual_case_type,
        "shadow_contract": shadow_contract,
        "source_rank_bin": rank_bin,
        "polysemy_band": polysemy_band,
        "product_outcome": product_outcome,
        "trigger": trigger,
        "triggers": [trigger],
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
