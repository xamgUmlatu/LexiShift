from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.pair_resources import (
    resolve_pair_resources as _resolve_pair_resources,
    resolve_stopwords_path as _resolve_stopwords_path,
)
from lexishift_core.helper.rulegen import (
    initialize_store_from_frequency_list_with_report,
    run_rulegen_for_pair,
    write_rulegen_outputs,
)
from lexishift_core.helper.status import HelperStatus, load_status, save_status
from lexishift_core.helper.use_cases.initialize_set import (
    initialize_srs_set as _initialize_srs_set_use_case,
)
from lexishift_core.helper.use_cases.rebalance_set import (
    apply_srs_rebalance as _apply_srs_rebalance_use_case,
    plan_srs_rebalance as _plan_srs_rebalance_use_case,
)
from lexishift_core.helper.use_cases.set_planning import (
    build_set_plan_payload as _build_set_plan_payload,
    count_items_for_pair as _count_items_for_pair,
    plan_srs_set as _plan_srs_set_use_case,
)
from lexishift_core.helper.use_cases.signals import (
    apply_exposure as _apply_exposure_use_case,
    apply_feedback as _apply_feedback_use_case,
)
from lexishift_core.srs import (
    SrsSettings,
    SrsStore,
    load_srs_settings,
    load_srs_store,
    save_srs_settings,
    save_srs_store,
)
from lexishift_core.srs.pair_policy import resolve_srs_pair_policy
from lexishift_core.srs.set_strategy import (
    OBJECTIVE_BOOTSTRAP,
    OBJECTIVE_REBALANCE,
    STRATEGY_FREQUENCY_BOOTSTRAP,
    STRATEGY_PROFILE_GROWTH,
)
from lexishift_core.srs.source import SOURCE_EXTENSION
from lexishift_core.srs.time import now_utc


def build_seed_candidates(*args, **kwargs):
    seed_module = __import__(
        "lexishift_core.srs.seed",
        fromlist=["build_seed_candidates"],
    )
    return seed_module.build_seed_candidates(*args, **kwargs)


def _get_srs_runtime_diagnostics_use_case(*args, **kwargs):
    diagnostics_module = __import__(
        "lexishift_core.helper.use_cases.runtime_diagnostics",
        fromlist=["get_srs_runtime_diagnostics"],
    )
    return diagnostics_module.get_srs_runtime_diagnostics(*args, **kwargs)


def _run_rulegen_job_use_case(*args, **kwargs):
    rulegen_job_module = __import__(
        "lexishift_core.helper.use_cases.rulegen_job",
        fromlist=["run_rulegen_job"],
    )
    return rulegen_job_module.run_rulegen_job(*args, **kwargs)


def _preview_srs_admission_use_case(*args, **kwargs):
    preview_module = __import__(
        "lexishift_core.helper.use_cases.admission_preview",
        fromlist=["preview_srs_admission"],
    )
    return preview_module.preview_srs_admission(*args, **kwargs)


def _refresh_srs_set_use_case(*args, **kwargs):
    refresh_module = __import__(
        "lexishift_core.helper.use_cases.refresh_set",
        fromlist=["refresh_srs_set"],
    )
    return refresh_module.refresh_srs_set(*args, **kwargs)


def _semantic_admit_batch_use_case(*args, **kwargs):
    semantic_admission_module = __import__(
        "lexishift_core.helper.use_cases.semantic_admission",
        fromlist=["semantic_admit_batch"],
    )
    return semantic_admission_module.semantic_admit_batch(*args, **kwargs)


def _reset_srs_data_use_case(*args, **kwargs):
    reset_module = __import__(
        "lexishift_core.helper.use_cases.reset",
        fromlist=["reset_srs_data"],
    )
    return reset_module.reset_srs_data(*args, **kwargs)


