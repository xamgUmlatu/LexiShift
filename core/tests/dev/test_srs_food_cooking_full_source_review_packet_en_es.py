from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_food_cooking_full_source_review_packet_en_es import (  # noqa: E402
    build_review_packet_from_candidates,
    render_markdown,
)


class SrsFoodCookingFullSourceReviewPacketTests(unittest.TestCase):
    def test_full_source_packet_excludes_current_frontier_candidates(self) -> None:
        report = build_review_packet_from_candidates(
            candidate_inventory=[
                _candidate("te", "B", "high", False, "translation", "primary_translation:tea"),
                _candidate("arroz", "C", "medium", True, "sense_categories", "foods"),
                _candidate("queso", "C", "medium", True, "entry_categories", "cheeses"),
                _candidate(
                    "sacar", "D", "review", True, "gloss_or_translation", "food_gloss_pattern"
                ),
            ],
            current_frontier_lemmas={"te"},
            sample_per_cell=4,
            max_rows=8,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "srs_food_cooking_full_source_review_packet_ready")
        self.assertEqual(report["summary"]["source_candidate_count"], 4)
        self.assertEqual(report["summary"]["excluded_current_frontier_candidate_count"], 1)
        self.assertEqual(report["summary"]["expansion_candidate_count"], 3)
        self.assertEqual(report["summary"]["review_queue_count"], 3)
        self.assertNotIn("te", {row["lemma"] for row in report["review_queue"]})
        self.assertEqual(
            {row["manual_review"]["state"] for row in report["review_queue"]},
            {"pending_user_review"},
        )

        markdown = render_markdown(report)
        self.assertIn("Food/Cooking Full-Source Review Packet", markdown)
        self.assertIn("full_local_kaikki_minus_current_frontier", markdown)
        self.assertIn("arroz", markdown)

    def test_full_source_packet_can_include_current_frontier_candidates(self) -> None:
        report = build_review_packet_from_candidates(
            candidate_inventory=[
                _candidate("te", "B", "high", False, "translation", "primary_translation:tea"),
                _candidate("arroz", "C", "medium", True, "sense_categories", "foods"),
            ],
            current_frontier_lemmas={"te"},
            exclude_current_frontier=False,
            sample_per_cell=4,
            max_rows=8,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["summary"]["excluded_current_frontier_candidate_count"], 0)
        self.assertEqual(report["summary"]["expansion_candidate_count"], 2)
        self.assertIn("te", {row["lemma"] for row in report["review_queue"]})

    def test_full_source_packet_applies_review_labels(self) -> None:
        labels = {
            "review_id": "unit_food_full_source_labels",
            "reviewer": "unit",
            "reviewed_at": "2026-05-19",
            "state": "agent_labeled_pending_user_approval",
            "labels": [
                {
                    "review_id": "srs-food-001",
                    "family": "food_cooking",
                    "lemma": "arroz",
                    "decision": "accept_strong_topic",
                    "notes": "Direct staple food.",
                }
            ],
        }

        report = build_review_packet_from_candidates(
            candidate_inventory=[
                _candidate("arroz", "C", "medium", True, "sense_categories", "foods"),
            ],
            current_frontier_lemmas=set(),
            labels_payload=labels,
            sample_per_cell=4,
            max_rows=8,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["summary"]["labeled_row_count"], 1)
        self.assertEqual(
            report["summary"]["manual_decision_counts"]["accept_strong_topic"],
            1,
        )
        self.assertIn("manual_labels_applied", {row["code"] for row in report["findings"]})
        markdown = render_markdown(report)
        self.assertIn("Accepted rows", markdown)
        self.assertIn("Direct staple food.", markdown)


def _candidate(
    lemma: str,
    tier: str,
    band: str,
    review_required: bool,
    source_channel: str,
    source_label: str,
) -> dict[str, object]:
    score = 0.855 if band == "high" else 0.72 if band == "medium" else 0.52
    return {
        "lemma": lemma,
        "confidence": score,
        "confidence_band": band,
        "best_tier": tier,
        "review_required": review_required,
        "evidence": [
            {
                "family": "food_cooking",
                "lemma": lemma,
                "tier": tier,
                "evidence_type": "source_signal",
                "source_channel": source_channel,
                "source_label": source_label,
                "snippet": source_label,
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
