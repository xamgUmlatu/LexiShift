from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
)

from i18n import t
from settings_language_packs_support import (
    LANGUAGE_RESOURCE_ORIGIN_MANAGED,
    EmbeddingPackRow,
    FrequencyPackRow,
    LanguagePackRow,
    is_pack_download_disabled,
    pack_download_disabled_tooltip,
)

_LANGUAGE_RESOURCE_COLUMN_WIDTHS = {
    0: 240,
    1: 120,
    2: 128,
    3: 150,
    4: 126,
    5: 112,
    6: 112,
    7: 86,
    8: 76,
}
_EMBEDDING_RESOURCE_COLUMN_WIDTHS = {
    0: 260,
    1: 145,
    2: 160,
    3: 126,
    4: 112,
    5: 116,
    6: 112,
    7: 86,
    8: 76,
}


class ResourcePackTable(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._base_column_widths: dict[int, int] = {}
        self._surplus_columns: tuple[int, ...] = ()
        self._applying_widths = False

    def configure_resource_columns(
        self,
        column_widths: dict[int, int],
        *,
        surplus_columns: tuple[int, ...],
    ) -> None:
        self._base_column_widths = dict(column_widths)
        self._surplus_columns = tuple(surplus_columns)
        self._apply_responsive_column_widths()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_column_widths()

    def _apply_responsive_column_widths(self) -> None:
        if self._applying_widths or not self._base_column_widths:
            return
        viewport_width = max(0, self.viewport().width())
        base_total = sum(self._base_column_widths.values())
        surplus = max(0, viewport_width - base_total)
        surplus_columns = tuple(
            column
            for column in self._surplus_columns
            if 0 <= column < self.columnCount() and column in self._base_column_widths
        )
        extra_per_column = surplus // len(surplus_columns) if surplus_columns else 0
        remainder = surplus % len(surplus_columns) if surplus_columns else 0
        self._applying_widths = True
        try:
            for column in range(self.columnCount()):
                width = self._base_column_widths.get(column)
                if width is None:
                    continue
                extra = 0
                if column in surplus_columns:
                    extra = extra_per_column + (1 if remainder > 0 else 0)
                    remainder = max(0, remainder - 1)
                self.setColumnWidth(column, width + extra)
        finally:
            self._applying_widths = False


class LanguagePackPanelTableMixin:
    def _resource_table_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("resourceTableAction", True)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(0)
        button.setMaximumHeight(26)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return button

    def _resource_table_info_button(self, pack, handler) -> QPushButton:
        button = self._resource_table_button("")
        button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        button.setMaximumWidth(42)
        button.setToolTip(
            t("language_packs.source_license.button_tooltip", name=pack.display_name())
        )
        button.setAccessibleName(t("language_packs.source_license.button"))
        button.clicked.connect(lambda checked=False, pack_id=pack.pack_id: handler(pack_id))
        return button

    def _configure_language_resource_table(self, table: QTableWidget) -> None:
        self._configure_resource_table_columns(
            table,
            _LANGUAGE_RESOURCE_COLUMN_WIDTHS,
            surplus_columns=(0, 3),
        )

    def _configure_embedding_resource_table(self, table: QTableWidget) -> None:
        self._configure_resource_table_columns(
            table,
            _EMBEDDING_RESOURCE_COLUMN_WIDTHS,
            surplus_columns=(0, 2),
        )

    def _configure_resource_table_columns(
        self,
        table: QTableWidget,
        column_widths: dict[int, int],
        *,
        surplus_columns: tuple[int, ...],
    ) -> None:
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setWordWrap(False)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(72)
        for column in range(table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            width = column_widths.get(column)
            if width:
                table.setColumnWidth(column, width)
        if isinstance(table, ResourcePackTable):
            table.configure_resource_columns(
                column_widths,
                surplus_columns=surplus_columns,
            )

    def _refresh_download_button_state(
        self,
        *,
        pack,
        download_button: QPushButton,
        download_exists: bool,
        resolved_path: str | None,
    ) -> None:
        if download_exists or resolved_path:
            download_button.setText(t("buttons.redownload"))
        else:
            download_button.setText(t("buttons.download"))
        if is_pack_download_disabled(
            getattr(self, "_pack_source_overrides", {}),
            pack.pack_id,
            pack,
        ):
            download_button.setEnabled(False)
            download_button.setToolTip(
                pack_download_disabled_tooltip(getattr(self, "_pack_source_overrides", {}), pack)
            )
            return
        download_button.setEnabled(True)
        download_button.setToolTip("")

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
            elif is_pack_download_disabled(
                getattr(self, "_pack_source_overrides", {}),
                pack_id,
                pack,
            ):
                row.status_item.setText(t("rules_table.disabled"))
                self._set_status_item_tone(row.status_item, "error")
                row.status_item.setToolTip(
                    pack_download_disabled_tooltip(
                        getattr(self, "_pack_source_overrides", {}),
                        pack,
                    )
                )
            else:
                row.status_item.setText(t("language_packs.status.available"))
                self._set_status_item_tone(row.status_item, "muted")
            download_exists = dest_path and os.path.exists(dest_path)
            row.delete_button.setEnabled(bool(local_path or resolved_path or download_exists))
            self._refresh_download_button_state(
                pack=pack,
                download_button=row.download_button,
                download_exists=bool(download_exists),
                resolved_path=resolved_path,
            )

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
            elif is_pack_download_disabled(
                getattr(self, "_pack_source_overrides", {}),
                pack_id,
                pack,
            ):
                row.status_item.setText(t("rules_table.disabled"))
                self._set_status_item_tone(row.status_item, "error")
                row.status_item.setToolTip(
                    pack_download_disabled_tooltip(
                        getattr(self, "_pack_source_overrides", {}),
                        pack,
                    )
                )
            else:
                row.status_item.setText(t("language_packs.status.available"))
                self._set_status_item_tone(row.status_item, "muted")
            download_exists = archive_path and os.path.exists(archive_path)
            row.delete_button.setEnabled(bool(local_path or sqlite_path or download_exists))
            self._refresh_download_button_state(
                pack=pack,
                download_button=row.download_button,
                download_exists=bool(download_exists),
                resolved_path=sqlite_path,
            )

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
            elif is_pack_download_disabled(
                getattr(self, "_pack_source_overrides", {}),
                pack_id,
                pack,
            ):
                row.status_item.setText(t("rules_table.disabled"))
                self._set_status_item_tone(row.status_item, "error")
                row.status_item.setToolTip(
                    pack_download_disabled_tooltip(
                        getattr(self, "_pack_source_overrides", {}),
                        pack,
                    )
                )
            else:
                row.status_item.setText(t("language_packs.status.available"))
                self._set_status_item_tone(row.status_item, "muted")
            download_exists = dest_path and os.path.exists(dest_path)
            row.delete_button.setEnabled(bool(local_path or resolved_path or download_exists))
            self._refresh_download_button_state(
                pack=pack,
                download_button=row.download_button,
                download_exists=bool(download_exists),
                resolved_path=resolved_path,
            )

    def _embedding_row_for(self, pack_id: str) -> Optional[EmbeddingPackRow]:
        return self._embedding_pack_rows.get(pack_id) or self._cross_embedding_pack_rows.get(
            pack_id
        )

    def _populate_language_packs(self) -> None:
        self._language_pack_rows.clear()
        self.language_pack_table.setRowCount(len(self._language_packs))
        for row, pack in enumerate(self._language_packs):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            source_item = QTableWidgetItem(pack.display_source())
            status_item = QTableWidgetItem(t("language_packs.status.available"))
            download_button = self._resource_table_button(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_language_pack(pack_id)
            )
            local_button = self._resource_table_button(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_language_pack_path(pack_id)
            )
            delete_button = self._resource_table_button(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_language_pack(pack_id)
            )
            info_button = self._resource_table_info_button(
                pack, self._show_language_pack_source_license
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
            self.language_pack_table.setCellWidget(row, 8, info_button)

            self._language_pack_rows[pack.pack_id] = LanguagePackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
            )
        self._refresh_language_pack_table()

    def _populate_frequency_packs(self) -> None:
        self._frequency_pack_rows.clear()
        self.frequency_pack_table.setRowCount(len(self._frequency_packs))
        for row, pack in enumerate(self._frequency_packs):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            source_item = QTableWidgetItem(pack.display_source())
            status_item = QTableWidgetItem(t("language_packs.status.available"))
            download_button = self._resource_table_button(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_frequency_pack(pack_id)
            )
            local_button = self._resource_table_button(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_frequency_pack_path(
                    pack_id
                )
            )
            delete_button = self._resource_table_button(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_frequency_pack(pack_id)
            )
            info_button = self._resource_table_info_button(
                pack, self._show_frequency_pack_source_license
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
            self.frequency_pack_table.setCellWidget(row, 8, info_button)

            self._frequency_pack_rows[pack.pack_id] = FrequencyPackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
            )
        self._refresh_frequency_pack_table()

    def _populate_embedding_packs(self) -> None:
        self._embedding_pack_rows.clear()
        self.embedding_pack_table = ResourcePackTable()
        self.embedding_pack_table.setColumnCount(9)
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
                t("language_packs.headers.info"),
            ]
        )
        self.embedding_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.embedding_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.embedding_pack_table.setAlternatingRowColors(True)
        self.embedding_pack_table.verticalHeader().setVisible(False)
        self._configure_embedding_resource_table(self.embedding_pack_table)
        self.embedding_pack_table.setMinimumHeight(220)

        self.embedding_pack_table.setRowCount(len(self._embedding_packs))
        for row, pack in enumerate(self._embedding_packs):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            status_item = QTableWidgetItem(t("language_packs.status.available"))
            download_button = self._resource_table_button(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_embedding_pack(pack_id)
            )
            local_button = self._resource_table_button(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_embedding_pack_path(
                    pack_id
                )
            )
            use_button = self._resource_table_button(t("buttons.use_embedding"))
            use_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._activate_embedding_pack(pack_id)
            )
            delete_button = self._resource_table_button(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_embedding_pack(pack_id)
            )
            info_button = self._resource_table_info_button(
                pack, self._show_embedding_pack_source_license
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
            self.embedding_pack_table.setCellWidget(row, 8, info_button)

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
        self.cross_embedding_pack_table = ResourcePackTable()
        self.cross_embedding_pack_table.setColumnCount(9)
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
                t("language_packs.headers.info"),
            ]
        )
        self.cross_embedding_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cross_embedding_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cross_embedding_pack_table.setAlternatingRowColors(True)
        self.cross_embedding_pack_table.verticalHeader().setVisible(False)
        self._configure_embedding_resource_table(self.cross_embedding_pack_table)
        self.cross_embedding_pack_table.setMinimumHeight(200)

        self.cross_embedding_pack_table.setRowCount(len(self._cross_embedding_packs))
        for row, pack in enumerate(self._cross_embedding_packs):
            name_item = QTableWidgetItem(pack.display_name())
            language_item = QTableWidgetItem(pack.display_language())
            status_item = QTableWidgetItem("")
            download_button = self._resource_table_button(t("buttons.download"))
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_embedding_pack(pack_id)
            )
            local_button = self._resource_table_button(t("buttons.select"))
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_embedding_pack_path(
                    pack_id
                )
            )
            use_button = self._resource_table_button(t("buttons.use_embedding"))
            use_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._activate_embedding_pack(pack_id)
            )
            delete_button = self._resource_table_button(t("buttons.delete"))
            delete_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._delete_embedding_pack(pack_id)
            )
            info_button = self._resource_table_info_button(
                pack, self._show_embedding_pack_source_license
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
            self.cross_embedding_pack_table.setCellWidget(row, 8, info_button)

            self._cross_embedding_pack_rows[pack.pack_id] = EmbeddingPackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
                delete_button=delete_button,
                use_button=use_button,
            )

        self._refresh_cross_embedding_pack_table()
