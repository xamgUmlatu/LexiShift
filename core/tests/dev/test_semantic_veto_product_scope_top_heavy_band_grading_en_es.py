from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_product_scope_top_heavy_band_grading_en_es import (  # noqa: E402
    build_top_heavy_band_grading_report,
    render_top_heavy_band_grading_markdown,
)


class SemanticVetoProductScopeTopHeavyBandGradingTests(unittest.TestCase):
    def test_compares_top_heavy_slices_against_equal_tertile_control(self) -> None:
        report = build_top_heavy_band_grading_report(
            formula_sweep_payload=_formula_sweep_payload(),
            score_surface_payload=_score_surface_payload(),
            srs_case_mix_prior_payload=_srs_case_mix_prior_payload(),
            acceptance_audit_payload=_acceptance_audit_payload(),
            generated_at="2026-05-10T00:00:00Z",
            top_n_details=10,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "product_scope_top_heavy_band_grading_established")
        self.assertTrue(report["e2e_checks"]["equal_tertile_control_included"])
        self.assertTrue(report["e2e_checks"]["top_heavy_strategies_included"])
        self.assertTrue(report["e2e_checks"]["source_exposure_ranking_modes_included"])
        self.assertTrue(report["e2e_checks"]["accepted_candidate_rows_available"])

        accepted = report["summary"]["accepted_candidate_strategy_rows"]
        top_10_algorithm = _row(
            accepted,
            strategy="top_10_next_20_rest",
            ranking="algorithm_need",
        )
        top_10_exposure = _row(
            accepted,
            strategy="top_10_next_20_rest",
            ranking="source_exposure_product",
        )
        equal_control = _row(
            accepted,
            strategy="equal_tertiles_33_33_34",
            ranking="algorithm_need",
        )

        self.assertEqual(
            top_10_algorithm["band_family_counts"],
            {"high_need": 1, "low_need": 6, "middle_need": 3},
        )
        self.assertIn("rare-high->raro", ", ".join(top_10_algorithm["high_sample_triggers"]))
        self.assertIn("common-hard->común", ", ".join(top_10_exposure["high_sample_triggers"]))
        self.assertGreater(
            top_10_exposure["primary_high_rest_failure_delta"],
            equal_control["primary_high_rest_failure_delta"],
        )

        markdown = render_top_heavy_band_grading_markdown(report)
        self.assertIn("Top-Heavy Band Grading", markdown)
        self.assertIn("source_exposure_product", markdown)


def _row(rows: list[dict[str, object]], *, strategy: str, ranking: str) -> dict[str, object]:
    for row in rows:
        if row["band_strategy_id"] == strategy and row["ranking_mode_id"] == ranking:
            return row
    raise AssertionError(f"missing row for {strategy} / {ranking}")


def _acceptance_audit_payload() -> dict[str, object]:
    return {
        "decision": "accept_band_grading_v1_for_next_research_stage",
        "summary": {
            "candidate": {
                "scorer_id": "scorer",
                "formula_id": "shadow_coverage_only",
                "formula_family": "fixed_single_signal",
                "weights": {"shadow_coverage_risk": 1.0},
            }
        },
    }


def _formula_sweep_payload() -> dict[str, object]:
    observations = [
        _observation("rare-high", "raro", shadow=0.95, source=0.2),
        _observation("common-hard", "común", shadow=0.70, source=1.0),
    ]
    observations.extend(
        _observation(f"ordinary-{index}", f"meta{index}", shadow=0.40 - index * 0.02, source=0.45)
        for index in range(8)
    )
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
        "observations": observations,
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
        ],
    }


def _observation(family_id: str, target: str, *, shadow: float, source: float) -> dict[str, object]:
    return {
        "scorer_id": "scorer",
        "family_id": family_id,
        "trigger": family_id,
        "target_lemma": target,
        "observed_failure_rate": 0.0,
        "features": {
            "source_zipf_risk": source,
            "target_zipf_risk": 0.4,
            "polysemy_risk": 0.4,
            "pos_shape_risk": 0.4,
            "shadow_coverage_risk": shadow,
        },
    }


def _score_surface_payload() -> dict[str, object]:
    rows = []
    for family_id in ["rare-high", "common-hard", *[f"ordinary-{index}" for index in range(8)]]:
        should_fail = family_id == "common-hard"
        rows.append(
            _case(
                family_id,
                "positive_active",
                gold="replace",
                predicted="abstain" if should_fail else "replace",
            )
        )
        rows.append(
            _case(
                family_id,
                "shadow_negative",
                gold="abstain",
                predicted="replace" if should_fail else "abstain",
            )
        )
    return {
        "pair": "en-es",
        "decision": "product_scope_selected_candidate_surface_established",
        "row_results": rows,
    }


def _case(family_id: str, case_type: str, *, gold: str, predicted: str) -> dict[str, object]:
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
                        "p_shadow_negative": 0.30,
                        "p_phrase_no_winner": 0.0,
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
