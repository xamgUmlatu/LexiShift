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

from lexishift_core.helper.os import open_path
from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.helper.status import load_status
from lexishift_core.helper.lp_capabilities import (
    default_frequency_db_path,
    default_jmdict_path,
    default_translation_dictionary_path,
)


PROTOCOL_VERSION = 1
HELPER_VERSION = "0.1.0"
_ENGINE_EXPORTS: Optional[dict[str, Any]] = None
_PROFILE_EXPORTS: Optional[dict[str, Any]] = None


def _load_engine_exports() -> dict[str, Any]:
    global _ENGINE_EXPORTS
    if _ENGINE_EXPORTS is None:
        from lexishift_core.helper.engine import (
            apply_srs_rebalance,
            get_srs_runtime_diagnostics,
            RulegenJobConfig,
            SrsRebalanceJobConfig,
            SetAdmissionPreviewJobConfig,
            SrsRefreshJobConfig,
            SetInitializationJobConfig,
            SetPlanningJobConfig,
            apply_exposure,
            apply_feedback,
            initialize_srs_set,
            load_ruleset,
            load_snapshot,
            plan_srs_rebalance,
            plan_srs_set,
            preview_srs_admission,
            refresh_srs_set,
            reset_srs_data,
            run_rulegen_job,
        )

        _ENGINE_EXPORTS = {
            "apply_srs_rebalance": apply_srs_rebalance,
            "get_srs_runtime_diagnostics": get_srs_runtime_diagnostics,
            "RulegenJobConfig": RulegenJobConfig,
            "SrsRebalanceJobConfig": SrsRebalanceJobConfig,
            "SetAdmissionPreviewJobConfig": SetAdmissionPreviewJobConfig,
            "SrsRefreshJobConfig": SrsRefreshJobConfig,
            "SetInitializationJobConfig": SetInitializationJobConfig,
            "SetPlanningJobConfig": SetPlanningJobConfig,
            "apply_exposure": apply_exposure,
            "apply_feedback": apply_feedback,
            "initialize_srs_set": initialize_srs_set,
            "load_ruleset": load_ruleset,
            "load_snapshot": load_snapshot,
            "plan_srs_rebalance": plan_srs_rebalance,
            "plan_srs_set": plan_srs_set,
            "preview_srs_admission": preview_srs_admission,
            "refresh_srs_set": refresh_srs_set,
            "reset_srs_data": reset_srs_data,
            "run_rulegen_job": run_rulegen_job,
        }
    return _ENGINE_EXPORTS


