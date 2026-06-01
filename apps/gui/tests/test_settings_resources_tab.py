from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressBar

from dialogs import SettingsDialog
from i18n import set_locale, t
from lexishift_core import AppSettings
import settings_language_packs_pair_setup_mixin as pair_setup_mixin


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _clear_learning_pairs() -> None:
    QSettings().remove("resources/learning_pairs")


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


def test_settings_resource_pair_focus_adds_learning_language_card() -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel

    assert panel._resource_tabs.currentIndex() == 0
    assert "en-es" in panel._learning_pair_keys
    learning_tab = panel._resource_tabs.widget(0)
    labels = learning_tab.findChildren(type(panel.language_pack_status))
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    label_text = "\n".join(label.text() for label in labels)
    button_text = {button.text() for button in buttons}

    assert "English to Spanish" in label_text
    assert "Spanish word frequency data" in label_text
    assert "Spanish-English dictionary" in label_text
    assert t("language_packs.learning_pairs.download_missing") in button_text
    assert t("language_packs.learning_pairs.show_file_location") in button_text
    assert "Add manually" not in button_text


def test_learning_pair_card_labels_are_localized() -> None:
    _app()
    set_locale("ja")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel
    learning_tab = panel._resource_tabs.widget(0)
    labels = learning_tab.findChildren(type(panel.language_pack_status))
    label_text = "\n".join(label.text() for label in labels)

    assert t("language_packs.learning_pairs.pairs.en_es") in label_text
    assert t("language_packs.learning_pairs.resources.freq_es_cde") in label_text
    assert t("language_packs.learning_pairs.resources.wiktionary_es_en") in label_text
    assert t("language_packs.learning_pairs.resources.freedict_es_en") in label_text
    assert "English to Spanish" not in label_text
    assert "Spanish word frequency data" not in label_text


def test_manual_learning_pair_resource_does_not_show_download_progress(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel
    freq_item = next(item for item in panel._pair_resource_items() if item.pack_id == "freq-es-cde")

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: False if item.pack_id == "freq-es-cde" else True,
    )

    panel._refresh_learning_pair_cards()
    learning_tab = panel._resource_tabs.widget(0)
    progress_bars = learning_tab.findChildren(QProgressBar)

    assert panel._download_disabled_for_pair_resource(freq_item)
    assert not panel._frequency_pack_rows["freq-es-cde"].download_button.isEnabled()
    assert not panel._pair_resource_download_active(freq_item)
    assert not any(bar.isVisible() for bar in progress_bars)


def test_manual_learning_pair_resource_shows_instructions_without_switching_tabs(
    monkeypatch,
) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel
    freq_item = next(item for item in panel._pair_resource_items() if item.pack_id == "freq-es-cde")
    shown: list[str] = []

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: False if item.pack_id == "freq-es-cde" else True,
    )
    monkeypatch.setattr(
        panel,
        "_show_learning_pair_manual_setup",
        lambda item: shown.append(item.pack_id),
    )

    panel._resource_tabs.setCurrentIndex(0)
    panel._open_learning_pair_resource_detail(freq_item)

    assert shown == ["freq-es-cde"]
    assert panel._resource_tabs.currentIndex() == 0


