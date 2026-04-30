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

from semantic_surface_pos_rescue_policy_validation_en_es import (  # noqa: E402
    build_surface_pos_rescue_policy_validation_report,
    render_surface_pos_rescue_policy_validation_markdown,
)


class SemanticSurfacePosRescuePolicyValidationTests(unittest.TestCase):
    def test_validation_applies_recommended_policy_to_scored_suite_rows(self) -> None:
        report = build_surface_pos_rescue_policy_validation_report(
            active_validation_report=_active_modifier_validation_report(),
            phrase_validation_report=_phrase_overreach_validation_report(),
            min_margin=0.0,
            phrase_prototype_margin=0.02,
            rescue_min_active_score=0.52,
            noun_max_phrase_lead=None,
            modifier_max_phrase_lead=0.02,
            generated_at="2026-04-30T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "scorer_backed_policy_pass")
        self.assertEqual(report["summary"]["harmful_replace_count"], 0)
        self.assertEqual(report["summary"]["false_abstain_count"], 0)
        self.assertEqual(report["summary"]["active_rescue_applied_count"], 1)
        self.assertEqual(
            report["summary"]["active_rescue_case_ids"],
            ["active:modifier:001"],
        )

        suite_rows = {row["suite_id"]: row for row in report["suite_results"]}
        self.assertTrue(suite_rows["active_shadow"]["passes"])
        self.assertTrue(suite_rows["phrase_no_winner"]["passes"])
        phrase_cases = {
            row["case_id"]: row for row in suite_rows["phrase_no_winner"]["policy_case_results"]
        }
        self.assertEqual(
            phrase_cases["phrase:modifier:low"]["surface_pos_rescue_blocked_reason"],
            "surface_pos_modifier_phrase_lead_above_ceiling",
        )
        self.assertEqual(
            phrase_cases["phrase:noun:bear"]["surface_pos_rescue_blocked_reason"],
            "surface_pos_active_score_below_floor",
        )

        markdown = render_surface_pos_rescue_policy_validation_markdown(report)
        self.assertIn("Surface-POS Rescue Policy Validation", markdown)
        self.assertIn("scorer_backed_policy_pass", markdown)
        self.assertIn("active:modifier:001", markdown)

    def test_validation_keeps_review_when_policy_still_misses(self) -> None:
        report = build_surface_pos_rescue_policy_validation_report(
            active_validation_report=_active_modifier_validation_report(),
            phrase_validation_report=_phrase_overreach_validation_report(),
            min_margin=0.0,
            phrase_prototype_margin=0.02,
            rescue_min_active_score=0.0,
            noun_max_phrase_lead=None,
            modifier_max_phrase_lead=None,
            generated_at="2026-04-30T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "scorer_backed_policy_review")
        self.assertEqual(report["summary"]["harmful_replace_count"], 2)
        self.assertEqual(
            report["summary"]["harmful_replace_case_ids"],
            ["phrase:modifier:low", "phrase:noun:bear"],
        )


def _active_modifier_validation_report() -> dict[str, object]:
    return {
        "status": "review",
        "decision": "heldout_review",
        "heldout_dataset_id": "active_modifier_cases",
        "heldout_case_scope": "active_shadow",
        "evidence_batch_id": "test_evidence",
        "configured_lane": {
            "scorer_id": "token_jaccard",
            "context_view": "masked_sentence",
            "decision_shape": "active_shadow_phrase_semantic_surface_pos",
        },
        "summary": {
            "max_harmful": 0,
            "max_false_abstain": 0,
        },
        "configured_case_results": [
            {
                "case_id": "active:modifier:001",
                "family_id": "fam:active",
                "trigger": "upset",
                "sentence": "She felt upset after the vote.",
                "gold_decision": "replace",
                "predicted_decision": "abstain",
                "active_score": 0.54,
                "strongest_shadow_score": 0.56,
                "phrase_control_score": 0.575,
                "active_evidence_text": "upset adjective sense: mentally troubled",
                "phrase_control_evidence_text": "turn something over",
                "surface_pos_signal": "active_modifier_frame",
            }
        ],
    }


def _phrase_overreach_validation_report() -> dict[str, object]:
    return {
        "status": "review",
        "decision": "heldout_review",
        "heldout_dataset_id": "phrase_cases",
        "heldout_case_scope": "phrase_no_winner",
        "evidence_batch_id": "test_evidence",
        "configured_lane": {
            "scorer_id": "token_jaccard",
            "context_view": "masked_sentence",
            "decision_shape": "active_shadow_phrase_semantic_surface_pos",
        },
        "summary": {
            "max_harmful": 0,
            "max_false_abstain": 0,
        },
        "configured_case_results": [
            {
                "case_id": "phrase:modifier:low",
                "family_id": "fam:low",
                "trigger": "low",
                "sentence": "The action brought him low.",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.588,
                "strongest_shadow_score": 0.611,
                "phrase_control_score": 0.651,
                "active_evidence_text": "low adverb sense: close to the ground",
                "phrase_control_evidence_text": "brought low in condition or status",
                "surface_pos_signal": "active_modifier_frame",
            },
            {
                "case_id": "phrase:noun:bear",
                "family_id": "fam:bear",
                "trigger": "bear",
                "sentence": "The bear crossed the road.",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "active_score": 0.495,
                "strongest_shadow_score": 0.591,
                "phrase_control_score": 0.567,
                "active_evidence_text": "bear noun sense: investor expecting prices to fall",
                "phrase_control_evidence_text": "large mammal with claws",
                "surface_pos_signal": "active_noun_frame",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
