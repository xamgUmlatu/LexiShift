#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _inject_core_path() -> None:
    candidates = [
        SCRIPT_DIR / "lexishift_core",
        SCRIPT_DIR.parent / "lexishift_core",
        SCRIPT_DIR.parent / "core" / "lexishift_core",
        PROJECT_ROOT / "core" / "lexishift_core",
    ]
    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate.parent))
            return


_inject_core_path()

from lexishift_core.helper_engine import (
    get_srs_runtime_diagnostics,
    RulegenJobConfig,
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    SetPlanningJobConfig,
    apply_exposure,
    apply_feedback,
    initialize_srs_set,
    load_ruleset,
    load_snapshot,
    plan_srs_set,
    refresh_srs_set,
    reset_srs_data,
    run_rulegen_job,
)
from lexishift_core.helper_profiles import get_profiles_snapshot
from lexishift_core.helper_os import open_path
from lexishift_core.helper_paths import build_helper_paths
from lexishift_core.helper_status import load_status
from lexishift_core.lp_capabilities import (
    default_freedict_de_en_path,
    default_frequency_db_path,
    default_jmdict_path,
)


PROTOCOL_VERSION = 1
HELPER_VERSION = "0.1.0"


def _read_message() -> Optional[dict]:
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    if len(raw_length) != 4:
        raise ValueError("Invalid message length header.")
    message_length = struct.unpack("<I", raw_length)[0]
    if message_length <= 0:
        return None
    raw_message = sys.stdin.buffer.read(message_length)
    if len(raw_message) != message_length:
        raise ValueError("Incomplete message payload.")
    return json.loads(raw_message.decode("utf-8"))


def _write_message(payload: dict) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def _error_response(request_id: str, message: str, code: str = "invalid_request") -> dict:
    return {"id": request_id, "ok": False, "data": None, "error": {"code": code, "message": message}}


def _optional_int(payload: Dict[str, Any], key: str) -> Optional[int]:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_profile_id(payload: Dict[str, Any]) -> Optional[str]:
    profile_id = str(payload.get("profile_id", "")).strip()
    return profile_id or None


def _optional_path(payload: Dict[str, Any], key: str) -> Optional[Path]:
    value = str(payload.get(key, "")).strip()
    return Path(value) if value else None


