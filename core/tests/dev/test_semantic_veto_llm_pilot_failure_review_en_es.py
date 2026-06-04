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

from semantic_veto_llm_pilot_failure_review_en_es import (  # noqa: E402
    build_failure_review_report,
    render_failure_review_markdown,
)


class SemanticVetoLlmPilotFailureReviewTests(unittest.TestCase):
    def test_review_separates_positive_strength_from_negative_gap(self) -> None:
        report = build_failure_review_report(
            scoring_payload=_scoring_payload(),
            manual_validation_payload=_manual_validation_payload(),
            product_quality_payload=_product_quality_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "llm_pilot_failure_review_complete")
        self.assertEqual(report["summary"]["failure_count"], 3)

        expectations = {row["expectation_id"]: row for row in report["expectation_rows"]}
        self.assertEqual(expectations["positive_allow"]["status"], "meets_target_and_comparator")
        self.assertEqual(
            expectations["negative_abstain_overall"]["status"],
            "below_manual_comparator",
        )
        self.assertEqual(expectations["phrase_no_winner_abstain"]["actual_rate"], 0.4)
        self.assertEqual(expectations["phrase_no_winner_abstain"]["manual_comparator_rate"], 0.625)
        self.assertEqual(expectations["phrase_no_winner_abstain"]["status"], "below_target")

        classes = {row["failure_class"]: row for row in report["failure_class_rows"]}
        self.assertEqual(classes["shadow_negative_active_score_dominated"]["case_count"], 1)
        self.assertEqual(classes["phrase_no_winner_phrase_score_not_dominant"]["case_count"], 1)
        self.assertEqual(classes["positive_overblocked_by_phrase_prototype"]["case_count"], 1)

        markdown = render_failure_review_markdown(report)
        self.assertIn("LLM Pilot Failure Review", markdown)
        self.assertIn("negative blocking is weaker", report["summary"]["main_read"])


def _scoring_payload() -> dict[str, object]:
    return {
        "summary": {
            "overall": {
                "case_count": 10,
                "positive_allow_count": 5,
                "positive_abstain_count": 1,
                "negative_abstain_count": 2,
                "negative_allow_count": 2,
                "positive_allow_rate": 0.8333,
                "negative_abstain_rate": 0.5,
                "utility_score": 5.4,
                "target_checks": {"target_status": "pass"},
            }
        },
        "gold_type_breakdowns": [
            {
                "scope_id": "positive_active",
                "case_count": 6,
                "positive_allow_count": 5,
                "positive_abstain_count": 1,
                "positive_allow_rate": 0.8333,
                "utility_score": 4.6,
                "target_checks": {"target_status": "pass"},
            },
            {
                "scope_id": "shadow_negative",
                "case_count": 2,
                "negative_abstain_count": 1,
                "negative_allow_count": 1,
                "negative_abstain_rate": 0.5,
                "utility_score": 0.2,
                "target_checks": {"target_status": "pass"},
            },
            {
                "scope_id": "phrase_no_winner",
                "case_count": 5,
                "negative_abstain_count": 2,
                "negative_allow_count": 3,
                "negative_abstain_rate": 0.4,
                "utility_score": -0.2,
                "target_checks": {"target_status": "fail"},
            },
        ],
        "split_breakdowns": [],
        "case_results": [
            _case("shadow", "shadow_negative", "negative_allow", "", 0.7, 0.6, -0.1, 0.3, -0.4),
            _case("phrase", "phrase_no_winner", "negative_allow", "", 0.6, 0.55, -0.05, 0.5, -0.1),
            _case(
                "positive",
                "positive_active",
                "positive_abstain",
                "phrase_score_lead",
                0.55,
                0.5,
                -0.05,
                0.62,
                0.07,
            ),
        ],
    }


def _case(
    case_id: str,
    gold_type: str,
    outcome: str,
    veto_reason: str,
    active: float,
    shadow: float,
    shadow_lead: float,
    phrase: float,
    phrase_lead: float,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "gold_type": gold_type,
        "trigger": case_id,
        "product_outcome": outcome,
        "veto_reason": veto_reason,
        "active_score": active,
        "strongest_shadow_score": shadow,
        "shadow_lead": shadow_lead,
        "phrase_control_score": phrase,
        "phrase_lead_to_best": phrase_lead,
        "sentence": f"Fixture sentence for {case_id}.",
    }


def _manual_validation_payload() -> dict[str, object]:
    return {
        "summary": {
            "best_product_rank_row": {
                "positive_allow_rate": 0.8125,
                "negative_abstain_rate": 0.75,
                "source_breakdowns": [
                    {
                        "report_id": "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout",
                        "positive_allow_rate": 0.8125,
                        "negative_abstain_rate": 0.875,
                    },
                    {
                        "report_id": "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase",
                        "negative_abstain_rate": 0.625,
                    },
                ],
            }
        }
    }


def _product_quality_payload() -> dict[str, object]:
    return {
        "summary": {
            "overall": {
                "case_count": 4,
                "positive_allow_rate": 0.5,
                "negative_abstain_rate": 1.0,
                "utility_score": 3.0,
                "target_checks": {"target_status": "fail"},
            }
        }
    }


if __name__ == "__main__":
    unittest.main()
