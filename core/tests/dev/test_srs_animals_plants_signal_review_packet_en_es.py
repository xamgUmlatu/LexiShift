from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_animals_plants_signal_review_packet_en_es import (  # noqa: E402
    build_review_packet,
    render_markdown,
)


class SrsAnimalsPlantsSignalReviewPacketTests(unittest.TestCase):
    def test_review_packet_samples_cells_and_keeps_labels_pending(self) -> None:
        report = build_review_packet(
            audit_payload=_sample_audit_payload(),
            sample_per_cell=1,
            max_rows=5,
            generated_at="2026-05-17T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["candidate_count"], 5)
        self.assertEqual(report["summary"]["review_queue_count"], 5)
        self.assertTrue(report["summary"]["full_candidate_inventory_used"])
        queue = report["review_queue"]
        self.assertEqual(len({row["review_id"] for row in queue}), 5)
        self.assertEqual(
            {row["manual_review"]["state"] for row in queue},
            {"pending_user_review"},
        )
        self.assertLessEqual(
            {"animals", "plants_nature"},
            {row["family"] for row in queue},
        )
        self.assertTrue(all("source=" in row["review_cell"] for row in queue))

        markdown = render_markdown(report)
        self.assertIn("Manual Review Queue", markdown)
        self.assertIn("accept_strong_topic", markdown)
        self.assertIn("srs-anpl-001", markdown)


def _sample_audit_payload() -> dict[str, object]:
    return {
        "decision": "animals_plants_existing_signal_audit_completed",
        "generated_at": "2026-05-17T00:00:00+00:00",
        "families": [
            {
                "family": "animals",
                "candidate_inventory": [
                    _candidate("animals", "perro", "B", "high", False, "primary_translation:dog"),
                    _candidate("animals", "broma", "B", "review", True, "primary_translation:dog"),
                    _candidate("animals", "pez", "C", "medium", False, "fish"),
                ],
            },
            {
                "family": "plants_nature",
                "candidate_inventory": [
                    _candidate(
                        "plants_nature",
                        "flor",
                        "B",
                        "high",
                        False,
                        "primary_translation:flower",
                    ),
                    _candidate("plants_nature", "espiga", "C", "medium", False, "grains"),
                ],
            },
        ],
    }


def _candidate(
    family: str,
    lemma: str,
    tier: str,
    band: str,
    review_required: bool,
    source_label: str,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "confidence": 0.855 if band == "high" else 0.76 if band == "medium" else 0.59,
        "confidence_band": band,
        "best_tier": tier,
        "review_required": review_required,
        "evidence": [
            {
                "family": family,
                "lemma": lemma,
                "tier": tier,
                "evidence_type": "primary_exact_translation",
                "source_channel": "translation",
                "source_label": source_label,
                "snippet": source_label.split(":", 1)[-1],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
