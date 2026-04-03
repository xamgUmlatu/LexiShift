from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from settings_language_packs_path_mixin import LanguagePackPanelPathMixin


def test_resolve_downloaded_path_accepts_legacy_translation_storage_filename() -> None:
    class _DummyPanel(LanguagePackPanelPathMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        dummy = _DummyPanel()
        dummy._language_pack_dir = str(root / "language_packs")
        legacy = root / "language_packs" / "freedict-en-es" / "freedict-en-es.sqlite"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(b"SQLite format 3\x00")
        pack = SimpleNamespace(pack_id="freedict-en-es", sqlite_filename="main.sqlite")

        resolved = dummy._resolve_downloaded_path(pack)

    assert resolved == str(legacy)


def test_resolve_downloaded_path_accepts_legacy_translation_flat_filename() -> None:
    class _DummyPanel(LanguagePackPanelPathMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        dummy = _DummyPanel()
        dummy._language_pack_dir = str(root / "language_packs")
        legacy = root / "language_packs" / "freedict-en-es.sqlite"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(b"SQLite format 3\x00")
        pack = SimpleNamespace(pack_id="freedict-en-es", sqlite_filename="main.sqlite")

        resolved = dummy._resolve_downloaded_path(pack)

    assert resolved == str(legacy)


def test_resolve_frequency_pack_path_accepts_legacy_storage_filename() -> None:
    class _DummyPanel(LanguagePackPanelPathMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        dummy = _DummyPanel()
        dummy._frequency_pack_dir = str(root / "frequency_packs")
        legacy = root / "frequency_packs" / "freq-en-coca" / "freq-en-coca.sqlite"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(b"SQLite format 3\x00")
        pack = SimpleNamespace(pack_id="freq-en-coca", sqlite_filename="main.sqlite")

        resolved = dummy._resolve_frequency_pack_path(pack)

    assert resolved == str(legacy)


def test_resolve_frequency_pack_path_accepts_legacy_flat_filename() -> None:
    class _DummyPanel(LanguagePackPanelPathMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        dummy = _DummyPanel()
        dummy._frequency_pack_dir = str(root / "frequency_packs")
        legacy = root / "frequency_packs" / "freq-en-coca.sqlite"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(b"SQLite format 3\x00")
        pack = SimpleNamespace(pack_id="freq-en-coca", sqlite_filename="main.sqlite")

        resolved = dummy._resolve_frequency_pack_path(pack)

    assert resolved == str(legacy)
