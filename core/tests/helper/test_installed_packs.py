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
    def test_write_and_resolve_translation_sqlite_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = installed_pack_root(base_dir, "freedict-en-de")
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact_path = pack_root / "freedict-en-de.sqlite"
            artifact_path.write_bytes(b"SQLite format 3\x00")

            manifest_path = write_installed_pack_manifest(
                base_dir,
                pack_id="freedict-en-de",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=artifact_path,
                source_filename="freedict-eng-deu.tar.xz",
                sqlite_filename="freedict-en-de.sqlite",
                required_files=("eng-deu.tei",),
            )

            self.assertEqual(
                manifest_path, installed_pack_manifest_path(base_dir, "freedict-en-de")
            )
            manifest = load_installed_pack_manifest(base_dir, "freedict-en-de")
            assert manifest is not None
            self.assertEqual(manifest.artifact_relpath, "freedict-en-de.sqlite")
            self.assertEqual(manifest.artifact_kind, "sqlite")
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

    def test_write_and_resolve_embedding_sqlite_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = installed_pack_root(base_dir, "embed-en-cc")
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact_path = pack_root / "main.sqlite"
            artifact_path.write_bytes(b"SQLite format 3\x00")

            write_installed_pack_manifest(
                base_dir,
                pack_id="embed-en-cc",
                pack_kind="embedding",
                provider="fasttext",
                local_kind="file",
                build_mode="convert_to_sqlite",
                artifact_path=artifact_path,
                source_filename="cc.en.300.vec.gz",
                sqlite_filename="main.sqlite",
            )

            manifest = load_installed_pack_manifest(base_dir, "embed-en-cc")
            assert manifest is not None
            self.assertEqual(manifest.pack_kind, "embedding")
            self.assertEqual(manifest.artifact_relpath, "main.sqlite")
            self.assertEqual(
                resolve_installed_pack_artifact(base_dir, "embed-en-cc"), artifact_path
            )


if __name__ == "__main__":
    unittest.main()
