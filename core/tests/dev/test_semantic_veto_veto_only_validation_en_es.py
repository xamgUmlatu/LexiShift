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

from semantic_veto_veto_only_validation_en_es import (  # noqa: E402
    build_veto_only_validation_report,
    render_veto_only_validation_markdown,
)


class SemanticVetoVetoOnlyValidationTests(unittest.TestCase):
    def test_validation_replays_configured_case_reports(self) -> None:
        report = build_veto_only_validation_report(
            policy=_policy(),
            validation_reports=[
                {
                    "report_id": "active_shadow_fixture",
                    "suite_id": "active_shadow",
                    "report": {
                        "schema_version": 1,
                        "status": "review",
                        "configured_lane": {
                            "scorer_id": "sentence_transformer_cosine",
                            "context_view": "raw_sentence",
                        },
                        "summary": {
                            "gold_replace_cases": 5,
                            "gold_abstain_cases": 5,
                            "harmful_replace_count": 2,
                            "false_abstain_count": 0,
                        },
                        "configured_case_results": [
                            *[
                                _case(f"positive-{index}", "replace", 0.6, 0.1)
                                for index in range(5)
                            ],
                            *[
                                _case(f"negative-{index}", "abstain", 0.1, 0.3)
                                for index in range(3)
                            ],
                            *[
                                _case(f"negative-open-{index}", "abstain", 0.3, 0.1)
                                for index in range(2)
                            ],
                        ],
                    },
                }
            ],
            shadow_lead_grid=[0.05],
            shadow_score_grid=[0.1],
            phrase_modes=["shadow_only"],
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "veto_only_validation_strict_source_product_target_pass_found",
        )
        self.assertEqual(report["summary"]["target_pass_count"], 1)
        self.assertEqual(report["summary"]["strict_target_pass_count"], 1)
        self.assertEqual(report["e2e_checks"]["input_case_rows_read"], 10)

        best = report["summary"]["best_product_rank_row"]
        self.assertEqual(best["positive_allow_rate"], 1.0)
        self.assertEqual(best["negative_abstain_rate"], 0.6)
        self.assertEqual(best["target_status"], "pass")
        self.assertEqual(best["strict_target_status"], "pass")
        self.assertEqual(
            best["source_breakdowns"][0]["report_id"],
            "active_shadow_fixture",
        )

        markdown = render_veto_only_validation_markdown(report)
        self.assertIn("Veto-Only Validation", markdown)
        self.assertIn("active_shadow_fixture", markdown)

    def test_validation_can_use_phrase_score_blocker(self) -> None:
        report = build_veto_only_validation_report(
            policy=_policy(),
            validation_reports=[
                {
                    "report_id": "phrase_fixture",
                    "suite_id": "phrase",
                    "report": {
                        "schema_version": 1,
                        "status": "review",
                        "configured_case_results": [
                            _case("positive-1", "replace", 0.6, 0.1, phrase_score=0.1),
                            _case("phrase-negative-1", "abstain", 0.6, 0.1, phrase_score=0.8),
                        ],
                    },
                }
            ],
            shadow_lead_grid=[0.05],
            shadow_score_grid=[0.1],
            phrase_modes=["shadow_only", "shadow_or_phrase_score"],
            generated_at="2026-05-01T00:00:00Z",
        )

        by_mode = {row["phrase_mode"]: row for row in report["rows"]}
        self.assertEqual(by_mode["shadow_only"]["negative_abstain_rate"], 0.0)
        self.assertEqual(by_mode["shadow_or_phrase_score"]["negative_abstain_rate"], 1.0)
        self.assertEqual(by_mode["shadow_or_phrase_score"]["target_status"], "pass")

    def test_overall_pass_is_review_when_a_source_breakdown_fails(self) -> None:
        report = build_veto_only_validation_report(
            policy=_policy(),
            validation_reports=[
                {
                    "report_id": "strong_positive_source",
                    "suite_id": "positive",
                    "report": {
                        "schema_version": 1,
                        "status": "ok",
                        "configured_case_results": [
                            _case(f"positive-{index}", "replace", 0.6, 0.1) for index in range(5)
                        ],
                    },
                },
                {
                    "report_id": "weak_negative_source",
                    "suite_id": "negative",
                    "report": {
                        "schema_version": 1,
                        "status": "ok",
                        "configured_case_results": [
                            *[
                                _case(f"negative-{index}", "abstain", 0.1, 0.3)
                                for index in range(2)
                            ],
                            *[
                                _case(f"negative-open-{index}", "abstain", 0.3, 0.1)
                                for index in range(3)
                            ],
                        ],
                    },
                },
                {
                    "report_id": "strong_negative_source",
                    "suite_id": "negative_control",
                    "report": {
                        "schema_version": 1,
                        "status": "ok",
                        "configured_case_results": [
                            _case(f"negative-control-{index}", "abstain", 0.1, 0.3)
                            for index in range(3)
                        ],
                    },
                },
            ],
            shadow_lead_grid=[0.05],
            shadow_score_grid=[0.1],
            phrase_modes=["shadow_only"],
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(
            report["decision"],
            "veto_only_validation_overall_product_target_pass_source_failures",
        )
        self.assertEqual(report["summary"]["target_pass_count"], 1)
        self.assertEqual(report["summary"]["strict_target_pass_count"], 0)
        row = report["rows"][0]
        self.assertEqual(row["target_status"], "pass")
        self.assertEqual(row["strict_target_status"], "fail")


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "test_policy",
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "utility_must_beat_lexical_baseline": True,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _case(
    case_id: str,
    gold_decision: str,
    active_score: float,
    shadow_score: float,
    *,
    phrase_score: float = 0.0,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": f"family:{case_id}",
        "trigger": case_id.split("-")[0],
        "sentence": f"Fixture sentence for {case_id}.",
        "gold_decision": gold_decision,
        "gold_winner_type": "active" if gold_decision == "replace" else "shadow",
        "active_score": active_score,
        "strongest_shadow_score": shadow_score,
        "phrase_control_score": phrase_score,
    }


if __name__ == "__main__":
    unittest.main()
