from __future__ import annotations

from typing import Mapping, Sequence


_MARKER_FIELDS: tuple[tuple[str, str], ...] = (
    ("entry_tags", "entry_tag"),
    ("entry_categories", "entry_category"),
    ("sense_tags", "sense_tag"),
    ("sense_topics", "sense_topic"),
    ("sense_categories", "sense_category"),
    ("translation_tags", "translation_tag"),
)
_TEXT_FIELDS: tuple[str, ...] = (
    "entry_pos_title",
    "translation_sense_text",
    "translation_english_text",
    "translation_note_text",
    "translation_roman_text",
)
_RELATION_FIELDS: tuple[tuple[str, str], ...] = (
    ("sense_form_of", "sense_form_of"),
    ("sense_alt_of", "sense_alt_of"),
)
_FAMILY_FIELD_RULES: tuple[tuple[str, Mapping[str, tuple[str, ...]]], ...] = (
    (
        "register_region",
        {
            "entry_tags": (
                "informal",
                "colloquial",
                "slang",
                "mexico",
                "mexican",
                "spain",
                "latin america",
                "latin-america",
                "argentina",
                "chile",
                "colombia",
                "cuba",
                "peru",
                "uruguay",
                "venezuela",
            ),
            "sense_tags": (
                "informal",
                "colloquial",
                "slang",
                "mexico",
                "mexican",
                "spain",
                "latin america",
                "latin-america",
                "argentina",
                "chile",
                "colombia",
                "cuba",
                "peru",
                "uruguay",
                "venezuela",
            ),
            "sense_categories": ("spanish informal terms",),
            "translation_tags": (
                "mexico",
                "mexican",
                "spain",
                "latin america",
                "latin-america",
                "argentina",
                "chile",
                "colombia",
                "cuba",
                "peru",
                "uruguay",
                "venezuela",
            ),
        },
    ),
    (
        "government_law",
        {
            "sense_topics": (
                "government",
                "law",
                "legal",
                "politic",
                "parliament",
                "legislation",
                "judicial",
                "court",
            ),
            "sense_categories": (
                "government",
                "law",
                "legal",
                "politic",
                "parliament",
                "legislation",
                "judicial",
                "court",
            ),
        },
    ),
    (
        "math_geometry",
        {
            "sense_topics": (
                "mathematics",
                "math",
                "geometry",
                "geometric",
            ),
            "sense_categories": (
                "mathematics",
                "math",
                "geometry",
                "geometric",
            ),
        },
    ),
    (
        "hunting_fishing_tools",
        {
            "sense_topics": (
                "hunting",
                "fishing",
                "tool",
                "tools",
            ),
            "sense_categories": (
                "hunting",
                "fishing",
                "tool",
                "tools",
            ),
        },
    ),
    (
        "art_media",
        {
            "sense_topics": (
                "art",
                "painting",
                "photography",
                "photographic",
                "film",
                "cinema",
                "television",
                "media",
            ),
            "sense_categories": (
                "art",
                "painting",
                "photography",
                "photographic",
                "film",
                "cinema",
                "television",
                "media",
            ),
            "entry_categories": (
                "art",
                "painting",
                "photography",
                "photographic",
                "film",
                "cinema",
                "television",
                "media",
            ),
        },
    ),
    (
        "computing",
        {
            "sense_topics": (
                "computing",
                "computer",
                "software",
                "internet",
            ),
            "sense_categories": (
                "computing",
                "computer",
                "software",
                "internet",
            ),
        },
    ),
    (
        "communication_network",
        {
            "sense_topics": (
                "communication",
                "communications",
                "network",
                "web",
                "transport",
            ),
            "sense_categories": (
                "communication",
                "communications",
                "network",
                "web",
                "transport",
            ),
        },
    ),
    (
        "abbreviation_ellipsis_formof",
        {
            "entry_tags": (
                "ellipsis",
                "abbreviation",
                "abbreviations",
                "acronym",
                "initialism",
                "clipping",
            ),
            "sense_tags": (
                "ellipsis",
                "abbreviation",
                "abbreviations",
                "acronym",
                "initialism",
                "clipping",
            ),
            "sense_categories": (
                "ellipsis",
                "abbreviation",
                "abbreviations",
                "acronym",
                "initialism",
                "clipping",
            ),
        },
    ),
)
_RELATION_FAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "abbreviation_ellipsis_formof",
        (
            "sense_form_of:",
            "sense_alt_of:",
        ),
    ),
)


