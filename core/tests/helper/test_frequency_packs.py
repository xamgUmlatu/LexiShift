from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.frequency_packs import (  # noqa: E402
    build_frequency_pack_ref,
    resolve_configured_frequency_pack,
)
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402


class TestFrequencyPacks(unittest.TestCase):
    def test_build_frequency_pack_ref_uses_manifest_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "freq-en-coca"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="freq-en-coca",
                pack_kind="frequency",
                provider="wordfrequency",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            resolved = build_frequency_pack_ref("en-en", artifact)
        assert resolved is not None
        self.assertEqual(resolved.pack_id, "freq-en-coca")
        self.assertEqual(resolved.provider, "wordfrequency")
        self.assertEqual(resolved.pos_source_profile, "compact-latin")

    def test_build_frequency_pack_ref_falls_back_to_filename_identity(self) -> None:
        resolved = build_frequency_pack_ref("en-es", Path("/tmp/freq-es-cde.sqlite"))
        assert resolved is not None
        self.assertEqual(resolved.pack_id, "freq-es-cde")
        self.assertEqual(resolved.provider, "freq-es-cde")
        self.assertEqual(resolved.pos_source_profile, "freq-es-cde")

    def test_build_frequency_pack_ref_recognizes_spalex_identity(self) -> None:
        resolved = build_frequency_pack_ref("en-es", Path("/tmp/freq-es-spalex-v1.sqlite"))
        assert resolved is not None
        self.assertEqual(resolved.pack_id, "freq-es-spalex-v1")
        self.assertEqual(resolved.provider, "freq-es-spalex-v1")
        self.assertEqual(resolved.pos_source_profile, "spalex_only_v1")

    def test_build_frequency_pack_ref_recognizes_english_leipzig_identity(self) -> None:
        resolved = build_frequency_pack_ref(
            "en-en",
            Path("/tmp/freq-en-leipzig-default.sqlite"),
        )
        assert resolved is not None
        self.assertEqual(resolved.pack_id, "freq-en-leipzig-default")
        self.assertEqual(resolved.provider, "freq-en-leipzig-default")
        self.assertEqual(resolved.pos_source_profile, "generic")

    def test_resolve_configured_frequency_pack_prefers_managed_pack_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "freq-en-coca"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="freq-en-coca",
                pack_kind="frequency",
                provider="wordfrequency",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            resolved, resolution = resolve_configured_frequency_pack(
                "en-en",
                frequency_packs_dir=base_dir,
                settings_frequency_pack_paths={},
                managed_frequency_pack_ids=("freq-en-coca",),
            )

        assert resolved is not None
        self.assertEqual(resolved.path.resolve(strict=False), artifact.resolve(strict=False))
        self.assertEqual(resolved.pack_id, "freq-en-coca")
        self.assertEqual(resolution, "managed:freq-en-coca")

    def test_resolve_configured_frequency_pack_uses_manual_linked_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            manual = base_dir / "manual.sqlite"
            manual.write_bytes(b"SQLite format 3\x00")
            resolved, resolution = resolve_configured_frequency_pack(
                "en-en",
                frequency_packs_dir=base_dir,
                settings_frequency_pack_paths={"freq-en-coca": str(manual)},
                managed_frequency_pack_ids=(),
            )

        assert resolved is not None
        self.assertEqual(resolved.path.resolve(strict=False), manual.resolve(strict=False))
        self.assertEqual(resolved.pack_id, "manual")
        self.assertEqual(resolution, "linked:freq-en-coca")

    def test_resolve_configured_frequency_pack_prefers_managed_artifact_over_same_key_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "freq-en-coca"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            stale = base_dir / "stale.sqlite"
            stale.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="freq-en-coca",
                pack_kind="frequency",
                provider="wordfrequency",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            resolved, resolution = resolve_configured_frequency_pack(
                "en-en",
                frequency_packs_dir=base_dir,
                settings_frequency_pack_paths={"freq-en-coca": str(stale)},
                managed_frequency_pack_ids=("freq-en-coca",),
            )

        assert resolved is not None
        self.assertEqual(resolved.path.resolve(strict=False), artifact.resolve(strict=False))
        self.assertEqual(resolved.pack_id, "freq-en-coca")
        self.assertEqual(resolution, "managed:freq-en-coca")

    def test_resolve_configured_frequency_pack_keeps_configured_path_when_managed_artifact_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            manual = base_dir / "manual.sqlite"
            manual.write_bytes(b"SQLite format 3\x00")
            resolved, resolution = resolve_configured_frequency_pack(
                "en-en",
                frequency_packs_dir=base_dir,
                settings_frequency_pack_paths={"freq-en-coca": str(manual)},
                managed_frequency_pack_ids=("freq-en-coca",),
            )

        assert resolved is not None
        self.assertEqual(resolved.path.resolve(strict=False), manual.resolve(strict=False))
        self.assertEqual(resolved.pack_id, "manual")
        self.assertEqual(resolution, "linked:freq-en-coca")

    def test_resolve_configured_frequency_pack_ignores_en_es_legacy_cde_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            manual = base_dir / "manual-cde.sqlite"
            manual.write_bytes(b"SQLite format 3\x00")
            resolved, resolution = resolve_configured_frequency_pack(
                "en-es",
                frequency_packs_dir=base_dir,
                settings_frequency_pack_paths={"freq-es-cde": str(manual)},
                managed_frequency_pack_ids=(),
            )

        self.assertIsNone(resolved)
        self.assertEqual(resolution, "missing")

    def test_resolve_configured_frequency_pack_ignores_stale_en_es_managed_cde(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            cde_root = base_dir / "freq-es-cde"
            cde_root.mkdir(parents=True, exist_ok=True)
            cde_artifact = cde_root / "main.sqlite"
            cde_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="freq-es-cde",
                pack_kind="frequency",
                provider="freq-es-cde",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=cde_artifact,
                sqlite_filename="main.sqlite",
            )
            spalex_root = base_dir / "freq-es-spalex-v1"
            spalex_root.mkdir(parents=True, exist_ok=True)
            spalex_artifact = spalex_root / "main.sqlite"
            spalex_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="freq-es-spalex-v1",
                pack_kind="frequency",
                provider="freq-es-spalex-v1",
                local_kind="file",
                build_mode="spalex_frequency_pipeline",
                artifact_path=spalex_artifact,
                sqlite_filename="main.sqlite",
            )
            resolved, resolution = resolve_configured_frequency_pack(
                "en-es",
                frequency_packs_dir=base_dir,
                settings_frequency_pack_paths={},
                managed_frequency_pack_ids=("freq-es-cde",),
            )

        assert resolved is not None
        self.assertEqual(resolved.path.resolve(strict=False), spalex_artifact.resolve(strict=False))
        self.assertEqual(resolved.pack_id, "freq-es-spalex-v1")
        self.assertEqual(resolution, "fallback_default")


if __name__ == "__main__":
    unittest.main()
