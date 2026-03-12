from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from windows_parity_audit import (  # noqa: E402
    assess_hosted_windows_validation,
    assess_windows_bundle_validation,
    assess_windows_helper_packaging,
    assess_windows_native_messaging_install,
    assess_windows_tray_launch,
)


class TestWindowsParityAudit(unittest.TestCase):
    def test_helper_packaging_fails_when_helper_is_macos_only(self) -> None:
        spec_text = """
if sys.platform == "darwin":
    helper_a = Analysis([])
else:
    coll = COLLECT(main_exe)
"""
        result = assess_windows_helper_packaging(spec_text)
        self.assertEqual(result.status, "FAIL")

    def test_bundle_validation_fails_without_windows_branch(self) -> None:
        validator_text = """
MAIN_APP_BUNDLE = "LexiShift.app"
def _validate_dist(dist_path):
    info = app_path / "Contents" / "Info.plist"
"""
        result = assess_windows_bundle_validation(validator_text)
        self.assertEqual(result.status, "FAIL")

    def test_hosted_windows_validation_passes_when_ci_has_windows_runner(self) -> None:
        ci_text = """
jobs:
  windows-parity:
    runs-on: windows-latest
"""
        result = assess_hosted_windows_validation(ci_text)
        self.assertEqual(result.status, "PASS")

    def test_native_messaging_install_fails_when_windows_path_is_unsupported(self) -> None:
        helper_installer_text = """
def _chrome_host_dir(browser: str = "chrome"):
    if sys.platform.startswith("win"):
        return None

def install_helper():
    return "Helper install not supported on this OS yet."
"""
        result = assess_windows_native_messaging_install(helper_installer_text)
        self.assertEqual(result.status, "FAIL")

    def test_tray_launch_fails_without_windows_specific_frozen_launch(self) -> None:
        helper_tray_text = """
def _open_main_app() -> None:
    if getattr(SYS, "frozen", False):
        if SYS.platform == "darwin":
            cmd = ["open", "LexiShift.app"]

class HelperTrayController:
    pass
"""
        result = assess_windows_tray_launch(helper_tray_text)
        self.assertEqual(result.status, "FAIL")


if __name__ == "__main__":
    unittest.main()
