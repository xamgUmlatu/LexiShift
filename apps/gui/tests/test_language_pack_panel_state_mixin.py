from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from settings_language_packs_panel_state_mixin import LanguagePackPanelStateMixin


def test_embedding_paths_omits_managed_pack_artifacts() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        managed = root / "embedding_packs" / "embed-xling-es" / "main.sqlite"
        managed.parent.mkdir(parents=True, exist_ok=True)
        managed.write_bytes(b"SQLite format 3\x00")
        external = root / "external.sqlite"
        external.write_bytes(b"SQLite format 3\x00")
        dummy = SimpleNamespace(
            _embedding_pack_paths={
                "embed-xling-es": str(managed),
                "embed-manual": str(external),
            },
            _embedding_pack_info={
                "embed-xling-es": SimpleNamespace(pack_id="embed-xling-es"),
                "embed-manual": SimpleNamespace(pack_id="embed-manual"),
            },
            _resolve_downloaded_path=lambda pack, embeddings=False: (
                str(managed)
                if embeddings and getattr(pack, "pack_id", "") == "embed-xling-es"
                else None
            ),
            _is_app_data_path=lambda path, embeddings=False: embeddings
            and os.path.commonpath([str(root / "embedding_packs"), os.path.abspath(path)])
            == str(root / "embedding_packs"),
        )

        resolved = LanguagePackPanelStateMixin.embedding_paths(dummy)

    assert resolved == {"embed-manual": str(external)}


def test_embedding_pair_paths_omits_managed_pair_artifacts() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        managed = root / "embedding_packs" / "embed-xling-es" / "main.sqlite"
        managed.parent.mkdir(parents=True, exist_ok=True)
        managed.write_bytes(b"SQLite format 3\x00")
        manual = root / "manual.sqlite"
        manual.write_bytes(b"SQLite format 3\x00")
        dummy = SimpleNamespace(
            _embedding_pair_paths={"en-es": [str(managed), str(manual)]},
            _embedding_pair_pack_ids={"en-es": ["embed-xling-es"]},
            _embedding_pack_info={
                "embed-xling-es": SimpleNamespace(pack_id="embed-xling-es"),
            },
            _resolve_downloaded_path=lambda pack, embeddings=False: (
                str(managed)
                if embeddings and getattr(pack, "pack_id", "") == "embed-xling-es"
                else None
            ),
        )

        resolved = LanguagePackPanelStateMixin.embedding_pair_paths(dummy)

    assert resolved == {"en-es": [str(manual)]}
