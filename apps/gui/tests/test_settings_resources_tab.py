from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from dialogs import SettingsDialog
from i18n import set_locale, t
from lexishift_core import AppSettings


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_settings_has_dedicated_resources_tab() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    tabs = dialog._tabs
    assert tabs.count() == 5
    assert tabs.tabText(1) == t("language_packs.title")


def test_settings_can_open_directly_to_resources_tab() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
    )

    assert dialog._tabs.currentIndex() == 1


def test_settings_app_tab_no_longer_contains_language_pack_panel() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    app_tab = dialog._tabs.widget(0)
    matches = app_tab.findChildren(type(dialog.language_pack_panel))
    assert not matches


def test_resources_tab_has_dedicated_resource_subviews() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    tabs = panel._resource_tabs

    assert tabs.count() == 4
    assert tabs.tabText(0) == t("language_packs.title")
    assert tabs.tabText(1) == t("language_packs.frequency_title")
    assert tabs.tabText(2) == t("language_packs.embeddings_title")
    assert tabs.tabText(3) == t("language_packs.cross_embeddings_title")


def test_language_pack_tab_describes_installed_vs_manual_contract() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    language_tab = panel._resource_tabs.widget(0)
    labels = language_tab.findChildren(type(panel.language_pack_status))

    assert any(label.text() == t("language_packs.language_description") for label in labels)


def test_resources_tab_intro_describes_installed_vs_manual_contract() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    resources_tab = dialog._tabs.widget(1)
    labels = resources_tab.findChildren(type(dialog.language_pack_panel.language_pack_status))
    description = t("language_packs.resources_description").lower()

    assert "installed" in description
    assert "manual" in description
    assert "import" in description
    assert any(label.text() == t("language_packs.resources_description") for label in labels)


def test_settings_srs_connections_button_uses_static_hub_label() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)

    assert dialog.install_helper_button.text() == t("menu.browser_connections")


def test_frequency_and_embedding_tabs_describe_manual_paths_as_compatibility_only() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel

    frequency_text = t("language_packs.frequency_description").lower()
    embeddings_help = t("language_packs.embeddings_help").lower()
    embeddings_text = t("language_packs.embeddings_description").lower()
    cross_help = t("language_packs.cross_embeddings_help").lower()
    cross_text = t("language_packs.cross_embeddings_description").lower()

    assert "default" in frequency_text
    assert "manual" in frequency_text
    assert "compatibility" in frequency_text
    assert "default" in embeddings_help
    assert "manual" in embeddings_help
    assert "import" in embeddings_help
    assert "installed" in embeddings_text
    assert "manual" in embeddings_text
    assert "default" in cross_help
    assert "manual" in cross_help
    assert "import" in cross_help
    assert "installed" in cross_text
    assert "manual" in cross_text

    frequency_tab = panel._resource_tabs.widget(1)
    embedding_tab = panel._resource_tabs.widget(2)
    cross_embedding_tab = panel._resource_tabs.widget(3)
    label_type = type(panel.language_pack_status)

    assert any(
        label.text() == t("language_packs.frequency_description")
        for label in frequency_tab.findChildren(label_type)
    )
    assert any(
        label.text() == t("language_packs.embeddings_description")
        for label in embedding_tab.findChildren(label_type)
    )
    assert any(
        label.text() == t("language_packs.cross_embeddings_description")
        for label in cross_embedding_tab.findChildren(label_type)
    )
