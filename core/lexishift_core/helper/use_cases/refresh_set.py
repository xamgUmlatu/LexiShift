from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig, RulegenOutput
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
)
from lexishift_core.srs.admission_refresh import (
    AdmissionRefreshPolicy,
    admission_refresh_result_to_dict,
    apply_admission_refresh,
)
from lexishift_core.srs.admission_suppression import (
    active_suppressed_lemmas,
    load_admission_suppression_store,
    prune_expired_suppression_entries,
    save_admission_suppression_store,
)
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.seed import SeedSelectionConfig, SeedWord, seed_to_selector_candidates
from lexishift_core.srs.signal_queue import load_signal_events
from lexishift_core.srs.store_ops import build_item_id
from lexishift_core.srs.time import now_utc


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
    run_rulegen_for_pair_fn: Callable[..., tuple[SrsStore, RulegenOutput]],
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
        ),
    )
    semantic_context_targets = tuple(
        dict.fromkeys(
            str(getattr(seed, "lemma", "")).strip()
            for seed in selection
            if str(getattr(seed, "lemma", "")).strip()
        )
    )
    selector_candidates = seed_to_selector_candidates(selection)
    signal_events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    allowed_pos = _normalize_allowed_pos(getattr(config, "allowed_pos", None))
    refresh_policy = AdmissionRefreshPolicy(
        feedback_window_size=effective_feedback_window_size,
        max_active_items_override=config.max_active_items,
        max_new_items_override=config.max_new_items,
        allowed_pos=allowed_pos or None,
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
    inventory_updated_at = None
    inventory_payload_source = inventory_source
    inventory_backfilled = False
    active_item_ids = tuple(active_item_ids_before)
    if refresh_result.applied:
        admitted_active_item_ids = tuple(
            build_item_id(pair, str(lemma).strip())
            for lemma in refresh_result.selected_lemmas
            if str(lemma).strip()
        )
        active_item_ids = merge_active_item_ids(active_item_ids_before, admitted_active_item_ids)
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
    elif config.persist_store and inventory_source == "store_fallback" and active_item_ids_before:
        inventory_updated_at = now_utc().isoformat()
        inventory = set_active_item_ids(
            inventory,
            pair=pair,
            active_item_ids=active_item_ids_before,
            last_refreshed_at=inventory_updated_at,
        )
        save_srs_inventory(inventory, inventory_path)
        inventory_backfilled = True
        inventory_payload_source = "inventory_backfilled"

    after_pair_count = count_items_for_pair_fn(updated_store, pair)
    added_items = max(0, after_pair_count - before_pair_count)
    published_rulegen = None
    if refresh_result.applied:
        effective_rulegen_tuning = resolve_rulegen_tuning(pair)
        _updated_store, rulegen_output = run_rulegen_for_pair_fn(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            store=updated_store,
            settings=settings,
            jmdict_path=resolved_jmdict_path,
            translation_dict_path=resolved_translation_dict_path,
            rulegen_config=RulegenConfig(
                language_pair=pair,
                confidence_threshold=effective_rulegen_tuning.confidence_threshold,
                max_definitions_per_target=effective_rulegen_tuning.max_definitions_per_target,
                max_rules_per_target=effective_rulegen_tuning.max_rules_per_target,
                semantic_demotion_scale=effective_rulegen_tuning.semantic_demotion_scale,
                include_variants=effective_rulegen_tuning.include_variants,
                allow_multiword_glosses=effective_rulegen_tuning.allow_multiword_glosses,
                scoring=effective_rulegen_tuning.scoring,
                reverse_check=effective_rulegen_tuning.reverse_check,
                enable_exact_gloss_demotions=(
                    effective_rulegen_tuning.enable_exact_gloss_demotions
                ),
            ),
            active_item_ids=active_item_ids,
            semantic_context_targets=semantic_context_targets,
            initialize_if_empty=False,
            persist_store=False,
        )
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
        }
    refresh_payload = admission_refresh_result_to_dict(refresh_result)
    refresh_payload["weight_terms"] = {
        "admission_weight": "Entry/growth score for adding words into S.",
        "serving_priority": "Due/scheduler-derived priority for selecting words already in S.",
    }
    return {
        "pair": pair,
        "profile_id": profile_id,
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
        "rulegen": published_rulegen,
        "applied": bool(refresh_result.applied),
        "persisted": bool(config.persist_store),
        "trigger": str(config.trigger or "manual"),
    }


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
