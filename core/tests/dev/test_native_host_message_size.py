from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"
HELPER_SCRIPT_DIR = NATIVE_HOST_SCRIPT.parent
if str(HELPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_SCRIPT_DIR))


def _load_native_host_module():
    spec = importlib.util.spec_from_file_location(
        "lexishift_native_host_message_size_test",
        NATIVE_HOST_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNativeHostMessageSize(unittest.TestCase):
    def test_oversized_response_is_replaced_with_framed_actionable_error(self) -> None:
        module = _load_native_host_module()
        output = io.BytesIO()

        with (
            mock.patch.object(module.sys, "stdout", SimpleNamespace(buffer=output)),
            mock.patch.object(module, "_native_host_log_line") as log_line,
        ):
            module._write_message(
                {
                    "id": "large-preview",
                    "ok": True,
                    "data": {"payload": "x" * module.native_messaging.NATIVE_MESSAGE_MAX_BYTES},
                    "error": None,
                }
            )

        framed = output.getvalue()
        response_length = struct.unpack("<I", framed[:4])[0]
        response = json.loads(framed[4 : 4 + response_length].decode("utf-8"))
        self.assertLessEqual(response_length, module.native_messaging.NATIVE_MESSAGE_MAX_BYTES)
        self.assertEqual(response["id"], "large-preview")
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "response_too_large")
        self.assertIn("too large", response["error"]["message"])
        log_line.assert_called_once()


if __name__ == "__main__":
    unittest.main()
