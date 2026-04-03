from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from lexishift_core import SynonymSourceSettings
from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from main import MainWindow


def test_embedding_paths_for_pair_resolves_managed_pack_ids_and_manual_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        managed_root = root / "embedding_packs" / "embed-xling-es"
        managed_root.mkdir(parents=True, exist_ok=True)
        managed_sqlite = managed_root / "main.sqlite"
        managed_sqlite.write_bytes(b"SQLite format 3\x00")
        write_installed_pack_manifest(
            root / "embedding_packs",
            pack_id="embed-xling-es",
            pack_kind="embedding",
            provider="fasttext",
            local_kind="file",
            build_mode="convert_to_sqlite",
            artifact_path=managed_sqlite,
            sqlite_filename="main.sqlite",
        )
        manual_sqlite = root / "manual.vec.sqlite"
        manual_sqlite.write_bytes(b"SQLite format 3\x00")
        settings = SynonymSourceSettings(
            use_embeddings=True,
            embedding_pair_pack_ids={
                "en-es": ["embed-xling-es"],
            },
            embedding_pair_paths={
                "en-es": [str(manual_sqlite)],
            },
        )
        dummy = SimpleNamespace()

        with patch("main_replacement_filter_mixin._app_data_dir", return_value=root):
            resolved = MainWindow._embedding_paths_for_pair(dummy, settings, "en-es")

    assert resolved == [managed_sqlite, manual_sqlite]
