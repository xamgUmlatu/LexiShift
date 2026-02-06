from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.srs_source import normalize_source_type
from lexishift_core.srs_time import now_utc

SIGNAL_FEEDBACK = "feedback"
SIGNAL_EXPOSURE = "exposure"


@dataclass(frozen=True)
class SrsSignalEvent:
    event_type: str
    pair: str
    lemma: str
    source_type: str
    rating: Optional[str] = None
    ts: str = field(default_factory=lambda: now_utc().isoformat())
    metadata: Mapping[str, object] = field(default_factory=dict)


def _normalize_event_type(value: object) -> str:
    event_type = str(value or "").strip().lower()
    if event_type in (SIGNAL_FEEDBACK, SIGNAL_EXPOSURE):
        return event_type
    return "unknown"


def _event_from_dict(data: Mapping[str, object]) -> Optional[SrsSignalEvent]:
    pair = str(data.get("pair", "")).strip()
    lemma = str(data.get("lemma", "")).strip()
    if not pair or not lemma:
        return None
    metadata = data.get("metadata") or {}
    if not isinstance(metadata, Mapping):
        metadata = {}
    return SrsSignalEvent(
        event_type=_normalize_event_type(data.get("event_type")),
        pair=pair,
        lemma=lemma,
        source_type=normalize_source_type(data.get("source_type")),
        rating=str(data.get("rating", "")).strip() or None,
        ts=str(data.get("ts", "")).strip() or now_utc().isoformat(),
        metadata={str(key): value for key, value in metadata.items()},
    )


def _event_to_dict(event: SrsSignalEvent) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_type": _normalize_event_type(event.event_type),
        "pair": event.pair,
        "lemma": event.lemma,
        "source_type": normalize_source_type(event.source_type),
        "ts": event.ts,
        "metadata": dict(event.metadata or {}),
    }
    if event.rating:
        payload["rating"] = event.rating
    return payload


def load_signal_events(path: Path) -> tuple[SrsSignalEvent, ...]:
    if not path.exists():
        return tuple()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return tuple()
    if not isinstance(data, Mapping):
        return tuple()
    raw_events = data.get("events")
    if not isinstance(raw_events, Sequence):
        return tuple()
    parsed: list[SrsSignalEvent] = []
    for entry in raw_events:
        if not isinstance(entry, Mapping):
            continue
        event = _event_from_dict(entry)
        if event is None:
            continue
        parsed.append(event)
    return tuple(parsed)


def save_signal_events(path: Path, events: Sequence[SrsSignalEvent], *, max_events: int = 5000) -> None:
    bounded = list(events)[-max(1, int(max_events)) :]
    payload = {
        "version": 1,
        "events": [_event_to_dict(event) for event in bounded],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_signal_event(path: Path, event: SrsSignalEvent, *, max_events: int = 5000) -> None:
    existing = list(load_signal_events(path))
    existing.append(event)
    save_signal_events(path, existing, max_events=max_events)


def summarize_signal_events(path: Path, *, pair: Optional[str] = None) -> dict[str, object]:
    events = load_signal_events(path)
    scoped = [
        event for event in events if not pair or event.pair == pair
    ]
    event_types: dict[str, int] = {}
    unique_lemmas = set()
    last_event_at = ""
    for event in scoped:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        unique_lemmas.add(event.lemma)
        if event.ts and event.ts > last_event_at:
            last_event_at = event.ts
    return {
        "pair": pair or "all",
        "event_count": len(scoped),
        "event_types": event_types,
        "unique_lemmas": len(unique_lemmas),
        "last_event_at": last_event_at or None,
    }