@dataclass(frozen=True)
class RulegenJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    translation_dict_path: Optional[Path] = None
    profile_id: str = "default"
    set_source_db: Optional[Path] = None
    set_top_n: Optional[int] = None
    confidence_threshold: Optional[float] = None
    max_definitions_per_target: Optional[int] = None
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: Optional[float] = None
    enable_exact_gloss_demotions: Optional[bool] = None
    include_variants: Optional[bool] = None
    allow_multiword_glosses: Optional[bool] = None
    pos_scoring_enabled: Optional[bool] = None
    pos_exact_match_bonus: Optional[float] = None
    pos_compatible_match_bonus: Optional[float] = None
    score_weight_dict_priority: Optional[float] = None
    score_weight_frequency_weight: Optional[float] = None
    score_weight_pos_match: Optional[float] = None
    score_weight_variant_penalty: Optional[float] = None
    score_weight_phrase_penalty: Optional[float] = None
    score_weight_embedding: Optional[float] = None
    reverse_check_enabled: Optional[bool] = None
    reverse_check_match_bonus: Optional[float] = None
    reverse_check_near_bonus: Optional[float] = None
    reverse_check_near_rank_max: Optional[int] = None
    reverse_check_far_hit_penalty: Optional[float] = None
    reverse_check_miss_penalty: Optional[float] = None
    reverse_check_exact_hit_ambiguity_threshold: Optional[int] = None
    reverse_check_exact_hit_ambiguity_penalty: Optional[float] = None
    reverse_check_exact_hit_specificity_bonus: Optional[float] = None
    snapshot_targets: int = 50
    snapshot_sources: int = 6
    initialize_if_empty: bool = True
    persist_store: bool = True
    persist_outputs: bool = True
    update_status: bool = True
    debug: bool = False
    debug_sample_size: int = 10
    sample_count: Optional[int] = None
    sample_strategy: Optional[str] = None
    sample_seed: Optional[int] = None


@dataclass(frozen=True)
class SetInitializationJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    translation_dict_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
    profile_id: str = "default"
    set_top_n: Optional[int] = None
    bootstrap_top_n: Optional[int] = None
    initial_active_count: Optional[int] = None
    max_active_items_hint: Optional[int] = None
    replace_pair: bool = False
    strategy: str = STRATEGY_FREQUENCY_BOOTSTRAP
    objective: str = OBJECTIVE_BOOTSTRAP
    profile_context: Optional[Mapping[str, object]] = None
    trigger: str = "manual"


@dataclass(frozen=True)
class SetPlanningJobConfig:
    pair: str
    profile_id: str = "default"
    strategy: str = STRATEGY_FREQUENCY_BOOTSTRAP
    objective: str = OBJECTIVE_BOOTSTRAP
    set_top_n: Optional[int] = None
    bootstrap_top_n: Optional[int] = None
    initial_active_count: Optional[int] = None
    max_active_items_hint: Optional[int] = None
    replace_pair: bool = False
    profile_context: Optional[Mapping[str, object]] = None
    trigger: str = "manual"


@dataclass(frozen=True)
class SetAdmissionPreviewJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
    profile_id: str = "default"
    strategy: str = STRATEGY_FREQUENCY_BOOTSTRAP
    objective: str = OBJECTIVE_BOOTSTRAP
    set_top_n: Optional[int] = None
    bootstrap_top_n: Optional[int] = None
    initial_active_count: Optional[int] = None
    max_active_items_hint: Optional[int] = None
    preview_count: Optional[int] = None
    preview_sampling_mode: Optional[str] = None
    preview_seed: Optional[int] = None
    profile_context: Optional[Mapping[str, object]] = None
    trigger: str = "manual"


@dataclass(frozen=True)
class SrsRefreshJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    translation_dict_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
    profile_id: str = "default"
    set_top_n: Optional[int] = None
    feedback_window_size: Optional[int] = None
    max_active_items: Optional[int] = None
    max_new_items: Optional[int] = None
    allowed_pos: Optional[Sequence[str]] = None
    persist_store: bool = True
    trigger: str = "manual"
    profile_context: Optional[Mapping[str, object]] = None


