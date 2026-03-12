from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from installer import _find_windows_distribution  # noqa: E402


class TestWindowsInstallerDistribution(unittest.TestCase):
    def test_find_windows_distribution_prefers_root_when_multiple_subdirs_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            main_exe = dist / "LexiShift" / "LexiShift.exe"
            helper_exe = dist / "LexiShiftHelper" / "LexiShiftHelper.exe"
            host_exe = dist / "LexiShiftNativeHost" / "lexishift_native_host.exe"
            main_exe.parent.mkdir(parents=True, exist_ok=True)
            helper_exe.parent.mkdir(parents=True, exist_ok=True)
            host_exe.parent.mkdir(parents=True, exist_ok=True)
            main_exe.write_bytes(b"main")
            helper_exe.write_bytes(b"helper")
            host_exe.write_bytes(b"host")

            exe_path, content_dir = _find_windows_distribution(dist)

        self.assertEqual(exe_path.name, "LexiShift.exe")
        self.assertEqual(content_dir, dist)


if __name__ == "__main__":
    unittest.main()
