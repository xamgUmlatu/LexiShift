from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from settings_language_packs import LanguagePackPanel


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_language_pack_failure_handler_does_not_access_embedding_only_fields() -> None:
    _app()
    panel = LanguagePackPanel()
    pack_id = next(iter(panel._language_pack_rows.keys()))
    panel._on_language_pack_failed(pack_id, "network error")
