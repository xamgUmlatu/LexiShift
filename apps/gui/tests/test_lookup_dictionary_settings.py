from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QTableWidget

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


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _write_yomitan_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "index.json",
            json.dumps(
                {
                    "title": "Local Japanese Dictionary",
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


def test_compatible_lookup_dictionary_directory_url_is_target_aware() -> None:
    japanese_url = _compatible_lookup_dictionary_directory_url("en-ja")

    assert japanese_url.startswith("https://github.com/MarvNC/yomitan-dictionaries#:~:text=")
    assert "%E7%84%A1%E3%81%97" in japanese_url
    assert _compatible_lookup_dictionary_directory_url("ja-ja") == japanese_url
    assert _compatible_lookup_dictionary_directory_url("en-de") == (
        "https://github.com/MarvNC/yomitan-dictionaries"
    )


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


def test_lookup_dictionary_selection_is_saved_per_language_pair() -> None:
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
        index = panel._lookup_dictionary_combo.findData(imported.dictionary.pack_id)
        assert index > 0
        panel._lookup_dictionary_combo.setCurrentIndex(index)

        ja_ja_index = panel._lookup_dictionary_pair_combo.findData("ja-ja")
        panel._lookup_dictionary_pair_combo.setCurrentIndex(ja_ja_index)
        dictionary_index = panel._lookup_dictionary_combo.findData(imported.dictionary.pack_id)
        assert dictionary_index > 0
        panel._lookup_dictionary_combo.setCurrentIndex(dictionary_index)

        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == (imported.dictionary.pack_id,)
        assert lookup_dictionary_pack_ids_for_pair(saved, "ja-ja") == (imported.dictionary.pack_id,)
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-de") == ()
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
            dictionary_index = panel._lookup_dictionary_combo.findData(pack_id)
            panel._lookup_dictionary_combo.setCurrentIndex(dictionary_index)

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
        assert "return to the built-in lookup source" in messages[0]
        saved = load_lookup_dictionary_settings(dictionaries_dir / "settings.json")
        assert lookup_dictionary_pack_ids_for_pair(saved, "en-ja") == ()
        assert lookup_dictionary_pack_ids_for_pair(saved, "ja-ja") == ()
        assert panel.findChild(QTableWidget, "lookupDictionaryLibrary").rowCount() == 0
        assert source.exists()
