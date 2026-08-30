from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


TARGET_CURVE_ID = "curriculum_band_curve_v1"
DEFAULT_BAND_WIDTH = 0.05

# Provisional field-knowledge curve for display-level SRS vocabulary.
#
# For a 74k-item frontier, the first band is roughly 110 items, and the curve
# gradually opens into the intermediate/advanced range while reserving only the
# very top tail for the rarest material. This is deliberately not uniform.
DEFAULT_TARGET_BAND_WEIGHTS: tuple[float, ...] = (
    0.0015,
    0.0040,
    0.0080,
    0.0120,
    0.0160,
    0.0220,
    0.0300,
    0.0400,
    0.0500,
    0.0600,
    0.0700,
    0.0800,
    0.0900,
    0.1000,
    0.1100,
    0.1200,
    0.1000,
    0.0600,
    0.0200,
    0.0065,
)


@dataclass(frozen=True)
class DifficultyBand:
    start: float
    end: float

    @property
    def label(self) -> str:
        return f"{self.start:.2f}-{self.end:.2f}"


def normalize_rows_by_target_curve(
    rows: Sequence[Mapping[str, object]],
    *,
    score_key: str,
    output_key: str,
    band_weights: Sequence[float] = DEFAULT_TARGET_BAND_WEIGHTS,
    band_width: float = DEFAULT_BAND_WIDTH,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    bands = difficulty_bands(band_width)
    if len(bands) != len(band_weights):
        raise ValueError(
            f"Expected {len(bands)} band weights for width={band_width}, got {len(band_weights)}."
        )
    ordered = sorted(
        (dict(row) for row in rows), key=lambda row: _normalization_sort_key(row, score_key)
    )
    band_counts = target_band_counts(len(ordered), band_weights)
    cursor = 0
    for band, count in zip(bands, band_counts):
        if count <= 0:
            continue
        for offset, row in enumerate(ordered[cursor : cursor + count]):
            row[output_key] = round(_position_in_band(band, offset=offset, count=count), 6)
            row[f"{output_key}_band"] = band.label
        cursor += count
    return ordered, {
        "normalization": "target_curve",
        "curve_id": TARGET_CURVE_ID,
        "band_width": band_width,
        "band_weights": [round(float(value), 8) for value in band_weights],
        "band_counts": [
            {
                "label": band.label,
                "start": band.start,
                "end": band.end,
                "target_weight": round(float(weight), 8),
                "assigned_count": count,
            }
            for band, weight, count in zip(bands, band_weights, band_counts)
        ],
    }


def target_band_counts(total_count: int, band_weights: Sequence[float]) -> list[int]:
    if total_count < 0:
        raise ValueError("total_count must be non-negative.")
    if total_count == 0:
        return [0 for _ in band_weights]
    normalized = _normalize_weights(band_weights)
    exact_counts = [weight * total_count for weight in normalized]
    floors = [int(math.floor(value)) for value in exact_counts]
    remainder = total_count - sum(floors)
    fractional_order = sorted(
        range(len(exact_counts)),
        key=lambda index: (exact_counts[index] - floors[index], -index),
        reverse=True,
    )
    for index in fractional_order[:remainder]:
        floors[index] += 1
    return floors


def difficulty_bands(width: float = DEFAULT_BAND_WIDTH) -> list[DifficultyBand]:
    if width <= 0.0 or width > 1.0:
        raise ValueError("Band width must be greater than 0 and at most 1.")
    units = round(1.0 / width)
    if not math.isclose(units * width, 1.0, abs_tol=1e-9):
        raise ValueError("Band width must divide 1.0 exactly enough for stable bands.")
    return [
        DifficultyBand(start=round(index * width, 6), end=round((index + 1) * width, 6))
        for index in range(units)
    ]


def parse_band_weights_csv(value: str) -> tuple[float, ...]:
    weights = tuple(float(item.strip()) for item in str(value or "").split(",") if item.strip())
    return weights or DEFAULT_TARGET_BAND_WEIGHTS


def _position_in_band(band: DifficultyBand, *, offset: int, count: int) -> float:
    if count <= 0:
        return band.start
    width = band.end - band.start
    return min(1.0, band.start + (((offset + 0.5) / count) * width))


def _normalize_weights(weights: Sequence[float]) -> list[float]:
    if not weights:
        raise ValueError("At least one band weight is required.")
    parsed = [max(0.0, float(value)) for value in weights]
    total = sum(parsed)
    if total <= 0.0:
        raise ValueError("At least one band weight must be positive.")
    return [value / total for value in parsed]


def _normalization_sort_key(row: Mapping[str, object], score_key: str) -> tuple[object, ...]:
    return (
        _optional_float(row.get(score_key))
        if _optional_float(row.get(score_key)) is not None
        else float("inf"),
        _optional_float(row.get("core_rank"))
        if _optional_float(row.get("core_rank")) is not None
        else float("inf"),
        str(row.get("lemma") or ""),
        str(row.get("reading") or ""),
        str(row.get("candidate_identity_key") or ""),
    )


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed
