from __future__ import annotations

import re
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.pos.normalization import (
    CANONICAL_POS_ADPOSITION,
    CANONICAL_POS_ADVERB,
    CANONICAL_POS_CONJUNCTION,
    CANONICAL_POS_DETERMINER,
    CANONICAL_POS_INTERJECTION,
    CANONICAL_POS_PRONOUN,
)
from lexishift_core.resources.dict_loaders import FreedictGlossRecord
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

_FUNCTION_WORD_CANONICALS = frozenset(
    {
        CANONICAL_POS_DETERMINER,
        CANONICAL_POS_PRONOUN,
        CANONICAL_POS_ADPOSITION,
        CANONICAL_POS_CONJUNCTION,
    }
)
_FUNCTION_LIKE_CANONICALS = frozenset({*_FUNCTION_WORD_CANONICALS, CANONICAL_POS_ADVERB})
_REGISTER_MARKERS = ("informal", "colloquial", "slang", "vulgar")
_REGION_MARKERS = (
    "mexico",
    "spain",
    "latin-america",
    "cuba",
    "argentina",
    "chile",
    "colombia",
    "peru",
    "uruguay",
    "venezuela",
)
_REGISTER_CATEGORY_MARKERS = (
    "spanish informal terms",
    "spanish vulgarities",
)
_EXPLICIT_VULGAR_USAGE_MARKERS = (
    "entry_tag:vulgar",
    "sense_tag:vulgar",
    "translation_tag:vulgar",
    "sense_category:spanish vulgarities",
)
_REGION_CATEGORY_MARKERS = (
    "latin american spanish",
    "peninsular spanish",
)
_GRAMMATICAL_POS_HINTS = ("det", "pron", "prep", "conj", "adp", "adposition", "preposition")
_VERB_POS_HINTS = ("verb", "auxiliary", "v")
_EN_ES_MAX_SPLIT_PARTS = 8
_EN_ES_MAX_ALIAS_WORDS = 4
_EN_ES_ARTICLE_PREFIXES = ("a ", "an ", "the ")
_EN_ES_INLINE_ANNOTATION_RE = re.compile(r"\s*(?:\([^)]*\)|\[[^\]]*\]|\{[^}]*\})")
_EN_ES_NOMINAL_HEAD_MAX_WORDS = 6
_EN_ES_NOMINAL_HEAD_CONNECTORS = frozenset({"and", "or"})
_EN_ES_NOMINAL_HEAD_ARTICLES = frozenset({"a", "an", "the"})
_EN_ES_LEADING_ALIAS_MARKERS = (
    "or other",
    "especially",
    "such as",
    "for example",
    "for instance",
    "one in",
)
_EN_ES_NOMINAL_HEAD_BLOCKERS = frozenset(
    {
        "of",
        "for",
        "from",
        "with",
        "without",
        "by",
        "in",
        "into",
        "on",
        "onto",
        "at",
        "to",
        "than",
        "that",
        "which",
        "whose",
        "while",
        "when",
        "where",
    }
)
_EN_ES_NOMINAL_HEAD_GENERIC_TAILS = frozenset(
    {
        "set",
        "kind",
        "sort",
        "type",
        "thing",
        "one",
        "ones",
        "someone",
        "somebody",
        "person",
        "people",
        "collection",
        "group",
        "piece",
        "part",
    }
)
_KAIKKI_POLICY_BASE_DEMOTIONS: Mapping[str, float] = {
    "math_geometry": 0.30,
    "government_law": 0.35,
    "hunting_fishing_tools": 0.30,
    "register_region": 0.35,
    "art_media": 0.25,
    "computing": 0.30,
    "communication_network": 0.30,
    "mechanics_tools": 0.30,
    "music": 0.30,
    "biology": 0.25,
    "chemistry": 0.25,
    "abbreviation_ellipsis_formof": 0.55,
}


