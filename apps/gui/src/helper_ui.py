from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Optional, Tuple

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog, QInputDialog

from frozen_layout import (
    HELPER_APP_BUNDLE_NAME,
    HELPER_WINDOWS_DIR_NAME,
    HELPER_WINDOWS_EXE_NAME,
    resolve_macos_sibling_bundle,
    resolve_windows_sibling_executable,
)
from helper_installer import (
    BrowserConnectionConfig,
    BrowserConnectionTarget,
    ExtensionEnvironment,
    default_host_script,
    get_environment,
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
    HELPER_STATE_NOT_CONFIGURED,
    HOST_MODE_BUNDLED,
    HOST_MODE_CUSTOM,
    HOST_MODE_WORKSPACE,
    install_helper,
    install_helper_autostart,
    inspect_helper_installation,
    infer_host_mode,
    is_helper_installed,
    log_helper_install,
    load_extension_environments,
    resolve_host_path_for_mode,
    resolve_extension_id,
    TARGET_KIND_PROD,
    TARGET_KIND_UNPACKED,
)
from helper_connection_models import (
    REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
    REPAIR_REASON_BUNDLED_CORE_STALE,
    REPAIR_REASON_BUNDLED_HOST_STALE,
    REPAIR_REASON_HOST_PATH_MISSING,
    REPAIR_REASON_MANIFEST_MISSING_HOST_PATH,
    REPAIR_REASON_MANIFEST_UNREADABLE,
    REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,
    REPAIR_REASON_WORKSPACE_PYTHON_MISSING,
    REPAIR_REASON_WORKSPACE_WRAPPER_STALE,
    REPAIR_REASON_WORKSPACE_WRAPPER_UNREADABLE,
)
from helper_logger import log_helper
from i18n import t

HELPER_EXECUTABLE_NAME = "LexiShiftHelper"
HELPER_BUNDLE_IDENTIFIER = "com.lexishift.helper.agent"
MAIN_BUNDLE_IDENTIFIER = "com.lexishift.app"
BROWSER_CONNECTIONS_KEY = "helper/browser_connections_v1"
_AUTO_REPAIR_SAFE_REASONS = {
    HOST_MODE_BUNDLED: {
        REPAIR_REASON_MANIFEST_UNREADABLE,
        REPAIR_REASON_MANIFEST_MISSING_HOST_PATH,
        REPAIR_REASON_HOST_PATH_MISSING,
        REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
        REPAIR_REASON_BUNDLED_HOST_STALE,
        REPAIR_REASON_BUNDLED_CORE_STALE,
    },
    HOST_MODE_WORKSPACE: {
        REPAIR_REASON_MANIFEST_UNREADABLE,
        REPAIR_REASON_MANIFEST_MISSING_HOST_PATH,
        REPAIR_REASON_HOST_PATH_MISSING,
        REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
        REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,
        REPAIR_REASON_WORKSPACE_PYTHON_MISSING,
        REPAIR_REASON_WORKSPACE_WRAPPER_UNREADABLE,
        REPAIR_REASON_WORKSPACE_WRAPPER_STALE,
    },
}


def _prefer_windows_gui_python(executable: str) -> str:
    candidate = Path(executable)
    if candidate.name.lower() == "python.exe":
        pythonw = candidate.with_name("pythonw.exe")
        if pythonw.exists():
            return str(pythonw)
    return str(candidate)


def _helper_program_args() -> list[str]:
    if getattr(sys, "frozen", False):
        current_exe = Path(sys.executable).resolve()
        if sys.platform == "darwin":
            helper_bundle = resolve_macos_sibling_bundle(current_exe, HELPER_APP_BUNDLE_NAME)
            if helper_bundle is None:
                raise RuntimeError(f"Helper app bundle not found next to: {current_exe}")
            helper_executable = helper_bundle / "Contents" / "MacOS" / HELPER_EXECUTABLE_NAME
            if not helper_executable.exists():
                raise RuntimeError(f"Helper executable not found: {helper_executable}")
            return [str(helper_executable)]
        if sys.platform.startswith("win"):
            helper_executable = resolve_windows_sibling_executable(
                current_exe,
                preferred_dir_name=HELPER_WINDOWS_DIR_NAME,
                exe_name=HELPER_WINDOWS_EXE_NAME,
            )
            if helper_executable is None:
                raise RuntimeError(f"Helper executable not found next to: {current_exe}")
            return [str(helper_executable)]
        return [str(current_exe)]

    entry = Path(__file__).resolve().parent / "helper_app.py"
    python_executable = (
        _prefer_windows_gui_python(sys.executable)
        if sys.platform.startswith("win")
        else sys.executable
    )
    return [python_executable, str(entry)]


