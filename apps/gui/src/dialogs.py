from __future__ import annotations

from dataclasses import replace
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
    RuleMetadata,
    SynonymSourceSettings,
    VocabRule,
    VocabSettings,
)
from settings_language_packs import LanguagePackPanel


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
        self.setMinimumSize(900, 680)
        self.resize(980, 720)
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
        language_pack_paths = self.language_pack_panel.paths()
        wordnet_dir = language_pack_paths.get("wordnet-en")
        moby_path = language_pack_paths.get("moby-en")
        synonyms = SynonymSourceSettings(
            moby_path=moby_path.strip() if moby_path else None,
            wordnet_dir=wordnet_dir.strip() if wordnet_dir else None,
            max_synonyms=max_synonyms,
            include_phrases=self.include_phrases_check.isChecked(),
            lower_case=self.lower_case_check.isChecked(),
            require_consensus=self.require_consensus_check.isChecked(),
            use_embeddings=self.use_embeddings_check.isChecked(),
            embedding_path=self.embedding_path_edit.text().strip() or None,
            embedding_threshold=embedding_threshold,
            embedding_fallback=self.embedding_fallback_check.isChecked(),
            language_packs=language_pack_paths,
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

    def closeEvent(self, event) -> None:
        self.language_pack_panel.cancel_downloads()
        super().closeEvent(event)

    def _build_app_tab(self) -> QWidget:
        self.allow_code_export_check = QCheckBox("Allow export as code")
        self.default_export_format = QComboBox()
        self.default_export_format.addItems(["json", "code"])

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
        self.embedding_browse_button.clicked.connect(self._browse_embeddings)
        self.embedding_threshold_slider.valueChanged.connect(self._update_embedding_threshold_label)
        self.use_embeddings_check.toggled.connect(self._toggle_embedding_fields)

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
        form.setContentsMargins(12, 8, 12, 16)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.addRow("", self.allow_code_export_check)
        form.addRow("Default export format", self.default_export_format)
        form.addRow(QLabel("Synonym generation"))
        form.addRow("Max synonyms", self.max_synonyms_edit)
        form.addRow("", self.include_phrases_check)
        form.addRow("", self.lower_case_check)
        form.addRow("", self.require_consensus_check)
        form.addRow("", self.use_embeddings_check)
        form.addRow("Embeddings file", embedding_row)
        form.addRow("Similarity threshold", threshold_widget)
        form.addRow("", self.embedding_fallback_check)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._build_language_pack_panel())
        layout.addLayout(form)

        panel = QWidget()
        panel.setLayout(layout)
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
        inflection_form.setContentsMargins(12, 8, 12, 16)
        inflection_form.setHorizontalSpacing(12)
        inflection_form.setVerticalSpacing(8)
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
        learning_form.setContentsMargins(12, 8, 12, 16)
        learning_form.setHorizontalSpacing(12)
        learning_form.setVerticalSpacing(8)
        learning_form.addRow("", self.learning_enabled_check)
        learning_form.addRow("", self.show_original_check)
        learning_form.addRow("Show original mode", self.show_original_mode_combo)
        learning_form.addRow("", self.highlight_replacements_check)

        learning_panel = QWidget()
        learning_panel.setLayout(learning_form)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Inflections"))
        layout.addWidget(inflection_panel)
        layout.addWidget(QLabel("Learning"))
        layout.addWidget(learning_panel)

        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _build_language_pack_panel(self) -> QWidget:
        self.language_pack_panel = LanguagePackPanel(parent=self)
        return self.language_pack_panel

    def _wrap_tab(self, panel: QWidget) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        container.setObjectName("settingsTabContainer")
        container.setStyleSheet(
            "QWidget#settingsTabContainer {"
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #FBF8F3, stop:1 #EFE7DC);"
            "border-radius: 10px;"
            "}"
        )
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 20)
        layout.addWidget(panel)
        scroll.setWidget(container)
        return scroll

    def _apply_import_export(self, settings: ImportExportSettings) -> None:
        self.allow_code_export_check.setChecked(settings.allow_code_export)
        self.default_export_format.setCurrentText(settings.default_export_format)
        synonym_settings = self._app_settings.synonyms or SynonymSourceSettings()
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
        self.language_pack_panel.apply_synonym_settings(synonym_settings)

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


def _parse_int(value: str, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
