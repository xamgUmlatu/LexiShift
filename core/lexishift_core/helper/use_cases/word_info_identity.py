from __future__ import annotations

from typing import Mapping

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.resources.japanese_script import contains_kanji
from lexishift_core.srs import load_srs_store


def find_srs_item(
    paths: HelperPaths,
    *,
    profile_id: str,
    pair: str,
    normalized_lemma: str,
    request_word_package: Mapping[str, object],
) -> object | None:
    store_path = paths.srs_store_path_for(profile_id)
    if not store_path.exists():
        return None
    store = load_srs_store(store_path)
    candidates = [
        item
        for item in store.items
        if item.language_pair == pair and _normalize(item.lemma) == normalized_lemma
    ]
    if not candidates or not request_word_package:
        return candidates[0] if candidates else None

    request_identity = _word_package_identity_key(request_word_package)
    if request_identity:
        for item in candidates:
            package = getattr(item, "word_package", None)
            if (
                isinstance(package, Mapping)
                and _word_package_identity_key(package) == request_identity
            ):
                return item

    request_surface = _normalize(request_word_package.get("surface"))
    request_reading = _normalize(request_word_package.get("reading"))
    if request_surface and request_reading:
        for item in candidates:
            package = getattr(item, "word_package", None)
            if not isinstance(package, Mapping):
                continue
            if (
                _normalize(package.get("surface")) == request_surface
                and _normalize(package.get("reading")) == request_reading
            ):
                return item
        return None
    return candidates[0]


def lookup_japanese_reading(
    package: Mapping[str, object],
    *,
    target_language: str,
    surface: str,
) -> str:
    if str(target_language or "").strip().lower() != "ja":
        return ""
    reading = str(package.get("reading") or "").strip()
    if contains_kanji(surface) and _normalize(reading) == _normalize(surface):
        return ""
    return reading


def _word_package_identity_key(package: Mapping[str, object]) -> str:
    source = package.get("source")
    source_mapping = source if isinstance(source, Mapping) else {}
    return _first_text(
        package.get("candidate_identity_key"),
        source_mapping.get("candidate_identity_key"),
    )


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _normalize(value: object) -> str:
    return str(value or "").strip().casefold()
