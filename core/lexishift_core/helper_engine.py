from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.helper_paths import HelperPaths
from lexishift_core.helper_rulegen import (
    RulegenConfig,
    SetInitializationConfig,
    initialize_store_from_frequency_list_with_report,
    run_rulegen_for_pair,
    write_rulegen_outputs,
)
from lexishift_core.helper_status import HelperStatus, load_status, save_status
from lexishift_core.srs_admission_refresh import (
    AdmissionRefreshPolicy,
    admission_refresh_result_to_dict,
    apply_admission_refresh,
)
from lexishift_core.srs import SrsSettings, SrsStore, load_srs_settings, load_srs_store, save_srs_settings, save_srs_store
from lexishift_core.srs_seed import (
    SeedSelectionConfig,
    build_seed_candidates,
    seed_to_selector_candidates,
)
from lexishift_core.srs_set_planner import SrsSetPlanRequest, build_srs_set_plan, plan_to_dict
from lexishift_core.srs_set_strategy import (
    OBJECTIVE_BOOTSTRAP,
    STRATEGY_FREQUENCY_BOOTSTRAP,
)
from lexishift_core.srs_set_policy import resolve_set_sizing_policy
from lexishift_core.srs_sampling import sample_store_items, sampling_result_to_dict
from lexishift_core.srs_signal_queue import (
    SIGNAL_EXPOSURE,
    SIGNAL_FEEDBACK,
    SrsSignalEvent,
    append_signal_event,
    load_signal_events,
    summarize_signal_events,
)
from lexishift_core.srs_source import SOURCE_EXTENSION, SOURCE_INITIAL_SET
from lexishift_core.srs_store_ops import record_exposure, record_feedback
from lexishift_core.srs_time import now_utc


@dataclass(frozen=True)
class RulegenJobConfig:
    pair: str
    jmdict_path: Path
    profile_id: str = "default"
    set_source_db: Optional[Path] = None
    set_top_n: int = 2000
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
    jmdict_path: Path
    set_source_db: Path
    profile_id: str = "default"
    set_top_n: int = 800
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
    set_top_n: int = 800
    bootstrap_top_n: Optional[int] = None
    initial_active_count: Optional[int] = None
    max_active_items_hint: Optional[int] = None
    replace_pair: bool = False
    profile_context: Optional[Mapping[str, object]] = None
    trigger: str = "manual"


@dataclass(frozen=True)
class SrsRefreshJobConfig:
    pair: str
    jmdict_path: Path
    set_source_db: Path
    profile_id: str = "default"
    set_top_n: int = 2000
    feedback_window_size: int = 100
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


