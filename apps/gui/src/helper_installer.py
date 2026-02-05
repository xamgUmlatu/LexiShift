from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import sys
from typing import Optional, Sequence
import shutil
import subprocess

from utils_paths import resource_path
from helper_logger import log_helper


@dataclass(frozen=True)
class HelperInstallResult:
    installed: bool
    message: str
    manifest_path: Optional[Path] = None


@dataclass(frozen=True)
class ExtensionEnvironment:
    key: str
    label: str
    browser: str
    extension_id: str
    fixed: bool


_ID_PLACEHOLDERS = {"", "__FILL_ME__", "<FILL_ME>"}


def _default_environments() -> tuple[list[ExtensionEnvironment], str]:
    envs = [
        ExtensionEnvironment(
            key="chrome_prod",
            label="Chrome (Web Store)",
            browser="chrome",
            extension_id="",
            fixed=True,
        ),
        ExtensionEnvironment(
            key="chrome_dev",
            label="Chrome (Unpacked Dev)",
            browser="chrome",
            extension_id="",
            fixed=False,
        ),
        ExtensionEnvironment(
            key="brave_prod",
            label="Brave (Web Store)",
            browser="brave",
            extension_id="",
            fixed=True,
        ),
        ExtensionEnvironment(
            key="chromium_dev",
            label="Chromium (Unpacked Dev)",
            browser="chromium",
            extension_id="",
            fixed=False,
        ),
    ]
    return envs, "chrome_prod"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_host_script() -> Path:
    override = os.environ.get("LEXISHIFT_HELPER_HOST")
    if override:
        log_helper(f"[Helper] Using override host path: {override}")
        return Path(override)
    log_helper(f"[Helper] frozen={getattr(sys, 'frozen', False)}, _MEIPASS={getattr(sys, '_MEIPASS', None)}")
    bundled = Path(resource_path("helper", "lexishift_native_host.py"))
    if bundled.exists():
        log_helper(f"[Helper] Found bundled host path: {bundled}")
        return bundled
    if getattr(sys, "frozen", False):
        candidate = _helper_data_root() / "helper" / "lexishift_native_host.py"
        log_helper(f"[Helper] Frozen app, bundled not found. Checking installed candidate: {candidate} exists={candidate.exists()}")
        return candidate
    repo_path = _repo_root() / "scripts" / "helper" / "lexishift_native_host.py"
    log_helper(f"[Helper] Dev mode, using repo path: {repo_path}")
    return repo_path


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
    if not _is_bundled_path(host_path):
        log_helper(f"[Helper] Host path {host_path} is not bundled; skipping stable copy.")
        return host_path
    target_dir = _helper_data_root() / "helper"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_host = target_dir / "lexishift_native_host.py"

    # 1. Copy the host script
    try:
        shutil.copy2(host_path, target_host)
        log_helper(f"[Helper] Copied bundled host to {target_host}")
    except OSError as e:
        log_helper(f"[Helper] Failed to copy bundled host to {target_host}: {e}")
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
            log_helper(f"[Helper] Copied lexishift_core from {core_src} to {core_dst}")
        except OSError as e:
            log_helper(f"[Helper] Failed to copy lexishift_core: {e}")
    else:
        log_helper(f"[Helper] Warning: lexishift_core not found in bundle near {host_path}")

    return target_host


def launch_agent_path() -> Optional[Path]:
    if sys.platform != "darwin":
        return None
    return Path.home() / "Library" / "LaunchAgents" / "com.lexishift.helper.plist"


def build_launch_agent(program_args: Sequence[str]) -> str:
    args = "\n".join([f'    <string>{arg}</string>' for arg in program_args])
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
  </dict>
