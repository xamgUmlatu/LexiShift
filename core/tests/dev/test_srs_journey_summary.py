from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_journey_summary import render_summary  # noqa: E402


class TestSrsJourneySummary(unittest.TestCase):
    def test_render_summary_reports_phase_counts_and_findings(self) -> None:
        markdown = render_summary(
            {
                "generated_at": "2026-03-21T00:00:00+00:00",
                "scenario": {
                    "name": "en-ja_core_journey_v1",
                    "pair": "en-ja",
                    "lane": "deterministic_core_journey",
                    "contract_mode": "observe_current_behavior",
                },
                "summary": {
                    "status": "WARN",
                    "pass_count": 4,
                    "warn_count": 1,
                    "fail_count": 0,
                    "should_fail": False,
                },
                "phases": [
                    {
                        "label": "high_retention_growth",
                        "counts": {"admitted": 5, "due": 3, "published": 5},
                        "refresh": {
                            "requested": True,
                            "payload": {
                                "applied": True,
                                "admission_refresh": {"reason_code": "normal"},
                            },
                        },
                        "deltas": {
                            "admitted_in": ["delta", "epsilon"],
                            "admitted_out": [],
                            "due_in": ["delta", "epsilon"],
                            "due_out": ["alpha", "beta"],
                            "published_in": ["delta", "epsilon"],
                            "published_out": [],
                        },
                        "relationships": {"published_not_due": ["alpha", "beta"]},
                    },
                    {
                        "label": "fade_check",
                        "counts": {"admitted": 7, "due": 3, "published": 7},
                        "refresh": {"requested": False, "payload": None},
                        "deltas": {
                            "admitted_in": [],
                            "admitted_out": [],
                            "due_in": ["gamma"],
                            "due_out": ["delta"],
                            "published_in": [],
                            "published_out": [],
                        },
                        "relationships": {
                            "published_not_due": ["alpha", "beta", "delta", "epsilon"]
                        },
                        "items": [
                            {"lemma": "alpha", "cohort": "stable", "in_due": False},
                            {"lemma": "beta", "cohort": "stable", "in_due": False},
                            {"lemma": "gamma", "cohort": "difficult", "in_due": True},
                        ],
                    },
                ],
                "findings": [
                    {
                        "level": "WARN",
                        "phase": "high_retention_growth",
                        "code": "SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED",
                        "message": "Published set is broader than the due subset in the current journey run.",
                        "details": "phase=high_retention_growth admitted=5 due=3 published=5",
                    }
                ],
            }
        )
        self.assertIn("# SRS Journey Harness", markdown)
        self.assertIn("- Lane: `deterministic_core_journey`", markdown)
        self.assertIn("### high_retention_growth", markdown)
        self.assertIn("- Counts: admitted=5 due=3 published=5", markdown)
        self.assertIn("- Stable cohort due in final phase: none", markdown)
        self.assertIn(
            "[WARN] [high_retention_growth] `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`", markdown
        )


if __name__ == "__main__":
    unittest.main()
