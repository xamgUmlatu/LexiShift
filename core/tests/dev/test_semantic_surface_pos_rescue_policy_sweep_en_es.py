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

from semantic_surface_pos_rescue_policy_sweep_en_es import (  # noqa: E402
    build_surface_pos_rescue_policy_sweep_report,
    render_surface_pos_rescue_policy_sweep_markdown,
)


class SemanticSurfacePosRescuePolicySweepTests(unittest.TestCase):
    def test_sweep_selects_policy_that_preserves_active_and_blocks_phrase_overreach(
        self,
    ) -> None:
        report = build_surface_pos_rescue_policy_sweep_report(
            active_report=_active_modifier_report(),
            phrase_report=_phrase_overreach_report(),
            min_margins=(0.0,),
            phrase_prototype_margins=(0.02,),
            rescue_min_active_scores=(0.0, 0.52),
            noun_max_phrase_leads=(None,),
            modifier_max_phrase_leads=(None, 0.03),
            generated_at="2026-04-29T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "rescue_policy_candidate_found")
        self.assertEqual(report["summary"]["passing_policy_count"], 1)
        self.assertEqual(
            report["summary"]["recommended_policy"],
            {
                "min_margin": 0.0,
                "phrase_prototype_margin": 0.02,
                "rescue_min_active_score": 0.52,
                "noun_max_phrase_lead": None,
                "modifier_max_phrase_lead": 0.03,
            },
        )

        rows = {(row["suite_id"], row["policy_id"]): row for row in report["rows"]}
        passing_active = rows[
            (
                "active_shadow",
                "m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.03",
            )
        ]
        self.assertTrue(passing_active["passes"])
        self.assertEqual(passing_active["active_rescue_case_ids"], ["active:modifier:001"])

        broad_phrase = rows[
            (
                "phrase_no_winner",
                "m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=none",
            )
        ]
        self.assertFalse(broad_phrase["passes"])
        self.assertEqual(
            broad_phrase["harmful_replace_case_ids"],
            ["phrase:modifier:low", "phrase:noun:bear"],
        )

        passing_phrase = rows[
            (
                "phrase_no_winner",
                "m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.03",
            )
        ]
        self.assertTrue(passing_phrase["passes"])
        self.assertEqual(
            passing_phrase["surface_pos_rescue_blocked_reasons"],
            {
                "surface_pos_active_score_below_floor": 1,
                "surface_pos_modifier_phrase_lead_above_ceiling": 1,
            },
        )

        markdown = render_surface_pos_rescue_policy_sweep_markdown(report)
        self.assertIn("Surface-POS Rescue Policy Sweep", markdown)
        self.assertIn("rescue_active=0.52", markdown)

    def test_sweep_reports_review_when_general_gates_cannot_rescue_active_blocker(
        self,
    ) -> None:
        report = build_surface_pos_rescue_policy_sweep_report(
            active_report=_active_unrescuable_noun_report(),
            phrase_report=_clean_phrase_report(),
            min_margins=(0.0,),
            phrase_prototype_margins=(0.02,),
            rescue_min_active_scores=(0.0, 0.52),
            noun_max_phrase_leads=(None,),
            modifier_max_phrase_leads=(None, 0.03),
            generated_at="2026-04-29T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "rescue_policy_review")
        self.assertIsNone(report["summary"]["recommended_policy"])
        self.assertEqual(report["recommendation"]["reason"], "no_policy_passed")

        blockers = report["recommendation"]["blockers_by_policy"]
        self.assertIn("m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=none", blockers)
        first_blocker = blockers["m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=none"][0]
        self.assertEqual(first_blocker["false_abstain_case_ids"], ["active:noun:leave"])

    def test_sweep_replays_strong_active_phrase_preemption_escape(self) -> None:
        report = build_surface_pos_rescue_policy_sweep_report(
            active_report=_strong_active_phrase_preemption_report(),
            phrase_report=_clean_phrase_report(),
            min_margins=(0.0,),
            phrase_prototype_margins=(0.02,),
            rescue_min_active_scores=(0.0,),
            noun_max_phrase_leads=(None,),
            modifier_max_phrase_leads=(None,),
            generated_at="2026-05-01T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        active_row = next(row for row in report["rows"] if row["suite_id"] == "active_shadow")
        self.assertTrue(active_row["passes"])
        self.assertEqual(active_row["false_abstain_case_ids"], [])


def _active_modifier_report() -> dict[str, object]:
    return {
        "status": "review",
        "heldout_dataset_id": "active_modifier_cases",
        "heldout_case_scope": "active_shadow",
        "configured_case_results": [
            {
                "case_id": "active:modifier:001",
                "gold_decision": "replace",
                "active_score": 0.54,
                "strongest_shadow_score": 0.56,
                "phrase_control_score": 0.575,
                "active_evidence_text": "upset adjective sense: mentally troubled",
                "phrase_control_evidence_text": "turn something over",
                "surface_pos_signal": "active_modifier_frame",
            }
        ],
    }


def _active_unrescuable_noun_report() -> dict[str, object]:
    return {
        "status": "review",
        "heldout_dataset_id": "active_noun_cases",
        "heldout_case_scope": "active_shadow",
        "configured_case_results": [
            {
                "case_id": "active:noun:leave",
                "gold_decision": "replace",
                "active_score": 0.58,
                "strongest_shadow_score": 0.59,
                "phrase_control_score": 0.57,
                "active_evidence_text": "leave noun sense: permission to be absent",
                "phrase_control_evidence_text": "go away from a place",
                "surface_pos_signal": "active_noun_frame",
                "surface_pos_rescue_blocked_reason": "strongest_shadow_not_verb_like",
            }
        ],
    }


def _strong_active_phrase_preemption_report() -> dict[str, object]:
    return {
        "status": "review",
        "heldout_dataset_id": "strong_active_phrase_cases",
        "heldout_case_scope": "active_shadow",
        "configured_case_results": [
            {
                "case_id": "active:phrase:even",
                "gold_decision": "replace",
                "active_score": 0.72,
                "strongest_shadow_score": 0.54,
                "phrase_control_score": 0.56,
                "active_evidence_text": "evening glow before nightfall",
                "phrase_control_evidence_text": "",
                "phrase_preemption_hit": True,
                "surface_pos_signal": "",
            }
        ],
    }


def _phrase_overreach_report() -> dict[str, object]:
    return {
        "status": "review",
        "heldout_dataset_id": "phrase_cases",
        "heldout_case_scope": "phrase_no_winner",
        "configured_case_results": [
            {
                "case_id": "phrase:modifier:low",
                "gold_decision": "abstain",
                "active_score": 0.588,
                "strongest_shadow_score": 0.611,
                "phrase_control_score": 0.651,
                "active_evidence_text": "low adverb sense: close to the ground",
                "phrase_control_evidence_text": "brought low in condition or status",
                "surface_pos_signal": "active_modifier_frame",
            },
            {
                "case_id": "phrase:noun:bear",
                "gold_decision": "abstain",
                "active_score": 0.495,
                "strongest_shadow_score": 0.591,
                "phrase_control_score": 0.567,
                "active_evidence_text": "bear noun sense: investor expecting prices to fall",
                "phrase_control_evidence_text": "large mammal with claws",
                "surface_pos_signal": "active_noun_frame",
            },
        ],
    }


def _clean_phrase_report() -> dict[str, object]:
    return {
        "status": "ok",
        "heldout_dataset_id": "clean_phrase_cases",
        "heldout_case_scope": "phrase_no_winner",
        "configured_case_results": [
            {
                "case_id": "phrase:clean:001",
                "gold_decision": "abstain",
                "active_score": 0.45,
                "strongest_shadow_score": 0.5,
                "phrase_control_score": 0.6,
                "active_evidence_text": "active evidence",
                "phrase_control_evidence_text": "phrase evidence",
                "surface_pos_signal": "",
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
