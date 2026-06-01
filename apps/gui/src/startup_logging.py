from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time


STARTUP_SESSION_ID_ENV = "LEXISHIFT_STARTUP_SESSION_ID"
STARTUP_REQUESTED_AT_ENV = "LEXISHIFT_STARTUP_REQUESTED_AT"
STARTUP_SOURCE_ENV = "LEXISHIFT_STARTUP_SOURCE"
STARTUP_LAUNCH_MODE_ENV = "LEXISHIFT_STARTUP_LAUNCH_MODE"
STARTUP_RESOURCE_PAIR_ENV = "LEXISHIFT_STARTUP_RESOURCE_PAIR"
STARTUP_LOG_PATH_ENV = "LEXISHIFT_STARTUP_LOG_PATH"
OPEN_RESOURCE_SETTINGS_FLAG_TEXT = "--open-resource-settings"
EARLY_START_TIME = time.perf_counter()


def early_startup_session_id() -> str:
    value = str(os.environ.get(STARTUP_SESSION_ID_ENV, "") or "").strip()
    if value:
        return value
    generated = f"direct-{os.getpid()}-{time.time_ns()}"
    os.environ[STARTUP_SESSION_ID_ENV] = generated
    return generated


def early_platform_data_root() -> Path:
    override = str(os.environ.get("LEXISHIFT_DATA_DIR", "") or "").strip()
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def early_startup_log_paths() -> list[Path]:
    override = str(os.environ.get(STARTUP_LOG_PATH_ENV, "") or "").strip()
    if override:
        return [Path(override).expanduser()]
    paths = [early_platform_data_root() / "startup_timing.log", Path("/tmp/lexishift_startup.log")]
    if sys.platform == "darwin":
        paths.append(Path.home() / "Library" / "Logs" / "LexiShift" / "lexishift_startup.log")
    elif sys.platform.startswith("win"):
        paths.append(
            Path.home() / "AppData" / "Local" / "LexiShift" / "Logs" / "lexishift_startup.log"
        )
    else:
        paths.append(Path.home() / ".local" / "state" / "LexiShift" / "lexishift_startup.log")
    return paths


def early_argv_mode() -> str:
    if OPEN_RESOURCE_SETTINGS_FLAG_TEXT in sys.argv:
        return "resource_settings"
    if "--helper-daemon" in sys.argv:
        return "helper_daemon"
    if "--diagnose-startup" in sys.argv:
        return "diagnose_startup"
    if "--print-data-dir" in sys.argv:
        return "print_data_dir"
    return "normal"


def write_early_startup_checkpoint(label: str) -> None:
    session_id = early_startup_session_id()
    total_ms = (time.perf_counter() - EARLY_START_TIME) * 1000.0
    metadata = [
        f"session={session_id}",
        f"pid={os.getpid()}",
        f"ppid={os.getppid()}",
        f"argv_mode={early_argv_mode()}",
        f"source={os.environ.get(STARTUP_SOURCE_ENV, 'direct')}",
        f"ts={datetime.now(timezone.utc).isoformat()}",
    ]
    launch_mode = str(os.environ.get(STARTUP_LAUNCH_MODE_ENV, "") or "").strip()
    if launch_mode:
        metadata.append(f"launch_mode={launch_mode}")
    resource_pair = str(os.environ.get(STARTUP_RESOURCE_PAIR_ENV, "") or "").strip()
    if resource_pair:
        metadata.append(f"resource_pair={resource_pair}")
    requested_at = str(os.environ.get(STARTUP_REQUESTED_AT_ENV, "") or "").strip()
    if requested_at:
        metadata.append(f"requested_at={requested_at}")
    message = f"[startup] {label} (+0.0 ms, total {total_ms:.1f} ms) " + " ".join(metadata)
    for path in early_startup_log_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except OSError:
            continue
