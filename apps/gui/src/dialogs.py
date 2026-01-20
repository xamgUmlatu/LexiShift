from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lexishift_core import (
    AppSettings,
    ImportExportSettings,
    InflectionSettings,
    InflectionSpec,
    LearningSettings,
    Profile,
    RuleMetadata,
    SynonymSourceSettings,
    VocabRule,
    VocabSettings,
)


class ProfilesDialog(QDialog):
    def __init__(
        self,
        profiles: tuple[Profile, ...],
        active_profile_id: Optional[str],
        default_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage Profiles")
        self.setSizeGripEnabled(True)
        self._default_dir = default_dir
        self._profiles = list(profiles)
        self._active_profile_id = active_profile_id
        self._current_index: Optional[int] = None
        self._updating = False

        self.list_widget = QListWidget()
        for profile in self._profiles:
            self.list_widget.addItem(_profile_display(profile))

        self.list_widget.currentRowChanged.connect(self._on_select)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._profile_context_menu)

        self.add_button = QPushButton("Add")
        self.remove_button = QPushButton("Remove")
        self.add_button.clicked.connect(self._add_profile)
        self.remove_button.clicked.connect(self._remove_profile)

        list_panel = QVBoxLayout()
        list_panel.addWidget(self.list_widget)
        list_button_row = QHBoxLayout()
        list_button_row.addWidget(self.add_button)
        list_button_row.addWidget(self.remove_button)
        list_panel.addLayout(list_button_row)

        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()

        self.ruleset_list = QListWidget()
        self.ruleset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ruleset_list.customContextMenuRequested.connect(self._ruleset_context_menu)

        self.ruleset_add_button = QPushButton("Add Ruleset")
        self.ruleset_remove_button = QPushButton("Remove")
        self.ruleset_set_active_button = QPushButton("Set Active")
        self.ruleset_add_button.clicked.connect(self._add_ruleset)
        self.ruleset_remove_button.clicked.connect(self._remove_ruleset)
        self.ruleset_set_active_button.clicked.connect(self._set_active_ruleset)
        self.ruleset_list.itemDoubleClicked.connect(lambda *_: self._set_active_ruleset())

        ruleset_button_row = QHBoxLayout()
        ruleset_button_row.addWidget(self.ruleset_add_button)
        ruleset_button_row.addWidget(self.ruleset_remove_button)
        ruleset_button_row.addWidget(self.ruleset_set_active_button)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow("Profile ID", self.id_edit)
        form.addRow("Name", self.name_edit)
        form.addRow("Rulesets", self.ruleset_list)
        form.addRow("", ruleset_button_row)
        form.addRow("Tags (comma)", self.tags_edit)
        form.addRow("Description", self.description_edit)

        right_panel = QWidget()
        right_panel.setLayout(form)

        main_row = QHBoxLayout()
        left_panel_widget = QWidget()
        left_panel_widget.setLayout(list_panel)
        main_row.addWidget(left_panel_widget, 1)
        main_row.addWidget(right_panel, 2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(main_row)
        hint_label = QLabel("Active profile is the selected row when saving.")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        layout.addWidget(button_box)

        self.id_edit.editingFinished.connect(self._commit_current)
        self.name_edit.textChanged.connect(self._commit_current)
        self.tags_edit.editingFinished.connect(self._commit_current)
        self.description_edit.textChanged.connect(self._commit_current)

        if self._profiles:
            initial_index = 0
            if active_profile_id:
                for idx, profile in enumerate(self._profiles):
                    if profile.profile_id == active_profile_id:
                        initial_index = idx
                        break
            self.list_widget.setCurrentRow(initial_index)

    def accept(self) -> None:
        self._commit_current()
        if self._validate_profiles():
            super().accept()

    def _validate_profiles(self) -> bool:
        if not self._profiles:
            QMessageBox.warning(self, "Profiles", "At least one profile is required.")
            return False
        ids = [profile.profile_id.strip() for profile in self._profiles]
        if any(not profile_id for profile_id in ids):
            QMessageBox.warning(self, "Profile ID", "Profile ID cannot be empty.")
            return False
        if len(set(ids)) != len(ids):
            QMessageBox.warning(self, "Profile ID", "Profile IDs must be unique.")
            return False
        for profile in self._profiles:
            if not profile.rulesets:
                QMessageBox.warning(self, "Rulesets", f"At least one ruleset is required for '{profile.name}'.")
                return False
        return True

    def result_profiles(self) -> tuple[Profile, ...]:
        return tuple(self._profiles)

    def result_active_profile_id(self) -> Optional[str]:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._profiles):
            return None
        return self._profiles[row].profile_id

    def _on_select(self, row: int) -> None:
        if self._updating:
            return
        self._commit_current()
        self._current_index = row
        self._load_current()

    def _load_current(self) -> None:
        if self._current_index is None or self._current_index < 0:
            return
        if self._current_index >= len(self._profiles):
            return
        self._updating = True
        profile = self._profiles[self._current_index]
        self.id_edit.setText(profile.profile_id)
        self.name_edit.setText(profile.name)
        self._load_rulesets(profile)
        self.tags_edit.setText(", ".join(profile.tags))
        self.description_edit.setPlainText(profile.description or "")
        self._updating = False

    def _commit_current(self) -> None:
        if self._updating:
            return
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            row = self.list_widget.currentRow()
            if row < 0 or row >= len(self._profiles):
                return
            self._current_index = row
        profile = self._profiles[self._current_index]
        profile_id = self.id_edit.text().strip() or profile.profile_id
        if profile_id != profile.profile_id and self._profile_id_exists(profile_id):
            QMessageBox.warning(self, "Profile ID", "Profile ID already exists.")
            profile_id = profile.profile_id
            self.id_edit.setText(profile.profile_id)
        tags = tuple(tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip())
        rulesets = self._collect_rulesets()
        active_ruleset = self._current_active_ruleset(rulesets, profile)
        updated = replace(
            profile,
            profile_id=profile_id,
            name=self.name_edit.text().strip() or profile_id,
            dataset_path=active_ruleset or profile.dataset_path,
            tags=tags,
            description=self.description_edit.toPlainText().strip() or None,
            rulesets=tuple(rulesets),
            active_ruleset=active_ruleset,
        )
        self._profiles[self._current_index] = updated
        item = self.list_widget.item(self._current_index)
        if item is not None:
            item.setText(_profile_display(updated))

    def _load_rulesets(self, profile: Profile) -> None:
        self.ruleset_list.clear()
        active_ruleset = profile.active_ruleset or profile.dataset_path
        rulesets: list[str] = []
        for path in profile.rulesets:
            if path and path not in rulesets:
                rulesets.append(path)
        for path in (profile.dataset_path, profile.active_ruleset):
            if path and path not in rulesets:
                rulesets.append(path)
        if not rulesets and active_ruleset:
            rulesets.append(active_ruleset)
        active_index = -1
        for path in rulesets:
            if not path:
                continue
            item = QListWidgetItem(self._ruleset_label(path, active_ruleset))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.ruleset_list.addItem(item)
            if path == active_ruleset:
                active_index = self.ruleset_list.count() - 1
        if active_index >= 0:
            self.ruleset_list.setCurrentRow(active_index)

    def _collect_rulesets(self) -> list[str]:
        rulesets: list[str] = []
        for idx in range(self.ruleset_list.count()):
            item = self.ruleset_list.item(idx)
            if item is None:
                continue
            path = item.data(Qt.UserRole) or item.text()
            if path and path not in rulesets:
                rulesets.append(path)
        return rulesets

    def _current_active_ruleset(self, rulesets: list[str], profile: Profile) -> Optional[str]:
        if profile.active_ruleset and profile.active_ruleset in rulesets:
            return profile.active_ruleset
        if rulesets:
            return rulesets[0]
        return None

    def _ruleset_label(self, path: str, active: Optional[str]) -> str:
        if path == active:
            return f"{path} (Active)"
        return path

    def _add_ruleset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Add Ruleset", str(self._default_dir), "JSON Files (*.json)")
        if not path:
            return
        rulesets = self._collect_rulesets()
        if path not in rulesets:
            rulesets.append(path)
        active = self._current_active_ruleset(rulesets, self._profiles[self._current_index])
        if active is None:
            active = path
        self._apply_rulesets(rulesets, active)
        self._commit_current()

    def _remove_ruleset(self) -> None:
        row = self.ruleset_list.currentRow()
        if row < 0:
            return
        self.ruleset_list.takeItem(row)
        self._commit_current()
        self._load_rulesets(self._profiles[self._current_index])

    def _set_active_ruleset(self) -> None:
        row = self.ruleset_list.currentRow()
        if row < 0:
            return
        item = self.ruleset_list.item(row)
        if item is None:
            return
        active_path = item.data(Qt.UserRole) or item.text()
        rulesets = self._collect_rulesets()
        self._apply_rulesets(rulesets, active_path)
        self._commit_current()

    def _apply_rulesets(self, rulesets: list[str], active: Optional[str]) -> None:
        self.ruleset_list.clear()
        active_index = -1
        for path in rulesets:
            item = QListWidgetItem(self._ruleset_label(path, active))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.ruleset_list.addItem(item)
            if path == active:
                active_index = self.ruleset_list.count() - 1
        if active_index >= 0:
            self.ruleset_list.setCurrentRow(active_index)

    def _ruleset_context_menu(self, position) -> None:
        item = self.ruleset_list.itemAt(position)
        if item is None:
            return
        path = item.data(Qt.UserRole) or item.text()
        menu = QMenu(self)
        reveal_action = menu.addAction("Reveal in Finder")
        action = menu.exec(self.ruleset_list.mapToGlobal(position))
        if action == reveal_action:
            _reveal_path(path)

    def _profile_context_menu(self, position) -> None:
        item = self.list_widget.itemAt(position)
        if item is None:
            return
        row = self.list_widget.row(item)
        if row < 0 or row >= len(self._profiles):
            return
        profile = self._profiles[row]
        active_path = profile.active_ruleset or profile.dataset_path
        menu = QMenu(self)
        reveal_action = menu.addAction("Reveal Ruleset in Finder")
        if not active_path:
            reveal_action.setEnabled(False)
        action = menu.exec(self.list_widget.mapToGlobal(position))
        if action == reveal_action and active_path:
            _reveal_path(active_path)

    def _profile_id_exists(self, profile_id: str) -> bool:
        return any(profile.profile_id == profile_id for profile in self._profiles)

    def _add_profile(self) -> None:
        profile_id = _next_profile_id(self._profiles)
        dataset_path = str(self._default_dir / f"{profile_id}.json")
        profile = Profile(
            profile_id=profile_id,
            name=profile_id,
            dataset_path=dataset_path,
            rulesets=(dataset_path,),
            active_ruleset=dataset_path,
        )
        self._profiles.append(profile)
        self.list_widget.addItem(_profile_display(profile))
        self.list_widget.setCurrentRow(len(self._profiles) - 1)

    def _remove_profile(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._profiles):
            return
        if len(self._profiles) <= 1:
            QMessageBox.information(self, "Profiles", "At least one profile is required.")
            return
        self._profiles.pop(row)
        self.list_widget.takeItem(row)
        if row >= len(self._profiles):
            row = len(self._profiles) - 1
        self.list_widget.setCurrentRow(row)

