from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_browsing_admission_runtime_smoke import build_report  # noqa: E402


class TestSrsBrowsingAdmissionRuntimeSmoke(unittest.TestCase):
    def test_extension_native_host_helper_admission_smoke_passes(self) -> None:
        report = build_report(pair="en-ja", admission_budget=4)

        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["live_user_data_touched"])
        self.assertTrue(all(check["status"] == "pass" for check in report["checks"]))
        self.assertEqual(report["native_host_ingest"]["statuses"], ["ok"])
        self.assertEqual(report["native_host_ingest"]["runtime_srs_mutation_values"], [False])

        extension = report["extension_payload"]
        self.assertTrue(extension["private_strings_absent"])
        self.assertIn("ctxh", extension["context_key_prefixes"])
        self.assertIn("pageh", extension["context_key_prefixes"])

        before_rows = {
            row["target_key"]: row for row in report["aggregate_store_before_maintenance"]["items"]
        }
        self.assertGreaterEqual(before_rows["料理"]["browsing_context_count"], 2)
        self.assertEqual(before_rows["会社"]["browsing_context_count"], 1)

        strong_rows = {row["target_key"]: row for row in report["simulations"]["strong"]["rows"]}
        self.assertEqual(strong_rows["料理"]["selected_lane"], "browsing")
        self.assertTrue(strong_rows["料理"]["selected"])
        self.assertEqual(strong_rows["会社"]["browsing_count_multiplier"], 0.0)
        self.assertFalse(strong_rows["会社"]["selected"])

        maintenance = report["maintenance"]
        self.assertEqual(maintenance["response_status"], "skipped")
        self.assertFalse(maintenance["runtime_srs_mutation"])
        after_rows = {
            row["target_key"]: row for row in maintenance["aggregate_store_after"]["items"]
        }
        self.assertLess(
            after_rows["料理"]["replacement_exposure_count"],
            before_rows["料理"]["replacement_exposure_count"],
        )

    def test_english_source_lp_runtime_smokes_pass(self) -> None:
        for pair in ("en-es", "en-de"):
            with self.subTest(pair=pair):
                report = build_report(pair=pair, admission_budget=4)

                self.assertEqual(report["status"], "PASS")
                self.assertFalse(report["live_user_data_touched"])
                self.assertTrue(all(check["status"] == "pass" for check in report["checks"]))
                self.assertEqual(report["native_host_ingest"]["statuses"], ["ok"])
                self.assertEqual(
                    report["native_host_ingest"]["runtime_srs_mutation_values"],
                    [False],
                )

                extension = report["extension_payload"]
                self.assertTrue(extension["private_strings_absent"])
                self.assertEqual(extension["ruby_signal_count"], 0)
                self.assertGreaterEqual(extension["source_signal_count"], 2)
                self.assertIn("pageh", extension["context_key_prefixes"])


if __name__ == "__main__":
    unittest.main()
