from __future__ import annotations

from dataclasses import replace
import re
from typing import TYPE_CHECKING, Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.pos.normalization import (
    CANONICAL_POS_ADPOSITION,
    CANONICAL_POS_CONJUNCTION,
    CANONICAL_POS_DETERMINER,
    CANONICAL_POS_NOUN,
    CANONICAL_POS_PRONOUN,
)
from lexishift_core.resources.dict_loaders import (
    TranslationGlossRecord,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.generation import CandidateFilter, RuleCandidate
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views
from lexishift_core.rulegen.pairs.en_es_compiled_filtering import EnEsCompiledCandidateFilterTable
from lexishift_core.rulegen.pairs.en_es_compiled_inventory import (
    EnEsCompiledResources,
    _build_static_candidate_inventory,
    _normalize_non_negative_optional_int,
)
from lexishift_core.rulegen.pairs.en_es_support import (
    build_reverse_lookup as _build_reverse_lookup,
    build_target_provenance_by_index as _build_target_provenance_by_index,
    collect_sanitized_gloss_records as _collect_sanitized_gloss_records,
    extract_canonical_from_component as _extract_canonical_from_component,
    normalize_reverse_token as _normalize_reverse_token,
)
from lexishift_core.rulegen.pairs.en_ja import DEFAULT_STOPWORDS
from lexishift_core.rulegen.pairs.pos_utils import (
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.utils import (
    InflectionArtifactFilter,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    sanitize_dictionary_gloss,
)

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_es import EnEsKaikkiPolicyConfig, EnEsRulegenConfig


_SPANISH_NOUN_WORD_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$")
_EN_ES_SINGLE_WORD_RE = re.compile(r"^[a-z0-9-]+$")
_EN_ES_MULTIWORD_RE = re.compile(r"^[a-z0-9-]+(?: [a-z0-9-]+){0,3}$")
_FUNCTION_WORD_CANONICALS = frozenset(
    {
        CANONICAL_POS_DETERMINER,
        CANONICAL_POS_PRONOUN,
        CANONICAL_POS_ADPOSITION,
        CANONICAL_POS_CONJUNCTION,
    }
)


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


def _resolve_spanish_target_surface(candidate: RuleCandidate, form: str) -> Optional[str]:
    if form != "plural":
        return None
    if _extract_target_pos_canonical(candidate) != CANONICAL_POS_NOUN:
        return None
    return _pluralize_spanish_noun(candidate.replacement)


def _pluralize_spanish_noun(word: str) -> Optional[str]:
    text = str(word or "").strip()
    if not text or not _SPANISH_NOUN_WORD_RE.fullmatch(text):
        return None
    lower = text.lower()
    if lower.endswith(("s", "x")):
        return None
    accent_map = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
    }
    if lower.endswith(tuple(accent_map)):
        return text[:-1] + accent_map[text[-1].lower()] + "es"
    if lower.endswith(("a", "e", "i", "o", "u")):
        return f"{text}s"
    return f"{text}es"


def _extract_target_pos_canonical(candidate: RuleCandidate) -> str:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    pos = metadata.get("pos")
    if isinstance(pos, Mapping):
        target = pos.get("target")
        if isinstance(target, Mapping):
            canonical = str(target.get("canonical") or "").strip().lower()
            if canonical:
                return canonical
    return str(metadata.get("target_pos_canonical") or "").strip().lower()


def _extract_dictionary_pos_canonical(candidate: RuleCandidate) -> str:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    pos = metadata.get("pos")
    if isinstance(pos, Mapping):
        dictionary = pos.get("dictionary") or pos.get("source")
        if isinstance(dictionary, Mapping):
            canonical = str(dictionary.get("canonical") or "").strip().lower()
            if canonical:
                return canonical
    return str(metadata.get("dictionary_pos_canonical") or "").strip().lower()


def _candidate_allows_function_word_phrase(candidate: RuleCandidate) -> bool:
    return _extract_dictionary_pos_canonical(candidate) in _FUNCTION_WORD_CANONICALS


class EnEsGlossShapeFilter:
    def __init__(self, *, allow_hyphen: bool = True, allow_multiword_glosses: bool = False):
        self.allow_hyphen = allow_hyphen
        self.allow_multiword_glosses = allow_multiword_glosses

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = candidate.source_phrase.lower()
        if not self.allow_hyphen and "-" in phrase:
            return False
        if self.allow_multiword_glosses or _candidate_allows_function_word_phrase(candidate):
            return bool(_EN_ES_MULTIWORD_RE.fullmatch(phrase))
        return bool(_EN_ES_SINGLE_WORD_RE.fullmatch(phrase))


class EnEsStopwordFilter:
    def __init__(self, *, stopwords: Iterable[str]):
        self.stopwords = {word.lower() for word in stopwords}

    def accept(self, candidate: RuleCandidate) -> bool:
        if candidate.source_phrase.lower() not in self.stopwords:
            return True
        return _candidate_allows_function_word_phrase(candidate)


class ShadowedInterjectionFilter:
    def accept(self, candidate: RuleCandidate) -> bool:
        metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
        if metadata.get("interjection_shadowed"):
            return False
        return True


class FreedictCandidateSource:
    def __init__(
        self,
        *,
        records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
        source_dict: str,
        source_type: str,
        reverse_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
        reverse_source_dict: str = "",
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
        dictionary_pos_source_profile: str = "freedict",
        kaikki_policy: EnEsKaikkiPolicyConfig,
        compiled_resources: Optional[EnEsCompiledResources] = None,
        compiled_filter_table: Optional[EnEsCompiledCandidateFilterTable] = None,
        apply_kaikki_policy_overlay: Callable[..., None],
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._reverse_source_dict = str(reverse_source_dict or "").strip()
        self._compiled_targets_by_target = (
            dict(compiled_resources.compiled_targets_by_target)
            if compiled_resources is not None
            else {}
        )
        self._reverse_lookup = (
            compiled_resources.reverse_lookup
            if compiled_resources is not None and compiled_resources.reverse_lookup is not None
            else (
                _build_reverse_lookup(reverse_records_by_source)
                if reverse_records_by_source is not None
                else None
            )
        )
        self._compiled_candidate_table = (
            compiled_resources.candidate_table if compiled_resources is not None else None
        )
        self._compiled_filter_table = compiled_filter_table
        self._compiled_base_candidates_by_id = (
            {
                int(candidate_id): candidate
                for context in self._compiled_targets_by_target.values()
                for candidate in context.base_candidates
                for candidate_id in (
                    _normalize_non_negative_optional_int(
                        (
                            candidate.metadata.get("compiled_candidate_id")
                            if isinstance(candidate.metadata, Mapping)
                            else None
                        )
                    ),
                )
                if candidate_id is not None
            }
            if compiled_filter_table is not None
            else {}
        )
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._dictionary_pos_source_profile = str(dictionary_pos_source_profile or "").strip() or (
            "freedict"
        )
        self._kaikki_policy = kaikki_policy
        self._apply_kaikki_policy_overlay = apply_kaikki_policy_overlay

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        from lexishift_core.rulegen.pairs.en_es_support import build_kaikki_policy_shadow_by_index

        for target in targets:
            compiled_target = self._compiled_targets_by_target.get(target)
            if compiled_target is not None:
                canonical_inventory = compiled_target.canonical_inventory
                dictionary_record_views_by_index = compiled_target.dictionary_record_views_by_index
                base_candidates = compiled_target.base_candidates
                kaikkei_policy_shadow_by_index = (
                    build_kaikki_policy_shadow_by_index(
                        dictionary_record_views_by_index=dictionary_record_views_by_index,
                        canonical_inventory=canonical_inventory,
                        risk_families=self._kaikki_policy.risk_families,
                    )
                    if self._kaikki_policy.enable_shadow_metadata
                    else [{} for _ in base_candidates]
                )
                if (
                    self._compiled_filter_table is not None
                    and self._compiled_candidate_table is not None
                ):
                    accepted_row_ids = (
                        self._compiled_filter_table.accepted_candidate_row_ids_by_target_id.get(
                            compiled_target.target_id,
                            (),
                        )
                    )
                    for row_id in accepted_row_ids:
                        candidate_id = int(self._compiled_candidate_table.candidate_ids[row_id])
                        base_candidate = self._compiled_base_candidates_by_id.get(candidate_id)
                        if base_candidate is None:
                            continue
                        metadata = dict(base_candidate.metadata)
                        metadata["reverse_check_source_dict"] = self._reverse_source_dict or None
                        local_index = int(
                            _normalize_non_negative_optional_int(
                                metadata.get("compiled_candidate_index")
                            )
                            or 0
                        )
                        if local_index < len(kaikkei_policy_shadow_by_index):
                            self._apply_kaikki_policy_overlay(
                                metadata=metadata,
                                shadow=kaikkei_policy_shadow_by_index[local_index],
                                kaikki_policy=self._kaikki_policy,
                            )
                        yield replace(
                            base_candidate,
                            source_phrase=self._compiled_filter_table.normalized_source_phrases[
                                row_id
                            ],
                            language_pair=language_pair,
                            source_dict=self._source_dict,
                            source_type=self._source_type,
                            metadata=metadata,
                        )
                    continue
            else:
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
                entries = tuple(
                    _collect_sanitized_gloss_records(self._records_by_target.get(target, ()))
                )
                dictionary_poses = tuple(
                    normalize_pos_component(
                        entry.pos_raw,
                        language_pair=language_pair,
                        source_provider=self._source_dict,
                        source_kind="dictionary",
                        source_profile=self._dictionary_pos_source_profile,
                    )
                    for entry in entries
                )
                canonical_inventory = tuple(
                    _extract_canonical_from_component(component) for component in dictionary_poses
                )
                dictionary_record_views_by_index = []
                for entry in entries:
                    if entry.metadata:
                        raw_record = dict(entry.metadata)
                        dictionary_record_views = build_kaikki_record_views(raw_record)
                        if dictionary_record_views:
                            dictionary_record_views_by_index.append(
                                {"kaikki": dictionary_record_views}
                            )
                            continue
                    dictionary_record_views_by_index.append({})
                target_provenance_by_index = tuple(
                    _build_target_provenance_by_index(
                        target=target,
                        entries=entries,
                        canonical_inventory=canonical_inventory,
                    )
                )
                base_candidates = _build_static_candidate_inventory(
                    target=target,
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    target_reverse_norm=target_reverse_norm,
                    target_word_package=target_word_package,
                    target_pos=target_pos,
                    entries=entries,
                    dictionary_poses=dictionary_poses,
                    canonical_inventory=canonical_inventory,
                    dictionary_record_views_by_index=tuple(dictionary_record_views_by_index),
                    target_provenance_by_index=target_provenance_by_index,
                    reverse_lookup=self._reverse_lookup,
                    generic_gloss_demotions=self._generic_gloss_demotions,
                )
                kaikkei_policy_shadow_by_index = (
                    build_kaikki_policy_shadow_by_index(
                        dictionary_record_views_by_index=dictionary_record_views_by_index,
                        canonical_inventory=canonical_inventory,
                        risk_families=self._kaikki_policy.risk_families,
                    )
                    if self._kaikki_policy.enable_shadow_metadata
                    else [{} for _ in base_candidates]
                )
            for index, base_candidate in enumerate(base_candidates):
                metadata = dict(base_candidate.metadata)
                metadata["reverse_check_source_dict"] = self._reverse_source_dict or None
                if index < len(kaikkei_policy_shadow_by_index):
                    self._apply_kaikki_policy_overlay(
                        metadata=metadata,
                        shadow=kaikkei_policy_shadow_by_index[index],
                        kaikki_policy=self._kaikki_policy,
                    )
                yield replace(
                    base_candidate,
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata=metadata,
                )


def _build_filters(
    config: EnEsRulegenConfig,
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None,
    gloss_base_forms: Optional[set[str]] = None,
) -> list[CandidateFilter]:
    filters: list[CandidateFilter] = [NonEmptyFilter()]
    filters.append(
        EnEsGlossShapeFilter(
            allow_hyphen=config.allow_hyphen,
            allow_multiword_glosses=config.allow_multiword_glosses,
        )
    )
    if config.enable_length_filter:
        filters.append(
            LengthFilter(min_length=config.min_source_length, max_length=config.max_source_length)
        )
    if config.enable_possessive_filter:
        filters.append(PossessiveFilter())
    filters.append(ShadowedInterjectionFilter())
    if config.enable_stopword_filter:
        stopwords = config.stopwords or DEFAULT_STOPWORDS
        filters.append(EnEsStopwordFilter(stopwords=stopwords))
    if config.enable_inflection_filter:
        base_forms = (
            set(gloss_base_forms)
            if gloss_base_forms is not None
            else _build_gloss_base_forms(gloss_mapping or {})
        )
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


def _resolve_gloss_records(
    config: EnEsRulegenConfig,
) -> dict[str, list[TranslationGlossRecord]]:
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
) -> dict[str, list[TranslationGlossRecord]]:
    records_by_target: dict[str, list[TranslationGlossRecord]] = {}
    for target, entries in mapping.items():
        bucket: list[TranslationGlossRecord] = []
        for entry in entries:
            if isinstance(entry, TranslationGlossRecord):
                bucket.append(entry)
                continue
            bucket.append(TranslationGlossRecord(translation=str(entry), pos_raw=""))
        records_by_target[str(target)] = bucket
    return records_by_target


def _resolve_reverse_gloss_records(
    config: EnEsRulegenConfig,
) -> Optional[dict[str, list[TranslationGlossRecord]]]:
    if config.reverse_gloss_records_by_source is not None:
        return _coerce_gloss_records(config.reverse_gloss_records_by_source)
    if config.reverse_translation_dict_path is None:
        return None
    if not config.reverse_translation_dict_path.exists():
        return None
    return load_translation_gloss_records_ordered(
        config.reverse_translation_dict_path,
        target_lang="es",
    )


def _records_to_gloss_mapping(
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
) -> dict[str, list[str]]:
    return {
        target: [entry.translation for entry in entries]
        for target, entries in records_by_target.items()
    }
