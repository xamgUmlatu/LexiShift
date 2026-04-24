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

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    augment_queue_dataset_with_llm_cue_views,
    build_prompt_downstream_report,
)
from semantic_llm_prompt_reporting import render_prompt_downstream_markdown  # noqa: E402


class SemanticLlmPromptDownstreamTests(unittest.TestCase):
    def test_llm_downstream_report_tracks_safe_candidate_and_coverage(self) -> None:
        queue_payload = {
            "queue_id": "semantic_prompt_bakeoff_test",
            "families": [
                {
                    "family_id": "fam:check",
                    "trigger": "check",
                    "role": "target",
                    "likely_bucket": "needs_cue_data",
                    "primary_prompt_slot": "cue_cross_pos_frame_v1",
                }
            ],
        }
        dataset_payload = {
            "schema_version": 1,
            "pair": "en-es",
            "dataset_id": "en_es_sentence_veto_test",
            "families": [
                {
                    "family_id": "fam:check",
                    "trigger": "check",
                    "active": {
                        "sense_id": "fam:check:active",
                        "target_lemma": "cheque",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "bank check",
                            "gloss_text": "payment document",
                            "all_evidence_text": "bank check | payment document",
                        },
                    },
                    "shadows": [
                        {
                            "sense_id": "fam:check:shadow",
                            "target_lemma": "revisar",
                            "canonical_pos": "verb",
                            "evidence_views": {
                                "sense_label": "inspect",
                                "gloss_text": "examine carefully",
                                "all_evidence_text": "inspect | examine carefully",
                            },
                        }
                    ],
                    "cases": [
                        {
                            "case_id": "check:001",
                            "sentence": "The check was signed and deposited yesterday.",
                            "source_phrase": "check",
                            "gold_winner": "fam:check:active",
                            "gold_decision": "replace",
                            "slice_tags": ["clear_active", "cross_pos"],
                        },
                        {
                            "case_id": "check:002",
                            "sentence": "They will check the records carefully tonight.",
                            "source_phrase": "check",
                            "gold_winner": "fam:check:shadow",
                            "gold_decision": "abstain",
                            "slice_tags": ["clear_shadow", "cross_pos"],
                        },
                    ],
                }
            ],
        }
        llm_batch_payload = {
            "batch_id": "en-es:target:test",
            "source_id": "semantic_prompt_bakeoff_en_es_test:target",
            "prompt_version": "semantic_prompt_bakeoff_v2",
            "model_id": "gpt-5.4",
            "generated_at": "2026-04-24T12:00:00Z",
            "review_state": "unreviewed",
            "rows": [
                {
                    "row_id": "row:check",
                    "relation_type": "anchor_cue",
                    "evidence_text": "signed deposited cashed payment slip",
                    "review_state": "unreviewed",
                    "runtime_publishable": False,
                    "provenance": {"prompt_slot": "cue_cross_pos_frame_v1"},
                    "active_sense_hint": {"target_key": "fam:check:active"},
                    "metadata": {
                        "family_id": "fam:check",
                        "active_sense_id": "fam:check:active",
                    },
                }
            ],
        }
        reverse_records_by_trigger = {
            "check": (
                TranslationGlossRecord(
                    translation="cheque",
                    pos_raw="noun",
                    metadata={"translation_sense_text": "written payment order"},
                ),
            )
        }

        report = build_prompt_downstream_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            llm_batch_payload=llm_batch_payload,
            reverse_records_by_trigger=reverse_records_by_trigger,
            data_root=REPO_ROOT,
            reverse_pack=self._pack("/tmp/rev.sqlite"),
            scorer_id="tfidf_cosine",
            min_active_score=0.05,
            min_margin=0.0,
            generated_at="2026-04-24T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["target_families_with_llm_cues"], 1)
        self.assertEqual(report["summary"]["negative_controls_with_llm_cues"], 0)

        configs = {
            str(config["config_id"]): config
            for config in report["configurations"]
            if isinstance(config, dict)
        }
        self.assertEqual(configs["hard_current_default"]["summary"]["false_abstain_count"], 1)
        self.assertEqual(
            configs["hard_reverse_aux_plus_all_evidence"]["summary"]["false_abstain_count"], 1
        )
        self.assertEqual(
            configs["hard_llm_cue_plus_all_evidence"]["summary"]["false_abstain_count"], 0
        )
        self.assertEqual(
            configs["hard_llm_cue_plus_all_evidence"]["fixed_false_abstain_case_ids"],
            ["check:001"],
        )
        self.assertIn("promotion-worthy", str(report["recommendation"]))

        markdown = render_prompt_downstream_markdown(report)
        self.assertIn("Semantic LLM Prompt Downstream Bakeoff", markdown)
        self.assertIn("Hard LLM cue plus all evidence", markdown)
        self.assertIn("check:001", markdown)

    def test_llm_augmentation_preserves_non_publishable_review_state(self) -> None:
        dataset_payload = {
            "families": [
                {
                    "family_id": "fam:check",
                    "trigger": "check",
                    "active": {
                        "sense_id": "fam:check:active",
                        "target_lemma": "cheque",
                        "evidence_views": {"all_evidence_text": "bank check"},
                    },
                    "shadows": [],
                    "cases": [],
                }
            ]
        }
        llm_batch_payload = {
            "batch_id": "batch:test",
            "source_id": "source:test",
            "prompt_version": "semantic_prompt_bakeoff_v2",
            "model_id": "gpt-5.4",
            "generated_at": "2026-04-24T12:00:00Z",
            "review_state": "unreviewed",
            "rows": [
                {
                    "row_id": "row:check",
                    "relation_type": "anchor_cue",
                    "evidence_text": "signed deposited cashed payment slip",
                    "review_state": "unreviewed",
                    "runtime_publishable": False,
                    "provenance": {"prompt_slot": "cue_cross_pos_frame_v1"},
                    "active_sense_hint": {"target_key": "fam:check:active"},
                    "metadata": {"family_id": "fam:check"},
                }
            ],
        }

        augmented_dataset, coverage_rows, batch_summary = augment_queue_dataset_with_llm_cue_views(
            dataset_payload,
            family_roles={"fam:check": "target"},
            llm_batch_payload=llm_batch_payload,
        )

        active_views = augmented_dataset["families"][0]["active"]["evidence_views"]
        self.assertIn("llm_cue_plus_all_evidence", active_views)
        self.assertTrue(active_views["llm_cue_plus_all_evidence"].endswith("payment slip"))
        self.assertEqual(coverage_rows[0]["llm_cue_row_count"], 1)
        self.assertEqual(batch_summary["runtime_publishable_count"], 0)
        self.assertEqual(batch_summary["distinct_review_states"], ["unreviewed"])

    @staticmethod
    def _pack(path: str) -> object:
        class _Pack:
            def __init__(self, path_value: str) -> None:
                self.path = Path(path_value)
                self.provider = "wiktionary"
                self.pack_id = "pack"
                self.direction = "test"

        pack = _Pack(path)
        pack.path.parent.mkdir(parents=True, exist_ok=True)
        pack.path.write_text("", encoding="utf-8")
        return pack


if __name__ == "__main__":
    unittest.main()
