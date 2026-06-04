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

from semantic_source_failure_class_mining_en_es import (  # noqa: E402
    build_source_failure_class_mining_report,
    render_source_failure_class_mining_markdown,
)


class SemanticSourceFailureClassMiningTests(unittest.TestCase):
    def test_clean_small_slice_routes_to_inventory_expansion(self) -> None:
        report = build_source_failure_class_mining_report(
            primary_admission_payload=_admission_report(seed_false_abstains=0),
            primary_heldout_payload=_heldout_report(),
            comparator_admission_payloads=[
                _admission_report(
                    label_status="review",
                    sense_rejects=2,
                    semantic_gap_families=["fam:rock", "fam:case"],
                    seed_false_abstains=3,
                )
            ],
            comparator_sense_payloads=[
                {
                    "summary": {
                        "semantic_rejected_row_count": 2,
                        "rejection_reason_counts": {"competitor_sense_not_lower": 2},
                    }
                }
            ],
            source_report_payloads=[_source_report()],
            min_broad_family_count=50,
            min_broad_case_count=200,
            generated_at="2026-04-26T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "seed_pass_expand_inventory")
        self.assertEqual(report["summary"]["blocking_failure_class_count"], 0)
        self.assertEqual(report["quality_gate"]["promotion_readiness"], "ready_for_broader_breadth")
        self.assertIn("insufficient_family_breadth", report["quality_gate"]["tracked_residuals"])
        self.assertEqual(report["leverage"]["manual_overfit_risk"], "medium")
        self.assertEqual(report["leverage"]["best_comparator_false_abstain_delta"], -3)
        self.assertEqual(report["leverage"]["best_comparator_sense_reject_delta"], -2)
        self.assertIn(
            "source_mode_reduced_sense_rejects", report["leverage"]["generalization_signals"]
        )

        markdown = render_source_failure_class_mining_markdown(report)
        self.assertIn("Semantic Source Failure-class Mining", markdown)
        self.assertIn("seed_pass_expand_inventory", markdown)
        self.assertIn(
            "source_mode_reduced_seed_false_abstains", report["leverage"]["generalization_signals"]
        )

    def test_blocking_primary_failures_override_expansion(self) -> None:
        report = build_source_failure_class_mining_report(
            primary_admission_payload=_admission_report(sense_rejects=1),
            primary_sense_payload={
                "summary": {
                    "semantic_rejected_row_count": 1,
                    "rejection_reason_counts": {"competitor_sense_not_lower": 1},
                }
            },
            primary_heldout_payload=_heldout_report(harmful=1),
            source_report_payloads=[_source_report()],
            generated_at="2026-04-26T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "fix_blocking_failure_classes")
        self.assertIn("heldout_harmful_replace", report["quality_gate"]["blockers"])
        self.assertIn("sense_filter_rejects", report["quality_gate"]["tracked_residuals"])

        blocking_classes = [
            row["class_id"] for row in report["failure_classes"] if row["blocks_semantic_promotion"]
        ]
        self.assertIn("heldout_harmful_replace", blocking_classes)
        self.assertNotIn("primary_sense_reject", blocking_classes)

    def test_seed_and_phrase_residuals_are_tracked_without_blocking_semantic_lane(self) -> None:
        report = build_source_failure_class_mining_report(
            primary_admission_payload=_admission_report(
                seed_false_abstains=2,
                phrase_gap_families=["fam:bank"],
            ),
            primary_heldout_payload=_heldout_report(),
            source_report_payloads=[_source_report()],
            generated_at="2026-04-26T00:00:00Z",
        )

        self.assertEqual(report["decision"], "seed_pass_expand_inventory")
        self.assertEqual(report["summary"]["blocking_failure_class_count"], 0)
        self.assertIn("seed_ablation_false_abstain", report["quality_gate"]["tracked_residuals"])
        self.assertIn("phrase_contract_gap", report["quality_gate"]["tracked_residuals"])

        tracked_classes = {
            row["class_id"]: row for row in report["failure_classes"] if row["tracked_residual"]
        }
        self.assertIn("primary_seed_false_abstain", tracked_classes)
        self.assertIn("primary_phrase_contract_gap", tracked_classes)
        self.assertFalse(
            tracked_classes["primary_phrase_contract_gap"]["blocks_semantic_promotion"]
        )

    def test_margin_blockers_preserve_case_family_tokens(self) -> None:
        report = build_source_failure_class_mining_report(
            primary_admission_payload=_admission_report(),
            primary_heldout_payload=_heldout_report(),
            margin_sweep_payload={
                "status": "ok",
                "decision": "margin_candidate_found",
                "summary": {"recommended_min_margin": 0.005},
                "recommendation": {
                    "passing_margins": [0.005],
                    "blockers_by_margin": {
                        "0": [
                            {
                                "suite_id": "phrase_v2",
                                "harmful_replace_count": 1,
                                "false_abstain_count": 0,
                                "harmful_replace_case_ids": [
                                    "en-es:source-phrase-heldout:v2:board:002"
                                ],
                                "false_abstain_case_ids": [],
                            }
                        ],
                    },
                },
            },
            generated_at="2026-04-26T00:00:00Z",
        )

        margin_class = [
            row for row in report["failure_classes"] if row["class_id"] == "margin_policy_blockers"
        ][0]
        self.assertEqual(margin_class["family_tokens"], ["board"])

    def test_additional_heldout_suites_count_toward_breadth(self) -> None:
        report = build_source_failure_class_mining_report(
            primary_admission_payload=_admission_report(),
            primary_heldout_payload=_heldout_report(
                case_count=8,
                family_ids=["fam:look", "fam:use"],
            ),
            additional_heldout_payloads=[
                _heldout_report(
                    case_count=6,
                    family_ids=["fam:use", "fam:rest"],
                )
            ],
            additional_heldout_labels=["phrase_suite"],
            source_report_payloads=[_source_report()],
            min_broad_family_count=4,
            min_broad_case_count=20,
            generated_at="2026-04-26T00:00:00Z",
        )

        self.assertEqual(report["summary"]["heldout_suite_count"], 2)
        self.assertEqual(report["leverage"]["heldout_case_count"], 14)
        self.assertEqual(report["leverage"]["heldout_family_count"], 3)
        self.assertEqual(report["leverage"]["heldout_suite_count"], 2)
        self.assertIn("insufficient_family_breadth", report["quality_gate"]["tracked_residuals"])
        self.assertIn("phrase_suite", render_source_failure_class_mining_markdown(report))

    def test_portfolio_materialization_report_counts_as_source_breadth(self) -> None:
        report = build_source_failure_class_mining_report(
            primary_admission_payload=_admission_report(),
            primary_heldout_payload=_heldout_report(),
            source_report_payloads=[
                {
                    "schema_version": 1,
                    "decision": "source_portfolio_materialized",
                    "summary": {
                        "selected_family_count": 16,
                        "materialized_family_count": 16,
                        "candidate_row_count": 51,
                        "final_admitted_row_count": 51,
                        "semantic_contract_complete_family_count": 16,
                        "phrase_contract_complete_family_count": 0,
                    },
                }
            ],
            generated_at="2026-04-26T00:00:00Z",
        )

        self.assertEqual(report["leverage"]["source_row_count"], 51)
        self.assertEqual(report["leverage"]["source_family_count"], 16)
        source_row = report["source_reports"][0]
        self.assertEqual(source_row["evidence_mode"], "source_portfolio_materialized")
        self.assertEqual(source_row["target_families_with_active_wordnet"], 16)
        self.assertEqual(source_row["families_with_phrase_control_examples"], 0)


def _admission_report(
    *,
    label_status: str = "ok",
    sense_rejects: int = 0,
    semantic_gap_families: list[str] | None = None,
    phrase_gap_families: list[str] | None = None,
    seed_false_abstains: int = 0,
) -> dict[str, object]:
    semantic_gap_families = semantic_gap_families or []
    phrase_gap_families = phrase_gap_families or []
    return {
        "schema_version": 1,
        "status": label_status,
        "decision": "analysis_only",
        "summary": {
            "leakage_rejected_row_count": 0,
            "sense_rejected_row_count": sense_rejects,
            "final_admitted_row_count": 10,
            "families_total": 2,
            "semantic_contract_complete_family_count": 2 - len(semantic_gap_families),
            "phrase_contract_complete_family_count": 2 - len(phrase_gap_families),
            "best_ablation_row": {
                "harmful_replace_count": 0,
                "false_abstain_count": seed_false_abstains,
                "harmful_replace_case_ids": [],
                "false_abstain_case_ids": [
                    f"en-es:test:v1:rock:{index:03d}" for index in range(1, seed_false_abstains + 1)
                ],
                "replace_recall": 0.8,
                "decision_accuracy": 0.9,
            },
        },
        "residuals": {
            "semantic_gap_family_keys": semantic_gap_families,
            "phrase_containment_gap_family_keys": phrase_gap_families,
        },
    }


def _heldout_report(
    *,
    harmful: int = 0,
    false_abstain: int = 0,
    case_count: int = 8,
    family_ids: list[str] | None = None,
) -> dict[str, object]:
    family_ids = family_ids or ["fam:rock", "fam:case"]
    return {
        "schema_version": 1,
        "status": "ok" if harmful == 0 and false_abstain == 0 else "review",
        "decision": "heldout_pass" if harmful == 0 and false_abstain == 0 else "heldout_review",
        "heldout_families": [
            {
                "family_id": family_id,
                "trigger": family_id.rsplit(":", maxsplit=1)[-1],
                "case_count": max(1, case_count // max(len(family_ids), 1)),
                "replace_cases": 1,
                "abstain_cases": 1,
                "case_ids": [],
            }
            for family_id in family_ids
        ],
        "summary": {
            "status": "ok" if harmful == 0 and false_abstain == 0 else "review",
            "decision": "heldout_pass" if harmful == 0 and false_abstain == 0 else "heldout_review",
            "case_count": case_count,
            "family_count": len(family_ids),
            "gold_replace_cases": 4,
            "gold_abstain_cases": 4,
            "harmful_replace_count": harmful,
            "false_abstain_count": false_abstain,
            "harmful_replace_case_ids": [
                f"en-es:test:v1:rock:harmful:{index}" for index in range(1, harmful + 1)
            ],
            "false_abstain_case_ids": [
                f"en-es:test:v1:case:false-abstain:{index}" for index in range(1, false_abstain + 1)
            ],
            "replace_recall": 1.0 if false_abstain == 0 else 0.5,
            "decision_accuracy": 1.0 if harmful == 0 and false_abstain == 0 else 0.875,
        },
    }


def _source_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "summary": {
            "evidence_mode": "definition_preferred",
            "source_family_count": 2,
            "target_family_count": 2,
            "row_count": 10,
            "families_with_active_wordnet": 2,
            "families_with_shadow_wordnet": 2,
            "target_families_with_active_wordnet": 2,
            "target_families_with_shadow_wordnet": 2,
            "missing_active_family_keys": [],
            "missing_shadow_family_keys": [],
            "families_with_phrase_control_examples": 0,
        },
    }


if __name__ == "__main__":
    unittest.main()
