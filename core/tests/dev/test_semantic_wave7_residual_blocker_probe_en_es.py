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

from semantic_wave7_residual_blocker_probe_en_es import (  # noqa: E402
    build_wave7_residual_blocker_probe_report,
    render_wave7_residual_blocker_probe_markdown,
)


class SemanticWave7ResidualBlockerProbeTests(unittest.TestCase):
    def test_probe_splits_residual_blockers_before_scalar_tuning(self) -> None:
        report = build_wave7_residual_blocker_probe_report(
            active_report=_active_report(),
            phrase_report=_phrase_report(),
            rescue_sweep=_rescue_sweep(),
            no_surface_margin_sweep=_no_surface_margin_sweep(),
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "targeted_remediation_required")
        self.assertEqual(report["summary"]["residual_case_count"], 5)
        self.assertEqual(report["summary"]["active_shadow_failure_count"], 3)
        self.assertEqual(report["summary"]["phrase_no_winner_failure_count"], 2)
        self.assertFalse(report["summary"]["scalar_policy_pass_available"])

        classes = {row["failure_class"]: row for row in report["class_summaries"]}
        self.assertEqual(classes["shadow_quantity_evidence_underweighted"]["case_count"], 1)
        self.assertEqual(
            classes["phrase_preemption_overreach_on_strong_active"]["triggers"], ["even"]
        )
        self.assertEqual(classes["shadow_overlap_overblocks_active"]["triggers"], ["fix"])
        self.assertEqual(
            classes["surface_rescue_overrode_dominant_phrase_control"]["case_count"],
            1,
        )
        self.assertEqual(
            classes["surface_rescue_leaks_when_phrase_control_close"]["case_count"],
            1,
        )

        markdown = render_wave7_residual_blocker_probe_markdown(report)
        self.assertIn("Wave7 Residual Blocker Probe", markdown)
        self.assertIn("targeted_remediation_required", markdown)
        self.assertIn("shadow_quantity_evidence_underweighted", markdown)
        self.assertIn("Do not tune one global scalar policy yet", markdown)


def _active_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "heldout_review",
        "heldout_dataset_id": "wave7_active_shadow",
        "heldout_case_scope": "active_shadow",
        "summary": {"case_count": 3, "harmful_replace_count": 1, "false_abstain_count": 2},
        "configured_case_results": [
            {
                "case_id": "gross:002",
                "family_id": "gross",
                "trigger": "gross",
                "sentence": "The shop ordered a gross of pencils.",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "predicted_winner": "gross:active",
                "predicted_winner_type": "active",
                "active_score": 0.67,
                "strongest_shadow_score": 0.63,
                "phrase_control_score": 0.62,
                "phrase_prototype_margin": 0.02,
                "active_evidence_text": "gross adjective sense: causing disgust",
                "strongest_shadow_evidence_text": "gross noun sense: twelve dozen",
                "phrase_control_evidence_text": "before deductions",
            },
            {
                "case_id": "fix:001",
                "family_id": "fix",
                "trigger": "fix",
                "sentence": "Losing the key left us in a fix.",
                "gold_decision": "replace",
                "predicted_decision": "abstain",
                "predicted_winner": "fix:shadow",
                "predicted_winner_type": "shadow",
                "active_score": 0.62,
                "strongest_shadow_score": 0.74,
                "phrase_control_score": 0.71,
                "phrase_prototype_margin": 0.02,
                "active_evidence_text": "difficult situation",
                "strongest_shadow_evidence_text": "restore something broken",
                "phrase_control_evidence_text": "determine a location",
            },
            {
                "case_id": "even:001",
                "family_id": "even",
                "trigger": "even",
                "sentence": "At even, the village lamps began to glow.",
                "gold_decision": "replace",
                "predicted_decision": "abstain",
                "predicted_winner": "phrase_control",
                "predicted_winner_type": "none",
                "active_score": 0.72,
                "strongest_shadow_score": 0.53,
                "phrase_control_score": 0.56,
                "phrase_prototype_margin": 0.02,
                "phrase_preemption_hit": True,
                "matched_phrase_pattern": "at even the",
                "active_evidence_text": "time of evening before nightfall",
                "strongest_shadow_evidence_text": "symmetrically arranged",
                "phrase_control_evidence_text": "even features",
            },
        ],
    }


def _phrase_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "heldout_review",
        "heldout_dataset_id": "wave7_phrase",
        "heldout_case_scope": "phrase_no_winner",
        "summary": {"case_count": 2, "harmful_replace_count": 2, "false_abstain_count": 0},
        "configured_case_results": [
            {
                "case_id": "cast:001",
                "family_id": "cast",
                "trigger": "cast",
                "sentence": "The director praised the cast.",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "predicted_winner": "cast:active",
                "predicted_winner_type": "active",
                "active_score": 0.56,
                "strongest_shadow_score": 0.61,
                "phrase_control_score": 0.73,
                "phrase_prototype_margin": 0.02,
                "surface_pos_signal": "active_noun_frame",
                "active_evidence_text": "object made by casting",
                "strongest_shadow_evidence_text": "assign a role",
                "phrase_control_evidence_text": "assign roles to actors",
            },
            {
                "case_id": "score:001",
                "family_id": "score",
                "trigger": "score",
                "sentence": "The composer wrote the score.",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "predicted_winner": "score:active",
                "predicted_winner_type": "active",
                "active_score": 0.73,
                "strongest_shadow_score": 0.71,
                "phrase_control_score": 0.738,
                "phrase_prototype_margin": 0.02,
                "surface_pos_signal": "active_noun_frame",
                "active_evidence_text": "twenty items",
                "strongest_shadow_evidence_text": "make a point",
                "phrase_control_evidence_text": "musical composition",
            },
        ],
    }


def _rescue_sweep() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "rescue_policy_review",
        "summary": {"policy_count": 25, "passing_policy_count": 0, "recommended_policy": None},
    }


def _no_surface_margin_sweep() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "margin_review",
        "summary": {"row_count": 40, "passing_policy_count": 0, "recommended_policy": None},
    }


if __name__ == "__main__":
    unittest.main()
