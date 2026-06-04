from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import stat
import sys
from typing import Optional, Sequence
import shutil
import subprocess
import plistlib

from frozen_layout import (
    NATIVE_HOST_WINDOWS_DIR_NAME,
    NATIVE_HOST_WINDOWS_EXE_NAME,
    resolve_windows_sibling_executable,
)
from helper_connection_models import (
    BrowserConnectionConfig,
    BrowserConnectionTarget,
    ExtensionEnvironment,
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
    HELPER_STATE_NOT_CONFIGURED,
    HelperInstallStatus,
    HOST_MODE_BUNDLED,
    HOST_MODE_CUSTOM,
    HOST_MODE_WORKSPACE,
    TARGET_KIND_PROD,
    TARGET_KIND_UNPACKED,
)
from helper_connection_inspection import (
    bundled_freshness_issue as _bundled_freshness_issue,
    inspect_helper_installation as _inspect_helper_installation,
    workspace_wrapper_issue as _workspace_wrapper_issue,
)
from helper_extension_environments import (
    get_environment,
    load_extension_environments,
    resolve_extension_id,
)
from helper_native_messaging_support import (
    build_workspace_wrapper_script as _build_workspace_wrapper_script,
    extension_id_from_origin as _extension_id_from_origin,
    hash_directory as _hash_directory,
    hash_file as _hash_file,
    normalize_extension_ids as _normalize_extension_ids,
    origin_for_extension_id as _origin_for_extension_id,
    resolve_workspace_python as _resolve_workspace_python,
    resolve_workspace_host_script,
    resolve_host_path_for_mode as _resolve_host_path_for_mode,
    stable_bundled_core_path as _stable_bundled_core_path,
    stable_bundled_host_path as _stable_bundled_host_path,
    workspace_host_wrapper_path as _workspace_host_wrapper_path,
)
from utils_paths import resource_path
from helper_logger import log_helper

__all__ = [
    "BrowserConnectionConfig",
    "BrowserConnectionTarget",
    "ExtensionEnvironment",
    "HelperInstallResult",
    "HelperInstallStatus",
    "get_environment",
    "HOST_MODE_BUNDLED",
    "HOST_MODE_CUSTOM",
    "HOST_MODE_WORKSPACE",
    "TARGET_KIND_PROD",
    "TARGET_KIND_UNPACKED",
    "HELPER_STATE_CONFIGURED",
    "HELPER_STATE_NEEDS_REPAIR",
    "HELPER_STATE_NOT_CONFIGURED",
    "load_extension_environments",
    "resolve_extension_id",
]


@dataclass(frozen=True)
class HelperInstallResult:
    installed: bool
    message: str
    manifest_path: Optional[Path] = None


WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RUN_VALUE_NAME = "LexiShiftHelper"
NATIVE_HOST_NAME = "com.lexishift.helper"
WINDOWS_NATIVE_MESSAGING_REGISTRY_KEYS = {
    "chrome": rf"Software\Google\Chrome\NativeMessagingHosts\{NATIVE_HOST_NAME}",
    "chromium": rf"Software\Chromium\NativeMessagingHosts\{NATIVE_HOST_NAME}",
    # Brave is Chromium-based but keeps its own host registration tree.
    "brave": rf"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\{NATIVE_HOST_NAME}",
}


def _helper_log_path() -> Path:
    return _helper_data_root() / "helper_install.log"


def _log_helper_file(message: str) -> None:
    try:
        stamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        _helper_log_path().write_text(
            "", encoding="utf-8"
        ) if not _helper_log_path().exists() else None
        with _helper_log_path().open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {message}\n")
    except OSError:
        pass


def log_helper_install(message: str) -> None:
    log_helper(message)
    _log_helper_file(message)


