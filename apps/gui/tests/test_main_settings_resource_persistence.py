from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QDialog

from lexishift_core import AppSettings, SynonymSourceSettings
from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from main import MainWindow


def _build_resource_panel(*, frequency_paths: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(
        paths=lambda: {
            "wordnet-en": "/tmp/wordnet",
            "moby-en": "/tmp/moby",
        },
        managed_language_pack_ids=lambda: ["freedict-en-es"],
        frequency_paths=lambda: {
            key: value for key, value in dict(frequency_paths).items() if key != "freq-en-coca"
        },
        managed_frequency_pack_ids=lambda: ["freq-en-coca"],
        embedding_paths=lambda: {"embed-es-cc": "/tmp/cc.es.300.vec"},
        embedding_pair_pack_ids=lambda: {"en-es": ["embed-es-cc"]},
        embedding_pair_paths=lambda: {"en-es": ["/tmp/cc.es.300.vec"]},
        embedding_pair_enabled=lambda: {"en-es": True},
    )


def test_sync_resource_settings_from_dialog_updates_pack_maps() -> None:
    base_synonyms = SynonymSourceSettings(
        frequency_pack_paths={"freq-de-default": "/tmp/freq-de-default.sqlite"},
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
    assert synonyms.managed_frequency_pack_ids == ("freq-en-coca",)
    assert synonyms.managed_language_pack_ids == ("freedict-en-es",)
    assert "freq-en-coca" not in synonyms.frequency_pack_paths
    assert "freedict-en-es" not in synonyms.language_pack_paths
    assert synonyms.embedding_pair_pack_ids["en-es"] == ["embed-es-cc"]


def test_open_settings_persists_resource_links_on_cancel() -> None:
    base_synonyms = SynonymSourceSettings(
        frequency_pack_paths={"freq-de-default": "/tmp/freq-de-default.sqlite"},
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
    dummy._sync_resource_settings_from_dialog = lambda dialog: (
        MainWindow._sync_resource_settings_from_dialog(dummy, dialog)
    )

    with patch("main.SettingsDialog", _FakeSettingsDialog):
        MainWindow._open_settings(dummy)

    assert len(updates) == 1
    synonyms = updates[0].synonyms
    assert synonyms is not None
    assert synonyms.managed_frequency_pack_ids == ("freq-en-coca",)
    assert "freq-en-coca" not in synonyms.frequency_pack_paths


def test_resolve_frequency_pack_for_pair_prefers_manifest_backed_default_app_data_pack() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "frequency_packs" / "freq-en-coca"
        fallback = pack_root / "main.sqlite"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.write_text("placeholder", encoding="utf-8")
        write_installed_pack_manifest(
            root / "frequency_packs",
            pack_id="freq-en-coca",
            pack_kind="frequency",
            provider="wordfrequency",
            local_kind="file",
            build_mode="convert_archive",
            artifact_path=fallback,
            sqlite_filename="main.sqlite",
        )
        dummy = SimpleNamespace()

        with patch("main_srs_mixin._app_data_dir", return_value=root):
            resolved = MainWindow._resolve_frequency_pack_for_pair(
                dummy,
                "es-en",
                frequency_pack_paths={},
            )

    assert resolved is not None
    assert resolved.path.resolve(strict=False) == fallback.resolve(strict=False)
    assert resolved.pack_id == "freq-en-coca"