def _load_profile_exports() -> dict[str, Any]:
    global _PROFILE_EXPORTS
    if _PROFILE_EXPORTS is None:
        from lexishift_core.helper.profiles import (
            get_profile_rulesets_snapshot,
            get_profiles_snapshot,
        )

        _PROFILE_EXPORTS = {
            "get_profile_rulesets_snapshot": get_profile_rulesets_snapshot,
            "get_profiles_snapshot": get_profiles_snapshot,
        }
    return _PROFILE_EXPORTS


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
        translation_dict_path = _optional_path(payload, "freedict_de_en_path")
    if translation_dict_path is None:
        translation_dict_path = default_translation_dictionary_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    set_source_db = _optional_path(payload, "set_source_db")
    if set_source_db is None:
        set_source_db = default_frequency_db_path(
            pair,
            frequency_packs_dir=paths.frequency_packs_dir,
        )
    return jmdict_path, translation_dict_path, set_source_db


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
    profile_id = _optional_profile_id(payload)
    if msg_type == "hello":
        return {"helper_version": HELPER_VERSION, "protocol_version": PROTOCOL_VERSION}
    paths = build_helper_paths()
    if msg_type == "status":
        resolved_profile_id = paths.normalize_profile_id(profile_id or "default")
        status = load_status(paths.srs_status_path_for(resolved_profile_id))
        payload = status.__dict__
        payload["profile_id"] = resolved_profile_id
        return payload
    if msg_type == "get_snapshot":
        pair = str(payload.get("pair", "en-ja"))
        load_snapshot = _load_engine_exports()["load_snapshot"]
        return load_snapshot(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "get_ruleset":
        pair = str(payload.get("pair", "en-ja"))
        load_ruleset = _load_engine_exports()["load_ruleset"]
        return load_ruleset(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "srs_diagnostics":
        pair = str(payload.get("pair", "en-ja"))
        get_srs_runtime_diagnostics = _load_engine_exports()["get_srs_runtime_diagnostics"]
        return get_srs_runtime_diagnostics(
            paths,
            pair=pair,
            profile_id=profile_id or "default",
        )
    if msg_type == "record_feedback":
        apply_feedback = _load_engine_exports()["apply_feedback"]
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
        apply_exposure = _load_engine_exports()["apply_exposure"]
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
        payload_for_rulegen = dict(payload)
        if (
            str(pair).lower() == "en-ja"
            and not payload_for_rulegen.get("translation_dict_path")
            and payload_for_rulegen.get("jmdict_path")
        ):
            payload_for_rulegen["translation_dict_path"] = payload_for_rulegen["jmdict_path"]
        jmdict_path, translation_dict_path, set_source_db = _resolve_pair_resource_paths(
            paths,
            pair=pair,
            payload=payload_for_rulegen,
        )
        rulegen_job_config_cls = _load_engine_exports()["RulegenJobConfig"]
        config = rulegen_job_config_cls(
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
        run_rulegen_job = _load_engine_exports()["run_rulegen_job"]
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
        set_initialization_job_config_cls = _load_engine_exports()["SetInitializationJobConfig"]
        initialize_srs_set = _load_engine_exports()["initialize_srs_set"]
        return initialize_srs_set(
            paths,
            config=set_initialization_job_config_cls(
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
        set_planning_job_config_cls = _load_engine_exports()["SetPlanningJobConfig"]
        plan_srs_set = _load_engine_exports()["plan_srs_set"]
        return plan_srs_set(
            paths,
            config=set_planning_job_config_cls(
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
        set_admission_preview_job_config_cls = _load_engine_exports()[
            "SetAdmissionPreviewJobConfig"
        ]
        preview_srs_admission = _load_engine_exports()["preview_srs_admission"]
        return preview_srs_admission(
            paths,
            config=set_admission_preview_job_config_cls(
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
        srs_refresh_job_config_cls = _load_engine_exports()["SrsRefreshJobConfig"]
        refresh_srs_set = _load_engine_exports()["refresh_srs_set"]
        return refresh_srs_set(
            paths,
            config=srs_refresh_job_config_cls(
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
        srs_rebalance_job_config_cls = _load_engine_exports()["SrsRebalanceJobConfig"]
        plan_srs_rebalance = _load_engine_exports()["plan_srs_rebalance"]
        return plan_srs_rebalance(
            paths,
            config=srs_rebalance_job_config_cls(
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
        srs_rebalance_job_config_cls = _load_engine_exports()["SrsRebalanceJobConfig"]
        apply_srs_rebalance = _load_engine_exports()["apply_srs_rebalance"]
        return apply_srs_rebalance(
            paths,
            config=srs_rebalance_job_config_cls(
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
        reset_srs_data = _load_engine_exports()["reset_srs_data"]
        return reset_srs_data(paths, pair=pair, profile_id=profile_id or "default")
    if msg_type == "open_data_dir":
        open_path(paths.data_root)
        return {"opened": str(paths.data_root)}
    if msg_type == "profiles_get":
        get_profiles_snapshot = _load_profile_exports()["get_profiles_snapshot"]
        return get_profiles_snapshot(paths)
    if msg_type == "profile_rulesets_get":
        get_profile_rulesets_snapshot = _load_profile_exports()["get_profile_rulesets_snapshot"]
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
    raise SystemExit(main())
