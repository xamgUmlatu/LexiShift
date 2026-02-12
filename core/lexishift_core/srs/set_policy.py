from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence


# Keep sizing policy constants centralized so callers do not duplicate
# "magic numbers" in UI, planner, and helper execution paths.
DEFAULT_BOOTSTRAP_TOP_N = 800
MIN_BOOTSTRAP_TOP_N = 200
MAX_BOOTSTRAP_TOP_N = 50000

DEFAULT_INITIAL_ACTIVE_COUNT = 40
MIN_INITIAL_ACTIVE_COUNT = 1
MAX_INITIAL_ACTIVE_COUNT = 5000


@dataclass(frozen=True)
class SrsSetSizingPolicy:
    bootstrap_top_n_requested: Optional[int]
    bootstrap_top_n_effective: int
    initial_active_count_requested: Optional[int]
    initial_active_count_effective: int
    max_active_items_hint: Optional[int] = None
    notes: Sequence[str] = field(default_factory=tuple)


def _parse_optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, float):
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return None
    return None


def _clamp(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def resolve_set_sizing_policy(
    *,
    bootstrap_top_n: object,
    initial_active_count: object,
    max_active_items_hint: object,
) -> SrsSetSizingPolicy:
    notes: list[str] = []
    requested_top_n = _parse_optional_int(bootstrap_top_n)
    if requested_top_n is None:
        effective_top_n = DEFAULT_BOOTSTRAP_TOP_N
        notes.append(
            f"bootstrap_top_n missing/invalid; defaulting to {DEFAULT_BOOTSTRAP_TOP_N}."
        )
    else:
        effective_top_n = _clamp(
            requested_top_n,
            minimum=MIN_BOOTSTRAP_TOP_N,
            maximum=MAX_BOOTSTRAP_TOP_N,
        )
        if effective_top_n != requested_top_n:
            notes.append(
                f"bootstrap_top_n clamped to {effective_top_n} "
                f"(allowed: {MIN_BOOTSTRAP_TOP_N}..{MAX_BOOTSTRAP_TOP_N})."
            )

    hint_max_active = _parse_optional_int(max_active_items_hint)
    if hint_max_active is not None and hint_max_active > 0:
        hint_max_active = _clamp(
            hint_max_active,
            minimum=MIN_INITIAL_ACTIVE_COUNT,
            maximum=MAX_INITIAL_ACTIVE_COUNT,
        )
    else:
        hint_max_active = None

    requested_initial_active = _parse_optional_int(initial_active_count)
    if requested_initial_active is None:
        effective_initial_active = hint_max_active or DEFAULT_INITIAL_ACTIVE_COUNT
        notes.append(
            f"initial_active_count missing/invalid; defaulting to {effective_initial_active}."
        )
    else:
        effective_initial_active = _clamp(
            requested_initial_active,
            minimum=MIN_INITIAL_ACTIVE_COUNT,
            maximum=MAX_INITIAL_ACTIVE_COUNT,
        )
        if effective_initial_active != requested_initial_active:
            notes.append(
                f"initial_active_count clamped to {effective_initial_active} "
                f"(allowed: {MIN_INITIAL_ACTIVE_COUNT}..{MAX_INITIAL_ACTIVE_COUNT})."
            )

    if effective_initial_active > effective_top_n:
        effective_initial_active = effective_top_n
        notes.append("initial_active_count exceeded bootstrap_top_n and was clamped.")

    return SrsSetSizingPolicy(
        bootstrap_top_n_requested=requested_top_n,
        bootstrap_top_n_effective=effective_top_n,
        initial_active_count_requested=requested_initial_active,
        initial_active_count_effective=effective_initial_active,
        max_active_items_hint=hint_max_active,
        notes=tuple(notes),
    )
