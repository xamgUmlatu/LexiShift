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

from semantic_source_heldout_validation_en_es import (  # noqa: E402
    build_heldout_sentence_dataset,
    build_source_heldout_validation_report,
    render_source_heldout_validation_markdown,
)


class SemanticSourceHeldoutValidationTests(unittest.TestCase):
    def test_heldout_dataset_reuses_base_senses_and_replaces_cases(self) -> None:
        dataset = build_heldout_sentence_dataset(
            base_dataset_payload=_base_dataset(),
            heldout_case_payload=_heldout_cases(),
        )

        self.assertEqual(dataset["dataset_id"], "en_es_source_heldout_test")
        self.assertEqual(len(dataset["families"]), 1)
        family = dataset["families"][0]
        self.assertEqual(family["family_id"], "fam:check")
        self.assertEqual(family["active"]["sense_id"], "fam:check:active")
        self.assertEqual(family["cases"][0]["case_id"], "heldout:check:001")
        self.assertEqual(len(family["cases"]), 2)

    def test_validation_report_selects_configured_lane(self) -> None:
        report = build_source_heldout_validation_report(
            base_dataset_payload=_base_dataset(),
            heldout_case_payload=_heldout_cases(),
            evidence_batch_payload=_evidence_batch(),
            scorer_id="token_jaccard",
            context_view="masked_sentence",
            min_active_score=0.0,
            min_margin=0.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "heldout_pass")
        self.assertEqual(report["summary"]["case_count"], 2)
        self.assertEqual(report["summary"]["harmful_replace_count"], 0)
        self.assertEqual(report["summary"]["false_abstain_count"], 0)
        self.assertEqual(report["configured_row"]["source_mode"], "promotion_candidate_composite")
        self.assertEqual(report["configured_row"]["scorer_id"], "token_jaccard")
        self.assertEqual(report["configured_row"]["phrase_prototype_margin"], 0.0)
        self.assertEqual(report["configured_row"]["cases_total"], 2)
        self.assertEqual(report["empty_baseline_row"]["source_mode"], "empty_batch")
        self.assertEqual(len(report["configured_case_results"]), 2)
        self.assertEqual(report["failure_case_results"], [])
        self.assertIn("row_results", report["configured_row"])
        self.assertIn("delta_vs_empty_baseline", report["summary"])

        markdown = render_source_heldout_validation_markdown(report)
        self.assertIn("Semantic Source Held-out Validation", markdown)
        self.assertIn("Family Coverage", markdown)
        self.assertIn("heldout_pass", markdown)
        self.assertIn("No configured-lane failure case details", markdown)

    def test_heldout_validation_accepts_no_winner_phrase_cases(self) -> None:
        dataset = build_heldout_sentence_dataset(
            base_dataset_payload=_base_dataset(),
            heldout_case_payload=_phrase_heldout_cases(),
        )

        self.assertEqual(dataset["families"][0]["cases"][0]["gold_winner"], "none")

        report = build_source_heldout_validation_report(
            base_dataset_payload=_base_dataset(),
            heldout_case_payload=_phrase_heldout_cases(),
            evidence_batch_payload=_empty_evidence_batch(),
            scorer_id="token_jaccard",
            context_view="masked_sentence",
            min_active_score=0.0,
            min_margin=0.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["gold_replace_cases"], 0)
        self.assertEqual(report["summary"]["gold_abstain_cases"], 1)
        self.assertEqual(report["summary"]["harmful_replace_count"], 0)
        self.assertIn("fresh no-winner", report["next_steps"][0])


def _base_dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "base_test",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "active": {
                    "sense_id": "fam:check:active",
                    "target_lemma": "cheque",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "bank payment",
                        "all_evidence_text": "bank payment",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:check:shadow",
                        "target_lemma": "revisar",
                        "canonical_pos": "verb",
                        "evidence_views": {
                            "sense_label": "inspect verify",
                            "all_evidence_text": "inspect verify",
                        },
                    }
                ],
                "cases": [
                    {
                        "case_id": "base:check:001",
                        "sentence": "The check cleared.",
                        "source_phrase": "check",
                        "gold_winner": "fam:check:active",
                        "gold_decision": "replace",
                    }
                ],
            }
        ],
    }


def _heldout_cases() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "en_es_source_heldout_test",
        "case_scope": "semantic_active_shadow_only",
        "families": [
            {
                "family_id": "fam:check",
                "cases": [
                    {
                        "case_id": "heldout:check:001",
                        "sentence": "The check paid the rent yesterday.",
                        "source_phrase": "check",
                        "gold_winner": "fam:check:active",
                        "gold_decision": "replace",
                    },
                    {
                        "case_id": "heldout:check:002",
                        "sentence": "Auditors check figures carefully.",
                        "source_phrase": "check",
                        "gold_winner": "fam:check:shadow",
                        "gold_decision": "abstain",
                    },
                ],
            }
        ],
    }


def _phrase_heldout_cases() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "en_es_source_phrase_heldout_test",
        "case_scope": "phrase_no_winner_only",
        "families": [
            {
                "family_id": "fam:check",
                "cases": [
                    {
                        "case_id": "heldout:check:phrase:001",
                        "sentence": "Please check out before noon.",
                        "source_phrase": "check",
                        "gold_winner": "none",
                        "gold_decision": "abstain",
                    }
                ],
            }
        ],
    }


def _evidence_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": "heldout_test_source",
        "batch_id": "heldout_test_batch",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "check",
                "evidence_text": "paid rent yesterday",
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                    "candidate_sense_id": "fam:check:active",
                },
            },
            {
                "relation_type": "shadow_candidate",
                "trigger": "check",
                "evidence_text": "auditors figures carefully",
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                    "candidate_sense_id": "fam:check:shadow",
                },
            },
        ],
    }


def _empty_evidence_batch() -> dict[str, object]:
    payload = _evidence_batch()
    payload["rows"] = []
    payload["row_count"] = 0
    return payload


if __name__ == "__main__":
    unittest.main()
