from __future__ import annotations

from pathlib import Path
import json
import stat
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
if str(GUI_SRC) not in sys.path:
    sys.path.insert(0, str(GUI_SRC))

import helper_installer  # noqa: E402
from helper_connection_models import (  # noqa: E402
    REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
    REPAIR_REASON_BUNDLED_HOST_STALE,
    REPAIR_REASON_MANIFEST_UNREADABLE,
    REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,
)


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
    def test_native_host_protocol_probe_accepts_valid_hello_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            host = Path(tmpdir) / "native-host"
            host.write_text(
                "#!/usr/bin/env python3\n"
                "import json, struct, sys\n"
                "size = struct.unpack('<I', sys.stdin.buffer.read(4))[0]\n"
                "request = json.loads(sys.stdin.buffer.read(size))\n"
                "response = json.dumps({'id': request['id'], 'ok': True, "
                "'data': {'protocol_version': 1}}).encode()\n"
                "sys.stdout.buffer.write(struct.pack('<I', len(response)) + response)\n",
                encoding="utf-8",
            )
            host.chmod(host.stat().st_mode | stat.S_IEXEC)

            ok, detail = helper_installer._probe_native_host(host)

        self.assertTrue(ok, detail)

    def test_build_manifest_supports_multiple_allowed_origins(self) -> None:
        payload = helper_installer.build_manifest(
            host_path=Path("/tmp/lexishift_native_host.py"),
            extension_ids=[
                "abcdefghijklmnopabcdefghijklmnop",
                "qrstuvwxyzabcdefqrstuvwxyzabcdef",
                "abcdefghijklmnopabcdefghijklmnop",
            ],
        )

        self.assertEqual(
            payload["allowed_origins"],
            [
                "chrome-extension://abcdefghijklmnopabcdefghijklmnop/",
                "chrome-extension://qrstuvwxyzabcdefqrstuvwxyzabcdef/",
            ],
        )

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

    def test_default_host_script_prefers_bundled_macos_host_exe_when_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app_root = Path(tmpdir) / "LexiShift.app" / "Contents"
            main_exe = app_root / "MacOS" / "LexiShift"
            host_exe = app_root / "MacOS" / "lexishift_native_host"
            main_exe.parent.mkdir(parents=True, exist_ok=True)
            main_exe.write_bytes(b"main")
            host_exe.write_bytes(b"host")

            with (
                mock.patch.object(helper_installer.sys, "platform", "darwin"),
                mock.patch.object(helper_installer.sys, "frozen", True, create=True),
                mock.patch.object(helper_installer.sys, "executable", str(main_exe)),
            ):
                resolved = helper_installer.default_host_script()

        self.assertEqual(resolved.resolve(), host_exe.resolve())

    def test_macos_legacy_bundled_script_manifest_requires_executable_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            old_host = root / "LexiShift.app" / "Contents" / "Resources" / "host.py"
            new_host = root / "LexiShift.app" / "Contents" / "MacOS" / "lexishift_native_host"
            manifest = root / "com.lexishift.helper.json"
            old_host.parent.mkdir(parents=True, exist_ok=True)
            new_host.parent.mkdir(parents=True, exist_ok=True)
            old_host.write_text("legacy\n", encoding="utf-8")
            new_host.write_bytes(b"native")
            manifest.write_text(
                json.dumps(
                    {
                        "path": str(old_host),
                        "allowed_origins": ["chrome-extension://abcdefghijklmnopabcdefghijklmnop/"],
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(helper_installer.sys, "platform", "darwin"),
                mock.patch.object(helper_installer.sys, "frozen", True, create=True),
                mock.patch.object(helper_installer, "manifest_path", return_value=manifest),
                mock.patch.object(helper_installer, "default_host_script", return_value=new_host),
                mock.patch.object(helper_installer, "_is_bundled_path", return_value=True),
            ):
                status = helper_installer.inspect_helper_installation(
                    browser="chrome",
                    expected_extension_ids=["abcdefghijklmnopabcdefghijklmnop"],
                )

        self.assertEqual(status.state, helper_installer.HELPER_STATE_NEEDS_REPAIR)
        self.assertIn(REPAIR_REASON_BUNDLED_HOST_STALE, status.repair_reasons)

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

    def test_inspect_helper_installation_reports_missing_allowed_origin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "com.lexishift.helper.json"
            host = root / "lexishift_native_host.py"
            host.write_text("print('host')\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "allowed_origins": [
                            "chrome-extension://abcdefghijklmnopabcdefghijklmnop/",
                        ],
                        "path": str(host),
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(helper_installer, "manifest_path", return_value=manifest):
                status = helper_installer.inspect_helper_installation(
                    browser="chrome",
                    expected_extension_ids=[
                        "abcdefghijklmnopabcdefghijklmnop",
                        "qrstuvwxyzabcdefqrstuvwxyzabcdef",
                    ],
                )

        self.assertEqual(status.state, helper_installer.HELPER_STATE_NEEDS_REPAIR)
        self.assertEqual(
            status.missing_extension_ids,
            ("qrstuvwxyzabcdefqrstuvwxyzabcdef",),
        )
        self.assertEqual(status.unexpected_extension_ids, ())
        self.assertEqual(status.repair_reasons, (REPAIR_REASON_ALLOWED_ORIGINS_MISSING,))

    def test_inspect_helper_installation_reports_stale_bundled_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_root = root / "data"
            bundle_root = root / "bundle"
            installed_host = data_root / "helper" / "lexishift_native_host.py"
            installed_core = data_root / "helper" / "lexishift_core"
            bundled_host = bundle_root / "resources" / "helper" / "lexishift_native_host.py"
            bundled_core = bundle_root / "resources" / "helper" / "lexishift_core"
            manifest = root / "com.lexishift.helper.json"

            installed_host.parent.mkdir(parents=True, exist_ok=True)
            installed_core.mkdir(parents=True, exist_ok=True)
            bundled_host.parent.mkdir(parents=True, exist_ok=True)
            bundled_core.mkdir(parents=True, exist_ok=True)

            installed_host.write_text("print('old host')\n", encoding="utf-8")
            bundled_host.write_text("print('new host')\n", encoding="utf-8")
            (installed_core / "__init__.py").write_text("old = 1\n", encoding="utf-8")
            (bundled_core / "__init__.py").write_text("new = 1\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "allowed_origins": [
                            "chrome-extension://abcdefghijklmnopabcdefghijklmnop/",
                        ],
                        "path": str(installed_host),
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(helper_installer, "_helper_data_root", return_value=data_root),
                mock.patch.object(helper_installer, "manifest_path", return_value=manifest),
                mock.patch.object(
                    helper_installer, "default_host_script", return_value=bundled_host
                ),
                mock.patch.object(
                    helper_installer,
                    "_is_bundled_path",
                    side_effect=lambda path: Path(path) == bundled_host,
                ),
            ):
                status = helper_installer.inspect_helper_installation(
                    browser="chrome",
                    expected_extension_ids=["abcdefghijklmnopabcdefghijklmnop"],
                )

        self.assertEqual(status.state, helper_installer.HELPER_STATE_NEEDS_REPAIR)
        self.assertIn("stale", status.message.lower())
        self.assertIn(REPAIR_REASON_BUNDLED_HOST_STALE, status.repair_reasons)

    def test_install_helper_wraps_workspace_host_with_pinned_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_root = root / "data"
            manifest = root / "com.lexishift.helper.json"
            repo_root = root / "repo"
            host = repo_root / "scripts" / "helper" / "lexishift_native_host.py"
            interpreter = repo_root / ".venv" / "bin" / "python"
            host.parent.mkdir(parents=True, exist_ok=True)
            interpreter.parent.mkdir(parents=True, exist_ok=True)
            host.write_text("print('host')\n", encoding="utf-8")
            interpreter.write_text("", encoding="utf-8")

            with (
                mock.patch.object(helper_installer, "_helper_data_root", return_value=data_root),
                mock.patch.object(helper_installer, "manifest_path", return_value=manifest),
                mock.patch.object(helper_installer, "workspace_host_script", return_value=host),
                mock.patch.object(
                    helper_installer,
                    "_resolve_workspace_python",
                    return_value=interpreter,
                ),
            ):
                result = helper_installer.install_helper(
                    extension_id="abcdefghijklmnopabcdefghijklmnop",
                    browser="chrome",
                    host_path=host,
                )
                wrapper_path = helper_installer.workspace_host_wrapper_path()

            self.assertTrue(result.installed)
            self.assertTrue(wrapper_path.exists())
            self.assertEqual(
                wrapper_path.read_text(encoding="utf-8"),
                helper_installer._build_workspace_wrapper_script(host, interpreter),
            )
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["path"], str(wrapper_path))

    def test_inspect_helper_installation_flags_legacy_direct_workspace_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_root = root / "data"
            manifest = root / "com.lexishift.helper.json"
            repo_root = root / "repo"
            host = repo_root / "scripts" / "helper" / "lexishift_native_host.py"
            host.parent.mkdir(parents=True, exist_ok=True)
            host.write_text("print('host')\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "allowed_origins": [
                            "chrome-extension://abcdefghijklmnopabcdefghijklmnop/",
                        ],
                        "path": str(host),
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(helper_installer, "_helper_data_root", return_value=data_root),
                mock.patch.object(helper_installer, "manifest_path", return_value=manifest),
                mock.patch.object(helper_installer, "workspace_host_script", return_value=host),
            ):
                status = helper_installer.inspect_helper_installation(
                    browser="chrome",
                    expected_extension_ids=["abcdefghijklmnopabcdefghijklmnop"],
                )

        self.assertEqual(status.state, helper_installer.HELPER_STATE_NEEDS_REPAIR)
        self.assertIn("legacy direct script path", status.message.lower())
        self.assertEqual(
            status.repair_reasons,
            (REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,),
        )

    def test_inspect_helper_installation_accepts_workspace_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_root = root / "data"
            manifest = root / "com.lexishift.helper.json"
            repo_root = root / "repo"
            host = repo_root / "scripts" / "helper" / "lexishift_native_host.py"
            interpreter = repo_root / ".venv" / "bin" / "python"
            host.parent.mkdir(parents=True, exist_ok=True)
            interpreter.parent.mkdir(parents=True, exist_ok=True)
            host.write_text("print('host')\n", encoding="utf-8")
            interpreter.write_text("", encoding="utf-8")

            with (
                mock.patch.object(helper_installer, "_helper_data_root", return_value=data_root),
                mock.patch.object(helper_installer, "manifest_path", return_value=manifest),
                mock.patch.object(helper_installer, "workspace_host_script", return_value=host),
                mock.patch.object(
                    helper_installer,
                    "_resolve_workspace_python",
                    return_value=interpreter,
                ),
            ):
                wrapper_path = helper_installer.workspace_host_wrapper_path()
                wrapper_path.parent.mkdir(parents=True, exist_ok=True)
                wrapper_path.write_text(
                    helper_installer._build_workspace_wrapper_script(host, interpreter),
                    encoding="utf-8",
                )
                manifest.write_text(
                    json.dumps(
                        {
                            "allowed_origins": [
                                "chrome-extension://abcdefghijklmnopabcdefghijklmnop/",
                            ],
                            "path": str(wrapper_path),
                        }
                    ),
                    encoding="utf-8",
                )
                status = helper_installer.inspect_helper_installation(
                    browser="chrome",
                    expected_extension_ids=["abcdefghijklmnopabcdefghijklmnop"],
                )

        self.assertEqual(status.state, helper_installer.HELPER_STATE_CONFIGURED)
        self.assertEqual(status.host_mode, helper_installer.HOST_MODE_WORKSPACE)

    def test_inspect_helper_installation_tracks_unexpected_allowed_origins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "com.lexishift.helper.json"
            host = root / "lexishift_native_host.py"
            host.write_text("print('host')\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "allowed_origins": [
                            "chrome-extension://abcdefghijklmnopabcdefghijklmnop/",
                            "chrome-extension://manualmanualmanualmanualmanualmanua/",
                        ],
                        "path": str(host),
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(helper_installer, "manifest_path", return_value=manifest):
                status = helper_installer.inspect_helper_installation(
                    browser="chrome",
                    expected_extension_ids=["abcdefghijklmnopabcdefghijklmnop"],
                )

        self.assertEqual(status.state, helper_installer.HELPER_STATE_CONFIGURED)
        self.assertEqual(
            status.unexpected_extension_ids,
            ("manualmanualmanualmanualmanualmanua",),
        )

    def test_inspect_helper_installation_marks_unreadable_manifest_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "com.lexishift.helper.json"
            manifest.write_text("{not-json", encoding="utf-8")

            with mock.patch.object(helper_installer, "manifest_path", return_value=manifest):
                status = helper_installer.inspect_helper_installation(browser="chrome")

        self.assertEqual(status.state, helper_installer.HELPER_STATE_NEEDS_REPAIR)
        self.assertEqual(status.repair_reasons, (REPAIR_REASON_MANIFEST_UNREADABLE,))


if __name__ == "__main__":
    unittest.main()
