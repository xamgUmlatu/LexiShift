from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from i18n import t

try:
    from language_packs import LANGUAGE_PACKS
except ImportError:  # pragma: no cover
    LANGUAGE_PACKS = []


PACK_INFO = {pack.pack_id: pack for pack in LANGUAGE_PACKS}
MONO_PACK_IDS = ("wordnet-en", "moby-en", "openthesaurus-de", "jp-wordnet")
XLANG_PACK_IDS = ("jmdict-ja-en", "cc-cedict-zh-en")


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
            button_box.button(QDialogButtonBox.Ok).setText(t("buttons.close"))
            button_box.button(QDialogButtonBox.Cancel).hide()

    def code(self) -> str:
        return self.code_edit.toPlainText().strip()


class BulkRulesDialog(QDialog):
    def __init__(self, *, default_pack_ids: set[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dialogs.bulk_add.title"))
        self.setSizeGripEnabled(True)

        self.targets_edit = QPlainTextEdit()
        self.targets_edit.setPlaceholderText(t("dialogs.bulk_add.placeholder"))
        self._pack_checkboxes: dict[str, QCheckBox] = {}
        default_pack_ids = default_pack_ids or set()

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow(t("dialogs.bulk_add.targets_label"), self.targets_edit)
        form.addRow(QLabel(t("dialogs.bulk_add.choose_dictionaries")))

        form.addRow(
            self._build_pack_group(
                t("dialogs.bulk_add.mono_group"),
                MONO_PACK_IDS,
                default_pack_ids,
            )
        )
        form.addRow(
            self._build_pack_group(
                t("dialogs.bulk_add.cross_group"),
                XLANG_PACK_IDS,
                default_pack_ids,
            )
        )

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

        button_box.button(QDialogButtonBox.Ok).setText(t("buttons.generate"))

    def selected_pack_ids(self) -> set[str]:
        return {pack_id for pack_id, checkbox in self._pack_checkboxes.items() if checkbox.isChecked()}

    def targets(self) -> list[str]:
        return _split_terms(self.targets_edit.toPlainText())

    def _build_pack_group(
        self,
        title: str,
        pack_ids: tuple[str, ...],
        default_pack_ids: set[str],
    ) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        for pack_id in pack_ids:
            pack = PACK_INFO.get(pack_id)
            label = (
                t("packs.label", name=pack.display_name(), language=pack.display_language())
                if pack
                else pack_id
            )
            checkbox = QCheckBox(label)
            checkbox.setChecked(pack_id in default_pack_ids)
            layout.addWidget(checkbox)
            self._pack_checkboxes[pack_id] = checkbox
        if not pack_ids:
            layout.addWidget(QLabel(t("dialogs.bulk_add.none_configured")))
        return group


def _split_terms(text: str) -> list[str]:
    import re

    parts = re.split(r"[,\s;\t|]+", text)
    return [part.strip() for part in parts if part.strip()]
