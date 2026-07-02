from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_wikidata_list_extractor_en_ja import (  # noqa: E402
    _evidence_rows_from_sparql_bindings,
    _sparql_query,
)


class SrsTopicAutotagWikidataListExtractorEnJaTests(unittest.TestCase):
    def test_exact_label_rows_keep_unique_candidates_and_reject_ambiguous_surfaces(self) -> None:
        candidates = [
            _candidate("寿司", "すし"),
            _candidate("今日", "きょう"),
            _candidate("今日", "こんにち"),
        ]
        collections = {
            "food_dishes_drinks": {
                "id": "food_dishes_drinks",
                "target_family": "food_cooking",
                "source_label": "food_dish_drink",
                "membership": 0.82,
                "confidence": 0.78,
            }
        }
        bindings = [
            _binding("寿司", "food_dishes_drinks", "Q123", "Q2095", "sushi", "food"),
            _binding("今日", "food_dishes_drinks", "Q999", "Q2095", "today", "food"),
        ]

        rows = _evidence_rows_from_sparql_bindings(
            bindings,
            candidates=candidates,
            collections=collections,
            policy=_policy(),
            overlay_keys={("寿司", "food_cooking")},
        )

        self.assertEqual([row["lemma"] for row in rows], ["寿司"])
        self.assertEqual(rows[0]["topic"], "food_cooking")
        self.assertEqual(rows[0]["source"], "wikidata_exact_label_list")
        self.assertTrue(rows[0]["extra"]["already_in_current_overlay"])

    def test_sparql_query_uses_label_only_by_default(self) -> None:
        query = _sparql_query(
            ["寿司"],
            [{"collection_id": "food_dishes_drinks", "qid": "Q2095"}],
            include_aliases=False,
        )

        self.assertIn('"寿司"@ja', query)
        self.assertIn('("food_dishes_drinks" wd:Q2095)', query)
        self.assertIn("rdfs:label ?label", query)
        self.assertNotIn("skos:altLabel ?label", query)


def _candidate(lemma: str, reading: str) -> dict[str, object]:
    return {
        "rank": 1,
        "lemma": lemma,
        "reading": reading,
        "score": 0.2,
        "band": "0.20-0.25",
        "core_rank": 1.0,
        "candidate_state": "normal_vocab",
        "topic_stretch_allowed": "true",
    }


def _binding(
    label: str,
    collection: str,
    item_qid: str,
    root_qid: str,
    item_label: str,
    root_label: str,
) -> dict[str, object]:
    return {
        "label": {"type": "literal", "value": label, "xml:lang": "ja"},
        "collection": {"type": "literal", "value": collection},
        "item": {"type": "uri", "value": f"http://www.wikidata.org/entity/{item_qid}"},
        "root": {"type": "uri", "value": f"http://www.wikidata.org/entity/{root_qid}"},
        "itemLabel": {"type": "literal", "value": item_label, "xml:lang": "en"},
        "rootLabel": {"type": "literal", "value": root_label, "xml:lang": "en"},
        "description": {"type": "literal", "value": "test item", "xml:lang": "en"},
        "matchKind": {"type": "literal", "value": "label"},
    }


def _policy() -> dict[str, object]:
    return {
        "source_posture": {
            "wikidata_online": {
                "default_membership": 0.75,
                "default_confidence": 0.72,
                "review_posture": "bounded_online_candidate_generation",
                "license_note": "Wikidata structured data is CC0.",
            }
        }
    }


if __name__ == "__main__":
    unittest.main()
