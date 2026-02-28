from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def _app_data_dir() -> Path:
    base_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _fallback_log_dirs() -> list[Path]:
    paths: list[Path] = []
    paths.append(Path("/tmp"))
    home = Path.home()
    if sys.platform == "darwin":
        paths.append(home / "Library" / "Logs" / "LexiShift")
    elif sys.platform.startswith("win"):
        paths.append(home / "AppData" / "Local" / "LexiShift" / "Logs")
    else:
        paths.append(home / ".local" / "state" / "LexiShift")
    return paths


def _startup_log_paths() -> list[Path]:
    paths: list[Path] = []
    try:
        paths.append(_app_data_dir() / "startup_timing.log")
    except Exception:
        pass
    for base in _fallback_log_dirs():
        try:
            base.mkdir(parents=True, exist_ok=True)
            paths.append(base / "lexishift_startup.log")
        except OSError:
            continue
    return paths


def _rulesets_dir() -> Path:
    target = Path(os.path.join(str(_app_data_dir()), "rulesets"))
    target.mkdir(parents=True, exist_ok=True)
    return target


def _settings_path() -> Path:
    return _app_data_dir() / "settings.json"


def _default_dataset_path() -> Path:
    return _rulesets_dir() / "vocab.json"
