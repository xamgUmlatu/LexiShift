from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_productization_readiness_en_es import (  # noqa: E402
    build_productization_readiness_report,
    render_productization_readiness_markdown,
)


class SemanticVetoProductizationReadinessTests(unittest.TestCase):
    def test_reports_active_only_candidate_as_packaging_ready_but_not_runtime_published(
        self,
    ) -> None:
        report = build_productization_readiness_report(
            prompt_bakeoff_payload=_prompt_bakeoff_payload(),
            admission_payload=_admission_payload(),
            postprocess_payload=_postprocess_payload(),
            score_contribution_payload=_score_contribution_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "active_only_candidate_ready_for_source_packaging")
        self.assertEqual(report["runtime_publication_status"], "source_packaging_required")
        self.assertEqual(report["candidate"]["prompt_variant_id"], "v5_refresh_control")
        self.assertEqual(report["candidate"]["score_delta"]["false_abstain_delta"], -21)
        self.assertFalse(
            report["source_to_runtime_seams"]["llm_rows_compiled_into_runtime_inventory"]
        )

        check_results = {check["check_id"]: check["result"] for check in report["readiness_checks"]}
        self.assertEqual(check_results["offline_lift_observed"], "pass")
        self.assertEqual(check_results["source_packaging_required"], "block")

        markdown = render_productization_readiness_markdown(report)
        self.assertIn("Productization Readiness", markdown)
        self.assertIn("source_packaging_required", markdown)
        self.assertIn("v5_refresh_control", markdown)

    def test_reports_inventory_compile_when_source_packaging_exists(self) -> None:
        report = build_productization_readiness_report(
            prompt_bakeoff_payload=_prompt_bakeoff_payload(),
            admission_payload=_admission_payload(),
            postprocess_payload=_postprocess_payload(),
            score_contribution_payload=_score_contribution_payload(),
            source_packaging_payload=_source_packaging_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "active_only_candidate_ready_for_inventory_compile")
        self.assertEqual(report["runtime_publication_status"], "inventory_compile_required")
        self.assertTrue(report["source_to_runtime_seams"]["canonical_source_packaging_available"])
        self.assertEqual(report["source_to_runtime_seams"]["packaged_canonical_row_count"], 45)

        check_results = {check["check_id"]: check["result"] for check in report["readiness_checks"]}
        self.assertEqual(check_results["source_packaging_done"], "pass")
        self.assertEqual(check_results["inventory_compile_required"], "block")

        markdown = render_productization_readiness_markdown(report)
        self.assertIn("inventory_compile_required", markdown)
        self.assertIn("Packaged canonical rows", markdown)

    def test_reports_runtime_smoke_when_inventory_replay_exists(self) -> None:
        report = build_productization_readiness_report(
            prompt_bakeoff_payload=_prompt_bakeoff_payload(),
            admission_payload=_admission_payload(),
            postprocess_payload=_postprocess_payload(),
            score_contribution_payload=_score_contribution_payload(),
            source_packaging_payload=_source_packaging_payload(),
            inventory_replay_payload=_inventory_replay_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "active_only_candidate_ready_for_runtime_smoke")
        self.assertEqual(report["runtime_publication_status"], "runtime_smoke_required")
        self.assertTrue(report["source_to_runtime_seams"]["inventory_shaped_replay_available"])
        self.assertEqual(report["source_to_runtime_seams"]["inventory_replay_case_count"], 91)

        check_results = {check["check_id"]: check["result"] for check in report["readiness_checks"]}
        self.assertEqual(check_results["inventory_replay_done"], "pass")
        self.assertEqual(check_results["runtime_smoke_required"], "block")

        markdown = render_productization_readiness_markdown(report)
        self.assertIn("runtime_smoke_required", markdown)
        self.assertIn("Inventory-shaped replay available", markdown)

    def test_reports_manual_testing_ready_when_helper_runtime_smoke_passes(self) -> None:
        report = build_productization_readiness_report(
            prompt_bakeoff_payload=_prompt_bakeoff_payload(),
            admission_payload=_admission_payload(),
            postprocess_payload=_postprocess_payload(),
            score_contribution_payload=_score_contribution_payload(),
            source_packaging_payload=_source_packaging_payload(),
            inventory_replay_payload=_inventory_replay_payload(),
            helper_runtime_smoke_payload=_helper_runtime_smoke_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "active_only_candidate_ready_for_manual_testing")
        self.assertEqual(report["runtime_publication_status"], "manual_testing_ready")
        self.assertTrue(report["source_to_runtime_seams"]["helper_runtime_smoke_available"])
        self.assertTrue(
            report["source_to_runtime_seams"]["llm_rows_compiled_into_runtime_inventory"]
        )
        self.assertEqual(report["source_to_runtime_seams"]["helper_runtime_smoke_case_count"], 91)
        self.assertEqual(
            report["source_to_runtime_seams"]["helper_runtime_smoke_fallback_decision_count"],
            0,
        )
        self.assertEqual(
            report["source_to_runtime_seams"]["helper_runtime_smoke_harmful_replace_count"],
            1,
        )

        check_results = {check["check_id"]: check["result"] for check in report["readiness_checks"]}
        self.assertEqual(check_results["inventory_replay_done"], "pass")
        self.assertEqual(check_results["helper_runtime_smoke_done"], "pass")

        markdown = render_productization_readiness_markdown(report)
        self.assertIn("manual_testing_ready", markdown)
        self.assertIn("Helper runtime smoke available", markdown)


def _prompt_bakeoff_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "primary_view_id": "no_high_eval_overlap_sentence_only",
        "summary": {
            "best_primary_variant_id": "v5_refresh_control",
        },
    }


def _admission_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "summary": {
            "admitted_item_count": 48,
            "rejected_item_count": 0,
            "coverage_shortfall_count": 0,
        },
    }


def _postprocess_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "summary": {
            "high_eval_overlap_count": 3,
            "medium_eval_overlap_count": 6,
            "definition_like_count": 2,
            "pos_weak_count": 1,
            "target_lemma_in_note_count": 1,
        },
    }


def _score_contribution_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "summary": {
            "base": {
                "cases_total": 91,
                "decision_accuracy": 0.5055,
                "replace_recall": 0.0833,
                "false_abstain_count": 44,
                "harmful_replace_count": 1,
                "winner_accuracy": 0.7015,
            },
            "generated_active_only": {
                "cases_total": 91,
                "decision_accuracy": 0.7363,
                "replace_recall": 0.5208,
                "false_abstain_count": 23,
                "harmful_replace_count": 1,
                "winner_accuracy": 0.8060,
            },
        },
        "comparisons": {
            "generated_active_only": {
                "decision_accuracy_delta": 0.2308,
                "replace_recall_delta": 0.4375,
                "false_abstain_delta": -21,
                "harmful_replace_delta": 0,
                "winner_accuracy_delta": 0.1045,
            }
        },
    }


def _source_packaging_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "summary": {
            "packaged_row_count": 45,
            "runtime_publishable_row_count": 0,
        },
    }


def _inventory_replay_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "summary": {
            "case_count": 91,
            "applied_row_count": 45,
            "unapplied_row_count": 0,
            "comparison": {
                "decision_accuracy_delta": 0.2308,
            },
        },
    }


def _helper_runtime_smoke_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "summary": {
            "case_count": 91,
            "fallback_decision_count": 0,
            "decision_accuracy": 0.7692,
            "replace_recall": 0.5833,
            "harmful_replace_count": 1,
            "false_abstain_count": 20,
        },
    }


if __name__ == "__main__":
    unittest.main()
