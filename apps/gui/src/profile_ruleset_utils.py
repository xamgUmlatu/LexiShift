from __future__ import annotations

import os
from pathlib import Path


def normalize_ruleset_path(path: str) -> Path:
    return Path(os.path.abspath(os.path.expanduser(path)))


def ruleset_display_name(path: str) -> str:
    normalized = normalize_ruleset_path(path)
    name = normalized.stem.strip()
    if name:
        return name
    raw_name = Path(path).name
    return raw_name or path
