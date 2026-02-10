from __future__ import annotations

from typing import Callable, Mapping, Optional, Sequence

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs import SrsStore
from lexishift_core.srs.pair_policy import pair_policy_to_dict, resolve_srs_pair_policy
from lexishift_core.srs.set_planner import SrsSetPlanRequest, build_srs_set_plan, plan_to_dict
from lexishift_core.srs.set_policy import resolve_set_sizing_policy
from lexishift_core.srs.signal_queue import summarize_signal_events


def count_items_for_pair(store: SrsStore, pair: str) -> int:
    return len([item for item in store.items if item.language_pair == pair])


def build_set_plan_payload(
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
    config,
    resolve_profile_id_fn: Callable[..., str],
    ensure_store_fn: Callable[..., SrsStore],
    resolve_pair_set_top_n_fn: Callable[..., int],
    resolve_pair_initial_active_count_fn: Callable[..., int],
    resolve_stopwords_path_fn: Callable[..., object],
) -> dict:
    raw_pair = str(config.pair or "").strip()
    if not raw_pair:
        raise ValueError("Missing pair.")
    pair = resolve_pair_capability(raw_pair).pair

    profile_id = resolve_profile_id_fn(
        paths,
        profile_id=config.profile_id,
        profile_context=config.profile_context,
    )
    store = ensure_store_fn(paths, profile_id=profile_id, persist_missing=False)
    existing_items_for_pair = count_items_for_pair(store, pair)
    resolved_set_top_n = resolve_pair_set_top_n_fn(
        pair=pair,
        requested_top_n=config.set_top_n,
        purpose="bootstrap",
    )
    resolved_initial_active_count = resolve_pair_initial_active_count_fn(
        pair=pair,
        requested_count=config.initial_active_count,
    )
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
    plan_payload = build_set_plan_payload(
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
        "pair_policy": pair_policy_to_dict(resolve_srs_pair_policy(pair)),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        "existing_items_for_pair": existing_items_for_pair,
        "signal_summary": signal_summary,
        "plan": plan_payload,
    }

