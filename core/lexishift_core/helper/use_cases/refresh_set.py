from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, cast

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.pair_resources import resolve_pair_frequency_pack
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig, RulegenOutput
from lexishift_core.helper.use_cases.rule_availability import (
    RuleAvailabilityReconciliation,
    reconcile_active_items_without_enabled_rules,
)
from lexishift_core.rulegen.tuning import resolve_rulegen_tuning
from lexishift_core.srs import (
    SrsInventory,
    SrsSettings,
    SrsStore,
    load_srs_inventory,
    merge_active_item_ids,
    plan_active_rotation_capacity_release,
    resolve_active_item_ids,
    save_srs_inventory,
    save_srs_store,
    set_active_item_ids,
    srs_item_is_active,
)
from lexishift_core.srs.admission_refresh import (
    AdmissionRefreshPolicy,
    admission_refresh_result_to_dict,
    apply_admission_refresh,
    preview_browsing_admission_refresh,
)
from lexishift_core.srs.admission_suppression import (
    active_suppressed_lemmas,
    load_admission_suppression_store,
    prune_expired_suppression_entries,
    save_admission_suppression_store,
)
from lexishift_core.srs.browsing_admission import load_browsing_signal_store
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.pos_overlay import (
    pos_overlay_resource_payload,
    resolve_pair_pos_overlay,
)
from lexishift_core.srs.profile_bootstrap import (
    DEFAULT_PROFILE_BOOTSTRAP_POLICY,
    FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
    score_seed_words_for_frontier_gaussian_hybrid_profile,
)
from lexishift_core.srs.seed import SeedSelectionConfig, SeedWord, seed_to_selector_candidates
from lexishift_core.srs.selector import SelectorCandidate, SelectorConfig
from lexishift_core.srs.signal_queue import load_signal_events
from lexishift_core.srs.set_strategy import (
    STRATEGY_FREQUENCY_BOOTSTRAP,
    STRATEGY_PROFILE_BOOTSTRAP,
    STRATEGY_PROFILE_GROWTH,
    normalize_set_strategy,
)
from lexishift_core.srs.store_ops import build_item_id
from lexishift_core.srs.time import now_utc


MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS = 3


