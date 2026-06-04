from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.store import SrsItem, SrsStore, srs_item_is_active
from lexishift_core.srs.time import now_utc, parse_ts


@dataclass(frozen=True)
class ActiveRotationReleasePolicy:
    min_history_count: int = 4
    min_future_due_days: int = 7
    require_review_state: bool = True


@dataclass(frozen=True)
class ActiveRotationReleaseResult:
    pair: str
    active_item_ids_before: Sequence[str] = field(default_factory=tuple)
    active_item_ids_after: Sequence[str] = field(default_factory=tuple)
    released_item_ids: Sequence[str] = field(default_factory=tuple)
    released_lemmas: Sequence[str] = field(default_factory=tuple)
    policy: ActiveRotationReleasePolicy = field(default_factory=ActiveRotationReleasePolicy)

    def to_dict(self) -> dict[str, object]:
        return active_rotation_release_result_to_dict(self)


def plan_active_rotation_capacity_release(
    *,
    store: SrsStore,
    pair: str,
    active_item_ids: Sequence[str],
    max_active_items: int,
    policy: Optional[ActiveRotationReleasePolicy] = None,
    now: Optional[datetime] = None,
) -> ActiveRotationReleaseResult:
    normalized_active_ids = _normalize_item_ids(active_item_ids)
    if len(normalized_active_ids) < max(1, int(max_active_items)):
        return ActiveRotationReleaseResult(
            pair=str(pair or "").strip(),
            active_item_ids_before=normalized_active_ids,
            active_item_ids_after=normalized_active_ids,
            policy=policy or ActiveRotationReleasePolicy(),
        )
    return plan_active_rotation_release(
        store=store,
        pair=pair,
        active_item_ids=normalized_active_ids,
        policy=policy,
        now=now,
    )


def plan_active_rotation_release(
    *,
    store: SrsStore,
    pair: str,
    active_item_ids: Sequence[str],
    policy: Optional[ActiveRotationReleasePolicy] = None,
    now: Optional[datetime] = None,
) -> ActiveRotationReleaseResult:
    policy = policy or ActiveRotationReleasePolicy()
    now = now or now_utc()
    normalized_pair = str(pair or "").strip()
    normalized_active_ids = _normalize_item_ids(active_item_ids)
    items_by_id = {
        item.item_id: item
        for item in store.items
        if item.language_pair == normalized_pair
        and srs_item_is_active(item)
        and str(item.item_id or "").strip()
    }

    retained: list[str] = []
    released_ids: list[str] = []
    released_lemmas: list[str] = []
    for item_id in normalized_active_ids:
        item = items_by_id.get(item_id)
        if item is None:
            continue
        if is_active_rotation_release_candidate(item, policy=policy, now=now):
            released_ids.append(item.item_id)
            released_lemmas.append(item.lemma)
            continue
        retained.append(item.item_id)

    return ActiveRotationReleaseResult(
        pair=normalized_pair,
        active_item_ids_before=normalized_active_ids,
        active_item_ids_after=tuple(retained),
        released_item_ids=tuple(released_ids),
        released_lemmas=tuple(released_lemmas),
        policy=policy,
    )


def is_active_rotation_release_candidate(
    item: SrsItem,
    *,
    policy: Optional[ActiveRotationReleasePolicy] = None,
    now: Optional[datetime] = None,
) -> bool:
    policy = policy or ActiveRotationReleasePolicy()
    if not srs_item_is_active(item):
        return False
    if policy.require_review_state and str(item.scheduler_state or "").strip().lower() != "review":
        return False
    if len(tuple(item.history or ())) < max(0, int(policy.min_history_count)):
        return False

    next_due = parse_ts(item.next_due)
    if next_due is None:
        return False
    now = now or now_utc()
    release_after = now + timedelta(days=max(0, int(policy.min_future_due_days)))
    return next_due >= release_after


def active_rotation_release_result_to_dict(
    result: ActiveRotationReleaseResult,
) -> dict[str, object]:
    return {
        "pair": result.pair,
        "active_count_before": len(tuple(result.active_item_ids_before)),
        "active_count_after": len(tuple(result.active_item_ids_after)),
        "released_count": len(tuple(result.released_item_ids)),
        "released_item_ids": list(result.released_item_ids),
        "released_lemmas": list(result.released_lemmas),
        "policy": active_rotation_release_policy_to_dict(result.policy),
    }


def active_rotation_release_policy_to_dict(
    policy: ActiveRotationReleasePolicy,
) -> Mapping[str, object]:
    return {
        "min_history_count": max(0, int(policy.min_history_count)),
        "min_future_due_days": max(0, int(policy.min_future_due_days)),
        "require_review_state": bool(policy.require_review_state),
    }


def _normalize_item_ids(values: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item_id = str(value or "").strip()
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        normalized.append(item_id)
    return tuple(normalized)
