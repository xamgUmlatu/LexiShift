from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from lexishift_core import AppSettings, SynonymSourceSettings, save_app_settings
from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from state import AppState


def test_load_settings_migrates_managed_translation_and_frequency_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        language_root = root / "language_packs" / "freedict-en-es"
        language_root.mkdir(parents=True, exist_ok=True)
        language_artifact = language_root / "main.sqlite"
        language_artifact.write_bytes(b"SQLite format 3\x00")
        write_installed_pack_manifest(
            root / "language_packs",
            pack_id="freedict-en-es",
            pack_kind="language",
            provider="freedict",
            local_kind="dir",
            build_mode="freedict_tei_to_sqlite",
            artifact_path=language_artifact,
            sqlite_filename="main.sqlite",
        )

        frequency_root = root / "frequency_packs" / "freq-en-coca"
        frequency_root.mkdir(parents=True, exist_ok=True)
        frequency_artifact = frequency_root / "main.sqlite"
        frequency_artifact.write_bytes(b"SQLite format 3\x00")
        write_installed_pack_manifest(
            root / "frequency_packs",
            pack_id="freq-en-coca",
            pack_kind="frequency",
            provider="wordfrequency",
            local_kind="file",
            build_mode="convert_archive",
            artifact_path=frequency_artifact,
            sqlite_filename="main.sqlite",
        )

        settings_path = root / "settings.json"
        save_app_settings(
            AppSettings(
                synonyms=SynonymSourceSettings(
                    language_packs={"freedict-en-es": str(language_artifact)},
                    frequency_packs={"freq-en-coca": str(frequency_artifact)},
                )
            ),
            settings_path,
        )

        state = AppState(settings_path=settings_path)
        with patch("state._app_data_dir", return_value=root):
            state.load_settings()

        synonyms = state.settings.synonyms
        assert synonyms is not None
        assert tuple(synonyms.managed_language_pack_ids) == ("freedict-en-es",)
        assert tuple(synonyms.managed_frequency_pack_ids) == ("freq-en-coca",)
        assert synonyms.language_packs == {}
        assert synonyms.frequency_packs == {}
