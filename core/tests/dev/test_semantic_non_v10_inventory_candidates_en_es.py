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

from semantic_non_v10_inventory_candidates_en_es import (  # noqa: E402
    build_non_v10_inventory_candidate_report,
    render_non_v10_inventory_candidate_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticNonV10InventoryCandidateTests(unittest.TestCase):
    def test_candidate_report_ranks_non_existing_cross_pos_headwords(self) -> None:
        report = build_non_v10_inventory_candidate_report(
            wordnet_index=_wordnet_index(),
            existing_trigger_payloads=[
                {
                    "families": [
                        {"trigger": "bank"},
                    ]
                }
            ],
            limit=10,
            min_score=0.0,
            generated_at="2026-04-26T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "inventory_candidates_found")
        triggers = [row["trigger"] for row in report["candidates"]]
        self.assertIn("seal", triggers)
        self.assertIn("draft", triggers)
        self.assertNotIn("bank", triggers)

        seal = [row for row in report["candidates"] if row["trigger"] == "seal"][0]
        self.assertTrue(seal["noun_verb"])
        self.assertEqual(seal["archetype"], "wordnet_noun_verb_cross_pos")
        self.assertGreaterEqual(seal["source_definition_count"], 2)
        self.assertGreaterEqual(seal["source_example_count"], 1)

        markdown = render_non_v10_inventory_candidate_markdown(report)
        self.assertIn("Non-v10 Semantic Inventory Candidates", markdown)
        self.assertIn("seal", markdown)

    def test_candidate_report_keeps_same_pos_polysemy_when_no_cross_pos_exists(self) -> None:
        report = build_non_v10_inventory_candidate_report(
            wordnet_index=_wordnet_index(),
            existing_trigger_payloads=[],
            limit=10,
            min_score=0.0,
            generated_at="2026-04-26T00:00:00Z",
        )

        spring = [row for row in report["candidates"] if row["trigger"] == "spring"][0]
        self.assertFalse(spring["cross_pos"])
        self.assertTrue(spring["same_pos_polysemy"])
        self.assertEqual(spring["archetype"], "wordnet_same_pos_polysemy")


def _wordnet_index() -> WordNetIndex:
    return WordNetIndex(
        entries_by_word={
            "bank": {
                "n": {"sense": [{"synset": "bank-n-1"}, {"synset": "bank-n-2"}]},
                "v": {"sense": [{"synset": "bank-v-1"}]},
            },
            "draft": {
                "n": {"sense": [{"synset": "draft-n-1"}]},
                "v": {"sense": [{"synset": "draft-v-1"}]},
            },
            "seal": {
                "n": {"sense": [{"synset": "seal-n-1"}, {"synset": "seal-n-2"}]},
                "v": {"sense": [{"synset": "seal-v-1"}]},
            },
            "spring": {
                "n": {"sense": [{"synset": "spring-n-1"}, {"synset": "spring-n-2"}]},
            },
            "the": {
                "n": {"sense": [{"synset": "the-n-1"}, {"synset": "the-n-2"}]},
            },
        },
        synsets_by_id={
            "bank-n-1": {
                "definition": ["financial institution"],
                "example": ["the bank approved the loan"],
                "members": ["depository financial institution"],
            },
            "bank-n-2": {
                "definition": ["sloping land beside water"],
                "example": ["the river bank flooded"],
            },
            "bank-v-1": {
                "definition": ["deposit money"],
                "example": ["bank the check"],
            },
            "draft-n-1": {
                "definition": ["a preliminary version of writing"],
                "example": ["the draft needs edits"],
            },
            "draft-v-1": {
                "definition": ["write a preliminary version"],
                "example": ["draft the letter"],
            },
            "seal-n-1": {
                "definition": ["official stamp"],
                "example": ["the seal was on the document"],
                "members": ["stamp"],
            },
            "seal-n-2": {
                "definition": ["marine mammal"],
                "example": ["a seal swam nearby"],
            },
            "seal-v-1": {
                "definition": ["close tightly"],
                "example": ["seal the envelope"],
            },
            "spring-n-1": {
                "definition": ["season after winter"],
                "example": ["flowers bloom in spring"],
            },
            "spring-n-2": {
                "definition": ["coiled elastic device"],
                "example": ["the spring snapped"],
            },
            "the-n-1": {"definition": ["ignored one"]},
            "the-n-2": {"definition": ["ignored two"]},
        },
        hyponyms_by_synset={},
        source_file_count=3,
    )


if __name__ == "__main__":
    unittest.main()
