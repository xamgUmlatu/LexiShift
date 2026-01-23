from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lexishift_core import Profile
from i18n import t
from utils_paths import reveal_path


class ProfilesDialog(QDialog):
    def __init__(
        self,
        profiles: tuple[Profile, ...],
        active_profile_id: Optional[str],
        default_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dialogs.manage_profiles.title"))
        self.setSizeGripEnabled(True)
        self._default_dir = default_dir
        self._profiles = list(profiles)
        self._active_profile_id = active_profile_id
        self._current_index: Optional[int] = None
        self._updating = False

        self.list_widget = QListWidget()
        for profile in self._profiles:
            self.list_widget.addItem(_profile_display(profile))

        self.list_widget.currentRowChanged.connect(self._on_select)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._profile_context_menu)

        self.add_button = QPushButton(t("buttons.add"))
        self.remove_button = QPushButton(t("buttons.remove"))
        self.add_button.clicked.connect(self._add_profile)
        self.remove_button.clicked.connect(self._remove_profile)

        list_panel = QVBoxLayout()
        list_panel.addWidget(self.list_widget)
        list_button_row = QHBoxLayout()
        list_button_row.addWidget(self.add_button)
        list_button_row.addWidget(self.remove_button)
        list_panel.addLayout(list_button_row)

        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()

        self.ruleset_list = QListWidget()
        self.ruleset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ruleset_list.customContextMenuRequested.connect(self._ruleset_context_menu)

        self.ruleset_add_button = QPushButton(t("buttons.add_ruleset"))
        self.ruleset_remove_button = QPushButton(t("buttons.remove"))
        self.ruleset_set_active_button = QPushButton(t("buttons.set_active"))
        self.ruleset_add_button.clicked.connect(self._add_ruleset)
        self.ruleset_remove_button.clicked.connect(self._remove_ruleset)
        self.ruleset_set_active_button.clicked.connect(self._set_active_ruleset)
        self.ruleset_list.itemDoubleClicked.connect(lambda *_: self._set_active_ruleset())

        ruleset_button_row = QHBoxLayout()
        ruleset_button_row.addWidget(self.ruleset_add_button)
        ruleset_button_row.addWidget(self.ruleset_remove_button)
        ruleset_button_row.addWidget(self.ruleset_set_active_button)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow(t("labels.profile_id"), self.id_edit)
        form.addRow(t("labels.name"), self.name_edit)
        form.addRow(t("labels.rulesets"), self.ruleset_list)
        form.addRow("", ruleset_button_row)
        form.addRow(t("labels.tags_comma"), self.tags_edit)
        form.addRow(t("labels.description"), self.description_edit)

        right_panel = QWidget()
        right_panel.setLayout(form)

        main_row = QHBoxLayout()
        left_panel_widget = QWidget()
        left_panel_widget.setLayout(list_panel)
        main_row.addWidget(left_panel_widget, 1)
        main_row.addWidget(right_panel, 2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(main_row)
        hint_label = QLabel(t("dialogs.manage_profiles.active_hint"))
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        layout.addWidget(button_box)

        self.id_edit.editingFinished.connect(self._commit_current)
        self.name_edit.textChanged.connect(self._commit_current)
        self.tags_edit.editingFinished.connect(self._commit_current)
        self.description_edit.textChanged.connect(self._commit_current)

        if self._profiles:
            initial_index = 0
            if active_profile_id:
                for idx, profile in enumerate(self._profiles):
                    if profile.profile_id == active_profile_id:
                        initial_index = idx
                        break
            self.list_widget.setCurrentRow(initial_index)

    def accept(self) -> None:
        self._commit_current()
        if self._validate_profiles():
            super().accept()

    def _validate_profiles(self) -> bool:
        if not self._profiles:
            QMessageBox.warning(self, t("dialogs.profiles.title"), t("dialogs.profiles.required"))
            return False
        ids = [profile.profile_id.strip() for profile in self._profiles]
        if any(not profile_id for profile_id in ids):
            QMessageBox.warning(self, t("dialogs.profile_id.title"), t("dialogs.profile_id.empty"))
            return False
        if len(set(ids)) != len(ids):
            QMessageBox.warning(self, t("dialogs.profile_id.title"), t("dialogs.profile_id.unique"))
            return False
        for profile in self._profiles:
            if not profile.rulesets:
                QMessageBox.warning(
                    self,
                    t("dialogs.rulesets.title"),
                    t("dialogs.rulesets.required_for", name=profile.name),
                )
                return False
        return True

    def result_profiles(self) -> tuple[Profile, ...]:
        return tuple(self._profiles)

    def result_active_profile_id(self) -> Optional[str]:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._profiles):
            return None
        return self._profiles[row].profile_id

    def _on_select(self, row: int) -> None:
        if self._updating:
            return
        self._commit_current()
        self._current_index = row
        self._load_current()

    def _load_current(self) -> None:
        if self._current_index is None or self._current_index < 0:
            return
        if self._current_index >= len(self._profiles):
            return
        self._updating = True
        profile = self._profiles[self._current_index]
        self.id_edit.setText(profile.profile_id)
        self.name_edit.setText(profile.name)
        self._load_rulesets(profile)
        self.tags_edit.setText(", ".join(profile.tags))
        self.description_edit.setPlainText(profile.description or "")
        self._updating = False

    def _commit_current(self) -> None:
        if self._updating:
            return
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            row = self.list_widget.currentRow()
            if row < 0 or row >= len(self._profiles):
                return
            self._current_index = row
        profile = self._profiles[self._current_index]
        profile_id = self.id_edit.text().strip() or profile.profile_id
        if profile_id != profile.profile_id and self._profile_id_exists(profile_id):
            QMessageBox.warning(self, t("dialogs.profile_id.title"), t("dialogs.profile_id.exists"))
            profile_id = profile.profile_id
            self.id_edit.setText(profile.profile_id)
        tags = tuple(tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip())
        rulesets = self._collect_rulesets()
        active_ruleset = self._current_active_ruleset(rulesets, profile)
        updated = replace(
            profile,
            profile_id=profile_id,
            name=self.name_edit.text().strip() or profile_id,
            dataset_path=active_ruleset or profile.dataset_path,
            tags=tags,
            description=self.description_edit.toPlainText().strip() or None,
            rulesets=tuple(rulesets),
            active_ruleset=active_ruleset,
        )
        self._profiles[self._current_index] = updated
        item = self.list_widget.item(self._current_index)
        if item is not None:
            item.setText(_profile_display(updated))

    def _load_rulesets(self, profile: Profile) -> None:
        self.ruleset_list.clear()
        active_ruleset = profile.active_ruleset or profile.dataset_path
        rulesets: list[str] = []
        for path in profile.rulesets:
            if path and path not in rulesets:
                rulesets.append(path)
        for path in (profile.dataset_path, profile.active_ruleset):
            if path and path not in rulesets:
                rulesets.append(path)
        if not rulesets and active_ruleset:
            rulesets.append(active_ruleset)
        active_index = -1
        for path in rulesets:
            if not path:
                continue
            item = QListWidgetItem(self._ruleset_label(path, active_ruleset))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.ruleset_list.addItem(item)
            if path == active_ruleset:
                active_index = self.ruleset_list.count() - 1
        if active_index >= 0:
            self.ruleset_list.setCurrentRow(active_index)

    def _collect_rulesets(self) -> list[str]:
        rulesets: list[str] = []
        for idx in range(self.ruleset_list.count()):
            item = self.ruleset_list.item(idx)
            if item is None:
                continue
            path = item.data(Qt.UserRole) or item.text()
            if path and path not in rulesets:
                rulesets.append(path)
        return rulesets

    def _current_active_ruleset(self, rulesets: list[str], profile: Profile) -> Optional[str]:
        if profile.active_ruleset and profile.active_ruleset in rulesets:
            return profile.active_ruleset
        if rulesets:
            return rulesets[0]
        return None

    def _ruleset_label(self, path: str, active: Optional[str]) -> str:
        if path == active:
            return t("ruleset.active_label", path=path)
        return path

    def _add_ruleset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.add_ruleset.title"),
            str(self._default_dir),
            t("filters.json"),
        )
        if not path:
            return
        rulesets = self._collect_rulesets()
        if path not in rulesets:
            rulesets.append(path)
        active = self._current_active_ruleset(rulesets, self._profiles[self._current_index])
        if active is None:
            active = path
        self._apply_rulesets(rulesets, active)
        self._commit_current()

    def _remove_ruleset(self) -> None:
        row = self.ruleset_list.currentRow()
        if row < 0:
            return
        self.ruleset_list.takeItem(row)
        self._commit_current()
        self._load_rulesets(self._profiles[self._current_index])

    def _set_active_ruleset(self) -> None:
        row = self.ruleset_list.currentRow()
        if row < 0:
            return
        item = self.ruleset_list.item(row)
        if item is None:
            return
        active_path = item.data(Qt.UserRole) or item.text()
        rulesets = self._collect_rulesets()
        self._apply_rulesets(rulesets, active_path)
        self._commit_current()

    def _apply_rulesets(self, rulesets: list[str], active: Optional[str]) -> None:
        self.ruleset_list.clear()
        active_index = -1
        for path in rulesets:
            item = QListWidgetItem(self._ruleset_label(path, active))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.ruleset_list.addItem(item)
            if path == active:
                active_index = self.ruleset_list.count() - 1
        if active_index >= 0:
            self.ruleset_list.setCurrentRow(active_index)

    def _ruleset_context_menu(self, position) -> None:
        item = self.ruleset_list.itemAt(position)
        if item is None:
            return
        path = item.data(Qt.UserRole) or item.text()
        menu = QMenu(self)
        reveal_action = menu.addAction(t("menu.reveal_in_finder"))
        action = menu.exec(self.ruleset_list.mapToGlobal(position))
        if action == reveal_action:
            reveal_path(path)

    def _profile_context_menu(self, position) -> None:
        item = self.list_widget.itemAt(position)
        if item is None:
            return
        row = self.list_widget.row(item)
        if row < 0 or row >= len(self._profiles):
            return
        profile = self._profiles[row]
        active_path = profile.active_ruleset or profile.dataset_path
        menu = QMenu(self)
        reveal_action = menu.addAction(t("menu.reveal_ruleset_in_finder"))
        if not active_path:
            reveal_action.setEnabled(False)
        action = menu.exec(self.list_widget.mapToGlobal(position))
        if action == reveal_action and active_path:
            reveal_path(active_path)

    def _profile_id_exists(self, profile_id: str) -> bool:
        return any(profile.profile_id == profile_id for profile in self._profiles)

    def _add_profile(self) -> None:
        profile_id = _next_profile_id(self._profiles)
        dataset_path = str(self._default_dir / f"{profile_id}.json")
        profile = Profile(
            profile_id=profile_id,
            name=profile_id,
            dataset_path=dataset_path,
            rulesets=(dataset_path,),
            active_ruleset=dataset_path,
        )
        self._profiles.append(profile)
        self.list_widget.addItem(_profile_display(profile))
        self.list_widget.setCurrentRow(len(self._profiles) - 1)

    def _remove_profile(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._profiles):
            return
        if len(self._profiles) <= 1:
            QMessageBox.information(self, t("dialogs.profiles.title"), t("dialogs.profiles.required"))
            return
        self._profiles.pop(row)
        self.list_widget.takeItem(row)
        if row >= len(self._profiles):
            row = len(self._profiles) - 1
        self.list_widget.setCurrentRow(row)


