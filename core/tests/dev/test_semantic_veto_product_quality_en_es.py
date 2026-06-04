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

from semantic_veto_product_quality_en_es import (  # noqa: E402
    build_product_quality_report,
    render_product_quality_markdown,
)


class SemanticVetoProductQualityTests(unittest.TestCase):
    def test_product_metrics_separate_stress_pass_from_promotion_evidence(self) -> None:
        report = build_product_quality_report(
            policy=_policy(),
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(
            report["decision"],
            "stress_lane_product_target_pass_representative_unmeasured",
        )

        overall = report["summary"]["overall"]
        self.assertEqual(overall["case_count"], 8)
        self.assertEqual(overall["positive_case_count"], 5)
        self.assertEqual(overall["negative_case_count"], 3)
        self.assertEqual(overall["positive_allow_count"], 4)
        self.assertEqual(overall["positive_abstain_count"], 1)
        self.assertEqual(overall["negative_abstain_count"], 2)
        self.assertEqual(overall["negative_allow_count"], 1)
        self.assertEqual(overall["positive_allow_rate"], 0.8)
        self.assertEqual(overall["negative_abstain_rate"], 0.6667)
        self.assertEqual(overall["target_checks"]["target_status"], "pass")
        self.assertEqual(overall["utility_score"], 4.6)
        self.assertGreater(overall["delta_vs_lexical_utility"], 0)

        failures = report["failure_rows"]
        self.assertEqual(len(failures), 2)
        self.assertEqual(
            {row["product_outcome"] for row in failures},
            {"positive_abstain", "negative_allow"},
        )

        lane = report["lanes"][0]
        self.assertEqual(lane["metrics"]["target_checks"]["target_status"], "pass")
        self.assertEqual(report["summary"]["measured_lane_types"], ["stress"])
        self.assertEqual(
            report["summary"]["planned_unmeasured_lane_types"],
            ["llm_expanded_eval", "representative"],
        )

        markdown = render_product_quality_markdown(report)
        self.assertIn("Semantic Veto Product Quality", markdown)
        self.assertIn("stress_lane_product_target_pass_representative_unmeasured", markdown)
        self.assertIn("representative", markdown)

    def test_product_metrics_can_read_sentence_veto_row_results(self) -> None:
        policy = _policy()
        policy["lanes"] = [
            {
                "lane_id": "representative_fixture",
                "lane_type": "representative",
                "reports": [
                    {
                        "source_id": "sentence_veto_fixture",
                        "suite_id": "sentence_veto_v10",
                        "report": {
                            "schema_version": 1,
                            "status": "ok",
                            "decision": "sentence_veto_fixture",
                            "summary": {
                                "cases_total": 4,
                                "gold_replace_cases": 2,
                                "gold_abstain_cases": 2,
                                "harmful_replace_count": 0,
                                "false_abstain_count": 1,
                            },
                            "row_results": [
                                _case("row-good-1", "replace", "replace"),
                                _case("row-good-2", "replace", "abstain"),
                                _case("row-bad-1", "abstain", "abstain"),
                                _case("row-bad-2", "abstain", "abstain"),
                            ],
                        },
                    }
                ],
            }
        ]
        policy["planned_lanes"] = [
            {"lane_id": "llm_fixture", "lane_type": "llm_expanded_eval"},
        ]

        report = build_product_quality_report(
            policy=policy,
            generated_at="2026-05-01T00:00:00Z",
        )

        overall = report["summary"]["overall"]
        self.assertEqual(overall["case_count"], 4)
        self.assertEqual(overall["positive_allow_rate"], 0.5)
        self.assertEqual(overall["negative_abstain_rate"], 1.0)
        self.assertEqual(overall["target_checks"]["target_status"], "fail")
        self.assertEqual(report["decision"], "product_target_missed")
        self.assertEqual(report["summary"]["measured_lane_types"], ["representative"])
        self.assertEqual(
            report["summary"]["planned_unmeasured_lane_types"],
            ["llm_expanded_eval"],
        )


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "test_policy",
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "utility_must_beat_lexical_baseline": True,
            "representative_lane_required_for_promotion": True,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
        "lanes": [
            {
                "lane_id": "stress_fixture",
                "lane_type": "stress",
                "reports": [
                    {
                        "source_id": "active_shadow_fixture",
                        "suite_id": "active_shadow",
                        "report": _active_report(),
                    },
                    {
                        "source_id": "phrase_fixture",
                        "suite_id": "phrase_no_winner",
                        "report": _phrase_report(),
                    },
                ],
            }
        ],
        "planned_lanes": [
            {"lane_id": "representative_fixture", "lane_type": "representative"},
            {"lane_id": "llm_fixture", "lane_type": "llm_expanded_eval"},
        ],
    }


def _active_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "heldout_review",
        "summary": {
            "case_count": 5,
            "gold_replace_cases": 4,
            "gold_abstain_cases": 1,
            "harmful_replace_count": 0,
            "false_abstain_count": 1,
        },
        "configured_case_results": [
            _case("good-1", "replace", "replace"),
            _case("good-2", "replace", "replace"),
            _case("good-3", "replace", "replace"),
            _case("good-4", "replace", "abstain"),
            _case("bad-1", "abstain", "abstain"),
        ],
    }


def _phrase_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "heldout_review",
        "summary": {
            "case_count": 3,
            "gold_replace_cases": 1,
            "gold_abstain_cases": 2,
            "harmful_replace_count": 1,
            "false_abstain_count": 0,
        },
        "configured_case_results": [
            _case("good-5", "replace", "replace"),
            _case("bad-2", "abstain", "abstain"),
            _case("bad-3", "abstain", "replace"),
        ],
    }


def _case(case_id: str, gold: str, predicted: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": f"family:{case_id}",
        "trigger": case_id.split("-")[0],
        "sentence": f"Fixture sentence for {case_id}.",
        "gold_decision": gold,
        "predicted_decision": predicted,
        "active_score": 0.7,
        "strongest_shadow_score": 0.4,
        "phrase_control_score": 0.5,
    }


if __name__ == "__main__":
    unittest.main()
