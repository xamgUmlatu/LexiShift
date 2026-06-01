from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from helper_installer import (
    BrowserConnectionConfig,
    BrowserConnectionTarget,
    HelperInstallStatus,
    get_environment,
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
    HOST_MODE_BUNDLED,
    HOST_MODE_CUSTOM,
    HOST_MODE_WORKSPACE,
    install_helper,
    inspect_helper_installation,
    load_extension_environments,
    TARGET_KIND_UNPACKED,
)
from helper_ui import (
    auto_repair_browser_connections,
    _browser_expected_ids,
    _browser_label,
    _find_browser_config,
    _fixed_target_from_env,
    _host_mode_label,
    _host_path_for_config,
    _remember_last_helper_selection,
    _remove_browser_target,
    _replace_browser_config,
    _upsert_browser_target,
    ensure_helper_autostart,
    load_browser_connections,
    save_browser_connections,
)
from i18n import t
from localized_message_box import localized_question
from theme_combo_popup import apply_combo_popup_theme
from theme_manager import resolve_current_theme
from utils_paths import reveal_path

_BROWSER_OPTIONS = [
    ("chrome", "Chrome"),
    ("chromium", "Chromium"),
    ("brave", "Brave"),
]


def _value_label(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


def _path_text(path: Path | None) -> str:
    return str(path) if path else t("dialogs.browser_connections.not_available")


def _status_badge_text(status: HelperInstallStatus) -> str:
    if status.state == HELPER_STATE_CONFIGURED:
        return t("dialogs.browser_connections.status_label_configured")
    if status.state == HELPER_STATE_NEEDS_REPAIR:
        return t("dialogs.browser_connections.status_label_needs_repair")
    return t("dialogs.browser_connections.status_label_not_configured")


def _unpacked_target(browser: str, extension_id: str) -> BrowserConnectionTarget:
    return BrowserConnectionTarget(
        key=f"{browser}_unpacked_{extension_id}",
        label=f"{_browser_label(browser)} (Unpacked Dev)",
        extension_id=extension_id,
        kind=TARGET_KIND_UNPACKED,
        fixed=False,
    )


class _UnpackedExtensionDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        title: str,
        browser: str = "chromium",
        extension_id: str = "",
        allow_browser_change: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 180)

        self._browser_combo = QComboBox(self)
        for key, label in _BROWSER_OPTIONS:
            self._browser_combo.addItem(label, key)
        self._browser_combo.setEnabled(allow_browser_change)
        browser_index = max(0, self._browser_combo.findData(browser))
        self._browser_combo.setCurrentIndex(browser_index)
        apply_combo_popup_theme(
            self._browser_combo,
            resolve_current_theme(screen_id="settings_dialog"),
        )

        self._extension_id_edit = QLineEdit(extension_id, self)
        self._extension_id_edit.setPlaceholderText("abcdefghijklmnopqrstuvwxyzabcdef")

        form = QFormLayout()
        form.addRow(t("dialogs.browser_connections.browser_label"), self._browser_combo)
        form.addRow(t("dialogs.browser_connections.extension_id_label"), self._extension_id_edit)

        note = QLabel(t("dialogs.browser_connections.unpacked_workspace_note"), self)
        note.setWordWrap(True)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(button_box)

    def values(self) -> tuple[str, str]:
        browser = str(self._browser_combo.currentData())
        extension_id = self._extension_id_edit.text().strip()
        return browser, extension_id

    def _accept(self) -> None:
        _browser, extension_id = self.values()
        if not extension_id:
            QMessageBox.warning(
                self,
                self.windowTitle(),
                t("dialogs.browser_connections.invalid_extension_id"),
            )
            return
        self.accept()


