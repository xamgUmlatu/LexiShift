from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.time import format_ts, now_utc, parse_ts

SUPPRESSION_REASON_DISCARDED = "discarded"
SUPPRESSION_REASON_SUSPENDED = "suspended"
SUPPRESSION_REASON_USER_BLOCKED = "user_blocked"
SUPPRESSION_REASON_MANUAL_COOLDOWN = "manual_cooldown"

SUPPRESSION_REASONS = frozenset(
    {
        SUPPRESSION_REASON_DISCARDED,
        SUPPRESSION_REASON_SUSPENDED,
        SUPPRESSION_REASON_USER_BLOCKED,
        SUPPRESSION_REASON_MANUAL_COOLDOWN,
    }
)


@dataclass(frozen=True)
class SrsAdmissionSuppressionPolicy:
    version: str = "srs_admission_suppression_v1"
    discarded_cooldown_days: int = 90
    suspended_cooldown_days: int = 365
    manual_cooldown_days: int = 30


@dataclass(frozen=True)
class SrsAdmissionSuppressionEntry:
    pair: str
    lemma: str
    reason: str
    created_at: str
    suppressed_until: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "pair": self.pair,
            "lemma": self.lemma,
            "reason": self.reason,
            "created_at": self.created_at,
        }
        if self.suppressed_until:
            payload["suppressed_until"] = self.suppressed_until
        if self.note:
            payload["note"] = self.note
        return payload


@dataclass(frozen=True)
class SrsAdmissionSuppressionStore:
    profile_id: str = "default"
    entries: Sequence[SrsAdmissionSuppressionEntry] = field(default_factory=tuple)
    version: int = 1
    policy_version: str = "srs_admission_suppression_v1"
    updated_at: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "profile_id": self.profile_id,
            "policy_version": self.policy_version,
            "updated_at": self.updated_at,
            "entries": [entry.to_dict() for entry in self.entries],
        }


def create_admission_suppression(
    *,
    pair: str,
    lemma: str,
    reason: str,
    policy: Optional[SrsAdmissionSuppressionPolicy] = None,
    now: Optional[datetime] = None,
    note: Optional[str] = None,
) -> SrsAdmissionSuppressionEntry:
    policy = policy or SrsAdmissionSuppressionPolicy()
    now = now or now_utc()
    normalized_reason = normalize_suppression_reason(reason)
    cooldown_days = _cooldown_days_for_reason(normalized_reason, policy=policy)
    suppressed_until = None
    if cooldown_days is not None:
        suppressed_until = format_ts(now + timedelta(days=cooldown_days))
    return SrsAdmissionSuppressionEntry(
        pair=str(pair or "").strip(),
        lemma=str(lemma or "").strip(),
        reason=normalized_reason,
        created_at=format_ts(now),
        suppressed_until=suppressed_until,
        note=str(note or "").strip() or None,
    )


def upsert_admission_suppression(
    store: SrsAdmissionSuppressionStore,
    entry: SrsAdmissionSuppressionEntry,
    *,
    now: Optional[datetime] = None,
) -> SrsAdmissionSuppressionStore:
    now = now or now_utc()
    key = _entry_key(entry)
    entries = [existing for existing in store.entries if _entry_key(existing) != key]
    entries.append(entry)
    entries.sort(key=lambda item: (item.pair, item.lemma, item.reason))
    return SrsAdmissionSuppressionStore(
        profile_id=store.profile_id,
        entries=tuple(entries),
        version=store.version,
        policy_version=store.policy_version,
        updated_at=format_ts(now),
    )


def active_suppressed_lemmas(
    store: SrsAdmissionSuppressionStore,
    *,
    pair: str,
    now: Optional[datetime] = None,
) -> dict[str, str]:
    now = now or now_utc()
    normalized_pair = str(pair or "").strip()
    result: dict[str, str] = {}
    for entry in store.entries:
        if entry.pair != normalized_pair or not entry.lemma:
            continue
        until = parse_ts(entry.suppressed_until)
        if until is not None and until <= now:
            continue
        result[entry.lemma] = entry.reason
    return result


def prune_expired_suppression_entries(
    store: SrsAdmissionSuppressionStore,
    *,
    now: Optional[datetime] = None,
) -> SrsAdmissionSuppressionStore:
    now = now or now_utc()
    retained: list[SrsAdmissionSuppressionEntry] = []
    for entry in store.entries:
        until = parse_ts(entry.suppressed_until)
        if until is not None and until <= now:
            continue
        retained.append(entry)
    return SrsAdmissionSuppressionStore(
        profile_id=store.profile_id,
        entries=tuple(retained),
        version=store.version,
        policy_version=store.policy_version,
        updated_at=format_ts(now),
    )


def admission_suppression_store_from_dict(
    data: Mapping[str, object],
) -> SrsAdmissionSuppressionStore:
    raw_entries = data.get("entries")
    entries: list[SrsAdmissionSuppressionEntry] = []
    if isinstance(raw_entries, list):
        for value in raw_entries:
            if not isinstance(value, Mapping):
                continue
            entry = admission_suppression_entry_from_dict(value)
            if entry.pair and entry.lemma:
                entries.append(entry)
    return SrsAdmissionSuppressionStore(
        profile_id=str(data.get("profile_id", "") or "default"),
        entries=tuple(entries),
        version=max(1, int(_safe_float(data.get("version")) or 1)),
        policy_version=str(data.get("policy_version", "") or "srs_admission_suppression_v1"),
        updated_at=_optional_str(data.get("updated_at")),
    )


def admission_suppression_entry_from_dict(
    data: Mapping[str, object],
) -> SrsAdmissionSuppressionEntry:
    return SrsAdmissionSuppressionEntry(
        pair=str(data.get("pair", "") or "").strip(),
        lemma=str(data.get("lemma", "") or "").strip(),
        reason=normalize_suppression_reason(data.get("reason")),
        created_at=str(data.get("created_at", "") or "").strip(),
        suppressed_until=_optional_str(data.get("suppressed_until")),
        note=_optional_str(data.get("note")),
    )


def load_admission_suppression_store(path: Path) -> SrsAdmissionSuppressionStore:
    if not path.exists():
        return SrsAdmissionSuppressionStore()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return SrsAdmissionSuppressionStore()
    if not isinstance(payload, Mapping):
        return SrsAdmissionSuppressionStore()
    return admission_suppression_store_from_dict(payload)


def save_admission_suppression_store(
    store: SrsAdmissionSuppressionStore,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(store.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalize_suppression_reason(value: object) -> str:
    reason = str(value or "").strip().lower()
    if reason in SUPPRESSION_REASONS:
        return reason
    return SUPPRESSION_REASON_MANUAL_COOLDOWN


def _cooldown_days_for_reason(
    reason: str,
    *,
    policy: SrsAdmissionSuppressionPolicy,
) -> Optional[int]:
    if reason == SUPPRESSION_REASON_DISCARDED:
        return max(0, int(policy.discarded_cooldown_days))
    if reason == SUPPRESSION_REASON_SUSPENDED:
        return max(0, int(policy.suspended_cooldown_days))
    if reason == SUPPRESSION_REASON_MANUAL_COOLDOWN:
        return max(0, int(policy.manual_cooldown_days))
    if reason == SUPPRESSION_REASON_USER_BLOCKED:
        return None
    return max(0, int(policy.manual_cooldown_days))


def _entry_key(entry: SrsAdmissionSuppressionEntry) -> tuple[str, str, str]:
    return (entry.pair, entry.lemma, entry.reason)


def _optional_str(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None
