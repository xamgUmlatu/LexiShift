from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_wikidata_plants_topic_candidates_en_es import build_report, render_markdown  # noqa: E402


class TestSrsWikidataPlantsTopicCandidatesEnEs(unittest.TestCase):
    def test_build_report_intersects_wikidata_rows_with_local_lemmas(self) -> None:
        report = build_report(
            local_lemmas=["flor", "manzana", "perro", "roble", "árbol"],
            wikidata_rows=[
                {"lemma": "flor", "qid": "Q506", "root": "flower"},
                {"lemma": "manzana", "qid": "Q89", "root": "fruit"},
                {"lemma": "perro", "qid": "Q144", "root": "animal"},
                {"lemma": "roble", "qid": "Q33036816", "root": "tree"},
                {"lemma": "fuera", "qid": "Q1", "root": "plant"},
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
        self.assertEqual(report["summary"]["wikidata_match_count"], 3)
        self.assertEqual(report["summary"]["new_candidate_count"], 2)
        self.assertEqual(report["summary"]["new_strong_candidate_count"], 1)
        candidates = {row["lemma"]: row for row in report["new_candidates"]}
        self.assertEqual(candidates["roble"]["confidence_label"], "strong_direct_plant")
        self.assertEqual(candidates["manzana"]["confidence_label"], "light")
        self.assertNotIn("perro", candidates)
        self.assertNotIn("fuera", candidates)

        markdown = render_markdown(report)
        self.assertIn("Wikidata Plants/Nature Candidate Audit", markdown)
        self.assertIn("roble", markdown)


if __name__ == "__main__":
    unittest.main()
