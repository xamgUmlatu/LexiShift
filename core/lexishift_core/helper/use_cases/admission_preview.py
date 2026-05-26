from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping, Sequence

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.pair_resources import resolve_pair_frequency_pack
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import SetInitializationConfig, SetInitializationReport
from lexishift_core.srs import SrsStore
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.selector import (
    SELECTION_POLICY_RESERVED_TOPIC_LANE,
    SELECTION_POLICY_TOP_N,
    SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
)
from lexishift_core.srs.set_policy import resolve_set_sizing_policy
from lexishift_core.srs.signal_queue import summarize_signal_events
from lexishift_core.srs.topic_overlay import resolve_preview_profile_topic_overlay

PREVIEW_SAMPLING_MODE_RANKED = "ranked"
PREVIEW_SAMPLING_MODE_RESERVED_TOPIC_LANE = "reserved_topic_lane"
PREVIEW_SAMPLING_MODE_WEIGHTED = "weighted_without_replacement"


def _build_frequency_resource_payload(
    paths: HelperPaths,
    *,
    pair: str,
    resolved_set_source_db: Path,
) -> dict[str, object]:
    resolved_frequency_pack = resolve_pair_frequency_pack(
        paths,
        pair=pair,
        set_source_db=resolved_set_source_db,
    )
    frequency_pack_path = (
        resolved_frequency_pack.path if resolved_frequency_pack else resolved_set_source_db
    )
    return {
        "set_source_db": str(resolved_set_source_db),
        "set_source_db_exists": resolved_set_source_db.exists(),
        "frequency_pack_path": str(frequency_pack_path) if frequency_pack_path else None,
        "frequency_pack_exists": bool(frequency_pack_path and frequency_pack_path.exists()),
        "frequency_pack_id": resolved_frequency_pack.pack_id if resolved_frequency_pack else None,
        "frequency_pack_provider": (
            resolved_frequency_pack.provider if resolved_frequency_pack else None
        ),
        "frequency_pos_source_profile": (
            resolved_frequency_pack.pos_source_profile if resolved_frequency_pack else None
        ),
    }


