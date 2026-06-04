from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import time
from typing import Mapping
import uuid


STARTUP_SESSION_ID_ENV = "LEXISHIFT_STARTUP_SESSION_ID"
STARTUP_REQUESTED_AT_ENV = "LEXISHIFT_STARTUP_REQUESTED_AT"
STARTUP_SOURCE_ENV = "LEXISHIFT_STARTUP_SOURCE"
STARTUP_LAUNCH_MODE_ENV = "LEXISHIFT_STARTUP_LAUNCH_MODE"
STARTUP_RESOURCE_PAIR_ENV = "LEXISHIFT_STARTUP_RESOURCE_PAIR"
STARTUP_LOG_PATH_ENV = "LEXISHIFT_STARTUP_LOG_PATH"


def duration_ms(start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000.0, 1)


def new_startup_session_id() -> str:
    return uuid.uuid4().hex


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def resource_launch_command_class(command: list[str]) -> str:
    if not command:
        return "unknown"
    first = Path(str(command[0])).name.lower()
    if first == "open":
        if "-b" in command:
            return "macos_open_bundle_id"
        if any(str(part).endswith(".app") for part in command):
            return "macos_open_app_bundle"
        return "macos_open"
    if len(command) > 1 and str(command[1]).endswith("main.py"):
        return "python_gui_entry"
    if str(command[0]).endswith((".exe", "LexiShift")):
        return "direct_gui_executable"
    return "subprocess"


def resource_settings_launch_env(
    *,
    base_env: Mapping[str, str] | None = None,
    session_id: str,
    requested_at: str,
    launch_mode: str,
    pair: str,
) -> dict[str, str]:
    env = dict(base_env or os.environ)
    for key in ("_MEIPASS2", "DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH"):
        env.pop(key, None)
    env[STARTUP_SESSION_ID_ENV] = session_id
    env[STARTUP_REQUESTED_AT_ENV] = requested_at
    env[STARTUP_SOURCE_ENV] = "native_host_resource_settings"
    env[STARTUP_LAUNCH_MODE_ENV] = launch_mode
    if pair:
        env[STARTUP_RESOURCE_PAIR_ENV] = pair.lower()
    else:
        env.pop(STARTUP_RESOURCE_PAIR_ENV, None)
    return env
