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

from semantic_veto_evidence_gap_generation_admission_en_es import (  # noqa: E402
    build_evidence_gap_generation_admission_report,
    render_evidence_gap_generation_admission_markdown,
)


class SemanticVetoEvidenceGapGenerationAdmissionTests(unittest.TestCase):
    def test_no_generated_responses_is_ready_for_admission(self) -> None:
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "ready_for_generated_response_admission")
        self.assertFalse(report["pilot"]["generated_responses_present"])
        self.assertEqual(report["summary"]["expected_request_count"], 3)
        self.assertEqual(report["summary"]["expected_item_count"], 5)

        markdown = render_evidence_gap_generation_admission_markdown(report)
        self.assertIn("ready_for_generated_response_admission", markdown)
        self.assertIn("high_need", markdown)

    def test_admits_clean_selected_subset_without_requiring_full_packet(self) -> None:
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:active"],
                "responses": [_active_response()],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "generated_items_admitted_for_pilot_rescoring")
        self.assertEqual(report["summary"]["expected_request_count"], 1)
        self.assertEqual(report["summary"]["admitted_item_count"], 2)
        self.assertEqual(report["summary"]["rejected_item_count"], 0)
        self.assertEqual(report["alignment"]["missing_expected_request_ids"], [])
        self.assertEqual(report["summary"]["coverage_shortfall_count"], 0)

    def test_admits_shadow_response_when_competitor_target_is_proposed(self) -> None:
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:shadow"],
                "responses": [_shadow_response()],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["admitted_item_count"], 2)
        self.assertEqual(report["admitted_items"][0]["proposed_competitor_target_lemma"], "orilla")
        self.assertEqual(report["admitted_items"][0]["competitor_sense_label"], "river edge")
        self.assertIn(
            "not a financial institution", report["admitted_items"][0]["active_sense_contrast"]
        )

    def test_rejects_shadow_response_without_contrast_fields(self) -> None:
        response = _shadow_response()
        response.pop("competitor_sense_label")
        response.pop("active_sense_contrast")
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:shadow"],
                "responses": [response],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        reasons = report["response_results"][0]["response_rejection_reasons"]
        self.assertIn("missing_response_field:competitor_sense_label", reasons)
        self.assertIn("missing_response_field:active_sense_contrast", reasons)

    def test_rejects_shadow_response_with_conflicting_competitor_targets(self) -> None:
        response = _shadow_response()
        response["target_lemma"] = "orilla"
        response["proposed_competitor_target_lemma"] = "banco"
        response["items"][0]["active_mismatch_note"] = "orilla is wrong here."
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:shadow"],
                "responses": [response],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        reasons = report["response_results"][0]["response_rejection_reasons"]
        self.assertIn("proposed_competitor_reuses_active_target_lemma", reasons)
        self.assertIn("conflicting_competitor_target_lemmas", reasons)

    def test_rejects_shadow_item_when_mismatch_note_does_not_name_active_target(self) -> None:
        response = _shadow_response()
        response["items"][0]["active_mismatch_note"] = "The river-edge sense is different."
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:shadow"],
                "responses": [response],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        reasons = report["rejection_reasons"]
        self.assertEqual(reasons["active_mismatch_note_missing_active_target_lemma"], 1)

    def test_rejects_no_winner_technical_container_and_missing_trigger_note(self) -> None:
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:no-winner"],
                "responses": [_weak_no_winner_response()],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "generated_items_need_repair")
        reasons = report["rejection_reasons"]
        self.assertEqual(reasons["source_phrase_missing_or_not_runtime_like"], 1)
        self.assertEqual(reasons["weak_no_winner_technical_container"], 1)
        self.assertEqual(reasons["missing_item_field:runtime_trigger_note"], 1)
        self.assertEqual(reasons["missing_item_field:no_winner_context_class"], 1)

    def test_admits_clean_no_winner_response_with_context_class(self) -> None:
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:no-winner"],
                "responses": [_clean_no_winner_response()],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["admitted_item_count"], 1)
        self.assertEqual(report["admitted_items"][0]["no_winner_context_class"], "ui_label")

    def test_rejects_no_winner_that_looks_like_ordinary_active_sentence(self) -> None:
        response = _clean_no_winner_response()
        response["items"] = [
            {
                "sentence": "The bank approved the loan yesterday.",
                "no_winner_context_class": "ui_label",
                "no_winner_reason": "The word should remain English.",
                "runtime_trigger_note": "bank is a standalone token.",
            }
        ]
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:no-winner"],
                "responses": [response],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(
            report["rejection_reasons"]["no_winner_context_lacks_visible_nontranslation_anchor"],
            1,
        )

    def test_accepts_honest_no_competitor_marker_as_waived_shadow_coverage(self) -> None:
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:shadow"],
                "responses": [
                    {
                        "request_id": "pilot:req:shadow",
                        "family_id": "family:bank:banco",
                        "slot_id": "slot:shadow",
                        "slot_type": "shadow_or_competitor_evidence_probe",
                        "source_phrase": "bank",
                        "target_lemma": "",
                        "unable_to_find_distinct_competitor": True,
                        "no_distinct_competitor_reason": "No clear distinct competitor was found.",
                        "items": [],
                    }
                ],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "generated_items_admitted_for_pilot_rescoring")
        self.assertEqual(report["summary"]["admitted_item_count"], 0)
        self.assertEqual(report["summary"]["rejected_item_count"], 0)
        self.assertEqual(report["response_results"][0]["response_rejection_reasons"], [])
        self.assertTrue(report["response_results"][0]["no_competitor_marker"])
        self.assertEqual(report["summary"]["coverage_shortfall_count"], 0)
        self.assertEqual(report["summary"]["coverage_waived_item_count"], 2)

    def test_rejects_leakage_spanish_target_and_non_runtime_trigger_shape(self) -> None:
        response = _active_response()
        response["items"] = [
            {
                "sentence": "The my_bank_notes file says allow banco here.",
                "evidence_note": "Leaky and not a runtime-like standalone trigger.",
            },
            {
                "sentence": "The bank approved the loan after review.",
                "evidence_note": "Clean duplicate target-sense context.",
            },
        ]
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:active"],
                "responses": [response],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "generated_items_need_repair")
        reasons = report["rejection_reasons"]
        self.assertEqual(reasons["source_phrase_missing_or_not_runtime_like"], 1)
        self.assertEqual(reasons["spanish_target_lemma_in_sentence"], 1)
        self.assertEqual(reasons["label_leakage_in_sentence"], 1)
        self.assertEqual(report["summary"]["admitted_item_count"], 1)

    def test_rejects_response_alignment_mismatch(self) -> None:
        response = _active_response()
        response["target_lemma"] = "orilla"
        report = build_evidence_gap_generation_admission_report(
            generation_requests_payload=_request_payload(),
            generated_responses_payload={
                "selected_request_ids": ["pilot:req:active"],
                "responses": [response],
            },
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "generated_responses_need_repair")
        self.assertIn(
            "request_mismatch:target_lemma",
            report["response_results"][0]["response_rejection_reasons"],
        )


