from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lexishift_core import Profile, load_vocab_dataset
from i18n import t
from profile_ruleset_utils import (
    collect_profile_rulesets,
    normalize_ruleset_path,
    profile_ruleset_paths,
    ruleset_display_name,
)
from ruleset_library_service import (
    analyze_ruleset_delete_impact,
    delete_ruleset_file,
    unlink_ruleset_from_library,
)
from ruleset_preview_service import build_ruleset_preview_lines
from theme_manager import apply_dialog_theme
from theme_widgets import ThemedBackgroundWidget
from utils_paths import reveal_path


class RulesetLibraryDialog(QDialog):
    def __init__(self, profiles: tuple[Profile, ...], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dialogs.manage_rulesets.title"))
        self.setSizeGripEnabled(True)
        self.resize(980, 640)
        self._profiles = list(profiles)
        self._ruleset_paths: list[str] = []

        self.list_title_label = QLabel(t("dialogs.manage_rulesets.list_title"))
        self.ruleset_list = QListWidget()
        self.ruleset_list.currentRowChanged.connect(self._on_select)

        self.preview_title_label = QLabel(t("dialogs.manage_rulesets.preview_title"))
        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.rules_count_label = QLabel("")
        self.rules_count_label.setWordWrap(True)
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.rules_preview = QPlainTextEdit()
        self.rules_preview.setReadOnly(True)
        self.rules_preview.setPlaceholderText(t("dialogs.manage_rulesets.no_selection"))

        self.reveal_button = QPushButton(t("menu.reveal_in_finder"))
        self.delete_button = QPushButton(t("buttons.delete_ruleset_file"))
        self.reveal_button.clicked.connect(self._reveal_selected)
        self.delete_button.clicked.connect(self._delete_selected_ruleset)
        self._set_button_variant(self.reveal_button, "secondary")
        self._set_button_variant(self.delete_button, "danger")

        action_row = QHBoxLayout()
        action_row.addWidget(self.reveal_button)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.list_title_label)
        left_layout.addWidget(self.ruleset_list, 1)
        left_layout.addLayout(action_row)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.addWidget(self.preview_title_label)
        right_layout.addWidget(self.path_label)
        right_layout.addWidget(self.rules_count_label)
        right_layout.addWidget(self.details_label)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.rules_preview, 1)

        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(12)
        body_row.addWidget(left_panel, 2)
        body_row.addWidget(right_panel, 3)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        close_button = button_box.button(QDialogButtonBox.Ok)
        if close_button is not None:
            close_button.setText(t("buttons.close"))
        self._set_button_variant(close_button, "primary")

        self._theme_container = ThemedBackgroundWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._theme_container)
        layout = QVBoxLayout(self._theme_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(body_row, 1)
        layout.addWidget(button_box)

        self._refresh_rulesets()
        self._apply_theme()

    def _apply_theme(self) -> None:
        apply_dialog_theme(self, self._theme_container, screen_id="profiles_dialog")

    def result_profiles(self) -> tuple[Profile, ...]:
        return tuple(self._profiles)

    def _profile_rulesets(self, profile: Profile) -> list[str]:
        return profile_ruleset_paths(profile)

    def _collect_rulesets(self) -> list[str]:
        return collect_profile_rulesets(self._profiles)

    def _refresh_rulesets(self) -> None:
        previous = self._selected_path()
        self._ruleset_paths = self._collect_rulesets()
        self.ruleset_list.clear()
        selected_index = -1
        for index, path in enumerate(self._ruleset_paths):
            display = self._ruleset_display_name(path)
            resolved = normalize_ruleset_path(path)
            if not resolved.exists():
                display = t("ruleset.missing", label=display)
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.ruleset_list.addItem(item)
            if previous and path == previous:
                selected_index = index
        if selected_index < 0 and self._ruleset_paths:
            selected_index = 0
        if selected_index >= 0:
            self.ruleset_list.setCurrentRow(selected_index)
        else:
            self._render_selected_details(None)

    def _on_select(self, _row: int) -> None:
        self._render_selected_details(self._selected_path())

    def _selected_path(self) -> str | None:
        row = self.ruleset_list.currentRow()
        if row < 0 or row >= len(self._ruleset_paths):
            return None
        item = self.ruleset_list.item(row)
        if item is None:
            return None
        path = item.data(Qt.UserRole)
        if not isinstance(path, str):
            return None
        return path

    def _linked_profiles(self, path: str) -> list[Profile]:
        impact = analyze_ruleset_delete_impact(self._profiles, path)
        return list(impact.linked_profiles)

    def _render_selected_details(self, path: str | None) -> None:
        if not path:
            self.reveal_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.path_label.setText("")
            self.rules_count_label.setText("")
            self.details_label.setText(t("dialogs.manage_rulesets.no_selection"))
            self.status_label.setText("")
            self.rules_preview.setPlainText("")
            return
        linked_profiles = self._linked_profiles(path)
        names = ", ".join(profile.name or profile.profile_id for profile in linked_profiles) or "(none)"
        self.path_label.setText(t("dialogs.manage_rulesets.path", path=path))
        self.details_label.setText(t("dialogs.manage_rulesets.linked_profiles", names=names))
        resolved = normalize_ruleset_path(path)
        if not resolved.exists():
            self.status_label.setText(t("dialogs.manage_rulesets.status_missing"))
        else:
            self.status_label.setText(t("dialogs.manage_rulesets.status_available"))
        self._render_rules_preview(path)
        self.reveal_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def _reveal_selected(self) -> None:
        path = self._selected_path()
        if not path:
            return
        reveal_path(path)

    def _delete_selected_ruleset(self) -> None:
        path = self._selected_path()
        if not path:
            return
        impact = analyze_ruleset_delete_impact(self._profiles, path)
        if not impact.linked_profiles:
            return
        blocked = impact.blocked_profile_names()
        if blocked:
            QMessageBox.warning(
                self,
                t("dialogs.rulesets.title"),
                t(
                    "dialogs.manage_rulesets.delete_blocked",
                    profiles="\n".join(f"- {name}" for name in blocked),
                ),
            )
            return

        first_confirm = QMessageBox(self)
        first_confirm.setIcon(QMessageBox.Warning)
        first_confirm.setWindowTitle(t("dialogs.rulesets.title"))
        first_confirm.setText(t(
            "dialogs.manage_rulesets.delete_unlink_confirm",
            profiles="\n".join(f"- {name}" for name in impact.linked_profile_names()),
        ))
        first_confirm.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        first_confirm.setDefaultButton(QMessageBox.Cancel)
        if first_confirm.exec() != QMessageBox.Ok:
            return

        second_confirm = QMessageBox(self)
        second_confirm.setIcon(QMessageBox.Warning)
        second_confirm.setWindowTitle(t("dialogs.rulesets.title"))
        second_confirm.setText(t("dialogs.manage_rulesets.delete_final_confirm"))
        second_confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        second_confirm.setDefaultButton(QMessageBox.Cancel)
        if second_confirm.exec() != QMessageBox.Yes:
            return

        try:
            delete_ruleset_file(path)
        except OSError as exc:
            QMessageBox.warning(self, t("dialogs.rulesets.title"), str(exc))
            return

        self._unlink_ruleset(path)
        self._refresh_rulesets()

    def _unlink_ruleset(self, path: str) -> None:
        self._profiles = list(unlink_ruleset_from_library(self._profiles, path))

    def _render_rules_preview(self, path: str) -> None:
        resolved = normalize_ruleset_path(path)
        if not resolved.exists() or not resolved.is_file():
            self.rules_count_label.setText(t("dialogs.manage_rulesets.rules_count", count=0))
            self.rules_preview.setPlainText(t("dialogs.manage_rulesets.preview_missing"))
            return
        try:
            dataset = load_vocab_dataset(resolved)
        except Exception as exc:  # noqa: BLE001
            self.rules_count_label.setText(t("dialogs.manage_rulesets.rules_count", count=0))
            self.rules_preview.setPlainText(
                t("dialogs.manage_rulesets.preview_load_error", message=str(exc))
            )
            return

        rules = list(dataset.rules or ())
        self.rules_count_label.setText(t("dialogs.manage_rulesets.rules_count", count=len(rules)))
        if not rules:
            self.rules_preview.setPlainText(t("dialogs.manage_rulesets.preview_empty"))
            return

        lines = build_ruleset_preview_lines(
            rules,
            max_rows=140,
            disabled_label=t("rules_table.disabled"),
            overflow_template=t("dialogs.manage_rulesets.preview_more"),
        )
        self.rules_preview.setPlainText("\n".join(lines))

    def _ruleset_display_name(self, path: str) -> str:
        return ruleset_display_name(path)

    def _set_button_variant(self, button: QPushButton | None, variant: str) -> None:
        if button is None:
            return
        button.setProperty("variant", variant)
