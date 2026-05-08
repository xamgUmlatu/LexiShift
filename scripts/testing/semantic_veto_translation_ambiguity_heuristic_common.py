from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
import hashlib
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _as_mapping, _safe_float


def _pairs(rows: Iterable[Mapping[str, object]]) -> list[tuple[float, float]]:
    return [
        (_safe_float(row.get("predicted_need")), _safe_float(row.get("observed_failure_rate")))
        for row in rows
    ]


def _spearman(pairs: Sequence[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    left = _ranks([pair[0] for pair in pairs])
    right = _ranks([pair[1] for pair in pairs])
    return _pearson(left, right)


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and order[end][1] == order[index][1]:
            end += 1
        rank = (index + end + 1) / 2.0
        for original, _value in order[index:end]:
            ranks[original] = rank
        index = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right, strict=True))
    denom_left = sum((a - mean_left) ** 2 for a in left)
    denom_right = sum((b - mean_right) ** 2 for b in right)
    if denom_left <= 0 or denom_right <= 0:
        return None
    return numerator / (denom_left * denom_right) ** 0.5


def _brier(pairs: Sequence[tuple[float, float]]) -> float | None:
    if not pairs:
        return None
    return sum((predicted - observed) ** 2 for predicted, observed in pairs) / len(pairs)


def _lift(top_values: Sequence[float], all_values: Sequence[float]) -> float | None:
    if not top_values or not all_values:
        return None
    baseline = sum(all_values) / len(all_values)
    if baseline <= 0:
        return None
    return (sum(top_values) / len(top_values)) / baseline


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for key, raw in _as_mapping(value).items():
        output[str(key)] = [str(item) for item in _sequence(raw) if str(item)]
    return output


def _first_dim(dimensions: Mapping[str, Sequence[str]], key: str) -> str:
    values = dimensions.get(key) or []
    return str(values[0]) if values else ""


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return [value]


def _split(family_id: str) -> str:
    digest = hashlib.sha256(family_id.encode("utf-8")).hexdigest()
    return "locked_eval_proxy" if int(digest[:8], 16) % 4 == 0 else "discovery_proxy"


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _mean(values: Iterable[float]) -> float:
    items = [float(value) for value in values]
    if not items:
        return 0.0
    return sum(items) / len(items)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _number(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_safe_float(value):.4f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
