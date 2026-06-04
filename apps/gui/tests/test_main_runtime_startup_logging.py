from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from main_runtime import (
    STARTUP_LAUNCH_MODE_ENV,
    STARTUP_REQUESTED_AT_ENV,
    STARTUP_RESOURCE_PAIR_ENV,
    STARTUP_SESSION_ID_ENV,
    STARTUP_SOURCE_ENV,
    StartupLogger,
    resource_settings_activation_message,
    startup_session_from_activation_message,
)


class TestMainRuntimeStartupLogging(unittest.TestCase):
    def test_startup_logger_writes_session_metadata(self) -> None:
        requested_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "startup.log"
            with patch.dict(
                "os.environ",
                {
                    STARTUP_SESSION_ID_ENV: "session-abc",
                    STARTUP_REQUESTED_AT_ENV: requested_at,
                    STARTUP_SOURCE_ENV: "native_host_resource_settings",
                    STARTUP_LAUNCH_MODE_ENV: "macos_installed_bundle",
                    STARTUP_RESOURCE_PAIR_ENV: "en-es",
                },
            ):
                logger = StartupLogger(
                    [log_path],
                    start_time=time.perf_counter() - 0.05,
                    argv=["main.py", "--open-resource-settings"],
                )
                logger.log("unit checkpoint")

            text = log_path.read_text(encoding="utf-8")
            self.assertIn("[startup] unit checkpoint", text)
            self.assertIn("session=session-abc", text)
            self.assertIn("argv_mode=resource_settings", text)
            self.assertIn("source=native_host_resource_settings", text)
            self.assertIn("launch_mode=macos_installed_bundle", text)
            self.assertIn("resource_pair=en-es", text)
            self.assertIn("since_request_ms=", text)

    def test_activation_message_carries_optional_session(self) -> None:
        message = resource_settings_activation_message("EN-ES", session_id="session-abc")

        self.assertEqual(
            message,
            "OPEN_SETTINGS:resources|pair=en-es|session=session-abc",
        )
        self.assertEqual(startup_session_from_activation_message(message), "session-abc")
        self.assertIsNone(startup_session_from_activation_message("ACTIVATE"))


if __name__ == "__main__":
    unittest.main()
