from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import json
from math import ceil
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from lexishift_core.srs.scheduler import RATING_EASY, RATING_GOOD
from lexishift_core.srs.signal_queue import SIGNAL_FEEDBACK, SrsSignalEvent
from lexishift_core.srs.time import format_ts, now_utc, parse_ts


DEFAULT_AUTO_REFRESH_MIN_FEEDBACK_EVENTS = 8
DEFAULT_AUTO_REFRESH_MIN_GOOD_EASY = 6
DEFAULT_AUTO_REFRESH_REPEAT_MIN_GOOD_EASY = 12
DEFAULT_AUTO_REFRESH_COOLDOWN_MINUTES = 90

GOOD_EASY_RATINGS = frozenset({RATING_GOOD, RATING_EASY})


@dataclass(frozen=True)
class SrsAutoRefreshPolicy:
    enabled: bool = True
    min_feedback_events: int = DEFAULT_AUTO_REFRESH_MIN_FEEDBACK_EVENTS
    min_good_easy: int = DEFAULT_AUTO_REFRESH_MIN_GOOD_EASY
    repeat_min_good_easy: int = DEFAULT_AUTO_REFRESH_REPEAT_MIN_GOOD_EASY
    cooldown_minutes: int = DEFAULT_AUTO_REFRESH_COOLDOWN_MINUTES


@dataclass(frozen=True)
class SrsAutoRefreshPairState:
    last_attempted_at: Optional[str] = None
    last_applied_at: Optional[str] = None
    last_result_reason: Optional[str] = None
    attempt_count: int = 0
    applied_count: int = 0


@dataclass(frozen=True)
class SrsAutoRefreshState:
    pairs: Mapping[str, SrsAutoRefreshPairState] = field(default_factory=dict)
    version: int = 1


@dataclass(frozen=True)
class SrsAutoRefreshDecision:
    pair: str
    eligible: bool
    reason_code: str
    feedback_count: int
    good_easy_count: int
    required_feedback_events: int
    required_good_easy_events: int
    cooldown_minutes: int
    cooldown_remaining_minutes: int
    attempted_today: bool
    last_attempted_at: Optional[str]
    last_applied_at: Optional[str]
    window_started_at: Optional[str]


def normalize_auto_refresh_policy(policy: Optional[SrsAutoRefreshPolicy]) -> SrsAutoRefreshPolicy:
    source = policy or SrsAutoRefreshPolicy()
    min_feedback = _positive_int(
        source.min_feedback_events,
        fallback=DEFAULT_AUTO_REFRESH_MIN_FEEDBACK_EVENTS,
    )
    min_good_easy = _positive_int(
        source.min_good_easy,
        fallback=DEFAULT_AUTO_REFRESH_MIN_GOOD_EASY,
    )
    repeat_min_good_easy = max(
        min_good_easy,
        _positive_int(
            source.repeat_min_good_easy,
            fallback=DEFAULT_AUTO_REFRESH_REPEAT_MIN_GOOD_EASY,
        ),
    )
    cooldown_minutes = max(0, int(source.cooldown_minutes or 0))
    return SrsAutoRefreshPolicy(
        enabled=source.enabled is not False,
        min_feedback_events=min_feedback,
        min_good_easy=min_good_easy,
        repeat_min_good_easy=repeat_min_good_easy,
        cooldown_minutes=cooldown_minutes,
    )


def plan_auto_refresh(
    events: Iterable[SrsSignalEvent],
    *,
    pair: str,
    state: Optional[SrsAutoRefreshPairState] = None,
    policy: Optional[SrsAutoRefreshPolicy] = None,
    now: Optional[datetime] = None,
) -> SrsAutoRefreshDecision:
    normalized_pair = str(pair or "").strip()
    resolved_policy = normalize_auto_refresh_policy(policy)
    pair_state = state or SrsAutoRefreshPairState()
    now = now or now_utc()
    last_attempted_at = parse_ts(pair_state.last_attempted_at)
    attempted_today = bool(last_attempted_at and last_attempted_at.date() == now.date())
    required_good_easy = (
        resolved_policy.repeat_min_good_easy if attempted_today else resolved_policy.min_good_easy
    )

    feedback_events = _feedback_events_since(
        events,
        pair=normalized_pair,
        started_after=last_attempted_at,
    )
    feedback_count = len(feedback_events)
    good_easy_count = sum(
        1
        for event in feedback_events
        if str(event.rating or "").strip().lower() in GOOD_EASY_RATINGS
    )

    cooldown_remaining_minutes = _cooldown_remaining_minutes(
        last_attempted_at,
        now=now,
        cooldown_minutes=resolved_policy.cooldown_minutes,
    )
    reason_code = "eligible"
    eligible = True
    if not resolved_policy.enabled:
        eligible = False
        reason_code = "disabled"
    elif cooldown_remaining_minutes > 0:
        eligible = False
        reason_code = "cooldown_active"
    elif feedback_count < resolved_policy.min_feedback_events:
        eligible = False
        reason_code = "insufficient_feedback"
    elif good_easy_count < required_good_easy:
        eligible = False
        reason_code = "insufficient_good_easy"

    return SrsAutoRefreshDecision(
        pair=normalized_pair,
        eligible=eligible,
        reason_code=reason_code,
        feedback_count=feedback_count,
        good_easy_count=good_easy_count,
        required_feedback_events=resolved_policy.min_feedback_events,
        required_good_easy_events=required_good_easy,
        cooldown_minutes=resolved_policy.cooldown_minutes,
        cooldown_remaining_minutes=cooldown_remaining_minutes,
        attempted_today=attempted_today,
        last_attempted_at=pair_state.last_attempted_at,
        last_applied_at=pair_state.last_applied_at,
        window_started_at=pair_state.last_attempted_at,
    )


