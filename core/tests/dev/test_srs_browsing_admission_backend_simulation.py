from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_browsing_admission_backend_simulation import build_report  # noqa: E402


class TestSrsBrowsingAdmissionBackendSimulation(unittest.TestCase):
    def test_en_ja_fixture_is_pair_driven_and_privacy_safe(self) -> None:
        report = build_report(pair="en-ja", admission_budget=6)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["language_pair"], "en-ja")
        self.assertFalse(report["privacy"]["raw_text_stored"])
        self.assertFalse(report["privacy"]["url_stored"])
        self.assertFalse(report["privacy"]["runtime_srs_mutation"])
        self.assertIn("料理", report["fixture"]["signal_lemmas"])

        aggregate = report["aggregate_store"]
        aggregate_lemmas = {row["target_lemma"] for row in aggregate["items"]}
        self.assertIn("料理", aggregate_lemmas)

        simulations = report["simulations"]
        self.assertEqual(
            simulations["off"]["selected_lemmas"],
            simulations["off"]["neutral_selected_lemmas"],
        )
        self.assertLessEqual(
            simulations["off"]["browsing_lane_share"],
            simulations["balanced"]["browsing_lane_share"],
        )
        self.assertLessEqual(
            simulations["balanced"]["browsing_lane_share"],
            simulations["strong"]["browsing_lane_share"],
        )
        rows_by_lemma = {row["lemma"]: row for row in simulations["strong"]["rows"]}
        self.assertEqual(rows_by_lemma["旅行"]["suppressed_reason"], "suspended")
        self.assertFalse(rows_by_lemma["旅行"]["selected"])

    def test_en_es_fixture_remains_available_for_old_research_comparison(self) -> None:
        report = build_report(pair="en-es", admission_budget=6)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["language_pair"], "en-es")
        self.assertIn("hipoteca", report["fixture"]["signal_lemmas"])
        self.assertIn("viaje", report["fixture"]["candidate_lemmas"])


if __name__ == "__main__":
    unittest.main()