def _host_file_dialog_filter() -> str:
    if sys.platform.startswith("win"):
        return "Helper Hosts (*.exe *.py);;All Files (*)"
    return t("dialogs.helper_install.host_filter")


def _browser_label(browser: str) -> str:
    return {
        "chrome": "Chrome",
        "brave": "Brave",
        "chromium": "Chromium",
    }.get(browser, browser.title())


def _host_mode_label(host_mode: str) -> str:
    return {
        HOST_MODE_BUNDLED: "Bundled host",
        HOST_MODE_WORKSPACE: "Workspace host",
        HOST_MODE_CUSTOM: "Custom host",
    }.get(host_mode, host_mode)


def _fixed_target_from_env(env: ExtensionEnvironment) -> Optional[BrowserConnectionTarget]:
    extension_id = resolve_extension_id(env, None)
    if not extension_id:
        return None
    return BrowserConnectionTarget(
        key=env.key,
        label=env.label,
        extension_id=extension_id,
        kind=TARGET_KIND_PROD,
        fixed=True,
    )


def _serialize_browser_connections(configs: list[BrowserConnectionConfig]) -> str:
    payload = {
        "version": 1,
        "browsers": [
            {
                "browser": config.browser,
                "host_mode": config.host_mode,
                "host_override_path": config.host_override_path,
                "targets": [
                    {
                        "key": target.key,
                        "label": target.label,
                        "extension_id": target.extension_id,
                        "kind": target.kind,
                        "fixed": target.fixed,
                    }
                    for target in config.targets
                ],
            }
            for config in configs
        ],
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)


def _deserialize_browser_connections(raw: str) -> list[BrowserConnectionConfig]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    browsers = payload.get("browsers") if isinstance(payload, dict) else None
    if not isinstance(browsers, list):
        return []
    configs: list[BrowserConnectionConfig] = []
    for item in browsers:
        if not isinstance(item, dict):
            continue
        browser = str(item.get("browser", "") or "").strip()
        host_mode = str(item.get("host_mode", "") or "").strip() or HOST_MODE_BUNDLED
        host_override_path = str(item.get("host_override_path", "") or "").strip() or None
        raw_targets = item.get("targets") if isinstance(item.get("targets"), list) else []
        targets: list[BrowserConnectionTarget] = []
        for raw_target in raw_targets:
            if not isinstance(raw_target, dict):
                continue
            extension_id = str(raw_target.get("extension_id", "") or "").strip()
            key = str(raw_target.get("key", "") or "").strip()
            label = str(raw_target.get("label", "") or "").strip()
            kind = str(raw_target.get("kind", "") or "").strip() or TARGET_KIND_UNPACKED
            if not browser or not extension_id or not key or not label:
                continue
            targets.append(
                BrowserConnectionTarget(
                    key=key,
                    label=label,
                    extension_id=extension_id,
                    kind=kind,
                    fixed=bool(raw_target.get("fixed", False)),
                )
            )
        if not browser or not targets:
            continue
        configs.append(
            BrowserConnectionConfig(
                browser=browser,
                host_mode=host_mode,
                host_override_path=host_override_path,
                targets=tuple(targets),
            )
        )
    return configs


def _migrate_legacy_browser_connections(ui_settings: QSettings) -> list[BrowserConnectionConfig]:
    env, extension_id = get_helper_environment(ui_settings)
    if not env or not extension_id:
        return []
    stored_host = str(ui_settings.value("helper/host_path", "") or "").strip()
    host_path = Path(stored_host).expanduser() if stored_host else default_host_script()
    host_mode = infer_host_mode(host_path) or HOST_MODE_BUNDLED
    host_override_path = None
    if host_mode in (HOST_MODE_WORKSPACE, HOST_MODE_CUSTOM):
        host_override_path = str(host_path)
    target = BrowserConnectionTarget(
        key=env.key,
        label=env.label,
        extension_id=extension_id,
        kind=TARGET_KIND_PROD if env.fixed else TARGET_KIND_UNPACKED,
        fixed=env.fixed,
    )
    return [
        BrowserConnectionConfig(
            browser=env.browser,
            host_mode=host_mode,
            host_override_path=host_override_path,
            targets=(target,),
        )
    ]


