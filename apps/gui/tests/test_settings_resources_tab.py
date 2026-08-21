from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QPalette, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
)

from dialogs import SettingsDialog
from dialogs_theme_utils import _ThemedTabContainer
from i18n import set_locale, t
from lexishift_core import AppSettings
import settings_language_packs_pair_setup_mixin as pair_setup_mixin
import settings_language_packs as language_packs_panel
from settings_language_packs_table_mixin import ResourcePackTable


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
    assert "Spanish POS overlay" in label_text
    assert "Spanish-English dictionary" in label_text
    assert "Sentence-veto semantic reference" in label_text
    assert t("language_packs.learning_pairs.download_missing") in button_text
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
    assert t("language_packs.learning_pairs.resources.freq_es_spalex") in label_text
    assert t("language_packs.learning_pairs.resources.pos_es_ud_ancora") in label_text
    assert t("language_packs.learning_pairs.resources.wiktionary_es_en") in label_text
    assert t("language_packs.learning_pairs.resources.freedict_es_en") in label_text
    assert t("language_packs.learning_pairs.resources.semantic_en_es_sentence_veto") in label_text
    assert "English to Spanish" not in label_text
    assert "Spanish word frequency data" not in label_text


def test_en_de_learning_pair_resource_card_uses_registry_resources() -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-de",
    )
    panel = dialog.language_pack_panel
    learning_tab = panel._resource_tabs.widget(0)
    labels = learning_tab.findChildren(type(panel.language_pack_status))
    label_text = "\n".join(label.text() for label in labels)

    assert "English to German" in label_text
    assert "German word frequency data" in label_text
    assert "German-English dictionary" in label_text
    assert "English-German dictionary" in label_text
    assert "Sentence-veto semantic reference" in label_text
    assert t("language_packs.pair_setup.not_available_yet") in label_text


def test_manual_frequency_source_candidate_can_be_imported_from_learning_pair_card(
    monkeypatch,
) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-ja",
    )
    panel = dialog.language_pack_panel
    candidate = "/tmp/BCCWJ_frequencylist_suw_ver1_0.zip"
    imported: list[tuple[str, str]] = []
    selected: list[str] = []

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: item.pack_id != "freq-ja-bccwj",
    )
    monkeypatch.setattr(
        panel,
        "_download_disabled_for_pair_resource",
        lambda item: item.pack_id == "freq-ja-bccwj",
    )
    monkeypatch.setattr(
        panel,
        "_manual_frequency_source_candidate_path",
        lambda pack: candidate if pack.pack_id == "freq-ja-bccwj" else None,
    )
    monkeypatch.setattr(
        panel,
        "_import_frequency_pack_candidate",
        lambda pack_id, source_path: imported.append((pack_id, source_path)),
    )
    monkeypatch.setattr(
        panel,
        "_select_frequency_pack_path",
        lambda pack_id: selected.append(pack_id),
    )

    panel._refresh_learning_pair_cards()
    QApplication.processEvents()
    learning_tab = panel._resource_tabs.widget(0)
    labels = learning_tab.findChildren(type(panel.language_pack_status))
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    label_text = "\n".join(label.text() for label in labels)
    import_buttons = [
        button
        for button in buttons
        if button.text() == t("language_packs.learning_pairs.import_downloaded")
    ]
    choose_buttons = [
        button
        for button in buttons
        if button.text() == t("language_packs.learning_pairs.import_file")
    ]

    assert t("language_packs.learning_pairs.downloaded_source_found") in label_text
    assert len(import_buttons) == 1
    assert choose_buttons

    import_buttons[0].click()
    bccwj_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "freq-ja-bccwj"
    )
    panel._select_learning_pair_resource_file(bccwj_item)

    assert imported == [("freq-ja-bccwj", candidate)]
    assert selected == ["freq-ja-bccwj"]


