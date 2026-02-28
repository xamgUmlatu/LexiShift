from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFileDialog, QMenu, QMessageBox

from dialogs_profiles import CreateProfileDialog, ProfilesDialog
from dialogs_rulesets import RulesetLibraryDialog
from i18n import t
from lexishift_core import Profile, VocabDataset
from main_paths import _app_data_dir, _default_dataset_path, _rulesets_dir
from main_profile_ruleset_service import (
    build_profile_combo_items,
    build_ruleset_combo_items,
    find_profile_by_id,
    resolve_active_profile,
)
from profile_ruleset_migration_service import migrate_profile_ruleset_paths
from profile_ruleset_utils import (
    assign_active_ruleset_to_profile,
    normalize_ruleset_path,
    preferred_active_ruleset,
    resolve_profile_dataset_path,
)


class MainWindowProfilesMixin:
    def _load_active_profile(self) -> None:
        settings = self.state.settings
        selected_profile = resolve_active_profile(settings.profiles, settings.active_profile_id)
        if selected_profile is None:
            return
        self._load_profile(selected_profile)

    def _on_empty_create_profile(self) -> None:
        self._create_profile()

    def _open_dataset(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.open_ruleset.title"),
            self._default_import_dir(),
            t("filters.json"),
        )
        if not path:
            return
        dataset_path = Path(path)
        self._set_active_ruleset_path(dataset_path)
        self.state.load_dataset(dataset_path)
        self._remember_import_path(dataset_path)

    def _manage_profiles(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = ProfilesDialog(
            profiles=self.state.settings.profiles,
            active_profile_id=self.state.settings.active_profile_id,
            default_dir=_rulesets_dir(),
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._apply_profile_collection_update(dialog.result_profiles())

    def _manage_rulesets(self) -> None:
        if not self._confirm_discard_changes():
            return
        dialog = RulesetLibraryDialog(self.state.settings.profiles, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._apply_profile_collection_update(dialog.result_profiles())

    def _apply_profile_collection_update(self, profiles: tuple[Profile, ...]) -> None:
        # Keep active profile id stable while applying dialog-managed profile/ruleset edits.
        active_id = self.state.settings.active_profile_id
        self.state.set_profiles(profiles, active_profile_id=active_id)
        self._load_active_profile()
        self._refresh_profiles_ui()

    def _create_profile(self) -> bool:
        if not self._confirm_discard_changes():
            return False
        dialog = CreateProfileDialog(default_dir=_rulesets_dir(), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        profile = dialog.profile()
        if any(existing.profile_id == profile.profile_id for existing in self.state.settings.profiles):
            QMessageBox.warning(self, t("dialogs.profile_id.title"), t("dialogs.profile_id.exists"))
            return False
        profiles = tuple(self.state.settings.profiles) + (profile,)
        self.state.set_profiles(profiles, active_profile_id=profile.profile_id)
        dataset_path = Path(profile.dataset_path)
        if not dataset_path.exists():
            self.state.update_dataset(VocabDataset())
            self.state.save_dataset(path=dataset_path)
        self._load_profile(profile)
        self._refresh_profiles_ui()
        return True

    def _load_profile(self, profile: Profile) -> None:
        settings = self.state.settings
        if settings.active_profile_id != profile.profile_id:
            self.state.set_profiles(settings.profiles, active_profile_id=profile.profile_id)
            profile = self._current_profile() or profile
        current_path = Path(self._active_ruleset_path(profile))
        resolved_path = self._resolve_profile_dataset_path(profile)
        if resolved_path != current_path:
            self._set_active_ruleset_path(resolved_path)
        self.state.load_dataset(resolved_path)

    def _active_ruleset_path(self, profile: Profile) -> str:
        return preferred_active_ruleset(profile, default_path=str(_default_dataset_path()))

    def _resolve_profile_dataset_path(self, profile: Profile) -> Path:
        return resolve_profile_dataset_path(profile, default_path=_default_dataset_path())

    def _activate_ruleset_for_profile(self, profile: Profile, path: Path) -> None:
        self._set_active_ruleset_path(path)
        self.state.load_dataset(path)

    def _set_active_ruleset_path(self, dataset_path: Path) -> None:
        settings = self.state.settings
        updated_profiles, updated = assign_active_ruleset_to_profile(
            settings.profiles,
            active_profile_id=settings.active_profile_id,
            dataset_path=dataset_path,
        )
        if updated:
            self.state.set_profiles(updated_profiles, active_profile_id=settings.active_profile_id)

    def _on_profile_selected(self, index: int) -> None:
        if self._profile_combo_updating:
            return
        profile = self.profile_combo.itemData(index)
        if profile is None:
            return
        if not self._confirm_discard_changes():
            self._refresh_profiles_ui()
            return
        self._load_profile(profile)

    def _on_ruleset_selected(self, index: int) -> None:
        if self._ruleset_combo_updating:
            return
        profile = self._current_profile()
        if profile is None:
            return
        path = self.ruleset_combo.itemData(index)
        if not path:
            return
        if not self._confirm_discard_changes():
            self._refresh_ruleset_ui()
            return
        self._activate_ruleset_for_profile(profile, Path(path))

    def _ruleset_context_menu(self, position) -> None:
        path = self.ruleset_combo.currentData()
        if not path:
            return
        menu = QMenu(self)
        reveal_action = menu.addAction(t("menu.reveal_in_finder"))
        action = menu.exec(self.ruleset_combo.mapToGlobal(position))
        if action == reveal_action:
            self._reveal_path(path)

    def _on_profiles_changed(self, profiles) -> None:
        self._refresh_profiles_ui()
        self._rebuild_profiles_menu()

    def _select_active_profile(self, *_args) -> None:
        self._refresh_profiles_ui()
        self._rebuild_profiles_menu()

    def _save_profiles(self) -> None:
        self.state.save_settings()

    def _refresh_profiles_ui(self) -> None:
        profiles = self.state.settings.profiles
        active_id = self.state.settings.active_profile_id
        combo_items, active_index = build_profile_combo_items(profiles, active_id)
        self._profile_combo_updating = True
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for combo_item in combo_items:
            self.profile_combo.addItem(combo_item.label, combo_item.profile)
        if active_index >= 0:
            self.profile_combo.setCurrentIndex(active_index)
        self.profile_combo.blockSignals(False)
        self._profile_combo_updating = False
        self._update_workspace_mode()
        self._refresh_ruleset_ui()

    def _update_workspace_mode(self) -> None:
        if not hasattr(self, "_workspace_stack"):
            return
        has_profiles = bool(self.state.settings.profiles)
        target = self._workspace_editor_page if has_profiles else self._workspace_empty_page
        if self._workspace_stack.currentWidget() is not target:
            self._workspace_stack.setCurrentWidget(target)

    def _current_profile(self) -> Optional[Profile]:
        return find_profile_by_id(self.state.settings.profiles, self.state.settings.active_profile_id)

    def _refresh_ruleset_ui(self) -> None:
        profile = self._current_profile()
        self._ruleset_combo_updating = True
        self.ruleset_combo.blockSignals(True)
        self.ruleset_combo.clear()
        if profile is None:
            self.ruleset_combo.blockSignals(False)
            self._ruleset_combo_updating = False
            if hasattr(self, "rules_table"):
                self.rules_table.set_empty_guide_button_visible(False)
            return
        combo_items, active_index = build_ruleset_combo_items(
            profile,
            default_dataset_path=str(_default_dataset_path()),
        )
        for idx, combo_item in enumerate(combo_items):
            display = combo_item.display_name
            if combo_item.missing:
                display = t("ruleset.missing", label=display)
            self.ruleset_combo.addItem(display, combo_item.path)
            self.ruleset_combo.setItemData(idx, combo_item.path, Qt.ToolTipRole)
        if active_index >= 0:
            self.ruleset_combo.setCurrentIndex(active_index)
        self.ruleset_combo.blockSignals(False)
        self._ruleset_combo_updating = False
        if hasattr(self, "_update_rules_table_help_affordance"):
            self._update_rules_table_help_affordance(profile=profile)

    def _update_rules_table_help_affordance(self, *, profile: Optional[Profile]) -> None:
        if not hasattr(self, "rules_table"):
            return
        if profile is None:
            self.rules_table.set_empty_guide_button_visible(False)
            return
        active_path = self._active_ruleset_path(profile)
        resolved_path = normalize_ruleset_path(active_path) if active_path else None
        missing_ruleset = resolved_path is None or not resolved_path.exists()
        empty_rules = self.rules_model.rowCount() == 0
        # Show contextual guidance when users have no editable rules loaded yet.
        self.rules_table.set_empty_guide_button_visible(empty_rules or missing_ruleset)

    def _migrate_ruleset_paths(self) -> None:
        settings = self.state.settings
        if not settings.profiles:
            return
        updated_profiles, changed = migrate_profile_ruleset_paths(
            settings.profiles,
            base_dir=_app_data_dir(),
            rulesets_dir=_rulesets_dir(),
        )
        if changed:
            self.state.update_settings(replace(settings, profiles=updated_profiles))
