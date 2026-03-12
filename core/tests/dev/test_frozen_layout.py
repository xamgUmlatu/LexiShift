from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
if str(GUI_SRC) not in sys.path:
    sys.path.insert(0, str(GUI_SRC))

from frozen_layout import (  # noqa: E402
    HELPER_APP_BUNDLE_NAME,
    HELPER_WINDOWS_DIR_NAME,
    HELPER_WINDOWS_EXE_NAME,
    MAIN_APP_BUNDLE_NAME,
    MAIN_WINDOWS_DIR_NAME,
    MAIN_WINDOWS_EXE_NAME,
    resolve_macos_sibling_bundle,
    resolve_windows_sibling_executable,
)


class TestFrozenLayout(unittest.TestCase):
    def test_resolve_windows_helper_from_main_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_exe = root / MAIN_WINDOWS_DIR_NAME / MAIN_WINDOWS_EXE_NAME
            helper_exe = root / HELPER_WINDOWS_DIR_NAME / HELPER_WINDOWS_EXE_NAME
            main_exe.parent.mkdir(parents=True)
            helper_exe.parent.mkdir(parents=True)
            main_exe.write_text("", encoding="utf-8")
            helper_exe.write_text("", encoding="utf-8")
            resolved = resolve_windows_sibling_executable(
                main_exe,
                preferred_dir_name=HELPER_WINDOWS_DIR_NAME,
                exe_name=HELPER_WINDOWS_EXE_NAME,
            )
            self.assertEqual(resolved.resolve(), helper_exe.resolve())

    def test_resolve_windows_main_from_helper_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_exe = root / MAIN_WINDOWS_DIR_NAME / MAIN_WINDOWS_EXE_NAME
            helper_exe = root / HELPER_WINDOWS_DIR_NAME / HELPER_WINDOWS_EXE_NAME
            main_exe.parent.mkdir(parents=True)
            helper_exe.parent.mkdir(parents=True)
            main_exe.write_text("", encoding="utf-8")
            helper_exe.write_text("", encoding="utf-8")
            resolved = resolve_windows_sibling_executable(
                helper_exe,
                preferred_dir_name=MAIN_WINDOWS_DIR_NAME,
                exe_name=MAIN_WINDOWS_EXE_NAME,
            )
            self.assertEqual(resolved.resolve(), main_exe.resolve())

    def test_resolve_macos_sibling_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_bundle = root / HELPER_APP_BUNDLE_NAME
            main_bundle = root / MAIN_APP_BUNDLE_NAME
            executable = current_bundle / "Contents" / "MacOS" / "LexiShiftHelper"
            executable.parent.mkdir(parents=True)
            main_bundle.mkdir(parents=True)
            executable.write_text("", encoding="utf-8")
            resolved = resolve_macos_sibling_bundle(executable, MAIN_APP_BUNDLE_NAME)
            self.assertEqual(resolved.resolve(), main_bundle.resolve())


if __name__ == "__main__":
    unittest.main()
