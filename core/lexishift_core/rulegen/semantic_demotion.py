from __future__ import annotations

from typing import Mapping

from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

_DEFAULT_ENGLISH_GLOSS_DEMOTIONS: Mapping[str, float] = {
    "appearing": 0.9,
    "looking": 0.9,
    "like": 0.9,
    "kind": 0.85,
    "sort": 0.85,
    "type": 0.85,
}

_DEFAULT_SPANISH_GLOSS_DEMOTIONS: Mapping[str, float] = {
    "tipo": 0.85,
    "clase": 0.85,
    "cosa": 0.8,
}

_DEFAULT_GERMAN_GLOSS_DEMOTIONS: Mapping[str, float] = {
    "art": 0.85,
    "typ": 0.85,
    "sorte": 0.85,
    "ding": 0.8,
}

_PAIR_GENERIC_GLOSS_DEMOTIONS: Mapping[str, Mapping[str, float]] = {
    "en-ja": _DEFAULT_ENGLISH_GLOSS_DEMOTIONS,
    "en-es": _DEFAULT_ENGLISH_GLOSS_DEMOTIONS,
    "en-de": _DEFAULT_ENGLISH_GLOSS_DEMOTIONS,
    "de-en": _DEFAULT_GERMAN_GLOSS_DEMOTIONS,
    "es-en": _DEFAULT_SPANISH_GLOSS_DEMOTIONS,
}


def resolve_pair_generic_gloss_demotions(pair: str) -> dict[str, float]:
    normalized = str(pair or "").strip().lower()
    entries = _PAIR_GENERIC_GLOSS_DEMOTIONS.get(normalized, {})
    return {key: float(value) for key, value in entries.items()}


def resolve_generic_gloss_demotion(
    source: object,
    *,
    demotions: Mapping[str, float],
) -> float:
    normalized = sanitize_dictionary_gloss(source).lower()
    if not normalized:
        return 0.0
    raw = demotions.get(normalized)
    if raw is None:
        return 0.0
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))
