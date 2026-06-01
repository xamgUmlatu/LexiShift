from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QPalette, QTextDocument
from PySide6.QtWidgets import QApplication, QComboBox, QFrame

import theme_manager
from preview import ReplacementHighlighter
from settings_language_packs import LanguagePackPanel
from theme_combo_popup import apply_combo_popup_theme
from theme_loader import _parse_surface_opacities
from theme_manager import (
    build_base_styles,
    readable_text_color,
    rgba_color,
    theme_surface_opacity,
)


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_language_pack_panel_status_colors_follow_theme_tokens() -> None:
    _app()
    panel = LanguagePackPanel()
    panel.set_theme(
        {
            "text": "#101112",
            "muted": "#131415",
            "status_error": "#AA0001",
            "status_info": "#0055AA",
        }
    )

    assert panel._status_color_hex("error") == "#AA0001"
    assert panel._status_color_hex("info") == "#0055AA"
    assert panel._status_color_hex("neutral") == "#101112"
    assert panel._status_color_hex("muted") == "#131415"


def test_preview_highlighter_uses_runtime_highlight_color() -> None:
    _app()
    doc = QTextDocument("sample")
    highlighter = ReplacementHighlighter(doc)
    expected = QColor("#6A8CB8")

    highlighter.set_highlight_color(expected)

    assert highlighter._format.background().color().name().lower() == expected.name().lower()


def test_readable_text_color_keeps_readable_theme_text() -> None:
    assert readable_text_color("#F0F1F2", "#222222") == "#F0F1F2"


def test_readable_text_color_falls_back_when_theme_text_lacks_contrast() -> None:
    assert readable_text_color("#222222", "#242424") == "#FFFFFF"


def test_rgba_color_resolves_theme_hex_with_alpha() -> None:
    assert rgba_color("#556677", 0.34) == "rgba(85, 102, 119, 87)"
    assert rgba_color("#334455", 56) == "rgba(51, 68, 85, 56)"
    assert rgba_color("#556677", 0.9) == "rgba(85, 102, 119, 230)"


def test_theme_surface_opacity_defaults_and_clamps() -> None:
    assert theme_surface_opacity({}, "table", default=0.9) == 0.9
    assert (
        theme_surface_opacity({"_surface_opacities": {"table": 2.0}}, "table", default=0.9) == 1.0
    )


def test_theme_loader_parses_surface_opacities() -> None:
    assert _parse_surface_opacities({"table": 0.72, "unknown": 0.1}) == {"table": 0.72}
    assert _parse_surface_opacities({"table": "not-number"}) == {}


def test_resolve_theme_applies_screen_surface_opacity_override(monkeypatch) -> None:
    monkeypatch.setattr(
        theme_manager,
        "load_user_themes",
        lambda: {
            "custom_theme": {
                "_surface_opacities": {"table": 0.82},
                "_screen_overrides": {"settings_dialog": {"_surface_opacities": {"table": 0.64}}},
            }
        },
    )

    theme = theme_manager.resolve_theme("custom_theme", screen_id="settings_dialog")

    assert theme_surface_opacity(theme, "table", default=0.9) == 0.64


def test_base_theme_styles_include_combo_popup_contract() -> None:
    styles = build_base_styles(
        {
            "bg": "#111111",
            "panel_top": "#223344",
            "panel_bottom": "#334455",
            "panel_border": "#445566",
            "table_bg": "#556677",
            "table_sel_bg": "#667788",
            "text": "#F0F1F2",
            "muted": "#C0C1C2",
            "accent": "#D0A040",
            "accent_soft": "#384858",
            "primary": "#204060",
            "primary_hover": "#305070",
        }
    )

    assert "QComboBox QAbstractItemView" in styles
    assert "background: #556677;" in styles
    assert "selection-background-color: #667788;" in styles


def test_combo_popup_theme_applies_to_actual_view_palette() -> None:
    _app()
    combo = QComboBox()
    combo.addItem("English to Spanish", "en-es")

    apply_combo_popup_theme(
        combo,
        {
            "panel_top": "#223344",
            "panel_border": "#445566",
            "table_bg": "#556677",
            "table_sel_bg": "#667788",
            "text": "#F0F1F2",
            "accent_soft": "#384858",
        },
        object_name="testPopup",
    )

    view = combo.view()

    assert view.objectName() == "testPopup"
    assert view.property("lexishiftThemedComboPopup") is True
    assert view.frameShape() == QFrame.NoFrame
    assert view.spacing() == 0
    assert view.contentsMargins().top() == 0
    assert "QListView" in view.styleSheet()
    assert "border: 0px;" in view.styleSheet()
    assert "selection-background-color: #667788;" in view.styleSheet()
    assert view.palette().color(QPalette.Base).name().upper() == "#556677"
    assert view.viewport().palette().color(QPalette.Base).name().upper() == "#556677"
