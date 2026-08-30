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
from dialogs import build_synonym_resource_settings_from_panel
from main import MainWindow
from settings_language_packs_support import (
    LANGUAGE_RESOURCE_FAMILY_SECONDARY,
    LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
    LANGUAGE_RESOURCE_ORIGIN_MANAGED,
    LANGUAGE_RESOURCE_ORIGIN_MANUAL,
    LanguageResourceBinding,
)


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


def test_open_settings_resources_starts_on_resource_tab() -> None:
    called_kwargs: list[dict] = []

    dummy = SimpleNamespace()
    dummy._open_settings = lambda **kwargs: called_kwargs.append(kwargs)

    MainWindow._open_settings_resources(dummy)

    assert called_kwargs
    assert called_kwargs[0]["initial_tab"] == "resources"


def test_open_settings_resources_passes_pair_focus() -> None:
    called_kwargs: list[dict] = []

    dummy = SimpleNamespace()
    dummy._open_settings = lambda **kwargs: called_kwargs.append(kwargs)

    MainWindow._open_settings_resources(dummy, pair="en-es")

    assert called_kwargs
    assert called_kwargs[0]["initial_tab"] == "resources"
    assert called_kwargs[0]["initial_resource_pair"] == "en-es"


def test_open_settings_resources_passes_activation_session() -> None:
    called_kwargs: list[dict] = []

    dummy = SimpleNamespace()
    dummy._open_settings = lambda **kwargs: called_kwargs.append(kwargs)

    MainWindow._open_settings_resources(
        dummy,
        pair="en-es",
        activation_session="activation-1",
    )

    assert called_kwargs[0]["activation_session"] == "activation-1"


def test_open_settings_reuses_visible_dialog_for_activation() -> None:
    calls: list[object] = []

    class _ExistingDialog:
        def isVisible(self) -> bool:
            return True

        def focus_resources(self, pair: str | None) -> None:
            calls.append(("focus", pair))

        def show(self) -> None:
            calls.append("show")

        def raise_(self) -> None:
            calls.append("raise")

        def activateWindow(self) -> None:
            calls.append("activate")

    class _Logger:
        def log(self, label: str) -> None:
            calls.append(label)

    dummy = SimpleNamespace(
        _settings_dialog=_ExistingDialog(),
        _startup_logger=_Logger(),
    )

    MainWindow._open_settings(
        dummy,
        initial_tab="resources",
        initial_resource_pair="en-es",
        activation_session="activation-1",
    )

    assert ("focus", "en-es") in calls
    assert "settings_dialog.reused activation_session=activation-1" in calls
    assert "settings_dialog.shown activation_session=activation-1" in calls


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


def test_resolve_frequency_pack_for_pair_prefers_managed_artifact_over_same_key_path() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "frequency_packs" / "freq-en-coca"
        artifact = pack_root / "main.sqlite"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("placeholder", encoding="utf-8")
        stale = root / "manual.sqlite"
        stale.write_text("placeholder", encoding="utf-8")
        write_installed_pack_manifest(
            root / "frequency_packs",
            pack_id="freq-en-coca",
            pack_kind="frequency",
            provider="wordfrequency",
            local_kind="file",
            build_mode="convert_archive",
            artifact_path=artifact,
            sqlite_filename="main.sqlite",
        )
        dummy = SimpleNamespace()

        with patch("main_srs_mixin._app_data_dir", return_value=root):
            resolved = MainWindow._resolve_frequency_pack_for_pair(
                dummy,
                "es-en",
                frequency_pack_paths={"freq-en-coca": str(stale)},
                managed_frequency_pack_ids=("freq-en-coca",),
            )

    assert resolved is not None
    assert resolved.path.resolve(strict=False) == artifact.resolve(strict=False)
    assert resolved.pack_id == "freq-en-coca"


def test_resolve_frequency_pack_for_pair_falls_back_to_configured_path_when_managed_artifact_missing() -> (
    None
):
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        manual = root / "manual.sqlite"
        manual.write_text("placeholder", encoding="utf-8")
        dummy = SimpleNamespace()

        with patch("main_srs_mixin._app_data_dir", return_value=root):
            resolved = MainWindow._resolve_frequency_pack_for_pair(
                dummy,
                "es-en",
                frequency_pack_paths={"freq-en-coca": str(manual)},
                managed_frequency_pack_ids=("freq-en-coca",),
            )

    assert resolved is not None
    assert resolved.path.resolve(strict=False) == manual.resolve(strict=False)
    assert resolved.pack_id == "manual"


def test_build_synonym_resource_settings_from_panel_preserves_non_ui_fields() -> None:
    base = SynonymSourceSettings(last_selected_pack_ids=("freedict-en-es",))
    panel = _build_resource_panel(
        frequency_paths={
            "freq-de-default": "/tmp/freq-de-default.sqlite",
            "freq-en-coca": "/tmp/freq-en-coca.sqlite",
        }
    )

    resolved = build_synonym_resource_settings_from_panel(
        panel,
        base_synonyms=base,
    )

    assert resolved.last_selected_pack_ids == ("freedict-en-es",)
    assert resolved.managed_language_pack_ids == ("freedict-en-es",)
    assert resolved.managed_frequency_pack_ids == ("freq-en-coca",)


def test_build_synonym_resource_settings_from_panel_prefers_language_bindings() -> None:
    panel = SimpleNamespace(
        language_resource_bindings=lambda: {
            "freedict-en-es": LanguageResourceBinding(
                pack_id="freedict-en-es",
                family=LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANAGED,
                effective_path="/tmp/freedict-en-es/main.sqlite",
            ),
            "wordnet-en": LanguageResourceBinding(
                pack_id="wordnet-en",
                family=LANGUAGE_RESOURCE_FAMILY_SECONDARY,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                effective_path="/tmp/wordnet",
            ),
        },
        managed_frequency_pack_ids=lambda: ["freq-en-coca"],
        frequency_paths=lambda: {},
        embedding_paths=lambda: {},
        embedding_pair_pack_ids=lambda: {},
        embedding_pair_paths=lambda: {},
        embedding_pair_enabled=lambda: {},
    )

    resolved = build_synonym_resource_settings_from_panel(panel)

    assert resolved.managed_language_pack_ids == ("freedict-en-es",)
    assert resolved.language_pack_paths == {"wordnet-en": "/tmp/wordnet"}
    assert resolved.wordnet_dir == "/tmp/wordnet"


def test_build_synonym_resource_settings_from_panel_preserves_secondary_bindings() -> None:
    panel = SimpleNamespace(
        language_resource_bindings=lambda: {
            "wordnet-en": LanguageResourceBinding(
                pack_id="wordnet-en",
                family=LANGUAGE_RESOURCE_FAMILY_SECONDARY,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                effective_path="/tmp/wordnet",
            ),
            "moby-en": LanguageResourceBinding(
                pack_id="moby-en",
                family=LANGUAGE_RESOURCE_FAMILY_SECONDARY,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                effective_path="/tmp/moby.txt",
            ),
        },
        managed_frequency_pack_ids=lambda: [],
        frequency_paths=lambda: {},
        embedding_paths=lambda: {},
        embedding_pair_pack_ids=lambda: {},
        embedding_pair_paths=lambda: {},
        embedding_pair_enabled=lambda: {},
    )

    resolved = build_synonym_resource_settings_from_panel(panel)

    assert resolved.language_pack_paths == {
        "wordnet-en": "/tmp/wordnet",
        "moby-en": "/tmp/moby.txt",
    }
    assert resolved.wordnet_dir == "/tmp/wordnet"
    assert resolved.moby_path == "/tmp/moby.txt"