@dataclass(frozen=True)
class SrsRebalanceJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    translation_dict_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
    profile_id: str = "default"
    strategy: str = STRATEGY_PROFILE_GROWTH
    objective: str = OBJECTIVE_REBALANCE
    set_top_n: Optional[int] = None
    max_active_items: Optional[int] = None
    profile_context: Optional[Mapping[str, object]] = None
    trigger: str = "manual"


def _ensure_settings(paths: HelperPaths, *, persist_missing: bool = True) -> SrsSettings:
    if paths.srs_settings_path.exists():
        return load_srs_settings(paths.srs_settings_path)
    settings = SrsSettings()
    if persist_missing:
        save_srs_settings(settings, paths.srs_settings_path)
    return settings


def _resolve_profile_id(
    paths: HelperPaths,
    *,
    profile_id: str | None,
    profile_context: Optional[Mapping[str, object]] = None,
) -> str:
    candidate = str(profile_id or "").strip()
    if not candidate and isinstance(profile_context, Mapping):
        context_profile_id = profile_context.get("profile_id")
        candidate = str(context_profile_id or "").strip()
    return paths.normalize_profile_id(candidate)


def _ensure_store(
    paths: HelperPaths,
    *,
    profile_id: str,
    persist_missing: bool = True,
) -> SrsStore:
    store_path = paths.srs_store_path_for(profile_id)
    if store_path.exists():
        return load_srs_store(store_path)
    store = SrsStore()
    if persist_missing:
        save_srs_store(store, store_path)
    return store


def _update_status(
    *,
    paths: HelperPaths,
    profile_id: str,
    pair: str,
    rule_count: int,
    target_count: int,
    error: Optional[str] = None,
) -> None:
    status_path = paths.srs_status_path_for(profile_id)
    status = load_status(status_path)
    status = HelperStatus(
        version=status.version,
        helper_version=status.helper_version,
        last_run_at=now_utc().isoformat(),
        last_error=error,
        last_pair=pair,
        last_rule_count=rule_count,
        last_target_count=target_count,
    )
    save_status(status, status_path)


def load_snapshot(paths: HelperPaths, *, pair: str, profile_id: str = "default") -> dict:
    snapshot_path = paths.snapshot_path(pair, profile_id=profile_id)
    if not snapshot_path.exists():
        raise FileNotFoundError(snapshot_path)
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def load_ruleset(paths: HelperPaths, *, pair: str, profile_id: str = "default") -> dict:
    ruleset_path = paths.ruleset_path(pair, profile_id=profile_id)
    if not ruleset_path.exists():
        raise FileNotFoundError(ruleset_path)
    return json.loads(ruleset_path.read_text(encoding="utf-8"))


def load_semantic_inventory(paths: HelperPaths, *, pair: str, profile_id: str = "default") -> dict:
    inventory_path = paths.semantic_inventory_path(pair, profile_id=profile_id)
    if not inventory_path.exists():
        raise FileNotFoundError(inventory_path)
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def get_srs_runtime_diagnostics(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
) -> dict:
    return _get_srs_runtime_diagnostics_use_case(
        paths,
        pair=pair,
        profile_id=profile_id,
    )


def semantic_admit_batch(
    paths: HelperPaths,
    *,
    payload: Mapping[str, object],
) -> dict:
    return _semantic_admit_batch_use_case(paths, payload=payload)


def _resolve_pair_set_top_n(*, pair: str, requested_top_n: Optional[int], purpose: str) -> int:
    policy = resolve_srs_pair_policy(pair)
    if requested_top_n is not None:
        return max(1, int(requested_top_n))
    if purpose == "bootstrap":
        return max(1, int(policy.bootstrap_top_n_default))
    return max(1, int(policy.refresh_top_n_default))


def _resolve_pair_feedback_window_size(*, pair: str, requested_size: Optional[int]) -> int:
    if requested_size is not None:
        return max(1, int(requested_size))
    policy = resolve_srs_pair_policy(pair)
    return max(1, int(policy.feedback_window_size_default))


