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

from semantic_veto_bound_ladder_wave7_residuals import (  # noqa: E402
    build_bound_ladder_report,
    render_bound_ladder_markdown,
)


class SemanticVetoBoundLadderWave7ResidualsTests(unittest.TestCase):
    def test_bound_ladder_separates_current_evidence_and_llm_lanes(self) -> None:
        report = build_bound_ladder_report(
            residual_probe=_residual_probe(),
            admission_report=_admission_report(),
            frame_evidence_report=_frame_evidence_report(),
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertTrue(report["research_only"])
        self.assertEqual(report["decision"], "bounds_reference_only_llm_lane_unmeasured")

        summary = report["summary"]
        self.assertEqual(summary["locked_case_count"], 6)
        self.assertEqual(summary["current_correct_case_count"], 3)
        self.assertEqual(summary["current_harmful_replace_count"], 2)
        self.assertEqual(summary["current_false_abstain_count"], 1)
        self.assertEqual(summary["score_visible_residual_count"], 2)
        self.assertEqual(summary["not_score_visible_residual_count"], 1)
        self.assertEqual(summary["runtime_policy_family_passing_count"], 0)

        bounds = report["bounds"]
        self.assertEqual(
            bounds["llm_pipeline_bound"]["status"],
            "not_measured",
        )
        self.assertEqual(
            bounds["current_evidence_upper_bound"][
                "optimistic_accuracy_if_all_score_visible_residuals_are_safely_recovered"
            ],
            0.8333,
        )
        self.assertEqual(
            bounds["admitted_evidence_presence_bound"]["admitted_gold_evidence_present_count"],
            3,
        )

        by_case = {row["case_id"]: row for row in report["case_bounds"]}
        self.assertTrue(by_case["gross:002"]["score_visible_for_gold"])
        self.assertFalse(by_case["fix:001"]["score_visible_for_gold"])
        self.assertTrue(by_case["cast:001"]["score_visible_for_gold"])
        self.assertEqual(
            by_case["fix:001"]["llm_evidence_opportunity"],
            "generate_stronger_contrastive_active_shadow_evidence",
        )

        markdown = render_bound_ladder_markdown(report)
        self.assertIn("Semantic Veto Bound Ladder", markdown)
        self.assertIn("LLM pipeline bound", markdown)
        self.assertIn("not_measured", markdown)


def _residual_probe() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "targeted_remediation_required",
        "score_surface": {
            "active_report": {
                "case_count": 4,
                "harmful_replace_count": 1,
                "false_abstain_count": 1,
            },
            "phrase_report": {
                "case_count": 2,
                "harmful_replace_count": 1,
                "false_abstain_count": 0,
            },
        },
        "policy_context": {
            "rescue_sweep": {"passing_policy_count": 0},
            "no_surface_margin_sweep": {"passing_policy_count": 0},
            "summary": {"combined_passing_policy_count": 0},
        },
        "residual_cases": [
            {
                "case_id": "gross:002",
                "suite_id": "active_shadow",
                "trigger": "gross",
                "sentence": "The shop ordered a gross of pencils.",
                "failure_class": "shadow_quantity_evidence_underweighted",
                "remediation_lane": "shadow_evidence_repair",
                "decision_error_type": "harmful_replace",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.67,
                "strongest_shadow_score": 0.72,
                "phrase_control_score": 0.63,
                "active_evidence_text": "gross adjective sense: causing disgust",
                "strongest_shadow_evidence_text": "a gross is a count for ordered goods",
                "phrase_control_evidence_text": "gross details",
            },
            {
                "case_id": "fix:001",
                "suite_id": "active_shadow",
                "trigger": "fix",
                "sentence": "Losing the key left us in a fix.",
                "failure_class": "shadow_overlap_overblocks_active",
                "remediation_lane": "shadow_evidence_repair",
                "decision_error_type": "false_abstain",
                "gold_decision": "replace",
                "predicted_decision": "abstain",
                "active_score": 0.62,
                "strongest_shadow_score": 0.74,
                "phrase_control_score": 0.71,
                "active_evidence_text": "fix noun sense: a difficult situation",
                "strongest_shadow_evidence_text": "restore something broken",
                "phrase_control_evidence_text": "determine a location",
            },
            {
                "case_id": "cast:001",
                "suite_id": "phrase_no_winner",
                "trigger": "cast",
                "sentence": "The director praised the cast.",
                "failure_class": "surface_rescue_overrode_dominant_phrase_control",
                "remediation_lane": "phrase_no_winner_rescue_guard",
                "decision_error_type": "harmful_replace",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.56,
                "strongest_shadow_score": 0.61,
                "phrase_control_score": 0.73,
                "active_evidence_text": "act of throwing",
                "strongest_shadow_evidence_text": "cast a spell",
                "phrase_control_evidence_text": "assign roles to actors",
            },
        ],
    }


def _admission_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "analysis_only",
        "summary": {
            "final_admitted_row_count": 326,
            "leakage_rejected_row_count": 6,
            "sense_rejected_row_count": 0,
            "semantic_contract_complete_family_count": 16,
            "phrase_contract_complete_family_count": 16,
        },
    }


def _frame_evidence_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "source_class_frame_rows_ready",
        "summary": {
            "family_count": 16,
            "matching_sense_count": 29,
            "row_count": 90,
        },
    }


if __name__ == "__main__":
    unittest.main()
