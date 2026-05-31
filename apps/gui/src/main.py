from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
CORE_ROOT = os.path.join(REPO_ROOT, "core")
GUI_ROOT = os.path.join(REPO_ROOT, "apps", "gui", "src")
for path in (CORE_ROOT, GUI_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtCore import (
    QByteArray,
    QCoreApplication,
    QLocale,
    QSettings,
    QSortFilterProxyModel,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QWidget,
    QVBoxLayout,
)

from lexishift_core import (
    ImportExportSettings,
    SynonymSourceSettings,
    VocabDataset,
    VocabRule,
)

from dialogs import (
    RuleMetadataDialog,
    SettingsDialog,
    build_synonym_resource_settings_from_panel,
)
from helper_ui import auto_install_helper
from i18n import set_locale, t
from main_mixins import (
    MainWindowBulkRulesMixin,
    MainWindowImportExportMixin,
    MainWindowLocaleMixin,
    MainWindowMenuMixin,
    MainWindowProfilesMixin,
    MainWindowReplacementFilterMixin,
    MainWindowSrsMixin,
)
from main_runtime import (
    StartupLogger,
    acquire_singleton_server,
    bind_activation_handler,
    handle_startup_cli_flags,
    is_resource_settings_activation_message,
    startup_activation_message,
    install_exception_hook,
    prime_theme_assets,
    resource_pair_from_activation_message,
    run_helper_daemon_if_requested,
    singleton_socket_name,
)
from models import RulesTableModel
from main_paths import (
    _app_data_dir,
    _settings_path,
    _startup_log_paths,
)
from main_ui_components import (
    ThemedBackgroundWidget,
    UtilityDock,
    apply_theme_background,
    configure_log_handlers,
)
from rules_table_view import DeleteButtonDelegate, RulesTableView
from state import AppState
from theme_manager import build_base_styles, resolve_current_theme


class MainWindow(
    MainWindowReplacementFilterMixin,
    MainWindowSrsMixin,
    MainWindowBulkRulesMixin,
    MainWindowProfilesMixin,
    MainWindowLocaleMixin,
    MainWindowMenuMixin,
    MainWindowImportExportMixin,
    QMainWindow,
):
    def __init__(self) -> None:
        super().__init__()
        self._window_title_base = t("app.window_title")
        self.setWindowTitle(self._window_title_base)
        self._ui_settings = QSettings()
        self._theme = dict(resolve_current_theme(screen_id="main_window"))

        settings_path = _settings_path()
        self.state = AppState(settings_path=settings_path)
        self.state.load_settings()
        self._migrate_ruleset_paths()

        self.rules_model = RulesTableModel([])
        self.rules_model.rulesChanged.connect(self._on_rules_changed)
        self._rules_proxy = QSortFilterProxyModel(self)
        self._rules_proxy.setSourceModel(self.rules_model)
        self._rules_proxy.setSortRole(Qt.UserRole)
        self._rules_proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._rules_proxy.setDynamicSortFilter(True)

        self._profile_combo_updating = False
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        # Style only the popup list (not the closed combo) for main workspace selectors.
        self.profile_combo.view().setObjectName("profileRulesetPopup")
        self.manage_profiles_button = QPushButton(t("buttons.manage_profiles"))
        self.manage_profiles_button.clicked.connect(self._manage_profiles)
        self.manage_rulesets_button = QPushButton(t("buttons.manage_rulesets"))
        self.manage_rulesets_button.clicked.connect(self._manage_rulesets)
        self._ruleset_combo_updating = False
        self.ruleset_combo = QComboBox()
        self.ruleset_combo.currentIndexChanged.connect(self._on_ruleset_selected)
        # Reuse the same popup styling hook as profile selector for visual consistency.
        self.ruleset_combo.view().setObjectName("profileRulesetPopup")
        self.ruleset_combo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ruleset_combo.customContextMenuRequested.connect(self._ruleset_context_menu)
        self.open_ruleset_button = QPushButton(t("buttons.select_ruleset"))
        self.open_ruleset_button.clicked.connect(self._open_dataset)
        self.save_ruleset_button = QPushButton(t("buttons.save_ruleset"))
        self.save_ruleset_button.clicked.connect(self._save_dataset)
        self.save_ruleset_button.setEnabled(False)

        self.manage_profiles_button.setProperty("variant", "primary")
        self.manage_rulesets_button.setProperty("variant", "primary")
        self.open_ruleset_button.setProperty("variant", "secondary")
        self.save_ruleset_button.setProperty("variant", "primary")
        self.manage_profiles_button.setProperty("size", "large")
        self.manage_rulesets_button.setProperty("size", "large")
        self.open_ruleset_button.setProperty("size", "large")
        self.save_ruleset_button.setProperty("size", "large")

        self.rules_table = RulesTableView()
        self.rules_table.setModel(self._rules_proxy)
        self.rules_table.emptyGuideRequested.connect(self._open_setup_guide)
        self.rules_table.setSortingEnabled(True)
        self.rules_table.setMouseTracking(True)
        self._delete_button_delegate = DeleteButtonDelegate(self.rules_table)
        self.rules_table.setItemDelegateForColumn(
            RulesTableModel.COLUMN_DELETE,
            self._delete_button_delegate,
        )
        header = self.rules_table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(RulesTableModel.COLUMN_ENABLED, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(RulesTableModel.COLUMN_PRIORITY, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(RulesTableModel.COLUMN_CREATED, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(RulesTableModel.COLUMN_DELETE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(RulesTableModel.COLUMN_SOURCE, QHeaderView.Stretch)
        header.setSectionResizeMode(RulesTableModel.COLUMN_REPLACEMENT, QHeaderView.Stretch)
        header.setSectionResizeMode(RulesTableModel.COLUMN_TAGS, QHeaderView.Stretch)
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.clicked.connect(self._on_rule_table_clicked)

        self._replacement_thresholds: dict[str, float] = {}
        self._replacement_slider_updating = False
        self._embedding_indices: dict[str, object] = {}
        self._embedding_thread: Optional[object] = None
        self._embedding_loading = False
        self._embedding_load_error: Optional[str] = None
        self._embedding_loading_pair: Optional[str] = None
        self._embedding_load_id = 0
        self.replacement_list = QListWidget()
        self.replacement_list.currentItemChanged.connect(self._on_replacement_selected)
        self.replacement_selected_label = QLabel(t("replacement.select_hint"))
        self.replacement_threshold_slider = QSlider(Qt.Horizontal)
        self.replacement_threshold_slider.setRange(0, 100)
        self.replacement_threshold_slider.valueChanged.connect(
            self._on_replacement_threshold_changed
        )
        self.replacement_threshold_value = QLabel("0.00")
        self.replacement_hint_label = QLabel(t("replacement.enable_embeddings_hint"))
        self.replacement_hint_label.setWordWrap(True)
        self.embedding_progress = QProgressBar()
        self.embedding_progress.setRange(0, 0)
        self.embedding_progress.setTextVisible(True)
        self.embedding_progress.setFormat(t("replacement.loading_embeddings"))
        self.embedding_progress.hide()

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText(t("logs.placeholder"))
        self._configure_log_handlers()

        self._utility_dock = UtilityDock()
        logs_expanded = bool(
            self._ui_settings.value("main_window/utility/logs_expanded", False, type=bool)
        )
        self._utility_dock.add_panel(
            "logs",
            t("logs.title"),
            self.log_edit,
            expanded=logs_expanded,
        )
        self._utility_dock.panelToggled.connect(self._on_utility_panel_toggled)

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addWidget(self._build_profile_header())
        editor_layout.addWidget(self.rules_table)

        right_panel = QSplitter(Qt.Vertical)
        right_panel.addWidget(self._build_replacement_panel())
        right_panel.addWidget(self._utility_dock)
        right_panel.setStretchFactor(0, 1)
        right_panel.setStretchFactor(1, 0)
        self._right_splitter = right_panel

        splitter = QSplitter()
        splitter.addWidget(editor_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 1)
        self._splitter = splitter
        self._workspace_editor_page = splitter
        self._workspace_empty_page = self._build_empty_profiles_workspace()
        self._workspace_stack = QStackedWidget()
        self._workspace_stack.addWidget(self._workspace_editor_page)
        self._workspace_stack.addWidget(self._workspace_empty_page)

        self._theme_container = ThemedBackgroundWidget()
        container_layout = QVBoxLayout(self._theme_container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.addWidget(self._workspace_stack)
        self.setCentralWidget(self._theme_container)

        self._setup_actions()
        self._setup_menu()
        self._refresh_helper_menu_label()
        auto_install_helper(self._ui_settings)
        self._refresh_helper_menu_label()
        self._setup_rule_selection()
        self._refresh_embedding_index()
        self.state.datasetChanged.connect(self._on_dataset_loaded)
        self.state.dirtyChanged.connect(self._on_dirty_changed)
        self.state.profilesChanged.connect(self._on_profiles_changed)
        self.state.activeProfileChanged.connect(self._select_active_profile)

        self._load_active_profile()
        self._refresh_profiles_ui()
        self._restore_window_state()
        self._apply_theme()
        self._rebalance_right_splitter(keep_current=True)
        self._refresh_window_title()

    def _build_profile_header(self) -> QWidget:
        self.manage_profiles_button.setToolTip(t("dialogs.manage_profiles.title"))
        self.manage_rulesets_button.setToolTip(t("dialogs.manage_rulesets.title"))
        self.open_ruleset_button.setToolTip(t("menu.open_ruleset"))
        self.save_ruleset_button.setToolTip(t("menu.save_ruleset"))
        self.profile_combo.setMinimumWidth(240)
        self.ruleset_combo.setMinimumWidth(260)

        profile_card = QGroupBox(t("workspace.profile_card_title"))
        profile_card_layout = QVBoxLayout(profile_card)
        profile_card_layout.setContentsMargins(12, 12, 12, 12)
        profile_card_layout.setSpacing(6)
        profile_row = QHBoxLayout()
        profile_row.setContentsMargins(0, 0, 0, 0)
        profile_row.setSpacing(8)
        profile_row.addWidget(self.profile_combo, 1)
        profile_row.addWidget(self.manage_profiles_button)
        profile_card_layout.addLayout(profile_row)

        ruleset_card = QGroupBox(t("workspace.ruleset_card_title"))
        ruleset_card_layout = QVBoxLayout(ruleset_card)
        ruleset_card_layout.setContentsMargins(12, 12, 12, 12)
        ruleset_card_layout.setSpacing(6)
        ruleset_row = QHBoxLayout()
        ruleset_row.setContentsMargins(0, 0, 0, 0)
        ruleset_row.setSpacing(8)
        ruleset_row.addWidget(self.ruleset_combo, 1)
        ruleset_row.addWidget(self.open_ruleset_button)
        ruleset_row.addWidget(self.save_ruleset_button)
        ruleset_row.addWidget(self.manage_rulesets_button)
        ruleset_card_layout.addLayout(ruleset_row)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)
        top_row.addWidget(profile_card, 3)
        top_row.addWidget(ruleset_card, 4)

        header = QWidget()
        header.setLayout(top_row)
        return header

    def _build_empty_profiles_workspace(self) -> QWidget:
        self.empty_create_profile_button = QPushButton(t("empty_workspace.create_profile"))
        self.empty_import_profile_button = QPushButton(t("empty_workspace.import_profile"))
        for button in (self.empty_create_profile_button, self.empty_import_profile_button):
            button.setProperty("variant", "primary")
            button.setProperty("size", "large")
            button.setMinimumHeight(68)
            button.setMinimumWidth(360)

        self.empty_locale_icon_badge = QLabel(t("empty_workspace.locale_icon"))
        self.empty_locale_icon_badge.setProperty("ftueLocaleIconBadge", True)
        self.empty_locale_icon_badge.setAlignment(Qt.AlignCenter)
        self.empty_locale_icon_badge.setMinimumHeight(48)
        self.empty_locale_icon_badge.setFixedWidth(56)
        self.empty_locale_icon_badge.setToolTip(t("empty_workspace.locale_tooltip"))

        self.empty_locale_button = QPushButton()
        self.empty_locale_button.setProperty("ftueLocaleSelectButton", True)
        self.empty_locale_button.setMinimumHeight(48)
        self.empty_locale_button.setMinimumWidth(210)
        self.empty_locale_button.setToolTip(t("empty_workspace.locale_tooltip"))
        self.empty_locale_button.clicked.connect(self._show_empty_locale_menu)
        self._refresh_empty_locale_button_label()

        locale_picker_row = QHBoxLayout()
        locale_picker_row.setContentsMargins(0, 0, 0, 0)
        locale_picker_row.setSpacing(0)
        locale_picker_row.addWidget(self.empty_locale_icon_badge)
        locale_picker_row.addWidget(self.empty_locale_button)

        locale_picker = QWidget()
        locale_picker.setLayout(locale_picker_row)

        self.empty_create_profile_button.clicked.connect(self._on_empty_create_profile)
        self.empty_import_profile_button.clicked.connect(self._import_profiles_from_file)

        button_col = QVBoxLayout()
        button_col.setContentsMargins(0, 0, 0, 0)
        button_col.setSpacing(14)
        button_col.addWidget(self.empty_create_profile_button)
        button_col.addWidget(self.empty_import_profile_button)

        centered = QHBoxLayout()
        centered.setContentsMargins(0, 0, 0, 0)
        centered.addStretch(1)
        centered.addLayout(button_col)
        centered.addStretch(1)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addStretch(1)
        top_row.addWidget(locale_picker, 0, Qt.AlignRight | Qt.AlignTop)

        root = QVBoxLayout()
        root.setContentsMargins(24, 24, 24, 24)
        root.addLayout(top_row)
        root.addStretch(1)
        root.addLayout(centered)
        root.addStretch(1)

        page = QWidget()
        page.setLayout(root)
        return page

    def _build_replacement_panel(self) -> QWidget:
        title = QLabel(t("replacement.panel_title"))
        slider_label = QLabel(t("replacement.threshold_label"))

        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(0, 0, 0, 0)
        slider_row.addWidget(self.replacement_threshold_slider, 1)
        slider_row.addWidget(self.replacement_threshold_value)
        slider_widget = QWidget()
        slider_widget.setLayout(slider_row)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.replacement_list, 1)
        layout.addWidget(self.replacement_selected_label)
        layout.addWidget(slider_label)
        layout.addWidget(slider_widget)
        layout.addWidget(self.embedding_progress)
        layout.addWidget(self.replacement_hint_label)

        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _current_source_row(self, *, index=None) -> int:
        view_index = index or self.rules_table.currentIndex()
        if not view_index.isValid():
            return -1
        source_index = self._rules_proxy.mapToSource(view_index)
        return source_index.row()

    def _default_import_dir(self) -> str:
        settings = self.state.settings.import_export
        if settings and settings.last_import_path:
            return settings.last_import_path
        return str(_app_data_dir())

    def _default_export_dir(self) -> str:
        settings = self.state.settings.import_export
        if settings and settings.last_export_path:
            return settings.last_export_path
        return str(_app_data_dir())

    def _remember_import_path(self, path: Path) -> None:
        settings = self.state.settings
        import_settings = settings.import_export or ImportExportSettings()
        updated = replace(import_settings, last_import_path=str(path.parent))
        self.state.update_settings(replace(settings, import_export=updated))

    def _remember_export_path(self, path: Path) -> None:
        settings = self.state.settings
        import_settings = settings.import_export or ImportExportSettings()
        updated = replace(import_settings, last_export_path=str(path.parent))
        self.state.update_settings(replace(settings, import_export=updated))

    def _reveal_path(self, path: str) -> None:
        if not path:
            return
        target = os.path.abspath(os.path.expanduser(path))
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", target], check=False)
            return
        if sys.platform.startswith("win"):
            subprocess.run(["explorer", "/select,", target], check=False)
            return
        directory = target if os.path.isdir(target) else os.path.dirname(target)
        subprocess.run(["xdg-open", directory], check=False)

    def _restore_window_state(self) -> None:
        geometry = self._ui_settings.value("main_window/geometry", type=QByteArray)
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1100, 700)
        splitter_state = self._ui_settings.value("main_window/splitter", type=QByteArray)
        if splitter_state:
            self._splitter.restoreState(splitter_state)
        else:
            self._splitter.setSizes([320, 780])
        right_splitter_state = self._ui_settings.value(
            "main_window/right_splitter", type=QByteArray
        )
        if right_splitter_state:
            self._right_splitter.restoreState(right_splitter_state)
        else:
            self._right_splitter.setSizes([620, 180])
        self._rebalance_right_splitter(keep_current=True)

    def _theme_color_hex(self, key: str, *, fallback: str) -> str:
        value = self._theme.get(key)
        if isinstance(value, str) and value.strip():
            return value
        return fallback

    def _status_color(self, tone: str) -> QColor:
        mapping = {
            "error": self._theme_color_hex("status_error", fallback="#A03030"),
            "info": self._theme_color_hex("status_info", fallback="#2E6BD6"),
        }
        return QColor(mapping.get(tone, self._theme_color_hex("text", fallback="#1F1F1F")))

    def _configure_log_handlers(self) -> None:
        configure_log_handlers(
            error_handler=lambda message: self._append_log(
                message, color=self._status_color("error")
            ),
            info_handler=lambda message: self._append_log(
                message, color=self._status_color("info")
            ),
        )

    def _apply_theme(self) -> None:
        self._theme = resolve_current_theme(screen_id="main_window")
        apply_theme_background(self._theme_container, self._theme)
        self.setStyleSheet(build_base_styles(self._theme))
        self._splitter.setStyleSheet("background: transparent;")
        self._right_splitter.setStyleSheet("background: transparent;")
        self._utility_dock.refresh_geometry_hint()
        self.rules_table.set_empty_palette(
            card_bg=self._theme_color_hex("panel_top", fallback="#F5F2E9"),
            card_border=self._theme_color_hex("panel_border", fallback="#D5CBB8"),
            title=self._theme_color_hex("text", fallback="#2C2A24"),
            hint=self._theme_color_hex("muted", fallback="#6F6558"),
            accent=self._theme_color_hex("primary", fallback="#4A7DB8"),
        )
        base_delete = self._status_color("error")
        self._delete_button_delegate.set_colors(base_delete, base_delete.darker(115))
        self._configure_log_handlers()
        self._rebalance_right_splitter(keep_current=True)

    def _save_window_state(self) -> None:
        self._ui_settings.setValue("main_window/geometry", self.saveGeometry())
        self._ui_settings.setValue("main_window/splitter", self._splitter.saveState())
        self._ui_settings.setValue("main_window/right_splitter", self._right_splitter.saveState())

    def _refresh_window_title(self, dirty: Optional[bool] = None) -> None:
        is_dirty = self.state.dirty if dirty is None else bool(dirty)
        title = self._window_title_base
        if is_dirty:
            title = f"{title} *"
        self.setWindowTitle(title)

    def closeEvent(self, event) -> None:
        if self.state.dirty:
            choice = QMessageBox(self)
            choice.setIcon(QMessageBox.Warning)
            choice.setWindowTitle(t("dialogs.unsaved.title"))
            choice.setText(t("dialogs.unsaved.text"))
            choice.setInformativeText(t("dialogs.unsaved.informative"))
            choice.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            choice.setDefaultButton(QMessageBox.Save)
            save_button = choice.button(QMessageBox.Save)
            if save_button is not None:
                save_button.setText(t("buttons.save_ruleset"))
            discard_button = choice.button(QMessageBox.Discard)
            if discard_button is not None:
                discard_button.setText(t("buttons.discard"))
            cancel_button = choice.button(QMessageBox.Cancel)
            if cancel_button is not None:
                cancel_button.setText(t("buttons.cancel"))
            result = choice.exec()
            if result == QMessageBox.Save:
                self._save_dataset()
                if self.state.dirty:
                    event.ignore()
                    return
            elif result == QMessageBox.Cancel:
                event.ignore()
                return
        self._save_window_state()
        super().closeEvent(event)

    def _setup_rule_selection(self) -> None:
        self.rules_table.selectionModel().currentRowChanged.connect(
            lambda *_: self._update_rule_actions()
        )

    def _on_utility_panel_toggled(self, panel_id: str, expanded: bool) -> None:
        panel_key = str(panel_id or "").strip()
        if not panel_key:
            return
        self._ui_settings.setValue(f"main_window/utility/{panel_key}_expanded", bool(expanded))
        if expanded:
            self._utility_dock.clear_unread(panel_key)
        self._rebalance_right_splitter()

    def _rebalance_right_splitter(self, *, keep_current: bool = False) -> None:
        if not hasattr(self, "_right_splitter") or not hasattr(self, "_utility_dock"):
            return
        logs_expanded = self._utility_dock.is_panel_expanded("logs")
        if keep_current and logs_expanded:
            return
        if logs_expanded:
            self._right_splitter.setSizes([620, 240])
            return
        collapsed_height = max(56, self._utility_dock.minimumSizeHint().height())
        self._right_splitter.setSizes([760, collapsed_height])

    def _sync_resource_settings_from_dialog(self, dialog: SettingsDialog) -> None:
        panel = getattr(dialog, "language_pack_panel", None)
        if panel is None:
            return
        current_settings = self.state.settings
        current_synonyms = current_settings.synonyms or SynonymSourceSettings()
        updated_synonyms = build_synonym_resource_settings_from_panel(
            panel,
            base_synonyms=current_synonyms,
        )
        if updated_synonyms == current_synonyms:
            return
        self.state.update_settings(replace(current_settings, synonyms=updated_synonyms))

    def _open_settings(
        self,
        initial_tab: str | None = None,
        initial_resource_pair: str | None = None,
    ) -> None:
        dialog = SettingsDialog(
            app_settings=self.state.settings,
            dataset_settings=self.state.dataset.settings,
            initial_tab=initial_tab,
            initial_resource_pair=initial_resource_pair,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._sync_resource_settings_from_dialog(dialog)
            return
        self.state.update_settings(dialog.result_app_settings())
        dataset = replace(self.state.dataset, settings=dialog.result_dataset_settings())
        self.state.update_dataset(dataset)
        self._apply_import_export_settings()
        self._refresh_embedding_index()
        self._apply_theme()
        self._refresh_srs_growth()
        self._refresh_helper_menu_label()
        self._refresh_empty_locale_button_label()

    def _open_settings_resources(self, pair: str | None = None) -> None:
        self._open_settings(initial_tab="resources", initial_resource_pair=pair)

    def _add_rule(self) -> None:
        self.rules_model.add_rule(VocabRule(source_phrase="", replacement=""))
        row = self.rules_model.rowCount() - 1
        source_index = self.rules_model.index(row, self.rules_model.COLUMN_SOURCE)
        proxy_index = self._rules_proxy.mapFromSource(source_index)
        if proxy_index.isValid():
            self.rules_table.setCurrentIndex(proxy_index)
            self.rules_table.edit(proxy_index)

    def _delete_rule(self) -> None:
        row = self._current_source_row()
        if row < 0:
            return
        self._confirm_and_delete_rule(row=row)

    def _confirm_and_delete_rule(self, *, row: int, skip_confirm: bool = False) -> None:
        if row < 0:
            return
        if not skip_confirm:
            rule = self.rules_model.rule_at(row)
            if rule is None:
                return
            message = t(
                "dialogs.delete_rule.message",
                source=rule.source_phrase,
                replacement=rule.replacement,
            )
            reply = QMessageBox.question(
                self,
                t("dialogs.delete_rule.title"),
                message,
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if reply != QMessageBox.Yes:
                return
        self.rules_model.remove_rule(row)

    def _edit_rule_metadata(self) -> None:
        row = self._current_source_row()
        rule = self.rules_model.rule_at(row)
        if rule is None:
            return
        dialog = RuleMetadataDialog(rule, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated = replace(rule, metadata=dialog.metadata())
        self.rules_model.update_rule(row, updated)

    def _on_rule_table_clicked(self, index) -> None:
        if index.column() == self.rules_model.COLUMN_DELETE:
            row = self._current_source_row(index=index)
            if row >= 0:
                skip_confirm = bool(QApplication.keyboardModifiers() & Qt.AltModifier)
                self._confirm_and_delete_rule(row=row, skip_confirm=skip_confirm)

    def _on_dataset_loaded(self, dataset: VocabDataset) -> None:
        self.rules_model.set_rules(list(dataset.rules))
        self._refresh_ruleset_ui()
        self._refresh_replacement_list()

    def _on_rules_changed(self, rules) -> None:
        dataset = replace(self.state.dataset, rules=tuple(rules))
        self.state.update_dataset(dataset)
        self._refresh_replacement_list()

    def _on_dirty_changed(self, dirty: bool) -> None:
        self._save_action.setEnabled(dirty)
        self.save_ruleset_button.setEnabled(dirty)
        self._refresh_window_title(dirty)

    def _update_rule_actions(self) -> None:
        has_selection = self._current_source_row() >= 0
        self._delete_rule_action.setEnabled(has_selection)
        self._edit_metadata_action.setEnabled(has_selection)

    def _apply_import_export_settings(self) -> None:
        settings = self.state.settings.import_export
        if settings is None:
            self._export_code_action.setEnabled(True)
            self._export_profiles_code_action.setEnabled(True)
            return
        self._export_code_action.setEnabled(settings.allow_code_export)
        self._export_profiles_code_action.setEnabled(settings.allow_code_export)

    def _append_log(self, message: str, *, color: Optional[QColor] = None) -> None:
        if not message:
            return
        if hasattr(self, "_utility_dock") and not self._utility_dock.is_panel_expanded("logs"):
            self._utility_dock.increment_unread("logs")
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        effective_color = color or QColor(self._theme_color_hex("text", fallback="#1F1F1F"))
        fmt.setForeground(effective_color)
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")
        self.log_edit.setTextCursor(cursor)
        self.log_edit.ensureCursorVisible()


def main() -> None:
    # Ensure AppDataLocation is scoped to LexiShift before any logging.
    QCoreApplication.setOrganizationName("LexiShift")
    QCoreApplication.setApplicationName("LexiShift")
    startup_logs = _startup_log_paths()
    startup_logger = StartupLogger(startup_logs)

    print("[LexiShift] STARTUP MARKER")
    startup_logger.log("main() begin")
    if handle_startup_cli_flags(sys.argv, startup_logs):
        return
    if run_helper_daemon_if_requested(sys.argv):
        return

    install_exception_hook(_app_data_dir)
    startup_logger.log("exception hook installed")

    app = QApplication(sys.argv)
    startup_logger.log("QApplication created")

    # Singleton check: ensure only one GUI window runs
    activation_message = startup_activation_message(sys.argv)
    server = acquire_singleton_server(singleton_socket_name(), activation_message)
    if server is None:
        sys.exit(0)
    startup_logger.log("single-instance server ready")

    prime_theme_assets(startup_logger)
    ui_settings = QSettings()
    locale_pref = ui_settings.value("appearance/locale", "system")
    if locale_pref == "system":
        locale_pref = QLocale.system().name()
    set_locale(str(locale_pref))
    startup_logger.log("locale initialized")
    window = MainWindow()
    startup_logger.log("MainWindow constructed")

    bind_activation_handler(server, window)

    window.show()
    if is_resource_settings_activation_message(activation_message):
        resource_pair = resource_pair_from_activation_message(activation_message)
        QTimer.singleShot(0, lambda: window._open_settings_resources(pair=resource_pair))
    startup_logger.log("window shown")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
