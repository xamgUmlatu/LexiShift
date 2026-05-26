from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from lexishift_core.lexicon.word_package import (
    normalize_word_package,
    resolve_language_tag_from_pair,
)

SRS_LIFECYCLE_ACTIVE = "active"
SRS_LIFECYCLE_DISCARDED = "discarded"
SRS_LIFECYCLE_CLEARED = "cleared"
SRS_LIFECYCLE_STATES = frozenset(
    {
        SRS_LIFECYCLE_ACTIVE,
        SRS_LIFECYCLE_DISCARDED,
        SRS_LIFECYCLE_CLEARED,
    }
)


@dataclass(frozen=True)
class SrsSync:
    export_last_at: Optional[str] = None
    import_last_at: Optional[str] = None


@dataclass(frozen=True)
class SrsPairSettings:
    enabled: bool = True


@dataclass(frozen=True)
class SrsSettings:
    enabled: bool = True
    coverage_scalar: float = 0.35
    max_active_items: int = 40
    max_new_items_per_day: int = 8
    feedback_scale: str = "again_hard_good_easy"
    scheduler: "SrsSchedulerSettings" = field(default_factory=lambda: SrsSchedulerSettings())
    pair_rules: Mapping[str, SrsPairSettings] = field(default_factory=dict)
    sync: Optional[SrsSync] = None
    version: int = 2


@dataclass(frozen=True)
class SrsSchedulerSettings:
    algorithm: str = "fsrs"
    desired_retention: float = 0.9
    learning_steps_minutes: Sequence[int] = field(default_factory=lambda: (1, 10))
    relearning_steps_minutes: Sequence[int] = field(default_factory=lambda: (10,))
    maximum_interval_days: int = 36500
    enable_fuzzing: bool = False
    parameters: Optional[Sequence[float]] = None


@dataclass(frozen=True)
class SrsHistoryEntry:
    ts: str
    rating: str


@dataclass(frozen=True)
class SrsItem:
    item_id: str
    lemma: str
    language_pair: str
    source_type: str
    confidence: Optional[float] = None
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    last_seen: Optional[str] = None
    last_review: Optional[str] = None
    next_due: Optional[str] = None
    scheduler_state: Optional[str] = None
    scheduler_step: Optional[int] = None
    exposures: int = 0
    history: Sequence[SrsHistoryEntry] = field(default_factory=tuple)
    word_package: Optional[Mapping[str, object]] = None
    lifecycle_state: str = SRS_LIFECYCLE_ACTIVE
    lifecycle_reason: Optional[str] = None
    lifecycle_updated_at: Optional[str] = None


@dataclass(frozen=True)
class SrsStore:
    items: Sequence[SrsItem] = field(default_factory=tuple)
    version: int = 2


@dataclass(frozen=True)
class PracticeGateState:
    active_pairs: Sequence[str] = field(default_factory=tuple)
    active_items: Sequence[str] = field(default_factory=tuple)
    generated_at: Optional[str] = None


