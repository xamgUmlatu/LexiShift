from __future__ import annotations

from pathlib import Path
from typing import Callable

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.pair_resources import resolve_pair_frequency_pack
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import (
    RulegenConfig,
    RulegenOutput,
    SetInitializationConfig,
    SetInitializationReport,
)
from lexishift_core.helper.use_cases.rule_availability import (
    reconcile_active_items_without_enabled_rules,
)
from lexishift_core.rulegen.tuning import resolve_rulegen_tuning
from lexishift_core.srs import (
    SrsInventory,
    SrsSettings,
    SrsStore,
    load_srs_inventory,
    merge_active_item_ids,
    resolve_active_item_ids,
    save_srs_inventory,
    save_srs_store,
    set_active_item_ids,
    srs_item_is_active,
)
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.pos_overlay import (
    pos_overlay_resource_payload,
    resolve_pair_pos_overlay,
)
from lexishift_core.srs.set_policy import resolve_set_sizing_policy
from lexishift_core.srs.signal_queue import summarize_signal_events
from lexishift_core.srs.source import SOURCE_INITIAL_SET
from lexishift_core.srs.store_ops import build_item_id
from lexishift_core.srs.time import now_utc

MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS = 3


def initialize_srs_set(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int | None],
    resolve_pair_initial_active_count_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., SrsSettings],
    ensure_store_fn: Callable[..., SrsStore],
    count_items_for_pair_fn: Callable[..., int],
    build_set_plan_payload_fn: Callable[..., dict[str, object]],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    initialize_store_from_frequency_list_with_report_fn: Callable[
        ...,
        tuple[SrsStore, SetInitializationReport],
    ],
    run_rulegen_for_pair_fn: Callable[..., tuple[SrsStore, RulegenOutput]],
    write_rulegen_outputs_fn: Callable[..., None],
    update_status_fn: Callable[..., None],
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
    resolved_initial_active_count = resolve_pair_initial_active_count_fn(
        pair=pair,
        requested_count=config.initial_active_count,
    )
    resolved_jmdict_path, resolved_translation_dict_path, resolved_set_source_db = (
        resolve_pair_resources_fn(
            paths,
            pair=pair,
            jmdict_path=config.jmdict_path,
            translation_dict_path=getattr(config, "translation_dict_path", None),
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
        check_rulegen_resources=True,
    )
    if resolved_set_source_db is None:
        raise ValueError(f"Missing frequency source DB for pair '{pair}'.")
    resolved_frequency_pack = resolve_pair_frequency_pack(
        paths,
        pair=pair,
        set_source_db=resolved_set_source_db,
    )
    resolved_pos_overlay = resolve_pair_pos_overlay(paths, pair=pair)
    frequency_source_label = resolved_frequency_pack.provider if resolved_frequency_pack else None
    pos_overlay_payload = pos_overlay_resource_payload(resolved_pos_overlay)

    profile_id = resolve_profile_id_fn(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    settings = ensure_settings_fn(paths, persist_missing=True)
    store = ensure_store_fn(paths, profile_id=profile_id, persist_missing=True)
    inventory_path = paths.srs_inventory_path_for(profile_id)
    inventory_exists = inventory_path.exists()
    inventory = load_srs_inventory(inventory_path) if inventory_exists else SrsInventory()
    existing_active_item_ids, inventory_source = resolve_active_item_ids(
        store=store,
        pair=pair,
        inventory=inventory if inventory_exists else None,
    )
    before_pair_count = count_items_for_pair_fn(store, pair)
    sizing_policy = resolve_set_sizing_policy(
        bootstrap_top_n=(
            config.bootstrap_top_n if config.bootstrap_top_n is not None else resolved_set_top_n
        ),
        initial_active_count=resolved_initial_active_count,
        max_active_items_hint=config.max_active_items_hint,
    )
    stopwords_path = resolve_stopwords_path_fn(paths, pair=pair)
    signal_summary = summarize_signal_events(
        paths.srs_signal_queue_path_for(profile_id),
        pair=pair,
    )
    plan_payload = build_set_plan_payload_fn(
        pair=pair,
        strategy=config.strategy,
        objective=config.objective,
        set_top_n=sizing_policy.bootstrap_top_n_effective,
        initial_active_count=sizing_policy.initial_active_count_effective,
        max_active_items_hint=sizing_policy.max_active_items_hint or 0,
        replace_pair=config.replace_pair,
        trigger=config.trigger,
        existing_items_for_pair=before_pair_count,
        profile_context=config.profile_context,
        signal_summary=signal_summary,
        policy_notes=sizing_policy.notes,
    )

    can_execute = bool(plan_payload.get("can_execute"))
    execution_mode = str(plan_payload.get("execution_mode", "planner_only"))
    if not can_execute or execution_mode not in {"frequency_bootstrap", "profile_bootstrap"}:
        return {
            "pair": pair,
            "profile_id": profile_id,
            "set_top_n": sizing_policy.bootstrap_top_n_effective,
            "bootstrap_top_n": sizing_policy.bootstrap_top_n_effective,
            "initial_active_count": sizing_policy.initial_active_count_effective,
            "max_active_items_hint": sizing_policy.max_active_items_hint,
            "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
            "source_type": SOURCE_INITIAL_SET,
            "replace_pair": config.replace_pair,
            "added_items": 0,
            "total_items_for_pair": before_pair_count,
            "store_path": str(paths.srs_store_path_for(profile_id)),
            "stopwords_path": str(stopwords_path) if stopwords_path else None,
            **pos_overlay_payload,
            "applied": False,
            "plan": plan_payload,
            "signal_summary": signal_summary,
        }

    base_store = store
    if config.replace_pair:
        retained = tuple(item for item in store.items if item.language_pair != pair)
        base_store = SrsStore(items=retained, version=store.version)

    updated_store, init_report = initialize_store_from_frequency_list_with_report_fn(
        base_store,
        config=SetInitializationConfig(
            frequency_db=resolved_set_source_db,
            jmdict_path=resolved_jmdict_path,
            top_n=sizing_policy.bootstrap_top_n_effective,
            initial_active_count=sizing_policy.initial_active_count_effective,
            language_pair=pair,
            stopwords_path=stopwords_path,
            require_jmdict=capability.requires_jmdict_for_seed,
            source_label=frequency_source_label,
            pos_overlay_path=resolved_pos_overlay.path if resolved_pos_overlay else None,
            seed_cache_dir=paths.srs_seed_frontier_cache_dir(),
            strategy=str(config.strategy or "frequency_bootstrap"),
            profile_context=config.profile_context,
        ),
    )
    save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
    initial_active_item_ids = tuple(
        build_item_id(pair, str(lemma).strip())
        for lemma in getattr(init_report, "initial_active_preview", ()) or ()
        if str(lemma).strip()
    )
    active_available_ids = {
        item.item_id
        for item in updated_store.items
        if item.language_pair == pair and srs_item_is_active(item)
    }
    initial_active_item_ids = tuple(
        item_id for item_id in initial_active_item_ids if item_id in active_available_ids
    )
    active_item_ids = (
        initial_active_item_ids
        if config.replace_pair
        else merge_active_item_ids(
            tuple(
                item_id for item_id in existing_active_item_ids if item_id in active_available_ids
            ),
            initial_active_item_ids,
        )
    )
    inventory_updated_at = now_utc().isoformat()
    updated_inventory = set_active_item_ids(
        inventory,
        pair=pair,
        active_item_ids=active_item_ids,
        last_initialized_at=inventory_updated_at,
    )
    save_srs_inventory(updated_inventory, inventory_path)

    effective_rulegen_tuning = resolve_rulegen_tuning(pair)
    rulegen_config = RulegenConfig(
        language_pair=pair,
        confidence_threshold=effective_rulegen_tuning.confidence_threshold,
        max_definitions_per_target=effective_rulegen_tuning.max_definitions_per_target,
        max_rules_per_target=effective_rulegen_tuning.max_rules_per_target,
        semantic_demotion_scale=effective_rulegen_tuning.semantic_demotion_scale,
        enable_source_frequency_prior=effective_rulegen_tuning.source_frequency_prior_enabled,
        include_variants=effective_rulegen_tuning.include_variants,
        allow_multiword_glosses=effective_rulegen_tuning.allow_multiword_glosses,
        scoring=effective_rulegen_tuning.scoring,
        reverse_check=effective_rulegen_tuning.reverse_check,
        enable_exact_gloss_demotions=(effective_rulegen_tuning.enable_exact_gloss_demotions),
    )

    target_active_count = len(active_item_ids)
    rule_availability_reconciliations = []
    refill_attempts: list[dict[str, object]] = []

    _updated_store, rulegen_output = run_rulegen_for_pair_fn(
        paths=paths,
        pair=pair,
        profile_id=profile_id,
        store=updated_store,
        settings=settings,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        rulegen_config=rulegen_config,
        active_item_ids=active_item_ids,
        semantic_context_targets=_active_lemmas_for_item_ids(
            updated_store,
            pair=pair,
            active_item_ids=active_item_ids,
        ),
        initialize_if_empty=False,
        persist_store=False,
    )
    (
        updated_store,
        updated_inventory,
        rule_availability_reconciliation,
    ) = reconcile_active_items_without_enabled_rules(
        store=updated_store,
        inventory=updated_inventory,
        pair=pair,
        active_item_ids=active_item_ids,
        rules=rulegen_output.rules,
        last_initialized_at=inventory_updated_at,
    )
    rule_availability_reconciliations.append(rule_availability_reconciliation)
    if rule_availability_reconciliation.changed:
        active_item_ids = rule_availability_reconciliation.active_item_ids_after
        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
        save_srs_inventory(updated_inventory, inventory_path)
    refill_attempt = 0
    while (
        len(active_item_ids) < target_active_count
        and refill_attempt < MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS
    ):
        missing_count = target_active_count - len(active_item_ids)
        blocked_refill_lemmas = set(
            _active_lemmas_for_item_ids(
                updated_store,
                pair=pair,
                active_item_ids=active_item_ids,
            )
        )
        for reconciliation in rule_availability_reconciliations:
            blocked_refill_lemmas.update(str(lemma) for lemma in reconciliation.discarded_lemmas)
        refill_store, refill_report = initialize_store_from_frequency_list_with_report_fn(
            updated_store,
            config=SetInitializationConfig(
                frequency_db=resolved_set_source_db,
                jmdict_path=resolved_jmdict_path,
                top_n=sizing_policy.bootstrap_top_n_effective,
                initial_active_count=missing_count,
                language_pair=pair,
                stopwords_path=stopwords_path,
                require_jmdict=capability.requires_jmdict_for_seed,
                source_label=frequency_source_label,
                pos_overlay_path=resolved_pos_overlay.path if resolved_pos_overlay else None,
                seed_cache_dir=paths.srs_seed_frontier_cache_dir(),
                strategy=str(config.strategy or "frequency_bootstrap"),
                profile_context=config.profile_context,
                blocked_lemmas=tuple(sorted(blocked_refill_lemmas)),
            ),
        )
        refill_preview_lemmas = tuple(
            str(lemma or "").strip()
            for lemma in getattr(refill_report, "initial_active_preview", ()) or ()
            if str(lemma or "").strip() and str(lemma or "").strip() not in blocked_refill_lemmas
        )
        refill_item_ids = tuple(
            item_id
            for item_id in _item_ids_for_lemmas(
                refill_store,
                pair=pair,
                lemmas=refill_preview_lemmas,
            )
            if item_id not in active_item_ids
        )
        refill_attempt += 1
        refill_attempts.append(
            {
                "attempt": refill_attempt,
                "requested_count": missing_count,
                "admitted_count": int(getattr(refill_report, "admitted_count", 0) or 0),
                "added_item_ids": list(refill_item_ids),
                "added_lemmas": list(
                    _active_lemmas_for_item_ids(
                        refill_store,
                        pair=pair,
                        active_item_ids=refill_item_ids,
                    )
                ),
                "blocked_lemmas": sorted(blocked_refill_lemmas),
            }
        )
        if not refill_item_ids:
            break
        updated_store = refill_store
        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
        active_item_ids = merge_active_item_ids(active_item_ids, refill_item_ids)
        updated_inventory = set_active_item_ids(
            updated_inventory,
            pair=pair,
            active_item_ids=active_item_ids,
            last_initialized_at=inventory_updated_at,
        )
        save_srs_inventory(updated_inventory, inventory_path)
        _updated_store, rulegen_output = run_rulegen_for_pair_fn(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            store=updated_store,
            settings=settings,
            jmdict_path=resolved_jmdict_path,
            translation_dict_path=resolved_translation_dict_path,
            rulegen_config=rulegen_config,
            active_item_ids=active_item_ids,
            semantic_context_targets=_active_lemmas_for_item_ids(
                updated_store,
                pair=pair,
                active_item_ids=active_item_ids,
            ),
            initialize_if_empty=False,
            persist_store=False,
        )
        (
            updated_store,
            updated_inventory,
            rule_availability_reconciliation,
        ) = reconcile_active_items_without_enabled_rules(
            store=updated_store,
            inventory=updated_inventory,
            pair=pair,
            active_item_ids=active_item_ids,
            rules=rulegen_output.rules,
            last_initialized_at=inventory_updated_at,
        )
        rule_availability_reconciliations.append(rule_availability_reconciliation)
        if rule_availability_reconciliation.changed:
            active_item_ids = rule_availability_reconciliation.active_item_ids_after
            save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
            save_srs_inventory(updated_inventory, inventory_path)
    write_rulegen_outputs_fn(
        paths=paths,
        pair=pair,
        profile_id=profile_id,
        rules=rulegen_output.rules,
        snapshot=rulegen_output.snapshot,
        semantic_inventory=getattr(rulegen_output, "semantic_inventory", None),
    )
    update_status_fn(
        paths=paths,
        profile_id=profile_id,
        pair=pair,
        rule_count=len(rulegen_output.rules),
        target_count=rulegen_output.target_count,
        error=None,
    )

    after_pair_count = count_items_for_pair_fn(updated_store, pair)
    added_items = max(0, after_pair_count - (0 if config.replace_pair else before_pair_count))
    return {
        "pair": pair,
        "profile_id": profile_id,
        "set_top_n": sizing_policy.bootstrap_top_n_effective,
        "bootstrap_top_n": sizing_policy.bootstrap_top_n_effective,
        "initial_active_count": sizing_policy.initial_active_count_effective,
        "max_active_items_hint": sizing_policy.max_active_items_hint,
        "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
        "source_type": SOURCE_INITIAL_SET,
        "replace_pair": config.replace_pair,
        "added_items": added_items,
        "total_items_for_pair": after_pair_count,
        "store_path": str(paths.srs_store_path_for(profile_id)),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        **pos_overlay_payload,
        "bootstrap_diagnostics": {
            "selected_count": init_report.selected_count,
            "selected_unique_count": init_report.selected_unique_count,
            "admitted_count": init_report.admitted_count,
            "inserted_count": init_report.inserted_count,
            "updated_count": init_report.updated_count,
            "selected_preview": list(init_report.selected_preview),
            "initial_active_preview": list(init_report.initial_active_preview),
            "admission_weight_profile": dict(
                getattr(init_report, "admission_weight_profile", {}) or {}
            ),
            "initial_active_weight_preview": list(
                getattr(init_report, "initial_active_weight_preview", ()) or ()
            ),
            "selection_strategy": str(
                getattr(init_report, "selection_strategy", None) or config.strategy
            ),
            "selection_policy": getattr(init_report, "selection_policy", None),
            "selection_seed": getattr(init_report, "selection_seed", None),
            "selector_version": getattr(init_report, "selector_version", None),
        },
        "inventory": {
            "path": str(inventory_path),
            "exists": True,
            "active_items_for_pair": len(active_item_ids),
            "source": "initialized",
            "backfilled_from_store": bool(
                not config.replace_pair
                and inventory_source == "store_fallback"
                and bool(existing_active_item_ids)
            ),
            "updated_at": inventory_updated_at,
        },
        "rule_availability_reconciliation": _rule_availability_reconciliation_payload(
            rule_availability_reconciliations
        ),
        "rule_availability_refill": {
            "attempted": bool(refill_attempts),
            "attempt_count": len(refill_attempts),
            "max_attempts": MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS,
            "target_active_count": target_active_count,
            "active_count_after": len(active_item_ids),
            "shortfall_count": max(0, target_active_count - len(active_item_ids)),
            "attempts": refill_attempts,
        },
        "rulegen": {
            "published": True,
            "targets": rulegen_output.target_count,
            "rules": len(rulegen_output.rules),
            "snapshot_path": str(paths.snapshot_path(pair, profile_id=profile_id)),
            "ruleset_path": str(paths.ruleset_path(pair, profile_id=profile_id)),
            "publication_manifest_path": str(
                paths.publication_manifest_path(pair, profile_id=profile_id)
            ),
            "semantic_inventory_path": (
                str(paths.semantic_inventory_path(pair, profile_id=profile_id))
                if getattr(rulegen_output, "semantic_inventory", None) is not None
                else None
            ),
        },
        "applied": True,
        "plan": plan_payload,
        "signal_summary": signal_summary,
    }


def _active_lemmas_for_item_ids(
    store: SrsStore,
    *,
    pair: str,
    active_item_ids: tuple[str, ...],
) -> tuple[str, ...]:
    items_by_id = {
        str(item.item_id or "").strip(): item
        for item in store.items
        if item.language_pair == pair and str(item.item_id or "").strip()
    }
    lemmas: list[str] = []
    seen: set[str] = set()
    for item_id in active_item_ids:
        item = items_by_id.get(str(item_id or "").strip())
        if item is None or not srs_item_is_active(item):
            continue
        lemma = str(item.lemma or "").strip()
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        lemmas.append(lemma)
    return tuple(lemmas)


def _item_ids_for_lemmas(
    store: SrsStore,
    *,
    pair: str,
    lemmas: tuple[str, ...],
) -> tuple[str, ...]:
    available_ids = {
        item.item_id
        for item in store.items
        if item.language_pair == pair and srs_item_is_active(item)
    }
    item_ids: list[str] = []
    seen: set[str] = set()
    for lemma in lemmas:
        item_id = build_item_id(pair, str(lemma or "").strip())
        if not item_id or item_id in seen or item_id not in available_ids:
            continue
        seen.add(item_id)
        item_ids.append(item_id)
    return tuple(item_ids)


def _rule_availability_reconciliation_payload(reconciliations: list[object]) -> dict[str, object]:
    if not reconciliations:
        return {
            "reason": "no_enabled_rules",
            "changed": False,
            "active_count_before": 0,
            "active_count_after": 0,
            "discarded_count": 0,
            "discarded_item_ids": [],
            "discarded_lemmas": [],
            "enabled_rule_lemma_count": 0,
        }
    first = reconciliations[0]
    last = reconciliations[-1]
    discarded_item_ids: list[str] = []
    discarded_lemmas: list[str] = []
    for reconciliation in reconciliations:
        discarded_item_ids.extend(str(item_id) for item_id in reconciliation.discarded_item_ids)
        discarded_lemmas.extend(str(lemma) for lemma in reconciliation.discarded_lemmas)
    return {
        "reason": str(getattr(first, "reason", "no_enabled_rules")),
        "changed": bool(discarded_item_ids),
        "active_count_before": len(getattr(first, "active_item_ids_before", ()) or ()),
        "active_count_after": len(getattr(last, "active_item_ids_after", ()) or ()),
        "discarded_count": len(discarded_item_ids),
        "discarded_item_ids": discarded_item_ids,
        "discarded_lemmas": discarded_lemmas,
        "enabled_rule_lemma_count": len(getattr(last, "enabled_rule_lemmas", ()) or ()),
    }
