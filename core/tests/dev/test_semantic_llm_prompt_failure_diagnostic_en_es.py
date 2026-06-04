from __future__ import annotations

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

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from semantic_llm_prompt_failure_diagnostic_en_es import (  # noqa: E402
    build_failure_diagnostic_report,
    render_failure_diagnostic_markdown,
)


class SemanticLlmPromptFailureDiagnosticTests(unittest.TestCase):
    def test_failure_diagnostic_report_includes_ablation_and_rescue_surfaces(self) -> None:
        queue_payload, dataset_payload, llm_batch_payload = _sample_inputs()
        reverse_records_by_trigger = {
            "check": (
                TranslationGlossRecord(
                    translation="cheque",
                    pos_raw="noun",
                    metadata={"translation_sense_text": "signed bank payment document"},
                ),
                TranslationGlossRecord(
                    translation="revisar",
                    pos_raw="verb",
                    metadata={"translation_sense_text": "inspect or verify information"},
                ),
            )
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            reverse_pack = _pack(str(Path(tmpdir) / "reverse.sqlite"))
            report = build_failure_diagnostic_report(
                queue_payload=queue_payload,
                dataset_payload=dataset_payload,
                llm_batch_payload=llm_batch_payload,
                reverse_records_by_trigger=reverse_records_by_trigger,
                data_root=REPO_ROOT,
                reverse_pack=reverse_pack,
                scorer_id="tfidf_cosine",
                min_active_score=0.0,
                min_margin=0.0,
                generated_at="2026-04-24T12:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        config_ids = {
            str(row.get("config_id") or "")
            for row in report["configurations"]
            if isinstance(row, dict)
        }
        self.assertIn("hard_reverse_aux_active_only", config_ids)
        self.assertIn("hard_reverse_aux_plus_llm_cue", config_ids)
        self.assertGreater(len(report["llm_rescue_sweep"]), 0)
        self.assertIn("reverse_aux_shadow_side_is_material", report["summary_findings"])

        markdown = render_failure_diagnostic_markdown(report)
        self.assertIn("Semantic LLM Prompt Failure Diagnostic", markdown)
        self.assertIn("LLM Rescue Probe", markdown)
        self.assertIn("Hard reverse aux active-only", markdown)


def _sample_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    queue_payload = {
        "queue_id": "semantic_prompt_bakeoff_test",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "role": "target",
                "likely_bucket": "needs_cue_data",
                "primary_prompt_slot": "cue_cross_pos_overlap_v1",
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
        "prompt_version": "semantic_prompt_bakeoff_v3",
        "model_id": "gpt-5.4",
        "generated_at": "2026-04-24T12:00:00Z",
        "review_state": "unreviewed",
        "rows": [
            {
                "row_id": "row:check",
                "relation_type": "anchor_cue",
                "evidence_text": "signed check for rent payment",
                "review_state": "unreviewed",
                "runtime_publishable": False,
                "provenance": {"prompt_slot": "cue_cross_pos_overlap_v1"},
                "active_sense_hint": {"target_key": "fam:check:active"},
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                },
            }
        ],
    }
    return queue_payload, dataset_payload, llm_batch_payload


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