def test_installed_manual_supply_resource_omits_disabled_redownload_button(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-ja",
    )
    panel = dialog.language_pack_panel

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: item.pack_id == "freq-ja-bccwj",
    )
    monkeypatch.setattr(
        panel,
        "_pair_resource_resolved_path",
        lambda item: f"/tmp/{item.pack_id}.sqlite" if item.pack_id == "freq-ja-bccwj" else None,
    )
    monkeypatch.setattr(
        panel,
        "_download_disabled_for_pair_resource",
        lambda item: item.pack_id == "freq-ja-bccwj",
    )

    panel._refresh_learning_pair_cards()
    QApplication.processEvents()
    learning_tab = panel._resource_tabs.widget(0)
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    button_texts = [button.text() for button in buttons]

    assert t("buttons.redownload") not in button_texts
    assert t("language_packs.learning_pairs.show_file_location") in button_texts
    assert t("language_packs.learning_pairs.uninstall_resource") in button_texts


def test_resources_panel_rechecks_downloads_when_app_becomes_active(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-ja",
    )
    panel = dialog.language_pack_panel
    calls: list[str] = []

    monkeypatch.setattr(
        panel, "_refresh_pair_resource_setup_panel", lambda: calls.append("refresh")
    )

    panel._on_application_state_changed(Qt.ApplicationState.ApplicationActive)

    assert calls == ["refresh"]


def test_manual_supply_frequency_resource_is_download_disabled_by_catalog(
    monkeypatch,
) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-ja",
    )
    panel = dialog.language_pack_panel
    bccwj_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "freq-ja-bccwj"
    )
    jmdict_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "jmdict-ja-en"
    )

    monkeypatch.setattr(panel, "_pair_resource_is_installed", lambda _item: False)

    panel._refresh_learning_pair_cards()
    learning_tab = panel._resource_tabs.widget(0)
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    manual_buttons = [
        button
        for button in buttons
        if button.text() == t("language_packs.learning_pairs.manual_setup")
    ]

    assert panel._download_disabled_for_pair_resource(bccwj_item)
    assert not panel._download_disabled_for_pair_resource(jmdict_item)
    assert manual_buttons


def test_manual_setup_opens_provider_page_for_browser_prompt(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-ja",
    )
    panel = dialog.language_pack_panel
    bccwj_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "freq-ja-bccwj"
    )
    button_texts: list[str] = []
    opened_urls: list[str] = []

    def fake_exec(message_box: QMessageBox) -> int:
        buttons = message_box.buttons()
        button_texts.extend(button.text() for button in buttons)
        for button in buttons:
            if button.text() == t("language_packs.learning_pairs.open_provider_page"):
                button.click()
                break
        return 0

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    monkeypatch.setattr(pair_setup_mixin.webbrowser, "open", lambda url: opened_urls.append(url))

    panel._show_learning_pair_manual_setup(bccwj_item)

    assert t("language_packs.learning_pairs.open_provider_page") in button_texts
    assert opened_urls == [
        panel._manual_pack_source_page_url(panel._pair_resource_pack(bccwj_item))
    ]


def test_learning_pair_cards_keep_creation_order_when_focus_changes() -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    QSettings().setValue("resources/learning_pairs", ["en-es", "en-de"])
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-de",
    )
    panel = dialog.language_pack_panel

    assert [plan.pair for plan in panel._ordered_learning_pair_plans()] == ["en-es", "en-de"]


def test_learning_pair_add_control_only_offers_pairs_not_already_shown() -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    QSettings().setValue("resources/learning_pairs", ["en-es"])
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
    )
    panel = dialog.language_pack_panel
    combo = panel._learning_pair_combo

    assert [plan.pair for plan in panel._ordered_learning_pair_plans()] == ["en-es"]
    assert combo.count() == 2
    assert combo.itemData(0) == "en-de"
    assert combo.itemData(1) == "en-ja"
    assert panel._learning_pair_add_button.isEnabled()

    panel._add_selected_learning_pair()

    assert [plan.pair for plan in panel._ordered_learning_pair_plans()] == ["en-es", "en-de"]
    assert combo.count() == 1
    assert combo.itemData(0) == "en-ja"
    assert combo.isEnabled()
    assert not combo.isHidden()
    assert panel._learning_pair_add_button.isEnabled()
    assert not panel._learning_pair_add_button.isHidden()
    assert panel._learning_pair_add_status_label.isHidden()

    panel._add_selected_learning_pair()

    assert [plan.pair for plan in panel._ordered_learning_pair_plans()] == [
        "en-es",
        "en-de",
        "en-ja",
    ]
    assert combo.count() == 0
    assert combo.isHidden()
    assert panel._learning_pair_add_button.isHidden()
    assert not panel._learning_pair_add_status_label.isHidden()
    _clear_learning_pairs()


