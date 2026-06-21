from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.profile_bootstrap import summarize_profile_bootstrap_context
from lexishift_core.srs.set_strategy import (
    OBJECTIVE_BOOTSTRAP,
    OBJECTIVE_GROWTH,
    OBJECTIVE_REBALANCE,
    OBJECTIVE_REFRESH,
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
    set_top_n: Optional[int] = None
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
    extra_diagnostics: dict[str, object] = {}

    if requested == STRATEGY_FREQUENCY_BOOTSTRAP:
        can_execute = True
        execution_mode = "frequency_bootstrap"
        notes.append("Using frequency bootstrap strategy.")
    elif requested == STRATEGY_PROFILE_BOOTSTRAP:
        required_fields.extend(("interests", "proficiency", "difficulty_preferences"))
        can_execute = True
        execution_mode = "profile_bootstrap"
        profile_bootstrap_summary = summarize_profile_bootstrap_context(request.profile_context)
        extra_diagnostics = {
            "profile_bootstrap": profile_bootstrap_summary,
        }
        notes.append(
            "Profile bootstrap applies profile-aware candidate scoring to the frequency "
            "bootstrap seed frontier."
        )
        profile_context_summary = profile_bootstrap_summary.get("context")
        profile_context_payload = (
            profile_context_summary if isinstance(profile_context_summary, Mapping) else {}
        )
        active_signals = _tuple_payload(profile_context_payload.get("active_signals"))
        missing_signals = _tuple_payload(profile_context_payload.get("missing_signals"))
        if not request.profile_context:
            notes.append(
                "No profile context was provided; ranking would remain close to neutral frequency order."
            )
        elif missing_signals:
            notes.append(
                "Profile bootstrap will keep missing signals neutral: "
                + ", ".join(str(signal) for signal in missing_signals)
                + "."
            )
        if active_signals:
            notes.append(
                "Active bootstrap profile signals: "
                + ", ".join(str(signal) for signal in active_signals)
                + "."
            )
    elif requested == STRATEGY_PROFILE_GROWTH:
        required_fields.extend(("interests", "proficiency", "empirical_trends"))
        if objective == OBJECTIVE_REBALANCE:
            can_execute = True
            execution_mode = "rebalance_preview"
            notes.append(
                "Profile growth rebalance reranks retained and seed candidates against the "
                "current active inventory."
            )
        elif objective in {OBJECTIVE_GROWTH, OBJECTIVE_REFRESH}:
            can_execute = True
            execution_mode = "profile_growth"
            notes.append(
                "Profile growth applies profile-aware candidate scoring during ongoing "
                "refresh/growth admission."
            )
        else:
            can_execute = False
            execution_mode = "planner_only"
            notes.append(
                "Profile growth is executable for refresh/growth objectives; choose "
                "objective=growth or objective=refresh for admission into S."
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
        notes.append(
            "Unknown objective was provided; caller should choose bootstrap/growth/refresh."
        )
    if not pair:
        notes.append("Missing pair; caller should provide a language pair.")
        can_execute = False
        execution_mode = "planner_only"

    resolved_top_n = _optional_positive_int(request.set_top_n)
    diagnostics = {
        "pair": pair,
        "set_top_n": resolved_top_n,
        "bootstrap_top_n": resolved_top_n,
        "candidate_frontier": "limited" if resolved_top_n is not None else "all",
        "initial_active_count": max(1, int(request.initial_active_count)),
        "max_active_items_hint": max(0, int(request.max_active_items_hint)),
        "replace_pair": bool(request.replace_pair),
        "trigger": str(request.trigger or "manual"),
        "existing_items_for_pair": max(0, int(request.existing_items_for_pair)),
        "profile_keys": sorted(str(key) for key in request.profile_context.keys()),
        "signal_summary_keys": sorted(str(key) for key in request.signal_summary.keys()),
        **extra_diagnostics,
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


def _optional_positive_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return max(1, parsed)


def _tuple_payload(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


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
