from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.frequency_packs import build_frequency_pack_ref  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
