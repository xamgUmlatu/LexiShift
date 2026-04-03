from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from i18n import t
from language_packs import (
    CROSS_EMBEDDING_PACKS,
    EMBEDDING_PACKS,
    FREQUENCY_PACKS,
    LANGUAGE_PACKS,
)
from settings_language_packs_support import (
    LANGUAGE_RESOURCE_ORIGIN_MANAGED,
    EmbeddingPackRow,
    FrequencyPackRow,
    LanguagePackRow,
)


class LanguagePackPanelTableMixin:
    def _language_pack_status_key(self, pack_id: str, path: str) -> str:
        if self._is_installed_language_pack_entry(pack_id, path):
            return "language_packs.status.installed"
        return "language_packs.status.manual"

    def _frequency_pack_status_key(self, pack_id: str, path: str) -> str:
        if self._is_installed_frequency_pack_entry(pack_id, path):
            return "language_packs.status.installed"
        return "language_packs.status.manual"

    def _embedding_pack_status_key(self, pack_id: str, path: str, *, active: bool) -> str:
        if self._is_installed_embedding_pack_entry(pack_id, path):
            if active:
                return "language_packs.status.active_installed"
            return "language_packs.status.installed"
        if active:
            return "language_packs.status.active_manual"
        return "language_packs.status.manual"

    def _refresh_language_pack_table(self) -> None:
        for pack_id, row in self._language_pack_rows.items():
            pack = self._language_pack_info.get(pack_id)
            if not pack:
                continue
            binding = self._language_resource_binding(pack_id)
            row.status_item.setToolTip("")
            self._set_status_item_tone(row.status_item, "neutral")
            dest_path = self._download_archive_path(pack)
            resolved_path = self._resolve_downloaded_path(pack)
            local_path = self._language_resource_effective_path(pack_id)
            if local_path:
                valid, message = self._validate_language_pack_path(pack, local_path)
                if valid:
                    status_key = self._language_pack_status_key(pack_id, local_path)
                    if binding and binding.origin == LANGUAGE_RESOURCE_ORIGIN_MANAGED:
                        status_key = "language_packs.status.installed"
                    row.status_item.setText(t(status_key))
                    self._set_status_item_tone(
                        row.status_item,
                        "success" if status_key == "language_packs.status.installed" else "info",
                    )
                    row.status_item.setToolTip(local_path)
                else:
                    row.status_item.setText(t("language_packs.status.invalid"))
                    self._set_status_item_tone(row.status_item, "error")
                    row.status_item.setToolTip(message)
            elif resolved_path:
                valid, message = self._validate_language_pack_path(pack, resolved_path)
                if valid:
                    row.status_item.setText(t("language_packs.status.installed"))
                    self._set_status_item_tone(row.status_item, "success")
                    row.status_item.setToolTip(resolved_path)
                else:
                    row.status_item.setText(t("language_packs.status.invalid"))
                    self._set_status_item_tone(row.status_item, "error")
                    row.status_item.setToolTip(message)
            else:
                row.status_item.setText(t("language_packs.status.available"))
                self._set_status_item_tone(row.status_item, "muted")
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
            self._set_status_item_tone(row.status_item, "neutral")
            archive_path = self._frequency_archive_path(pack)
            sqlite_path = self._resolve_frequency_pack_path(pack)
            local_path = self._frequency_pack_paths.get(pack_id)
            if local_path:
                valid, message = self._validate_frequency_pack_path(pack, local_path)
                if valid:
                    row.status_item.setText(t(self._frequency_pack_status_key(pack_id, local_path)))
                    self._set_status_item_tone(
                        row.status_item,
                        "success"
                        if self._is_installed_frequency_pack_entry(pack_id, local_path)
                        else "info",
                    )
                    row.status_item.setToolTip(local_path)
                else:
                    row.status_item.setText(t("language_packs.status.invalid"))
                    self._set_status_item_tone(row.status_item, "error")
                    row.status_item.setToolTip(message)
            elif sqlite_path:
                valid, message = self._validate_frequency_pack_path(pack, sqlite_path)
                if valid:
                    row.status_item.setText(t("language_packs.status.installed"))
                    self._set_status_item_tone(row.status_item, "success")
                    row.status_item.setToolTip(sqlite_path)
                else:
                    row.status_item.setText(t("language_packs.status.invalid"))
                    self._set_status_item_tone(row.status_item, "error")
                    row.status_item.setToolTip(message)
            else:
                row.status_item.setText(t("language_packs.status.available"))
                self._set_status_item_tone(row.status_item, "muted")
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
            self._set_status_item_tone(row.status_item, "neutral")
            dest_path = self._download_archive_path(pack, embeddings=True)
            resolved_path = self._resolve_downloaded_path(pack, embeddings=True)
            local_path = self._embedding_pack_paths.get(pack_id)
            pair_key = pack.pair_key
            is_active = False
            if pair_key:
                enabled = self._embedding_pair_enabled.get(pair_key, True)
                active_pack_ids = set(self._embedding_pair_pack_ids.get(pair_key, []))
                active_paths = {
                    os.path.abspath(path) for path in self._embedding_pair_paths.get(pair_key, [])
                }
                if enabled and pack_id in active_pack_ids:
                    is_active = True
                if enabled and local_path and os.path.abspath(local_path) in active_paths:
                    is_active = True
                if enabled and resolved_path and os.path.abspath(resolved_path) in active_paths:
                    is_active = True
            if is_active and local_path:
                row.status_item.setText(
                    t(self._embedding_pack_status_key(pack_id, local_path, active=True))
                )
                self._set_status_item_tone(row.status_item, "info")
                row.status_item.setToolTip(local_path)
            elif is_active and resolved_path:
                row.status_item.setText(t("language_packs.status.active_installed"))
                self._set_status_item_tone(row.status_item, "info")
                row.status_item.setToolTip(resolved_path)
            elif local_path:
                row.status_item.setText(
                    t(self._embedding_pack_status_key(pack_id, local_path, active=False))
                )
                self._set_status_item_tone(
                    row.status_item,
                    "success"
                    if self._is_installed_embedding_pack_entry(pack_id, local_path)
                    else "info",
                )
                row.status_item.setToolTip(local_path)
            elif resolved_path:
                row.status_item.setText(t("language_packs.status.installed"))
                self._set_status_item_tone(row.status_item, "success")
                row.status_item.setToolTip(resolved_path)
            else:
                row.status_item.setText(t("language_packs.status.available"))
                self._set_status_item_tone(row.status_item, "muted")
            download_exists = dest_path and os.path.exists(dest_path)
            row.delete_button.setEnabled(bool(local_path or resolved_path or download_exists))
            if download_exists or resolved_path:
                row.download_button.setText(t("buttons.redownload"))
            else:
                row.download_button.setText(t("buttons.download"))

    def _embedding_row_for(self, pack_id: str) -> Optional[EmbeddingPackRow]:
        return self._embedding_pack_rows.get(pack_id) or self._cross_embedding_pack_rows.get(
            pack_id
        )

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
                lambda checked=False, pack_id=pack.pack_id: self._select_frequency_pack_path(
                    pack_id
                )
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
                lambda checked=False, pack_id=pack.pack_id: self._select_embedding_pack_path(
                    pack_id
                )
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
                lambda checked=False, pack_id=pack.pack_id: self._select_embedding_pack_path(
                    pack_id
                )
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
