from __future__ import annotations

import json
import os
from typing import Any

from PySide6.QtCore import QStandardPaths

from theme_logger import log_theme
from utils_paths import resource_path

THEME_COLOR_KEYS = (
    "bg",
    "panel_top",
    "panel_bottom",
    "panel_border",
    "text",
    "muted",
    "accent",
    "accent_soft",
    "primary",
    "primary_hover",
    "table_bg",
    "table_sel_bg",
)

THEME_OPTIONAL_COLOR_KEYS = (
    "status_success",
    "status_warning",
    "status_error",
    "status_info",
    "status_neutral",
    "status_muted",
)

THEME_ALL_COLOR_KEYS = THEME_COLOR_KEYS + THEME_OPTIONAL_COLOR_KEYS


def theme_dir() -> str:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    base_dir = base_dir or os.path.expanduser("~")
    target = os.path.join(base_dir, "themes")
    os.makedirs(target, exist_ok=True)
    return target


def load_user_themes() -> dict[str, dict[str, Any]]:
    themes: dict[str, dict[str, Any]] = {}
    base_dir = theme_dir()
    for path in _iter_theme_paths(base_dir):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        colors = data.get("colors")
        if not isinstance(colors, dict):
            continue
        if any(key not in colors for key in THEME_COLOR_KEYS):
            continue
        fallback_theme_id = os.path.splitext(os.path.basename(path))[0]
        theme_id = str(data.get("id") or fallback_theme_id)
        theme_name = str(data.get("name") or theme_id)
        theme: dict[str, Any] = {key: str(colors[key]) for key in THEME_COLOR_KEYS}
        for key in THEME_OPTIONAL_COLOR_KEYS:
            if key in colors:
                theme[key] = str(colors[key])
        theme["_name"] = theme_name
        theme["_source"] = path
        theme["_base_dir"] = os.path.dirname(path)
        background = data.get("background")
        if isinstance(background, dict):
            theme["_background"] = background
            image_path = _resolve_image_path(background.get("image_path"), theme["_base_dir"])
            if image_path:
                theme["_background_path"] = image_path
        screen_overrides = data.get("screen_overrides")
        if isinstance(screen_overrides, dict):
            parsed_overrides = _parse_screen_overrides(screen_overrides, theme["_base_dir"])
            if parsed_overrides:
                theme["_screen_overrides"] = parsed_overrides
        themes[theme_id] = theme
    return themes


def _resolve_image_path(value: Any, base_dir: str) -> str:
    if not isinstance(value, str) or not value:
        return ""
    expanded = os.path.expanduser(value)
    candidate = expanded if os.path.isabs(expanded) else os.path.join(base_dir, expanded)
    if os.path.exists(candidate):
        return candidate
    # Fallback: packaged resources (useful for sample_images in one-dir builds)
    fallback = resource_path(expanded)
    if os.path.exists(fallback):
        return fallback
    # If the theme references just a filename, try the packaged sample_images folder
    if os.path.basename(expanded) == expanded:
        sample_fallback = resource_path("sample_images", expanded)
        if os.path.exists(sample_fallback):
            return sample_fallback
    log_theme(f"[Theme] Image not found: {value} (base: {base_dir})")
    return ""


def _parse_screen_overrides(raw: dict[str, Any], base_dir: str) -> dict[str, dict[str, Any]]:
    overrides: dict[str, dict[str, Any]] = {}
    for screen_id, override in raw.items():
        if not isinstance(override, dict):
            continue
        entry: dict[str, Any] = {}
        colors = override.get("colors")
        if isinstance(colors, dict):
            entry["colors"] = {key: str(value) for key, value in colors.items() if key in THEME_ALL_COLOR_KEYS}
        background = override.get("background")
        if isinstance(background, dict):
            entry["_background"] = background
            image_path = _resolve_image_path(background.get("image_path"), base_dir)
            if image_path:
                entry["_background_path"] = image_path
        if entry:
            overrides[str(screen_id)] = entry
    return overrides


def _iter_theme_paths(base_dir: str) -> list[str]:
    entries: list[str] = []
    for entry in os.listdir(base_dir):
        if entry.startswith("."):
            continue
        path = os.path.join(base_dir, entry)
        if os.path.isfile(path) and entry.lower().endswith(".json"):
            entries.append(path)
        elif os.path.isdir(path):
            theme_path = os.path.join(path, "theme.json")
            if os.path.isfile(theme_path):
                entries.append(theme_path)
    return sorted(entries)
