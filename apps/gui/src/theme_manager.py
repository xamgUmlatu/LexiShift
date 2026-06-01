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


# Utility used for FTUE globe badge tinting.
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


# Shared color parsing/blending + contrast helpers keep text readable across themes.
def _parse_hex_rgb(hex_color: str) -> tuple[int, int, int] | None:
    raw = str(hex_color or "").strip()
    if not raw.startswith("#"):
        return None
    token = raw[1:]
    if len(token) == 3:
        token = "".join(ch * 2 for ch in token)
    if len(token) != 6:
        return None
    try:
        return int(token[0:2], 16), int(token[2:4], 16), int(token[4:6], 16)
    except ValueError:
        return None


def _blend_hex(colors: list[str], *, fallback: str) -> str:
    parsed: list[tuple[int, int, int]] = []
    for color in colors:
        rgb = _parse_hex_rgb(color)
        if rgb is not None:
            parsed.append(rgb)
    if not parsed:
        return fallback
    r = int(sum(item[0] for item in parsed) / len(parsed))
    g = int(sum(item[1] for item in parsed) / len(parsed))
    b = int(sum(item[2] for item in parsed) / len(parsed))
    return f"#{r:02X}{g:02X}{b:02X}"


def _channel_linear(value: int) -> float:
    c = value / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str, *, fallback: float = 0.5) -> float:
    rgb = _parse_hex_rgb(hex_color)
    if rgb is None:
        return fallback
    r = _channel_linear(rgb[0])
    g = _channel_linear(rgb[1])
    b = _channel_linear(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    l1 = _relative_luminance(fg_hex)
    l2 = _relative_luminance(bg_hex)
    high = max(l1, l2)
    low = min(l1, l2)
    return (high + 0.05) / (low + 0.05)


def _best_text_color(bg_hex: str, *, light: str = "#FFFFFF", dark: str = "#0E1B2C") -> str:
    light_ratio = _contrast_ratio(light, bg_hex)
    dark_ratio = _contrast_ratio(dark, bg_hex)
    return light if light_ratio >= dark_ratio else dark


def readable_text_color(
    preferred_hex: str,
    bg_hex: str,
    *,
    minimum_ratio: float = 4.5,
    light: str = "#FFFFFF",
    dark: str = "#0E1B2C",
) -> str:
    if _contrast_ratio(preferred_hex, bg_hex) >= minimum_ratio:
        return preferred_hex
    return _best_text_color(bg_hex, light=light, dark=dark)


def rgba_color(hex_color: str, alpha: float, *, fallback: str = "#FFFFFF") -> str:
    rgb = _parse_hex_rgb(hex_color) or _parse_hex_rgb(fallback) or (255, 255, 255)
    if alpha <= 1:
        alpha_value = round(max(0.0, min(1.0, alpha)) * 255)
    else:
        alpha_value = round(max(0.0, min(255.0, alpha)))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha_value})"


def build_browser_connection_styles(theme: dict) -> str:
    configured_bg = _blend_hex(
        [theme["accent_soft"], theme["table_bg"]], fallback=theme["accent_soft"]
    )
    repair_bg = _blend_hex(
        [theme["panel_bottom"], theme["accent_soft"]], fallback=theme["panel_bottom"]
    )
    missing_bg = _blend_hex(
        [theme["panel_bottom"], theme["table_bg"]], fallback=theme["panel_bottom"]
    )
    return f"""
QScrollArea[browserConnectionsScroll="true"] {{
  background: transparent;
  border: none;
}}
QWidget[browserConnectionsCanvas="true"] {{
  background: transparent;
}}
QFrame[browserConnectionPanel="true"] {{
  border: 2px solid {theme["panel_border"]};
  border-radius: 12px;
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["panel_top"]}, stop:1 {theme["panel_bottom"]});
}}
QFrame[browserConnectionCard="true"] {{
  border: 1px solid {theme["panel_border"]};
  border-radius: 10px;
  background: {theme["table_bg"]};
}}
QLabel[browserConnectionSectionTitle="true"] {{
  color: {theme["accent"]};
  font-weight: 700;
  font-size: 14px;
  margin-top: 4px;
}}
QLabel[browserConnectionCardTitle="true"] {{
  color: {theme["text"]};
  font-weight: 700;
}}
QLabel[browserConnectionStatusBadge="true"] {{
  color: {theme["text"]};
  border: 1px solid {theme["panel_border"]};
  border-radius: 10px;
  padding: 3px 9px;
  font-weight: 600;
}}
QLabel[browserConnectionStatusBadge="true"][statusState="configured"] {{
  background: {configured_bg};
  border-color: {theme["accent"]};
}}
QLabel[browserConnectionStatusBadge="true"][statusState="needs_repair"] {{
  background: {repair_bg};
  border-color: {theme["accent"]};
}}
QLabel[browserConnectionStatusBadge="true"][statusState="not_configured"] {{
  background: {missing_bg};
}}
"""


