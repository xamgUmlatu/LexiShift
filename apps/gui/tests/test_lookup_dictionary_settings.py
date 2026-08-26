from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QTableWidget

from i18n import set_locale
from lexishift_core.helper.lookup_dictionary_settings import (
    load_lookup_dictionary_settings,
    lookup_dictionary_pack_ids_for_pair,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import (
    import_yomitan_dictionary_zip,
)
from settings_language_packs import LanguagePackPanel
from settings_lookup_dictionaries_mixin import (
    _compatible_lookup_dictionary_directory_url,
)
from settings_lookup_dictionary_stack_mixin import _lookup_pair_builtin_source


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _write_yomitan_zip(
    path: Path,
    *,
    title: str = "Local Japanese Dictionary",
) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "index.json",
            json.dumps(
                {
                    "title": title,
                    "revision": "2026.1",
                    "format": 3,
                    "sourceLanguage": "ja",
                    "targetLanguage": "ja",
                },
                ensure_ascii=False,
            ),
        )
        archive.writestr(
            "term_bank_1.json",
            json.dumps(
                [["時", "とき", "", "n", 1, ["time"], 1, ""]],
                ensure_ascii=False,
            ),
        )


def _add_dictionary_to_current_pair(panel: LanguagePackPanel, pack_id: str) -> None:
    index = panel._lookup_dictionary_add_combo.findData(pack_id)
    assert index > 0
    panel._lookup_dictionary_add_combo.setCurrentIndex(index)
    assert panel._lookup_dictionary_add_button.isEnabled()
    panel._lookup_dictionary_add_button.click()


def _stack_action_button(
    panel: LanguagePackPanel,
    *,
    row: int,
    label: str,
) -> QPushButton:
    actions = panel._lookup_dictionary_order_table.cellWidget(row, 3)
    assert actions is not None
    return next(
        button
        for button in actions.findChildren(QPushButton)
        if button.text() == label or button.accessibleName() == label
    )


def test_compatible_lookup_dictionary_directory_url_is_target_aware() -> None:
    japanese_url = _compatible_lookup_dictionary_directory_url("en-ja")

    assert japanese_url == (
        "https://github.com/MarvNC/yomitan-dictionaries#daijirin-fourth-edition"
    )
    assert _compatible_lookup_dictionary_directory_url("ja-ja") == japanese_url
    assert _compatible_lookup_dictionary_directory_url("en-de") == (
        "https://github.com/MarvNC/yomitan-dictionaries"
    )


def test_builtin_lookup_source_support_is_reported_per_pair() -> None:
    assert _lookup_pair_builtin_source("en-ja") == "jmdict"
    assert _lookup_pair_builtin_source("en-es") == "translation"
    assert _lookup_pair_builtin_source("en-de") == "translation"
    assert _lookup_pair_builtin_source("ja-ja") == ""
    assert _lookup_pair_builtin_source("es-es") == ""


def test_language_pack_panel_exposes_lookup_dictionary_tab() -> None:
    _app()
    set_locale("en")
    with tempfile.TemporaryDirectory() as tmp:
        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(Path(tmp) / "lookup_dictionaries"),
        ):
            panel = LanguagePackPanel(pack_source_overrides={})

        assert panel._resource_tabs.count() == 2
        assert panel._resource_tabs.tabText(1) == "Lookup Dictionaries"
        assert any(
            "do not affect replacements" in label.text() for label in panel.findChildren(QLabel)
        )
        assert any(label.text() == "Installed dictionaries" for label in panel.findChildren(QLabel))
        assert any(label.text() == "Get a dictionary" for label in panel.findChildren(QLabel))
        assert any("Start here" in label.text() for label in panel.findChildren(QLabel))
        assert panel._lookup_dictionary_find_button.text() == "Get dictionaries..."
        assert panel._lookup_dictionary_find_button.objectName() == "settingsPrimaryButton"
        assert panel._lookup_dictionary_import_button.text() == "Import downloaded ZIP..."
        assert panel._lookup_dictionary_import_button.objectName() != "settingsPrimaryButton"
        assert panel._lookup_dictionary_detected_import_button.isHidden()


