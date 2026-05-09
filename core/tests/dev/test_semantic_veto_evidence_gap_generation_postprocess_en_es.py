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

from semantic_veto_evidence_gap_generation_postprocess_en_es import (  # noqa: E402
    build_evidence_gap_generation_postprocess_report,
    render_evidence_gap_generation_postprocess_markdown,
)


class SemanticVetoEvidenceGapGenerationPostprocessTests(unittest.TestCase):
    def test_audits_generated_items_and_scores_filtered_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_evidence_gap_generation_postprocess_report(
                dataset_payload=_dataset_payload(),
                admission_payload=_admission_payload(),
                augmented_dir=Path(tmp),
                generated_at="2026-05-09T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["active_item_count"], 2)
        self.assertEqual(report["summary"]["high_eval_overlap_count"], 1)
        self.assertEqual(report["summary"]["target_lemma_in_note_count"], 1)

        audits_by_sentence = {row["sentence"]: row for row in report["item_audits"]}
        smile = audits_by_sentence["She tried to smile after hearing the good news."]
        self.assertEqual(smile["observed_source_syntax"], "verb_infinitive")
        self.assertGreaterEqual(smile["pos_anchor_strength"], 0.9)
        self.assertIn("high_eval_overlap", smile["flags"])
        self.assertIn("target_lemma_in_evidence_note", smile["flags"])

        by_view = {row["view_id"]: row for row in report["view_scores"]}
        self.assertIn("sentence_only_all", by_view)
        self.assertIn("note_only_diagnostic", by_view)
        self.assertEqual(by_view["no_high_eval_overlap_sentence_only"]["item_count"], 1)
        self.assertEqual(by_view["all_sentence_plus_note"]["score_status"], "ok")

        markdown = render_evidence_gap_generation_postprocess_markdown(report)
        self.assertIn("Generated-Evidence Postprocess", markdown)
        self.assertIn("sentence_only_all", markdown)


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "dataset_id": "tiny-postprocess",
        "pair": "en-es",
        "families": [
            {
                "family_id": "family:smile:sonreir",
                "trigger": "smile",
                "active": {
                    "sense_id": "family:smile:sonreir:active",
                    "target_lemma": "sonreír",
                    "canonical_pos": "verb",
                    "evidence_views": {
                        "all_evidence_text": "smile -> sonreír | make a smiling facial expression",
                        "sense_label": "smile -> sonreír",
                    },
                },
                "shadows": [],
                "cases": [
                    {
                        "case_id": "case:active",
                        "sentence": "Please smile for the camera.",
                        "source_phrase": "smile",
                        "gold_decision": "replace",
                        "gold_winner": "family:smile:sonreir:active",
                    },
                    {
                        "case_id": "case:noun",
                        "sentence": "Her smile returned after the good news.",
                        "source_phrase": "smile",
                        "gold_decision": "abstain",
                        "gold_winner": "none",
                    },
                ],
            }
        ],
    }


def _admission_payload() -> dict[str, object]:
    return {
        "summary": {"coverage_waived_item_count": 0},
        "admitted_items": [
            {
                "item_id": "item:smile:1",
                "family_id": "family:smile:sonreir",
                "pilot_arm": "high_need",
                "slot_type": "active_evidence_expansion",
                "source_phrase": "smile",
                "target_lemma": "sonreír",
                "sentence": "She tried to smile after hearing the good news.",
                "evidence_note": "The verb use matches the active sense of sonreír.",
            },
            {
                "item_id": "item:smile:2",
                "family_id": "family:smile:sonreir",
                "pilot_arm": "high_need",
                "slot_type": "active_evidence_expansion",
                "source_phrase": "smile",
                "target_lemma": "sonreír",
                "sentence": "He could not smile because the bright light made him squint.",
                "evidence_note": "Facial expression action.",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
