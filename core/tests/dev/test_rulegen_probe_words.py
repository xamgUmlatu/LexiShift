from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
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
        self.assertIn("--german-targets", result.stdout)
        self.assertIn("--translation-dict-en-es", result.stdout)
        self.assertIn("--translation-dict-es-en-reverse", result.stdout)
        self.assertIn("--translation-dict-en-de", result.stdout)
        self.assertIn("--translation-dict-en-de-reverse", result.stdout)
        self.assertIn("--kaikki-policy-live-demotion", result.stdout)
        self.assertIn("--kaikki-policy-register-demotion", result.stdout)
        self.assertIn("--enable-exact-gloss-demotion", result.stdout)
        self.assertIn("--enable-source-frequency-prior", result.stdout)
        self.assertIn("--cleaner-later-competition-penalty", result.stdout)
        self.assertIn("--source-frequency-db-en-de", result.stdout)
        self.assertIn("Installed language packs are used by default.", result.stdout)
        self.assertIn("Installed frequency", result.stdout)
        self.assertIn("packs are used by default", result.stdout)
        self.assertNotIn("--freedict-es-en", result.stdout)
        self.assertNotIn("--freedict-en-es-reverse", result.stdout)
        self.assertNotIn("--freedict-de-en", result.stdout)

    def test_empty_target_run_writes_json_payload_without_resources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "probe.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--spanish-targets",
                    "",
                    "--german-targets",
                    "",
                    "--japanese-targets",
                    "",
                    "--json-output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pairs"]["en-es"], {})
            self.assertEqual(payload["pairs"]["en-de"], {})
            self.assertEqual(payload["pairs"]["en-ja"], {})
            self.assertEqual(
                payload["resources"],
                {
                    "en-es": {},
                    "en-de": {},
                    "en-ja": {},
                },
            )
            self.assertIn("Rulegen Probe", result.stdout)
            self.assertIn("resource_identity:", result.stdout)
            self.assertIn("JSON output written:", result.stdout)


if __name__ == "__main__":
    unittest.main()
