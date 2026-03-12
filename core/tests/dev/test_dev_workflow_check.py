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
    _python_change_is_substantive,
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

    def test_build_commands_include_repo_style_strict(self) -> None:
        commands = build_commands()
        labels = [label for label, _command in commands]
        self.assertIn("repo_style_strict", labels)
        style_command = dict(commands)["repo_style_strict"]
        self.assertEqual(
            style_command,
            [sys.executable, "scripts/dev/dev_workflow_style_check.py", "--strict"],
        )

    def test_python_change_is_not_substantive_for_format_only_diff(self) -> None:
        base = "value = {'name': 'lexishift'}\n"
        current = 'value = {"name": "lexishift"}\n'
        self.assertFalse(_python_change_is_substantive(base, current))

    def test_python_change_is_substantive_for_behavior_change(self) -> None:
        base = "value = {'name': 'lexishift'}\n"
        current = 'value = {"name": "codex"}\n'
        self.assertTrue(_python_change_is_substantive(base, current))


if __name__ == "__main__":
    unittest.main()