def _log_app_bundle_info() -> None:
    if sys.platform != "darwin":
        return
    try:
        exe = Path(sys.executable).resolve()
        contents = exe.parent.parent
        info_plist = contents / "Info.plist"
        resources = contents / "Resources"
        icon_file = None
        if info_plist.exists():
            with info_plist.open("rb") as handle:
                plist = plistlib.load(handle)
            icon_file = plist.get("CFBundleIconFile")
        icon_path = None
        if icon_file:
            icon_name = str(icon_file)
            if not icon_name.endswith(".icns"):
                icon_name = icon_name + ".icns"
            icon_path = resources / icon_name
        log_helper(f"[Helper] App bundle: exe={exe} contents={contents} resources={resources}")
        log_helper(
            f"[Helper] App icon file={icon_file} resolved={icon_path} exists={icon_path.exists() if icon_path else None}"
        )
        _log_helper_file(f"App bundle exe={exe} contents={contents} resources={resources}")
        _log_helper_file(
            f"App icon file={icon_file} resolved={icon_path} exists={icon_path.exists() if icon_path else None}"
        )
    except Exception as exc:
        log_helper(f"[Helper] Failed to inspect app bundle icon: {exc}")
        _log_helper_file(f"Failed to inspect app bundle icon: {exc}")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def workspace_host_script() -> Optional[Path]:
    path = resolve_workspace_host_script()
    if path is None:
        log_helper_install("[Helper] Unable to resolve runtime repo root for workspace host.")
        return None
    log_helper_install(f"[Helper] Resolved workspace host path: {path} exists={path.exists()}")
    return path


def default_host_script() -> Path:
    override = os.environ.get("LEXISHIFT_HELPER_HOST")
    if override:
        log_helper_install(f"[Helper] Using override host path: {override}")
        return Path(override)
    log_helper_install(
        f"[Helper] frozen={getattr(sys, 'frozen', False)}, _MEIPASS={getattr(sys, '_MEIPASS', None)}"
    )
    if getattr(sys, "frozen", False) and sys.platform.startswith("win"):
        current_exe = Path(sys.executable).resolve()
        bundled_host = resolve_windows_sibling_executable(
            current_exe,
            preferred_dir_name=NATIVE_HOST_WINDOWS_DIR_NAME,
            exe_name=NATIVE_HOST_WINDOWS_EXE_NAME,
        )
        log_helper_install(
            f"[Helper] Bundled Windows host candidate: {bundled_host} "
            f"exists={bundled_host.exists() if bundled_host else False}"
        )
        if bundled_host and bundled_host.exists():
            return bundled_host
    bundled = Path(resource_path("helper", "lexishift_native_host.py"))
    log_helper_install(f"[Helper] Bundled host candidate: {bundled} exists={bundled.exists()}")
    if bundled.exists():
        return bundled
    if getattr(sys, "frozen", False):
        candidate = _helper_data_root() / "helper" / "lexishift_native_host.py"
        log_helper_install(
            f"[Helper] Frozen app, bundled not found. Checking installed candidate: {candidate} exists={candidate.exists()}"
        )
        return candidate
    repo_path = _repo_root() / "scripts" / "helper" / "lexishift_native_host.py"
    log_helper_install(
        f"[Helper] Dev mode, using repo path: {repo_path} exists={repo_path.exists()}"
    )
    return repo_path


def stable_bundled_host_path() -> Path:
    return _stable_bundled_host_path(
        _helper_data_root(),
        is_windows=sys.platform.startswith("win"),
        windows_host_executable_name=f"{NATIVE_HOST_WINDOWS_EXE_NAME}.exe",
    )


def stable_bundled_core_path() -> Path:
    return _stable_bundled_core_path(_helper_data_root())


def workspace_host_wrapper_path() -> Path:
    return _workspace_host_wrapper_path(_helper_data_root())


def resolve_host_path_for_mode(
    host_mode: str,
    *,
    host_override_path: Optional[str] = None,
) -> Optional[Path]:
    return _resolve_host_path_for_mode(
        host_mode,
        host_override_path=host_override_path,
        default_host_resolver=default_host_script,
        workspace_host_resolver=workspace_host_script,
    )


