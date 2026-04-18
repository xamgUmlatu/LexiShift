from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
HELPER_DIR = REPO_ROOT / "scripts" / "helper"
HELPER_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_helper.py"
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(HELPER_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_DIR))

from lexishift_core.helper.engine import get_srs_runtime_diagnostics  # noqa: E402
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestFrequencyRuntimeContracts(unittest.TestCase):
    def test_helper_and_native_host_resolve_manifest_backed_frequency_defaults(self) -> None:
        helper_module = _load_module("lexishift_helper_frequency_test", HELPER_SCRIPT)
        native_module = _load_module("lexishift_native_host_frequency_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            artifact = self._write_manifest_backed_frequency_pack(
                paths.frequency_packs_dir,
                pack_id="freq-en-coca",
                provider="wordfrequency",
            )

            helper_resolved = helper_module._resolve_pair_resource_paths(
                paths,
                pair="en-en",
                jmdict_arg=None,
                translation_dict_arg=None,
                set_source_db_arg=None,
            )[2]
            native_resolved = native_module._resolve_pair_resource_paths(
                paths,
                pair="en-en",
                payload={},
            )[2]

        self.assertEqual(helper_resolved, artifact)
        self.assertEqual(native_resolved, artifact)

    def test_helper_and_native_host_resolve_legacy_frequency_defaults_without_manifest(
        self,
    ) -> None:
        helper_module = _load_module("lexishift_helper_frequency_legacy_test", HELPER_SCRIPT)
        native_module = _load_module(
            "lexishift_native_host_frequency_legacy_test", NATIVE_HOST_SCRIPT
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            legacy = paths.frequency_packs_dir / "freq-en-coca.sqlite"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_bytes(b"SQLite format 3\x00")

            helper_resolved = helper_module._resolve_pair_resource_paths(
                paths,
                pair="en-en",
                jmdict_arg=None,
                translation_dict_arg=None,
                set_source_db_arg=None,
            )[2]
            native_resolved = native_module._resolve_pair_resource_paths(
                paths,
                pair="en-en",
                payload={},
            )[2]

        self.assertEqual(helper_resolved, legacy)
        self.assertEqual(native_resolved, legacy)

    def test_runtime_diagnostics_reports_manifest_backed_frequency_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            artifact = self._write_manifest_backed_frequency_pack(
                paths.frequency_packs_dir,
                pack_id="freq-en-coca",
                provider="wordfrequency",
            )

            payload = get_srs_runtime_diagnostics(paths, pair="en-en")

        self.assertEqual(payload["pair"], "en-en")
        self.assertEqual(payload["set_source_db"], str(artifact))
        self.assertTrue(payload["set_source_db_exists"])
        self.assertEqual(payload["frequency_pack_path"], str(artifact))
        self.assertTrue(payload["frequency_pack_exists"])
        self.assertEqual(payload["frequency_pack_id"], "freq-en-coca")
        self.assertEqual(payload["frequency_pack_provider"], "wordfrequency")
        self.assertEqual(payload["frequency_pos_source_profile"], "compact-latin")
        self.assertEqual(payload["missing_inputs"], [])

    def _write_manifest_backed_frequency_pack(
        self,
        frequency_packs_dir: Path,
        *,
        pack_id: str,
        provider: str,
    ) -> Path:
        pack_root = frequency_packs_dir / pack_id
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact = pack_root / "main.sqlite"
        artifact.write_bytes(b"SQLite format 3\x00")
        write_installed_pack_manifest(
            frequency_packs_dir,
            pack_id=pack_id,
            pack_kind="frequency",
            provider=provider,
            local_kind="file",
            build_mode="convert_archive",
            artifact_path=artifact,
            sqlite_filename="main.sqlite",
        )
        return artifact


if __name__ == "__main__":
    unittest.main()