def test_downloadable_learning_pair_resource_does_not_show_progress_until_download_starts(
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
    freq_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "freq-es-spalex-v1"
    )

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: False if item.pack_id == "freq-es-spalex-v1" else True,
    )

    panel._refresh_learning_pair_cards()
    learning_tab = panel._resource_tabs.widget(0)
    progress_bars = learning_tab.findChildren(QProgressBar)

    assert not panel._download_disabled_for_pair_resource(freq_item)
    assert panel._frequency_pack_rows["freq-es-spalex-v1"].download_button.isEnabled()
    assert not panel._pair_resource_download_active(freq_item)
    assert not any(bar.isVisible() for bar in progress_bars)


def test_optional_learning_pair_resource_does_not_block_ready_status(monkeypatch) -> None:
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

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: item.pack_id != "pos-es-ud-ancora-v1",
    )

    panel._refresh_learning_pair_cards()
    learning_tab = panel._resource_tabs.widget(0)
    labels = learning_tab.findChildren(type(panel.language_pack_status))
    label_text = "\n".join(label.text() for label in labels)

    assert t("language_packs.pair_setup.status_ready") in label_text
    assert t("language_packs.pair_setup.recommended") in label_text


def test_learning_pair_pos_overlay_download_uses_overlay_downloader(monkeypatch) -> None:
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
    started: list[str] = []
    pos_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "pos-es-ud-ancora-v1"
    )
    pos_pack = panel._pos_overlay_pack_info["pos-es-ud-ancora-v1"]

    monkeypatch.setattr(
        panel, "_download_pos_overlay_pack", lambda pack_id: started.append(pack_id)
    )

    panel._download_learning_pair_resource(pos_item)

    assert started == ["pos-es-ud-ancora-v1"]
    assert Path(panel._pos_overlay_sqlite_path(pos_pack)).parts[-3:] == (
        "pos_packs",
        "pos-es-ud-ancora-v1",
        "main.sqlite",
    )


def test_learning_pair_semantic_pack_installs_pair_level_copy(tmp_path) -> None:
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
    panel._language_pack_dir = str(tmp_path / "language_packs")
    semantic_item = next(
        item for item in panel._pair_resource_items() if item.kind == "semantic_pack"
    )

    assert semantic_item.available
    assert not panel._pair_resource_is_installed(semantic_item)

    panel._download_learning_pair_resource(semantic_item)

    inventory_path = tmp_path / "language_packs" / "en-es" / "semantic_packs"
    inventory_path = (
        inventory_path
        / "en-es-active-only-combined-full-v1-tranche-011"
        / "semantic_inventory.json"
    )
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))

    assert payload["pair"] == "en-es"
    assert panel._pair_resource_is_installed(semantic_item)
    assert "Installed Sentence-veto semantic reference" in panel.language_pack_status.text()


def test_learning_pair_pending_semantic_pack_is_informational(monkeypatch) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-de",
    )
    panel = dialog.language_pack_panel

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: item.kind != "semantic_pack",
    )

    panel._refresh_learning_pair_cards()
    semantic_item = next(
        item for item in panel._pair_resource_items() if item.kind == "semantic_pack"
    )
    missing_pack_ids = [item.pack_id for item in panel._pair_resource_missing_items()]

    assert not semantic_item.available
    assert semantic_item.pack_id not in missing_pack_ids
    assert panel._learning_pair_status_text(3, 3) == t("language_packs.pair_setup.status_ready")


