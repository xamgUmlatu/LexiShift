from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from lexishift_core.helper.use_cases.seed_cache import (
    get_srs_seed_frontier_cache_status,
    prepare_srs_seed_frontier_cache,
    prepare_srs_seed_frontier_caches_for_pack,
)


def handle_srs_seed_cache_request(paths, msg_type: str, payload: Dict[str, Any]) -> dict:
    if msg_type == "srs_seed_cache_status":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        return get_srs_seed_frontier_cache_status(
            paths,
            pair=pair,
            set_source_db=_optional_path(payload, "frequency_pack_path")
            or _optional_path(payload, "set_source_db"),
            jmdict_path=_optional_path(payload, "jmdict_path"),
        )
    pack_id = str(payload.get("pack_id", "") or "").strip()
    cleanup = _optional_bool(payload, "cleanup")
    if cleanup is None:
        cleanup = True
    if pack_id:
        return prepare_srs_seed_frontier_caches_for_pack(
            paths,
            pack_id=pack_id,
            cleanup=cleanup,
        )
    pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
    return prepare_srs_seed_frontier_cache(
        paths,
        pair=pair,
        set_source_db=_optional_path(payload, "frequency_pack_path")
        or _optional_path(payload, "set_source_db"),
        jmdict_path=_optional_path(payload, "jmdict_path"),
        cleanup=cleanup,
    )


def _optional_path(payload: Dict[str, Any], key: str) -> Path | None:
    value = str(payload.get(key, "")).strip()
    return Path(value) if value else None


def _optional_bool(payload: Dict[str, Any], key: str) -> bool | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None
