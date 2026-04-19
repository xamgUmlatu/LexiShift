from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import (
    FreedictGlossRecord,
    TranslationGlossRecord,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.generation import CandidateFilter, RuleCandidate
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views
from lexishift_core.rulegen.pairs.en_de_gloss_processing import (
    _apply_kaikki_policy_overlay,
    _canonical_for_competition,
    _expand_en_de_gloss_variants,
    _extract_kaikki_family_names,
    _normalize_competition_penalty,
    _resolve_cleaner_later_competition,
    _resolve_en_de_kaikki_register_demotion,
    _resolve_en_de_marked_sense_demotion,
    _resolve_sense_representative_indexes,
)
from lexishift_core.rulegen.pairs.en_es_support import (
    apply_semantic_demotion as _apply_semantic_demotion,
    build_definition_bucket_key as _build_definition_bucket_key,
    build_gloss_provenance as _build_gloss_provenance,
    build_kaikki_policy_shadow_by_index as _build_kaikki_policy_shadow_by_index,
    build_sense_provenance as _build_sense_provenance,
    build_target_provenance_by_index as _build_target_provenance_by_index,
    normalize_reverse_token as _normalize_reverse_token,
    normalize_reverse_token_with_pos as _normalize_reverse_token_with_pos,
)
from lexishift_core.rulegen.pairs.en_ja import DEFAULT_STOPWORDS
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.semantic_demotion import resolve_generic_gloss_demotion
from lexishift_core.rulegen.utils import (
    InflectionArtifactFilter,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
    sanitize_dictionary_gloss,
)

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_de import EnDeKaikkiPolicyConfig, EnDeRulegenConfig


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


class FreedictCandidateSource:
    def __init__(
        self,
        *,
        records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
        source_dict: str,
        source_type: str,
        dictionary_pos_source_profile: str = "freedict",
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
        reverse_lookup: Optional[Mapping[str, tuple[str, ...]]] = None,
        reverse_source_dict_id: Optional[str] = None,
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
        source_frequency_provider: Optional[Callable[[str], float]] = None,
        cleaner_later_competition_penalty: float = 0.0,
        sense_representative_selection: bool = False,
        kaikki_policy: Optional[EnDeKaikkiPolicyConfig] = None,
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._dictionary_pos_source_profile = (
            str(dictionary_pos_source_profile or "").strip() or "freedict"
        )
        self._word_packages_by_target = word_packages_by_target or {}
        self._reverse_lookup = reverse_lookup
        self._reverse_source_dict_id = (
            str(reverse_source_dict_id).strip() if reverse_source_dict_id is not None else None
        )
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._source_frequency_provider = source_frequency_provider
        self._cleaner_later_competition_penalty = _normalize_competition_penalty(
            cleaner_later_competition_penalty
        )
        self._sense_representative_selection = bool(sense_representative_selection)
        self._kaikki_policy = kaikki_policy

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            target_reverse_norm = _normalize_reverse_token(target)
            target_word_package = resolve_target_word_package(
                target=target,
                language_pair=language_pair,
                fallback_provider="frequency",
                package_hint=self._word_packages_by_target.get(target),
            )
            target_pos = extract_target_pos_component(
                target_word_package=target_word_package,
                language_pair=language_pair,
            )
            entries = _collect_sanitized_gloss_records(self._records_by_target.get(target, ()))
            total = len(entries)
            dictionary_pos_rows = [
                normalize_pos_component(
                    entry.pos_raw,
                    language_pair=language_pair,
                    source_provider=self._source_dict,
                    source_kind="dictionary",
                    source_profile=self._dictionary_pos_source_profile,
                )
                for entry in entries
            ]
            canonical_inventory = [
                _canonical_for_competition(dictionary_pos) for dictionary_pos in dictionary_pos_rows
            ]
            dictionary_record_views_by_index = []
            for entry in entries:
                raw_record = entry.metadata if isinstance(entry.metadata, Mapping) else {}
                dictionary_record_views = build_kaikki_record_views(raw_record)
                dictionary_record_views_by_index.append(
                    {"kaikki": dictionary_record_views} if dictionary_record_views else {}
                )
            target_provenance_by_index = tuple(
                _build_target_provenance_by_index(
                    target=target,
                    entries=entries,
                    canonical_inventory=canonical_inventory,
                )
            )
            shadow_by_index = (
                _build_kaikki_policy_shadow_by_index(
                    dictionary_record_views_by_index=dictionary_record_views_by_index,
                    canonical_inventory=canonical_inventory,
                    risk_families=self._kaikki_policy.risk_families,
                )
                if self._kaikki_policy is not None and self._kaikki_policy.enable_shadow_metadata
                else [{} for _ in entries]
            )
            source_frequency_priors = [
                (
                    max(0.0, float(self._source_frequency_provider(entry.translation)))
                    if self._source_frequency_provider is not None
                    else 0.0
                )
                for entry in entries
            ]
            representative_by_index = (
                _resolve_sense_representative_indexes(
                    entries=entries,
                    source_frequency_priors=source_frequency_priors,
                )
                if self._sense_representative_selection
                and self._source_frequency_provider is not None
                else {}
            )
            for index, entry in enumerate(entries):
                dictionary_pos = dictionary_pos_rows[index]
                dictionary_record_views = (
                    dictionary_record_views_by_index[index]
                    if index < len(dictionary_record_views_by_index)
                    else {}
                )
                target_provenance = (
                    target_provenance_by_index[index]
                    if index < len(target_provenance_by_index)
                    else None
                )
                metadata: dict[str, object] = {
                    "gloss_index": index,
                    "gloss_total": total,
                    "definition_bucket_key": _build_definition_bucket_key(
                        entry,
                        fallback_index=index,
                    ),
                }
                if entry.metadata:
                    metadata["dictionary_record"] = dict(entry.metadata)
                if dictionary_record_views:
                    metadata["dictionary_record_views"] = dict(dictionary_record_views)
                kaikki_family_names = _extract_kaikki_family_names(dictionary_record_views)
                if kaikki_family_names:
                    metadata["kaikki_family_names"] = kaikki_family_names
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
                    self._reverse_lookup.get(source_reverse_norm, ())
                    if self._reverse_lookup is not None
                    else ()
                )
                reverse_rank = (
                    reverse_targets.index(target_reverse_norm)
                    if target_reverse_norm and target_reverse_norm in reverse_targets
                    else None
                )
                metadata.update(
                    {
                        "reverse_check_supported": self._reverse_lookup is not None,
                        "reverse_check_hit": reverse_rank is not None,
                        "reverse_check_rank": reverse_rank,
                        "reverse_check_total": len(reverse_targets),
                        "reverse_check_source_dict": self._reverse_source_dict_id,
                        "reverse_check_target_norm": target_reverse_norm,
                        "reverse_check_source_norm": source_reverse_norm,
                    }
                )
                demotion = resolve_generic_gloss_demotion(
                    entry.translation,
                    demotions=self._generic_gloss_demotions,
                )
                if demotion > 0.0:
                    _apply_semantic_demotion(
                        metadata,
                        demotion=demotion,
                        reason="generic_gloss",
                    )
                marked_demotion, marked_reasons = _resolve_en_de_marked_sense_demotion(
                    entry.metadata if isinstance(entry.metadata, Mapping) else {}
                )
                if marked_demotion > 0.0:
                    _apply_semantic_demotion(
                        metadata,
                        demotion=marked_demotion,
                        reason=";".join(marked_reasons) if marked_reasons else "marked_sense",
                    )
                if self._kaikki_policy is not None and self._kaikki_policy.enable_register_demotion:
                    register_demotion, register_reasons = _resolve_en_de_kaikki_register_demotion(
                        entry.metadata if isinstance(entry.metadata, Mapping) else {}
                    )
                    if register_demotion > 0.0:
                        _apply_semantic_demotion(
                            metadata,
                            demotion=register_demotion,
                            reason=(
                                ";".join(register_reasons)
                                if register_reasons
                                else "kaikki_register_or_region"
                            ),
                        )
                if self._source_frequency_provider is not None:
                    metadata["source_frequency_prior"] = source_frequency_priors[index]
                representative_index = representative_by_index.get(index)
                if representative_index is not None:
                    representative_entry = entries[representative_index]
                    representative_prior = (
                        float(source_frequency_priors[representative_index])
                        if representative_index < len(source_frequency_priors)
                        else 0.0
                    )
                    metadata["sense_representative_selection_present"] = True
                    metadata["sense_representative_index"] = representative_index
                    metadata["sense_representative_phrase"] = str(representative_entry.translation)
                    metadata["sense_representative_prior"] = representative_prior
                    _apply_semantic_demotion(
                        metadata,
                        demotion=0.60,
                        reason="sense_representative_selection",
                    )
                if (
                    self._cleaner_later_competition_penalty > 0.0
                    and self._source_frequency_provider is not None
                ):
                    cleaner_later_index = _resolve_cleaner_later_competition(
                        current_index=index,
                        source_frequency_priors=source_frequency_priors,
                        canonical_inventory=canonical_inventory,
                    )
                    if cleaner_later_index is not None:
                        metadata["cleaner_later_competition_present"] = True
                        metadata["cleaner_later_competitor_index"] = cleaner_later_index
                        metadata["cleaner_later_competitor_phrase"] = str(
                            entries[cleaner_later_index].translation
                        )
                        metadata["cleaner_later_competitor_prior"] = float(
                            source_frequency_priors[cleaner_later_index]
                        )
                        metadata["cleaner_later_competition_penalty"] = (
                            self._cleaner_later_competition_penalty
                        )
                        _apply_semantic_demotion(
                            metadata,
                            demotion=self._cleaner_later_competition_penalty,
                            reason="cleaner_later_competition",
                        )
                shadow = shadow_by_index[index] if index < len(shadow_by_index) else {}
                if shadow and self._kaikki_policy is not None:
                    _apply_kaikki_policy_overlay(
                        metadata=metadata,
                        shadow=shadow,
                        kaikki_policy=self._kaikki_policy,
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
                yield RuleCandidate(
                    source_phrase=str(entry.translation),
                    replacement=str(target),
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata=metadata,
                )


def _build_filters(
    config: EnDeRulegenConfig,
    mapping: Mapping[str, Sequence[str]],
) -> list[CandidateFilter]:
    filters: list[CandidateFilter] = [NonEmptyFilter()]
    if not config.allow_multiword_glosses:
        filters.append(SingleWordFilter(allow_hyphen=config.allow_hyphen))
    if config.enable_length_filter:
        filters.append(
            LengthFilter(min_length=config.min_source_length, max_length=config.max_source_length)
        )
    if config.enable_punctuation_filter:
        filters.append(PunctuationFilter())
    if config.enable_possessive_filter:
        filters.append(PossessiveFilter())
    if config.enable_stopword_filter:
        stopwords = config.stopwords or DEFAULT_STOPWORDS
        filters.append(StopwordFilter(stopwords=stopwords))
    if config.enable_inflection_filter:
        base_forms = _build_gloss_base_forms(mapping)
        filters.append(
            InflectionArtifactFilter(
                suffixes=config.inflection_suffixes,
                base_forms=base_forms,
            )
        )
    return filters


def _build_gloss_base_forms(mapping: Mapping[str, Sequence[str]]) -> set[str]:
    base_forms: set[str] = set()
    for glosses in mapping.values():
        for gloss in glosses:
            sanitized = sanitize_dictionary_gloss(gloss).lower()
            if sanitized:
                base_forms.add(sanitized)
    return base_forms


def _resolve_gloss_records(config: EnDeRulegenConfig) -> dict[str, list[FreedictGlossRecord]]:
    if config.gloss_records_by_target is not None:
        return _coerce_gloss_records(config.gloss_records_by_target)
    if config.gloss_mapping is not None:
        return _coerce_gloss_records(config.gloss_mapping)
    return load_translation_gloss_records_ordered(
        config.translation_dict_path,
        target_lang="en",
    )


def _coerce_gloss_records(
    mapping: Mapping[str, Sequence[object]],
) -> dict[str, list[FreedictGlossRecord]]:
    records_by_target: dict[str, list[FreedictGlossRecord]] = {}
    for target, entries in mapping.items():
        bucket: list[FreedictGlossRecord] = []
        for entry in entries:
            if isinstance(entry, FreedictGlossRecord):
                bucket.append(entry)
                continue
            bucket.append(FreedictGlossRecord(translation=str(entry), pos_raw=""))
        records_by_target[str(target)] = bucket
    return records_by_target


def _resolve_reverse_gloss_records(
    config: EnDeRulegenConfig,
) -> Optional[dict[str, list[TranslationGlossRecord]]]:
    if config.reverse_gloss_records_by_source is not None:
        return _coerce_gloss_records(config.reverse_gloss_records_by_source)
    if config.reverse_translation_dict_path is None:
        return None
    if not config.reverse_translation_dict_path.exists():
        return None
    return load_translation_gloss_records_ordered(
        config.reverse_translation_dict_path,
        target_lang="de",
    )


def _records_to_gloss_mapping(
    records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
) -> dict[str, list[str]]:
    return {
        target: [entry.translation for entry in entries]
        for target, entries in records_by_target.items()
    }


def _collect_sanitized_gloss_records(
    records: Iterable[FreedictGlossRecord],
) -> list[FreedictGlossRecord]:
    cleaned: list[FreedictGlossRecord] = []
    seen: dict[str, int] = {}
    for record in records:
        normalized_pos = str(record.pos_raw or "").strip()
        variants = _expand_en_de_gloss_variants(record.translation, pos_raw=normalized_pos)
        for sanitized, variant_metadata in variants:
            existing_index = seen.get(sanitized)
            metadata = dict(record.metadata or {})
            if variant_metadata:
                metadata.update(variant_metadata)
            if existing_index is None:
                cleaned.append(
                    FreedictGlossRecord(
                        translation=sanitized,
                        pos_raw=normalized_pos,
                        metadata=metadata,
                    )
                )
                seen[sanitized] = len(cleaned) - 1
                continue
            if not cleaned[existing_index].pos_raw and normalized_pos:
                cleaned[existing_index] = FreedictGlossRecord(
                    translation=sanitized,
                    pos_raw=normalized_pos,
                    metadata=cleaned[existing_index].metadata,
                )
    return cleaned
