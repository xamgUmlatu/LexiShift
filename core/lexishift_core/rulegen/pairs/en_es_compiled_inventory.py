from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.generation import RuleCandidate, extract_candidate_pos_canonical
from lexishift_core.rulegen.pairs.en_es_support import (
    apply_semantic_demotion as _apply_semantic_demotion,
    build_definition_bucket_key as _build_definition_bucket_key,
    build_gloss_provenance as _build_gloss_provenance,
    build_sense_provenance as _build_sense_provenance,
    normalize_reverse_token_with_pos as _normalize_reverse_token_with_pos,
    resolve_kaikki_register_demotion as _resolve_kaikki_register_demotion,
    should_demote_shadowed_adverb as _should_demote_shadowed_adverb,
    should_shadow_interjection as _should_shadow_interjection,
)
from lexishift_core.rulegen.pairs.pos_utils import build_candidate_pos_metadata
from lexishift_core.rulegen.semantic_demotion import resolve_generic_gloss_demotion
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    LeadingEnglishInfinitiveNormalizer,
)


@dataclass(frozen=True)
class EnEsCompiledCandidateFact:
    candidate_id: int
    target_id: int
    definition_bucket_id: int
    source_dict_id: int
    source_type_id: int
    local_candidate_index: int
    gloss_index: int
    gloss_total: int
    source_phrase: str
    reverse_check_source_norm: str
    reverse_check_target_norm: str
    reverse_check_supported: bool
    reverse_check_hit: bool
    reverse_check_rank: Optional[int]
    reverse_check_total: int
    source_phrase_token_count: int
    source_phrase_is_ascii: bool
    source_phrase_is_phrase: bool
    is_variant: bool
    source_pos_canonical: str
    target_pos_canonical: str
    dictionary_pos_canonical: str
    semantic_demotion_base: float
    semantic_demotion_reason: Optional[str]
    interjection_shadowed: bool
    has_word_package: bool
    has_gloss_provenance: bool
    has_sense_provenance: bool
    has_target_provenance: bool
    current_sense_position: int
    kaikkei_family_names: tuple[str, ...] = ()
    family_marker_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class EnEsCompiledCandidateTable:
    candidate_ids: tuple[int, ...] = ()
    target_ids: tuple[int, ...] = ()
    definition_bucket_ids: tuple[int, ...] = ()
    source_phrases: tuple[str, ...] = ()
    source_phrase_lowers: tuple[str, ...] = ()
    normalized_source_phrases: tuple[str, ...] = ()
    normalized_source_phrase_order_ids: tuple[int, ...] = ()
    source_dict_ids: tuple[int, ...] = ()
    source_type_ids: tuple[int, ...] = ()
    local_candidate_indices: tuple[int, ...] = ()
    gloss_indices: tuple[int, ...] = ()
    gloss_totals: tuple[int, ...] = ()
    semantic_demotion_bases: tuple[float, ...] = ()
    source_pos_canonicals: tuple[str, ...] = ()
    target_pos_canonicals: tuple[str, ...] = ()
    dictionary_pos_canonicals: tuple[str, ...] = ()
    phrase_flags: tuple[bool, ...] = ()
    variant_flags: tuple[bool, ...] = ()
    interjection_shadowed_flags: tuple[bool, ...] = ()
    reverse_check_supported_flags: tuple[bool, ...] = ()
    reverse_check_hit_flags: tuple[bool, ...] = ()
    reverse_check_rank_values: tuple[int, ...] = ()
    reverse_check_total_values: tuple[int, ...] = ()
    current_sense_positions: tuple[int, ...] = ()
    family_marker_id_rows: tuple[tuple[int, ...], ...] = ()
    candidate_row_id_by_candidate_id: Mapping[int, int] = field(default_factory=dict)
    candidate_row_ids_by_target_id: Mapping[int, tuple[int, ...]] = field(default_factory=dict)
    candidate_row_ids_by_definition_bucket_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )
    candidate_row_ids_by_family_marker_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class EnEsCompiledTargetContext:
    target: str
    target_reverse_norm: str
    target_word_package: Optional[Mapping[str, object]]
    target_pos: Mapping[str, object]
    entries: tuple[TranslationGlossRecord, ...]
    dictionary_poses: tuple[Mapping[str, object], ...]
    canonical_inventory: tuple[str, ...]
    dictionary_record_views_by_index: tuple[Mapping[str, object], ...]
    target_provenance_by_index: tuple[Mapping[str, object], ...]
    target_id: int = -1
    base_candidates: tuple[RuleCandidate, ...] = ()
    candidate_facts: tuple[EnEsCompiledCandidateFact, ...] = ()