def load_browser_connections(ui_settings: QSettings) -> list[BrowserConnectionConfig]:
    raw = str(ui_settings.value(BROWSER_CONNECTIONS_KEY, "") or "").strip()
    if raw:
        configs = _deserialize_browser_connections(raw)
        if configs:
            return configs
    configs = _migrate_legacy_browser_connections(ui_settings)
    if configs:
        save_browser_connections(ui_settings, configs)
    return configs


def save_browser_connections(
    ui_settings: QSettings,
    configs: list[BrowserConnectionConfig],
) -> None:
    if not configs:
        ui_settings.remove(BROWSER_CONNECTIONS_KEY)
        return
    ui_settings.setValue(BROWSER_CONNECTIONS_KEY, _serialize_browser_connections(configs))


def _find_browser_config(
    configs: list[BrowserConnectionConfig],
    browser: str,
) -> Optional[BrowserConnectionConfig]:
    for config in configs:
        if config.browser == browser:
            return config
    return None


def _replace_browser_config(
    configs: list[BrowserConnectionConfig],
    replacement: BrowserConnectionConfig,
) -> list[BrowserConnectionConfig]:
    updated = [config for config in configs if config.browser != replacement.browser]
    updated.append(replacement)
    updated.sort(key=lambda config: config.browser)
    return updated


def _upsert_browser_target(
    configs: list[BrowserConnectionConfig],
    *,
    browser: str,
    target: BrowserConnectionTarget,
    host_mode: str,
    host_override_path: Optional[str],
) -> list[BrowserConnectionConfig]:
    existing = _find_browser_config(configs, browser)
    targets = []
    if existing:
        targets.extend(item for item in existing.targets if item.key != target.key)
    targets.append(target)
    targets.sort(key=lambda item: (item.kind != TARGET_KIND_PROD, item.label, item.extension_id))
    replacement = BrowserConnectionConfig(
        browser=browser,
        host_mode=host_mode,
        host_override_path=host_override_path,
        targets=tuple(targets),
    )
    return _replace_browser_config(configs, replacement)


def _remove_browser_target(
    configs: list[BrowserConnectionConfig],
    *,
    browser: str,
    target_key: str,
) -> list[BrowserConnectionConfig]:
    existing = _find_browser_config(configs, browser)
    if existing is None:
        return list(configs)
    remaining_targets = tuple(target for target in existing.targets if target.key != target_key)
    if not remaining_targets:
        updated = [config for config in configs if config.browser != browser]
        updated.sort(key=lambda config: config.browser)
        return updated
    replacement = BrowserConnectionConfig(
        browser=existing.browser,
        host_mode=existing.host_mode,
        host_override_path=existing.host_override_path,
        targets=remaining_targets,
    )
    return _replace_browser_config(configs, replacement)


def _browser_expected_ids(config: Optional[BrowserConnectionConfig]) -> tuple[str, ...]:
    if config is None:
        return ()
    return tuple(target.extension_id for target in config.targets)


def _remember_last_helper_selection(
    ui_settings: QSettings,
    *,
    target: BrowserConnectionTarget,
    host_path: Path,
) -> None:
    ui_settings.setValue("helper/extension_env", target.key)
    ui_settings.setValue("helper/extension_id", target.extension_id)
    ui_settings.setValue(f"helper/extension_id/{target.key}", target.extension_id)
    ui_settings.setValue("helper/host_path", str(host_path))
    ui_settings.setValue("helper/host_path_env", target.key)


def _host_path_for_config(
    config: BrowserConnectionConfig,
) -> Optional[tuple[BrowserConnectionConfig, Path]]:
    host_path = resolve_host_path_for_mode(
        config.host_mode,
        host_override_path=config.host_override_path,
    )
    if host_path is not None and host_path.exists():
        return config, host_path
    return None


def _is_auto_repair_safe(
    config: BrowserConnectionConfig,
    status,
) -> bool:
    if status.state != HELPER_STATE_NEEDS_REPAIR:
        return False
    if config.host_mode == HOST_MODE_CUSTOM:
        return False
    if status.unexpected_extension_ids:
        return False
    safe_reasons = _AUTO_REPAIR_SAFE_REASONS.get(config.host_mode, set())
    if not safe_reasons:
        return False
    if not status.repair_reasons:
        return False
    return all(reason in safe_reasons for reason in status.repair_reasons)


