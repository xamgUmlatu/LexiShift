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

from semantic_veto_product_scope_band_grading_acceptance_audit_en_es import (  # noqa: E402
    build_band_grading_acceptance_audit_report,
    render_band_grading_acceptance_audit_markdown,
)


class SemanticVetoProductScopeBandGradingAcceptanceAuditTests(unittest.TestCase):
    def test_accepts_candidate_when_sensitivity_neighbors_and_controls_pass(self) -> None:
        report = build_band_grading_acceptance_audit_report(
            band_grading_payload=_band_grading_payload(),
            generated_at="2026-05-10T00:00:00Z",
            near_neighbor_fraction=0.90,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "accept_band_grading_v1_for_next_research_stage")
        self.assertTrue(report["summary"]["normalization_all_positive"])
        self.assertTrue(report["summary"]["sentence_transformer_all_positive"])
        self.assertFalse(report["summary"]["backend_agnostic"])
        self.assertTrue(report["summary"]["candidate_beats_best_fixed_control"])
        self.assertEqual(report["summary"]["near_neighbor_count"], 5)

        markdown = render_band_grading_acceptance_audit_markdown(report)
        self.assertIn("Acceptance Audit", markdown)
        self.assertIn("Normalization Sensitivity", markdown)


def _band_grading_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "product_scope_band_grading_established",
        "summary": {
            "best_by_primary_band_grade": [
                _grade_row(
                    scorer_id="safe_sentence_transformer",
                    formula_id="candidate",
                    grade=0.20,
                    srs_delta=0.22,
                    raw_delta=0.10,
                    order=1.0,
                    weights={"source_zipf_risk": 0.2, "pos_shape_risk": 0.3},
                )
            ]
        },
        "formula_grade_rows": [
            _grade_row(
                scorer_id="safe_sentence_transformer",
                formula_id="candidate",
                grade=0.20,
                srs_delta=0.22,
                raw_delta=0.10,
                order=1.0,
                weights={"source_zipf_risk": 0.2, "pos_shape_risk": 0.3},
            ),
            _grade_row(
                scorer_id="safe_sentence_transformer",
                formula_id="neighbor",
                grade=0.19,
                srs_delta=0.20,
                raw_delta=0.09,
                order=1.0,
                weights={"source_zipf_risk": 0.25, "pos_shape_risk": 0.25},
            ),
            _grade_row(
                scorer_id="safe_sentence_transformer",
                formula_id="neighbor_two",
                grade=0.188,
                srs_delta=0.19,
                raw_delta=0.08,
                order=1.0,
                weights={"source_zipf_risk": 0.22, "pos_shape_risk": 0.28},
            ),
            _grade_row(
                scorer_id="safe_sentence_transformer",
                formula_id="neighbor_three",
                grade=0.186,
                srs_delta=0.18,
                raw_delta=0.07,
                order=1.0,
                weights={"source_zipf_risk": 0.18, "pos_shape_risk": 0.32},
            ),
            _grade_row(
                scorer_id="safe_sentence_transformer",
                formula_id="neighbor_four",
                grade=0.181,
                srs_delta=0.17,
                raw_delta=0.06,
                order=1.0,
                weights={"source_zipf_risk": 0.20, "pos_shape_risk": 0.30},
            ),
            _grade_row(
                scorer_id="other_sentence_transformer",
                formula_id="candidate",
                grade=0.12,
                srs_delta=0.14,
                raw_delta=0.07,
                order=1.0,
                weights={"source_zipf_risk": 0.2, "pos_shape_risk": 0.3},
            ),
            _grade_row(
                scorer_id="tfidf_best",
                formula_id="candidate",
                grade=0.0,
                srs_delta=-0.02,
                raw_delta=0.03,
                order=0.33,
                weights={"source_zipf_risk": 0.2, "pos_shape_risk": 0.3},
            ),
            _grade_row(
                scorer_id="safe_sentence_transformer",
                formula_id="pos_shape_only",
                grade=0.10,
                srs_delta=0.12,
                raw_delta=0.05,
                order=1.0,
                weights={"pos_shape_risk": 1.0},
                family="fixed_single_signal",
            ),
        ],
        "top_formula_band_details": [
            {
                **_grade_row(
                    scorer_id="safe_sentence_transformer",
                    formula_id="candidate",
                    grade=0.20,
                    srs_delta=0.22,
                    raw_delta=0.10,
                    order=1.0,
                    weights={"source_zipf_risk": 0.2, "pos_shape_risk": 0.3},
                ),
                "band_metrics": [
                    _band("high_need", {"global_test_case_mix": 0.30, "base_product_prior": 0.28}),
                    _band(
                        "middle_need", {"global_test_case_mix": 0.15, "base_product_prior": 0.14}
                    ),
                    _band("low_need", {"global_test_case_mix": 0.05, "base_product_prior": 0.06}),
                ],
            }
        ],
    }


def _grade_row(
    *,
    scorer_id: str,
    formula_id: str,
    grade: float,
    srs_delta: float,
    raw_delta: float,
    order: float,
    weights: dict[str, float],
    family: str = "sweep_linear",
) -> dict[str, object]:
    return {
        "scorer_id": scorer_id,
        "formula_id": formula_id,
        "formula_family": family,
        "primary_grade_score": grade,
        "primary_normalized_high_low_failure_delta": srs_delta,
        "primary_normalized_order_score": order,
        "raw_high_low_failure_delta": raw_delta,
        "band_family_counts": {"high_need": 2, "middle_need": 2, "low_need": 2},
        "weights": weights,
    }


def _band(band_id: str, target_rates: dict[str, float]) -> dict[str, object]:
    return {
        "band_id": band_id,
        "target_normalized_metrics": [
            {
                "target_id": target_id,
                "measured_only_failure_rate": rate,
                "measured_target_weight": 1.0,
                "unmeasured_target_weight": 0.0,
            }
            for target_id, rate in target_rates.items()
        ],
    }


if __name__ == "__main__":
    unittest.main()
