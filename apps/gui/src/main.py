from __future__ import annotations

import os
import subprocess
import sys
import traceback
import time
from datetime import datetime
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
    QStandardPaths,
    QSize,
    QThread,
    Qt,
    Signal,
    QTimer,
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import QAction, QActionGroup, QColor, QPainter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QSlider,
    QSplitter,
    QStyledItemDelegate,
    QTableView,
    QTextEdit,
    QStyle,
    QWidget,
    QVBoxLayout,
)

from lexishift_core import (
    AppSettings,
    ImportExportSettings,
    Profile,
    PracticeGate,
    RuleMetadata,
    SeedSelectionConfig,
    SrsGrowthConfig,
    SrsSettings,
    SynonymSourceSettings,
    VocabDataset,
    VocabRule,
    export_app_settings_code,
    export_app_settings_json,
    export_dataset_code,
    export_dataset_json,
    import_app_settings_code,
    import_app_settings_json,
    import_dataset_code,
    import_dataset_json,
    build_seed_candidates,
    grow_srs_store,
    resolve_allowed_pairs,
    seed_to_selector_candidates,
    select_active_items,
    SynonymGenerator,
    SynonymOptions,
    SynonymSources,
)
from lexishift_core.synonyms import EmbeddingIndex

from dialogs import RuleMetadataDialog, SettingsDialog
from helper_installer import install_helper, is_helper_installed
from helper_ui import auto_install_helper, ensure_helper_autostart, get_helper_environment, prompt_for_helper_environment
from dialogs_code import BulkRulesDialog, CodeDialog
from dialogs_profiles import CreateProfileDialog, FirstRunDialog, ProfilesDialog
from i18n import set_locale, t
from models import RulesTableModel
from preview import PreviewController, ReplacementHighlighter
from state import AppState
from theme_assets import ensure_sample_images, ensure_sample_themes
from theme_loader import theme_dir
from theme_logger import set_log_handler
from helper_logger import set_helper_log_handler
from theme_manager import build_base_styles, resolve_current_theme
from theme_widgets import ThemedBackgroundWidget, apply_theme_background


class DeleteButtonDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        rect = option.rect.adjusted(6, 4, -6, -4)
        hover = option.state & QStyle.State_MouseOver
        color = QColor("#D64545") if not hover else QColor("#C73C3C")
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(Qt.white)
        painter.drawText(rect, Qt.AlignCenter, t("buttons.delete"))
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return size.expandedTo(QSize(64, size.height()))


