from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_active_only_source_packaging_en_es import (  # noqa: E402
    build_active_only_source_packaging_bundle,
    render_active_only_source_packaging_markdown,
)


class SemanticVetoActiveOnlySourcePackagingTests(unittest.TestCase):
    def test_packages_filtered_active_items_as_non_runtime_canonical_evidence(self) -> None:
        bundle = build_active_only_source_packaging_bundle(
            admission_payload=_admission_payload(),
            generation_run_payload=_generation_run_payload(),
            postprocess_payload=_postprocess_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )

        report = bundle["report"]
        normalized = bundle["normalized_batch"]
        intake = bundle["intake_batch"]

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "active_only_source_packaging_ready_for_inventory_compile",
        )
        self.assertEqual(report["summary"]["admitted_input_item_count"], 2)
        self.assertEqual(report["summary"]["packaged_row_count"], 1)
        self.assertEqual(report["summary"]["excluded_row_count"], 1)
        self.assertEqual(report["summary"]["runtime_publishable_row_count"], 0)
        self.assertEqual(report["summary"]["exclusion_reason_counts"], {"high_eval_overlap": 1})

        self.assertEqual(len(intake["items"]), 1)
        self.assertEqual(intake["source_id"], "active-only-poc-v5-source-packaging-latest")
        intake_row = intake["items"][0]
        self.assertTrue(
            intake_row["row_id"].startswith(
                "active-only-poc-v5-source-packaging-latest-source-row-001-bank-banco"
            )
        )
        self.assertEqual(intake_row["evidence_text"], "The bank approved the loan.")
        self.assertNotIn("financial institution", intake_row["evidence_text"])
        self.assertEqual(intake_row["relation_type"], "anchor_cue")
        self.assertEqual(intake_row["candidate_target"], "banco")

        normalized_row = normalized["rows"][0]
        self.assertFalse(normalized_row["runtime_publishable"])
        self.assertEqual(normalized_row["relation_type"], "anchor_cue")
        self.assertEqual(normalized_row["evidence_text"], "The bank approved the loan.")
        self.assertEqual(normalized_row["candidate_pos"], "noun")
        self.assertEqual(
            normalized_row["metadata"]["packaging_audit"]["eval_overlap_risk"],
            "low",
        )

        markdown = render_active_only_source_packaging_markdown(report)
        self.assertIn("Active-Only Source Packaging", markdown)
        self.assertIn("source_packaging", markdown)

    def test_custom_run_id_keeps_tranche_provenance_in_source_and_row_ids(self) -> None:
        bundle = build_active_only_source_packaging_bundle(
            admission_payload=_admission_payload(),
            generation_run_payload=_generation_run_payload(),
            postprocess_payload=_postprocess_payload(),
            run_id="product-scope-band-grading-v1-active-only-source-packaging-latest",
            generated_at="2026-05-09T00:00:00Z",
        )

        intake = bundle["intake_batch"]
        self.assertEqual(
            intake["source_id"],
            "product-scope-band-grading-v1-active-only-source-packaging-latest",
        )
        self.assertTrue(
            intake["items"][0]["row_id"].startswith(
                "product-scope-band-grading-v1-active-only-source-packaging-latest-source-row"
            )
        )


def _admission_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "generated_at": "2026-05-09T00:00:00Z",
        "summary": {
            "admitted_item_count": 2,
            "rejected_item_count": 0,
            "coverage_shortfall_count": 0,
        },
        "admitted_items": [
            {
                "item_id": "item:bank:1",
                "request_id": "request:bank",
                "slot_id": "slot:bank",
                "slot_type": "active_evidence_expansion",
                "family_id": "en-es:test:bank:banco",
                "source_phrase": "bank",
                "target_lemma": "banco",
                "active_target_lemma": "banco",
                "sentence": "The bank approved the loan.",
                "evidence_note": "Shows the financial institution sense.",
                "pilot_arm": "high_need",
                "global_need_rank": 1,
                "arm_rank": 1,
                "predicted_need": 0.9,
            },
            {
                "item_id": "item:bank:2",
                "request_id": "request:bank",
                "slot_id": "slot:bank",
                "slot_type": "active_evidence_expansion",
                "family_id": "en-es:test:bank:banco",
                "source_phrase": "bank",
                "target_lemma": "banco",
                "active_target_lemma": "banco",
                "sentence": "The bank manages checking accounts.",
                "evidence_note": "High overlap diagnostic.",
                "pilot_arm": "high_need",
                "global_need_rank": 1,
                "arm_rank": 1,
                "predicted_need": 0.9,
            },
        ],
    }


def _generation_run_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "generated_at": "2026-05-09T00:00:00Z",
        "prompt_id": "semantic_veto_evidence_gap_generation_v5",
        "selected_model_id": "gpt-test",
        "selected_temperature": 0.0,
        "summary": {
            "input_tokens": 100,
            "output_tokens": 50,
            "reasoning_tokens": 0,
        },
    }


def _postprocess_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "generated_at": "2026-05-09T00:00:00Z",
        "item_audits": [
            {
                "audit_id": "audit:bank:1",
                "item_id": "item:bank:1",
                "family_id": "en-es:test:bank:banco",
                "source_phrase": "bank",
                "target_lemma": "banco",
                "expected_pos": "noun",
                "observed_source_syntax": "noun_subject",
                "quality_score": 1.0,
                "definition_like_sentence": False,
                "flags": [],
                "eval_overlap": {
                    "risk": "low",
                    "case_id": "case:bank:1",
                },
                "shadow_confusability": {
                    "risk": "low",
                },
                "target_lemma_in_evidence_note": False,
            },
            {
                "audit_id": "audit:bank:2",
                "item_id": "item:bank:2",
                "family_id": "en-es:test:bank:banco",
                "source_phrase": "bank",
                "target_lemma": "banco",
                "expected_pos": "noun",
                "observed_source_syntax": "noun_subject",
                "quality_score": 0.2,
                "definition_like_sentence": False,
                "flags": [],
                "eval_overlap": {
                    "risk": "high",
                    "case_id": "case:bank:2",
                },
                "shadow_confusability": {
                    "risk": "low",
                },
                "target_lemma_in_evidence_note": False,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
