from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QDialog

from lexishift_core import AppSettings, SynonymSourceSettings
from main import MainWindow


def _build_resource_panel(*, frequency_paths: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(
        paths=lambda: {
            "wordnet-en": "/tmp/wordnet",
            "moby-en": "/tmp/moby",
            "freedict-en-es": "/tmp/freedict-eng-spa.tei",
        },
        frequency_paths=lambda: dict(frequency_paths),
        embedding_paths=lambda: {"embed-es-cc": "/tmp/cc.es.300.vec"},
        embedding_pair_paths=lambda: {"en-es": ["/tmp/cc.es.300.vec"]},
        embedding_pair_enabled=lambda: {"en-es": True},
    )


def test_sync_resource_settings_from_dialog_updates_pack_maps() -> None:
    base_synonyms = SynonymSourceSettings(
        frequency_packs={"freq-de-default": "/tmp/freq-de-default.sqlite"},
    )
    state = SimpleNamespace(
        settings=AppSettings(synonyms=base_synonyms),
    )
    updates: list[AppSettings] = []
    state.update_settings = lambda settings: updates.append(settings)
    panel = _build_resource_panel(
        frequency_paths={
            "freq-de-default": "/tmp/freq-de-default.sqlite",
            "freq-en-coca": "/tmp/freq-en-coca.sqlite",
        }
    )
    dialog = SimpleNamespace(language_pack_panel=panel)
    dummy = SimpleNamespace(state=state)

    MainWindow._sync_resource_settings_from_dialog(dummy, dialog)

    assert len(updates) == 1
    synonyms = updates[0].synonyms
    assert synonyms is not None
    assert synonyms.wordnet_dir == "/tmp/wordnet"
    assert synonyms.moby_path == "/tmp/moby"
    assert synonyms.frequency_packs["freq-en-coca"] == "/tmp/freq-en-coca.sqlite"
    assert synonyms.language_packs["freedict-en-es"] == "/tmp/freedict-eng-spa.tei"


def test_open_settings_persists_resource_links_on_cancel() -> None:
    base_synonyms = SynonymSourceSettings(
        frequency_packs={"freq-de-default": "/tmp/freq-de-default.sqlite"},
    )
    state = SimpleNamespace(
        settings=AppSettings(synonyms=base_synonyms),
        dataset=SimpleNamespace(settings=None),
    )
    updates: list[AppSettings] = []
    state.update_settings = lambda settings: updates.append(settings)
    panel = _build_resource_panel(
        frequency_paths={
            "freq-de-default": "/tmp/freq-de-default.sqlite",
            "freq-en-coca": "/tmp/freq-en-coca.sqlite",
        }
    )

    class _FakeSettingsDialog:
        def __init__(self, *args, **kwargs) -> None:
            self.language_pack_panel = panel

        def exec(self):
            return QDialog.DialogCode.Rejected

    dummy = SimpleNamespace(state=state)
    dummy._sync_resource_settings_from_dialog = lambda dialog: MainWindow._sync_resource_settings_from_dialog(
        dummy, dialog
    )

    with patch("main.SettingsDialog", _FakeSettingsDialog):
        MainWindow._open_settings(dummy)

    assert len(updates) == 1
    synonyms = updates[0].synonyms
    assert synonyms is not None
    assert synonyms.frequency_packs["freq-en-coca"] == "/tmp/freq-en-coca.sqlite"


def test_resolve_frequency_db_for_pair_falls_back_to_default_app_data_pack() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        fallback = root / "frequency_packs" / "freq-en-coca.sqlite"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.write_text("placeholder", encoding="utf-8")
        dummy = SimpleNamespace()

        with patch("main._app_data_dir", return_value=root):
            resolved = MainWindow._resolve_frequency_db_for_pair(
                dummy,
                "es-en",
                frequency_packs={},
            )

    assert resolved == fallback