class EmbeddingLoaderThread(QThread):
    loaded = Signal(str, object, str)

    def __init__(self, pair_key: str, paths: list[Path], *, lower_case: bool, parent=None) -> None:
        super().__init__(parent)
        self._pair_key = pair_key
        self._paths = paths
        self._lower_case = lower_case

    def run(self) -> None:
        try:
            index = EmbeddingIndex(self._paths, lower_case=self._lower_case)
        except Exception as exc:
            self.loaded.emit(self._pair_key, None, str(exc))
            return
        self.loaded.emit(self._pair_key, index, "")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(t("app.window_title"))
        self._ui_settings = QSettings()

        settings_path = _settings_path()
        self.state = AppState(settings_path=settings_path)
        first_run = not settings_path.exists()
        self.state.load_settings()
        self._migrate_ruleset_paths()
        if not self.state.settings.profiles:
            if not self._run_first_time_setup(first_run=first_run):
                self._seed_default_profile()

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
        self.manage_profiles_button = QPushButton(t("buttons.manage_profiles"))
        self.manage_profiles_button.clicked.connect(self._manage_profiles)
        self.save_profiles_button = QPushButton(t("buttons.save_profiles"))
        self.save_profiles_button.clicked.connect(self._save_profiles)
        self._ruleset_combo_updating = False
        self.ruleset_combo = QComboBox()
        self.ruleset_combo.currentIndexChanged.connect(self._on_ruleset_selected)
        self.ruleset_combo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ruleset_combo.customContextMenuRequested.connect(self._ruleset_context_menu)
        self.open_ruleset_button = QPushButton(t("buttons.select_ruleset"))
        self.open_ruleset_button.clicked.connect(self._open_dataset)
        self.save_ruleset_button = QPushButton(t("buttons.save_ruleset"))
        self.save_ruleset_button.clicked.connect(self._save_dataset)
        self.save_ruleset_button.setEnabled(False)

        self.rules_table = QTableView()
        self.rules_table.setModel(self._rules_proxy)
        self.rules_table.setSortingEnabled(True)
        self.rules_table.setMouseTracking(True)
        self.rules_table.setItemDelegateForColumn(
            RulesTableModel.COLUMN_DELETE,
            DeleteButtonDelegate(self.rules_table),
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
        self._embedding_indices: dict[str, EmbeddingIndex] = {}
        self._embedding_thread: Optional[EmbeddingLoaderThread] = None
        self._embedding_loading = False
        self._embedding_load_error: Optional[str] = None
        self._embedding_loading_pair: Optional[str] = None
        self._embedding_load_id = 0
        self.replacement_list = QListWidget()
        self.replacement_list.currentItemChanged.connect(self._on_replacement_selected)
        self.replacement_selected_label = QLabel(t("replacement.select_hint"))
        self.replacement_threshold_slider = QSlider(Qt.Horizontal)
        self.replacement_threshold_slider.setRange(0, 100)
        self.replacement_threshold_slider.valueChanged.connect(self._on_replacement_threshold_changed)
        self.replacement_threshold_value = QLabel("0.00")
        self.replacement_hint_label = QLabel(t("replacement.enable_embeddings_hint"))
        self.replacement_hint_label.setWordWrap(True)
        self.embedding_progress = QProgressBar()
        self.embedding_progress.setRange(0, 0)
        self.embedding_progress.setTextVisible(True)
        self.embedding_progress.setFormat(t("replacement.loading_embeddings"))
        self.embedding_progress.hide()

        self.input_edit = QPlainTextEdit()
        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setReadOnly(True)
        self.highlighter = ReplacementHighlighter(self.preview_edit.document())
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText(t("logs.placeholder"))
        set_log_handler(lambda message: self._append_log(message, color=QColor("#A03030")))
        set_helper_log_handler(lambda message: self._append_log(message, color=QColor("#2E6BD6")))

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addWidget(self._build_profile_header())
        editor_layout.addWidget(self.rules_table)

        preview_panel = QSplitter(Qt.Vertical)
        preview_panel.addWidget(self.input_edit)
        preview_panel.addWidget(self.preview_edit)
        preview_panel.addWidget(self._build_log_panel())
        preview_panel.setStretchFactor(1, 1)
        self._preview_splitter = preview_panel

        right_panel = QSplitter(Qt.Vertical)
        right_panel.addWidget(self._build_replacement_panel())
        right_panel.addWidget(preview_panel)
        right_panel.setStretchFactor(1, 1)
        self._right_splitter = right_panel

        splitter = QSplitter()
        splitter.addWidget(editor_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 1)
        self._splitter = splitter

        self._theme_container = ThemedBackgroundWidget()
        container_layout = QVBoxLayout(self._theme_container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.addWidget(splitter)
        self.setCentralWidget(self._theme_container)

        self._setup_actions()
        self._setup_menu()
        self._refresh_helper_menu_label()
        auto_install_helper(self._ui_settings)
        self._refresh_helper_menu_label()
        self._setup_preview()
        self._refresh_embedding_index()
        self.state.datasetChanged.connect(self._on_dataset_loaded)
        self.state.dirtyChanged.connect(self._on_dirty_changed)
        self.state.profilesChanged.connect(self._on_profiles_changed)
        self.state.activeProfileChanged.connect(self._select_active_profile)

        self._load_active_profile()
        self._refresh_profiles_ui()
        self._restore_window_state()
        self._apply_theme()

    def _setup_actions(self) -> None:
        self._open_action = QAction(t("menu.open_ruleset"), self)
        self._open_action.triggered.connect(self._open_dataset)

        self._save_action = QAction(t("menu.save_ruleset"), self)
        self._save_action.triggered.connect(self._save_dataset)

        self._save_as_action = QAction(t("menu.save_ruleset_as"), self)
        self._save_as_action.triggered.connect(self._save_dataset_as)

        self._settings_action = QAction(t("menu.settings"), self)
        self._settings_action.setMenuRole(QAction.PreferencesRole)
        self._settings_action.triggered.connect(self._open_settings)

        self._manage_profiles_action = QAction(t("menu.manage_profiles"), self)
        self._manage_profiles_action.triggered.connect(self._manage_profiles)

        self._save_profiles_action = QAction(t("menu.save_profiles"), self)
        self._save_profiles_action.triggered.connect(self._save_profiles)

        self._add_rule_action = QAction(t("menu.add_rule"), self)
        self._add_rule_action.triggered.connect(self._add_rule)

        self._bulk_add_action = QAction(t("menu.bulk_add"), self)
        self._bulk_add_action.triggered.connect(self._bulk_add_rules)

        self._delete_rule_action = QAction(t("menu.delete_rule"), self)
        self._delete_rule_action.triggered.connect(self._delete_rule)

        self._edit_metadata_action = QAction(t("menu.edit_metadata"), self)
        self._edit_metadata_action.triggered.connect(self._edit_rule_metadata)

        self._install_helper_action = QAction(t("menu.install_helper"), self)
        self._install_helper_action.setMenuRole(QAction.ApplicationSpecificRole)
        self._install_helper_action.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self._install_helper_action.triggered.connect(self._install_helper)

        self._startup_diagnostics_action = QAction(t("menu.startup_diagnostics"), self)
        self._startup_diagnostics_action.triggered.connect(self._show_startup_diagnostics)

        self._open_log_dir_action = QAction(t("menu.open_log_directory"), self)
        self._open_log_dir_action.triggered.connect(self._open_log_directory)

        self._export_json_action = QAction(t("menu.export_ruleset_json"), self)
        self._export_json_action.triggered.connect(self._export_json)

        self._export_code_action = QAction(t("menu.export_ruleset_code"), self)
        self._export_code_action.triggered.connect(self._export_code)

        self._export_profiles_json_action = QAction(t("menu.export_profiles_json"), self)
        self._export_profiles_json_action.triggered.connect(self._export_profiles_json)

        self._export_profiles_code_action = QAction(t("menu.export_profiles_code"), self)
        self._export_profiles_code_action.triggered.connect(self._export_profiles_code)

        self._import_json_action = QAction(t("menu.import_ruleset_json"), self)
        self._import_json_action.triggered.connect(self._import_json)

        self._import_code_action = QAction(t("menu.import_ruleset_code"), self)
        self._import_code_action.triggered.connect(self._import_code)

        self._import_profiles_json_action = QAction(t("menu.import_profiles_json"), self)
        self._import_profiles_json_action.triggered.connect(self._import_profiles_json)

        self._import_profiles_code_action = QAction(t("menu.import_profiles_code"), self)
        self._import_profiles_code_action.triggered.connect(self._import_profiles_code)

        self._save_action.setEnabled(False)
        self._update_rule_actions()
        self._apply_import_export_settings()

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        app_menu = menu_bar.addMenu(t("menu.app"))
        app_menu.addAction(self._install_helper_action)

        file_menu = menu_bar.addMenu(t("menu.file"))
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)

        import_menu = file_menu.addMenu(t("menu.import"))
        import_menu.addAction(self._import_json_action)
        import_menu.addAction(self._import_code_action)
        import_menu.addSeparator()
        import_menu.addAction(self._import_profiles_json_action)
        import_menu.addAction(self._import_profiles_code_action)

        export_menu = file_menu.addMenu(t("menu.export"))
        export_menu.addAction(self._export_json_action)
        export_menu.addAction(self._export_code_action)
        export_menu.addSeparator()
        export_menu.addAction(self._export_profiles_json_action)
        export_menu.addAction(self._export_profiles_code_action)

        file_menu.addSeparator()
        file_menu.addAction(self._settings_action)
        file_menu.addSeparator()

        self._quit_action = QAction(t("menu.quit"), self)
        self._quit_action.setMenuRole(QAction.QuitRole)
        self._quit_action.triggered.connect(self.close)
        file_menu.addAction(self._quit_action)

        profiles_menu = menu_bar.addMenu(t("menu.profiles"))
        profiles_menu.addAction(self._manage_profiles_action)
        profiles_menu.addAction(self._save_profiles_action)
        profiles_menu.addSeparator()

        self._profiles_menu = profiles_menu
        self._profiles_action_group = QActionGroup(self)
        self._profiles_action_group.setExclusive(True)
        self._profile_actions: list[QAction] = []
        self._rebuild_profiles_menu()

        edit_menu = menu_bar.addMenu(t("menu.edit"))
        edit_menu.addAction(self._add_rule_action)
        edit_menu.addAction(self._bulk_add_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._edit_metadata_action)
        edit_menu.addAction(self._delete_rule_action)

        debug_menu = menu_bar.addMenu(t("menu.debug"))
        debug_menu.addAction(self._startup_diagnostics_action)
        debug_menu.addAction(self._open_log_dir_action)

    def _refresh_helper_menu_label(self) -> None:
        env, extension_id = get_helper_environment(self._ui_settings)
        if env and extension_id and is_helper_installed(str(extension_id), browser=env.browser):
            self._install_helper_action.setText(t("menu.reinstall_helper"))
        else:
            self._install_helper_action.setText(t("menu.install_helper"))

    def _install_helper(self) -> None:
        choice = prompt_for_helper_environment(self, self._ui_settings)
        if not choice:
            return
        env, extension_id, host_path = choice
        result = install_helper(
            extension_id=str(extension_id).strip(),
            browser=env.browser,
            host_path=host_path,
        )
        if result.installed:
            try:
                ensure_helper_autostart()
                QMessageBox.information(
                    self,
                    t("dialogs.helper_install.title"),
                    t("dialogs.helper_install.success", path=str(result.manifest_path or "")),
                )
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(
                    self,
                    t("dialogs.helper_install.title"),
                    t("dialogs.helper_install.failed", message=str(exc)),
                )
        else:
            QMessageBox.warning(
                self,
                t("dialogs.helper_install.title"),
                t("dialogs.helper_install.failed", message=str(result.message)),
            )
        self._refresh_helper_menu_label()

    def _open_log_directory(self) -> None:
        reveal_path(str(_app_data_dir()))

    def _show_startup_diagnostics(self) -> None:
        log_paths = _startup_log_paths()
        helper_log = _app_data_dir() / "helper_install.log"
        helper_tray_log = _app_data_dir() / "helper_tray.log"
        info = [
            f"AppDataLocation: {_app_data_dir()}",
            f"Executable: {sys.executable}",
            f"Frozen: {getattr(sys, 'frozen', False)}",
            f"_MEIPASS: {getattr(sys, '_MEIPASS', None)}",
            f"Startup log paths:",
        ]
        for path in log_paths:
            info.append(f"  - {path} (exists={path.exists()})")
        info.append(f"Helper install log: {helper_log} (exists={helper_log.exists()})")
        info.append(f"Helper tray log: {helper_tray_log} (exists={helper_tray_log.exists()})")
        info.append("If logs are missing, try launching with: --diagnose-startup")
        QMessageBox.information(
            self,
            t("dialogs.startup_diagnostics.title"),
            "\n".join(info),
        )

    def _build_profile_header(self) -> QWidget:
        profile_label = QLabel(t("labels.profile"))
        ruleset_label = QLabel(t("labels.ruleset"))

        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(profile_label)
        left_layout.addWidget(self.profile_combo, 1)
        left_layout.addWidget(self.manage_profiles_button)
        left_layout.addWidget(self.save_profiles_button)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(ruleset_label)
        right_layout.addWidget(self.ruleset_combo, 1)
        right_layout.addWidget(self.open_ruleset_button)
        right_layout.addWidget(self.save_ruleset_button)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(left_widget, 1)
        header_layout.addStretch(1)
        header_layout.addWidget(right_widget, 2)

        header = QWidget()
        header.setLayout(header_layout)
        return header

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

    def _build_log_panel(self) -> QWidget:
        title = QLabel(t("logs.title"))
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(self.log_edit)
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
        right_splitter_state = self._ui_settings.value("main_window/right_splitter", type=QByteArray)
        if right_splitter_state:
            self._right_splitter.restoreState(right_splitter_state)
        else:
            self._right_splitter.setSizes([280, 420])
        preview_splitter_state = self._ui_settings.value("main_window/preview_splitter", type=QByteArray)
        if preview_splitter_state:
            self._preview_splitter.restoreState(preview_splitter_state)
        else:
            self._preview_splitter.setSizes([200, 300, 150])

    def _apply_theme(self) -> None:
        theme = resolve_current_theme(screen_id="main_window")
        apply_theme_background(self._theme_container, theme)
        self.setStyleSheet(build_base_styles(theme))
        self._splitter.setStyleSheet("background: transparent;")
        self._right_splitter.setStyleSheet("background: transparent;")
        self._preview_splitter.setStyleSheet("background: transparent;")

    def _save_window_state(self) -> None:
        self._ui_settings.setValue("main_window/geometry", self.saveGeometry())
        self._ui_settings.setValue("main_window/splitter", self._splitter.saveState())
        self._ui_settings.setValue("main_window/right_splitter", self._right_splitter.saveState())
        self._ui_settings.setValue("main_window/preview_splitter", self._preview_splitter.saveState())

    def closeEvent(self, event) -> None:
        if self.state.dirty:
            choice = QMessageBox(self)
            choice.setIcon(QMessageBox.Warning)
            choice.setWindowTitle(t("dialogs.unsaved.title"))
            choice.setText(t("dialogs.unsaved.text"))
            choice.setInformativeText(t("dialogs.unsaved.informative"))
            choice.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            choice.setDefaultButton(QMessageBox.Save)
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

    def _setup_preview(self) -> None:
        self._preview_controller = PreviewController()
        self._preview_controller.previewReady.connect(self._apply_preview)

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(300)
        self._preview_timer.timeout.connect(self._run_preview)

        self.input_edit.textChanged.connect(self._schedule_preview)
        self.rules_table.selectionModel().currentRowChanged.connect(lambda *_: self._update_rule_actions())

    def _load_active_profile(self) -> None:
        settings = self.state.settings
        active_id = settings.active_profile_id
        if not active_id and settings.profiles:
            active_id = settings.profiles[0].profile_id
        if not active_id:
            return
        for profile in settings.profiles:
            if profile.profile_id == active_id:
                self._load_profile(profile)
                break

    def _seed_default_profile(self) -> None:
        default_dataset = _default_dataset_path()
        dataset_path = str(default_dataset)
        profile = Profile(
            profile_id="default",
            name=t("profiles.default_name"),
            dataset_path=dataset_path,
            rulesets=(dataset_path,),
            active_ruleset=dataset_path,
        )
        settings = AppSettings(profiles=(profile,), active_profile_id="default")
        self.state.set_profiles(settings.profiles, active_profile_id=settings.active_profile_id)
        if not default_dataset.exists():
            self.state.update_dataset(VocabDataset())
            self.state.save_dataset(path=default_dataset)

    def _run_first_time_setup(self, *, first_run: bool) -> bool:
        if first_run:
            dialog = FirstRunDialog(parent=self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
        return self._create_profile()

    def _open_dataset(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.open_ruleset.title"),
            self._default_import_dir(),
            t("filters.json"),
        )
        if not path:
            return
        dataset_path = Path(path)
        self._set_active_ruleset_path(dataset_path)
        self.state.load_dataset(dataset_path)
        self._remember_import_path(dataset_path)

    def _manage_profiles(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = ProfilesDialog(
            profiles=self.state.settings.profiles,
            active_profile_id=self.state.settings.active_profile_id,
            default_dir=_rulesets_dir(),
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        profiles = dialog.result_profiles()
        active_profile_id = dialog.result_active_profile_id()
        self.state.set_profiles(profiles, active_profile_id=active_profile_id)
        self._load_active_profile()
        self._refresh_profiles_ui()

    def _create_profile(self) -> bool:
        if not self._confirm_discard_changes():
            return False
        dialog = CreateProfileDialog(default_dir=_rulesets_dir(), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        profile = dialog.profile()
        if any(existing.profile_id == profile.profile_id for existing in self.state.settings.profiles):
            QMessageBox.warning(self, t("dialogs.profile_id.title"), t("dialogs.profile_id.exists"))
            return False
        profiles = tuple(self.state.settings.profiles) + (profile,)
        self.state.set_profiles(profiles, active_profile_id=profile.profile_id)
        dataset_path = Path(profile.dataset_path)
        if not dataset_path.exists():
            self.state.update_dataset(VocabDataset())
            self.state.save_dataset(path=dataset_path)
        self._load_profile(profile)
        self._refresh_profiles_ui()
        return True

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            app_settings=self.state.settings,
            dataset_settings=self.state.dataset.settings,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.state.update_settings(dialog.result_app_settings())
        dataset = replace(self.state.dataset, settings=dialog.result_dataset_settings())
        self.state.update_dataset(dataset)
        self._apply_import_export_settings()
        self._refresh_embedding_index()
        self._schedule_preview()
        self._apply_theme()
        self._refresh_srs_growth()
        self._refresh_helper_menu_label()

    def _add_rule(self) -> None:
        self.rules_model.add_rule(VocabRule(source_phrase="", replacement=""))
        row = self.rules_model.rowCount() - 1
        source_index = self.rules_model.index(row, self.rules_model.COLUMN_SOURCE)
        proxy_index = self._rules_proxy.mapFromSource(source_index)
        if proxy_index.isValid():
            self.rules_table.setCurrentIndex(proxy_index)
            self.rules_table.edit(proxy_index)

    def _bulk_add_rules(self) -> None:
        default_pack_ids = self._default_bulk_pack_ids()
        dialog = BulkRulesDialog(default_pack_ids=default_pack_ids, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        targets = dialog.targets()
        if not targets:
            return
        selected_pack_ids = dialog.selected_pack_ids()
        if not selected_pack_ids:
            QMessageBox.information(
                self,
                t("dialogs.bulk_add.title"),
                t("dialogs.bulk_add.select_dictionary"),
            )
            return
        self._remember_bulk_pack_selection(selected_pack_ids)
        self._append_log(t("logs.bulk_add_targets", count=len(targets)))
        rules = self._generate_synonym_rules(targets, selected_pack_ids=selected_pack_ids)
        if not rules:
            QMessageBox.information(
                self,
                t("dialogs.bulk_add.title"),
                t("dialogs.bulk_add.no_synonyms"),
            )
            return
        self.rules_model.add_rules(rules)

    def _default_bulk_pack_ids(self) -> set[str]:
        settings = self.state.settings.synonyms
        pack_ids: set[str] = set()
        if not settings:
            return pack_ids
        if settings.wordnet_dir:
            pack_ids.add("wordnet-en")
        if settings.moby_path:
            pack_ids.add("moby-en")
        if settings.last_selected_pack_ids:
            return set(settings.last_selected_pack_ids)
        language_packs = settings.language_packs or {}
        if language_packs.get("odenet-de"):
            pack_ids.add("odenet-de")
        elif language_packs.get("openthesaurus-de"):
            pack_ids.add("openthesaurus-de")
        if language_packs.get("jp-wordnet-sqlite"):
            pack_ids.add("jp-wordnet-sqlite")
        elif language_packs.get("jp-wordnet"):
            pack_ids.add("jp-wordnet")
        for pack_id in ("jmdict-ja-en", "freedict-de-en", "freedict-en-de", "cc-cedict-zh-en"):
            if language_packs.get(pack_id):
                pack_ids.add(pack_id)
        return pack_ids

    def _remember_bulk_pack_selection(self, selected_pack_ids: set[str]) -> None:
        settings = self.state.settings.synonyms or SynonymSourceSettings()
        updated = replace(settings, last_selected_pack_ids=tuple(sorted(selected_pack_ids)))
        self.state.update_settings(replace(self.state.settings, synonyms=updated))

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

    def _generate_synonym_rules(
        self,
        targets: list[str],
        *,
        selected_pack_ids: set[str] | None = None,
    ) -> list[VocabRule]:
        settings = self.state.settings.synonyms
        selected_pack_ids = set(selected_pack_ids or [])
        language_packs = settings.language_packs if settings else {}
        if not settings:
            QMessageBox.warning(
                self,
                t("dialogs.synonym_expansion.title"),
                t("dialogs.synonym_expansion.configure_sources"),
            )
            return []
        packs_by_pair: dict[str, set[str]] = {}
        for pack_id in selected_pack_ids:
            pair_key = self._pair_for_pack(pack_id)
            if not pair_key:
                continue
            packs_by_pair.setdefault(pair_key, set()).add(pack_id)
        openthesaurus_path = language_packs.get("openthesaurus-de") if language_packs else None
        odenet_path = language_packs.get("odenet-de") if language_packs else None
        jp_wordnet_path = language_packs.get("jp-wordnet") if language_packs else None
        jp_wordnet_sqlite_path = (
            language_packs.get("jp-wordnet-sqlite") if language_packs else None
        )
        jmdict_path = language_packs.get("jmdict-ja-en") if language_packs else None
        freedict_de_en_path = language_packs.get("freedict-de-en") if language_packs else None
        freedict_en_de_path = language_packs.get("freedict-en-de") if language_packs else None
        cc_cedict_path = language_packs.get("cc-cedict-zh-en") if language_packs else None
        if cc_cedict_path and Path(cc_cedict_path).is_dir():
            candidate = Path(cc_cedict_path) / "cedict_ts.u8"
            cc_cedict_path = str(candidate) if candidate.exists() else cc_cedict_path
        if freedict_de_en_path and Path(freedict_de_en_path).is_dir():
            candidate = Path(freedict_de_en_path) / "deu-eng.tei"
            freedict_de_en_path = str(candidate) if candidate.exists() else freedict_de_en_path
        if freedict_en_de_path and Path(freedict_en_de_path).is_dir():
            candidate = Path(freedict_en_de_path) / "eng-deu.tei"
            freedict_en_de_path = str(candidate) if candidate.exists() else freedict_en_de_path
        rules: list[VocabRule] = []
        seen_sources: set[str] = set()
        duplicate_count = 0
        for pair_key, pack_ids in sorted(packs_by_pair.items()):
            use_wordnet = "wordnet-en" in pack_ids
            use_moby = "moby-en" in pack_ids
            use_openthesaurus = "openthesaurus-de" in pack_ids
            use_odenet = "odenet-de" in pack_ids
            use_jp_wordnet = "jp-wordnet" in pack_ids
            use_jp_wordnet_sqlite = "jp-wordnet-sqlite" in pack_ids
            use_jmdict = "jmdict-ja-en" in pack_ids
            use_freedict_de_en = "freedict-de-en" in pack_ids
            use_freedict_en_de = "freedict-en-de" in pack_ids
            use_cc_cedict = "cc-cedict-zh-en" in pack_ids

            if not any(
                [
                    use_wordnet and settings.wordnet_dir,
                    use_moby and settings.moby_path,
                    use_openthesaurus and openthesaurus_path,
                    use_odenet and odenet_path,
                    use_jp_wordnet and jp_wordnet_path,
                    use_jp_wordnet_sqlite and jp_wordnet_sqlite_path,
                    use_jmdict and jmdict_path,
                    use_freedict_de_en and freedict_de_en_path,
                    use_freedict_en_de and freedict_en_de_path,
                    use_cc_cedict and cc_cedict_path,
                ]
            ):
                continue

            missing_sources = []
            if use_wordnet and settings.wordnet_dir and not Path(settings.wordnet_dir).exists():
                missing_sources.append(t("sources.wordnet_dir"))
            if use_moby and settings.moby_path and not Path(settings.moby_path).exists():
                missing_sources.append(t("sources.moby_file"))
            if use_openthesaurus and openthesaurus_path and not Path(openthesaurus_path).exists():
                missing_sources.append(t("sources.openthesaurus_file"))
            if use_odenet and odenet_path and not Path(odenet_path).exists():
                missing_sources.append(t("sources.odenet_file"))
            if use_jp_wordnet and jp_wordnet_path and not Path(jp_wordnet_path).exists():
                missing_sources.append(t("sources.jp_wordnet_file"))
            if use_jp_wordnet_sqlite and jp_wordnet_sqlite_path and not Path(jp_wordnet_sqlite_path).exists():
                missing_sources.append(t("sources.jp_wordnet_sqlite_file"))
            if use_jmdict and jmdict_path and not Path(jmdict_path).exists():
                missing_sources.append(t("sources.jmdict_file"))
            if use_freedict_de_en and freedict_de_en_path and not Path(freedict_de_en_path).exists():
                missing_sources.append(t("sources.freedict_de_en_file"))
            if use_freedict_en_de and freedict_en_de_path and not Path(freedict_en_de_path).exists():
                missing_sources.append(t("sources.freedict_en_de_file"))
            if use_cc_cedict and cc_cedict_path and Path(cc_cedict_path).is_dir():
                missing_sources.append(t("sources.cc_cedict_file"))
            if use_cc_cedict and cc_cedict_path and not Path(cc_cedict_path).exists():
                missing_sources.append(t("sources.cc_cedict_file"))
            if missing_sources:
                QMessageBox.warning(
                    self,
                    t("dialogs.synonym_expansion.title"),
                    t("dialogs.synonym_expansion.missing_sources", sources=", ".join(missing_sources)),
                )
                return []

            selected_labels = []
            label_map = {
                "wordnet-en": t("packs.wordnet"),
                "moby-en": t("packs.moby"),
                "openthesaurus-de": t("packs.openthesaurus"),
                "odenet-de": t("packs.odenet"),
                "jp-wordnet": t("packs.jp_wordnet"),
                "jp-wordnet-sqlite": t("packs.jp_wordnet_sqlite"),
                "jmdict-ja-en": t("packs.jmdict"),
                "freedict-de-en": t("packs.freedict_de_en"),
                "freedict-en-de": t("packs.freedict_en_de"),
                "cc-cedict-zh-en": t("packs.cc_cedict"),
            }
            for pack_id in pack_ids:
                selected_labels.append(label_map.get(pack_id, pack_id))
            if selected_labels:
                self._append_log(
                    t("logs.dictionaries", dictionaries=", ".join(sorted(selected_labels)))
                )

            cc_cedict_file = (
                Path(cc_cedict_path)
                if use_cc_cedict and cc_cedict_path and Path(cc_cedict_path).is_file()
                else None
            )
            sources = SynonymSources(
                wordnet_dir=Path(settings.wordnet_dir) if use_wordnet and settings.wordnet_dir else None,
                moby_path=Path(settings.moby_path) if use_moby and settings.moby_path else None,
                openthesaurus_path=Path(openthesaurus_path) if use_openthesaurus and openthesaurus_path else None,
                odenet_path=Path(odenet_path) if use_odenet and odenet_path else None,
                jp_wordnet_path=Path(jp_wordnet_path) if use_jp_wordnet and jp_wordnet_path else None,
                jp_wordnet_sqlite_path=(
                    Path(jp_wordnet_sqlite_path)
                    if use_jp_wordnet_sqlite and jp_wordnet_sqlite_path
                    else None
                ),
                jmdict_path=Path(jmdict_path) if use_jmdict and jmdict_path else None,
                freedict_de_en_path=(
                    Path(freedict_de_en_path)
                    if use_freedict_de_en and freedict_de_en_path
                    else None
                ),
                freedict_en_de_path=(
                    Path(freedict_en_de_path)
                    if use_freedict_en_de and freedict_en_de_path
                    else None
                ),
                cc_cedict_path=cc_cedict_file,
            )
            embedding_paths = self._embedding_paths_for_pair(settings, pair_key)
            options = SynonymOptions(
                max_synonyms=settings.max_synonyms,
                include_phrases=settings.include_phrases,
                lower_case=settings.lower_case,
                require_consensus=settings.require_consensus,
                use_embeddings=settings.use_embeddings,
                embedding_paths=embedding_paths,
                embedding_pair=pair_key,
                embedding_threshold=settings.embedding_threshold,
                embedding_fallback=settings.embedding_fallback,
            )
            generator = SynonymGenerator(sources, options=options)
            self._log_source_stats(pack_ids, generator.stats())
            if generator.total_entries() == 0:
                stats = generator.stats()
                QMessageBox.information(
                    self,
                    t("dialogs.synonym_expansion.title"),
                    t(
                        "dialogs.synonym_expansion.no_entries",
                        wordnet=stats.get("wordnet", 0),
                        moby=stats.get("moby", 0),
                        openthesaurus=stats.get("openthesaurus", 0),
                        odenet=stats.get("odenet", 0),
                        jp_wordnet=stats.get("jp_wordnet", 0),
                        jmdict=stats.get("jmdict", 0),
                        cc_cedict=stats.get("cc_cedict", 0),
                        freedict_de_en=stats.get("freedict_de_en", 0),
                        freedict_en_de=stats.get("freedict_en_de", 0),
                    ),
                )
                continue

            for target in targets:
                synonyms, used_fallback = generator.synonyms_for_detail(target)
                if not synonyms:
                    self._append_log(
                        t("logs.no_synonyms_for", target=target),
                        color=QColor("#C73C3C"),
                    )
                    if settings and settings.use_embeddings and settings.embedding_fallback:
                        if not generator.has_embeddings():
                            self._append_log(t("logs.embeddings_not_loaded", target=target))
                        elif not generator.embeddings_support_neighbors():
                            self._append_log(
                                t("logs.embeddings_no_neighbors")
                            )
                        elif not generator.embeddings_has_vector(target):
                            self._append_log(t("logs.no_embedding_vector", target=target))
                        else:
                            self._append_log(t("logs.embeddings_zero_neighbors", target=target))
                else:
                    if used_fallback:
                        self._append_log(
                            t("logs.embeddings_fallback_count", target=target, count=len(synonyms))
                        )
                    else:
                        self._append_log(
                            t("logs.synonyms_found", target=target, count=len(synonyms))
                        )
                for synonym in synonyms:
                    if synonym in seen_sources:
                        duplicate_count += 1
                        tags = ("synonym", "conflict")
                        rules.append(
                            VocabRule(
                                source_phrase=synonym,
                                replacement=target,
                                enabled=False,
                                tags=tags,
                                metadata=RuleMetadata(language_pair=pair_key),
                            )
                        )
                        continue
                    seen_sources.add(synonym)
                    rules.append(
                        VocabRule(
                            source_phrase=synonym,
                            replacement=target,
                            tags=("synonym",),
                            metadata=RuleMetadata(language_pair=pair_key),
                        )
                    )
        if not rules and selected_pack_ids:
            QMessageBox.warning(
                self,
                t("dialogs.synonym_expansion.title"),
                t("dialogs.synonym_expansion.select_configured"),
            )
            return []
        if duplicate_count:
            message = t("dialogs.bulk_add.duplicates", count=duplicate_count)
            QMessageBox.information(self, t("dialogs.bulk_add.title"), message)
            self._append_log(message)
        return rules

    def _log_source_stats(self, selected_pack_ids: set[str], stats: dict[str, int]) -> None:
        if not selected_pack_ids:
            return
        settings = self.state.settings.synonyms or SynonymSourceSettings()
        language_packs = settings.language_packs or {}
        pack_to_stat = {
            "wordnet-en": "wordnet",
            "moby-en": "moby",
            "openthesaurus-de": "openthesaurus",
            "odenet-de": "odenet",
            "jp-wordnet": "jp_wordnet",
            "jp-wordnet-sqlite": "jp_wordnet",
            "jmdict-ja-en": "jmdict",
            "cc-cedict-zh-en": "cc_cedict",
            "freedict-de-en": "freedict_de_en",
            "freedict-en-de": "freedict_en_de",
        }
        pack_to_path = {
            "wordnet-en": settings.wordnet_dir,
            "moby-en": settings.moby_path,
            "openthesaurus-de": language_packs.get("openthesaurus-de"),
            "odenet-de": language_packs.get("odenet-de"),
            "jp-wordnet": language_packs.get("jp-wordnet"),
            "jp-wordnet-sqlite": language_packs.get("jp-wordnet-sqlite"),
            "jmdict-ja-en": language_packs.get("jmdict-ja-en"),
            "cc-cedict-zh-en": language_packs.get("cc-cedict-zh-en"),
            "freedict-de-en": language_packs.get("freedict-de-en"),
            "freedict-en-de": language_packs.get("freedict-en-de"),
        }
        label_map = {
            "wordnet-en": t("packs.wordnet"),
            "moby-en": t("packs.moby"),
            "openthesaurus-de": t("packs.openthesaurus"),
            "odenet-de": t("packs.odenet"),
            "jp-wordnet": t("packs.jp_wordnet"),
            "jp-wordnet-sqlite": t("packs.jp_wordnet_sqlite"),
            "jmdict-ja-en": t("packs.jmdict"),
            "cc-cedict-zh-en": t("packs.cc_cedict"),
            "freedict-de-en": t("packs.freedict_de_en"),
            "freedict-en-de": t("packs.freedict_en_de"),
        }
        for pack_id in sorted(selected_pack_ids):
            stat_key = pack_to_stat.get(pack_id)
            if not stat_key:
                continue
            count = stats.get(stat_key, 0)
            if count > 0:
                self._append_log(
                    t("logs.source_loaded", name=label_map.get(pack_id, pack_id), count=count)
                )
            else:
                path = pack_to_path.get(pack_id) or ""
                size = ""
                if path and Path(path).exists():
                    try:
                        size = str(Path(path).stat().st_size)
                    except OSError:
                        size = ""
                self._append_log(
                    t(
                        "logs.source_empty",
                        name=label_map.get(pack_id, pack_id),
                        path=path,
                        size=size,
                    ),
                    color=QColor("#C73C3C"),
                )
                if pack_id == "odenet-de" and path:
                    probe = self._probe_odenet(path)
                    if probe:
                        self._append_log(
                            t(
                                "logs.odenet_probe",
                                entries=probe.get("entries", 0),
                                lemmas=probe.get("lemmas", 0),
                                senses=probe.get("senses", 0),
                            ),
                            color=QColor("#C73C3C"),
                        )
                        if probe.get("parse_error"):
                            self._append_log(
                                t("logs.odenet_parse_error", error=probe.get("parse_error")),
                                color=QColor("#C73C3C"),
                            )

    def _probe_odenet(self, path: str) -> dict[str, int]:
        from xml.etree import ElementTree

        try:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return {}
        data: dict[str, int | str] = {
            "entries": text.count("LexicalEntry"),
            "lemmas": text.count("Lemma"),
            "senses": text.count("Sense"),
        }
        try:
            for _event, _elem in ElementTree.iterparse(path, events=("end",)):
                pass
        except ElementTree.ParseError as exc:
            data["parse_error"] = str(exc)
        return data

    def _save_dataset(self) -> None:
        if self.state.dataset_path is None:
            self._save_dataset_as()
            return
        self.state.save_dataset()

    def _save_dataset_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.save_ruleset_as.title"),
            self._default_export_dir(),
            t("filters.json"),
        )
        if not path:
            return
        dataset_path = Path(path)
        self.state.save_dataset(path=dataset_path)
        self._set_active_ruleset_path(dataset_path)
        self._remember_export_path(dataset_path)

    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.export_ruleset_json.title"),
            self._default_export_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = export_dataset_json(self.state.dataset)
        Path(path).write_text(payload, encoding="utf-8")
        self._remember_export_path(Path(path))

    def _export_code(self) -> None:
        payload = export_dataset_code(self.state.dataset)
        dialog = CodeDialog(t("dialogs.export_ruleset_code.title"), code=payload, read_only=True, parent=self)
        dialog.exec()

    def _export_profiles_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.export_profiles_json.title"),
            self._default_export_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = export_app_settings_json(self.state.settings)
        Path(path).write_text(payload, encoding="utf-8")
        self._remember_export_path(Path(path))

    def _export_profiles_code(self) -> None:
        payload = export_app_settings_code(self.state.settings)
        dialog = CodeDialog(t("dialogs.export_profiles_code.title"), code=payload, read_only=True, parent=self)
        dialog.exec()

    def _import_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.import_ruleset_json.title"),
            self._default_import_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        dataset = import_dataset_json(payload)
        self.state.update_dataset(dataset)
        self._remember_import_path(Path(path))

    def _import_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog(t("dialogs.import_ruleset_code.title"), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        dataset = import_dataset_code(dialog.code())
        self.state.update_dataset(dataset)

    def _import_profiles_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.import_profiles_json.title"),
            self._default_import_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        settings = import_app_settings_json(payload)
        self.state.update_settings(settings)
        self._refresh_embedding_index()
        self._load_active_profile()
        self._remember_import_path(Path(path))

    def _import_profiles_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog(t("dialogs.import_profiles_code.title"), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        settings = import_app_settings_code(dialog.code())
        self.state.update_settings(settings)
        self._refresh_embedding_index()
        self._load_active_profile()

    def _confirm_discard_changes(self) -> bool:
        if not self.state.dirty:
            return True
        reply = QMessageBox.question(
            self,
            t("dialogs.unsaved.title"),
            t("dialogs.unsaved.discard"),
            QMessageBox.Yes | QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _load_profile(self, profile: Profile) -> None:
        dataset_path = Path(self._active_ruleset_path(profile))
        self.state.load_dataset(dataset_path)
        settings = self.state.settings
        if settings.active_profile_id != profile.profile_id:
            self.state.set_profiles(settings.profiles, active_profile_id=profile.profile_id)

    def _active_ruleset_path(self, profile: Profile) -> str:
        if profile.active_ruleset:
            return profile.active_ruleset
        if profile.rulesets:
            return profile.rulesets[0]
        if profile.dataset_path:
            return profile.dataset_path
        return str(_default_dataset_path())

    def _activate_ruleset_for_profile(self, profile: Profile, path: Path) -> None:
        self._set_active_ruleset_path(path)
        self.state.load_dataset(path)

    def _set_active_ruleset_path(self, dataset_path: Path) -> None:
        settings = self.state.settings
        active_id = settings.active_profile_id
        if not active_id:
            return
        updated_profiles = []
        updated = False
        for profile in settings.profiles:
            if profile.profile_id == active_id:
                rulesets = list(profile.rulesets)
                path_str = str(dataset_path)
                if path_str not in rulesets:
                    rulesets.append(path_str)
                updated_profiles.append(
                    replace(
                        profile,
                        dataset_path=path_str,
                        rulesets=tuple(rulesets),
                        active_ruleset=path_str,
                    )
                )
                updated = True
            else:
                updated_profiles.append(profile)
        if updated:
            self.state.set_profiles(tuple(updated_profiles), active_profile_id=active_id)

    def _on_profile_selected(self, index: int) -> None:
        if self._profile_combo_updating:
            return
        profile = self.profile_combo.itemData(index)
        if profile is None:
            return
        if not self._confirm_discard_changes():
            self._refresh_profiles_ui()
            return
        self._load_profile(profile)

    def _on_ruleset_selected(self, index: int) -> None:
        if self._ruleset_combo_updating:
            return
        profile = self._current_profile()
        if profile is None:
            return
        path = self.ruleset_combo.itemData(index)
        if not path:
            return
        if not self._confirm_discard_changes():
            self._refresh_ruleset_ui()
            return
        self._activate_ruleset_for_profile(profile, Path(path))

    def _ruleset_context_menu(self, position) -> None:
        path = self.ruleset_combo.currentData()
        if not path:
            return
        menu = QMenu(self)
        reveal_action = menu.addAction(t("menu.reveal_in_finder"))
        action = menu.exec(self.ruleset_combo.mapToGlobal(position))
        if action == reveal_action:
            self._reveal_path(path)

    def _on_dataset_loaded(self, dataset: VocabDataset) -> None:
        self.rules_model.set_rules(list(dataset.rules))
        self._schedule_preview()
        self._refresh_ruleset_ui()
        self._refresh_replacement_list()

    def _on_rules_changed(self, rules) -> None:
        dataset = replace(self.state.dataset, rules=tuple(rules))
        self.state.update_dataset(dataset)
        self._schedule_preview()
        self._refresh_replacement_list()

    def _on_dirty_changed(self, dirty: bool) -> None:
        self._save_action.setEnabled(dirty)
        self.save_ruleset_button.setEnabled(dirty)

    def _on_profiles_changed(self, profiles) -> None:
        self._refresh_profiles_ui()
        self._rebuild_profiles_menu()

    def _schedule_preview(self) -> None:
        self._preview_timer.start()

    def _build_practice_gate(self) -> Optional[PracticeGate]:
        settings = self.state.settings.srs
        if not settings or not settings.enabled:
            return None
        active_items = self._select_active_srs_items(settings)
        return PracticeGate(
            active_items=active_items,
            include_unpaired_rules=True,
            include_all_if_empty=True,
        )

    def _select_active_srs_items(self, settings: SrsSettings):
        allowed_pairs = self._allowed_srs_pairs(settings)
        return select_active_items(
            self.state.srs_store.items,
            max_active=settings.max_active_items,
            allowed_pairs=allowed_pairs,
        )

    def _allowed_srs_pairs(self, settings: SrsSettings) -> Optional[list[str]]:
        if not settings.pair_rules:
            return None
        allowed = [pair for pair, rule in settings.pair_rules.items() if rule.enabled]
        return allowed or None

    def _run_preview(self) -> None:
        practice_gate = self._build_practice_gate()
        self._preview_controller.request(
            self.state.dataset,
            self.input_edit.toPlainText(),
            practice_gate=practice_gate,
        )

    def _apply_preview(self, output: str, spans) -> None:
        self.preview_edit.setPlainText(output)
        self.highlighter.set_spans(spans)

    def _select_active_profile(self, *_args) -> None:
        self._refresh_profiles_ui()
        self._rebuild_profiles_menu()

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

    def _save_profiles(self) -> None:
        self.state.save_settings()

    def _refresh_srs_growth(self) -> None:
        settings = self.state.settings.srs
        if not settings or not settings.enabled:
            return
        synonym_settings = self.state.settings.synonyms
        if not synonym_settings:
            return
        language_packs = synonym_settings.language_packs or {}
        frequency_packs = synonym_settings.frequency_packs or {}

        bccwj_path = frequency_packs.get("freq-ja-bccwj")
        jmdict_path = language_packs.get("jmdict-ja-en")
        if not bccwj_path or not jmdict_path:
            self._append_log(t("logs.srs_seed_missing"))
            return
        try:
            seed_config = SeedSelectionConfig(
                language_pair="en-ja",
                top_n=2000,
                jmdict_path=Path(jmdict_path),
                require_jmdict=True,
            )
            seeds = build_seed_candidates(frequency_db=Path(bccwj_path), config=seed_config)
            candidates = seed_to_selector_candidates(seeds)
            growth_config = SrsGrowthConfig(
                coverage_scalar=settings.coverage_scalar,
                max_new_items=settings.max_new_items_per_day,
            )
            updated_store, plan = grow_srs_store(
                candidates,
                store=self.state.srs_store,
                settings=settings,
                config=growth_config,
                allowed_pairs=resolve_allowed_pairs(settings),
            )
            if plan.add_count > 0:
                self.state.update_srs_store(updated_store)
                self._append_log(
                    t(
                        "logs.srs_seed_updated",
                        added=plan.add_count,
                        total=len(updated_store.items),
                        pool=plan.pool_size,
                    )
                )
            else:
                self._append_log(
                    t(
                        "logs.srs_seed_noop",
                        total=len(updated_store.items),
                        pool=plan.pool_size,
                    )
                )
        except Exception as exc:
            self._append_log(t("logs.srs_seed_failed", error=str(exc)))

    def _refresh_embedding_index(self) -> None:
        self._embedding_indices.clear()
        self._embedding_load_error = None
        self._embedding_loading = False
        self._embedding_loading_pair = None
        self._update_replacement_filter_state()
        self._ensure_embedding_loaded_for_selection()

    def _ensure_embedding_loaded_for_selection(self) -> None:
        pair_key = self._embedding_pair_for_replacement(self._selected_replacement())
        if not pair_key:
            self._update_replacement_filter_state()
            return
        self._ensure_embedding_loaded(pair_key)

    def _ensure_embedding_loaded(self, pair_key: str) -> None:
        if pair_key in self._embedding_indices:
            self._update_replacement_filter_state()
            return
        settings = self.state.settings.synonyms
        paths = self._embedding_paths_for_pair(settings, pair_key)
        if not settings or not settings.use_embeddings or not paths:
            self._embedding_load_error = t("replacement.embeddings_missing")
            self._update_replacement_filter_state()
            return
        self._embedding_loading = True
        self._embedding_loading_pair = pair_key
        self._embedding_load_id += 1
        load_id = self._embedding_load_id
        self._embedding_thread = EmbeddingLoaderThread(
            pair_key,
            paths,
            lower_case=settings.lower_case,
            parent=self,
        )
        self._embedding_thread.loaded.connect(
            lambda loaded_pair, index, error, load_id=load_id: self._on_embeddings_loaded(
                load_id, loaded_pair, index, error
            )
        )
        self._embedding_thread.start()
        self._update_replacement_filter_state()

    def _update_replacement_filter_state(self) -> None:
        replacement = self._selected_replacement()
        has_selection = replacement is not None
        pair_key = self._embedding_pair_for_replacement(replacement)
        has_embeddings = bool(pair_key and pair_key in self._embedding_indices)
        scope = self._replacement_filter_scope(replacement)
        enabled = has_embeddings and has_selection and scope != "none" and not self._embedding_loading
        self.replacement_threshold_slider.setEnabled(enabled)
        self.replacement_threshold_value.setEnabled(enabled)
        self.embedding_progress.setVisible(self._embedding_loading)
        if self._embedding_loading:
            self.replacement_hint_label.setText(t("replacement.loading_embeddings"))
            self.replacement_hint_label.setVisible(True)
        elif self._embedding_load_error:
            self.replacement_hint_label.setText(self._embedding_load_error)
            self.replacement_hint_label.setVisible(True)
        elif not has_embeddings:
            self.replacement_hint_label.setText(t("replacement.enable_embeddings_hint"))
            self.replacement_hint_label.setVisible(True)
        elif scope == "all":
            self.replacement_hint_label.setText(t("replacement.no_synonym_tags"))
            self.replacement_hint_label.setVisible(True)
        else:
            self.replacement_hint_label.setVisible(False)

    def _refresh_replacement_list(self) -> None:
        selected = self._selected_replacement()
        replacement_counts: dict[str, tuple[int, int, int]] = {}
        for rule in self.rules_model.rules():
            replacement = rule.replacement.strip()
            if not replacement:
                continue
            syn_total, syn_enabled, total = replacement_counts.get(replacement, (0, 0, 0))
            total += 1
            if "synonym" in rule.tags:
                syn_total += 1
                if rule.enabled:
                    syn_enabled += 1
            replacement_counts[replacement] = (syn_total, syn_enabled, total)
        self.replacement_list.blockSignals(True)
        self.replacement_list.clear()
        for replacement in sorted(replacement_counts.keys(), key=str.lower):
            syn_total, syn_enabled, total = replacement_counts[replacement]
            if syn_total:
                label = t(
                    "replacement.list_label",
                    replacement=replacement,
                    enabled=syn_enabled,
                    total=syn_total,
                )
            else:
                label = replacement
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, replacement)
            if syn_total:
                item.setToolTip(
                    t(
                        "replacement.tooltip_counts",
                        enabled=syn_enabled,
                        total=syn_total,
                        overall=total,
                    )
                )
            self.replacement_list.addItem(item)
        restored = False
        if selected:
            for row in range(self.replacement_list.count()):
                item = self.replacement_list.item(row)
                if item and item.data(Qt.UserRole) == selected:
                    self.replacement_list.setCurrentRow(row)
                    restored = True
                    break
        self.replacement_list.blockSignals(False)
        if selected and not restored:
            self.replacement_selected_label.setText(t("replacement.select_hint"))
        self._update_replacement_filter_state()

    def _selected_replacement(self) -> Optional[str]:
        item = self.replacement_list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _normalize_pair(self, lang_a: str, lang_b: str) -> str:
        if lang_a == lang_b:
            return f"{lang_a}-{lang_b}"
        return "-".join(sorted([lang_a, lang_b]))

    def _pair_for_pack(self, pack_id: str) -> Optional[str]:
        if pack_id in {"wordnet-en", "moby-en"}:
            return "en-en"
        if pack_id in {"openthesaurus-de", "odenet-de"}:
            return "de-de"
        if pack_id in {"jp-wordnet", "jp-wordnet-sqlite"}:
            return "ja-ja"
        if pack_id == "freedict-de-en" or pack_id == "freedict-en-de":
            return "de-en"
        if pack_id == "jmdict-ja-en":
            return "en-ja"
        if pack_id == "cc-cedict-zh-en":
            return "en-zh"
        return None

    def _embedding_pair_for_replacement(self, replacement: Optional[str]) -> Optional[str]:
        if not replacement:
            return None
        counts: dict[str, int] = {}
        for rule in self.rules_model.rules():
            if rule.replacement != replacement:
                continue
            pair = rule.metadata.language_pair if rule.metadata else None
            if not pair:
                continue
            counts[pair] = counts.get(pair, 0) + 1
        if not counts:
            return None
        return max(counts.items(), key=lambda item: item[1])[0]

    def _embedding_paths_for_pair(
        self,
        settings: Optional[SynonymSourceSettings],
        pair_key: Optional[str],
    ) -> list[Path]:
        if not settings or not settings.use_embeddings or not pair_key:
            return []
        enabled = dict(settings.embedding_pair_enabled or {})
        if pair_key in enabled and not enabled[pair_key]:
            return []
        pair_paths = dict(settings.embedding_pair_paths or {}).get(pair_key)
        paths: list[Path] = []
        if pair_paths:
            paths = [Path(path) for path in pair_paths if path]
        existing = [path for path in paths if path.exists()]
        return existing

    def _replacement_filter_scope(self, replacement: Optional[str]) -> str:
        if not replacement:
            return "none"
        has_any = False
        for rule in self.rules_model.rules():
            if rule.replacement != replacement:
                continue
            has_any = True
            if "synonym" in rule.tags:
                return "synonyms"
        return "all" if has_any else "none"

    def _default_embedding_threshold(self) -> float:
        settings = self.state.settings.synonyms
        if settings:
            return settings.embedding_threshold
        return 0.0

    def _on_replacement_selected(self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]) -> None:
        replacement = current.data(Qt.UserRole) if current else None
        if replacement:
            threshold = self._replacement_thresholds.get(replacement, self._default_embedding_threshold())
            self._replacement_slider_updating = True
            self.replacement_threshold_slider.setValue(int(round(threshold * 100)))
            self.replacement_threshold_value.setText(f"{threshold:.2f}")
            self._replacement_slider_updating = False
            scope = self._replacement_filter_scope(replacement)
            if scope == "all":
                self.replacement_selected_label.setText(
                    t("replacement.filter_rules", replacement=replacement)
                )
            else:
                self.replacement_selected_label.setText(
                    t("replacement.filter_synonyms", replacement=replacement)
                )
        else:
            self.replacement_selected_label.setText(t("replacement.select_hint"))
        self._ensure_embedding_loaded_for_selection()
        self._update_replacement_filter_state()

    def _on_replacement_threshold_changed(self, value: int) -> None:
        if self._replacement_slider_updating:
            return
        replacement = self._selected_replacement()
        if not replacement:
            return
        threshold = value / 100.0
        self.replacement_threshold_value.setText(f"{threshold:.2f}")
        self._replacement_thresholds[replacement] = threshold
        self._apply_replacement_threshold(replacement, threshold)

    def _on_embeddings_loaded(self, load_id: int, pair_key: str, index: Optional[EmbeddingIndex], error: str) -> None:
        if load_id != self._embedding_load_id:
            return
        self._embedding_loading = False
        if index is not None:
            self._embedding_indices[pair_key] = index
        self._embedding_load_error = error or None
        self._embedding_loading_pair = None
        if self._embedding_thread:
            self._embedding_thread.quit()
            self._embedding_thread = None
        self._update_replacement_filter_state()

    def _apply_replacement_threshold(self, replacement: str, threshold: float) -> None:
        pair_key = self._embedding_pair_for_replacement(replacement)
        if not pair_key:
            return
        index = self._embedding_indices.get(pair_key)
        if index is None:
            return
        scope = self._replacement_filter_scope(replacement)
        if scope == "none":
            return
        updates: list[tuple[int, VocabRule]] = []
        for row, rule in enumerate(self.rules_model.rules()):
            if rule.replacement != replacement:
                continue
            if scope == "synonyms" and "synonym" not in rule.tags:
                continue
            score = index.similarity(rule.source_phrase, replacement)
            if score is None:
                enabled = threshold <= 0.0
            else:
                enabled = score >= threshold
            if rule.enabled != enabled:
                updates.append((row, replace(rule, enabled=enabled)))
        if updates:
            self.rules_model.update_rules_bulk(updates)

    def _append_log(self, message: str, *, color: Optional[QColor] = None) -> None:
        if not message:
            return
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        if color:
            fmt.setForeground(color)
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")
        self.log_edit.setTextCursor(cursor)
        self.log_edit.ensureCursorVisible()

    def _refresh_profiles_ui(self) -> None:
        profiles = self.state.settings.profiles
        active_id = self.state.settings.active_profile_id
        self._profile_combo_updating = True
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        active_index = -1
        for idx, profile in enumerate(profiles):
            label = profile.name or profile.profile_id
            self.profile_combo.addItem(label, profile)
            if profile.profile_id == active_id:
                active_index = idx
        if active_index >= 0:
            self.profile_combo.setCurrentIndex(active_index)
        self.profile_combo.blockSignals(False)
        self._profile_combo_updating = False
        self._refresh_ruleset_ui()

    def _current_profile(self) -> Optional[Profile]:
        active_id = self.state.settings.active_profile_id
        for profile in self.state.settings.profiles:
            if profile.profile_id == active_id:
                return profile
        return None

    def _refresh_ruleset_ui(self) -> None:
        profile = self._current_profile()
        self._ruleset_combo_updating = True
        self.ruleset_combo.blockSignals(True)
        self.ruleset_combo.clear()
        if profile is None:
            self.ruleset_combo.blockSignals(False)
            self._ruleset_combo_updating = False
            return
        active_path = self._active_ruleset_path(profile)
        active_index = -1
        for idx, path in enumerate(profile.rulesets or (active_path,)):
            if not path:
                continue
            label = str(Path(path).name) or path
            display = label
            if not Path(path).exists():
                display = t("ruleset.missing", label=label)
            self.ruleset_combo.addItem(display, path)
            self.ruleset_combo.setItemData(idx, path, Qt.ToolTipRole)
            if path == active_path:
                active_index = idx
        if active_index >= 0:
            self.ruleset_combo.setCurrentIndex(active_index)
        self.ruleset_combo.blockSignals(False)
        self._ruleset_combo_updating = False

    def _rebuild_profiles_menu(self) -> None:
        if not hasattr(self, "_profiles_menu"):
            return
        for action in self._profile_actions:
            self._profiles_menu.removeAction(action)
            self._profiles_action_group.removeAction(action)
        self._profile_actions = []

        settings = self.state.settings
        active_id = settings.active_profile_id
        for profile in settings.profiles:
            label = profile.name or profile.profile_id
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(profile.profile_id == active_id)
            action.triggered.connect(
                lambda checked, p=profile: self._switch_profile_from_menu(p, checked)
            )
            self._profiles_action_group.addAction(action)
            self._profiles_menu.addAction(action)
            self._profile_actions.append(action)

    def _switch_profile_from_menu(self, profile: Profile, checked: bool) -> None:
        if not checked:
            return
        if not self._confirm_discard_changes():
            self._rebuild_profiles_menu()
            return
        self._load_profile(profile)

    def _migrate_ruleset_paths(self) -> None:
        settings = self.state.settings
        if not settings.profiles:
            return
        base_dir = os.path.abspath(str(_app_data_dir()))
        rulesets_dir = os.path.abspath(str(_rulesets_dir()))
        changed = False
        updated_profiles: list[Profile] = []

        def migrate_path(path: Optional[str]) -> tuple[Optional[str], bool]:
            if not path:
                return path, False
            expanded = os.path.abspath(os.path.expanduser(path))
            if expanded.startswith(rulesets_dir + os.sep):
                return path, False
            try:
                if os.path.commonpath([expanded, base_dir]) != base_dir:
                    return path, False
            except ValueError:
                return path, False
            if not os.path.exists(expanded):
                return path, False
            new_path = os.path.join(rulesets_dir, os.path.basename(expanded))
            if expanded != new_path:
                os.makedirs(rulesets_dir, exist_ok=True)
                if not os.path.exists(new_path):
                    try:
                        os.replace(expanded, new_path)
                    except OSError:
                        return path, False
                return new_path, True
            return path, False

        for profile in settings.profiles:
            dataset_path, changed_dataset = migrate_path(profile.dataset_path)
            active_ruleset, changed_active = migrate_path(profile.active_ruleset)
            rulesets = []
            changed_rulesets = False
            for ruleset_path in profile.rulesets:
                migrated, changed_rule = migrate_path(ruleset_path)
                rulesets.append(migrated or ruleset_path)
                changed_rulesets = changed_rulesets or changed_rule
            if changed_dataset or changed_active or changed_rulesets:
                changed = True
                updated_profiles.append(
                    replace(
                        profile,
                        dataset_path=dataset_path or profile.dataset_path,
                        active_ruleset=active_ruleset or profile.active_ruleset,
                        rulesets=tuple(rulesets),
                    )
                )
            else:
                updated_profiles.append(profile)

        if changed:
            self.state.update_settings(replace(settings, profiles=tuple(updated_profiles)))


def _app_data_dir() -> Path:
    base_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _fallback_log_dirs() -> list[Path]:
    paths: list[Path] = []
    paths.append(Path("/tmp"))
    home = Path.home()
    if sys.platform == "darwin":
        paths.append(home / "Library" / "Logs" / "LexiShift")
    elif sys.platform.startswith("win"):
        paths.append(home / "AppData" / "Local" / "LexiShift" / "Logs")
    else:
        paths.append(home / ".local" / "state" / "LexiShift")
    return paths


def _startup_log_paths() -> list[Path]:
    paths: list[Path] = []
    try:
        paths.append(_app_data_dir() / "startup_timing.log")
    except Exception:
        pass
    for base in _fallback_log_dirs():
        try:
            base.mkdir(parents=True, exist_ok=True)
            paths.append(base / "lexishift_startup.log")
        except OSError:
            continue
    return paths


def _rulesets_dir() -> Path:
    target = Path(os.path.join(str(_app_data_dir()), "rulesets"))
    target.mkdir(parents=True, exist_ok=True)
    return target


def _settings_path() -> Path:
    return _app_data_dir() / "settings.json"


def _default_dataset_path() -> Path:
    return _rulesets_dir() / "vocab.json"


def main() -> None:
    # Ensure AppDataLocation is scoped to LexiShift before any logging.
    QCoreApplication.setOrganizationName("LexiShift")
    QCoreApplication.setApplicationName("LexiShift")
    startup_logs = _startup_log_paths()
    start_time = time.perf_counter()
    last_time = start_time

    def log_startup(label: str) -> None:
        nonlocal last_time
        now = time.perf_counter()
        delta_ms = (now - last_time) * 1000.0
        total_ms = (now - start_time) * 1000.0
        last_time = now
        message = f"[startup] {label} (+{delta_ms:.1f} ms, total {total_ms:.1f} ms)"
        for path in startup_logs:
            try:
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write(message + "\n")
            except OSError:
                continue
        print(message)

    print("[LexiShift] STARTUP MARKER")
    log_startup("main() begin")
    if "--print-data-dir" in sys.argv:
        print(f"[LexiShift] AppDataLocation={_app_data_dir()}")
        print(f"[LexiShift] Startup log paths={startup_logs}")
        return
    if "--diagnose-startup" in sys.argv:
        print(f"[LexiShift] AppDataLocation={_app_data_dir()}")
        print(f"[LexiShift] Startup log paths={startup_logs}")
    if "--helper-daemon" in sys.argv:
        from helper_daemon import run_daemon_from_cli

        filtered_args = [arg for arg in sys.argv[1:] if arg != "--helper-daemon"]
        run_daemon_from_cli(filtered_args)
        return

    # Setup global exception hook to catch crashes
    def exception_hook(exctype, value, tb):
        error_msg = "".join(traceback.format_exception(exctype, value, tb))
        crash_log = _app_data_dir() / "crash.log"
        with open(crash_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Crash:\n{error_msg}\n\n")
        sys.__excepthook__(exctype, value, tb)
    sys.excepthook = exception_hook
    log_startup("exception hook installed")

    app = QApplication(sys.argv)
    log_startup("QApplication created")

    # Singleton check: ensure only one GUI window runs
    import getpass
    socket_name = f"LexiShiftGUI_{getpass.getuser()}"
    socket = QLocalSocket()
    socket.connectToServer(socket_name)
    if socket.waitForConnected(500):
        socket.write(b"ACTIVATE")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        sys.exit(0)

    server = QLocalServer()
    server.removeServer(socket_name)
    server.listen(socket_name)
    log_startup("single-instance server ready")

    theme_dir()
    log_startup("theme_dir()")
    ensure_sample_images()
    log_startup("ensure_sample_images()")
    ensure_sample_themes()
    log_startup("ensure_sample_themes()")
    ui_settings = QSettings()
    locale_pref = ui_settings.value("appearance/locale", "system")
    if locale_pref == "system":
        locale_pref = QLocale.system().name()
    set_locale(str(locale_pref))
    log_startup("locale initialized")
    window = MainWindow()
    log_startup("MainWindow constructed")

    def handle_activation():
        client = server.nextPendingConnection()
        if client:
            client.waitForReadyRead(100)
            window.show()
            window.raise_()
            window.activateWindow()
            client.disconnectFromServer()
    server.newConnection.connect(handle_activation)

    window.show()
    log_startup("window shown")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
