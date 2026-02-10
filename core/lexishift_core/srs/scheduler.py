from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Iterable, Optional, Sequence

from lexishift_core.srs import SrsHistoryEntry, SrsItem
from lexishift_core.srs.time import format_ts, now_utc, parse_ts


RATING_AGAIN = "again"
RATING_HARD = "hard"
RATING_GOOD = "good"
RATING_EASY = "easy"
RATINGS = {RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY}


def select_active_items(
    items: Iterable[SrsItem],
    *,
    now: Optional[datetime] = None,
    max_active: int = 40,
    allowed_pairs: Optional[Sequence[str]] = None,
) -> list[SrsItem]:
    now = now or now_utc()
    allowed = set(allowed_pairs or [])
    due: list[tuple[datetime, SrsItem]] = []
    for item in items:
        if allowed and item.language_pair not in allowed:
            continue
        next_due = parse_ts(item.next_due)
        due_time = next_due or datetime.min.replace(tzinfo=now.tzinfo)
        if next_due is None or next_due <= now:
            due.append((due_time, item))
    due.sort(key=lambda entry: entry[0])
    return [item for _time, item in due[: max(0, max_active)]]


def apply_feedback(
    item: SrsItem,
    rating: str,
    *,
    now: Optional[datetime] = None,
) -> SrsItem:
    rating = rating.lower().strip()
    if rating not in RATINGS:
        raise ValueError(f"Unknown rating: {rating}")
    now = now or now_utc()

    stability = item.stability if item.stability is not None else 1.0
    difficulty = item.difficulty if item.difficulty is not None else 0.5

    if rating == RATING_AGAIN:
        interval = max(1, int(round(stability * 0.5)))
        stability = max(0.5, stability * 0.5)
        difficulty = min(1.0, difficulty + 0.15)
    elif rating == RATING_HARD:
        interval = max(1, int(round(stability * 2.0)))
        stability = stability * 1.2
        difficulty = min(1.0, difficulty + 0.05)
    elif rating == RATING_GOOD:
        interval = max(1, int(round(stability * 4.0)))
        stability = stability * 1.5
        difficulty = max(0.2, difficulty - 0.05)
    else:
        interval = max(1, int(round(stability * 6.0)))
        stability = stability * 1.8
        difficulty = max(0.2, difficulty - 0.1)

    next_due = now + timedelta(days=interval)
    history = tuple(item.history) + (SrsHistoryEntry(ts=format_ts(now), rating=rating),)

    return replace(
        item,
        stability=stability,
        difficulty=difficulty,
        last_seen=format_ts(now),
        next_due=format_ts(next_due),
        exposures=item.exposures,
        history=history,
    )