def _helper_data_root() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        root = Path(base) / "LexiShift" / "LexiShift"
    else:
        root = home / ".local" / "share" / "LexiShift" / "LexiShift"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _ensure_workspace_host_wrapper(host_script: Path) -> Optional[Path]:
    if sys.platform.startswith("win"):
        return None
    python_path = _resolve_workspace_python(
        host_script,
        validate=True,
        log=log_helper_install,
    )
    if python_path is None:
        log_helper_install(
            f"[Helper] Unable to resolve compatible workspace Python for host {host_script}"
        )
        return None
    wrapper_path = workspace_host_wrapper_path()
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(
        _build_workspace_wrapper_script(host_script, python_path),
        encoding="utf-8",
    )
    try:
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)
    except OSError:
        pass
    log_helper_install(
        f"[Helper] Prepared workspace host wrapper: {wrapper_path} python={python_path} host={host_script}"
    )
    return wrapper_path


def _is_bundled_path(path: Path) -> bool:
    if not getattr(sys, "frozen", False):
        return False
    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    try:
        path.resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def _ensure_stable_helper(host_path: Path) -> Path:
    if sys.platform.startswith("win") and host_path.suffix.lower() == ".exe":
        target_dir = _helper_data_root() / "helper" / "native_host"
        resolved_host = host_path.resolve()
        if resolved_host.parent == target_dir.resolve():
            log_helper_install(
                f"[Helper] Windows native host already stable at {resolved_host}; skipping copy."
            )
            return host_path
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(host_path.parent, target_dir)
            target_host = target_dir / host_path.name
            log_helper_install(f"[Helper] Copied Windows native host directory to {target_dir}")
            return target_host
        except OSError as e:
            log_helper_install(f"[Helper] Failed to copy Windows native host to {target_dir}: {e}")
            return host_path
    if not _is_bundled_path(host_path):
        log_helper_install(f"[Helper] Host path {host_path} is not bundled; skipping stable copy.")
        return host_path
    target_dir = _helper_data_root() / "helper"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_host = target_dir / "lexishift_native_host.py"

    # 1. Copy the host script
    try:
        shutil.copy2(host_path, target_host)
        log_helper_install(f"[Helper] Copied bundled host to {target_host}")
    except OSError as e:
        log_helper_install(f"[Helper] Failed to copy bundled host to {target_host}: {e}")
        # If copy fails, we return the original path, but this is risky for one-file apps.
        return host_path

    # 2. Copy lexishift_core dependency
    # Look in the same dir as host, or one level up (bundle root)
    candidates = [
        host_path.parent / "lexishift_core",
        host_path.parent.parent / "lexishift_core",
        host_path.parent.parent.parent / "lexishift_core",
    ]
    core_src = next((c for c in candidates if c.exists() and c.is_dir()), None)

    if core_src:
        core_dst = target_dir / "lexishift_core"
        try:
            if core_dst.exists():
                shutil.rmtree(core_dst)
            shutil.copytree(core_src, core_dst, dirs_exist_ok=True)
            log_helper_install(f"[Helper] Copied lexishift_core from {core_src} to {core_dst}")
        except OSError as e:
            log_helper_install(f"[Helper] Failed to copy lexishift_core: {e}")
    else:
        log_helper_install(f"[Helper] Warning: lexishift_core not found in bundle near {host_path}")

    return target_host


def launch_agent_path() -> Optional[Path]:
    if sys.platform != "darwin":
        return None
    return Path.home() / "Library" / "LaunchAgents" / "com.lexishift.helper.plist"


