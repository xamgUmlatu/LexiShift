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

from semantic_llm_example_frame_leakage_audit_en_es import (  # noqa: E402
    build_example_frame_leakage_audit_report,
    render_example_frame_leakage_audit_markdown,
)


class SemanticLlmExampleFrameLeakageAuditTests(unittest.TestCase):
    def test_flags_benchmark_sentence_containment_and_filters_row(self) -> None:
        report = build_example_frame_leakage_audit_report(
            dataset_payload=_dataset_payload(),
            batch_payload=_batch_payload(),
            generated_at="2026-04-25T17:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["input_row_count"], 4)
        self.assertEqual(report["summary"]["leakage_hit_count"], 3)
        self.assertEqual(report["summary"]["rejected_row_count"], 3)
        self.assertEqual(report["summary"]["kept_row_count"], 1)
        self.assertEqual(report["leakage_rows"][0]["row_id"], "row:plant")
        self.assertEqual(
            report["leakage_rows"][0]["reason_code"],
            "benchmark_token_sequence_contained",
        )
        self.assertEqual(report["leakage_rows"][1]["row_id"], "row:plant-variant")
        self.assertEqual(
            report["leakage_rows"][1]["reason_code"],
            "benchmark_canonical_token_sequence_contained",
        )
        self.assertEqual(report["leakage_rows"][1]["common_sequence_length"], 7)
        self.assertEqual(report["leakage_rows"][2]["row_id"], "row:plant-possessive")
        self.assertEqual(
            report["leakage_rows"][2]["reason_code"],
            "benchmark_canonical_token_sequence_contained",
        )
        self.assertEqual(report["filtered_batch"]["row_count"], 1)
        self.assertEqual(report["filtered_batch"]["rows"][0]["row_id"], "row:order")

        markdown = render_example_frame_leakage_audit_markdown(report)
        self.assertIn("Leakage Audit", markdown)
        self.assertIn("row:plant", markdown)

    def test_flags_prior_source_duplicates_without_benchmark_leakage(self) -> None:
        report = build_example_frame_leakage_audit_report(
            dataset_payload=_dataset_payload(),
            batch_payload=_duplicate_batch_payload(),
            prior_batch_payloads=[_prior_batch_payload()],
            generated_at="2026-04-25T17:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["leakage_hit_count"], 0)
        self.assertEqual(report["summary"]["duplicate_hit_count"], 1)
        self.assertEqual(report["summary"]["rejected_row_count"], 1)
        self.assertEqual(report["summary"]["kept_row_count"], 1)
        self.assertEqual(report["duplicate_rows"][0]["row_id"], "row:order-duplicate")
        self.assertEqual(
            report["duplicate_rows"][0]["duplicate_reason_code"],
            "source_duplicate_exact_text",
        )
        self.assertEqual(
            report["duplicate_rows"][0]["duplicate_matched_row_id"],
            "prior:order",
        )
        self.assertEqual(report["filtered_batch"]["rows"][0]["row_id"], "row:order-new")

        markdown = render_example_frame_leakage_audit_markdown(report)
        self.assertIn("Duplicate Rows", markdown)
        self.assertIn("row:order-duplicate", markdown)

    def test_ignores_non_quality_loader_cases_for_leakage(self) -> None:
        report = build_example_frame_leakage_audit_report(
            dataset_payload={
                "families": [
                    {
                        "family_id": "fam:dry",
                        "cases": [
                            {
                                "case_id": "dry:loader",
                                "sentence": "The word dry is being checked for free from liquid or moisture.",
                                "slice_tags": ["loader_only", "not_quality_evaluation"],
                            }
                        ],
                    }
                ]
            },
            batch_payload={
                "schema_version": 1,
                "normalization_version": "semantic_evidence_v1",
                "batch_id": "batch",
                "pair": "en-es",
                "source_type": "external",
                "source_id": "wordnet",
                "source_family": "external_sense_graph",
                "rows": [
                    _row(
                        row_id="row:dry",
                        family_id="fam:dry",
                        trigger="dry",
                        active_target="seco",
                        candidate_target="seco",
                        evidence_text="free from liquid or moisture",
                    )
                ],
            },
            generated_at="2026-04-25T17:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["leakage_hit_count"], 0)
        self.assertEqual(report["summary"]["kept_row_count"], 1)


def _dataset_payload() -> dict[str, object]:
    return {
        "families": [
            {
                "family_id": "fam:plant",
                "cases": [
                    {
                        "case_id": "plant:001",
                        "sentence": "She watered the plant on the windowsill.",
                    }
                ],
            },
            {
                "family_id": "fam:order",
                "cases": [
                    {
                        "case_id": "order:001",
                        "sentence": "The order shipped this morning.",
                    }
                ],
            },
        ]
    }


def _batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "batch",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "test",
        "source_family": "silver_llm_generation",
        "roles": ["discrimination"],
        "review_state": "unreviewed",
        "rows": [
            {
                "row_id": "row:plant",
                "relation_type": "anchor_cue",
                "roles": ["cue_generation", "discrimination"],
                "trigger": "plant",
                "active_target": "planta",
                "candidate_target": "planta",
                "evidence_text": "She watered the plant on the windowsill every morning.",
                "runtime_publishable": False,
                "metadata": {"family_id": "fam:plant"},
            },
            {
                "row_id": "row:order",
                "relation_type": "anchor_cue",
                "roles": ["cue_generation", "discrimination"],
                "trigger": "order",
                "active_target": "pedido",
                "candidate_target": "pedido",
                "evidence_text": "I placed an order for two laptops online.",
                "runtime_publishable": False,
                "metadata": {"family_id": "fam:order"},
            },
            {
                "row_id": "row:plant-variant",
                "relation_type": "anchor_cue",
                "roles": ["cue_generation", "discrimination"],
                "trigger": "plant",
                "active_target": "planta",
                "candidate_target": "planta",
                "evidence_text": "I watered the plant on the windowsill every morning.",
                "runtime_publishable": False,
                "metadata": {"family_id": "fam:plant"},
            },
            {
                "row_id": "row:plant-possessive",
                "relation_type": "anchor_cue",
                "roles": ["cue_generation", "discrimination"],
                "trigger": "plant",
                "active_target": "planta",
                "candidate_target": "planta",
                "evidence_text": "I watered the plant on my windowsill every morning.",
                "runtime_publishable": False,
                "metadata": {"family_id": "fam:plant"},
            },
        ],
    }


def _prior_batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "prior",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "prior",
        "source_family": "silver_llm_generation",
        "rows": [
            _row(
                row_id="prior:order",
                family_id="fam:order",
                trigger="order",
                active_target="pedido",
                candidate_target="pedido",
                evidence_text="I placed an order for two laptops online.",
            )
        ],
    }


def _duplicate_batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "dupes",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "test",
        "source_family": "silver_llm_generation",
        "rows": [
            _row(
                row_id="row:order-duplicate",
                family_id="fam:order",
                trigger="order",
                active_target="pedido",
                candidate_target="pedido",
                evidence_text="I placed an order for two laptops online.",
            ),
            _row(
                row_id="row:order-new",
                family_id="fam:order",
                trigger="order",
                active_target="pedido",
                candidate_target="pedido",
                evidence_text="The customer changed the order before payment.",
            ),
        ],
    }


def _row(
    *,
    row_id: str,
    family_id: str,
    trigger: str,
    active_target: str,
    candidate_target: str,
    evidence_text: str,
) -> dict[str, object]:
    return {
        "row_id": row_id,
        "relation_type": "anchor_cue",
        "roles": ["cue_generation", "discrimination"],
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "evidence_text": evidence_text,
        "runtime_publishable": False,
        "metadata": {"family_id": family_id},
    }


if __name__ == "__main__":
    unittest.main()
