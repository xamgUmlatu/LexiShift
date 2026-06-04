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

from semantic_wordnet_alternate_sense_phrase_evidence_en_es import (  # noqa: E402
    build_wordnet_alternate_sense_phrase_bundle,
    render_wordnet_alternate_sense_phrase_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticWordnetAlternateSensePhraseEvidenceTests(unittest.TestCase):
    def test_builds_phrase_control_rows_for_non_active_wordnet_senses(self) -> None:
        bundle = build_wordnet_alternate_sense_phrase_bundle(
            dataset_payload=_dataset_payload(),
            wordnet_index=_wordnet_index(),
            generated_at="2026-04-29T04:00:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "external")
        self.assertEqual(normalized["source_family"], "external_sense_graph")
        self.assertEqual(normalized["row_count"], 2)
        self.assertEqual(
            {row["relation_type"] for row in normalized["rows"]},
            {"phrase_control_example"},
        )
        evidence_texts = [row["evidence_text"] for row in normalized["rows"]]
        self.assertTrue(any("animal" in text for text in evidence_texts))
        self.assertTrue(any("carry" in text for text in evidence_texts))
        self.assertFalse(any("financial trader" in text for text in evidence_texts))

        report = bundle["report"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["source_family_count"], 1)
        self.assertEqual(report["summary"]["active_like_skip_count"], 1)

        markdown = render_wordnet_alternate_sense_phrase_markdown(report)
        self.assertIn("Alternate-Sense Phrase Evidence", markdown)
        self.assertIn("Active-like Skips", markdown)

    def test_respects_max_rows_per_family(self) -> None:
        bundle = build_wordnet_alternate_sense_phrase_bundle(
            dataset_payload=_dataset_payload(),
            wordnet_index=_wordnet_index(),
            max_rows_per_family=1,
            generated_at="2026-04-29T04:00:00Z",
        )

        self.assertEqual(bundle["normalized_batch"]["row_count"], 1)
        self.assertEqual(bundle["report"]["summary"]["row_count"], 1)


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:bear",
                "trigger": "bear",
                "active": {
                    "sense_id": "bear:active",
                    "target_lemma": "bajista",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "bear noun sense: financial trader",
                        "gloss_text": "financial trader",
                        "all_evidence_text": "bear financial trader stock market",
                    },
                    "metadata": {"translation_sense_text": "financial trader"},
                },
                "shadows": [],
            }
        ],
    }


def _wordnet_index() -> WordNetIndex:
    return WordNetIndex(
        entries_by_word={
            "bear": {
                "n": {
                    "sense": [
                        {"id": "bear%1:animal", "synset": "bear-animal-n"},
                        {"id": "bear%1:finance", "synset": "bear-finance-n"},
                    ]
                },
                "v": {
                    "sense": [
                        {"id": "bear%2:carry", "synset": "bear-carry-v"},
                    ]
                },
            }
        },
        synsets_by_id={
            "bear-animal-n": {
                "definition": ["large animal with claws"],
                "example": ["The bear crossed the trail."],
                "members": ["bear"],
            },
            "bear-finance-n": {
                "definition": ["financial trader expecting stocks to fall"],
                "example": ["The bear sold shares."],
                "members": ["bear"],
            },
            "bear-carry-v": {
                "definition": ["to carry or support"],
                "example": ["Workers bear the load."],
                "members": ["bear"],
            },
        },
        hyponyms_by_synset={},
        source_file_count=2,
    )


if __name__ == "__main__":
    unittest.main()
