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

from semantic_translation_sense_evidence_batch_en_es import (  # noqa: E402
    build_translation_sense_evidence_bundle,
    render_translation_sense_evidence_markdown,
)


class SemanticTranslationSenseEvidenceBatchTests(unittest.TestCase):
    def test_builds_supported_translation_sense_rows_without_target_leakage(self) -> None:
        bundle = build_translation_sense_evidence_bundle(
            dataset_payload=_dataset_payload(),
            generated_at="2026-04-29T02:00:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "external")
        self.assertEqual(normalized["source_family"], "external_structured_dictionary_dump")
        self.assertEqual(normalized["row_count"], 2)
        self.assertEqual(
            [row["relation_type"] for row in normalized["rows"]],
            ["anchor_cue", "shadow_candidate"],
        )

        active_row = normalized["rows"][0]
        shadow_row = normalized["rows"][1]
        self.assertEqual(active_row["candidate_sense_hint"]["target_key"], "black:active")
        self.assertEqual(shadow_row["candidate_sense_hint"]["target_key"], "black:shadow")
        self.assertIn("black adjective sense: without light", active_row["evidence_text"])
        self.assertIn("black noun sense: color", shadow_row["evidence_text"])
        self.assertNotIn("oscuro", active_row["evidence_text"].lower())
        self.assertNotIn("negro", shadow_row["evidence_text"].lower())
        self.assertEqual(active_row["metadata"]["source_view"], "translation_sense_text")
        self.assertEqual(active_row["metadata"]["active_sense_id"], "black:active")
        self.assertEqual(shadow_row["metadata"]["candidate_sense_id"], "black:shadow")
        self.assertEqual(
            active_row["metadata"]["wiktextract_translation_support_matches"][0][
                "translation_sense"
            ],
            "without light",
        )

        report = bundle["report"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["source_family_count"], 1)
        self.assertEqual(report["summary"]["target_family_count"], 1)
        self.assertEqual(report["summary"]["selected_sense_count"], 2)
        self.assertEqual(report["summary"]["source_supported_sense_count"], 2)

        markdown = render_translation_sense_evidence_markdown(report)
        self.assertIn("Translation-Sense Evidence Batch", markdown)
        self.assertIn("external_structured_dictionary_dump", markdown)

    def test_skips_senses_without_wiktextract_support_matches(self) -> None:
        dataset = _dataset_payload()
        dataset["families"][0]["shadows"][0]["metadata"][
            "wiktextract_translation_support_matches"
        ] = []

        bundle = build_translation_sense_evidence_bundle(
            dataset_payload=dataset,
            generated_at="2026-04-29T02:00:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["row_count"], 1)
        self.assertEqual(normalized["rows"][0]["relation_type"], "anchor_cue")
        self.assertEqual(bundle["report"]["status"], "review")
        self.assertEqual(bundle["report"]["summary"]["skipped_sense_count"], 1)


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:black",
                "trigger": "black",
                "active": {
                    "sense_id": "black:active",
                    "target_lemma": "oscuro",
                    "canonical_pos": "adjective",
                    "evidence_views": {
                        "gloss_text": "without light",
                        "all_evidence_text": "oscuro | black adjective sense: without light",
                    },
                    "metadata": {
                        "translation_sense_text": "without light",
                        "support_sources": [
                            "wiktionary_en_es",
                            "wiktextract_en_es_translation_table",
                        ],
                        "wiktextract_translation_support": True,
                        "wiktextract_translation_support_matches": [
                            {
                                "record_word": "black",
                                "record_pos": "adj",
                                "translation_word": "oscuro",
                                "translation_sense": "without light",
                                "translation_tags": ["masculine"],
                                "sense_overlap": ["light"],
                            }
                        ],
                    },
                },
                "shadows": [
                    {
                        "sense_id": "black:shadow",
                        "target_lemma": "negro",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "gloss_text": "color",
                            "all_evidence_text": "negro | black noun sense: color",
                        },
                        "metadata": {
                            "translation_sense_text": "color",
                            "support_sources": [
                                "wiktionary_en_es",
                                "wiktextract_en_es_translation_table",
                            ],
                            "wiktextract_translation_support": True,
                            "wiktextract_translation_support_matches": [
                                {
                                    "record_word": "black",
                                    "record_pos": "noun",
                                    "translation_word": "negro",
                                    "translation_sense": "color",
                                    "translation_tags": ["masculine"],
                                    "sense_overlap": ["color"],
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
