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

from semantic_veto_representative_gap_plan_en_es import (  # noqa: E402
    build_representative_gap_plan_report,
    render_representative_gap_plan_markdown,
)


class SemanticVetoRepresentativeGapPlanTests(unittest.TestCase):
    def test_gap_plan_creates_open_primary_slots_and_keeps_llm_proxy_separate(self) -> None:
        report = build_representative_gap_plan_report(
            manifest=_manifest(),
            stage1_report=_stage1_report(),
            representative_frame=_representative_frame(),
            llm_scoring=_llm_scoring(),
            product_quality=_product_quality(),
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "representative_gap_collection_plan_ready")
        self.assertEqual(report["summary"]["remaining_representative_rows_needed"], 3)
        self.assertEqual(report["summary"]["open_primary_collection_slots"], 3)
        self.assertEqual(report["summary"]["llm_locked_proxy_rows_available"], 1)
        self.assertEqual(report["summary"]["llm_discovery_rows_seen"], 1)
        self.assertEqual(
            report["summary"]["primary_slot_source_counts"],
            {
                "corpus_sampled_app_candidate_contexts": 1,
                "runtime_observed_semantic_admit_contexts": 2,
            },
        )

        slots = report["collection_slots"]
        self.assertEqual(len(slots), 3)
        self.assertTrue(all(row["counts_toward_primary_representative_target"] for row in slots))
        self.assertTrue(all(row["status"] == "open" for row in slots))

        proxy_rows = report["proxy_backstop_rows"]
        self.assertEqual(len(proxy_rows), 1)
        self.assertFalse(proxy_rows[0]["counts_toward_primary_representative_target"])

        markdown = render_representative_gap_plan_markdown(report)
        self.assertIn("Representative Gap Plan", markdown)
        self.assertIn("Open Slots", markdown)
        self.assertIn("Proxy Backstop", markdown)

    def test_missing_primary_source_lane_is_review(self) -> None:
        manifest = _manifest()
        manifest["source_lanes"] = [
            {
                "source_id": "llm_proxy",
                "source_class": "generated_proxy_backstop",
                "slot_quota": 0,
                "eligibility": "proxy_only_not_primary_representative",
            }
        ]

        report = build_representative_gap_plan_report(
            manifest=manifest,
            stage1_report=_stage1_report(),
            representative_frame=_representative_frame(),
            llm_scoring=_llm_scoring(),
            product_quality=_product_quality(),
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("no_primary_source_lane_for_shortfall", report["summary"]["issues"])

    def test_closed_gap_has_no_open_slots(self) -> None:
        stage1 = _stage1_report()
        stage1["decision"] = "sampling_stage1_materialized"
        stage1["summary"]["available_representative_rows"] = 5
        stage1["summary"]["selected_locked_eval_rows"] = 5
        stage1["summary"]["remaining_representative_rows_needed"] = 0
        frame = _representative_frame()
        frame["summary"]["available_representative_rows"] = 5
        frame["summary"]["selected_locked_eval_rows"] = 5

        report = build_representative_gap_plan_report(
            manifest=_manifest(),
            stage1_report=stage1,
            representative_frame=frame,
            llm_scoring=_llm_scoring(),
            product_quality=_product_quality(),
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "representative_gap_closed")
        self.assertEqual(report["summary"]["remaining_representative_rows_needed"], 0)
        self.assertEqual(report["summary"]["open_primary_collection_slots"], 0)
        self.assertEqual(report["collection_slots"], [])
        self.assertIn("Human-review", report["next_steps"][0])


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "random_seed": "unit_test_seed",
        "global_rules": ["Do not use targeted rows as representative rows."],
        "source_lanes": [
            {
                "source_id": "runtime_observed_semantic_admit_contexts",
                "source_class": "primary_observed",
                "slot_quota": 2,
                "eligibility": "primary_representative_if_sampled_before_scoring",
                "collection_contract": "Observed runtime contexts.",
            },
            {
                "source_id": "corpus_sampled_app_candidate_contexts",
                "source_class": "primary_corpus_proxy",
                "slot_quota": 1,
                "eligibility": "primary_proxy_if_sampled_before_scoring",
                "collection_contract": "Corpus-like contexts.",
            },
            {
                "source_id": "llm_pilot_locked_eval_proxy_backstop",
                "source_class": "generated_proxy_backstop",
                "slot_quota": 0,
                "eligibility": "proxy_only_not_primary_representative",
                "collection_contract": "LLM proxy rows.",
            },
        ],
    }


def _stage1_report() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "sampling_stage1_materialized_with_representative_shortfall",
        "summary": {
            "target_locked_eval_rows": 5,
            "available_representative_rows": 2,
            "selected_locked_eval_rows": 2,
            "remaining_representative_rows_needed": 3,
        },
    }


def _representative_frame() -> dict[str, object]:
    return {
        "frame_id": "test_frame",
        "summary": {
            "target_locked_eval_rows": 5,
            "available_representative_rows": 2,
            "selected_locked_eval_rows": 2,
        },
    }


def _llm_scoring() -> dict[str, object]:
    return {
        "case_results": [
            {
                "case_id": "llm:locked:001",
                "split": "locked_eval",
                "trigger": "bank",
                "gold_type": "positive_active",
                "gold_decision": "replace",
                "sentence": "The bank approved the loan.",
            },
            {
                "case_id": "llm:discovery:001",
                "split": "discovery",
                "trigger": "bank",
                "gold_type": "phrase_no_winner",
                "gold_decision": "abstain",
                "sentence": "Bank on arriving early.",
            },
        ]
    }


def _product_quality() -> dict[str, object]:
    return {
        "case_traces": [
            {"lane_type": "representative", "case_id": "rep:001"},
            {"lane_type": "stress", "case_id": "stress:001"},
            {"lane_type": "stress", "case_id": "stress:002"},
        ]
    }


if __name__ == "__main__":
    unittest.main()
