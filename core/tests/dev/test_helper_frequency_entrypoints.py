from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CORE_ROOT = Path(__file__).resolve().parents[3] / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402


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
                self.assertIn("--frequency-pack-path", result.stdout)
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
                self.assertIn(
                    "Legacy alias: --set-source-db.",
                    normalized_help,
                )

    def test_native_host_accepts_frequency_pack_path_payload_alias(self) -> None:
        native_module = _load_module(
            "lexishift_native_host_frequency_alias_test", NATIVE_HOST_SCRIPT
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            pack_root = paths.frequency_packs_dir / "freq-en-coca"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                paths.frequency_packs_dir,
                pack_id="freq-en-coca",
                pack_kind="frequency",
                provider="wordfrequency",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            legacy_override = paths.frequency_packs_dir / "freq-en-coca.sqlite"
            legacy_override.write_bytes(b"SQLite format 3\x00")

            resolved = native_module._resolve_pair_resource_paths(
                paths,
                pair="en-en",
                payload={
                    "frequency_pack_path": str(artifact),
                    "set_source_db": str(legacy_override),
                },
            )[2]

        self.assertEqual(resolved, artifact)


if __name__ == "__main__":
    unittest.main()
