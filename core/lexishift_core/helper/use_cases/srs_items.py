from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Mapping, Optional

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs import (
    SRS_LIFECYCLE_ACTIVE,
    SRS_LIFECYCLE_CLEARED,
    SRS_LIFECYCLE_DISCARDED,
    SrsInventory,
    SrsItem,
    load_srs_inventory,
    load_srs_store,
    normalize_srs_lifecycle_state,
    resolve_active_item_ids,
)
from lexishift_core.srs.time import now_utc, parse_ts


SECONDS_PER_DAY = 24 * 60 * 60


def list_srs_items(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
    now: datetime | None = None,
    resolve_profile_id_fn: Callable[..., str],
) -> dict[str, object]:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("Missing pair.")
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    store_path = paths.srs_store_path_for(normalized_profile_id)
    inventory_path = paths.srs_inventory_path_for(normalized_profile_id)
    anchor = now or now_utc()

    if not store_path.exists():
        return {
            "status": "ok",
            "pair": normalized_pair,
            "profile_id": normalized_profile_id,
            "store_path": str(store_path),
            "store_exists": False,
            "inventory_path": str(inventory_path),
            "inventory_exists": inventory_path.exists(),
            "inventory_source": "missing_store",
            "summary": _empty_summary(),
            "items": [],
        }

    store = load_srs_store(store_path)
    inventory = _load_inventory_if_present(inventory_path)
    active_item_ids, inventory_source = resolve_active_item_ids(
        store=store,
        pair=normalized_pair,
        inventory=inventory,
    )
    active_item_id_set = set(active_item_ids)
    scoped_items = [item for item in store.items if item.language_pair == normalized_pair]
    payload_items = [
        _item_payload(
            item,
            active_item_ids=active_item_id_set,
            now=anchor,
        )
        for item in scoped_items
    ]
    payload_items.sort(key=_item_sort_key)

    return {
        "status": "ok",
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "store_path": str(store_path),
        "store_exists": True,
        "inventory_path": str(inventory_path),
        "inventory_exists": inventory_path.exists(),
        "inventory_source": inventory_source,
        "summary": _summary(payload_items, inventory_active_count=len(active_item_ids)),
        "items": payload_items,
    }


def _load_inventory_if_present(path: Path) -> Optional[SrsInventory]:
    if not path.exists():
        return None
    return load_srs_inventory(path)


def _item_payload(
    item: SrsItem,
    *,
    active_item_ids: set[str],
    now: datetime,
) -> dict[str, object]:
    lifecycle_state = normalize_srs_lifecycle_state(item.lifecycle_state)
    active = lifecycle_state == SRS_LIFECYCLE_ACTIVE and item.item_id in active_item_ids
    status, status_label = _dashboard_status(
        item,
        lifecycle_state=lifecycle_state,
        active=active,
        now=now,
    )
    word_package = _word_package_payload(item.word_package)
    display = str(word_package.get("surface") or item.lemma or item.item_id)
    source = word_package.get("source") if isinstance(word_package.get("source"), Mapping) else {}
    source_label = str(source.get("provider") or item.source_type or "srs")
    next_due_dt = parse_ts(item.next_due)
    due_in_seconds = int((next_due_dt - now).total_seconds()) if next_due_dt is not None else None
    last_history = item.history[-1] if item.history else None

    return {
        "item_id": item.item_id,
        "lemma": item.lemma,
        "display": display,
        "reading": word_package.get("reading") or "",
        "pair": item.language_pair,
        "active": active,
        "status": status,
        "status_label": status_label,
        "next_due": item.next_due,
        "due_in_seconds": due_in_seconds,
        "last_review": item.last_review,
        "last_seen": item.last_seen,
        "exposures": max(0, int(item.exposures or 0)),
        "review_count": len(item.history),
        "last_rating": last_history.rating if last_history else None,
        "source_type": item.source_type,
        "source_label": source_label,
        "pos": word_package.get("pos_canonical") or word_package.get("pos") or "",
        "advanced": {
            "lifecycle_state": lifecycle_state,
            "lifecycle_reason": item.lifecycle_reason,
            "lifecycle_updated_at": item.lifecycle_updated_at,
            "scheduler_state": item.scheduler_state,
            "scheduler_step": item.scheduler_step,
            "stability": item.stability,
            "difficulty": item.difficulty,
            "confidence": item.confidence,
            "word_package": word_package,
            "history": [{"ts": entry.ts, "rating": entry.rating} for entry in item.history[-5:]],
        },
    }


def _dashboard_status(
    item: SrsItem,
    *,
    lifecycle_state: str,
    active: bool,
    now: datetime,
) -> tuple[str, str]:
    if lifecycle_state == SRS_LIFECYCLE_DISCARDED:
        return "discarded", "Discarded"
    if lifecycle_state == SRS_LIFECYCLE_CLEARED:
        return "cleared", "Cleared"
    if lifecycle_state != SRS_LIFECYCLE_ACTIVE:
        return "removed", "Removed"
    if not active:
        return "queued", "Queued"

    next_due = parse_ts(item.next_due)
    if next_due is None:
        return "learning", "Learning"
    if next_due <= now:
        return "due_now", "Due now"
    if next_due <= now + timedelta(seconds=SECONDS_PER_DAY):
        return "due_soon", "Due soon"
    if str(item.scheduler_state or "").strip().lower() == "review":
        return "reviewing", "Reviewing"
    return "learning", "Learning"


def _word_package_payload(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


def _summary(items: list[dict[str, object]], *, inventory_active_count: int) -> dict[str, int]:
    summary = _empty_summary()
    summary["total"] = len(items)
    summary["inventory_active_count"] = max(0, int(inventory_active_count))
    for item in items:
        status = str(item.get("status") or "")
        if item.get("active") is True:
            summary["active"] += 1
        if status in summary:
            summary[status] += 1
        if status in {"discarded", "cleared", "removed"}:
            summary["removed"] += 1
        advanced = item.get("advanced")
        if isinstance(advanced, Mapping) and advanced.get("word_package"):
            summary["with_word_package"] += 1
    return summary


def _empty_summary() -> dict[str, int]:
    return {
        "total": 0,
        "active": 0,
        "queued": 0,
        "due_now": 0,
        "due_soon": 0,
        "learning": 0,
        "reviewing": 0,
        "discarded": 0,
        "cleared": 0,
        "removed": 0,
        "with_word_package": 0,
        "inventory_active_count": 0,
    }


def _item_sort_key(item: dict[str, object]) -> tuple[int, int, str, str]:
    status_order = {
        "due_now": 0,
        "due_soon": 1,
        "learning": 2,
        "reviewing": 3,
        "queued": 4,
        "discarded": 8,
        "cleared": 8,
        "removed": 9,
    }
    due = item.get("due_in_seconds")
    due_order = int(due) if isinstance(due, int) else 10**12
    return (
        status_order.get(str(item.get("status") or ""), 7),
        due_order,
        str(item.get("display") or ""),
        str(item.get("item_id") or ""),
    )
