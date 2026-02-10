from __future__ import annotations

from typing import Callable

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig
from lexishift_core.srs.admission_refresh import (
    AdmissionRefreshPolicy,
    admission_refresh_result_to_dict,
    apply_admission_refresh,
)
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.seed import SeedSelectionConfig, seed_to_selector_candidates
from lexishift_core.srs.signal_queue import load_signal_events


def refresh_srs_set(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_feedback_window_size_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[object, object, object]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., object],
    ensure_store_fn: Callable[..., object],
    count_items_for_pair_fn: Callable[..., int],
    resolve_stopwords_path_fn: Callable[..., object],
    build_seed_candidates_fn: Callable[..., object],
    run_rulegen_for_pair_fn: Callable[..., tuple[object, object]],
    write_rulegen_outputs_fn: Callable[..., None],
    update_status_fn: Callable[..., None],
) -> dict:
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
    resolved_jmdict_path, resolved_freedict_de_en_path, resolved_set_source_db = resolve_pair_resources_fn(
        paths,
        pair=pair,
        jmdict_path=config.jmdict_path,
        freedict_de_en_path=config.freedict_de_en_path,
        set_source_db=config.set_source_db,
    )
    ensure_pair_requirements_fn(
        pair=pair,
        jmdict_path=resolved_jmdict_path,
        freedict_de_en_path=resolved_freedict_de_en_path,
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
    selector_candidates = seed_to_selector_candidates(selection)
    signal_events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    refresh_policy = AdmissionRefreshPolicy(
        feedback_window_size=effective_feedback_window_size,
        max_active_items_override=config.max_active_items,
        max_new_items_override=config.max_new_items,
    )
    updated_store, refresh_result = apply_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        candidates=selector_candidates,
        events=signal_events,
        policy=refresh_policy,
    )
    if config.persist_store:
        from lexishift_core.srs import save_srs_store

        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))

    after_pair_count = count_items_for_pair_fn(updated_store, pair)
    added_items = max(0, after_pair_count - before_pair_count)
    published_rulegen = None
    if refresh_result.applied:
        _updated_store, rulegen_output = run_rulegen_for_pair_fn(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            store=updated_store,
            settings=settings,
            jmdict_path=resolved_jmdict_path,
            freedict_de_en_path=resolved_freedict_de_en_path,
            rulegen_config=RulegenConfig(language_pair=pair),
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
        "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
        "max_active_items": refresh_result.decision.max_active_items,
        "max_new_items_per_day": refresh_result.decision.max_new_items_per_day,
        "added_items": added_items,
        "total_items_for_pair": after_pair_count,
        "store_path": str(paths.srs_store_path_for(profile_id)),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        "admission_refresh": refresh_payload,
        "rulegen": published_rulegen,
        "applied": bool(refresh_result.applied),
        "persisted": bool(config.persist_store),
        "trigger": str(config.trigger or "manual"),
    }

