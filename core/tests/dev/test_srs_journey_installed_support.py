from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from srs_journey_installed_support import stage_installed_pair_resources  # noqa: E402


class TestSrsJourneyInstalledSupport(unittest.TestCase):
    def test_stage_installed_pair_resources_preserves_manifest_backed_translation_pack_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as installed_tmp, tempfile.TemporaryDirectory() as tmp:
            installed_paths = build_helper_paths(Path(installed_tmp))
            paths = build_helper_paths(Path(tmp))

            forward_root = installed_paths.language_packs_dir / "wiktionary-es-en"
            forward_root.mkdir(parents=True, exist_ok=True)
            forward_artifact = forward_root / "main.sqlite"
            forward_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                installed_paths.language_packs_dir,
                pack_id="wiktionary-es-en",
                pack_kind="language",
                provider="wiktionary",
                local_kind="file",
                build_mode="kaikki_jsonl_to_sqlite",
                artifact_path=forward_artifact,
                sqlite_filename="wiktionary-es-en.sqlite",
            )

            reverse_root = installed_paths.language_packs_dir / "wiktionary-en-es"
            reverse_root.mkdir(parents=True, exist_ok=True)
            reverse_artifact = reverse_root / "main.sqlite"
            reverse_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                installed_paths.language_packs_dir,
                pack_id="wiktionary-en-es",
                pack_kind="language",
                provider="wiktionary",
                local_kind="file",
                build_mode="kaikki_jsonl_to_sqlite",
                artifact_path=reverse_artifact,
                sqlite_filename="wiktionary-en-es.sqlite",
            )

            with patch(
                "srs_journey_installed_support.build_helper_paths",
                return_value=installed_paths,
            ):
                resources = stage_installed_pair_resources(paths, pair="en-es")

            forward = resources["translation_dict_path"]
            reverse = resources["reverse_translation_dict_path"]
            assert forward is not None
            assert reverse is not None
            self.assertTrue(str(forward).endswith("language_packs/wiktionary-es-en/main.sqlite"))
            self.assertTrue(str(reverse).endswith("language_packs/wiktionary-en-es/main.sqlite"))
            self.assertTrue(
                (paths.language_packs_dir / "wiktionary-es-en" / "manifest.json").exists()
            )
            self.assertTrue(
                (paths.language_packs_dir / "wiktionary-en-es" / "manifest.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
