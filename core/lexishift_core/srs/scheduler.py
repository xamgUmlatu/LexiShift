from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
from typing import Iterable, Optional, Sequence

from fsrs import Card, Rating as FsrsRating, Scheduler as FsrsScheduler, State as FsrsState

from lexishift_core.srs import (
    SrsHistoryEntry,
    SrsItem,
    SrsSchedulerSettings,
    SrsSettings,
)
from lexishift_core.srs.time import format_ts, now_utc, parse_ts


RATING_AGAIN = "again"
RATING_HARD = "hard"
RATING_GOOD = "good"
RATING_EASY = "easy"
RATINGS = {RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY}

SCHEDULER_ALGORITHM_FSRS = "fsrs"
STATE_LEARNING = "learning"
STATE_REVIEW = "review"
STATE_RELEARNING = "relearning"


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
    settings: Optional[SrsSettings] = None,
) -> SrsItem:
    rating = rating.lower().strip()
    if rating not in RATINGS:
        raise ValueError(f"Unknown rating: {rating}")
    now = now or now_utc()

    scheduler = build_scheduler(settings=settings)
    card = _card_from_item(item, now=now)
    reviewed_card, _review_log = scheduler.review_card(
        card,
        _rating_to_fsrs(rating),
        review_datetime=_ensure_utc(now),
    )
    history = tuple(item.history) + (SrsHistoryEntry(ts=format_ts(now), rating=rating),)

    return replace(
        item,
        stability=float(reviewed_card.stability) if reviewed_card.stability is not None else None,
        difficulty=(
            float(reviewed_card.difficulty) if reviewed_card.difficulty is not None else None
        ),
        last_seen=format_ts(now),
        last_review=(
            format_ts(reviewed_card.last_review) if reviewed_card.last_review is not None else None
        ),
        next_due=format_ts(reviewed_card.due),
        scheduler_state=_state_to_name(reviewed_card.state),
        scheduler_step=reviewed_card.step,
        history=history,
    )


def build_scheduler(*, settings: Optional[SrsSettings] = None) -> FsrsScheduler:
    scheduler = settings.scheduler if settings is not None else SrsSchedulerSettings()
    return _build_scheduler_cached(
        algorithm=str(scheduler.algorithm or SCHEDULER_ALGORITHM_FSRS).strip().lower(),
        desired_retention=float(scheduler.desired_retention),
        learning_steps_minutes=tuple(int(value) for value in scheduler.learning_steps_minutes),
        relearning_steps_minutes=tuple(int(value) for value in scheduler.relearning_steps_minutes),
        maximum_interval_days=int(scheduler.maximum_interval_days),
        enable_fuzzing=bool(scheduler.enable_fuzzing),
        parameters=(
            tuple(float(value) for value in scheduler.parameters)
            if scheduler.parameters is not None
            else None
        ),
    )


def get_item_retrievability(
    item: SrsItem,
    *,
    settings: Optional[SrsSettings] = None,
    now: Optional[datetime] = None,
) -> Optional[float]:
    if item.stability is None or item.difficulty is None:
        return None
    if _resolved_last_review(item) is None:
        return None
    now = now or now_utc()
    scheduler = build_scheduler(settings=settings)
    card = _card_from_item(item, now=now)
    return float(scheduler.get_card_retrievability(card, current_datetime=_ensure_utc(now)))


def normalize_scheduler_difficulty(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    parsed = float(value)
    if 0.0 <= parsed <= 1.0:
        return parsed
    return max(0.0, min(1.0, (parsed - 1.0) / 9.0))


@lru_cache(maxsize=16)
def _build_scheduler_cached(
    *,
    algorithm: str,
    desired_retention: float,
    learning_steps_minutes: tuple[int, ...],
    relearning_steps_minutes: tuple[int, ...],
    maximum_interval_days: int,
    enable_fuzzing: bool,
    parameters: Optional[tuple[float, ...]],
) -> FsrsScheduler:
    if algorithm != SCHEDULER_ALGORITHM_FSRS:
        algorithm = SCHEDULER_ALGORITHM_FSRS
    learning_steps = tuple(timedelta(minutes=value) for value in learning_steps_minutes)
    relearning_steps = tuple(timedelta(minutes=value) for value in relearning_steps_minutes)
    if parameters is not None:
        return FsrsScheduler(
            parameters=parameters,
            desired_retention=desired_retention,
            learning_steps=learning_steps,
            relearning_steps=relearning_steps,
            maximum_interval=maximum_interval_days,
            enable_fuzzing=enable_fuzzing,
        )
    return FsrsScheduler(
        desired_retention=desired_retention,
        learning_steps=learning_steps,
        relearning_steps=relearning_steps,
        maximum_interval=maximum_interval_days,
        enable_fuzzing=enable_fuzzing,
    )


def _card_from_item(item: SrsItem, *, now: datetime) -> Card:
    due = parse_ts(item.next_due) or _ensure_utc(now)
    state = _state_from_item(item)
    step = item.scheduler_step
    if state == FsrsState.Learning and step is None:
        step = 0
    if state == FsrsState.Review:
        step = None
    return Card(
        card_id=_card_id_from_item(item),
        state=state,
        step=step,
        stability=float(item.stability) if item.stability is not None else None,
        difficulty=float(item.difficulty) if item.difficulty is not None else None,
        due=_ensure_utc(due),
        last_review=_resolved_last_review(item),
    )


def _state_from_item(item: SrsItem) -> FsrsState:
    raw_state = str(item.scheduler_state or "").strip().lower()
    if raw_state == STATE_REVIEW:
        return FsrsState.Review
    if raw_state == STATE_RELEARNING:
        return FsrsState.Relearning
    if raw_state == STATE_LEARNING:
        return FsrsState.Learning
    if item.stability is not None and item.difficulty is not None and item.history:
        return FsrsState.Review
    return FsrsState.Learning


def _state_to_name(state: FsrsState) -> str:
    if state == FsrsState.Review:
        return STATE_REVIEW
    if state == FsrsState.Relearning:
        return STATE_RELEARNING
    return STATE_LEARNING


def _rating_to_fsrs(rating: str) -> FsrsRating:
    if rating == RATING_AGAIN:
        return FsrsRating.Again
    if rating == RATING_HARD:
        return FsrsRating.Hard
    if rating == RATING_GOOD:
        return FsrsRating.Good
    return FsrsRating.Easy


def _card_id_from_item(item: SrsItem) -> int:
    digest = hashlib.sha1(item.item_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _resolved_last_review(item: SrsItem) -> Optional[datetime]:
    last_review = parse_ts(item.last_review)
    if last_review is not None:
        return _ensure_utc(last_review)
    history = tuple(item.history)
    if history:
        resolved = parse_ts(history[-1].ts)
        if resolved is not None:
            return _ensure_utc(resolved)
    if item.last_seen is not None and history:
        resolved = parse_ts(item.last_seen)
        if resolved is not None:
            return _ensure_utc(resolved)
    return None


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