def refresh_srs_set(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_feedback_window_size_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., SrsSettings],
    ensure_store_fn: Callable[..., SrsStore],
    count_items_for_pair_fn: Callable[..., int],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    build_seed_candidates_fn: Callable[..., list[SeedWord]],
    run_rulegen_for_pair_fn: Callable[..., tuple[object, RulegenOutput]],
    write_rulegen_outputs_fn: Callable[..., None],
    update_status_fn: Callable[..., None],
) -> dict[str, object]:
    raw_pair = str(config.pair or "").strip()
    if not raw_pair:
        raise ValueError("Missing pair.")
    capability = resolve_pair_capability(raw_pair)
    pair = capability.pair
    effective_set_top_n = resolve_pair_set_top_n_fn(
        pair=pair,
        requested_top_n=config.set_top_n,
        purpose="refresh",
    )
    effective_feedback_window_size = resolve_pair_feedback_window_size_fn(
        pair=pair,
        requested_size=config.feedback_window_size,
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
    active_item_ids_before, inventory_source = resolve_active_item_ids(
        store=store,
        pair=pair,
        inventory=inventory if inventory_exists else None,
    )
    max_active_items_for_release = max(
        1,
        int(config.max_active_items)
        if config.max_active_items is not None
        else int(settings.max_active_items),
    )
    active_rotation_release = plan_active_rotation_capacity_release(
        store=store,
        pair=pair,
        active_item_ids=active_item_ids_before,
        max_active_items=max_active_items_for_release,
    )
    active_item_ids_for_refresh = tuple(active_rotation_release.active_item_ids_after)
    suppression_path = paths.srs_admission_suppression_store_path_for(profile_id)
    suppression_store = load_admission_suppression_store(suppression_path)
    pruned_suppression_store = (
        prune_expired_suppression_entries(suppression_store)
        if suppression_path.exists()
        else suppression_store
    )
    if (
        suppression_path.exists()
        and len(pruned_suppression_store.entries) != len(suppression_store.entries)
        and config.persist_store
    ):
        save_admission_suppression_store(pruned_suppression_store, suppression_path)
    suppressed_lemmas = active_suppressed_lemmas(pruned_suppression_store, pair=pair)
    before_pair_count = count_items_for_pair_fn(store, pair)
    stopwords_path = resolve_stopwords_path_fn(paths, pair=pair)
    selection = build_seed_candidates_fn(
        frequency_db=resolved_set_source_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=effective_set_top_n,
            jmdict_path=resolved_jmdict_path,
            stopwords_path=stopwords_path,
            require_jmdict=capability.requires_jmdict_for_seed,
            source_label=resolved_frequency_pack.provider if resolved_frequency_pack else None,
            pos_overlay_path=resolved_pos_overlay.path if resolved_pos_overlay else None,
            cache_dir=paths.srs_seed_frontier_cache_dir(),
        ),
    )
    semantic_context_targets = tuple(
        dict.fromkeys(
            str(getattr(seed, "lemma", "")).strip()
            for seed in selection
            if str(getattr(seed, "lemma", "")).strip()
        )
    )
    strategy_requested = str(
        getattr(config, "strategy", STRATEGY_PROFILE_GROWTH) or STRATEGY_PROFILE_GROWTH
    ).strip()
    strategy_effective = _resolve_refresh_strategy(strategy_requested)
    selector_config: Optional[SelectorConfig] = None
    profile_growth_diagnostics: Mapping[str, object] = {}
    if strategy_effective == STRATEGY_PROFILE_GROWTH:
        selector_candidates, profile_growth_diagnostics = _profile_growth_selector_candidates(
            selection,
            profile_context=getattr(config, "profile_context", None),
        )
        selector_config = DEFAULT_PROFILE_BOOTSTRAP_POLICY.selector_config
    else:
        selector_candidates = seed_to_selector_candidates(selection)
    signal_events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    allowed_pos = _normalize_allowed_pos(getattr(config, "allowed_pos", None))
    refresh_policy = AdmissionRefreshPolicy(
        feedback_window_size=effective_feedback_window_size,
        max_active_items_override=config.max_active_items,
        max_new_items_override=config.max_new_items,
        active_item_ids=active_item_ids_for_refresh,
        allowed_pos=allowed_pos or None,
        selector_config=selector_config or AdmissionRefreshPolicy().selector_config,
        blocked_lemmas=set(suppressed_lemmas.keys()) or None,
    )
    updated_store, refresh_result = apply_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        candidates=selector_candidates,
        events=signal_events,
        policy=refresh_policy,
    )
    browsing_store_path = paths.srs_browsing_signal_store_path_for(profile_id, pair)
    browsing_store = load_browsing_signal_store(browsing_store_path)
    browsing_preview = preview_browsing_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        candidates=selector_candidates,
        events=signal_events,
        browsing_store=browsing_store,
        policy=refresh_policy,
        row_limit=10,
    )
    browsing_preview["store_path"] = str(browsing_store_path)
    browsing_preview["store_exists"] = bool(browsing_store_path.exists())
    browsing_preview["selection_strategy_requested"] = strategy_requested
    browsing_preview["selection_strategy_effective"] = strategy_effective
    inventory_updated_at = None
    inventory_payload_source = inventory_source
    inventory_backfilled = False
    active_item_ids = active_item_ids_for_refresh
    if refresh_result.applied:
        admitted_active_item_ids = tuple(
            build_item_id(pair, str(lemma).strip())
            for lemma in refresh_result.selected_lemmas
            if str(lemma).strip()
        )
        active_item_ids = merge_active_item_ids(active_item_ids_before, admitted_active_item_ids)
        if active_rotation_release.released_item_ids:
            active_item_ids = merge_active_item_ids(
                active_item_ids_for_refresh,
                admitted_active_item_ids,
            )
        if config.persist_store:
            save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
            inventory_updated_at = now_utc().isoformat()
            inventory = set_active_item_ids(
                inventory,
                pair=pair,
                active_item_ids=active_item_ids,
                last_refreshed_at=inventory_updated_at,
            )
            save_srs_inventory(inventory, inventory_path)
        inventory_backfilled = inventory_source == "store_fallback"
        inventory_payload_source = "refreshed"
    elif (
        config.persist_store
        and (inventory_source == "store_fallback" or active_rotation_release.released_item_ids)
        and active_item_ids_before
    ):
        inventory_updated_at = now_utc().isoformat()
        inventory = set_active_item_ids(
            inventory,
            pair=pair,
            active_item_ids=active_item_ids,
            last_refreshed_at=inventory_updated_at,
        )
        save_srs_inventory(inventory, inventory_path)
        inventory_backfilled = inventory_source == "store_fallback"
        inventory_payload_source = (
            "active_rotation_released"
            if active_rotation_release.released_item_ids
            else "inventory_backfilled"
        )

    published_rulegen = None
    rule_availability_refill_payload = {
        "attempted": False,
        "attempt_count": 0,
        "max_attempts": MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS,
        "target_active_count": len(active_item_ids),
        "active_count_after": len(active_item_ids),
        "shortfall_count": 0,
        "attempts": [],
    }
    if refresh_result.applied or active_rotation_release.released_item_ids:
        rulegen_config = _rulegen_config_for_pair(pair)
        target_active_count = len(active_item_ids)
        rule_availability_reconciliations: list[RuleAvailabilityReconciliation] = []
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
            semantic_context_targets=semantic_context_targets,
            initialize_if_empty=False,
            persist_store=False,
        )
        if config.persist_store and active_item_ids:
            (
                updated_store,
                inventory,
                rule_availability_reconciliation,
            ) = reconcile_active_items_without_enabled_rules(
                store=updated_store,
                inventory=inventory,
                pair=pair,
                active_item_ids=active_item_ids,
                rules=rulegen_output.rules,
                last_refreshed_at=inventory_updated_at,
            )
            rule_availability_reconciliations.append(rule_availability_reconciliation)
            if rule_availability_reconciliation.changed:
                active_item_ids = rule_availability_reconciliation.active_item_ids_after
                save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
                save_srs_inventory(inventory, inventory_path)
            refill_attempt = 0
            while (
                refresh_result.applied
                and len(active_item_ids) < target_active_count
                and refill_attempt < MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS
            ):
                missing_count = target_active_count - len(active_item_ids)
                blocked_refill_lemmas = set(suppressed_lemmas.keys())
                blocked_refill_lemmas.update(
                    _active_lemmas_for_item_ids(
                        updated_store,
                        pair=pair,
                        active_item_ids=active_item_ids,
                    )
                )
                for reconciliation in rule_availability_reconciliations:
                    blocked_refill_lemmas.update(
                        str(lemma).strip()
                        for lemma in reconciliation.discarded_lemmas
                        if str(lemma).strip()
                    )
                refill_policy = replace(
                    refresh_policy,
                    active_item_ids=active_item_ids,
                    max_new_items_override=missing_count,
                    blocked_lemmas=blocked_refill_lemmas or None,
                )
                refill_store, refill_result = apply_admission_refresh(
                    store=updated_store,
                    settings=settings,
                    pair=pair,
                    candidates=selector_candidates,
                    events=signal_events,
                    policy=refill_policy,
                )
                refill_item_ids = tuple(
                    item_id
                    for item_id in _item_ids_for_lemmas(
                        refill_store,
                        pair=pair,
                        lemmas=tuple(refill_result.selected_lemmas),
                    )
                    if item_id not in active_item_ids
                )
                refill_attempt += 1
                refill_attempts.append(
                    {
                        "attempt": refill_attempt,
                        "requested_count": missing_count,
                        "admitted_count": int(refill_result.admitted_count),
                        "added_item_ids": list(refill_item_ids),
                        "added_lemmas": list(
                            _active_lemmas_for_item_ids(
                                refill_store,
                                pair=pair,
                                active_item_ids=refill_item_ids,
                            )
                        ),
                        "blocked_lemmas": sorted(blocked_refill_lemmas),
                        "reason_code": refill_result.decision.reason_code,
                    }
                )
                if not refill_item_ids:
                    break
                updated_store = refill_store
                save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
                active_item_ids = merge_active_item_ids(active_item_ids, refill_item_ids)
                inventory = set_active_item_ids(
                    inventory,
                    pair=pair,
                    active_item_ids=active_item_ids,
                    last_refreshed_at=inventory_updated_at,
                )
                save_srs_inventory(inventory, inventory_path)
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
                    semantic_context_targets=semantic_context_targets,
                    initialize_if_empty=False,
                    persist_store=False,
                )
                (
                    updated_store,
                    inventory,
                    rule_availability_reconciliation,
                ) = reconcile_active_items_without_enabled_rules(
                    store=updated_store,
                    inventory=inventory,
                    pair=pair,
                    active_item_ids=active_item_ids,
                    rules=rulegen_output.rules,
                    last_refreshed_at=inventory_updated_at,
                )
                rule_availability_reconciliations.append(rule_availability_reconciliation)
                if rule_availability_reconciliation.changed:
                    active_item_ids = rule_availability_reconciliation.active_item_ids_after
                    save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
                    save_srs_inventory(inventory, inventory_path)
            rule_availability_refill_payload = {
                "attempted": bool(refill_attempts),
                "attempt_count": len(refill_attempts),
                "max_attempts": MAX_RULE_AVAILABILITY_REFILL_ATTEMPTS,
                "target_active_count": target_active_count,
                "active_count_after": len(active_item_ids),
                "shortfall_count": max(0, target_active_count - len(active_item_ids)),
                "attempts": refill_attempts,
            }
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
        published_rulegen = {
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
            "rule_availability_reconciliation": _rule_availability_reconciliation_payload(
                rule_availability_reconciliations
            ),
            "rule_availability_refill": rule_availability_refill_payload,
        }
    after_pair_count = count_items_for_pair_fn(updated_store, pair)
    added_items = max(0, after_pair_count - before_pair_count)
    refresh_payload = admission_refresh_result_to_dict(refresh_result)
    effective_selected_lemmas = _new_active_lemmas_after_refresh(
        updated_store,
        pair=pair,
        active_item_ids_before=active_item_ids_for_refresh,
        active_item_ids_after=active_item_ids,
    )
    refresh_payload["effective_selected_lemmas"] = list(effective_selected_lemmas)
    refresh_payload["effective_admitted_count"] = len(effective_selected_lemmas)
    refresh_payload["active_rotation_release"] = active_rotation_release.to_dict()
    refresh_payload["selection_strategy_requested"] = strategy_requested
    refresh_payload["selection_strategy_effective"] = strategy_effective
    refresh_payload["selection_policy"] = refresh_policy.selector_config.selection_policy
    if profile_growth_diagnostics:
        refresh_payload["profile_growth"] = _profile_growth_payload(profile_growth_diagnostics)
        if _has_active_profile_signals(profile_growth_diagnostics):
            refresh_payload["selected_preferred_topic"] = _selected_preferred_topic_payload(
                effective_selected_lemmas,
                selector_candidates,
            )
    refresh_payload["weight_terms"] = {
        "admission_weight": "Entry/growth score for adding words into S.",
        "serving_priority": "Due/scheduler-derived priority for selecting words already in S.",
    }
    refresh_payload["rule_availability_refill"] = rule_availability_refill_payload
    return {
        "pair": pair,
        "profile_id": profile_id,
        "strategy_requested": strategy_requested,
        "strategy_effective": strategy_effective,
        "set_top_n": effective_set_top_n,
        "feedback_window_size": effective_feedback_window_size,
        "allowed_pos": sorted(allowed_pos),
        "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
        "max_active_items": refresh_result.decision.max_active_items,
        "max_new_items_per_day": refresh_result.decision.max_new_items_per_day,
        "added_items": added_items,
        "total_items_for_pair": after_pair_count,
        "store_path": str(paths.srs_store_path_for(profile_id)),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        **pos_overlay_payload,
        "admission_refresh": refresh_payload,
        "inventory": {
            "path": str(inventory_path),
            "exists": bool(inventory_path.exists()),
            "active_items_for_pair": len(active_item_ids),
            "source": inventory_payload_source,
            "backfilled_from_store": inventory_backfilled,
            "updated_at": inventory_updated_at,
        },
        "suppression": {
            "path": str(suppression_path),
            "exists": bool(suppression_path.exists()),
            "active_suppressed_lemmas": suppressed_lemmas,
            "active_suppressed_count": len(suppressed_lemmas),
        },
        "browsing_admission_preview": browsing_preview,
        "rulegen": published_rulegen,
        "applied": bool(refresh_result.applied),
        "persisted": bool(config.persist_store),
        "trigger": str(config.trigger or "manual"),
    }


