from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_source_admission_cycle_en_es import (  # noqa: E402
    build_source_admission_cycle_bundle,
    render_source_admission_cycle_markdown,
    write_source_admission_cycle_bundle,
)


class SemanticSourceAdmissionCycleTests(unittest.TestCase):
    def test_cycle_accepts_clean_candidate_batch_without_ablation(self) -> None:
        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_empty_batch_payload("base"),
            candidate_batch_payload=_candidate_batch_payload(),
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        report = bundle["report"]
        summary = report["summary"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "analysis_only")
        self.assertEqual(summary["leakage_rejected_row_count"], 0)
        self.assertEqual(summary["sense_rejected_row_count"], 0)
        self.assertEqual(summary["pre_sense_merged_row_count"], 3)
        self.assertEqual(summary["final_admitted_row_count"], 3)
        self.assertEqual(summary["semantic_contract_complete_family_count"], 1)
        self.assertEqual(summary["phrase_contract_complete_family_count"], 1)
        self.assertEqual(summary["semantic_gate_status"], "ok")
        self.assertEqual(summary["phrase_contract_status"], "ok")
        self.assertEqual(summary["combined_contract_status"], "ok")
        self.assertEqual(
            report["policy"]["contract_lanes"]["semantic_active_shadow"]["status"],
            "ok",
        )
        self.assertEqual(report["residuals"]["semantic_gap_family_keys"], [])
        self.assertEqual(report["residuals"]["phrase_containment_gap_family_keys"], [])

        markdown = render_source_admission_cycle_markdown(bundle)
        self.assertIn("Semantic Source Admission Cycle", markdown)
        self.assertIn("Final admitted rows: `3`", markdown)
        self.assertIn("Ablation was skipped", markdown)

    def test_cycle_keeps_phrase_contract_separate_from_semantic_gate(self) -> None:
        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_empty_batch_payload("base"),
            candidate_batch_payload=_candidate_batch_payload(include_phrase=False),
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        report = bundle["report"]
        summary = report["summary"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(summary["semantic_gate_status"], "ok")
        self.assertEqual(summary["phrase_contract_status"], "review")
        self.assertEqual(summary["combined_contract_status"], "review")
        self.assertEqual(summary["semantic_contract_complete_family_count"], 1)
        self.assertEqual(summary["phrase_contract_complete_family_count"], 0)
        self.assertEqual(report["residuals"]["semantic_gap_family_keys"], [])
        self.assertEqual(report["residuals"]["phrase_containment_gap_family_keys"], ["fam:bank"])
        self.assertFalse(
            report["policy"]["contract_lanes"]["phrase_containment"][
                "blocks_offline_semantic_promotion"
            ]
        )

        markdown = render_source_admission_cycle_markdown(bundle)
        self.assertIn("Offline lane: `semantic_active_shadow`", markdown)

    def test_cycle_reports_passing_heldout_validation(self) -> None:
        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_empty_batch_payload("base"),
            candidate_batch_payload=_candidate_batch_payload(),
            heldout_validation_payload=_heldout_payload(),
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        report = bundle["report"]
        heldout = report["summary"]["heldout_validation"]
        self.assertTrue(heldout["provided"])
        self.assertTrue(heldout["passed"])
        self.assertEqual(heldout["status"], "ok")
        self.assertEqual(heldout["decision"], "heldout_pass")
        self.assertEqual(heldout["case_count"], 2)
        self.assertEqual(
            report["policy"]["contract_lanes"]["held_out_seed_validation"]["status"],
            "ok",
        )

        markdown = render_source_admission_cycle_markdown(bundle)
        self.assertIn("Held-out validation: `ok` / `heldout_pass`", markdown)
        self.assertIn("Held-out cases: `2`", markdown)

    def test_cycle_flags_failed_heldout_validation(self) -> None:
        heldout_payload = _heldout_payload()
        heldout_payload["status"] = "review"
        heldout_payload["decision"] = "heldout_review"
        heldout_payload["summary"]["false_abstain_count"] = 1

        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_empty_batch_payload("base"),
            candidate_batch_payload=_candidate_batch_payload(),
            heldout_validation_payload=heldout_payload,
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        report = bundle["report"]
        heldout = report["summary"]["heldout_validation"]
        self.assertEqual(report["status"], "review")
        self.assertFalse(heldout["passed"])
        self.assertTrue(heldout["blocks_offline_semantic_promotion"])
        self.assertTrue(
            report["policy"]["contract_lanes"]["held_out_seed_validation"][
                "blocks_offline_semantic_promotion"
            ]
        )

    def test_cycle_sense_admits_the_final_merged_batch(self) -> None:
        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_base_batch_with_bad_row(),
            candidate_batch_payload=_candidate_batch_payload(),
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        report = bundle["report"]
        summary = report["summary"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(summary["pre_sense_merged_row_count"], 4)
        self.assertEqual(summary["final_admitted_row_count"], 3)
        self.assertEqual(summary["sense_rejected_row_count"], 1)
        self.assertEqual(
            [row["row_id"] for row in bundle["sense_report"]["rejected_rows"]],
            ["row:base-generic"],
        )
        self.assertNotIn(
            "row:base-generic",
            [row["row_id"] for row in bundle["merged_batch"]["rows"]],
        )
        self.assertTrue(bundle["contract_report"]["summary"]["contract_complete"])

    def test_cycle_exposes_admitted_candidate_delta_batch(self) -> None:
        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_base_batch_with_bad_row(),
            candidate_batch_payload=_candidate_batch_payload(),
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        admitted = bundle["candidate_admitted_batch"]
        admitted_row_ids = [row["row_id"] for row in admitted["rows"]]
        self.assertEqual(admitted["row_count"], 3)
        self.assertEqual(admitted["review_state"], "admitted_by_semantic_source_cycle")
        self.assertEqual(
            admitted["provenance"]["admission_cycle"]["admitted_candidate_row_count"],
            3,
        )
        self.assertNotIn("row:base-generic", admitted_row_ids)
        self.assertEqual(
            admitted["batch_id"],
            "candidate:candidate-admitted",
        )

    def test_cycle_writer_links_sidecar_artifacts(self) -> None:
        bundle = build_source_admission_cycle_bundle(
            dataset_payload=_dataset_payload(),
            queue_payload=_queue_payload(),
            required_family_payload=_dataset_payload(),
            base_batch_payload=_empty_batch_payload("base"),
            candidate_batch_payload=_candidate_batch_payload(),
            sense_scorers=("token_jaccard", "tfidf_cosine"),
            sense_min_intended_score=0.05,
            run_ablation=False,
            generated_at="2026-04-25T19:00:00Z",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            json_out = tmp / "cycle.json"
            markdown_out = tmp / "cycle.md"
            write_source_admission_cycle_bundle(
                bundle=bundle,
                json_out=json_out,
                markdown_out=markdown_out,
                filtered_batch_out=tmp / "filtered.json",
                sense_batch_out=tmp / "sense.json",
                merged_batch_out=tmp / "merged.json",
                candidate_admitted_batch_out=tmp / "candidate_admitted.json",
            )

            report = json.loads(json_out.read_text(encoding="utf-8"))
            artifacts = report["artifacts"]
            self.assertIn("leakage_json", artifacts)
            self.assertIn("contract_markdown", artifacts)
            self.assertIn("candidate_admitted_batch_json", artifacts)
            self.assertTrue(Path(artifacts["leakage_json"]).exists())
            self.assertTrue(Path(artifacts["contract_markdown"]).exists())
            self.assertTrue(Path(artifacts["candidate_admitted_batch_json"]).exists())
            self.assertNotIn(
                "filtered_batch",
                json.loads(Path(artifacts["leakage_json"]).read_text(encoding="utf-8")),
            )
            self.assertIn("leakage_json", markdown_out.read_text(encoding="utf-8"))


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
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
                "cases": [
                    {
                        "case_id": "bank:001",
                        "sentence": "The bank approved the loan.",
                        "gold_winner": "fam:bank:banco:active",
                        "gold_decision": "replace",
                    }
                ],
            }
        ],
    }


