from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lexishift_core.helper.paths import build_helper_paths


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_helper.py"
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestHelperTranslationDictEntrypoints(unittest.TestCase):
    def test_helper_cli_uses_generic_translation_dict_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HELPER_SCRIPT), "run_rulegen", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        help_text = result.stdout
        self.assertIn("--translation-dict", help_text)
        self.assertNotIn("--freedict-de-en", help_text)

    def test_native_host_ignores_legacy_translation_dict_payload_key(self) -> None:
        module = _load_module("lexishift_native_host_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            legacy_path = Path(tmp) / "legacy.sqlite"
            resolved_jmdict, resolved_translation_dict, resolved_frequency_db = (
                module._resolve_pair_resource_paths(
                    paths,
                    pair="en-de",
                    payload={"freedict_de_en_path": str(legacy_path)},
                )
            )

        self.assertIsNone(resolved_jmdict)
        self.assertIsNotNone(resolved_translation_dict)
        self.assertIsNotNone(resolved_frequency_db)
        self.assertNotEqual(resolved_translation_dict, legacy_path)
        self.assertTrue(str(resolved_translation_dict).endswith("freedict-de-en.sqlite"))


if __name__ == "__main__":
    unittest.main()
