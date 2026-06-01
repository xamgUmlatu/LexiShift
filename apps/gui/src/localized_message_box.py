from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from i18n import t


_STANDARD_BUTTON_TEXT_KEYS = {
    QMessageBox.StandardButton.Ok: "buttons.ok",
    QMessageBox.StandardButton.Yes: "buttons.yes",
    QMessageBox.StandardButton.No: "buttons.no",
    QMessageBox.StandardButton.Save: "buttons.save",
    QMessageBox.StandardButton.Discard: "buttons.discard",
    QMessageBox.StandardButton.Cancel: "buttons.cancel",
    QMessageBox.StandardButton.Close: "buttons.close",
}


def localize_standard_buttons(dialog: QMessageBox) -> None:
    for standard_button, key in _STANDARD_BUTTON_TEXT_KEYS.items():
        button = dialog.button(standard_button)
        if button is not None:
            button.setText(t(key))


def localized_question(
    parent,
    title: str,
    text: str,
    buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    default_button=QMessageBox.StandardButton.NoButton,
):
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Question)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setStandardButtons(buttons)
    if default_button != QMessageBox.StandardButton.NoButton:
        dialog.setDefaultButton(default_button)
    localize_standard_buttons(dialog)
    return QMessageBox.StandardButton(dialog.exec())
