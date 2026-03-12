from __future__ import annotations

from typing import Mapping, Optional

from lexishift_core.lexicon.word_package import (
    normalize_word_package,
    resolve_language_tag_from_pair,
)
from lexishift_core.pos.normalization import (
    CANONICAL_POS_OTHER,
    CANONICAL_POS_TAGS,
    normalize_pos,
)


def normalize_pos_component(
    raw_pos: object,
    *,
    language_pair: str,
    source_provider: str,
    source_kind: str,
    source_profile: str = "",
    target_language: str = "",
) -> Optional[dict[str, object]]:
    raw_text = str(raw_pos or "").strip()
    if not raw_text:
        return None
    normalized = normalize_pos(
        raw_text,
        language_pair=language_pair,
        source_provider=source_provider,
        source_kind=source_kind,
        target_language=target_language,
        source_profile=source_profile,
    )
    component: dict[str, object] = {
        "raw": raw_text,
        "mapped": bool(normalized.mapped),
        "source_profile": normalized.source_profile,
        "matched_rule": normalized.matched_rule,
    }
    canonical = str(normalized.canonical or "").strip().lower()
    if normalized.mapped and canonical in CANONICAL_POS_TAGS:
        component["canonical"] = canonical
    return component


def resolve_target_word_package(
    *,
    target: str,
    language_pair: str,
    fallback_provider: str,
    package_hint: Optional[Mapping[str, object]],
) -> Optional[dict[str, object]]:
    return normalize_word_package(
        package_hint,
        fallback_surface=target,
        fallback_language_tag=resolve_language_tag_from_pair(language_pair),
        fallback_provider=fallback_provider,
    )


def extract_target_pos_component(
    *,
    target_word_package: Optional[Mapping[str, object]],
    language_pair: str,
    default_provider: str = "frequency",
) -> Optional[dict[str, object]]:
    if not isinstance(target_word_package, Mapping):
        return None
    provider = default_provider
    source = target_word_package.get("source")
    if isinstance(source, Mapping):
        provider_text = str(source.get("provider") or "").strip()
        if provider_text:
            provider = provider_text
    canonical = str(target_word_package.get("pos_canonical") or "").strip().lower()
    raw_pos = str(
        target_word_package.get("pos_raw") or target_word_package.get("pos") or ""
    ).strip()
    if canonical in CANONICAL_POS_TAGS and canonical != CANONICAL_POS_OTHER:
        component: dict[str, object] = {
            "canonical": canonical,
            "mapped": True,
            "source_profile": "word_package",
            "matched_rule": "word_package:pos_canonical",
        }
        if raw_pos:
            component["raw"] = raw_pos
        return component
    if not raw_pos:
        return None
    return normalize_pos_component(
        raw_pos,
        language_pair=language_pair,
        source_provider=provider,
        source_kind="frequency",
    )


def build_candidate_pos_metadata(
    *,
    source_pos: Optional[Mapping[str, object]] = None,
    target_pos: Optional[Mapping[str, object]] = None,
    dictionary_pos: Optional[Mapping[str, object]] = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    pos: dict[str, dict[str, object]] = {}

    normalized_source = _normalize_component(source_pos)
    if normalized_source:
        pos["source"] = normalized_source
        _copy_component_fields(metadata, prefix="source_pos", component=normalized_source)

    normalized_target = _normalize_component(target_pos)
    if normalized_target:
        pos["target"] = normalized_target
        _copy_component_fields(metadata, prefix="target_pos", component=normalized_target)

    normalized_dictionary = _normalize_component(dictionary_pos)
    if normalized_dictionary:
        pos["dictionary"] = normalized_dictionary
        _copy_component_fields(metadata, prefix="dictionary_pos", component=normalized_dictionary)
        _copy_component_fields(metadata, prefix="dict_entry_pos", component=normalized_dictionary)

    if pos:
        metadata["pos"] = pos
    return metadata


def _normalize_component(value: Optional[Mapping[str, object]]) -> Optional[dict[str, object]]:
    if not isinstance(value, Mapping):
        return None
    component: dict[str, object] = {}
    raw = str(value.get("raw") or "").strip()
    if raw:
        component["raw"] = raw
    canonical = str(value.get("canonical") or "").strip().lower()
    if canonical in CANONICAL_POS_TAGS:
        component["canonical"] = canonical
    if "mapped" in value:
        component["mapped"] = bool(value.get("mapped"))
    source_profile = str(value.get("source_profile") or "").strip()
    if source_profile:
        component["source_profile"] = source_profile
    matched_rule = str(value.get("matched_rule") or "").strip()
    if matched_rule:
        component["matched_rule"] = matched_rule
    return component or None


def _copy_component_fields(
    metadata: dict[str, object],
    *,
    prefix: str,
    component: Mapping[str, object],
) -> None:
    for key in ("raw", "canonical", "mapped", "source_profile", "matched_rule"):
        if key not in component:
            continue
        metadata[f"{prefix}_{key}"] = component[key]


__all__ = [
    "build_candidate_pos_metadata",
    "extract_target_pos_component",
    "normalize_pos_component",
    "resolve_target_word_package",
]
