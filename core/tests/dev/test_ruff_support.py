from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ruff_support import resolve_ruff  # noqa: E402


class TestRuffSupport(unittest.TestCase):
    @mock.patch("ruff_support.shutil.which", return_value="/usr/local/bin/ruff")
    @mock.patch("ruff_support.subprocess.run")
    def test_resolve_ruff_prefers_python_module(
        self, run_mock: mock.Mock, _which_mock: mock.Mock
    ) -> None:
        run_mock.return_value = mock.Mock(returncode=0)

        resolution = resolve_ruff()

        self.assertTrue(resolution.available)
        self.assertEqual(resolution.source, "python-module")
        self.assertEqual(resolution.command("check"), [sys.executable, "-m", "ruff", "check"])
        run_mock.assert_called_once_with(
            [sys.executable, "-m", "ruff", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )

    @mock.patch("ruff_support.shutil.which", return_value="/usr/local/bin/ruff")
    @mock.patch("ruff_support.subprocess.run")
    def test_resolve_ruff_falls_back_to_path_binary(
        self, run_mock: mock.Mock, _which_mock: mock.Mock
    ) -> None:
        run_mock.side_effect = [
            mock.Mock(returncode=1),
            mock.Mock(returncode=0),
        ]

        resolution = resolve_ruff()

        self.assertTrue(resolution.available)
        self.assertEqual(resolution.source, "path")
        self.assertEqual(
            resolution.command("format", "--check"), ["/usr/local/bin/ruff", "format", "--check"]
        )
        self.assertEqual(run_mock.call_count, 2)

    @mock.patch("ruff_support.shutil.which", return_value=None)
    @mock.patch("ruff_support.subprocess.run")
    def test_resolve_ruff_reports_unavailable_when_no_invocation_works(
        self,
        run_mock: mock.Mock,
        _which_mock: mock.Mock,
    ) -> None:
        run_mock.return_value = mock.Mock(returncode=1)

        resolution = resolve_ruff()

        self.assertFalse(resolution.available)
        self.assertEqual(resolution.source, "unavailable")
        self.assertIn("ruff", resolution.detail)
        with self.assertRaises(RuntimeError):
            resolution.command("check")


if __name__ == "__main__":
    unittest.main()
