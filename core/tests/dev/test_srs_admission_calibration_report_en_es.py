from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_admission_calibration_report_en_es import build_report, render_markdown  # noqa: E402


def _create_frequency_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT,
                profile_topics TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos,
                profile_topics
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                ("alpha", 1.0, 100.0, "n", None),
                ("beta", 2.0, 98.0, "n", None),
                ("gamma", 3.0, 96.0, "n", None),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_overlay(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "overlay_id": "unit_animals_plants_overlay",
                "overlay_policy": {
                    "promotion_state": "poc_candidate_not_product_overlay",
                },
                "summary": {"row_count": 2},
                "rows": [
                    {
                        "lemma": "beta",
                        "language_pair": "en-es",
                        "topic": "animals",
                        "membership": 1.0,
                        "review_id": "unit-animal",
                        "confidence_label": "strong",
                    },
                    {
                        "lemma": "gamma",
                        "language_pair": "en-es",
                        "topic": "plants_nature",
                        "membership": 1.0,
                        "review_id": "unit-plant",
                        "confidence_label": "strong",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


class TestSrsAdmissionCalibrationReportEnEs(unittest.TestCase):
    def test_build_report_summarizes_ranked_and_weighted_topic_shares(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = _create_frequency_db(root / "freq.sqlite")
            overlay_path = _create_overlay(root / "overlay.json")

            report = build_report(
                frequency_db=frequency_db,
                overlay_source_path=overlay_path,
                set_top_n=3,
                admission_budget=3,
                weighted_seeds=(1, 2),
                augment_with_zipf_bridge=False,
            )

        self.assertEqual(report["summary"]["fail_count"], 0)
        ranked_rows = {row["name"]: row for row in report["ranked_rows"]}
        weighted_rows = {row["name"]: row for row in report["weighted_rows"]}
        self.assertEqual(ranked_rows["neutral"]["selected_topic_share"], 0.0)
        self.assertGreater(ranked_rows["animals_interest"]["selected_topic_share"], 0.0)
        self.assertGreater(ranked_rows["plants_nature_interest"]["selected_topic_share"], 0.0)
        self.assertEqual(weighted_rows["animals_interest"]["seed_count"], 2)
        self.assertIn("mean_selected_topic_share", weighted_rows["animals_interest"])
        self.assertTrue(report["comparisons"]["ranked_animals_strength_monotonic"])

        markdown = render_markdown(report)
        self.assertIn("## Ranked Admission Batch Shares", markdown)
        self.assertIn("## Weighted Admission Batch Shares", markdown)


if __name__ == "__main__":
    unittest.main()
