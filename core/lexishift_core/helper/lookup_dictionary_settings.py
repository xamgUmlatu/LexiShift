from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from lexishift_core.helper.lp_capabilities import normalize_pair_key


LOOKUP_DICTIONARY_SETTINGS_VERSION = 2
BUILTIN_SOURCE_PREFIX = "builtin:"


@dataclass(frozen=True)
class LookupDictionarySettings:
    pair_pack_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    pair_source_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    version: int = LOOKUP_DICTIONARY_SETTINGS_VERSION


def load_lookup_dictionary_settings(path: Path) -> LookupDictionarySettings:
    candidate = Path(path)
    if not candidate.exists():
        return LookupDictionarySettings()
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return LookupDictionarySettings()
    if not isinstance(payload, Mapping):
        return LookupDictionarySettings()
    raw_pairs = payload.get("pair_pack_ids")
    raw_source_pairs = payload.get("pair_source_ids")
    pairs: dict[str, tuple[str, ...]] = {}
    source_pairs: dict[str, tuple[str, ...]] = {}
    if isinstance(raw_pairs, Mapping):
        for raw_pair, raw_pack_ids in raw_pairs.items():
            pair = normalize_pair_key(raw_pair, default="")
            pack_ids = _pack_id_values(raw_pack_ids)
            if pair and pack_ids:
                pairs[pair] = pack_ids
    if isinstance(raw_source_pairs, Mapping):
        for raw_pair, raw_source_ids in raw_source_pairs.items():
            pair = normalize_pair_key(raw_pair, default="")
            source_ids = _source_id_values(raw_source_ids)
            if pair and source_ids:
                source_pairs[pair] = source_ids
    return LookupDictionarySettings(
        pair_pack_ids=pairs,
        pair_source_ids=source_pairs,
        version=_safe_version(payload.get("version")),
    )


def save_lookup_dictionary_settings(
    settings: LookupDictionarySettings,
    path: Path,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": LOOKUP_DICTIONARY_SETTINGS_VERSION,
        "pair_pack_ids": {
            pair: list(pack_ids)
            for pair, pack_ids in sorted(settings.pair_pack_ids.items())
            if pair and pack_ids
        },
        "pair_source_ids": {
            pair: list(source_ids)
            for pair, source_ids in sorted(settings.pair_source_ids.items())
            if pair and source_ids
        },
    }
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def lookup_dictionary_pack_ids_for_pair(
    settings: LookupDictionarySettings,
    pair: str,
) -> tuple[str, ...]:
    normalized_pair = normalize_pair_key(pair, default="")
    return tuple(settings.pair_pack_ids.get(normalized_pair, ()))


def lookup_dictionary_source_ids_for_pair(
    settings: LookupDictionarySettings,
    pair: str,
    *,
    builtin_source_id: str = "",
) -> tuple[str, ...]:
    """Return the effective, unified lookup order for a language pair.

    Version-1 settings only stored imported pack IDs. They migrate lazily by
    retaining that order and appending the pair's built-in source. Stored
    version-2 orders are repaired conservatively when a pack is added, removed,
    or temporarily missing from older settings.
    """

    normalized_pair = normalize_pair_key(pair, default="")
    pack_ids = lookup_dictionary_pack_ids_for_pair(settings, normalized_pair)
    builtin_id = _normalized_builtin_source_id(builtin_source_id)
    allowed = {*pack_ids}
    if builtin_id:
        allowed.add(builtin_id)
    ordered = [
        source_id
        for source_id in settings.pair_source_ids.get(normalized_pair, ())
        if source_id in allowed
    ]
    for source_id in (*pack_ids, *((builtin_id,) if builtin_id else ())):
        if source_id not in ordered:
            ordered.append(source_id)
    return tuple(ordered)


