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

from semantic_veto_upstream_gap_audit_wave7 import (  # noqa: E402
    build_upstream_gap_audit_report,
    render_upstream_gap_audit_markdown,
)


class SemanticVetoUpstreamGapAuditWave7Tests(unittest.TestCase):
    def test_upstream_gap_audit_routes_residuals_by_bound_and_ceiling_evidence(self) -> None:
        report = build_upstream_gap_audit_report(
            residual_probe=_residual_probe(),
            bound_ladder=_bound_ladder(),
            current_evidence_ceiling=_ceiling(),
            frame_evidence=_frame_evidence(),
            phrase_evidence=_phrase_evidence(),
            admission_report=_admission_report(),
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(
            report["decision"],
            "upstream_work_required_before_acceptance_target",
        )
        self.assertTrue(report["research_only"])

        summary = report["summary"]
        self.assertEqual(summary["residual_case_count"], 3)
        self.assertEqual(summary["fixed_by_best_no_regression_count"], 1)
        self.assertEqual(summary["still_failing_after_best_no_regression_count"], 2)
        self.assertEqual(summary["final_admitted_row_count"], 326)
        self.assertEqual(summary["source_class_frame_row_count"], 90)
        self.assertEqual(summary["phrase_control_source_row_count"], 179)

        by_case = {row["case_id"]: row for row in report["case_audits"]}
        self.assertEqual(
            by_case["cast:001"]["bottleneck"],
            "general_guard_headroom_confirmed",
        )
        self.assertEqual(
            by_case["fix:001"]["bottleneck"],
            "evidence_representation_or_scorer_gap",
        )
        self.assertEqual(
            by_case["wrong:001"]["bottleneck"],
            "guard_signal_collides_with_valid_active_replace",
        )

        markdown = render_upstream_gap_audit_markdown(report)
        self.assertIn("Wave7 Upstream Gap Audit", markdown)
        self.assertIn("evidence_representation_or_scorer_gap", markdown)
        self.assertIn("guard_signal_collides_with_valid_active_replace", markdown)


def _residual_probe() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "targeted_remediation_required",
        "residual_cases": [
            {
                "case_id": "cast:001",
                "suite_id": "phrase_no_winner",
                "trigger": "cast",
                "sentence": "The director praised the cast.",
                "failure_class": "surface_rescue_overrode_dominant_phrase_control",
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
            {
                "case_id": "fix:001",
                "suite_id": "active_shadow",
                "trigger": "fix",
                "sentence": "Losing the key left us in a fix.",
                "failure_class": "shadow_overlap_overblocks_active",
                "decision_error_type": "false_abstain",
                "gold_decision": "replace",
                "predicted_decision": "abstain",
                "active_score": 0.62,
                "strongest_shadow_score": 0.74,
                "phrase_control_score": 0.71,
                "active_evidence_text": "difficult situation",
                "strongest_shadow_evidence_text": "repair",
                "phrase_control_evidence_text": "location",
            },
            {
                "case_id": "wrong:001",
                "suite_id": "phrase_no_winner",
                "trigger": "wrong",
                "sentence": "He rubbed the organizer the wrong way.",
                "failure_class": "surface_rescue_overrode_dominant_phrase_control",
                "decision_error_type": "harmful_replace",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.67,
                "strongest_shadow_score": 0.68,
                "phrase_control_score": 0.71,
                "active_evidence_text": "incorrect",
                "strongest_shadow_evidence_text": "treat unjustly",
                "phrase_control_evidence_text": "contrary to justice",
            },
        ],
    }


def _bound_ladder() -> dict[str, object]:
    return {
        "schema_version": 1,
        "case_bounds": [
            {
                "case_id": "cast:001",
                "score_visible_for_gold": True,
                "required_evidence_lane": "phrase_control",
                "representation_status": "phrase_signal_present_but_guard_failed",
                "llm_evidence_opportunity": "generate_exact_no_winner_phrase_evidence_and_guard_examples",
            },
            {
                "case_id": "fix:001",
                "score_visible_for_gold": False,
                "required_evidence_lane": "active",
                "representation_status": "evidence_present_but_not_score_visible",
                "llm_evidence_opportunity": "generate_stronger_contrastive_active_shadow_evidence",
            },
            {
                "case_id": "wrong:001",
                "score_visible_for_gold": True,
                "required_evidence_lane": "phrase_control",
                "representation_status": "phrase_signal_present_but_guard_failed",
                "llm_evidence_opportunity": "generate_exact_no_winner_phrase_evidence_and_guard_examples",
            },
        ],
    }


def _ceiling() -> dict[str, object]:
    return {
        "schema_version": 1,
        "summary": {
            "ceiling_assessment": {
                "ceiling_status": "partial_headroom_but_optimistic_ceiling_collapsed",
                "best_no_regression_correct_case_count": 42,
                "optimistic_correct_case_count": 46,
            }
        },
        "representative_policies": {
            "best_no_regression": {
                "fixed_case_ids": ["cast:001"],
            },
            "best_zero_harm": {
                "fixed_case_ids": ["cast:001", "wrong:001"],
            },
        },
    }


def _frame_evidence() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "source_class_frame_rows_ready",
        "summary": {"row_count": 90},
        "family_rows": [
            {
                "trigger": "cast",
                "row_count": 6,
                "matching_sense_count": 2,
                "active_row_count": 3,
                "shadow_row_count": 3,
                "sense_rows": [
                    {
                        "relation_type": "anchor_cue",
                        "support_sources": ["wiktionary_en_es"],
                    }
                ],
            },
            {
                "trigger": "fix",
                "row_count": 4,
                "matching_sense_count": 2,
                "active_row_count": 2,
                "shadow_row_count": 2,
                "sense_rows": [
                    {
                        "relation_type": "shadow_candidate",
                        "support_sources": ["wiktextract_en_es_translation_table"],
                    }
                ],
            },
        ],
    }


def _phrase_evidence() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "phrase_rows_ready",
        "summary": {"row_count": 179},
        "family_rows": [
            {
                "trigger": "cast",
                "candidate_sense_count": 8,
                "row_count": 6,
                "active_like_skip_count": 2,
            },
            {
                "trigger": "wrong",
                "candidate_sense_count": 7,
                "row_count": 5,
                "active_like_skip_count": 1,
            },
        ],
    }


def _admission_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "analysis_only",
        "summary": {"final_admitted_row_count": 326},
    }


if __name__ == "__main__":
    unittest.main()
