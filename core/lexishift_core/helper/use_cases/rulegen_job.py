from __future__ import annotations

from pathlib import Path
from typing import Callable

from lexishift_core.helper.lp_capabilities import pair_requirements, resolve_pair_capability
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig, RulegenOutput, SetInitializationConfig
from lexishift_core.rulegen.tuning import (
    RulegenTuningOverrides,
    resolve_pair_rulegen_tuning,
    resolve_rulegen_tuning,
    resolved_rulegen_tuning_to_dict,
    rulegen_pair_tuning_to_dict,
    rulegen_tuning_overrides_to_dict,
)
from lexishift_core.srs import SrsSettings, SrsStore
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.sampling import (
    SrsSamplingResult,
    sample_store_items,
    sampling_result_to_dict,
)


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
    resolved_jmdict_path, resolved_translation_dict_path, resolved_set_source_db = (
        resolve_pair_resources_fn(
            paths,
            pair=pair,
            jmdict_path=config.jmdict_path,
            translation_dict_path=getattr(config, "translation_dict_path", None),
            set_source_db=config.set_source_db,
        )
    )
    should_seed_from_frequency = bool(
        config.initialize_if_empty
        and resolved_set_source_db is not None
        and resolved_set_source_db.exists()
    )
    ensure_pair_requirements_fn(
        pair=pair,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        require_frequency_db=False,
        set_source_db=resolved_set_source_db,
        check_seed_resources=should_seed_from_frequency,
        check_rulegen_resources=True,
    )
    resolved_translation_pack, resolved_reverse_translation_pack = resolve_pair_translation_packs(
        paths,
        pair=pair,
        translation_dict_path=resolved_translation_dict_path,
        reverse_translation_dict_path=None,
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
    pair_tuning = resolve_pair_rulegen_tuning(pair)
    rulegen_overrides = RulegenTuningOverrides(
        confidence_threshold=config.confidence_threshold,
        max_definitions_per_target=config.max_definitions_per_target,
        max_rules_per_target=config.max_rules_per_target,
        semantic_demotion_scale=config.semantic_demotion_scale,
        enable_exact_gloss_demotions=config.enable_exact_gloss_demotions,
        include_variants=config.include_variants,
        allow_multiword_glosses=config.allow_multiword_glosses,
        pos_scoring_enabled=config.pos_scoring_enabled,
        pos_exact_match_bonus=config.pos_exact_match_bonus,
        pos_compatible_match_bonus=config.pos_compatible_match_bonus,
        score_weight_dict_priority=config.score_weight_dict_priority,
        score_weight_frequency_weight=config.score_weight_frequency_weight,
        score_weight_pos_match=config.score_weight_pos_match,
        score_weight_variant_penalty=config.score_weight_variant_penalty,
        score_weight_phrase_penalty=config.score_weight_phrase_penalty,
        score_weight_embedding=config.score_weight_embedding,
        reverse_check_enabled=config.reverse_check_enabled,
        reverse_check_match_bonus=config.reverse_check_match_bonus,
        reverse_check_near_bonus=config.reverse_check_near_bonus,
        reverse_check_near_rank_max=config.reverse_check_near_rank_max,
        reverse_check_far_hit_penalty=config.reverse_check_far_hit_penalty,
        reverse_check_miss_penalty=config.reverse_check_miss_penalty,
        reverse_check_exact_hit_ambiguity_threshold=(
            config.reverse_check_exact_hit_ambiguity_threshold
        ),
        reverse_check_exact_hit_ambiguity_penalty=config.reverse_check_exact_hit_ambiguity_penalty,
        reverse_check_exact_hit_specificity_bonus=config.reverse_check_exact_hit_specificity_bonus,
    )
    effective_rulegen_tuning = resolve_rulegen_tuning(pair, overrides=rulegen_overrides)
    rulegen_config = RulegenConfig(
        language_pair=pair,
        confidence_threshold=effective_rulegen_tuning.confidence_threshold,
        max_definitions_per_target=effective_rulegen_tuning.max_definitions_per_target,
        max_rules_per_target=effective_rulegen_tuning.max_rules_per_target,
        semantic_demotion_scale=effective_rulegen_tuning.semantic_demotion_scale,
        enable_exact_gloss_demotions=effective_rulegen_tuning.enable_exact_gloss_demotions,
        include_variants=effective_rulegen_tuning.include_variants,
        allow_multiword_glosses=effective_rulegen_tuning.allow_multiword_glosses,
        scoring=effective_rulegen_tuning.scoring,
        reverse_check=effective_rulegen_tuning.reverse_check,
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
            "rulegen_tuning": {
                "confidence_threshold": float(effective_rulegen_tuning.confidence_threshold),
                "max_definitions_per_target": (
                    int(effective_rulegen_tuning.max_definitions_per_target)
                    if effective_rulegen_tuning.max_definitions_per_target is not None
                    else None
                ),
                "max_rules_per_target": (
                    int(effective_rulegen_tuning.max_rules_per_target)
                    if effective_rulegen_tuning.max_rules_per_target is not None
                    else None
                ),
                "semantic_demotion_scale": float(effective_rulegen_tuning.semantic_demotion_scale),
                "enable_exact_gloss_demotions": bool(
                    effective_rulegen_tuning.enable_exact_gloss_demotions
                ),
                "include_variants": bool(effective_rulegen_tuning.include_variants),
                "allow_multiword_glosses": bool(effective_rulegen_tuning.allow_multiword_glosses),
                "pos_scoring_enabled": bool(effective_rulegen_tuning.scoring.pos_match.enabled),
                "pos_exact_match_bonus": float(
                    effective_rulegen_tuning.scoring.pos_match.exact_match_bonus
                ),
                "pos_compatible_match_bonus": float(
                    effective_rulegen_tuning.scoring.pos_match.compatible_match_bonus
                ),
                "score_weights": {
                    "dict_priority": float(effective_rulegen_tuning.scoring.weights.dict_priority),
                    "frequency_weight": float(
                        effective_rulegen_tuning.scoring.weights.frequency_weight
                    ),
                    "pos_match": float(effective_rulegen_tuning.scoring.weights.pos_match),
                    "variant_penalty": float(
                        effective_rulegen_tuning.scoring.weights.variant_penalty
                    ),
                    "phrase_penalty": float(
                        effective_rulegen_tuning.scoring.weights.phrase_penalty
                    ),
                    "embedding_weight": float(
                        effective_rulegen_tuning.scoring.weights.embedding_weight
                    ),
                },
                "reverse_check": {
                    "enabled": bool(effective_rulegen_tuning.reverse_check.enabled),
                    "match_bonus": float(effective_rulegen_tuning.reverse_check.match_bonus),
                    "near_bonus": float(effective_rulegen_tuning.reverse_check.near_bonus),
                    "near_rank_max": int(effective_rulegen_tuning.reverse_check.near_rank_max),
                    "far_hit_penalty": float(
                        effective_rulegen_tuning.reverse_check.far_hit_penalty
                    ),
                    "miss_penalty": float(effective_rulegen_tuning.reverse_check.miss_penalty),
                    "exact_hit_ambiguity_threshold": int(
                        effective_rulegen_tuning.reverse_check.exact_hit_ambiguity_threshold
                    ),
                    "exact_hit_ambiguity_penalty": float(
                        effective_rulegen_tuning.reverse_check.exact_hit_ambiguity_penalty
                    ),
                    "exact_hit_specificity_bonus": float(
                        effective_rulegen_tuning.reverse_check.exact_hit_specificity_bonus
                    ),
                },
                "pair_defaults": rulegen_pair_tuning_to_dict(pair_tuning),
                "overrides": rulegen_tuning_overrides_to_dict(rulegen_overrides),
                "effective": resolved_rulegen_tuning_to_dict(effective_rulegen_tuning),
            },
            "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
            "jmdict_exists": bool(resolved_jmdict_path and resolved_jmdict_path.exists()),
            "translation_dict_path": (
                str(resolved_translation_dict_path) if resolved_translation_dict_path else None
            ),
            "translation_dict_exists": bool(
                resolved_translation_dict_path and resolved_translation_dict_path.exists()
            ),
            "translation_pack_path": (
                str(resolved_translation_dict_path) if resolved_translation_dict_path else None
            ),
            "translation_pack_exists": bool(
                resolved_translation_dict_path and resolved_translation_dict_path.exists()
            ),
            "translation_dict_provider": (
                resolved_translation_pack.provider if resolved_translation_pack else None
            ),
            "translation_pack_id": (
                resolved_translation_pack.pack_id if resolved_translation_pack else None
            ),
            "translation_pos_source_profile": (
                resolved_translation_pack.pos_source_profile if resolved_translation_pack else None
            ),
            "reverse_translation_dict_path": (
                str(resolved_reverse_translation_pack.path)
                if resolved_reverse_translation_pack
                else None
            ),
            "reverse_translation_dict_exists": bool(
                resolved_reverse_translation_pack
                and resolved_reverse_translation_pack.path.exists()
            ),
            "reverse_translation_pack_path": (
                str(resolved_reverse_translation_pack.path)
                if resolved_reverse_translation_pack
                else None
            ),
            "reverse_translation_pack_exists": bool(
                resolved_reverse_translation_pack
                and resolved_reverse_translation_pack.path.exists()
            ),
            "reverse_translation_dict_provider": (
                resolved_reverse_translation_pack.provider
                if resolved_reverse_translation_pack
                else None
            ),
            "reverse_translation_pack_id": (
                resolved_reverse_translation_pack.pack_id
                if resolved_reverse_translation_pack
                else None
            ),
            "reverse_translation_pos_source_profile": (
                resolved_reverse_translation_pack.pos_source_profile
                if resolved_reverse_translation_pack
                else None
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
            "store_items_for_pair": len(
                [item for item in store.items if item.language_pair == pair]
            ),
            "store_sample": [item.lemma for item in store.items if item.language_pair == pair][
                : max(1, int(config.debug_sample_size))
            ],
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
        translation_dict_path=resolved_translation_dict_path,
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
            str(paths.ruleset_path(pair, profile_id=profile_id)) if config.persist_outputs else None
        ),
        "store_persisted": config.persist_store,
        "outputs_persisted": config.persist_outputs,
    }
    if diagnostics is not None:
        response["diagnostics"] = diagnostics
    if sampling_result is not None:
        response["sampling"] = sampling_result_to_dict(sampling_result)
    return response
