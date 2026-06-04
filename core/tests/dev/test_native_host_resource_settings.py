from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid


REPO_ROOT = Path(__file__).resolve().parents[3]
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"
GUI_ACTIVATION_MODULE = REPO_ROOT / "core" / "lexishift_core" / "helper" / "gui_activation.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNativeHostResourceSettings(unittest.TestCase):
    def test_open_resource_settings_launches_dev_gui_entrypoint(self) -> None:
        module = _load_module("lexishift_native_host_resource_settings_test", NATIVE_HOST_SCRIPT)

        with (
            patch.dict(
                module.os.environ,
                {"LEXISHIFT_GUI_ENTRY": "", "LEXISHIFT_GUI_PYTHON": ""},
            ),
            patch.object(module.sys, "platform", "linux"),
            patch.object(module.subprocess, "Popen") as popen,
            patch.object(module, "activate_gui_resource_settings", return_value=False),
            patch.object(module, "_native_host_log_line") as log_line,
        ):
            response = module._open_resource_settings({"pair": "en-es"})

        popen.assert_called_once()
        args, kwargs = popen.call_args
        self.assertEqual(
            args[0],
            [
                sys.executable,
                str(REPO_ROOT / "apps" / "gui" / "src" / "main.py"),
                module.OPEN_RESOURCE_SETTINGS_FLAG,
                module.RESOURCE_PAIR_FLAG,
                "en-es",
            ],
        )
        self.assertIs(kwargs["close_fds"], True)
        self.assertIsInstance(kwargs["env"], dict)
        self.assertEqual(
            kwargs["env"]["LEXISHIFT_STARTUP_SESSION_ID"],
            response["startup_session_id"],
        )
        self.assertEqual(kwargs["env"]["LEXISHIFT_STARTUP_SOURCE"], "native_host_resource_settings")
        self.assertEqual(kwargs["env"]["LEXISHIFT_STARTUP_LAUNCH_MODE"], "dev_gui_entry")
        self.assertEqual(kwargs["env"]["LEXISHIFT_STARTUP_RESOURCE_PAIR"], "en-es")
        self.assertIn("LEXISHIFT_STARTUP_REQUESTED_AT", kwargs["env"])
        self.assertEqual(response["opened"], True)
        self.assertEqual(response["target"], "resource_settings")
        self.assertEqual(response["launch_mode"], "dev_gui_entry")
        self.assertEqual(response["launch_command_class"], "python_gui_entry")
        self.assertIn("startup_session_id", response)
        self.assertGreaterEqual(response["activation_duration_ms"], 0)
        messages = [call.args[0] for call in log_line.call_args_list]
        self.assertTrue(
            any("resource_settings_request_received" in message for message in messages)
        )
        self.assertTrue(
            any("resource_settings_activation_result" in message for message in messages)
        )
        self.assertTrue(any("opened_resource_settings" in message for message in messages))
        self.assertTrue(any("pair=en-es" in message for message in messages))

    def test_open_resource_settings_reuses_existing_gui_when_available(self) -> None:
        module = _load_module(
            "lexishift_native_host_resource_settings_existing_gui_test",
            NATIVE_HOST_SCRIPT,
        )

        with (
            patch.object(module, "activate_gui_resource_settings", return_value=True) as activate,
            patch.object(module.subprocess, "Popen") as popen,
            patch.object(module, "_native_host_log_line") as log_line,
        ):
            response = module._open_resource_settings({"pair": "EN-ES"})

        popen.assert_not_called()
        self.assertEqual(response["opened"], True)
        self.assertEqual(response["target"], "resource_settings")
        self.assertEqual(response["launch_mode"], "existing_gui")
        self.assertIn("startup_session_id", response)
        self.assertGreaterEqual(response["activation_duration_ms"], 0)
        _activate_args, activate_kwargs = activate.call_args
        self.assertEqual(activate_kwargs["pair"], "EN-ES")
        self.assertEqual(activate_kwargs["session_id"], response["startup_session_id"])
        messages = [call.args[0] for call in log_line.call_args_list]
        self.assertTrue(any("mode=existing_gui" in message for message in messages))
        self.assertTrue(any("pair=EN-ES" in message for message in messages))

    def test_macos_resource_settings_prefers_installed_app_over_dev_entry(self) -> None:
        module = _load_module(
            "lexishift_native_host_resource_settings_installed_macos_test",
            NATIVE_HOST_SCRIPT,
        )
        from lexishift_core.helper import gui_app_launch

        with (
            patch.object(module.sys, "platform", "darwin"),
            patch.object(
                gui_app_launch,
                "_resolve_macos_bundle_from_host_script",
                return_value=None,
            ),
            patch.object(
                gui_app_launch,
                "_resolve_macos_installed_bundle",
                return_value=Path("/Applications/LexiShift.app"),
            ),
        ):
            command, launch_mode = module._resource_settings_launch_command({"pair": "en-es"})

        self.assertEqual(launch_mode, "macos_installed_bundle")
        self.assertEqual(command[0], "open")
        self.assertEqual(command[1], "/Applications/LexiShift.app")
        self.assertNotIn("main.py", " ".join(command))
        self.assertIn(module.OPEN_RESOURCE_SETTINGS_FLAG, command)
        self.assertIn(module.RESOURCE_PAIR_FLAG, command)
        self.assertIn("en-es", command)

    def test_resource_settings_activation_message_carries_pair(self) -> None:
        module = _load_module("lexishift_gui_activation_message_test", GUI_ACTIVATION_MODULE)

        self.assertEqual(
            module.resource_settings_activation_message("EN-ES"),
            "OPEN_SETTINGS:resources|pair=en-es",
        )
        self.assertEqual(
            module.resource_settings_activation_message("EN-ES", session_id="session-1"),
            "OPEN_SETTINGS:resources|pair=en-es|session=session-1",
        )
        self.assertEqual(
            module.resource_settings_activation_message(),
            "OPEN_SETTINGS:resources",
        )

    def test_local_activation_message_writes_to_existing_qt_server(self) -> None:
        module = _load_module("lexishift_gui_activation_socket_test", GUI_ACTIVATION_MODULE)
        from PySide6.QtNetwork import QLocalServer

        server_name = f"LexiShiftTest_{uuid.uuid4().hex}"
        server = QLocalServer()
        QLocalServer.removeServer(server_name)
        self.assertTrue(server.listen(server_name))

        try:
            message = "OPEN_SETTINGS:resources|pair=en-es"
            self.assertTrue(module.send_local_activation_message(server_name, message))
            if not server.hasPendingConnections():
                server.waitForNewConnection(1000)
            client = server.nextPendingConnection()
            self.assertIsNotNone(client)
            client.waitForReadyRead(1000)
            self.assertEqual(bytes(client.readAll()).decode("utf-8"), message)
            client.disconnectFromServer()
        finally:
            server.close()
            QLocalServer.removeServer(server_name)

    def test_macos_resource_settings_launch_does_not_force_new_instance(self) -> None:
        module = _load_module(
            "lexishift_native_host_resource_settings_macos_launch_test",
            NATIVE_HOST_SCRIPT,
        )
        from lexishift_core.helper import gui_app_launch

        with (
            patch.object(module, "PROJECT_ROOT", Path("/tmp/lexishift-no-dev-entry")),
            patch.object(module.sys, "platform", "darwin"),
            patch.object(
                gui_app_launch,
                "_resolve_macos_bundle_from_host_script",
                return_value=Path("/Applications/LexiShift.app"),
            ),
        ):
            command, launch_mode = module._resource_settings_launch_command({"pair": "en-es"})

        self.assertEqual(launch_mode, "macos_host_bundle")
        self.assertEqual(command[0], "open")
        self.assertNotIn("-n", command)
        self.assertIn("/Applications/LexiShift.app", command)
        self.assertIn(module.OPEN_RESOURCE_SETTINGS_FLAG, command)
        self.assertIn(module.RESOURCE_PAIR_FLAG, command)
        self.assertIn("en-es", command)


if __name__ == "__main__":
    unittest.main()
