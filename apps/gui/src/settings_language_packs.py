from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTabWidget,
    QTableWidget,
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
)
from i18n import t
from settings_language_packs_layout_mixin import LanguagePackPanelLayoutMixin
from settings_language_packs_path_mixin import LanguagePackPanelPathMixin
from settings_language_packs_panel_state_mixin import LanguagePackPanelStateMixin
from settings_language_packs_table_mixin import LanguagePackPanelTableMixin
from settings_language_packs_transfer_mixin import LanguagePackPanelTransferMixin
from settings_language_packs_support import (
    EmbeddingConversionThread,
    EmbeddingPackRow,
    FrequencyPackRow,
    LanguageResourceBinding,
    LanguagePackRow,
    embedding_pack_dir as _embedding_pack_dir,
    frequency_pack_dir as _frequency_pack_dir,
    has_frequency_table as _has_frequency_table,
    language_pack_dir as _language_pack_dir,
)
from theme_manager import resolve_current_theme
from lexishift_core.helper.installed_packs import write_installed_pack_manifest


class LanguagePackPanel(
    LanguagePackPanelLayoutMixin,
    LanguagePackPanelPathMixin,
    LanguagePackPanelStateMixin,
    LanguagePackPanelTableMixin,
    LanguagePackPanelTransferMixin,
    QWidget,
):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._theme = dict(resolve_current_theme(screen_id="settings_dialog"))
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
        self._embedding_conversion_threads: list[EmbeddingConversionThread] = []
        self._language_resource_bindings: dict[str, LanguageResourceBinding] = {}
        self._language_pack_paths: dict[str, str] = {}
        self._managed_language_pack_ids: set[str] = set()
        self._frequency_pack_paths: dict[str, str] = {}
        self._managed_frequency_pack_ids: set[str] = set()
        self._embedding_pack_paths: dict[str, str] = {}
        self._embedding_pair_pack_ids: dict[str, list[str]] = {}
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

        layout = QVBoxLayout(self)
        title = QLabel(t("language_packs.title"))
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(title)

        self._resource_tabs = QTabWidget(self)
        self._resource_tabs.addTab(self._build_language_pack_tab(), t("language_packs.title"))
        self._resource_tabs.addTab(
            self._build_frequency_pack_tab(), t("language_packs.frequency_title")
        )
        self._resource_tabs.addTab(
            self._build_embedding_pack_tab(), t("language_packs.embeddings_title")
        )
        self._resource_tabs.addTab(
            self._build_cross_embedding_pack_tab(),
            t("language_packs.cross_embeddings_title"),
        )
        layout.addWidget(self._resource_tabs)
        layout.addWidget(self.language_pack_status)

    def _download_language_pack(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        dest_path = self._download_archive_path(pack)
        row.status_item.setText(t("language_packs.status.downloading"))
        self._set_status_item_tone(row.status_item, "info")
        row.download_button.setEnabled(False)
        self._set_status_message(
            t("language_packs.downloading", name=pack.display_name()), tone="info"
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
        self._set_status_item_tone(row.status_item, "info")
        row.download_button.setEnabled(False)
        self._set_status_message(
            t("language_packs.downloading", name=pack.display_name()), tone="info"
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
        self._set_status_item_tone(row.status_item, "info")
        row.download_button.setEnabled(False)
        row.use_button.setEnabled(False)
        self._set_status_message(
            t("language_packs.downloading", name=pack.display_name()), tone="info"
        )
        thread = LanguagePackDownloadThread(
            pack,
            dest_path,
            self,
            pack_kind="embedding",
            write_manifest_on_complete=False,
        )
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
            self._set_status_message(message, tone="error")
            self._clear_language_pack_entry(pack_id)
            self._refresh_language_pack_table()
            return
        if self._is_managed_translation_pack_entry(pack_id, path):
            self._set_managed_language_pack_entry(pack_id, effective_path=path)
        else:
            self._set_manual_language_pack_entry(pack_id, path)
        self._set_status_message(
            t(
                "language_packs.installed_linked"
                if self._is_installed_language_pack_entry(pack_id, path)
                else "language_packs.manual_linked",
                name=pack.display_name(),
                path=path,
            ),
            tone="success",
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
            self._set_status_message(message, tone="error")
            self._clear_frequency_pack_entry(pack_id)
            self._refresh_frequency_pack_table()
            return
        if self._is_managed_frequency_pack_entry(pack_id, path):
            self._set_managed_frequency_pack_entry(pack_id)
        else:
            self._set_manual_frequency_pack_entry(pack_id, path)
        self._set_status_message(
            t(
                "language_packs.installed_linked"
                if self._is_installed_frequency_pack_entry(pack_id, path)
                else "language_packs.manual_linked",
                name=pack.display_name(),
                path=path,
            ),
            tone="success",
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
            QMessageBox.warning(
                self,
                t("dialogs.invalid_resource.title"),
                t("language_packs.validation.expected_file", name=pack.display_name()),
            )
            return
        self._embedding_pack_paths[pack_id] = path
        self._set_status_message(
            t(
                "language_packs.installed_linked"
                if self._is_installed_embedding_pack_entry(pack_id, path)
                else "language_packs.manual_linked",
                name=pack.display_name(),
                path=path,
            ),
            tone="success",
        )
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _delete_language_pack(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        local_path = self._language_resource_effective_path(pack_id)
        storage_dir = str(self._language_pack_storage_dir(pack))
        archive_path = self._download_archive_path(pack)
        resolved_path = self._resolve_downloaded_path(pack)
        delete_paths = []
        if os.path.isdir(storage_dir) and self._is_app_data_path(storage_dir):
            delete_paths.append(storage_dir)
        if local_path and self._is_app_data_path(local_path):
            delete_paths.append(local_path)
        if archive_path and os.path.exists(archive_path) and self._is_app_data_path(archive_path):
            delete_paths.append(archive_path)
        if (
            resolved_path
            and os.path.exists(resolved_path)
            and self._is_app_data_path(resolved_path)
        ):
            delete_paths.append(resolved_path)
        delete_paths = list(dict.fromkeys(delete_paths))
        unlink_only = local_path and not delete_paths
        if not delete_paths and not unlink_only:
            QMessageBox.information(
                self,
                t("language_packs.title"),
                t("language_packs.no_local_files", name=pack.display_name()),
            )
            self._clear_language_pack_entry(pack_id)
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
        self._clear_language_pack_entry(pack_id)
        for path in delete_paths:
            self._remove_path(path)
        self._set_status_message(t("language_packs.removed", name=pack.display_name()))
        self._refresh_language_pack_table()

    def _delete_frequency_pack(self, pack_id: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        local_path = self._frequency_pack_paths.get(pack_id)
        storage_dir = str(self._frequency_pack_storage_dir(pack))
        archive_path = self._frequency_archive_path(pack)
        sqlite_path = self._frequency_sqlite_path(pack)
        delete_paths = []
        if os.path.exists(storage_dir) and self._is_frequency_pack_data_path(storage_dir):
            delete_paths.append(storage_dir)
        if local_path and self._is_frequency_pack_data_path(local_path):
            delete_paths.append(local_path)
        if (
            archive_path
            and os.path.exists(archive_path)
            and self._is_frequency_pack_data_path(archive_path)
        ):
            delete_paths.append(archive_path)
        if (
            sqlite_path
            and os.path.exists(sqlite_path)
            and self._is_frequency_pack_data_path(sqlite_path)
        ):
            delete_paths.append(sqlite_path)
        delete_paths = list(dict.fromkeys(delete_paths))
        unlink_only = local_path and not delete_paths
        if not delete_paths and not unlink_only:
            QMessageBox.information(
                self,
                t("language_packs.frequency_title"),
                t("language_packs.no_local_files", name=pack.display_name()),
            )
            self._clear_frequency_pack_entry(pack_id)
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
        self._clear_frequency_pack_entry(pack_id)
        for path in delete_paths:
            self._remove_path(path)
        self._set_status_message(t("language_packs.removed", name=pack.display_name()))
        self._refresh_frequency_pack_table()

    def _delete_embedding_pack(self, pack_id: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        local_path = self._embedding_pack_paths.get(pack_id)
        storage_dir = str(self._embedding_pack_storage_dir(pack))
        local_optimized_path = self._embedding_sqlite_path(local_path) if local_path else None
        archive_path = self._download_archive_path(pack, embeddings=True)
        archive_optimized_path = self._embedding_sqlite_path(archive_path)
        resolved_path = self._resolve_downloaded_path(pack, embeddings=True)
        resolved_optimized_path = (
            self._embedding_sqlite_path(resolved_path) if resolved_path else None
        )
        delete_paths = []
        if os.path.exists(storage_dir) and self._is_app_data_path(storage_dir, embeddings=True):
            delete_paths.append(storage_dir)
        if local_path and self._is_app_data_path(local_path, embeddings=True):
            delete_paths.append(local_path)
        if local_optimized_path and local_optimized_path != local_path:
            if os.path.exists(local_optimized_path) and self._is_app_data_path(
                local_optimized_path, embeddings=True
            ):
                delete_paths.append(local_optimized_path)
        if (
            archive_path
            and os.path.exists(archive_path)
            and self._is_app_data_path(archive_path, embeddings=True)
        ):
            delete_paths.append(archive_path)
        if archive_optimized_path and archive_optimized_path != archive_path:
            if os.path.exists(archive_optimized_path) and self._is_app_data_path(
                archive_optimized_path, embeddings=True
            ):
                delete_paths.append(archive_optimized_path)
        if (
            resolved_path
            and os.path.exists(resolved_path)
            and self._is_app_data_path(resolved_path, embeddings=True)
        ):
            delete_paths.append(resolved_path)
        if resolved_optimized_path and resolved_optimized_path != resolved_path:
            if os.path.exists(resolved_optimized_path) and self._is_app_data_path(
                resolved_optimized_path, embeddings=True
            ):
                delete_paths.append(resolved_optimized_path)
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
        if pack.pair_key:
            pair_key = pack.pair_key
            pack_ids = [value for value in self._embedding_pair_pack_ids.get(pair_key, []) if value]
            pack_ids = [value for value in pack_ids if value != pack_id]
            if pack_ids:
                self._embedding_pair_pack_ids[pair_key] = pack_ids
            else:
                self._embedding_pair_pack_ids.pop(pair_key, None)
            if local_path:
                paths = [
                    path
                    for path in self._embedding_pair_paths.get(pair_key, [])
                    if path != local_path
                ]
                if paths:
                    self._embedding_pair_paths[pair_key] = paths
                else:
                    self._embedding_pair_paths.pop(pair_key, None)
        for path in delete_paths:
            self._remove_path(path)
        self._set_status_message(t("language_packs.removed", name=pack.display_name()))
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
        optimized_path = self._embedding_sqlite_path(local_path)
        if optimized_path != local_path and self._is_sqlite_db(optimized_path):
            local_path = optimized_path
            self._embedding_pack_paths[pack_id] = local_path
        if pack and pack.pair_key:
            pair_key = pack.pair_key
            pack_ids = list(self._embedding_pair_pack_ids.get(pair_key, []))
            if pack_id not in pack_ids:
                pack_ids.append(pack_id)
            self._embedding_pair_pack_ids[pair_key] = pack_ids
            self._embedding_pair_enabled[pair_key] = True
        # Per-pair activation now prefers pack ids for managed packs while keeping
        # path-based compatibility for older settings/manual imports.
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _validate_language_pack_path(self, pack: LanguagePackInfo, path: str) -> tuple[bool, str]:
        if pack.build_mode == "freedict_tei_to_sqlite":
            if os.path.isdir(path):
                missing = [
                    name
                    for name in pack.required_files
                    if not os.path.exists(os.path.join(path, name))
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
            lowered = path.lower()
            if self._is_sqlite_db(path):
                return True, ""
            if lowered.endswith((".tei", ".xml")):
                return True, ""
            return False, t("language_packs.validation.sqlite")
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
        if pack.sqlite_filename and not self._is_sqlite_db(path):
            return False, t("language_packs.validation.sqlite")
        if pack.pack_id == "jp-wordnet-sqlite":
            if not self._is_sqlite_db(path):
                return False, t("language_packs.validation.sqlite")
        return True, ""

    def _validate_frequency_pack_path(self, pack: FrequencyPackInfo, path: str) -> tuple[bool, str]:
        if not os.path.isfile(path):
            return False, t("language_packs.validation.expected_file", name=pack.display_name())
        if not self._is_sqlite_db(path):
            return False, t("language_packs.validation.sqlite")
        if not _has_frequency_table(path):
            return False, f"{t('language_packs.validation.sqlite')} (missing frequency table)"
        return True, ""

    def _auto_link_downloaded_packs(self) -> None:
        for pack_id, pack in self._language_pack_info.items():
            if self._language_resource_binding(pack_id):
                continue
            candidate = self._resolve_downloaded_path(pack)
            if not candidate:
                continue
            valid, _message = self._validate_language_pack_path(pack, candidate)
            if valid:
                if self._is_pack_id_first_translation_pack(pack):
                    self._set_managed_language_pack_entry(pack_id, effective_path=candidate)
                else:
                    self._set_manual_language_pack_entry(pack_id, candidate)

    def _auto_link_downloaded_frequency_packs(self) -> None:
        for pack_id, pack in self._frequency_pack_info.items():
            if pack_id in self._frequency_pack_paths or pack_id in self._managed_frequency_pack_ids:
                continue
            candidate = self._resolve_frequency_pack_path(pack)
            if not candidate:
                continue
            valid, _message = self._validate_frequency_pack_path(pack, candidate)
            if valid:
                self._set_managed_frequency_pack_entry(pack_id)

    def _auto_link_downloaded_embeddings(self) -> None:
        for pack_id, pack in self._embedding_pack_info.items():
            if pack_id in self._embedding_pack_paths:
                continue
            candidate = self._resolve_downloaded_path(pack, embeddings=True)
            if candidate:
                self._embedding_pack_paths[pack_id] = candidate

    def _on_language_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if pack.pack_id == "wordnet-en":
            dest_path = self._normalize_wordnet_path(dest_path)
        valid, message = self._validate_language_pack_path(pack, dest_path)
        if valid:
            if self._is_pack_id_first_translation_pack(pack):
                self._set_managed_language_pack_entry(pack_id, effective_path=dest_path)
            else:
                self._set_manual_language_pack_entry(pack_id, dest_path)
            row.status_item.setText(t("language_packs.status.installed"))
            self._set_status_item_tone(row.status_item, "success")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_linked", name=pack.display_name(), path=dest_path),
                tone="success",
            )
        else:
            self._clear_language_pack_entry(pack_id)
            row.status_item.setText(t("language_packs.status.invalid"))
            self._set_status_item_tone(row.status_item, "error")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_invalid", name=pack.display_name(), message=message),
                tone="error",
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
            self._set_managed_frequency_pack_entry(pack_id)
            row.status_item.setText(t("language_packs.status.installed"))
            self._set_status_item_tone(row.status_item, "success")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_linked", name=pack.display_name(), path=dest_path),
                tone="success",
            )
        else:
            self._clear_frequency_pack_entry(pack_id)
            row.status_item.setText(t("language_packs.status.invalid"))
            self._set_status_item_tone(row.status_item, "error")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_invalid", name=pack.display_name(), message=message),
                tone="error",
            )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        self._refresh_frequency_pack_table()

    def _on_embedding_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        if self._is_sqlite_db(dest_path):
            self._finalize_embedding_pack(pack_id=pack_id, resolved_path=dest_path)
            return
        optimized_path = self._embedding_pack_sqlite_path(pack)
        if self._is_sqlite_db(optimized_path):
            self._finalize_embedding_pack(pack_id=pack_id, resolved_path=optimized_path)
            return
        self._embedding_pack_paths[pack_id] = dest_path
        row.status_item.setText(t("language_packs.status.converting"))
        self._set_status_item_tone(row.status_item, "info")
        row.status_item.setToolTip(dest_path)
        row.download_button.setEnabled(False)
        row.use_button.setEnabled(False)
        self._set_status_message(
            t("language_packs.converting_for_optimized_use", name=pack.display_name()),
            tone="info",
        )
        thread = EmbeddingConversionThread(
            pack_id=pack_id,
            source_path=dest_path,
            output_path=optimized_path,
            parent=self,
        )
        thread.completed.connect(self._on_embedding_conversion_completed)
        thread.failed.connect(self._on_embedding_conversion_failed)
        thread.finished.connect(lambda: self._cleanup_embedding_conversion_thread(thread))
        self._embedding_conversion_threads.append(thread)
        thread.start()

    def _on_embedding_conversion_completed(self, pack_id: str, sqlite_path: str) -> None:
        self._finalize_embedding_pack(pack_id=pack_id, resolved_path=sqlite_path)

    def _on_embedding_conversion_failed(self, pack_id: str, message: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        self._embedding_pack_paths.pop(pack_id, None)
        row.status_item.setText(t("language_packs.status.failed"))
        self._set_status_item_tone(row.status_item, "error")
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        row.use_button.setEnabled(False)
        self._set_status_message(
            t(
                "language_packs.download_completed_but_conversion_failed",
                name=pack.display_name(),
                message=message,
            ),
            tone="error",
            tooltip=message,
        )
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _finalize_embedding_pack(self, *, pack_id: str, resolved_path: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        prior_path = self._embedding_pack_paths.get(pack_id)
        self._embedding_pack_paths[pack_id] = resolved_path
        if self._is_sqlite_db(resolved_path) and self._is_app_data_path(
            resolved_path, embeddings=True
        ):
            write_installed_pack_manifest(
                Path(self._embedding_pack_dir),
                pack_id=pack_id,
                pack_kind="embedding",
                provider=str(pack.source or "").strip().lower(),
                local_kind="file",
                build_mode="convert_to_sqlite",
                artifact_path=Path(resolved_path),
                source_filename=pack.filename,
                sqlite_filename=os.path.basename(resolved_path),
                raw_retained=False,
            )
            if (
                prior_path
                and prior_path != resolved_path
                and os.path.exists(prior_path)
                and self._is_app_data_path(prior_path, embeddings=True)
            ):
                self._remove_path(prior_path)
        row.status_item.setText(t("language_packs.status.installed"))
        self._set_status_item_tone(row.status_item, "success")
        row.status_item.setToolTip(resolved_path)
        self._set_status_message(
            t("language_packs.installed_linked", name=pack.display_name(), path=resolved_path),
            tone="success",
        )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        row.use_button.setEnabled(True)
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()
