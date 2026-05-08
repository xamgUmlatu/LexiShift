from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from semantic_veto_product_quality_en_es import _safe_float


RANK_BINS = (
    (1, 500, "1-500"),
    (501, 1000, "501-1000"),
    (1001, 2000, "1001-2000"),
    (2001, 5000, "2001-5000"),
)
RANK_BIN_ORDER = [item[2] for item in RANK_BINS] + [">5000", "missing"]
SOURCE_ZIPF_BIN_ORDER = [
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
]
COUNT_BIN_ORDER = ["0", "1", "2-4", "5-9", "10+", "missing"]
OUTCOME_FAILURES = {"positive_abstain", "negative_allow"}


def _optional_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return _round4(numerator / denominator)


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _round4(value: object) -> float:
    return round(_safe_float(value), 4)


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(value)
    return True


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
