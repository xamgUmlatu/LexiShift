from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_food_cooking_topic_overlay_poc_en_es import (  # noqa: E402
    build_report,
    build_topic_overlay,
    render_markdown,
)


class SrsFoodCookingTopicOverlayPocTests(unittest.TestCase):
    def test_overlay_builds_only_accepted_review_rows(self) -> None:
        overlay = build_topic_overlay(
            review_packet_payload=_review_packet_payload(),
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(overlay["status"], "ok")
        self.assertEqual(overlay["summary"]["row_count"], 2)
        self.assertEqual(overlay["summary"]["counts_by_topic"], {"food_cooking": 2})
        self.assertEqual(
            overlay["overlay_policy"]["rejected_decisions_excluded"],
            {
                "reject_secondary_or_obscure_sense": 1,
                "reject_wrong_topic": 1,
            },
        )
        memberships = {row["lemma"]: row["membership"] for row in overlay["rows"]}
        self.assertEqual(memberships["te"], 1.0)
        self.assertEqual(memberships["panadero"], 0.65)
        self.assertNotIn("sacar", memberships)
        self.assertNotIn("mariposa", memberships)

    def test_poc_injects_strong_overlay_into_profile_bootstrap_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "frequency.sqlite"
            _write_frequency_db(db_path)

            report = build_report(
                review_packet_payload=_review_packet_payload(),
                frequency_db=db_path,
                top_n=4,
                profile_top_n=3,
                generated_at="2026-05-19T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["overlay_row_count"], 2)
        self.assertEqual(report["profile_scenario"]["baseline"]["overlay_topic_rows_in_top_n"], 0)
        self.assertGreaterEqual(
            report["profile_scenario"]["with_overlay"]["overlay_topic_rows_in_top_n"],
            1,
        )
        self.assertGreaterEqual(
            report["profile_scenario"]["delta"]["overlay_topic_rows_in_top_n"],
            1,
        )

        markdown = render_markdown(report)
        self.assertIn("Food/Cooking Topic Overlay PoC", markdown)
        self.assertIn("te", markdown)


def _review_packet_payload() -> dict[str, object]:
    return {
        "decision": "srs_food_cooking_signal_review_packet_ready",
        "review_queue": [
            _review_row(
                review_id="srs-food-001",
                lemma="te",
                decision="accept_strong_topic",
            ),
            _review_row(
                review_id="srs-food-002",
                lemma="panadero",
                decision="accept_light_topic",
            ),
            _review_row(
                review_id="srs-food-003",
                lemma="sacar",
                decision="reject_secondary_or_obscure_sense",
            ),
            _review_row(
                review_id="srs-food-004",
                lemma="mariposa",
                decision="reject_wrong_topic",
            ),
        ],
    }


def _review_row(
    *,
    review_id: str,
    lemma: str,
    decision: str,
) -> dict[str, object]:
    return {
        "review_id": review_id,
        "family": "food_cooking",
        "lemma": lemma,
        "confidence": 0.82,
        "confidence_band": "high",
        "best_tier": "B",
        "source_channel": "translation",
        "source_label": "unit",
        "manual_review": {
            "state": "agent_labeled_pending_user_approval",
            "decision": decision,
            "reviewer": "unit",
            "label_source": "unit.json",
            "notes": "unit",
        },
    }


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma, pos) VALUES (?, ?, ?, ?)",
            [
                (1, 100.0, "casa", "n"),
                (2, 96.0, "te", "n"),
                (3, 94.0, "mesa", "n"),
                (4, 92.0, "panadero", "n"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