def srs_settings_from_dict(data: Mapping[str, Any]) -> SrsSettings:
    pair_rules = {
        key: SrsPairSettings(enabled=bool(value.get("enabled", True)))
        for key, value in dict(data.get("pair_rules", {})).items()
        if isinstance(value, Mapping)
    }
    scheduler_data = data.get("scheduler") or {}
    scheduler = SrsSchedulerSettings(
        algorithm=str(scheduler_data.get("algorithm", "fsrs") or "fsrs"),
        desired_retention=float(scheduler_data.get("desired_retention", 0.9)),
        learning_steps_minutes=_coerce_int_sequence(
            scheduler_data.get("learning_steps_minutes"),
            default=(1, 10),
        ),
        relearning_steps_minutes=_coerce_int_sequence(
            scheduler_data.get("relearning_steps_minutes"),
            default=(10,),
        ),
        maximum_interval_days=int(scheduler_data.get("maximum_interval_days", 36500)),
        enable_fuzzing=bool(scheduler_data.get("enable_fuzzing", False)),
        parameters=_coerce_optional_float_sequence(scheduler_data.get("parameters")),
    )
    sync_data = data.get("sync") or {}
    sync = None
    if sync_data:
        sync = SrsSync(
            export_last_at=sync_data.get("export_last_at"),
            import_last_at=sync_data.get("import_last_at"),
        )
    return SrsSettings(
        enabled=bool(data.get("enabled", True)),
        coverage_scalar=float(data.get("coverage_scalar", 0.35)),
        max_active_items=int(data.get("max_active_items", 40)),
        max_new_items_per_day=int(data.get("max_new_items_per_day", 8)),
        feedback_scale=str(data.get("feedback_scale", "again_hard_good_easy")),
        scheduler=scheduler,
        pair_rules=pair_rules,
        sync=sync,
        version=int(data.get("version", 2)),
    )


def srs_settings_to_dict(settings: SrsSettings) -> dict[str, Any]:
    data: dict[str, Any] = {
        "version": settings.version,
        "enabled": settings.enabled,
        "coverage_scalar": settings.coverage_scalar,
        "max_active_items": settings.max_active_items,
        "max_new_items_per_day": settings.max_new_items_per_day,
        "feedback_scale": settings.feedback_scale,
        "scheduler": {
            "algorithm": settings.scheduler.algorithm,
            "desired_retention": settings.scheduler.desired_retention,
            "learning_steps_minutes": [
                int(value) for value in settings.scheduler.learning_steps_minutes
            ],
            "relearning_steps_minutes": [
                int(value) for value in settings.scheduler.relearning_steps_minutes
            ],
            "maximum_interval_days": settings.scheduler.maximum_interval_days,
            "enable_fuzzing": settings.scheduler.enable_fuzzing,
            "parameters": (
                [float(value) for value in settings.scheduler.parameters]
                if settings.scheduler.parameters
                else None
            ),
        },
        "pair_rules": {
            key: {"enabled": value.enabled}
            for key, value in dict(settings.pair_rules or {}).items()
        },
    }
    if settings.sync:
        data["sync"] = {
            "export_last_at": settings.sync.export_last_at,
            "import_last_at": settings.sync.import_last_at,
        }
    trimmed = {key: value for key, value in data.items() if value not in (None, {}, [])}
    return trimmed


def srs_store_from_dict(data: Mapping[str, Any]) -> SrsStore:
    items = []
    for item in data.get("items", []):
        if not isinstance(item, Mapping):
            continue
        lemma = str(item.get("lemma", ""))
        language_pair = str(item.get("language_pair", ""))
        source_type = str(item.get("source_type", ""))
        word_package = normalize_word_package(
            item.get("word_package"),
            fallback_surface=lemma,
            fallback_language_tag=resolve_language_tag_from_pair(language_pair),
            fallback_provider=source_type or "srs",
        )
        history = tuple(
            SrsHistoryEntry(ts=str(entry.get("ts", "")), rating=str(entry.get("rating", "")))
            for entry in item.get("srs_history", [])
            if isinstance(entry, Mapping)
        )
        items.append(
            SrsItem(
                item_id=str(item.get("item_id", "")),
                lemma=lemma,
                language_pair=language_pair,
                source_type=source_type,
                confidence=item.get("confidence"),
                stability=item.get("stability"),
                difficulty=item.get("difficulty"),
                last_seen=item.get("last_seen"),
                last_review=item.get("last_review"),
                next_due=item.get("next_due"),
                scheduler_state=item.get("scheduler_state"),
                scheduler_step=item.get("scheduler_step"),
                exposures=int(item.get("exposures", 0)),
                history=history,
                word_package=word_package,
                lifecycle_state=normalize_srs_lifecycle_state(item.get("lifecycle_state")),
                lifecycle_reason=_normalize_optional_string(item.get("lifecycle_reason")),
                lifecycle_updated_at=_normalize_optional_string(item.get("lifecycle_updated_at")),
            )
        )
    return SrsStore(items=tuple(items), version=int(data.get("version", 1)))


