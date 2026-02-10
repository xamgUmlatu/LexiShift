from __future__ import annotations

from typing import Iterable

SOURCE_INITIAL_SET = "initial_set"
SOURCE_EXTENSION = "extension"
SOURCE_FREQUENCY_LIST = "frequency_list"
SOURCE_USER_STREAM = "user_stream"
SOURCE_CURATED = "curated"
SOURCE_UNKNOWN = "unknown"

KNOWN_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        SOURCE_INITIAL_SET,
        SOURCE_EXTENSION,
        SOURCE_FREQUENCY_LIST,
        SOURCE_USER_STREAM,
        SOURCE_CURATED,
        SOURCE_UNKNOWN,
    }
)


def normalize_source_type(value: object, *, default: str = SOURCE_UNKNOWN) -> str:
    source = str(value or "").strip().lower()
    if not source:
        return default
    if source in KNOWN_SOURCE_TYPES:
        return source
    return source


def merge_source_types(values: Iterable[object]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        normalized = normalize_source_type(value)
        if normalized not in seen:
            seen.append(normalized)
    return tuple(seen)
