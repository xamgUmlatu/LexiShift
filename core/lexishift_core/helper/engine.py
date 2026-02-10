from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Optional

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
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
from lexishift_core.helper.use_cases.refresh_set import (
    refresh_srs_set as _refresh_srs_set_use_case,
)
from lexishift_core.helper.use_cases.reset import reset_srs_data as _reset_srs_data_use_case
from lexishift_core.helper.use_cases.rulegen_job import run_rulegen_job as _run_rulegen_job_use_case
from lexishift_core.helper.use_cases.runtime_diagnostics import get_srs_runtime_diagnostics
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
from lexishift_core.srs.seed import build_seed_candidates
from lexishift_core.srs.set_strategy import (
    OBJECTIVE_BOOTSTRAP,
    STRATEGY_FREQUENCY_BOOTSTRAP,
)
from lexishift_core.srs.source import SOURCE_EXTENSION
from lexishift_core.srs.time import now_utc


@dataclass(frozen=True)
class RulegenJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
    profile_id: str = "default"
    set_source_db: Optional[Path] = None
    set_top_n: Optional[int] = None
    confidence_threshold: float = 0.0
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
    freedict_de_en_path: Optional[Path] = None
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
class SrsRefreshJobConfig:
    pair: str
    jmdict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
    profile_id: str = "default"
    set_top_n: Optional[int] = None
    feedback_window_size: Optional[int] = None
    max_active_items: Optional[int] = None
    max_new_items: Optional[int] = None
    persist_store: bool = True
    trigger: str = "manual"
    profile_context: Optional[Mapping[str, object]] = None


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
    freedict_de_en_path: Optional[Path],
    require_frequency_db: bool,
    set_source_db: Optional[Path],
    check_seed_resources: bool = False,
    check_rulegen_resources: bool = False,
) -> None:
    capability = resolve_pair_capability(pair)
    requires_jmdict = (
        (check_seed_resources and capability.requires_jmdict_for_seed)
        or (check_rulegen_resources and capability.requires_jmdict_for_rulegen)
    )
    if requires_jmdict:
        if jmdict_path is None:
            raise ValueError(f"Missing JMDict path for pair '{pair}'.")
        if not jmdict_path.exists():
            raise FileNotFoundError(jmdict_path)
    requires_freedict_de_en = (
        check_rulegen_resources and capability.requires_freedict_de_en_for_rulegen
    )
    if requires_freedict_de_en:
        if freedict_de_en_path is None:
            raise ValueError(f"Missing FreeDict DE->EN path for pair '{pair}'.")
        if not freedict_de_en_path.exists():
            raise FileNotFoundError(freedict_de_en_path)
    if require_frequency_db:
        if set_source_db is None:
            raise ValueError(f"Missing frequency source DB for pair '{pair}'.")
        if not set_source_db.exists():
            raise FileNotFoundError(set_source_db)


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
