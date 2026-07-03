from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def safe_share(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 6)


def lane_probability_by_key(
    rows: Sequence[Mapping[str, object]],
    *,
    budget: int,
    mass_key: str,
) -> dict[str, float]:
    if budget <= 0 or not rows:
        return {}
    masses = {
        str(row.get("target_key") or ""): max(0.0, _safe_float(row.get(mass_key)) or 0.0)
        for row in rows
        if str(row.get("target_key") or "")
    }
    total_mass = sum(masses.values())
    if total_mass <= 0.0:
        return {}
    return {
        key: _approx_without_replacement_inclusion_probability(
            mass=mass,
            total_mass=total_mass,
            budget=budget,
        )
        for key, mass in masses.items()
    }


def combined_probability(browsing_probability: float, general_probability: float) -> float:
    browsing = max(0.0, min(1.0, browsing_probability))
    general = max(0.0, min(1.0, general_probability))
    return max(0.0, min(1.0, browsing + (1.0 - browsing) * general))


def _approx_without_replacement_inclusion_probability(
    *,
    mass: float,
    total_mass: float,
    budget: int,
) -> float:
    if mass <= 0.0 or total_mass <= 0.0 or budget <= 0:
        return 0.0
    return max(
        0.0,
        min(1.0, 1.0 - math.exp(-(max(0, int(budget)) * mass / total_mass))),
    )


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
