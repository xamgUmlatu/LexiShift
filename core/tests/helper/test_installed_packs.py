from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.installed_packs import (  # noqa: E402
    installed_pack_manifest_path,
    installed_pack_root,
    load_installed_pack_manifest,
    resolve_installed_pack_artifact,
    write_installed_pack_manifest,
)


class TestInstalledPacks(unittest.TestCase):
    def test_write_and_resolve_file_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = installed_pack_root(base_dir, "freedict-en-de")
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact_path = pack_root / "eng-deu.tei"
            artifact_path.write_text("<tei/>", encoding="utf-8")

            manifest_path = write_installed_pack_manifest(
                base_dir,
                pack_id="freedict-en-de",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="download_only",
                artifact_path=artifact_path,
                source_filename="freedict-eng-deu.tar.xz",
                required_files=("eng-deu.tei",),
            )

            self.assertEqual(
                manifest_path, installed_pack_manifest_path(base_dir, "freedict-en-de")
            )
            manifest = load_installed_pack_manifest(base_dir, "freedict-en-de")
            assert manifest is not None
            self.assertEqual(manifest.artifact_relpath, "eng-deu.tei")
            self.assertEqual(
                resolve_installed_pack_artifact(base_dir, "freedict-en-de"), artifact_path
            )

    def test_write_and_resolve_directory_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = installed_pack_root(base_dir, "wordnet-en")
            artifact_path = pack_root / "english-wordnet"
            artifact_path.mkdir(parents=True, exist_ok=True)

            write_installed_pack_manifest(
                base_dir,
                pack_id="wordnet-en",
                pack_kind="language",
                provider="princeton",
                local_kind="dir",
                build_mode="download_only",
                artifact_path=artifact_path,
                source_filename="english-wordnet.zip",
            )

            manifest = load_installed_pack_manifest(base_dir, "wordnet-en")
            assert manifest is not None
            self.assertEqual(manifest.artifact_relpath, "english-wordnet")
            self.assertEqual(resolve_installed_pack_artifact(base_dir, "wordnet-en"), artifact_path)


if __name__ == "__main__":
    unittest.main()
