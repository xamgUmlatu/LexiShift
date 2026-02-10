from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from lexishift_core.srs.set_strategy import (
    OBJECTIVE_BOOTSTRAP,
    STRATEGY_ADAPTIVE_REFRESH,
    STRATEGY_FREQUENCY_BOOTSTRAP,
    STRATEGY_PROFILE_BOOTSTRAP,
    STRATEGY_PROFILE_GROWTH,
    normalize_set_objective,
    normalize_set_strategy,
)


@dataclass(frozen=True)
class SrsSetPlanRequest:
    pair: str
    strategy: str = STRATEGY_FREQUENCY_BOOTSTRAP
    objective: str = OBJECTIVE_BOOTSTRAP
    set_top_n: int = 800
    initial_active_count: int = 40
    max_active_items_hint: int = 0
    replace_pair: bool = False
    existing_items_for_pair: int = 0
    trigger: str = "manual"
    profile_context: Mapping[str, object] = field(default_factory=dict)
    signal_summary: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SrsSetPlan:
    pair: str
    strategy_requested: str
    strategy_effective: str
    objective: str
    can_execute: bool
    execution_mode: str
    requires_profile_fields: Sequence[str] = field(default_factory=tuple)
    notes: Sequence[str] = field(default_factory=tuple)
    diagnostics: Mapping[str, object] = field(default_factory=dict)


def build_srs_set_plan(request: SrsSetPlanRequest) -> SrsSetPlan:
    requested = normalize_set_strategy(request.strategy)
    objective = normalize_set_objective(request.objective)
    pair = str(request.pair or "").strip()
    notes: list[str] = []
    required_fields: list[str] = []
    can_execute = False
    execution_mode = "planner_only"
    effective = requested

    if requested == STRATEGY_FREQUENCY_BOOTSTRAP:
        can_execute = True
        execution_mode = "frequency_bootstrap"
        notes.append("Using frequency bootstrap strategy.")
    elif requested == STRATEGY_PROFILE_BOOTSTRAP:
        required_fields.extend(("interests", "proficiency", "empirical_trends"))
        can_execute = True
        execution_mode = "frequency_bootstrap"
        effective = STRATEGY_FREQUENCY_BOOTSTRAP
        notes.append(
            "Profile-aware weighting is scaffolding-only. Falling back to frequency bootstrap."
        )
    elif requested == STRATEGY_PROFILE_GROWTH:
        required_fields.extend(("interests", "proficiency", "empirical_trends"))
        can_execute = False
        execution_mode = "planner_only"
        notes.append(
            "Profile growth strategy is planned but not implemented. Planner returns requirements only."
        )
    elif requested == STRATEGY_ADAPTIVE_REFRESH:
        required_fields.extend(("feedback_signals", "exposure_signals"))
        can_execute = False
        execution_mode = "planner_only"
        notes.append(
            "Adaptive refresh strategy is planned but not implemented. Needs signal aggregation."
        )
    else:
        can_execute = True
        execution_mode = "frequency_bootstrap"
        effective = STRATEGY_FREQUENCY_BOOTSTRAP
        notes.append("Unknown strategy. Falling back to frequency bootstrap.")

    if objective == "unknown":
        notes.append("Unknown objective was provided; caller should choose bootstrap/growth/refresh.")
    if not pair:
        notes.append("Missing pair; caller should provide a language pair.")
        can_execute = False
        execution_mode = "planner_only"

    diagnostics = {
        "pair": pair,
        "set_top_n": max(1, int(request.set_top_n)),
        "bootstrap_top_n": max(1, int(request.set_top_n)),
        "initial_active_count": max(1, int(request.initial_active_count)),
        "max_active_items_hint": max(0, int(request.max_active_items_hint)),
        "replace_pair": bool(request.replace_pair),
        "trigger": str(request.trigger or "manual"),
        "existing_items_for_pair": max(0, int(request.existing_items_for_pair)),
        "profile_keys": sorted(str(key) for key in request.profile_context.keys()),
        "signal_summary_keys": sorted(str(key) for key in request.signal_summary.keys()),
    }
    return SrsSetPlan(
        pair=pair,
        strategy_requested=requested,
        strategy_effective=effective,
        objective=objective,
        can_execute=can_execute,
        execution_mode=execution_mode,
        requires_profile_fields=tuple(required_fields),
        notes=tuple(notes),
        diagnostics=diagnostics,
    )


def plan_to_dict(plan: SrsSetPlan) -> dict[str, object]:
    return {
        "pair": plan.pair,
        "strategy_requested": plan.strategy_requested,
        "strategy_effective": plan.strategy_effective,
        "objective": plan.objective,
        "can_execute": plan.can_execute,
        "execution_mode": plan.execution_mode,
        "requires_profile_fields": list(plan.requires_profile_fields),
        "notes": list(plan.notes),
        "diagnostics": dict(plan.diagnostics),
    }
