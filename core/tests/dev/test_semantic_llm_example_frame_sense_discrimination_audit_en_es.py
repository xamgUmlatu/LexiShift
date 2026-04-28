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

from semantic_llm_example_frame_sense_discrimination_audit_en_es import (  # noqa: E402
    build_example_frame_sense_discrimination_audit_report,
    render_example_frame_sense_discrimination_audit_markdown,
)


class SemanticLlmExampleFrameSenseDiscriminationAuditTests(unittest.TestCase):
    def test_admits_rows_that_score_closer_to_intended_sense(self) -> None:
        report = build_example_frame_sense_discrimination_audit_report(
            dataset_payload=_dataset_payload(),
            batch_payload=_passing_batch_payload(),
            scorers=("token_jaccard", "tfidf_cosine"),
            generated_at="2026-04-25T18:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(summary["semantic_input_row_count"], 2)
        self.assertEqual(summary["semantic_admitted_row_count"], 2)
        self.assertEqual(summary["semantic_rejected_row_count"], 0)
        self.assertEqual(summary["non_semantic_passthrough_row_count"], 1)
        self.assertEqual(report["admitted_batch"]["row_count"], 3)
        self.assertEqual(
            [row["admission_status"] for row in report["row_results"]],
            ["admitted", "admitted", "not_applicable"],
        )

        markdown = render_example_frame_sense_discrimination_audit_markdown(report)
        self.assertIn("Sense-Discrimination Audit", markdown)
        self.assertIn("Semantic admitted rows: `2`", markdown)

    def test_rejects_generic_and_unknown_shadow_rows_before_merge(self) -> None:
        report = build_example_frame_sense_discrimination_audit_report(
            dataset_payload=_dataset_payload(),
            batch_payload=_failing_batch_payload(),
            scorers=("token_jaccard", "tfidf_cosine"),
            generated_at="2026-04-25T18:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(report["status"], "review")
        self.assertEqual(summary["semantic_input_row_count"], 3)
        self.assertEqual(summary["semantic_admitted_row_count"], 1)
        self.assertEqual(summary["semantic_rejected_row_count"], 2)
        self.assertEqual(
            summary["rejection_reason_counts"],
            {
                "competitor_sense_not_lower": 1,
                "unknown_intended_sense": 1,
            },
        )
        self.assertEqual(
            [row["row_id"] for row in report["rejected_rows"]],
            ["row:generic", "row:unknown-shadow"],
        )
        self.assertEqual(
            [row["row_id"] for row in report["admitted_batch"]["rows"]],
            ["row:shadow"],
        )


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:bank",
                "trigger": "bank",
                "active": {
                    "sense_id": "fam:bank:banco:active",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "bank money deposit account payment",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:bank:orilla:shadow",
                        "target_lemma": "orilla",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "all_evidence_text": "river shore water edge bank",
                        },
                    }
                ],
                "cases": [],
            }
        ],
    }


def _passing_batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "passing",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "test",
        "source_family": "silver_llm_generation",
        "rows": [
            _row(
                row_id="row:active",
                relation_type="anchor_cue",
                candidate_sense_id="fam:bank:banco:active",
                evidence_text="The customer deposited money into a bank account.",
            ),
            _row(
                row_id="row:shadow",
                relation_type="shadow_candidate",
                candidate_sense_id="fam:bank:orilla:shadow",
                candidate_target="orilla",
                evidence_text="The canoe drifted toward the muddy river bank.",
            ),
            _row(
                row_id="row:phrase",
                relation_type="phrase_control_example",
                candidate_sense_id="",
                candidate_target="phrase_control",
                evidence_text="Please bank on arriving early.",
                roles=["discrimination", "phrase_containment"],
            ),
        ],
    }


def _failing_batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "failing",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "test",
        "source_family": "silver_llm_generation",
        "rows": [
            _row(
                row_id="row:generic",
                relation_type="anchor_cue",
                candidate_sense_id="fam:bank:banco:active",
                evidence_text="The bank was mentioned twice.",
            ),
            _row(
                row_id="row:shadow",
                relation_type="shadow_candidate",
                candidate_sense_id="fam:bank:orilla:shadow",
                candidate_target="orilla",
                evidence_text="The canoe drifted toward the muddy river bank.",
            ),
            _row(
                row_id="row:unknown-shadow",
                relation_type="shadow_candidate",
                candidate_sense_id="fam:bank:missing:shadow",
                candidate_target="missing",
                evidence_text="The teller checked the form.",
            ),
        ],
    }


def _row(
    *,
    row_id: str,
    relation_type: str,
    candidate_sense_id: str,
    evidence_text: str,
    candidate_target: str = "banco",
    roles: list[str] | None = None,
) -> dict[str, object]:
    active_sense_id = "fam:bank:banco:active"
    return {
        "row_id": row_id,
        "relation_type": relation_type,
        "roles": roles or ["cue_generation", "discrimination"],
        "trigger": "bank",
        "active_target": "banco",
        "candidate_target": candidate_target,
        "evidence_text": evidence_text,
        "runtime_publishable": False,
        "metadata": {
            "family_id": "fam:bank",
            "active_sense_id": active_sense_id,
            "candidate_sense_id": candidate_sense_id,
        },
        "active_sense_hint": {
            "target_key": active_sense_id,
        },
        "candidate_sense_hint": {
            "target_key": candidate_sense_id,
        },
    }


if __name__ == "__main__":
    unittest.main()
