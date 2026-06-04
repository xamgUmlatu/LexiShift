from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_active_only_full_generation_plan_en_es import (  # noqa: E402
    build_active_only_full_generation_plan_report,
    render_active_only_full_generation_plan_markdown,
)


class SemanticVetoActiveOnlyFullGenerationPlanTests(unittest.TestCase):
    def test_compares_full_denominator_to_existing_active_only_pack(self) -> None:
        report = build_active_only_full_generation_plan_report(
            srs_zipf_bridge_payload=_bridge_payload(),
            existing_evidence_payloads=[_active_evidence_payload()],
            requested_items=2,
            tranche_size=2,
            request_family_limit=1,
            generated_at="2026-05-12T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "active_only_full_generation_plan_ready")
        self.assertEqual(report["strict_flow"]["llm_call"], "none")
        self.assertEqual(report["strict_flow"]["runtime_policy_change"], "none")
        self.assertEqual(report["summary"]["denominator_family_count"], 3)
        self.assertEqual(report["summary"]["covered_denominator_family_count"], 1)
        self.assertEqual(report["summary"]["uncovered_family_count"], 2)
        self.assertEqual(report["summary"]["selected_request_family_count"], 1)
        self.assertEqual(report["summary"]["tranche_count"], 1)
        self.assertEqual(report["summary"]["full_expected_generated_item_count"], 4)
        self.assertEqual(
            report["e2e_checks"]["selected_rows_do_not_overlap_existing_coverage"], True
        )
        self.assertEqual(report["e2e_checks"]["all_requests_active_only"], True)

        request = report["requests"][0]
        self.assertEqual(request["slot_type"], "active_evidence_expansion")
        self.assertEqual(request["requested_items"], 2)
        self.assertEqual(request["expected_output_token_budget"], 280)
        self.assertIn("Return exactly one JSON object", request["prompt_text"])
        self.assertIn("target_lemma", request["prompt_text"])
        self.assertNotIn("bank:banco", request["request_id"])

        markdown = render_active_only_full_generation_plan_markdown(report)
        self.assertIn("Active-Only Full Generation Plan", markdown)
        self.assertIn("Denominator source-target families", markdown)
        self.assertIn("Safe First-Run Command Shape", markdown)

    def test_marks_missing_denominator_for_review(self) -> None:
        report = build_active_only_full_generation_plan_report(
            srs_zipf_bridge_payload={"decision": "srs_zipf_bridge_needs_mapping"},
            existing_evidence_payloads=[],
            generated_at="2026-05-12T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("full_source_target_denominator_missing", report["issues"])
        self.assertIn("srs_zipf_bridge_not_established", report["issues"])

    def test_source_target_review_filters_paid_request_packet(self) -> None:
        report = build_active_only_full_generation_plan_report(
            srs_zipf_bridge_payload=_bridge_payload(),
            existing_evidence_payloads=[],
            source_target_review_payload={
                "decision": "test_review",
                "decisions": [
                    {
                        "source": "bank",
                        "target": "banco",
                        "approved_for_active_only_generation": False,
                        "decision": "exclude_no_visible_replacement",
                    },
                    {
                        "source": "current",
                        "target": "corriente",
                        "approved_for_active_only_generation": True,
                        "decision": "approve_direct_mapping",
                        "rationale": "Use the electricity or flowing-water sense, not current as present time.",
                    },
                ],
            },
            requested_items=2,
            tranche_size=2,
            request_family_limit=3,
            generated_at="2026-05-12T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["strict_flow"]["source_target_review"], "approved_rows_only")
        self.assertEqual(report["summary"]["source_target_review_active"], True)
        self.assertEqual(report["summary"]["source_target_review_status_counts"]["approved"], 1)
        self.assertEqual(report["summary"]["source_target_review_status_counts"]["excluded"], 1)
        self.assertEqual(report["summary"]["source_target_review_status_counts"]["unreviewed"], 1)
        self.assertEqual(report["summary"]["selected_request_count"], 1)
        self.assertEqual(report["selected_request_families"][0]["source"], "current")
        self.assertEqual(
            report["e2e_checks"]["selected_rows_review_approved_or_review_inactive"], True
        )
        self.assertNotIn("bank:banco", report["requests"][0]["request_id"])
        self.assertIn(
            "Reviewed intended-sense note: Use the electricity or flowing-water sense",
            report["requests"][0]["active_evidence_text"],
        )
        self.assertIn(
            "Reviewed intended-sense note: Use the electricity or flowing-water sense",
            report["requests"][0]["prompt_text"],
        )


def _bridge_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "srs_zipf_bridge_established",
        "full_source_target_pairs": [
            {
                "source": "bank",
                "target": "banco",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "target_zipf_band_es": "zipf_5_plus_very_common",
            },
            {
                "source": "current",
                "target": "corriente",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "target_zipf_band_es": "zipf_4_to_5_common",
            },
            {
                "source": "adder",
                "target": "víbora",
                "source_zipf_band_en": "zipf_below_3_rare",
                "target_zipf_band_es": "zipf_3_to_4_mid",
            },
        ],
    }


def _active_evidence_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "rows": [
            {
                "relation_type": "anchor_cue",
                "normalized_trigger": "bank",
                "normalized_active_target": "banco",
                "metadata": {"family_id": "en-es:full-family-repaired-full:bank:banco"},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