def preview_srs_admission(
    paths: HelperPaths,
    *,
    config,
    resolve_profile_id_fn: Callable[..., str],
    ensure_store_fn: Callable[..., SrsStore],
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_initial_active_count_fn: Callable[..., int],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    count_items_for_pair_fn: Callable[..., int],
    build_set_plan_payload_fn: Callable[..., dict[str, object]],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    initialize_store_from_frequency_list_with_report_fn: Callable[
        ...,
        tuple[SrsStore, SetInitializationReport],
    ],
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
    resolved_jmdict_path, _resolved_translation_dict_path, resolved_set_source_db = (
        resolve_pair_resources_fn(
            paths,
            pair=pair,
            jmdict_path=config.jmdict_path,
            translation_dict_path=None,
            set_source_db=config.set_source_db,
        )
    )
    ensure_pair_requirements_fn(
        pair=pair,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=None,
        require_frequency_db=True,
        set_source_db=resolved_set_source_db,
        check_seed_resources=True,
        check_rulegen_resources=False,
    )
    if resolved_set_source_db is None:
        raise ValueError(f"Missing frequency source DB for pair '{pair}'.")
    frequency_resource_payload = _build_frequency_resource_payload(
        paths,
        pair=pair,
        resolved_set_source_db=resolved_set_source_db,
    )

    profile_id = resolve_profile_id_fn(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    store = ensure_store_fn(paths, profile_id=profile_id, persist_missing=False)
    existing_items_for_pair = count_items_for_pair_fn(store, pair)
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
    profile_topic_overlay, profile_topic_overlay_diagnostics = (
        resolve_preview_profile_topic_overlay(
            paths,
            pair=pair,
            profile_context=config.profile_context,
        )
    )
    plan_payload = build_set_plan_payload_fn(
        pair=pair,
        strategy=config.strategy,
        objective=config.objective,
        set_top_n=sizing_policy.bootstrap_top_n_effective,
        initial_active_count=sizing_policy.initial_active_count_effective,
        max_active_items_hint=sizing_policy.max_active_items_hint or 0,
        replace_pair=False,
        trigger=config.trigger,
        existing_items_for_pair=existing_items_for_pair,
        profile_context=config.profile_context,
        signal_summary=signal_summary,
        policy_notes=sizing_policy.notes,
    )

    preview_count_requested = max(1, int(config.preview_count or 5))
    preview_payload = {
        "sample_count_requested": preview_count_requested,
        "sample_count_effective": 0,
        "sampling_mode": str(
            getattr(config, "preview_sampling_mode", "") or PREVIEW_SAMPLING_MODE_RANKED
        ),
        "sampling_pool_count": 0,
        "selected_count": 0,
        "selected_unique_count": 0,
        "admitted_count": 0,
        "inserted_count": 0,
        "updated_count": 0,
        "selection_strategy": str(config.strategy or "frequency_bootstrap"),
        "selector_version": None,
        "selected_preview": [],
        "initial_active_preview": [],
        "admission_weight_profile": {},
        "admitted_words": [],
        "profile_bootstrap": {},
    }
    can_execute = bool(plan_payload.get("can_execute"))
    execution_mode = str(plan_payload.get("execution_mode", "planner_only"))
    if not can_execute or execution_mode not in {"frequency_bootstrap", "profile_bootstrap"}:
        return {
            "pair": pair,
            "profile_id": profile_id,
            "set_top_n": sizing_policy.bootstrap_top_n_effective,
            "bootstrap_top_n": sizing_policy.bootstrap_top_n_effective,
            "initial_active_count": sizing_policy.initial_active_count_effective,
            "max_active_items_hint": sizing_policy.max_active_items_hint,
            "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
            "stopwords_path": str(stopwords_path) if stopwords_path else None,
            **frequency_resource_payload,
            "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
            "existing_items_for_pair": existing_items_for_pair,
            "signal_summary": signal_summary,
            "plan": plan_payload,
            "preview": preview_payload,
        }

    _preview_store, init_report = initialize_store_from_frequency_list_with_report_fn(
        store,
        config=SetInitializationConfig(
            frequency_db=resolved_set_source_db,
            jmdict_path=resolved_jmdict_path,
            top_n=sizing_policy.bootstrap_top_n_effective,
            initial_active_count=sizing_policy.initial_active_count_effective,
            language_pair=pair,
            stopwords_path=stopwords_path,
            require_jmdict=capability.requires_jmdict_for_seed,
            strategy=str(config.strategy or "frequency_bootstrap"),
            profile_context=config.profile_context,
            selection_seed=getattr(config, "preview_seed", None),
            selection_policy_override=_resolve_preview_selection_policy(
                getattr(config, "preview_sampling_mode", None)
            ),
            profile_topic_overlay=profile_topic_overlay,
            profile_topic_overlay_diagnostics=profile_topic_overlay_diagnostics,
        ),
    )
    preview_payload = _build_preview_payload(
        init_report=init_report,
        preview_count_requested=preview_count_requested,
    )
    return {
        "pair": pair,
        "profile_id": profile_id,
        "set_top_n": sizing_policy.bootstrap_top_n_effective,
        "bootstrap_top_n": sizing_policy.bootstrap_top_n_effective,
        "initial_active_count": sizing_policy.initial_active_count_effective,
        "max_active_items_hint": sizing_policy.max_active_items_hint,
        "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        **frequency_resource_payload,
        "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
        "existing_items_for_pair": existing_items_for_pair,
        "signal_summary": signal_summary,
        "plan": plan_payload,
        "preview": preview_payload,
    }


def _build_preview_payload(
    *,
    init_report: SetInitializationReport,
    preview_count_requested: int,
) -> dict[str, object]:
    raw_profile_bootstrap = dict(getattr(init_report, "profile_bootstrap_diagnostics", {}) or {})
    ranking_preview_raw = raw_profile_bootstrap.get("ranking_preview")
    ranking_preview = list(ranking_preview_raw) if isinstance(ranking_preview_raw, list) else []
    ranking_by_lemma: dict[str, dict[str, object]] = {}
    for entry in ranking_preview:
        if not isinstance(entry, Mapping):
            continue
        lemma = str(entry.get("lemma", "")).strip()
        if lemma and lemma not in ranking_by_lemma:
            ranking_by_lemma[lemma] = dict(entry)
    weight_preview_raw = getattr(init_report, "initial_active_weight_preview", ()) or ()
    weight_by_lemma: dict[str, dict[str, object]] = {}
    for entry in weight_preview_raw:
        if not isinstance(entry, Mapping):
            continue
        lemma = str(entry.get("lemma", "")).strip()
        if lemma and lemma not in weight_by_lemma:
            weight_by_lemma[lemma] = dict(entry)
    planned_active_lemmas = [
        str(lemma).strip()
        for lemma in getattr(init_report, "initial_active_preview", ()) or ()
        if str(lemma).strip()
    ]
    planned_active_words = _build_planned_active_words(
        planned_active_lemmas=planned_active_lemmas,
        ranking_by_lemma=ranking_by_lemma,
        weight_by_lemma=weight_by_lemma,
    )
    sampled_words = list(planned_active_words[:preview_count_requested])
    profile_bootstrap = _build_helper_preview_profile_bootstrap_payload(raw_profile_bootstrap)
    return {
        "sample_count_requested": preview_count_requested,
        "sample_count_effective": len(sampled_words),
        "sampling_mode": str(
            getattr(init_report, "selection_policy", None) or PREVIEW_SAMPLING_MODE_RANKED
        ),
        "sampling_pool_count": int(init_report.selected_unique_count),
        "selected_count": int(init_report.selected_count),
        "selected_unique_count": int(init_report.selected_unique_count),
        "admitted_count": int(init_report.admitted_count),
        "inserted_count": int(init_report.inserted_count),
        "updated_count": int(init_report.updated_count),
        "selection_strategy": str(init_report.selection_strategy or "frequency_bootstrap"),
        "selection_seed": getattr(init_report, "selection_seed", None),
        "selector_version": init_report.selector_version,
        "selected_preview": list((getattr(init_report, "selected_preview", ()) or ())[:10]),
        "initial_active_preview": planned_active_lemmas,
        "admission_weight_profile": dict(
            getattr(init_report, "admission_weight_profile", {}) or {}
        ),
        "admitted_words": sampled_words,
        "profile_bootstrap": profile_bootstrap,
    }


def _build_helper_preview_profile_bootstrap_payload(
    profile_bootstrap_diagnostics: Mapping[str, object],
) -> dict[str, object]:
    payload = dict(profile_bootstrap_diagnostics or {})
    payload.pop("ranking_preview", None)
    return payload


def _build_planned_active_words(
    *,
    planned_active_lemmas: Sequence[str],
    ranking_by_lemma: Mapping[str, dict[str, object]],
    weight_by_lemma: Mapping[str, dict[str, object]],
) -> list[dict[str, object]]:
    planned_active_words: list[dict[str, object]] = []
    seen_lemmas: set[str] = set()
    for lemma in planned_active_lemmas:
        normalized_lemma = str(lemma or "").strip()
        if not normalized_lemma or normalized_lemma in seen_lemmas:
            continue
        seen_lemmas.add(normalized_lemma)
        word_payload = {
            "lemma": normalized_lemma,
            **weight_by_lemma.get(normalized_lemma, {}),
            **ranking_by_lemma.get(normalized_lemma, {}),
        }
        if "explanation" not in word_payload:
            word_payload["explanation"] = "Selected for the initial active bootstrap preview."
        planned_active_words.append(word_payload)
    return planned_active_words


def _resolve_preview_selection_policy(value: object) -> str | None:
    normalized_mode = str(value or "").strip().lower()
    if not normalized_mode:
        return None
    if normalized_mode == PREVIEW_SAMPLING_MODE_RESERVED_TOPIC_LANE:
        return SELECTION_POLICY_RESERVED_TOPIC_LANE
    if normalized_mode == PREVIEW_SAMPLING_MODE_WEIGHTED:
        return SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT
    return SELECTION_POLICY_TOP_N
