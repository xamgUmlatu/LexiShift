from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Mapping
import urllib.request

from language_packs_catalog import PackTransportOverride
from main_paths import _app_data_dir

PACK_SOURCE_MANIFEST_SCHEMA_VERSION = 1
PACK_SOURCE_MANIFEST_CACHE_VERSION = 1
DEFAULT_PACK_SOURCE_MANIFEST_TTL_HOURS = 24
DEFAULT_PACK_SOURCE_MANIFEST_URL = (
    "https://xamgUmlatu.github.io/LexiShift/pack_source_manifest.json"
)
PACK_SOURCE_MANIFEST_CACHE_FILENAME = "pack_source_manifest_cache.json"


class PackSourceManifestValidationError(ValueError):
    pass


@dataclass(frozen=True)
class PackSourceManifestSnapshot:
    source_url: str
    fetched_at: datetime
    ttl_hours: int
    overrides: dict[str, PackTransportOverride]
    generated_at: datetime | None = None

    def is_fresh(self, *, now: datetime | None = None) -> bool:
        current = _utc_now() if now is None else _ensure_utc(now)
        return current <= self.fetched_at + timedelta(hours=self.ttl_hours)


def default_pack_source_manifest_url() -> str:
    override = str(os.getenv("LEXISHIFT_PACK_SOURCE_MANIFEST_URL") or "").strip()
    return override or DEFAULT_PACK_SOURCE_MANIFEST_URL


