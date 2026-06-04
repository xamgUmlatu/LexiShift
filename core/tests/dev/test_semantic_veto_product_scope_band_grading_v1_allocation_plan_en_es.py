from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es import (  # noqa: E402
    build_band_grading_v1_allocation_plan_report,
    render_band_grading_v1_allocation_plan_markdown,
)


class SemanticVetoProductScopeBandGradingV1AllocationPlanTests(unittest.TestCase):
    def test_selects_new_high_middle_low_families_from_accepted_v1_heuristic(self) -> None:
        report = build_band_grading_v1_allocation_plan_report(
            acceptance_audit_payload=_acceptance_audit_payload(),
            band_formula_payload=_band_formula_payload(),
            dataset_payload=_dataset_payload(),
            previous_plan_payload=_previous_plan_payload(),
            previous_admission_payload=_previous_admission_payload(),
            generated_at="2026-05-10T00:00:00Z",
            selection_seed="unit-seed",
            high_size=2,
            middle_size=2,
            low_size=2,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "product_scope_band_grading_v1_allocation_plan_established",
        )
        self.assertEqual(
            report["summary"]["selected_arm_counts"],
            {"high_need": 2, "low_control": 2, "middle_control": 2},
        )
        self.assertEqual(report["summary"]["selected_previous_overlap_count"], 0)
        self.assertTrue(report["e2e_checks"]["acceptance_audit_ok"])
        self.assertTrue(report["e2e_checks"]["no_previous_overlap_selected"])
        self.assertTrue(
            report["e2e_checks"]["generation_contract_compatible_with_existing_request_renderer"]
        )
        self.assertFalse(any(row["previous_pilot_overlap"] for row in report["selected_families"]))
        self.assertEqual(
            report["pilot_manifest"]["selection"]["candidate_id"], "product_scope_band_grading_v1"
        )

        markdown = render_band_grading_v1_allocation_plan_markdown(report)
        self.assertIn("Band-Grading v1 Allocation Plan", markdown)
        self.assertIn("Previous-overlap selected", markdown)


def _acceptance_audit_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "decision": "accept_band_grading_v1_for_next_research_stage",
        "summary": {
            "candidate": {
                "scorer_id": "safe_sentence_transformer",
                "formula_id": "sweep_linear_fixture",
                "formula_family": "sweep_linear",
                "weights": {"source_zipf_risk": 1.0},
                "primary_grade_score": 0.2,
                "primary_normalized_high_low_failure_delta": 0.2,
                "primary_normalized_order_score": 1.0,
                "raw_high_low_failure_delta": 0.1,
            }
        },
    }


def _band_formula_payload() -> dict[str, object]:
    observations = []
    for index, score in enumerate((0.95, 0.9, 0.85, 0.55, 0.5, 0.45, 0.2, 0.15, 0.1)):
        observations.append(
            {
                "family_id": f"family:{index}",
                "scorer_id": "safe_sentence_transformer",
                "trigger": f"trigger{index}",
                "target_lemma": f"target{index}",
                "features": {"source_zipf_risk": score},
                "feature_context": {"source_zipf_band_en": "zipf_4_to_5_common"},
                "observed_failure_rate": 1.0 - score,
                "failure_count": index,
                "harmful_replace_count": 0,
                "false_abstain_count": index,
                "case_count": 10,
            }
        )
    return {
        "pair": "en-es",
        "decision": "repaired_full_band_formula_sweep_established",
        "observations": observations,
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "fixture",
        "manual_review_state": "approved_by_user",
        "families": [_family(index) for index in range(9)],
    }


def _previous_plan_payload() -> dict[str, object]:
    return {
        "pilot_families": [
            {"family_id": "family:0"},
            {"family_id": "family:3"},
            {"family_id": "family:6"},
        ]
    }


def _previous_admission_payload() -> dict[str, object]:
    return {
        "admitted_items": [
            {"family_id": "family:0"},
            {"family_id": "family:3"},
            {"family_id": "family:6"},
        ]
    }


def _family(index: int) -> dict[str, object]:
    return {
        "family_id": f"family:{index}",
        "trigger": f"trigger{index}",
        "active": {
            "sense_id": f"family:{index}:active",
            "target_lemma": f"target{index}",
            "canonical_pos": "noun",
            "evidence_views": {"all_evidence_text": f"trigger{index} active"},
        },
        "shadows": [
            {
                "sense_id": f"family:{index}:shadow",
                "target_lemma": f"shadow{index}",
                "canonical_pos": "noun",
                "evidence_views": {"all_evidence_text": f"trigger{index} shadow"},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