def auto_refresh_decision_to_dict(decision: SrsAutoRefreshDecision) -> dict[str, object]:
    return {
        "pair": decision.pair,
        "eligible": decision.eligible,
        "reason_code": decision.reason_code,
        "feedback_count": decision.feedback_count,
        "good_easy_count": decision.good_easy_count,
        "required_feedback_events": decision.required_feedback_events,
        "required_good_easy_events": decision.required_good_easy_events,
        "cooldown_minutes": decision.cooldown_minutes,
        "cooldown_remaining_minutes": decision.cooldown_remaining_minutes,
        "attempted_today": decision.attempted_today,
        "last_attempted_at": decision.last_attempted_at,
        "last_applied_at": decision.last_applied_at,
        "window_started_at": decision.window_started_at,
    }


def record_auto_refresh_attempt(
    state: SrsAutoRefreshState,
    *,
    pair: str,
    now: Optional[datetime] = None,
    applied: bool,
    reason_code: str,
) -> SrsAutoRefreshState:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        return state
    timestamp = format_ts(now or now_utc())
    pairs = dict(state.pairs or {})
    current = pairs.get(normalized_pair, SrsAutoRefreshPairState())
    pairs[normalized_pair] = replace(
        current,
        last_attempted_at=timestamp,
        last_applied_at=timestamp if applied else current.last_applied_at,
        last_result_reason=str(reason_code or "").strip() or None,
        attempt_count=max(0, int(current.attempt_count or 0)) + 1,
        applied_count=max(0, int(current.applied_count or 0)) + (1 if applied else 0),
    )
    return SrsAutoRefreshState(pairs=pairs, version=max(1, int(state.version or 1)))


def remove_auto_refresh_pair_state(state: SrsAutoRefreshState, *, pair: str) -> SrsAutoRefreshState:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        return state
    pairs = dict(state.pairs or {})
    pairs.pop(normalized_pair, None)
    return SrsAutoRefreshState(pairs=pairs, version=max(1, int(state.version or 1)))


def load_auto_refresh_state(path: Path) -> SrsAutoRefreshState:
    if not path.exists():
        return SrsAutoRefreshState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return SrsAutoRefreshState()
    if not isinstance(data, Mapping):
        return SrsAutoRefreshState()
    return auto_refresh_state_from_dict(data)


def save_auto_refresh_state(state: SrsAutoRefreshState, path: Path) -> None:
    normalized_path = Path(path)
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(auto_refresh_state_to_dict(state), indent=2, sort_keys=True)
    normalized_path.write_text(payload + "\n", encoding="utf-8")


def auto_refresh_state_from_dict(data: Mapping[str, Any]) -> SrsAutoRefreshState:
    raw_pairs = data.get("pairs")
    pairs: dict[str, SrsAutoRefreshPairState] = {}
    if isinstance(raw_pairs, Mapping):
        for pair, value in raw_pairs.items():
            normalized_pair = str(pair or "").strip()
            if not normalized_pair or not isinstance(value, Mapping):
                continue
            pairs[normalized_pair] = SrsAutoRefreshPairState(
                last_attempted_at=_optional_str(value.get("last_attempted_at")),
                last_applied_at=_optional_str(value.get("last_applied_at")),
                last_result_reason=_optional_str(value.get("last_result_reason")),
                attempt_count=max(0, int(value.get("attempt_count", 0) or 0)),
                applied_count=max(0, int(value.get("applied_count", 0) or 0)),
            )
    return SrsAutoRefreshState(
        pairs=pairs,
        version=max(1, int(data.get("version", 1) or 1)),
    )


def auto_refresh_state_to_dict(state: SrsAutoRefreshState) -> dict[str, object]:
    return {
        "version": max(1, int(state.version or 1)),
        "pairs": {
            str(pair): _pair_state_to_dict(pair_state)
            for pair, pair_state in dict(state.pairs or {}).items()
        },
    }


def _pair_state_to_dict(state: SrsAutoRefreshPairState) -> dict[str, object]:
    payload = {
        "last_attempted_at": state.last_attempted_at,
        "last_applied_at": state.last_applied_at,
        "last_result_reason": state.last_result_reason,
        "attempt_count": max(0, int(state.attempt_count or 0)),
        "applied_count": max(0, int(state.applied_count or 0)),
    }
    return {key: value for key, value in payload.items() if value not in (None, "")}


def _feedback_events_since(
    events: Iterable[SrsSignalEvent],
    *,
    pair: str,
    started_after: Optional[datetime],
) -> list[SrsSignalEvent]:
    scoped: list[SrsSignalEvent] = []
    for event in events:
        if event.event_type != SIGNAL_FEEDBACK or event.pair != pair:
            continue
        if started_after is not None:
            event_ts = parse_ts(event.ts)
            if event_ts is None or event_ts <= started_after:
                continue
        scoped.append(event)
    return scoped


def _cooldown_remaining_minutes(
    last_attempted_at: Optional[datetime],
    *,
    now: datetime,
    cooldown_minutes: int,
) -> int:
    if last_attempted_at is None or cooldown_minutes <= 0:
        return 0
    elapsed_seconds = max(0.0, (now - last_attempted_at).total_seconds())
    remaining_seconds = (cooldown_minutes * 60) - elapsed_seconds
    if remaining_seconds <= 0:
        return 0
    return max(1, int(ceil(remaining_seconds / 60.0)))


def _positive_int(value: object, *, fallback: int) -> int:
    try:
        if isinstance(value, bool):
            parsed = int(value)
        elif isinstance(value, (int, float)):
            parsed = int(value)
        else:
            parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        parsed = int(fallback)
    return max(1, parsed)


def _optional_str(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
