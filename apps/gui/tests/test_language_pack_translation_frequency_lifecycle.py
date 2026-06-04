from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QMessageBox

from settings_language_packs import LanguagePackPanel
from settings_language_packs_panel_state_mixin import LanguagePackPanelStateMixin
from settings_language_packs_support import (
    LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
    LANGUAGE_RESOURCE_ORIGIN_MANUAL,
    LanguageResourceBinding,
)


def test_delete_language_pack_unlinks_manual_binding() -> None:
    class _DummyPanel(LanguagePackPanelStateMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        refreshed: list[str] = []
        dummy = _DummyPanel()
        dummy._language_pack_rows = {"freedict-en-es": SimpleNamespace()}
        dummy._language_pack_info = {
            "freedict-en-es": SimpleNamespace(
                pack_id="freedict-en-es",
                display_name=lambda: "FreeDict EN-ES",
            )
        }
        dummy._language_resource_bindings = {
            "freedict-en-es": LanguageResourceBinding(
                pack_id="freedict-en-es",
                family=LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                effective_path=str(root / "external" / "eng-spa.tei"),
            )
        }
        dummy._sync_language_pack_compat_state()
        dummy._language_pack_storage_dir = lambda pack: root / "language_packs" / pack.pack_id
        dummy._download_archive_path = lambda pack: str(
            root / "language_packs" / pack.pack_id / "archive.tei"
        )
        dummy._resolve_downloaded_path = lambda pack: None
        dummy._is_app_data_path = lambda path: False
        dummy._refresh_language_pack_table = lambda: refreshed.append("language")
        dummy._set_status_message = lambda *args, **kwargs: None

        with patch(
            "settings_language_packs.localized_question",
            return_value=QMessageBox.Yes,
        ) as question_mock:
            LanguagePackPanel._delete_language_pack(dummy, "freedict-en-es")

    question_mock.assert_called_once()
    assert dummy.language_resource_bindings() == {}
    assert dummy.managed_language_pack_ids() == []
    assert dummy.paths() == {}
    assert refreshed == ["language"]


def test_delete_frequency_pack_without_local_files_clears_managed_id_state() -> None:
    class _DummyPanel(LanguagePackPanelStateMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        refreshed: list[str] = []
        dummy = _DummyPanel()
        dummy._frequency_pack_rows = {"freq-en-coca": SimpleNamespace()}
        dummy._frequency_pack_info = {
            "freq-en-coca": SimpleNamespace(
                pack_id="freq-en-coca",
                display_name=lambda: "COCA Frequency",
            )
        }
        dummy._frequency_pack_paths = {}
        dummy._managed_frequency_pack_ids = {"freq-en-coca"}
        dummy._frequency_pack_storage_dir = lambda pack: root / "frequency_packs" / pack.pack_id
        dummy._frequency_archive_path = lambda pack: str(
            root / "frequency_packs" / pack.pack_id / "archive.zip"
        )
        dummy._frequency_sqlite_path = lambda pack: str(
            root / "frequency_packs" / pack.pack_id / "main.sqlite"
        )
        dummy._is_frequency_pack_data_path = lambda path: True
        dummy._refresh_frequency_pack_table = lambda: refreshed.append("frequency")

        with patch("settings_language_packs.QMessageBox.information") as info_mock:
            LanguagePackPanel._delete_frequency_pack(dummy, "freq-en-coca")

    info_mock.assert_called_once()
    assert dummy.managed_frequency_pack_ids() == []
    assert dummy.frequency_paths() == {}
    assert refreshed == ["frequency"]


def test_delete_frequency_pack_unlinks_manual_external_path() -> None:
    class _DummyPanel(LanguagePackPanelStateMixin):
        pass

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        refreshed: list[str] = []
        dummy = _DummyPanel()
        dummy._frequency_pack_rows = {"freq-manual": SimpleNamespace()}
        dummy._frequency_pack_info = {
            "freq-manual": SimpleNamespace(
                pack_id="freq-manual",
                display_name=lambda: "Manual Frequency",
            )
        }
        dummy._frequency_pack_paths = {"freq-manual": str(root / "manual" / "freq.sqlite")}
        dummy._managed_frequency_pack_ids = set()
        dummy._frequency_pack_storage_dir = lambda pack: root / "frequency_packs" / pack.pack_id
        dummy._frequency_archive_path = lambda pack: str(
            root / "frequency_packs" / pack.pack_id / "archive.zip"
        )
        dummy._frequency_sqlite_path = lambda pack: str(
            root / "frequency_packs" / pack.pack_id / "main.sqlite"
        )
        dummy._is_frequency_pack_data_path = lambda path: False
        dummy._refresh_frequency_pack_table = lambda: refreshed.append("frequency")
        dummy._set_status_message = lambda *args, **kwargs: None

        with patch(
            "settings_language_packs.localized_question",
            return_value=QMessageBox.Yes,
        ) as question_mock:
            LanguagePackPanel._delete_frequency_pack(dummy, "freq-manual")

    question_mock.assert_called_once()
    assert dummy.managed_frequency_pack_ids() == []
    assert dummy.frequency_paths() == {}
    assert refreshed == ["frequency"]
