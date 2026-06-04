from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_food_cooking_signal_review_packet_en_es import (  # noqa: E402
    build_review_packet,
    render_markdown,
)


class SrsFoodCookingSignalReviewPacketTests(unittest.TestCase):
    def test_review_packet_includes_full_small_food_candidate_universe(self) -> None:
        report = build_review_packet(
            audit_payload=_sample_audit_payload(),
            max_rows=8,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["candidate_count"], 4)
        self.assertEqual(report["summary"]["review_queue_count"], 4)
        self.assertTrue(report["summary"]["full_candidate_inventory_used"])
        self.assertIn(
            "full_candidate_universe_selected",
            {row["code"] for row in report["findings"]},
        )
        self.assertEqual(
            {row["manual_review"]["state"] for row in report["review_queue"]},
            {"pending_user_review"},
        )
        self.assertTrue(
            all(str(row["review_id"]).startswith("srs-food-") for row in report["review_queue"])
        )

        markdown = render_markdown(report)
        self.assertIn("Food/Cooking Signal Review Packet", markdown)
        self.assertIn("srs-food-001", markdown)
        self.assertIn("accept_strong_topic", markdown)

    def test_review_packet_applies_complete_labels(self) -> None:
        pending = build_review_packet(
            audit_payload=_sample_audit_payload(),
            max_rows=8,
            generated_at="2026-05-19T00:00:00+00:00",
        )
        labels = [
            {
                "review_id": row["review_id"],
                "family": row["family"],
                "lemma": row["lemma"],
                "decision": "accept_light_topic",
                "notes": f"Reviewed {row['lemma']}.",
            }
            for row in pending["review_queue"]
        ]

        report = build_review_packet(
            audit_payload=_sample_audit_payload(),
            labels_payload={
                "review_id": "sample_food_labels",
                "reviewer": "codex_agent",
                "reviewed_at": "2026-05-19",
                "state": "agent_labeled_pending_user_approval",
                "labels": labels,
            },
            max_rows=8,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["labeled_row_count"], 4)
        self.assertEqual(
            report["summary"]["manual_decision_counts"]["accept_light_topic"],
            4,
        )
        self.assertIn("manual_labels_applied", {row["code"] for row in report["findings"]})
        self.assertEqual(
            {row["manual_review"]["state"] for row in report["review_queue"]},
            {"agent_labeled_pending_user_approval"},
        )
        self.assertIn("Reviewed", render_markdown(report))


def _sample_audit_payload() -> dict[str, object]:
    return {
        "decision": "food_cooking_existing_signal_audit_completed",
        "generated_at": "2026-05-19T00:00:00+00:00",
        "family": {
            "family": "food_cooking",
            "candidate_inventory": [
                _candidate("té", "B", "high", False, "translation", "primary_translation:tea"),
                _candidate("caldo", "C", "medium", True, "entry_categories", "soups"),
                _candidate(
                    "dulce", "D", "inventory", True, "gloss_or_translation", "food_gloss_pattern"
                ),
                _candidate("careta", "A", "medium", False, "sense_topics", "cooking"),
            ],
        },
    }


def _candidate(
    lemma: str,
    tier: str,
    band: str,
    review_required: bool,
    source_channel: str,
    source_label: str,
) -> dict[str, object]:
    score = 0.855 if band == "high" else 0.72 if band == "medium" else 0.36
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