def build_launch_agent(
    program_args: Sequence[str],
    *,
    associated_bundle_identifiers: Sequence[str] | None = None,
) -> str:
    args = "\n".join([f"    <string>{arg}</string>" for arg in program_args])
    associated_ids = [
        str(value).strip() for value in (associated_bundle_identifiers or []) if str(value).strip()
    ]
    associated_xml = ""
    if associated_ids:
        associated_values = "\n".join(
            [f"      <string>{bundle_id}</string>" for bundle_id in associated_ids]
        )
        associated_xml = (
            "    <key>AssociatedBundleIdentifiers</key>\n"
            "    <array>\n"
            f"{associated_values}\n"
            "    </array>\n"
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.lexishift.helper</string>
    <key>ProgramArguments</key>
    <array>
{args}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
{associated_xml.rstrip()}
  </dict>
</plist>
"""


def install_launch_agent(
    program_args: Sequence[str],
    *,
    associated_bundle_identifiers: Sequence[str] | None = None,
) -> bool:
    plist_path = launch_agent_path()
    if not plist_path:
        log_helper("[Helper] LaunchAgent not supported on this platform.")
        return False
    _log_app_bundle_info()
    log_helper(f"[Helper] LaunchAgent program args: {program_args}")
    if associated_bundle_identifiers:
        log_helper(
            f"[Helper] LaunchAgent associated bundle ids: {list(associated_bundle_identifiers)}"
        )
    _log_helper_file(f"LaunchAgent program args: {program_args}")
    if associated_bundle_identifiers:
        _log_helper_file(
            f"LaunchAgent associated bundle ids: {list(associated_bundle_identifiers)}"
        )
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(
        build_launch_agent(
            program_args, associated_bundle_identifiers=associated_bundle_identifiers
        ),
        encoding="utf-8",
    )
    log_helper(f"[Helper] Installed LaunchAgent: {plist_path}")
    _log_helper_file(f"Installed LaunchAgent: {plist_path}")
    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
    subprocess.run(["launchctl", "load", str(plist_path)], check=False)
    return True


def build_windows_startup_command(program_args: Sequence[str]) -> str:
    return subprocess.list2cmdline([str(value) for value in program_args])


def install_windows_startup(program_args: Sequence[str]) -> bool:
    if not sys.platform.startswith("win"):
        log_helper("[Helper] Windows startup registration is not supported on this platform.")
        return False
    command = build_windows_startup_command(program_args)
    try:
        import winreg

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            WINDOWS_RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, WINDOWS_RUN_VALUE_NAME, 0, winreg.REG_SZ, command)
    except OSError as exc:
        log_helper(f"[Helper] Failed to register Windows startup command: {exc}")
        _log_helper_file(f"Failed to register Windows startup command: {exc}")
        return False
    log_helper(f"[Helper] Registered Windows startup command: {command}")
    _log_helper_file(f"Registered Windows startup command: {command}")
    return True


def install_helper_autostart(
    program_args: Sequence[str],
    *,
    associated_bundle_identifiers: Sequence[str] | None = None,
) -> bool:
    if sys.platform == "darwin":
        return install_launch_agent(
            program_args,
            associated_bundle_identifiers=associated_bundle_identifiers,
        )
    if sys.platform.startswith("win"):
        return install_windows_startup(program_args)
    log_helper("[Helper] Helper autostart is not supported on this platform.")
    return False


def _windows_native_messaging_registry_key(browser: str) -> str:
    return WINDOWS_NATIVE_MESSAGING_REGISTRY_KEYS.get(
        browser, WINDOWS_NATIVE_MESSAGING_REGISTRY_KEYS["chrome"]
    )


def _windows_registry_view_flags(winreg) -> list[int]:
    flags = [0]
    for name in ("KEY_WOW64_32KEY", "KEY_WOW64_64KEY"):
        flag = int(getattr(winreg, name, 0) or 0)
        if flag and flag not in flags:
            flags.append(flag)
    return flags


def _write_windows_native_messaging_registry(browser: str, manifest: Path) -> bool:
    if not sys.platform.startswith("win"):
        return False
    try:
        import winreg
    except ImportError:
        log_helper_install("[Helper] winreg unavailable; cannot register Windows native messaging.")
        return False
    registry_key = _windows_native_messaging_registry_key(browser)
    wrote_any = False
    errors: list[str] = []
    for view_flag in _windows_registry_view_flags(winreg):
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                registry_key,
                0,
                winreg.KEY_SET_VALUE | view_flag,
            ) as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, str(manifest))
            wrote_any = True
        except OSError as exc:
            errors.append(str(exc))
    if not wrote_any:
        log_helper_install(
            f"[Helper] Failed to register native messaging manifest for {browser}: {errors}"
        )
        return False
    if errors:
        log_helper_install(
            f"[Helper] Native messaging manifest registered for {browser} with partial registry-view errors: {errors}"
        )
    else:
        log_helper_install(
            f"[Helper] Registered native messaging manifest for {browser}: {manifest}"
        )
    return True


def _read_windows_native_messaging_manifest(browser: str) -> Optional[Path]:
    if not sys.platform.startswith("win"):
        return None
    try:
        import winreg
    except ImportError:
        return None
    registry_key = _windows_native_messaging_registry_key(browser)
    for view_flag in _windows_registry_view_flags(winreg):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                registry_key,
                0,
                winreg.KEY_QUERY_VALUE | view_flag,
            ) as key:
                value, _ = winreg.QueryValueEx(key, None)
            if value:
                return Path(str(value))
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return None


def _chrome_host_dir(browser: str = "chrome") -> Optional[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        if browser == "chromium":
            return home / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts"
        if browser == "brave":
            return (
                home
                / "Library"
                / "Application Support"
                / "BraveSoftware"
                / "Brave-Browser"
                / "NativeMessagingHosts"
            )
        return (
            home / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
        )
    if sys.platform.startswith("win"):
        return None
    return home / ".config" / "google-chrome" / "NativeMessagingHosts"


def manifest_path(browser: str = "chrome") -> Optional[Path]:
    if sys.platform.startswith("win"):
        return _helper_data_root() / "native_messaging" / browser / f"{NATIVE_HOST_NAME}.json"
    base = _chrome_host_dir(browser)
    if base is None:
        return None
    return base / f"{NATIVE_HOST_NAME}.json"


def _candidate_core_dirs(host_path: Path) -> tuple[Path, ...]:
    return (
        host_path.parent / "lexishift_core",
        host_path.parent.parent / "lexishift_core",
        host_path.parent.parent.parent / "lexishift_core",
    )


def _find_core_dir(host_path: Path) -> Optional[Path]:
    return next(
        (candidate for candidate in _candidate_core_dirs(host_path) if candidate.is_dir()), None
    )


def infer_host_mode(host_path: Optional[Path]) -> Optional[str]:
    if host_path is None:
        return None
    try:
        resolved = host_path.resolve()
    except OSError:
        resolved = host_path
    workspace_wrapper = workspace_host_wrapper_path()
    try:
        if resolved == workspace_wrapper.resolve():
            return HOST_MODE_WORKSPACE
    except OSError:
        if resolved == workspace_wrapper:
            return HOST_MODE_WORKSPACE
    workspace = workspace_host_script()
    if workspace is not None:
        try:
            if resolved == workspace.resolve():
                return HOST_MODE_WORKSPACE
        except OSError:
            if resolved == workspace:
                return HOST_MODE_WORKSPACE
    stable_path = stable_bundled_host_path()
    try:
        if resolved == stable_path.resolve():
            return HOST_MODE_BUNDLED
    except OSError:
        if resolved == stable_path:
            return HOST_MODE_BUNDLED
    if _is_bundled_path(host_path):
        return HOST_MODE_BUNDLED
    return HOST_MODE_CUSTOM


def _bundled_source_host() -> Optional[Path]:
    source = default_host_script()
    if not source.exists():
        return None
    if _is_bundled_path(source):
        return source
    if sys.platform.startswith("win") and getattr(sys, "frozen", False):
        stable_path = stable_bundled_host_path()
        try:
            if source.resolve() != stable_path.resolve():
                return source
        except OSError:
            if source != stable_path:
                return source
    return None


def build_manifest(*, host_path: Path, extension_ids: Sequence[str]) -> dict:
    allowed_origins = [
        _origin_for_extension_id(extension_id)
        for extension_id in _normalize_extension_ids(extension_ids)
    ]
    return {
        "name": NATIVE_HOST_NAME,
        "description": "LexiShift local helper for rule generation and SRS syncing.",
        "path": str(host_path),
        "type": "stdio",
        "allowed_origins": allowed_origins,
    }


def inspect_helper_installation(
    *,
    browser: str = "chrome",
    expected_extension_ids: Sequence[str] = (),
) -> HelperInstallStatus:
    return _inspect_helper_installation(
        browser=browser,
        expected_extension_ids=expected_extension_ids,
        read_windows_manifest=_read_windows_native_messaging_manifest,
        manifest_path=manifest_path,
        normalize_extension_ids=_normalize_extension_ids,
        extension_id_from_origin=_extension_id_from_origin,
        infer_host_mode=infer_host_mode,
        bundled_freshness_issue=lambda host_path: _bundled_freshness_issue(
            host_path,
            bundled_source_host=_bundled_source_host,
            stable_bundled_host_path=stable_bundled_host_path,
            hash_file=_hash_file,
            stable_bundled_core_path=stable_bundled_core_path,
            find_core_dir=_find_core_dir,
            hash_directory=_hash_directory,
            is_windows=sys.platform.startswith("win"),
        ),
        workspace_wrapper_issue=lambda host_path: _workspace_wrapper_issue(
            host_path,
            workspace_host_script=workspace_host_script,
            workspace_host_wrapper_path=workspace_host_wrapper_path,
            resolve_workspace_python=_resolve_workspace_python,
            build_workspace_wrapper_script=_build_workspace_wrapper_script,
        ),
    )


def is_helper_installed(extension_id: Optional[str] = None, *, browser: str = "chrome") -> bool:
    expected_ids = [extension_id] if extension_id else ()
    status = inspect_helper_installation(browser=browser, expected_extension_ids=expected_ids)
    log_helper_install(
        f"[Helper] is_helper_installed: browser={browser} state={status.state} "
        f"host={status.host_path} message={status.message}"
    )
    return status.state == HELPER_STATE_CONFIGURED


def install_helper(
    *,
    extension_id: Optional[str] = None,
    extension_ids: Optional[Sequence[str]] = None,
    browser: str = "chrome",
    host_path: Optional[Path] = None,
) -> HelperInstallResult:
    normalized_ids = _normalize_extension_ids(
        extension_ids or ([extension_id] if extension_id else ())
    )
    if not normalized_ids:
        log_helper_install("[Helper] install_helper failed: missing extension id.")
        return HelperInstallResult(False, "At least one extension ID is required.")
    manifest = manifest_path(browser)
    if manifest is None:
        log_helper_install("[Helper] install_helper failed: unsupported OS.")
        return HelperInstallResult(False, "Helper install not supported on this OS yet.")
    host_path = host_path or default_host_script()
    log_helper_install(
        f"[Helper] install_helper: host_path={host_path} exists={host_path.exists()}"
    )

    resolved_mode = infer_host_mode(host_path)
    if resolved_mode == HOST_MODE_WORKSPACE and not sys.platform.startswith("win"):
        stable_path = _ensure_workspace_host_wrapper(host_path)
        if stable_path is None:
            return HelperInstallResult(
                False,
                "Workspace host wrapper could not be prepared. Ensure the repo .venv is available.",
            )
    else:
        # Force copy to stable location and use THAT path for the manifest
        stable_path = _ensure_stable_helper(host_path)
    log_helper_install(
        f"[Helper] install_helper: stable_path={stable_path} exists={stable_path.exists()}"
    )

    if not stable_path.exists():
        log_helper_install(
            f"[Helper] install_helper failed: stable host not found at {stable_path}"
        )
        return HelperInstallResult(False, f"Helper host not found: {stable_path}")
    if sys.platform.startswith("win") and stable_path.suffix.lower() != ".exe":
        log_helper_install(
            f"[Helper] install_helper failed: Windows native host must be an .exe, got {stable_path}"
        )
        return HelperInstallResult(
            False,
            "Windows helper install requires a native host executable (.exe).",
        )
    try:
        mode = stable_path.stat().st_mode
        stable_path.chmod(mode | stat.S_IEXEC)
    except OSError:
        pass
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = build_manifest(host_path=stable_path, extension_ids=normalized_ids)
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if sys.platform.startswith("win") and not _write_windows_native_messaging_registry(
        browser, manifest
    ):
        return HelperInstallResult(False, "Failed to register Windows native messaging host.")
    log_helper(f"[Helper] install_helper wrote manifest: {manifest}")
    _log_helper_file(f"install_helper wrote manifest: {manifest}")
    _log_helper_file(f"manifest payload: {payload}")
    return HelperInstallResult(True, "Helper installed.", manifest)
