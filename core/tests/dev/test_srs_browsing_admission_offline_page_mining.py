from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_browsing_admission_offline_page_mining import build_report  # noqa: E402


class TestSrsBrowsingAdmissionOfflinePageMining(unittest.TestCase):
    def test_saved_pages_mine_and_ingest_expected_signals(self) -> None:
        report = build_report(generated_at="2026-07-03T00:00:00Z")

        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["live_user_data_touched"])
        self.assertEqual(report["case_count"], 2)

        cases = {case["name"]: case for case in report["cases"]}
        case = cases["en-ja_source_and_ruby_saved_pages_v1"]
        self.assertEqual(case["name"], "en-ja_source_and_ruby_saved_pages_v1")
        self.assertEqual(case["status"], "PASS")
        self.assertTrue(all(check["status"] == "pass" for check in case["checks"]))

        extension = case["extension_payload"]
        self.assertGreaterEqual(extension["packet_count"], 1)
        self.assertGreaterEqual(extension["source_signal_count"], 3)
        self.assertGreaterEqual(extension["target_signal_count"], 2)
        self.assertIn("発酵|はっこう", extension["target_keys"])
        self.assertIn("血圧|けつあつ", extension["target_keys"])
        self.assertIn("麹|こうじ", extension["target_keys"])
        self.assertNotIn("光|ひかり", extension["target_keys"])
        self.assertNotIn("軽い|かるい", extension["target_keys"])
        self.assertNotIn("仕事|しごと", extension["target_keys"])

        rows = {row["target_key"]: row for row in case["aggregate_store"]["items"]}
        self.assertGreaterEqual(rows["発酵|はっこう"]["source_hit_count"], 2.3)
        self.assertGreaterEqual(rows["発酵|はっこう"]["target_hit_count"], 2.0)
        self.assertGreaterEqual(rows["発酵|はっこう"]["browsing_context_count"], 3)
        self.assertIn("source_mapping", rows["発酵|はっこう"]["observation_sources"])
        self.assertIn("target_surface", rows["発酵|はっこう"]["observation_sources"])
        self.assertGreaterEqual(rows["血圧|けつあつ"]["source_hit_count"], 0.7)

        strong_rows = {
            row["target_key"]: row for row in case["admission_simulations"]["strong"]["rows"]
        }
        self.assertTrue(strong_rows["発酵|はっこう"]["selected"])
        self.assertEqual(strong_rows["発酵|はっこう"]["selected_lane"], "browsing")
        self.assertGreaterEqual(strong_rows["発酵|はっこう"]["effective_browsing_signal"], 0.25)

        unsupported = cases["en-es_source_saved_page_currently_unsupported_v1"]
        self.assertEqual(unsupported["status"], "PASS")
        self.assertEqual(unsupported["extension_payload"]["packet_count"], 0)
        self.assertEqual(unsupported["extension_payload"]["signal_count"], 0)
        self.assertEqual(unsupported["native_host_ingest"]["response_count"], 0)
        self.assertEqual(unsupported["aggregate_store"]["item_count"], 0)

        report_text = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("Fermentation changes sugars", report_text)
        self.assertNotIn("window.hiddenTopic", report_text)
        self.assertNotIn("offline-source-a", report_text)


if __name__ == "__main__":
    unittest.main()
