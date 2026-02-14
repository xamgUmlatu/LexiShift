from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QTextDocument
from PySide6.QtWidgets import QApplication

from preview import ReplacementHighlighter
from settings_language_packs import LanguagePackPanel


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
