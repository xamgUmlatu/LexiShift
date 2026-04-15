from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from lexishift_core.srs.store import SrsStore


@dataclass(frozen=True)
class SrsPairInventory:
    active_item_ids: Sequence[str] = field(default_factory=tuple)
    last_initialized_at: Optional[str] = None
    last_refreshed_at: Optional[str] = None
    last_rebalanced_at: Optional[str] = None


@dataclass(frozen=True)
class SrsInventory:
    pairs: Mapping[str, SrsPairInventory] = field(default_factory=dict)
    version: int = 1


def srs_pair_inventory_from_dict(data: Mapping[str, Any]) -> SrsPairInventory:
    return SrsPairInventory(
        active_item_ids=_normalize_item_ids(data.get("active_item_ids")),
        last_initialized_at=_normalize_optional_string(data.get("last_initialized_at")),
        last_refreshed_at=_normalize_optional_string(data.get("last_refreshed_at")),
        last_rebalanced_at=_normalize_optional_string(data.get("last_rebalanced_at")),
    )


def srs_pair_inventory_to_dict(inventory: SrsPairInventory) -> dict[str, Any]:
    payload = {
        "active_item_ids": list(_normalize_item_ids(inventory.active_item_ids)),
        "last_initialized_at": _normalize_optional_string(inventory.last_initialized_at),
        "last_refreshed_at": _normalize_optional_string(inventory.last_refreshed_at),
        "last_rebalanced_at": _normalize_optional_string(inventory.last_rebalanced_at),
    }
    return {key: value for key, value in payload.items() if value not in (None, [])}


def srs_inventory_from_dict(data: Mapping[str, Any]) -> SrsInventory:
    raw_pairs = data.get("pairs")
    pairs: dict[str, SrsPairInventory] = {}
    if isinstance(raw_pairs, Mapping):
        for pair, value in raw_pairs.items():
            normalized_pair = str(pair or "").strip()
            if not normalized_pair or not isinstance(value, Mapping):
                continue
            pairs[normalized_pair] = srs_pair_inventory_from_dict(value)
    return SrsInventory(
        pairs=pairs,
        version=max(1, int(data.get("version", 1) or 1)),
    )


def srs_inventory_to_dict(inventory: SrsInventory) -> dict[str, Any]:
    return {
        "version": max(1, int(inventory.version)),
        "pairs": {
            str(pair): srs_pair_inventory_to_dict(pair_inventory)
            for pair, pair_inventory in dict(inventory.pairs or {}).items()
        },
    }


def load_srs_inventory(path: str | Path) -> SrsInventory:
    payload = Path(path).read_text(encoding="utf-8")
    return srs_inventory_from_dict(json.loads(payload))


def save_srs_inventory(inventory: SrsInventory, path: str | Path) -> None:
    payload = json.dumps(srs_inventory_to_dict(inventory), indent=2, sort_keys=True)
    Path(path).write_text(payload, encoding="utf-8")


def active_item_ids_for_pair(inventory: SrsInventory, pair: str) -> tuple[str, ...]:
    normalized_pair = str(pair or "").strip()
    pair_inventory = dict(inventory.pairs or {}).get(normalized_pair)
    if pair_inventory is None:
        return tuple()
    return _normalize_item_ids(pair_inventory.active_item_ids)


def set_active_item_ids(
    inventory: SrsInventory,
    *,
    pair: str,
    active_item_ids: Sequence[str],
    last_initialized_at: Optional[str] = None,
    last_refreshed_at: Optional[str] = None,
    last_rebalanced_at: Optional[str] = None,
) -> SrsInventory:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("Missing pair.")
    normalized_ids = _normalize_item_ids(active_item_ids)
    pairs = dict(inventory.pairs or {})
    existing = pairs.get(normalized_pair, SrsPairInventory())
    updated = replace(
        existing,
        active_item_ids=normalized_ids,
        last_initialized_at=(
            _normalize_optional_string(last_initialized_at)
            if last_initialized_at is not None
            else existing.last_initialized_at
        ),
        last_refreshed_at=(
            _normalize_optional_string(last_refreshed_at)
            if last_refreshed_at is not None
            else existing.last_refreshed_at
        ),
        last_rebalanced_at=(
            _normalize_optional_string(last_rebalanced_at)
            if last_rebalanced_at is not None
            else existing.last_rebalanced_at
        ),
    )
    pairs[normalized_pair] = updated
    return SrsInventory(pairs=pairs, version=max(1, int(inventory.version)))


def remove_pair_inventory(inventory: SrsInventory, pair: str) -> SrsInventory:
    normalized_pair = str(pair or "").strip()
    pairs = dict(inventory.pairs or {})
    pairs.pop(normalized_pair, None)
    return SrsInventory(pairs=pairs, version=max(1, int(inventory.version)))


def derive_active_item_ids_from_store(store: SrsStore, *, pair: str) -> tuple[str, ...]:
    normalized_pair = str(pair or "").strip()
    item_ids = [
        item.item_id
        for item in store.items
        if item.language_pair == normalized_pair and str(item.item_id or "").strip()
    ]
    return _normalize_item_ids(item_ids)


def resolve_active_item_ids(
    *,
    store: SrsStore,
    pair: str,
    inventory: Optional[SrsInventory],
) -> tuple[tuple[str, ...], str]:
    normalized_pair = str(pair or "").strip()
    if inventory is None or normalized_pair not in dict(inventory.pairs or {}):
        return derive_active_item_ids_from_store(store, pair=normalized_pair), "store_fallback"

    available_ids = {
        item.item_id
        for item in store.items
        if item.language_pair == normalized_pair and str(item.item_id or "").strip()
    }
    resolved_ids = [
        item_id
        for item_id in active_item_ids_for_pair(inventory, normalized_pair)
        if item_id in available_ids
    ]
    return _normalize_item_ids(resolved_ids), "inventory"


def merge_active_item_ids(
    existing_ids: Sequence[str],
    added_ids: Sequence[str],
) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for item_id in list(existing_ids) + list(added_ids):
        normalized = str(item_id or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)
    return tuple(merged)


def _normalize_item_ids(values: object) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return tuple()
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item_id = str(value or "").strip()
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        normalized.append(item_id)
    return tuple(normalized)


def _normalize_optional_string(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