def _queue_payload() -> dict[str, object]:
    return {"queue_id": "test", "families": [{"family_id": "fam:bank"}]}


def _heldout_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "heldout_pass",
        "summary": {
            "status": "ok",
            "decision": "heldout_pass",
            "family_count": 1,
            "case_count": 2,
            "harmful_replace_count": 0,
            "false_abstain_count": 0,
            "replace_recall": 1.0,
            "decision_accuracy": 1.0,
        },
    }


def _empty_batch_payload(batch_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": batch_id,
        "pair": "en-es",
        "source_type": "internal",
        "source_id": batch_id,
        "source_family": "test",
        "rows": [],
    }


def _candidate_batch_payload(*, include_phrase: bool = True) -> dict[str, object]:
    rows = [
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
    ]
    if include_phrase:
        rows.append(
            _row(
                row_id="row:phrase",
                relation_type="phrase_control_example",
                candidate_sense_id="",
                candidate_target="phrase_control",
                evidence_text="Please bank on arriving early.",
                roles=["discrimination", "phrase_containment"],
            )
        )
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "candidate",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "candidate",
        "source_family": "silver_llm_generation",
        "rows": rows,
    }


def _base_batch_with_bad_row() -> dict[str, object]:
    payload = _empty_batch_payload("base")
    payload["rows"] = [
        _row(
            row_id="row:base-generic",
            relation_type="anchor_cue",
            candidate_sense_id="fam:bank:banco:active",
            evidence_text="The family rested by the river shore at the bank.",
            source_id="base",
        )
    ]
    return payload


def _row(
    *,
    row_id: str,
    relation_type: str,
    candidate_sense_id: str,
    evidence_text: str,
    candidate_target: str = "banco",
    roles: list[str] | None = None,
    source_id: str = "candidate",
) -> dict[str, object]:
    active_sense_id = "fam:bank:banco:active"
    return {
        "row_id": row_id,
        "source_id": source_id,
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