def auto_repair_browser_connections(ui_settings: QSettings) -> bool:
    configs = load_browser_connections(ui_settings)
    repaired_any = False
    for config in configs:
        status = inspect_helper_installation(
            browser=config.browser,
            expected_extension_ids=_browser_expected_ids(config),
        )
        if not _is_auto_repair_safe(config, status):
            continue
        resolved = _host_path_for_config(config)
        if resolved is None:
            continue
        _, host_path = resolved
        log_helper_install(
            f"[Helper] Auto-repairing browser connection for {config.browser}: "
            f"reasons={status.repair_reasons}"
        )
        result = install_helper(
            extension_ids=[target.extension_id for target in config.targets],
            browser=config.browser,
            host_path=host_path,
        )
        if not result.installed:
            log_helper_install(
                f"[Helper] Auto-repair failed for {config.browser}: {result.message}"
            )
            continue
        remember_target = config.targets[0] if config.targets else None
        if remember_target is not None:
            _remember_last_helper_selection(
                ui_settings,
                target=remember_target,
                host_path=host_path,
            )
        repaired_any = True
    if repaired_any:
        try:
            ensure_helper_autostart()
        except Exception as exc:  # noqa: BLE001
            log_helper_install(f"[Helper] Auto-repair autostart setup failed: {exc}")
    return repaired_any


def helper_connection_overall_state(ui_settings: QSettings) -> str:
    configs = load_browser_connections(ui_settings)
    statuses = [
        inspect_helper_installation(
            browser=config.browser,
            expected_extension_ids=_browser_expected_ids(config),
        )
        for config in configs
    ]
    covered_browsers = {config.browser for config in configs}
    envs, _ = load_extension_environments()
    fixed_ids_by_browser: dict[str, list[str]] = {}
    for env in envs:
        target = _fixed_target_from_env(env)
        if target is None or env.browser in covered_browsers:
            continue
        fixed_ids_by_browser.setdefault(env.browser, []).append(target.extension_id)
    statuses.extend(
        inspect_helper_installation(browser=browser, expected_extension_ids=extension_ids)
        for browser, extension_ids in fixed_ids_by_browser.items()
    )
    if any(status.state == HELPER_STATE_NEEDS_REPAIR for status in statuses):
        return HELPER_STATE_NEEDS_REPAIR
    if any(status.state == HELPER_STATE_CONFIGURED for status in statuses):
        return HELPER_STATE_CONFIGURED
    return HELPER_STATE_NOT_CONFIGURED


def helper_connection_summary_text(ui_settings: QSettings) -> str:
    state = helper_connection_overall_state(ui_settings)
    if state == HELPER_STATE_NEEDS_REPAIR:
        return t("settings.helper_status_needs_repair")
    if state == HELPER_STATE_CONFIGURED:
        return t("settings.helper_status_installed")
    return t("settings.helper_status_missing")


def get_helper_environment(
    ui_settings: QSettings,
) -> tuple[Optional[ExtensionEnvironment], Optional[str]]:
    envs, default_key = load_extension_environments()
    if not envs:
        log_helper_install("[Helper] get_helper_environment: no environments loaded.")
        return None, None
    stored_key = ui_settings.value("helper/extension_env", default_key)
    env = get_environment(str(stored_key), envs)
    if not env:
        log_helper_install("[Helper] get_helper_environment: stored environment not found.")
        return None, None
    custom_key = f"helper/extension_id/{env.key}"
    custom_id = str(ui_settings.value(custom_key, "") or "")
    extension_id = resolve_extension_id(env, custom_id)
    log_helper_install(
        f"[Helper] get_helper_environment: env={env.key} browser={env.browser} "
        f"extension_id={'set' if extension_id else 'missing'}"
    )
    return env, extension_id


