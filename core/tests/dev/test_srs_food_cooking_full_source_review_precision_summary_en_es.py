from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_food_cooking_full_source_review_precision_summary_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsFoodCookingFullSourceReviewPrecisionSummaryTests(unittest.TestCase):
    def test_summary_counts_accepts_rejects_and_policy_guidance(self) -> None:
        report = build_report(
            packet_payload=_packet_payload(),
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["count"], 4)
        self.assertEqual(report["summary"]["accepted_count"], 2)
        self.assertEqual(report["summary"]["rejected_count"], 2)
        self.assertEqual(report["summary"]["wrong_topic_count"], 1)
        self.assertEqual(report["summary"]["secondary_or_obscure_count"], 1)
        self.assertIn("policy_guards_still_needed", {row["code"] for row in report["findings"]})
        self.assertTrue(report["flow_assessment"]["doing_the_right_thing"])

        tier_rows = {row["label"]: row for row in report["precision_by_tier"]}
        self.assertEqual(tier_rows["B"]["rejected_count"], 2)
        self.assertEqual(tier_rows["C"]["accepted_count"], 2)
        self.assertTrue(any("fruit-word translation" in item for item in report["policy_guidance"]))

        markdown = render_markdown(report)
        self.assertIn("Food/Cooking Full-Source Review Precision Summary", markdown)
        self.assertIn("Rejected Rows", markdown)
        self.assertIn("anaranjado", markdown)

    def test_summary_fails_when_rows_are_unlabeled(self) -> None:
        payload = _packet_payload()
        payload["review_queue"][0]["manual_review"]["decision"] = ""

        report = build_report(
            packet_payload=payload,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("review_rows_unlabeled", report["summary"]["issues"])


def _packet_payload() -> dict[str, object]:
    return {
        "decision": "srs_food_cooking_full_source_review_packet_ready",
        "label_result": {
            "labels_json": "docs/test_inputs/unit.json",
            "labels_state": "agent_labeled_pending_user_approval",
            "missing_review_ids": [],
            "unknown_review_ids": [],
        },
        "review_queue": [
            _row("srs-food-001", "arroz", "C", "medium", "foods", "accept_strong_topic"),
            _row("srs-food-002", "cola", "C", "review", "beverages", "accept_light_topic"),
            _row(
                "srs-food-003",
                "anaranjado",
                "B",
                "review",
                "primary_translation:orange",
                "reject_wrong_topic",
            ),
            _row(
                "srs-food-004",
                "cha",
                "B",
                "high",
                "primary_translation:tea",
                "reject_secondary_or_obscure_sense",
            ),
        ],
    }


def _row(
    review_id: str,
    lemma: str,
    tier: str,
    band: str,
    source_label: str,
    decision: str,
) -> dict[str, object]:
    return {
        "review_id": review_id,
        "lemma": lemma,
        "best_tier": tier,
        "confidence_band": band,
        "source_channel": "translation" if source_label.startswith("primary_") else "category",
        "source_label": source_label,
        "manual_review": {
            "decision": decision,
            "notes": f"Reviewed {lemma}.",
        },
    }


if __name__ == "__main__":
    unittest.main()
