from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gui_app import _cleanup_windows_collect_duplicates  # noqa: E402
from gui_app import _terminate_windows_dist_processes  # noqa: E402


class TestGuiAppBuild(unittest.TestCase):
    def test_cleanup_windows_collect_duplicates_removes_root_exes_when_collected_layout_exists(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            for dir_name, exe_name in (
                ("LexiShift", "LexiShift.exe"),
                ("LexiShiftHelper", "LexiShiftHelper.exe"),
                ("LexiShiftNativeHost", "lexishift_native_host.exe"),
            ):
                nested = dist / dir_name / exe_name
                root = dist / exe_name
                nested.parent.mkdir(parents=True, exist_ok=True)
                nested.write_bytes(b"nested")
                root.write_bytes(b"root")

            _cleanup_windows_collect_duplicates(str(dist))

            self.assertFalse((dist / "LexiShift.exe").exists())
            self.assertFalse((dist / "LexiShiftHelper.exe").exists())
            self.assertFalse((dist / "lexishift_native_host.exe").exists())
            self.assertTrue((dist / "LexiShift" / "LexiShift.exe").exists())
            self.assertTrue((dist / "LexiShiftHelper" / "LexiShiftHelper.exe").exists())
            self.assertTrue((dist / "LexiShiftNativeHost" / "lexishift_native_host.exe").exists())

    def test_terminate_windows_dist_processes_only_targets_dist_owned_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            dist_owned = dist / "LexiShiftHelper.exe"
            installed = Path("C:/Program Files/LexiShift/LexiShiftHelper.exe")
            terminated: list[int] = []

            from unittest import mock

            with (
                mock.patch("gui_app.platform.system", return_value="Windows"),
                mock.patch(
                    "gui_app._list_windows_lexishift_processes",
                    return_value=[
                        (101, str(dist_owned)),
                        (202, str(installed)),
                    ],
                ),
                mock.patch(
                    "gui_app._terminate_windows_process_tree",
                    side_effect=lambda pid: terminated.append(pid),
                ),
            ):
                _terminate_windows_dist_processes(str(dist))

        self.assertEqual(terminated, [101])


if __name__ == "__main__":
    unittest.main()
