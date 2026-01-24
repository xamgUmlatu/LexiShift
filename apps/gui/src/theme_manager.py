from __future__ import annotations

from PySide6.QtCore import QSettings

from theme_loader import THEME_COLOR_KEYS, load_user_themes
from theme_registry import BUILTIN_THEMES
from theme_widgets import apply_theme_background


def load_themes() -> dict[str, dict]:
    themes = dict(BUILTIN_THEMES)
    for theme_id, theme in load_user_themes().items():
        theme_label = theme_id
        merged = _merge_theme(themes.get("light_sand", {}), theme)
        merged["_name"] = str(theme.get("_name") or theme_label)
        themes[theme_id] = merged
    return themes


def current_theme_id() -> str:
    value = QSettings().value("appearance/theme", "light_sand")
    return str(value) if value else "light_sand"


def resolve_theme(theme_id: str, *, screen_id: str | None = None) -> dict:
    themes = load_themes()
    theme = themes.get(theme_id) or themes.get("light_sand", {})
    resolved = {key: theme.get(key) for key in THEME_COLOR_KEYS}
    resolved["_background"] = theme.get("_background", {})
    resolved["_background_path"] = theme.get("_background_path")
    if screen_id:
        overrides = theme.get("_screen_overrides", {})
        if isinstance(overrides, dict):
            screen = overrides.get(screen_id)
            if isinstance(screen, dict):
                colors = screen.get("colors", {})
                if isinstance(colors, dict):
                    for key, value in colors.items():
                        if key in THEME_COLOR_KEYS:
                            resolved[key] = value
                if "_background" in screen:
                    resolved["_background"] = screen.get("_background", {})
                if "_background_path" in screen:
                    resolved["_background_path"] = screen.get("_background_path")
    return resolved


def resolve_current_theme(*, screen_id: str | None = None) -> dict:
    return resolve_theme(current_theme_id(), screen_id=screen_id)


def build_base_styles(theme: dict) -> str:
    return (
        "QWidget {"
        f"color: {theme['text']};"
        "}"
        "QDialog, QMainWindow {"
        f"background: {theme['bg']};"
        "}"
        "QLabel {"
        f"color: {theme['text']};"
        "}"
        "QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {"
        f"background: {theme['table_bg']};"
        f"color: {theme['text']};"
        f"border: 1px solid {theme['panel_border']};"
        "border-radius: 6px;"
        "padding: 4px 6px;"
        "}"
        "QListWidget, QTableView {"
        f"background: {theme['table_bg']};"
        f"border: 1px solid {theme['panel_border']};"
        "}"
        "QHeaderView::section {"
        f"background: {theme['accent_soft']};"
        f"color: {theme['text']};"
        "padding: 6px;"
        "border: none;"
        "}"
        "QGroupBox {"
        f"border: 1px solid {theme['panel_border']};"
        "border-radius: 6px;"
        "margin-top: 8px;"
        "}"
        "QGroupBox::title {"
        f"color: {theme['accent']};"
        "subcontrol-origin: margin;"
        "left: 8px;"
        "padding: 0 3px;"
        "}"
        "QPushButton {"
        f"background: {theme['primary']};"
        "color: #FFFFFF;"
        "padding: 6px 12px;"
        "border-radius: 6px;"
        "}"
        "QPushButton:hover {"
        f"background: {theme['primary_hover']};"
        "}"
        "QSplitter::handle {"
        f"background: {theme['panel_border']};"
        "}"
    )


def apply_dialog_theme(dialog, container, *, screen_id: str) -> dict:
    theme = resolve_current_theme(screen_id=screen_id)
    dialog.setStyleSheet(build_base_styles(theme))
    apply_theme_background(container, theme)
    return theme


def _merge_theme(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key in THEME_COLOR_KEYS:
        if key in override:
            merged[key] = override[key]
    for key in (
        "_background",
        "_background_path",
        "_name",
        "_source",
        "_base_dir",
        "_screen_overrides",
    ):
        if key in override:
            merged[key] = override[key]
    return merged
