from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_admission_preference_sanity import build_report  # noqa: E402


class TestSrsAdmissionPreferenceSanity(unittest.TestCase):
    def test_build_report_surfaces_interest_and_implicit_lifts_without_failures(self) -> None:
        report = build_report(preview_limit=5)
        summary = report["summary"]
        self.assertEqual(summary["fail_count"], 0)
        self.assertEqual(summary["warn_count"], 0)

        scenarios = {scenario["name"]: scenario for scenario in report["scenarios"]}
        self.assertEqual(
            scenarios["neutral"]["top_lemmas"][:3],
            ["money", "home", "case"],
        )
        self.assertIn("dog", scenarios["explicit_animals"]["top_lemmas"][:3])
        self.assertIn("elephant", scenarios["explicit_animals"]["top_lemmas"][:3])
        self.assertEqual(
            scenarios["explicit_animals"]["profile_context"]["signal_sources"]["interests"],
            "interests",
        )
        self.assertEqual(
            scenarios["implicit_streaming_comedy"]["profile_context"]["signal_sources"][
                "interests"
            ],
            "empirical_trends.topic_bias",
        )
        self.assertGreater(
            report["comparisons"]["explicit_animals_vs_neutral"]["average_rank_gain"],
            0.0,
        )
        self.assertGreater(
            report["comparisons"]["implicit_streaming_comedy_vs_neutral"]["average_rank_gain"],
            0.0,
        )
        findings = {finding["code"]: finding for finding in report["findings"]}
        self.assertIn("LIVE_METADATA_COVERAGE_AUDIT_AVAILABLE", findings)


if __name__ == "__main__":
    unittest.main()
