from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from dialogs_code import CodeDialog
from i18n import t
from localized_message_box import localized_question
from lexishift_core import (
    export_app_settings_code,
    export_app_settings_json,
    export_dataset_code,
    export_dataset_json,
    import_app_settings_code,
    import_app_settings_json,
    import_dataset_code,
    import_dataset_json,
)


class MainWindowImportExportMixin:
    def _save_dataset(self) -> None:
        if self.state.dataset_path is None:
            self._save_dataset_as()
            return
        self.state.save_dataset()

    def _save_dataset_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.save_ruleset_as.title"),
            self._default_export_dir(),
            t("filters.json"),
        )
        if not path:
            return
        dataset_path = Path(path)
        self.state.save_dataset(path=dataset_path)
        self._set_active_ruleset_path(dataset_path)
        self._remember_export_path(dataset_path)

    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.export_ruleset_json.title"),
            self._default_export_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = export_dataset_json(self.state.dataset)
        Path(path).write_text(payload, encoding="utf-8")
        self._remember_export_path(Path(path))

    def _export_code(self) -> None:
        payload = export_dataset_code(self.state.dataset)
        dialog = CodeDialog(
            t("dialogs.export_ruleset_code.title"), code=payload, read_only=True, parent=self
        )
        dialog.exec()

    def _export_profiles_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.export_profiles_json.title"),
            self._default_export_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = export_app_settings_json(self.state.settings)
        Path(path).write_text(payload, encoding="utf-8")
        self._remember_export_path(Path(path))

    def _export_profiles_code(self) -> None:
        payload = export_app_settings_code(self.state.settings)
        dialog = CodeDialog(
            t("dialogs.export_profiles_code.title"), code=payload, read_only=True, parent=self
        )
        dialog.exec()

    def _import_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.import_ruleset_json.title"),
            self._default_import_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        dataset = import_dataset_json(payload)
        self.state.update_dataset(dataset)
        self._remember_import_path(Path(path))

    def _import_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog(t("dialogs.import_ruleset_code.title"), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        dataset = import_dataset_code(dialog.code())
        self.state.update_dataset(dataset)

    def _import_profiles_json(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.import_profiles_json.title"),
            self._default_import_dir(),
            t("filters.json"),
        )
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        settings = import_app_settings_json(payload)
        self._apply_imported_profiles_settings(settings=settings, source_path=Path(path))

    def _import_profiles_code(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = CodeDialog(t("dialogs.import_profiles_code.title"), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        settings = import_app_settings_code(dialog.code())
        self._apply_imported_profiles_settings(settings=settings)

    def _import_profiles_from_file(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.import_profiles_json.title"),
            self._default_import_dir(),
            f"{t('filters.json')};;{t('filters.all')}",
        )
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        suffix = Path(path).suffix.lower()
        if suffix == ".py":
            settings = import_app_settings_code(payload)
        else:
            settings = import_app_settings_json(payload)
        self._apply_imported_profiles_settings(settings=settings, source_path=Path(path))

    def _apply_imported_profiles_settings(
        self, *, settings, source_path: Optional[Path] = None
    ) -> None:
        self.state.update_settings(settings)
        self._refresh_embedding_index()
        self._load_active_profile()
        if source_path is not None:
            self._remember_import_path(source_path)

    def _confirm_discard_changes(self) -> bool:
        if not self.state.dirty:
            return True
        reply = localized_question(
            self,
            t("dialogs.unsaved.title"),
            t("dialogs.unsaved.discard"),
            QMessageBox.Yes | QMessageBox.No,
        )
        return reply == QMessageBox.Yes
