from __future__ import annotations

import json
import os
from typing import Any, Mapping

from utils_paths import resource_path

DEFAULT_LOCALE = "en"
_LOCALE = DEFAULT_LOCALE
_CATALOG: dict[str, Any] = {}
_FALLBACK: dict[str, Any] = {}


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # pragma: no cover - defensive fallback
        return "{" + key + "}"


def _load_json(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _load_catalog(locale: str) -> dict[str, Any]:
    path = resource_path("i18n", f"{locale}.json")
    return _load_json(path)


def available_locales() -> Mapping[str, str]:
    meta_path = resource_path("i18n", "locales.json")
    data = _load_json(meta_path)
    if not data:
        return {DEFAULT_LOCALE: "English"}
    return {str(key): str(value) for key, value in data.items()}


def normalize_locale(locale: str | None) -> str:
    if not locale or locale == "system":
        return DEFAULT_LOCALE
    normalized = locale.replace("-", "_")
    locales = available_locales()
    if normalized in locales:
        return normalized
    base = normalized.split("_")[0]
    if base in locales:
        return base
    return DEFAULT_LOCALE


def set_locale(locale: str | None) -> str:
    global _LOCALE, _CATALOG, _FALLBACK
    normalized = normalize_locale(locale)
    _LOCALE = normalized
    _CATALOG = _load_catalog(normalized)
    _FALLBACK = _load_catalog(DEFAULT_LOCALE)
    return _LOCALE


def current_locale() -> str:
    return _LOCALE


def _lookup(catalog: Mapping[str, Any], key: str) -> str | None:
    if not key:
        return None
    node: Any = catalog
    for part in key.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, str) else None


def t(key: str, **kwargs: Any) -> str:
    text = _lookup(_CATALOG, key) or _lookup(_FALLBACK, key) or key
    if kwargs:
        return text.format_map(_SafeDict(kwargs))
    return text
