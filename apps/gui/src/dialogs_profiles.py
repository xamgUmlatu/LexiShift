from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lexishift_core import Profile, VocabDataset, save_vocab_dataset
from i18n import t
from theme_manager import apply_dialog_theme
from theme_widgets import ThemedBackgroundWidget
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
        self.resize(1220, 740)
        self._default_dir = default_dir
        self._profiles = list(profiles)
        self._initial_profile_id = self._resolve_initial_profile_id(active_profile_id)
        self._current_index: Optional[int] = None
        self._updating = False
        self._active_ruleset_override: Optional[str] = None

        self.list_widget = QListWidget()
        self._populate_profile_list()
        self.list_widget.currentRowChanged.connect(self._on_select)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._profile_context_menu)

        self.add_button = QPushButton(t("dialogs.manage_profiles.create_profile"))
        self.remove_button = QPushButton(t("dialogs.manage_profiles.delete_profile"))
        self.add_button.clicked.connect(self._add_profile)
        self.remove_button.clicked.connect(self._remove_profile)

        self.name_edit = QLineEdit()

        self.ruleset_list = QListWidget()
        self.ruleset_list.currentRowChanged.connect(self._on_ruleset_selected)

        self.ruleset_link_button = QPushButton(t("dialogs.manage_profiles.link_existing_ruleset"))
        self.ruleset_create_button = QPushButton(t("dialogs.manage_profiles.create_ruleset"))
        self.ruleset_unlink_button = QPushButton(t("dialogs.manage_profiles.unlink_ruleset"))
        self.ruleset_set_active_button = QPushButton(t("dialogs.manage_profiles.set_active_ruleset"))
        self.ruleset_reveal_button = QPushButton(t("menu.reveal_in_finder"))
        self.ruleset_link_button.clicked.connect(self._link_ruleset)
        self.ruleset_create_button.clicked.connect(self._create_ruleset)
        self.ruleset_unlink_button.clicked.connect(self._remove_ruleset)
        self.ruleset_set_active_button.clicked.connect(self._set_active_ruleset)
        self.ruleset_reveal_button.clicked.connect(self._reveal_selected_ruleset)
        self.ruleset_list.itemDoubleClicked.connect(lambda *_: self._set_active_ruleset())

        self._set_button_variant(self.add_button, "primary")
        self._set_button_variant(self.remove_button, "danger")
        self._set_button_variant(self.ruleset_link_button, "primary")
        self._set_button_variant(self.ruleset_create_button, "primary")
        self._set_button_variant(self.ruleset_unlink_button, "danger")
        self._set_button_variant(self.ruleset_set_active_button, "secondary")
        self._set_button_variant(self.ruleset_reveal_button, "secondary")

        self._set_button_size(self.add_button, "large")
        self._set_button_size(self.remove_button, "large")
        self._set_button_size(self.ruleset_link_button, "large")
        self._set_button_size(self.ruleset_create_button, "large")
        self._set_button_size(self.ruleset_unlink_button, "large")
        self._set_button_size(self.ruleset_set_active_button, "large")
        self._set_button_size(self.ruleset_reveal_button, "large")

        profile_section = QGroupBox(t("dialogs.manage_profiles.profiles_section"))
        profile_section_layout = QVBoxLayout(profile_section)
        profile_section_layout.setContentsMargins(12, 14, 12, 12)
        profile_section_layout.setSpacing(8)
        profile_section_layout.addWidget(self.list_widget, 1)

        profile_actions_row = QHBoxLayout()
        profile_actions_row.setContentsMargins(0, 0, 0, 0)
        profile_actions_row.setSpacing(8)
        profile_actions_row.addWidget(self.add_button)
        profile_actions_row.addWidget(self.remove_button)
        profile_section_layout.addLayout(profile_actions_row)
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(8)
        name_row.addWidget(QLabel(t("labels.name")))
        name_row.addWidget(self.name_edit, 1)
        profile_section_layout.addLayout(name_row)

        rulesets_section = QGroupBox(t("dialogs.manage_profiles.rulesets_section"))
        rulesets_section_layout = QVBoxLayout(rulesets_section)
        rulesets_section_layout.setContentsMargins(12, 14, 12, 12)
        rulesets_section_layout.setSpacing(8)
        rulesets_section_layout.addWidget(self.ruleset_list, 1)

        ruleset_primary_actions_row = QHBoxLayout()
        ruleset_primary_actions_row.setContentsMargins(0, 0, 0, 0)
        ruleset_primary_actions_row.setSpacing(8)
        ruleset_primary_actions_row.addWidget(self.ruleset_link_button)
        ruleset_primary_actions_row.addWidget(self.ruleset_create_button)
        rulesets_section_layout.addLayout(ruleset_primary_actions_row)

        ruleset_secondary_actions_row = QHBoxLayout()
        ruleset_secondary_actions_row.setContentsMargins(0, 0, 0, 0)
        ruleset_secondary_actions_row.setSpacing(8)
        ruleset_secondary_actions_row.addWidget(self.ruleset_set_active_button)
        ruleset_secondary_actions_row.addWidget(self.ruleset_reveal_button)
        rulesets_section_layout.addLayout(ruleset_secondary_actions_row)

        rulesets_section_layout.addWidget(self.ruleset_unlink_button)

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(12)
        main_row.addWidget(profile_section, 3)
        main_row.addWidget(rulesets_section, 5)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self._set_button_variant(button_box.button(QDialogButtonBox.Ok), "primary")
        self._set_button_variant(button_box.button(QDialogButtonBox.Cancel), "secondary")
        self._set_button_size(button_box.button(QDialogButtonBox.Ok), "large")
        self._set_button_size(button_box.button(QDialogButtonBox.Cancel), "large")

        self._theme_container = ThemedBackgroundWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._theme_container)
        layout = QVBoxLayout(self._theme_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(main_row)
        hint_label = QLabel(t("dialogs.manage_profiles.workflow_hint"))
        hint_label.setWordWrap(True)
        hint_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout.addWidget(hint_label)
        layout.addWidget(button_box)

        self.name_edit.textChanged.connect(self._commit_current)

        if self._profiles:
            initial_index = 0
            if self._initial_profile_id:
                for idx, profile in enumerate(self._profiles):
                    if profile.profile_id == self._initial_profile_id:
                        initial_index = idx
                        break
            self.list_widget.setCurrentRow(initial_index)
        else:
            self._clear_current()
        self._refresh_action_enabled_state()
        self._apply_theme()

    def _apply_theme(self) -> None:
        apply_dialog_theme(self, self._theme_container, screen_id="profiles_dialog")

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

    def _on_select(self, row: int) -> None:
        if self._updating:
            return
        previous_index = self._current_index
        if previous_index is not None and 0 <= previous_index < len(self._profiles):
            self._commit_profile(previous_index)
        if row < 0 or row >= len(self._profiles):
            self._current_index = None
            self._clear_current()
            return
        self._current_index = row
        self._load_current()
        self._refresh_action_enabled_state()

    def _load_current(self) -> None:
        if self._current_index is None or self._current_index < 0:
            return
        if self._current_index >= len(self._profiles):
            return
        self._updating = True
        profile = self._profiles[self._current_index]
        self.name_edit.setText(profile.name)
        self._load_rulesets(profile)
        self._updating = False
        self._refresh_action_enabled_state()

    def _commit_current(self) -> None:
        if self._updating:
            return
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            return
        self._commit_profile(self._current_index)

    def _commit_profile(self, index: int) -> None:
        profile = self._profiles[index]
        rulesets = self._collect_rulesets()
        active_ruleset = self._current_active_ruleset(rulesets, profile)
        updated = replace(
            profile,
            name=self.name_edit.text().strip() or profile.profile_id,
            dataset_path=active_ruleset or profile.dataset_path,
            rulesets=tuple(rulesets),
            active_ruleset=active_ruleset,
        )
        self._profiles[index] = updated
        self._refresh_profile_list_labels()
        if index == self._current_index:
            self._active_ruleset_override = active_ruleset

    def _load_rulesets(self, profile: Profile) -> None:
        rulesets: list[str] = []
        for path in profile.rulesets:
            if path and path not in rulesets:
                rulesets.append(path)
        for path in (profile.dataset_path, profile.active_ruleset):
            if path and path not in rulesets:
                rulesets.append(path)
        active_ruleset = profile.active_ruleset or profile.dataset_path
        if not rulesets and active_ruleset:
            rulesets.append(active_ruleset)
        self._apply_rulesets(rulesets, active_ruleset)

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
        if self._active_ruleset_override and self._active_ruleset_override in rulesets:
            return self._active_ruleset_override
        if profile.active_ruleset and profile.active_ruleset in rulesets:
            return profile.active_ruleset
        if rulesets:
            return rulesets[0]
        return None

    def _ruleset_label(self, path: str, active: Optional[str]) -> str:
        display_path = self._format_ruleset_display(path)
        if path == active:
            return t("ruleset.active_label", path=display_path)
        return display_path

    def _link_ruleset(self) -> None:
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.open_ruleset.title"),
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

    def _create_ruleset(self) -> None:
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialogs.add_ruleset.title"),
            str(self._default_dir),
            t("filters.json"),
        )
        if not path:
            return
        if not self._ensure_ruleset_file(path):
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
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            return
        row = self.ruleset_list.currentRow()
        if row < 0:
            return
        self.ruleset_list.takeItem(row)
        rulesets = self._collect_rulesets()
        active = self._current_active_ruleset(rulesets, self._profiles[self._current_index])
        self._apply_rulesets(rulesets, active)
        self._commit_current()

    def _set_active_ruleset(self) -> None:
        if self._current_index is None or self._current_index < 0 or self._current_index >= len(self._profiles):
            return
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

    def _on_ruleset_selected(self, _row: int) -> None:
        if self._updating:
            return
        self._refresh_action_enabled_state()

    def _apply_rulesets(self, rulesets: list[str], active: Optional[str]) -> None:
        self._active_ruleset_override = active
        unique_rulesets = [path for path in rulesets if path]
        if active and active not in unique_rulesets:
            unique_rulesets.append(active)
        if not unique_rulesets:
            self._active_ruleset_override = None
        self._updating = True
        self.ruleset_list.clear()
        active_index = -1
        for path in unique_rulesets:
            item = QListWidgetItem(self._ruleset_label(path, active))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.ruleset_list.addItem(item)
            if path == active:
                active_index = self.ruleset_list.count() - 1
        if active_index < 0 and unique_rulesets:
            active_index = 0
        if active_index >= 0:
            self.ruleset_list.setCurrentRow(active_index)
        self._updating = False
        self._refresh_action_enabled_state()

    def _selected_ruleset_path(self) -> Optional[str]:
        row = self.ruleset_list.currentRow()
        if row < 0:
            return None
        item = self.ruleset_list.item(row)
        if item is None:
            return None
        path = item.data(Qt.UserRole) or item.text()
        if not isinstance(path, str):
            return None
        return path

    def _refresh_action_enabled_state(self) -> None:
        has_profiles = bool(self._profiles)
        can_remove_profile = len(self._profiles) > 1 and self._current_index is not None
        has_ruleset = self._selected_ruleset_path() is not None
        self.remove_button.setEnabled(can_remove_profile)
        self.ruleset_link_button.setEnabled(has_profiles and self._current_index is not None)
        self.ruleset_create_button.setEnabled(has_profiles and self._current_index is not None)
        self.ruleset_unlink_button.setEnabled(has_ruleset)
        self.ruleset_set_active_button.setEnabled(has_ruleset)
        self.ruleset_reveal_button.setEnabled(has_ruleset)

    def _reveal_selected_ruleset(self) -> None:
        path = self._selected_ruleset_path()
        if not path:
            return
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

    def _clear_current(self) -> None:
        self._updating = True
        self.name_edit.clear()
        self.ruleset_list.clear()
        self._active_ruleset_override = None
        self._updating = False
        self._refresh_action_enabled_state()

    def _add_profile(self) -> None:
        self._commit_current()
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
        self.list_widget.addItem("")
        self._refresh_profile_list_labels()
        self.list_widget.setCurrentRow(len(self._profiles) - 1)
        self._refresh_action_enabled_state()

    def _remove_profile(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._profiles):
            return
        if len(self._profiles) <= 1:
            QMessageBox.information(self, t("dialogs.profiles.title"), t("dialogs.profiles.required"))
            return
        profile = self._profiles[row]
        confirm = QMessageBox.question(
            self,
            t("dialogs.profiles.title"),
            t("dialogs.manage_profiles.delete_profile_confirm", name=profile.name or profile.profile_id),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if confirm != QMessageBox.Yes:
            return
        self._commit_current()
        self._updating = True
        self.list_widget.blockSignals(True)
        removed = self._profiles.pop(row)
        self.list_widget.takeItem(row)
        if row >= len(self._profiles):
            row = len(self._profiles) - 1
        self._current_index = row if row >= 0 else None
        self.list_widget.setCurrentRow(row)
        self.list_widget.blockSignals(False)
        self._updating = False
        self._refresh_profile_list_labels()
        self._load_current()
        self._refresh_action_enabled_state()

    def _format_ruleset_display(self, path: str) -> str:
        display_name = self._ruleset_display_name(path)
        normalized = Path(os.path.abspath(os.path.expanduser(path)))
        if not normalized.exists():
            return t("ruleset.missing", label=display_name)
        return display_name

    def _ruleset_display_name(self, path: str) -> str:
        normalized = Path(os.path.abspath(os.path.expanduser(path)))
        name = normalized.stem.strip()
        if name:
            return name
        raw_name = Path(path).name
        return raw_name or path

    def _populate_profile_list(self) -> None:
        self.list_widget.clear()
        for _ in self._profiles:
            self.list_widget.addItem("")
        self._refresh_profile_list_labels()

    def _refresh_profile_list_labels(self) -> None:
        for index, profile in enumerate(self._profiles):
            item = self.list_widget.item(index)
            if item is None:
                continue
            item.setText(_profile_display(profile))

    def _resolve_initial_profile_id(self, active_profile_id: Optional[str]) -> Optional[str]:
        if not self._profiles:
            return None
        requested = str(active_profile_id or "").strip()
        if requested and any(profile.profile_id == requested for profile in self._profiles):
            return requested
        return self._profiles[0].profile_id

    def _ensure_ruleset_file(self, path: str) -> bool:
        candidate = Path(os.path.abspath(os.path.expanduser(path)))
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            if not candidate.exists():
                save_vocab_dataset(VocabDataset(), candidate)
            return True
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, t("dialogs.rulesets.title"), str(exc))
            return False

    def _set_button_variant(self, button: QPushButton | None, variant: str) -> None:
        if button is None:
            return
        button.setProperty("variant", variant)

    def _set_button_size(self, button: QPushButton | None, size: str) -> None:
        if button is None:
            return
        button.setProperty("size", size)


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

        self._theme_container = ThemedBackgroundWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._theme_container)
        layout = QVBoxLayout(self._theme_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addLayout(form)
        layout.addWidget(button_box)

        self._sync_id()
        if not self.path_edit.text():
            self._apply_default_path()
        self._apply_theme()

    def _apply_theme(self) -> None:
        apply_dialog_theme(self, self._theme_container, screen_id="profiles_dialog")

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
        self._theme_container = ThemedBackgroundWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._theme_container)
        layout = QVBoxLayout(self._theme_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(label)
        layout.addWidget(button_box)
        self._apply_theme()

    def _apply_theme(self) -> None:
        apply_dialog_theme(self, self._theme_container, screen_id="first_run_dialog")


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
