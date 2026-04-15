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
    set_active_item_ids,
)
from lexishift_core.srs.admission_refresh import (
    AdmissionRefreshPolicy,
    admission_refresh_result_to_dict,
    apply_admission_refresh,
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
        check_rulegen_resources=True,
    )
    if resolved_set_source_db is None:
        raise ValueError(f"Missing frequency source DB for pair '{pair}'.")

    profile_id = resolve_profile_id_fn(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    inventory_path = paths.srs_inventory_path_for(profile_id)
    inventory = load_srs_inventory(inventory_path) if inventory_path.exists() else SrsInventory()
    settings = ensure_settings_fn(paths, persist_missing=True)
    store = ensure_store_fn(paths, profile_id=profile_id, persist_missing=True)
    before_pair_count = count_items_for_pair_fn(store, pair)
    existing_active_item_ids, _ = resolve_active_item_ids(
        store=store,
        pair=pair,
        inventory=inventory if inventory_path.exists() else None,
    )
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
    selector_candidates = seed_to_selector_candidates(selection)
    signal_events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    allowed_pos = _normalize_allowed_pos(getattr(config, "allowed_pos", None))
    refresh_policy = AdmissionRefreshPolicy(
        feedback_window_size=effective_feedback_window_size,
        max_active_items_override=config.max_active_items,
        max_new_items_override=config.max_new_items,
        allowed_pos=allowed_pos or None,
        selection_seed=getattr(config, "selection_seed", None),
    )
    updated_store, refresh_result = apply_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        candidates=selector_candidates,
        events=signal_events,
        policy=refresh_policy,
    )
    refreshed_at = now_utc().isoformat()
    admitted_active_item_ids = tuple(
        build_item_id(pair, lemma) for lemma in refresh_result.selected_lemmas if str(lemma).strip()
    )
    active_item_ids = merge_active_item_ids(existing_active_item_ids, admitted_active_item_ids)
    if config.persist_store:
        from lexishift_core.srs import save_srs_store

        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
        inventory = set_active_item_ids(
            inventory,
            pair=pair,
            active_item_ids=active_item_ids,
            last_refreshed_at=refreshed_at,
        )
        save_srs_inventory(inventory, inventory_path)

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
            ),
            active_item_ids=active_item_ids,
            initialize_if_empty=False,
            persist_store=False,
        )
        write_rulegen_outputs_fn(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            rules=rulegen_output.rules,
            snapshot=rulegen_output.snapshot,
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
        "inventory": {
            "path": str(inventory_path),
            "exists": bool(config.persist_store or inventory_path.exists()),
            "active_items_for_pair": len(active_item_ids),
            "updated_at": refreshed_at if config.persist_store else None,
        },
        "admission_refresh": refresh_payload,
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
