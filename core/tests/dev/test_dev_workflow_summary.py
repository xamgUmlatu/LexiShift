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
                "platform": "Darwin",
                "expected_artifact_count": 2,
                "verified_artifact_count": 2,
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
        self.assertIn("- Platform: `Darwin`", markdown)
        self.assertIn("- Commands passed: 1/1", markdown)
        self.assertIn("- Verified artifacts: 2/2", markdown)

    def test_render_summary_reports_changed_scope_advisory_style_debt(self) -> None:
        markdown = render_summary(
            changed_payload={
                "scope": "branch",
                "base_ref": "origin/main",
                "changed_files_count": 12,
                "substantive_changed_files_count": 4,
                "format_only_python_files_count": 2,
                "format_only_text_files_count": 3,
                "project_health": {"exit_code": 0},
                "changed_python_files": ["a.py", "b.py"],
                "style": {
                    "status": "advisory-fail",
                    "lint_summary": "Found 39 errors.",
                    "format_summary": "46 files would be reformatted",
                },
                "betterdiscord_freshness": {
                    "required": True,
                    "exit_code": 0,
                    "trigger_files": ["apps/betterdiscord-plugin/build_plugin.js"],
                },
                "feature_state": {
                    "required": True,
                    "compare_ref": "origin/main",
                    "exit_code": 0,
                    "trigger_files": ["docs/developer/feature_state_matrix.md"],
                },
                "windows_parity": {
                    "required": True,
                    "exit_code": 0,
                    "trigger_files": ["apps/gui/src/helper_installer.py"],
                },
                "rulegen_quality": {
                    "required": True,
                    "mode": "dry-run",
                    "exit_code": 0,
                    "inference_basis": "substantive_changed_files",
                    "trigger_files": ["core/lexishift_core/rulegen/generation.py"],
                },
            }
        )
        self.assertIn("## Changed Scope", markdown)
        self.assertIn("- Status: PASS (advisory style debt)", markdown)
        self.assertIn("- Substantive changed files: 4", markdown)
        self.assertIn("- Format-only Python files ignored for heavy-loop inference: 2", markdown)
        self.assertIn("- Format-only text/data files ignored for heavy-loop inference: 3", markdown)
        self.assertIn(
            "- Style: `advisory-fail` (39 lint errors, 46 files need formatting)", markdown
        )
        self.assertIn(
            "- Feature-state audit: required (`origin/main`), PASS via `docs/developer/feature_state_matrix.md`",
            markdown,
        )
        self.assertIn(
            "- Windows parity: required, PASS via `apps/gui/src/helper_installer.py`",
            markdown,
        )
        self.assertIn(
            "- Rulegen quality: required (`dry-run`), PASS via `substantive_changed_files` from `core/lexishift_core/rulegen/generation.py`",
            markdown,
        )

    def test_render_summary_reports_ci_safe_build_skips(self) -> None:
        markdown = render_summary(
            build_payload={
                "overall_exit_code": 0,
                "ci_safe": True,
                "platform": "Linux",
                "expected_artifact_count": 1,
                "verified_artifact_count": 1,
                "commands": [
                    {"label": "betterdiscord_build", "exit_code": 0},
                ],
                "skipped_commands": [
                    {
                        "label": "gui_build_validate",
                        "reason": "macOS app-bundle validation is not supported on this host",
                    }
                ],
            }
        )
        self.assertIn("## Build Safety", markdown)
        self.assertIn("- Status: PASS (ci-safe partial)", markdown)
        self.assertIn("- Verified artifacts: 1/1", markdown)
        self.assertIn(
            "- Skipped: `gui_build_validate` (macOS app-bundle validation is not supported on this host)",
            markdown,
        )

    def test_render_summary_treats_artifact_verification_failure_as_failed_command(self) -> None:
        markdown = render_summary(
            build_payload={
                "overall_exit_code": 1,
                "platform": "Darwin",
                "expected_artifact_count": 4,
                "verified_artifact_count": 3,
                "commands": [
                    {
                        "label": "gui_build_validate",
                        "exit_code": 0,
                        "artifact_verification_exit_code": 1,
                        "missing_artifacts": [
                            "/tmp/LexiShift.app",
                            "/tmp/LexiShift Helper.app",
                        ],
                        "stdout_tail": [
                            "Build complete!",
                            "[validate] Main app not found: /tmp/LexiShift.app",
                        ],
                    }
                ],
            }
        )
        self.assertIn("- Status: FAIL", markdown)
        self.assertIn("- Commands passed: 0/1", markdown)
        self.assertIn("- First failed command: `gui_build_validate`", markdown)
        self.assertIn("- Missing artifacts:", markdown)
        self.assertIn("`/tmp/LexiShift.app`", markdown)
        self.assertIn("- Failure stdout tail:", markdown)
        self.assertIn("[validate] Main app not found: /tmp/LexiShift.app", markdown)

    def test_render_summary_includes_repo_safety_failure_output_tails(self) -> None:
        markdown = render_summary(
            check_payload={
                "overall_exit_code": 1,
                "commands": [
                    {
                        "label": "unit_tests",
                        "exit_code": 0,
                    },
                    {
                        "label": "mypy",
                        "exit_code": 1,
                        "stdout_tail": ["+ python -m mypy core/lexishift_core"],
                        "stderr_tail": [
                            "core/lexishift_core/example.py:10: error: Incompatible types"
                        ],
                    },
                ],
            }
        )
        self.assertIn("- Status: FAIL", markdown)
        self.assertIn("- First failed command: `mypy`", markdown)
        self.assertIn("- Failure stdout tail:", markdown)
        self.assertIn("+ python -m mypy core/lexishift_core", markdown)
        self.assertIn("- Failure stderr tail:", markdown)
        self.assertIn("error: Incompatible types", markdown)


if __name__ == "__main__":
    unittest.main()
