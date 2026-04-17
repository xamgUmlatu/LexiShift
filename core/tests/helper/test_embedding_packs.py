from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.embedding_packs import (  # noqa: E402
    build_embedding_pack_ref,
    resolve_embedding_pack_artifact,
)
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402


class TestEmbeddingPacks(unittest.TestCase):
    def test_resolve_embedding_pack_artifact_prefers_manifest_backed_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "embed-es-cc"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            configured = base_dir / "manual.sqlite"
            configured.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="embed-es-cc",
                pack_kind="embedding",
                provider="fasttext",
                local_kind="file",
                build_mode="convert_to_sqlite",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            resolved = resolve_embedding_pack_artifact(
                base_dir,
                pack_id="embed-es-cc",
                configured_path=configured,
            )
        self.assertEqual(resolved, artifact)

    def test_resolve_embedding_pack_artifact_falls_back_to_configured_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            configured = base_dir / "manual.sqlite"
            configured.write_bytes(b"SQLite format 3\x00")

            resolved = resolve_embedding_pack_artifact(
                base_dir,
                pack_id="embed-es-cc",
                configured_path=configured,
            )

        self.assertEqual(resolved, configured)

    def test_build_embedding_pack_ref_uses_manifest_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "embed-xling-es"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="embed-xling-es",
                pack_kind="embedding",
                provider="fasttext",
                local_kind="file",
                build_mode="convert_to_sqlite",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            resolved = build_embedding_pack_ref("en-es", artifact)
        assert resolved is not None
        self.assertEqual(resolved.pack_id, "embed-xling-es")
        self.assertEqual(resolved.provider, "fasttext")
        self.assertEqual(resolved.source_profile, "fasttext-aligned")


if __name__ == "__main__":
    unittest.main()
