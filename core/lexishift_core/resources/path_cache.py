from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping, Optional, TypeVar


T = TypeVar("T")

_PATH_CACHE_VERSION = 1


def load_or_compute_path_json_value(
    path: Path,
    *,
    namespace: str,
    key: Mapping[str, object],
    compute: Callable[[], T],
    serialize: Callable[[T], object],
    deserialize: Callable[[object], T],
) -> T:
    if not path.exists() or not path.is_file():
        return compute()
    signature = _path_signature(path)
    if signature is None:
        return compute()
    cache_path = _build_cache_path(path, namespace=namespace, key=key)
    cached_payload = _read_cache_payload(cache_path=cache_path)
    if _cache_payload_matches(cached_payload, path=path, signature=signature, key=key):
        try:
            return deserialize(cached_payload.get("value"))
        except (TypeError, ValueError):
            pass
    value = compute()
    _write_cache_payload(
        cache_path=cache_path,
        path=path,
        signature=signature,
        key=key,
        value=serialize(value),
    )
    return value


def _path_signature(path: Path) -> Optional[tuple[int, int]]:
    try:
        stat = path.stat()
    except OSError:
        return None
    return int(stat.st_size), int(stat.st_mtime_ns)


def _build_cache_path(path: Path, *, namespace: str, key: Mapping[str, object]) -> Path:
    normalized_key = _normalize_key(key)
    cache_root = path.parent / ".lexishift_cache" / str(namespace or "default").strip()
    payload = json.dumps(
        {
            "path": str(path.expanduser().resolve(strict=False)),
            "key": normalized_key,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return cache_root / f"{digest}.json"


def _normalize_key(key: Mapping[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    normalized_items = sorted(
        ((str(name or "").strip(), value) for name, value in key.items()),
        key=lambda item: item[0],
    )
    for raw_name, raw_value in normalized_items:
        if not raw_name or raw_name in normalized:
            continue
        normalized[raw_name] = _normalize_key_value(raw_value)
    return normalized


def _normalize_key_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value.expanduser().resolve(strict=False))
    if isinstance(value, Mapping):
        return _normalize_key(value)
    if isinstance(value, (set, frozenset)):
        return sorted(_normalize_key_value(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_normalize_key_value(item) for item in value]
    return str(value)


def _read_cache_payload(*, cache_path: Path) -> Optional[dict[str, object]]:
    if not cache_path.exists() or not cache_path.is_file():
        return None
    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _cache_payload_matches(
    payload: Optional[Mapping[str, object]],
    *,
    path: Path,
    signature: tuple[int, int],
    key: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if int(payload.get("cache_version") or -1) != _PATH_CACHE_VERSION:
        return False
    cached_path = str(payload.get("path") or "").strip()
    expected_path = str(path.expanduser().resolve(strict=False))
    if cached_path != expected_path:
        return False
    cached_size = int(payload.get("size") or -1)
    cached_mtime_ns = int(payload.get("mtime_ns") or -1)
    if (cached_size, cached_mtime_ns) != signature:
        return False
    cached_key = payload.get("key")
    return cached_key == _normalize_key(key)


def _write_cache_payload(
    *,
    cache_path: Path,
    path: Path,
    signature: tuple[int, int],
    key: Mapping[str, object],
    value: object,
) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cache_version": _PATH_CACHE_VERSION,
            "path": str(path.expanduser().resolve(strict=False)),
            "size": int(signature[0]),
            "mtime_ns": int(signature[1]),
            "key": _normalize_key(key),
            "value": value,
        }
        temp_path = cache_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        temp_path.replace(cache_path)
    except OSError:
        return
