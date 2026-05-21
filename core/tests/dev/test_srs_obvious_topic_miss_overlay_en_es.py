from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_obvious_topic_miss_overlay_en_es import build_overlay  # noqa: E402


class TestSrsObviousTopicMissOverlayEnEs(unittest.TestCase):
    def test_build_overlay_skips_existing_and_flags_missing_bridge_targets(self) -> None:
        report = build_overlay(
            review_payload={
                "labels": [
                    {
                        "review_id": "unit-keep",
                        "topic": "games",
                        "lemma": "jugar",
                        "decision": "accept_strong_topic",
                        "bridge_source": "play",
                    },
                    {
                        "review_id": "unit-skip",
                        "topic": "games",
                        "lemma": "juego",
                        "decision": "accept_strong_topic",
                    },
                    {
                        "review_id": "unit-missing",
                        "topic": "games",
                        "lemma": "missing",
                        "decision": "accept_strong_topic",
                    },
                    {
                        "review_id": "unit-missing-requested-source",
                        "topic": "sports_fitness",
                        "lemma": "jugar",
                        "decision": "accept_strong_topic",
                        "bridge_source": "throw",
                    },
                ]
            },
            zipf_bridge_payload={
                "full_source_target_pairs": [
                    {
                        "source": "play",
                        "source_zipf_frequency_en": 5.61,
                        "target": "jugar",
                        "target_zipf_band_es": "zipf_5_plus_very_common",
                        "target_zipf_frequency_es": 5.05,
                    },
                    {
                        "source": "game",
                        "source_zipf_frequency_en": 5.48,
                        "target": "juego",
                        "target_zipf_band_es": "zipf_5_plus_very_common",
                        "target_zipf_frequency_es": 5.38,
                    },
                ]
            },
            existing_overlay_payloads=[
                {
                    "status": "ok",
                    "rows": [{"language_pair": "en-es", "lemma": "juego", "topic": "games"}],
                }
            ],
            generated_at="2026-05-21T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["row_count"], 1)
        self.assertEqual(report["summary"]["skipped_existing_count"], 1)
        self.assertEqual(report["summary"]["skipped_missing_count"], 2)
        self.assertEqual(report["rows"][0]["lemma"], "jugar")
        self.assertEqual(report["rows"][0]["topic"], "games")
        self.assertEqual(report["rows"][0]["membership"], 1.0)


if __name__ == "__main__":
    unittest.main()
