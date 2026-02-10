from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import random
from typing import Optional, Sequence

from lexishift_core.srs import SrsItem, SrsStore
from lexishift_core.srs.time import now_utc, parse_ts


SAMPLE_STRATEGY_WEIGHTED_PRIORITY = "weighted_priority"
SAMPLE_STRATEGY_UNIFORM = "uniform"
SUPPORTED_SAMPLE_STRATEGIES = {
    SAMPLE_STRATEGY_WEIGHTED_PRIORITY,
    SAMPLE_STRATEGY_UNIFORM,
}

DEFAULT_SAMPLE_COUNT = 5
MAX_SAMPLE_COUNT = 200


@dataclass(frozen=True)
class SrsSamplingResult:
    pair: str
    strategy_requested: Optional[str]
    strategy_effective: str
    sample_count_requested: int
    sample_count_effective: int
    total_items_for_pair: int
    sampled_lemmas: Sequence[str]
    weight_sample: Sequence[dict[str, object]]
    notes: Sequence[str]


def sample_store_items(
    store: SrsStore,
    *,
    pair: str,
    sample_count: Optional[int],
    strategy: Optional[str] = None,
    seed: Optional[int] = None,
    now: Optional[datetime] = None,
) -> SrsSamplingResult:
    now = now or now_utc()
    normalized_pair = str(pair or "").strip()
    normalized_strategy = str(strategy or "").strip() or SAMPLE_STRATEGY_WEIGHTED_PRIORITY
    notes: list[str] = []
    if normalized_strategy not in SUPPORTED_SAMPLE_STRATEGIES:
        notes.append(
            f"Unknown sample strategy '{normalized_strategy}'. Falling back to "
            f"{SAMPLE_STRATEGY_WEIGHTED_PRIORITY}."
        )
        effective_strategy = SAMPLE_STRATEGY_WEIGHTED_PRIORITY
    else:
        effective_strategy = normalized_strategy

    parsed_count = _parse_optional_int(sample_count)
    requested_count = _normalize_sample_count(parsed_count)
    if parsed_count is None:
        notes.append(f"sample_count missing/invalid; defaulting to {DEFAULT_SAMPLE_COUNT}.")
    elif requested_count != parsed_count:
        notes.append(f"sample_count clamped to {requested_count} (max {MAX_SAMPLE_COUNT}).")

    candidates = [
        item
        for item in store.items
        if item.language_pair == normalized_pair and str(item.lemma or "").strip()
    ]
    requested = min(requested_count, len(candidates))
    weights = _build_weights(candidates, now=now, strategy=effective_strategy)
    sampled = _weighted_sample_without_replacement(
        candidates,
        weights=weights,
        sample_count=requested,
        seed=seed,
    )
    weight_sample = _build_weight_sample(candidates, weights, limit=10)
    return SrsSamplingResult(
        pair=normalized_pair,
        strategy_requested=normalized_strategy,
        strategy_effective=effective_strategy,
        sample_count_requested=requested_count,
        sample_count_effective=len(sampled),
        total_items_for_pair=len(candidates),
        sampled_lemmas=tuple(item.lemma for item in sampled),
        weight_sample=tuple(weight_sample),
        notes=tuple(notes),
    )


def sampling_result_to_dict(result: SrsSamplingResult) -> dict[str, object]:
    return {
        "pair": result.pair,
        "strategy_requested": result.strategy_requested,
        "strategy_effective": result.strategy_effective,
        "sample_count_requested": result.sample_count_requested,
        "sample_count_effective": result.sample_count_effective,
        "total_items_for_pair": result.total_items_for_pair,
        "sampled_lemmas": list(result.sampled_lemmas),
        "weight_sample": list(result.weight_sample),
        "notes": list(result.notes),
    }


def _normalize_sample_count(value: Optional[int]) -> int:
    if value is None:
        return DEFAULT_SAMPLE_COUNT
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_SAMPLE_COUNT
    if parsed < 1:
        return DEFAULT_SAMPLE_COUNT
    if parsed > MAX_SAMPLE_COUNT:
        return MAX_SAMPLE_COUNT
    return parsed


def _parse_optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_weights(
    items: Sequence[SrsItem],
    *,
    now: datetime,
    strategy: str,
) -> list[float]:
    if strategy == SAMPLE_STRATEGY_UNIFORM:
        return [1.0 for _ in items]
    return [_priority_weight(item, now=now) for item in items]


def _priority_weight(item: SrsItem, *, now: datetime) -> float:
    difficulty = _clamp_01(item.difficulty if item.difficulty is not None else 0.5)
    stability = max(0.25, float(item.stability)) if item.stability is not None else 1.0
    history_size = len(item.history or ())
    novelty_bonus = 0.35 if history_size == 0 else 0.0

    base = 1.0
    base += difficulty * 1.5
    base += 1.0 / stability
    base += min(0.5, history_size / 20.0)
    base += novelty_bonus

    next_due = parse_ts(item.next_due)
    if next_due is None:
        due_multiplier = 1.1
    else:
        delta_days = (next_due - now).total_seconds() / 86400.0
        if delta_days <= 0:
            due_multiplier = 1.5 + min(2.0, abs(delta_days) / 7.0)
        else:
            due_multiplier = max(0.25, 1.0 / (1.0 + (delta_days / 14.0)))

    return max(0.001, base * due_multiplier)


def _weighted_sample_without_replacement(
    items: Sequence[SrsItem],
    *,
    weights: Sequence[float],
    sample_count: int,
    seed: Optional[int],
) -> list[SrsItem]:
    rng = random.Random(seed)
    pool = list(zip(items, weights))
    selected: list[SrsItem] = []
    target = max(0, int(sample_count))
    while len(selected) < target and pool:
        total = sum(max(0.0, weight) for _item, weight in pool)
        if total <= 0:
            break
        roll = rng.random() * total
        pick_index = 0
        for index, (_item, weight) in enumerate(pool):
            roll -= max(0.0, weight)
            if roll <= 0:
                pick_index = index
                break
        item, _weight = pool.pop(pick_index)
        selected.append(item)
    return selected


def _build_weight_sample(
    items: Sequence[SrsItem],
    weights: Sequence[float],
    *,
    limit: int,
) -> list[dict[str, object]]:
    ranked = sorted(
        zip(items, weights),
        key=lambda entry: entry[1],
        reverse=True,
    )
    sample = []
    for item, weight in ranked[: max(1, int(limit))]:
        sample.append(
            {
                "lemma": item.lemma,
                "weight": round(float(weight), 6),
                "next_due": item.next_due,
                "difficulty": item.difficulty,
                "stability": item.stability,
            }
        )
    return sample


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
