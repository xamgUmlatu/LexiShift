from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_helper.py"


class TestHelperFrequencyEntrypoints(unittest.TestCase):
    def test_helper_cli_subcommands_describe_installed_frequency_pack_defaults(self) -> None:
        commands = (
            "run_rulegen",
            "init_srs_set",
            "refresh_srs_set",
            "preview_srs_admission",
            "plan_srs_rebalance",
            "apply_srs_rebalance",
        )

        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, str(HELPER_SCRIPT), command, "--help"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertIn("--set-source-db", result.stdout)
                normalized_help = " ".join(result.stdout.split())
                self.assertIn(
                    "Installed frequency packs are used by default.",
                    normalized_help,
                )
                self.assertIn(
                    "manual frequency SQLite override",
                    normalized_help,
                )


if __name__ == "__main__":
    unittest.main()