def pack_source_manifest_cache_path(*, app_data_dir: Path | None = None) -> Path:
    base_dir = _app_data_dir() if app_data_dir is None else Path(app_data_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / PACK_SOURCE_MANIFEST_CACHE_FILENAME


def load_pack_source_manifest_cache(
    *, cache_path: Path | None = None
) -> PackSourceManifestSnapshot | None:
    target = pack_source_manifest_cache_path() if cache_path is None else Path(cache_path)
    if not target.exists() or not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    cache_version = _coerce_positive_int(payload.get("cache_version"), field_name="cache_version")
    if cache_version != PACK_SOURCE_MANIFEST_CACHE_VERSION:
        return None
    fetched_at = _parse_utc_datetime(payload.get("fetched_at"), field_name="fetched_at")
    if fetched_at is None:
        return None
    source_url = str(payload.get("source_url") or "").strip() or default_pack_source_manifest_url()
    raw_manifest = payload.get("manifest")
    if not isinstance(raw_manifest, dict):
        return None
    try:
        return pack_source_manifest_snapshot_from_payload(
            raw_manifest,
            source_url=source_url,
            fetched_at=fetched_at,
        )
    except PackSourceManifestValidationError:
        return None


def write_pack_source_manifest_cache(
    snapshot: PackSourceManifestSnapshot,
    *,
    cache_path: Path | None = None,
) -> Path:
    target = pack_source_manifest_cache_path() if cache_path is None else Path(cache_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cache_version": PACK_SOURCE_MANIFEST_CACHE_VERSION,
        "source_url": snapshot.source_url,
        "fetched_at": _format_utc_datetime(snapshot.fetched_at),
        "manifest": {
            "schema_version": PACK_SOURCE_MANIFEST_SCHEMA_VERSION,
            "generated_at": _format_utc_datetime(snapshot.generated_at),
            "ttl_hours": snapshot.ttl_hours,
            "packs": {
                pack_id: _pack_transport_override_to_dict(override)
                for pack_id, override in sorted(snapshot.overrides.items())
            },
        },
    }
    temp_path = target.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(target)
    return target


def fetch_pack_source_manifest(
    *,
    manifest_url: str | None = None,
    timeout_seconds: float = 5.0,
    now: datetime | None = None,
) -> PackSourceManifestSnapshot:
    source_url = str(manifest_url or default_pack_source_manifest_url()).strip()
    if not source_url:
        raise PackSourceManifestValidationError("Pack source manifest URL is empty.")
    request = urllib.request.Request(
        source_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "LexiShift/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        try:
            payload = json.loads(response.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PackSourceManifestValidationError(
                "Pack source manifest response is not valid UTF-8 JSON."
            ) from exc
    if not isinstance(payload, dict):
        raise PackSourceManifestValidationError("Pack source manifest payload must be an object.")
    fetched_at = _utc_now() if now is None else _ensure_utc(now)
    return pack_source_manifest_snapshot_from_payload(
        payload,
        source_url=source_url,
        fetched_at=fetched_at,
    )


def resolve_pack_source_manifest(
    *,
    manifest_url: str | None = None,
    cache_path: Path | None = None,
    refresh_remote: bool = True,
    timeout_seconds: float = 5.0,
    now: datetime | None = None,
) -> PackSourceManifestSnapshot | None:
    current_time = _utc_now() if now is None else _ensure_utc(now)
    resolved_url = str(manifest_url or default_pack_source_manifest_url()).strip()
    cached = load_pack_source_manifest_cache(cache_path=cache_path)
    cache_matches_url = cached is not None and cached.source_url == resolved_url
    if cache_matches_url and cached.is_fresh(now=current_time):
        return cached
    if not refresh_remote or not resolved_url:
        return cached
    try:
        snapshot = fetch_pack_source_manifest(
            manifest_url=resolved_url,
            timeout_seconds=timeout_seconds,
            now=current_time,
        )
    except Exception:
        return cached
    write_pack_source_manifest_cache(snapshot, cache_path=cache_path)
    return snapshot


def load_pack_source_overrides(
    *,
    manifest_url: str | None = None,
    cache_path: Path | None = None,
    refresh_remote: bool = True,
    timeout_seconds: float = 5.0,
    now: datetime | None = None,
) -> dict[str, PackTransportOverride]:
    snapshot = resolve_pack_source_manifest(
        manifest_url=manifest_url,
        cache_path=cache_path,
        refresh_remote=refresh_remote,
        timeout_seconds=timeout_seconds,
        now=now,
    )
    if snapshot is None:
        return {}
    return dict(snapshot.overrides)


def pack_source_manifest_snapshot_from_payload(
    payload: Mapping[str, object],
    *,
    source_url: str,
    fetched_at: datetime,
) -> PackSourceManifestSnapshot:
    schema_version = _coerce_positive_int(
        payload.get("schema_version"), field_name="schema_version"
    )
    if schema_version != PACK_SOURCE_MANIFEST_SCHEMA_VERSION:
        raise PackSourceManifestValidationError(
            f"Unsupported pack source manifest schema_version: {payload.get('schema_version')!r}"
        )
    raw_ttl_hours = _coerce_positive_int(
        payload.get("ttl_hours", DEFAULT_PACK_SOURCE_MANIFEST_TTL_HOURS),
        field_name="ttl_hours",
    )
    generated_at = _parse_utc_datetime(payload.get("generated_at"), field_name="generated_at")
    raw_packs = payload.get("packs", {})
    if raw_packs is None:
        raw_packs = {}
    if not isinstance(raw_packs, Mapping):
        raise PackSourceManifestValidationError("packs must be an object keyed by pack_id.")
    overrides: dict[str, PackTransportOverride] = {}
    for raw_pack_id, raw_entry in raw_packs.items():
        pack_id = str(raw_pack_id or "").strip()
        if not pack_id:
            raise PackSourceManifestValidationError(
                "Pack source manifest contains a blank pack_id."
            )
        if not isinstance(raw_entry, Mapping):
            raise PackSourceManifestValidationError(f"Pack entry '{pack_id}' must be an object.")
        override = PackTransportOverride(
            url=_coerce_optional_manifest_string(raw_entry.get("url"), field_name="url"),
            wayback_url=_coerce_optional_manifest_string(
                raw_entry.get("wayback_url"),
                field_name="wayback_url",
            ),
            filename=_coerce_optional_manifest_string(
                raw_entry.get("filename"),
                field_name="filename",
            ),
        )
        if override.url is None and override.wayback_url is None and override.filename is None:
            continue
        overrides[pack_id] = override
    return PackSourceManifestSnapshot(
        source_url=source_url,
        fetched_at=_ensure_utc(fetched_at),
        ttl_hours=raw_ttl_hours,
        overrides=overrides,
        generated_at=generated_at,
    )


def _coerce_optional_manifest_string(raw: object, *, field_name: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise PackSourceManifestValidationError(f"{field_name} must be a string when present.")
    normalized = raw.strip()
    return normalized or None


def _coerce_positive_int(raw: object, *, field_name: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise PackSourceManifestValidationError(
            f"{field_name} must be a positive integer."
        ) from exc
    if value <= 0:
        raise PackSourceManifestValidationError(f"{field_name} must be a positive integer.")
    return value


def _pack_transport_override_to_dict(override: PackTransportOverride) -> dict[str, str]:
    payload: dict[str, str] = {}
    if override.url is not None:
        payload["url"] = override.url
    if override.wayback_url is not None:
        payload["wayback_url"] = override.wayback_url
    if override.filename is not None:
        payload["filename"] = override.filename
    return payload


def _parse_utc_datetime(raw: object, *, field_name: str) -> datetime | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise PackSourceManifestValidationError(f"{field_name} must be an ISO-8601 string.")
    text = raw.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PackSourceManifestValidationError(
            f"{field_name} must be an ISO-8601 UTC timestamp."
        ) from exc
    return _ensure_utc(parsed)


def _format_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = _ensure_utc(value).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
