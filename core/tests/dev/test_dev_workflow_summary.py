from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dev_workflow_summary import render_summary  # noqa: E402


class TestDevWorkflowSummary(unittest.TestCase):
    def test_render_summary_includes_clean_repo_safety_and_build_sections(self) -> None:
        markdown = render_summary(
            check_payload={
                "overall_exit_code": 0,
                "commands": [
                    {"label": "unit_tests", "exit_code": 0},
                    {"label": "mypy", "exit_code": 0},
                ],
            },
            build_payload={
                "overall_exit_code": 0,
                "commands": [
                    {"label": "betterdiscord_build", "exit_code": 0},
                ],
            },
            title="Workflow",
        )
        self.assertIn("# Workflow", markdown)
        self.assertIn("## Repo Safety", markdown)
        self.assertIn("- Status: PASS", markdown)
        self.assertIn("- Commands passed: 2/2", markdown)
        self.assertIn("## Build Safety", markdown)
        self.assertIn("- Commands passed: 1/1", markdown)

    def test_render_summary_reports_changed_scope_advisory_style_debt(self) -> None:
        markdown = render_summary(
            changed_payload={
                "scope": "branch",
                "base_ref": "origin/main",
                "changed_files_count": 12,
                "project_health": {"exit_code": 0},
                "changed_python_files": ["a.py", "b.py"],
                "style": {
                    "status": "advisory-fail",
                    "lint_summary": "Found 39 errors.",
                    "format_summary": "46 files would be reformatted",
                },
                "betterdiscord_freshness": {"required": True, "exit_code": 0},
                "rulegen_quality": {"required": True, "mode": "dry-run", "exit_code": 0},
            }
        )
        self.assertIn("## Changed Scope", markdown)
        self.assertIn("- Status: PASS (advisory style debt)", markdown)
        self.assertIn(
            "- Style: `advisory-fail` (39 lint errors, 46 files need formatting)", markdown
        )
        self.assertIn("- Rulegen quality: required (`dry-run`), PASS", markdown)


if __name__ == "__main__":
    unittest.main()
