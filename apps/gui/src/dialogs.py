from __future__ import annotations

from dataclasses import replace
from typing import Optional

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtGui import QPainter, QPixmap
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
from i18n import available_locales, t
from settings_language_packs import LanguagePackPanel
from theme_loader import load_user_themes, theme_dir, THEME_COLOR_KEYS
from theme_manager import resolve_theme
from theme_registry import BUILTIN_THEMES
from utils_paths import reveal_path
from integrations import open_integration_link


class RuleMetadataDialog(QDialog):
    def __init__(self, rule: VocabRule, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dialogs.rule_metadata.title"))
        self.setSizeGripEnabled(True)
        self._rule = rule

        self.label_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()
        self.examples_edit = QPlainTextEdit()
        self.notes_edit = QPlainTextEdit()
        self.source_edit = QLineEdit()

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow(t("dialogs.rule_metadata.label"), self.label_edit)
        form.addRow(t("dialogs.rule_metadata.description"), self.description_edit)
        form.addRow(t("dialogs.rule_metadata.examples"), self.examples_edit)
        form.addRow(t("dialogs.rule_metadata.notes"), self.notes_edit)
        form.addRow(t("dialogs.rule_metadata.source"), self.source_edit)

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
        self.setWindowTitle(t("dialogs.settings.title"))
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
        self._ui_settings = QSettings()
        self._themes, self._theme_labels = self._load_themes()
        theme_id = self._ui_settings.value("appearance/theme", "light_sand")
        theme_id = theme_id if theme_id in self._themes else "light_sand"
        self._theme_id = theme_id
        self._theme = self._themes[self._theme_id]
        locale_pref = self._ui_settings.value("appearance/locale", "system")
        self._locale_pref = str(locale_pref) if locale_pref is not None else "system"
        tabs = QTabWidget()
        tabs.addTab(self._wrap_tab(self._build_app_tab()), t("tabs.app"))
        tabs.addTab(self._wrap_tab(self._build_appearance_tab()), t("tabs.appearance"))
        tabs.addTab(self._wrap_tab(self._build_dataset_tab()), t("tabs.dataset"))
        tabs.addTab(self._wrap_tab(self._build_integrations_tab()), t("tabs.integrations"))

        self._apply_import_export(self._import_settings)
        self._apply_inflections(inflections)
        self._apply_learning(learning)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(button_box)
        self._apply_theme()

    def result_app_settings(self) -> AppSettings:
        export_format = self.default_export_format.currentData()
        export_format = export_format or self.default_export_format.currentText()
        import_settings = ImportExportSettings(
            allow_code_export=self.allow_code_export_check.isChecked(),
            default_export_format=str(export_format),
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
            apply_to=str(self.apply_to_combo.currentData() or self.apply_to_combo.currentText()),
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
            show_original_mode=str(self.show_original_mode_combo.currentData() or self.show_original_mode_combo.currentText()),
            highlight_replacements=self.highlight_replacements_check.isChecked(),
        )
        return VocabSettings(inflections=inflections, learning=learning)

    def closeEvent(self, event) -> None:
        self.language_pack_panel.cancel_downloads()
        super().closeEvent(event)

    def _build_appearance_tab(self) -> QWidget:
        self.theme_combo = QComboBox()
        for theme_id, label in self._theme_labels.items():
            self.theme_combo.addItem(label, theme_id)
        self._set_theme_combo(self._theme_id)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        self.open_themes_button = QPushButton(t("buttons.open_themes_folder"))
        self.open_themes_button.clicked.connect(self._open_themes_folder)

        self.language_combo = QComboBox()
        self.language_combo.addItem(t("appearance.language.system_default"), "system")
        for locale, label in sorted(available_locales().items(), key=lambda item: item[1].lower()):
            self.language_combo.addItem(label, locale)
        self._set_language_combo(self._locale_pref)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setContentsMargins(12, 8, 12, 16)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.addRow(t("appearance.theme.label"), self.theme_combo)
        form.addRow(t("appearance.themes_folder.label"), self.open_themes_button)
        form.addRow(t("appearance.language.label"), self.language_combo)
        form.addRow(QLabel(t("appearance.hint")))

        panel = QWidget()
        panel.setLayout(form)
        return panel

    def _open_themes_folder(self) -> None:
        reveal_path(theme_dir())

    def _build_app_tab(self) -> QWidget:
        self.allow_code_export_check = QCheckBox(t("settings.allow_code_export"))
        self.default_export_format = QComboBox()
        self.default_export_format.addItem(t("formats.json"), "json")
        self.default_export_format.addItem(t("formats.code"), "code")

        self.max_synonyms_edit = QLineEdit()
        self.include_phrases_check = QCheckBox(t("settings.include_phrases"))
        self.lower_case_check = QCheckBox(t("settings.lower_case"))
        self.require_consensus_check = QCheckBox(t("settings.require_consensus"))
        self.require_consensus_check.setToolTip(t("settings.require_consensus_tip"))
        self.use_embeddings_check = QCheckBox(t("settings.use_embeddings"))
        self.embedding_path_edit = QLineEdit()
        self.embedding_browse_button = QPushButton(t("buttons.browse"))
        self.embedding_threshold_slider = QSlider(Qt.Horizontal)
        self.embedding_threshold_slider.setRange(0, 100)
        self.embedding_threshold_value = QLabel("0.00")
        self.embedding_fallback_check = QCheckBox(t("settings.embedding_fallback"))
        self.embedding_fallback_check.setToolTip(
            t("settings.embedding_fallback_tip")
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
        form.addRow(t("settings.default_export_format"), self.default_export_format)
        synonym_label = QLabel(t("settings.synonym_generation"))
        synonym_label.setObjectName("sectionLabel")
        form.addRow(synonym_label)
        form.addRow(t("settings.max_synonyms"), self.max_synonyms_edit)
        form.addRow("", self.include_phrases_check)
        form.addRow("", self.lower_case_check)
        form.addRow("", self.require_consensus_check)
        form.addRow("", self.use_embeddings_check)
        form.addRow(t("settings.embeddings_file"), embedding_row)
        form.addRow(t("settings.similarity_threshold"), threshold_widget)
        form.addRow("", self.embedding_fallback_check)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._build_language_pack_panel())
        layout.addLayout(form)

        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _build_integrations_tab(self) -> QWidget:
        title = QLabel(t("integrations.title"))
        title.setObjectName("sectionLabel")
        description = QLabel(t("integrations.description"))
        description.setWordWrap(True)

        app_button = QPushButton(t("integrations.app_button"))
        extension_button = QPushButton(t("integrations.extension_button"))
        plugin_button = QPushButton(t("integrations.plugin_button"))

        app_button.clicked.connect(lambda: open_integration_link("app_download"))
        extension_button.clicked.connect(lambda: open_integration_link("chrome_extension"))
        plugin_button.clicked.connect(lambda: open_integration_link("betterdiscord_plugin"))

        buttons = QHBoxLayout()
        buttons.addWidget(app_button)
        buttons.addWidget(extension_button)
        buttons.addWidget(plugin_button)
        buttons.addStretch()

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(buttons)
        layout.addStretch()

        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _build_dataset_tab(self) -> QWidget:
        self.inflections_enabled_check = QCheckBox(t("settings.inflections_enabled"))
        self.inflections_strict_check = QCheckBox(t("settings.inflections_strict"))
        self.include_generated_tag_check = QCheckBox(t("settings.include_generated_tag"))
        self.generated_tag_edit = QLineEdit()
        self.apply_to_combo = QComboBox()
        self.apply_to_combo.addItem(t("inflections.apply_last_word"), "last_word")
        self.apply_to_combo.addItem(t("inflections.apply_all_words"), "all_words")
        self.include_original_check = QCheckBox(t("settings.include_original"))

        self._form_checks = {
            "plural": QCheckBox(t("inflections.forms.plural")),
            "possessive": QCheckBox(t("inflections.forms.possessive")),
            "past": QCheckBox(t("inflections.forms.past")),
            "gerund": QCheckBox(t("inflections.forms.gerund")),
            "third_person": QCheckBox(t("inflections.forms.third_person")),
        }

        inflection_form = QFormLayout()
        inflection_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        inflection_form.setContentsMargins(12, 8, 12, 16)
        inflection_form.setHorizontalSpacing(12)
        inflection_form.setVerticalSpacing(8)
        inflection_form.addRow("", self.inflections_enabled_check)
        inflection_form.addRow("", self.inflections_strict_check)
        inflection_form.addRow("", self.include_generated_tag_check)
        inflection_form.addRow(t("inflections.generated_tag"), self.generated_tag_edit)
        inflection_form.addRow(t("inflections.apply_to"), self.apply_to_combo)
        inflection_form.addRow("", self.include_original_check)
        for checkbox in self._form_checks.values():
            inflection_form.addRow("", checkbox)

        inflection_panel = QWidget()
        inflection_panel.setLayout(inflection_form)

        self.learning_enabled_check = QCheckBox(t("settings.learning_enabled"))
        self.show_original_check = QCheckBox(t("settings.show_original"))
        self.show_original_mode_combo = QComboBox()
        self.show_original_mode_combo.addItem(t("learning.mode.tooltip"), "tooltip")
        self.show_original_mode_combo.addItem(t("learning.mode.inline"), "inline")
        self.show_original_mode_combo.addItem(t("learning.mode.side_by_side"), "side-by-side")
        self.highlight_replacements_check = QCheckBox(t("settings.highlight_replacements"))

        learning_form = QFormLayout()
        learning_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        learning_form.setContentsMargins(12, 8, 12, 16)
        learning_form.setHorizontalSpacing(12)
        learning_form.setVerticalSpacing(8)
        learning_form.addRow("", self.learning_enabled_check)
        learning_form.addRow("", self.show_original_check)
        learning_form.addRow(t("learning.show_original_mode"), self.show_original_mode_combo)
        learning_form.addRow("", self.highlight_replacements_check)

        learning_panel = QWidget()
        learning_panel.setLayout(learning_form)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        inflections_label = QLabel(t("settings.inflections_section"))
        inflections_label.setObjectName("sectionLabel")
        layout.addWidget(inflections_label)
        layout.addWidget(inflection_panel)
        learning_label = QLabel(t("settings.learning_section"))
        learning_label.setObjectName("sectionLabel")
        layout.addWidget(learning_label)
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

        container = _ThemedTabContainer()
        container.setObjectName("settingsTabContainer")
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 20)
        layout.addWidget(panel)
        scroll.setWidget(container)
        if not hasattr(self, "_tab_containers"):
            self._tab_containers = []
        self._tab_containers.append(container)
        return scroll

    def _apply_theme(self) -> None:
        theme = resolve_theme(self._theme_id, screen_id="settings_dialog")
        background = theme.get("_background", {})
        background_path = theme.get("_background_path")
        if hasattr(self, "_tab_containers"):
            for container in self._tab_containers:
                container.set_background(
                    image_path=background_path,
                    opacity=_coerce_float(background.get("opacity"), default=1.0),
                    position=str(background.get("position") or "center"),
                    size=str(background.get("size") or "cover"),
                    repeat=str(background.get("repeat") or "no-repeat"),
                )
        self.setStyleSheet(
            "QDialog {"
            f"background: {theme['bg']};"
            f"color: {theme['text']};"
            "}"
            "QLabel {"
            f"color: {theme['text']};"
            "}"
            "QWidget#settingsTabContainer {"
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {theme['panel_top']}, stop:1 {theme['panel_bottom']});"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 10px;"
            "}"
            "QLabel#sectionLabel {"
            f"color: {theme['accent']};"
            "font-weight: 600;"
            "font-size: 13px;"
            "margin-top: 8px;"
            "}"
            "QTabWidget::pane {"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 8px;"
            "}"
            "QTabBar::tab {"
            f"background: {theme['panel_bottom']};"
            f"color: {theme['muted']};"
            "padding: 6px 12px;"
            "margin-right: 4px;"
            "border-top-left-radius: 6px;"
            "border-top-right-radius: 6px;"
            "}"
            "QTabBar::tab:selected {"
            f"background: {theme['panel_top']};"
            f"color: {theme['text']};"
            "}"
            "QComboBox, QLineEdit, QPlainTextEdit {"
            f"background: {theme['table_bg']};"
            f"color: {theme['text']};"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 6px;"
            "padding: 4px 6px;"
            "}"
            "QHeaderView::section {"
            f"background: {theme['accent_soft']};"
            f"color: {theme['text']};"
            "padding: 6px;"
            "border: none;"
            "}"
            "QTableWidget {"
            f"background: {theme['table_bg']};"
            f"gridline-color: {theme['panel_border']};"
            "}"
            "QTableWidget::item:selected {"
            f"background: {theme['table_sel_bg']};"
            f"color: {theme['text']};"
            "}"
            "QPushButton#settingsPrimaryButton {"
            f"background: {theme['primary']};"
            "color: #FFFFFF;"
            "padding: 6px 14px;"
            "border-radius: 6px;"
            "}"
            "QPushButton#settingsPrimaryButton:hover {"
            f"background: {theme['primary_hover']};"
            "}"
        )

    def _apply_import_export(self, settings: ImportExportSettings) -> None:
        self.allow_code_export_check.setChecked(settings.allow_code_export)
        self._set_combo_value(self.default_export_format, settings.default_export_format)
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

    def _browse_embeddings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.select_embeddings.title"),
            "",
            t("filters.embeddings"),
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

    def _apply_inflections(self, settings: InflectionSettings) -> None:
        self.inflections_enabled_check.setChecked(settings.enabled)
        self.inflections_strict_check.setChecked(settings.strict)
        self.include_generated_tag_check.setChecked(settings.include_generated_tag)
        self.generated_tag_edit.setText(settings.generated_tag)
        self._set_combo_value(self.apply_to_combo, settings.spec.apply_to)
        self.include_original_check.setChecked(settings.spec.include_original)
        for key, checkbox in self._form_checks.items():
            checkbox.setChecked(key in settings.spec.forms)

    def _apply_learning(self, settings: LearningSettings) -> None:
        self.learning_enabled_check.setChecked(settings.enabled)
        self.show_original_check.setChecked(settings.show_original)
        self._set_combo_value(self.show_original_mode_combo, settings.show_original_mode)
        self.highlight_replacements_check.setChecked(settings.highlight_replacements)

    def _on_theme_changed(self) -> None:
        theme_id = self.theme_combo.currentData()
        if not theme_id or theme_id not in self._themes:
            return
        self._theme_id = theme_id
        self._theme = self._themes[theme_id]
        self._ui_settings.setValue("appearance/theme", theme_id)
        self._apply_theme()

    def _on_language_changed(self) -> None:
        locale = self.language_combo.currentData()
        if not locale:
            return
        self._ui_settings.setValue("appearance/locale", str(locale))

    def _set_theme_combo(self, theme_id: str) -> None:
        for idx in range(self.theme_combo.count()):
            if self.theme_combo.itemData(idx) == theme_id:
                self.theme_combo.setCurrentIndex(idx)
                return

    def _set_language_combo(self, locale: str) -> None:
        self._set_combo_value(self.language_combo, locale or "system")

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        for idx in range(combo.count()):
            if combo.itemData(idx) == value or combo.itemText(idx) == value:
                combo.setCurrentIndex(idx)
                return

    def _load_themes(self) -> tuple[dict[str, dict], dict[str, str]]:
        themes = dict(BUILTIN_THEMES)
        labels = {
            "light_sand": t("appearance.theme.light_sand"),
            "chalk": t("appearance.theme.chalk"),
            "dusk": t("appearance.theme.dusk"),
            "night_slate": t("appearance.theme.night_slate"),
        }
        for theme_id, theme in load_user_themes().items():
            theme_label = str(theme.get("_name") or theme_id)
            themes[theme_id] = _merge_theme(themes.get("light_sand", {}), theme)
            labels[theme_id] = theme_label
        return themes, labels


