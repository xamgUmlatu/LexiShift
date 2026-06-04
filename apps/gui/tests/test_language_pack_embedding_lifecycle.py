from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from settings_language_packs import LanguagePackPanel


def test_delete_embedding_pack_without_local_files_clears_stale_pair_activation() -> None:
    class _DummyPanel:
        def _embedding_row_for(self, pack_id: str):
            return self._embedding_pack_rows.get(pack_id) or self._cross_embedding_pack_rows.get(
                pack_id
            )

        def _clear_embedding_pack_entry(
            self, pack_id: str, *, local_path: str | None = None
        ) -> None:
            LanguagePackPanel._clear_embedding_pack_entry(self, pack_id, local_path=local_path)

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        refreshed: list[str] = []
        dummy = _DummyPanel()
        dummy._embedding_pack_rows = {"embed-xling-es": SimpleNamespace()}
        dummy._cross_embedding_pack_rows = {}
        dummy._embedding_pack_info = {
            "embed-xling-es": SimpleNamespace(
                pack_id="embed-xling-es",
                pair_key="en-es",
                display_name=lambda: "Aligned ES Embeddings",
            )
        }
        dummy._embedding_pack_paths = {}
        dummy._embedding_pair_pack_ids = {"en-es": ["embed-xling-es"]}
        dummy._embedding_pair_paths = {}
        dummy._embedding_pair_enabled = {"en-es": True}
        dummy._embedding_pack_storage_dir = lambda pack: root / "embedding_packs" / pack.pack_id
        dummy._download_archive_path = lambda pack, embeddings=True: str(
            root / "embedding_packs" / pack.pack_id / "archive.vec"
        )
        dummy._embedding_sqlite_path = lambda path: path
        dummy._resolve_downloaded_path = lambda pack, embeddings=True: None
        dummy._is_app_data_path = lambda path, embeddings=False: True
        dummy._refresh_embedding_pack_table = lambda: refreshed.append("embedding")
        dummy._refresh_cross_embedding_pack_table = lambda: refreshed.append("cross")

        with patch("settings_language_packs.QMessageBox.information") as info_mock:
            LanguagePackPanel._delete_embedding_pack(dummy, "embed-xling-es")

    info_mock.assert_called_once()
    assert dummy._embedding_pack_paths == {}
    assert dummy._embedding_pair_pack_ids == {}
    assert refreshed == ["embedding", "cross"]