def _resolve_pair_initial_active_count(*, pair: str, requested_count: Optional[int]) -> int:
    if requested_count is not None:
        return max(1, int(requested_count))
    policy = resolve_srs_pair_policy(pair)
    return max(1, int(policy.initial_active_count_default))


def _ensure_pair_requirements(
    *,
    pair: str,
    jmdict_path: Optional[Path],
    translation_dict_path: Optional[Path],
    require_frequency_db: bool,
    set_source_db: Optional[Path],
    check_seed_resources: bool = False,
    check_rulegen_resources: bool = False,
) -> None:
    lp_capabilities = __import__(
        "lexishift_core.helper.lp_capabilities",
        fromlist=["resolve_pair_capability"],
    )
    capability = lp_capabilities.resolve_pair_capability(pair)
    requires_jmdict = (check_seed_resources and capability.requires_jmdict_for_seed) or (
        check_rulegen_resources and capability.requires_jmdict_for_rulegen
    )
    if requires_jmdict:
        if jmdict_path is None:
            raise ValueError(f"Missing JMDict path for pair '{pair}'.")
        if not jmdict_path.exists():
            raise FileNotFoundError(jmdict_path)
    requires_translation_dictionary = (
        check_rulegen_resources and capability.requires_translation_dictionary_for_rulegen
    )
    if requires_translation_dictionary:
        if translation_dict_path is None:
            raise ValueError(f"Missing translation dictionary path for pair '{pair}'.")
        if not translation_dict_path.exists():
            raise FileNotFoundError(translation_dict_path)
    if require_frequency_db:
        if set_source_db is None:
            raise ValueError(f"Missing frequency source DB for pair '{pair}'.")
        if not set_source_db.exists():
            raise FileNotFoundError(set_source_db)
    should_validate_frequency_db = bool(
        set_source_db is not None
        and set_source_db.exists()
        and (require_frequency_db or check_seed_resources)
    )
    if should_validate_frequency_db:
        sqlite_store = __import__(
            "lexishift_core.frequency.sqlite_store",
            fromlist=["validate_frequency_sqlite_db"],
        )
        sqlite_store.validate_frequency_sqlite_db(set_source_db, table="frequency")


def run_rulegen_job(
    paths: HelperPaths,
    *,
    config: RulegenJobConfig,
) -> dict:
    return _run_rulegen_job_use_case(
        paths,
        config=config,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_resources_fn=_resolve_pair_resources,
        ensure_pair_requirements_fn=_ensure_pair_requirements,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_settings_fn=_ensure_settings,
        ensure_store_fn=_ensure_store,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
        update_status_fn=_update_status,
        run_rulegen_for_pair_fn=run_rulegen_for_pair,
        write_rulegen_outputs_fn=write_rulegen_outputs,
    )


def plan_srs_set(
    paths: HelperPaths,
    *,
    config: SetPlanningJobConfig,
) -> dict:
    return _plan_srs_set_use_case(
        paths,
        config=config,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_store_fn=_ensure_store,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_initial_active_count_fn=_resolve_pair_initial_active_count,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
    )


def preview_srs_admission(
    paths: HelperPaths,
    *,
    config: SetAdmissionPreviewJobConfig,
) -> dict:
    return _preview_srs_admission_use_case(
        paths,
        config=config,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_store_fn=_ensure_store,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_initial_active_count_fn=_resolve_pair_initial_active_count,
        resolve_pair_resources_fn=_resolve_pair_resources,
        ensure_pair_requirements_fn=_ensure_pair_requirements,
        count_items_for_pair_fn=_count_items_for_pair,
        build_set_plan_payload_fn=_build_set_plan_payload,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
        initialize_store_from_frequency_list_with_report_fn=initialize_store_from_frequency_list_with_report,
    )


