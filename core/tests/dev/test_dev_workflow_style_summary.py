from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dev_workflow_style_summary import render_summary  # noqa: E402


class TestDevWorkflowStyleSummary(unittest.TestCase):
    def test_render_summary_reports_advisory_style_debt(self) -> None:
        markdown = render_summary(
            {
                "lint_exit_code": 1,
                "format_exit_code": 1,
                "strict": False,
                "lint_statistics": [
                    {"count": 39, "code": "F821", "label": "undefined-name"},
                    {"count": 12, "code": "F401", "label": "unused-import"},
                ],
                "format_summary": "46 files would be reformatted\n1 file already formatted",
            }
        )
        self.assertIn("# Repo Style Debt", markdown)
        self.assertIn("- Status: PASS (advisory debt)", markdown)
        self.assertIn("  - 39 `F821` undefined-name", markdown)
        self.assertIn("- Format summary: 1 file already formatted", markdown)

    def test_render_summary_reports_clean_style_state(self) -> None:
        markdown = render_summary(
            {
                "lint_exit_code": 0,
                "format_exit_code": 0,
                "strict": False,
                "lint_statistics": [],
                "format_summary": "318 files already formatted",
            },
            title="Style",
        )
        self.assertIn("# Style", markdown)
        self.assertIn("- Status: PASS", markdown)
        self.assertIn("- Lint exit code: 0", markdown)
        self.assertIn("- Format exit code: 0", markdown)

    def test_render_summary_reports_ruff_unavailable(self) -> None:
        markdown = render_summary(
            {
                "status": "unavailable",
                "lint_exit_code": 127,
                "format_exit_code": 127,
                "strict": False,
                "lint_statistics": [],
                "format_summary": "",
                "ruff_source": "unavailable",
                "ruff_detail": "Tried /tmp/venv/bin/python -m ruff and ruff on PATH",
            }
        )
        self.assertIn("- Status: PASS (ruff unavailable)", markdown)
        self.assertIn("- Ruff source: `unavailable`", markdown)
        self.assertIn(
            "- Ruff detail: Tried /tmp/venv/bin/python -m ruff and ruff on PATH",
            markdown,
        )


if __name__ == "__main__":
    unittest.main()
