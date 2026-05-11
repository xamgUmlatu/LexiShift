from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_evidence_gap_generation_requests_en_es import (  # noqa: E402
    build_evidence_gap_generation_request_report,
    render_evidence_gap_generation_request_markdown,
)


class SemanticVetoEvidenceGapGenerationRequestsTests(unittest.TestCase):
    def test_renders_equal_slot_generation_requests_without_llm_call(self) -> None:
        report = build_evidence_gap_generation_request_report(
            plan_payload=_plan_payload(),
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "evidence_gap_generation_request_packet_ready")
        self.assertEqual(report["summary"]["request_count"], 6)
        self.assertEqual(report["summary"]["expected_generated_item_count"], 10)
        self.assertEqual(report["summary"]["requests_by_arm"]["high_need"]["request_count"], 3)
        self.assertEqual(report["summary"]["requests_by_arm"]["low_control"]["request_count"], 3)
        self.assertTrue(report["request_checks"]["same_slot_counts_per_arm"])
        self.assertEqual(report["strict_flow"]["llm_call"], "none")

        first = report["requests"][0]
        self.assertEqual(first["slot_type"], "active_evidence_expansion")
        self.assertIn("Return exactly one JSON object", first["prompt_text"])
        self.assertIn("must not contain Spanish target lemmas", first["prompt_text"])
        self.assertIn("standalone browser-replaceable token", first["prompt_text"])

        shadow = report["requests"][1]
        self.assertIn("active_mismatch_note", shadow["prompt_text"])
        self.assertIn("starts with active_target_lemma exactly", shadow["prompt_text"])
        self.assertIn("target_lemma the correct Spanish replacement", shadow["prompt_text"])
        self.assertIn("active_sense_contrast", shadow["prompt_text"])

        no_winner = report["requests"][2]
        self.assertIn("runtime_trigger_note", no_winner["prompt_text"])
        self.assertIn("filenames", no_winner["prompt_text"])
        self.assertIn("proper_name_or_title", no_winner["prompt_text"])
        self.assertIn("source_language_meta_use", no_winner["prompt_text"])
        self.assertNotIn("search_query", no_winner["prompt_text"])

        markdown = render_evidence_gap_generation_request_markdown(report)
        self.assertIn("Evidence-Gap Generation Requests", markdown)
        self.assertIn("No runtime policy change", markdown)

    def test_rejects_plan_when_selection_uses_observed_outcomes(self) -> None:
        plan = _plan_payload()
        plan["selection"]["selection_uses_observed_outcomes"] = True
        report = build_evidence_gap_generation_request_report(
            plan_payload=plan,
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "evidence_gap_generation_request_packet_needs_repair")
        self.assertEqual(report["summary"]["request_count"], 0)
        self.assertGreater(report["plan_checks"]["issue_count"], 0)


def _plan_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pilot_id": "semantic_veto_evidence_gap_control_pilot_en_es_v1",
        "pair": "en-es",
        "status": "no_spend_manifest_only",
        "selection": {
            "selection_scorer": "tfidf_cosine",
            "selection_formula": "evidence_gap_only",
            "selection_uses_observed_outcomes": False,
        },
        "generation_contract": {
            "same_contract_for_all_arms": True,
            "slot_types": [
                "active_evidence_expansion",
                "shadow_or_competitor_evidence_probe",
                "no_winner_context_probe",
            ],
        },
        "pilot_families": [
            _family("high_need", "bank", "banco"),
            _family("low_control", "quartz", "cuarzo"),
        ],
    }


def _family(arm: str, trigger: str, target: str) -> dict[str, object]:
    family_id = f"family:{trigger}:{target}"
    return {
        "family_id": family_id,
        "pilot_arm": arm,
        "arm_rank": 1,
        "global_need_rank": 1,
        "predicted_need": 0.8,
        "trigger": trigger,
        "active": {
            "target_lemma": target,
            "evidence_text": f"{trigger} -> {target} | active evidence",
        },
        "shadows": [{"target_lemma": "orilla"}],
        "planned_generation_slots": [
            {
                "slot_id": f"{family_id}:active_evidence_expansion",
                "slot_type": "active_evidence_expansion",
                "source_phrase": trigger,
                "target_lemma": target,
                "requested_items": 2,
                "purpose": "active",
            },
            {
                "slot_id": f"{family_id}:shadow_or_competitor_evidence_probe",
                "slot_type": "shadow_or_competitor_evidence_probe",
                "source_phrase": trigger,
                "target_lemma": "orilla",
                "requested_items": 2,
                "purpose": "shadow",
            },
            {
                "slot_id": f"{family_id}:no_winner_context_probe",
                "slot_type": "no_winner_context_probe",
                "source_phrase": trigger,
                "target_lemma": "",
                "requested_items": 1,
                "purpose": "none",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
