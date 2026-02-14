from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QTextEdit

from main import MainWindow


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _first_character_color_name(editor: QTextEdit) -> str:
    cursor = QTextCursor(editor.document())
    cursor.movePosition(QTextCursor.Start)
    cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
    return cursor.charFormat().foreground().color().name().lower()


def test_append_log_defaults_to_theme_text_color() -> None:
    _app()
    dummy = SimpleNamespace(
        log_edit=QTextEdit(),
        _theme={"text": "#224466"},
    )
    dummy._theme_color_hex = (
        lambda key, fallback: MainWindow._theme_color_hex(dummy, key, fallback=fallback)
    )

    MainWindow._append_log(dummy, "hello")

    assert _first_character_color_name(dummy.log_edit) == "#224466"
