from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "testing" / "rulegen_benchmark.py"


class TestRulegenBenchmarkCli(unittest.TestCase):
    def test_help_describes_installed_pack_defaults(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--translation-dict-en-de", result.stdout)
        self.assertIn("--translation-dict-en-es", result.stdout)
        self.assertIn("--translation-dict-es-en", result.stdout)
        self.assertRegex(
            result.stdout,
            r"Installed language packs are used by\s+default\.",
        )
        self.assertRegex(
            result.stdout,
            r"Installed frequency\s+packs are used by\s+default\.",
        )
        self.assertNotIn("wiktionary-de-en.sqlite", result.stdout)
        self.assertNotIn("deu-eng.sqlite", result.stdout)
        self.assertNotIn("wiktionary-es-en.sqlite", result.stdout)
        self.assertNotIn("spa-eng.sqlite", result.stdout)
        self.assertNotIn("eng-spa.sqlite", result.stdout)
        self.assertNotIn(".tei", result.stdout)


if __name__ == "__main__":
    unittest.main()
