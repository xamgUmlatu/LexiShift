from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Callable, Mapping, Optional

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig, RulegenOutput
from lexishift_core.lexicon.word_package import (
    normalize_word_package,
    resolve_language_tag_from_pair,
)
from lexishift_core.rulegen.tuning import resolve_rulegen_tuning
from lexishift_core.srs import (
    SrsInventory,
    SrsItem,
    SrsSettings,
    SrsStore,
    load_srs_inventory,
    resolve_active_item_ids,
    save_srs_inventory,
    save_srs_store,
    set_active_item_ids,
)
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.rebalance import (
    SOURCE_KIND_NEW_SEED,
    build_rebalance_plan,
)
from lexishift_core.srs.seed import SeedSelectionConfig, SeedWord
from lexishift_core.srs.signal_queue import summarize_signal_events
from lexishift_core.srs.source import SOURCE_FREQUENCY_LIST, normalize_source_type
from lexishift_core.srs.store_ops import upsert_item
from lexishift_core.srs.time import now_utc


def plan_srs_rebalance(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., SrsSettings],
    ensure_store_fn: Callable[..., SrsStore],
    count_items_for_pair_fn: Callable[..., int],
    build_set_plan_payload_fn: Callable[..., dict[str, object]],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    build_seed_candidates_fn: Callable[..., list[SeedWord]],
) -> dict[str, object]:
    context = _prepare_rebalance_context(
        paths=paths,
        config=config,
        resolve_pair_set_top_n_fn=resolve_pair_set_top_n_fn,
        resolve_pair_resources_fn=resolve_pair_resources_fn,
        ensure_pair_requirements_fn=ensure_pair_requirements_fn,
        resolve_profile_id_fn=resolve_profile_id_fn,
        ensure_settings_fn=ensure_settings_fn,
        ensure_store_fn=ensure_store_fn,
        count_items_for_pair_fn=count_items_for_pair_fn,
        build_set_plan_payload_fn=build_set_plan_payload_fn,
        resolve_stopwords_path_fn=resolve_stopwords_path_fn,
        check_rulegen_resources=False,
    )
    preview_payload = _build_rebalance_preview_payload(
        **context,
        build_seed_candidates_fn=build_seed_candidates_fn,
    )
    preview_payload.pop("_rebalance_plan", None)
    return preview_payload


