from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
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
        host_mode: str = HOST_MODE_WORKSPACE,
        host_override_path: str | None = None,
        allow_browser_change: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(540, 220)

        self._browser_combo = QComboBox(self)
        for key, label in _BROWSER_OPTIONS:
            self._browser_combo.addItem(label, key)
        self._browser_combo.setEnabled(allow_browser_change)
        browser_index = max(0, self._browser_combo.findData(browser))
        self._browser_combo.setCurrentIndex(browser_index)

        self._extension_id_edit = QLineEdit(extension_id, self)
        self._extension_id_edit.setPlaceholderText("abcdefghijklmnopqrstuvwxyzabcdef")

        self._host_mode_combo = QComboBox(self)
        self._host_mode_combo.addItem(
            t("dialogs.browser_connections.host_mode_workspace"),
            HOST_MODE_WORKSPACE,
        )
        self._host_mode_combo.addItem(
            t("dialogs.browser_connections.host_mode_bundled"),
            HOST_MODE_BUNDLED,
        )
        self._host_mode_combo.addItem(
            t("dialogs.browser_connections.host_mode_custom"),
            HOST_MODE_CUSTOM,
        )
        host_mode_index = max(0, self._host_mode_combo.findData(host_mode))
        self._host_mode_combo.setCurrentIndex(host_mode_index)
        self._host_mode_combo.currentIndexChanged.connect(self._sync_custom_host_state)

        self._custom_host_edit = QLineEdit(host_override_path or "", self)
        self._custom_host_browse = QPushButton(t("dialogs.browser_connections.browse"), self)
        self._custom_host_browse.clicked.connect(self._browse_custom_host)
        custom_host_row = QHBoxLayout()
        custom_host_row.setContentsMargins(0, 0, 0, 0)
        custom_host_row.addWidget(self._custom_host_edit, 1)
        custom_host_row.addWidget(self._custom_host_browse, 0)
        custom_host_widget = QWidget(self)
        custom_host_widget.setLayout(custom_host_row)
        self._custom_host_widget = custom_host_widget

        shared_note = QLabel(t("dialogs.browser_connections.host_scope_note"), self)
        shared_note.setWordWrap(True)

        form = QFormLayout()
        form.addRow(t("dialogs.browser_connections.browser_label"), self._browser_combo)
        form.addRow(t("dialogs.browser_connections.extension_id_label"), self._extension_id_edit)
        form.addRow(t("dialogs.browser_connections.host_mode_label"), self._host_mode_combo)
        form.addRow(
            t("dialogs.browser_connections.custom_host_path_label"),
            self._custom_host_widget,
        )

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(shared_note)
        layout.addWidget(button_box)

        self._sync_custom_host_state()

    def values(self) -> tuple[str, str, str, str | None]:
        browser = str(self._browser_combo.currentData())
        extension_id = self._extension_id_edit.text().strip()
        host_mode = str(self._host_mode_combo.currentData())
        custom_host = self._custom_host_edit.text().strip() or None
        return browser, extension_id, host_mode, custom_host

    def _sync_custom_host_state(self) -> None:
        is_custom = self._host_mode_combo.currentData() == HOST_MODE_CUSTOM
        self._custom_host_widget.setEnabled(is_custom)

    def _browse_custom_host(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            t("dialogs.browser_connections.choose_host_path"),
            str(Path.home()),
            t("dialogs.helper_install.host_filter"),
        )
        if filename:
            self._custom_host_edit.setText(filename)

    def _accept(self) -> None:
        _browser, extension_id, host_mode, host_override_path = self.values()
        if not extension_id:
            QMessageBox.warning(
                self,
                self.windowTitle(),
                t("dialogs.browser_connections.invalid_extension_id"),
            )
            return
        if host_mode == HOST_MODE_CUSTOM and not host_override_path:
            QMessageBox.warning(
                self,
                self.windowTitle(),
                t("dialogs.browser_connections.missing_custom_host"),
            )
            return
        self.accept()


