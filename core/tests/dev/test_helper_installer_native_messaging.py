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

import helper_installer  # noqa: E402


class _FakeRegistryKey:
    def __init__(self, registry: "_FakeWinreg", path: str):
        self._registry = registry
        self.path = path

    def __enter__(self) -> "_FakeRegistryKey":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeWinreg:
    HKEY_CURRENT_USER = object()
    KEY_SET_VALUE = 0x0002
    KEY_QUERY_VALUE = 0x0001
    KEY_WOW64_32KEY = 0x0200
    KEY_WOW64_64KEY = 0x0100
    REG_SZ = 1

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def CreateKeyEx(self, root, path, reserved, access):  # noqa: N802
        return _FakeRegistryKey(self, path)

    def OpenKey(self, root, path, reserved, access):  # noqa: N802
        if path not in self.values:
            raise FileNotFoundError(path)
        return _FakeRegistryKey(self, path)

    def SetValueEx(self, key, name, reserved, reg_type, value):  # noqa: N802
        self.values[key.path] = str(value)

    def QueryValueEx(self, key, name):  # noqa: N802
        return self.values[key.path], self.REG_SZ


class TestHelperInstallerNativeMessaging(unittest.TestCase):
    def test_default_host_script_prefers_bundled_windows_host_exe_when_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_exe = root / "LexiShift" / "LexiShift.exe"
            host_exe = root / "LexiShiftNativeHost" / "lexishift_native_host.exe"
            main_exe.parent.mkdir(parents=True, exist_ok=True)
            host_exe.parent.mkdir(parents=True, exist_ok=True)
            main_exe.write_bytes(b"main")
            host_exe.write_bytes(b"host")

            with (
                mock.patch.object(helper_installer.sys, "platform", "win32"),
                mock.patch.object(helper_installer.sys, "frozen", True, create=True),
                mock.patch.object(helper_installer.sys, "executable", str(main_exe)),
            ):
                resolved = helper_installer.default_host_script()

        self.assertEqual(resolved.resolve(), host_exe.resolve())

    def test_install_helper_writes_windows_manifest_and_registry(self) -> None:
        fake_winreg = _FakeWinreg()
        with tempfile.TemporaryDirectory() as tmpdir:
            data_root = Path(tmpdir) / "data"
            host_dir = Path(tmpdir) / "LexiShiftNativeHost"
            host_exe = host_dir / "lexishift_native_host.exe"
            dependency = host_dir / "python310.dll"
            host_dir.mkdir(parents=True, exist_ok=True)
            host_exe.write_bytes(b"host")
            dependency.write_bytes(b"dll")

            with (
                mock.patch.object(helper_installer.sys, "platform", "win32"),
                mock.patch.dict(sys.modules, {"winreg": fake_winreg}),
                mock.patch.object(helper_installer, "_helper_data_root", return_value=data_root),
            ):
                result = helper_installer.install_helper(
                    extension_id="abcdefghijklmnopabcdefghijklmnop",
                    browser="chrome",
                    host_path=host_exe,
                )

            self.assertTrue(result.installed)
            self.assertIsNotNone(result.manifest_path)
            assert result.manifest_path is not None
            manifest_payload = result.manifest_path.read_text(encoding="utf-8")
            self.assertIn("chrome-extension://abcdefghijklmnopabcdefghijklmnop/", manifest_payload)
            copied_host = data_root / "helper" / "native_host" / "lexishift_native_host.exe"
            self.assertTrue(copied_host.exists())
            self.assertTrue((data_root / "helper" / "native_host" / "python310.dll").exists())
            registry_key = helper_installer.WINDOWS_NATIVE_MESSAGING_REGISTRY_KEYS["chrome"]
            self.assertEqual(fake_winreg.values[registry_key], str(result.manifest_path))

    def test_is_helper_installed_reads_windows_registry_manifest(self) -> None:
        fake_winreg = _FakeWinreg()
        with tempfile.TemporaryDirectory() as tmpdir:
            data_root = Path(tmpdir) / "data"
            manifest = data_root / "native_messaging" / "chrome" / "com.lexishift.helper.json"
            host = data_root / "helper" / "native_host" / "lexishift_native_host.exe"
            host.parent.mkdir(parents=True, exist_ok=True)
            manifest.parent.mkdir(parents=True, exist_ok=True)
            host.write_bytes(b"host")
            manifest.write_text(
                (
                    "{\n"
                    '  "allowed_origins": ["chrome-extension://abcdefghijklmnopabcdefghijklmnop/"],\n'
                    f'  "path": "{host}"\n'
                    "}\n"
                ),
                encoding="utf-8",
            )
            fake_winreg.values[
                helper_installer.WINDOWS_NATIVE_MESSAGING_REGISTRY_KEYS["chrome"]
            ] = str(manifest)

            with (
                mock.patch.object(helper_installer.sys, "platform", "win32"),
                mock.patch.dict(sys.modules, {"winreg": fake_winreg}),
            ):
                installed = helper_installer.is_helper_installed(
                    "abcdefghijklmnopabcdefghijklmnop",
                    browser="chrome",
                )

        self.assertTrue(installed)


if __name__ == "__main__":
    unittest.main()
