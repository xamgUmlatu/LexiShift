from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from installer import _build_windows_installer, _ensure_iscc, _find_windows_distribution  # noqa: E402


class TestWindowsInstallerDistribution(unittest.TestCase):
    def test_find_windows_distribution_prefers_collected_main_exe(self) -> None:
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

        self.assertEqual(exe_path, main_exe)
        self.assertEqual(content_dir, dist)

    def test_find_windows_distribution_falls_back_to_root_main_exe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            main_exe = dist / "LexiShift.exe"
            helper_exe = dist / "LexiShiftHelper.exe"
            host_exe = dist / "lexishift_native_host.exe"
            main_exe.parent.mkdir(parents=True, exist_ok=True)
            main_exe.write_bytes(b"main")
            helper_exe.write_bytes(b"helper")
            host_exe.write_bytes(b"host")

            exe_path, content_dir = _find_windows_distribution(dist)

        self.assertEqual(exe_path, main_exe)
        self.assertEqual(content_dir, dist)

    def test_build_windows_installer_rejects_output_inside_dist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dist = root / "dist"
            output = dist / "installers"
            main_exe = dist / "LexiShift" / "LexiShift.exe"
            helper_exe = dist / "LexiShiftHelper" / "LexiShiftHelper.exe"
            host_exe = dist / "LexiShiftNativeHost" / "lexishift_native_host.exe"
            for path in (main_exe, helper_exe, host_exe):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x")

            with self.assertRaises(SystemExit) as ctx:
                with mock.patch("installer._ensure_iscc", return_value="iscc.exe"):
                    _build_windows_installer(
                        repo_root=root,
                        dist_dir=dist,
                        output_dir=output,
                        app_name="LexiShift",
                        app_version="0.1.0",
                    )

        self.assertIn("outside the dist directory", str(ctx.exception))

    def test_build_windows_installer_passes_relative_app_exe_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dist = root / "dist"
            output = root / "installers"
            main_exe = dist / "LexiShift" / "LexiShift.exe"
            helper_exe = dist / "LexiShiftHelper" / "LexiShiftHelper.exe"
            host_exe = dist / "LexiShiftNativeHost" / "lexishift_native_host.exe"
            for path in (main_exe, helper_exe, host_exe):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x")

            with (
                mock.patch("installer._ensure_iscc", return_value="iscc.exe"),
                mock.patch("installer.subprocess.run") as run_mock,
            ):
                run_mock.return_value = mock.Mock(returncode=0)
                result = _build_windows_installer(
                    repo_root=root,
                    dist_dir=dist,
                    output_dir=output,
                    app_name="LexiShift",
                    app_version="0.1.0",
                )

        command = run_mock.call_args.args[0]
        self.assertIn("/DAppExePath=LexiShift\\LexiShift.exe", command)
        self.assertEqual(result, output)

    def test_ensure_iscc_finds_user_local_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            fake_iscc = fake_home / "AppData" / "Local" / "Programs" / "Inno Setup 6" / "ISCC.exe"
            fake_iscc.parent.mkdir(parents=True, exist_ok=True)
            fake_iscc.write_bytes(b"iscc")

            with (
                mock.patch("installer.shutil.which", return_value=None),
                mock.patch("installer.Path.home", return_value=fake_home),
                mock.patch.dict(
                    "installer.os.environ",
                    {"ProgramFiles": "", "ProgramFiles(x86)": ""},
                    clear=False,
                ),
            ):
                resolved = _ensure_iscc()

        self.assertEqual(resolved, str(fake_iscc))


if __name__ == "__main__":
    unittest.main()