class CreateProfileDialog(QDialog):
    def __init__(self, default_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dialogs.create_profile.title"))
        self.setSizeGripEnabled(True)
        self._default_dir = default_dir

        self.name_edit = QLineEdit()
        self.id_edit = QLineEdit()
        self.path_edit = QLineEdit()
        self.path_button = QPushButton(t("buttons.browse"))
        self.path_button.clicked.connect(self._browse_path)

        self.name_edit.textChanged.connect(self._sync_id)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(self.path_button)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.addRow(t("labels.name"), self.name_edit)
        form.addRow(t("labels.profile_id"), self.id_edit)
        form.addRow(t("labels.ruleset_path"), path_row)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

        self._sync_id()
        if not self.path_edit.text():
            self._apply_default_path()

    def profile(self) -> Profile:
        profile_id = self.id_edit.text().strip() or _slugify(self.name_edit.text()) or "profile"
        name = self.name_edit.text().strip() or profile_id
        dataset_path = self.path_edit.text().strip() or str(self._default_dir / f"{profile_id}.json")
        return Profile(
            profile_id=profile_id,
            name=name,
            dataset_path=dataset_path,
            rulesets=(dataset_path,),
            active_ruleset=dataset_path,
        )

    def _sync_id(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return
        slug = _slugify(name)
        if slug and not self.id_edit.text().strip():
            self.id_edit.setText(slug)
            self._apply_default_path()

    def _apply_default_path(self) -> None:
        profile_id = self.id_edit.text().strip() or "profile"
        self.path_edit.setText(str(self._default_dir / f"{profile_id}.json"))

    def _browse_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.select_ruleset_path.title"),
            str(self._default_dir),
            t("filters.json"),
        )
        if not path:
            return
        self.path_edit.setText(path)


class FirstRunDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dialogs.first_run.title"))
        label = QLabel(
            t("dialogs.first_run.message")
        )
        label.setWordWrap(True)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(button_box)


def _profile_display(profile: Profile) -> str:
    return profile.name or profile.profile_id


def _next_profile_id(profiles: list[Profile]) -> str:
    used = {profile.profile_id for profile in profiles}
    idx = 1
    while True:
        candidate = f"profile-{idx}"
        if candidate not in used:
            return candidate
        idx += 1


def _slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug
