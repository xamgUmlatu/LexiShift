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
    QSettings,
    QSortFilterProxyModel,
    QStandardPaths,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import QAction, QActionGroup, QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStyledItemDelegate,
    QTableView,
    QStyle,
    QWidget,
    QVBoxLayout,
)

from lexishift_core import (
    AppSettings,
    ImportExportSettings,
    Profile,
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
    SynonymGenerator,
    SynonymOptions,
    SynonymSources,
)

from dialogs import (
    BulkRulesDialog,
    CodeDialog,
    CreateProfileDialog,
    FirstRunDialog,
    ProfilesDialog,
    RuleMetadataDialog,
    SettingsDialog,
)
from models import RulesTableModel
from preview import PreviewController, ReplacementHighlighter
from state import AppState


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
        painter.drawText(rect, Qt.AlignCenter, "Delete")
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return size.expandedTo(QSize(64, size.height()))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LexiShift")
        self._ui_settings = QSettings()

        settings_path = _settings_path()
        self.state = AppState(settings_path=settings_path)
        first_run = not settings_path.exists()
        self.state.load_settings()
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
        self.manage_profiles_button = QPushButton("Manage...")
        self.manage_profiles_button.clicked.connect(self._manage_profiles)
        self.save_profiles_button = QPushButton("Save Profiles")
        self.save_profiles_button.clicked.connect(self._save_profiles)
        self._ruleset_combo_updating = False
        self.ruleset_combo = QComboBox()
        self.ruleset_combo.currentIndexChanged.connect(self._on_ruleset_selected)
        self.ruleset_combo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ruleset_combo.customContextMenuRequested.connect(self._ruleset_context_menu)
        self.open_ruleset_button = QPushButton("Select...")
        self.open_ruleset_button.clicked.connect(self._open_dataset)
        self.save_ruleset_button = QPushButton("Save Ruleset")
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

        self.input_edit = QPlainTextEdit()
        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setReadOnly(True)
        self.highlighter = ReplacementHighlighter(self.preview_edit.document())

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addWidget(self._build_profile_header())
        editor_layout.addWidget(self.rules_table)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.addWidget(self.input_edit)
        preview_layout.addWidget(self.preview_edit)

        splitter = QSplitter()
        splitter.addWidget(editor_panel)
        splitter.addWidget(preview_panel)
        splitter.setStretchFactor(1, 1)
        self._splitter = splitter

        self.setCentralWidget(splitter)

        self._setup_actions()
        self._setup_menu()
        self._setup_preview()
        self._load_active_profile()
        self._refresh_profiles_ui()
        self._restore_window_state()

        self.state.datasetChanged.connect(self._on_dataset_loaded)
        self.state.dirtyChanged.connect(self._on_dirty_changed)
        self.state.profilesChanged.connect(self._on_profiles_changed)
        self.state.activeProfileChanged.connect(self._select_active_profile)

    def _setup_actions(self) -> None:
        self._open_action = QAction("Open Ruleset...", self)
        self._open_action.triggered.connect(self._open_dataset)

        self._save_action = QAction("Save Ruleset", self)
        self._save_action.triggered.connect(self._save_dataset)

        self._save_as_action = QAction("Save Ruleset As...", self)
        self._save_as_action.triggered.connect(self._save_dataset_as)

        self._settings_action = QAction("Settings...", self)
        self._settings_action.setMenuRole(QAction.PreferencesRole)
        self._settings_action.triggered.connect(self._open_settings)

        self._manage_profiles_action = QAction("Manage Profiles...", self)
        self._manage_profiles_action.triggered.connect(self._manage_profiles)

        self._save_profiles_action = QAction("Save Profiles", self)
        self._save_profiles_action.triggered.connect(self._save_profiles)

        self._add_rule_action = QAction("Add Rule", self)
        self._add_rule_action.triggered.connect(self._add_rule)

        self._bulk_add_action = QAction("Synonym Bulk Add...", self)
        self._bulk_add_action.triggered.connect(self._bulk_add_rules)

        self._delete_rule_action = QAction("Delete Rule", self)
        self._delete_rule_action.triggered.connect(self._delete_rule)

        self._edit_metadata_action = QAction("Edit Metadata...", self)
        self._edit_metadata_action.triggered.connect(self._edit_rule_metadata)

        self._export_json_action = QAction("Export Ruleset (JSON)...", self)
        self._export_json_action.triggered.connect(self._export_json)

        self._export_code_action = QAction("Export Ruleset (Code)...", self)
        self._export_code_action.triggered.connect(self._export_code)

        self._export_profiles_json_action = QAction("Export Profiles (JSON)...", self)
        self._export_profiles_json_action.triggered.connect(self._export_profiles_json)

        self._export_profiles_code_action = QAction("Export Profiles (Code)...", self)
        self._export_profiles_code_action.triggered.connect(self._export_profiles_code)

        self._import_json_action = QAction("Import Ruleset (JSON)...", self)
        self._import_json_action.triggered.connect(self._import_json)

        self._import_code_action = QAction("Import Ruleset (Code)...", self)
        self._import_code_action.triggered.connect(self._import_code)

        self._import_profiles_json_action = QAction("Import Profiles (JSON)...", self)
        self._import_profiles_json_action.triggered.connect(self._import_profiles_json)

        self._import_profiles_code_action = QAction("Import Profiles (Code)...", self)
        self._import_profiles_code_action.triggered.connect(self._import_profiles_code)

        self._save_action.setEnabled(False)
        self._update_rule_actions()
        self._apply_import_export_settings()

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)

        import_menu = file_menu.addMenu("Import")
        import_menu.addAction(self._import_json_action)
        import_menu.addAction(self._import_code_action)
        import_menu.addSeparator()
        import_menu.addAction(self._import_profiles_json_action)
        import_menu.addAction(self._import_profiles_code_action)

        export_menu = file_menu.addMenu("Export")
        export_menu.addAction(self._export_json_action)
        export_menu.addAction(self._export_code_action)
        export_menu.addSeparator()
        export_menu.addAction(self._export_profiles_json_action)
        export_menu.addAction(self._export_profiles_code_action)

        file_menu.addSeparator()
        file_menu.addAction(self._settings_action)
        file_menu.addSeparator()

        self._quit_action = QAction("Quit", self)
        self._quit_action.setMenuRole(QAction.QuitRole)
        self._quit_action.triggered.connect(self.close)
        file_menu.addAction(self._quit_action)

        profiles_menu = menu_bar.addMenu("Profiles")
        profiles_menu.addAction(self._manage_profiles_action)
        profiles_menu.addAction(self._save_profiles_action)
        profiles_menu.addSeparator()

        self._profiles_menu = profiles_menu
        self._profiles_action_group = QActionGroup(self)
        self._profiles_action_group.setExclusive(True)
        self._profile_actions: list[QAction] = []
        self._rebuild_profiles_menu()

        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction(self._add_rule_action)
        edit_menu.addAction(self._bulk_add_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._edit_metadata_action)
        edit_menu.addAction(self._delete_rule_action)

    def _build_profile_header(self) -> QWidget:
        profile_label = QLabel("Profile")
        ruleset_label = QLabel("Ruleset")

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

    def _save_window_state(self) -> None:
        self._ui_settings.setValue("main_window/geometry", self.saveGeometry())
        self._ui_settings.setValue("main_window/splitter", self._splitter.saveState())

    def closeEvent(self, event) -> None:
        if self.state.dirty:
            choice = QMessageBox(self)
            choice.setIcon(QMessageBox.Warning)
            choice.setWindowTitle("Unsaved Changes")
            choice.setText("Save changes to the current ruleset before quitting?")
            choice.setInformativeText("Your edits will be lost if you don't save.")
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
            name="Default",
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
        path, _ = QFileDialog.getOpenFileName(self, "Select Ruleset", self._default_import_dir(), "JSON Files (*.json)")
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
            default_dir=_app_data_dir(),
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
        dialog = CreateProfileDialog(default_dir=_app_data_dir(), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        profile = dialog.profile()
        if any(existing.profile_id == profile.profile_id for existing in self.state.settings.profiles):
            QMessageBox.warning(self, "Profile ID", "Profile ID already exists.")
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
        self._schedule_preview()

    def _add_rule(self) -> None:
        self.rules_model.add_rule(VocabRule(source_phrase="", replacement=""))
        row = self.rules_model.rowCount() - 1
        source_index = self.rules_model.index(row, self.rules_model.COLUMN_SOURCE)
        proxy_index = self._rules_proxy.mapFromSource(source_index)
        if proxy_index.isValid():
            self.rules_table.setCurrentIndex(proxy_index)
            self.rules_table.edit(proxy_index)

    def _bulk_add_rules(self) -> None:
        dialog = BulkRulesDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        targets = dialog.targets()
        if not targets:
            return
        rules = self._generate_synonym_rules(targets)
        if not rules:
            QMessageBox.information(self, "Synonym Bulk Add", "No synonyms found for the provided targets.")
            return
        self.rules_model.add_rules(rules)

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
            message = f"Delete this rule?\n\n{rule.source_phrase} -> {rule.replacement}\n\nThis cannot be undone."
            reply = QMessageBox.question(
                self,
                "Delete Rule",
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

    def _generate_synonym_rules(self, targets: list[str]) -> list[VocabRule]:
        settings = self.state.settings.synonyms
        if not settings or (not settings.wordnet_dir and not settings.moby_path):
            QMessageBox.warning(self, "Synonym Expansion", "Configure synonym sources in Settings first.")
            return []
        missing_sources = []
        if settings.wordnet_dir and not Path(settings.wordnet_dir).exists():
            missing_sources.append("WordNet directory")
        if settings.moby_path and not Path(settings.moby_path).exists():
            missing_sources.append("Moby thesaurus file")
        if missing_sources:
            QMessageBox.warning(
                self,
                "Synonym Expansion",
                "Missing sources: " + ", ".join(missing_sources),
            )
            return []
        sources = SynonymSources(
            wordnet_dir=Path(settings.wordnet_dir) if settings.wordnet_dir else None,
            moby_path=Path(settings.moby_path) if settings.moby_path else None,
        )
        options = SynonymOptions(
            max_synonyms=settings.max_synonyms,
            include_phrases=settings.include_phrases,
            lower_case=settings.lower_case,
        )
        generator = SynonymGenerator(sources, options=options)
        if generator.total_entries() == 0:
            stats = generator.stats()
            QMessageBox.information(
                self,
                "Synonym Expansion",
                f"No entries loaded from sources (WordNet={stats.get('wordnet', 0)}, Moby={stats.get('moby', 0)}).",
            )
            return []
        pairs = generator.generate_rules(targets, avoid_duplicates=True)
        return [VocabRule(source_phrase=source, replacement=target) for source, target in pairs]

    def _save_dataset(self) -> None:
        if self.state.dataset_path is None:
            self._save_dataset_as()
            return
        self.state.save_dataset()

    def _save_dataset_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Ruleset As", self._default_export_dir(), "JSON Files (*.json)")
        if not path:
            return
        dataset_path = Path(path)
        self.state.save_dataset(path=dataset_path)
        self._set_active_ruleset_path(dataset_path)
        self._remember_export_path(dataset_path)

    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Ruleset JSON", self._default_export_dir(), "JSON Files (*.json)")
        if not path:
            return
        payload = export_dataset_json(self.state.dataset)
        Path(path).write_text(payload, encoding="utf-8")
        self._remember_export_path(Path(path))

    def _export_code(self) -> None:
        payload = export_dataset_code(self.state.dataset)
        dialog = CodeDialog("Export Ruleset Code", code=payload, read_only=True, parent=self)
        dialog.exec()

    def _export_profiles_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Profiles JSON", self._default_export_dir(), "JSON Files (*.json)")
        if not path:
            return
        payload = export_app_settings_json(self.state.settings)
        Path(path).write_text(payload, encoding="utf-8")
        self._remember_export_path(Path(path))

    def _export_profiles_code(self) -> None:
        payload = export_app_settings_code(self.state.settings)
        dialog = CodeDialog("Export Profiles Code", code=payload, read_only=True, parent=self)
        dialog.exec()

    def _import_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import Ruleset JSON", self._default_import_dir(), "JSON Files (*.json)")
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        dataset = import_dataset_json(payload)
        self.state.update_dataset(dataset)
        self._remember_import_path(Path(path))

    def _import_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog("Import Ruleset Code", parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        dataset = import_dataset_code(dialog.code())
        self.state.update_dataset(dataset)

    def _import_profiles_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import Profiles JSON", self._default_import_dir(), "JSON Files (*.json)")
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        settings = import_app_settings_json(payload)
        self.state.update_settings(settings)
        self._load_active_profile()
        self._remember_import_path(Path(path))

    def _import_profiles_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog("Import Profiles Code", parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        settings = import_app_settings_code(dialog.code())
        self.state.update_settings(settings)
        self._load_active_profile()

    def _confirm_discard_changes(self) -> bool:
        if not self.state.dirty:
            return True
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Discard them?",
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
        reveal_action = menu.addAction("Reveal in Finder")
        action = menu.exec(self.ruleset_combo.mapToGlobal(position))
        if action == reveal_action:
            self._reveal_path(path)

    def _on_dataset_loaded(self, dataset: VocabDataset) -> None:
        self.rules_model.set_rules(list(dataset.rules))
        self._schedule_preview()
        self._refresh_ruleset_ui()

    def _on_rules_changed(self, rules) -> None:
        dataset = replace(self.state.dataset, rules=tuple(rules))
        self.state.update_dataset(dataset)
        self._schedule_preview()

    def _on_dirty_changed(self, dirty: bool) -> None:
        self._save_action.setEnabled(dirty)
        self.save_ruleset_button.setEnabled(dirty)

    def _on_profiles_changed(self, profiles) -> None:
        self._refresh_profiles_ui()
        self._rebuild_profiles_menu()

    def _schedule_preview(self) -> None:
        self._preview_timer.start()

    def _run_preview(self) -> None:
        self._preview_controller.request(self.state.dataset, self.input_edit.toPlainText())

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
                display = f"{label} (missing)"
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


def _app_data_dir() -> Path:
    base_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _settings_path() -> Path:
    return _app_data_dir() / "settings.json"


def _default_dataset_path() -> Path:
    return _app_data_dir() / "vocab.json"


def main() -> None:
    QCoreApplication.setOrganizationName("LexiShift")
    QCoreApplication.setApplicationName("LexiShift")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
