from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark_triage_summary import render_summary  # noqa: E402


class TestRulegenBenchmarkTriageSummary(unittest.TestCase):
    def test_render_summary_reports_fail_and_review_items(self) -> None:
        markdown = render_summary(
            {
                "benchmark_json": "bench.json",
                "pairs_processed": 2,
                "failing_or_review_count": 2,
                "items": [
                    {
                        "pair": "en-es",
                        "case_id": "case-1",
                        "target": "madre",
                        "status": "FAIL",
                        "reasons": ["top1_is_forbidden"],
                        "top1_source": "bed",
                    },
                    {
                        "pair": "en-ja",
                        "case_id": "case-2",
                        "target": "車",
                        "status": "REVIEW",
                        "reasons": ["top1_not_in_expected_set"],
                        "top1_source": "car",
                    },
                ],
            }
        )
        self.assertIn("# Rulegen Benchmark Triage", markdown)
        self.assertIn("- FAIL items: 1", markdown)
        self.assertIn("- REVIEW items: 1", markdown)
        self.assertIn("1. [FAIL] `en-es` `case-1` target=`madre`", markdown)
        self.assertIn("2. [REVIEW] `en-ja` `case-2` target=`車`", markdown)


if __name__ == "__main__":
    unittest.main()