def _resolve_pair_resource_paths(
    paths,
    *,
    pair: str,
    payload: Dict[str, Any],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    jmdict_path = _optional_path(payload, "jmdict_path")
    if jmdict_path is None:
        jmdict_path = default_jmdict_path(pair, language_packs_dir=paths.language_packs_dir)
    freedict_de_en_path = _optional_path(payload, "freedict_de_en_path")
    if freedict_de_en_path is None:
        freedict_de_en_path = default_freedict_de_en_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    set_source_db = _optional_path(payload, "set_source_db")
    if set_source_db is None:
        set_source_db = default_frequency_db_path(
            pair,
            frequency_packs_dir=paths.frequency_packs_dir,
        )
    return jmdict_path, freedict_de_en_path, set_source_db


def _validate_request(request: Dict[str, Any]) -> tuple[str, str, dict]:
    request_id = str(request.get("id", ""))
    if not request_id:
        raise ValueError("Missing request id.")
    msg_type = str(request.get("type", ""))
    if not msg_type:
        raise ValueError("Missing request type.")
    version = int(request.get("version", PROTOCOL_VERSION))
    if version > PROTOCOL_VERSION:
        raise ValueError("Unsupported protocol version.")
    payload = request.get("payload") or {}
    if not isinstance(payload, dict):
        raise ValueError("Payload must be an object.")
    return request_id, msg_type, payload


def _handle_request(msg_type: str, payload: dict) -> dict:
    paths = build_helper_paths()
    profile_id = _optional_profile_id(payload)
    if msg_type == "hello":
        return {"helper_version": HELPER_VERSION, "protocol_version": PROTOCOL_VERSION}
    if msg_type == "status":
        resolved_profile_id = paths.normalize_profile_id(profile_id or "default")
        status = load_status(paths.srs_status_path_for(resolved_profile_id))
        payload = status.__dict__
        payload["profile_id"] = resolved_profile_id
        return payload
    if msg_type == "get_snapshot":
        pair = str(payload.get("pair", "en-ja"))
        return load_snapshot(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "get_ruleset":
        pair = str(payload.get("pair", "en-ja"))
        return load_ruleset(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "srs_diagnostics":
        pair = str(payload.get("pair", "en-ja"))
        return get_srs_runtime_diagnostics(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "record_feedback":
        apply_feedback(
            paths,
            pair=str(payload.get("pair", "")),
            lemma=str(payload.get("lemma", "")),
            rating=str(payload.get("rating", "")),
            source_type=str(payload.get("source_type", "extension")),
            profile_id=profile_id or "default",
        )
        return {"ok": True}
    if msg_type == "record_exposure":
        apply_exposure(
            paths,
            pair=str(payload.get("pair", "")),
            lemma=str(payload.get("lemma", "")),
            source_type=str(payload.get("source_type", "extension")),
            profile_id=profile_id or "default",
        )
        return {"ok": True}
    if msg_type == "trigger_rulegen":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, freedict_de_en_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        config = RulegenJobConfig(
            pair=pair,
            jmdict_path=jmdict_path,
            freedict_de_en_path=freedict_de_en_path,
            profile_id=profile_id or "default",
            set_source_db=set_source_db,
            set_top_n=int(payload.get("set_top_n", 2000)),
            confidence_threshold=float(payload.get("confidence_threshold", 0.0)),
            snapshot_targets=int(payload.get("snapshot_targets", 50)),
            snapshot_sources=int(payload.get("snapshot_sources", 6)),
            initialize_if_empty=payload.get("initialize_if_empty", True),
            persist_store=payload.get("persist_store", True),
            persist_outputs=payload.get("persist_outputs", True),
            update_status=payload.get("update_status", True),
            debug=bool(payload.get("debug", False)),
            debug_sample_size=int(payload.get("debug_sample_size", 10)),
            sample_count=_optional_int(payload, "sample_count"),
            sample_strategy=str(payload.get("sample_strategy", "")).strip() or None,
            sample_seed=_optional_int(payload, "sample_seed"),
        )
        return run_rulegen_job(paths, config=config)
    if msg_type == "srs_initialize":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, freedict_de_en_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        set_top_n = _optional_int(payload, "set_top_n")
        bootstrap_top_n = _optional_int(payload, "bootstrap_top_n")
        return initialize_srs_set(
            paths,
            config=SetInitializationJobConfig(
                pair=pair,
                jmdict_path=jmdict_path,
                freedict_de_en_path=freedict_de_en_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                set_top_n=set_top_n if set_top_n is not None else 800,
                bootstrap_top_n=bootstrap_top_n,
                initial_active_count=_optional_int(payload, "initial_active_count"),
                max_active_items_hint=_optional_int(payload, "max_active_items_hint"),
                replace_pair=bool(payload.get("replace_pair", False)),
                strategy=str(payload.get("strategy", "frequency_bootstrap")),
                objective=str(payload.get("objective", "bootstrap")),
                profile_context=payload.get("profile_context") if isinstance(payload.get("profile_context"), dict) else None,
                trigger=str(payload.get("trigger", "manual")),
            ),
        )
    if msg_type == "srs_plan_set":
        pair = str(payload.get("pair", "en-ja"))
        set_top_n = _optional_int(payload, "set_top_n")
        bootstrap_top_n = _optional_int(payload, "bootstrap_top_n")
        return plan_srs_set(
            paths,
            config=SetPlanningJobConfig(
                pair=pair,
                profile_id=profile_id or "default",
                strategy=str(payload.get("strategy", "frequency_bootstrap")),
                objective=str(payload.get("objective", "bootstrap")),
                set_top_n=set_top_n if set_top_n is not None else 800,
                bootstrap_top_n=bootstrap_top_n,
                initial_active_count=_optional_int(payload, "initial_active_count"),
                max_active_items_hint=_optional_int(payload, "max_active_items_hint"),
                replace_pair=bool(payload.get("replace_pair", False)),
                profile_context=payload.get("profile_context") if isinstance(payload.get("profile_context"), dict) else None,
                trigger=str(payload.get("trigger", "manual")),
            ),
        )
    if msg_type == "srs_refresh":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, freedict_de_en_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        set_top_n = _optional_int(payload, "set_top_n")
        feedback_window_size = _optional_int(payload, "feedback_window_size")
        return refresh_srs_set(
            paths,
            config=SrsRefreshJobConfig(
                pair=pair,
                jmdict_path=jmdict_path,
                freedict_de_en_path=freedict_de_en_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                set_top_n=set_top_n if set_top_n is not None else 2000,
                feedback_window_size=feedback_window_size
                if feedback_window_size is not None
                else 100,
                max_active_items=_optional_int(payload, "max_active_items"),
                max_new_items=_optional_int(payload, "max_new_items"),
                persist_store=bool(payload.get("persist_store", True)),
                trigger=str(payload.get("trigger", "manual")),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
            ),
        )
    if msg_type == "srs_reset":
        pair = str(payload.get("pair", "")).strip() or None
        return reset_srs_data(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "open_data_dir":
        open_path(paths.data_root)
        return {"opened": str(paths.data_root)}
    if msg_type == "profiles_get":
        return get_profiles_snapshot(paths)
    raise ValueError(f"Unknown command: {msg_type}")


def main() -> int:
    while True:
        request = _read_message()
        if request is None:
            return 0
        try:
            request_id, msg_type, payload = _validate_request(request)
            data = _handle_request(msg_type, payload)
            response = {"id": request_id, "ok": True, "data": data, "error": None}
        except Exception as exc:  # noqa: BLE001
            request_id = str(request.get("id", "")) if isinstance(request, dict) else ""
            response = _error_response(request_id, str(exc))
        _write_message(response)


if __name__ == "__main__":
    raise SystemExit(main())
