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
                    "status": "PASS",
                    "pass_count": 7,
                    "warn_count": 0,
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
                        "srs_due_metadata_count": 12,
                        "runtime_due_active_count": 8,
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
                            "runtime_due_active_count": 2,
                            "selected_lemmas": ["beta", "gamma"],
                            "feedback_delta": {"reviewed_lemmas": ["alpha"]},
                            "refresh_delta": {"added_lemmas": ["beta", "gamma"]},
                        }
                    ]
                },
                "encounter_watch_scenario": {
                    "stale_age_days": 7,
                    "dashboard_summary": {
                        "active_zero_exposure_zero_feedback": 4,
                        "active_stale_zero_exposure_zero_feedback": 2,
                        "active_zero_exposure_zero_feedback_age_unknown": 1,
                        "active_without_enabled_rules": 1,
                        "encounter_watch": 4,
                    },
                },
                "findings": [
                    {
                        "level": "PASS",
                        "pair": "en-ja",
                        "code": "SRS_DUE_AWARE_RUNTIME_GATE_VERIFIED",
                        "message": (
                            "Helper ruleset may remain broader than due, but due metadata supports "
                            "runtime due-aware serving."
                        ),
                        "details": (
                            "total_items=12 due_count=8 ruleset_count=12 "
                            "srs_due_metadata_count=12 runtime_due_active_count=8"
                        ),
                    }
                ],
            }
        )
        self.assertIn("# SRS Quality Harness", markdown)
        self.assertIn("- Status: PASS", markdown)
        self.assertIn("### en-ja", markdown)
        self.assertIn("- SRS due metadata/runtime-active targets: 12/8", markdown)
        self.assertIn("## Feedback Cycle", markdown)
        self.assertIn("runtime_due_active=2", markdown)
        self.assertIn("selected=beta, gamma", markdown)
        self.assertIn("feedback_reviewed=alpha", markdown)
        self.assertIn("refresh_added=beta, gamma", markdown)
        self.assertIn("## Encounter Watch", markdown)
        self.assertIn("- Stale unseen/no-feedback: 2 over 7d", markdown)
        self.assertIn("- Active without enabled rules: 1", markdown)
        self.assertIn("None.", markdown)


if __name__ == "__main__":
    unittest.main()
