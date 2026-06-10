from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton  # noqa: E402

from i18n import set_locale, t  # noqa: E402
from localized_message_box import localized_question, prepare_message_box  # noqa: E402


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_localized_question_uses_catalog_button_text(monkeypatch) -> None:
    _app()
    set_locale("ja")
    observed: dict[str, str] = {}

    def inspect_dialog(dialog: QMessageBox) -> int:
        yes_button = dialog.button(QMessageBox.StandardButton.Yes)
        cancel_button = dialog.button(QMessageBox.StandardButton.Cancel)
        assert yes_button is not None
        assert cancel_button is not None
        observed["yes"] = yes_button.text()
        observed["cancel"] = cancel_button.text()
        return QMessageBox.StandardButton.Cancel.value

    monkeypatch.setattr("localized_message_box.QMessageBox.exec", inspect_dialog)

    reply = localized_question(
        None,
        "title",
        "message",
        QMessageBox.Yes | QMessageBox.Cancel,
        QMessageBox.Cancel,
    )

    assert reply == QMessageBox.Cancel
    assert observed == {
        "yes": t("buttons.yes"),
        "cancel": t("buttons.cancel"),
    }


def test_message_box_details_button_is_localized_and_themed() -> None:
    app = _app()
    set_locale("ja")

    dialog = QMessageBox()
    dialog.setText("message")
    dialog.setDetailedText("details")
    dialog.addButton(QMessageBox.StandardButton.Close)
    prepare_message_box(dialog)

    buttons = dialog.findChildren(QPushButton)
    detail_button = next(button for button in buttons if button.text() == t("buttons.show_details"))
    assert dialog.styleSheet()

    detail_button.click()
    app.processEvents()

    assert detail_button.text() == t("buttons.hide_details")
