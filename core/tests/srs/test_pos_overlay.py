from __future__ import annotations

from types import SimpleNamespace
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.srs.pos_overlay import (  # noqa: E402
    load_pos_overlay_entries,
    pos_overlay_resource_payload,
    resolve_pair_pos_overlay,
)


class TestSrsPosOverlay(unittest.TestCase):
    def test_resolves_managed_spanish_target_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            base_dir = data_root / "pos_packs"
            pack_root = base_dir / "pos-es-ud-ancora-v1"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            _write_overlay_sqlite(artifact)
            write_installed_pack_manifest(
                base_dir,
                pack_id="pos-es-ud-ancora-v1",
                pack_kind="pos_overlay",
                provider="universal-dependencies-ud-ancora",
                local_kind="file",
                build_mode="ud_ancora_pos_overlay",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )

            ref = resolve_pair_pos_overlay(SimpleNamespace(data_root=data_root), pair="en-es")

            self.assertIsNotNone(ref)
            assert ref is not None
            self.assertEqual(ref.path, artifact)
            self.assertEqual(ref.pack_id, "pos-es-ud-ancora-v1")
            self.assertEqual(ref.provider, "universal-dependencies-ud-ancora")
            self.assertEqual(ref.resolution, "managed:pos-es-ud-ancora-v1")
            self.assertEqual(
                pos_overlay_resource_payload(ref)["pos_overlay_id"],
                "pos-es-ud-ancora-v1",
            )

    def test_loads_overlay_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "overlay.sqlite"
            _write_overlay_sqlite(artifact)

            entries = load_pos_overlay_entries(artifact)

            self.assertIn("gato", entries)
            self.assertEqual(entries["gato"].raw_pos, "NOUN")
            self.assertEqual(entries["gato"].pos_source_profile, "universal-dependencies")


def _write_overlay_sqlite(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE pos_overlay (
              lemma TEXT PRIMARY KEY,
              raw_pos TEXT,
              pos_source_profile TEXT,
              source_provider TEXT,
              overlay_id TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO pos_overlay (
              lemma, raw_pos, pos_source_profile, source_provider, overlay_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "gato",
                "NOUN",
                "universal-dependencies",
                "universal-dependencies-ud-ancora",
                "pos-es-ud-ancora-v1",
            ),
        )
        conn.commit()


if __name__ == "__main__":
    unittest.main()