def _request_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": "en-es",
        "pilot": {
            "pilot_id": "semantic_veto_evidence_gap_control_pilot_en_es_v1",
            "request_kind": "semantic_veto_evidence_gap_generation",
        },
        "requests": [
            {
                "request_id": "pilot:req:active",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "arm_rank": 1,
                "global_need_rank": 1,
                "predicted_need": 0.9,
                "slot_id": "slot:active",
                "slot_type": "active_evidence_expansion",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "slot_target_lemma": "banco",
                "known_shadow_targets": ["orilla"],
                "requested_items": 2,
            },
            {
                "request_id": "pilot:req:shadow",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "arm_rank": 1,
                "global_need_rank": 1,
                "predicted_need": 0.9,
                "slot_id": "slot:shadow",
                "slot_type": "shadow_or_competitor_evidence_probe",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "slot_target_lemma": "",
                "known_shadow_targets": ["orilla"],
                "requested_items": 2,
            },
            {
                "request_id": "pilot:req:no-winner",
                "family_id": "family:bank:banco",
                "pilot_arm": "low_control",
                "arm_rank": 1,
                "global_need_rank": 20,
                "predicted_need": 0.2,
                "slot_id": "slot:no-winner",
                "slot_type": "no_winner_context_probe",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "slot_target_lemma": "",
                "known_shadow_targets": ["orilla"],
                "requested_items": 1,
            },
        ],
    }


def _active_response() -> dict[str, object]:
    return {
        "request_id": "pilot:req:active",
        "family_id": "family:bank:banco",
        "slot_id": "slot:active",
        "slot_type": "active_evidence_expansion",
        "source_phrase": "bank",
        "target_lemma": "banco",
        "items": [
            {
                "sentence": "The bank approved the loan after reviewing the application.",
                "evidence_note": "Financial institution sense.",
            },
            {
                "sentence": "A small bank opened near the train station last month.",
                "evidence_note": "Financial institution sense.",
            },
        ],
    }


def _shadow_response() -> dict[str, object]:
    return {
        "request_id": "pilot:req:shadow",
        "family_id": "family:bank:banco",
        "slot_id": "slot:shadow",
        "slot_type": "shadow_or_competitor_evidence_probe",
        "source_phrase": "bank",
        "target_lemma": "",
        "proposed_competitor_target_lemma": "orilla",
        "competitor_sense_label": "river edge",
        "active_sense_contrast": "The source refers to land beside water, not a financial institution.",
        "items": [
            {
                "sentence": "The river bank collapsed after the storm.",
                "evidence_note": "Land beside water sense.",
                "active_mismatch_note": "banco is wrong because a financial institution cannot collapse after a storm.",
            },
            {
                "sentence": "Children sat on the grassy bank beside the stream.",
                "evidence_note": "Land beside water sense.",
                "active_mismatch_note": "banco does not fit because the children are sitting on terrain, not at a financial institution.",
            },
        ],
    }


def _clean_no_winner_response() -> dict[str, object]:
    return {
        "request_id": "pilot:req:no-winner",
        "family_id": "family:bank:banco",
        "slot_id": "slot:no-winner",
        "slot_type": "no_winner_context_probe",
        "source_phrase": "bank",
        "target_lemma": "",
        "items": [
            {
                "sentence": "Menu label: Bank tools.",
                "no_winner_context_class": "ui_label",
                "no_winner_reason": "The source is part of a visible UI label that should remain English.",
                "runtime_trigger_note": "Bank is a standalone token after label punctuation.",
            }
        ],
    }


def _weak_no_winner_response() -> dict[str, object]:
    return {
        "request_id": "pilot:req:no-winner",
        "family_id": "family:bank:banco",
        "slot_id": "slot:no-winner",
        "slot_type": "no_winner_context_probe",
        "source_phrase": "bank",
        "target_lemma": "",
        "items": [
            {
                "sentence": "The file named my_bank_notes.txt opened in the browser.",
                "no_winner_reason": "The source appears inside a filename.",
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
