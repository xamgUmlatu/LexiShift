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

from srs_animals_plants_topic_overlay_poc_en_es import (  # noqa: E402
    build_report,
    build_topic_overlay,
    render_markdown,
)


class SrsAnimalsPlantsTopicOverlayPocTests(unittest.TestCase):
    def test_overlay_builds_only_accepted_review_rows(self) -> None:
        overlay = build_topic_overlay(
            review_packet_payload=_review_packet_payload(),
            generated_at="2026-05-17T00:00:00+00:00",
        )

        self.assertEqual(overlay["status"], "ok")
        self.assertEqual(overlay["summary"]["row_count"], 2)
        self.assertEqual(
            overlay["summary"]["counts_by_topic"],
            {"animals": 1, "plants_nature": 1},
        )
        memberships = {row["lemma"]: row["membership"] for row in overlay["rows"]}
        self.assertEqual(memberships["perro"], 1.0)
        self.assertEqual(memberships["flor"], 0.65)
        self.assertNotIn("tipo", memberships)

    def test_poc_injects_overlay_into_profile_bootstrap_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "frequency.sqlite"
            _write_frequency_db(db_path)

            report = build_report(
                review_packet_payload=_review_packet_payload(),
                frequency_db=db_path,
                top_n=4,
                profile_top_n=3,
                generated_at="2026-05-17T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        scenario_by_interest = {row["interest"]: row for row in report["profile_scenarios"]}
        animals = scenario_by_interest["animals"]
        self.assertEqual(animals["baseline"]["overlay_topic_rows_in_top_n"], 0)
        self.assertGreaterEqual(animals["with_overlay"]["overlay_topic_rows_in_top_n"], 1)
        self.assertGreaterEqual(animals["delta"]["overlay_topic_rows_in_top_n"], 1)

        markdown = render_markdown(report)
        self.assertIn("Animals/Plants Topic Overlay PoC", markdown)
        self.assertIn("perro", markdown)


def _review_packet_payload() -> dict[str, object]:
    return {
        "decision": "srs_animals_plants_signal_review_packet_ready",
        "review_queue": [
            _review_row(
                review_id="srs-anpl-001",
                family="animals",
                lemma="perro",
                decision="accept_strong_topic",
            ),
            _review_row(
                review_id="srs-anpl-002",
                family="plants_nature",
                lemma="flor",
                decision="accept_light_topic",
            ),
            _review_row(
                review_id="srs-anpl-003",
                family="plants_nature",
                lemma="tipo",
                decision="reject_secondary_or_obscure_sense",
            ),
        ],
    }


def _review_row(
    *,
    review_id: str,
    family: str,
    lemma: str,
    decision: str,
) -> dict[str, object]:
    return {
        "review_id": review_id,
        "family": family,
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
                (2, 96.0, "perro", "n"),
                (3, 94.0, "mesa", "n"),
                (4, 92.0, "flor", "n"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
