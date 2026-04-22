from __future__ import annotations

import json
from hashlib import sha1
from pathlib import Path

from lexishift_core.helper.lp_capabilities import pair_requirements, resolve_pair_capability
from lexishift_core.helper.pair_resources import (
    resolve_pair_frequency_pack,
    resolve_pair_resources,
    resolve_pair_translation_packs,
    resolve_stopwords_path,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.status import load_status
from lexishift_core.srs import load_srs_inventory, load_srs_store, resolve_active_item_ids
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy


def _read_artifact_state(path: Path) -> dict[str, object]:
    if not path.exists() or not path.is_file():
        return {
            "exists": False,
            "bytes": 0,
            "sha1": None,
        }
    payload = path.read_bytes()
    return {
        "exists": True,
        "bytes": len(payload),
        "sha1": sha1(payload).hexdigest(),
    }


def _append_family_error(errors: list[str], message: str) -> None:
    rendered = str(message or "").strip()
    if rendered and rendered not in errors:
        errors.append(rendered)


def _resolve_semantic_runtime_capability(
    diagnostics: dict[str, object],
) -> tuple[str, str]:
    semantic_pointer_count = int(diagnostics.get("ruleset_rules_with_semantic_admission") or 0)
    semantic_ready_count = int(diagnostics.get("ruleset_rules_semantic_ready") or 0)
    publication_manifest_family_valid = diagnostics.get("publication_manifest_family_valid")

    if semantic_pointer_count <= 0:
        return "unavailable", "no_semantic_rules"
    if semantic_ready_count <= 0:
        return "published_unready", "no_ready_rules"
    if diagnostics.get("semantic_inventory_exists") is not True:
        return "error", "semantic_inventory_missing"
    if diagnostics.get("semantic_inventory_error") is not None:
        return "error", "semantic_inventory_unreadable"
    if publication_manifest_family_valid is False:
        return "error", "publication_family_invalid"
    return "active", "ready_rules_available"


def _recompute_publication_family_validation(
    *,
    diagnostics: dict,
    manifest_payload: dict,
    normalized_pair: str,
    normalized_profile_id: str,
    ruleset_path: Path,
    snapshot_path: Path,
    semantic_inventory_path: Path,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    manifest_pair = str(manifest_payload.get("pair") or "").strip()
    if manifest_pair != normalized_pair:
        _append_family_error(
            errors,
            f"publication_manifest.pair {manifest_pair!r} does not match requested pair {normalized_pair!r}",
        )
    manifest_profile_id = str(manifest_payload.get("profile_id") or "").strip()
    if manifest_profile_id != normalized_profile_id:
        _append_family_error(
            errors,
            "publication_manifest.profile_id "
            f"{manifest_profile_id!r} does not match requested profile {normalized_profile_id!r}",
        )

    manifest_generation_id = str(manifest_payload.get("generation_id") or "").strip()
    if not manifest_generation_id:
        _append_family_error(errors, "publication_manifest.generation_id is required")

    validation_payload = (
        dict(manifest_payload.get("validation"))
        if isinstance(manifest_payload.get("validation"), dict)
        else {}
    )
    raw_validation_errors = validation_payload.get("errors")
    if isinstance(raw_validation_errors, list):
        for item in raw_validation_errors:
            _append_family_error(errors, str(item))
    if validation_payload.get("family_valid") is False and not errors:
        _append_family_error(errors, "publication_manifest.validation.family_valid is false")

    manifest_artifacts = (
        dict(manifest_payload.get("artifacts"))
        if isinstance(manifest_payload.get("artifacts"), dict)
        else {}
    )
    current_artifacts = {
        "ruleset": _read_artifact_state(ruleset_path),
        "snapshot": _read_artifact_state(snapshot_path),
        "semantic_inventory": _read_artifact_state(semantic_inventory_path),
    }
    for artifact_name, current_state in current_artifacts.items():
        manifest_entry = manifest_artifacts.get(artifact_name)
        if not isinstance(manifest_entry, dict):
            _append_family_error(
                errors,
                f"publication_manifest.artifacts.{artifact_name} is missing or invalid",
            )
            continue
        expected_exists = bool(manifest_entry.get("exists"))
        if expected_exists != current_state["exists"]:
            _append_family_error(
                errors,
                "publication_manifest.artifacts."
                f"{artifact_name}.exists={expected_exists} but current file exists={current_state['exists']}",
            )
        if expected_exists and current_state["exists"]:
            expected_sha1 = str(manifest_entry.get("sha1") or "").strip() or None
            if expected_sha1 and expected_sha1 != current_state["sha1"]:
                _append_family_error(
                    errors,
                    "publication_manifest.artifacts."
                    f"{artifact_name}.sha1 does not match current file",
                )
            expected_bytes = manifest_entry.get("bytes")
            if isinstance(expected_bytes, int) and expected_bytes != current_state["bytes"]:
                _append_family_error(
                    errors,
                    "publication_manifest.artifacts."
                    f"{artifact_name}.bytes does not match current file",
                )

    if diagnostics["ruleset_exists"] and diagnostics["ruleset_error"] is not None:
        _append_family_error(
            errors,
            f"ruleset is unreadable: {diagnostics['ruleset_error']}",
        )
    if diagnostics["snapshot_exists"] and diagnostics["snapshot_error"] is not None:
        _append_family_error(
            errors,
            f"snapshot is unreadable: {diagnostics['snapshot_error']}",
        )
    if (
        diagnostics["semantic_inventory_exists"]
        and diagnostics["semantic_inventory_error"] is not None
    ):
        _append_family_error(
            errors,
            f"semantic inventory is unreadable: {diagnostics['semantic_inventory_error']}",
        )

    semantic_inventory_included = validation_payload.get("semantic_inventory_included")
    if semantic_inventory_included is True and not diagnostics["semantic_inventory_exists"]:
        _append_family_error(
            errors,
            "publication_manifest expects semantic inventory but current file is missing",
        )
    if semantic_inventory_included is False and diagnostics["semantic_inventory_exists"]:
        _append_family_error(
            errors,
            "publication_manifest marks semantic inventory absent but current file exists",
        )

    if manifest_generation_id:
        snapshot_generation_id = (
            str(diagnostics.get("snapshot_generation_id") or "").strip() or None
        )
        if diagnostics["snapshot_exists"] and snapshot_generation_id != manifest_generation_id:
            _append_family_error(
                errors,
                "snapshot.generation_id "
                f"{snapshot_generation_id!r} does not match publication_manifest generation {manifest_generation_id!r}",
            )
        semantic_inventory_generation_id = (
            str(diagnostics.get("semantic_inventory_generation_id") or "").strip() or None
        )
        if diagnostics["semantic_inventory_exists"] and (
            semantic_inventory_generation_id != manifest_generation_id
        ):
            _append_family_error(
                errors,
                "semantic_inventory.generation_id "
                f"{semantic_inventory_generation_id!r} does not match publication_manifest generation {manifest_generation_id!r}",
            )

    return len(errors) == 0, errors


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
    publication_manifest_path = paths.publication_manifest_path(
        normalized_pair, profile_id=normalized_profile_id
    )
    inventory_path = paths.srs_inventory_path_for(normalized_profile_id)
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
        "inventory_path": str(inventory_path),
        "inventory_exists": inventory_path.exists(),
        "inventory_active_items_for_pair": 0,
        "inventory_source": None,
        "inventory_last_initialized_at": None,
        "inventory_last_refreshed_at": None,
        "inventory_last_rebalanced_at": None,
        "inventory_store_missing_item_ids_count": 0,
        "inventory_error": None,
        "ruleset_path": str(ruleset_path),
        "ruleset_exists": ruleset_path.exists(),
        "ruleset_rules_count": 0,
        "ruleset_rules_with_script_forms": 0,
        "ruleset_rules_with_word_package": 0,
        "ruleset_rules_with_semantic_admission": 0,
        "ruleset_rules_semantic_ready": 0,
        "ruleset_rules_semantic_unavailable": 0,
        "ruleset_rules_semantic_not_applicable": 0,
        "semantic_runtime_capability": "unavailable",
        "semantic_runtime_reason_code": "no_semantic_rules",
        "ruleset_error": None,
        "snapshot_path": str(snapshot_path),
        "snapshot_exists": snapshot_path.exists(),
        "snapshot_target_count": 0,
        "snapshot_generation_id": None,
        "snapshot_error": None,
        "semantic_inventory_path": str(semantic_inventory_path),
        "semantic_inventory_exists": semantic_inventory_path.exists(),
        "semantic_inventory_schema_version": None,
        "semantic_inventory_generation_id": None,
        "semantic_inventory_pointer_modes": [],
        "semantic_inventory_default_unavailable_reason_code": None,
        "semantic_inventory_trigger_count": 0,
        "semantic_inventory_sense_count": 0,
        "semantic_inventory_competition_set_count": 0,
        "semantic_inventory_phrase_set_count": 0,
        "semantic_inventory_error": None,
        "publication_manifest_path": str(publication_manifest_path),
        "publication_manifest_exists": publication_manifest_path.exists(),
        "publication_manifest_generation_id": None,
        "publication_manifest_family_valid": None,
        "publication_manifest_error_count": 0,
        "publication_manifest_errors": [],
        "status": load_status(status_path).__dict__,
    }
    store = None
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
    inventory = None
    if diagnostics["inventory_exists"]:
        try:
            inventory = load_srs_inventory(inventory_path)
            pair_inventory = dict(inventory.pairs or {}).get(normalized_pair)
            if pair_inventory is not None:
                diagnostics["inventory_last_initialized_at"] = pair_inventory.last_initialized_at
                diagnostics["inventory_last_refreshed_at"] = pair_inventory.last_refreshed_at
                diagnostics["inventory_last_rebalanced_at"] = pair_inventory.last_rebalanced_at
        except Exception as exc:  # noqa: BLE001
            diagnostics["inventory_error"] = str(exc)
            inventory = None
    if diagnostics["store_error"] is None and store is not None:
        try:
            active_item_ids, inventory_source = resolve_active_item_ids(
                store=store,
                pair=normalized_pair,
                inventory=inventory if diagnostics["inventory_exists"] else None,
            )
            diagnostics["inventory_active_items_for_pair"] = len(active_item_ids)
            diagnostics["inventory_source"] = inventory_source
            if inventory is not None and normalized_pair in dict(inventory.pairs or {}):
                raw_active_item_ids = tuple(
                    dict(inventory.pairs)[normalized_pair].active_item_ids or ()
                )
                available_item_ids = {
                    item.item_id
                    for item in store.items
                    if item.language_pair == normalized_pair and str(item.item_id or "").strip()
                }
                diagnostics["inventory_store_missing_item_ids_count"] = len(
                    [
                        item_id
                        for item_id in raw_active_item_ids
                        if str(item_id).strip() and item_id not in available_item_ids
                    ]
                )
        except Exception as exc:  # noqa: BLE001
            diagnostics["inventory_error"] = str(exc)
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
            diagnostics["snapshot_generation_id"] = (
                str(snapshot_payload.get("generation_id") or "").strip() or None
            )
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
            diagnostics["semantic_inventory_generation_id"] = (
                str(semantic_inventory_payload.get("generation_id") or "").strip() or None
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
    if diagnostics["publication_manifest_exists"]:
        try:
            manifest_payload = json.loads(publication_manifest_path.read_text(encoding="utf-8"))
            diagnostics["publication_manifest_generation_id"] = (
                str(manifest_payload.get("generation_id") or "").strip() or None
            )
            family_valid, family_errors = _recompute_publication_family_validation(
                diagnostics=diagnostics,
                manifest_payload=manifest_payload,
                normalized_pair=normalized_pair,
                normalized_profile_id=normalized_profile_id,
                ruleset_path=ruleset_path,
                snapshot_path=snapshot_path,
                semantic_inventory_path=semantic_inventory_path,
            )
            diagnostics["publication_manifest_family_valid"] = family_valid
            diagnostics["publication_manifest_errors"] = family_errors
            diagnostics["publication_manifest_error_count"] = len(family_errors)
        except Exception as exc:  # noqa: BLE001
            diagnostics["publication_manifest_family_valid"] = False
            diagnostics["publication_manifest_errors"] = [str(exc)]
            diagnostics["publication_manifest_error_count"] = 1
    (
        diagnostics["semantic_runtime_capability"],
        diagnostics["semantic_runtime_reason_code"],
    ) = _resolve_semantic_runtime_capability(diagnostics)
    return diagnostics
