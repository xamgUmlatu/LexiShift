from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_family_depth_audit_en_es import build_report, render_markdown  # noqa: E402


class SrsTopicFamilyDepthAuditTests(unittest.TestCase):
    def test_build_report_measures_trusted_topics_and_register_review_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            taxonomy.write_text(json.dumps(_taxonomy_json()), encoding="utf-8")
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                taxonomy_path=taxonomy,
                kaikki_forward_db=kaikki_db,
                difficulty_ranking_csv=None,
                frontiers=[("unit_frontier", frequency_db, True)],
                top_n=8,
                generated_at="2026-05-19T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            frontier = report["frontiers"][0]
            family_by_id = {row["family"]: row for row in frontier["families"]}
            medicine = family_by_id["medicine_health"]
            self.assertEqual(medicine["trusted_candidate_count"], 2)
            self.assertGreaterEqual(medicine["trusted_nonempty_band_count"], 1)
            labels = {row["label"]: row["count"] for row in medicine["trusted_top_source_labels"]}
            self.assertEqual(labels["medicine"], 2)

            register = family_by_id["casual_slang_register"]
            self.assertEqual(register["trusted_candidate_count"], 0)
            self.assertEqual(register["review_only_candidate_count"], 1)
            self.assertEqual(register["coverage_posture"], "review_only_signal_available")

            animals = family_by_id["animals"]
            self.assertEqual(animals["trusted_candidate_count"], 0)
            excluded_labels = {
                row["label"]: row["count"] for row in animals["trusted_excluded_source_labels"]
            }
            self.assertEqual(excluded_labels["animals"], 1)
            self.assertEqual(animals["trusted_excluded_examples"][0]["lemma"], "perro")

            markdown = render_markdown(report)
            self.assertIn("Topic Family Depth Audit", markdown)
            self.assertIn("casual_slang_register", markdown)

    def test_missing_optional_frontier_is_warning_not_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            frequency_db = root / "freq.sqlite"
            missing_db = root / "missing.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            taxonomy.write_text(json.dumps(_taxonomy_json()), encoding="utf-8")
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                taxonomy_path=taxonomy,
                kaikki_forward_db=kaikki_db,
                difficulty_ranking_csv=None,
                frontiers=[
                    ("unit_frontier", frequency_db, True),
                    ("optional_missing", missing_db, False),
                ],
                top_n=8,
                generated_at="2026-05-19T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            self.assertIn("frontier_missing:optional_missing", report["summary"]["warnings"])
            self.assertEqual(report["summary"]["issues"], [])

    def test_corrected_ranking_csv_drives_difficulty_bands_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            ranking_csv = root / "ranking.csv"
            taxonomy.write_text(json.dumps(_taxonomy_json()), encoding="utf-8")
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)
            ranking_csv.write_text(
                "rank,lemma,score\n1,salud,0.10\n2,clínica,0.90\n",
                encoding="utf-8",
            )

            report = build_report(
                taxonomy_path=taxonomy,
                kaikki_forward_db=kaikki_db,
                difficulty_ranking_csv=ranking_csv,
                frontiers=[("unit_frontier", frequency_db, True)],
                top_n=8,
                generated_at="2026-05-19T00:00:00+00:00",
            )

            self.assertEqual(
                report["methodology"]["difficulty_source"],
                "corrected_learner_difficulty_ranking",
            )
            self.assertEqual(report["difficulty_ranking"]["score_count"], 2)
            frontier = report["frontiers"][0]
            self.assertEqual(
                frontier["difficulty_source_counts"]["corrected_learner_difficulty_ranking"],
                2,
            )
            medicine = {row["family"]: row for row in frontier["families"]}["medicine_health"]
            self.assertEqual(medicine["trusted_nonempty_band_count"], 2)
            self.assertEqual(medicine["trusted_max_difficulty"], 0.9)
            hardest = medicine["trusted_hardest_examples"][0]
            self.assertEqual(hardest["lemma"], "clínica")
            self.assertEqual(
                hardest["difficulty_source"],
                "corrected_learner_difficulty_ranking",
            )


def _taxonomy_json() -> dict[str, object]:
    return {
        "schema_version": 1,
        "taxonomy_id": "unit_taxonomy",
        "families": [
            {
                "id": "medicine_health",
                "display_name": "Medicine & Health",
                "axis": "topic",
                "ux_group": "interests_style",
                "pair_scope": "all_supported_pairs",
                "readiness_state": "source_ready",
            },
            {
                "id": "animals",
                "display_name": "Animals",
                "axis": "topic",
                "ux_group": "interests_style",
                "pair_scope": "all_supported_pairs",
                "readiness_state": "p0_enrichment",
            },
            {
                "id": "casual_slang_register",
                "display_name": "Casual & Slang",
                "axis": "register",
                "ux_group": "interests_style",
                "pair_scope": "all_supported_pairs",
                "readiness_state": "review_only",
            },
        ],
        "source_label_mappings": [
            {
                "source_channel": "sense_topics",
                "source_label": "medicine",
                "target_family": "medicine_health",
                "weight": 0.9,
                "confidence": 0.9,
            },
            {
                "source_channel": "sense_topics",
                "source_label": "animals",
                "target_family": "animals",
                "weight": 0.9,
                "confidence": 0.9,
            },
        ],
        "source_topic_candidate_exclusions": [
            {
                "target_family": "animals",
                "source_labels": ["animals"],
                "lemmas": ["perro"],
                "reason": "unit-test exclusion",
            }
        ],
    }


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma, pos) VALUES (?, ?, ?, ?)",
            [
                (1, 1000.0, "el", "d"),
                (2, 900.0, "salud", "n"),
                (3, 800.0, "clínica", "n"),
                (4, 700.0, "onda", "n"),
                (5, 600.0, "perro", "n"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entry_meta (headword_lc TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "headword_lc TEXT, topics_json TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.executemany(
            "INSERT INTO entry_meta (headword_lc, tags_json, categories_json) VALUES (?, ?, ?)",
            [
                ("salud", "[]", "[]"),
                ("clínica", "[]", "[]"),
                ("onda", "[]", '["Spanish slang"]'),
                ("perro", "[]", "[]"),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(headword_lc, topics_json, tags_json, categories_json) VALUES (?, ?, ?, ?)",
            [
                ("salud", '["medicine"]', "[]", "[]"),
                ("clínica", '["medicine"]', "[]", "[]"),
                ("onda", "[]", '["slang"]', "[]"),
                ("perro", '["animals"]', "[]", "[]"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