def initialize_srs_set(
    paths: HelperPaths,
    *,
    config: SetInitializationJobConfig,
) -> dict:
    return _initialize_srs_set_use_case(
        paths,
        config=config,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_initial_active_count_fn=_resolve_pair_initial_active_count,
        resolve_pair_resources_fn=_resolve_pair_resources,
        ensure_pair_requirements_fn=_ensure_pair_requirements,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_settings_fn=_ensure_settings,
        ensure_store_fn=_ensure_store,
        count_items_for_pair_fn=_count_items_for_pair,
        build_set_plan_payload_fn=_build_set_plan_payload,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
        initialize_store_from_frequency_list_with_report_fn=initialize_store_from_frequency_list_with_report,
        run_rulegen_for_pair_fn=run_rulegen_for_pair,
        write_rulegen_outputs_fn=write_rulegen_outputs,
        update_status_fn=_update_status,
    )


def plan_srs_rebalance(
    paths: HelperPaths,
    *,
    config: SrsRebalanceJobConfig,
) -> dict:
    return _plan_srs_rebalance_use_case(
        paths,
        config=config,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_resources_fn=_resolve_pair_resources,
        ensure_pair_requirements_fn=_ensure_pair_requirements,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_settings_fn=_ensure_settings,
        ensure_store_fn=_ensure_store,
        count_items_for_pair_fn=_count_items_for_pair,
        build_set_plan_payload_fn=_build_set_plan_payload,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
        build_seed_candidates_fn=build_seed_candidates,
    )


def refresh_srs_set(
    paths: HelperPaths,
    *,
    config: SrsRefreshJobConfig,
) -> dict:
    return _refresh_srs_set_use_case(
        paths,
        config=config,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_feedback_window_size_fn=_resolve_pair_feedback_window_size,
        resolve_pair_resources_fn=_resolve_pair_resources,
        ensure_pair_requirements_fn=_ensure_pair_requirements,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_settings_fn=_ensure_settings,
        ensure_store_fn=_ensure_store,
        count_items_for_pair_fn=_count_items_for_pair,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
        build_seed_candidates_fn=build_seed_candidates,
        run_rulegen_for_pair_fn=run_rulegen_for_pair,
        write_rulegen_outputs_fn=write_rulegen_outputs,
        update_status_fn=_update_status,
    )


def apply_srs_rebalance(
    paths: HelperPaths,
    *,
    config: SrsRebalanceJobConfig,
) -> dict:
    return _apply_srs_rebalance_use_case(
        paths,
        config=config,
        resolve_pair_set_top_n_fn=_resolve_pair_set_top_n,
        resolve_pair_resources_fn=_resolve_pair_resources,
        ensure_pair_requirements_fn=_ensure_pair_requirements,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_settings_fn=_ensure_settings,
        ensure_store_fn=_ensure_store,
        count_items_for_pair_fn=_count_items_for_pair,
        build_set_plan_payload_fn=_build_set_plan_payload,
        resolve_stopwords_path_fn=_resolve_stopwords_path,
        build_seed_candidates_fn=build_seed_candidates,
        run_rulegen_for_pair_fn=run_rulegen_for_pair,
        write_rulegen_outputs_fn=write_rulegen_outputs,
        update_status_fn=_update_status,
    )


def apply_feedback(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    rating: str,
    profile_id: str = "default",
    source_type: str = SOURCE_EXTENSION,
) -> None:
    _apply_feedback_use_case(
        paths,
        pair=pair,
        lemma=lemma,
        rating=rating,
        profile_id=profile_id,
        source_type=source_type,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_settings_fn=_ensure_settings,
        ensure_store_fn=_ensure_store,
    )


def apply_exposure(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    profile_id: str = "default",
    source_type: str = SOURCE_EXTENSION,
) -> None:
    _apply_exposure_use_case(
        paths,
        pair=pair,
        lemma=lemma,
        profile_id=profile_id,
        source_type=source_type,
        resolve_profile_id_fn=_resolve_profile_id,
        ensure_store_fn=_ensure_store,
    )


def reset_srs_data(
    paths: HelperPaths,
    *,
    pair: Optional[str] = None,
    profile_id: str = "default",
) -> dict:
    return _reset_srs_data_use_case(
        paths,
        pair=pair,
        profile_id=profile_id,
        resolve_profile_id_fn=_resolve_profile_id,
    )
