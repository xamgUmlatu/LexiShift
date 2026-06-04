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

from semantic_veto_current_evidence_ceiling_wave7 import (  # noqa: E402
    build_current_evidence_ceiling_report,
    render_current_evidence_ceiling_markdown,
)


class SemanticVetoCurrentEvidenceCeilingWave7Tests(unittest.TestCase):
    def test_ceiling_sweep_reports_partial_headroom_without_validating_ceiling(self) -> None:
        report = build_current_evidence_ceiling_report(
            active_report=_active_report(),
            phrase_report=_phrase_report(),
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertTrue(report["research_only"])

        summary = report["summary"]
        self.assertEqual(summary["baseline"]["correct_case_count"], 3)
        self.assertEqual(summary["baseline"]["harmful_replace_count"], 2)
        self.assertEqual(summary["baseline"]["false_abstain_count"], 0)
        self.assertEqual(
            summary["optimistic_current_evidence_bound"]["optimistic_correct_case_count"],
            5,
        )

        assessment = summary["ceiling_assessment"]
        self.assertEqual(
            assessment["ceiling_status"],
            "partial_headroom_but_optimistic_ceiling_collapsed",
        )
        self.assertEqual(assessment["best_no_regression_correct_case_count"], 4)
        self.assertEqual(assessment["best_no_regression_harmful_replace_count"], 1)
        self.assertEqual(
            assessment["best_no_regression_fixed_score_visible_residual_count"],
            1,
        )

        representatives = report["representative_policies"]
        self.assertEqual(representatives["best_zero_harm"]["harmful_replace_count"], 0)
        self.assertGreater(representatives["best_zero_harm"]["regressed_case_count"], 0)

        markdown = render_current_evidence_ceiling_markdown(report)
        self.assertIn("Current-Evidence Ceiling Validation", markdown)
        self.assertIn("partial_headroom_but_optimistic_ceiling_collapsed", markdown)
        self.assertIn("Top No-Regression Policies", markdown)


def _active_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "heldout_review",
        "heldout_dataset_id": "active",
        "heldout_case_scope": "active_shadow",
        "summary": {
            "case_count": 3,
            "harmful_replace_count": 1,
            "false_abstain_count": 0,
        },
        "configured_case_results": [
            {
                "case_id": "active-pass:001",
                "trigger": "pass",
                "gold_decision": "replace",
                "predicted_decision": "replace",
                "active_score": 0.70,
                "strongest_shadow_score": 0.60,
                "phrase_control_score": 0.68,
                "surface_pos_signal": "active_noun_frame",
                "active_rescue_applied": True,
            },
            {
                "case_id": "gross:002",
                "trigger": "gross",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.67,
                "strongest_shadow_score": 0.72,
                "phrase_control_score": 0.63,
                "surface_pos_signal": "active_modifier_frame",
                "active_rescue_applied": True,
            },
            {
                "case_id": "already-abstain:001",
                "trigger": "shadow",
                "gold_decision": "abstain",
                "predicted_decision": "abstain",
                "active_score": 0.50,
                "strongest_shadow_score": 0.80,
                "phrase_control_score": 0.30,
                "surface_pos_signal": "",
                "active_rescue_applied": False,
            },
        ],
    }


def _phrase_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "heldout_review",
        "heldout_dataset_id": "phrase",
        "heldout_case_scope": "phrase_no_winner",
        "summary": {
            "case_count": 2,
            "harmful_replace_count": 1,
            "false_abstain_count": 0,
        },
        "configured_case_results": [
            {
                "case_id": "cast:001",
                "trigger": "cast",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.62,
                "strongest_shadow_score": 0.61,
                "phrase_control_score": 0.65,
                "surface_pos_signal": "active_noun_frame",
                "active_rescue_applied": True,
            },
            {
                "case_id": "phrase-pass:001",
                "trigger": "music",
                "gold_decision": "replace",
                "predicted_decision": "replace",
                "active_score": 0.70,
                "strongest_shadow_score": 0.60,
                "phrase_control_score": 0.74,
                "surface_pos_signal": "active_noun_frame",
                "active_rescue_applied": True,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