def metadata_int_value(metadata: Mapping[str, object], key: str) -> Optional[int]:
    value = metadata.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def metadata_string_tuple(metadata: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = metadata.get(key)
    if isinstance(value, str):
        text = str(value).strip()
        return (text,) if text else ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    values: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            values.append(text)
    return tuple(values)


def build_target_provenance_by_index(
    *,
    target: str,
    entries: Sequence[FreedictGlossRecord],
    canonical_inventory: Sequence[str],
) -> list[dict[str, object]]:
    if not entries:
        return []
    sense_keys = [
        _resolve_entry_sense_key(entry, fallback_index=index) for index, entry in enumerate(entries)
    ]
    sense_order: list[tuple[object, ...]] = []
    sense_position_by_key: dict[tuple[object, ...], int] = {}
    sense_candidate_counts: dict[tuple[object, ...], int] = {}
    sense_ord_by_key: dict[tuple[object, ...], int] = {}
    entry_ord_by_key: dict[tuple[object, ...], int] = {}
    gloss_ord_by_key: dict[tuple[object, ...], int] = {}
    entry_ordinals: list[int] = []
    sense_ordinals: list[int] = []
    for index, entry in enumerate(entries):
        key = sense_keys[index]
        if key not in sense_position_by_key:
            sense_position_by_key[key] = len(sense_order)
            sense_order.append(key)
            metadata = entry.metadata if isinstance(entry.metadata, Mapping) else {}
            sense_ord = metadata_int_value(metadata, "sense_ord")
            if sense_ord is not None:
                sense_ord_by_key[key] = sense_ord
                sense_ordinals.append(sense_ord)
            entry_ord = metadata_int_value(metadata, "entry_ord")
            if entry_ord is not None:
                entry_ord_by_key[key] = entry_ord
                entry_ordinals.append(entry_ord)
            gloss_ord = metadata_int_value(metadata, "gloss_ord")
            if gloss_ord is not None:
                gloss_ord_by_key[key] = gloss_ord
        sense_candidate_counts[key] = sense_candidate_counts.get(key, 0) + 1

    surviving_sense_ordinals = tuple(dict.fromkeys(sense_ordinals))
    surviving_entry_ordinals = tuple(dict.fromkeys(entry_ordinals))
    surviving_canonicals = tuple(
        dict.fromkeys(canonical for canonical in canonical_inventory if canonical)
    )
    provenances: list[dict[str, object]] = []
    for index, _entry in enumerate(entries):
        key = sense_keys[index]
        sense_position = sense_position_by_key[key]
        earlier_keys = sense_order[:sense_position]
        provenance: dict[str, object] = {
            "target": str(target),
            "candidate_total": len(entries),
            "sense_total": len(sense_order),
            "current_sense_position": sense_position,
            "current_sense_candidate_count": sense_candidate_counts.get(key, 0),
            "earlier_sense_count": len(earlier_keys),
            "earlier_candidate_count": sum(
                sense_candidate_counts.get(earlier_key, 0) for earlier_key in earlier_keys
            ),
        }
        current_entry_ord = entry_ord_by_key.get(key)
        if current_entry_ord is not None:
            provenance["current_entry_ord"] = current_entry_ord
        current_sense_ord = sense_ord_by_key.get(key)
        if current_sense_ord is not None:
            provenance["current_sense_ord"] = current_sense_ord
        current_gloss_ord = gloss_ord_by_key.get(key)
        if current_gloss_ord is not None:
            provenance["current_gloss_ord"] = current_gloss_ord
        if surviving_entry_ordinals:
            provenance["surviving_entry_ordinals"] = surviving_entry_ordinals
        if surviving_sense_ordinals:
            provenance["surviving_sense_ordinals"] = surviving_sense_ordinals
        if surviving_canonicals:
            provenance["surviving_dictionary_canonicals"] = surviving_canonicals
        provenances.append(provenance)
    return provenances


def build_definition_bucket_key(
    entry: FreedictGlossRecord,
    *,
    fallback_index: int,
) -> str:
    metadata = entry.metadata if isinstance(entry.metadata, Mapping) else {}
    entry_ord = metadata_int_value(metadata, "entry_ord")
    sense_ord = metadata_int_value(metadata, "sense_ord")
    if entry_ord is not None or sense_ord is not None:
        return (
            f"sense:{entry_ord if entry_ord is not None else 'na'}:"
            f"{sense_ord if sense_ord is not None else 'na'}"
        )
    gloss_ord = metadata_int_value(metadata, "gloss_ord")
    if gloss_ord is not None:
        return f"gloss:{gloss_ord}"
    return f"gloss:{fallback_index}"


def build_gloss_provenance(entry: FreedictGlossRecord) -> dict[str, object]:
    metadata = entry.metadata if isinstance(entry.metadata, Mapping) else {}
    provenance: dict[str, object] = {}
    input_text = str(metadata.get("gloss_input_text") or "").strip()
    if input_text:
        provenance["input_text"] = input_text
    raw_gloss_text = str(metadata.get("gloss_raw_text") or "").strip()
    if raw_gloss_text:
        provenance["raw_gloss_text"] = raw_gloss_text
    source_text = str(metadata.get("gloss_fragment_source_text") or "").strip()
    if source_text:
        provenance["fragment_source_text"] = source_text
    emitted_text = str(entry.translation or "").strip()
    if emitted_text:
        provenance["fragment_emitted_text"] = emitted_text
        provenance["normalized_gloss_text"] = emitted_text
    strategy = str(metadata.get("gloss_fragment_strategy") or "").strip()
    if strategy:
        provenance["fragment_strategy"] = strategy
    separator = str(metadata.get("gloss_fragment_separator") or "").strip()
    if separator:
        provenance["fragment_separator"] = separator
    fragment_index = metadata_int_value(metadata, "gloss_fragment_index")
    if fragment_index is not None:
        provenance["fragment_index"] = fragment_index
    fragment_count = metadata_int_value(metadata, "gloss_fragment_count")
    if fragment_count is not None:
        provenance["fragment_count"] = fragment_count
    operations = metadata.get("gloss_fragment_operations")
    if isinstance(operations, Sequence) and not isinstance(operations, (str, bytes)):
        normalized_operations = tuple(str(item).strip() for item in operations if str(item).strip())
        if normalized_operations:
            provenance["normalization_operations"] = normalized_operations
    if bool(metadata.get("gloss_fragment_parenthetical_stripped")):
        provenance["parenthetical_stripped"] = True
    return provenance


def build_sense_provenance(
    entry: FreedictGlossRecord,
    *,
    dictionary_pos: Optional[Mapping[str, object]],
) -> dict[str, object]:
    metadata = entry.metadata if isinstance(entry.metadata, Mapping) else {}
    provenance: dict[str, object] = {}
    for key in ("entry_ord", "sense_ord", "gloss_ord"):
        value = metadata_int_value(metadata, key)
        if value is not None:
            provenance[key] = value
    pos_raw = str(entry.pos_raw or "").strip()
    if pos_raw:
        provenance["pos_raw"] = pos_raw
    entry_pos_title = str(metadata.get("entry_pos_title") or "").strip()
    if entry_pos_title:
        provenance["entry_pos_title"] = entry_pos_title
    if isinstance(dictionary_pos, Mapping):
        pos_canonical = str(dictionary_pos.get("canonical") or "").strip().lower()
        if pos_canonical:
            provenance["dictionary_pos_canonical"] = pos_canonical
        source_profile = str(dictionary_pos.get("source_profile") or "").strip()
        if source_profile:
            provenance["dictionary_pos_source_profile"] = source_profile
    for key in (
        "sense_raw_glosses",
        "entry_tags",
        "entry_categories",
        "sense_tags",
        "sense_topics",
        "sense_categories",
        "translation_tags",
    ):
        values = metadata_string_tuple(metadata, key)
        if values:
            provenance[key] = values
    for key in ("sense_form_of", "sense_alt_of"):
        relation_value = metadata.get(key)
        if isinstance(relation_value, Sequence) and not isinstance(relation_value, (str, bytes)):
            provenance[key] = tuple(relation_value)
    return provenance


def build_kaikki_policy_shadow_by_index(
    *,
    dictionary_record_views_by_index: Sequence[Mapping[str, object]],
    canonical_inventory: Sequence[str],
    risk_families: Sequence[str],
) -> list[dict[str, object]]:
    configured_risk_families = tuple(
        str(value).strip() for value in risk_families if str(value).strip()
    )
    risk_family_set = set(configured_risk_families)
    family_inventory: list[tuple[str, ...]] = []
    family_fields_by_index: list[Mapping[str, Sequence[str]]] = []
    risky_family_inventory: list[tuple[str, ...]] = []
    for views in dictionary_record_views_by_index:
        kaikki_views = views.get("kaikki") if isinstance(views, Mapping) else None
        if isinstance(kaikki_views, Mapping):
            combined_families = kaikki_views.get("combined_families")
            family_values = (
                tuple(str(value).strip() for value in combined_families if str(value).strip())
                if isinstance(combined_families, Sequence)
                and not isinstance(combined_families, (str, bytes))
                else ()
            )
            family_fields = kaikki_views.get("family_fields")
            normalized_family_fields = family_fields if isinstance(family_fields, Mapping) else {}
        else:
            family_values = ()
            normalized_family_fields = {}
        family_inventory.append(family_values)
        family_fields_by_index.append(normalized_family_fields)
        risky_family_inventory.append(
            tuple(family for family in family_values if family in risk_family_set)
        )

    shadow_by_index: list[dict[str, object]] = []
    for index, families in enumerate(family_inventory):
        risky_families_for_candidate = risky_family_inventory[index]
        family_fields = family_fields_by_index[index]
        current_canonical = canonical_inventory[index] if index < len(canonical_inventory) else ""
        same_canonical_indexes = [
            candidate_index
            for candidate_index, other_canonical in enumerate(canonical_inventory)
            if candidate_index != index
            and current_canonical
            and other_canonical == current_canonical
        ]
        competitor_indexes = (
            same_canonical_indexes
            if same_canonical_indexes
            else [
                candidate_index
                for candidate_index in range(len(family_inventory))
                if candidate_index != index
            ]
        )
        cleaner_indexes = [
            candidate_index
            for candidate_index in competitor_indexes
            if not risky_family_inventory[candidate_index]
        ]
        earlier_cleaner_indexes = [
            candidate_index for candidate_index in cleaner_indexes if candidate_index < index
        ]
        risk_family_sources = {
            family: tuple(
                str(value).strip() for value in family_fields.get(family, ()) if str(value).strip()
            )
            for family in risky_families_for_candidate
        }
        reasons = [f"risk_family:{family}" for family in risky_families_for_candidate]
        if cleaner_indexes:
            reasons.append("clean_competition_present")
        if earlier_cleaner_indexes:
            reasons.append("clean_earlier_competition_present")
        shadow: dict[str, object] = {
            "mode": "shadow",
            "configured_risk_families": configured_risk_families,
            "families": families,
            "risky_families": risky_families_for_candidate,
            "same_canonical_competition": bool(same_canonical_indexes),
            "competitor_count": len(competitor_indexes),
            "cleaner_competitor_count": len(cleaner_indexes),
            "cleaner_earlier_competitor_count": len(earlier_cleaner_indexes),
            "clean_competition_present": bool(cleaner_indexes),
            "clean_earlier_competition_present": bool(earlier_cleaner_indexes),
            "would_demote": bool(risky_families_for_candidate and cleaner_indexes),
            "live_demotion_applied": False,
        }
        if risk_family_sources:
            shadow["risk_family_sources"] = risk_family_sources
        if reasons:
            shadow["reasons"] = tuple(reasons)
        shadow_by_index.append(shadow)
    return shadow_by_index


def resolve_kaikki_policy_live_demotion(
    shadow: Mapping[str, object],
    *,
    family_demotions: Optional[Mapping[str, float]] = None,
) -> tuple[float, tuple[str, ...]]:
    if not bool(shadow.get("would_demote")):
        return 0.0, ()
    risky_families = shadow.get("risky_families")
    if not isinstance(risky_families, Sequence) or isinstance(risky_families, (str, bytes)):
        return 0.0, ()
    resolved_family_demotions = dict(_KAIKKI_POLICY_BASE_DEMOTIONS)
    if isinstance(family_demotions, Mapping):
        for raw_family, raw_value in family_demotions.items():
            family = str(raw_family).strip()
            if not family:
                continue
            try:
                value = max(0.0, float(raw_value))
            except (TypeError, ValueError):
                continue
            resolved_family_demotions[family] = value
    matched_families = [
        str(family).strip()
        for family in risky_families
        if str(family).strip() in resolved_family_demotions
    ]
    if not matched_families:
        return 0.0, ()
    demotion = max(resolved_family_demotions[family] for family in matched_families)
    reasons = tuple(f"kaikki_policy:{family}" for family in matched_families)
    return demotion, reasons


def resolve_kaikki_policy_live_suppression(
    shadow: Mapping[str, object],
) -> tuple[bool, tuple[str, ...]]:
    if not bool(shadow.get("clean_competition_present")):
        return False, ()
    risk_family_sources = shadow.get("risk_family_sources")
    if not isinstance(risk_family_sources, Mapping):
        return False, ()
    register_sources = risk_family_sources.get("register_region")
    if not isinstance(register_sources, Sequence) or isinstance(register_sources, (str, bytes)):
        return False, ()
    matched_sources = tuple(
        marker
        for marker in register_sources
        if str(marker).strip() in _EXPLICIT_VULGAR_USAGE_MARKERS
    )
    if not matched_sources:
        return False, ()
    reasons = [f"kaikki_policy_suppress:{marker}" for marker in matched_sources]
    if bool(shadow.get("clean_earlier_competition_present")):
        reasons.append("kaikki_policy_suppress:clean_earlier_competition")
    else:
        reasons.append("kaikki_policy_suppress:clean_competition")
    return True, tuple(reasons)


def resolve_kaikki_provenance_competition_demotion(
    *,
    target_provenance: Mapping[str, object] | None,
    gloss_provenance: Mapping[str, object] | None,
    shadow: Mapping[str, object] | None,
    late_sense_clean_earlier_competition_penalty: float,
) -> tuple[float, tuple[str, ...]]:
    try:
        penalty = max(0.0, float(late_sense_clean_earlier_competition_penalty))
    except (TypeError, ValueError):
        penalty = 0.0
    if penalty <= 0.0:
        return 0.0, ()
    if not isinstance(target_provenance, Mapping) or not isinstance(shadow, Mapping):
        return 0.0, ()
    current_sense_position = metadata_int_value(target_provenance, "current_sense_position") or 0
    if current_sense_position <= 0:
        return 0.0, ()
    if not bool(shadow.get("clean_earlier_competition_present")):
        return 0.0, ()
    reasons = ["kaikki_provenance:late_sense_clean_earlier_competition"]
    if isinstance(gloss_provenance, Mapping):
        fragment_strategy = str(gloss_provenance.get("fragment_strategy") or "").strip()
        if fragment_strategy and fragment_strategy.lower() != "identity":
            reasons.append(f"kaikki_provenance:fragment_strategy:{fragment_strategy}")
    return penalty, tuple(reasons)


def collect_sanitized_gloss_records(
    records: Iterable[FreedictGlossRecord],
) -> list[FreedictGlossRecord]:
    cleaned: list[FreedictGlossRecord] = []
    seen: dict[str, int] = {}
    for record in records:
        normalized_pos = str(record.pos_raw or "").strip()
        variants = _expand_en_es_gloss_variants(record.translation, pos_raw=normalized_pos)
        for sanitized, variant_metadata in variants:
            if not sanitized:
                continue
            existing_index = seen.get(sanitized)
            metadata = dict(record.metadata)
            if variant_metadata:
                metadata.update(variant_metadata)
            if existing_index is None:
                metadata.setdefault("gloss_variant_occurrence_count", 1)
                cleaned.append(
                    FreedictGlossRecord(
                        translation=sanitized,
                        pos_raw=normalized_pos,
                        metadata=metadata,
                    )
                )
                seen[sanitized] = len(cleaned) - 1
                continue
            existing_record = cleaned[existing_index]
            existing_metadata = dict(existing_record.metadata)
            existing_count = metadata_int_value(existing_metadata, "gloss_variant_occurrence_count")
            existing_metadata["gloss_variant_occurrence_count"] = (
                int(existing_count) if existing_count is not None else 1
            ) + 1
            resolved_pos = existing_record.pos_raw or normalized_pos
            cleaned[existing_index] = FreedictGlossRecord(
                translation=sanitized,
                pos_raw=resolved_pos,
                metadata=existing_metadata,
            )
    return cleaned


def extract_canonical_from_component(component: Optional[Mapping[str, object]]) -> str:
    if not isinstance(component, Mapping):
        return ""
    return str(component.get("canonical") or "").strip().lower()


def should_shadow_interjection(
    *,
    current_canonical: str,
    entry_metadata: Mapping[str, object],
    earlier_canonicals: Sequence[str],
) -> bool:
    if current_canonical != CANONICAL_POS_INTERJECTION:
        return False
    if any(canonical in _FUNCTION_WORD_CANONICALS for canonical in earlier_canonicals):
        return True
    if any(
        canonical and canonical != CANONICAL_POS_INTERJECTION for canonical in earlier_canonicals
    ):
        return resolve_kaikki_register_demotion(entry_metadata) > 0.0
    return False


def should_demote_shadowed_adverb(
    *,
    current_canonical: str,
    canonical_inventory: Sequence[str],
) -> bool:
    if current_canonical != CANONICAL_POS_ADVERB:
        return False
    observed = [canonical for canonical in canonical_inventory if canonical]
    if not observed:
        return False
    if any(canonical not in _FUNCTION_LIKE_CANONICALS for canonical in observed):
        return False
    return any(canonical in _FUNCTION_WORD_CANONICALS for canonical in observed)


def resolve_kaikki_register_demotion(metadata: Mapping[str, object]) -> float:
    register_hit, region_hit = _resolve_kaikki_register_hits(metadata)
    if not register_hit and not region_hit:
        return 0.0
    if register_hit and region_hit:
        return 0.55
    if register_hit:
        return 0.40
    if region_hit:
        return 0.20
    return 0.0


def apply_semantic_demotion(
    metadata: dict[str, object],
    *,
    demotion: float,
    reason: str,
) -> None:
    try:
        parsed = float(demotion)
    except (TypeError, ValueError):
        return
    if parsed <= 0.0:
        return
    existing = metadata.get("semantic_demotion")
    if isinstance(existing, bool):
        existing_value = 0.0
    elif isinstance(existing, (int, float, str)):
        try:
            existing_value = float(existing)
        except ValueError:
            existing_value = 0.0
    else:
        existing_value = 0.0
    if parsed <= existing_value:
        return
    metadata["semantic_demotion"] = parsed
    metadata["semantic_demotion_reason"] = reason


def normalize_reverse_token(value: object) -> str:
    return normalize_reverse_token_with_pos(value)


def normalize_reverse_token_with_pos(
    value: object,
    *,
    pos_raw: object = "",
) -> str:
    normalized = sanitize_dictionary_gloss(value).lower()
    if not normalized:
        return ""
    if _raw_pos_looks_verbal(pos_raw) and normalized.startswith("to "):
        stripped = normalized[3:].strip()
        if stripped:
            return stripped
    return normalized


def build_reverse_lookup(
    records_by_source: Mapping[str, Sequence[FreedictGlossRecord]],
) -> dict[str, tuple[str, ...]]:
    lookup: dict[str, tuple[str, ...]] = {}
    for raw_source, raw_records in records_by_source.items():
        source_pos_raw = next(
            (
                str(record.pos_raw or "").strip()
                for record in raw_records
                if str(record.pos_raw or "").strip()
            ),
            "",
        )
        source_norm = normalize_reverse_token_with_pos(raw_source, pos_raw=source_pos_raw)
        if not source_norm:
            continue
        ordered: list[str] = []
        seen: set[str] = set()
        for record in raw_records:
            target_norm = normalize_reverse_token(record.translation)
            if not target_norm or target_norm in seen:
                continue
            seen.add(target_norm)
            ordered.append(target_norm)
        lookup[source_norm] = tuple(ordered)
    return lookup


def _resolve_entry_sense_key(
    entry: FreedictGlossRecord,
    *,
    fallback_index: int,
) -> tuple[object, ...]:
    metadata = entry.metadata if isinstance(entry.metadata, Mapping) else {}
    entry_ord = metadata_int_value(metadata, "entry_ord")
    sense_ord = metadata_int_value(metadata, "sense_ord")
    if entry_ord is not None or sense_ord is not None:
        return ("sense", entry_ord, sense_ord)
    gloss_ord = metadata_int_value(metadata, "gloss_ord")
    if gloss_ord is not None:
        return ("gloss", gloss_ord)
    return ("fallback", fallback_index)


def _expand_en_es_gloss_variants(
    translation: object,
    *,
    pos_raw: str,
) -> list[tuple[str, dict[str, object]]]:
    input_text = str(translation or "").strip()
    sanitized = sanitize_dictionary_gloss(translation)
    if not sanitized:
        return []
    fragments = _split_en_es_gloss_fragments(sanitized, pos_raw=pos_raw)
    variants: list[tuple[str, dict[str, object]]] = []
    seen: set[str] = set()
    fragment_count = len(fragments)
    for index, fragment in enumerate(fragments):
        raw_source_text = str(fragment.get("raw_text") or "").strip()
        fragment_text = str(fragment.get("text") or "").strip()
        normalization_input = fragment_text or raw_source_text
        normalized_text, normalization_operations = _normalize_en_es_gloss_fragment(
            normalization_input
        )
        if not normalized_text or normalized_text in seen:
            continue
        raw_operations = fragment.get("operations", ())
        if isinstance(raw_operations, Sequence) and not isinstance(raw_operations, (str, bytes)):
            operations = [str(item).strip() for item in raw_operations if str(item).strip()]
        else:
            operations = []
        operations.extend(normalization_operations)
        metadata: dict[str, object] = {
            "gloss_fragment_index": index,
            "gloss_fragment_count": fragment_count,
            "gloss_fragment_strategy": str(fragment.get("strategy") or "identity"),
            "gloss_input_text": input_text,
            "gloss_raw_text": sanitized,
            "gloss_fragment_emitted_text": normalized_text,
        }
        separator = str(fragment.get("separator") or "").strip()
        if separator:
            metadata["gloss_fragment_separator"] = separator
        if raw_source_text:
            metadata["gloss_fragment_source_text"] = raw_source_text
        if operations:
            metadata["gloss_fragment_operations"] = tuple(dict.fromkeys(operations))
        if "strip_inline_annotation" in operations:
            metadata["gloss_fragment_parenthetical_stripped"] = True
        variants.append((normalized_text, metadata))
        seen.add(normalized_text)
        head_variant = _recover_en_es_nominal_head_variant(normalized_text, pos_raw=pos_raw)
        if head_variant:
            head_text, head_operations = head_variant
            if head_text and head_text not in seen:
                head_metadata = dict(metadata)
                head_metadata["gloss_fragment_strategy"] = "nominal_head"
                head_metadata["gloss_fragment_emitted_text"] = head_text
                merged_operations = tuple(dict.fromkeys((*operations, *head_operations)))
                if merged_operations:
                    head_metadata["gloss_fragment_operations"] = merged_operations
                variants.append((head_text, head_metadata))
                seen.add(head_text)
        alias_variant = _recover_en_es_leading_alias_variant(normalized_text, pos_raw=pos_raw)
        if alias_variant:
            alias_text, alias_operations = alias_variant
            if alias_text and alias_text not in seen:
                alias_metadata = dict(metadata)
                alias_metadata["gloss_fragment_strategy"] = "leading_alias"
                alias_metadata["gloss_fragment_emitted_text"] = alias_text
                merged_operations = tuple(dict.fromkeys((*operations, *alias_operations)))
                if merged_operations:
                    alias_metadata["gloss_fragment_operations"] = merged_operations
                variants.append((alias_text, alias_metadata))
                seen.add(alias_text)
    if variants:
        return variants
    normalized_text, normalization_operations = _normalize_en_es_gloss_fragment(sanitized)
    if not normalized_text:
        return []
    fallback_metadata: dict[str, object] = {
        "gloss_fragment_index": 0,
        "gloss_fragment_count": 1,
        "gloss_fragment_strategy": "identity",
        "gloss_input_text": input_text,
        "gloss_raw_text": sanitized,
        "gloss_fragment_emitted_text": normalized_text,
    }
    if normalization_operations:
        fallback_metadata["gloss_fragment_operations"] = normalization_operations
    if "strip_inline_annotation" in normalization_operations:
        fallback_metadata["gloss_fragment_parenthetical_stripped"] = True
    variants = [(normalized_text, fallback_metadata)]
    head_variant = _recover_en_es_nominal_head_variant(normalized_text, pos_raw=pos_raw)
    if head_variant:
        head_text, head_operations = head_variant
        if head_text and head_text != normalized_text:
            head_metadata = dict(fallback_metadata)
            head_metadata["gloss_fragment_strategy"] = "nominal_head"
            head_metadata["gloss_fragment_emitted_text"] = head_text
            merged_operations = tuple(dict.fromkeys((*normalization_operations, *head_operations)))
            if merged_operations:
                head_metadata["gloss_fragment_operations"] = merged_operations
            variants.append((head_text, head_metadata))
    alias_variant = _recover_en_es_leading_alias_variant(normalized_text, pos_raw=pos_raw)
    if alias_variant:
        alias_text, alias_operations = alias_variant
        if alias_text and alias_text != normalized_text:
            alias_metadata = dict(fallback_metadata)
            alias_metadata["gloss_fragment_strategy"] = "leading_alias"
            alias_metadata["gloss_fragment_emitted_text"] = alias_text
            merged_operations = tuple(dict.fromkeys((*normalization_operations, *alias_operations)))
            if merged_operations:
                alias_metadata["gloss_fragment_operations"] = merged_operations
            variants.append((alias_text, alias_metadata))
    return variants


def _split_en_es_gloss_fragments(text: str, *, pos_raw: str) -> list[dict[str, object]]:
    semicolon_parts = _split_top_level_fragments(text, separator=";")
    if _should_split_semicolon_fragments(semicolon_parts):
        fragments: list[dict[str, object]] = []
        for part in semicolon_parts:
            fragments.extend(_split_en_es_comma_fragments(part, pos_raw=pos_raw))
        return fragments or [
            {"raw_text": text, "text": text, "strategy": "identity", "separator": ""}
        ]
    return _split_en_es_comma_fragments(text, pos_raw=pos_raw)


def _split_en_es_comma_fragments(text: str, *, pos_raw: str) -> list[dict[str, object]]:
    comma_parts = _split_top_level_fragments(text, separator=",")
    if not _should_split_comma_fragments(comma_parts, pos_raw=pos_raw):
        return [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]
    verb_list = _looks_like_verb_comma_gloss(comma_parts, pos_raw=pos_raw)
    prefix_infinitive = bool(comma_parts and comma_parts[0].strip().lower().startswith("to "))
    fragments: list[dict[str, object]] = []
    for part in comma_parts:
        raw_fragment_text = re.sub(r"\s+", " ", str(part or "")).strip()
        if not raw_fragment_text:
            continue
        if not _normalize_en_es_gloss_fragment(raw_fragment_text)[0]:
            continue
        fragment_text = raw_fragment_text
        operations: list[str] = []
        if verb_list and prefix_infinitive and not fragment_text.lower().startswith("to "):
            fragment_text = f"to {fragment_text}"
            operations.append("prepend_to_prefix")
        fragments.append(
            {
                "raw_text": raw_fragment_text,
                "text": fragment_text,
                "strategy": "top_level_comma",
                "separator": ",",
                "operations": tuple(operations),
            }
        )
    return fragments or [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]


def _allows_en_es_comma_split(pos_raw: str) -> bool:
    lowered = str(pos_raw or "").strip().lower()
    return any(marker in lowered for marker in _GRAMMATICAL_POS_HINTS)


def _normalize_en_es_gloss_fragment(text: str) -> tuple[str, tuple[str, ...]]:
    raw_text = str(text or "").strip()
    if not raw_text:
        return "", ()
    operations: list[str] = []
    collapsed = re.sub(r"\s+", " ", raw_text).strip()
    if collapsed != raw_text:
        operations.append("sanitize_gloss")
    stripped = _strip_inline_gloss_annotations(collapsed)
    if stripped != collapsed:
        operations.append("strip_inline_annotation")
    normalized = sanitize_dictionary_gloss(stripped)
    if normalized:
        if normalized != stripped:
            operations.append("resanitize_gloss")
        return normalized, tuple(dict.fromkeys(operations))
    sanitized = sanitize_dictionary_gloss(collapsed)
    if sanitized:
        return sanitized, tuple(dict.fromkeys(operations))
    return "", tuple(dict.fromkeys(operations))


def _recover_en_es_nominal_head_variant(
    text: str,
    *,
    pos_raw: str,
) -> tuple[str, tuple[str, ...]] | None:
    lowered_pos = str(pos_raw or "").strip().lower()
    if not lowered_pos:
        return None
    if _raw_pos_looks_verbal(lowered_pos):
        return None
    if any(marker in lowered_pos for marker in _GRAMMATICAL_POS_HINTS):
        return None
    normalized = sanitize_dictionary_gloss(text)
    if not normalized:
        return None
    if any(separator in normalized for separator in (",", ";", "/")):
        return None
    words = [token for token in normalized.lower().split(" ") if token]
    if len(words) < 3 or len(words) > _EN_ES_NOMINAL_HEAD_MAX_WORDS:
        return None
    if any(any(character.isdigit() for character in token) for token in words):
        return None
    if any(token in _EN_ES_NOMINAL_HEAD_BLOCKERS for token in words[:-1]):
        return None
    if any(
        not re.fullmatch(r"[a-z][a-z-]*", token)
        and token not in _EN_ES_NOMINAL_HEAD_CONNECTORS
        and token not in _EN_ES_NOMINAL_HEAD_ARTICLES
        for token in words
    ):
        return None
    head = words[-1]
    if head in _EN_ES_NOMINAL_HEAD_CONNECTORS or head in _EN_ES_NOMINAL_HEAD_GENERIC_TAILS:
        return None
    prefix_words = [
        token
        for token in words[:-1]
        if token not in _EN_ES_NOMINAL_HEAD_CONNECTORS and token not in _EN_ES_NOMINAL_HEAD_ARTICLES
    ]
    if len(prefix_words) < 2 and not any(
        token in _EN_ES_NOMINAL_HEAD_CONNECTORS for token in words[:-1]
    ):
        return None
    if not re.fullmatch(r"[a-z][a-z-]*", head):
        return None
    return head, ("extract_nominal_head",)


def _recover_en_es_leading_alias_variant(
    text: str,
    *,
    pos_raw: str,
) -> tuple[str, tuple[str, ...]] | None:
    lowered_pos = str(pos_raw or "").strip().lower()
    if not lowered_pos:
        return None
    if _raw_pos_looks_verbal(lowered_pos):
        return None
    if any(marker in lowered_pos for marker in _GRAMMATICAL_POS_HINTS):
        return None
    normalized = sanitize_dictionary_gloss(text)
    if not normalized or "," not in normalized:
        return None
    parts = _split_top_level_fragments(normalized, separator=",")
    if len(parts) < 2 or len(parts) > _EN_ES_MAX_SPLIT_PARTS:
        return None
    first = _normalize_en_es_gloss_fragment(parts[0])[0]
    if not first or _word_count(first) > 2:
        return None
    lowered_first = first.lower()
    if lowered_first.startswith(_EN_ES_ARTICLE_PREFIXES):
        return None
    trailing_parts = [_normalize_en_es_gloss_fragment(part)[0] for part in parts[1:]]
    trailing_parts = [part for part in trailing_parts if part]
    if not trailing_parts:
        return None
    trailing_text = " ".join(trailing_parts).lower()
    if not any(marker in trailing_text for marker in _EN_ES_LEADING_ALIAS_MARKERS):
        return None
    if not any(_word_count(part) > _EN_ES_MAX_ALIAS_WORDS for part in trailing_parts):
        return None
    return first, ("extract_leading_alias",)


def _strip_inline_gloss_annotations(text: str) -> str:
    current = str(text or "").strip()
    previous = None
    while current and current != previous:
        previous = current
        current = _EN_ES_INLINE_ANNOTATION_RE.sub("", current)
        current = re.sub(r"\s+", " ", current).strip()
    return current


def _split_top_level_fragments(text: str, *, separator: str) -> list[str]:
    if not text or separator not in text:
        return [text]
    parts: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    for char in text:
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth > 0:
            bracket_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth > 0:
            brace_depth -= 1
        if char == separator and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            part = "".join(buffer).strip()
            if part:
                parts.append(part)
            buffer = []
            continue
        buffer.append(char)
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return parts or [text]


def _should_split_semicolon_fragments(parts: Sequence[str]) -> bool:
    if len(parts) <= 1 or len(parts) > _EN_ES_MAX_SPLIT_PARTS:
        return False
    return all(sanitize_dictionary_gloss(part) for part in parts)


def _should_split_comma_fragments(parts: Sequence[str], *, pos_raw: str) -> bool:
    if len(parts) <= 1 or len(parts) > _EN_ES_MAX_SPLIT_PARTS:
        return False
    normalized_parts = [_normalize_en_es_gloss_fragment(part)[0] for part in parts]
    if not all(normalized_parts):
        return False
    if _allows_en_es_comma_split(pos_raw):
        return True
    if _looks_like_verb_comma_gloss(parts, pos_raw=pos_raw):
        return True
    return _looks_like_alias_gloss_list(normalized_parts)


def _looks_like_verb_comma_gloss(parts: Sequence[str], *, pos_raw: str) -> bool:
    lowered = str(pos_raw or "").strip().lower()
    if not any(marker in lowered for marker in _VERB_POS_HINTS):
        return False
    normalized_parts = [_normalize_en_es_gloss_fragment(part)[0] for part in parts]
    if not all(normalized_parts):
        return False
    if not normalized_parts[0].lower().startswith("to "):
        return False
    return all(_word_count(fragment) <= _EN_ES_MAX_ALIAS_WORDS for fragment in normalized_parts)


def _looks_like_alias_gloss_list(parts: Sequence[str]) -> bool:
    if len(parts) > 4:
        return False
    for fragment in parts:
        lowered = fragment.strip().lower()
        if not lowered:
            return False
        if lowered.startswith(_EN_ES_ARTICLE_PREFIXES):
            return False
        if _word_count(fragment) > _EN_ES_MAX_ALIAS_WORDS:
            return False
    return True


def _word_count(text: str) -> int:
    return len([token for token in str(text or "").strip().split(" ") if token])


def _collect_lowered_metadata_markers(value: object) -> tuple[str, ...]:
    markers: list[str] = []
    _visit_marker_values(value, markers)
    return tuple(markers)


def _resolve_kaikki_register_hits(metadata: Mapping[str, object]) -> tuple[bool, bool]:
    register_hit = False
    region_hit = False
    views = metadata.get("dictionary_record_views")
    if isinstance(views, Mapping):
        nested_views = views.get("kaikki")
        normalized_views = nested_views if isinstance(nested_views, Mapping) else views
        combined_prefixed_markers = normalized_views.get("combined_prefixed_markers")
        combined_markers = _collect_lowered_metadata_markers(combined_prefixed_markers)
        if combined_markers:
            register_hit, region_hit = _scan_prefixed_register_markers(combined_markers)
            if register_hit or region_hit:
                return register_hit, region_hit
    raw_record = metadata.get("dictionary_record")
    if isinstance(raw_record, Mapping):
        record_register_hit, record_region_hit = _scan_raw_register_markers(raw_record)
        register_hit = register_hit or record_register_hit
        region_hit = region_hit or record_region_hit
    metadata_register_hit, metadata_region_hit = _scan_raw_register_markers(metadata)
    register_hit = register_hit or metadata_register_hit
    region_hit = region_hit or metadata_region_hit
    return register_hit, region_hit


def _scan_prefixed_register_markers(markers: Sequence[str]) -> tuple[bool, bool]:
    register_hit = False
    region_hit = False
    for marker in markers:
        text = str(marker or "").strip().lower()
        if not text or ":" not in text:
            continue
        prefix, raw_value = text.split(":", 1)
        value = raw_value.strip()
        if prefix in {"entry_tag", "sense_tag", "translation_tag"}:
            if any(token in value for token in _REGISTER_MARKERS):
                register_hit = True
            if any(token in value for token in _REGION_MARKERS):
                region_hit = True
        elif prefix in {"entry_category", "sense_category"}:
            if value in _REGISTER_CATEGORY_MARKERS:
                register_hit = True
            if value in _REGION_CATEGORY_MARKERS:
                region_hit = True
    return register_hit, region_hit


def _scan_raw_register_markers(metadata: Mapping[str, object]) -> tuple[bool, bool]:
    register_hit = False
    region_hit = False
    tag_keys = ("entry_tags", "sense_tags", "translation_tags")
    category_keys = ("entry_categories", "sense_categories")
    for key in tag_keys:
        if key not in metadata:
            continue
        markers = _collect_lowered_metadata_markers(metadata.get(key))
        if any(any(token in marker for token in _REGISTER_MARKERS) for marker in markers):
            register_hit = True
        if any(any(token in marker for token in _REGION_MARKERS) for marker in markers):
            region_hit = True
    for key in category_keys:
        if key not in metadata:
            continue
        markers = _collect_lowered_metadata_markers(metadata.get(key))
        if any(marker in _REGISTER_CATEGORY_MARKERS for marker in markers):
            register_hit = True
        if any(marker in _REGION_CATEGORY_MARKERS for marker in markers):
            region_hit = True
    return register_hit, region_hit


def _raw_pos_looks_verbal(value: object) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in _VERB_POS_HINTS)


def _visit_marker_values(value: object, markers: list[str]) -> None:
    if isinstance(value, str):
        text = " ".join(value.strip().lower().split())
        if text:
            markers.append(text)
        return
    if isinstance(value, Mapping):
        for item in value.values():
            _visit_marker_values(item, markers)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _visit_marker_values(item, markers)