def test_lookup_dictionary_acquisition_detects_and_validates_recent_download(
    monkeypatch,
) -> None:
    _app()
    set_locale("en")
    QSettings().remove("resources/lookup_dictionary_acquisition_started_epoch")
    QSettings().remove("resources/lookup_dictionary_acquisition_pair")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dictionaries_dir = root / "lookup_dictionaries"
        downloads_dir = root / "Downloads"
        downloads_dir.mkdir()
        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(dictionaries_dir),
        ):
            panel = LanguagePackPanel(focused_pair="en-ja", pack_source_overrides={})
        monkeypatch.setattr(
            panel,
            "_lookup_dictionary_download_search_dirs",
            lambda: (downloads_dir,),
        )
        panel._begin_lookup_dictionary_acquisition("en-ja")

        unrelated = downloads_dir / "unrelated.zip"
        with zipfile.ZipFile(unrelated, "w") as archive:
            archive.writestr("notes.txt", "not a dictionary")
        source = downloads_dir / "大辞林　第四版　画像無し (1).zip"
        _write_yomitan_zip(source)
        panel._refresh_lookup_dictionary_download_candidate()

        candidate = panel._lookup_dictionary_download_candidate
        assert candidate is not None
        assert candidate.path == source
        assert candidate.title == "Local Japanese Dictionary"
        assert not panel._lookup_dictionary_detected_import_button.isHidden()
        assert "Local Japanese Dictionary" in panel._lookup_dictionary_status.text()

        selected: list[tuple[Path, str]] = []
        monkeypatch.setattr(
            panel,
            "_confirm_and_start_lookup_dictionary_import",
            lambda path, *, pair="": selected.append((path, pair)),
        )
        panel._lookup_dictionary_detected_import_button.click()

        assert selected == [(source, "en-ja")]
        panel._clear_lookup_dictionary_acquisition()


def test_lookup_dictionary_stack_is_saved_per_language_pair() -> None:
    _app()
    set_locale("en")
    QSettings().remove("resources/learning_pairs")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dictionaries_dir = root / "lookup_dictionaries"
        source = root / "dictionary.zip"
        _write_yomitan_zip(source)
        imported = import_yomitan_dictionary_zip(
            source,
            dictionaries_dir=dictionaries_dir,
        )
        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(dictionaries_dir),
        ):
            panel = LanguagePackPanel(focused_pair="en-ja", pack_source_overrides={})

        assert panel._lookup_dictionary_pair_combo.findData("ja-ja") >= 0
        assert panel._lookup_dictionary_pair_combo.findData("en-de") == -1
        assert panel._lookup_dictionary_order_table.rowCount() == 1
        assert panel._lookup_dictionary_order_table.item(0, 0).text() == "1"
        assert "JMdict" in panel._lookup_dictionary_order_table.item(0, 1).text()
        assert "fixed" in panel._lookup_dictionary_order_table.item(0, 1).text()
        _add_dictionary_to_current_pair(panel, imported.dictionary.pack_id)
        move_up = _stack_action_button(panel, row=0, label="Up")
        move_down = _stack_action_button(panel, row=0, label="Down")
        assert move_up.text() == "↑"
        assert move_down.text() == "↓"
        assert not move_up.isEnabled()
        assert not move_down.isEnabled()
        assert "first imported source" in move_up.toolTip()
        assert "built-in source remains fixed" in move_down.toolTip()
        remove_from_pair = _stack_action_button(panel, row=0, label="Remove from pair...")
        assert remove_from_pair.property("resourceTableAction")
        assert remove_from_pair.minimumWidth() >= remove_from_pair.sizeHint().width()
        assert panel._lookup_dictionary_order_table.columnWidth(3) > (
            remove_from_pair.minimumWidth() + 68
        )
        assert panel._lookup_dictionary_order_table.item(1, 0).text() == "2"

        ja_ja_index = panel._lookup_dictionary_pair_combo.findData("ja-ja")
        panel._lookup_dictionary_pair_combo.setCurrentIndex(ja_ja_index)
        assert panel._lookup_dictionary_order_table.rowCount() == 0
        assert "no built-in popup source" in panel._lookup_dictionary_fallback.text()
        _add_dictionary_to_current_pair(panel, imported.dictionary.pack_id)

        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (imported.dictionary.pack_id,)
        assert lookup_dictionary_pack_ids_for_pair(saved, "ja-ja") == (imported.dictionary.pack_id,)
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-de") == ()
        assert panel._lookup_dictionary_order_table.rowCount() == 1
        assert "Local Japanese Dictionary" in (
            panel._lookup_dictionary_order_table.item(0, 1).text()
        )
        assert "no built-in popup source" in panel._lookup_dictionary_fallback.text()
        assert panel._lookup_dictionary_table.rowCount() == 1
        assert "Japanese" in panel._lookup_dictionary_table.item(0, 1).text()
        used_by = panel._lookup_dictionary_table.item(0, 2).text()
        assert "en-ja" in used_by
        assert "ja-ja" in used_by
        actions = panel._lookup_dictionary_table.cellWidget(0, 4)
        assert actions is not None
        assert panel._lookup_dictionary_table.columnWidth(4) >= actions.sizeHint().width()
        assert source.exists()