@dataclass(frozen=True)
class EnEsCompiledResources:
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]]
    reverse_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext] = field(
        default_factory=dict
    )
    target_ids_by_target: Mapping[str, int] = field(default_factory=dict)
    definition_bucket_ids_by_key: Mapping[str, int] = field(default_factory=dict)
    family_marker_ids_by_name: Mapping[str, int] = field(default_factory=dict)
    source_dict_ids_by_name: Mapping[str, int] = field(default_factory=dict)
    source_type_ids_by_name: Mapping[str, int] = field(default_factory=dict)
    candidate_facts: tuple[EnEsCompiledCandidateFact, ...] = ()
    candidate_table: Optional[EnEsCompiledCandidateTable] = None
    gloss_base_forms: frozenset[str] = frozenset()
    reverse_lookup: Optional[Mapping[str, tuple[str, ...]]] = None
    compile_version: int = 3
    cache_token: int = -1


def _normalize_compiled_source_phrase(source_phrase: object) -> str:
    phrase = str(source_phrase or "")
    normalized = BasicStringNormalizer().normalize(
        RuleCandidate(
            source_phrase=phrase,
            replacement="",
            language_pair="en-es",
            source_dict="compiled",
        )
    )
    normalized = LeadingEnglishInfinitiveNormalizer().normalize(normalized)
    return str(normalized.source_phrase or "").strip()


def _build_static_candidate_inventory(
    *,
    target: str,
    language_pair: str,
    source_dict: str,
    source_type: str,
    target_reverse_norm: str,
    target_word_package: Optional[Mapping[str, object]],
    target_pos: Mapping[str, object],
    entries: Sequence[TranslationGlossRecord],
    dictionary_poses: Sequence[Mapping[str, object]],
    canonical_inventory: Sequence[str],
    dictionary_record_views_by_index: Sequence[Mapping[str, object]],
    target_provenance_by_index: Sequence[Mapping[str, object]],
    reverse_lookup: Optional[Mapping[str, tuple[str, ...]]],
    generic_gloss_demotions: Mapping[str, float],
) -> tuple[RuleCandidate, ...]:
    total = len(entries)
    candidates: list[RuleCandidate] = []
    for index, entry in enumerate(entries):
        dictionary_pos = dictionary_poses[index] if index < len(dictionary_poses) else {}
        dictionary_canonical = (
            canonical_inventory[index] if index < len(canonical_inventory) else ""
        )
        dictionary_record_views = (
            dictionary_record_views_by_index[index]
            if index < len(dictionary_record_views_by_index)
            else {}
        )
        target_provenance = (
            target_provenance_by_index[index] if index < len(target_provenance_by_index) else None
        )
        metadata = _build_static_candidate_metadata(
            entry=entry,
            index=index,
            total=total,
            target=target,
            target_reverse_norm=target_reverse_norm,
            target_word_package=target_word_package,
            target_pos=target_pos,
            dictionary_pos=dictionary_pos,
            dictionary_canonical=dictionary_canonical,
            canonical_inventory=canonical_inventory,
            dictionary_record_views=dictionary_record_views,
            target_provenance=target_provenance,
            reverse_lookup=reverse_lookup,
            generic_gloss_demotions=generic_gloss_demotions,
        )
        candidates.append(
            RuleCandidate(
                source_phrase=str(entry.translation),
                replacement=str(target),
                language_pair=language_pair,
                source_dict=source_dict,
                source_type=source_type,
                metadata=metadata,
            )
        )
    return tuple(candidates)


