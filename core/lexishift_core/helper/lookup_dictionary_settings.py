from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from lexishift_core.helper.lp_capabilities import normalize_pair_key


LOOKUP_DICTIONARY_SETTINGS_VERSION = 1


@dataclass(frozen=True)
class LookupDictionarySettings:
    pair_pack_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
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
    pairs: dict[str, tuple[str, ...]] = {}
    if isinstance(raw_pairs, Mapping):
        for raw_pair, raw_pack_ids in raw_pairs.items():
            pair = normalize_pair_key(raw_pair, default="")
            pack_ids = _pack_id_values(raw_pack_ids)
            if pair and pack_ids:
                pairs[pair] = pack_ids
    return LookupDictionarySettings(
        pair_pack_ids=pairs,
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
    return LookupDictionarySettings(pair_pack_ids=pairs)


def without_lookup_dictionary_pack(
    settings: LookupDictionarySettings,
    pack_id: str,
) -> LookupDictionarySettings:
    normalized_pack_id = str(pack_id or "").strip()
    pairs: dict[str, tuple[str, ...]] = {}
    for pair, pack_ids in settings.pair_pack_ids.items():
        filtered = tuple(value for value in pack_ids if value != normalized_pack_id)
        if filtered:
            pairs[pair] = filtered
    return LookupDictionarySettings(pair_pack_ids=pairs)


def _pack_id_values(value: object) -> tuple[str, ...]:
    raw_values: Sequence[object]
    if isinstance(value, str):
        raw_values = (value,)
    elif isinstance(value, Sequence):
        raw_values = value
    else:
        return ()
    values: list[str] = []
    for raw_value in raw_values:
        pack_id = str(raw_value or "").strip()
        if pack_id and pack_id not in values:
            values.append(pack_id)
    return tuple(values)


def _safe_version(value: object) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return LOOKUP_DICTIONARY_SETTINGS_VERSION
    return parsed if parsed > 0 else LOOKUP_DICTIONARY_SETTINGS_VERSION


__all__ = [
    "LookupDictionarySettings",
    "load_lookup_dictionary_settings",
    "lookup_dictionary_pack_ids_for_pair",
    "save_lookup_dictionary_settings",
    "with_lookup_dictionary_pack_ids",
    "without_lookup_dictionary_pack",
]