def apply_srs_rebalance(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., SrsSettings],
    ensure_store_fn: Callable[..., SrsStore],
    count_items_for_pair_fn: Callable[..., int],
    build_set_plan_payload_fn: Callable[..., dict[str, object]],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    build_seed_candidates_fn: Callable[..., list[SeedWord]],
    run_rulegen_for_pair_fn: Callable[..., tuple[SrsStore, RulegenOutput]],
    write_rulegen_outputs_fn: Callable[..., None],
    update_status_fn: Callable[..., None],
) -> dict[str, object]:
    context = _prepare_rebalance_context(
        paths=paths,
        config=config,
        resolve_pair_set_top_n_fn=resolve_pair_set_top_n_fn,
        resolve_pair_resources_fn=resolve_pair_resources_fn,
        ensure_pair_requirements_fn=ensure_pair_requirements_fn,
        resolve_profile_id_fn=resolve_profile_id_fn,
        ensure_settings_fn=ensure_settings_fn,
        ensure_store_fn=ensure_store_fn,
        count_items_for_pair_fn=count_items_for_pair_fn,
        build_set_plan_payload_fn=build_set_plan_payload_fn,
        resolve_stopwords_path_fn=resolve_stopwords_path_fn,
        check_rulegen_resources=True,
    )
    preview_payload = _build_rebalance_preview_payload(
        **context,
        build_seed_candidates_fn=build_seed_candidates_fn,
    )
    plan_payload = deepcopy(preview_payload["plan"])
    plan_payload["execution_mode"] = "rebalance_apply"
    preview_payload["plan"] = plan_payload
    rebalance_plan = preview_payload.pop("_rebalance_plan", None)
    if rebalance_plan is None or preview_payload["plan"].get("can_execute") is not True:
        preview_payload["applied"] = False
        preview_payload["rulegen"] = None
        preview_payload["inventory"] = {
            "path": str(context["inventory_path"]),
            "exists": context["inventory_path"].exists(),
            "active_items_for_pair": len(context["active_item_ids_before"]),
            "source": context["inventory_source"],
            "updated_at": None,
        }
        return preview_payload

    inventory_changed = (
        tuple(rebalance_plan.proposed_active_item_ids)
        != tuple(rebalance_plan.active_item_ids_before)
        or context["inventory_source"] != "inventory"
    )
    activation_payloads = dict(getattr(rebalance_plan, "activation_payloads", {}) or {})
    updated_store = context["store"]
    inserted_items = 0
    for activation_payload in activation_payloads.values():
        if str(activation_payload.get("source_kind") or "") != SOURCE_KIND_NEW_SEED:
            continue
        inserted_items += 1
        updated_store = upsert_item(
            updated_store,
            _build_new_seed_item(activation_payload),
        )

    inventory_updated_at = None
    published_rulegen = None
    applied = bool(inventory_changed or inserted_items)
    if applied:
        inventory_updated_at = now_utc().isoformat()
        updated_inventory = set_active_item_ids(
            context["inventory"],
            pair=context["pair"],
            active_item_ids=rebalance_plan.proposed_active_item_ids,
            last_rebalanced_at=inventory_updated_at,
        )
        save_srs_store(updated_store, paths.srs_store_path_for(context["profile_id"]))
        save_srs_inventory(updated_inventory, context["inventory_path"])
        effective_rulegen_tuning = resolve_rulegen_tuning(context["pair"])
        _rulegen_store, rulegen_output = run_rulegen_for_pair_fn(
            paths=paths,
            pair=context["pair"],
            profile_id=context["profile_id"],
            store=updated_store,
            settings=context["settings"],
            jmdict_path=context["resolved_jmdict_path"],
            translation_dict_path=context["resolved_translation_dict_path"],
            rulegen_config=RulegenConfig(
                language_pair=context["pair"],
                confidence_threshold=effective_rulegen_tuning.confidence_threshold,
                max_definitions_per_target=effective_rulegen_tuning.max_definitions_per_target,
                max_rules_per_target=effective_rulegen_tuning.max_rules_per_target,
                semantic_demotion_scale=effective_rulegen_tuning.semantic_demotion_scale,
                include_variants=effective_rulegen_tuning.include_variants,
                allow_multiword_glosses=effective_rulegen_tuning.allow_multiword_glosses,
                scoring=effective_rulegen_tuning.scoring,
                reverse_check=effective_rulegen_tuning.reverse_check,
            ),
            active_item_ids=rebalance_plan.proposed_active_item_ids,
            initialize_if_empty=False,
            persist_store=False,
        )
        write_rulegen_outputs_fn(
            paths=paths,
            pair=context["pair"],
            profile_id=context["profile_id"],
            rules=rulegen_output.rules,
            snapshot=rulegen_output.snapshot,
        )
        update_status_fn(
            paths=paths,
            profile_id=context["profile_id"],
            pair=context["pair"],
            rule_count=len(rulegen_output.rules),
            target_count=rulegen_output.target_count,
            error=None,
        )
        published_rulegen = {
            "published": True,
            "targets": rulegen_output.target_count,
            "rules": len(rulegen_output.rules),
            "snapshot_path": str(
                paths.snapshot_path(context["pair"], profile_id=context["profile_id"])
            ),
            "ruleset_path": str(
                paths.ruleset_path(context["pair"], profile_id=context["profile_id"])
            ),
        }
    preview_payload["applied"] = applied
    preview_payload["inserted_items"] = inserted_items
    preview_payload["total_items_for_pair"] = count_items_for_pair_fn(
        updated_store, context["pair"]
    )
    preview_payload["inventory"] = {
        "path": str(context["inventory_path"]),
        "exists": bool(applied or context["inventory_path"].exists()),
        "active_items_for_pair": len(rebalance_plan.proposed_active_item_ids),
        "source": context["inventory_source"],
        "updated_at": inventory_updated_at,
    }
    preview_payload["rulegen"] = published_rulegen
    return preview_payload


