from __future__ import annotations

STRATEGY_FREQUENCY_BOOTSTRAP = "frequency_bootstrap"
STRATEGY_PROFILE_BOOTSTRAP = "profile_bootstrap"
STRATEGY_PROFILE_GROWTH = "profile_growth"
STRATEGY_ADAPTIVE_REFRESH = "adaptive_refresh"
STRATEGY_UNKNOWN = "unknown"

OBJECTIVE_BOOTSTRAP = "bootstrap"
OBJECTIVE_GROWTH = "growth"
OBJECTIVE_REFRESH = "refresh"
OBJECTIVE_UNKNOWN = "unknown"

KNOWN_SET_STRATEGIES: frozenset[str] = frozenset(
    {
        STRATEGY_FREQUENCY_BOOTSTRAP,
        STRATEGY_PROFILE_BOOTSTRAP,
        STRATEGY_PROFILE_GROWTH,
        STRATEGY_ADAPTIVE_REFRESH,
    }
)

KNOWN_SET_OBJECTIVES: frozenset[str] = frozenset(
    {
        OBJECTIVE_BOOTSTRAP,
        OBJECTIVE_GROWTH,
        OBJECTIVE_REFRESH,
    }
)


def normalize_set_strategy(value: object) -> str:
    strategy = str(value or "").strip().lower()
    if strategy in KNOWN_SET_STRATEGIES:
        return strategy
    return STRATEGY_UNKNOWN


def normalize_set_objective(value: object) -> str:
    objective = str(value or "").strip().lower()
    if objective in KNOWN_SET_OBJECTIVES:
        return objective
    return OBJECTIVE_UNKNOWN