def test_learning_pair_resource_location_button_reveals_resolved_path(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel
    revealed: list[str] = []

    monkeypatch.setattr(panel, "_pair_resource_is_installed", lambda _item: True)
    monkeypatch.setattr(
        panel,
        "_pair_resource_resolved_path",
        lambda item: f"/tmp/{item.pack_id}.sqlite",
    )
    monkeypatch.setattr(pair_setup_mixin, "reveal_path", lambda path: revealed.append(path))

    panel._refresh_learning_pair_cards()
    learning_tab = panel._resource_tabs.widget(0)
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    location_buttons = [
        button
        for button in buttons
        if button.text() == t("language_packs.learning_pairs.show_file_location")
        and button.isEnabled()
    ]

    assert location_buttons

    location_buttons[0].click()

    assert revealed
    assert revealed[0].startswith("/tmp/")


def test_learning_pair_installed_resource_can_be_uninstalled_from_card(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel
    deleted: list[str] = []

    monkeypatch.setattr(panel, "_pair_resource_is_installed", lambda _item: True)
    monkeypatch.setattr(
        panel,
        "_pair_resource_resolved_path",
        lambda item: f"/tmp/{item.pack_id}.sqlite",
    )
    monkeypatch.setattr(panel, "_delete_frequency_pack", lambda pack_id: deleted.append(pack_id))
    monkeypatch.setattr(panel, "_delete_language_pack", lambda pack_id: deleted.append(pack_id))

    panel._refresh_learning_pair_cards()
    learning_tab = panel._resource_tabs.widget(0)
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    uninstall_buttons = [
        button
        for button in buttons
        if button.text() == t("language_packs.learning_pairs.uninstall_resource")
    ]

    assert len(uninstall_buttons) == len(panel._pair_resource_items())

    uninstall_buttons[0].click()

    assert deleted == ["freq-es-cde"]


def test_remove_learning_pair_confirms_when_pair_has_installed_resources(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-es",
    )
    panel = dialog.language_pack_panel
    messages: list[str] = []

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: item.pack_id == "freq-es-cde",
    )

    def cancel_remove(_parent, _title, message, *_args) -> QMessageBox.StandardButton:
        messages.append(message)
        return QMessageBox.Cancel

    monkeypatch.setattr(pair_setup_mixin, "localized_question", cancel_remove)

    panel._remove_learning_pair("en-es")

    assert panel._learning_pair_keys == ["en-es"]
    assert messages
    assert "Spanish word frequency data" in messages[0]

    monkeypatch.setattr(pair_setup_mixin, "localized_question", lambda *_args: QMessageBox.Yes)

    panel._remove_learning_pair("en-es")

    assert panel._learning_pair_keys == []


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

    assert tabs.count() == 5
    assert tabs.tabText(0) == t("language_packs.learning_pairs.tab_title")
    assert tabs.tabText(1) == t("language_packs.title")
    assert tabs.tabText(2) == t("language_packs.frequency_title")
    assert tabs.tabText(3) == t("language_packs.embeddings_title")
    assert tabs.tabText(4) == t("language_packs.cross_embeddings_title")


def test_resources_tab_uses_roomier_table_and_theme_contract() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    panel.set_theme(
        {
            "bg": "#111111",
            "panel_top": "#223344",
            "panel_bottom": "#334455",
            "panel_border": "#445566",
            "table_bg": "#556677",
            "table_sel_bg": "#667788",
            "text": "#F0F1F2",
            "muted": "#C0C1C2",
            "accent": "#D0A040",
            "accent_soft": "#384858",
            "primary": "#204060",
            "primary_hover": "#305070",
        }
    )
    language_tab = panel._resource_tabs.widget(1)
    labels = language_tab.findChildren(type(panel.language_pack_status))
    stylesheet = panel.styleSheet()

    assert panel._resource_tabs.objectName() == "lexishiftResourceTabs"
    assert language_tab.property("resourcePanelTab") is True
    assert panel.language_pack_table.minimumHeight() >= 460
    assert panel.language_pack_table.verticalHeader().defaultSectionSize() >= 38
    assert panel.frequency_pack_table.minimumHeight() >= 380
    assert 'QWidget[resourcePanelTab="true"]' in stylesheet
    assert "QTableWidget" in stylesheet
    assert "QTabWidget#lexishiftResourceTabs::pane" in stylesheet
    assert "#223344" in stylesheet
    assert "#556677" in stylesheet
    assert "#F0F1F2" in stylesheet
    assert any(label.property("resourceSectionTitle") is True for label in labels)
    assert any(label.property("resourceDescription") is True for label in labels)


def test_language_pack_tab_describes_installed_vs_manual_contract() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    language_tab = panel._resource_tabs.widget(1)
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

    frequency_tab = panel._resource_tabs.widget(2)
    embedding_tab = panel._resource_tabs.widget(3)
    cross_embedding_tab = panel._resource_tabs.widget(4)
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
