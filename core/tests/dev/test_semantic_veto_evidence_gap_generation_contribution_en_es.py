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

from semantic_veto_evidence_gap_generation_contribution_en_es import (  # noqa: E402
    build_evidence_gap_generation_contribution_report,
    render_evidence_gap_generation_contribution_markdown,
)


class SemanticVetoEvidenceGapGenerationContributionTests(unittest.TestCase):
    def test_contribution_report_separates_active_from_review_required_slots(self) -> None:
        report = build_evidence_gap_generation_contribution_report(
            generation_requests_payload=_request_payload(),
            admission_payload=_admission_payload(),
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["admitted_item_count"], 3)
        self.assertEqual(report["summary"]["semantic_review_required_count"], 2)
        self.assertEqual(report["summary"]["new_competitor_target_item_count"], 1)
        actions = report["summary"]["recommended_actions"]
        self.assertEqual(actions["candidate_active_evidence_for_rescoring"], 1)
        self.assertEqual(actions["review_competitor_target_before_rescoring"], 1)
        self.assertEqual(actions["review_no_winner_context_before_rescoring"], 1)

        markdown = render_evidence_gap_generation_contribution_markdown(report)
        self.assertIn("Review-required items", markdown)
        self.assertIn("review_competitor_target_before_rescoring", markdown)

    def test_missing_admitted_items_is_review_status(self) -> None:
        report = build_evidence_gap_generation_contribution_report(
            generation_requests_payload=_request_payload(),
            admission_payload={"admitted_items": []},
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("no_admitted_generated_items", report["summary"]["issues"])


def _request_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "requests": [
            {
                "request_id": "req:active",
                "family_id": "family:bank:banco",
                "slot_id": "slot:active",
                "slot_type": "active_evidence_expansion",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "active_evidence_text": "bank -> banco | financial institution",
                "known_shadow_targets": ["orilla"],
            },
            {
                "request_id": "req:shadow",
                "family_id": "family:bank:banco",
                "slot_id": "slot:shadow",
                "slot_type": "shadow_or_competitor_evidence_probe",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "active_evidence_text": "bank -> banco | financial institution",
                "known_shadow_targets": ["orilla"],
            },
            {
                "request_id": "req:no-winner",
                "family_id": "family:bank:banco",
                "slot_id": "slot:no-winner",
                "slot_type": "no_winner_context_probe",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "active_evidence_text": "bank -> banco | financial institution",
                "known_shadow_targets": ["orilla"],
            },
        ],
    }


def _admission_payload() -> dict[str, object]:
    return {
        "admitted_items": [
            {
                "item_id": "req:active:item:001",
                "request_id": "req:active",
                "family_id": "family:bank:banco",
                "slot_type": "active_evidence_expansion",
                "source_phrase": "bank",
                "active_target_lemma": "banco",
                "target_lemma": "banco",
                "sentence": "The bank approved the loan yesterday.",
                "evidence_note": "Financial institution sense.",
            },
            {
                "item_id": "req:shadow:item:001",
                "request_id": "req:shadow",
                "family_id": "family:bank:banco",
                "slot_type": "shadow_or_competitor_evidence_probe",
                "source_phrase": "bank",
                "active_target_lemma": "banco",
                "target_lemma": "ribera",
                "competitor_sense_label": "river edge",
                "active_sense_contrast": "The source refers to terrain beside water, not a bank as an institution.",
                "sentence": "The river bank collapsed after the storm.",
                "evidence_note": "Land beside water sense.",
                "active_mismatch_note": "A financial institution is not the thing collapsing by the river.",
            },
            {
                "item_id": "req:no-winner:item:001",
                "request_id": "req:no-winner",
                "family_id": "family:bank:banco",
                "slot_type": "no_winner_context_probe",
                "source_phrase": "bank",
                "active_target_lemma": "banco",
                "target_lemma": "",
                "sentence": "The browser tab title read Bank Notes.",
                "no_winner_context_class": "page_title",
                "no_winner_reason": "The source appears in a title.",
                "runtime_trigger_note": "Bank is a standalone visible token in the title.",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
