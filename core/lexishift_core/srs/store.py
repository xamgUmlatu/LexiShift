from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from lexishift_core.lexicon.word_package import (
    normalize_word_package,
    resolve_language_tag_from_pair,
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
    pair_rules: Mapping[str, SrsPairSettings] = field(default_factory=dict)
    sync: Optional[SrsSync] = None
    version: int = 1


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
    next_due: Optional[str] = None
    exposures: int = 0
    history: Sequence[SrsHistoryEntry] = field(default_factory=tuple)
    word_package: Optional[Mapping[str, object]] = None


@dataclass(frozen=True)
class SrsStore:
    items: Sequence[SrsItem] = field(default_factory=tuple)
    version: int = 1


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
        pair_rules=pair_rules,
        sync=sync,
        version=int(data.get("version", 1)),
    )


def srs_settings_to_dict(settings: SrsSettings) -> dict[str, Any]:
    data: dict[str, Any] = {
        "version": settings.version,
        "enabled": settings.enabled,
        "coverage_scalar": settings.coverage_scalar,
        "max_active_items": settings.max_active_items,
        "max_new_items_per_day": settings.max_new_items_per_day,
        "feedback_scale": settings.feedback_scale,
        "pair_rules": {
            key: {"enabled": value.enabled} for key, value in dict(settings.pair_rules or {}).items()
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
                next_due=item.get("next_due"),
                exposures=int(item.get("exposures", 0)),
                history=history,
                word_package=word_package,
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
            "next_due": item.next_due,
            "exposures": item.exposures,
            "srs_history": [
                {"ts": entry.ts, "rating": entry.rating} for entry in item.history
            ],
            "word_package": word_package,
        }
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