def _prepare_rebalance_context(
    *,
    paths: HelperPaths,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., SrsSettings],
    ensure_store_fn: Callable[..., SrsStore],
    count_items_for_pair_fn: Callable[..., int],
    build_set_plan_payload_fn: Callable[..., dict[str, object]],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    check_rulegen_resources: bool,
) -> dict[str, object]:
    raw_pair = str(config.pair or "").strip()
    if not raw_pair:
        raise ValueError("Missing pair.")
    capability = resolve_pair_capability(raw_pair)
    pair = capability.pair
    resolved_set_top_n = resolve_pair_set_top_n_fn(
        pair=pair,
        requested_top_n=config.set_top_n,
        purpose="bootstrap",
    )
    resolved_jmdict_path, resolved_translation_dict_path, resolved_set_source_db = (
        resolve_pair_resources_fn(
            paths,
            pair=pair,
            jmdict_path=config.jmdict_path,
            translation_dict_path=(
                config.translation_dict_path
                if config.translation_dict_path is not None
                else config.freedict_de_en_path
            ),
            set_source_db=config.set_source_db,
        )
    )
    ensure_pair_requirements_fn(
        pair=pair,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        require_frequency_db=True,
        set_source_db=resolved_set_source_db,
        check_seed_resources=True,
        check_rulegen_resources=check_rulegen_resources,
    )
    if resolved_set_source_db is None:
        raise ValueError(f"Missing frequency source DB for pair '{pair}'.")

    profile_id = resolve_profile_id_fn(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    settings = ensure_settings_fn(paths, persist_missing=True)
    store = ensure_store_fn(paths, profile_id=profile_id, persist_missing=True)
    inventory_path = paths.srs_inventory_path_for(profile_id)
    inventory = load_srs_inventory(inventory_path) if inventory_path.exists() else SrsInventory()
    active_item_ids_before, inventory_source = resolve_active_item_ids(
        store=store,
        pair=pair,
        inventory=inventory if inventory_path.exists() else None,
    )
    existing_items_for_pair = count_items_for_pair_fn(store, pair)
    stopwords_path = resolve_stopwords_path_fn(paths, pair=pair)
    signal_summary = summarize_signal_events(
        paths.srs_signal_queue_path_for(profile_id),
        pair=pair,
    )
    max_active_items = _resolve_max_active_items(config, settings)
    plan_payload = build_set_plan_payload_fn(
        pair=pair,
        strategy=config.strategy,
        objective=config.objective,
        set_top_n=resolved_set_top_n,
        initial_active_count=max_active_items,
        max_active_items_hint=max_active_items,
        replace_pair=False,
        trigger=config.trigger,
        existing_items_for_pair=existing_items_for_pair,
        profile_context=config.profile_context,
        signal_summary=signal_summary,
        policy_notes=(),
    )
    return {
        "pair": pair,
        "profile_id": profile_id,
        "settings": settings,
        "store": store,
        "inventory": inventory,
        "inventory_path": inventory_path,
        "inventory_source": inventory_source,
        "active_item_ids_before": tuple(active_item_ids_before),
        "existing_items_for_pair": existing_items_for_pair,
        "resolved_set_top_n": resolved_set_top_n,
        "resolved_jmdict_path": resolved_jmdict_path,
        "resolved_translation_dict_path": resolved_translation_dict_path,
        "resolved_set_source_db": resolved_set_source_db,
        "stopwords_path": stopwords_path,
        "signal_summary": signal_summary,
        "plan_payload": plan_payload,
        "max_active_items": max_active_items,
        "profile_context": config.profile_context,
    }


def _build_rebalance_preview_payload(
    *,
    pair: str,
    profile_id: str,
    settings: SrsSettings,
    store: SrsStore,
    inventory: SrsInventory,
    inventory_path: Path,
    inventory_source: str,
    active_item_ids_before: Sequence[str],
    existing_items_for_pair: int,
    resolved_set_top_n: int,
    resolved_jmdict_path: Optional[Path],
    resolved_translation_dict_path: Optional[Path],
    resolved_set_source_db: Path,
    stopwords_path: Optional[Path],
    signal_summary: Mapping[str, object],
    plan_payload: Mapping[str, object],
    max_active_items: int,
    profile_context: Optional[Mapping[str, object]],
    build_seed_candidates_fn: Callable[..., list[SeedWord]],
) -> dict[str, object]:
    payload = {
        "pair": pair,
        "profile_id": profile_id,
        "set_top_n": resolved_set_top_n,
        "max_active_items": max_active_items,
        "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        "set_source_db": str(resolved_set_source_db),
        "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
        "translation_dict_path": (
            str(resolved_translation_dict_path) if resolved_translation_dict_path else None
        ),
        "existing_items_for_pair": existing_items_for_pair,
        "signal_summary": dict(signal_summary),
        "plan": dict(plan_payload),
        "summary": {
            "active_count_before": len(tuple(active_item_ids_before)),
            "protected_count": 0,
            "swappable_count": 0,
            "candidate_slots_available": 0,
            "proposed_keep_count": 0,
            "proposed_park_count": 0,
            "proposed_activate_count": 0,
            "active_count_after": len(tuple(active_item_ids_before)),
        },
        "protected_items": [],
        "swappable_items": [],
        "proposed_parks": [],
        "proposed_activations": [],
        "diagnostics": {
            "inventory_source": inventory_source,
            "inventory_path": str(inventory_path),
            "inventory_exists": inventory_path.exists(),
        },
    }
    if not active_item_ids_before:
        blocked_plan = dict(payload["plan"])
        blocked_plan["can_execute"] = False
        notes = list(blocked_plan.get("notes") or [])
        note = "No active inventory exists for this pair yet. Initialize S before rebalancing."
        if note not in notes:
            notes.append(note)
        blocked_plan["notes"] = notes
        payload["plan"] = blocked_plan
        return payload

    if payload["plan"].get("can_execute") is not True:
        return payload

    selection = build_seed_candidates_fn(
        frequency_db=resolved_set_source_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=resolved_set_top_n,
            jmdict_path=resolved_jmdict_path,
            stopwords_path=stopwords_path,
            require_jmdict=resolve_pair_capability(pair).requires_jmdict_for_seed,
        ),
    )
    rebalance_plan = build_rebalance_plan(
        store=store,
        pair=pair,
        inventory=inventory if inventory_path.exists() else None,
        candidates=selection,
        profile_context=profile_context,
        target_active_count=max_active_items,
    )
    plan_with_notes = dict(payload["plan"])
    if inventory_source == "store_fallback":
        notes = list(plan_with_notes.get("notes") or [])
        note = (
            "Active inventory manifest is missing for this pair; using current store membership "
            "as a compatibility fallback."
        )
        if note not in notes:
            notes.append(note)
        plan_with_notes["notes"] = notes
    payload["plan"] = plan_with_notes
    payload.update(rebalance_plan.to_dict())
    payload["pair_policy"] = pair_policy_to_dict(resolve_srs_pair_policy(pair))
    payload["set_top_n"] = resolved_set_top_n
    payload["max_active_items"] = max_active_items
    payload["stopwords_path"] = str(stopwords_path) if stopwords_path else None
    payload["set_source_db"] = str(resolved_set_source_db)
    payload["jmdict_path"] = str(resolved_jmdict_path) if resolved_jmdict_path else None
    payload["translation_dict_path"] = (
        str(resolved_translation_dict_path) if resolved_translation_dict_path else None
    )
    payload["existing_items_for_pair"] = existing_items_for_pair
    payload["signal_summary"] = dict(signal_summary)
    payload["_rebalance_plan"] = rebalance_plan
    return payload


def _resolve_max_active_items(config, settings: SrsSettings) -> int:
    requested = getattr(config, "max_active_items", None)
    if requested is not None:
        return max(1, int(requested))
    return max(1, int(settings.max_active_items))


def _build_new_seed_item(payload: Mapping[str, object]) -> SrsItem:
    language_pair = str(payload.get("language_pair", "") or "").strip()
    lemma = str(payload.get("lemma", "") or "").strip()
    source_type = normalize_source_type(payload.get("source_type") or SOURCE_FREQUENCY_LIST)
    return SrsItem(
        item_id=str(payload.get("item_id", "") or "").strip(),
        lemma=lemma,
        language_pair=language_pair,
        source_type=source_type,
        confidence=_safe_optional_float(payload.get("confidence")),
        word_package=normalize_word_package(
            payload.get("word_package"),
            fallback_surface=lemma,
            fallback_language_tag=resolve_language_tag_from_pair(language_pair),
            fallback_provider=source_type or "srs",
        ),
    )


def _safe_optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None
