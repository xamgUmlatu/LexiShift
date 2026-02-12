from __future__ import annotations

from pathlib import Path
from typing import Callable

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import (
    RulegenConfig,
    RulegenOutput,
    SetInitializationConfig,
    SetInitializationReport,
)
from lexishift_core.srs import SrsSettings, SrsStore, save_srs_store
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.set_policy import resolve_set_sizing_policy
from lexishift_core.srs.signal_queue import summarize_signal_events
from lexishift_core.srs.source import SOURCE_INITIAL_SET


def initialize_srs_set(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
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
    sizing_policy = resolve_set_sizing_policy(
        bootstrap_top_n=(
            max(1, int(config.bootstrap_top_n))
            if config.bootstrap_top_n is not None
            else resolved_set_top_n
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
    if not can_execute or execution_mode != "frequency_bootstrap":
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
        ),
    )
    save_srs_store(updated_store, paths.srs_store_path_for(profile_id))

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
        },
        "rulegen": {
            "published": True,
            "targets": rulegen_output.target_count,
            "rules": len(rulegen_output.rules),
            "snapshot_path": str(paths.snapshot_path(pair, profile_id=profile_id)),
            "ruleset_path": str(paths.ruleset_path(pair, profile_id=profile_id)),
        },
        "applied": True,
        "plan": plan_payload,
        "signal_summary": signal_summary,
    }