def build_kaikki_record_views(metadata: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(metadata, Mapping):
        return {}
    marker_fields: dict[str, tuple[str, ...]] = {}
    prefixed_marker_fields: dict[str, tuple[str, ...]] = {}
    combined_markers: list[str] = []
    combined_prefixed_markers: list[str] = []
    for field_name, prefix in _MARKER_FIELDS:
        normalized_values = _normalize_string_sequence(metadata.get(field_name))
        if not normalized_values:
            continue
        marker_fields[field_name] = normalized_values
        prefixed_values = tuple(f"{prefix}:{value}" for value in normalized_values)
        prefixed_marker_fields[field_name] = prefixed_values
        combined_markers.extend(normalized_values)
        combined_prefixed_markers.extend(prefixed_values)

    text_fields: dict[str, str] = {}
    for field_name in _TEXT_FIELDS:
        normalized_text = _normalize_marker_text(metadata.get(field_name))
        if normalized_text:
            text_fields[field_name] = normalized_text

    relation_fields: dict[str, tuple[str, ...]] = {}
    combined_relations: list[str] = []
    for field_name, prefix in _RELATION_FIELDS:
        normalized_values = _normalize_relation_values(metadata.get(field_name))
        if not normalized_values:
            continue
        relation_fields[field_name] = normalized_values
        combined_relations.extend(f"{prefix}:{value}" for value in normalized_values)

    views: dict[str, object] = {}
    if marker_fields:
        views["marker_fields"] = marker_fields
        views["combined_markers"] = tuple(_dedupe_preserve_order(combined_markers))
    if prefixed_marker_fields:
        views["prefixed_marker_fields"] = prefixed_marker_fields
        views["combined_prefixed_markers"] = tuple(
            _dedupe_preserve_order(combined_prefixed_markers)
        )
    if text_fields:
        views["text_fields"] = text_fields
    if relation_fields:
        views["relation_fields"] = relation_fields
        views["combined_relations"] = tuple(_dedupe_preserve_order(combined_relations))
    family_fields = _build_family_fields(
        prefixed_marker_fields=prefixed_marker_fields,
        combined_relations=combined_relations,
    )
    if family_fields:
        views["family_fields"] = family_fields
        views["combined_families"] = tuple(family_fields.keys())
    return views


def _build_family_fields(
    *,
    prefixed_marker_fields: Mapping[str, Sequence[str]],
    combined_relations: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    relation_values = [str(value).strip() for value in combined_relations if str(value).strip()]
    family_fields: dict[str, tuple[str, ...]] = {}
    for family_name, field_rules in _FAMILY_FIELD_RULES:
        matched: list[str] = []
        for field_name, keywords in field_rules.items():
            markers = prefixed_marker_fields.get(field_name, ())
            matched.extend(
                marker for marker in markers if any(keyword in marker for keyword in keywords)
            )
        relation_keywords = _relation_keywords_for_family(family_name)
        if relation_keywords:
            matched.extend(
                relation
                for relation in relation_values
                if any(keyword in relation for keyword in relation_keywords)
            )
        normalized_matches = tuple(_dedupe_preserve_order(matched))
        if normalized_matches:
            family_fields[family_name] = normalized_matches
    return family_fields


def _relation_keywords_for_family(family_name: str) -> tuple[str, ...]:
    for candidate_family, prefixes in _RELATION_FAMILY_RULES:
        if candidate_family == family_name:
            return prefixes
    return ()


def _normalize_relation_values(value: object) -> tuple[str, ...]:
    values: list[str] = []
    _visit_relation_values(value, values)
    return tuple(_dedupe_preserve_order(values))


def _visit_relation_values(value: object, values: list[str]) -> None:
    if isinstance(value, str):
        normalized = _normalize_marker_text(value)
        if normalized:
            values.append(normalized)
        return
    if isinstance(value, Mapping):
        preferred = _normalize_marker_text(value.get("word"))
        if preferred:
            values.append(preferred)
            return
        for item in value.values():
            _visit_relation_values(item, values)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _visit_relation_values(item, values)


def _normalize_string_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        normalized = _normalize_marker_text(value)
        return (normalized,) if normalized else ()
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return ()
    values: list[str] = []
    for item in value:
        normalized = _normalize_marker_text(item)
        if normalized:
            values.append(normalized)
    return tuple(_dedupe_preserve_order(values))


def _normalize_marker_text(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return " ".join(text.split())


def _dedupe_preserve_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


__all__ = ["build_kaikki_record_views"]