def _build_static_candidate_metadata(
    *,
    entry: TranslationGlossRecord,
    index: int,
    total: int,
    target: str,
    target_reverse_norm: str,
    target_word_package: Optional[Mapping[str, object]],
    target_pos: Mapping[str, object],
    dictionary_pos: Mapping[str, object],
    dictionary_canonical: str,
    canonical_inventory: Sequence[str],
    dictionary_record_views: Mapping[str, object],
    target_provenance: Optional[Mapping[str, object]],
    reverse_lookup: Optional[Mapping[str, tuple[str, ...]]],
    generic_gloss_demotions: Mapping[str, float],
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "gloss_index": index,
        "gloss_total": total,
        "definition_bucket_key": _build_definition_bucket_key(
            entry,
            fallback_index=index,
        ),
        "compiled_candidate_index": index,
    }
    if entry.metadata:
        raw_record = dict(entry.metadata)
        metadata["dictionary_record"] = raw_record
    if dictionary_record_views:
        metadata["dictionary_record_views"] = dict(dictionary_record_views)
    kaikkei_family_names = _extract_kaikki_family_names(dictionary_record_views)
    if kaikkei_family_names:
        metadata["kaikki_family_names"] = kaikkei_family_names
    gloss_provenance = _build_gloss_provenance(entry)
    if gloss_provenance:
        metadata["gloss_provenance"] = gloss_provenance
    sense_provenance = _build_sense_provenance(entry, dictionary_pos=dictionary_pos)
    if sense_provenance:
        metadata["sense_provenance"] = sense_provenance
    if target_provenance:
        metadata["target_provenance"] = target_provenance
    source_reverse_norm = _normalize_reverse_token_with_pos(
        entry.translation,
        pos_raw=entry.pos_raw,
    )
    reverse_targets = (
        reverse_lookup.get(source_reverse_norm, ()) if reverse_lookup is not None else ()
    )
    reverse_rank = (
        reverse_targets.index(target_reverse_norm)
        if target_reverse_norm and target_reverse_norm in reverse_targets
        else None
    )
    metadata.update(
        {
            "reverse_check_supported": reverse_lookup is not None,
            "reverse_check_hit": reverse_rank is not None,
            "reverse_check_rank": reverse_rank,
            "reverse_check_total": len(reverse_targets),
            "reverse_check_source_dict": None,
            "reverse_check_target_norm": target_reverse_norm,
            "reverse_check_source_norm": source_reverse_norm,
        }
    )
    demotion = resolve_generic_gloss_demotion(
        entry.translation,
        demotions=generic_gloss_demotions,
    )
    if demotion > 0.0:
        metadata["semantic_demotion"] = demotion
        metadata["semantic_demotion_reason"] = "generic_gloss"
    if _should_shadow_interjection(
        current_canonical=dictionary_canonical,
        entry_metadata=entry.metadata,
        earlier_canonicals=canonical_inventory[:index],
    ):
        metadata["interjection_shadowed"] = True
    if _should_demote_shadowed_adverb(
        current_canonical=dictionary_canonical,
        canonical_inventory=canonical_inventory,
    ):
        _apply_semantic_demotion(
            metadata,
            demotion=0.65,
            reason="function_word_adverb_shadowed",
        )
    register_demotion = _resolve_kaikki_register_demotion(entry.metadata)
    if register_demotion > 0.0:
        _apply_semantic_demotion(
            metadata,
            demotion=register_demotion,
            reason="kaikki_register_or_region",
        )
    if target_word_package is not None:
        metadata["word_package"] = target_word_package
    metadata.update(
        build_candidate_pos_metadata(
            source_pos=dictionary_pos,
            target_pos=target_pos,
            dictionary_pos=dictionary_pos,
        )
    )
    return metadata


def _extract_kaikki_family_names(dictionary_record_views: Mapping[str, object]) -> tuple[str, ...]:
    if not isinstance(dictionary_record_views, Mapping):
        return ()
    kaikki_views = dictionary_record_views.get("kaikki")
    if not isinstance(kaikki_views, Mapping):
        return ()
    combined = kaikki_views.get("combined_families")
    if isinstance(combined, Sequence) and not isinstance(combined, (str, bytes)):
        return tuple(dict.fromkeys(str(value).strip() for value in combined if str(value).strip()))
    family_fields = kaikki_views.get("family_fields")
    if isinstance(family_fields, Mapping):
        return tuple(sorted(str(key).strip() for key in family_fields if str(key).strip()))
    return ()


def _build_definition_bucket_ids(
    *,
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext],
    ordered_targets: Sequence[str],
) -> dict[str, int]:
    keys = {
        str(candidate.metadata.get("definition_bucket_key") or "").strip()
        for target in ordered_targets
        for candidate in compiled_targets_by_target[target].base_candidates
        if str(candidate.metadata.get("definition_bucket_key") or "").strip()
    }
    return {key: index for index, key in enumerate(sorted(keys))}


def _build_family_marker_ids(
    *,
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext],
    ordered_targets: Sequence[str],
) -> dict[str, int]:
    names = {
        family_name
        for target in ordered_targets
        for candidate in compiled_targets_by_target[target].base_candidates
        for family_name in _normalize_family_names(candidate.metadata.get("kaikki_family_names"))
    }
    return {name: index for index, name in enumerate(sorted(names))}


