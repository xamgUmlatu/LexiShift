from __future__ import annotations

from typing import Mapping, Sequence, cast

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.semantic_shadow_support import (
    normalize_shadow_string_list,
    parse_shadow_optional_int,
)
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss


def cluster_shadow_records(
    *,
    target_override: str | None,
    records: Sequence[TranslationGlossRecord],
    provider: str,
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, object, object, object], dict[str, object]] = {}
    for index, record in enumerate(records):
        metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
        target = str(target_override or record.translation or "").strip()
        if not target:
            continue
        entry_ord = parse_shadow_optional_int(metadata.get("entry_ord"))
        sense_ord = parse_shadow_optional_int(metadata.get("sense_ord"))
        gloss_ord = parse_shadow_optional_int(metadata.get("gloss_ord"))
        key = (target, entry_ord, sense_ord, gloss_ord)
        if entry_ord is None and sense_ord is None and gloss_ord is None:
            key = (target, None, None, index)
        bucket = grouped.get(key)
        if bucket is None:
            bucket = {
                "target": target,
                "sense_label": build_shadow_sense_label(record),
                "canonical_pos": build_shadow_canonical_pos(record),
                "provider": provider,
                "locator": _build_locator(
                    provider=provider,
                    target=target,
                    entry_ord=entry_ord,
                    sense_ord=sense_ord,
                    gloss_ord=gloss_ord,
                    fallback_index=index,
                ),
                "glosses": [],
                "qualifiers": build_shadow_qualifiers(metadata),
            }
            grouped[key] = bucket
        emitted_gloss = sanitize_dictionary_gloss(record.translation)
        glosses = cast(list[str], bucket["glosses"])
        if emitted_gloss and emitted_gloss not in glosses:
            glosses.append(emitted_gloss)
    return list(grouped.values())


def build_shadow_sense_label(record: TranslationGlossRecord) -> str:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    raw_glosses = metadata.get("sense_raw_glosses")
    if isinstance(raw_glosses, Sequence) and not isinstance(raw_glosses, (str, bytes)):
        first = next((str(item).strip() for item in raw_glosses if str(item).strip()), "")
        if first:
            return first
    for key in ("gloss_raw_text", "gloss_fragment_source_text", "gloss_input_text"):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    sanitized = sanitize_dictionary_gloss(record.translation)
    return sanitized or str(record.translation or "").strip()


def build_shadow_canonical_pos(record: TranslationGlossRecord) -> str:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    candidate = str(metadata.get("dictionary_pos_canonical") or "").strip().lower()
    if candidate:
        return candidate
    return str(record.pos_raw or "").strip().lower()


def build_shadow_qualifiers(metadata: Mapping[str, object]) -> dict[str, list[str]] | None:
    qualifiers: dict[str, list[str]] = {}
    tags = normalize_shadow_string_list(
        metadata.get("sense_tags"),
        metadata.get("translation_tags"),
        metadata.get("entry_tags"),
    )
    if tags:
        qualifiers["tags"] = tags
    topics = normalize_shadow_string_list(metadata.get("sense_topics"))
    if topics:
        qualifiers["topics"] = topics
    categories = normalize_shadow_string_list(
        metadata.get("sense_categories"),
        metadata.get("entry_categories"),
    )
    if categories:
        qualifiers["categories"] = categories
    return qualifiers or None


def _build_locator(
    *,
    provider: str,
    target: str,
    entry_ord: int | None,
    sense_ord: int | None,
    gloss_ord: int | None,
    fallback_index: int,
) -> dict[str, object]:
    provider_text = str(provider or "").strip() or "unknown"
    if "wiktionary" in provider_text and entry_ord is not None and sense_ord is not None:
        locator: dict[str, object] = {
            "provider": provider_text,
            "locator_kind": "wiktionary_ordinal",
            "entry_ord": entry_ord,
            "sense_ord": sense_ord,
        }
        if gloss_ord is not None:
            locator["gloss_ord"] = gloss_ord
        return locator
    if gloss_ord is not None:
        return {
            "provider": provider_text,
            "locator_kind": "translation_gloss",
            "target_key": target,
            "gloss_ord": gloss_ord,
        }
    return {
        "provider": provider_text,
        "locator_kind": "opaque",
        "opaque_id": f"{_normalize_shadow_text(target)}:{fallback_index}",
    }


def _normalize_shadow_text(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())
