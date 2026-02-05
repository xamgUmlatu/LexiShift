from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QToolButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from language_packs import (
    LanguagePackDownloadThread,
    LanguagePackInfo,
    LANGUAGE_PACKS,
    EMBEDDING_PACKS,
    CROSS_EMBEDDING_PACKS,
    FrequencyPackDownloadThread,
    FrequencyPackInfo,
    FREQUENCY_PACKS,
    download_log_path,
)
from lexishift_core import SynonymSourceSettings
from i18n import t
from utils_paths import reveal_path


@dataclass
class LanguagePackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton
    delete_button: QPushButton


@dataclass
class FrequencyPackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton
    delete_button: QPushButton


@dataclass
class EmbeddingPackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton
    delete_button: QPushButton
    use_button: QPushButton


class LanguagePackPanel(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._language_pack_dir = _language_pack_dir()
        self._embedding_pack_dir = _embedding_pack_dir()
        self._frequency_pack_dir = _frequency_pack_dir()
        self._language_pack_info = {pack.pack_id: pack for pack in LANGUAGE_PACKS}
        self._frequency_pack_info = {pack.pack_id: pack for pack in FREQUENCY_PACKS}
        self._embedding_pack_info = {
            pack.pack_id: pack for pack in (EMBEDDING_PACKS + CROSS_EMBEDDING_PACKS)
        }
        self._language_pack_rows: dict[str, LanguagePackRow] = {}
        self._frequency_pack_rows: dict[str, FrequencyPackRow] = {}
        self._embedding_pack_rows: dict[str, EmbeddingPackRow] = {}
        self._cross_embedding_pack_rows: dict[str, EmbeddingPackRow] = {}
        self._language_pack_threads: list[LanguagePackDownloadThread] = []
        self._frequency_pack_threads: list[FrequencyPackDownloadThread] = []
        self._language_pack_paths: dict[str, str] = {}
        self._frequency_pack_paths: dict[str, str] = {}
        self._embedding_pack_paths: dict[str, str] = {}
        self._embedding_pair_paths: dict[str, list[str]] = {}
        self._embedding_pair_enabled: dict[str, bool] = {}
        self._closing = False

        self.open_language_pack_button = QPushButton(t("language_packs.open_directory"))
        self.open_language_pack_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.open_language_pack_button.setMinimumHeight(34)
        self.open_language_pack_button.setObjectName("settingsPrimaryButton")
        self.open_language_pack_button.clicked.connect(self._open_language_pack_dir)

        self.open_frequency_pack_button = QPushButton(t("language_packs.frequency_open_directory"))
        self.open_frequency_pack_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.open_frequency_pack_button.setMinimumHeight(34)
        self.open_frequency_pack_button.setObjectName("settingsPrimaryButton")
        self.open_frequency_pack_button.clicked.connect(self._open_frequency_pack_dir)

        self.language_pack_table = QTableWidget()
        self.language_pack_table.setColumnCount(8)
        self.language_pack_table.setHorizontalHeaderLabels(
            [
                t("language_packs.headers.pack"),
                t("language_packs.headers.language"),
                t("language_packs.headers.source"),
                t("language_packs.headers.status"),
                t("language_packs.headers.download"),
                t("language_packs.headers.local"),
                t("language_packs.headers.delete"),
                t("language_packs.headers.size"),
            ]
        )
        self.language_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.language_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.language_pack_table.setAlternatingRowColors(True)
        self.language_pack_table.verticalHeader().setVisible(False)
        header = self.language_pack_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.language_pack_table.setMinimumHeight(320)

        self.frequency_pack_table = QTableWidget()
        self.frequency_pack_table.setColumnCount(8)
        self.frequency_pack_table.setHorizontalHeaderLabels(
            [
                t("language_packs.headers.pack"),
                t("language_packs.headers.language"),
                t("language_packs.headers.source"),
                t("language_packs.headers.status"),
                t("language_packs.headers.download"),
                t("language_packs.headers.local"),
                t("language_packs.headers.delete"),
                t("language_packs.headers.size"),
            ]
        )
        self.frequency_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frequency_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.frequency_pack_table.setAlternatingRowColors(True)
        self.frequency_pack_table.verticalHeader().setVisible(False)
        freq_header = self.frequency_pack_table.horizontalHeader()
        freq_header.setSectionResizeMode(0, QHeaderView.Stretch)
        freq_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        freq_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        freq_header.setSectionResizeMode(3, QHeaderView.Stretch)
        freq_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        freq_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        freq_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        freq_header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.frequency_pack_table.setMinimumHeight(220)

        self.language_pack_status = QLabel("")
        self.language_pack_status.setWordWrap(True)
        self.language_pack_status.setOpenExternalLinks(True)

        self._populate_language_packs()
        self._populate_frequency_packs()
        self._populate_embedding_packs()
        self._populate_cross_embedding_packs()

        header_row = QHBoxLayout()
        title = QLabel(t("language_packs.title"))
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(self.open_language_pack_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_row)
        layout.addWidget(self.language_pack_table)
        layout.addWidget(self.language_pack_status)

        frequency_row = QHBoxLayout()
        frequency_title = QLabel(t("language_packs.frequency_title"))
        frequency_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        frequency_row.addWidget(frequency_title)
        frequency_row.addStretch(1)
        frequency_row.addWidget(self.open_frequency_pack_button)
        layout.addLayout(frequency_row)
        frequency_desc = QLabel(t("language_packs.frequency_description"))
        frequency_desc.setWordWrap(True)
        layout.addWidget(frequency_desc)
        layout.addWidget(self.frequency_pack_table)

        embeddings_row = QHBoxLayout()
        embeddings_title = QLabel(t("language_packs.embeddings_title"))
        embeddings_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        help_button = QToolButton()
        help_button.setText("?")
        help_button.setToolTip(t("language_packs.embeddings_help"))
        help_button.setAutoRaise(True)
        help_button.clicked.connect(self._show_embeddings_help)
        embeddings_row.addWidget(embeddings_title)
        embeddings_row.addWidget(help_button)
        embeddings_row.addStretch(1)
        layout.addLayout(embeddings_row)
        embeddings_desc = QLabel(t("language_packs.embeddings_description"))
        embeddings_desc.setWordWrap(True)
        layout.addWidget(embeddings_desc)
        layout.addWidget(self.embedding_pack_table)

        cross_row = QHBoxLayout()
        cross_title = QLabel(t("language_packs.cross_embeddings_title"))
        cross_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        cross_help = QToolButton()
        cross_help.setText("?")
        cross_help.setToolTip(t("language_packs.cross_embeddings_help"))
        cross_help.setAutoRaise(True)
        cross_help.clicked.connect(self._show_cross_embeddings_help)
        cross_row.addWidget(cross_title)
        cross_row.addWidget(cross_help)
        cross_row.addStretch(1)
        layout.addLayout(cross_row)
        cross_desc = QLabel(t("language_packs.cross_embeddings_description"))
        cross_desc.setWordWrap(True)
        layout.addWidget(cross_desc)
        layout.addWidget(self.cross_embedding_pack_table)

    def apply_synonym_settings(self, synonym_settings: SynonymSourceSettings) -> None:
        self._seed_language_pack_paths(synonym_settings)
        self._seed_frequency_pack_paths(synonym_settings)
        self._seed_embedding_pack_paths(synonym_settings)
        self._auto_link_downloaded_packs()
        self._auto_link_downloaded_frequency_packs()
        self._auto_link_downloaded_embeddings()
        self._refresh_language_pack_table()
        self._refresh_frequency_pack_table()
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def paths(self) -> dict[str, str]:
        return dict(self._language_pack_paths)

    def frequency_paths(self) -> dict[str, str]:
        return dict(self._frequency_pack_paths)

    def embedding_paths(self) -> dict[str, str]:
        return dict(self._embedding_pack_paths)

    def embedding_pair_paths(self) -> dict[str, list[str]]:
        return {key: list(value) for key, value in self._embedding_pair_paths.items()}

    def embedding_pair_enabled(self) -> dict[str, bool]:
        return dict(self._embedding_pair_enabled)

    def cancel_downloads(self) -> None:
        self._closing = True
        for thread in list(self._language_pack_threads):
            if thread.isRunning():
                thread.requestInterruption()
        for thread in list(self._frequency_pack_threads):
            if thread.isRunning():
                thread.requestInterruption()

    def _open_language_pack_dir(self) -> None:
        reveal_path(self._language_pack_dir)

    def _open_frequency_pack_dir(self) -> None:
        reveal_path(self._frequency_pack_dir)

    def _show_embeddings_help(self) -> None:
        QMessageBox.information(
            self,
            t("language_packs.embeddings_title"),
            t("language_packs.embeddings_help"),
        )

    def _show_cross_embeddings_help(self) -> None:
        QMessageBox.information(
            self,
            t("language_packs.cross_embeddings_title"),
            t("language_packs.cross_embeddings_help"),
        )

    def _seed_language_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._language_pack_paths = dict(getattr(synonym_settings, "language_packs", {}) or {})
        if synonym_settings.wordnet_dir:
            self._language_pack_paths.setdefault("wordnet-en", synonym_settings.wordnet_dir)
        if synonym_settings.moby_path:
            self._language_pack_paths.setdefault("moby-en", synonym_settings.moby_path)

    def _seed_frequency_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._frequency_pack_paths = dict(getattr(synonym_settings, "frequency_packs", {}) or {})

    def _seed_embedding_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._embedding_pack_paths = dict(getattr(synonym_settings, "embedding_packs", {}) or {})
        self._embedding_pair_paths = {
            key: list(value)
            for key, value in dict(getattr(synonym_settings, "embedding_pair_paths", {}) or {}).items()
            if isinstance(value, (list, tuple))
        }
        self._embedding_pair_enabled = dict(
            getattr(synonym_settings, "embedding_pair_enabled", {}) or {}
        )

    def _refresh_language_pack_table(self) -> None:
        for pack_id, row in self._language_pack_rows.items():
            pack = self._language_pack_info.get(pack_id)
            if not pack:
                continue
            row.status_item.setToolTip("")
            row.status_item.setForeground(QColor("#2C2C2C"))
            dest_path = self._download_archive_path(pack)
            resolved_path = self._resolve_downloaded_path(pack)
            local_path = self._language_pack_paths.get(pack_id)
            if local_path:
                valid, message = self._validate_language_pack_path(pack, local_path)
                if valid:
                    row.status_item.setText(t("language_packs.status.local_ok"))
                    row.status_item.setForeground(QColor("#2F6B2F"))
                    row.status_item.setToolTip(local_path)
                else:
                    row.status_item.setText(t("language_packs.status.invalid"))
                    row.status_item.setForeground(QColor("#A03030"))
                    row.status_item.setToolTip(message)
            elif resolved_path:
                row.status_item.setText(t("language_packs.status.downloaded"))
                row.status_item.setForeground(QColor("#8A6D1D"))
                row.status_item.setToolTip(resolved_path)
            else:
                row.status_item.setText(t("language_packs.status.available"))
                row.status_item.setForeground(QColor("#5C5C5C"))
            download_exists = dest_path and os.path.exists(dest_path)
            row.delete_button.setEnabled(bool(local_path or resolved_path or download_exists))
            if download_exists or resolved_path:
                row.download_button.setText(t("buttons.redownload"))
            else:
                row.download_button.setText(t("buttons.download"))

    def _refresh_frequency_pack_table(self) -> None:
        for pack_id, row in self._frequency_pack_rows.items():
            pack = self._frequency_pack_info.get(pack_id)
            if not pack:
                continue
            row.status_item.setToolTip("")
            row.status_item.setForeground(QColor("#2C2C2C"))
            archive_path = self._frequency_archive_path(pack)
            sqlite_path = self._resolve_frequency_pack_path(pack)
            local_path = self._frequency_pack_paths.get(pack_id)
            if local_path:
                valid, message = self._validate_frequency_pack_path(pack, local_path)
                if valid:
                    row.status_item.setText(t("language_packs.status.local_ok"))
                    row.status_item.setForeground(QColor("#2F6B2F"))
                    row.status_item.setToolTip(local_path)
                else:
                    row.status_item.setText(t("language_packs.status.invalid"))
                    row.status_item.setForeground(QColor("#A03030"))
                    row.status_item.setToolTip(message)
            elif sqlite_path:
                row.status_item.setText(t("language_packs.status.downloaded"))
                row.status_item.setForeground(QColor("#8A6D1D"))
                row.status_item.setToolTip(sqlite_path)
            else:
                row.status_item.setText(t("language_packs.status.available"))
                row.status_item.setForeground(QColor("#5C5C5C"))
            download_exists = archive_path and os.path.exists(archive_path)
            row.delete_button.setEnabled(bool(local_path or sqlite_path or download_exists))
            if download_exists or sqlite_path:
                row.download_button.setText(t("buttons.redownload"))
            else:
                row.download_button.setText(t("buttons.download"))

    def _refresh_embedding_pack_table(self) -> None:
        self._refresh_embedding_rows(self._embedding_pack_rows)

    def _refresh_cross_embedding_pack_table(self) -> None:
        self._refresh_embedding_rows(self._cross_embedding_pack_rows)

    def _refresh_embedding_rows(self, rows: dict[str, EmbeddingPackRow]) -> None:
        for pack_id, row in rows.items():
            pack = self._embedding_pack_info.get(pack_id)
            if not pack:
                continue
            row.status_item.setToolTip("")
            row.status_item.setForeground(QColor("#2C2C2C"))
            dest_path = self._download_archive_path(pack, embeddings=True)
            resolved_path = self._resolve_downloaded_path(pack, embeddings=True)
            local_path = self._embedding_pack_paths.get(pack_id)
            pair_key = pack.pair_key
            is_active = False
            if pair_key:
                enabled = self._embedding_pair_enabled.get(pair_key, True)
                active_paths = {os.path.abspath(path) for path in self._embedding_pair_paths.get(pair_key, [])}
                if enabled and local_path and os.path.abspath(local_path) in active_paths:
                    is_active = True
                if enabled and resolved_path and os.path.abspath(resolved_path) in active_paths:
                    is_active = True
            if is_active and local_path:
                row.status_item.setText(t("language_packs.status.active"))
                row.status_item.setForeground(QColor("#1B4F9C"))
                row.status_item.setToolTip(local_path)
            elif is_active and resolved_path:
                row.status_item.setText(t("language_packs.status.active"))
                row.status_item.setForeground(QColor("#1B4F9C"))
                row.status_item.setToolTip(resolved_path)
            elif local_path:
                row.status_item.setText(t("language_packs.status.local_ok"))
                row.status_item.setForeground(QColor("#2F6B2F"))
                row.status_item.setToolTip(local_path)
            elif resolved_path:
                row.status_item.setText(t("language_packs.status.downloaded"))
                row.status_item.setForeground(QColor("#8A6D1D"))
                row.status_item.setToolTip(resolved_path)
            else:
                row.status_item.setText(t("language_packs.status.available"))
                row.status_item.setForeground(QColor("#5C5C5C"))
            download_exists = dest_path and os.path.exists(dest_path)
            row.delete_button.setEnabled(bool(local_path or resolved_path or download_exists))
            if download_exists or resolved_path:
                row.download_button.setText(t("buttons.redownload"))
            else:
                row.download_button.setText(t("buttons.download"))

    def _embedding_row_for(self, pack_id: str) -> Optional[EmbeddingPackRow]:
        return self._embedding_pack_rows.get(pack_id) or self._cross_embedding_pack_rows.get(pack_id)

    def _populate_language_packs(self) -> None:
        self._language_pack_rows.clear()
        self.language_pack_table.setRowCount(len(LANGUAGE_PACKS))
        for row, pack in enumerate(LANGUAGE_PACKS):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            source_item = QTableWidgetItem(pack.display_source())
            status_item = QTableWidgetItem(t("language_packs.status.available"))
            download_button = QPushButton(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_language_pack(pack_id)
            )
            local_button = QPushButton(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_language_pack_path(pack_id)
            )
            delete_button = QPushButton(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_language_pack(pack_id)
            )
            size_item = QTableWidgetItem(pack.size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.language_pack_table.setItem(row, 0, name_item)
            self.language_pack_table.setItem(row, 1, language_item)
            self.language_pack_table.setItem(row, 2, source_item)
            self.language_pack_table.setItem(row, 3, status_item)
            self.language_pack_table.setCellWidget(row, 4, download_button)
            self.language_pack_table.setCellWidget(row, 5, local_button)
            self.language_pack_table.setCellWidget(row, 6, delete_button)
            self.language_pack_table.setItem(row, 7, size_item)

            self._language_pack_rows[pack.pack_id] = LanguagePackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
            )
        self._refresh_language_pack_table()

    def _populate_frequency_packs(self) -> None:
        self._frequency_pack_rows.clear()
        self.frequency_pack_table.setRowCount(len(FREQUENCY_PACKS))
        for row, pack in enumerate(FREQUENCY_PACKS):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            source_item = QTableWidgetItem(pack.display_source())
            status_item = QTableWidgetItem(t("language_packs.status.available"))
            download_button = QPushButton(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_frequency_pack(pack_id)
            )
            local_button = QPushButton(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_frequency_pack_path(pack_id)
            )
            delete_button = QPushButton(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_frequency_pack(pack_id)
            )
            size_item = QTableWidgetItem(pack.size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.frequency_pack_table.setItem(row, 0, name_item)
            self.frequency_pack_table.setItem(row, 1, language_item)
            self.frequency_pack_table.setItem(row, 2, source_item)
            self.frequency_pack_table.setItem(row, 3, status_item)
            self.frequency_pack_table.setCellWidget(row, 4, download_button)
            self.frequency_pack_table.setCellWidget(row, 5, local_button)
            self.frequency_pack_table.setCellWidget(row, 6, delete_button)
            self.frequency_pack_table.setItem(row, 7, size_item)

            self._frequency_pack_rows[pack.pack_id] = FrequencyPackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
            )
        self._refresh_frequency_pack_table()

    def _populate_embedding_packs(self) -> None:
        self._embedding_pack_rows.clear()
        self.embedding_pack_table = QTableWidget()
        self.embedding_pack_table.setColumnCount(8)
        self.embedding_pack_table.setHorizontalHeaderLabels(
            [
                t("language_packs.headers.pack"),
                t("language_packs.headers.language"),
                t("language_packs.headers.status"),
                t("language_packs.headers.download"),
                t("language_packs.headers.local"),
                t("language_packs.headers.use"),
                t("language_packs.headers.delete"),
                t("language_packs.headers.size"),
            ]
        )
        self.embedding_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.embedding_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.embedding_pack_table.setAlternatingRowColors(True)
        self.embedding_pack_table.verticalHeader().setVisible(False)
        header = self.embedding_pack_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.embedding_pack_table.setMinimumHeight(220)

        self.embedding_pack_table.setRowCount(len(EMBEDDING_PACKS))
        for row, pack in enumerate(EMBEDDING_PACKS):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            status_item = QTableWidgetItem(t("language_packs.status.available"))
            download_button = QPushButton(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_embedding_pack(pack_id)
            )
            local_button = QPushButton(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_embedding_pack_path(pack_id)
            )
            use_button = QPushButton(t("buttons.use_embedding"))
            use_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._activate_embedding_pack(pack_id)
            )
            delete_button = QPushButton(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_embedding_pack(pack_id)
            )
            size_item = QTableWidgetItem(pack.size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.embedding_pack_table.setItem(row, 0, name_item)
            self.embedding_pack_table.setItem(row, 1, language_item)
            self.embedding_pack_table.setItem(row, 2, status_item)
            self.embedding_pack_table.setCellWidget(row, 3, download_button)
            self.embedding_pack_table.setCellWidget(row, 4, local_button)
            self.embedding_pack_table.setCellWidget(row, 5, use_button)
            self.embedding_pack_table.setCellWidget(row, 6, delete_button)
            self.embedding_pack_table.setItem(row, 7, size_item)

            self._embedding_pack_rows[pack.pack_id] = EmbeddingPackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
                use_button=use_button,
            )
        self._refresh_embedding_pack_table()

    def _populate_cross_embedding_packs(self) -> None:
        self._cross_embedding_pack_rows.clear()
        self.cross_embedding_pack_table = QTableWidget()
        self.cross_embedding_pack_table.setColumnCount(8)
        self.cross_embedding_pack_table.setHorizontalHeaderLabels(
            [
                t("language_packs.headers.pack"),
                t("language_packs.headers.language"),
                t("language_packs.headers.status"),
                t("language_packs.headers.download"),
                t("language_packs.headers.local"),
                t("language_packs.headers.use"),
                t("language_packs.headers.delete"),
                t("language_packs.headers.size"),
            ]
        )
        self.cross_embedding_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cross_embedding_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cross_embedding_pack_table.setAlternatingRowColors(True)
        self.cross_embedding_pack_table.verticalHeader().setVisible(False)
        header = self.cross_embedding_pack_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.cross_embedding_pack_table.setMinimumHeight(200)

        self.cross_embedding_pack_table.setRowCount(len(CROSS_EMBEDDING_PACKS))
        for row, pack in enumerate(CROSS_EMBEDDING_PACKS):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            status_item = QTableWidgetItem("")
            download_button = QPushButton(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_embedding_pack(pack_id)
            )
            local_button = QPushButton(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_embedding_pack_path(pack_id)
            )
            use_button = QPushButton(t("buttons.use_embedding"))
            use_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._activate_embedding_pack(pack_id)
            )
            delete_button = QPushButton(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_embedding_pack(pack_id)
            )
            size_item = QTableWidgetItem(pack.size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.cross_embedding_pack_table.setItem(row, 0, name_item)
            self.cross_embedding_pack_table.setItem(row, 1, language_item)
            self.cross_embedding_pack_table.setItem(row, 2, status_item)
            self.cross_embedding_pack_table.setCellWidget(row, 3, download_button)
            self.cross_embedding_pack_table.setCellWidget(row, 4, local_button)
            self.cross_embedding_pack_table.setCellWidget(row, 5, use_button)
            self.cross_embedding_pack_table.setCellWidget(row, 6, delete_button)
            self.cross_embedding_pack_table.setItem(row, 7, size_item)

            self._cross_embedding_pack_rows[pack.pack_id] = EmbeddingPackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
                use_button=use_button,
            )

        self._refresh_cross_embedding_pack_table()

    def _download_language_pack(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        dest_path = self._download_archive_path(pack)
        row.status_item.setText(t("language_packs.status.downloading"))
        row.download_button.setEnabled(False)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(
            t("language_packs.downloading", name=pack.display_name())
        )
        thread = LanguagePackDownloadThread(pack, dest_path, self)
        thread.progress.connect(self._on_language_pack_progress)
        thread.completed.connect(self._on_language_pack_completed)
        thread.failed.connect(self._on_language_pack_failed)
        thread.finished.connect(lambda: self._cleanup_language_pack_thread(thread))
        self._language_pack_threads.append(thread)
        thread.start()

    def _download_frequency_pack(self, pack_id: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        archive_path = self._frequency_archive_path(pack)
        sqlite_path = self._frequency_sqlite_path(pack)
        row.status_item.setText(t("language_packs.status.downloading"))
        row.download_button.setEnabled(False)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(
            t("language_packs.downloading", name=pack.display_name())
        )
        thread = FrequencyPackDownloadThread(pack, archive_path, sqlite_path, self)
        thread.progress.connect(self._on_frequency_pack_progress)
        thread.completed.connect(self._on_frequency_pack_completed)
        thread.failed.connect(self._on_frequency_pack_failed)
        thread.finished.connect(lambda: self._cleanup_frequency_pack_thread(thread))
        self._frequency_pack_threads.append(thread)
        thread.start()

    def _download_embedding_pack(self, pack_id: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        dest_path = self._download_archive_path(pack, embeddings=True)
        row.status_item.setText(t("language_packs.status.downloading"))
        row.download_button.setEnabled(False)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(
            t("language_packs.downloading", name=pack.display_name())
        )
        thread = LanguagePackDownloadThread(pack, dest_path, self)
        thread.progress.connect(self._on_embedding_pack_progress)
        thread.completed.connect(self._on_embedding_pack_completed)
        thread.failed.connect(self._on_embedding_pack_failed)
        thread.finished.connect(lambda: self._cleanup_language_pack_thread(thread))
        self._language_pack_threads.append(thread)
        thread.start()

    def _select_language_pack_path(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        if not pack:
            return
        if pack.local_kind == "dir":
            path = QFileDialog.getExistingDirectory(
                self,
                t("dialogs.select_pack_directory", name=pack.display_name()),
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                t("dialogs.select_pack_file", name=pack.display_name()),
                "",
                t("filters.all"),
            )
        if not path:
            return
        if pack.pack_id == "wordnet-en":
            path = self._normalize_wordnet_path(path)
        valid, message = self._validate_language_pack_path(pack, path)
        if not valid:
            QMessageBox.warning(self, t("dialogs.invalid_resource.title"), message)
            self.language_pack_status.setStyleSheet("color: #A03030;")
            self.language_pack_status.setText(message)
            self._language_pack_paths.pop(pack_id, None)
            self._refresh_language_pack_table()
            return
        self._language_pack_paths[pack_id] = path
        self.language_pack_status.setStyleSheet("color: #2F6B2F;")
        self.language_pack_status.setText(
            t("language_packs.linked", name=pack.display_name(), path=path)
        )
        self._refresh_language_pack_table()

    def _select_frequency_pack_path(self, pack_id: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        if not pack:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.select_pack_file", name=pack.display_name()),
            "",
            t("filters.all"),
        )
        if not path:
            return
        valid, message = self._validate_frequency_pack_path(pack, path)
        if not valid:
            QMessageBox.warning(self, t("dialogs.invalid_resource.title"), message)
            self.language_pack_status.setStyleSheet("color: #A03030;")
            self.language_pack_status.setText(message)
            self._frequency_pack_paths.pop(pack_id, None)
            self._refresh_frequency_pack_table()
            return
        self._frequency_pack_paths[pack_id] = path
        self.language_pack_status.setStyleSheet("color: #2F6B2F;")
        self.language_pack_status.setText(
            t("language_packs.linked", name=pack.display_name(), path=path)
        )
        self._refresh_frequency_pack_table()

    def _select_embedding_pack_path(self, pack_id: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        if not pack:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.select_pack_file", name=pack.display_name()),
            "",
            t("filters.embeddings"),
        )
        if not path:
            return
        if not os.path.isfile(path):
            QMessageBox.warning(self, t("dialogs.invalid_resource.title"), t("language_packs.validation.expected_file", name=pack.display_name()))
            return
        self._embedding_pack_paths[pack_id] = path
        self.language_pack_status.setStyleSheet("color: #2F6B2F;")
        self.language_pack_status.setText(
            t("language_packs.linked", name=pack.display_name(), path=path)
        )
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _delete_language_pack(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        local_path = self._language_pack_paths.get(pack_id)
        archive_path = self._download_archive_path(pack)
        resolved_path = self._resolve_downloaded_path(pack)
        delete_paths = []
        if local_path and self._is_app_data_path(local_path):
            delete_paths.append(local_path)
        if archive_path and os.path.exists(archive_path) and self._is_app_data_path(archive_path):
            delete_paths.append(archive_path)
        if resolved_path and os.path.exists(resolved_path) and self._is_app_data_path(resolved_path):
            delete_paths.append(resolved_path)
        delete_paths = list(dict.fromkeys(delete_paths))
        unlink_only = local_path and not delete_paths
        if not delete_paths and not unlink_only:
            QMessageBox.information(
                self,
                t("language_packs.title"),
                t("language_packs.no_local_files", name=pack.display_name()),
            )
            self._language_pack_paths.pop(pack_id, None)
            self._refresh_language_pack_table()
            return
        if unlink_only:
            message = t("language_packs.unlink_confirm", name=pack.display_name())
        else:
            message = t("language_packs.delete_confirm", name=pack.display_name())
        reply = QMessageBox.question(
            self,
            t("language_packs.delete_title"),
            message,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        self._language_pack_paths.pop(pack_id, None)
        for path in delete_paths:
            self._remove_path(path)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(t("language_packs.removed", name=pack.display_name()))
        self._refresh_language_pack_table()

    def _delete_frequency_pack(self, pack_id: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        local_path = self._frequency_pack_paths.get(pack_id)
        archive_path = self._frequency_archive_path(pack)
        sqlite_path = self._frequency_sqlite_path(pack)
        delete_paths = []
        if local_path and self._is_frequency_pack_data_path(local_path):
            delete_paths.append(local_path)
        if archive_path and os.path.exists(archive_path) and self._is_frequency_pack_data_path(archive_path):
            delete_paths.append(archive_path)
        if sqlite_path and os.path.exists(sqlite_path) and self._is_frequency_pack_data_path(sqlite_path):
            delete_paths.append(sqlite_path)
        delete_paths = list(dict.fromkeys(delete_paths))
        unlink_only = local_path and not delete_paths
        if not delete_paths and not unlink_only:
            QMessageBox.information(
                self,
                t("language_packs.frequency_title"),
                t("language_packs.no_local_files", name=pack.display_name()),
            )
            self._frequency_pack_paths.pop(pack_id, None)
            self._refresh_frequency_pack_table()
            return
        if unlink_only:
            message = t("language_packs.unlink_confirm", name=pack.display_name())
        else:
            message = t("language_packs.delete_confirm", name=pack.display_name())
        reply = QMessageBox.question(
            self,
            t("language_packs.delete_title"),
            message,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        self._frequency_pack_paths.pop(pack_id, None)
        for path in delete_paths:
            self._remove_path(path)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(t("language_packs.removed", name=pack.display_name()))
        self._refresh_frequency_pack_table()

    def _delete_embedding_pack(self, pack_id: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        local_path = self._embedding_pack_paths.get(pack_id)
        archive_path = self._download_archive_path(pack, embeddings=True)
        resolved_path = self._resolve_downloaded_path(pack, embeddings=True)
        delete_paths = []
        if local_path and self._is_app_data_path(local_path, embeddings=True):
            delete_paths.append(local_path)
        if archive_path and os.path.exists(archive_path) and self._is_app_data_path(archive_path, embeddings=True):
            delete_paths.append(archive_path)
        if resolved_path and os.path.exists(resolved_path) and self._is_app_data_path(resolved_path, embeddings=True):
            delete_paths.append(resolved_path)
        delete_paths = list(dict.fromkeys(delete_paths))
        unlink_only = local_path and not delete_paths
        if not delete_paths and not unlink_only:
            QMessageBox.information(
                self,
                t("language_packs.title"),
                t("language_packs.no_local_files", name=pack.display_name()),
            )
            self._embedding_pack_paths.pop(pack_id, None)
            self._refresh_embedding_pack_table()
            self._refresh_cross_embedding_pack_table()
            return
        if unlink_only:
            message = t("language_packs.unlink_confirm", name=pack.display_name())
        else:
            message = t("language_packs.delete_confirm", name=pack.display_name())
        reply = QMessageBox.question(
            self,
            t("language_packs.delete_title"),
            message,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        self._embedding_pack_paths.pop(pack_id, None)
        if pack.pair_key and local_path:
            pair_key = pack.pair_key
            paths = [path for path in self._embedding_pair_paths.get(pair_key, []) if path != local_path]
            if paths:
                self._embedding_pair_paths[pair_key] = paths
            else:
                self._embedding_pair_paths.pop(pair_key, None)
        for path in delete_paths:
            self._remove_path(path)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(t("language_packs.removed", name=pack.display_name()))
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _activate_embedding_pack(self, pack_id: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        local_path = self._embedding_pack_paths.get(pack_id)
        if not local_path:
            resolved = self._resolve_downloaded_path(pack, embeddings=True)
            if resolved and os.path.isfile(resolved):
                local_path = resolved
                self._embedding_pack_paths[pack_id] = local_path
        if not local_path:
            return
        if pack and pack.pair_key:
            pair_key = pack.pair_key
            paths = list(self._embedding_pair_paths.get(pair_key, []))
            if local_path not in paths:
                paths.append(local_path)
            self._embedding_pair_paths[pair_key] = paths
            self._embedding_pair_enabled[pair_key] = True
        # per-pair activation is tracked in _embedding_pair_paths/_embedding_pair_enabled
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _validate_language_pack_path(self, pack: LanguagePackInfo, path: str) -> tuple[bool, str]:
        if pack.local_kind == "dir":
            if not os.path.isdir(path):
                return False, t("language_packs.validation.expected_dir", name=pack.display_name())
            if pack.pack_id == "wordnet-en":
                if self._has_wordnet_classic(path) or self._has_wordnet_json(path):
                    return True, ""
                return False, t("language_packs.validation.wordnet")
            missing = [
                name for name in pack.required_files if not os.path.exists(os.path.join(path, name))
            ]
            if missing:
                missing_str = ", ".join(missing)
                return False, t(
                    "language_packs.validation.missing_files",
                    name=pack.display_name(),
                    files=missing_str,
                )
            return True, ""
        if not os.path.isfile(path):
            return False, t("language_packs.validation.expected_file", name=pack.display_name())
        if pack.pack_id == "jp-wordnet-sqlite":
            if not self._is_sqlite_db(path):
                return False, t("language_packs.validation.sqlite")
        return True, ""

    def _validate_frequency_pack_path(self, pack: FrequencyPackInfo, path: str) -> tuple[bool, str]:
        if not os.path.isfile(path):
            return False, t("language_packs.validation.expected_file", name=pack.display_name())
        if not self._is_sqlite_db(path):
            return False, t("language_packs.validation.sqlite")
        return True, ""

    def _auto_link_downloaded_packs(self) -> None:
        for pack_id, pack in self._language_pack_info.items():
            if pack_id in self._language_pack_paths:
                continue
            candidate = self._resolve_downloaded_path(pack)
            if not candidate:
                continue
            valid, _message = self._validate_language_pack_path(pack, candidate)
            if valid:
                self._language_pack_paths[pack_id] = candidate

    def _auto_link_downloaded_frequency_packs(self) -> None:
        for pack_id, pack in self._frequency_pack_info.items():
            if pack_id in self._frequency_pack_paths:
                continue
            candidate = self._resolve_frequency_pack_path(pack)
            if not candidate:
                continue
            valid, _message = self._validate_frequency_pack_path(pack, candidate)
            if valid:
                self._frequency_pack_paths[pack_id] = candidate

    def _auto_link_downloaded_embeddings(self) -> None:
        for pack_id, pack in self._embedding_pack_info.items():
            if pack_id in self._embedding_pack_paths:
                continue
            candidate = self._resolve_downloaded_path(pack, embeddings=True)
            if candidate:
                self._embedding_pack_paths[pack_id] = candidate

    def _download_archive_path(self, pack: LanguagePackInfo, *, embeddings: bool = False) -> str:
        base_dir = self._embedding_pack_dir if embeddings else self._language_pack_dir
        return os.path.join(base_dir, pack.filename)

    def _frequency_archive_path(self, pack: FrequencyPackInfo) -> str:
        return os.path.join(self._frequency_pack_dir, pack.filename)

    def _frequency_sqlite_path(self, pack: FrequencyPackInfo) -> str:
        return os.path.join(self._frequency_pack_dir, pack.sqlite_filename)

    def _resolve_downloaded_path(self, pack: Optional[LanguagePackInfo], *, embeddings: bool = False) -> Optional[str]:
        if not pack:
            return None
        archive_path = self._download_archive_path(pack, embeddings=embeddings)
        if archive_path.endswith(".zip"):
            extracted = os.path.splitext(archive_path)[0]
            if os.path.isdir(extracted):
                return extracted
        if archive_path.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz")):
            extracted = archive_path
            for suffix in (".tar.gz", ".tgz", ".tar.xz", ".txz"):
                if extracted.endswith(suffix):
                    extracted = extracted[: -len(suffix)]
                    break
            if os.path.isdir(extracted):
                return extracted
        if archive_path.endswith(".gz"):
            extracted = os.path.splitext(archive_path)[0]
            if os.path.exists(extracted):
                return extracted
        if os.path.exists(archive_path):
            return archive_path
        return None

    def _resolve_frequency_pack_path(self, pack: Optional[FrequencyPackInfo]) -> Optional[str]:
        if not pack:
            return None
        sqlite_path = self._frequency_sqlite_path(pack)
        if os.path.exists(sqlite_path):
            return sqlite_path
        return None

    def _is_app_data_path(self, path: str, *, embeddings: bool = False) -> bool:
        base = os.path.abspath(self._embedding_pack_dir if embeddings else self._language_pack_dir)
        target = os.path.abspath(os.path.expanduser(path))
        try:
            return os.path.commonpath([base, target]) == base
        except ValueError:
            return False

    def _is_frequency_pack_data_path(self, path: str) -> bool:
        base = os.path.abspath(self._frequency_pack_dir)
        target = os.path.abspath(os.path.expanduser(path))
        try:
            return os.path.commonpath([base, target]) == base
        except ValueError:
            return False

    def _remove_path(self, path: str) -> None:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def _has_wordnet_classic(self, path: str) -> bool:
        required = ("data.noun", "data.verb", "data.adj", "data.adv")
        return all(os.path.exists(os.path.join(path, name)) for name in required)

    def _has_wordnet_json(self, path: str) -> bool:
        markers = ("entries-a.json", "adj.all.json", "adv.all.json", "noun.act.json", "verb.body.json")
        return any(os.path.exists(os.path.join(path, name)) for name in markers)

    def _normalize_wordnet_path(self, path: str) -> str:
        if not os.path.isdir(path):
            return path
        if self._has_wordnet_classic(path) or self._has_wordnet_json(path):
            return path
        entries = [entry for entry in os.listdir(path) if os.path.isdir(os.path.join(path, entry))]
        if len(entries) == 1:
            candidate = os.path.join(path, entries[0])
            if self._has_wordnet_classic(candidate) or self._has_wordnet_json(candidate):
                return candidate
        return path

    def _is_sqlite_db(self, path: str) -> bool:
        try:
            with open(path, "rb") as handle:
                header = handle.read(16)
            return header.startswith(b"SQLite format 3")
        except OSError:
            return False

    def _on_language_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._language_pack_rows.get(pack_id)
        if not row:
            return
        row.status_item.setForeground(QColor("#1B4F9C"))
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(t("language_packs.status.downloading_pct", percent=pct))
        else:
            row.status_item.setText(t("language_packs.status.downloading"))

    def _on_frequency_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._frequency_pack_rows.get(pack_id)
        if not row:
            return
        row.status_item.setForeground(QColor("#1B4F9C"))
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(t("language_packs.status.downloading_pct", percent=pct))
        else:
            row.status_item.setText(t("language_packs.status.downloading"))

    def _on_embedding_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._embedding_row_for(pack_id)
        if not row:
            return
        row.status_item.setForeground(QColor("#1B4F9C"))
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(t("language_packs.status.downloading_pct", percent=pct))
        else:
            row.status_item.setText(t("language_packs.status.downloading"))

    def _on_language_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if pack.pack_id == "wordnet-en":
            dest_path = self._normalize_wordnet_path(dest_path)
        valid, message = self._validate_language_pack_path(pack, dest_path)
        if valid:
            self._language_pack_paths[pack_id] = dest_path
            row.status_item.setText(t("language_packs.status.local_ok"))
            row.status_item.setToolTip(dest_path)
            self.language_pack_status.setStyleSheet("color: #2F6B2F;")
            self.language_pack_status.setText(
                t("language_packs.downloaded_linked", name=pack.display_name(), path=dest_path)
            )
        else:
            self._language_pack_paths.pop(pack_id, None)
            row.status_item.setText(t("language_packs.status.downloaded"))
            row.status_item.setToolTip(dest_path)
            self.language_pack_status.setStyleSheet("color: #A03030;")
            self.language_pack_status.setText(
                t("language_packs.downloaded_invalid", name=pack.display_name(), message=message)
            )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        self._refresh_language_pack_table()

    def _on_frequency_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        valid, message = self._validate_frequency_pack_path(pack, dest_path)
        if valid:
            self._frequency_pack_paths[pack_id] = dest_path
            row.status_item.setText(t("language_packs.status.local_ok"))
            row.status_item.setToolTip(dest_path)
            self.language_pack_status.setStyleSheet("color: #2F6B2F;")
            self.language_pack_status.setText(
                t("language_packs.downloaded_linked", name=pack.display_name(), path=dest_path)
            )
        else:
            self._frequency_pack_paths.pop(pack_id, None)
            row.status_item.setText(t("language_packs.status.downloaded"))
            row.status_item.setToolTip(dest_path)
            self.language_pack_status.setStyleSheet("color: #A03030;")
            self.language_pack_status.setText(
                t("language_packs.downloaded_invalid", name=pack.display_name(), message=message)
            )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        self._refresh_frequency_pack_table()

    def _on_embedding_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        self._embedding_pack_paths[pack_id] = dest_path
        row.status_item.setText(t("language_packs.status.local_ok"))
        row.status_item.setToolTip(dest_path)
        self.language_pack_status.setStyleSheet("color: #2F6B2F;")
        self.language_pack_status.setText(
            t("language_packs.downloaded_linked", name=pack.display_name(), path=dest_path)
        )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _on_language_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if message == "cancelled" and self._closing:
            row.status_item.setText(t("language_packs.status.cancelled"))
            row.status_item.setForeground(QColor("#6B6B6B"))
            row.download_button.setEnabled(True)
            row.download_button.setText(t("buttons.download"))
            return
        row.status_item.setText(t("language_packs.status.failed"))
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        link = pack.wayback_url
        log_path = download_log_path()
        row.status_item.setToolTip(log_path)
        self.language_pack_status.setToolTip(log_path)
        self.language_pack_status.setStyleSheet("color: #A03030;")
        self.language_pack_status.setText(
            t("language_packs.download_failed", name=pack.display_name(), error=message, link=link)
        )

    def _on_frequency_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if message == "cancelled" and self._closing:
            row.status_item.setText(t("language_packs.status.cancelled"))
            row.status_item.setForeground(QColor("#6B6B6B"))
            row.download_button.setEnabled(True)
            row.download_button.setText(t("buttons.download"))
            return
        row.status_item.setText(t("language_packs.status.failed"))
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        link = pack.wayback_url
        log_path = download_log_path()
        row.status_item.setToolTip(log_path)
        self.language_pack_status.setToolTip(log_path)
        self.language_pack_status.setStyleSheet("color: #A03030;")
        self.language_pack_status.setText(
            t("language_packs.download_failed", name=pack.display_name(), error=message, link=link)
        )

    def _on_embedding_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        if message == "cancelled" and self._closing:
            row.status_item.setText(t("language_packs.status.cancelled"))
            row.status_item.setForeground(QColor("#6B6B6B"))
            row.download_button.setEnabled(True)
            row.download_button.setText(t("buttons.download"))
            return
        row.status_item.setText(t("language_packs.status.failed"))
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        link = pack.wayback_url
        log_path = download_log_path()
        row.status_item.setToolTip(log_path)
        self.language_pack_status.setToolTip(log_path)
        self.language_pack_status.setStyleSheet("color: #A03030;")
        self.language_pack_status.setText(
            t("language_packs.download_failed", name=pack.display_name(), error=message, link=link)
        )

    def _cleanup_language_pack_thread(self, thread: LanguagePackDownloadThread) -> None:
        if thread in self._language_pack_threads:
            self._language_pack_threads.remove(thread)
        thread.deleteLater()

    def _cleanup_frequency_pack_thread(self, thread: FrequencyPackDownloadThread) -> None:
        if thread in self._frequency_pack_threads:
            self._frequency_pack_threads.remove(thread)
        thread.deleteLater()


def _language_pack_dir() -> str:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    base_dir = base_dir or os.path.expanduser("~")
    target = os.path.join(base_dir, "language_packs")
    os.makedirs(target, exist_ok=True)
    return target


def _embedding_pack_dir() -> str:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    base_dir = base_dir or os.path.expanduser("~")
    target = os.path.join(base_dir, "embeddings")
    os.makedirs(target, exist_ok=True)
    return target


def _frequency_pack_dir() -> str:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    base_dir = base_dir or os.path.expanduser("~")
    target = os.path.join(base_dir, "frequency_packs")
    os.makedirs(target, exist_ok=True)
    return target
