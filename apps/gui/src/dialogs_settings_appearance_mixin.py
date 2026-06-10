from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dialogs_theme_utils import _ThemedTabContainer, _coerce_float, _merge_theme
from i18n import available_locales, t
from theme_combo_popup import apply_combo_popup_theme_to_children
from theme_loader import load_user_themes, theme_dir
from theme_manager import build_browser_connection_styles, readable_text_color, resolve_theme
from theme_registry import BUILTIN_THEMES
from utils_paths import reveal_path


class SettingsDialogAppearanceMixin:
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

    def _wrap_tab(self, panel: QWidget) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

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
        self.language_pack_panel.set_theme(theme)
        canvas_text = readable_text_color(theme["text"], theme["bg"])
        canvas_muted = readable_text_color(theme["muted"], theme["bg"], minimum_ratio=3.8)
        canvas_accent = readable_text_color(theme["accent"], theme["bg"], minimum_ratio=3.8)
        tab_text = readable_text_color(theme["muted"], theme["panel_bottom"], minimum_ratio=3.8)
        selected_tab_text = readable_text_color(theme["text"], theme["panel_top"])
        table_text = readable_text_color(theme["text"], theme["table_bg"])
        header_text = readable_text_color(theme["text"], theme["accent_soft"])
        selection_text = readable_text_color(theme["text"], theme["table_sel_bg"])
        primary_text = readable_text_color("#FFFFFF", theme["primary"])
        background = theme.get("_background", {})
        background_path = theme.get("_background_path")
        if hasattr(self, "_tab_containers"):
            for container in self._tab_containers:
                container.set_base_style(
                    top=theme["panel_top"],
                    bottom=theme["panel_bottom"],
                    border=theme["panel_border"],
                    radius=10,
                )
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
            f"color: {canvas_text};"
            "}"
            "QLabel {"
            f"color: {canvas_text};"
            "}"
            "QLabel#settingsIntroLabel {"
            f"color: {canvas_muted};"
            "font-size: 13px;"
            "font-weight: 500;"
            "}"
            "QWidget#settingsTabContainer {"
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {theme['panel_top']}, stop:1 {theme['panel_bottom']});"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 10px;"
            "}"
            "QLabel#sectionLabel {"
            f"color: {canvas_accent};"
            "font-weight: 600;"
            "font-size: 14px;"
            "margin-top: 8px;"
            "}"
            "QTabWidget::pane {"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 8px;"
            "}"
            "QTabBar::tab {"
            f"background: {theme['panel_bottom']};"
            f"color: {tab_text};"
            "padding: 6px 12px;"
            "margin-right: 4px;"
            "border-top-left-radius: 6px;"
            "border-top-right-radius: 6px;"
            "}"
            "QTabBar::tab:selected {"
            f"background: {theme['panel_top']};"
            f"color: {selected_tab_text};"
            "}"
            "QComboBox, QLineEdit, QPlainTextEdit {"
            f"background: {theme['table_bg']};"
            f"color: {table_text};"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 6px;"
            "padding: 4px 6px;"
            "}"
            "QComboBox QAbstractItemView {"
            f"background: {theme['table_bg']};"
            f"color: {table_text};"
            f"border: 1px solid {theme['panel_border']};"
            f"selection-background-color: {theme['table_sel_bg']};"
            f"selection-color: {selection_text};"
            "outline: 0px;"
            "}"
            "QComboBox QAbstractItemView::item {"
            "min-height: 24px;"
            "padding: 6px 8px;"
            "}"
            "QComboBox QAbstractItemView::item:hover {"
            f"background: {theme['accent_soft']};"
            f"color: {readable_text_color(theme['text'], theme['accent_soft'])};"
            "}"
            "QComboBox QAbstractItemView::item:selected {"
            f"background: {theme['table_sel_bg']};"
            f"color: {selection_text};"
            "}"
            "QHeaderView::section {"
            f"background: {theme['accent_soft']};"
            f"color: {header_text};"
            "padding: 6px;"
            "border: none;"
            "}"
            "QTableWidget {"
            f"background: {theme['table_bg']};"
            f"gridline-color: {theme['panel_border']};"
            "}"
            "QTableWidget::item:selected {"
            f"background: {theme['table_sel_bg']};"
            f"color: {selection_text};"
            "}"
            "QPushButton#settingsPrimaryButton {"
            f"background: {theme['primary']};"
            f"color: {primary_text};"
            "padding: 6px 14px;"
            "border-radius: 6px;"
            "}"
            "QPushButton#settingsPrimaryButton:hover {"
            f"background: {theme['primary_hover']};"
            f"color: {readable_text_color(primary_text, theme['primary_hover'])};"
            "}"
            "QPushButton#integrationTileButton {"
            f"background: {theme['table_bg']};"
            f"color: {table_text};"
            f"border: 1px solid {theme['panel_border']};"
            "border-radius: 8px;"
            "padding: 0px;"
            "}"
            "QPushButton#integrationTileButton:hover {"
            f"background: {theme['accent_soft']};"
            f"color: {readable_text_color(table_text, theme['accent_soft'])};"
            "}"
            'QLabel[integrationTileLabel="true"] {'
            f"color: {canvas_text};"
            "font-size: 13px;"
            "font-weight: 600;"
            "}"
            f"{build_browser_connection_styles(theme)}"
        )
        apply_combo_popup_theme_to_children(self, theme)

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