class BrowserConnectionsDialog(QDialog):
    def __init__(self, parent, ui_settings: QSettings) -> None:
        super().__init__(parent)
        self._ui_settings = ui_settings
        self.setWindowTitle(t("dialogs.browser_connections.title"))
        self.resize(900, 620)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._content_widget = QWidget(scroll)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)
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
        self._content_layout.addWidget(self._build_overview_card(fixed_rows, unpacked_rows))
        self._content_layout.addWidget(self._build_fixed_section(fixed_rows))
        self._content_layout.addWidget(self._build_unpacked_section(unpacked_rows))
        self._content_layout.addStretch(1)

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
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        title = QLabel(t("dialogs.browser_connections.overview_title"), card)
        title.setStyleSheet("font-weight: 600;")
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

        host_note = QLabel(t("dialogs.browser_connections.host_scope_note"), card)
        host_note.setWordWrap(True)
        layout.addWidget(host_note)
        return card

    def _build_fixed_section(self, fixed_rows: list[tuple]) -> QGroupBox:
        group = QGroupBox(t("dialogs.browser_connections.production_section"), self)
        layout = QVBoxLayout(group)
        description = QLabel(t("dialogs.browser_connections.production_description"), group)
        description.setWordWrap(True)
        layout.addWidget(description)
        for env, target, config, status in fixed_rows:
            layout.addWidget(self._build_fixed_card(env, target, config, status))
        return group

    def _build_fixed_card(
        self,
        env,
        target: BrowserConnectionTarget | None,
        config: BrowserConnectionConfig | None,
        status: HelperInstallStatus,
    ) -> QFrame:
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
        actions.extend(self._reveal_actions(status))

        return self._build_connection_card(
            title=env.label,
            status=status,
            detail_rows=detail_rows,
            actions=actions,
        )

    def _build_unpacked_section(self, unpacked_rows: list[tuple]) -> QGroupBox:
        group = QGroupBox(t("dialogs.browser_connections.unpacked_section"), self)
        layout = QVBoxLayout(group)
        description = QLabel(t("dialogs.browser_connections.unpacked_description"), group)
        description.setWordWrap(True)
        layout.addWidget(description)

        if not unpacked_rows:
            empty = QLabel(t("dialogs.browser_connections.no_unpacked"), group)
            empty.setWordWrap(True)
            layout.addWidget(empty)
        else:
            for config, target, status in unpacked_rows:
                layout.addWidget(self._build_unpacked_card(config, target, status))

        add_button = QPushButton(t("dialogs.browser_connections.add_unpacked"), group)
        add_button.clicked.connect(self._add_unpacked)
        layout.addWidget(add_button, 0, Qt.AlignLeft)
        return group

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
        ]
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
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        header = QHBoxLayout()
        title_label = QLabel(title, card)
        title_label.setStyleSheet("font-weight: 600;")
        header.addWidget(title_label, 1)
        badge = QLabel(_status_badge_text(status), card)
        badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(badge, 0)
        card_layout.addLayout(header)

        summary = QLabel(self._status_summary(status), card)
        summary.setWordWrap(True)
        card_layout.addWidget(summary)

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
            host_mode = _host_mode_label(status.host_mode or HOST_MODE_BUNDLED)
            return t("dialogs.browser_connections.status_configured", host_mode=host_mode)
        if status.state == HELPER_STATE_NEEDS_REPAIR:
            return t("dialogs.browser_connections.status_needs_repair", message=status.message)
        return t("dialogs.browser_connections.status_not_configured")

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
        browser, extension_id, host_mode, host_override_path = dialog.values()
        target = _unpacked_target(browser, extension_id)
        configs = load_browser_connections(self._ui_settings)
        updated = _upsert_browser_target(
            configs,
            browser=browser,
            target=target,
            host_mode=host_mode,
            host_override_path=host_override_path,
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
            host_mode=config.host_mode,
            host_override_path=config.host_override_path,
            allow_browser_change=False,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        browser, extension_id, host_mode, host_override_path = dialog.values()
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
            host_mode=host_mode,
            host_override_path=host_override_path,
        )
        replacement_config = _find_browser_config(updated, browser)
        if replacement_config is None:
            return
        self._install_config(replacement_config, updated, remember_target=replacement_target)

    def _install_config(
        self,
        config: BrowserConnectionConfig,
        configs: list[BrowserConnectionConfig],
        *,
        remember_target: BrowserConnectionTarget | None,
    ) -> None:
        resolved = _host_path_for_config(config, parent=self, allow_prompt=True)
        if resolved is None:
            QMessageBox.warning(
                self,
                t("dialogs.browser_connections.title"),
                t("dialogs.browser_connections.missing_host"),
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
                t("dialogs.browser_connections.saved", path=str(result.manifest_path or "")),
            )
        self._rebuild()