def _rulegen_config_for_pair(pair: str) -> RulegenConfig:
    effective_rulegen_tuning = resolve_rulegen_tuning(pair)
    return RulegenConfig(
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
        enable_exact_gloss_demotions=effective_rulegen_tuning.enable_exact_gloss_demotions,
    )


def _rule_availability_reconciliation_payload(
    reconciliations: Sequence[RuleAvailabilityReconciliation],
) -> dict[str, object] | None:
    if not reconciliations:
        return None
    if len(reconciliations) == 1:
        return reconciliations[0].to_dict()
    discarded_lemmas: list[str] = []
    discarded_item_ids: list[str] = []
    for reconciliation in reconciliations:
        discarded_lemmas.extend(reconciliation.discarded_lemmas)
        discarded_item_ids.extend(reconciliation.discarded_item_ids)
    return {
        "reason": reconciliations[-1].reason,
        "changed": any(reconciliation.changed for reconciliation in reconciliations),
        "active_count_before": len(reconciliations[0].active_item_ids_before),
        "active_count_after": len(reconciliations[-1].active_item_ids_after),
        "discarded_count": len(discarded_item_ids),
        "discarded_item_ids": discarded_item_ids,
        "discarded_lemmas": discarded_lemmas,
        "enabled_rule_lemma_count": len(reconciliations[-1].enabled_rule_lemmas),
        "passes": [reconciliation.to_dict() for reconciliation in reconciliations],
    }


