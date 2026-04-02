from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "testing" / "rulegen_probe_words.py"


class TestRulegenProbeWords(unittest.TestCase):
    def test_help_uses_generic_translation_dict_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--translation-dict-en-es", result.stdout)
        self.assertIn("--translation-dict-es-en-reverse", result.stdout)
        self.assertNotIn("--freedict-es-en", result.stdout)
        self.assertNotIn("--freedict-en-es-reverse", result.stdout)


if __name__ == "__main__":
    unittest.main()
