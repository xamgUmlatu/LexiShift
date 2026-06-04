from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
MEASURE_SCRIPT = REPO_ROOT / "scripts" / "dev" / "packaged_gui_startup_measure.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "packaged_gui_startup_measure_test", MEASURE_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {MEASURE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPackagedGuiStartupMeasure(unittest.TestCase):
    def test_build_launch_command_modes(self) -> None:
        module = _load_module()
        app = Path("/Applications/LexiShift.app")

        self.assertEqual(
            module._build_launch_command(app, launch_mode="open", pair="en-es"),
            [
                "open",
                "/Applications/LexiShift.app",
                "--args",
                "--open-resource-settings",
                "--resource-pair",
                "en-es",
            ],
        )
        self.assertEqual(
            module._build_launch_command(app, launch_mode="bundle-id", pair="en-es"),
            [
                "open",
                "-b",
                "com.lexishift.app",
                "--args",
                "--open-resource-settings",
                "--resource-pair",
                "en-es",
            ],
        )
        self.assertEqual(
            module._build_launch_command(app, launch_mode="direct", pair="en-es"),
            [
                "/Applications/LexiShift.app/Contents/MacOS/LexiShift",
                "--open-resource-settings",
                "--resource-pair",
                "en-es",
            ],
        )

    def test_wait_for_log_line_matches_session_and_marker(self) -> None:
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "startup.log"
            log_path.write_text(
                "\n".join(
                    [
                        "[startup] window shown session=other",
                        "[startup] window shown session=session-1 since_request_ms=123.4",
                    ]
                ),
                encoding="utf-8",
            )

            line = module._wait_for_log_line(
                startup_log_path=log_path,
                session_id="session-1",
                marker="window shown",
                timeout_seconds=0.1,
            )

        self.assertIsNotNone(line)
        self.assertIn("since_request_ms=123.4", line)
        self.assertEqual(module._extract_float(module.SINCE_REQUEST_RE, line), 123.4)

    def test_activation_summary_uses_observed_time(self) -> None:
        module = _load_module()

        summary = module._summary(
            [
                {
                    "status": "ok",
                    "launch_mode": "activation",
                    "observed_elapsed_ms": 150.0,
                    "since_request_ms": 50000.0,
                }
            ]
        )

        self.assertEqual(summary["median_ms"], 150.0)
        self.assertIsNone(summary["pre_entry"])

    def test_cold_launch_summary_reports_pre_entry_split(self) -> None:
        module = _load_module()

        summary = module._summary(
            [
                {
                    "status": "ok",
                    "launch_mode": "open",
                    "observed_elapsed_ms": 1000.0,
                    "since_request_ms": 950.0,
                    "startup_total_ms": 300.0,
                    "pre_entry_ms": 650.0,
                }
            ]
        )

        self.assertEqual(summary["median_ms"], 950.0)
        self.assertEqual(summary["pre_entry"]["median_ms"], 650.0)
        self.assertEqual(summary["process_entry_to_window"]["median_ms"], 300.0)


if __name__ == "__main__":
    unittest.main()
