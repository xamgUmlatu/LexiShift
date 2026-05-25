from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs.admission_suppression import (
    SrsAdmissionSuppressionPolicy,
    active_suppressed_lemmas,
    create_admission_suppression,
    load_admission_suppression_store,
    prune_expired_suppression_entries,
    save_admission_suppression_store,
    upsert_admission_suppression,
)


def suppress_srs_admission(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    reason: str = "manual_cooldown",
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
        "runtime_srs_mutation": False,
        "refresh_admission_blocked": active_reason is not None,
        "active_suppressed_lemma_count": len(active),
    }
