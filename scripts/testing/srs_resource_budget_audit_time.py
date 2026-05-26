from __future__ import annotations

from datetime import datetime, timezone


def parse_datetime(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def age_days(value: object, *, now: datetime) -> int | None:
    parsed = parse_datetime(value)
    if parsed is None:
        return None
    return max(0, int((now - parsed).total_seconds() // (24 * 60 * 60)))