def get_srs_runtime_diagnostics(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
) -> dict:
    normalized_pair = str(pair or "").strip() or "en-ja"
    normalized_profile_id = _resolve_profile_id(paths, profile_id=profile_id)
    store_path = paths.srs_store_path_for(normalized_profile_id)
    ruleset_path = paths.ruleset_path(normalized_pair, profile_id=normalized_profile_id)
    snapshot_path = paths.snapshot_path(normalized_pair, profile_id=normalized_profile_id)
    status_path = paths.srs_status_path_for(normalized_profile_id)
    diagnostics = {
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "store_path": str(store_path),
        "store_exists": store_path.exists(),
        "store_items_total": 0,
        "store_items_for_pair": 0,
        "store_error": None,
        "ruleset_path": str(ruleset_path),
        "ruleset_exists": ruleset_path.exists(),
        "ruleset_rules_count": 0,
        "ruleset_error": None,
        "snapshot_path": str(snapshot_path),
        "snapshot_exists": snapshot_path.exists(),
        "snapshot_target_count": 0,
        "snapshot_error": None,
        "status": load_status(status_path).__dict__,
    }
    if diagnostics["store_exists"]:
        try:
            store = load_srs_store(store_path)
            diagnostics["store_items_total"] = len(store.items)
            diagnostics["store_items_for_pair"] = len(
                [item for item in store.items if item.language_pair == normalized_pair]
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics["store_error"] = str(exc)
    if diagnostics["ruleset_exists"]:
        try:
            ruleset_payload = json.loads(ruleset_path.read_text(encoding="utf-8"))
            rules = ruleset_payload.get("rules", [])
            diagnostics["ruleset_rules_count"] = len(rules) if isinstance(rules, list) else 0
        except Exception as exc:  # noqa: BLE001
            diagnostics["ruleset_error"] = str(exc)
    if diagnostics["snapshot_exists"]:
        try:
            snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            stats = snapshot_payload.get("stats", {})
            target_count = stats.get("target_count")
            if target_count is None and isinstance(snapshot_payload.get("targets"), list):
                target_count = len(snapshot_payload.get("targets", []))
            diagnostics["snapshot_target_count"] = int(target_count or 0)
        except Exception as exc:  # noqa: BLE001
            diagnostics["snapshot_error"] = str(exc)
    return diagnostics


def _target_language_from_pair(pair: str) -> str:
    normalized = str(pair or "").strip()
    parts = normalized.split("-", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip().lower()
    return ""


def _resolve_stopwords_path(paths: HelperPaths, *, pair: str) -> Optional[Path]:
    target_lang = _target_language_from_pair(pair)
    if not target_lang:
        return None
    candidates = (
        paths.srs_dir / f"stopwords-{target_lang}.json",
        paths.srs_dir / "stopwords" / f"stopwords-{target_lang}.json",
        paths.data_root / "stopwords" / f"stopwords-{target_lang}.json",
        paths.language_packs_dir / f"stopwords-{target_lang}.json",
    )
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def run_rulegen_job(
    paths: HelperPaths,
    *,
    config: RulegenJobConfig,
) -> dict:
    if not config.jmdict_path.exists():
        raise FileNotFoundError(config.jmdict_path)
    profile_id = _resolve_profile_id(paths, profile_id=config.profile_id)
    settings = _ensure_settings(paths, persist_missing=config.persist_store)
    store = _ensure_store(paths, profile_id=profile_id, persist_missing=config.persist_store)
    diagnostics: dict[str, object] | None = None
    sampling_result = None
    set_init_config = None
    stopwords_path = _resolve_stopwords_path(paths, pair=config.pair)
    if config.set_source_db and config.set_source_db.exists():
        set_init_config = SetInitializationConfig(
            frequency_db=config.set_source_db,
            jmdict_path=config.jmdict_path,
            top_n=config.set_top_n,
            language_pair=config.pair,
            stopwords_path=stopwords_path,
        )
    rulegen_config = RulegenConfig(
        language_pair=config.pair,
        confidence_threshold=config.confidence_threshold,
        max_snapshot_targets=config.snapshot_targets,
        max_snapshot_sources=config.snapshot_sources,
    )
    targets_override: list[str] | None = None
    if config.sample_count is not None:
        sampling_result = sample_store_items(
            store,
            pair=config.pair,
            sample_count=config.sample_count,
            strategy=config.sample_strategy,
            seed=config.sample_seed,
        )
        targets_override = list(sampling_result.sampled_lemmas)
    if config.debug:
        missing_inputs = []
        if config.set_source_db and not config.set_source_db.exists():
            missing_inputs.append(
                {"type": "set_source_db", "path": str(config.set_source_db)}
            )
        diagnostics = {
            "pair": config.pair,
            "jmdict_path": str(config.jmdict_path),
            "jmdict_exists": config.jmdict_path.exists(),
            "set_source_db": str(config.set_source_db) if config.set_source_db else None,
            "set_source_db_exists": bool(config.set_source_db and config.set_source_db.exists()),
            "stopwords_path": str(stopwords_path) if stopwords_path else None,
            "stopwords_exists": bool(stopwords_path and stopwords_path.exists()),
            "missing_inputs": missing_inputs,
            "store_items": len(store.items),
            "store_items_for_pair": len([item for item in store.items if item.language_pair == config.pair]),
            "store_sample": [
                item.lemma for item in store.items if item.language_pair == config.pair
            ][: max(1, int(config.debug_sample_size))],
        }
        if sampling_result is not None:
            diagnostics["sampling"] = sampling_result_to_dict(sampling_result)
    store, output = run_rulegen_for_pair(
        paths=paths,
        pair=config.pair,
        profile_id=profile_id,
        store=store,
        settings=settings,
        jmdict_path=config.jmdict_path,
        set_init_config=set_init_config,
        rulegen_config=rulegen_config,
        targets_override=targets_override,
        initialize_if_empty=config.initialize_if_empty,
        persist_store=config.persist_store,
    )
    if config.persist_outputs:
        write_rulegen_outputs(
            paths=paths,
            pair=config.pair,
            profile_id=profile_id,
            rules=output.rules,
            snapshot=output.snapshot,
        )
    if config.update_status:
        _update_status(
            paths=paths,
            profile_id=profile_id,
            pair=config.pair,
            rule_count=len(output.rules),
            target_count=output.target_count,
            error=None,
        )
    response = {
        "pair": config.pair,
        "profile_id": profile_id,
        "targets": output.target_count,
        "rules": len(output.rules),
        "snapshot": output.snapshot,
        "snapshot_path": (
            str(paths.snapshot_path(config.pair, profile_id=profile_id))
            if config.persist_outputs
            else None
        ),
        "ruleset_path": (
            str(paths.ruleset_path(config.pair, profile_id=profile_id))
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


def _count_items_for_pair(store: SrsStore, pair: str) -> int:
    return len([item for item in store.items if item.language_pair == pair])


def _build_set_plan_payload(
    *,
    pair: str,
    strategy: str,
    objective: str,
    set_top_n: int,
    initial_active_count: int,
    max_active_items_hint: int,
    replace_pair: bool,
    trigger: str,
    existing_items_for_pair: int,
    profile_context: Optional[Mapping[str, object]],
    signal_summary: Mapping[str, object],
    policy_notes: Sequence[str] = (),
) -> dict[str, object]:
    plan = build_srs_set_plan(
        SrsSetPlanRequest(
            pair=pair,
            strategy=strategy,
            objective=objective,
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            max_active_items_hint=max_active_items_hint,
            replace_pair=replace_pair,
            existing_items_for_pair=existing_items_for_pair,
            trigger=trigger,
            profile_context=profile_context or {},
            signal_summary=signal_summary,
        )
    )
    payload = plan_to_dict(plan)
    if policy_notes:
        merged_notes = list(payload.get("notes", []))
        for note in policy_notes:
            if note and note not in merged_notes:
                merged_notes.append(note)
        payload["notes"] = merged_notes
    diagnostics = dict(payload.get("diagnostics", {}))
    diagnostics["bootstrap_top_n"] = max(1, int(set_top_n))
    diagnostics["initial_active_count"] = max(1, int(initial_active_count))
    diagnostics["max_active_items_hint"] = max(0, int(max_active_items_hint))
    payload["diagnostics"] = diagnostics
    return payload


def plan_srs_set(
    paths: HelperPaths,
    *,
    config: SetPlanningJobConfig,
) -> dict:
    pair = str(config.pair or "").strip()
    if not pair:
        raise ValueError("Missing pair.")

    profile_id = _resolve_profile_id(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    store = _ensure_store(paths, profile_id=profile_id, persist_missing=False)
    existing_items_for_pair = _count_items_for_pair(store, pair)
    sizing_policy = resolve_set_sizing_policy(
        bootstrap_top_n=config.bootstrap_top_n
        if config.bootstrap_top_n is not None
        else config.set_top_n,
        initial_active_count=config.initial_active_count,
        max_active_items_hint=config.max_active_items_hint,
    )
    stopwords_path = _resolve_stopwords_path(paths, pair=pair)
    signal_summary = summarize_signal_events(
        paths.srs_signal_queue_path_for(profile_id),
        pair=pair,
    )
    plan_payload = _build_set_plan_payload(
        pair=pair,
        strategy=config.strategy,
        objective=config.objective,
        set_top_n=sizing_policy.bootstrap_top_n_effective,
        initial_active_count=sizing_policy.initial_active_count_effective,
        max_active_items_hint=sizing_policy.max_active_items_hint or 0,
        replace_pair=config.replace_pair,
        trigger=config.trigger,
        existing_items_for_pair=existing_items_for_pair,
        profile_context=config.profile_context,
        signal_summary=signal_summary,
        policy_notes=sizing_policy.notes,
    )
    return {
        "pair": pair,
        "profile_id": profile_id,
        "set_top_n": sizing_policy.bootstrap_top_n_effective,
        "bootstrap_top_n": sizing_policy.bootstrap_top_n_effective,
        "initial_active_count": sizing_policy.initial_active_count_effective,
        "max_active_items_hint": sizing_policy.max_active_items_hint,
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        "existing_items_for_pair": existing_items_for_pair,
        "signal_summary": signal_summary,
        "plan": plan_payload,
    }


def initialize_srs_set(
    paths: HelperPaths,
    *,
    config: SetInitializationJobConfig,
) -> dict:
    if not config.jmdict_path.exists():
        raise FileNotFoundError(config.jmdict_path)
    if not config.set_source_db.exists():
        raise FileNotFoundError(config.set_source_db)

    pair = str(config.pair or "").strip()
    if not pair:
        raise ValueError("Missing pair.")

    profile_id = _resolve_profile_id(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    settings = _ensure_settings(paths, persist_missing=True)
    store = _ensure_store(paths, profile_id=profile_id, persist_missing=True)
    before_pair_count = _count_items_for_pair(store, pair)
    sizing_policy = resolve_set_sizing_policy(
        bootstrap_top_n=config.bootstrap_top_n
        if config.bootstrap_top_n is not None
        else config.set_top_n,
        initial_active_count=config.initial_active_count,
        max_active_items_hint=config.max_active_items_hint,
    )
    stopwords_path = _resolve_stopwords_path(paths, pair=pair)
    signal_summary = summarize_signal_events(
        paths.srs_signal_queue_path_for(profile_id),
        pair=pair,
    )
    plan_payload = _build_set_plan_payload(
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

    updated_store, init_report = initialize_store_from_frequency_list_with_report(
        base_store,
        config=SetInitializationConfig(
            frequency_db=config.set_source_db,
            jmdict_path=config.jmdict_path,
            top_n=sizing_policy.bootstrap_top_n_effective,
            initial_active_count=sizing_policy.initial_active_count_effective,
            language_pair=pair,
            stopwords_path=stopwords_path,
        ),
    )
    save_srs_store(updated_store, paths.srs_store_path_for(profile_id))

    _updated_store, rulegen_output = run_rulegen_for_pair(
        paths=paths,
        pair=pair,
        profile_id=profile_id,
        store=updated_store,
        settings=settings,
        jmdict_path=config.jmdict_path,
        rulegen_config=RulegenConfig(language_pair=pair),
        initialize_if_empty=False,
        persist_store=False,
    )
    write_rulegen_outputs(
        paths=paths,
        pair=pair,
        profile_id=profile_id,
        rules=rulegen_output.rules,
        snapshot=rulegen_output.snapshot,
    )
    _update_status(
        paths=paths,
        profile_id=profile_id,
        pair=pair,
        rule_count=len(rulegen_output.rules),
        target_count=rulegen_output.target_count,
        error=None,
    )

    after_pair_count = _count_items_for_pair(updated_store, pair)
    added_items = max(0, after_pair_count - (0 if config.replace_pair else before_pair_count))
    return {
        "pair": pair,
        "profile_id": profile_id,
        "set_top_n": sizing_policy.bootstrap_top_n_effective,
        "bootstrap_top_n": sizing_policy.bootstrap_top_n_effective,
        "initial_active_count": sizing_policy.initial_active_count_effective,
        "max_active_items_hint": sizing_policy.max_active_items_hint,
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


def refresh_srs_set(
    paths: HelperPaths,
    *,
    config: SrsRefreshJobConfig,
) -> dict:
    if not config.jmdict_path.exists():
        raise FileNotFoundError(config.jmdict_path)
    if not config.set_source_db.exists():
        raise FileNotFoundError(config.set_source_db)

    pair = str(config.pair or "").strip()
    if not pair:
        raise ValueError("Missing pair.")

    profile_id = _resolve_profile_id(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    settings = _ensure_settings(paths, persist_missing=True)
    store = _ensure_store(paths, profile_id=profile_id, persist_missing=True)
    before_pair_count = _count_items_for_pair(store, pair)
    stopwords_path = _resolve_stopwords_path(paths, pair=pair)
    selection = build_seed_candidates(
        frequency_db=config.set_source_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=max(1, int(config.set_top_n)),
            jmdict_path=config.jmdict_path,
            stopwords_path=stopwords_path,
        ),
    )
    selector_candidates = seed_to_selector_candidates(selection)
    signal_events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    refresh_policy = AdmissionRefreshPolicy(
        feedback_window_size=max(1, int(config.feedback_window_size)),
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
        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))

    after_pair_count = _count_items_for_pair(updated_store, pair)
    added_items = max(0, after_pair_count - before_pair_count)
    published_rulegen = None
    if refresh_result.applied:
        _updated_store, rulegen_output = run_rulegen_for_pair(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            store=updated_store,
            settings=settings,
            jmdict_path=config.jmdict_path,
            rulegen_config=RulegenConfig(language_pair=pair),
            initialize_if_empty=False,
            persist_store=False,
        )
        write_rulegen_outputs(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            rules=rulegen_output.rules,
            snapshot=rulegen_output.snapshot,
        )
        _update_status(
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
        "set_top_n": max(1, int(config.set_top_n)),
        "feedback_window_size": max(1, int(config.feedback_window_size)),
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


def apply_feedback(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    rating: str,
    profile_id: str = "default",
    source_type: str = SOURCE_EXTENSION,
) -> None:
    normalized_profile_id = _resolve_profile_id(paths, profile_id=profile_id)
    store = _ensure_store(paths, profile_id=normalized_profile_id)
    normalized_pair = str(pair or "").strip()
    normalized_lemma = str(lemma or "").strip()
    normalized_source_type = str(source_type or SOURCE_EXTENSION).strip() or SOURCE_EXTENSION
    store = record_feedback(
        store,
        language_pair=normalized_pair,
        lemma=normalized_lemma,
        rating=rating,
        create_if_missing=True,
        source_type=normalized_source_type,
    )
    save_srs_store(store, paths.srs_store_path_for(normalized_profile_id))
    if normalized_pair and normalized_lemma:
        append_signal_event(
            paths.srs_signal_queue_path_for(normalized_profile_id),
            SrsSignalEvent(
                event_type=SIGNAL_FEEDBACK,
                pair=normalized_pair,
                lemma=normalized_lemma,
                source_type=normalized_source_type,
                rating=rating,
            ),
        )


def apply_exposure(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    profile_id: str = "default",
    source_type: str = SOURCE_EXTENSION,
) -> None:
    normalized_profile_id = _resolve_profile_id(paths, profile_id=profile_id)
    store = _ensure_store(paths, profile_id=normalized_profile_id)
    normalized_pair = str(pair or "").strip()
    normalized_lemma = str(lemma or "").strip()
    normalized_source_type = str(source_type or SOURCE_EXTENSION).strip() or SOURCE_EXTENSION
    store = record_exposure(
        store,
        language_pair=normalized_pair,
        lemma=normalized_lemma,
        create_if_missing=True,
        source_type=normalized_source_type,
    )
    save_srs_store(store, paths.srs_store_path_for(normalized_profile_id))
    if normalized_pair and normalized_lemma:
        append_signal_event(
            paths.srs_signal_queue_path_for(normalized_profile_id),
            SrsSignalEvent(
                event_type=SIGNAL_EXPOSURE,
                pair=normalized_pair,
                lemma=normalized_lemma,
                source_type=normalized_source_type,
            ),
        )


def _remove_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    path.unlink()
    return True


def reset_srs_data(
    paths: HelperPaths,
    *,
    pair: Optional[str] = None,
    profile_id: str = "default",
) -> dict:
    normalized_profile_id = _resolve_profile_id(paths, profile_id=profile_id)
    scoped_pair = str(pair or "").strip() or None
    profile_store_path = paths.srs_store_path_for(normalized_profile_id)
    profile_srs_dir = paths.profile_srs_dir(normalized_profile_id)
    profile_status_path = paths.srs_status_path_for(normalized_profile_id)

    removed_items = 0
    remaining_items = 0
    if profile_store_path.exists():
        store = load_srs_store(profile_store_path)
        if scoped_pair:
            kept_items = tuple(item for item in store.items if item.language_pair != scoped_pair)
        else:
            kept_items = tuple()
        removed_items = len(store.items) - len(kept_items)
        remaining_items = len(kept_items)
        save_srs_store(SrsStore(items=kept_items, version=store.version), profile_store_path)
    else:
        save_srs_store(SrsStore(), profile_store_path)

    removed_snapshots = 0
    removed_rulesets = 0
    if scoped_pair:
        if _remove_file(paths.snapshot_path(scoped_pair, profile_id=normalized_profile_id)):
            removed_snapshots += 1
        if _remove_file(paths.ruleset_path(scoped_pair, profile_id=normalized_profile_id)):
            removed_rulesets += 1
    else:
        for snapshot in profile_srs_dir.glob("srs_rulegen_snapshot_*.json"):
            if _remove_file(snapshot):
                removed_snapshots += 1
        for ruleset in profile_srs_dir.glob("srs_ruleset_*.json"):
            if _remove_file(ruleset):
                removed_rulesets += 1

    status = load_status(profile_status_path)
    save_status(
        HelperStatus(
            version=status.version,
            helper_version=status.helper_version,
            last_run_at=now_utc().isoformat(),
            last_error=None,
            last_pair=scoped_pair,
            last_rule_count=0,
            last_target_count=0,
        ),
        profile_status_path,
    )

    return {
        "pair": scoped_pair or "all",
        "profile_id": normalized_profile_id,
        "removed_items": removed_items,
        "remaining_items": remaining_items,
        "removed_snapshots": removed_snapshots,
        "removed_rulesets": removed_rulesets,
    }
