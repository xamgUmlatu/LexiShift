from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from helper_installer import (
    BrowserConnectionConfig,
    BrowserConnectionTarget,
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
    _replace_browser_config,
    _upsert_browser_target,
    ensure_helper_autostart,
    load_browser_connections,
    save_browser_connections,
)
from i18n import t


class BrowserConnectionsDialog(QDialog):
    def __init__(self, parent, ui_settings: QSettings) -> None:
        super().__init__(parent)
        self._ui_settings = ui_settings
        self.setWindowTitle(t("dialogs.browser_connections.title"))
        self.resize(720, 420)

        self._content_widget = QWidget(self)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.addWidget(self._content_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
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
        intro = QLabel(t("dialogs.browser_connections.intro"), self)
        intro.setWordWrap(True)
        self._content_layout.addWidget(intro)

        section = QLabel(t("dialogs.browser_connections.production_section"), self)
        section.setObjectName("sectionLabel")
        self._content_layout.addWidget(section)
        self._build_fixed_rows()

        advanced = QLabel(t("dialogs.browser_connections.unpacked_section"), self)
        advanced.setObjectName("sectionLabel")
        self._content_layout.addWidget(advanced)
        self._build_unpacked_rows()

        note = QLabel(t("dialogs.browser_connections.host_scope_note"), self)
        note.setWordWrap(True)
        self._content_layout.addWidget(note)
        self._content_layout.addStretch(1)

    def _build_fixed_rows(self) -> None:
        envs, _ = load_extension_environments()
        fixed_envs = [env for env in envs if env.fixed]
        configs = load_browser_connections(self._ui_settings)
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
            row = QHBoxLayout()
            label = QLabel(env.label, self)
            row.addWidget(label, 2)
            if target is None:
                status_text = QLabel(t("dialogs.browser_connections.fixed_id_missing"), self)
                action = QPushButton(t("dialogs.browser_connections.unavailable"), self)
                action.setEnabled(False)
            else:
                status_text = QLabel(self._status_summary(status), self)
                action = QPushButton(self._action_label(status), self)
                action.clicked.connect(
                    lambda _checked=False, env_key=env.key: self._connect_fixed(env_key)
                )
            status_text.setWordWrap(True)
            row.addWidget(status_text, 3)
            row.addWidget(action, 0)
            self._content_layout.addLayout(row)

    def _build_unpacked_rows(self) -> None:
        configs = load_browser_connections(self._ui_settings)
        unpacked_rows = [
            (config, target)
            for config in configs
            for target in config.targets
            if target.kind == TARGET_KIND_UNPACKED
        ]
        if not unpacked_rows:
            empty = QLabel(t("dialogs.browser_connections.no_unpacked"), self)
            empty.setWordWrap(True)
            self._content_layout.addWidget(empty)
        else:
            for config, target in unpacked_rows:
                status = inspect_helper_installation(
                    browser=config.browser,
                    expected_extension_ids=_browser_expected_ids(config),
                )
                row = QHBoxLayout()
                label = QLabel(
                    t(
                        "dialogs.browser_connections.unpacked_row",
                        browser=_browser_label(config.browser),
                        extension_id=target.extension_id,
                        host_mode=_host_mode_label(config.host_mode),
                    ),
                    self,
                )
                label.setWordWrap(True)
                row.addWidget(label, 3)
                row.addWidget(QLabel(self._status_summary(status), self), 2)
                repair = QPushButton(t("dialogs.browser_connections.repair"), self)
                repair.clicked.connect(
                    lambda _checked=False, browser=config.browser: self._repair_browser(browser)
                )
                row.addWidget(repair, 0)
                self._content_layout.addLayout(row)
        add_button = QPushButton(t("dialogs.browser_connections.add_unpacked"), self)
        add_button.clicked.connect(self._add_unpacked)
        self._content_layout.addWidget(add_button)

    def _status_summary(self, status) -> str:
        if status.state == HELPER_STATE_CONFIGURED:
            host_mode = _host_mode_label(status.host_mode or HOST_MODE_BUNDLED)
            return t("dialogs.browser_connections.status_configured", host_mode=host_mode)
        if status.state == HELPER_STATE_NEEDS_REPAIR:
            return t("dialogs.browser_connections.status_needs_repair", message=status.message)
        return t("dialogs.browser_connections.status_not_configured")

    def _action_label(self, status) -> str:
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
        browsers = [("chrome", "Chrome"), ("chromium", "Chromium"), ("brave", "Brave")]
        labels = [label for _, label in browsers]
        label, ok = QInputDialog.getItem(
            self,
            t("dialogs.browser_connections.add_unpacked_title"),
            t("dialogs.browser_connections.add_unpacked_browser_prompt"),
            labels,
            1,
            False,
        )
        if not ok:
            return
        browser = next(key for key, value in browsers if value == label)
        extension_id, ok = QInputDialog.getText(
            self,
            t("dialogs.browser_connections.add_unpacked_title"),
            t("dialogs.browser_connections.add_unpacked_id_prompt"),
        )
        if not ok or not extension_id.strip():
            return
        host_modes = [
            (HOST_MODE_WORKSPACE, t("dialogs.browser_connections.host_mode_workspace")),
            (HOST_MODE_BUNDLED, t("dialogs.browser_connections.host_mode_bundled")),
            (HOST_MODE_CUSTOM, t("dialogs.browser_connections.host_mode_custom")),
        ]
        host_label, ok = QInputDialog.getItem(
            self,
            t("dialogs.browser_connections.add_unpacked_title"),
            t("dialogs.browser_connections.add_unpacked_host_mode_prompt"),
            [value for _, value in host_modes],
            0,
            False,
        )
        if not ok:
            return
        host_mode = next(key for key, value in host_modes if value == host_label)
        extension_id = extension_id.strip()
        target = BrowserConnectionTarget(
            key=f"{browser}_unpacked_{extension_id}",
            label=f"{_browser_label(browser)} (Unpacked Dev)",
            extension_id=extension_id,
            kind=TARGET_KIND_UNPACKED,
            fixed=False,
        )
        configs = load_browser_connections(self._ui_settings)
        existing = _find_browser_config(configs, browser)
        host_override_path = existing.host_override_path if existing else None
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