</plist>
"""


def install_launch_agent(program_args: Sequence[str]) -> bool:
    plist_path = launch_agent_path()
    if not plist_path:
        log_helper("[Helper] LaunchAgent not supported on this platform.")
        return False
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(build_launch_agent(program_args), encoding="utf-8")
    log_helper(f"[Helper] Installed LaunchAgent: {plist_path}")
    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
    subprocess.run(["launchctl", "load", str(plist_path)], check=False)
    return True


def load_extension_environments() -> tuple[list[ExtensionEnvironment], str]:
    path = resource_path("helper_extension_ids.json")
    if not os.path.exists(path):
        log_helper(f"[Helper] helper_extension_ids.json missing at {path}; using defaults.")
        return _default_environments()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        log_helper(f"[Helper] helper_extension_ids.json unreadable at {path}; using defaults.")
        return _default_environments()
    raw_envs = data.get("environments") if isinstance(data, dict) else None
    if not isinstance(raw_envs, list):
        return _default_environments()
    envs: list[ExtensionEnvironment] = []
    for item in raw_envs:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip()
        label = str(item.get("label", "")).strip()
        browser = str(item.get("browser", "chrome")).strip() or "chrome"
        extension_id = str(item.get("extension_id", "")).strip()
        fixed = bool(item.get("fixed", False))
        if not key or not label:
            continue
        envs.append(
            ExtensionEnvironment(
                key=key,
                label=label,
                browser=browser,
                extension_id=extension_id,
                fixed=fixed,
            )
        )
    default_key = str(data.get("default", "")).strip() if isinstance(data, dict) else ""
    if not default_key:
        default_key = envs[0].key if envs else "chrome_prod"
    return envs, default_key


def resolve_extension_id(env: ExtensionEnvironment, custom_id: Optional[str]) -> Optional[str]:
    if env.fixed and env.extension_id and env.extension_id not in _ID_PLACEHOLDERS:
        return env.extension_id
    if custom_id:
        custom_id = custom_id.strip()
        return custom_id or None
    return None


def get_environment(env_key: str, envs: list[ExtensionEnvironment]) -> Optional[ExtensionEnvironment]:
    for env in envs:
        if env.key == env_key:
            return env
    return envs[0] if envs else None


def _chrome_host_dir(browser: str = "chrome") -> Optional[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        if browser == "chromium":
            return home / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts"
        if browser == "brave":
            return home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts"
        return home / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
    if sys.platform.startswith("win"):
        return None
    return home / ".config" / "google-chrome" / "NativeMessagingHosts"


def manifest_path(browser: str = "chrome") -> Optional[Path]:
    base = _chrome_host_dir(browser)
    if base is None:
        return None
    return base / "com.lexishift.helper.json"


def build_manifest(*, host_path: Path, extension_id: str) -> dict:
    return {
        "name": "com.lexishift.helper",
        "description": "LexiShift local helper for rule generation and SRS syncing.",
        "path": str(host_path),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }


def is_helper_installed(extension_id: Optional[str] = None, *, browser: str = "chrome") -> bool:
    manifest = manifest_path(browser)
    if not manifest or not manifest.exists():
        return False
    if not extension_id:
        return True
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    allowed = data.get("allowed_origins") or []
    return f"chrome-extension://{extension_id}/" in allowed


def install_helper(
    *,
    extension_id: str,
    browser: str = "chrome",
    host_path: Optional[Path] = None,
) -> HelperInstallResult:
    if not extension_id.strip():
        log_helper("[Helper] install_helper failed: missing extension id.")
        return HelperInstallResult(False, "Extension ID is required.")
    manifest = manifest_path(browser)
    if manifest is None:
        log_helper("[Helper] install_helper failed: unsupported OS.")
        return HelperInstallResult(False, "Helper install not supported on this OS yet.")
    host_path = host_path or default_host_script()
    
    # Force copy to stable location and use THAT path for the manifest
    stable_path = _ensure_stable_helper(host_path)
    
    if not stable_path.exists():
        log_helper(f"[Helper] install_helper failed: stable host not found at {stable_path}")
        return HelperInstallResult(False, f"Helper host not found: {stable_path}")
    try:
        mode = stable_path.stat().st_mode
        stable_path.chmod(mode | stat.S_IEXEC)
    except OSError:
        pass
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = build_manifest(host_path=stable_path, extension_id=extension_id.strip())
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    log_helper(f"[Helper] install_helper wrote manifest: {manifest}")
    return HelperInstallResult(True, "Helper installed.", manifest)
