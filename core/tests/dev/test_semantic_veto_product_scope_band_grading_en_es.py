from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_scope_band_grading_en_es import (  # noqa: E402
    build_product_scope_band_grading_report,
    render_product_scope_band_grading_markdown,
)


class SemanticVetoProductScopeBandGradingTests(unittest.TestCase):
    def test_grades_formula_bands_with_srs_case_mix_normalization(self) -> None:
        report = build_product_scope_band_grading_report(
            formula_sweep_payload=_formula_sweep_payload(),
            score_surface_payload=_score_surface_payload(),
            srs_case_mix_prior_payload=_srs_case_mix_prior_payload(),
            generated_at="2026-05-10T00:00:00Z",
            top_n_details=5,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "product_scope_band_grading_established")
        self.assertTrue(report["e2e_checks"]["base_product_prior_available"])
        self.assertTrue(report["e2e_checks"]["unmeasured_case_mass_visible"])

        best = report["summary"]["best_by_primary_band_grade"][0]
        self.assertEqual(best["formula_id"], "shadow_coverage_only")
        self.assertEqual(
            best["band_family_counts"], {"high_need": 1, "low_need": 1, "middle_need": 1}
        )
        self.assertGreater(best["primary_normalized_high_low_failure_delta"], 0)
        self.assertGreater(best["primary_max_unmeasured_target_weight"], 0)

        markdown = render_product_scope_band_grading_markdown(report)
        self.assertIn("Product-Scope Band Grading", markdown)
        self.assertIn("SRS high-low", markdown)


def _formula_sweep_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "repaired_full_band_formula_sweep_established",
        "summary": {
            "best_by_scope": [
                {
                    "scorer_id": "scorer",
                    "formula_id": "shadow_coverage_only",
                }
            ]
        },
        "observations": [
            _observation("family-high", 1.0),
            _observation("family-middle", 0.6),
            _observation("family-low", 0.2),
        ],
        "comparison_rows": [
            {
                "scorer_id": "scorer",
                "formula_id": "shadow_coverage_only",
                "formula_family": "fixed_single_signal",
                "scope_id": "scorer::shadow_coverage_only",
                "weights": {"shadow_coverage_risk": 1.0},
                "discovery_spearman": 1.0,
                "internal_locked_eval_spearman": 1.0,
                "top_k_lift": 2.0,
            },
            {
                "scorer_id": "scorer",
                "formula_id": "source_zipf_only",
                "formula_family": "fixed_single_signal",
                "scope_id": "scorer::source_zipf_only",
                "weights": {"source_zipf_risk": 1.0},
                "discovery_spearman": 0.0,
                "internal_locked_eval_spearman": 0.0,
                "top_k_lift": 1.0,
            },
        ],
    }


def _observation(family_id: str, shadow_risk: float) -> dict[str, object]:
    return {
        "scorer_id": "scorer",
        "family_id": family_id,
        "observed_failure_rate": shadow_risk,
        "features": {
            "source_zipf_risk": 0.4,
            "target_zipf_risk": 0.4,
            "polysemy_risk": 0.4,
            "pos_shape_risk": 0.4,
            "shadow_coverage_risk": shadow_risk,
        },
    }


def _score_surface_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "product_scope_selected_candidate_surface_established",
        "row_results": [
            _row("family-high", "positive_active", "replace", "abstain"),
            _row("family-high", "shadow_negative", "abstain", "replace"),
            _row("family-middle", "positive_active", "replace", "replace"),
            _row("family-middle", "shadow_negative", "abstain", "abstain"),
            _row("family-low", "positive_active", "replace", "replace"),
            _row("family-low", "shadow_negative", "abstain", "abstain"),
        ],
    }


def _row(family_id: str, case_type: str, gold: str, predicted: str) -> dict[str, object]:
    error = ""
    if gold == "replace" and predicted == "abstain":
        error = "false_abstain"
    if gold == "abstain" and predicted == "replace":
        error = "harmful_replace"
    return {
        "scorer_id": "scorer",
        "family_id": family_id,
        "trigger": family_id,
        "gold_decision": gold,
        "predicted_decision": predicted,
        "error_type": error,
        "slice_dimensions": {"manual_case_type": [case_type]},
    }


def _srs_case_mix_prior_payload() -> dict[str, object]:
    return {
        "decision": "srs_case_mix_prior_established",
        "scenario_rows": [
            {
                "scenario_id": "base_product_prior",
                "description": "unit prior",
                "band_prior_rows": [
                    {
                        "srs_pair_share": 1.0,
                        "p_positive_active": 0.70,
                        "p_shadow_negative": 0.20,
                        "p_phrase_no_winner": 0.10,
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
