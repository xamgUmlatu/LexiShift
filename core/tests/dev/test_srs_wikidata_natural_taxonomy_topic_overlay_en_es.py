from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_wikidata_natural_taxonomy_topic_overlay_en_es import build_overlay  # noqa: E402


class TestSrsWikidataNaturalTaxonomyTopicOverlayEnEs(unittest.TestCase):
    def test_build_overlay_promotes_new_natural_taxonomy_candidates(self) -> None:
        report = build_overlay(
            candidate_payload={
                "decision": "srs_wikidata_natural_taxonomy_candidates_ready",
                "new_candidates": [
                    {
                        "lemma": "perro",
                        "topic": "animals",
                        "membership": 1.0,
                        "confidence_label": "strong_direct_taxonomy",
                        "wikidata_qids": ["Q144"],
                        "wikidata_roots": ["animal"],
                        "wikidata_match_kinds": ["label"],
                    },
                    {
                        "lemma": "manzana",
                        "topic": "plants_nature",
                        "membership": 0.65,
                        "confidence_label": "light",
                        "wikidata_qids": ["Q89"],
                        "wikidata_roots": ["fruit"],
                        "wikidata_match_kinds": ["label"],
                    },
                    {
                        "lemma": "jugar",
                        "topic": "games",
                        "membership": 1.0,
                        "confidence_label": "strong_direct_taxonomy",
                    },
                    {
                        "lemma": "rubio",
                        "topic": "animals",
                        "membership": 1.0,
                        "confidence_label": "strong_direct_taxonomy",
                    },
                ],
            },
            generated_at="2026-05-23T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["row_count"], 2)
        self.assertEqual(report["summary"]["counts_by_topic"], {"animals": 1, "plants_nature": 1})
        rows_by_lemma = {str(row["lemma"]): row for row in report["rows"]}
        self.assertEqual(rows_by_lemma["perro"]["confidence_label"], "strong")
        self.assertEqual(rows_by_lemma["perro"]["membership"], 1.0)
        self.assertEqual(rows_by_lemma["manzana"]["confidence_label"], "light")
        self.assertEqual(rows_by_lemma["manzana"]["membership"], 0.65)
        self.assertEqual(report["summary"]["skipped_count"], 2)
        self.assertEqual(report["rows"][0]["source_channel"], "wikidata_structured_data")
        self.assertEqual(report["rows"][0]["provenance"]["runtime_dependency"], "none")


if __name__ == "__main__":
    unittest.main()
