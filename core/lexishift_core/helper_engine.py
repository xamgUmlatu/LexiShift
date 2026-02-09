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
from lexishift_core.lp_capabilities import (
    default_freedict_de_en_path,
    default_frequency_db_path,
    default_jmdict_path,
    pair_requirements,
    resolve_pair_capability,
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
    jmdict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
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
    jmdict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
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
    jmdict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
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
    capability = resolve_pair_capability(pair)
    normalized_pair = capability.pair
    normalized_profile_id = _resolve_profile_id(paths, profile_id=profile_id)
    resolved_jmdict_path, resolved_freedict_de_en_path, resolved_set_source_db = _resolve_pair_resources(
        paths,
        pair=normalized_pair,
        jmdict_path=None,
        freedict_de_en_path=None,
        set_source_db=None,
    )
    missing_inputs: list[dict[str, object]] = []
    if capability.requires_jmdict_for_seed or capability.requires_jmdict_for_rulegen:
        if not resolved_jmdict_path:
            missing_inputs.append({"type": "jmdict_path", "path": None})
        elif not resolved_jmdict_path.exists():
            missing_inputs.append({"type": "jmdict_path", "path": str(resolved_jmdict_path)})
    if capability.requires_freedict_de_en_for_rulegen:
        if not resolved_freedict_de_en_path:
            missing_inputs.append({"type": "freedict_de_en_path", "path": None})
        elif not resolved_freedict_de_en_path.exists():
            missing_inputs.append(
                {"type": "freedict_de_en_path", "path": str(resolved_freedict_de_en_path)}
            )
    if not resolved_set_source_db:
        missing_inputs.append({"type": "set_source_db", "path": None})
    elif not resolved_set_source_db.exists():
        missing_inputs.append({"type": "set_source_db", "path": str(resolved_set_source_db)})

    store_path = paths.srs_store_path_for(normalized_profile_id)
    ruleset_path = paths.ruleset_path(normalized_pair, profile_id=normalized_profile_id)
    snapshot_path = paths.snapshot_path(normalized_pair, profile_id=normalized_profile_id)
    status_path = paths.srs_status_path_for(normalized_profile_id)
    diagnostics = {
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "requirements": pair_requirements(normalized_pair),
        "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
        "jmdict_exists": bool(resolved_jmdict_path and resolved_jmdict_path.exists()),
        "freedict_de_en_path": (
            str(resolved_freedict_de_en_path) if resolved_freedict_de_en_path else None
        ),
        "freedict_de_en_exists": bool(
            resolved_freedict_de_en_path and resolved_freedict_de_en_path.exists()
        ),
        "set_source_db": str(resolved_set_source_db) if resolved_set_source_db else None,
        "set_source_db_exists": bool(resolved_set_source_db and resolved_set_source_db.exists()),
        "missing_inputs": missing_inputs,
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


def _resolve_pair_resources(
    paths: HelperPaths,
    *,
    pair: str,
    jmdict_path: Optional[Path],
    freedict_de_en_path: Optional[Path],
    set_source_db: Optional[Path],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    capability = resolve_pair_capability(pair)
    resolved_jmdict = (
        Path(jmdict_path)
        if jmdict_path is not None
        else default_jmdict_path(capability.pair, language_packs_dir=paths.language_packs_dir)
    )
    resolved_freedict_de_en = (
        Path(freedict_de_en_path)
        if freedict_de_en_path is not None
        else default_freedict_de_en_path(
            capability.pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    resolved_frequency_db = (
        Path(set_source_db)
        if set_source_db is not None
        else default_frequency_db_path(capability.pair, frequency_packs_dir=paths.frequency_packs_dir)
    )
    return resolved_jmdict, resolved_freedict_de_en, resolved_frequency_db


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
    capability = resolve_pair_capability(config.pair)
    pair = capability.pair
    resolved_jmdict_path, resolved_freedict_de_en_path, resolved_set_source_db = _resolve_pair_resources(
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
    _ensure_pair_requirements(
        pair=pair,
        jmdict_path=resolved_jmdict_path,
        freedict_de_en_path=resolved_freedict_de_en_path,
        require_frequency_db=False,
        set_source_db=resolved_set_source_db,
        check_seed_resources=should_seed_from_frequency,
        check_rulegen_resources=True,
    )
    profile_id = _resolve_profile_id(paths, profile_id=config.profile_id)
    settings = _ensure_settings(paths, persist_missing=config.persist_store)
    store = _ensure_store(paths, profile_id=profile_id, persist_missing=config.persist_store)
    diagnostics: dict[str, object] | None = None
    sampling_result = None
    set_init_config = None
    stopwords_path = _resolve_stopwords_path(paths, pair=pair)
    if resolved_set_source_db and resolved_set_source_db.exists():
        set_init_config = SetInitializationConfig(
            frequency_db=resolved_set_source_db,
            jmdict_path=resolved_jmdict_path,
            top_n=config.set_top_n,
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
    store, output = run_rulegen_for_pair(
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
        write_rulegen_outputs(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            rules=output.rules,
            snapshot=output.snapshot,
        )
    if config.update_status:
        _update_status(
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
    pair = str(config.pair or "").strip()
    if not pair:
        raise ValueError("Missing pair.")
    capability = resolve_pair_capability(pair)
    resolved_jmdict_path, resolved_freedict_de_en_path, resolved_set_source_db = _resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=config.jmdict_path,
        freedict_de_en_path=config.freedict_de_en_path,
        set_source_db=config.set_source_db,
    )
    _ensure_pair_requirements(
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

    _updated_store, rulegen_output = run_rulegen_for_pair(
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
    pair = str(config.pair or "").strip()
    if not pair:
        raise ValueError("Missing pair.")
    capability = resolve_pair_capability(pair)
    resolved_jmdict_path, resolved_freedict_de_en_path, resolved_set_source_db = _resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=config.jmdict_path,
        freedict_de_en_path=config.freedict_de_en_path,
        set_source_db=config.set_source_db,
    )
    _ensure_pair_requirements(
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
        frequency_db=resolved_set_source_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=max(1, int(config.set_top_n)),
            jmdict_path=resolved_jmdict_path,
            stopwords_path=stopwords_path,
            require_jmdict=capability.requires_jmdict_for_seed,
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
            jmdict_path=resolved_jmdict_path,
            freedict_de_en_path=resolved_freedict_de_en_path,
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