def srs_store_to_dict(store: SrsStore) -> dict[str, Any]:
    items = []
    for item in store.items:
        word_package = normalize_word_package(
            item.word_package,
            fallback_surface=item.lemma,
            fallback_language_tag=resolve_language_tag_from_pair(item.language_pair),
            fallback_provider=item.source_type or "srs",
        )
        record: dict[str, Any] = {
            "item_id": item.item_id,
            "lemma": item.lemma,
            "language_pair": item.language_pair,
            "source_type": item.source_type,
            "confidence": item.confidence,
            "stability": item.stability,
            "difficulty": item.difficulty,
            "last_seen": item.last_seen,
            "last_review": item.last_review,
            "next_due": item.next_due,
            "scheduler_state": item.scheduler_state,
            "scheduler_step": item.scheduler_step,
            "exposures": item.exposures,
            "srs_history": [{"ts": entry.ts, "rating": entry.rating} for entry in item.history],
            "word_package": word_package,
        }
        lifecycle_state = normalize_srs_lifecycle_state(item.lifecycle_state)
        if lifecycle_state != SRS_LIFECYCLE_ACTIVE:
            record["lifecycle_state"] = lifecycle_state
            record["lifecycle_reason"] = item.lifecycle_reason
            record["lifecycle_updated_at"] = item.lifecycle_updated_at
        trimmed = {key: value for key, value in record.items() if value not in (None, [], "")}
        items.append(trimmed)
    return {"version": store.version, "items": items}


def load_srs_settings(path: str | Path) -> SrsSettings:
    payload = Path(path).read_text(encoding="utf-8")
    return srs_settings_from_dict(json.loads(payload))


def save_srs_settings(settings: SrsSettings, path: str | Path) -> None:
    payload = json.dumps(srs_settings_to_dict(settings), indent=2, sort_keys=True)
    Path(path).write_text(payload, encoding="utf-8")


def load_srs_store(path: str | Path) -> SrsStore:
    payload = Path(path).read_text(encoding="utf-8")
    return srs_store_from_dict(json.loads(payload))


def save_srs_store(store: SrsStore, path: str | Path) -> None:
    payload = json.dumps(srs_store_to_dict(store), indent=2, sort_keys=True)
    Path(path).write_text(payload, encoding="utf-8")


def srs_bundle_to_dict(settings: SrsSettings, store: SrsStore) -> dict[str, Any]:
    return {
        "settings": srs_settings_to_dict(settings),
        "items": srs_store_to_dict(store),
    }


def srs_bundle_from_dict(data: Mapping[str, Any]) -> tuple[SrsSettings, SrsStore]:
    settings = srs_settings_from_dict(data.get("settings", {}))
    store = srs_store_from_dict(data.get("items", {}))
    return settings, store


def normalize_srs_lifecycle_state(value: object) -> str:
    state = str(value or "").strip().lower()
    if state in SRS_LIFECYCLE_STATES:
        return state
    return SRS_LIFECYCLE_ACTIVE


def srs_item_is_active(item: SrsItem) -> bool:
    return normalize_srs_lifecycle_state(item.lifecycle_state) == SRS_LIFECYCLE_ACTIVE


def _coerce_int_sequence(value: object, *, default: Sequence[int]) -> tuple[int, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return tuple(int(item) for item in default)
    result = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return tuple(result) or tuple(int(item) for item in default)


def _coerce_optional_float_sequence(value: object) -> Optional[tuple[float, ...]]:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    result = []
    for item in value:
        try:
            result.append(float(item))
        except (TypeError, ValueError):
            continue
    return tuple(result) or None


def _normalize_optional_string(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