def test_lookup_dictionary_global_remove_names_affected_pairs() -> None:
    _app()
    set_locale("en")
    QSettings().remove("resources/learning_pairs")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dictionaries_dir = root / "lookup_dictionaries"
        source = root / "dictionary.zip"
        _write_yomitan_zip(source)
        imported = import_yomitan_dictionary_zip(
            source,
            dictionaries_dir=dictionaries_dir,
        )
        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(dictionaries_dir),
        ):
            panel = LanguagePackPanel(focused_pair="en-ja", pack_source_overrides={})

        pack_id = imported.dictionary.pack_id
        for pair in ("en-ja", "ja-ja"):
            pair_index = panel._lookup_dictionary_pair_combo.findData(pair)
            panel._lookup_dictionary_pair_combo.setCurrentIndex(pair_index)
            _add_dictionary_to_current_pair(panel, pack_id)

        messages: list[str] = []

        def approve_remove(_parent, _title, message, *_args):
            messages.append(message)
            return QMessageBox.Yes

        with patch(
            "settings_lookup_dictionaries_mixin.localized_question",
            side_effect=approve_remove,
        ):
            panel._remove_lookup_dictionary(pack_id)

        assert messages
        assert "en-ja" in messages[0]
        assert "ja-ja" in messages[0]
        assert "remaining lookup order" in messages[0]
        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == ()
        assert lookup_dictionary_pack_ids_for_pair(saved, "ja-ja") == ()
        assert panel.findChild(QTableWidget, "lookupDictionaryLibrary").rowCount() == 0
        assert source.exists()


def test_lookup_dictionary_stack_adds_first_reorders_and_removes_without_uninstalling() -> None:
    _app()
    set_locale("en")
    QSettings().remove("resources/learning_pairs")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dictionaries_dir = root / "lookup_dictionaries"
        first_source = root / "first.zip"
        second_source = root / "second.zip"
        _write_yomitan_zip(first_source, title="First Dictionary")
        _write_yomitan_zip(second_source, title="Second Dictionary")
        first = import_yomitan_dictionary_zip(
            first_source,
            dictionaries_dir=dictionaries_dir,
        )
        second = import_yomitan_dictionary_zip(
            second_source,
            dictionaries_dir=dictionaries_dir,
        )
        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(dictionaries_dir),
        ):
            panel = LanguagePackPanel(focused_pair="en-ja", pack_source_overrides={})

        _add_dictionary_to_current_pair(panel, first.dictionary.pack_id)
        _add_dictionary_to_current_pair(panel, second.dictionary.pack_id)
        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (
            second.dictionary.pack_id,
            first.dictionary.pack_id,
        )
        assert "Second Dictionary" in panel._lookup_dictionary_order_table.item(0, 1).text()
        assert "First Dictionary" in panel._lookup_dictionary_order_table.item(1, 1).text()
        assert "JMdict" in panel._lookup_dictionary_order_table.item(2, 1).text()

        assert not _stack_action_button(panel, row=0, label="Up").isEnabled()
        move_second_down = _stack_action_button(panel, row=0, label="Down")
        assert move_second_down.isEnabled()
        move_second_down.click()
        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (
            first.dictionary.pack_id,
            second.dictionary.pack_id,
        )

        messages: list[str] = []

        def reject_remove(_parent, _title, message, *_args):
            messages.append(message)
            return QMessageBox.Cancel

        with patch(
            "settings_lookup_dictionary_stack_mixin.localized_question",
            side_effect=reject_remove,
        ):
            panel._remove_lookup_dictionary_from_stack(first.dictionary.pack_id)
        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (
            first.dictionary.pack_id,
            second.dictionary.pack_id,
        )
        assert messages
        assert "will not be deleted" in messages[0]
        assert "en-ja" in messages[0]

        with patch(
            "settings_lookup_dictionary_stack_mixin.localized_question",
            return_value=QMessageBox.Yes,
        ):
            panel._remove_lookup_dictionary_from_stack(first.dictionary.pack_id)
        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (second.dictionary.pack_id,)
        assert first.artifact_path.exists()
        assert panel._lookup_dictionary_add_combo.findData(first.dictionary.pack_id) > 0

        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(dictionaries_dir),
        ):
            reopened = LanguagePackPanel(focused_pair="en-ja", pack_source_overrides={})
        assert "Second Dictionary" in reopened._lookup_dictionary_order_table.item(0, 1).text()
        assert "JMdict" in reopened._lookup_dictionary_order_table.item(1, 1).text()


def test_completed_import_is_added_first_without_replacing_existing_stack() -> None:
    _app()
    set_locale("en")
    QSettings().remove("resources/learning_pairs")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dictionaries_dir = root / "lookup_dictionaries"
        first_source = root / "first.zip"
        second_source = root / "second.zip"
        _write_yomitan_zip(first_source, title="Existing Dictionary")
        _write_yomitan_zip(second_source, title="New Dictionary")
        first = import_yomitan_dictionary_zip(
            first_source,
            dictionaries_dir=dictionaries_dir,
        )
        second = import_yomitan_dictionary_zip(
            second_source,
            dictionaries_dir=dictionaries_dir,
        )
        with patch(
            "settings_language_packs._lookup_dictionary_pack_dir",
            return_value=str(dictionaries_dir),
        ):
            panel = LanguagePackPanel(focused_pair="en-ja", pack_source_overrides={})

        _add_dictionary_to_current_pair(panel, first.dictionary.pack_id)
        panel._on_lookup_dictionary_import_completed("en-ja", second)

        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (
            second.dictionary.pack_id,
            first.dictionary.pack_id,
        )
