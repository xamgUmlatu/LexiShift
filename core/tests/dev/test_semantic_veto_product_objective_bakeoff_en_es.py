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

from semantic_veto_product_objective_bakeoff_en_es import (  # noqa: E402
    build_product_objective_bakeoff_report,
    render_product_objective_bakeoff_markdown,
)
from semantic_veto_product_quality_en_es import score_product_outcome_counts  # noqa: E402


class SemanticVetoProductObjectiveBakeoffTests(unittest.TestCase):
    def test_bakeoff_ranks_historical_rows_with_product_calculus(self) -> None:
        report = build_product_objective_bakeoff_report(
            policy=_policy(),
            sources=[
                {
                    "source_id": "sentence_sweep_fixture",
                    "source_type": "sentence_veto_sweep",
                    "report": _sentence_sweep_report(),
                },
                {
                    "source_id": "decision_matrix_fixture",
                    "source_type": "decision_rule_matrix",
                    "report": _decision_matrix_report(),
                },
            ],
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "historical_product_target_pass_found")
        self.assertEqual(report["summary"]["row_count"], 4)
        self.assertEqual(report["summary"]["target_pass_count"], 1)
        self.assertTrue(report["e2e_checks"]["all_source_rows_read"])
        self.assertEqual(report["e2e_checks"]["product_rows_emitted"], 4)

        best = report["summary"]["best_product_rank_row"]
        self.assertEqual(best["config_id"], "pass_target")
        self.assertEqual(best["positive_allow_rate"], 0.9)
        self.assertEqual(best["negative_abstain_rate"], 0.5)
        self.assertEqual(best["target_status"], "pass")

        closest = report["summary"]["closest_target_shape_row"]
        self.assertEqual(closest["config_id"], "pass_target")

        source_ids = {row["source_id"] for row in report["summary"]["best_by_source"]}
        self.assertEqual(source_ids, {"sentence_sweep_fixture", "decision_matrix_fixture"})

        markdown = render_product_objective_bakeoff_markdown(report)
        self.assertIn("Product Objective Bakeoff", markdown)
        self.assertIn("score_product_outcome_counts", markdown)
        self.assertIn("pass_target", markdown)

    def test_product_bakeoff_uses_same_count_math_as_product_quality(self) -> None:
        policy = _policy()
        source = {
            "source_id": "sentence_sweep_fixture",
            "source_type": "sentence_veto_sweep",
            "report": {
                "schema_version": 1,
                "status": "ok",
                "rows": [
                    {
                        "config_id": "same_math",
                        "gold_replace_cases": 5,
                        "gold_abstain_cases": 5,
                        "false_abstain_count": 1,
                        "harmful_replace_count": 2,
                    }
                ],
            },
        }
        report = build_product_objective_bakeoff_report(
            policy=policy,
            sources=[source],
            generated_at="2026-05-01T00:00:00Z",
        )

        row = report["rows"][0]
        direct = score_product_outcome_counts(
            outcome_counts={
                "positive_allow": 4,
                "positive_abstain": 1,
                "negative_abstain": 3,
                "negative_allow": 2,
            },
            weights=policy["utility_weights"],
            acceptance=policy["acceptance"],
        )

        self.assertEqual(row["utility_score"], direct["utility_score"])
        self.assertEqual(row["positive_allow_rate"], direct["positive_allow_rate"])
        self.assertEqual(row["negative_abstain_rate"], direct["negative_abstain_rate"])
        self.assertEqual(row["target_status"], direct["target_checks"]["target_status"])

    def test_no_passing_rows_stays_review_and_keeps_near_miss_visible(self) -> None:
        report = build_product_objective_bakeoff_report(
            policy=_policy(),
            sources=[
                {
                    "source_id": "matrix_fixture",
                    "source_type": "decision_rule_matrix",
                    "report": {
                        "schema_version": 1,
                        "status": "ok",
                        "config_rows": [
                            {
                                "config_id": "near_miss",
                                "scorer_id": "tfidf_cosine",
                                "decision_rule": "active_minus_strongest_shadow",
                                "gold_replace_cases": 10,
                                "gold_abstain_cases": 10,
                                "false_abstain_count": 2,
                                "harmful_replace_count": 6,
                            },
                            {
                                "config_id": "conservative",
                                "scorer_id": "tfidf_cosine",
                                "decision_rule": "active_minus_strongest_shadow",
                                "gold_replace_cases": 10,
                                "gold_abstain_cases": 10,
                                "false_abstain_count": 6,
                                "harmful_replace_count": 0,
                            },
                        ],
                    },
                }
            ],
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "historical_product_target_not_met")
        self.assertEqual(report["summary"]["target_pass_count"], 0)
        self.assertEqual(
            report["summary"]["closest_target_shape_row"]["config_id"],
            "near_miss",
        )
        self.assertIn(
            "No historical sweep or matrix row meets",
            report["summary"]["recommendation"][0],
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
    }


def _sentence_sweep_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "dataset_id": "fixture_v10",
        "rows": [
            {
                "config_id": "pass_target",
                "scorer_id": "tfidf_cosine",
                "context_view": "masked_sentence",
                "evidence_view": "all_evidence_text",
                "gold_replace_cases": 10,
                "gold_abstain_cases": 10,
                "false_abstain_count": 1,
                "harmful_replace_count": 5,
                "objective_score": 1.0,
            },
            {
                "config_id": "high_negative_low_positive",
                "scorer_id": "tfidf_cosine",
                "context_view": "masked_sentence",
                "evidence_view": "all_evidence_text",
                "gold_replace_cases": 10,
                "gold_abstain_cases": 10,
                "false_abstain_count": 7,
                "harmful_replace_count": 0,
                "objective_score": 2.0,
            },
        ],
    }


def _decision_matrix_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "dataset_id": "fixture_v10",
        "config_rows": [
            {
                "config_id": "too_permissive",
                "scorer_id": "tfidf_cosine",
                "sense_representation": "definition_and_example_rows_separate",
                "aggregation_rule": "source_weighted_top_k",
                "decision_rule": "pairwise_active_beats_all_shadows",
                "gold_replace_cases": 10,
                "gold_abstain_cases": 10,
                "false_abstain_count": 0,
                "harmful_replace_count": 8,
                "objective_score": 3.0,
            },
            {
                "config_id": "matrix_near_miss",
                "scorer_id": "sentence_transformer_cosine",
                "sense_representation": "all_evidence_text",
                "aggregation_rule": "single_concatenated_text",
                "decision_rule": "active_minus_strongest_shadow",
                "gold_replace_cases": 10,
                "gold_abstain_cases": 10,
                "false_abstain_count": 2,
                "harmful_replace_count": 6,
                "objective_score": 4.0,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
