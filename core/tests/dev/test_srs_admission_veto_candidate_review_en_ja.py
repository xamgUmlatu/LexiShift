from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_admission_veto_candidate_review_en_ja import build_report, render_markdown  # noqa: E402


CSV_FIELDS = [
    "rank",
    "lemma",
    "reading",
    "score",
    "model_score",
    "correction_delta",
    "exact_commonness",
    "jlpt_exact_known",
    "jlpt_raw_exact_known",
    "jlpt_normalized_only_known",
    "lesson_known",
    "kana_preferred",
    "rare_wago_obscure_written",
    "kanji_surface",
    "same_surface_risk",
    "hard_form",
    "soft_form",
    "reading_inheritance",
    "tail_guard",
    "suspicion_full",
    "candidate_state",
    "correction_types",
    "display_form",
    "admission_override",
    "correction_status",
    "manual_correction_active",
    "manual_review",
    "review_flags",
]


class TestSrsAdmissionVetoCandidateReviewEnJa(unittest.TestCase):
    def test_tracks_hypothesis_visibility_and_active_hard_vetoes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_raw:
            temp_dir = Path(temp_dir_raw)
            csv_in = temp_dir / "learner_difficulty_corrected.csv"
            product_json = temp_dir / "product.json"
            random_json = temp_dir / "random.json"

            write_csv(
                csv_in,
                [
                    {
                        "rank": "10",
                        "lemma": "明日",
                        "reading": "あした",
                        "score": "0.106",
                        "exact_commonness": "0.010",
                        "same_surface_risk": "0.90",
                        "review_flags": "early_same_surface_risk",
                    },
                    {
                        "rank": "20",
                        "lemma": "つく",
                        "reading": "つく",
                        "score": "0.030",
                        "candidate_state": "suppressed_default",
                        "correction_types": "exclude_standalone_srs",
                        "admission_override": "exclude_standalone_srs",
                        "manual_correction_active": "1",
                    },
                    {
                        "rank": "30",
                        "lemma": "猶",
                        "reading": "なお",
                        "score": "0.190",
                        "correction_status": "watch",
                    },
                    {
                        "rank": "40",
                        "lemma": "形",
                        "reading": "かた",
                        "score": "0.480",
                        "exact_commonness": "0.005",
                        "kanji_surface": "1",
                        "same_surface_risk": "0.95",
                        "kana_preferred": "1",
                    },
                ],
            )
            product_json.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {
                                "name": "neutral_p10",
                                "proficiency": 0.10,
                                "requested_topics": [],
                                "admitted_words": [
                                    {
                                        "lemma": "明日",
                                        "reading": "あした",
                                        "runtime_difficulty_estimate": 0.106,
                                    }
                                ],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            random_json.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {
                                "name": "arts_p10",
                                "proficiency": 0.10,
                                "requested_topics": ["arts_literature_humanities"],
                                "draws": [
                                    {
                                        "admitted_words": [
                                            {
                                                "lemma": "明日",
                                                "reading": "あした",
                                                "difficulty_for_summary": 0.106,
                                                "is_topic_mover": False,
                                            }
                                        ]
                                    }
                                ],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(
                csv_in=csv_in,
                category_limit=8,
                product_samples_json=product_json,
                random_samples_json=random_json,
            )
            categories = {category["key"]: category for category in report["categories"]}
            tracking = {row["category"]: row for row in report["hypothesis_tracking"]}

            self.assertEqual(report["summary"]["hard_veto_runtime_row_count"], 1)
            self.assertEqual(report["summary"]["product_visible_review_pack_row_count"], 1)
            self.assertEqual(report["summary"]["random_visible_review_pack_row_count"], 1)
            self.assertEqual(report["summary"]["product_exact_visible_review_pack_row_count"], 1)
            self.assertEqual(report["summary"]["random_exact_visible_review_pack_row_count"], 1)
            self.assertEqual(
                categories["active_hard_veto"]["rows"][0]["recommendation"],
                "already_hard_vetoed",
            )
            self.assertEqual(
                categories["unhandled_review_flags"]["rows"][0]["visibility"]["match_mode"],
                "exact_reading",
            )
            self.assertEqual(
                tracking["same_surface_rare_reading"]["candidate_distribution"][
                    "recommendation_counts"
                ],
                {"likely_restrict_or_score_floor": 1},
            )
            self.assertEqual(
                tracking["same_surface_rare_reading"]["candidate_distribution"][
                    "candidate_shape_counts"
                ],
                {"single_kanji": 1},
            )

            markdown = render_markdown(report)
            self.assertIn("## Hypothesis Tracking", markdown)
            self.assertIn("Visible", markdown)
            self.assertIn("already_hard_vetoed", markdown)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


if __name__ == "__main__":
    unittest.main()
