from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from lexishift_core import AppSettings, SynonymSourceSettings, save_app_settings
from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from main import MainWindow
from state import AppState


def test_legacy_managed_embedding_paths_migrate_and_still_resolve_runtime() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        embedding_root = root / "embedding_packs" / "embed-xling-es"
        embedding_root.mkdir(parents=True, exist_ok=True)
        embedding_artifact = embedding_root / "main.sqlite"
        embedding_artifact.write_bytes(b"SQLite format 3\x00")
        write_installed_pack_manifest(
            root / "embedding_packs",
            pack_id="embed-xling-es",
            pack_kind="embedding",
            provider="fasttext",
            local_kind="file",
            build_mode="convert_to_sqlite",
            artifact_path=embedding_artifact,
            sqlite_filename="main.sqlite",
        )
        settings_path = root / "settings.json"
        save_app_settings(
            AppSettings(
                synonyms=SynonymSourceSettings(
                    use_embeddings=True,
                    embedding_pack_paths={"embed-xling-es": str(embedding_artifact)},
                    embedding_pair_paths={"en-es": [str(embedding_artifact)]},
                )
            ),
            settings_path,
        )

        state = AppState(settings_path=settings_path)
        dummy = SimpleNamespace()
        with (
            patch("state._app_data_dir", return_value=root),
            patch("main_replacement_filter_mixin._app_data_dir", return_value=root),
        ):
            state.load_settings()
            synonyms = state.settings.synonyms
            assert synonyms is not None
            assert synonyms.embedding_pack_paths == {}
            assert synonyms.embedding_pair_paths == {}
            assert synonyms.embedding_pair_pack_ids == {"en-es": ["embed-xling-es"]}
            assert synonyms.embedding_pair_enabled == {"en-es": True}

            resolved = MainWindow._embedding_paths_for_pair(dummy, synonyms, "en-es")

    assert resolved == [embedding_artifact]