def _active_lemmas_for_item_ids(
    store: SrsStore,
    *,
    pair: str,
    active_item_ids: Sequence[str],
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
    lemmas: Sequence[str],
) -> tuple[str, ...]:
    available_ids = {
        str(item.item_id or "").strip()
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


def _new_active_lemmas_after_refresh(
    store: SrsStore,
    *,
    pair: str,
    active_item_ids_before: Sequence[str],
    active_item_ids_after: Sequence[str],
) -> tuple[str, ...]:
    before = {str(item_id or "").strip() for item_id in active_item_ids_before}
    new_item_ids = tuple(
        str(item_id or "").strip()
        for item_id in active_item_ids_after
        if str(item_id or "").strip() and str(item_id or "").strip() not in before
    )
    return _active_lemmas_for_item_ids(store, pair=pair, active_item_ids=new_item_ids)


def _resolve_refresh_strategy(value: object) -> str:
    normalized = normalize_set_strategy(value)
    if normalized in {STRATEGY_PROFILE_BOOTSTRAP, STRATEGY_PROFILE_GROWTH}:
        return STRATEGY_PROFILE_GROWTH
    return STRATEGY_FREQUENCY_BOOTSTRAP


def _profile_growth_selector_candidates(
    seeds: Sequence[SeedWord],
    *,
    profile_context: Optional[Mapping[str, object]],
) -> tuple[list[SelectorCandidate], Mapping[str, object]]:
    selection_count = min(
        len(seeds),
        max(AdmissionRefreshPolicy().selector_config.top_n, 200),
    )
    frontier_entries, diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
        seeds,
        profile_context=profile_context,
        selection_count=selection_count,
        preview_limit=10,
        policy=FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
    )
    candidates: list[SelectorCandidate] = []
    for entry in frontier_entries:
        base_candidates = seed_to_selector_candidates([cast(SeedWord, entry.seed)])
        if not base_candidates:
            continue
        base_candidate = base_candidates[0]
        profile_candidate = entry.source_entry.scored_candidate.candidate
        lane_name = str(entry.selected_lane or "")
        lane_score = max(0.0, float(entry.lane_scores.get(lane_name, 0.0)))
        base_metadata = (
            dict(base_candidate.metadata) if isinstance(base_candidate.metadata, Mapping) else {}
        )
        profile_metadata = (
            dict(profile_candidate.metadata)
            if isinstance(profile_candidate.metadata, Mapping)
            else {}
        )
        metadata = {
            **base_metadata,
            **profile_metadata,
            "selection_strategy": STRATEGY_PROFILE_GROWTH,
            "profile_growth_policy": FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY.version,
            "profile_growth_lane": lane_name,
            "profile_growth_score": round(
                lane_score,
                6,
            ),
            "profile_growth_weighted_components": {
                "frontier_lane_score": round(lane_score, 6),
                "topic_affinity": round(float(entry.signal_pack.preference_affinity), 6),
                "admission_suitability": round(
                    float(entry.signal_pack.admission_suitability),
                    6,
                ),
            },
        }
        candidates.append(
            replace(
                profile_candidate,
                base_freq=lane_score,
                topic_bias=float(entry.signal_pack.preference_affinity),
                user_pref=lane_score,
                confidence=base_candidate.confidence,
                source_type=base_candidate.source_type,
                metadata=metadata,
            )
        )
    return candidates, diagnostics


