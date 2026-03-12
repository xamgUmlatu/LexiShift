from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
if str(GUI_SRC) not in sys.path:
    sys.path.insert(0, str(GUI_SRC))

import helper_ui  # noqa: E402


class TestHelperUiAutostart(unittest.TestCase):
    def test_ensure_helper_autostart_uses_windows_helper_exe_when_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_exe = root / "LexiShift" / "LexiShift.exe"
            helper_exe = root / "LexiShiftHelper" / "LexiShiftHelper.exe"
            main_exe.parent.mkdir(parents=True)
            helper_exe.parent.mkdir(parents=True)
            main_exe.write_text("", encoding="utf-8")
            helper_exe.write_text("", encoding="utf-8")

            with (
                mock.patch.object(helper_ui.sys, "platform", "win32"),
                mock.patch.object(helper_ui.sys, "frozen", True, create=True),
                mock.patch.object(helper_ui.sys, "executable", str(main_exe)),
                mock.patch.object(
                    helper_ui, "install_helper_autostart", return_value=True
                ) as install_mock,
            ):
                helper_ui.ensure_helper_autostart()

            install_mock.assert_called_once()
            self.assertEqual(
                [Path(value).resolve() for value in install_mock.call_args.args[0]],
                [helper_exe.resolve()],
            )
