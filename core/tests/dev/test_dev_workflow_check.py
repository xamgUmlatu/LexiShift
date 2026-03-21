from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dev_workflow_check import build_commands  # noqa: E402
from dev_workflow_changed_check import (  # noqa: E402
    _json_change_is_substantive,
    _needs_doc_reference_check,
    _python_change_is_substantive,
    _text_change_is_substantive,
)


class TestDevWorkflowCheck(unittest.TestCase):
    def test_build_commands_include_strict_windows_parity_audit(self) -> None:
        commands = build_commands()
        labels = [label for label, _command in commands]
        self.assertIn("windows_parity_audit", labels)
        parity_command = dict(commands)["windows_parity_audit"]
        self.assertEqual(
            parity_command,
            [sys.executable, "scripts/dev/windows_parity_audit.py", "--strict"],
        )

    def test_build_commands_can_skip_windows_parity_audit(self) -> None:
        commands = build_commands(skip_windows_parity=True)
        labels = [label for label, _command in commands]
        self.assertNotIn("windows_parity_audit", labels)

    def test_build_commands_include_repo_style_strict(self) -> None:
        commands = build_commands()
        labels = [label for label, _command in commands]
        self.assertIn("repo_style_strict", labels)
        style_command = dict(commands)["repo_style_strict"]
        self.assertEqual(
            style_command,
            [sys.executable, "scripts/dev/dev_workflow_style_check.py", "--strict"],
        )

    def test_build_commands_compile_new_srs_journey_scripts(self) -> None:
        commands = build_commands()
        compile_command = dict(commands)["workflow_py_compile"]
        self.assertIn("scripts/testing/srs_journey_harness.py", compile_command)
        self.assertIn("scripts/testing/srs_journey_harness_support.py", compile_command)
        self.assertIn("scripts/testing/srs_journey_installed_support.py", compile_command)
        self.assertIn("scripts/testing/srs_journey_review_support.py", compile_command)
        self.assertIn("scripts/testing/srs_journey_runtime_support.py", compile_command)
        self.assertIn("scripts/testing/srs_journey_summary.py", compile_command)
        self.assertIn("scripts/testing/srs_journey_html.py", compile_command)

    def test_build_commands_include_doc_reference_audit(self) -> None:
        commands = build_commands()
        labels = [label for label, _command in commands]
        self.assertIn("doc_references", labels)
        doc_reference_command = dict(commands)["doc_references"]
        self.assertEqual(
            doc_reference_command,
            [sys.executable, "scripts/dev/check_doc_references.py"],
        )

    def test_python_change_is_not_substantive_for_format_only_diff(self) -> None:
        base = "value = {'name': 'lexishift'}\n"
        current = 'value = {"name": "lexishift"}\n'
        self.assertFalse(_python_change_is_substantive(base, current))

    def test_python_change_is_substantive_for_behavior_change(self) -> None:
        base = "value = {'name': 'lexishift'}\n"
        current = 'value = {"name": "codex"}\n'
        self.assertTrue(_python_change_is_substantive(base, current))

    def test_json_change_is_not_substantive_for_pretty_print_only(self) -> None:
        base = '{"name":"lexishift","enabled":true}\n'
        current = '{\n  "enabled": true,\n  "name": "lexishift"\n}\n'
        self.assertFalse(_json_change_is_substantive(base, current))

    def test_json_change_is_substantive_for_value_change(self) -> None:
        base = '{"name":"lexishift","enabled":true}\n'
        current = '{"name":"lexishift","enabled":false}\n'
        self.assertTrue(_json_change_is_substantive(base, current))

    def test_text_change_is_not_substantive_for_reflow_only(self) -> None:
        base = "Line one wraps here.\nLine two continues.\n"
        current = "Line one wraps here. Line two continues.\n"
        self.assertFalse(_text_change_is_substantive(base, current))

    def test_text_change_is_substantive_for_content_change(self) -> None:
        base = "Line one wraps here.\nLine two continues.\n"
        current = "Line one wraps here.\nLine two changed.\n"
        self.assertTrue(_text_change_is_substantive(base, current))

    def test_doc_reference_check_is_required_for_referenced_source_paths(self) -> None:
        self.assertTrue(_needs_doc_reference_check(["core/lexishift_core/helper/rulegen.py"]))
        self.assertTrue(_needs_doc_reference_check(["apps/chrome-extension/options.html"]))
        self.assertTrue(_needs_doc_reference_check(["scripts/README.md"]))

    def test_doc_reference_check_is_not_required_for_unrelated_paths(self) -> None:
        self.assertFalse(_needs_doc_reference_check(["data/sample.txt"]))


if __name__ == "__main__":
    unittest.main()