def with_lookup_dictionary_pack_ids(
    settings: LookupDictionarySettings,
    *,
    pair: str,
    pack_ids: Sequence[str],
) -> LookupDictionarySettings:
    normalized_pair = normalize_pair_key(pair, default="")
    if not normalized_pair:
        raise ValueError("Missing language pair.")
    normalized_pack_ids = _pack_id_values(pack_ids)
    pairs = dict(settings.pair_pack_ids)
    if normalized_pack_ids:
        pairs[normalized_pair] = normalized_pack_ids
    else:
        pairs.pop(normalized_pair, None)
    source_pairs = dict(settings.pair_source_ids)
    existing_order = source_pairs.get(normalized_pair, ())
    retained = tuple(
        source_id
        for source_id in existing_order
        if source_id.startswith(BUILTIN_SOURCE_PREFIX) or source_id in normalized_pack_ids
    )
    ordered = tuple(dict.fromkeys((*normalized_pack_ids, *retained)))
    if ordered:
        source_pairs[normalized_pair] = ordered
    else:
        source_pairs.pop(normalized_pair, None)
    return LookupDictionarySettings(pair_pack_ids=pairs, pair_source_ids=source_pairs)


def with_lookup_dictionary_source_ids(
    settings: LookupDictionarySettings,
    *,
    pair: str,
    source_ids: Sequence[str],
) -> LookupDictionarySettings:
    normalized_pair = normalize_pair_key(pair, default="")
    if not normalized_pair:
        raise ValueError("Missing language pair.")
    normalized_source_ids = _source_id_values(source_ids)
    pack_ids = tuple(
        source_id
        for source_id in normalized_source_ids
        if not source_id.startswith(BUILTIN_SOURCE_PREFIX)
    )
    pairs = dict(settings.pair_pack_ids)
    source_pairs = dict(settings.pair_source_ids)
    if pack_ids:
        pairs[normalized_pair] = pack_ids
    else:
        pairs.pop(normalized_pair, None)
    if normalized_source_ids:
        source_pairs[normalized_pair] = normalized_source_ids
    else:
        source_pairs.pop(normalized_pair, None)
    return LookupDictionarySettings(pair_pack_ids=pairs, pair_source_ids=source_pairs)


def without_lookup_dictionary_pack(
    settings: LookupDictionarySettings,
    pack_id: str,
) -> LookupDictionarySettings:
    normalized_pack_id = str(pack_id or "").strip()
    pairs: dict[str, tuple[str, ...]] = {}
    source_pairs: dict[str, tuple[str, ...]] = {}
    for pair, pack_ids in settings.pair_pack_ids.items():
        filtered = tuple(value for value in pack_ids if value != normalized_pack_id)
        if filtered:
            pairs[pair] = filtered
    for pair, source_ids in settings.pair_source_ids.items():
        filtered = tuple(value for value in source_ids if value != normalized_pack_id)
        if filtered:
            source_pairs[pair] = filtered
    return LookupDictionarySettings(pair_pack_ids=pairs, pair_source_ids=source_pairs)


def _pack_id_values(value: object) -> tuple[str, ...]:
    return tuple(
        source_id
        for source_id in _source_id_values(value)
        if not source_id.startswith(BUILTIN_SOURCE_PREFIX)
    )


def _source_id_values(value: object) -> tuple[str, ...]:
    raw_values: Sequence[object]
    if isinstance(value, str):
        raw_values = (value,)
    elif isinstance(value, Sequence):
        raw_values = value
    else:
        return ()
    values: list[str] = []
    for raw_value in raw_values:
        source_id = str(raw_value or "").strip()
        if source_id and source_id not in values:
            values.append(source_id)
    return tuple(values)


def _normalized_builtin_source_id(value: object) -> str:
    source_id = str(value or "").strip()
    if not source_id:
        return ""
    return (
        source_id
        if source_id.startswith(BUILTIN_SOURCE_PREFIX)
        else f"{BUILTIN_SOURCE_PREFIX}{source_id}"
    )


def _safe_version(value: object) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return LOOKUP_DICTIONARY_SETTINGS_VERSION
    return parsed if parsed > 0 else LOOKUP_DICTIONARY_SETTINGS_VERSION


__all__ = [
    "LookupDictionarySettings",
    "lookup_dictionary_source_ids_for_pair",
    "load_lookup_dictionary_settings",
    "lookup_dictionary_pack_ids_for_pair",
    "save_lookup_dictionary_settings",
    "with_lookup_dictionary_pack_ids",
    "with_lookup_dictionary_source_ids",
    "without_lookup_dictionary_pack",
]