def test_downloadable_learning_pair_resource_detail_keeps_single_tab_surface(
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
    freq_item = next(
        item for item in panel._pair_resource_items() if item.pack_id == "freq-es-spalex-v1"
    )
    shown: list[str] = []

    monkeypatch.setattr(
        panel,
        "_pair_resource_is_installed",
        lambda item: False if item.pack_id == "freq-es-spalex-v1" else True,
    )
    monkeypatch.setattr(
        panel,
        "_show_learning_pair_manual_setup",
        lambda item: shown.append(item.pack_id),
    )

    panel._resource_tabs.setCurrentIndex(0)
    panel._open_learning_pair_resource_detail(freq_item)

    assert shown == []
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


def test_learning_pair_resource_source_license_button_opens_pack_dialog(monkeypatch) -> None:
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
    shown: list[tuple[str, str | None]] = []

    monkeypatch.setattr(
        panel,
        "_show_pack_source_license",
        lambda pack, resolved_path=None: shown.append((pack.pack_id, resolved_path)),
    )

    learning_tab = panel._resource_tabs.widget(0)
    buttons = learning_tab.findChildren(type(panel.open_language_pack_button))
    info_buttons = [
        button for button in buttons if button.text() == t("language_packs.source_license.button")
    ]

    assert info_buttons

    info_buttons[0].click()

    assert shown
    assert shown[0][0] in {item.pack_id for item in panel._pair_resource_items()}


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
    monkeypatch.setattr(panel, "_delete_pos_overlay_pack", lambda pack_id: deleted.append(pack_id))

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

    assert deleted == ["freq-es-spalex-v1"]


def test_frequency_pack_delete_refreshes_learning_pair_cards(monkeypatch, tmp_path) -> None:
    _app()
    set_locale("en")
    _clear_learning_pairs()
    dialog = SettingsDialog(
        app_settings=AppSettings(),
        dataset_settings=None,
        initial_tab="resources",
        initial_resource_pair="en-ja",
    )
    panel = dialog.language_pack_panel
    panel._frequency_pack_dir = str(tmp_path / "frequency_packs")
    pack_root = Path(panel._frequency_pack_dir) / "freq-ja-bccwj"
    pack_root.mkdir(parents=True)
    (pack_root / "main.sqlite").write_bytes(b"SQLite format 3\x00")
    refreshes: list[str] = []

    monkeypatch.setattr(
        language_packs_panel,
        "localized_question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )
    monkeypatch.setattr(
        panel, "_refresh_pair_resource_setup_panel", lambda: refreshes.append("yes")
    )

    panel._delete_frequency_pack("freq-ja-bccwj")

    assert not pack_root.exists()
    assert refreshes == ["yes"]


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
        lambda item: item.pack_id == "freq-es-spalex-v1",
    )

    def cancel_remove(_parent, _title, message, *_args) -> QMessageBox.StandardButton:
        messages.append(message)
        return QMessageBox.Cancel

    monkeypatch.setattr(pair_setup_mixin, "localized_question", cancel_remove)

    panel._remove_learning_pair("en-es")

    assert panel._learning_pair_keys == ["en-es"]
    assert messages
    assert "SPALEX Spanish word frequency data" in messages[0]

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


def test_resources_tab_shows_learning_languages_and_lookup_dictionaries() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    tabs = panel._resource_tabs

    assert tabs.count() == 2
    assert tabs.tabText(0) == t("language_packs.learning_pairs.tab_title")
    assert tabs.tabText(1) == t("language_packs.lookup_dictionaries.tab_title")


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
    learning_tab = panel._resource_tabs.widget(0)
    labels = learning_tab.findChildren(type(panel.language_pack_status))
    stylesheet = panel.styleSheet()

    assert panel._resource_tabs.objectName() == "lexishiftResourceTabs"
    assert learning_tab.property("resourcePanelTab") is True
    assert panel.language_pack_table.minimumHeight() >= 460
    assert panel.language_pack_table.verticalHeader().defaultSectionSize() >= 38
    assert panel.language_pack_table.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert panel.language_pack_table.horizontalScrollMode() == QAbstractItemView.ScrollPerPixel
    assert (
        panel.language_pack_table.horizontalHeader().sectionResizeMode(0) == QHeaderView.Interactive
    )
    assert panel.language_pack_table.columnWidth(0) >= 240
    assert panel.language_pack_table.columnWidth(3) >= 150
    table_button = panel.language_pack_table.cellWidget(0, 4)
    assert table_button.property("resourceTableAction") is True
    assert table_button.sizePolicy().verticalPolicy() == QSizePolicy.Fixed
    assert panel.frequency_pack_table.minimumHeight() >= 380
    assert 'QWidget[resourcePanelTab="true"]' in stylesheet
    assert 'QWidget[resourcePanelTab="true"], QWidget[resourcePanelCanvas="true"]' in stylesheet
    assert "background: transparent;" in stylesheet
    assert "QTableWidget" in stylesheet
    assert "QTabWidget#lexishiftResourceTabs::pane" in stylesheet
    assert "QFrame#learningLanguagePairCard" in stylesheet
    assert "background: rgba(85, 102, 119, 230);" in stylesheet
    assert "alternate-background-color: rgba(34, 51, 68, 230);" in stylesheet
    assert "QComboBox QAbstractItemView" in stylesheet
    assert "selection-background-color: #667788;" in stylesheet
    popup_view = panel._learning_pair_combo.view()
    assert popup_view.property("lexishiftThemedComboPopup") is True
    assert "background: #556677;" in popup_view.styleSheet()
    assert popup_view.palette().color(QPalette.Base).name().upper() == "#556677"
    assert 'QTableWidget QPushButton[resourceTableAction="true"]' in stylesheet
    assert "max-height: 24px;" in stylesheet
    assert "background: rgba(85, 102, 119, 87);" in stylesheet
    assert "background: rgba(51, 68, 85, 56);" in stylesheet
    assert "QFrame#learningLanguagePairCard QLabel {\n  color: #F0F1F2;" in stylesheet
    assert "#223344" in stylesheet
    assert "#556677" in stylesheet
    assert "#F0F1F2" in stylesheet
    assert any(label.property("resourceSectionTitle") is True for label in labels)
    assert any(label.property("resourceDescription") is True for label in labels)


def test_resource_tables_expose_source_license_info_actions(monkeypatch) -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    shown: list[str] = []

    monkeypatch.setattr(
        panel,
        "_show_pack_source_license",
        lambda pack, resolved_path=None: shown.append(pack.pack_id),
    )

    language_button = panel.language_pack_table.cellWidget(0, 8)
    frequency_button = panel.frequency_pack_table.cellWidget(0, 8)
    embedding_button = panel.embedding_pack_table.cellWidget(0, 8)

    assert language_button.accessibleName() == t("language_packs.source_license.button")
    assert frequency_button.accessibleName() == t("language_packs.source_license.button")
    assert embedding_button.accessibleName() == t("language_packs.source_license.button")

    language_button.click()
    frequency_button.click()
    embedding_button.click()

    assert shown == [
        panel._language_packs[0].pack_id,
        panel._frequency_packs[0].pack_id,
        panel._embedding_packs[0].pack_id,
    ]


def test_resource_pack_table_distributes_surplus_width_without_viewport_gutter() -> None:
    app = _app()
    table = ResourcePackTable()
    table.setColumnCount(3)
    table.configure_resource_columns({0: 100, 1: 80, 2: 60}, surplus_columns=(0, 2))
    table.resize(420, 120)
    table.show()
    app.processEvents()
    table._apply_responsive_column_widths()

    column_total = sum(table.columnWidth(column) for column in range(table.columnCount()))

    assert column_total >= table.viewport().width()
    assert table.columnWidth(0) > 100
    assert table.columnWidth(1) == 80


def test_resources_tab_style_falls_back_when_theme_text_lacks_contrast() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel

    panel.set_theme(
        {
            "bg": "#242424",
            "panel_top": "#FFFFFF",
            "panel_bottom": "#FFFFFF",
            "panel_border": "#333333",
            "table_bg": "#FFFFFF",
            "table_sel_bg": "#FFFFFF",
            "text": "#252525",
            "muted": "#252525",
            "accent": "#252525",
            "accent_soft": "#FFFFFF",
            "primary": "#252525",
            "primary_hover": "#252525",
        }
    )
    stylesheet = panel.styleSheet()

    assert "background: transparent;" in stylesheet
    assert 'QLabel[resourceSectionTitle="true"] {\n  color: #FFFFFF;' in stylesheet
    assert 'QLabel[resourceDescription="true"] {\n  color: #FFFFFF;' in stylesheet
    assert "font-size: 15px;" in stylesheet
    assert "font-size: 13px;" in stylesheet


def test_resources_tab_table_opacity_uses_theme_surface_opacity() -> None:
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
            "_surface_opacities": {"table": 0.72},
        }
    )

    stylesheet = panel.styleSheet()

    assert "background: rgba(85, 102, 119, 184);" in stylesheet
    assert "alternate-background-color: rgba(34, 51, 68, 184);" in stylesheet


