from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_srs_zipf_bridge_en_es import (  # noqa: E402
    build_full_srs_admissible_rows,
    build_srs_zipf_bridge_report,
    render_srs_zipf_bridge_markdown,
)


class SemanticVetoSrsZipfBridgeTests(unittest.TestCase):
    def test_full_srs_rows_can_use_candidate_frequency_db_override(self) -> None:
        with TemporaryDirectory() as temp_dir:
            frequency_db = Path(temp_dir) / "candidate.sqlite"
            _write_frequency_db(frequency_db)

            rows, inputs = build_full_srs_admissible_rows(
                pair="en-es",
                top_n=3,
                frequency_db=frequency_db,
            )

        self.assertEqual(inputs["status"], "ok")
        self.assertEqual(inputs["frequency_db_source"], "override")
        self.assertEqual(inputs["frequency_db"], str(frequency_db))
        self.assertEqual(inputs["seed_row_count"], 3)
        self.assertEqual(inputs["unique_target_count"], 3)
        self.assertCountEqual([row["lemma"] for row in rows], ["uno", "dos", "tres"])

    def test_reports_srs_targets_and_source_target_pairs_separately(self) -> None:
        report = build_srs_zipf_bridge_report(
            srs_journey_payload={
                "scenario": {
                    "pair": "en-es",
                    "name": "fixture",
                    "resource_mode": "installed",
                    "candidate_universe": [
                        {
                            "lemma": "siglo",
                            "selected": True,
                            "admission_weight": 0.7,
                        },
                        {
                            "lemma": "música",
                            "selected": False,
                            "admission_weight": 0.4,
                        },
                    ],
                },
                "phases": [
                    {
                        "items": [
                            {
                                "lemma": "siglo",
                                "confidence": 0.7,
                                "in_due": True,
                                "in_published": True,
                            },
                            {
                                "lemma": "música",
                                "confidence": 0.4,
                                "in_due": False,
                                "in_published": False,
                            },
                        ],
                        "sets": {"published": ["siglo"]},
                        "runtime": {
                            "ruleset_source_target_pairs": [
                                {"source": "century", "target": "siglo"},
                                {"source": "music", "target": "música"},
                            ]
                        },
                    }
                ],
            },
            full_srs_rows=[
                {"lemma": "siglo", "admission_weight": 0.7},
                {"lemma": "música", "admission_weight": 0.4},
            ],
            full_srs_inputs={
                "status": "ok",
                "pair": "en-es",
                "seed_row_count": 2,
                "frequency_db_source": "override",
            },
            full_source_target_pairs=[
                {"source": "century", "target": "siglo"},
                {"source": "music", "target": "música"},
            ],
            full_rulegen_inputs={
                "status": "ok",
                "rule_count": 2,
                "source_target_pair_count": 2,
            },
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["full_srs_admissible_target_count"], 2)
        self.assertEqual(report["summary"]["srs_candidate_target_count"], 2)
        self.assertEqual(report["summary"]["srs_selected_initial_active_count"], 1)
        self.assertEqual(report["summary"]["journey_union_source_target_pair_count"], 2)
        self.assertEqual(report["summary"]["full_source_target_pair_count"], 2)
        self.assertEqual(
            report["summary"]["source_mapping_status"], "source_target_pairs_available"
        )
        self.assertEqual(
            report["summary"]["full_source_mapping_status"],
            "full_source_target_pairs_available",
        )
        self.assertTrue(report["full_source_target_family_zipf_matrix"])
        self.assertTrue(report["source_target_family_zipf_matrix"])
        self.assertEqual(len(report["full_source_target_pairs"]), 2)
        self.assertIn("source_zipf_band_en", report["full_source_target_pairs"][0])
        self.assertIn(
            "full_srs_universe_uses_candidate_frequency_db_override",
            report["limitations"],
        )

        markdown = render_srs_zipf_bridge_markdown(report)
        self.assertIn("Target-Side SRS Distribution", markdown)
        self.assertIn("Full SRS-admissible targets", markdown)
        self.assertIn("Full Source-Target Family Matrix", markdown)

    def test_marks_missing_source_target_pairs_for_review(self) -> None:
        report = build_srs_zipf_bridge_report(
            srs_journey_payload={
                "scenario": {
                    "pair": "en-es",
                    "candidate_universe": [{"lemma": "siglo", "selected": True}],
                },
                "phases": [
                    {
                        "items": [{"lemma": "siglo", "in_due": True, "in_published": True}],
                        "sets": {"published": ["siglo"]},
                        "runtime": {"ruleset_sources_preview": ["century"]},
                    }
                ],
            },
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("source_target_rule_pairs_missing", report["summary"]["issues"])
        self.assertEqual(
            report["summary"]["source_mapping_status"],
            "preview_only_sources_without_targets",
        )


def _write_frequency_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE frequency (id INTEGER PRIMARY KEY, lemma TEXT NOT NULL, freq REAL)"
        )
        conn.executemany(
            "INSERT INTO frequency (id, lemma, freq) VALUES (?, ?, ?)",
            [(1, "uno", 6.0), (2, "dos", 5.0), (3, "tres", 4.0)],
        )
        conn.commit()


if __name__ == "__main__":
    unittest.main()
