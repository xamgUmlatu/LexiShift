from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dev_workflow_check import build_commands  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
