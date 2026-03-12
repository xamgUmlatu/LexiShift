from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
if str(GUI_SRC) not in sys.path:
    sys.path.insert(0, str(GUI_SRC))

from helper_installer import build_windows_startup_command  # noqa: E402


class TestHelperInstallerAutostart(unittest.TestCase):
    def test_build_windows_startup_command_quotes_spaced_paths(self) -> None:
        python_path = Path("C:/Program Files/Python/pythonw.exe")
        script_path = Path("C:/Program Files/LexiShift/helper_app.py")
        command = build_windows_startup_command([python_path, script_path])
        self.assertIn('"C:/Program Files/Python/pythonw.exe"', command)
        self.assertIn('"C:/Program Files/LexiShift/helper_app.py"', command)


if __name__ == "__main__":
    unittest.main()
