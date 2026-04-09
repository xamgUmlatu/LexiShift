from __future__ import annotations

import json

from lexishift_core.helper.lp_capabilities import pair_requirements, resolve_pair_capability
from lexishift_core.helper.pair_resources import (
    resolve_pair_frequency_pack,
    resolve_pair_resources,
    resolve_pair_translation_packs,
    resolve_stopwords_path,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.status import load_status
from lexishift_core.srs import load_srs_store
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy


def get_srs_runtime_diagnostics(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
) -> dict:
    capability = resolve_pair_capability(pair)
    normalized_pair = capability.pair
    normalized_profile_id = paths.normalize_profile_id(profile_id)
    pair_policy = resolve_srs_pair_policy(normalized_pair)
    resolved_jmdict_path, resolved_translation_dict_path, resolved_set_source_db = (
        resolve_pair_resources(
            paths,
            pair=normalized_pair,
            jmdict_path=None,
            translation_dict_path=None,
            set_source_db=None,
        )
    )
    resolved_translation_pack, resolved_reverse_translation_pack = resolve_pair_translation_packs(
        paths,
        pair=normalized_pair,
        translation_dict_path=resolved_translation_dict_path,
        reverse_translation_dict_path=None,
    )
    resolved_frequency_pack = resolve_pair_frequency_pack(
        paths,
        pair=normalized_pair,
        set_source_db=resolved_set_source_db,
    )
    resolved_stopwords_path = resolve_stopwords_path(paths, pair=normalized_pair)
    missing_inputs: list[dict[str, object]] = []
    if capability.requires_jmdict_for_seed or capability.requires_jmdict_for_rulegen:
        if not resolved_jmdict_path:
            missing_inputs.append({"type": "jmdict_path", "path": None})
        elif not resolved_jmdict_path.exists():
            missing_inputs.append({"type": "jmdict_path", "path": str(resolved_jmdict_path)})
    if capability.requires_translation_dictionary_for_rulegen:
        if not resolved_translation_dict_path:
            missing_inputs.append({"type": "translation_dict_path", "path": None})
            missing_inputs.append({"type": "translation_pack_path", "path": None})
        elif not resolved_translation_dict_path.exists():
            missing_inputs.append(
                {"type": "translation_dict_path", "path": str(resolved_translation_dict_path)}
            )
            missing_inputs.append(
                {"type": "translation_pack_path", "path": str(resolved_translation_dict_path)}
            )
    if not resolved_set_source_db:
        missing_inputs.append({"type": "set_source_db", "path": None})
    elif not resolved_set_source_db.exists():
        missing_inputs.append({"type": "set_source_db", "path": str(resolved_set_source_db)})

    store_path = paths.srs_store_path_for(normalized_profile_id)
    ruleset_path = paths.ruleset_path(normalized_pair, profile_id=normalized_profile_id)
    snapshot_path = paths.snapshot_path(normalized_pair, profile_id=normalized_profile_id)
    semantic_inventory_path = paths.semantic_inventory_path(
        normalized_pair, profile_id=normalized_profile_id
    )
    status_path = paths.srs_status_path_for(normalized_profile_id)
    translation_dict_path_text = (
        str(resolved_translation_dict_path) if resolved_translation_dict_path else None
    )
    reverse_translation_dict_path_text = (
        str(resolved_reverse_translation_pack.path) if resolved_reverse_translation_pack else None
    )
    diagnostics = {
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "requirements": pair_requirements(normalized_pair),
        "pair_policy": pair_policy_to_dict(pair_policy),
        "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
        "jmdict_exists": bool(resolved_jmdict_path and resolved_jmdict_path.exists()),
        "translation_dict_path": translation_dict_path_text,
        "translation_dict_exists": bool(
            resolved_translation_dict_path and resolved_translation_dict_path.exists()
        ),
        "translation_pack_path": translation_dict_path_text,
        "translation_pack_exists": bool(
            resolved_translation_dict_path and resolved_translation_dict_path.exists()
        ),
        "translation_dict_provider": (
            resolved_translation_pack.provider if resolved_translation_pack else None
        ),
        "translation_pack_id": resolved_translation_pack.pack_id
        if resolved_translation_pack
        else None,
        "translation_pos_source_profile": (
            resolved_translation_pack.pos_source_profile if resolved_translation_pack else None
        ),
        "reverse_translation_dict_path": reverse_translation_dict_path_text,
        "reverse_translation_dict_exists": bool(
            resolved_reverse_translation_pack and resolved_reverse_translation_pack.path.exists()
        ),
        "reverse_translation_pack_path": reverse_translation_dict_path_text,
        "reverse_translation_pack_exists": bool(
            resolved_reverse_translation_pack and resolved_reverse_translation_pack.path.exists()
        ),
        "reverse_translation_dict_provider": (
            resolved_reverse_translation_pack.provider
            if resolved_reverse_translation_pack
            else None
        ),
        "reverse_translation_pack_id": (
            resolved_reverse_translation_pack.pack_id if resolved_reverse_translation_pack else None
        ),
        "reverse_translation_pos_source_profile": (
            resolved_reverse_translation_pack.pos_source_profile
            if resolved_reverse_translation_pack
            else None
        ),
        "set_source_db": str(resolved_set_source_db) if resolved_set_source_db else None,
        "set_source_db_exists": bool(resolved_set_source_db and resolved_set_source_db.exists()),
        "frequency_pack_path": str(resolved_frequency_pack.path)
        if resolved_frequency_pack
        else None,
        "frequency_pack_exists": bool(
            resolved_frequency_pack and resolved_frequency_pack.path.exists()
        ),
        "frequency_pack_id": resolved_frequency_pack.pack_id if resolved_frequency_pack else None,
        "frequency_pack_provider": (
            resolved_frequency_pack.provider if resolved_frequency_pack else None
        ),
        "frequency_pos_source_profile": (
            resolved_frequency_pack.pos_source_profile if resolved_frequency_pack else None
        ),
        "stopwords_path": str(resolved_stopwords_path) if resolved_stopwords_path else None,
        "stopwords_exists": bool(resolved_stopwords_path and resolved_stopwords_path.exists()),
        "missing_inputs": missing_inputs,
        "store_path": str(store_path),
        "store_exists": store_path.exists(),
        "store_items_total": 0,
        "store_items_for_pair": 0,
        "store_items_with_word_package_total": 0,
        "store_items_with_word_package_for_pair": 0,
        "store_error": None,
        "ruleset_path": str(ruleset_path),
        "ruleset_exists": ruleset_path.exists(),
        "ruleset_rules_count": 0,
        "ruleset_rules_with_script_forms": 0,
        "ruleset_rules_with_word_package": 0,
        "ruleset_rules_with_semantic_admission": 0,
        "ruleset_rules_semantic_ready": 0,
        "ruleset_rules_semantic_unavailable": 0,
        "ruleset_rules_semantic_not_applicable": 0,
        "ruleset_error": None,
        "snapshot_path": str(snapshot_path),
        "snapshot_exists": snapshot_path.exists(),
        "snapshot_target_count": 0,
        "snapshot_error": None,
        "semantic_inventory_path": str(semantic_inventory_path),
        "semantic_inventory_exists": semantic_inventory_path.exists(),
        "semantic_inventory_schema_version": None,
        "semantic_inventory_pointer_modes": [],
        "semantic_inventory_default_unavailable_reason_code": None,
        "semantic_inventory_trigger_count": 0,
        "semantic_inventory_sense_count": 0,
        "semantic_inventory_competition_set_count": 0,
        "semantic_inventory_phrase_set_count": 0,
        "semantic_inventory_error": None,
        "status": load_status(status_path).__dict__,
    }
    if diagnostics["store_exists"]:
        try:
            store = load_srs_store(store_path)
            diagnostics["store_items_total"] = len(store.items)
            diagnostics["store_items_with_word_package_total"] = len(
                [item for item in store.items if item.word_package]
            )
            pair_items = [item for item in store.items if item.language_pair == normalized_pair]
            diagnostics["store_items_for_pair"] = len(pair_items)
            diagnostics["store_items_with_word_package_for_pair"] = len(
                [item for item in pair_items if item.word_package]
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics["store_error"] = str(exc)
    if diagnostics["ruleset_exists"]:
        try:
            ruleset_payload = json.loads(ruleset_path.read_text(encoding="utf-8"))
            rules = ruleset_payload.get("rules", [])
            if isinstance(rules, list):
                diagnostics["ruleset_rules_count"] = len(rules)
                diagnostics["ruleset_rules_with_script_forms"] = len(
                    [
                        rule
                        for rule in rules
                        if isinstance(rule, dict)
                        and isinstance(rule.get("metadata"), dict)
                        and isinstance(rule.get("metadata", {}).get("script_forms"), dict)
                    ]
                )
                diagnostics["ruleset_rules_with_word_package"] = len(
                    [
                        rule
                        for rule in rules
                        if isinstance(rule, dict)
                        and isinstance(rule.get("metadata"), dict)
                        and isinstance(rule.get("metadata", {}).get("word_package"), dict)
                    ]
                )
                semantic_admission_rules = [
                    rule
                    for rule in rules
                    if isinstance(rule, dict)
                    and isinstance(rule.get("metadata"), dict)
                    and isinstance(rule.get("metadata", {}).get("semantic_admission"), dict)
                ]
                diagnostics["ruleset_rules_with_semantic_admission"] = len(semantic_admission_rules)
                semantic_statuses = [
                    str(rule.get("metadata", {}).get("semantic_admission", {}).get("status") or "")
                    for rule in semantic_admission_rules
                ]
                diagnostics["ruleset_rules_semantic_ready"] = len(
                    [status for status in semantic_statuses if status == "ready"]
                )
                diagnostics["ruleset_rules_semantic_unavailable"] = len(
                    [status for status in semantic_statuses if status == "unavailable"]
                )
                diagnostics["ruleset_rules_semantic_not_applicable"] = len(
                    [status for status in semantic_statuses if status == "not_applicable"]
                )
            else:
                diagnostics["ruleset_rules_count"] = 0
        except Exception as exc:  # noqa: BLE001
            diagnostics["ruleset_error"] = str(exc)
    if diagnostics["snapshot_exists"]:
        try:
            snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            stats = snapshot_payload.get("stats", {})
            target_count = stats.get("target_count")
            if target_count is None and isinstance(snapshot_payload.get("targets"), list):
                target_count = len(snapshot_payload.get("targets", []))
            diagnostics["snapshot_target_count"] = int(target_count or 0)
        except Exception as exc:  # noqa: BLE001
            diagnostics["snapshot_error"] = str(exc)
    if diagnostics["semantic_inventory_exists"]:
        try:
            semantic_inventory_payload = json.loads(
                semantic_inventory_path.read_text(encoding="utf-8")
            )
            diagnostics["semantic_inventory_schema_version"] = semantic_inventory_payload.get(
                "schema_version"
            )
            capability = semantic_inventory_payload.get("capability")
            if isinstance(capability, dict):
                pointer_modes = capability.get("pointer_modes")
                if isinstance(pointer_modes, list):
                    diagnostics["semantic_inventory_pointer_modes"] = [
                        str(mode).strip() for mode in pointer_modes if str(mode).strip()
                    ]
                diagnostics["semantic_inventory_default_unavailable_reason_code"] = (
                    str(capability.get("default_unavailable_reason_code") or "").strip() or None
                )
            diagnostics["semantic_inventory_trigger_count"] = len(
                semantic_inventory_payload.get("triggers", {}) or {}
            )
            diagnostics["semantic_inventory_sense_count"] = len(
                semantic_inventory_payload.get("senses", {}) or {}
            )
            diagnostics["semantic_inventory_competition_set_count"] = len(
                semantic_inventory_payload.get("competition_sets", {}) or {}
            )
            diagnostics["semantic_inventory_phrase_set_count"] = len(
                semantic_inventory_payload.get("phrase_sets", {}) or {}
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics["semantic_inventory_error"] = str(exc)
    return diagnostics
