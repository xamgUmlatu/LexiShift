from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)


class CodeDialog(QDialog):
    def __init__(self, title: str, *, code: str = "", read_only: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setSizeGripEnabled(True)
        self.code_edit = QPlainTextEdit()
        self.code_edit.setPlainText(code)
        self.code_edit.setReadOnly(read_only)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.code_edit)
        layout.addWidget(button_box)

        if read_only:
            button_box.button(QDialogButtonBox.Ok).setText("Close")
            button_box.button(QDialogButtonBox.Cancel).hide()

    def code(self) -> str:
        return self.code_edit.toPlainText().strip()


class BulkRulesDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Synonym Bulk Add")
        self.setSizeGripEnabled(True)

        self.targets_edit = QPlainTextEdit()
        self.targets_edit.setPlaceholderText("Paste target words (delimiters: space, comma, newline, semicolon).")

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow("Targets", self.targets_edit)
        form.addRow(QLabel("Synonyms are generated from configured WordNet/Moby sources."))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

        button_box.button(QDialogButtonBox.Ok).setText("Generate")

    def targets(self) -> list[str]:
        return _split_terms(self.targets_edit.toPlainText())


def _split_terms(text: str) -> list[str]:
    import re

    parts = re.split(r"[,\s;\t|]+", text)
    return [part.strip() for part in parts if part.strip()]
