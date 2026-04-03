from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from settings_language_packs_panel_state_mixin import LanguagePackPanelStateMixin


def test_paths_omit_managed_translation_pack_artifacts() -> None:
    class _DummyPanel(LanguagePackPanelStateMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        managed = root / "language_packs" / "freedict-en-es" / "main.sqlite"
        managed.parent.mkdir(parents=True, exist_ok=True)
        managed.write_bytes(b"SQLite format 3\x00")
        dummy = _DummyPanel()
        dummy._language_pack_paths = {
            "freedict-en-es": str(managed),
            "wordnet-en": "/tmp/wordnet",
        }
        dummy._language_pack_info = {
            "freedict-en-es": SimpleNamespace(
                pack_id="freedict-en-es",
                build_mode="freedict_tei_to_sqlite",
                sqlite_filename="freedict-en-es.sqlite",
            ),
            "wordnet-en": SimpleNamespace(
                pack_id="wordnet-en",
                build_mode="download_only",
                sqlite_filename=None,
            ),
        }
        dummy._resolve_downloaded_path = lambda pack, embeddings=False: (
            str(managed)
            if not embeddings and getattr(pack, "pack_id", "") == "freedict-en-es"
            else None
        )
        dummy._is_app_data_path = (
            lambda path, embeddings=False: not embeddings
            and os.path.commonpath([str(root / "language_packs"), os.path.abspath(path)])
            == str(root / "language_packs")
        )

        resolved = dummy.paths()
        managed_ids = dummy.managed_language_pack_ids()

    assert resolved == {"wordnet-en": "/tmp/wordnet"}
    assert managed_ids == ["freedict-en-es"]


def test_frequency_paths_omit_managed_pack_artifacts() -> None:
    class _DummyPanel(LanguagePackPanelStateMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        managed = root / "frequency_packs" / "freq-en-coca" / "main.sqlite"
        managed.parent.mkdir(parents=True, exist_ok=True)
        managed.write_bytes(b"SQLite format 3\x00")
        manual = root / "manual.sqlite"
        manual.write_bytes(b"SQLite format 3\x00")
        dummy = _DummyPanel()
        dummy._frequency_pack_paths = {
            "freq-en-coca": str(managed),
            "freq-manual": str(manual),
        }
        dummy._frequency_pack_info = {
            "freq-en-coca": SimpleNamespace(pack_id="freq-en-coca"),
            "freq-manual": SimpleNamespace(pack_id="freq-manual"),
        }
        dummy._resolve_frequency_pack_path = lambda pack: (
            str(managed) if getattr(pack, "pack_id", "") == "freq-en-coca" else None
        )
        dummy._is_frequency_pack_data_path = lambda path: os.path.commonpath(
            [str(root / "frequency_packs"), os.path.abspath(path)]
        ) == str(root / "frequency_packs")

        resolved = dummy.frequency_paths()
        managed_ids = dummy.managed_frequency_pack_ids()

    assert resolved == {"freq-manual": str(manual)}
    assert managed_ids == ["freq-en-coca"]


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
