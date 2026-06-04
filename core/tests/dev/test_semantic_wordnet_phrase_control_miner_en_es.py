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

from semantic_wordnet_phrase_control_miner_en_es import (  # noqa: E402
    build_wordnet_phrase_control_miner_bundle,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticWordnetPhraseControlMinerTests(unittest.TestCase):
    def test_miner_builds_containment_row_from_wordnet_example(self) -> None:
        bundle = build_wordnet_phrase_control_miner_bundle(
            dataset_payload=_dataset_payload(),
            heldout_case_payload=_heldout_payload(),
            wordnet_index=WordNetIndex(
                entries_by_word={},
                synsets_by_id={
                    "01686137-s": {
                        "partOfSpeech": "s",
                        "members": ["placed"],
                        "example": ["end tables placed conveniently"],
                    }
                },
                hyponyms_by_synset={},
                source_file_count=2,
            ),
            generated_at="2026-04-29T00:00:00Z",
        )

        self.assertEqual(bundle["report"]["status"], "ok")
        self.assertEqual(bundle["batch"]["row_count"], 1)
        row = bundle["batch"]["rows"][0]
        self.assertEqual(row["relation_type"], "phrase_control_example")
        self.assertIn("phrase_containment", row["roles"])
        self.assertEqual(row["metadata"]["phrase_containment_pattern"], "end tables")


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test_dataset",
        "families": [
            {
                "family_id": "fam:end",
                "trigger": "end",
                "active": {
                    "sense_id": "fam:end:active",
                    "target_lemma": "fin",
                    "canonical_pos": "noun",
                    "evidence_views": {"all_evidence_text": "either extremity"},
                },
                "shadows": [],
                "cases": [],
            }
        ],
    }


def _heldout_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "case_scope": "phrase_no_winner",
        "families": [
            {
                "family_id": "fam:end",
                "cases": [
                    {
                        "case_id": "case:end:001",
                        "sentence": "The end table held a small lamp.",
                        "source_phrase": "end",
                        "gold_winner": "none",
                        "gold_decision": "abstain",
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
