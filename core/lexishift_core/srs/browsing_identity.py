from __future__ import annotations

from collections.abc import Sequence


BROWSING_OBSERVATION_SOURCE_MAPPING = "source_mapping"
BROWSING_OBSERVATION_TARGET_SURFACE = "target_surface"
BROWSING_OBSERVATION_REPLACEMENT_EXPOSURE = "replacement_exposure"
BROWSING_OBSERVATION_SOURCES = frozenset(
    {
        BROWSING_OBSERVATION_SOURCE_MAPPING,
        BROWSING_OBSERVATION_TARGET_SURFACE,
        BROWSING_OBSERVATION_REPLACEMENT_EXPOSURE,
    }
)


def build_browsing_target_key(
    *,
    target_lemma: object,
    target_reading: object = None,
    target_key: object = None,
) -> str:
    explicit_key = str(target_key or "").strip()
    if explicit_key:
        return explicit_key
    lemma = str(target_lemma or "").strip()
    reading = str(target_reading or "").strip()
    if lemma and reading and reading != lemma:
        return f"{lemma}|{reading}"
    return lemma


def aggregate_target_key(aggregate: object) -> str:
    return build_browsing_target_key(
        target_lemma=getattr(aggregate, "target_lemma", ""),
        target_reading=getattr(aggregate, "target_reading", ""),
        target_key=getattr(aggregate, "target_key", ""),
    )


def candidate_target_key(candidate: object) -> str:
    return build_browsing_target_key(
        target_lemma=getattr(candidate, "lemma", ""),
        target_reading=getattr(candidate, "target_reading", ""),
        target_key=getattr(candidate, "target_key", ""),
    )


def resolve_reading_confidence(value: object) -> float:
    parsed = _safe_float(value)
    if parsed is None:
        return 1.0
    return max(0.0, min(1.0, parsed))


def aggregate_reading_confidence(aggregate: object) -> float:
    return resolve_reading_confidence(getattr(aggregate, "reading_confidence", 1.0))


def normalize_observation_source(value: object) -> str:
    source = str(value or "").strip().lower()
    return source if source in BROWSING_OBSERVATION_SOURCES else ""


def normalize_observation_sources(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        normalized = normalize_observation_source(value)
        return (normalized,) if normalized else tuple()
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return tuple()
    return tuple(
        sorted({normalized for raw in value if (normalized := normalize_observation_source(raw))})
    )


def observation_source_for_side(*, explicit: object = "", side: object = "") -> str:
    normalized = normalize_observation_source(explicit)
    if normalized:
        return normalized
    side_text = str(side or "").strip()
    if side_text == "source":
        return BROWSING_OBSERVATION_SOURCE_MAPPING
    if side_text == "replacement_exposure":
        return BROWSING_OBSERVATION_REPLACEMENT_EXPOSURE
    if side_text == "target":
        return BROWSING_OBSERVATION_TARGET_SURFACE
    return ""


def merge_observation_sources(
    left: Sequence[str],
    right: Sequence[str],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                normalized
                for raw in tuple(left or ()) + tuple(right or ())
                if (normalized := normalize_observation_source(raw))
            }
        )
    )


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(str(value))
    except (TypeError, ValueError):
        return None