def test_settings_resource_tab_omits_legacy_intro_label() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    resources_tab = dialog._tabs.widget(1)
    labels = resources_tab.findChildren(type(dialog.language_pack_panel.language_pack_status))

    assert not any(label.objectName() == "settingsIntroLabel" for label in labels)


def test_settings_combo_dropdowns_follow_theme_style() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    view = dialog.theme_combo.view()
    language_view = dialog.language_combo.view()

    assert view.property("lexishiftThemedComboPopup") is True
    assert language_view.property("lexishiftThemedComboPopup") is True
    assert "QListView" in view.styleSheet()
    assert "selection-background-color: #E7D9C6;" in view.styleSheet()
    assert view.palette().color(QPalette.Base).name().upper() == "#FFFFFF"


def test_themed_tab_container_paints_theme_base_without_viewport_fallback() -> None:
    _app()
    container = _ThemedTabContainer()
    container.resize(120, 80)
    container.set_base_style(
        top="#FFF7FD",
        bottom="#EFE6F5",
        border="#D8CBE6",
        radius=10,
    )
    container.set_background(
        image_path=None,
        opacity=1.0,
        position="center",
        size="cover",
        repeat="no-repeat",
    )

    pixmap = QPixmap(container.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    container.render(pixmap)
    image = pixmap.toImage()

    assert QColor(image.pixel(60, 10)).name().upper() == "#FDF5FC"
    assert QColor(image.pixel(60, 40)).name().upper() == "#F7EEF9"
    assert QColor(image.pixel(60, 10)).name().upper() != "#EFEFEF"


def test_language_pack_tab_describes_installed_vs_manual_contract() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    panel = dialog.language_pack_panel
    language_tab = panel._build_language_pack_tab()
    labels = language_tab.findChildren(type(panel.language_pack_status))

    assert any(label.text() == t("language_packs.language_description") for label in labels)


def test_resources_tab_does_not_render_legacy_intro_copy() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    resources_tab = dialog._tabs.widget(1)
    labels = resources_tab.findChildren(type(dialog.language_pack_panel.language_pack_status))

    assert not any(label.text() == t("language_packs.resources_description") for label in labels)


def test_settings_srs_connections_button_uses_static_hub_label() -> None:
    _app()
    set_locale("en")
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)

    assert dialog.install_helper_button.text() == t("menu.browser_connections")