class BrowserConnectionsDialog(QDialog):
    def __init__(self, parent, ui_settings: QSettings) -> None:
        super().__init__(parent)
        self._ui_settings = ui_settings
        self._show_diagnostics = False
        self.setWindowTitle(t("dialogs.browser_connections.title"))
        self.resize(900, 620)
        auto_repair_browser_connections(self._ui_settings)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setProperty("browserConnectionsScroll", True)

        self._content_widget = QWidget(scroll)
        self._content_widget.setProperty("browserConnectionsCanvas", True)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(6, 6, 6, 6)
        self._content_layout.setSpacing(16)
        scroll.setWidget(self._content_widget)

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.addWidget(scroll, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        button_box.rejected.connect(self.reject)
        root.addWidget(button_box)

        self._rebuild()

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                while child_layout.count():
                    child_item = child_layout.takeAt(0)
                    child_widget = child_item.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()

    def _rebuild(self) -> None:
        self._clear_content()
        fixed_rows, unpacked_rows = self._collect_rows()

        intro = QLabel(t("dialogs.browser_connections.intro"), self)
        intro.setWordWrap(True)
        self._content_layout.addWidget(intro)
        self._content_layout.addWidget(self._build_diagnostics_toggle(), 0, Qt.AlignLeft)
        self._content_layout.addWidget(self._build_overview_card(fixed_rows, unpacked_rows))
        self._content_layout.addWidget(self._build_fixed_section(fixed_rows))
        self._content_layout.addWidget(self._build_unpacked_section(unpacked_rows))
        self._content_layout.addStretch(1)

    def _build_diagnostics_toggle(self) -> QToolButton:
        button = QToolButton(self)
        button.setCheckable(True)
        button.setChecked(self._show_diagnostics)
        button.setText(
            t(
                "dialogs.browser_connections.hide_diagnostics"
                if self._show_diagnostics
                else "dialogs.browser_connections.show_diagnostics"
            )
        )
        button.clicked.connect(self._toggle_diagnostics)
        return button

    def _toggle_diagnostics(self, checked: bool) -> None:
        self._show_diagnostics = bool(checked)
        self._rebuild()

    def _collect_rows(self) -> tuple[list[tuple], list[tuple]]:
        envs, _ = load_extension_environments()
        fixed_envs = [env for env in envs if env.fixed]
        configs = load_browser_connections(self._ui_settings)

        fixed_rows = []
        for env in fixed_envs:
            target = _fixed_target_from_env(env)
            config = _find_browser_config(configs, env.browser)
            expected_ids = list(_browser_expected_ids(config))
            if target and target.extension_id not in expected_ids:
                expected_ids.append(target.extension_id)
            status = inspect_helper_installation(
                browser=env.browser,
                expected_extension_ids=expected_ids,
            )
            fixed_rows.append((env, target, config, status))

        unpacked_rows = []
        for config in configs:
            unpacked_targets = [
                target for target in config.targets if target.kind == TARGET_KIND_UNPACKED
            ]
            if not unpacked_targets:
                continue
            status = inspect_helper_installation(
                browser=config.browser,
                expected_extension_ids=_browser_expected_ids(config),
            )
            for target in unpacked_targets:
                unpacked_rows.append((config, target, status))
        return fixed_rows, unpacked_rows

    def _build_overview_card(self, fixed_rows: list[tuple], unpacked_rows: list[tuple]) -> QFrame:
        production_total = len(fixed_rows)
        configured = sum(
            1 for *_rest, status in fixed_rows if status.state == HELPER_STATE_CONFIGURED
        )
        repair = sum(
            1 for *_rest, status in fixed_rows if status.state == HELPER_STATE_NEEDS_REPAIR
        )
        card = QFrame(self)
        card.setFrameShape(QFrame.StyledPanel)
        card.setProperty("browserConnectionPanel", True)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        title = QLabel(t("dialogs.browser_connections.overview_title"), card)
        title.setProperty("browserConnectionCardTitle", True)
        layout.addWidget(title)

        summary = QLabel(
            t(
                "dialogs.browser_connections.overview_summary",
                production_total=production_total,
                configured=configured,
                repair=repair,
                unpacked_total=len(unpacked_rows),
            ),
            card,
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)
        return card

    def _section_title_label(self, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setProperty("browserConnectionSectionTitle", True)
        return label

    def _section_panel(self) -> tuple[QFrame, QVBoxLayout]:
        panel = QFrame(self)
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setProperty("browserConnectionPanel", True)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        return panel, layout

    def _build_fixed_section(self, fixed_rows: list[tuple]) -> QWidget:
        section = QWidget(self)
        outer = QVBoxLayout(section)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        outer.addWidget(
            self._section_title_label(t("dialogs.browser_connections.production_section"))
        )

        panel, layout = self._section_panel()
        description = QLabel(t("dialogs.browser_connections.production_description"), panel)
        description.setWordWrap(True)
        layout.addWidget(description)
        for env, target, config, status in fixed_rows:
            layout.addWidget(self._build_fixed_card(env, target, config, status))
        outer.addWidget(panel)
        return section

    def _build_fixed_card(
        self,
        env,
        target: BrowserConnectionTarget | None,
        config: BrowserConnectionConfig | None,
        status: HelperInstallStatus,
    ) -> QFrame:
        detail_rows: list[tuple[str, str]] = []
        if self._show_diagnostics:
            detail_rows = [
                (
                    t("dialogs.browser_connections.extension_id_label"),
                    target.extension_id
                    if target
                    else t("dialogs.browser_connections.fixed_id_missing"),
                ),
                (
                    t("dialogs.browser_connections.manifest_label"),
                    _path_text(status.manifest_path),
                ),
                (
                    t("dialogs.browser_connections.host_mode_label"),
                    _host_mode_label(
                        status.host_mode or (config.host_mode if config else HOST_MODE_BUNDLED)
                    ),
                ),
                (
                    t("dialogs.browser_connections.host_path_label"),
                    _path_text(status.host_path),
                ),
                (
                    t("dialogs.browser_connections.allowed_extension_ids_label"),
                    ", ".join(status.allowed_extension_ids)
                    or t("dialogs.browser_connections.not_available"),
                ),
            ]
            if status.state == HELPER_STATE_NEEDS_REPAIR:
                detail_rows.append((t("dialogs.browser_connections.issue_label"), status.message))
            if target is None:
                detail_rows.append(
                    (
                        t("dialogs.browser_connections.issue_label"),
                        t("dialogs.browser_connections.fixed_id_missing"),
                    )
                )

        actions = []
        if target is None:
            actions.append(
                (
                    t("dialogs.browser_connections.unavailable"),
                    None,
                    False,
                )
            )
        else:
            actions.append(
                (
                    self._action_label(status),
                    lambda _checked=False, env_key=env.key: self._connect_fixed(env_key),
                    True,
                )
            )
        if self._show_diagnostics:
            actions.extend(self._reveal_actions(status))

        return self._build_connection_card(
            title=env.label,
            status=status,
            detail_rows=detail_rows,
            actions=actions,
        )

    def _build_unpacked_section(self, unpacked_rows: list[tuple]) -> QWidget:
        section = QWidget(self)
        outer = QVBoxLayout(section)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        outer.addWidget(
            self._section_title_label(t("dialogs.browser_connections.unpacked_section"))
        )

        panel, layout = self._section_panel()
        description = QLabel(t("dialogs.browser_connections.unpacked_description"), panel)
        description.setWordWrap(True)
        layout.addWidget(description)

        if not unpacked_rows:
            empty = QLabel(t("dialogs.browser_connections.no_unpacked"), panel)
            empty.setWordWrap(True)
            layout.addWidget(empty)
        else:
            for config, target, status in unpacked_rows:
                layout.addWidget(self._build_unpacked_card(config, target, status))

        add_button = QPushButton(t("dialogs.browser_connections.add_unpacked"), panel)
        add_button.clicked.connect(self._add_unpacked)
        layout.addWidget(add_button, 0, Qt.AlignLeft)
        outer.addWidget(panel)
        return section

    def _build_unpacked_card(
        self,
        config: BrowserConnectionConfig,
        target: BrowserConnectionTarget,
        status: HelperInstallStatus,
    ) -> QFrame:
        detail_rows = [
            (
                t("dialogs.browser_connections.browser_label"),
                _browser_label(config.browser),
            ),
            (
                t("dialogs.browser_connections.extension_id_label"),
                target.extension_id,
            ),
        ]
        if self._show_diagnostics:
            detail_rows.extend(
                [
                    (
                        t("dialogs.browser_connections.host_mode_label"),
                        _host_mode_label(config.host_mode),
                    ),
                    (
                        t("dialogs.browser_connections.shared_manifest_label"),
                        _browser_label(config.browser),
                    ),
                    (
                        t("dialogs.browser_connections.manifest_label"),
                        _path_text(status.manifest_path),
                    ),
                    (
                        t("dialogs.browser_connections.host_path_label"),
                        _path_text(status.host_path),
                    ),
                    (
                        t("dialogs.browser_connections.allowed_extension_ids_label"),
                        ", ".join(status.allowed_extension_ids or _browser_expected_ids(config))
                        or t("dialogs.browser_connections.not_available"),
                    ),
                ]
            )
            if status.state == HELPER_STATE_NEEDS_REPAIR:
                detail_rows.append((t("dialogs.browser_connections.issue_label"), status.message))

        actions = [
            (
                t("dialogs.browser_connections.edit"),
                lambda _checked=False, config=config, target=target: self._edit_unpacked(
                    config, target
                ),
                True,
            ),
            (
                t("dialogs.browser_connections.repair"),
                lambda _checked=False, browser=config.browser: self._repair_browser(browser),
                True,
            ),
            (
                t("buttons.remove"),
                lambda _checked=False, browser=config.browser, target_key=target.key: (
                    self._remove_unpacked(browser, target_key)
                ),
                True,
            ),
        ]
        if self._show_diagnostics:
            actions.extend(self._reveal_actions(status))

        return self._build_connection_card(
            title=target.label,
            status=status,
            detail_rows=detail_rows,
            actions=actions,
        )

    def _build_connection_card(
        self,
        *,
        title: str,
        status: HelperInstallStatus,
        detail_rows: list[tuple[str, str]],
        actions: list[tuple[str, object, bool]],
    ) -> QFrame:
        card = QFrame(self)
        card.setFrameShape(QFrame.StyledPanel)
        card.setProperty("browserConnectionCard", True)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        header = QHBoxLayout()
        title_label = QLabel(title, card)
        title_label.setProperty("browserConnectionCardTitle", True)
        header.addWidget(title_label, 1)
        badge = QLabel(_status_badge_text(status), card)
        badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        badge.setProperty("browserConnectionStatusBadge", True)
        badge.setProperty("statusState", self._status_state(status))
        header.addWidget(badge, 0)
        card_layout.addLayout(header)

        summary = QLabel(self._status_summary(status), card)
        summary.setWordWrap(True)
        card_layout.addWidget(summary)

        if detail_rows:
            form = QFormLayout()
            form.setContentsMargins(0, 0, 0, 0)
            form.setSpacing(6)
            for label_text, value in detail_rows:
                form.addRow(f"{label_text}:", _value_label(value, card))
            card_layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        for label, slot, enabled in actions:
            button = QPushButton(label, card)
            button.setEnabled(enabled)
            if callable(slot):
                button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch(1)
        card_layout.addLayout(buttons)
        return card

    def _reveal_actions(self, status: HelperInstallStatus) -> list[tuple[str, object, bool]]:
        manifest_enabled = bool(status.manifest_path and status.manifest_path.exists())
        host_enabled = bool(status.host_path and status.host_path.exists())
        return [
            (
                t("dialogs.browser_connections.reveal_manifest"),
                (
                    lambda _checked=False, path=status.manifest_path: (
                        reveal_path(str(path)) if path is not None else None
                    )
                ),
                manifest_enabled,
            ),
            (
                t("dialogs.browser_connections.reveal_host"),
                (
                    lambda _checked=False, path=status.host_path: (
                        reveal_path(str(path)) if path is not None else None
                    )
                ),
                host_enabled,
            ),
        ]

    def _status_summary(self, status: HelperInstallStatus) -> str:
        if status.state == HELPER_STATE_CONFIGURED:
            if self._show_diagnostics:
                host_mode = _host_mode_label(status.host_mode or HOST_MODE_BUNDLED)
                return t("dialogs.browser_connections.status_configured", host_mode=host_mode)
            return t("dialogs.browser_connections.status_label_configured")
        if status.state == HELPER_STATE_NEEDS_REPAIR:
            return t("dialogs.browser_connections.status_needs_repair", message=status.message)
        return t("dialogs.browser_connections.status_not_configured")

    def _status_state(self, status: HelperInstallStatus) -> str:
        if status.state == HELPER_STATE_CONFIGURED:
            return "configured"
        if status.state == HELPER_STATE_NEEDS_REPAIR:
            return "needs_repair"
        return "not_configured"

    def _action_label(self, status: HelperInstallStatus) -> str:
        if status.state == HELPER_STATE_CONFIGURED:
            return t("dialogs.browser_connections.repair")
        return t("dialogs.browser_connections.connect")

    def _connect_fixed(self, env_key: str) -> None:
        envs, _ = load_extension_environments()
        env = get_environment(env_key, envs)
        if env is None:
            return
        target = _fixed_target_from_env(env)
        if target is None:
            QMessageBox.warning(
                self,
                t("dialogs.browser_connections.title"),
                t("dialogs.browser_connections.fixed_id_missing"),
            )
            return
        configs = load_browser_connections(self._ui_settings)
        existing = _find_browser_config(configs, env.browser)
        host_mode = existing.host_mode if existing else HOST_MODE_BUNDLED
        host_override_path = existing.host_override_path if existing else None
        updated = _upsert_browser_target(
            configs,
            browser=env.browser,
            target=target,
            host_mode=host_mode,
            host_override_path=host_override_path,
        )
        config = _find_browser_config(updated, env.browser)
        if config is None:
            return
        self._install_config(config, updated, remember_target=target)

    def _repair_browser(self, browser: str) -> None:
        configs = load_browser_connections(self._ui_settings)
        config = _find_browser_config(configs, browser)
        if config is None:
            return
        remember_target = config.targets[0] if config.targets else None
        self._install_config(config, configs, remember_target=remember_target)

    def _add_unpacked(self) -> None:
        dialog = _UnpackedExtensionDialog(
            self,
            title=t("dialogs.browser_connections.add_unpacked_title"),
        )
        if dialog.exec() != QDialog.Accepted:
            return
        browser, extension_id = dialog.values()
        target = _unpacked_target(browser, extension_id)
        configs = load_browser_connections(self._ui_settings)
        existing = _find_browser_config(configs, browser)
        if not self._confirm_workspace_host_switch(existing):
            return
        updated = _upsert_browser_target(
            configs,
            browser=browser,
            target=target,
            host_mode=HOST_MODE_WORKSPACE,
            host_override_path=None,
        )
        config = _find_browser_config(updated, browser)
        if config is None:
            return
        self._install_config(config, updated, remember_target=target)

    def _edit_unpacked(
        self,
        config: BrowserConnectionConfig,
        target: BrowserConnectionTarget,
    ) -> None:
        dialog = _UnpackedExtensionDialog(
            self,
            title=t("dialogs.browser_connections.edit_unpacked_title"),
            browser=config.browser,
            extension_id=target.extension_id,
            allow_browser_change=False,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        browser, extension_id = dialog.values()
        if not self._confirm_workspace_host_switch(config):
            return
        updated = _remove_browser_target(
            load_browser_connections(self._ui_settings),
            browser=config.browser,
            target_key=target.key,
        )
        replacement_target = _unpacked_target(browser, extension_id)
        updated = _upsert_browser_target(
            updated,
            browser=browser,
            target=replacement_target,
            host_mode=HOST_MODE_WORKSPACE,
            host_override_path=None,
        )
        replacement_config = _find_browser_config(updated, browser)
        if replacement_config is None:
            return
        self._install_config(replacement_config, updated, remember_target=replacement_target)

    def _remove_unpacked(self, browser: str, target_key: str) -> None:
        updated = _remove_browser_target(
            load_browser_connections(self._ui_settings),
            browser=browser,
            target_key=target_key,
        )
        save_browser_connections(self._ui_settings, updated)
        self._rebuild()

    def _install_config(
        self,
        config: BrowserConnectionConfig,
        configs: list[BrowserConnectionConfig],
        *,
        remember_target: BrowserConnectionTarget | None,
    ) -> None:
        resolved = _host_path_for_config(config)
        if resolved is None:
            QMessageBox.warning(
                self,
                t("dialogs.browser_connections.title"),
                self._missing_host_message(config),
            )
            return
        config, host_path = resolved
        result = install_helper(
            extension_ids=[target.extension_id for target in config.targets],
            browser=config.browser,
            host_path=host_path,
        )
        if not result.installed:
            QMessageBox.warning(
                self,
                t("dialogs.browser_connections.title"),
                t("dialogs.helper_install.failed", message=result.message),
            )
            return
        save_browser_connections(self._ui_settings, _replace_browser_config(configs, config))
        if remember_target is not None:
            _remember_last_helper_selection(
                self._ui_settings,
                target=remember_target,
                host_path=host_path,
            )
        try:
            ensure_helper_autostart()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(
                self,
                t("dialogs.browser_connections.title"),
                t("dialogs.helper_install.failed", message=str(exc)),
            )
        else:
            QMessageBox.information(
                self,
                t("dialogs.browser_connections.title"),
                t("dialogs.browser_connections.saved"),
            )
        self._rebuild()

    def _missing_host_message(self, config: BrowserConnectionConfig) -> str:
        if config.host_mode == HOST_MODE_WORKSPACE:
            return t("dialogs.browser_connections.missing_workspace_host")
        if config.host_mode == HOST_MODE_CUSTOM:
            return t("dialogs.browser_connections.invalid_custom_host")
        return t("dialogs.browser_connections.missing_host")

    def _confirm_workspace_host_switch(
        self,
        config: BrowserConnectionConfig | None,
    ) -> bool:
        if config is None or config.host_mode == HOST_MODE_WORKSPACE:
            return True
        answer = localized_question(
            self,
            t("dialogs.browser_connections.shared_host_warning_title"),
            t(
                "dialogs.browser_connections.shared_host_warning_message",
                browser=_browser_label(config.browser),
            ),
        )
        return answer == QMessageBox.Yes
