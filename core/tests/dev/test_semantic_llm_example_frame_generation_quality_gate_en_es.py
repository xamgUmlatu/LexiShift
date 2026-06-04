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

from semantic_llm_example_frame_generation_quality_gate_en_es import (  # noqa: E402
    build_example_frame_generation_quality_gate_report,
    render_example_frame_generation_quality_gate_markdown,
)


class SemanticLlmExampleFrameGenerationQualityGateTests(unittest.TestCase):
    def test_rejects_contract_complete_batch_when_prototype_quality_fails(self) -> None:
        report = build_example_frame_generation_quality_gate_report(
            run_payload=_run_payload(),
            contract_payload=_contract_payload(),
            prototype_payload=_prototype_payload(),
            generated_at="2026-04-25T15:00:00Z",
        )

        self.assertEqual(report["status"], "reject")
        self.assertEqual(report["decision"], "analysis_only")
        self.assertEqual(report["contract_summary"]["complete_families"], 8)
        self.assertFalse(report["prototype_config_rows"][0]["quality_gate_pass"])
        self.assertEqual(report["diagnostics"]["phrase_overreach_false_abstain_count"], 1)
        self.assertEqual(report["diagnostics"]["containment_overreach_reduction_count"], 1)
        self.assertEqual(report["diagnostics"]["harmful_replace_count"], 1)
        self.assertIn("analysis-only", report["recommendation"])

        markdown = render_example_frame_generation_quality_gate_markdown(report)
        self.assertIn("Example-Frame Generation Quality Gate", markdown)
        self.assertIn("Phrase-overreach", markdown)

    def test_accepts_when_run_contract_and_quality_all_pass(self) -> None:
        prototype = _prototype_payload(
            decision_accuracy=1.0,
            replace_recall=1.0,
            harmful=0,
            false_abstain=0,
            row_results=[],
        )
        report = build_example_frame_generation_quality_gate_report(
            run_payload=_run_payload(),
            contract_payload=_contract_payload(),
            prototype_payload=prototype,
            generated_at="2026-04-25T15:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "promotion_candidate")


def _run_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "batch_id": "generated",
        "summary": {
            "selected_request_count": 11,
            "accepted_item_count": 11,
            "input_tokens": 3000,
            "output_tokens": 350,
        },
    }


def _contract_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "batch_id": "merged",
        "summary": {
            "contract_complete_family_count": 8,
            "families_total": 8,
        },
    }


def _prototype_payload(
    *,
    decision_accuracy: float = 0.625,
    replace_recall: float = 0.1875,
    harmful: int = 2,
    false_abstain: int = 13,
    row_results: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if row_results is None:
        row_results = [
            {
                "case_id": "active:001",
                "gold_decision": "replace",
                "predicted_decision": "abstain",
                "predicted_winner": "phrase_control",
                "active_score": 0.5,
                "strongest_shadow_score": 0.3,
                "phrase_control_score": 0.8,
                "active_evidence_text": "active evidence",
                "phrase_control_evidence_text": "phrase evidence",
            },
            {
                "case_id": "shadow:001",
                "gold_decision": "abstain",
                "predicted_decision": "replace",
                "predicted_winner": "active",
                "active_score": 0.7,
                "strongest_shadow_score": 0.6,
                "phrase_control_score": 0.2,
                "active_evidence_text": "active evidence",
                "strongest_shadow_evidence_text": "shadow evidence",
            },
        ]
    active_row_results = [
        row for row in row_results if str(row.get("case_id") or "") != "active:001"
    ]
    return {
        "configurations": [
            {
                "config_id": "prototype_reviewed_examples_phrase_containment_guard",
                "label": "Phrase containment guard",
                "phrase_control_evidence_mode": "local_containment_patterns",
                "use_phrase_containment_gate": True,
                "summary": {
                    "decision_accuracy": decision_accuracy,
                    "replace_recall": replace_recall,
                    "harmful_replace_count": harmful,
                    "false_abstain_count": false_abstain,
                    "phrase_containment_hit_count": 0,
                },
                "row_results": [],
            },
            {
                "config_id": "prototype_reviewed_examples_phrase_prototype_guard",
                "label": "Phrase guard",
                "phrase_control_evidence_mode": "semantic_prototype_competition",
                "summary": {
                    "decision_accuracy": decision_accuracy,
                    "replace_recall": replace_recall,
                    "harmful_replace_count": harmful,
                    "false_abstain_count": false_abstain,
                },
                "row_results": row_results,
            },
            {
                "config_id": "prototype_reviewed_examples_active_guard",
                "label": "Active guard",
                "phrase_control_evidence_mode": "runtime_phrase_guard_only",
                "summary": {
                    "decision_accuracy": decision_accuracy,
                    "replace_recall": replace_recall,
                    "harmful_replace_count": harmful,
                    "false_abstain_count": false_abstain,
                },
                "row_results": active_row_results,
            },
        ]
    }


if __name__ == "__main__":
    unittest.main()
