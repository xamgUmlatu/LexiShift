from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_quality_harness import build_report  # noqa: E402


class TestSrsQualityHarness(unittest.TestCase):
    def test_build_report_for_en_ja_surfaces_due_aware_warning_without_failures(self) -> None:
        report = build_report(pairs=("en-ja",), include_feedback=True)
        summary = report["summary"]
        findings = report["findings"]
        self.assertEqual(summary["fail_count"], 0)
        self.assertGreaterEqual(summary["warn_count"], 1)
        self.assertTrue(
            any(item.get("code") == "SRS_DUE_AWARE_PUBLISH_UNVERIFIED" for item in findings)
        )


if __name__ == "__main__":
    unittest.main()
