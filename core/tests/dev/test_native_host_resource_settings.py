from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"


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
            patch.object(module.subprocess, "Popen") as popen,
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
            ],
        )
        self.assertIs(kwargs["close_fds"], True)
        self.assertIsInstance(kwargs["env"], dict)
        self.assertEqual(response["opened"], True)
        self.assertEqual(response["target"], "resource_settings")
        self.assertEqual(response["launch_mode"], "dev_gui_entry")
        log_line.assert_called_once()
        self.assertIn("pair=en-es", log_line.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
