from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Optional, Sequence

from lexishift_core.srs import SrsHistoryEntry, SrsItem, SrsStore
from lexishift_core.srs_scheduler import apply_feedback
from lexishift_core.srs_time import format_ts, now_utc


def build_item_id(language_pair: str, lemma: str) -> str:
    return f"{language_pair}:{lemma}"


def find_item(store: SrsStore, *, language_pair: str, lemma: str) -> Optional[SrsItem]:
    item_id = build_item_id(language_pair, lemma)
    for item in store.items:
        if item.item_id == item_id:
            return item
    return None


def upsert_item(store: SrsStore, item: SrsItem) -> SrsStore:
    items = list(store.items)
    for idx, existing in enumerate(items):
        if existing.item_id == item.item_id:
            items[idx] = item
            return SrsStore(items=tuple(items), version=store.version)
    items.append(item)
    return SrsStore(items=tuple(items), version=store.version)


def record_exposure(
    store: SrsStore,
    *,
    language_pair: str,
    lemma: str,
    now: Optional[datetime] = None,
    create_if_missing: bool = False,
    source_type: str = "unknown",
) -> SrsStore:
    now = now or now_utc()
    item = find_item(store, language_pair=language_pair, lemma=lemma)
    if item is None:
        if not create_if_missing:
            return store
        item = SrsItem(
            item_id=build_item_id(language_pair, lemma),
            lemma=lemma,
            language_pair=language_pair,
            source_type=source_type,
            exposures=0,
        )
    updated = replace(
        item,
        exposures=item.exposures + 1,
        last_seen=format_ts(now),
    )
    return upsert_item(store, updated)


def record_feedback(
    store: SrsStore,
    *,
    language_pair: str,
    lemma: str,
    rating: str,
    now: Optional[datetime] = None,
    create_if_missing: bool = False,
    source_type: str = "unknown",
    increment_exposures: bool = True,
) -> SrsStore:
    now = now or now_utc()
    item = find_item(store, language_pair=language_pair, lemma=lemma)
    if item is None:
        if not create_if_missing:
            return store
        item = SrsItem(
            item_id=build_item_id(language_pair, lemma),
            lemma=lemma,
            language_pair=language_pair,
            source_type=source_type,
            history=(),
        )
    updated = apply_feedback(item, rating, now=now)
    if increment_exposures:
        updated = replace(updated, exposures=updated.exposures + 1)
    return upsert_item(store, updated)


def append_history(
    store: SrsStore,
    *,
    language_pair: str,
    lemma: str,
    rating: str,
    now: Optional[datetime] = None,
    create_if_missing: bool = False,
    source_type: str = "unknown",
) -> SrsStore:
    now = now or now_utc()
    item = find_item(store, language_pair=language_pair, lemma=lemma)
    if item is None:
        if not create_if_missing:
            return store
        item = SrsItem(
            item_id=build_item_id(language_pair, lemma),
            lemma=lemma,
            language_pair=language_pair,
            source_type=source_type,
            history=(),
        )
    history: Sequence[SrsHistoryEntry] = tuple(item.history) + (
        SrsHistoryEntry(ts=format_ts(now), rating=rating),
    )
    updated = replace(item, history=history)
    return upsert_item(store, updated)