class _ThemedTabContainer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._bg_pixmap: QPixmap | None = None
        self._bg_opacity = 1.0
        self._bg_position = "center"
        self._bg_size = "cover"
        self._bg_repeat = "no-repeat"

    def set_background(
        self,
        *,
        image_path: str | None,
        opacity: float,
        position: str,
        size: str,
        repeat: str,
    ) -> None:
        if image_path:
            pixmap = QPixmap(image_path)
            self._bg_pixmap = pixmap if not pixmap.isNull() else None
        else:
            self._bg_pixmap = None
        self._bg_opacity = max(0.0, min(1.0, opacity))
        self._bg_position = position
        self._bg_size = size
        self._bg_repeat = repeat
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._bg_pixmap:
            return
        painter = QPainter(self)
        painter.setOpacity(self._bg_opacity)
        rect = self.rect()
        if self._bg_repeat == "repeat":
            painter.drawTiledPixmap(rect, self._bg_pixmap)
            return
        target = _scale_pixmap(self._bg_pixmap, rect.size(), self._bg_size)
        pos = _position_pixmap(rect, target.size(), self._bg_position)
        painter.drawPixmap(pos, target)


def _merge_theme(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key in THEME_COLOR_KEYS:
        if key in override:
            merged[key] = override[key]
    for key in ("_background", "_background_path", "_name", "_source", "_base_dir", "_screen_overrides"):
        if key in override:
            merged[key] = override[key]
    return merged


def _scale_pixmap(pixmap: QPixmap, target_size, mode: str) -> QPixmap:
    if mode == "contain":
        return pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if mode == "cover":
        return pixmap.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    if mode.endswith("%"):
        try:
            pct = max(1, min(100, int(mode[:-1])))
        except ValueError:
            return pixmap
        w = int(target_size.width() * pct / 100)
        h = int(target_size.height() * pct / 100)
        return pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pixmap


def _position_pixmap(rect, size, position: str) -> QPoint:
    pos = position.lower().split()
    if not pos:
        pos = ["center"]
    if "left" in pos:
        x = rect.left()
    elif "right" in pos:
        x = rect.right() - size.width()
    else:
        x = rect.center().x() - size.width() // 2
    if "top" in pos:
        y = rect.top()
    elif "bottom" in pos:
        y = rect.bottom() - size.height()
    else:
        y = rect.center().y() - size.height() // 2
    return QPoint(int(x), int(y))


def _coerce_float(value, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: str, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
