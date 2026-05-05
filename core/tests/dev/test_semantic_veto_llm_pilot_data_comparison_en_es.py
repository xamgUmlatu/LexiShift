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

from semantic_veto_llm_pilot_data_comparison_en_es import (  # noqa: E402
    build_data_comparison_report,
    render_data_comparison_markdown,
)


class SemanticVetoLlmPilotDataComparisonTests(unittest.TestCase):
    def test_report_compares_failed_llm_rows_to_manual_same_class_data(self) -> None:
        report = build_data_comparison_report(
            scoring_payload=_scoring_payload(),
            manual_dataset_payload=_manual_dataset_payload(),
            manual_matrix_payload=_manual_matrix_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "llm_manual_failed_case_data_comparison_complete",
        )
        self.assertEqual(report["summary"]["failed_llm_case_count"], 2)
        self.assertEqual(report["summary"]["manual_matching_case_count"], 3)

        rows = {row["case_id"]: row for row in report["comparison_rows"]}
        bank = rows["pilotrow:bank:phrase"]
        self.assertEqual(bank["source_overlap"]["largest_surface_overlap"], "phrase")
        self.assertEqual(bank["source_overlap"]["score_winner"], "active")
        self.assertIn(
            "phrase_surface_pattern_visible_but_not_weighted_enough",
            bank["data_difference"]["notes"],
        )

        check = rows["pilotrow:check:shadow"]
        self.assertEqual(check["manual_matching_summary"]["manual_failure_count"], 0)
        self.assertIn(
            "scorer_chose_active_evidence_over_blocker",
            check["data_difference"]["notes"],
        )
        self.assertEqual(
            check["nearest_manual_matching_case"]["product_outcome"],
            "negative_abstain",
        )

        markdown = render_data_comparison_markdown(report)
        self.assertIn("LLM vs Manual Failed-Case Data Comparison", markdown)
        self.assertIn("Score winner vs surface-pattern winner", markdown)


def _scoring_payload() -> dict[str, object]:
    return {
        "case_results": [
            {
                "case_id": "pilotrow:bank:phrase",
                "family_id": "bank",
                "trigger": "bank",
                "gold_type": "phrase_no_winner",
                "product_outcome": "negative_allow",
                "sentence": "Bank on getting there early.",
                "context_text": "___ on getting there early.",
                "active_score": 0.7,
                "strongest_shadow_score": 0.5,
                "phrase_control_score": 0.6,
                "shadow_lead": -0.2,
                "phrase_lead_to_best": -0.1,
                "active_evidence_text": "She deposited cash at the ___ before lunch.",
                "strongest_shadow_evidence_text": "Wildflowers grew along the muddy ___.",
                "phrase_control_evidence_text": "You can ___ on her support.",
                "veto_reason": "",
            },
            {
                "case_id": "pilotrow:check:shadow",
                "family_id": "check",
                "trigger": "check",
                "gold_type": "shadow_negative",
                "product_outcome": "negative_allow",
                "sentence": "At the gate, the final check clears the bag.",
                "context_text": "At the gate, the final ___ clears the bag.",
                "active_score": 0.76,
                "strongest_shadow_score": 0.6,
                "phrase_control_score": 0.5,
                "shadow_lead": -0.16,
                "phrase_lead_to_best": -0.26,
                "active_evidence_text": "The ___ cleared after the holiday weekend.",
                "strongest_shadow_evidence_text": "Please ___ the figures one more time.",
                "phrase_control_evidence_text": "You should ___ out the exhibit.",
                "veto_reason": "",
            },
        ]
    }


def _manual_dataset_payload() -> dict[str, object]:
    return {
        "families": [
            {
                "family_id": "bank",
                "active": {"sense_id": "bank:financial"},
                "cases": [
                    {
                        "case_id": "manual:bank:phrase",
                        "sentence": "You can bank on her support.",
                        "gold_decision": "abstain",
                        "gold_winner": "none",
                        "slice_tags": ["phrase_control"],
                    }
                ],
            },
            {
                "family_id": "check",
                "active": {"sense_id": "check:cheque"},
                "cases": [
                    {
                        "case_id": "manual:check:shadow:1",
                        "sentence": "Please check the figures one more time.",
                        "gold_decision": "abstain",
                        "gold_winner": "check:inspect",
                        "slice_tags": [],
                    },
                    {
                        "case_id": "manual:check:shadow:2",
                        "sentence": "Technicians check the pressure every hour.",
                        "gold_decision": "abstain",
                        "gold_winner": "check:inspect",
                        "slice_tags": [],
                    },
                ],
            },
        ]
    }


def _manual_matrix_payload() -> dict[str, object]:
    return {
        "case_results": [
            {
                "config_id": "control_st_masked_all_margin_phrase_override",
                "case_id": "manual:bank:phrase",
                "gold_winner_type": "none",
                "gold_decision": "abstain",
                "predicted_decision": "abstain",
                "active_score": 0.56,
                "strongest_shadow_score": 0.53,
            },
            {
                "config_id": "control_st_masked_all_margin_phrase_override",
                "case_id": "manual:check:shadow:1",
                "gold_winner_type": "shadow",
                "gold_decision": "abstain",
                "predicted_decision": "abstain",
                "active_score": 0.54,
                "strongest_shadow_score": 0.6,
            },
            {
                "config_id": "control_st_masked_all_margin_phrase_override",
                "case_id": "manual:check:shadow:2",
                "gold_winner_type": "shadow",
                "gold_decision": "abstain",
                "predicted_decision": "abstain",
                "active_score": 0.51,
                "strongest_shadow_score": 0.65,
            },
        ]
    }


if __name__ == "__main__":
    unittest.main()