def prompt_for_helper_environment(
    parent,
    ui_settings: QSettings,
) -> Optional[Tuple[ExtensionEnvironment, str, Path]]:
    envs, default_key = load_extension_environments()
    if not envs:
        log_helper_install("[Helper] No extension environments available.")
        return None
    stored_key = ui_settings.value("helper/extension_env", default_key)
    current_env = get_environment(str(stored_key), envs)
    labels = [env.label for env in envs]
    current_index = envs.index(current_env) if current_env in envs else 0
    label, ok = QInputDialog.getItem(
        parent,
        t("dialogs.helper_install.env_title"),
        t("dialogs.helper_install.env_prompt"),
        labels,
        current_index,
        False,
    )
    if not ok:
        log_helper_install("[Helper] Helper install canceled at environment prompt.")
        return None
    env = envs[labels.index(label)]
    ui_settings.setValue("helper/extension_env", env.key)
    custom_key = f"helper/extension_id/{env.key}"
    custom_id = str(ui_settings.value(custom_key, "") or "")
    extension_id = resolve_extension_id(env, custom_id)
    if not extension_id:
        log_helper_install(f"[Helper] Extension id missing for env={env.key}; prompting user.")
        extension_id, ok = QInputDialog.getText(
            parent,
            t("dialogs.helper_install.title"),
            t("dialogs.helper_install.prompt"),
            text=str(custom_id),
        )
        if not ok or not extension_id.strip():
            log_helper_install("[Helper] Helper install canceled at extension id prompt.")
            return None
        extension_id = extension_id.strip()
        ui_settings.setValue(custom_key, extension_id)
    ui_settings.setValue("helper/extension_id", extension_id)
    stored_host = str(ui_settings.value("helper/host_path", "") or "")
    stored_host_env = str(ui_settings.value("helper/host_path_env", "") or "")
    default_host = default_host_script()
    log_helper_install(f"[Helper] Resolved default host path: {default_host}")
    host_path = None
    if stored_host and stored_host_env == env.key:
        candidate = Path(stored_host)
        if candidate.exists():
            log_helper_install(f"[Helper] Using stored host path: {candidate}")
            host_path = candidate
    if host_path is None:
        host_path = default_host
    if not host_path.exists():
        if default_host.exists():
            host_path = default_host
        else:
            log_helper_install("[Helper] Host not found; prompting user to locate helper script.")
            filename, _ = QFileDialog.getOpenFileName(
                parent,
                t("dialogs.helper_install.host_title"),
                str(Path.home()),
                _host_file_dialog_filter(),
            )
            if not filename:
                log_helper_install("[Helper] Helper install canceled at host picker.")
                return None
            host_path = Path(filename)
    log_helper_install(f"[Helper] Selected host path: {host_path} exists={host_path.exists()}")
    ui_settings.setValue("helper/host_path", str(host_path))
    ui_settings.setValue("helper/host_path_env", env.key)
    return env, extension_id, host_path


def manage_browser_connections(parent, ui_settings: QSettings) -> None:
    from helper_connections_dialog import BrowserConnectionsDialog

    dialog = BrowserConnectionsDialog(parent, ui_settings)
    dialog.exec()


def ensure_helper_autostart() -> None:
    if sys.platform != "darwin" and not sys.platform.startswith("win"):
        raise RuntimeError("Helper autostart is currently supported on macOS and Windows only.")
    program_args = _helper_program_args()
    log_helper(f"[Helper] Ensuring helper autostart with args: {program_args}")
    if not install_helper_autostart(
        program_args,
        associated_bundle_identifiers=[HELPER_BUNDLE_IDENTIFIER, MAIN_BUNDLE_IDENTIFIER],
    ):
        raise RuntimeError("Failed to install helper autostart for helper tray.")


def auto_install_helper(ui_settings: QSettings) -> bool:
    if auto_repair_browser_connections(ui_settings):
        return True
    envs, default_key = load_extension_environments()
    if not envs:
        log_helper("[Helper] auto_install_helper: no environments loaded.")
        return False
    stored_key = ui_settings.value("helper/extension_env", default_key)
    env = get_environment(str(stored_key), envs)
    if not env:
        log_helper("[Helper] auto_install_helper: environment not found.")
        return False
    custom_key = f"helper/extension_id/{env.key}"
    custom_id = str(ui_settings.value(custom_key, "") or "")
    extension_id = resolve_extension_id(env, custom_id)
    if is_helper_installed(extension_id, browser=env.browser):
        log_helper(f"[Helper] auto_install_helper: already installed for {env.key}.")
        try:
            ensure_helper_autostart()
            return True
        except Exception as exc:  # noqa: BLE001
            log_helper(f"[Helper] auto_install_helper: failed to ensure helper autostart: {exc}")
            return False
    if not extension_id or not env.fixed:
        log_helper("[Helper] auto_install_helper: missing fixed extension id; skipping.")
        return False
    host_path = default_host_script()
    if not host_path.exists():
        log_helper(f"[Helper] auto_install_helper: host missing at {host_path}")
        return False
    result = install_helper(extension_id=extension_id, browser=env.browser, host_path=host_path)
    if result.installed:
        ui_settings.setValue("helper/extension_env", env.key)
        ui_settings.setValue("helper/extension_id", extension_id)
        ui_settings.setValue(custom_key, extension_id)
        ui_settings.setValue("helper/host_path", str(host_path))
        ui_settings.setValue("helper/host_path_env", env.key)
        try:
            ensure_helper_autostart()
            return True
        except Exception as exc:  # noqa: BLE001
            log_helper(
                f"[Helper] auto_install_helper: helper installed but autostart failed: {exc}"
            )
            return False
    return False
