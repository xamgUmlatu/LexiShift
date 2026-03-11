from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_quality_summary import render_summary  # noqa: E402


class TestSrsQualitySummary(unittest.TestCase):
    def test_render_summary_reports_bootstrap_and_feedback_sections(self) -> None:
        markdown = render_summary(
            {
                "fail_on_warn": False,
                "supported_pairs": ["en-ja", "en-de"],
                "unsupported_pairs": ["en-es"],
                "summary": {
                    "status": "WARN",
                    "pass_count": 6,
                    "warn_count": 1,
                    "fail_count": 0,
                    "should_fail": False,
                },
                "pair_bootstrap_scenarios": [
                    {
                        "pair": "en-ja",
                        "store_items_for_pair": 12,
                        "due_count": 8,
                        "snapshot_target_count": 12,
                        "ruleset_unique_targets": 12,
                        "diagnostics": {
                            "store_exists": True,
                            "ruleset_exists": True,
                            "snapshot_exists": True,
                        },
                    }
                ],
                "feedback_cycle_scenario": {
                    "phases": [
                        {
                            "label": "high_retention_1",
                            "applied": True,
                            "reason_code": "normal",
                            "total_items_for_pair": 3,
                            "ruleset_count": 3,
                        }
                    ]
                },
                "findings": [
                    {
                        "level": "WARN",
                        "pair": "en-ja",
                        "code": "SRS_DUE_AWARE_PUBLISH_UNVERIFIED",
                        "message": "Published snapshot appears to cover admitted items beyond the due subset.",
                        "details": "store_items_for_pair=12 due_count=8 snapshot_target_count=12",
                    }
                ],
            }
        )
        self.assertIn("# SRS Quality Harness", markdown)
        self.assertIn("- Status: WARN", markdown)
        self.assertIn("### en-ja", markdown)
        self.assertIn("## Feedback Cycle", markdown)
        self.assertIn("[WARN] [en-ja] `SRS_DUE_AWARE_PUBLISH_UNVERIFIED`", markdown)


if __name__ == "__main__":
    unittest.main()
