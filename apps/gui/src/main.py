from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
CORE_ROOT = os.path.join(REPO_ROOT, "core")
GUI_ROOT = os.path.join(REPO_ROOT, "apps", "gui", "src")
for path in (CORE_ROOT, GUI_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtCore import QStandardPaths, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QListView,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTableView,
    QToolBar,
    QWidget,
    QVBoxLayout,
)

from lexishift_core import (
    AppSettings,
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
from models import ProfilesListModel, RulesTableModel
from preview import PreviewController, ReplacementHighlighter
from state import AppState


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VocabReplacer")

        settings_path = _settings_path()
        self.state = AppState(settings_path=settings_path)
        first_run = not settings_path.exists()
        self.state.load_settings()
        if not self.state.settings.profiles:
            if not self._run_first_time_setup(first_run=first_run):
                self._seed_default_profile()

        self.profile_model = ProfilesListModel(
            self.state.settings.profiles,
            active_profile_id=self.state.settings.active_profile_id,
        )
        self.rules_model = RulesTableModel([])
        self.rules_model.rulesChanged.connect(self._on_rules_changed)

        self.profile_list = QListView()
        self.profile_list.setModel(self.profile_model)
        self.profile_list.clicked.connect(self._on_profile_selected)

        self.rules_table = QTableView()
        self.rules_table.setModel(self.rules_model)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.clicked.connect(self._on_rule_table_clicked)

        self.input_edit = QPlainTextEdit()
        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setReadOnly(True)
        self.highlighter = ReplacementHighlighter(self.preview_edit.document())

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addWidget(self.profile_list)
        editor_layout.addWidget(self.rules_table)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.addWidget(self.input_edit)
        preview_layout.addWidget(self.preview_edit)

        splitter = QSplitter()
        splitter.addWidget(editor_panel)
        splitter.addWidget(preview_panel)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        self._setup_toolbar()
        self._setup_preview()
        self._load_active_profile()

        self.state.datasetChanged.connect(self._on_dataset_loaded)
        self.state.dirtyChanged.connect(self._on_dirty_changed)
        self.state.profilesChanged.connect(self._on_profiles_changed)
        self.state.activeProfileChanged.connect(self._select_active_profile)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self._open_dataset)
        toolbar.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_dataset)
        toolbar.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self._save_dataset_as)
        toolbar.addAction(save_as_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

        new_profile_action = QAction("New Profile", self)
        new_profile_action.triggered.connect(self._create_profile)
        toolbar.addAction(new_profile_action)

        profiles_action = QAction("Profiles", self)
        profiles_action.triggered.connect(self._manage_profiles)
        toolbar.addAction(profiles_action)

        add_rule_action = QAction("Add Rule", self)
        add_rule_action.triggered.connect(self._add_rule)
        toolbar.addAction(add_rule_action)

        bulk_add_action = QAction("Synonym Bulk Add", self)
        bulk_add_action.triggered.connect(self._bulk_add_rules)
        toolbar.addAction(bulk_add_action)

        delete_rule_action = QAction("Delete Rule", self)
        delete_rule_action.triggered.connect(self._delete_rule)
        toolbar.addAction(delete_rule_action)

        edit_metadata_action = QAction("Edit Metadata", self)
        edit_metadata_action.triggered.connect(self._edit_rule_metadata)
        toolbar.addAction(edit_metadata_action)

        export_json_action = QAction("Export Vocab Pool (JSON)", self)
        export_json_action.triggered.connect(self._export_json)
        toolbar.addAction(export_json_action)

        export_code_action = QAction("Export Vocab Pool (Code)", self)
        export_code_action.triggered.connect(self._export_code)
        toolbar.addAction(export_code_action)

        export_profiles_json_action = QAction("Export Profiles (JSON)", self)
        export_profiles_json_action.triggered.connect(self._export_profiles_json)
        toolbar.addAction(export_profiles_json_action)

        export_profiles_code_action = QAction("Export Profiles (Code)", self)
        export_profiles_code_action.triggered.connect(self._export_profiles_code)
        toolbar.addAction(export_profiles_code_action)

        import_json_action = QAction("Import Vocab Pool (JSON)", self)
        import_json_action.triggered.connect(self._import_json)
        toolbar.addAction(import_json_action)

        import_code_action = QAction("Import Vocab Pool (Code)", self)
        import_code_action.triggered.connect(self._import_code)
        toolbar.addAction(import_code_action)

        import_profiles_json_action = QAction("Import Profiles (JSON)", self)
        import_profiles_json_action.triggered.connect(self._import_profiles_json)
        toolbar.addAction(import_profiles_json_action)

        import_profiles_code_action = QAction("Import Profiles (Code)", self)
        import_profiles_code_action.triggered.connect(self._import_profiles_code)
        toolbar.addAction(import_profiles_code_action)

        self._save_action = save_action
        self._save_action.setEnabled(False)
        self._edit_metadata_action = edit_metadata_action
        self._delete_rule_action = delete_rule_action
        self._export_code_action = export_code_action
        self._export_profiles_code_action = export_profiles_code_action
        self._update_rule_actions()
        self._apply_import_export_settings()

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
        profile = Profile(profile_id="default", name="Default", dataset_path=str(default_dataset))
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
        path, _ = QFileDialog.getOpenFileName(self, "Open Dataset", str(_default_dataset_path()), "JSON Files (*.json)")
        if not path:
            return
        self.state.load_dataset(Path(path))

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
        index = self.rules_model.index(row, self.rules_model.COLUMN_SOURCE)
        self.rules_table.setCurrentIndex(index)
        self.rules_table.edit(index)

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
        row = self.rules_table.currentIndex().row()
        if row < 0:
            return
        self.rules_model.remove_rule(row)

    def _edit_rule_metadata(self) -> None:
        row = self.rules_table.currentIndex().row()
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
            self.rules_model.remove_rule(index.row())

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
        path, _ = QFileDialog.getSaveFileName(self, "Save Dataset", str(_default_dataset_path()), "JSON Files (*.json)")
        if not path:
            return
        self.state.save_dataset(path=Path(path))

    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Dataset JSON", "", "JSON Files (*.json)")
        if not path:
            return
        payload = export_dataset_json(self.state.dataset)
        Path(path).write_text(payload, encoding="utf-8")

    def _export_code(self) -> None:
        payload = export_dataset_code(self.state.dataset)
        dialog = CodeDialog("Export Vocab Pool Code", code=payload, read_only=True, parent=self)
        dialog.exec()

    def _export_profiles_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Profiles JSON", "", "JSON Files (*.json)")
        if not path:
            return
        payload = export_app_settings_json(self.state.settings)
        Path(path).write_text(payload, encoding="utf-8")

    def _export_profiles_code(self) -> None:
        payload = export_app_settings_code(self.state.settings)
        dialog = CodeDialog("Export Profiles Code", code=payload, read_only=True, parent=self)
        dialog.exec()

    def _import_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import Dataset JSON", "", "JSON Files (*.json)")
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        dataset = import_dataset_json(payload)
        self.state.update_dataset(dataset)

    def _import_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog("Import Vocab Pool Code", parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        dataset = import_dataset_code(dialog.code())
        self.state.update_dataset(dataset)

    def _import_profiles_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import Profiles JSON", "", "JSON Files (*.json)")
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        settings = import_app_settings_json(payload)
        self.state.update_settings(settings)
        self._load_active_profile()

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
        dataset_path = Path(profile.dataset_path)
        self.state.load_dataset(dataset_path)
        settings = self.state.settings
        if settings.active_profile_id != profile.profile_id:
            self.state.set_profiles(settings.profiles, active_profile_id=profile.profile_id)

    def _on_profile_selected(self, index) -> None:
        profile = self.profile_model.data(index, Qt.UserRole)
        if profile is None:
            return
        if not self._confirm_discard_changes():
            return
        self._load_profile(profile)

    def _on_dataset_loaded(self, dataset: VocabDataset) -> None:
        self.rules_model.set_rules(list(dataset.rules))
        self._schedule_preview()

    def _on_rules_changed(self, rules) -> None:
        dataset = replace(self.state.dataset, rules=tuple(rules))
        self.state.update_dataset(dataset)
        self._schedule_preview()

    def _on_dirty_changed(self, dirty: bool) -> None:
        self._save_action.setEnabled(dirty)

    def _on_profiles_changed(self, profiles) -> None:
        self._refresh_profiles_ui()

    def _schedule_preview(self) -> None:
        self._preview_timer.start()

    def _run_preview(self) -> None:
        self._preview_controller.request(self.state.dataset, self.input_edit.toPlainText())

    def _apply_preview(self, output: str, spans) -> None:
        self.preview_edit.setPlainText(output)
        self.highlighter.set_spans(spans)

    def _select_active_profile(self, *_args) -> None:
        self._refresh_profiles_ui()

    def _update_rule_actions(self) -> None:
        has_selection = self.rules_table.currentIndex().row() >= 0
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

    def _refresh_profiles_ui(self) -> None:
        profiles = self.state.settings.profiles
        active_id = self.state.settings.active_profile_id
        self.profile_model.set_profiles(profiles)
        self.profile_model.set_active_profile_id(active_id)
        if not active_id:
            return
        for row, profile in enumerate(profiles):
            if profile.profile_id == active_id:
                index = self.profile_model.index(row, 0)
                self.profile_list.setCurrentIndex(index)
                break


def _app_data_dir() -> Path:
    base_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _settings_path() -> Path:
    return _app_data_dir() / "settings.json"


def _default_dataset_path() -> Path:
    return _app_data_dir() / "vocab.json"


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