def _profile_growth_payload(diagnostics: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    profile_context = diagnostics.get("profile_context")
    active_signals = (
        profile_context.get("active_signals") if isinstance(profile_context, Mapping) else None
    )
    has_active_profile_signals = bool(active_signals)
    for key in (
        "selector_version",
        "selector_policy_version",
        "selection_weights",
        "selection_policy",
        "utility_weights",
        "profile_context",
    ):
        if key in diagnostics:
            payload[key] = diagnostics[key]
    if not has_active_profile_signals:
        return payload
    for key in (
        "active_topic_support",
        "topic_depth_by_level",
        "ranking_preview",
    ):
        if key in diagnostics:
            if key == "ranking_preview":
                payload[key] = _compact_profile_growth_ranking_preview(diagnostics[key])
            else:
                payload[key] = diagnostics[key]
    return payload


def _has_active_profile_signals(diagnostics: Mapping[str, object]) -> bool:
    profile_context = diagnostics.get("profile_context")
    if not isinstance(profile_context, Mapping):
        return False
    active_signals = profile_context.get("active_signals")
    return bool(active_signals)


def _selected_preferred_topic_payload(
    selected_lemmas: Sequence[str],
    candidates: Sequence[SelectorCandidate],
) -> dict[str, object]:
    selected = [str(lemma or "").strip() for lemma in selected_lemmas if str(lemma or "").strip()]
    selected_set = set(selected)
    preferred = {
        candidate.lemma
        for candidate in candidates
        if str(candidate.lemma or "").strip() in selected_set
        and _candidate_has_topic_lift(candidate)
    }
    selected_count = len(selected)
    preferred_count = len(preferred)
    return {
        "selected_count": selected_count,
        "preferred_count": preferred_count,
        "share": round(preferred_count / selected_count, 6) if selected_count else 0.0,
        "lemmas": [lemma for lemma in selected if lemma in preferred],
    }


def _candidate_has_topic_lift(candidate: SelectorCandidate) -> bool:
    if float(candidate.topic_bias or 0.0) > 0.0:
        return True
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    signals = metadata.get("profile_bootstrap_signals")
    if not isinstance(signals, Mapping):
        return False
    try:
        return float(signals.get("preference_affinity") or 0.0) > 0.0
    except (TypeError, ValueError):
        return False


def _compact_profile_growth_ranking_preview(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    preview: list[dict[str, object]] = []
    for entry in value[:10]:
        if not isinstance(entry, Mapping):
            continue
        signals = entry.get("signals")
        signal_map = signals if isinstance(signals, Mapping) else {}
        preview.append(
            {
                "lemma": entry.get("lemma"),
                "base_rank": entry.get("base_rank"),
                "reranked_rank": entry.get("reranked_rank"),
                "rank_delta": entry.get("rank_delta"),
                "pos_bucket": entry.get("pos_bucket"),
                "base_weight": entry.get("base_weight"),
                "admission_weight": entry.get("admission_weight"),
                "profile_score": entry.get("profile_score"),
                "topic_affinity": signal_map.get("topic_affinity"),
                "topic_affinity_source": signal_map.get("topic_affinity_source"),
                "proficiency_fit": signal_map.get("proficiency_fit"),
                "challenge_fit": signal_map.get("challenge_fit"),
                "readiness_multiplier": signal_map.get("readiness_multiplier"),
                "difficulty_estimate": signal_map.get("difficulty_estimate"),
                "active_profile_drivers": _list_payload(entry.get("active_profile_drivers")),
            }
        )
    return preview


def _list_payload(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _normalize_allowed_pos(value: object) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        candidates = [part for part in value.split(",")]
    elif isinstance(value, Sequence):
        candidates = list(value)
    else:
        return set()
    normalized = {str(item).strip().lower() for item in candidates if str(item).strip()}
    return normalized
