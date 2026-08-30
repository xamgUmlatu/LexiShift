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

from srs_jmdict_topic_overlay_poc_en_ja import (  # noqa: E402
    build_report,
    build_topic_overlay,
    render_markdown,
)


class SrsJmdictTopicOverlayPocEnJaTests(unittest.TestCase):
    def test_overlay_builds_only_accepted_review_rows(self) -> None:
        overlay = build_topic_overlay(
            review_packet_payload=_review_packet_payload(),
            generated_at="2026-06-10T00:00:00+00:00",
        )

        self.assertEqual(overlay["status"], "ok")
        self.assertEqual(overlay["summary"]["row_count"], 2)
        self.assertEqual(
            overlay["summary"]["counts_by_topic"],
            {"finance_business": 1, "medicine_health": 1},
        )
        self.assertEqual(
            overlay["overlay_policy"]["rejected_decisions_excluded"],
            {
                "reject_secondary_or_obscure_sense": 1,
                "reject_wrong_topic": 1,
            },
        )
        memberships = {row["lemma"]: row["membership"] for row in overlay["rows"]}
        self.assertEqual(memberships["脳"], 1.0)
        self.assertEqual(memberships["展開"], 0.65)
        self.assertNotIn("プロ", memberships)
        self.assertNotIn("回答", memberships)

    def test_poc_injects_strong_overlay_into_profile_bootstrap_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "frequency.sqlite"
            jmdict_path = root / "JMdict_e"
            _write_frequency_db(db_path)
            _write_jmdict(jmdict_path)

            report = build_report(
                review_packet_payload=_review_packet_payload(),
                frequency_db=db_path,
                jmdict_path=jmdict_path,
                top_n=4,
                profile_top_n=3,
                generated_at="2026-06-10T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["overlay_row_count"], 2)
        scenarios = {row["interest"]: row for row in report["profile_scenarios"]}
        medicine = scenarios["medicine_health"]
        self.assertEqual(medicine["baseline"]["overlay_topic_rows_in_top_n"], 0)
        self.assertGreaterEqual(
            medicine["with_overlay"]["overlay_topic_rows_in_top_n"],
            1,
        )
        self.assertGreaterEqual(
            medicine["delta"]["overlay_topic_rows_in_top_n"],
            1,
        )

        markdown = render_markdown(report)
        self.assertIn("JMDict Topic Overlay PoC", markdown)
        self.assertIn("脳", markdown)


def _review_packet_payload() -> dict[str, object]:
    return {
        "decision": "srs_jmdict_topic_review_packet_ready",
        "review_queue": [
            _review_row(
                review_id="srs-enja-topic-001",
                family_id="medicine_health",
                lemma="脳",
                decision="accept_strong_topic",
            ),
            _review_row(
                review_id="srs-enja-topic-002",
                family_id="finance_business",
                lemma="展開",
                decision="accept_light_topic",
            ),
            _review_row(
                review_id="srs-enja-topic-003",
                family_id="medicine_health",
                lemma="プロ",
                decision="reject_wrong_topic",
            ),
            _review_row(
                review_id="srs-enja-topic-004",
                family_id="medicine_health",
                lemma="回答",
                decision="reject_secondary_or_obscure_sense",
            ),
        ],
    }


def _review_row(
    *,
    review_id: str,
    family_id: str,
    lemma: str,
    decision: str,
) -> dict[str, object]:
    return {
        "review_id": review_id,
        "family_id": family_id,
        "lemma": lemma,
        "match_strength": "strong",
        "pos": "名詞",
        "pos_bucket": "noun",
        "primary_source_label": "unit",
        "source_labels": ["unit"],
        "jmdict_match_modes": ["exact"],
        "jmdict_matched_terms": [lemma],
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
        conn.execute("CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT, lform TEXT, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma, lform, pos) VALUES (?, ?, ?, ?, ?)",
            [
                (1, 100.0, "事", "コト", "名詞"),
                (2, 98.0, "展開", "テンカイ", "名詞"),
                (3, 96.0, "脳", "ノウ", "名詞"),
                (4, 94.0, "プロ", "プロ", "名詞"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_jmdict(path: Path) -> None:
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry><k_ele><keb>事</keb></k_ele><r_ele><reb>こと</reb></r_ele></entry>
  <entry><k_ele><keb>展開</keb></k_ele><r_ele><reb>てんかい</reb></r_ele></entry>
  <entry><k_ele><keb>脳</keb></k_ele><r_ele><reb>のう</reb></r_ele></entry>
  <entry><k_ele><keb>プロ</keb></k_ele><r_ele><reb>ぷろ</reb></r_ele></entry>
</JMdict>
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
