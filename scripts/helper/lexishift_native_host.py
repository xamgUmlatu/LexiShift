#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import sys
import traceback
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _platform_data_root() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def _native_host_log_path() -> Optional[Path]:
    override = str(os.environ.get("LEXISHIFT_DATA_DIR", "") or "").strip()
    try:
        data_root = Path(override).expanduser() if override else _platform_data_root()
        log_dir = data_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return log_dir / "native_host.log"


def _log_native_host_failure(stage: str, exc: BaseException) -> None:
    log_path = _native_host_log_path()
    if log_path is None:
        return
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] stage={stage}\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=handle)
            handle.write("\n")
    except OSError:
        return


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


try:
    _inject_core_path()

    from lexishift_core.helper.engine import (
        SetAdmissionPreviewJobConfig,
        get_srs_runtime_diagnostics,
        RulegenJobConfig,
        SrsRebalanceJobConfig,
        SrsRefreshJobConfig,
        SetInitializationJobConfig,
        SetPlanningJobConfig,
        apply_srs_rebalance,
        apply_exposure,
        apply_feedback,
        get_srs_item_rule_details,
        ingest_browsing_admission_signals,
        initialize_srs_set,
        list_srs_items,
        load_semantic_inventory,
        load_ruleset,
        load_snapshot,
        plan_srs_rebalance,
        plan_srs_set,
        preview_srs_admission,
        refresh_srs_set,
        reset_srs_data,
        run_rulegen_job,
        semantic_admit_batch,
        suppress_srs_admission,
    )
    from lexishift_core.helper.profiles import get_profile_rulesets_snapshot, get_profiles_snapshot
    from lexishift_core.helper.os import open_path
    from lexishift_core.helper.paths import build_helper_paths
    from lexishift_core.helper.status import load_status
    from lexishift_core.helper.use_cases.semantic_pack_install import (
        DEFAULT_PACK_ID,
        SemanticPackInstallConfig,
        install_semantic_pack,
    )
    from lexishift_core.helper.lp_capabilities import (
        default_frequency_db_path,
        default_jmdict_path,
        default_translation_dictionary_path,
    )
except Exception as exc:  # noqa: BLE001
    _log_native_host_failure("startup_import", exc)
    raise


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
    return {
        "id": request_id,
        "ok": False,
        "data": None,
        "error": {"code": code, "message": message},
    }


def _optional_int(payload: Dict[str, Any], key: str) -> Optional[int]:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(payload: Dict[str, Any], key: str) -> Optional[float]:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(payload: Dict[str, Any], key: str) -> Optional[bool]:
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


def _optional_string_list(payload: Dict[str, Any], key: str) -> Optional[list[str]]:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        return None
    normalized = [item for item in items if item]
    return normalized or None


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
    translation_dict_path = _optional_path(payload, "translation_dict_path")
    if translation_dict_path is None:
        translation_dict_path = default_translation_dictionary_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    set_source_db = _optional_path(payload, "frequency_pack_path")
    if set_source_db is None:
        set_source_db = _optional_path(payload, "set_source_db")
    if set_source_db is None:
        set_source_db = default_frequency_db_path(
            pair,
            frequency_packs_dir=paths.frequency_packs_dir,
        )
    return jmdict_path, translation_dict_path, set_source_db


