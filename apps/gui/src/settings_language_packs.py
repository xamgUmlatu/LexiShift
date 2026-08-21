from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Mapping
import webbrowser

from PySide6.QtCore import QSettings, QStandardPaths, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from language_packs import (
    FrequencyPackDownloadThread,
    FrequencyPackInfo,
    LanguagePackDownloadThread,
    LanguagePackInfo,
    PackTransportOverride,
    PosOverlayPackDownloadThread,
    PosOverlayPackInfo,
    SemanticPackInfo,
    build_pack_catalogs,
)
from frequency_pack_import import import_frequency_source_file
from i18n import t
from localized_message_box import localized_question, prepare_message_box
from pack_source_manifest import load_pack_source_overrides
from settings_language_packs_layout_mixin import LanguagePackPanelLayoutMixin
from settings_language_packs_pair_setup_mixin import LanguagePackPanelPairSetupMixin
from settings_language_packs_path_mixin import LanguagePackPanelPathMixin
from settings_language_packs_panel_state_mixin import LanguagePackPanelStateMixin
from settings_language_packs_table_mixin import LanguagePackPanelTableMixin
from settings_language_packs_table_mixin import ResourcePackTable
from settings_language_packs_transfer_mixin import LanguagePackPanelTransferMixin
from settings_language_packs_support import (
    EmbeddingConversionThread,
    EmbeddingPackRow,
    FrequencyPackRow,
    LanguageResourceBinding,
    LanguagePackRow,
    SeedFrontierCachePrepareThread,
    embedding_pack_dir as _embedding_pack_dir,
    frequency_pack_dir as _frequency_pack_dir,
    has_frequency_table as _has_frequency_table,
    has_pos_overlay_table as _has_pos_overlay_table,
    is_pack_download_disabled,
    language_pack_dir as _language_pack_dir,
    lookup_dictionary_pack_dir as _lookup_dictionary_pack_dir,
    pack_download_disabled_tooltip,
    pos_overlay_pack_dir as _pos_overlay_pack_dir,
)
from settings_lookup_dictionaries_mixin import LanguagePackPanelLookupDictionariesMixin
from theme_manager import resolve_current_theme

_FREQUENCY_SOURCE_IMPORT_BUILD_MODES = frozenset(
    {
        "convert_archive",
        "spalex_frequency_pipeline",
    }
)
_MANUAL_SOURCE_IMPORT_DIR_SETTINGS_KEY = "resources/manual_source_import_dir"


