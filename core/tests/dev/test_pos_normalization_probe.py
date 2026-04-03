from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPT_DIR)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core import AppSettings, SynonymSourceSettings, save_app_settings  # noqa: E402
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from pos_normalization_probe import (  # noqa: E402
    _load_synonym_settings,
    _resolve_frequency_db_for_pair,
)


class TestPosNormalizationProbe(unittest.TestCase):
    def test_load_synonym_settings_preserves_managed_frequency_pack_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            save_app_settings(
                AppSettings(
                    synonyms=SynonymSourceSettings(
                        managed_frequency_pack_ids=("freq-en-coca",),
                        frequency_packs={"freq-manual": "/tmp/manual.sqlite"},
                    )
                ),
                settings_path,
            )

            loaded = _load_synonym_settings(settings_path)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(tuple(loaded.managed_frequency_pack_ids), ("freq-en-coca",))
        self.assertEqual(dict(loaded.frequency_packs), {"freq-manual": "/tmp/manual.sqlite"})

    def test_resolve_frequency_db_for_pair_prefers_managed_pack_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            pack_root = frequency_packs_dir / "freq-en-coca"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_packs_dir,
                pack_id="freq-en-coca",
                pack_kind="frequency",
                provider="wordfrequency",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )

            resolved, resolution = _resolve_frequency_db_for_pair(
                "en-en",
                frequency_packs_dir=frequency_packs_dir,
                settings_frequency_packs={},
                managed_frequency_pack_ids=("freq-en-coca",),
            )

        self.assertEqual(
            resolved.resolve(strict=False) if resolved is not None else None,
            artifact.resolve(strict=False),
        )
        self.assertEqual(resolution, "managed:freq-en-coca")


if __name__ == "__main__":
    unittest.main()