def _normalize_family_names(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def _normalize_optional_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        return text in {"1", "true", "yes", "on"}
    return False


def _normalize_non_negative_optional_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = int(text)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def _normalize_optional_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0
    return 0.0


def _build_compiled_candidate_fact(
    *,
    candidate: RuleCandidate,
    candidate_id: int,
    target_id: int,
    definition_bucket_ids_by_key: Mapping[str, int],
    family_marker_ids_by_name: Mapping[str, int],
    source_dict_ids_by_name: Mapping[str, int],
    source_type_ids_by_name: Mapping[str, int],
) -> EnEsCompiledCandidateFact:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    bucket_key = str(metadata.get("definition_bucket_key") or "").strip()
    family_names = _normalize_family_names(metadata.get("kaikki_family_names"))
    phrase = str(candidate.source_phrase or "").strip()
    semantic_demotion_reason = str(metadata.get("semantic_demotion_reason") or "").strip() or None
    return EnEsCompiledCandidateFact(
        candidate_id=int(candidate_id),
        target_id=int(target_id),
        definition_bucket_id=int(definition_bucket_ids_by_key.get(bucket_key, -1)),
        source_dict_id=int(source_dict_ids_by_name.get(candidate.source_dict, -1)),
        source_type_id=int(source_type_ids_by_name.get(candidate.source_type, -1)),
        local_candidate_index=int(
            _normalize_non_negative_optional_int(metadata.get("compiled_candidate_index")) or 0
        ),
        gloss_index=int(_normalize_non_negative_optional_int(metadata.get("gloss_index")) or 0),
        gloss_total=int(_normalize_non_negative_optional_int(metadata.get("gloss_total")) or 0),
        source_phrase=phrase,
        reverse_check_source_norm=str(metadata.get("reverse_check_source_norm") or "").strip(),
        reverse_check_target_norm=str(metadata.get("reverse_check_target_norm") or "").strip(),
        reverse_check_supported=_normalize_optional_bool(metadata.get("reverse_check_supported")),
        reverse_check_hit=_normalize_optional_bool(metadata.get("reverse_check_hit")),
        reverse_check_rank=_normalize_non_negative_optional_int(metadata.get("reverse_check_rank")),
        reverse_check_total=int(
            _normalize_non_negative_optional_int(metadata.get("reverse_check_total")) or 0
        ),
        source_phrase_token_count=len(phrase.split()) if phrase else 0,
        source_phrase_is_ascii=bool(phrase) and all(ord(ch) < 128 for ch in phrase),
        source_phrase_is_phrase=" " in phrase,
        is_variant=_normalize_optional_bool(metadata.get("variant")),
        source_pos_canonical=extract_candidate_pos_canonical(
            metadata,
            nested_key="source",
            flat_key="source_pos_canonical",
        ),
        target_pos_canonical=extract_candidate_pos_canonical(
            metadata,
            nested_key="target",
            flat_key="target_pos_canonical",
        ),
        dictionary_pos_canonical=extract_candidate_pos_canonical(
            metadata,
            nested_key="dictionary",
            flat_key="dictionary_pos_canonical",
        ),
        semantic_demotion_base=max(
            0.0, _normalize_optional_float(metadata.get("semantic_demotion"))
        ),
        semantic_demotion_reason=semantic_demotion_reason,
        interjection_shadowed=_normalize_optional_bool(metadata.get("interjection_shadowed")),
        has_word_package=isinstance(metadata.get("word_package"), Mapping),
        has_gloss_provenance=isinstance(metadata.get("gloss_provenance"), Mapping),
        has_sense_provenance=isinstance(metadata.get("sense_provenance"), Mapping),
        has_target_provenance=isinstance(metadata.get("target_provenance"), Mapping),
        current_sense_position=int(
            _normalize_non_negative_optional_int(
                (
                    metadata.get("target_provenance").get("current_sense_position")
                    if isinstance(metadata.get("target_provenance"), Mapping)
                    else None
                )
            )
            or 0
        ),
        kaikkei_family_names=family_names,
        family_marker_ids=tuple(
            family_marker_ids_by_name[name]
            for name in family_names
            if name in family_marker_ids_by_name
        ),
    )


def _build_compiled_candidate_table(
    candidate_facts: Sequence[EnEsCompiledCandidateFact],
) -> EnEsCompiledCandidateTable:
    candidate_ids: list[int] = []
    target_ids: list[int] = []
    definition_bucket_ids: list[int] = []
    source_phrases: list[str] = []
    source_phrase_lowers: list[str] = []
    normalized_source_phrases: list[str] = []
    normalized_source_phrase_order_ids: list[int] = []
    source_dict_ids: list[int] = []
    source_type_ids: list[int] = []
    local_candidate_indices: list[int] = []
    gloss_indices: list[int] = []
    gloss_totals: list[int] = []
    semantic_demotion_bases: list[float] = []
    source_pos_canonicals: list[str] = []
    target_pos_canonicals: list[str] = []
    dictionary_pos_canonicals: list[str] = []
    phrase_flags: list[bool] = []
    variant_flags: list[bool] = []
    interjection_shadowed_flags: list[bool] = []
    reverse_check_supported_flags: list[bool] = []
    reverse_check_hit_flags: list[bool] = []
    reverse_check_rank_values: list[int] = []
    reverse_check_total_values: list[int] = []
    current_sense_positions: list[int] = []
    family_marker_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_by_candidate_id: dict[int, int] = {}
    candidate_row_ids_by_target_id: dict[int, list[int]] = {}
    candidate_row_ids_by_definition_bucket_id: dict[int, list[int]] = {}
    candidate_row_ids_by_family_marker_id: dict[int, list[int]] = {}

    for row_id, fact in enumerate(candidate_facts):
        candidate_ids.append(int(fact.candidate_id))
        target_ids.append(int(fact.target_id))
        definition_bucket_ids.append(int(fact.definition_bucket_id))
        source_phrases.append(str(fact.source_phrase))
        source_phrase_lowers.append(str(fact.source_phrase).lower())
        normalized_source_phrases.append(_normalize_compiled_source_phrase(fact.source_phrase))
        source_dict_ids.append(int(fact.source_dict_id))
        source_type_ids.append(int(fact.source_type_id))
        local_candidate_indices.append(int(fact.local_candidate_index))
        gloss_indices.append(int(fact.gloss_index))
        gloss_totals.append(int(fact.gloss_total))
        semantic_demotion_bases.append(float(fact.semantic_demotion_base))
        source_pos_canonicals.append(str(fact.source_pos_canonical))
        target_pos_canonicals.append(str(fact.target_pos_canonical))
        dictionary_pos_canonicals.append(str(fact.dictionary_pos_canonical))
        phrase_flags.append(bool(fact.source_phrase_is_phrase))
        variant_flags.append(bool(fact.is_variant))
        interjection_shadowed_flags.append(bool(fact.interjection_shadowed))
        reverse_check_supported_flags.append(bool(fact.reverse_check_supported))
        reverse_check_hit_flags.append(bool(fact.reverse_check_hit))
        reverse_check_rank_values.append(
            int(fact.reverse_check_rank) if fact.reverse_check_rank is not None else -1
        )
        reverse_check_total_values.append(int(fact.reverse_check_total))
        current_sense_positions.append(int(fact.current_sense_position))
        family_marker_id_rows.append(tuple(int(value) for value in fact.family_marker_ids))

        candidate_row_id_by_candidate_id[int(fact.candidate_id)] = row_id
        if fact.target_id >= 0:
            candidate_row_ids_by_target_id.setdefault(int(fact.target_id), []).append(row_id)
        if fact.definition_bucket_id >= 0:
            candidate_row_ids_by_definition_bucket_id.setdefault(
                int(fact.definition_bucket_id), []
            ).append(row_id)
        for family_marker_id in fact.family_marker_ids:
            if family_marker_id >= 0:
                candidate_row_ids_by_family_marker_id.setdefault(int(family_marker_id), []).append(
                    row_id
                )

    normalized_source_phrase_order_id_by_phrase = {
        phrase: order_id for order_id, phrase in enumerate(sorted(set(normalized_source_phrases)))
    }
    normalized_source_phrase_order_ids = [
        int(normalized_source_phrase_order_id_by_phrase[phrase])
        for phrase in normalized_source_phrases
    ]

    return EnEsCompiledCandidateTable(
        candidate_ids=tuple(candidate_ids),
        target_ids=tuple(target_ids),
        definition_bucket_ids=tuple(definition_bucket_ids),
        source_phrases=tuple(source_phrases),
        source_phrase_lowers=tuple(source_phrase_lowers),
        normalized_source_phrases=tuple(normalized_source_phrases),
        normalized_source_phrase_order_ids=tuple(normalized_source_phrase_order_ids),
        source_dict_ids=tuple(source_dict_ids),
        source_type_ids=tuple(source_type_ids),
        local_candidate_indices=tuple(local_candidate_indices),
        gloss_indices=tuple(gloss_indices),
        gloss_totals=tuple(gloss_totals),
        semantic_demotion_bases=tuple(semantic_demotion_bases),
        source_pos_canonicals=tuple(source_pos_canonicals),
        target_pos_canonicals=tuple(target_pos_canonicals),
        dictionary_pos_canonicals=tuple(dictionary_pos_canonicals),
        phrase_flags=tuple(phrase_flags),
        variant_flags=tuple(variant_flags),
        interjection_shadowed_flags=tuple(interjection_shadowed_flags),
        reverse_check_supported_flags=tuple(reverse_check_supported_flags),
        reverse_check_hit_flags=tuple(reverse_check_hit_flags),
        reverse_check_rank_values=tuple(reverse_check_rank_values),
        reverse_check_total_values=tuple(reverse_check_total_values),
        current_sense_positions=tuple(current_sense_positions),
        family_marker_id_rows=tuple(family_marker_id_rows),
        candidate_row_id_by_candidate_id=dict(candidate_row_id_by_candidate_id),
        candidate_row_ids_by_target_id={
            key: tuple(value) for key, value in sorted(candidate_row_ids_by_target_id.items())
        },
        candidate_row_ids_by_definition_bucket_id={
            key: tuple(value)
            for key, value in sorted(candidate_row_ids_by_definition_bucket_id.items())
        },
        candidate_row_ids_by_family_marker_id={
            key: tuple(value)
            for key, value in sorted(candidate_row_ids_by_family_marker_id.items())
        },
    )


def _finalize_compiled_target_contexts(
    *,
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext],
    ordered_targets: Sequence[str],
    target_ids_by_target: Mapping[str, int],
    definition_bucket_ids_by_key: Mapping[str, int],
    family_marker_ids_by_name: Mapping[str, int],
    source_dict_ids_by_name: Mapping[str, int],
    source_type_ids_by_name: Mapping[str, int],
) -> tuple[dict[str, EnEsCompiledTargetContext], tuple[EnEsCompiledCandidateFact, ...]]:
    finalized_targets_by_target: dict[str, EnEsCompiledTargetContext] = {}
    candidate_facts: list[EnEsCompiledCandidateFact] = []
    next_candidate_id = 0
    for target in ordered_targets:
        target_context = compiled_targets_by_target[target]
        target_id = int(target_ids_by_target.get(target, -1))
        finalized_candidates: list[RuleCandidate] = []
        finalized_facts: list[EnEsCompiledCandidateFact] = []
        for candidate in target_context.base_candidates:
            metadata = dict(candidate.metadata)
            bucket_key = str(metadata.get("definition_bucket_key") or "").strip()
            family_names = _normalize_family_names(metadata.get("kaikki_family_names"))
            metadata["compiled_target_id"] = target_id
            metadata["compiled_candidate_id"] = next_candidate_id
            metadata["compiled_definition_bucket_id"] = definition_bucket_ids_by_key.get(
                bucket_key, -1
            )
            metadata["compiled_family_marker_ids"] = tuple(
                family_marker_ids_by_name[name]
                for name in family_names
                if name in family_marker_ids_by_name
            )
            metadata["compiled_source_dict_id"] = source_dict_ids_by_name.get(
                candidate.source_dict, -1
            )
            metadata["compiled_source_type_id"] = source_type_ids_by_name.get(
                candidate.source_type, -1
            )
            finalized_candidate = replace(candidate, metadata=metadata)
            fact = _build_compiled_candidate_fact(
                candidate=finalized_candidate,
                candidate_id=next_candidate_id,
                target_id=target_id,
                definition_bucket_ids_by_key=definition_bucket_ids_by_key,
                family_marker_ids_by_name=family_marker_ids_by_name,
                source_dict_ids_by_name=source_dict_ids_by_name,
                source_type_ids_by_name=source_type_ids_by_name,
            )
            finalized_candidates.append(finalized_candidate)
            finalized_facts.append(fact)
            candidate_facts.append(fact)
            next_candidate_id += 1
        finalized_targets_by_target[target] = replace(
            target_context,
            target_id=target_id,
            base_candidates=tuple(finalized_candidates),
            candidate_facts=tuple(finalized_facts),
        )
    return finalized_targets_by_target, tuple(candidate_facts)
