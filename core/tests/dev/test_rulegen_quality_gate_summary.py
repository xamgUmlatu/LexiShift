from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_quality_gate_summary import render_summary  # noqa: E402


class TestRulegenQualityGateSummary(unittest.TestCase):
    def test_render_summary_reports_warn_status_and_actionable_findings(self) -> None:
        markdown = render_summary(
            {
                "benchmark_json": "bench.json",
                "policy_json": "policy.json",
                "pair_scope": "en-de",
                "fail_on_warn": False,
                "strict_saturation": False,
                "summary": {
                    "status": "WARN",
                    "pass_count": 3,
                    "warn_count": 2,
                    "fail_count": 0,
                    "should_fail": False,
                },
                "findings": [
                    {
                        "level": "WARN",
                        "code": "SATURATION_TOP_VECTOR_WARN",
                        "message": "Top vector share is too high.",
                        "details": "run_count=10 unique_vectors=2 top_count=8",
                    },
                    {
                        "level": "PASS",
                        "code": "QUALITY_FLOOR_OK",
                        "message": "Quality floor satisfied.",
                        "details": None,
                    },
                ],
            }
        )
        self.assertIn("# Rulegen Quality Gate", markdown)
        self.assertIn("- Status: WARN", markdown)
        self.assertIn("- Findings: pass=3 warn=2 fail=0", markdown)
        self.assertIn("- Pair scope: `en-de`", markdown)
        self.assertIn(
            "1. [WARN] `SATURATION_TOP_VECTOR_WARN`: Top vector share is too high.", markdown
        )
        self.assertIn("run_count=10 unique_vectors=2 top_count=8", markdown)


if __name__ == "__main__":
    unittest.main()
