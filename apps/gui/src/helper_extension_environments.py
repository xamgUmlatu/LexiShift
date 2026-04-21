from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from helper_connection_models import (
    _ID_PLACEHOLDERS,
    default_extension_environments,
    ExtensionEnvironment,
)
from helper_logger import log_helper
from utils_paths import resource_path


def load_extension_environments() -> tuple[list[ExtensionEnvironment], str]:
    path = resource_path("helper_extension_ids.json")
    if not os.path.exists(path):
        log_helper(f"[Helper] helper_extension_ids.json missing at {path}; using defaults.")
        return default_extension_environments()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        log_helper(f"[Helper] helper_extension_ids.json unreadable at {path}; using defaults.")
        return default_extension_environments()
    raw_envs = data.get("environments") if isinstance(data, dict) else None
    if not isinstance(raw_envs, list):
        return default_extension_environments()
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


def get_environment(
    env_key: str,
    envs: list[ExtensionEnvironment],
) -> Optional[ExtensionEnvironment]:
    for env in envs:
        if env.key == env_key:
            return env
    return envs[0] if envs else None
