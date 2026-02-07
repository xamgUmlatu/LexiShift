from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional, Tuple

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QInputDialog, QFileDialog

from helper_installer import (
    ExtensionEnvironment,
    default_host_script,
    get_environment,
    install_helper,
    install_launch_agent,
    is_helper_installed,
    log_helper_install,
    load_extension_environments,
    resolve_extension_id,
)
from helper_logger import log_helper
from i18n import t

HELPER_APP_BUNDLE_NAME = "LexiShift Helper.app"
HELPER_EXECUTABLE_NAME = "LexiShiftHelper"
HELPER_BUNDLE_IDENTIFIER = "com.lexishift.helper.agent"
MAIN_BUNDLE_IDENTIFIER = "com.lexishift.app"


def get_helper_environment(ui_settings: QSettings) -> tuple[Optional[ExtensionEnvironment], Optional[str]]:
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
                t("dialogs.helper_install.host_filter"),
            )
            if not filename:
                log_helper_install("[Helper] Helper install canceled at host picker.")
                return None
            host_path = Path(filename)
    log_helper_install(f"[Helper] Selected host path: {host_path} exists={host_path.exists()}")
    ui_settings.setValue("helper/host_path", str(host_path))
    ui_settings.setValue("helper/host_path_env", env.key)
    return env, extension_id, host_path


def ensure_helper_autostart() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("Helper autostart is currently supported on macOS only.")
    if getattr(sys, "frozen", False):
        current_exe = Path(sys.executable).resolve()
        current_macos_dir = current_exe.parent
        current_contents_dir = current_macos_dir.parent
        current_bundle_dir = current_contents_dir.parent
        if current_macos_dir.name != "MacOS" or current_contents_dir.name != "Contents" or current_bundle_dir.suffix != ".app":
            raise RuntimeError(f"Unexpected app executable layout: {current_exe}")
        helper_bundle = current_bundle_dir.with_name(HELPER_APP_BUNDLE_NAME)
        helper_executable = helper_bundle / "Contents" / "MacOS" / HELPER_EXECUTABLE_NAME
        if not helper_executable.exists():
            raise RuntimeError(f"Helper executable not found: {helper_executable}")
        program_args = [str(helper_executable)]
    else:
        entry = Path(__file__).resolve().parent / "helper_app.py"
        program_args = [sys.executable, str(entry)]
    log_helper(f"[Helper] Ensuring LaunchAgent with args: {program_args}")
    if not install_launch_agent(
        program_args,
        associated_bundle_identifiers=[HELPER_BUNDLE_IDENTIFIER, MAIN_BUNDLE_IDENTIFIER],
    ):
        raise RuntimeError("Failed to install LaunchAgent for helper tray.")


def auto_install_helper(ui_settings: QSettings) -> bool:
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
            log_helper(f"[Helper] auto_install_helper: helper installed but autostart failed: {exc}")
            return False
    return False