def test_integrations_tab_uses_square_tiles_without_desktop_app_link(monkeypatch) -> None:
    _app()
    set_locale("en")
    opened: list[str] = []
    monkeypatch.setattr("dialogs.open_integration_link", lambda key: opened.append(key))
    dialog = SettingsDialog(app_settings=AppSettings(), dataset_settings=None)
    integrations_tab = dialog._tabs.widget(4)

    buttons = [
        button
        for button in integrations_tab.findChildren(QPushButton)
        if button.objectName() == "integrationTileButton"
    ]
    labels = [
        label.text()
        for label in integrations_tab.findChildren(
            type(dialog.language_pack_panel.language_pack_status)
        )
        if label.property("integrationTileLabel") is True
    ]

    assert [button.property("integrationLinkKey") for button in buttons] == [
        "chrome_extension",
        "betterdiscord_plugin",
        "website",
    ]
    assert [button.property("integrationIconKey") for button in buttons] == [
        "extension",
        "plugin",
        "lexishift",
    ]
    assert all(button.text() == "" for button in buttons)
    assert all(button.width() == button.height() == 108 for button in buttons)
    assert all(not button.icon().isNull() for button in buttons)
    assert labels == [
        t("integrations.extension_button"),
        t("integrations.plugin_button"),
        t("integrations.website_button"),
    ]
    assert "app_download" not in [button.property("integrationLinkKey") for button in buttons]

    for button in buttons:
        button.click()

    assert opened == ["chrome_extension", "betterdiscord_plugin", "website"]


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

    frequency_tab = panel._build_frequency_pack_tab()
    embedding_tab = panel._build_embedding_pack_tab()
    cross_embedding_tab = panel._build_cross_embedding_pack_tab()
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
