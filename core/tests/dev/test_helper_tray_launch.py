from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
CORE_SRC = REPO_ROOT / "core"
if str(GUI_SRC) not in sys.path:
    sys.path.insert(0, str(GUI_SRC))
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

import helper_tray  # noqa: E402


class TestHelperTrayLaunch(unittest.TestCase):
    def test_open_main_app_uses_windows_main_exe_when_helper_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_exe = root / "LexiShift" / "LexiShift.exe"
            helper_exe = root / "LexiShiftHelper" / "LexiShiftHelper.exe"
            main_exe.parent.mkdir(parents=True)
            helper_exe.parent.mkdir(parents=True)
            main_exe.write_text("", encoding="utf-8")
            helper_exe.write_text("", encoding="utf-8")

            with (
                mock.patch.object(helper_tray.SYS, "platform", "win32"),
                mock.patch.object(helper_tray.SYS, "frozen", True, create=True),
                mock.patch.object(helper_tray.SYS, "executable", str(helper_exe)),
                mock.patch.object(helper_tray, "Popen") as popen_mock,
            ):
                helper_tray._open_main_app()

            popen_mock.assert_called_once()
            self.assertEqual(
                [Path(value).resolve() for value in popen_mock.call_args.args[0]],
                [main_exe.resolve()],
            )