def _handle_install_semantic_pack(payload: Dict[str, Any]) -> dict[str, object]:
    data_root = _optional_path(payload, "data_root")
    allow_default_data_root = _optional_bool(payload, "allow_default_data_root") is True
    if data_root is None and not allow_default_data_root:
        raise ValueError(
            "install_semantic_pack requires payload.data_root for now, or "
            "payload.allow_default_data_root to target the platform default."
        )
    semantic_inventory_path = _optional_path(payload, "semantic_inventory_path")
    copy_pack = _optional_bool(payload, "copy_pack")
    if copy_pack is None:
        copy_pack = _optional_bool(payload, "no_pack_copy") is not True
    paths = build_helper_paths(data_root)
    return install_semantic_pack(
        paths,
        config=SemanticPackInstallConfig(
            pair=str(payload.get("pair", "en-es")).strip() or "en-es",
            profile_id=_optional_profile_id(payload) or "default",
            semantic_inventory_path=semantic_inventory_path,
            pack_id=str(payload.get("pack_id", DEFAULT_PACK_ID)).strip() or DEFAULT_PACK_ID,
            generated_at=str(payload.get("generated_at", "")).strip(),
            copy_pack=copy_pack,
            dry_run=_optional_bool(payload, "dry_run") is True,
            rule_source=str(payload.get("rule_source", "semantic_pack_install")).strip()
            or "semantic_pack_install",
            rule_source_type=str(payload.get("rule_source_type", "semantic_veto_candidate")).strip()
            or "semantic_veto_candidate",
        ),
    )


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
    if msg_type == "install_semantic_pack":
        return _handle_install_semantic_pack(payload)
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
    if msg_type == "get_semantic_inventory":
        pair = str(payload.get("pair", "en-ja"))
        return load_semantic_inventory(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "srs_diagnostics":
        pair = str(payload.get("pair", "en-ja"))
        return get_srs_runtime_diagnostics(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "srs_items_list":
        pair = str(payload.get("pair", "en-ja"))
        return list_srs_items(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "srs_item_rule_details":
        pair = str(payload.get("pair", "en-ja"))
        return get_srs_item_rule_details(
            paths,
            pair=pair,
            profile_id=profile_id or "default",
            lemma=str(payload.get("lemma", "")),
            limit=_optional_int(payload, "limit"),
        )
    if msg_type == "semantic_admit_batch":
        return semantic_admit_batch(paths, payload=payload)
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
    if msg_type == "srs_admission_suppress":
        return suppress_srs_admission(
            paths,
            pair=str(payload.get("pair", "")),
            lemma=str(payload.get("lemma", "")),
            reason=str(payload.get("reason", "user_blocked")),
            note=str(payload.get("note", "")).strip() or None,
            profile_id=profile_id or "default",
        )
    if msg_type == "srs_browsing_signal_ingest":
        signals = payload.get("signals")
        if not isinstance(signals, list):
            signals = []
        opt_in = _optional_bool(payload, "opt_in") is True
        if not opt_in:
            opt_in = _optional_bool(payload, "browsing_admission_enabled") is True
        return ingest_browsing_admission_signals(
            paths,
            pair=str(payload.get("pair", "")),
            signals=signals,
            profile_id=profile_id or "default",
            captured_at=str(payload.get("captured_at", "")).strip() or None,
            opt_in=opt_in,
        )
    if msg_type == "trigger_rulegen":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, translation_dict_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        config = RulegenJobConfig(
            pair=pair,
            jmdict_path=jmdict_path,
            translation_dict_path=translation_dict_path,
            profile_id=profile_id or "default",
            set_source_db=set_source_db,
            set_top_n=_optional_int(payload, "set_top_n"),
            confidence_threshold=_optional_float(payload, "confidence_threshold"),
            max_definitions_per_target=_optional_int(payload, "max_definitions_per_target"),
            max_rules_per_target=_optional_int(payload, "max_rules_per_target"),
            semantic_demotion_scale=_optional_float(payload, "semantic_demotion_scale"),
            include_variants=_optional_bool(payload, "include_variants"),
            allow_multiword_glosses=_optional_bool(payload, "allow_multiword_glosses"),
            pos_scoring_enabled=_optional_bool(payload, "pos_scoring_enabled"),
            pos_exact_match_bonus=_optional_float(payload, "pos_exact_match_bonus"),
            pos_compatible_match_bonus=_optional_float(payload, "pos_compatible_match_bonus"),
            score_weight_dict_priority=_optional_float(payload, "score_weight_dict_priority"),
            score_weight_frequency_weight=_optional_float(payload, "score_weight_frequency_weight"),
            score_weight_pos_match=_optional_float(payload, "score_weight_pos_match"),
            score_weight_variant_penalty=_optional_float(payload, "score_weight_variant_penalty"),
            score_weight_phrase_penalty=_optional_float(payload, "score_weight_phrase_penalty"),
            score_weight_embedding=_optional_float(payload, "score_weight_embedding"),
            reverse_check_enabled=_optional_bool(payload, "reverse_check_enabled"),
            reverse_check_match_bonus=_optional_float(payload, "reverse_check_match_bonus"),
            reverse_check_near_bonus=_optional_float(payload, "reverse_check_near_bonus"),
            reverse_check_near_rank_max=_optional_int(payload, "reverse_check_near_rank_max"),
            reverse_check_far_hit_penalty=_optional_float(payload, "reverse_check_far_hit_penalty"),
            reverse_check_miss_penalty=_optional_float(payload, "reverse_check_miss_penalty"),
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
        jmdict_path, translation_dict_path, set_source_db = _resolve_pair_resource_paths(
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
                translation_dict_path=translation_dict_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                set_top_n=set_top_n,
                bootstrap_top_n=bootstrap_top_n,
                initial_active_count=_optional_int(payload, "initial_active_count"),
                max_active_items_hint=_optional_int(payload, "max_active_items_hint"),
                replace_pair=bool(payload.get("replace_pair", False)),
                strategy=str(payload.get("strategy", "frequency_bootstrap")),
                objective=str(payload.get("objective", "bootstrap")),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
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
                set_top_n=set_top_n,
                bootstrap_top_n=bootstrap_top_n,
                initial_active_count=_optional_int(payload, "initial_active_count"),
                max_active_items_hint=_optional_int(payload, "max_active_items_hint"),
                replace_pair=bool(payload.get("replace_pair", False)),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
                trigger=str(payload.get("trigger", "manual")),
            ),
        )
    if msg_type == "srs_preview_admission":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, _translation_dict_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        set_top_n = _optional_int(payload, "set_top_n")
        bootstrap_top_n = _optional_int(payload, "bootstrap_top_n")
        return preview_srs_admission(
            paths,
            config=SetAdmissionPreviewJobConfig(
                pair=pair,
                jmdict_path=jmdict_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                strategy=str(payload.get("strategy", "frequency_bootstrap")),
                objective=str(payload.get("objective", "bootstrap")),
                set_top_n=set_top_n,
                bootstrap_top_n=bootstrap_top_n,
                initial_active_count=_optional_int(payload, "initial_active_count"),
                max_active_items_hint=_optional_int(payload, "max_active_items_hint"),
                preview_count=_optional_int(payload, "preview_count"),
                preview_sampling_mode=str(payload.get("preview_sampling_mode", "")).strip() or None,
                preview_seed=_optional_int(payload, "preview_seed"),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
                trigger=str(payload.get("trigger", "manual")),
            ),
        )
    if msg_type == "srs_refresh":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, translation_dict_path, set_source_db = _resolve_pair_resource_paths(
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
                translation_dict_path=translation_dict_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                set_top_n=set_top_n,
                feedback_window_size=feedback_window_size,
                max_active_items=_optional_int(payload, "max_active_items"),
                max_new_items=_optional_int(payload, "max_new_items"),
                allowed_pos=_optional_string_list(payload, "allowed_pos"),
                persist_store=bool(payload.get("persist_store", True)),
                trigger=str(payload.get("trigger", "manual")),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
            ),
        )
    if msg_type == "srs_rebalance_plan":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, translation_dict_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        return plan_srs_rebalance(
            paths,
            config=SrsRebalanceJobConfig(
                pair=pair,
                jmdict_path=jmdict_path,
                translation_dict_path=translation_dict_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                strategy=str(payload.get("strategy", "profile_growth")),
                objective=str(payload.get("objective", "rebalance")),
                set_top_n=_optional_int(payload, "set_top_n"),
                max_active_items=_optional_int(payload, "max_active_items"),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
                trigger=str(payload.get("trigger", "manual")),
            ),
        )
    if msg_type == "srs_rebalance_apply":
        pair = str(payload.get("pair", "en-ja")).strip() or "en-ja"
        jmdict_path, translation_dict_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload,
        )
        return apply_srs_rebalance(
            paths,
            config=SrsRebalanceJobConfig(
                pair=pair,
                jmdict_path=jmdict_path,
                translation_dict_path=translation_dict_path,
                set_source_db=set_source_db,
                profile_id=profile_id or "default",
                strategy=str(payload.get("strategy", "profile_growth")),
                objective=str(payload.get("objective", "rebalance")),
                set_top_n=_optional_int(payload, "set_top_n"),
                max_active_items=_optional_int(payload, "max_active_items"),
                profile_context=payload.get("profile_context")
                if isinstance(payload.get("profile_context"), dict)
                else None,
                trigger=str(payload.get("trigger", "manual")),
            ),
        )
    if msg_type == "srs_reset":
        pair = str(payload.get("pair", "")).strip() or None
        return reset_srs_data(
            paths,
            pair=pair,
            profile_id=profile_id or "default",
            preserve_lifecycle_metadata=_optional_bool(
                payload,
                "preserve_lifecycle_metadata",
            )
            is True,
        )
    if msg_type == "open_data_dir":
        open_path(paths.data_root)
        return {"opened": str(paths.data_root)}
    if msg_type == "profiles_get":
        return get_profiles_snapshot(paths)
    if msg_type == "profile_rulesets_get":
        return get_profile_rulesets_snapshot(paths, profile_id=profile_id)
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
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        _log_native_host_failure("startup_runtime", exc)
        raise