class RuleMetadataDialog(QDialog):
    def __init__(self, rule: VocabRule, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rule Metadata")
        self.setSizeGripEnabled(True)
        self._rule = rule

        self.label_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()
        self.examples_edit = QPlainTextEdit()
        self.notes_edit = QPlainTextEdit()
        self.source_edit = QLineEdit()

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow("Label", self.label_edit)
        form.addRow("Description", self.description_edit)
        form.addRow("Examples (one per line)", self.examples_edit)
        form.addRow("Notes", self.notes_edit)
        form.addRow("Source", self.source_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

        self._load_metadata(rule.metadata)

    def metadata(self) -> Optional[RuleMetadata]:
        label = self.label_edit.text().strip() or None
        description = self.description_edit.toPlainText().strip() or None
        examples = tuple(
            line.strip()
            for line in self.examples_edit.toPlainText().splitlines()
            if line.strip()
        )
        notes = self.notes_edit.toPlainText().strip() or None
        source = self.source_edit.text().strip() or None
        if not any([label, description, examples, notes, source]):
            return None
        return RuleMetadata(
            label=label,
            description=description,
            examples=examples,
            notes=notes,
            source=source,
        )

    def _load_metadata(self, metadata: Optional[RuleMetadata]) -> None:
        if not metadata:
            return
        self.label_edit.setText(metadata.label or "")
        self.description_edit.setPlainText(metadata.description or "")
        self.examples_edit.setPlainText("\n".join(metadata.examples))
        self.notes_edit.setPlainText(metadata.notes or "")
        self.source_edit.setText(metadata.source or "")


class CreateProfileDialog(QDialog):
    def __init__(self, default_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Profile")
        self.setSizeGripEnabled(True)
        self._default_dir = default_dir

        self.name_edit = QLineEdit()
        self.id_edit = QLineEdit()
        self.path_edit = QLineEdit()
        self.path_button = QPushButton("Browse")
        self.path_button.clicked.connect(self._browse_path)

        self.name_edit.textChanged.connect(self._sync_id)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(self.path_button)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow("Name", self.name_edit)
        form.addRow("Profile ID", self.id_edit)
        form.addRow("Ruleset Path", path_row)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

        self._sync_id()
        if not self.path_edit.text():
            self._apply_default_path()

    def profile(self) -> Profile:
        profile_id = self.id_edit.text().strip() or _slugify(self.name_edit.text()) or "profile"
        name = self.name_edit.text().strip() or profile_id
        dataset_path = self.path_edit.text().strip() or str(self._default_dir / f"{profile_id}.json")
        return Profile(
            profile_id=profile_id,
            name=name,
            dataset_path=dataset_path,
            rulesets=(dataset_path,),
            active_ruleset=dataset_path,
        )

    def _sync_id(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return
        slug = _slugify(name)
        if slug and not self.id_edit.text().strip():
            self.id_edit.setText(slug)
            self._apply_default_path()

    def _apply_default_path(self) -> None:
        profile_id = self.id_edit.text().strip() or "profile"
        self.path_edit.setText(str(self._default_dir / f"{profile_id}.json"))

    def _browse_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select Ruleset Path", str(self._default_dir), "JSON Files (*.json)")
        if not path:
            return
        self.path_edit.setText(path)


class FirstRunDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to LexiShift")
        label = QLabel(
            "Create your first profile to start managing rulesets.\n"
            "You can always add more profiles later."
        )
        label.setWordWrap(True)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(button_box)


class SettingsDialog(QDialog):
    def __init__(
        self,
        app_settings: AppSettings,
        dataset_settings: Optional[VocabSettings],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setSizeGripEnabled(True)
        self._app_settings = app_settings
        self._dataset_settings = dataset_settings or VocabSettings(
            inflections=InflectionSettings(),
            learning=LearningSettings(),
        )

        self._import_settings = app_settings.import_export or ImportExportSettings()
        inflections = self._dataset_settings.inflections or InflectionSettings()
        learning = self._dataset_settings.learning or LearningSettings()

        tabs = QTabWidget()
        tabs.addTab(self._wrap_tab(self._build_app_tab()), "App")
        tabs.addTab(self._wrap_tab(self._build_dataset_tab()), "Dataset")

        self._apply_import_export(self._import_settings)
        self._apply_inflections(inflections)
        self._apply_learning(learning)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(button_box)

    def result_app_settings(self) -> AppSettings:
        import_settings = ImportExportSettings(
            allow_code_export=self.allow_code_export_check.isChecked(),
            default_export_format=self.default_export_format.currentText(),
            last_import_path=self._import_settings.last_import_path,
            last_export_path=self._import_settings.last_export_path,
        )
        max_synonyms = _parse_int(self.max_synonyms_edit.text(), default=30)
        embedding_threshold = self.embedding_threshold_slider.value() / 100.0
        synonyms = SynonymSourceSettings(
            moby_path=self.moby_path_edit.text().strip() or None,
            wordnet_dir=self.wordnet_dir_edit.text().strip() or None,
            max_synonyms=max_synonyms,
            include_phrases=self.include_phrases_check.isChecked(),
            lower_case=self.lower_case_check.isChecked(),
            require_consensus=self.require_consensus_check.isChecked(),
            use_embeddings=self.use_embeddings_check.isChecked(),
            embedding_path=self.embedding_path_edit.text().strip() or None,
            embedding_threshold=embedding_threshold,
            embedding_fallback=self.embedding_fallback_check.isChecked(),
        )
        return replace(self._app_settings, import_export=import_settings, synonyms=synonyms)

    def result_dataset_settings(self) -> VocabSettings:
        forms = {key for key, checkbox in self._form_checks.items() if checkbox.isChecked()}
        spec = InflectionSpec(
            forms=frozenset(forms),
            apply_to=self.apply_to_combo.currentText(),
            include_original=self.include_original_check.isChecked(),
        )
        inflections = InflectionSettings(
            enabled=self.inflections_enabled_check.isChecked(),
            spec=spec,
            per_rule_spec=self._dataset_settings.inflections.per_rule_spec
            if self._dataset_settings.inflections
            else {},
            strict=self.inflections_strict_check.isChecked(),
            overrides=self._dataset_settings.inflections.overrides
            if self._dataset_settings.inflections
            else InflectionSettings().overrides,
            include_generated_tag=self.include_generated_tag_check.isChecked(),
            generated_tag=self.generated_tag_edit.text().strip() or "generated",
        )
        learning = LearningSettings(
            enabled=self.learning_enabled_check.isChecked(),
            show_original=self.show_original_check.isChecked(),
            show_original_mode=self.show_original_mode_combo.currentText(),
            highlight_replacements=self.highlight_replacements_check.isChecked(),
        )
        return VocabSettings(inflections=inflections, learning=learning)

    def _build_app_tab(self) -> QWidget:
        self.allow_code_export_check = QCheckBox("Allow export as code")
        self.default_export_format = QComboBox()
        self.default_export_format.addItems(["json", "code"])

        self.moby_path_edit = QLineEdit()
        self.wordnet_dir_edit = QLineEdit()
        self.max_synonyms_edit = QLineEdit()
        self.include_phrases_check = QCheckBox("Include multi-word synonyms")
        self.lower_case_check = QCheckBox("Lowercase synonyms")
        self.require_consensus_check = QCheckBox("Require consensus between sources")
        self.require_consensus_check.setToolTip("Only keep synonyms found in every configured source.")
        self.use_embeddings_check = QCheckBox("Rank synonyms with embeddings")
        self.embedding_path_edit = QLineEdit()
        self.embedding_browse_button = QPushButton("Browse")
        self.embedding_threshold_slider = QSlider(Qt.Horizontal)
        self.embedding_threshold_slider.setRange(0, 100)
        self.embedding_threshold_value = QLabel("0.00")
        self.embedding_fallback_check = QCheckBox("Use embeddings when no synonyms found")
        self.embedding_fallback_check.setToolTip(
            "Requires embeddings file with neighbor support (.vec/.bin or SQLite built via convert_embeddings.py)."
        )
        self.moby_browse_button = QPushButton("Browse")
        self.wordnet_browse_button = QPushButton("Browse")
        self.moby_browse_button.clicked.connect(self._browse_moby)
        self.wordnet_browse_button.clicked.connect(self._browse_wordnet)
        self.embedding_browse_button.clicked.connect(self._browse_embeddings)
        self.embedding_threshold_slider.valueChanged.connect(self._update_embedding_threshold_label)
        self.use_embeddings_check.toggled.connect(self._toggle_embedding_fields)

        moby_row = QHBoxLayout()
        moby_row.addWidget(self.moby_path_edit)
        moby_row.addWidget(self.moby_browse_button)

        wordnet_row = QHBoxLayout()
        wordnet_row.addWidget(self.wordnet_dir_edit)
        wordnet_row.addWidget(self.wordnet_browse_button)

        embedding_row = QHBoxLayout()
        embedding_row.addWidget(self.embedding_path_edit)
        embedding_row.addWidget(self.embedding_browse_button)

        threshold_row = QHBoxLayout()
        threshold_row.addWidget(self.embedding_threshold_slider, 1)
        threshold_row.addWidget(self.embedding_threshold_value)
        threshold_widget = QWidget()
        threshold_widget.setLayout(threshold_row)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow("", self.allow_code_export_check)
        form.addRow("Default export format", self.default_export_format)
        form.addRow(QLabel("Synonym sources"))
        form.addRow("Moby thesaurus", moby_row)
        form.addRow("WordNet directory", wordnet_row)
        form.addRow("Max synonyms", self.max_synonyms_edit)
        form.addRow("", self.include_phrases_check)
        form.addRow("", self.lower_case_check)
        form.addRow("", self.require_consensus_check)
        form.addRow("", self.use_embeddings_check)
        form.addRow("Embeddings file", embedding_row)
        form.addRow("Similarity threshold", threshold_widget)
        form.addRow("", self.embedding_fallback_check)

        panel = QWidget()
        panel.setLayout(form)
        return panel

    def _build_dataset_tab(self) -> QWidget:
        self.inflections_enabled_check = QCheckBox("Enable inflections")
        self.inflections_strict_check = QCheckBox("Strict inflections")
        self.include_generated_tag_check = QCheckBox("Tag generated forms")
        self.generated_tag_edit = QLineEdit()
        self.apply_to_combo = QComboBox()
        self.apply_to_combo.addItems(["last_word", "all_words"])
        self.include_original_check = QCheckBox("Include original phrase")

        self._form_checks = {
            "plural": QCheckBox("Plural"),
            "possessive": QCheckBox("Possessive"),
            "past": QCheckBox("Past"),
            "gerund": QCheckBox("Gerund"),
            "third_person": QCheckBox("Third person"),
        }

        inflection_form = QFormLayout()
        inflection_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        inflection_form.addRow("", self.inflections_enabled_check)
        inflection_form.addRow("", self.inflections_strict_check)
        inflection_form.addRow("", self.include_generated_tag_check)
        inflection_form.addRow("Generated tag", self.generated_tag_edit)
        inflection_form.addRow("Apply to", self.apply_to_combo)
        inflection_form.addRow("", self.include_original_check)
        for checkbox in self._form_checks.values():
            inflection_form.addRow("", checkbox)

        inflection_panel = QWidget()
        inflection_panel.setLayout(inflection_form)

        self.learning_enabled_check = QCheckBox("Enable learning mode")
        self.show_original_check = QCheckBox("Show original text")
        self.show_original_mode_combo = QComboBox()
        self.show_original_mode_combo.addItems(["tooltip", "inline", "side-by-side"])
        self.highlight_replacements_check = QCheckBox("Highlight replacements")

        learning_form = QFormLayout()
        learning_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        learning_form.addRow("", self.learning_enabled_check)
        learning_form.addRow("", self.show_original_check)
        learning_form.addRow("Show original mode", self.show_original_mode_combo)
        learning_form.addRow("", self.highlight_replacements_check)

        learning_panel = QWidget()
        learning_panel.setLayout(learning_form)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Inflections"))
        layout.addWidget(inflection_panel)
        layout.addWidget(QLabel("Learning"))
        layout.addWidget(learning_panel)

        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _wrap_tab(self, panel: QWidget) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(panel)
        return scroll

    def _apply_import_export(self, settings: ImportExportSettings) -> None:
        self.allow_code_export_check.setChecked(settings.allow_code_export)
        self.default_export_format.setCurrentText(settings.default_export_format)
        synonym_settings = self._app_settings.synonyms or SynonymSourceSettings()
        self.moby_path_edit.setText(synonym_settings.moby_path or "")
        self.wordnet_dir_edit.setText(synonym_settings.wordnet_dir or "")
        self.max_synonyms_edit.setText(str(synonym_settings.max_synonyms))
        self.include_phrases_check.setChecked(synonym_settings.include_phrases)
        self.lower_case_check.setChecked(synonym_settings.lower_case)
        self.require_consensus_check.setChecked(synonym_settings.require_consensus)
        self.use_embeddings_check.setChecked(synonym_settings.use_embeddings)
        self.embedding_path_edit.setText(synonym_settings.embedding_path or "")
        threshold = int(round(synonym_settings.embedding_threshold * 100))
        self.embedding_threshold_slider.setValue(max(0, min(100, threshold)))
        self._update_embedding_threshold_label(self.embedding_threshold_slider.value())
        self.embedding_fallback_check.setChecked(synonym_settings.embedding_fallback)
        self._toggle_embedding_fields(self.use_embeddings_check.isChecked())

    def _apply_inflections(self, settings: InflectionSettings) -> None:
        self.inflections_enabled_check.setChecked(settings.enabled)
        self.inflections_strict_check.setChecked(settings.strict)
        self.include_generated_tag_check.setChecked(settings.include_generated_tag)
        self.generated_tag_edit.setText(settings.generated_tag)
        self.apply_to_combo.setCurrentText(settings.spec.apply_to)
        self.include_original_check.setChecked(settings.spec.include_original)
        for key, checkbox in self._form_checks.items():
            checkbox.setChecked(key in settings.spec.forms)

    def _apply_learning(self, settings: LearningSettings) -> None:
        self.learning_enabled_check.setChecked(settings.enabled)
        self.show_original_check.setChecked(settings.show_original)
        self.show_original_mode_combo.setCurrentText(settings.show_original_mode)
        self.highlight_replacements_check.setChecked(settings.highlight_replacements)

    def _browse_moby(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Moby Thesaurus", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        self.moby_path_edit.setText(path)

    def _browse_wordnet(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select WordNet Directory")
        if not path:
            return
        self.wordnet_dir_edit.setText(path)

    def _browse_embeddings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Embeddings File",
            "",
            "Embedding Files (*.vec *.txt *.bin *.db *.sqlite *.sqlite3);;All Files (*)",
        )
        if not path:
            return
        self.embedding_path_edit.setText(path)

    def _update_embedding_threshold_label(self, value: int) -> None:
        self.embedding_threshold_value.setText(f"{value / 100:.2f}")

    def _toggle_embedding_fields(self, enabled: bool) -> None:
        self.embedding_path_edit.setEnabled(enabled)
        self.embedding_browse_button.setEnabled(enabled)
        self.embedding_threshold_slider.setEnabled(enabled)
        self.embedding_threshold_value.setEnabled(enabled)
        self.embedding_fallback_check.setEnabled(enabled)


class CodeDialog(QDialog):
    def __init__(self, title: str, *, code: str = "", read_only: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setSizeGripEnabled(True)
        self.code_edit = QPlainTextEdit()
        self.code_edit.setPlainText(code)
        self.code_edit.setReadOnly(read_only)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.code_edit)
        layout.addWidget(button_box)

        if read_only:
            button_box.button(QDialogButtonBox.Ok).setText("Close")
            button_box.button(QDialogButtonBox.Cancel).hide()

    def code(self) -> str:
        return self.code_edit.toPlainText().strip()


class BulkRulesDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Synonym Bulk Add")
        self.setSizeGripEnabled(True)

        self.targets_edit = QPlainTextEdit()
        self.targets_edit.setPlaceholderText("Paste target words (delimiters: space, comma, newline, semicolon).")

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow("Targets", self.targets_edit)
        form.addRow(QLabel("Synonyms are generated from configured WordNet/Moby sources."))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

        button_box.button(QDialogButtonBox.Ok).setText("Generate")

    def targets(self) -> list[str]:
        return _split_terms(self.targets_edit.toPlainText())

def _profile_display(profile: Profile) -> str:
    return profile.name or profile.profile_id


def _next_profile_id(profiles: list[Profile]) -> str:
    used = {profile.profile_id for profile in profiles}
    idx = 1
    while True:
        candidate = f"profile-{idx}"
        if candidate not in used:
            return candidate
        idx += 1


def _slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug


def _split_terms(text: str) -> list[str]:
    import re

    parts = re.split(r"[,\s;\t|]+", text)
    return [part.strip() for part in parts if part.strip()]


def _parse_int(value: str, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _reveal_path(path: str) -> None:
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
