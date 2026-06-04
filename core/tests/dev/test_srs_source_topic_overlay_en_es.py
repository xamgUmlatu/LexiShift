from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_source_topic_overlay_en_es import build_topic_overlay, render_markdown  # noqa: E402


class SrsSourceTopicOverlayEnEsTests(unittest.TestCase):
    def test_build_topic_overlay_uses_source_ready_mappings_and_exclusions(self) -> None:
        overlay = build_topic_overlay(
            taxonomy_payload=_taxonomy_payload(),
            source_labels_by_lemma={
                "controlador": ["computing"],
                "desarrollar": ["engineering"],
                "poner": ["computing"],
                "perro": ["animals"],
            },
            seed_infos=[
                _seed_info("controlador", 10, 0.32),
                _seed_info("desarrollar", 20, 0.48),
                _seed_info("poner", 30, 0.22),
                _seed_info("perro", 40, 0.12),
            ],
            precision_review_payload={
                "summary": {
                    "count": 8,
                    "accepted_count": 7,
                    "accepted_rate": 0.875,
                    "rejected_count": 1,
                    "rejected_rate": 0.125,
                },
                "precision_by_family": [
                    {
                        "label": "science_technology",
                        "count": 8,
                        "accepted_count": 7,
                        "pending_count": 0,
                        "rejected_rate": 0.125,
                    }
                ],
            },
            generated_at="2026-05-20T00:00:00+00:00",
        )

        self.assertEqual(overlay["status"], "ok")
        self.assertEqual(overlay["summary"]["counts_by_topic"], {"science_technology": 2})
        self.assertEqual(overlay["summary"]["counts_by_confidence"], {"light": 1, "strong": 1})
        self.assertEqual(overlay["overlay_policy"]["excluded_candidate_count"], 1)

        rows_by_lemma = {row["lemma"]: row for row in overlay["rows"]}
        self.assertEqual(rows_by_lemma["controlador"]["membership"], 1.0)
        self.assertEqual(rows_by_lemma["desarrollar"]["membership"], 0.65)
        self.assertNotIn("poner", rows_by_lemma)
        self.assertNotIn("perro", rows_by_lemma)
        self.assertEqual(
            overlay["precision_review_summary"],
            {
                "exists": True,
                "reviewed_count": 8,
                "accepted_count": 7,
                "accepted_rate": 0.875,
                "rejected_count": 1,
                "rejected_rate": 0.125,
                "pending_count": 0,
            },
        )

        markdown = render_markdown(overlay)
        self.assertIn("Source Topic Overlay", markdown)
        self.assertIn("science_technology", markdown)

    def test_missing_precision_review_blocks_overlay_rows(self) -> None:
        overlay = build_topic_overlay(
            taxonomy_payload=_taxonomy_payload(),
            source_labels_by_lemma={"controlador": ["computing"]},
            seed_infos=[_seed_info("controlador", 10, 0.32)],
            precision_review_payload=None,
            generated_at="2026-05-20T00:00:00+00:00",
        )

        self.assertEqual(overlay["status"], "review")
        self.assertEqual(overlay["summary"]["row_count"], 0)
        self.assertEqual(overlay["overlay_policy"]["precision_family_filter"], [])
        self.assertEqual(overlay["precision_review_summary"], {"exists": False})

    def test_pending_precision_family_does_not_promote_to_overlay(self) -> None:
        overlay = build_topic_overlay(
            taxonomy_payload=_taxonomy_payload(),
            source_labels_by_lemma={"controlador": ["computing"]},
            seed_infos=[_seed_info("controlador", 10, 0.32)],
            precision_review_payload={
                "summary": {
                    "count": 2,
                    "accepted_count": 1,
                    "accepted_rate": 0.5,
                    "rejected_count": 0,
                    "rejected_rate": 0.0,
                    "pending_count": 1,
                },
                "precision_by_family": [
                    {
                        "label": "science_technology",
                        "count": 2,
                        "accepted_count": 1,
                        "pending_count": 1,
                        "rejected_rate": 0.0,
                    }
                ],
            },
            generated_at="2026-05-20T00:00:00+00:00",
        )

        self.assertEqual(overlay["status"], "review")
        self.assertEqual(overlay["summary"]["row_count"], 0)
        self.assertEqual(overlay["overlay_policy"]["precision_family_filter"], [])


def _taxonomy_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "families": [
            {
                "id": "science_technology",
                "axis": "topic",
                "readiness_state": "source_ready",
            },
            {
                "id": "animals",
                "axis": "topic",
                "readiness_state": "p0_enrichment",
            },
        ],
        "source_label_mappings": [
            {
                "source_channel": "sense_topics",
                "source_label": "computing",
                "target_family": "science_technology",
                "weight": 0.9,
                "confidence": 0.9,
            },
            {
                "source_channel": "sense_topics",
                "source_label": "engineering",
                "target_family": "science_technology",
                "weight": 0.7,
                "confidence": 0.8,
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
                "target_family": "science_technology",
                "source_labels": ["computing"],
                "lemmas": ["poner"],
                "reason": "unit-test source-topic false positive",
            }
        ],
    }


def _seed_info(lemma: str, rank: int, difficulty: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "seed_rank": rank,
        "difficulty": difficulty,
        "admission_weight": round(1.0 - difficulty, 6),
        "pos_bucket": "noun",
    }


if __name__ == "__main__":
    unittest.main()
