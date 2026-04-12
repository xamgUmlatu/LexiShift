from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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

    def test_native_host_serves_semantic_inventory_payload(self) -> None:
        module = _load_module("lexishift_native_host_semantic_inventory_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = {
                "schema_version": 1,
                "pair": "en-es",
                "profile_id": "default",
                "generated_at": "2026-04-13T00:00:00Z",
                "triggers": {},
                "senses": {},
                "competition_sets": {},
                "phrase_sets": {},
            }
            paths.semantic_inventory_path("en-es").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "get_semantic_inventory",
                    {"pair": "en-es", "profile_id": "default"},
                )

        self.assertEqual(response["pair"], "en-es")
        self.assertEqual(response["schema_version"], 1)

    def test_native_host_routes_semantic_admit_batch(self) -> None:
        module = _load_module("lexishift_native_host_semantic_admit_batch_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "semantic_admit_batch",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                        "fallback_policy": "abstain_on_unavailable",
                        "matches": [
                            {
                                "match_id": "m1",
                                "source_phrase": "bank",
                                "context_text": "You can bank on her support.",
                                "match_start": 8,
                                "match_end": 12,
                                "semantic_admission": {
                                    "schema_version": 1,
                                    "status": "ready",
                                    "trigger_id": "en-es:trigger:bank",
                                    "sense_id": "sense:banco",
                                    "competition_set_id": "comp:bank",
                                },
                            }
                        ],
                    },
                )

        self.assertEqual(response["pair"], "en-es")
        self.assertEqual(response["decisions"][0]["decision_source"], "fallback_policy")
        self.assertIn("semantic_inventory_missing", response["decisions"][0]["reason_codes"])


if __name__ == "__main__":
    unittest.main()
