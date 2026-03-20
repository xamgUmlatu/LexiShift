from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_journey_harness import build_report  # noqa: E402


class TestSrsJourneyHarness(unittest.TestCase):
    def test_build_report_surfaces_deterministic_growth_pause_and_publication_warning(self) -> None:
        report = build_report()
        summary = report["summary"]
        findings = report["findings"]
        phases = report["phases"]

        self.assertEqual(summary["status"], "WARN")
        self.assertEqual(report["scenario"]["name"], "en-ja_core_journey_v1")
        self.assertEqual(len(phases), 6)
        self.assertEqual(phases[0]["counts"]["admitted"], 3)
        self.assertEqual(phases[2]["counts"]["admitted"], 5)
        self.assertEqual(phases[3]["counts"]["admitted"], 5)
        self.assertEqual(phases[4]["counts"]["admitted"], 7)
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_HIGH_RETENTION_ADMITS" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_LOW_RETENTION_PAUSES" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_RECOVERY_RESUMES" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED" for item in findings)
        )

        fade_phase = phases[-1]
        stable_due = [
            item["lemma"]
            for item in fade_phase["items"]
            if item["cohort"] == "stable" and item["in_due"]
        ]
        difficult_due = [
            item["lemma"]
            for item in fade_phase["items"]
            if item["cohort"] == "difficult" and item["in_due"]
        ]
        self.assertEqual(stable_due, [])
        self.assertEqual(difficult_due, ["gamma"])


if __name__ == "__main__":
    unittest.main()
