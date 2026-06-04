from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QFrame, QListView, QWidget

from theme_manager import readable_text_color

_POPUP_VIEW_PROPERTY = "lexishiftThemedComboPopup"


class ThemedComboPopupView(QListView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._popup_theme: dict = {}

    def set_popup_theme(self, theme: dict) -> None:
        self._popup_theme = dict(theme or {})
        _apply_popup_palette(self, self._popup_theme)
        _paint_popup_container_surfaces(self, self._popup_theme)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        _paint_popup_container_surfaces(self, self._popup_theme)


def apply_combo_popup_theme(combo: QComboBox, theme: dict, *, object_name: str = "") -> None:
    view = _combo_popup_view(combo)
    if object_name:
        view.setObjectName(object_name)
    if isinstance(view, ThemedComboPopupView):
        view.set_popup_theme(theme)
    else:
        _apply_popup_palette(view, theme)
        _paint_popup_container_surfaces(view, theme)
    view.setStyleSheet(combo_popup_view_style(theme))


def apply_combo_popup_theme_to_children(root: QWidget, theme: dict) -> None:
    for combo in root.findChildren(QComboBox):
        apply_combo_popup_theme(combo, theme)


def combo_popup_view_style(theme: dict) -> str:
    table_bg = _theme_hex(theme, "table_bg", "#FFFFFF")
    table_sel_bg = _theme_hex(theme, "table_sel_bg", "#E7D9C6")
    text = _theme_hex(theme, "text", "#1F2933")
    accent_soft = _theme_hex(theme, "accent_soft", "#E9D6BF")
    selection_text = readable_text_color(text, table_sel_bg)
    hover_text = readable_text_color(text, accent_soft)
    return f"""
QListView, QAbstractItemView {{
  background: {table_bg};
  color: {text};
  border: 0px;
  margin: 0px;
  padding: 0px;
  selection-background-color: {table_sel_bg};
  selection-color: {selection_text};
  outline: 0px;
}}
QListView::item, QAbstractItemView::item {{
  min-height: 24px;
  margin: 0px;
  padding: 6px 8px;
  border: 0px;
}}
QListView::item:hover, QAbstractItemView::item:hover {{
  background: {accent_soft};
  color: {hover_text};
}}
QListView::item:selected, QAbstractItemView::item:selected {{
  background: {table_sel_bg};
  color: {selection_text};
}}
"""


def _combo_popup_view(combo: QComboBox) -> QAbstractItemView:
    view = combo.view()
    if bool(view.property(_POPUP_VIEW_PROPERTY)) and isinstance(view, ThemedComboPopupView):
        return view
    object_name = view.objectName()
    replacement = ThemedComboPopupView(combo)
    replacement.setObjectName(object_name)
    replacement.setProperty(_POPUP_VIEW_PROPERTY, True)
    replacement.setUniformItemSizes(True)
    replacement.setMouseTracking(True)
    replacement.setAlternatingRowColors(False)
    replacement.setAutoFillBackground(True)
    replacement.viewport().setAutoFillBackground(True)
    replacement.setAttribute(Qt.WA_StyledBackground, True)
    replacement.viewport().setAttribute(Qt.WA_StyledBackground, True)
    replacement.setFrameShape(QFrame.NoFrame)
    replacement.setLineWidth(0)
    replacement.setMidLineWidth(0)
    replacement.setSpacing(0)
    replacement.setContentsMargins(0, 0, 0, 0)
    replacement.setViewportMargins(0, 0, 0, 0)
    combo.setView(replacement)
    return replacement


def _apply_popup_palette(view: QAbstractItemView, theme: dict) -> None:
    table_bg = QColor(_theme_hex(theme, "table_bg", "#FFFFFF"))
    table_sel_bg = QColor(_theme_hex(theme, "table_sel_bg", "#E7D9C6"))
    text = QColor(_theme_hex(theme, "text", "#1F2933"))
    selection_text = QColor(readable_text_color(text.name(), table_sel_bg.name()))
    panel_bg = QColor(_theme_hex(theme, "panel_top", table_bg.name()))

    palette = view.palette()
    palette.setColor(QPalette.Base, table_bg)
    palette.setColor(QPalette.AlternateBase, panel_bg)
    palette.setColor(QPalette.Window, table_bg)
    palette.setColor(QPalette.Button, table_bg)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Highlight, table_sel_bg)
    palette.setColor(QPalette.HighlightedText, selection_text)
    view.setPalette(palette)
    view.viewport().setPalette(palette)


def _paint_popup_container_surfaces(view: QAbstractItemView, theme: dict) -> None:
    table_bg = QColor(_theme_hex(theme, "table_bg", "#FFFFFF"))
    palette = view.palette()
    palette.setColor(QPalette.Window, table_bg)
    palette.setColor(QPalette.Base, table_bg)
    for widget in (view.parentWidget(), view.window()):
        if widget is None:
            continue
        if isinstance(widget, QComboBox):
            continue
        if not (widget.windowFlags() & Qt.Popup):
            continue
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
        widget.setStyleSheet(f"background: {table_bg.name()};")


def _theme_hex(theme: dict, key: str, fallback: str) -> str:
    value = theme.get(key) if isinstance(theme, dict) else None
    return str(value) if isinstance(value, str) and value.strip() else fallback
