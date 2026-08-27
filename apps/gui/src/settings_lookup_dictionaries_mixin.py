from __future__ import annotations

from pathlib import Path
import webbrowser

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from i18n import t
from lexishift_core.helper.lp_capabilities import known_pairs, normalize_pair_key
from lexishift_core.helper.lookup_dictionary_settings import (
    load_lookup_dictionary_settings,
    lookup_dictionary_pack_ids_for_pair,
    save_lookup_dictionary_settings,
    with_lookup_dictionary_pack_ids,
    without_lookup_dictionary_pack,
)
from lexishift_core.helper.yomitan_dictionary_health import (
    InstalledLookupDictionaryHealth,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import (
    list_installed_lookup_dictionaries,
    remove_installed_lookup_dictionary,
)
from localized_message_box import localized_question, prepare_message_box
from lookup_dictionary_import import YomitanDictionaryImportThread
from settings_lookup_dictionary_health_mixin import (
    LanguagePackPanelLookupDictionaryHealthMixin,
)
from settings_lookup_dictionary_stack_mixin import (
    LanguagePackPanelLookupDictionaryStackMixin,
)
from utils_paths import reveal_path


_COMPATIBLE_DICTIONARY_DIRECTORY_URL = "https://github.com/MarvNC/yomitan-dictionaries"
_JAPANESE_DICTIONARY_DIRECTORY_SECTION = "#daijirin-fourth-edition"

_LOOKUP_LANGUAGE_LABEL_KEYS = {
    "de": "languages.german",
    "en": "languages.english",
    "es": "languages.spanish",
    "ja": "languages.japanese",
    "zh": "languages.chinese",
}


def _lookup_language_label(language: str) -> str:
    normalized = str(language or "").strip().lower()
    key = _LOOKUP_LANGUAGE_LABEL_KEYS.get(normalized)
    return t(key) if key else normalized.upper()


def _lookup_pair_label(pair: str) -> str:
    source, separator, target = normalize_pair_key(pair, default="").partition("-")
    if not separator:
        return str(pair or "").strip()
    return (
        f"{_lookup_language_label(source)} → {_lookup_language_label(target)} ({source}-{target})"
    )


def _lookup_pair_target_language(pair: str) -> str:
    _source, separator, target = normalize_pair_key(pair, default="").partition("-")
    return target if separator else ""


def _compatible_lookup_dictionary_directory_url(pair: str) -> str:
    if _lookup_pair_target_language(pair) == "ja":
        return _COMPATIBLE_DICTIONARY_DIRECTORY_URL + _JAPANESE_DICTIONARY_DIRECTORY_SECTION
    return _COMPATIBLE_DICTIONARY_DIRECTORY_URL


def _format_lookup_dictionary_size(size_bytes: int) -> str:
    size = max(0, int(size_bytes))
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


class LanguagePackPanelLookupDictionariesMixin(
    LanguagePackPanelLookupDictionaryHealthMixin,
    LanguagePackPanelLookupDictionaryStackMixin,
):
    def _initialize_lookup_dictionaries(self) -> None:
        self._lookup_dictionary_threads: list[YomitanDictionaryImportThread] = []
        self._lookup_dictionary_download_candidate = None
        self._lookup_dictionary_settings_path = Path(self._lookup_dictionary_dir) / "settings.json"
        self._lookup_dictionary_settings = load_lookup_dictionary_settings(
            self._lookup_dictionary_settings_path
        )
        self._updating_lookup_dictionary_controls = False
        self._lookup_dictionary_health_records: (
            tuple[InstalledLookupDictionaryHealth, ...] | None
        ) = None
        self._lookup_dictionary_health_request_token = 0
        self._lookup_dictionary_health_pending = False

    def _build_lookup_dictionaries_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(t("language_packs.lookup_dictionaries.title"), tab)
        title.setProperty("resourceSectionTitle", True)
        header.addWidget(title)
        header.addStretch(1)
        open_button = QPushButton(
            t("language_packs.lookup_dictionaries.open_directory"),
            tab,
        )
        open_button.clicked.connect(lambda: reveal_path(self._lookup_dictionary_dir))
        header.addWidget(open_button)
        layout.addLayout(header)

        description = QLabel(
            t("language_packs.lookup_dictionaries.description"),
            tab,
        )
        description.setProperty("resourceDescription", True)
        description.setWordWrap(True)
        layout.addWidget(description)

        add_title = QLabel(t("language_packs.lookup_dictionaries.add_title"), tab)
        add_title.setProperty("resourceSectionTitle", True)
        layout.addWidget(add_title)
        add_description = QLabel(
            t("language_packs.lookup_dictionaries.add_description"),
            tab,
        )
        add_description.setProperty("resourceDescription", True)
        add_description.setWordWrap(True)
        layout.addWidget(add_description)

        action_row = QHBoxLayout()
        self._lookup_dictionary_find_button = QPushButton(
            t("language_packs.lookup_dictionaries.find_compatible"),
            tab,
        )
        self._lookup_dictionary_find_button.setObjectName("settingsPrimaryButton")
        self._lookup_dictionary_find_button.clicked.connect(
            self._show_compatible_lookup_dictionaries
        )
        action_row.addWidget(self._lookup_dictionary_find_button)
        self._lookup_dictionary_detected_import_button = QPushButton(
            t("language_packs.lookup_dictionaries.import_detected_zip"),
            tab,
        )
        self._lookup_dictionary_detected_import_button.clicked.connect(
            self._import_detected_lookup_dictionary_zip
        )
        self._lookup_dictionary_detected_import_button.setVisible(False)
        action_row.addWidget(self._lookup_dictionary_detected_import_button)
        self._lookup_dictionary_import_button = QPushButton(
            t("language_packs.lookup_dictionaries.import_downloaded_zip"),
            tab,
        )
        self._lookup_dictionary_import_button.clicked.connect(self._select_lookup_dictionary_zip)
        action_row.addWidget(self._lookup_dictionary_import_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self._lookup_dictionary_status = QLabel("", tab)
        self._lookup_dictionary_status.setWordWrap(True)
        layout.addWidget(self._lookup_dictionary_status)

        assignment_title = QLabel(
            t("language_packs.lookup_dictionaries.assignment_title"),
            tab,
        )
        assignment_title.setProperty("resourceSectionTitle", True)
        layout.addWidget(assignment_title)

        pair_row = QHBoxLayout()
        pair_row.addWidget(QLabel(t("language_packs.lookup_dictionaries.pair"), tab))
        self._lookup_dictionary_pair_combo = QComboBox(tab)
        pair_row.addWidget(self._lookup_dictionary_pair_combo, 1)
        layout.addLayout(pair_row)

        order_description = QLabel(
            t("language_packs.lookup_dictionaries.lookup_order_description"),
            tab,
        )
        order_description.setProperty("resourceDescription", True)
        order_description.setWordWrap(True)
        layout.addWidget(order_description)

        self._lookup_dictionary_order_table = QTableWidget(tab)
        self._lookup_dictionary_order_table.setObjectName("lookupDictionaryOrder")
        self._lookup_dictionary_order_table.setColumnCount(4)
        self._lookup_dictionary_order_table.setHorizontalHeaderLabels(
            [
                t("language_packs.lookup_dictionaries.headers.order"),
                t("language_packs.lookup_dictionaries.headers.dictionary"),
                t("language_packs.lookup_dictionaries.headers.headwords"),
                t("language_packs.lookup_dictionaries.headers.actions"),
            ]
        )
        self._lookup_dictionary_order_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._lookup_dictionary_order_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._lookup_dictionary_order_table.setAlternatingRowColors(True)
        self._lookup_dictionary_order_table.verticalHeader().setVisible(False)
        self._lookup_dictionary_order_table.verticalHeader().setDefaultSectionSize(48)
        order_header = self._lookup_dictionary_order_table.horizontalHeader()
        order_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        order_header.setSectionResizeMode(1, QHeaderView.Stretch)
        order_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        order_header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._lookup_dictionary_order_table.setMinimumHeight(190)
        layout.addWidget(self._lookup_dictionary_order_table)

        dictionary_row = QHBoxLayout()
        dictionary_row.addWidget(
            QLabel(t("language_packs.lookup_dictionaries.add_installed_dictionary"), tab)
        )
        self._lookup_dictionary_add_combo = QComboBox(tab)
        dictionary_row.addWidget(self._lookup_dictionary_add_combo, 1)
        self._lookup_dictionary_add_button = QPushButton(
            t("language_packs.lookup_dictionaries.add_to_lookup_order"),
            tab,
        )
        self._lookup_dictionary_add_button.clicked.connect(self._add_lookup_dictionary_to_stack)
        dictionary_row.addWidget(self._lookup_dictionary_add_button)
        layout.addLayout(dictionary_row)

        self._lookup_dictionary_detail = QLabel("", tab)
        self._lookup_dictionary_detail.setProperty("resourceDescription", True)
        self._lookup_dictionary_detail.setWordWrap(True)
        layout.addWidget(self._lookup_dictionary_detail)
        self._lookup_dictionary_compatibility = QLabel("", tab)
        self._lookup_dictionary_compatibility.setStyleSheet(
            f"color: {self._status_color_hex('warning')}; font-size: 13px; font-weight: 600;"
        )
        self._lookup_dictionary_compatibility.setWordWrap(True)
        layout.addWidget(self._lookup_dictionary_compatibility)
        self._lookup_dictionary_fallback = QLabel(
            t("language_packs.lookup_dictionaries.fallback_detail"),
            tab,
        )
        self._lookup_dictionary_fallback.setProperty("resourceDescription", True)
        self._lookup_dictionary_fallback.setWordWrap(True)
        layout.addWidget(self._lookup_dictionary_fallback)

        library_header = QHBoxLayout()
        library_title = QLabel(
            t("language_packs.lookup_dictionaries.library_title"),
            tab,
        )
        library_title.setProperty("resourceSectionTitle", True)
        library_header.addWidget(library_title)
        library_header.addStretch(1)
        self._lookup_dictionary_health_button = QPushButton(
            t("language_packs.lookup_dictionaries.check_health"),
            tab,
        )
        self._lookup_dictionary_health_button.clicked.connect(
            self._start_lookup_dictionary_health_check
        )
        library_header.addWidget(self._lookup_dictionary_health_button)
        layout.addLayout(library_header)
        library_description = QLabel(
            t("language_packs.lookup_dictionaries.library_description"),
            tab,
        )
        library_description.setProperty("resourceDescription", True)
        library_description.setWordWrap(True)
        layout.addWidget(library_description)

        self._lookup_dictionary_table = QTableWidget(tab)
        self._lookup_dictionary_table.setObjectName("lookupDictionaryLibrary")
        self._lookup_dictionary_table.setColumnCount(6)
        self._lookup_dictionary_table.setHorizontalHeaderLabels(
            [
                t("language_packs.lookup_dictionaries.headers.dictionary"),
                t("language_packs.lookup_dictionaries.headers.languages"),
                t("language_packs.lookup_dictionaries.headers.used_by"),
                t("language_packs.lookup_dictionaries.headers.size"),
                t("language_packs.lookup_dictionaries.headers.health"),
                t("language_packs.lookup_dictionaries.headers.actions"),
            ]
        )
        self._lookup_dictionary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._lookup_dictionary_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._lookup_dictionary_table.setAlternatingRowColors(True)
        self._lookup_dictionary_table.verticalHeader().setVisible(False)
        self._lookup_dictionary_table.verticalHeader().setDefaultSectionSize(48)
        header_view = self._lookup_dictionary_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        # QHeaderView does not include cell-widget size hints when calculating
        # ResizeToContents, so the actions column is sized explicitly below.
        header_view.setSectionResizeMode(5, QHeaderView.Fixed)
        self._lookup_dictionary_table.setMinimumHeight(190)
        layout.addWidget(self._lookup_dictionary_table, 1)

        self._lookup_dictionary_empty = QLabel(
            t("language_packs.lookup_dictionaries.library_empty"),
            tab,
        )
        self._lookup_dictionary_empty.setProperty("resourceDescription", True)
        self._lookup_dictionary_empty.setWordWrap(True)
        layout.addWidget(self._lookup_dictionary_empty)

        self._lookup_dictionary_pair_combo.currentIndexChanged.connect(
            self._refresh_lookup_dictionary_stack
        )
        self._lookup_dictionary_add_combo.currentIndexChanged.connect(
            self._refresh_lookup_dictionary_add_detail
        )
        self._refresh_lookup_dictionary_pair_choices()
        self._refresh_lookup_dictionary_stack()
        self._refresh_installed_lookup_dictionary_library()
        self._refresh_lookup_dictionary_download_candidate()
        QTimer.singleShot(0, self._start_lookup_dictionary_health_check)
        return tab

    def _refresh_learning_pair_cards(self) -> None:
        super()._refresh_learning_pair_cards()
        self._refresh_lookup_dictionary_pair_choices()

    def _lookup_dictionary_pairs(self) -> tuple[str, ...]:
        focused_pair = normalize_pair_key(getattr(self, "_focused_pair", ""), default="")
        pairs: list[str] = []

        def add_pair(value: object) -> None:
            pair = normalize_pair_key(value, default="")
            if pair and pair not in pairs:
                pairs.append(pair)

        add_pair(focused_pair)
        for pair in getattr(self, "_learning_pair_keys", ()):
            add_pair(pair)
        for pair in self._lookup_dictionary_settings.pair_pack_ids:
            add_pair(pair)

        # A target-language monolingual LP is the most useful companion to a
        # configured cross-lingual LP (for example en-ja and ja-ja can share one
        # Japanese-headword dictionary) without exposing every theoretical pair.
        known = set(known_pairs())
        for pair in tuple(pairs):
            target = _lookup_pair_target_language(pair)
            monolingual_pair = f"{target}-{target}" if target else ""
            if monolingual_pair in known:
                add_pair(monolingual_pair)
        if not pairs:
            add_pair("en-ja")
        return tuple(pairs)

    def _refresh_lookup_dictionary_pair_choices(self, preferred_pair: str = "") -> None:
        combo = getattr(self, "_lookup_dictionary_pair_combo", None)
        if combo is None:
            return
        selected_pair = normalize_pair_key(
            preferred_pair or combo.currentData() or getattr(self, "_focused_pair", ""),
            default="en-ja",
        )
        pairs = list(self._lookup_dictionary_pairs())
        if selected_pair and selected_pair not in pairs:
            pairs.insert(0, selected_pair)
        combo.blockSignals(True)
        try:
            combo.clear()
            selected_index = 0
            for index, pair in enumerate(pairs):
                combo.addItem(_lookup_pair_label(pair), pair)
                if pair == selected_pair:
                    selected_index = index
            combo.setCurrentIndex(selected_index)
        finally:
            combo.blockSignals(False)

    def _current_lookup_dictionary_pair(self) -> str:
        return (
            str(
                self._lookup_dictionary_pair_combo.currentData()
                or self._lookup_dictionary_pair_combo.currentText()
                or ""
            )
            .strip()
            .lower()
        )

    def _installed_lookup_dictionaries(self):
        if self._lookup_dictionary_health_records is not None:
            return tuple(
                record.dictionary
                for record in self._lookup_dictionary_health_records
                if record.healthy
            )
        return list_installed_lookup_dictionaries(Path(self._lookup_dictionary_dir))

    def _lookup_dictionary_used_by_pairs(self, pack_id: str) -> tuple[str, ...]:
        return tuple(
            pair
            for pair, pack_ids in sorted(self._lookup_dictionary_settings.pair_pack_ids.items())
            if pack_id in pack_ids
        )

    def _lookup_dictionary_disk_usage(self, pack_id: str) -> int:
        pack_root = Path(self._lookup_dictionary_dir) / pack_id
        total = 0
        try:
            for path in pack_root.iterdir():
                if path.is_file():
                    total += path.stat().st_size
        except OSError:
            return total
        return total

    def _lookup_dictionary_languages(self, dictionary) -> str:
        headwords = (
            _lookup_language_label(dictionary.source_language)
            if dictionary.source_language
            else t("language_packs.lookup_dictionaries.unknown_language")
        )
        definitions = (
            _lookup_language_label(dictionary.target_language)
            if dictionary.target_language
            else t("language_packs.lookup_dictionaries.unknown_language")
        )
        return t(
            "language_packs.lookup_dictionaries.dictionary_languages",
            headwords=headwords,
            definitions=definitions,
        )

    def _refresh_installed_lookup_dictionary_library(self) -> None:
        table = getattr(self, "_lookup_dictionary_table", None)
        if table is None:
            return
        records = self._lookup_dictionary_library_records()
        for row in range(table.rowCount()):
            actions = table.cellWidget(row, 5)
            if actions is not None:
                table.removeCellWidget(row, 5)
                actions.hide()
                actions.deleteLater()
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(records))
        self._lookup_dictionary_empty.setVisible(not records)
        table.setVisible(bool(records))
        actions_width = table.horizontalHeaderItem(5).sizeHint().width() + 18
        for row, record in enumerate(records):
            dictionary = record.dictionary
            name = dictionary.title
            if dictionary.revision:
                name = f"{name}\n{dictionary.revision}"
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(
                t(
                    "language_packs.lookup_dictionaries.dictionary_tooltip",
                    filename=dictionary.source_filename or "—",
                    terms=dictionary.term_count,
                )
            )
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(self._lookup_dictionary_languages(dictionary)))
            used_by = self._lookup_dictionary_used_by_pairs(dictionary.pack_id)
            used_by_label = (
                ", ".join(_lookup_pair_label(pair) for pair in used_by)
                if used_by
                else t("language_packs.lookup_dictionaries.not_in_use")
            )
            table.setItem(row, 2, QTableWidgetItem(used_by_label))
            table.setItem(
                row,
                3,
                QTableWidgetItem(_format_lookup_dictionary_size(record.disk_usage_bytes)),
            )
            health_item = QTableWidgetItem(self._lookup_dictionary_health_label(record.status))
            health_item.setToolTip(self._lookup_dictionary_health_tooltip(record.status))
            table.setItem(row, 4, health_item)

            actions = QWidget(table)
            action_layout = QHBoxLayout(actions)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            if record.status not in {"healthy", "checking"}:
                repair_button = QPushButton(
                    t("language_packs.lookup_dictionaries.reimport"),
                    actions,
                )
                repair_button.setMinimumWidth(
                    repair_button.fontMetrics().horizontalAdvance(repair_button.text()) + 28
                )
                repair_button.clicked.connect(
                    lambda checked=False, pack_id=dictionary.pack_id, title=(dictionary.title): (
                        self._select_lookup_dictionary_repair_zip(pack_id, title)
                    )
                )
                action_layout.addWidget(repair_button)
            show_button = QPushButton(
                t("language_packs.lookup_dictionaries.show_files"),
                actions,
            )
            show_button.setMinimumWidth(
                show_button.fontMetrics().horizontalAdvance(show_button.text()) + 28
            )
            show_button.clicked.connect(
                lambda checked=False, pack_id=dictionary.pack_id: (
                    self._show_lookup_dictionary_files(pack_id)
                )
            )
            action_layout.addWidget(show_button)
            remove_button = QPushButton(
                t("language_packs.lookup_dictionaries.remove"),
                actions,
            )
            remove_button.setMinimumWidth(
                remove_button.fontMetrics().horizontalAdvance(remove_button.text()) + 28
            )
            remove_button.clicked.connect(
                lambda checked=False, pack_id=dictionary.pack_id: self._remove_lookup_dictionary(
                    pack_id
                )
            )
            action_layout.addWidget(remove_button)
            table.setCellWidget(row, 5, actions)
            actions_width = max(actions_width, actions.sizeHint().width() + 8)
        if records:
            table.setColumnWidth(5, actions_width)

    def _show_lookup_dictionary_files(self, pack_id: str) -> None:
        reveal_path(str(Path(self._lookup_dictionary_dir) / pack_id))

    def _show_compatible_lookup_dictionaries(self) -> None:
        pair = self._current_lookup_dictionary_pair()
        pair_label = _lookup_pair_label(pair)
        target_language = _lookup_language_label(_lookup_pair_target_language(pair))
        directory_url = _compatible_lookup_dictionary_directory_url(pair)
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setWindowTitle(t("language_packs.lookup_dictionaries.find_compatible_title"))
        dialog.setText(
            t(
                "language_packs.lookup_dictionaries.find_compatible_summary",
                pair=pair_label,
            )
        )
        dialog.setInformativeText(
            t(
                "language_packs.lookup_dictionaries.find_compatible_details",
                target_language=target_language,
            )
        )
        dialog.setDetailedText(
            t(
                "language_packs.lookup_dictionaries.find_compatible_technical_details",
                pair=pair,
                target_language=target_language,
                directory_url=directory_url,
            )
        )
        directory_button = dialog.addButton(
            t("language_packs.lookup_dictionaries.open_community_directory"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        import_button = dialog.addButton(
            t("language_packs.lookup_dictionaries.import_downloaded_zip"),
            QMessageBox.ButtonRole.ActionRole,
        )
        dialog.addButton(QMessageBox.Close)
        prepare_message_box(dialog)
        dialog.exec()
        if dialog.clickedButton() == directory_button:
            self._begin_lookup_dictionary_acquisition(pair)
            webbrowser.open(directory_url)
            self._lookup_dictionary_status.setText(
                t("language_packs.lookup_dictionaries.community_directory_opened")
            )
        elif dialog.clickedButton() == import_button:
            self._select_lookup_dictionary_zip()

    def _select_lookup_dictionary_zip(self) -> None:
        start_directory = ""
        if hasattr(self, "_manual_source_search_dirs"):
            search_directories = self._manual_source_search_dirs()
            if search_directories:
                start_directory = str(search_directories[0])
        source_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            t("language_packs.lookup_dictionaries.select_zip"),
            start_directory,
            t("language_packs.lookup_dictionaries.zip_filter"),
        )
        if not source_path:
            return
        self._confirm_and_start_lookup_dictionary_import(Path(source_path))

    def _confirm_and_start_lookup_dictionary_import(
        self,
        source_path: Path,
        *,
        pair: str = "",
        expected_pack_id: str = "",
    ) -> None:
        confirmation_title_key = "rights_title"
        confirmation_message_key = "rights_message"
        if expected_pack_id:
            confirmation_title_key = "repair_title"
            confirmation_message_key = "repair_message"
        reply = localized_question(
            self,
            t(f"language_packs.lookup_dictionaries.{confirmation_title_key}"),
            t(f"language_packs.lookup_dictionaries.{confirmation_message_key}"),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        if hasattr(self, "_remember_manual_source_import_dir"):
            self._remember_manual_source_import_dir(source_path)
        selected_pair = normalize_pair_key(pair, default="") or (
            self._current_lookup_dictionary_pair()
        )
        thread = YomitanDictionaryImportThread(
            pair=selected_pair,
            source_path=source_path,
            dictionaries_dir=self._lookup_dictionary_dir,
            expected_pack_id=expected_pack_id,
            parent=self,
        )
        thread.progress.connect(self._on_lookup_dictionary_import_progress)
        thread.completed.connect(self._on_lookup_dictionary_import_completed)
        thread.failed.connect(self._on_lookup_dictionary_import_failed)
        thread.cancelled.connect(self._on_lookup_dictionary_import_cancelled)
        thread.finished.connect(lambda worker=thread: self._forget_lookup_dictionary_thread(worker))
        self._lookup_dictionary_threads.append(thread)
        self._set_lookup_dictionary_import_active(True)
        self._lookup_dictionary_status.setText(t("language_packs.lookup_dictionaries.importing"))
        thread.start()

    def _on_lookup_dictionary_import_progress(self, current: int, total: int) -> None:
        self._lookup_dictionary_status.setText(
            t(
                "language_packs.lookup_dictionaries.import_progress",
                current=current,
                total=total,
            )
        )

    def _on_lookup_dictionary_import_completed(
        self,
        pair: str,
        result: object,
        repaired_pack_id: str = "",
    ) -> None:
        dictionary = getattr(result, "dictionary", None)
        pack_id = str(getattr(dictionary, "pack_id", "") or "").strip()
        title = str(getattr(dictionary, "title", "") or pack_id).strip()
        if pack_id and not repaired_pack_id:
            current = lookup_dictionary_pack_ids_for_pair(
                self._lookup_dictionary_settings,
                pair,
            )
            self._lookup_dictionary_settings = with_lookup_dictionary_pack_ids(
                self._lookup_dictionary_settings,
                pair=pair,
                pack_ids=(pack_id, *(value for value in current if value != pack_id)),
            )
            save_lookup_dictionary_settings(
                self._lookup_dictionary_settings,
                self._lookup_dictionary_settings_path,
            )
        self._clear_lookup_dictionary_acquisition()
        self._lookup_dictionary_health_records = None
        self._refresh_lookup_dictionary_pair_choices(preferred_pair=pair)
        self._refresh_lookup_dictionary_stack()
        self._refresh_installed_lookup_dictionary_library()
        status_key = "repaired" if repaired_pack_id else "imported"
        self._lookup_dictionary_status.setText(
            t(f"language_packs.lookup_dictionaries.{status_key}", title=title)
        )
        self._start_lookup_dictionary_health_check()

    def _on_lookup_dictionary_import_failed(self, _pair: str, message: str) -> None:
        self._lookup_dictionary_status.setText(
            t("language_packs.lookup_dictionaries.import_failed", message=message)
        )
        QMessageBox.warning(
            self,
            t("language_packs.lookup_dictionaries.import_failed_title"),
            message,
        )

    def _on_lookup_dictionary_import_cancelled(self, _pair: str) -> None:
        self._lookup_dictionary_status.setText(
            t("language_packs.lookup_dictionaries.import_cancelled")
        )

    def _forget_lookup_dictionary_thread(
        self,
        thread: YomitanDictionaryImportThread,
    ) -> None:
        if thread in self._lookup_dictionary_threads:
            self._lookup_dictionary_threads.remove(thread)
        self._set_lookup_dictionary_import_active(bool(self._lookup_dictionary_threads))
        thread.deleteLater()

    def _set_lookup_dictionary_import_active(self, active: bool) -> None:
        self._lookup_dictionary_import_button.setEnabled(not active)
        self._lookup_dictionary_find_button.setEnabled(not active)
        self._lookup_dictionary_detected_import_button.setEnabled(not active)
        self._lookup_dictionary_pair_combo.setEnabled(not active)
        self._lookup_dictionary_add_combo.setEnabled(not active)
        self._lookup_dictionary_add_button.setEnabled(False)
        self._lookup_dictionary_health_button.setEnabled(
            not active and not self._lookup_dictionary_health_pending
        )
        self._lookup_dictionary_order_table.setEnabled(not active)
        self._lookup_dictionary_table.setEnabled(not active)
        if not active:
            self._refresh_lookup_dictionary_add_detail()

    def _remove_lookup_dictionary(self, pack_id: str) -> None:
        dictionary = next(
            (item for item in self._installed_lookup_dictionaries() if item.pack_id == pack_id),
            None,
        )
        if dictionary is None and self._lookup_dictionary_health_records is not None:
            dictionary = next(
                (
                    record.dictionary
                    for record in self._lookup_dictionary_health_records
                    if record.dictionary.pack_id == pack_id
                ),
                None,
            )
        if dictionary is None:
            return
        used_by = self._lookup_dictionary_used_by_pairs(pack_id)
        if used_by:
            message = t(
                "language_packs.lookup_dictionaries.remove_message_used",
                title=dictionary.title,
                pairs=", ".join(_lookup_pair_label(pair) for pair in used_by),
            )
        else:
            message = t(
                "language_packs.lookup_dictionaries.remove_message",
                title=dictionary.title,
            )
        reply = localized_question(
            self,
            t("language_packs.lookup_dictionaries.remove_title"),
            message,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        remove_installed_lookup_dictionary(Path(self._lookup_dictionary_dir), pack_id)
        self._lookup_dictionary_health_records = None
        self._lookup_dictionary_settings = without_lookup_dictionary_pack(
            self._lookup_dictionary_settings,
            pack_id,
        )
        save_lookup_dictionary_settings(
            self._lookup_dictionary_settings,
            self._lookup_dictionary_settings_path,
        )
        current_pair = self._current_lookup_dictionary_pair()
        self._refresh_lookup_dictionary_pair_choices(preferred_pair=current_pair)
        self._refresh_lookup_dictionary_stack()
        self._refresh_installed_lookup_dictionary_library()
        self._lookup_dictionary_status.setText(
            t("language_packs.lookup_dictionaries.removed", title=dictionary.title)
        )
        self._start_lookup_dictionary_health_check()

    def _cancel_lookup_dictionary_imports(self) -> None:
        threads = list(getattr(self, "_lookup_dictionary_threads", []))
        for thread in threads:
            if thread.isRunning():
                thread.requestInterruption()
        for thread in threads:
            if thread.isRunning():
                thread.wait(5_000)
