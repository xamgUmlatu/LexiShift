from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_wikidata_natural_taxonomy_candidates_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class TestSrsWikidataNaturalTaxonomyCandidatesEnEs(unittest.TestCase):
    def test_build_report_intersects_wikidata_rows_with_local_lemmas(self) -> None:
        report = build_report(
            local_lemmas=["flor", "manzana", "perro", "roble", "árbol"],
            wikidata_rows=[
                {"lemma": "flor", "qid": "Q506", "root": "flower", "match_kind": "label"},
                {"lemma": "manzana", "qid": "Q89", "root": "fruit", "match_kind": "label"},
                {"lemma": "perro", "qid": "Q144", "root": "animal", "match_kind": "label"},
                {"lemma": "roble", "qid": "Q33036816", "root": "tree", "match_kind": "label"},
                {"lemma": "fuera", "qid": "Q1", "root": "plant", "match_kind": "label"},
            ],
            existing_overlay_payloads=[
                {
                    "status": "ok",
                    "rows": [
                        {
                            "lemma": "flor",
                            "topic": "plants_nature",
                            "confidence_label": "strong",
                        }
                    ],
                }
            ],
            generated_at="2026-05-23T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["wikidata_match_count"], 4)
        self.assertEqual(report["summary"]["new_candidate_count"], 3)
        self.assertEqual(report["summary"]["new_strong_candidate_count"], 2)
        by_key = {(str(row["topic"]), str(row["lemma"])): row for row in report["new_candidates"]}
        self.assertEqual(
            by_key[("plants_nature", "roble")]["confidence_label"],
            "strong_direct_taxonomy",
        )
        self.assertEqual(
            by_key[("animals", "perro")]["confidence_label"],
            "strong_direct_taxonomy",
        )
        candidates = {str(row["lemma"]): row for row in report["new_candidates"]}
        self.assertEqual(candidates["manzana"]["confidence_label"], "light")
        self.assertNotIn("fuera", candidates)

        markdown = render_markdown(report)
        self.assertIn("Wikidata Natural Taxonomy Candidate Audit", markdown)
        self.assertIn("animals", markdown)
        self.assertIn("roble", markdown)


if __name__ == "__main__":
    unittest.main()