def build_base_styles(theme: dict) -> str:
    status_error = str(theme.get("status_error") or "#B42318")
    status_error_hover = "#8F1A14"
    disabled_bg = str(theme.get("status_muted") or theme["panel_border"])
    ftue_badge_start = _blue_darker(theme["primary_hover"], darken=0.76, blue_boost=88)
    ftue_badge_mid = _blue_darker(theme["primary"], darken=0.76, blue_boost=88)
    ftue_badge_end = _blue_darker(theme["accent"], darken=0.76, blue_boost=88)
    primary_bg = _blend_hex(
        [theme["primary_hover"], theme["primary"], theme["accent"]], fallback=theme["primary"]
    )
    primary_text = _best_text_color(primary_bg)
    utility_badge_text = _best_text_color(str(theme["primary"]))
    ftue_badge_bg = _blend_hex(
        [ftue_badge_start, ftue_badge_mid, ftue_badge_end], fallback=ftue_badge_mid
    )
    ftue_badge_text = _best_text_color(ftue_badge_bg)
    empty_guide_bg = _blend_hex(
        [theme["primary_hover"], theme["primary"]], fallback=theme["primary"]
    )
    empty_guide_text = _best_text_color(empty_guide_bg)
    # Popup sheen tones for the main-window profile/ruleset dropdown list panel.
    popup_sheen_soft = _blend_hex([theme["table_bg"], "#FFFFFF"], fallback=theme["table_bg"])
    popup_sheen_hot = _blend_hex(
        [theme["table_bg"], "#FFFFFF", "#FFFFFF"], fallback=popup_sheen_soft
    )
    popup_shadow_edge = _blend_hex(
        [theme["panel_border"], theme["accent_soft"]], fallback=theme["panel_border"]
    )
    popup_hover_sheen = _blend_hex([theme["accent_soft"], "#FFFFFF"], fallback=theme["accent_soft"])
    popup_selected_sheen = _blend_hex(
        [theme["table_sel_bg"], "#FFFFFF"], fallback=theme["table_sel_bg"]
    )
    return f"""
QWidget {{
  color: {theme["text"]};
}}
QDialog, QMainWindow {{
  background: {theme["bg"]};
}}
QLabel {{
  color: {theme["text"]};
}}
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {{
  background: {theme["table_bg"]};
  color: {theme["text"]};
  border: 1px solid {theme["panel_border"]};
  border-radius: 10px;
  padding: 7px 9px;
}}
/* Main window profile/ruleset selector popup only (objectName: profileRulesetPopup). */
QAbstractItemView#profileRulesetPopup {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {popup_sheen_hot},
    stop:0.06 {popup_sheen_soft},
    stop:0.14 {theme["table_bg"]},
    stop:0.24 {popup_sheen_soft},
    stop:0.58 {theme["table_bg"]},
    stop:1 {theme["accent_soft"]});
  color: {theme["text"]};
  border-top: 2px solid {popup_sheen_soft};
  border-left: 2px solid {popup_sheen_soft};
  border-right: 2px solid {popup_shadow_edge};
  border-bottom: 2px solid {popup_shadow_edge};
  border-radius: 12px;
  padding: 5px;
  outline: 0px;
  selection-background-color: transparent;
  selection-color: {theme["text"]};
}}
QAbstractItemView#profileRulesetPopup::item {{
  min-height: 24px;
  padding: 6px 10px;
  margin: 2px;
  border-radius: 8px;
  background: transparent;
}}
QAbstractItemView#profileRulesetPopup::item:hover {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {popup_hover_sheen},
    stop:0.22 {theme["accent_soft"]},
    stop:1 {theme["table_bg"]});
  border: 1px solid {theme["panel_border"]};
}}
QAbstractItemView#profileRulesetPopup::item:selected {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {popup_selected_sheen},
    stop:0.24 {theme["table_sel_bg"]},
    stop:1 {theme["accent_soft"]});
  border: 1px solid {theme["accent"]};
}}
QListWidget, QTableView {{
  background: {theme["table_bg"]};
  border: 2px solid {theme["panel_border"]};
  border-radius: 12px;
}}
QListWidget::item {{
  padding: 8px 10px;
  border-radius: 8px;
  margin: 2px;
}}
QListWidget::item:hover {{
  background: {theme["accent_soft"]};
}}
QListWidget::item:selected {{
  background: {theme["table_sel_bg"]};
  border: 1px solid {theme["accent"]};
}}
QHeaderView::section {{
  background: {theme["accent_soft"]};
  color: {theme["text"]};
  padding: 8px;
  border: none;
}}
QGroupBox {{
  border: 2px solid {theme["panel_border"]};
  border-radius: 12px;
  margin-top: 10px;
  background: {theme["panel_top"]};
}}
QGroupBox::title {{
  color: {theme["accent"]};
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 4px;
  font-weight: 700;
}}
QFrame[workspaceCard="true"] {{
  border: 2px solid {theme["panel_border"]};
  border-radius: 12px;
  background: {theme["panel_top"]};
}}
QWidget[utilityDockPanel="true"] {{
  border: 2px solid {theme["panel_border"]};
  border-radius: 12px;
  background: {theme["panel_top"]};
  padding: 8px;
}}
QPushButton {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["panel_top"]}, stop:1 {theme["accent_soft"]});
  color: {theme["text"]};
  border: 2px solid {theme["panel_border"]};
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
  border: 2px solid {theme["accent"]};
}}
QLabel[utilityDockBadge="true"] {{
  color: {utility_badge_text};
  background: {theme["primary"]};
  border: 1px solid {theme["primary_hover"]};
  border-radius: 9px;
  padding: 1px 7px;
  font-weight: 700;
}}
QPushButton:hover {{
  border: 2px solid {theme["accent"]};
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["table_bg"]}, stop:1 {theme["panel_top"]});
}}
QPushButton:pressed {{
  padding-top: 12px;
  padding-bottom: 8px;
}}
QPushButton:disabled {{
  background: {disabled_bg};
  color: {theme["muted"]};
  border: 2px solid {theme["panel_border"]};
}}
QPushButton[variant="primary"] {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["primary_hover"]}, stop:0.55 {theme["primary"]}, stop:1 {theme["accent"]});
  color: {primary_text};
  border: 2px solid {theme["primary_hover"]};
}}
QPushButton[variant="primary"]:hover {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["primary"]}, stop:1 {theme["primary_hover"]});
}}
QPushButton[variant="secondary"] {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["table_bg"]}, stop:1 {theme["accent_soft"]});
  color: {theme["text"]};
  border: 2px solid {theme["accent"]};
}}
QPushButton[variant="secondary"]:hover {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["accent_soft"]}, stop:1 {theme["table_bg"]});
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
  color: {ftue_badge_text};
  font-size: 17px;
  font-weight: 900;
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {ftue_badge_start}, stop:0.7 {ftue_badge_mid}, stop:1 {ftue_badge_end});
}}
QPushButton[ftueLocaleSelectButton="true"] {{
  min-height: 42px;
  padding: 10px 14px;
  border: 2px solid {theme["primary_hover"]};
  border-left: 1px solid {theme["primary_hover"]};
  border-top-left-radius: 6px;
  border-bottom-left-radius: 6px;
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
  color: {primary_text};
  font-size: 13px;
  font-weight: 800;
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["primary_hover"]}, stop:0.7 {theme["primary"]}, stop:1 {theme["accent"]});
}}
QPushButton[ftueLocaleSelectButton="true"]:hover {{
  border: 2px solid {theme["accent"]};
  border-left: 1px solid {theme["accent"]};
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["primary"]}, stop:1 {theme["primary_hover"]});
}}
QPushButton[emptyGuideFab="true"] {{
  min-width: 28px;
  max-width: 28px;
  min-height: 28px;
  max-height: 28px;
  padding: 0px;
  border-radius: 14px;
  color: {empty_guide_text};
  font-size: 16px;
  font-weight: 900;
  border: 2px solid {theme["accent"]};
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["primary_hover"]}, stop:1 {theme["primary"]});
}}
QPushButton[emptyGuideFab="true"]:hover {{
  border: 2px solid {theme["primary_hover"]};
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {theme["primary"]}, stop:1 {theme["primary_hover"]});
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
  background: {theme["panel_border"]};
}}
{build_browser_connection_styles(theme)}
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
