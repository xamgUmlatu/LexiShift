from __future__ import annotations

from PySide6.QtCore import QSettings

from theme_loader import THEME_ALL_COLOR_KEYS, load_user_themes
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
    resolved = {key: theme.get(key) for key in THEME_ALL_COLOR_KEYS}
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
                        if key in THEME_ALL_COLOR_KEYS:
                            resolved[key] = value
                if "_background" in screen:
                    resolved["_background"] = screen.get("_background", {})
                if "_background_path" in screen:
                    resolved["_background_path"] = screen.get("_background_path")
    return resolved


def resolve_current_theme(*, screen_id: str | None = None) -> dict:
    return resolve_theme(current_theme_id(), screen_id=screen_id)


def _blue_darker(hex_color: str, *, darken: float = 0.88, blue_boost: int = 16) -> str:
    raw = str(hex_color or "").strip()
    if not raw.startswith("#"):
        return raw
    token = raw[1:]
    if len(token) == 3:
        token = "".join(ch * 2 for ch in token)
    if len(token) != 6:
        return raw
    try:
        r = int(token[0:2], 16)
        g = int(token[2:4], 16)
        b = int(token[4:6], 16)
    except ValueError:
        return raw
    r = max(0, min(255, int(r * darken)))
    g = max(0, min(255, int(g * darken)))
    b = max(0, min(255, int(b * darken) + blue_boost))
    return f"#{r:02X}{g:02X}{b:02X}"


def build_base_styles(theme: dict) -> str:
    status_error = str(theme.get("status_error") or "#B42318")
    status_error_hover = "#8F1A14"
    disabled_bg = str(theme.get("status_muted") or theme["panel_border"])
    button_text = "#FFFFFF"
    ftue_badge_start = _blue_darker(theme["primary_hover"], darken=0.76, blue_boost=88)
    ftue_badge_mid = _blue_darker(theme["primary"], darken=0.76, blue_boost=88)
    ftue_badge_end = _blue_darker(theme["accent"], darken=0.76, blue_boost=88)
    return f"""
QWidget {{
  color: {theme['text']};
}}
QDialog, QMainWindow {{
  background: {theme['bg']};
}}
QLabel {{
  color: {theme['text']};
}}
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {{
  background: {theme['table_bg']};
  color: {theme['text']};
  border: 1px solid {theme['panel_border']};
  border-radius: 10px;
  padding: 7px 9px;
}}
QListWidget, QTableView {{
  background: {theme['table_bg']};
  border: 2px solid {theme['panel_border']};
  border-radius: 12px;
}}
QListWidget::item {{
  padding: 8px 10px;
  border-radius: 8px;
  margin: 2px;
}}
QListWidget::item:hover {{
  background: {theme['accent_soft']};
}}
QListWidget::item:selected {{
  background: {theme['table_sel_bg']};
  border: 1px solid {theme['accent']};
}}
QHeaderView::section {{
  background: {theme['accent_soft']};
  color: {theme['text']};
  padding: 8px;
  border: none;
}}
QGroupBox {{
  border: 2px solid {theme['panel_border']};
  border-radius: 12px;
  margin-top: 10px;
  background: {theme['panel_top']};
}}
QGroupBox::title {{
  color: {theme['accent']};
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 4px;
  font-weight: 700;
}}
QFrame[workspaceCard="true"] {{
  border: 2px solid {theme['panel_border']};
  border-radius: 12px;
  background: {theme['panel_top']};
}}
QWidget[utilityDockPanel="true"] {{
  border: 2px solid {theme['panel_border']};
  border-radius: 12px;
  background: {theme['panel_top']};
  padding: 8px;
}}
QPushButton {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['panel_top']}, stop:1 {theme['accent_soft']});
  color: {theme['text']};
  border: 2px solid {theme['panel_border']};
  border-radius: 12px;
  padding: 10px 18px;
  min-height: 28px;
  font-weight: 700;
}}
QPushButton[size="large"] {{
  min-height: 36px;
  padding: 12px 20px;
  font-size: 13px;
}}
QPushButton[dockHeader="true"] {{
  min-height: 30px;
  padding: 8px 12px;
  text-align: left;
}}
QPushButton[dockHeader="true"]:checked {{
  border: 2px solid {theme['accent']};
}}
QLabel[utilityDockBadge="true"] {{
  color: #FFFFFF;
  background: {theme['primary']};
  border: 1px solid {theme['primary_hover']};
  border-radius: 9px;
  padding: 1px 7px;
  font-weight: 700;
}}
QPushButton:hover {{
  border: 2px solid {theme['accent']};
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['table_bg']}, stop:1 {theme['panel_top']});
}}
QPushButton:pressed {{
  padding-top: 12px;
  padding-bottom: 8px;
}}
QPushButton:disabled {{
  background: {disabled_bg};
  color: {theme['muted']};
  border: 2px solid {theme['panel_border']};
}}
QPushButton[variant="primary"] {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['primary_hover']}, stop:0.55 {theme['primary']}, stop:1 {theme['accent']});
  color: {button_text};
  border: 2px solid {theme['primary_hover']};
}}
QPushButton[variant="primary"]:hover {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['primary']}, stop:1 {theme['primary_hover']});
}}
QPushButton[variant="secondary"] {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['table_bg']}, stop:1 {theme['accent_soft']});
  color: {theme['text']};
  border: 2px solid {theme['accent']};
}}
QPushButton[variant="secondary"]:hover {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['accent_soft']}, stop:1 {theme['table_bg']});
}}
QLabel[ftueLocaleIconBadge="true"] {{
  min-height: 42px;
  max-width: 56px;
  padding: 10px 0px;
  border: 2px solid {ftue_badge_mid};
  border-right: 1px solid {ftue_badge_mid};
  border-top-left-radius: 16px;
  border-bottom-left-radius: 16px;
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
  color: #FFFFFF;
  font-size: 17px;
  font-weight: 900;
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {ftue_badge_start}, stop:0.7 {ftue_badge_mid}, stop:1 {ftue_badge_end});
}}
QPushButton[ftueLocaleSelectButton="true"] {{
  min-height: 42px;
  padding: 10px 14px;
  border: 2px solid {theme['primary_hover']};
  border-left: 1px solid {theme['primary_hover']};
  border-top-left-radius: 6px;
  border-bottom-left-radius: 6px;
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 800;
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['primary_hover']}, stop:0.7 {theme['primary']}, stop:1 {theme['accent']});
}}
QPushButton[ftueLocaleSelectButton="true"]:hover {{
  border: 2px solid {theme['accent']};
  border-left: 1px solid {theme['accent']};
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme['primary']}, stop:1 {theme['primary_hover']});
}}
QPushButton[variant="danger"] {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {status_error_hover}, stop:1 {status_error});
  color: #FFFFFF;
  border: 2px solid {status_error_hover};
}}
QPushButton[variant="danger"]:hover {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {status_error}, stop:1 {status_error_hover});
}}
QSplitter::handle {{
  background: {theme['panel_border']};
}}
"""


def apply_dialog_theme(dialog, container, *, screen_id: str) -> dict:
    theme = resolve_current_theme(screen_id=screen_id)
    dialog.setStyleSheet(build_base_styles(theme))
    apply_theme_background(container, theme)
    return theme


def _merge_theme(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key in THEME_ALL_COLOR_KEYS:
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
