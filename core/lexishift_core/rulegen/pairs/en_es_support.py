from __future__ import annotations

from typing import Mapping, Optional, Sequence

from lexishift_core.pos.normalization import (
    CANONICAL_POS_ADPOSITION,
    CANONICAL_POS_ADVERB,
    CANONICAL_POS_CONJUNCTION,
    CANONICAL_POS_DETERMINER,
    CANONICAL_POS_INTERJECTION,
    CANONICAL_POS_PRONOUN,
)
from lexishift_core.resources.dict_loaders import FreedictGlossRecord
from lexishift_core.rulegen.pairs.en_es_gloss_processing import (
    build_reverse_lookup as _build_reverse_lookup,
    collect_sanitized_gloss_records as _collect_sanitized_gloss_records,
    normalize_reverse_token as _normalize_reverse_token,
    normalize_reverse_token_with_pos as _normalize_reverse_token_with_pos,
)

build_reverse_lookup = _build_reverse_lookup
collect_sanitized_gloss_records = _collect_sanitized_gloss_records
normalize_reverse_token = _normalize_reverse_token
normalize_reverse_token_with_pos = _normalize_reverse_token_with_pos

_FUNCTION_WORD_CANONICALS = frozenset(
    {
        CANONICAL_POS_DETERMINER,
        CANONICAL_POS_PRONOUN,
        CANONICAL_POS_ADPOSITION,
        CANONICAL_POS_CONJUNCTION,
    }
)
_FUNCTION_LIKE_CANONICALS = frozenset({*_FUNCTION_WORD_CANONICALS, CANONICAL_POS_ADVERB})
_REGISTER_MARKERS = ("informal", "colloquial", "slang")
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
_KAIKKI_POLICY_BASE_DEMOTIONS: Mapping[str, float] = {
    "math_geometry": 0.30,
    "government_law": 0.35,
    "hunting_fishing_tools": 0.30,
    "register_region": 0.35,
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
    gloss_ord = metadata_int_value(metadata, "gloss_ord")
    if entry_ord is not None and sense_ord is None and gloss_ord is not None:
        return f"sense:{entry_ord}:gloss:{gloss_ord}"
    if entry_ord is not None or sense_ord is not None:
        return (
            f"sense:{entry_ord if entry_ord is not None else 'na'}:"
            f"{sense_ord if sense_ord is not None else 'na'}"
        )
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
) -> tuple[float, tuple[str, ...]]:
    if not bool(shadow.get("would_demote")):
        return 0.0, ()
    risky_families = shadow.get("risky_families")
    if not isinstance(risky_families, Sequence) or isinstance(risky_families, (str, bytes)):
        return 0.0, ()
    matched_families = [
        str(family).strip()
        for family in risky_families
        if str(family).strip() in _KAIKKI_POLICY_BASE_DEMOTIONS
    ]
    if not matched_families:
        return 0.0, ()
    demotion = max(_KAIKKI_POLICY_BASE_DEMOTIONS[family] for family in matched_families)
    reasons = tuple(f"kaikki_policy:{family}" for family in matched_families)
    return demotion, reasons


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
    markers = _collect_lowered_metadata_markers(metadata)
    if not markers:
        return 0.0
    register_hit = any(any(token in marker for token in _REGISTER_MARKERS) for marker in markers)
    region_hit = any(any(token in marker for token in _REGION_MARKERS) for marker in markers)
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


def _collect_lowered_metadata_markers(value: object) -> tuple[str, ...]:
    markers: list[str] = []
    _visit_marker_values(value, markers)
    return tuple(markers)


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
