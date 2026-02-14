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
