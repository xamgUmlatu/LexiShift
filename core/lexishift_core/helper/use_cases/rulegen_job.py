from __future__ import annotations

from pathlib import Path
from typing import Callable

from lexishift_core.helper.lp_capabilities import pair_requirements, resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig, RulegenOutput, SetInitializationConfig
from lexishift_core.srs import SrsSettings, SrsStore
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.sampling import SrsSamplingResult, sample_store_items, sampling_result_to_dict


def run_rulegen_job(
    paths: HelperPaths,
    *,
    config,
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    ensure_settings_fn: Callable[..., SrsSettings],
    ensure_store_fn: Callable[..., SrsStore],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    update_status_fn: Callable[..., None],
    run_rulegen_for_pair_fn: Callable[..., tuple[SrsStore, RulegenOutput]],
    write_rulegen_outputs_fn: Callable[..., None],
) -> dict[str, object]:
    capability = resolve_pair_capability(config.pair)
    pair = capability.pair
    effective_set_top_n = resolve_pair_set_top_n_fn(
        pair=pair,
        requested_top_n=config.set_top_n,
        purpose="refresh",
    )
    resolved_jmdict_path, resolved_freedict_de_en_path, resolved_set_source_db = resolve_pair_resources_fn(
        paths,
        pair=pair,
        jmdict_path=config.jmdict_path,
        freedict_de_en_path=config.freedict_de_en_path,
        set_source_db=config.set_source_db,
    )
    should_seed_from_frequency = bool(
        config.initialize_if_empty
        and resolved_set_source_db is not None
        and resolved_set_source_db.exists()
    )
    ensure_pair_requirements_fn(
        pair=pair,
        jmdict_path=resolved_jmdict_path,
        freedict_de_en_path=resolved_freedict_de_en_path,
        require_frequency_db=False,
        set_source_db=resolved_set_source_db,
        check_seed_resources=should_seed_from_frequency,
        check_rulegen_resources=True,
    )
    profile_id = resolve_profile_id_fn(paths, profile_id=config.profile_id)
    settings = ensure_settings_fn(paths, persist_missing=config.persist_store)
    store = ensure_store_fn(paths, profile_id=profile_id, persist_missing=config.persist_store)
    diagnostics: dict[str, object] | None = None
    sampling_result: SrsSamplingResult | None = None
    set_init_config: SetInitializationConfig | None = None
    stopwords_path = resolve_stopwords_path_fn(paths, pair=pair)
    if resolved_set_source_db and resolved_set_source_db.exists():
        set_init_config = SetInitializationConfig(
            frequency_db=resolved_set_source_db,
            jmdict_path=resolved_jmdict_path,
            top_n=effective_set_top_n,
            language_pair=pair,
            stopwords_path=stopwords_path,
            require_jmdict=capability.requires_jmdict_for_seed,
        )
    rulegen_config = RulegenConfig(
        language_pair=pair,
        confidence_threshold=config.confidence_threshold,
        max_snapshot_targets=config.snapshot_targets,
        max_snapshot_sources=config.snapshot_sources,
    )
    targets_override: list[str] | None = None
    if config.sample_count is not None:
        sampling_result = sample_store_items(
            store,
            pair=pair,
            sample_count=config.sample_count,
            strategy=config.sample_strategy,
            seed=config.sample_seed,
        )
        targets_override = list(sampling_result.sampled_lemmas)
    if config.debug:
        missing_inputs = []
        if resolved_set_source_db and not resolved_set_source_db.exists():
            missing_inputs.append({"type": "set_source_db", "path": str(resolved_set_source_db)})
        diagnostics = {
            "pair": pair,
            "requirements": pair_requirements(pair),
            "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
            "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
            "jmdict_exists": bool(resolved_jmdict_path and resolved_jmdict_path.exists()),
            "freedict_de_en_path": (
                str(resolved_freedict_de_en_path) if resolved_freedict_de_en_path else None
            ),
            "freedict_de_en_exists": bool(
                resolved_freedict_de_en_path and resolved_freedict_de_en_path.exists()
            ),
            "set_source_db": str(resolved_set_source_db) if resolved_set_source_db else None,
            "set_source_db_exists": bool(
                resolved_set_source_db and resolved_set_source_db.exists()
            ),
            "set_initialization_enabled": bool(set_init_config),
            "effective_set_top_n": effective_set_top_n,
            "stopwords_path": str(stopwords_path) if stopwords_path else None,
            "stopwords_exists": bool(stopwords_path and stopwords_path.exists()),
            "missing_inputs": missing_inputs,
            "store_items": len(store.items),
            "store_items_for_pair": len([item for item in store.items if item.language_pair == pair]),
            "store_sample": [
                item.lemma for item in store.items if item.language_pair == pair
            ][: max(1, int(config.debug_sample_size))],
        }
        if sampling_result is not None:
            diagnostics["sampling"] = sampling_result_to_dict(sampling_result)
    store, output = run_rulegen_for_pair_fn(
        paths=paths,
        pair=pair,
        profile_id=profile_id,
        store=store,
        settings=settings,
        jmdict_path=resolved_jmdict_path,
        freedict_de_en_path=resolved_freedict_de_en_path,
        set_init_config=set_init_config,
        rulegen_config=rulegen_config,
        targets_override=targets_override,
        initialize_if_empty=config.initialize_if_empty,
        persist_store=config.persist_store,
    )
    if config.persist_outputs:
        write_rulegen_outputs_fn(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            rules=output.rules,
            snapshot=output.snapshot,
        )
    if config.update_status:
        update_status_fn(
            paths=paths,
            profile_id=profile_id,
            pair=pair,
            rule_count=len(output.rules),
            target_count=output.target_count,
            error=None,
        )
    response = {
        "pair": pair,
        "profile_id": profile_id,
        "targets": output.target_count,
        "rules": len(output.rules),
        "snapshot": output.snapshot,
        "snapshot_path": (
            str(paths.snapshot_path(pair, profile_id=profile_id))
            if config.persist_outputs
            else None
        ),
        "ruleset_path": (
            str(paths.ruleset_path(pair, profile_id=profile_id))
            if config.persist_outputs
            else None
        ),
        "store_persisted": config.persist_store,
        "outputs_persisted": config.persist_outputs,
    }
    if diagnostics is not None:
        response["diagnostics"] = diagnostics
    if sampling_result is not None:
        response["sampling"] = sampling_result_to_dict(sampling_result)
    return response
