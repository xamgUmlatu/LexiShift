from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs import (
    SRS_LIFECYCLE_DISCARDED,
    active_item_ids_for_pair,
    load_srs_inventory,
    load_srs_store,
    save_srs_inventory,
    save_srs_store,
    set_active_item_ids,
)
from lexishift_core.srs.admission_suppression import (
    SrsAdmissionSuppressionPolicy,
    active_suppressed_lemmas,
    create_admission_suppression,
    load_admission_suppression_store,
    prune_expired_suppression_entries,
    save_admission_suppression_store,
    upsert_admission_suppression,
)
from lexishift_core.srs.store_ops import mark_item_lifecycle


def suppress_srs_admission(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    reason: str = "user_blocked",
    profile_id: str = "default",
    note: str | None = None,
    policy: Optional[SrsAdmissionSuppressionPolicy] = None,
    now: Optional[datetime] = None,
    resolve_profile_id_fn: Callable[..., str],
) -> dict[str, object]:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("SRS admission suppression requires a language pair.")
    normalized_lemma = str(lemma or "").strip()
    if not normalized_lemma:
        raise ValueError("SRS admission suppression requires a lemma.")

    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    suppression_path = paths.srs_admission_suppression_store_path_for(normalized_profile_id)
    policy = policy or SrsAdmissionSuppressionPolicy()
    existing_store = load_admission_suppression_store(suppression_path)
    store = prune_expired_suppression_entries(existing_store, now=now)
    if store.profile_id != normalized_profile_id:
        store = type(store)(
            profile_id=normalized_profile_id,
            entries=store.entries,
            version=store.version,
            policy_version=policy.version,
            updated_at=store.updated_at,
        )

    entry = create_admission_suppression(
        pair=normalized_pair,
        lemma=normalized_lemma,
        reason=reason,
        policy=policy,
        now=now,
        note=note,
    )
    updated_store = upsert_admission_suppression(store, entry, now=now)
    save_admission_suppression_store(updated_store, suppression_path)
    active = active_suppressed_lemmas(updated_store, pair=normalized_pair, now=now)
    active_reason = active.get(normalized_lemma)
    srs_store_mutation, removed_active_item = _mark_existing_item_discarded(
        paths,
        pair=normalized_pair,
        lemma=normalized_lemma,
        profile_id=normalized_profile_id,
        reason=entry.reason,
        now=now,
    )
    return {
        "status": "ok",
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "lemma": normalized_lemma,
        "reason": entry.reason,
        "active_reason": active_reason,
        "created_at": entry.created_at,
        "suppressed_until": entry.suppressed_until,
        "suppression_store_path": str(suppression_path),
        "suppression_store_mutation": True,
        "runtime_srs_mutation": srs_store_mutation,
        "srs_store_lifecycle_mutation": srs_store_mutation,
        "active_item_removed": removed_active_item,
        "refresh_admission_blocked": active_reason is not None,
        "active_suppressed_lemma_count": len(active),
    }


def _mark_existing_item_discarded(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    profile_id: str,
    reason: str,
    now: Optional[datetime],
) -> tuple[bool, bool]:
    store_path = paths.srs_store_path_for(profile_id)
    if not store_path.exists():
        return False, False

    store = load_srs_store(store_path)
    updated_store, updated_item = mark_item_lifecycle(
        store,
        language_pair=pair,
        lemma=lemma,
        lifecycle_state=SRS_LIFECYCLE_DISCARDED,
        reason=reason,
        now=now,
    )
    if updated_item is None:
        return False, False

    save_srs_store(updated_store, store_path)
    removed_active_item = _remove_item_from_active_inventory(
        paths,
        pair=pair,
        profile_id=profile_id,
        item_id=updated_item.item_id,
    )
    return True, removed_active_item


def _remove_item_from_active_inventory(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    item_id: str,
) -> bool:
    normalized_item_id = str(item_id or "").strip()
    if not normalized_item_id:
        return False
    inventory_path = paths.srs_inventory_path_for(profile_id)
    if not inventory_path.exists():
        return False
    inventory = load_srs_inventory(inventory_path)
    active_ids = active_item_ids_for_pair(inventory, pair)
    if normalized_item_id not in active_ids:
        return False
    updated_ids = tuple(existing for existing in active_ids if existing != normalized_item_id)
    updated_inventory = set_active_item_ids(
        inventory,
        pair=pair,
        active_item_ids=updated_ids,
    )
    save_srs_inventory(updated_inventory, inventory_path)
    return True