class LanguagePackPanel(
    LanguagePackPanelLayoutMixin,
    LanguagePackPanelLookupDictionariesMixin,
    LanguagePackPanelPathMixin,
    LanguagePackPanelPairSetupMixin,
    LanguagePackPanelStateMixin,
    LanguagePackPanelTableMixin,
    LanguagePackPanelTransferMixin,
    QWidget,
):
    def __init__(
        self,
        parent=None,
        *,
        focused_pair: str | None = None,
        pack_source_overrides: Mapping[str, PackTransportOverride | Mapping[str, object]]
        | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = dict(resolve_current_theme(screen_id="settings_dialog"))
        self._set_focused_pair(focused_pair)
        self._language_pack_dir = _language_pack_dir()
        self._embedding_pack_dir = _embedding_pack_dir()
        self._frequency_pack_dir = _frequency_pack_dir()
        self._pos_overlay_pack_dir = _pos_overlay_pack_dir()
        self._lookup_dictionary_dir = _lookup_dictionary_pack_dir()
        self._initialize_lookup_dictionaries()
        self._uses_dynamic_pack_source_overrides = pack_source_overrides is None
        self._pack_source_overrides = (
            load_pack_source_overrides(refresh_remote=False)
            if self._uses_dynamic_pack_source_overrides
            else dict(pack_source_overrides or {})
        )
        self._set_pack_source_overrides(self._pack_source_overrides)
        self._language_pack_rows: dict[str, LanguagePackRow] = {}
        self._frequency_pack_rows: dict[str, FrequencyPackRow] = {}
        self._embedding_pack_rows: dict[str, EmbeddingPackRow] = {}
        self._cross_embedding_pack_rows: dict[str, EmbeddingPackRow] = {}
        self._language_pack_threads: list[LanguagePackDownloadThread] = []
        self._frequency_pack_threads: list[FrequencyPackDownloadThread] = []
        self._pos_overlay_pack_threads: list[PosOverlayPackDownloadThread] = []
        self._embedding_conversion_threads: list[EmbeddingConversionThread] = []
        self._seed_cache_prepare_threads: list[SeedFrontierCachePrepareThread] = []
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

        self.language_pack_table = ResourcePackTable()
        self.language_pack_table.setColumnCount(9)
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
                t("language_packs.headers.info"),
            ]
        )
        self.language_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.language_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.language_pack_table.setAlternatingRowColors(True)
        self.language_pack_table.verticalHeader().setVisible(False)
        self.language_pack_table.verticalHeader().setDefaultSectionSize(38)
        self.language_pack_table.verticalHeader().setMinimumSectionSize(34)
        self.language_pack_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._configure_language_resource_table(self.language_pack_table)
        self.language_pack_table.setMinimumHeight(460)

        self.frequency_pack_table = ResourcePackTable()
        self.frequency_pack_table.setColumnCount(9)
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
                t("language_packs.headers.info"),
            ]
        )
        self.frequency_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frequency_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.frequency_pack_table.setAlternatingRowColors(True)
        self.frequency_pack_table.verticalHeader().setVisible(False)
        self.frequency_pack_table.verticalHeader().setDefaultSectionSize(38)
        self.frequency_pack_table.verticalHeader().setMinimumSectionSize(34)
        self.frequency_pack_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._configure_language_resource_table(self.frequency_pack_table)
        self.frequency_pack_table.setMinimumHeight(380)

        self.language_pack_status = QLabel("")
        self.language_pack_status.setWordWrap(True)
        self.language_pack_status.setOpenExternalLinks(True)

        self._populate_language_packs()
        self._populate_frequency_packs()
        self._populate_embedding_packs()
        self._populate_cross_embedding_packs()

        layout = QVBoxLayout(self)
        title = QLabel(t("language_packs.title"))
        title.setProperty("resourcePanelTitle", True)
        layout.addWidget(title)

        self._resource_tabs = QTabWidget(self)
        self._resource_tabs.setObjectName("lexishiftResourceTabs")
        self._resource_tabs.addTab(
            self._build_learning_languages_tab(),
            t("language_packs.learning_pairs.tab_title"),
        )
        self._resource_tabs.addTab(
            self._build_lookup_dictionaries_tab(),
            t("language_packs.lookup_dictionaries.tab_title"),
        )
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._on_application_state_changed)
        layout.addWidget(self._resource_tabs)
        layout.addWidget(self.language_pack_status)
        self._apply_pair_resource_setup_style()
        self._refresh_pair_resource_setup_panel()

    def _on_application_state_changed(self, state) -> None:
        if state == Qt.ApplicationState.ApplicationActive:
            self._refresh_pair_resource_setup_panel()
            if hasattr(self, "_refresh_lookup_dictionary_download_candidate"):
                self._refresh_lookup_dictionary_download_candidate()

    def _set_pack_source_overrides(
        self,
        source_overrides: Mapping[str, PackTransportOverride | Mapping[str, object]] | None,
    ) -> None:
        catalogs = build_pack_catalogs(source_overrides=source_overrides)
        self._language_packs = catalogs.language_packs
        self._frequency_packs = catalogs.frequency_packs
        self._pos_overlay_packs = catalogs.pos_overlay_packs
        self._semantic_packs = catalogs.semantic_packs
        self._embedding_packs = catalogs.embedding_packs
        self._cross_embedding_packs = catalogs.cross_embedding_packs
        self._language_pack_info = {pack.pack_id: pack for pack in self._language_packs}
        self._frequency_pack_info = {pack.pack_id: pack for pack in self._frequency_packs}
        self._pos_overlay_pack_info = {pack.pack_id: pack for pack in self._pos_overlay_packs}
        self._semantic_pack_info: dict[str, SemanticPackInfo] = {
            pack.pack_id: pack for pack in self._semantic_packs
        }
        self._embedding_pack_info = {
            pack.pack_id: pack for pack in (*self._embedding_packs, *self._cross_embedding_packs)
        }

    def _pack_source_license_details(self, pack, resolved_path: str | None = None) -> str:
        not_recorded = t("language_packs.source_license.not_recorded")
        source_urls = [str(getattr(pack, "url", "") or "").strip()]
        source_urls.extend(str(url).strip() for url in getattr(pack, "source_urls", ()) or ())
        source_urls = [
            url for index, url in enumerate(source_urls) if url and url not in source_urls[:index]
        ]
        notes = tuple(str(note) for note in getattr(pack, "license_notes", ()) or () if str(note))
        rows = [
            (t("language_packs.source_license.pack"), pack.display_name()),
            (
                t("language_packs.source_license.pack_id"),
                getattr(pack, "pack_id", "") or not_recorded,
            ),
            (t("language_packs.source_license.source"), pack.display_source()),
            (
                t("language_packs.source_license.license"),
                getattr(pack, "license_name", "") or not_recorded,
            ),
            (
                t("language_packs.source_license.license_url"),
                getattr(pack, "license_url", "") or not_recorded,
            ),
            (
                t("language_packs.source_license.distribution_mode"),
                getattr(pack, "distribution_mode", "") or not_recorded,
            ),
            (
                t("language_packs.source_license.status"),
                getattr(pack, "license_status", "") or not_recorded,
            ),
            (
                t("language_packs.source_license.source_url"),
                "\n".join(source_urls) if source_urls else not_recorded,
            ),
            (
                t("language_packs.source_license.installed_path"),
                resolved_path or not_recorded,
            ),
        ]
        if notes:
            rows.append((t("language_packs.source_license.notes"), "\n".join(notes)))
        rows.append(
            (
                t("language_packs.source_license.notices"),
                "docs/language_pairs/THIRD_PARTY_DATA_NOTICES.md",
            )
        )
        return "\n".join(f"{label}: {value}" for label, value in rows)

    def _show_pack_source_license(self, pack, resolved_path: str | None = None) -> None:
        source_url = str(getattr(pack, "url", "") or "").strip()
        license_url = str(getattr(pack, "license_url", "") or "").strip()
        license_name = str(getattr(pack, "license_name", "") or "").strip()
        if not license_name:
            license_name = t("language_packs.source_license.not_recorded")

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle(t("language_packs.source_license.title"))
        dialog.setText(t("language_packs.source_license.summary", name=pack.display_name()))
        dialog.setInformativeText(
            t(
                "language_packs.source_license.informative",
                source=pack.display_source(),
                license=license_name,
            )
        )
        dialog.setDetailedText(self._pack_source_license_details(pack, resolved_path))
        source_button = None
        if source_url:
            source_button = dialog.addButton(
                t("language_packs.source_license.open_source"),
                QMessageBox.ButtonRole.ActionRole,
            )
        license_button = None
        if license_url:
            license_button = dialog.addButton(
                t("language_packs.source_license.open_license"),
                QMessageBox.ButtonRole.ActionRole,
            )
        dialog.addButton(QMessageBox.StandardButton.Close)
        prepare_message_box(dialog)
        dialog.exec()
        clicked = dialog.clickedButton()
        if source_button is not None and clicked == source_button:
            webbrowser.open(source_url)
            return
        if license_button is not None and clicked == license_button:
            webbrowser.open(license_url)

    def _show_language_pack_source_license(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        if pack is None:
            return
        resolved_path = self._language_resource_effective_path(
            pack_id
        ) or self._resolve_downloaded_path(pack)
        self._show_pack_source_license(pack, resolved_path)

    def _show_frequency_pack_source_license(self, pack_id: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        if pack is None:
            return
        resolved_path = self._frequency_pack_paths.get(
            pack_id
        ) or self._resolve_frequency_pack_path(pack)
        self._show_pack_source_license(pack, resolved_path)

    def _show_embedding_pack_source_license(self, pack_id: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        if pack is None:
            return
        resolved_path = self._embedding_pack_paths.get(pack_id) or self._resolve_downloaded_path(
            pack, embeddings=True
        )
        self._show_pack_source_license(pack, resolved_path)

    def _show_pos_overlay_pack_source_license(self, pack_id: str) -> None:
        pack = self._pos_overlay_pack_info.get(pack_id)
        if pack is None:
            return
        resolved_path = self._resolve_pos_overlay_pack_path(pack)
        self._show_pack_source_license(pack, resolved_path)

    def _refresh_pack_source_overrides_for_download(self) -> None:
        if not self._uses_dynamic_pack_source_overrides:
            return
        overrides = load_pack_source_overrides(refresh_remote=True)
        if overrides == self._pack_source_overrides:
            return
        self._pack_source_overrides = dict(overrides)
        self._set_pack_source_overrides(self._pack_source_overrides)
        self._refresh_language_pack_table()
        self._refresh_frequency_pack_table()
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

    def _download_language_pack(self, pack_id: str) -> None:
        self._refresh_pack_source_overrides_for_download()
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if is_pack_download_disabled(self._pack_source_overrides, pack_id, pack):
            message = pack_download_disabled_tooltip(self._pack_source_overrides, pack)
            self._refresh_language_pack_table()
            self._set_status_message(message, tone="error", tooltip=message)
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
        self._refresh_pack_source_overrides_for_download()
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if is_pack_download_disabled(self._pack_source_overrides, pack_id, pack):
            message = pack_download_disabled_tooltip(self._pack_source_overrides, pack)
            self._refresh_frequency_pack_table()
            self._set_status_message(message, tone="error", tooltip=message)
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

    def _download_pos_overlay_pack(self, pack_id: str) -> None:
        self._refresh_pack_source_overrides_for_download()
        pack = self._pos_overlay_pack_info.get(pack_id)
        if not pack:
            return
        if is_pack_download_disabled(self._pack_source_overrides, pack_id, pack):
            message = pack_download_disabled_tooltip(self._pack_source_overrides, pack)
            self._set_status_message(message, tone="error", tooltip=message)
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        source_dir = self._pos_overlay_source_dir(pack)
        sqlite_path = self._pos_overlay_sqlite_path(pack)
        self._set_status_message(
            t("language_packs.downloading", name=pack.display_name()), tone="info"
        )
        thread = PosOverlayPackDownloadThread(pack, source_dir, sqlite_path, self)
        thread.progress.connect(self._on_pos_overlay_pack_progress)
        thread.completed.connect(self._on_pos_overlay_pack_completed)
        thread.failed.connect(self._on_pos_overlay_pack_failed)
        thread.finished.connect(lambda: self._cleanup_pos_overlay_pack_thread(thread))
        self._pos_overlay_pack_threads.append(thread)
        thread.start()

    def _download_embedding_pack(self, pack_id: str) -> None:
        self._refresh_pack_source_overrides_for_download()
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        if is_pack_download_disabled(self._pack_source_overrides, pack_id, pack):
            message = pack_download_disabled_tooltip(self._pack_source_overrides, pack)
            if pack_id in self._cross_embedding_pack_rows:
                self._refresh_cross_embedding_pack_table()
            else:
                self._refresh_embedding_pack_table()
            self._set_status_message(message, tone="error", tooltip=message)
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
        self._prepare_seed_cache_for_pack(pack_id)

    def _select_frequency_pack_path(self, pack_id: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        if not pack:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.select_pack_file", name=pack.display_name()),
            self._frequency_pack_file_picker_start(pack),
            self._frequency_pack_file_filters(pack),
        )
        if not path:
            return
        self._remember_manual_source_import_dir(path)
        if self._supports_frequency_source_import(pack):
            if not self._is_sqlite_db(path):
                self._import_frequency_pack_source(pack, path)
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
        self._prepare_seed_cache_for_pack(pack_id)

    def _select_pos_overlay_pack_path(self, pack_id: str) -> None:
        pack = self._pos_overlay_pack_info.get(pack_id)
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
        valid, message = self._validate_pos_overlay_pack_path(pack, path)
        if not valid:
            QMessageBox.warning(self, t("dialogs.invalid_resource.title"), message)
            self._set_status_message(message, tone="error")
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        managed_path = self._pos_overlay_sqlite_path(pack)
        Path(managed_path).parent.mkdir(parents=True, exist_ok=True)
        if os.path.abspath(path) != os.path.abspath(managed_path):
            shutil.copy2(path, managed_path)
        self._set_status_message(
            t("language_packs.installed_linked", name=pack.display_name(), path=managed_path),
            tone="success",
        )
        self._prepare_seed_cache_for_pack(pack_id)
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

    def _supports_frequency_source_import(self, pack: FrequencyPackInfo) -> bool:
        build_mode = str(pack.build_mode or "").strip()
        if build_mode not in _FREQUENCY_SOURCE_IMPORT_BUILD_MODES:
            return False
        return bool(self._frequency_source_candidate_names(pack))

    def _frequency_pack_file_picker_start(self, pack: FrequencyPackInfo) -> str:
        if not self._supports_frequency_source_import(pack):
            return ""
        candidate = self._manual_frequency_source_candidate_path(pack)
        if candidate:
            return candidate
        search_dirs = self._manual_source_search_dirs()
        return str(search_dirs[0]) if search_dirs else ""

    def _frequency_pack_file_filters(self, pack: FrequencyPackInfo) -> str:
        if not self._supports_frequency_source_import(pack):
            return t("filters.all")
        patterns = self._frequency_source_file_patterns(pack)
        if not patterns:
            return t("filters.frequency_source")
        source_filter = f"{pack.display_name()} ({' '.join(patterns)})"
        return f"{source_filter};;{t('filters.frequency_source')}"

    def _frequency_source_file_patterns(self, pack: FrequencyPackInfo) -> tuple[str, ...]:
        patterns: list[str] = []
        for name in self._frequency_source_candidate_names(pack):
            for suffix in Path(name).suffixes:
                pattern = f"*{suffix}"
                if pattern not in patterns:
                    patterns.append(pattern)
        for pattern in ("*.db", "*.sqlite", "*.sqlite3"):
            if pattern not in patterns:
                patterns.append(pattern)
        return tuple(patterns)

    def _remember_manual_source_import_dir(self, source_path: str | Path) -> None:
        parent = Path(source_path).expanduser().parent
        if parent.is_dir():
            QSettings().setValue(_MANUAL_SOURCE_IMPORT_DIR_SETTINGS_KEY, str(parent))

    def _manual_source_search_dirs(self) -> tuple[Path, ...]:
        raw_dirs: list[str] = []
        remembered = QSettings().value(_MANUAL_SOURCE_IMPORT_DIR_SETTINGS_KEY, "")
        if remembered:
            raw_dirs.append(str(remembered))
        downloads = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        if downloads:
            raw_dirs.append(downloads)
        raw_dirs.append(str(Path.home() / "Downloads"))

        candidates: list[Path] = []
        seen: set[str] = set()
        for raw_dir in raw_dirs:
            path = Path(str(raw_dir or "")).expanduser()
            if not path.is_dir():
                continue
            normalized = str(path.resolve())
            if normalized in seen:
                continue
            seen.add(normalized)
            candidates.append(path)
        return tuple(candidates)

    def _frequency_source_candidate_names(self, pack: FrequencyPackInfo) -> tuple[str, ...]:
        names: list[str] = []
        for raw_name in (pack.filename, pack.source_filename):
            name = str(raw_name or "").strip()
            if name and name not in names:
                names.append(name)
        pack_filename = str(pack.filename or "").strip()
        if pack_filename.endswith(".gz"):
            unpacked_name = str(Path(pack_filename).with_suffix("").name).strip()
            if unpacked_name and unpacked_name not in names:
                names.append(unpacked_name)
        return tuple(names)

    def _manual_frequency_source_candidate_path(
        self,
        pack: FrequencyPackInfo,
        *,
        downloads_dir: str | None = None,
    ) -> str | None:
        if not self._supports_frequency_source_import(pack):
            return None
        roots = (
            (Path(downloads_dir).expanduser(),)
            if downloads_dir
            else self._manual_source_search_dirs()
        )
        for root in roots:
            if not root.is_dir():
                continue
            for name in self._frequency_source_candidate_names(pack):
                candidate = root / name
                if candidate.is_file():
                    return str(candidate)
        return None

    def _manual_pack_source_page_url(self, pack) -> str:
        if str(getattr(pack, "distribution_mode", "") or "").strip() == "manual-supply":
            license_url = str(getattr(pack, "license_url", "") or "").strip()
            if license_url:
                return license_url
        return str(getattr(pack, "url", "") or "").strip()

    def _import_frequency_pack_candidate(self, pack_id: str, source_path: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        if not pack or not source_path:
            return
        self._remember_manual_source_import_dir(source_path)
        if not self._supports_frequency_source_import(pack):
            self._select_frequency_pack_path(pack_id)
            return
        if self._is_sqlite_db(source_path):
            valid, message = self._validate_frequency_pack_path(pack, source_path)
            if not valid:
                QMessageBox.warning(self, t("dialogs.invalid_resource.title"), message)
                self._set_status_message(message, tone="error")
                self._clear_frequency_pack_entry(pack_id)
                self._refresh_frequency_pack_table()
                return
            if self._is_managed_frequency_pack_entry(pack_id, source_path):
                self._set_managed_frequency_pack_entry(pack_id)
            else:
                self._set_manual_frequency_pack_entry(pack_id, source_path)
            self._set_status_message(
                t(
                    "language_packs.installed_linked"
                    if self._is_installed_frequency_pack_entry(pack_id, source_path)
                    else "language_packs.manual_linked",
                    name=pack.display_name(),
                    path=source_path,
                ),
                tone="success",
            )
            self._refresh_frequency_pack_table()
            self._prepare_seed_cache_for_pack(pack_id)
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        self._import_frequency_pack_source(pack, source_path)

    def _import_frequency_pack_source(self, pack: FrequencyPackInfo, source_path: str) -> None:
        try:
            self._set_status_message(
                t("language_packs.importing_source", name=pack.display_name()),
                tone="info",
            )
            sqlite_path = import_frequency_source_file(
                pack,
                Path(source_path),
                frequency_pack_dir=self._frequency_pack_dir,
            )
        except Exception as exc:
            message = t(
                "language_packs.import_failed",
                name=pack.display_name(),
                message=str(exc),
            )
            QMessageBox.warning(self, t("dialogs.invalid_resource.title"), message)
            self._set_status_message(message, tone="error")
            self._clear_frequency_pack_entry(pack.pack_id)
            self._refresh_frequency_pack_table()
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        self._on_frequency_pack_completed(pack.pack_id, str(sqlite_path))
        self._set_status_message(
            t(
                "language_packs.imported_source",
                name=pack.display_name(),
                path=str(sqlite_path),
            ),
            tone="success",
        )

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
        valid, message = self._validate_embedding_pack_path(pack, path)
        if not valid:
            QMessageBox.warning(self, t("dialogs.invalid_resource.title"), message)
            self._set_status_message(message, tone="error")
            return
        if self._embedding_pack_pair_key(pack_id) and self._is_installed_embedding_pack_entry(
            pack_id, path
        ):
            self._embedding_pack_paths.pop(pack_id, None)
        else:
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

    def _clear_embedding_pack_entry(self, pack_id: str, *, local_path: str | None = None) -> None:
        self._embedding_pack_paths.pop(pack_id, None)
        pack = self._embedding_pack_info.get(pack_id)
        pair_key = str(getattr(pack, "pair_key", "") or "").strip()
        if not pair_key:
            return
        pack_ids = [value for value in self._embedding_pair_pack_ids.get(pair_key, []) if value]
        pack_ids = [value for value in pack_ids if value != pack_id]
        if pack_ids:
            self._embedding_pair_pack_ids[pair_key] = pack_ids
        else:
            self._embedding_pair_pack_ids.pop(pair_key, None)
        if local_path:
            paths = [
                path for path in self._embedding_pair_paths.get(pair_key, []) if path != local_path
            ]
            if paths:
                self._embedding_pair_paths[pair_key] = paths
            else:
                self._embedding_pair_paths.pop(pair_key, None)

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
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        if unlink_only:
            message = t("language_packs.unlink_confirm", name=pack.display_name())
        else:
            message = t("language_packs.delete_confirm", name=pack.display_name())
        reply = localized_question(
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
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

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
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        if unlink_only:
            message = t("language_packs.unlink_confirm", name=pack.display_name())
        else:
            message = t("language_packs.delete_confirm", name=pack.display_name())
        reply = localized_question(
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
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

    def _delete_pos_overlay_pack(self, pack_id: str) -> None:
        pack = self._pos_overlay_pack_info.get(pack_id)
        if not pack:
            return
        storage_dir = str(self._pos_overlay_pack_storage_dir(pack))
        sqlite_path = self._pos_overlay_sqlite_path(pack)
        resolved_path = self._resolve_pos_overlay_pack_path(pack)
        delete_paths = []
        if os.path.exists(storage_dir) and self._is_pos_overlay_pack_data_path(storage_dir):
            delete_paths.append(storage_dir)
        if (
            sqlite_path
            and os.path.exists(sqlite_path)
            and self._is_pos_overlay_pack_data_path(sqlite_path)
        ):
            delete_paths.append(sqlite_path)
        if (
            resolved_path
            and os.path.exists(resolved_path)
            and self._is_pos_overlay_pack_data_path(resolved_path)
        ):
            delete_paths.append(resolved_path)
        delete_paths = list(dict.fromkeys(delete_paths))
        if not delete_paths:
            QMessageBox.information(
                self,
                t("language_packs.title"),
                t("language_packs.no_local_files", name=pack.display_name()),
            )
            if hasattr(self, "_refresh_pair_resource_setup_panel"):
                self._refresh_pair_resource_setup_panel()
            return
        reply = localized_question(
            self,
            t("language_packs.delete_title"),
            t("language_packs.delete_confirm", name=pack.display_name()),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        for path in delete_paths:
            self._remove_path(path)
        self._set_status_message(t("language_packs.removed", name=pack.display_name()))
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

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
            self._clear_embedding_pack_entry(pack_id, local_path=local_path)
            self._refresh_embedding_pack_table()
            self._refresh_cross_embedding_pack_table()
            return
        if unlink_only:
            message = t("language_packs.unlink_confirm", name=pack.display_name())
        else:
            message = t("language_packs.delete_confirm", name=pack.display_name())
        reply = localized_question(
            self,
            t("language_packs.delete_title"),
            message,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        self._clear_embedding_pack_entry(pack_id, local_path=local_path)
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
        if not local_path:
            return
        optimized_path = self._embedding_sqlite_path(local_path)
        if optimized_path != local_path and self._is_sqlite_db(optimized_path):
            local_path = optimized_path
        if self._embedding_pack_pair_key(pack_id) and self._is_installed_embedding_pack_entry(
            pack_id, local_path
        ):
            self._embedding_pack_paths.pop(pack_id, None)
        else:
            self._embedding_pack_paths[pack_id] = local_path
        if pack and pack.pair_key:
            pair_key = pack.pair_key
            self._ensure_embedding_pair_pack_id(pack_id, pair_key=pair_key)
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

    def _validate_pos_overlay_pack_path(
        self,
        pack: PosOverlayPackInfo,
        path: str,
    ) -> tuple[bool, str]:
        if not os.path.isfile(path):
            return False, t("language_packs.validation.expected_file", name=pack.display_name())
        if not self._is_sqlite_db(path):
            return False, t("language_packs.validation.sqlite")
        if not _has_pos_overlay_table(path):
            return False, f"{t('language_packs.validation.sqlite')} (missing pos_overlay table)"
        return True, ""

    def _validate_embedding_pack_path(self, pack: LanguagePackInfo, path: str) -> tuple[bool, str]:
        if not os.path.isfile(path):
            return False, t("language_packs.validation.expected_file", name=pack.display_name())
        if self._is_sqlite_db(path):
            return True, ""
        if path.lower().endswith((".vec", ".txt", ".bin")):
            return True, ""
        return False, t("language_packs.validation.embedding_format", name=pack.display_name())
