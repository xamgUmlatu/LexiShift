from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from windows_parity_summary import render_summary  # noqa: E402


class TestWindowsParitySummary(unittest.TestCase):
    def test_render_summary_lists_status_counts_and_checks(self) -> None:
        markdown = render_summary(
            {
                "status": "FAIL",
                "counts": {"pass": 2, "warn": 1, "fail": 3},
                "checks": [
                    {
                        "title": "Hosted Windows Validation",
                        "status": "FAIL",
                        "summary": "Hosted CI has no Windows runner yet for build/parity reporting.",
                    }
                ],
            },
            title="Windows Parity",
        )

        self.assertIn("# Windows Parity", markdown)
        self.assertIn("- Status: FAIL", markdown)
        self.assertIn("- Counts: PASS=2 WARN=1 FAIL=3", markdown)
        self.assertIn(
            "- `FAIL` Hosted Windows Validation: Hosted CI has no Windows runner yet for build/parity reporting.",
            markdown,
        )


if __name__ == "__main__":
    unittest.main()
