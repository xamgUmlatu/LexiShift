from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.lexicon.word_package import (
    merge_script_forms,
    normalize_reading,
    normalize_word_package,
    resolve_language_tag_from_pair,
)
from lexishift_core.resources.dict_loaders import (
    JmdictEntryRecord,
    TranslationGlossRecord,
    load_jmdict_entry_index_glosses_and_script_forms,
    load_translation_gloss_records_ordered,
)
from lexishift_core.replacement.inflect import FORM_PLURAL, InflectionSpec
from lexishift_core.resources.japanese_script import contains_kana, contains_kanji, kana_to_romaji
from lexishift_core.frequency import (
    FrequencyLexicon,
    FrequencySourceConfig,
    build_frequency_provider,
    load_frequency_lexicon,
)
from lexishift_core.rulegen.generation import (
    CandidateNormalizer,
    CandidateFilter,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    RuleScoringConfig,
    SimpleSignalProvider,
    build_optional_pos_match_provider,
)
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package as resolve_generic_target_word_package,
)
from lexishift_core.rulegen.semantic_demotion import (
    resolve_generic_gloss_demotion,
    resolve_pair_generic_gloss_demotions,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionVariantExpander,
    InflectionArtifactFilter,
    LengthFilter,
    LeadingEnglishInfinitiveNormalizer,
    NonEmptyFilter,
    PossessiveFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
    sanitize_dictionary_gloss,
)
from lexishift_core.scoring.weighting import GlossDecay


def _should_expand_english(candidate: RuleCandidate) -> bool:
    phrase = str(candidate.source_phrase or "").strip().lower()
    if not phrase:
        return False
    if not all(ord(ch) < 128 for ch in phrase):
        return False
    if phrase in _EN_JA_NO_INFLECTION_EXPANSION_TERMS:
        return False
    return not phrase.endswith("ly")


_EN_JA_MAX_SPLIT_PARTS = 5
_EN_JA_ARTICLE_PREFIXES = (
    "a ",
    "an ",
    "the ",
    "one's ",
    "one’s ",
)
_EN_JA_INLINE_ANNOTATION_RE = re.compile(r"\s*(?:\([^)]*\)|\[[^\]]*\]|\{[^}]*\})")
_EN_JA_PARENTHESES_RE = re.compile(r"[\(\[]([^()\[\]]+)[\)\]]")
_EN_JA_KANA_RE = re.compile(r"[ぁ-んァ-ンー]+")
_EN_JA_JAPANESE_TEXT_RE = re.compile(r"[ぁ-んァ-ン一-龯々]")
_EN_JA_WORD_RE = re.compile(r"[a-z][a-z-]*")
_EN_JA_ASCII_ALIAS_RE = re.compile(r"[a-z][a-z' -]{1,31}")
_EN_JA_HEAD_BLOCKERS = {
    "as",
    "be",
    "having",
    "if",
    "indicates",
    "look",
    "representing",
    "seem",
    "to",
}
_EN_JA_HEAD_TAIL_BLOCKERS = {
    "as",
    "etc",
    "for",
    "if",
    "of",
    "or",
    "to",
}
_EN_JA_HEAD_QUALIFIERS = {
    "certain",
    "general",
    "particular",
    "same",
    "similar",
    "specific",
    "such",
    "various",
}
_EN_JA_SAFE_HEAD_NOUNS = {"train"}
_EN_JA_SAFE_LEADING_HEADS = {
    ("presence", "people"): "presence",
}
_EN_JA_SAFE_ADJECTIVE_HEADS = {
    ("spicy", "hot"): "spicy",
}
_EN_JA_SAFE_QUANTITY_HEADS = {
    "few",
    "little",
    "many",
    "much",
    "numerous",
    "several",
}
_EN_JA_TEMPORAL_HEAD_PREFIXES = {"all", "one"}
_EN_JA_TEMPORAL_HEAD_NOUNS = {"day", "days", "hour", "hours", "month", "months", "week", "weeks"}
_EN_JA_TRAILING_HEAD_QUALIFIERS = {"general", "particular"}
_EN_JA_ADMIN_DIVISION_HEADS = {"county", "department", "district", "prefecture", "province"}
_EN_JA_OCCUPATIONAL_TITLE_TERMS = {"teacher", "professor", "instructor", "master"}
_EN_JA_OCCUPATIONAL_TITLE_COMPETITORS = {"elder", "scholar", "sir", "sensei"}
_EN_JA_SPATIAL_NOUN_TERMS = {"above", "top", "surface"}
_EN_JA_SPATIAL_NOUN_COMPETITORS = {"earlier", "limit", "offer"}
_EN_JA_METHOD_TERMS = {"way", "method"}
_EN_JA_METHOD_COMPETITORS = {"direction", "alternative", "square"}
_EN_JA_EVENT_NOUN_TERMS = {
    "case",
    "circumstance",
    "circumstances",
    "instance",
    "occasion",
    "situation",
}
_EN_JA_EVENT_FUNCTION_COMPETITORS = {"if", "when"}
_EN_JA_BUSINESS_TERMS = {"business", "enterprise", "industry", "venture"}
_EN_JA_BUSINESS_COMPETITORS = {"activity", "program", "project", "service", "work"}
_EN_JA_GEOPOLITICAL_TERMS = {"country", "nation", "prefecture", "state"}
_EN_JA_GEOPOLITICAL_COMPETITORS = {"birthplace", "crown", "earth", "home", "land", "region"}
_EN_JA_MENTAL_STATE_TERMS = {"feeling", "heart", "mind", "mood", "spirit"}
_EN_JA_MENTAL_STATE_COMPETITORS = {"breath", "chi", "gas", "ki", "qi"}
_EN_JA_COMMUNICATION_NOUN_TERMS = {
    "chat",
    "communication",
    "conversation",
    "lecture",
    "speech",
    "story",
    "subject",
    "talk",
    "tale",
    "topic",
}
_EN_JA_COMMUNICATION_COMPETITORS = {"speaking", "talking"}
_EN_JA_QUIET_STATE_TERMS = {"calm", "peaceful", "quiet", "silent", "still", "tranquil"}
_EN_JA_QUIET_STATE_COMPETITORS = {"inaudible"}
_EN_JA_IMMEDIACY_ADVERB_TERMS = {"immediately", "right away", "soon"}
_EN_JA_IMMEDIACY_ADVERB_COMPETITORS = {
    "not bent",
    "quick to",
    "right close by",
    "right next to",
    "straight",
}
_EN_JA_CONTINUATION_ADVERB_TERMS = {"still", "yet"}
_EN_JA_PRACTICAL_EVALUATIVE_TERMS = {
    "all right",
    "enough",
    "fine",
    "okay",
    "sufficient",
    "tolerable",
}
_EN_JA_PRACTICAL_EVALUATIVE_COMPETITORS = {
    "assemble",
    "assembly",
    "composition",
    "compose",
    "plan",
    "preparations",
    "prepare",
    "quite",
    "scheme",
    "splendid",
    "to assemble",
    "to plan",
    "to prepare",
    "wonderful",
}
_EN_JA_TIME_SPAN_TERMS = {"24 hours", "all day", "day", "one day"}
_EN_JA_TIME_SPAN_COMPETITORS = {"daytime"}
_EN_JA_CERTAINTY_ADVERB_TERMS = {
    "always",
    "certainly",
    "inevitably",
    "invariably",
    "necessarily",
    "surely",
    "without fail",
}
_EN_JA_CERTAINTY_ADVERB_COMPETITORS = {"absolutely", "categorically", "definitely"}
_EN_JA_TOTALITY_NOUN_TERMS = {"all", "everything"}
_EN_JA_TOTALITY_ADVERB_COMPETITORS = {"approximately", "completely", "entirely", "wholly"}
_EN_JA_NONLEXICAL_FRAGMENT_TERMS = {"etc"}
_EN_JA_NO_INFLECTION_EXPANSION_TERMS = {"etc", "if", "when"}
_EN_JA_VERB_OBJECT_PLACEHOLDERS = {
    "it",
    "one",
    "oneself",
    "someone",
    "somebody",
    "something",
    "them",
    "this",
}
_EN_JA_STRUCTURAL_POS_DEMOTIONS = {
    "character": 0.7,
    "counter": 0.85,
    "name": 0.65,
    "prefix": 0.7,
}
_EN_JA_CONTENT_POS_VALUES = {
    "adj",
    "adjective",
    "adv",
    "adverb",
    "noun",
    "pron",
    "pronoun",
    "verb",
}


@dataclass(frozen=True)
class EnJaRulegenConfig:
    jmdict_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    gloss_records_by_reading: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    gloss_records_by_alias: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    script_forms_by_target: Optional[Mapping[str, Mapping[str, str]]] = None
    jmdict_entries_by_term: Optional[Mapping[str, Sequence[JmdictEntryRecord]]] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    language_pair: str = "en-ja"
    source_dict_id: str = ""
    dictionary_pos_source_profile: str = ""
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: float = 1.0
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    include_variants: bool = True
    variant_penalty: float = 0.2
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()
    enable_punctuation_filter: bool = True
    enable_possessive_filter: bool = True
    enable_inflection_filter: bool = True
    enable_stopword_filter: bool = True
    enable_length_filter: bool = True
    min_source_length: int = 2
    max_source_length: Optional[int] = None
    stopwords: Optional[set[str]] = None
    inflection_suffixes: Sequence[str] = ("s", "es")
    inflection_forms: Sequence[str] = (FORM_PLURAL,)
    allow_hyphen: bool = True
    generic_gloss_demotions: Mapping[str, float] = field(
        default_factory=lambda: resolve_pair_generic_gloss_demotions("en-ja")
    )
    frequency_config: Optional[FrequencySourceConfig] = None
    frequency_lexicon: Optional[FrequencyLexicon] = None
    frequency_provider: Optional[Callable[[RuleCandidate], float]] = None
    embedding_provider: Optional[Callable[[RuleCandidate], Optional[float]]] = None


def build_en_ja_pipeline(config: EnJaRulegenConfig) -> RuleGenerationPipeline:
    if _is_kaikki_dictionary_path(config.jmdict_path) or config.gloss_records_by_target is not None:
        records_by_target = _resolve_translation_gloss_records(config)
        mapping = _records_to_gloss_mapping(records_by_target)
        source = TranslationGlossCandidateSource(
            records_by_target=records_by_target,
            records_by_reading=config.gloss_records_by_reading,
            records_by_alias=config.gloss_records_by_alias,
            source_dict=_resolve_translation_source_dict_id(config),
            source_type="translation",
            word_packages_by_target=config.word_packages_by_target,
            generic_gloss_demotions=config.generic_gloss_demotions,
            dictionary_pos_source_profile=_resolve_translation_pos_profile(config),
        )
        return _build_pipeline_from_source(
            config=config,
            mapping=mapping,
            source=source,
        )
    script_forms_by_target: Mapping[str, Mapping[str, str]] = config.script_forms_by_target or {}
    jmdict_entries_by_term: Mapping[str, Sequence[JmdictEntryRecord]] = (
        config.jmdict_entries_by_term or {}
    )
    word_packages_by_target: Mapping[str, Mapping[str, object]] = (
        config.word_packages_by_target or {}
    )
    if config.gloss_mapping is not None:
        mapping = config.gloss_mapping
    else:
        discovered_entries, mapping, discovered_forms = (
            load_jmdict_entry_index_glosses_and_script_forms(config.jmdict_path)
        )
        if not jmdict_entries_by_term:
            jmdict_entries_by_term = discovered_entries
        if not script_forms_by_target:
            script_forms_by_target = discovered_forms
    source = JmdictCandidateSource(
        mapping=mapping,
        entries_by_term=jmdict_entries_by_term,
        source_dict="jmdict",
        source_type="translation",
        script_forms_by_target=script_forms_by_target,
        word_packages_by_target=word_packages_by_target,
        generic_gloss_demotions=config.generic_gloss_demotions,
    )
    return _build_pipeline_from_source(
        config=config,
        mapping=mapping,
        source=source,
    )


def _build_pipeline_from_source(
    *,
    config: EnJaRulegenConfig,
    mapping: Mapping[str, Sequence[str]],
    source: object,
) -> RuleGenerationPipeline:
    normalizers: list[CandidateNormalizer] = [
        BasicStringNormalizer(),
        LeadingEnglishInfinitiveNormalizer(),
    ]
    expanders = []
    if config.include_variants:
        expanders.append(
            InflectionVariantExpander(
                should_expand=_should_expand_english,
                spec=InflectionSpec(forms=frozenset(config.inflection_forms)),
            )
        )

    def variant_penalty_provider(candidate: RuleCandidate) -> float:
        return config.variant_penalty if candidate.metadata.get("variant") else 0.0

    def gloss_decay_multiplier(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    frequency_provider = config.frequency_provider
    if frequency_provider is None:
        if config.frequency_lexicon is not None:
            frequency_provider = build_frequency_provider(config.frequency_lexicon)
        elif config.frequency_config is not None:
            lexicon = load_frequency_lexicon(config.frequency_config)
            frequency_provider = build_frequency_provider(lexicon)

    if frequency_provider is not None:
        base_provider = frequency_provider

        def frequency_provider(candidate: RuleCandidate) -> float:
            return base_provider(candidate) * gloss_decay_multiplier(candidate)

    signal_provider = SimpleSignalProvider(
        dict_priorities={str(config.source_dict_id or "jmdict"): config.dict_priority},
        frequency_provider=frequency_provider,
        pos_match_provider=build_optional_pos_match_provider(config.scoring.pos_match),
        variant_penalty_provider=variant_penalty_provider,
        embedding_provider=config.embedding_provider,
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=expanders,
        filters=_build_filters(config, mapping),
        scorer=RuleScorer(weights=config.scoring.weights),
        signal_provider=signal_provider,
    )


def generate_en_ja_results(
    targets: Iterable[str],
    *,
    config: EnJaRulegenConfig,
) -> list[RuleGenerationResult]:
    pipeline = build_en_ja_pipeline(config)
    rule_config = RuleGenerationConfig(
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        max_definitions_per_target=config.max_definitions_per_target,
        max_rules_per_target=config.max_rules_per_target,
        semantic_demotion_scale=config.semantic_demotion_scale,
        tags=("translation", str(config.source_dict_id or "jmdict")),
    )
    return pipeline.generate_results(targets, config=rule_config)


def generate_en_ja_rules(
    targets: Iterable[str],
    *,
    config: EnJaRulegenConfig,
):
    return [result.rule for result in generate_en_ja_results(targets, config=config)]


class JmdictCandidateSource:
    def __init__(
        self,
        *,
        mapping: Mapping[str, Sequence[str]],
        entries_by_term: Mapping[str, Sequence[JmdictEntryRecord]],
        source_dict: str,
        source_type: str,
        script_forms_by_target: Optional[Mapping[str, Mapping[str, str]]] = None,
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
    ) -> None:
        self._mapping = mapping
        self._entries_by_term = entries_by_term
        self._source_dict = source_dict
        self._source_type = source_type
        self._script_forms_by_target = script_forms_by_target or {}
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            package_hint = self._word_packages_by_target.get(target)
            normalized_package = normalize_word_package(
                package_hint,
                fallback_surface=target,
                fallback_language_tag=resolve_language_tag_from_pair(language_pair),
                fallback_provider="frequency",
            )
            if normalized_package is None:
                continue
            reading = str(normalized_package.get("reading") or "").strip()
            if not reading:
                continue
            matched_entries = _select_entries_for_reading(
                entries=self._entries_by_term.get(target, ()),
                target=target,
                reading=reading,
            )
            if not matched_entries:
                continue
            sources = _collect_entry_glosses(matched_entries)
            total = len(sources)
            if not sources:
                continue
            discovered_script_forms = _build_matched_script_forms(
                target=target,
                reading=reading,
                entries=matched_entries,
                fallback=self._script_forms_by_target.get(target),
            )
            resolved_word_package = _resolve_target_word_package(
                target=target,
                language_pair=language_pair,
                source_dict=self._source_dict,
                package_hint=normalized_package,
                discovered_script_forms=discovered_script_forms,
            )
            if resolved_word_package is None:
                continue
            resolved_script_forms = _resolve_word_package_script_forms(
                resolved_word_package,
                fallback=discovered_script_forms,
            )
            target_pos = extract_target_pos_component(
                target_word_package=resolved_word_package,
                language_pair=language_pair,
            )
            entry_pos_raw = _resolve_entry_pos_raw(matched_entries)
            source_pos = normalize_pos_component(
                entry_pos_raw,
                language_pair=language_pair,
                source_provider=self._source_dict,
                source_kind="dictionary",
            )
            for index, source in enumerate(sources):
                metadata: dict[str, object] = {
                    "gloss_index": index,
                    "gloss_total": total,
                }
                demotion = self._resolve_generic_gloss_demotion(source)
                if demotion > 0.0:
                    metadata["semantic_demotion"] = demotion
                    metadata["semantic_demotion_reason"] = "generic_gloss"
                if resolved_script_forms:
                    metadata["script_forms"] = resolved_script_forms
                if resolved_word_package:
                    metadata["word_package"] = resolved_word_package
                metadata.update(
                    build_candidate_pos_metadata(
                        source_pos=source_pos,
                        target_pos=target_pos,
                        dictionary_pos=source_pos,
                    )
                )
                yield RuleCandidate(
                    source_phrase=str(source),
                    replacement=str(target),
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata=metadata,
                )

    def _resolve_generic_gloss_demotion(self, source: object) -> float:
        return resolve_generic_gloss_demotion(
            source,
            demotions=self._generic_gloss_demotions,
        )


class TranslationGlossCandidateSource:
    def __init__(
        self,
        *,
        records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
        records_by_reading: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
        records_by_alias: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
        source_dict: str,
        source_type: str,
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
        dictionary_pos_source_profile: str = "",
    ) -> None:
        self._records_by_target = records_by_target
        self._records_by_reading = (
            records_by_reading
            if records_by_reading is not None
            else _build_translation_gloss_reading_index(records_by_target)
        )
        self._records_by_alias = (
            records_by_alias
            if records_by_alias is not None
            else _build_translation_gloss_alias_index(records_by_target)
        )
        self._source_dict = source_dict
        self._source_type = source_type
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._dictionary_pos_source_profile = str(dictionary_pos_source_profile or "").strip()

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            target_word_package = resolve_generic_target_word_package(
                target=target,
                language_pair=language_pair,
                fallback_provider="frequency",
                package_hint=self._word_packages_by_target.get(target),
            )
            target_reading = ""
            if isinstance(target_word_package, Mapping):
                target_reading = str(target_word_package.get("reading") or "").strip()
            target_pos = extract_target_pos_component(
                target_word_package=target_word_package,
                language_pair=language_pair,
            )
            entries = _collect_sanitized_translation_gloss_records(
                _resolve_target_translation_gloss_records(
                    self._records_by_target,
                    records_by_reading=self._records_by_reading,
                    records_by_alias=self._records_by_alias,
                    target=target,
                    target_word_package=target_word_package,
                ),
                target_reading=target_reading,
            )
            total = len(entries)
            for index, entry in enumerate(entries):
                dictionary_pos = normalize_pos_component(
                    entry.pos_raw,
                    language_pair=language_pair,
                    source_provider=self._source_dict,
                    source_kind="dictionary",
                    source_profile=self._dictionary_pos_source_profile,
                )
                metadata: dict[str, object] = {
                    "gloss_index": index,
                    "gloss_total": total,
                }
                local_demotion = _resolve_local_translation_demotion(entry)
                demotion = resolve_generic_gloss_demotion(
                    entry.translation,
                    demotions=self._generic_gloss_demotions,
                )
                if local_demotion is not None:
                    local_value, local_reason = local_demotion
                    if local_value > demotion:
                        demotion = local_value
                        metadata["semantic_demotion_reason"] = local_reason
                if demotion > 0.0:
                    metadata["semantic_demotion"] = demotion
                    metadata.setdefault("semantic_demotion_reason", "generic_gloss")
                if target_word_package is not None:
                    metadata["word_package"] = target_word_package
                if entry.metadata:
                    metadata["dictionary_metadata"] = dict(entry.metadata)
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


def _is_kaikki_dictionary_path(path: Path | None) -> bool:
    if path is None:
        return False
    name = str(path.name or "").strip().lower()
    return "wiktionary" in name or "kaikki" in name


def _resolve_translation_source_dict_id(config: EnJaRulegenConfig) -> str:
    source_dict_id = str(config.source_dict_id or "").strip()
    if source_dict_id:
        return source_dict_id
    if _is_kaikki_dictionary_path(config.jmdict_path):
        return "wiktionary_ja_en"
    return "translation_dict"


def _resolve_translation_pos_profile(config: EnJaRulegenConfig) -> str:
    profile = str(config.dictionary_pos_source_profile or "").strip()
    if profile:
        return profile
    if _is_kaikki_dictionary_path(config.jmdict_path):
        return "wiktionary"
    return ""


def _resolve_translation_gloss_records(
    config: EnJaRulegenConfig,
) -> dict[str, list[TranslationGlossRecord]]:
    if config.gloss_records_by_target is not None:
        return _coerce_translation_gloss_records(config.gloss_records_by_target)
    if config.gloss_mapping is not None:
        return _coerce_translation_gloss_records(config.gloss_mapping)
    return load_translation_gloss_records_ordered(
        config.jmdict_path,
        target_lang="en",
    )


def _coerce_translation_gloss_records(
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


def _records_to_gloss_mapping(
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
) -> dict[str, list[str]]:
    return {
        target: [entry.translation for entry in entries]
        for target, entries in records_by_target.items()
    }


def _resolve_target_translation_gloss_records(
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    *,
    records_by_reading: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
    records_by_alias: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
    target: str,
    target_word_package: Optional[Mapping[str, object]],
) -> Sequence[TranslationGlossRecord]:
    direct = records_by_target.get(target, ())
    if direct:
        return direct
    for lookup_key in _iter_en_ja_translation_lookup_keys(
        target=target,
        target_word_package=target_word_package,
    ):
        fallback = records_by_target.get(lookup_key, ())
        if fallback:
            return fallback
    if records_by_alias:
        for lookup_key in _iter_en_ja_translation_alias_lookup_keys(
            target=target,
            target_word_package=target_word_package,
        ):
            fallback = records_by_alias.get(lookup_key, ())
            if fallback:
                return fallback
    if records_by_reading:
        for lookup_key in _iter_en_ja_translation_lookup_keys(
            target=target,
            target_word_package=target_word_package,
        ):
            fallback = records_by_reading.get(lookup_key, ())
            if fallback:
                return fallback
    return ()


def _iter_en_ja_translation_lookup_keys(
    *,
    target: str,
    target_word_package: Optional[Mapping[str, object]],
) -> Iterable[str]:
    seen: set[str] = set()
    if not isinstance(target_word_package, Mapping):
        return ()
    lookup_keys: list[str] = []
    reading = str(target_word_package.get("reading") or "").strip()
    if reading:
        normalized = normalize_reading(reading, language_tag="ja")
        if normalized and normalized not in seen:
            lookup_keys.append(normalized)
            seen.add(normalized)
    script_forms = target_word_package.get("script_forms")
    if isinstance(script_forms, Mapping):
        kana = str(script_forms.get("kana") or "").strip()
        if kana:
            normalized = normalize_reading(kana, language_tag="ja")
            if normalized and normalized not in seen:
                lookup_keys.append(normalized)
                seen.add(normalized)
    return tuple(lookup_keys)


def _build_translation_gloss_reading_index(
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
) -> dict[str, list[TranslationGlossRecord]]:
    records_by_reading: dict[str, list[TranslationGlossRecord]] = {}
    for entries in records_by_target.values():
        for record in entries:
            for reading in _extract_translation_record_readings(record):
                bucket = records_by_reading.setdefault(reading, [])
                bucket.append(record)
    return records_by_reading


def _build_translation_gloss_alias_index(
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
) -> dict[str, list[TranslationGlossRecord]]:
    records_by_alias: dict[str, list[TranslationGlossRecord]] = {}
    for entries in records_by_target.values():
        for record in entries:
            for alias in _extract_translation_record_aliases(record):
                bucket = records_by_alias.setdefault(alias, [])
                bucket.append(record)
    return records_by_alias


def _iter_en_ja_translation_alias_lookup_keys(
    *,
    target: str,
    target_word_package: Optional[Mapping[str, object]],
) -> tuple[str, ...]:
    keys: list[str] = []
    seen: set[str] = set()

    def _append(value: object) -> None:
        text = str(value or "").strip()
        if not text:
            return
        lowered = text.lower()
        if lowered in seen:
            return
        keys.append(lowered)
        seen.add(lowered)

    _append(target)
    if not isinstance(target_word_package, Mapping):
        return tuple(keys)
    script_forms = target_word_package.get("script_forms")
    if isinstance(script_forms, Mapping):
        _append(script_forms.get("romaji"))
    reading = normalize_reading(target_word_package.get("reading"), language_tag="ja")
    if reading:
        _append(kana_to_romaji(reading))
    return tuple(keys)


def _collect_sanitized_translation_gloss_records(
    records: Iterable[TranslationGlossRecord],
    *,
    target_reading: str = "",
) -> list[TranslationGlossRecord]:
    filtered_records = _select_translation_gloss_records_for_reading(
        records,
        target_reading=target_reading,
    )
    cleaned: list[TranslationGlossRecord] = []
    seen: dict[str, int] = {}
    for record in filtered_records:
        normalized_pos = str(record.pos_raw or "").strip()
        variants = _expand_en_ja_translation_gloss_variants(
            record,
            target_reading=target_reading,
        )
        for variant in variants:
            sanitized = sanitize_dictionary_gloss(variant.translation)
            if not sanitized:
                continue
            existing_index = seen.get(sanitized)
            if existing_index is None:
                cleaned.append(
                    TranslationGlossRecord(
                        translation=sanitized,
                        pos_raw=normalized_pos,
                        metadata=dict(variant.metadata),
                    )
                )
                seen[sanitized] = len(cleaned) - 1
                continue
            candidate_record = TranslationGlossRecord(
                translation=sanitized,
                pos_raw=normalized_pos,
                metadata=dict(variant.metadata),
            )
            existing_record = cleaned[existing_index]
            if _should_prefer_en_ja_duplicate_record(existing_record, candidate_record):
                cleaned[existing_index] = candidate_record
            elif not existing_record.pos_raw and normalized_pos:
                cleaned[existing_index] = TranslationGlossRecord(
                    translation=sanitized,
                    pos_raw=normalized_pos,
                    metadata=existing_record.metadata,
                )
    return _apply_en_ja_target_local_demotions(cleaned)


def _select_translation_gloss_records_for_reading(
    records: Iterable[TranslationGlossRecord],
    *,
    target_reading: str,
) -> list[TranslationGlossRecord]:
    entries = list(records)
    normalized_target_reading = normalize_reading(target_reading, language_tag="ja")
    if not normalized_target_reading:
        return entries
    annotated_entries: list[tuple[TranslationGlossRecord, str]] = []
    matched_any = False
    for record in entries:
        readings = _extract_translation_record_readings(record)
        if not readings:
            state = (
                "compatible_unresolved"
                if (
                    _record_has_japanese_entry_form(record)
                    or _is_en_ja_plain_unresolved_character_gloss(record)
                )
                else "unresolved"
            )
            annotated_entries.append((record, state))
            continue
        matched = normalized_target_reading in readings
        annotated_entries.append((record, "matched" if matched else "mismatched"))
        if matched:
            matched_any = True
    if not matched_any:
        return entries
    return [
        record
        for record, state in annotated_entries
        if state in {"matched", "compatible_unresolved"}
    ]


def _extract_translation_record_readings(record: TranslationGlossRecord) -> tuple[str, ...]:
    readings: list[str] = []
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    entry_forms = metadata.get("entry_forms")
    if isinstance(entry_forms, Sequence) and not isinstance(entry_forms, (str, bytes)):
        for form in entry_forms:
            for reading in _extract_entry_form_readings(form):
                if reading and reading not in readings:
                    readings.append(reading)
    if readings:
        return tuple(readings)
    for reading in _extract_parenthetical_kana_readings(record.translation):
        if reading not in readings:
            readings.append(reading)
    return tuple(readings)


def _extract_translation_record_aliases(record: TranslationGlossRecord) -> tuple[str, ...]:
    aliases: list[str] = []
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    entry_forms = metadata.get("entry_forms")
    if not isinstance(entry_forms, Sequence) or isinstance(entry_forms, (str, bytes)):
        return ()
    for form in entry_forms:
        if not isinstance(form, Mapping):
            continue
        form_text = str(form.get("form") or "").strip()
        if not form_text:
            continue
        normalized_reading = normalize_reading(form_text, language_tag="ja")
        if normalized_reading and normalized_reading not in aliases:
            aliases.append(normalized_reading)
        lowered = form_text.lower()
        if _EN_JA_ASCII_ALIAS_RE.fullmatch(lowered) and lowered not in aliases:
            aliases.append(lowered)
    return tuple(aliases)


def _record_has_japanese_entry_form(record: TranslationGlossRecord) -> bool:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    entry_forms = metadata.get("entry_forms")
    if not isinstance(entry_forms, Sequence) or isinstance(entry_forms, (str, bytes)):
        return False
    for form in entry_forms:
        if not isinstance(form, Mapping):
            continue
        form_text = str(form.get("form") or "").strip()
        if form_text and (contains_kanji(form_text) or contains_kana(form_text)):
            return True
    return False


def _is_en_ja_plain_unresolved_character_gloss(record: TranslationGlossRecord) -> bool:
    if str(record.pos_raw or "").strip().lower() != "character":
        return False
    normalized, _operations = _normalize_en_ja_gloss_fragment(
        str(record.translation or ""),
        target_reading="",
    )
    if not normalized:
        return False
    return " " not in normalized


def _extract_entry_form_readings(value: object) -> tuple[str, ...]:
    if not isinstance(value, Mapping):
        return ()
    readings: list[str] = []
    ruby = value.get("ruby")
    if isinstance(ruby, Sequence) and not isinstance(ruby, (str, bytes)):
        ruby_readings: list[str] = []
        for segment in ruby:
            reading = _extract_ruby_segment_reading(segment)
            if not reading:
                continue
            ruby_readings.append(reading)
            if reading not in readings:
                readings.append(reading)
        combined = normalize_reading("".join(ruby_readings), language_tag="ja")
        if combined and combined not in readings:
            readings.append(combined)
    form_text = normalize_reading(value.get("form"), language_tag="ja")
    if form_text and _EN_JA_KANA_RE.fullmatch(form_text) and form_text not in readings:
        readings.append(form_text)
    return tuple(readings)


def _extract_ruby_segment_reading(value: object) -> str:
    candidate = value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ""
        try:
            candidate = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            candidate = text
    if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes)):
        values = list(candidate)
        if len(values) >= 2:
            return normalize_reading(values[1], language_tag="ja")
    if isinstance(candidate, str):
        matches = _EN_JA_KANA_RE.findall(candidate)
        if matches:
            return normalize_reading(matches[-1], language_tag="ja")
    return ""


def _expand_en_ja_translation_gloss_variants(
    record: TranslationGlossRecord,
    *,
    target_reading: str,
) -> list[TranslationGlossRecord]:
    input_text = str(record.translation or "").strip()
    working_text, _stripped_source_label = _strip_en_ja_source_label_prefix(input_text)
    sanitized = sanitize_dictionary_gloss(working_text)
    if not sanitized:
        return []
    fragments = _split_en_ja_gloss_fragments(sanitized)
    variants: list[TranslationGlossRecord] = []
    seen: set[str] = set()
    for fragment_index, fragment in enumerate(fragments):
        raw_source_text = str(fragment.get("raw_text") or "").strip()
        fragment_text = str(fragment.get("text") or "").strip()
        normalized_text, operations = _normalize_en_ja_gloss_fragment(
            fragment_text or raw_source_text,
            target_reading=target_reading,
        )
        if not normalized_text:
            continue
        base_metadata = dict(record.metadata)
        fragment_metadata = _build_en_ja_gloss_fragment_metadata(
            input_text=input_text,
            sanitized_text=sanitized,
            raw_source_text=raw_source_text,
            fragment_text=normalized_text,
            fragment=fragment,
            fragment_index=fragment_index,
            fragment_count=len(fragments),
            operations=operations,
        )
        verb_variant = _recover_en_ja_verb_head_variant(
            normalized_text,
            pos_raw=record.pos_raw,
        )
        if verb_variant:
            verb_text, verb_operations = verb_variant
            if verb_text and verb_text not in seen:
                verb_metadata = dict(base_metadata)
                verb_metadata.update(fragment_metadata)
                verb_metadata["gloss_fragment_strategy"] = "verb_head"
                verb_metadata["gloss_fragment_emitted_text"] = verb_text
                verb_metadata["gloss_fragment_operations"] = tuple(
                    dict.fromkeys((*operations, *verb_operations))
                )
                variants.append(
                    TranslationGlossRecord(
                        translation=verb_text,
                        pos_raw=record.pos_raw,
                        metadata=verb_metadata,
                    )
                )
                seen.add(verb_text)
        adjective_variant = _recover_en_ja_adjective_head_variant(
            normalized_text,
            pos_raw=record.pos_raw,
        )
        if adjective_variant:
            adjective_text, adjective_operations = adjective_variant
            if adjective_text and adjective_text not in seen:
                adjective_metadata = dict(base_metadata)
                adjective_metadata.update(fragment_metadata)
                adjective_metadata["gloss_fragment_strategy"] = "adjective_head"
                adjective_metadata["gloss_fragment_emitted_text"] = adjective_text
                adjective_metadata["gloss_fragment_operations"] = tuple(
                    dict.fromkeys((*operations, *adjective_operations))
                )
                variants.append(
                    TranslationGlossRecord(
                        translation=adjective_text,
                        pos_raw=record.pos_raw,
                        metadata=adjective_metadata,
                    )
                )
                seen.add(adjective_text)
        head_variant = _recover_en_ja_nominal_head_variant(
            normalized_text,
            pos_raw=record.pos_raw,
        )
        if head_variant:
            head_text, head_operations = head_variant
            if head_text and head_text not in seen:
                head_metadata = dict(base_metadata)
                head_metadata.update(fragment_metadata)
                head_metadata["gloss_fragment_strategy"] = "nominal_head"
                head_metadata["gloss_fragment_emitted_text"] = head_text
                head_metadata["gloss_fragment_operations"] = tuple(
                    dict.fromkeys((*operations, *head_operations))
                )
                variants.append(
                    TranslationGlossRecord(
                        translation=head_text,
                        pos_raw=record.pos_raw,
                        metadata=head_metadata,
                    )
                )
                seen.add(head_text)
        if normalized_text in seen:
            continue
        metadata = dict(base_metadata)
        metadata.update(fragment_metadata)
        variants.append(
            TranslationGlossRecord(
                translation=normalized_text,
                pos_raw=record.pos_raw,
                metadata=metadata,
            )
        )
        seen.add(normalized_text)
    return variants


def _build_en_ja_gloss_fragment_metadata(
    *,
    input_text: str,
    sanitized_text: str,
    raw_source_text: str,
    fragment_text: str,
    fragment: Mapping[str, object],
    fragment_index: int,
    fragment_count: int,
    operations: Sequence[str],
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "gloss_input_text": input_text,
        "gloss_raw_text": sanitized_text,
        "gloss_fragment_index": fragment_index,
        "gloss_fragment_count": fragment_count,
        "gloss_fragment_strategy": str(fragment.get("strategy") or "identity"),
        "gloss_fragment_emitted_text": fragment_text,
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
    return metadata


def _apply_en_ja_target_local_demotions(
    records: Sequence[TranslationGlossRecord],
) -> list[TranslationGlossRecord]:
    translations = {str(record.translation or "").strip().lower() for record in records}
    has_occupational_titles = bool(translations & _EN_JA_OCCUPATIONAL_TITLE_TERMS)
    has_spatial_nouns = bool(translations & _EN_JA_SPATIAL_NOUN_TERMS)
    has_method_terms = bool(translations & _EN_JA_METHOD_TERMS)
    has_event_nouns = bool(translations & _EN_JA_EVENT_NOUN_TERMS)
    has_business_terms = bool(translations & _EN_JA_BUSINESS_TERMS)
    has_geopolitical_terms = bool(translations & _EN_JA_GEOPOLITICAL_TERMS)
    has_mental_state_terms = bool(translations & _EN_JA_MENTAL_STATE_TERMS)
    has_communication_nouns = bool(translations & _EN_JA_COMMUNICATION_NOUN_TERMS)
    has_quiet_state_terms = bool(translations & _EN_JA_QUIET_STATE_TERMS)
    has_immediacy_adverbs = bool(translations & _EN_JA_IMMEDIACY_ADVERB_TERMS)
    has_continuation_adverbs = any(
        str(record.translation or "").strip().lower() in _EN_JA_CONTINUATION_ADVERB_TERMS
        and _normalize_en_ja_pos(record.pos_raw) in {"adv", "adverb"}
        for record in records
    )
    has_practical_evaluatives = bool(translations & _EN_JA_PRACTICAL_EVALUATIVE_TERMS)
    has_time_span_terms = bool(translations & _EN_JA_TIME_SPAN_TERMS)
    has_certainty_adverbs = bool(translations & _EN_JA_CERTAINTY_ADVERB_TERMS)
    has_totality_nouns = bool(translations & _EN_JA_TOTALITY_NOUN_TERMS)
    has_content_pos = any(_has_en_ja_content_pos(record.pos_raw) for record in records)
    adjusted: list[TranslationGlossRecord] = []
    for record in records:
        metadata = dict(record.metadata)
        translation = str(record.translation or "").strip().lower()
        if translation in _EN_JA_NONLEXICAL_FRAGMENT_TERMS:
            continue
        current = float(metadata.get("semantic_demotion") or 0.0)
        pos = _normalize_en_ja_pos(record.pos_raw)
        strategy = str(metadata.get("gloss_fragment_strategy") or "identity").strip()
        if has_practical_evaluatives and translation in _EN_JA_PRACTICAL_EVALUATIVE_COMPETITORS:
            continue
        if has_content_pos:
            structural_demotion = _EN_JA_STRUCTURAL_POS_DEMOTIONS.get(pos)
            if (
                structural_demotion is not None
                and strategy not in {"nominal_head", "verb_head"}
                and structural_demotion > current
            ):
                metadata["semantic_demotion"] = structural_demotion
                metadata["semantic_demotion_reason"] = f"structural_{pos}"
                current = structural_demotion
        if has_occupational_titles and translation in _EN_JA_OCCUPATIONAL_TITLE_COMPETITORS:
            if 0.75 > current:
                metadata["semantic_demotion"] = 0.75
                metadata["semantic_demotion_reason"] = "occupational_title_competition"
                current = 0.75
        if has_event_nouns and translation in _EN_JA_EVENT_FUNCTION_COMPETITORS:
            if 0.8 > current:
                metadata["semantic_demotion"] = 0.8
                metadata["semantic_demotion_reason"] = "event_noun_competition"
                current = 0.8
        if has_business_terms and translation in _EN_JA_BUSINESS_COMPETITORS:
            if 0.8 > current:
                metadata["semantic_demotion"] = 0.8
                metadata["semantic_demotion_reason"] = "business_family_competition"
                current = 0.8
        if has_geopolitical_terms and translation in _EN_JA_GEOPOLITICAL_COMPETITORS:
            if 0.8 > current:
                metadata["semantic_demotion"] = 0.8
                metadata["semantic_demotion_reason"] = "geopolitical_competition"
                current = 0.8
        if has_mental_state_terms and translation in _EN_JA_MENTAL_STATE_COMPETITORS:
            if 0.8 > current:
                metadata["semantic_demotion"] = 0.8
                metadata["semantic_demotion_reason"] = "mental_state_competition"
                current = 0.8
        if has_communication_nouns and translation in _EN_JA_COMMUNICATION_COMPETITORS:
            if 0.8 > current:
                metadata["semantic_demotion"] = 0.8
                metadata["semantic_demotion_reason"] = "communication_noun_competition"
                current = 0.8
        if has_spatial_nouns and translation in _EN_JA_SPATIAL_NOUN_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "spatial_noun_competition"
                current = 0.9
        if has_method_terms and translation in _EN_JA_METHOD_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "method_suffix_competition"
                current = 0.9
        if has_quiet_state_terms and translation in _EN_JA_QUIET_STATE_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "quiet_state_competition"
                current = 0.9
        if has_immediacy_adverbs and translation in _EN_JA_IMMEDIACY_ADVERB_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "immediacy_adverb_competition"
                current = 0.9
        if has_continuation_adverbs and pos not in {"adv", "adverb"}:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "continuation_adverb_competition"
                current = 0.9
        if has_time_span_terms and translation in _EN_JA_TIME_SPAN_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "time_span_competition"
                current = 0.9
        if has_totality_nouns and translation in _EN_JA_TOTALITY_ADVERB_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "totality_noun_competition"
                current = 0.9
        if has_certainty_adverbs and translation in _EN_JA_CERTAINTY_ADVERB_COMPETITORS:
            if 0.9 > current:
                metadata["semantic_demotion"] = 0.9
                metadata["semantic_demotion_reason"] = "certainty_adverb_competition"
        adjusted.append(
            TranslationGlossRecord(
                translation=record.translation,
                pos_raw=record.pos_raw,
                metadata=metadata,
            )
        )
    return adjusted


def _resolve_local_translation_demotion(
    record: TranslationGlossRecord,
) -> tuple[float, str] | None:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    raw_value = metadata.get("semantic_demotion")
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None
    if value <= 0.0:
        return None
    reason = str(metadata.get("semantic_demotion_reason") or "local_gloss").strip() or "local_gloss"
    return value, reason


def _should_prefer_en_ja_duplicate_record(
    current: TranslationGlossRecord,
    candidate: TranslationGlossRecord,
) -> bool:
    current_metadata = current.metadata if isinstance(current.metadata, Mapping) else {}
    candidate_metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    current_strategy = str(current_metadata.get("gloss_fragment_strategy") or "identity").strip()
    candidate_strategy = str(
        candidate_metadata.get("gloss_fragment_strategy") or "identity"
    ).strip()
    if current_strategy in {"nominal_head", "verb_head"} and candidate_strategy == "identity":
        return True
    current_pos = _normalize_en_ja_pos(current.pos_raw)
    candidate_pos = _normalize_en_ja_pos(candidate.pos_raw)
    if current_pos in _EN_JA_STRUCTURAL_POS_DEMOTIONS and _has_en_ja_content_pos(candidate.pos_raw):
        return True
    current_demotion = _read_en_ja_semantic_demotion(current_metadata)
    candidate_demotion = _read_en_ja_semantic_demotion(candidate_metadata)
    return candidate_demotion < current_demotion


def _read_en_ja_semantic_demotion(metadata: Mapping[str, object]) -> float:
    try:
        return float(metadata.get("semantic_demotion") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _split_en_ja_gloss_fragments(text: str) -> list[dict[str, object]]:
    if not text:
        return [{"raw_text": "", "text": "", "strategy": "identity", "separator": ""}]
    semicolon_parts = _split_top_level_fragments(text, separator=";")
    if _should_split_en_ja_fragments(semicolon_parts):
        fragments: list[dict[str, object]] = []
        for part in semicolon_parts:
            fragments.extend(_split_en_ja_comma_and_or_fragments(part))
        if fragments:
            return fragments
    return _split_en_ja_comma_and_or_fragments(text)


def _split_en_ja_comma_and_or_fragments(text: str) -> list[dict[str, object]]:
    comma_parts = _split_top_level_fragments(text, separator=",")
    if _should_split_en_ja_fragments(comma_parts):
        fragments: list[dict[str, object]] = []
        for part in comma_parts:
            fragments.extend(_split_en_ja_or_fragments(part))
        if fragments:
            return fragments
    return _split_en_ja_or_fragments(text)


def _split_en_ja_or_fragments(text: str) -> list[dict[str, object]]:
    parts = _split_top_level_text_fragments(text, separator=" or ")
    if not _should_split_en_ja_fragments(parts):
        return [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]
    return [
        {
            "raw_text": part,
            "text": part,
            "strategy": "top_level_or",
            "separator": " or ",
        }
        for part in parts
        if str(part or "").strip()
    ] or [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]


def _should_split_en_ja_fragments(parts: Sequence[str]) -> bool:
    if len(parts) <= 1 or len(parts) > _EN_JA_MAX_SPLIT_PARTS:
        return False
    return all(str(part or "").strip() for part in parts)


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


def _split_top_level_text_fragments(text: str, *, separator: str) -> list[str]:
    if not text or separator not in text.lower():
        return [text]
    parts: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    index = 0
    separator_length = len(separator)
    lowered = text.lower()
    while index < len(text):
        char = text[index]
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
        if (
            paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
            and lowered[index : index + separator_length] == separator
        ):
            part = "".join(buffer).strip()
            if part:
                parts.append(part)
            buffer = []
            index += separator_length
            continue
        buffer.append(char)
        index += 1
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return parts or [text]


def _normalize_en_ja_gloss_fragment(
    text: str,
    *,
    target_reading: str,
) -> tuple[str, tuple[str, ...]]:
    raw_text = str(text or "").strip()
    if not raw_text:
        return "", ()
    operations: list[str] = []
    collapsed = re.sub(r"\s+", " ", raw_text).strip()
    if collapsed != raw_text:
        operations.append("sanitize_gloss")
    stripped, stripped_parenthetical = _strip_en_ja_inline_annotations(
        collapsed,
        target_reading=target_reading,
    )
    if not stripped:
        return "", tuple(dict.fromkeys(operations))
    if stripped_parenthetical:
        operations.append("strip_inline_annotation")
    stripped, stripped_label = _strip_en_ja_source_label_prefix(stripped)
    if not stripped:
        return "", tuple(dict.fromkeys(operations))
    if stripped_label:
        operations.append("strip_source_label")
    lowered = stripped.lower()
    for prefix in _EN_JA_ARTICLE_PREFIXES:
        if lowered.startswith(prefix):
            stripped = stripped[len(prefix) :].strip()
            operations.append("strip_article_prefix")
            break
    normalized = sanitize_dictionary_gloss(stripped)
    if normalized and normalized != stripped:
        operations.append("resanitize_gloss")
    return normalized, tuple(dict.fromkeys(operations))


def _strip_en_ja_source_label_prefix(text: str) -> tuple[str, bool]:
    current = str(text or "").strip()
    if not current or ":" not in current:
        return current, False
    prefix, rest = current.split(":", 1)
    prefix = prefix.strip()
    rest = rest.strip()
    if not prefix or not rest:
        return current, False
    if not _EN_JA_JAPANESE_TEXT_RE.search(prefix):
        return current, False
    if not re.search(r"[A-Za-z]", rest):
        return current, False
    return rest, True


def _strip_en_ja_inline_annotations(
    text: str,
    *,
    target_reading: str,
) -> tuple[str, bool]:
    current = str(text or "").strip()
    normalized_target_reading = normalize_reading(target_reading, language_tag="ja")
    parenthetical_readings = _extract_parenthetical_kana_readings(current)
    if parenthetical_readings and normalized_target_reading:
        if normalized_target_reading not in parenthetical_readings:
            return "", False
    previous = None
    changed = False
    while current and current != previous:
        previous = current
        current = _EN_JA_INLINE_ANNOTATION_RE.sub("", current)
        current = re.sub(r"\s+", " ", current).strip()
        if current != previous:
            changed = True
    return current, changed


def _extract_parenthetical_kana_readings(value: object) -> tuple[str, ...]:
    text = str(value or "").strip()
    if not text:
        return ()
    readings: list[str] = []
    for match in _EN_JA_PARENTHESES_RE.findall(text):
        for kana in _EN_JA_KANA_RE.findall(match):
            normalized = normalize_reading(kana, language_tag="ja")
            if normalized and normalized not in readings:
                readings.append(normalized)
    return tuple(readings)


def _recover_en_ja_nominal_head_variant(
    text: str,
    *,
    pos_raw: str,
) -> tuple[str, tuple[str, ...]] | None:
    normalized = sanitize_dictionary_gloss(text)
    if not normalized or " " not in normalized:
        return None
    lowered_pos = str(pos_raw or "").strip().lower()
    if "verb" in lowered_pos:
        return None
    trailing_qualifier_variant = _recover_en_ja_trailing_qualifier_head_variant(normalized)
    if trailing_qualifier_variant is not None:
        return trailing_qualifier_variant
    admin_division_variant = _recover_en_ja_admin_division_head_variant(normalized)
    if admin_division_variant is not None:
        return admin_division_variant
    words = [token for token in normalized.lower().split(" ") if token]
    if len(words) < 2 or len(words) > 3:
        if len(words) == 4 and words[-1] in _EN_JA_SAFE_HEAD_NOUNS:
            if all(_EN_JA_WORD_RE.fullmatch(token) for token in words):
                return words[-1], ("extract_nominal_head",)
        return None
    if len(words) == 2:
        leading, head = words
        if (
            leading.isdigit() or leading in _EN_JA_TEMPORAL_HEAD_PREFIXES
        ) and head in _EN_JA_TEMPORAL_HEAD_NOUNS:
            singular = head[:-1] if head.endswith("s") and len(head) > 1 else head
            return singular, ("extract_temporal_head",)
    if any(not _EN_JA_WORD_RE.fullmatch(token) for token in words):
        return None
    if len(words) == 3 and words[1] == "of":
        leading = _EN_JA_SAFE_LEADING_HEADS.get((words[0], words[2]))
        if leading:
            return leading, ("extract_nominal_head",)
    if words[0] == "color" and len(words) == 2:
        return words[-1], ("extract_color_value",)
    if words[0] not in _EN_JA_HEAD_QUALIFIERS:
        return None
    if "of" in words[1:-1]:
        return None
    if words[0] in _EN_JA_HEAD_BLOCKERS:
        return None
    head = words[-1]
    if head in _EN_JA_HEAD_TAIL_BLOCKERS:
        return None
    return head, ("extract_nominal_head",)


def _recover_en_ja_adjective_head_variant(
    text: str,
    *,
    pos_raw: str,
) -> tuple[str, tuple[str, ...]] | None:
    lowered_pos = str(pos_raw or "").strip().lower()
    if "adj" not in lowered_pos:
        return None
    normalized = sanitize_dictionary_gloss(text).lower()
    quantity_variant = _recover_en_ja_quantity_head_variant(normalized)
    if quantity_variant is not None:
        return quantity_variant
    words = [token for token in normalized.split(" ") if token]
    if len(words) != 2:
        return None
    if any(not _EN_JA_WORD_RE.fullmatch(token) for token in words):
        return None
    head = _EN_JA_SAFE_ADJECTIVE_HEADS.get((words[0], words[1]))
    if not head:
        return None
    return head, ("extract_adjective_head",)


def _recover_en_ja_verb_head_variant(
    text: str,
    *,
    pos_raw: str,
) -> tuple[str, tuple[str, ...]] | None:
    lowered_pos = str(pos_raw or "").strip().lower()
    if "verb" not in lowered_pos:
        return None
    normalized = sanitize_dictionary_gloss(text).lower()
    if normalized.startswith("to "):
        normalized = normalized[3:].strip()
    if normalized.startswith("be able to "):
        return "able", ("extract_ability_head",)
    words = [token for token in normalized.split(" ") if token]
    if len(words) != 2:
        return None
    head, tail = words
    if not _EN_JA_WORD_RE.fullmatch(head):
        return None
    if tail not in _EN_JA_VERB_OBJECT_PLACEHOLDERS:
        return None
    return head, ("extract_verb_head",)


def _recover_en_ja_quantity_head_variant(
    text: str,
) -> tuple[str, tuple[str, ...]] | None:
    fragments = _split_top_level_fragments(text, separator=",")
    for fragment in fragments:
        words = [token for token in sanitize_dictionary_gloss(fragment).lower().split(" ") if token]
        if len(words) != 3:
            continue
        if tuple(words[:2]) not in {("there", "are"), ("there", "is")}:
            continue
        candidate = words[-1]
        if candidate in _EN_JA_SAFE_QUANTITY_HEADS:
            return candidate, ("extract_quantity_head",)
    return None


def _recover_en_ja_trailing_qualifier_head_variant(
    text: str,
) -> tuple[str, tuple[str, ...]] | None:
    words = [token for token in sanitize_dictionary_gloss(text).lower().split(" ") if token]
    if len(words) != 3:
        return None
    if words[1] != "in" or words[2] not in _EN_JA_TRAILING_HEAD_QUALIFIERS:
        return None
    if not _EN_JA_WORD_RE.fullmatch(words[0]):
        return None
    return words[0], ("extract_trailing_qualifier_head",)


def _recover_en_ja_admin_division_head_variant(
    text: str,
) -> tuple[str, tuple[str, ...]] | None:
    normalized = sanitize_dictionary_gloss(text).lower()
    words = [token for token in normalized.split(" ") if token]
    if len(words) < 4:
        return None
    if "including" not in words and not any(token.isdigit() for token in words):
        return None
    for token in words:
        if not _EN_JA_WORD_RE.fullmatch(token):
            continue
        singular = _singularize_en_ja_simple_plural(token)
        if singular in _EN_JA_ADMIN_DIVISION_HEADS:
            return singular, ("extract_admin_division_head",)
    return None


def _singularize_en_ja_simple_plural(word: str) -> str:
    text = str(word or "").strip().lower()
    if len(text) > 3 and text.endswith("ies"):
        return text[:-3] + "y"
    if len(text) > 3 and text.endswith("es") and text[:-2] in _EN_JA_ADMIN_DIVISION_HEADS:
        return text[:-2]
    if len(text) > 2 and text.endswith("s") and not text.endswith("ss"):
        singular = text[:-1]
        if singular in _EN_JA_ADMIN_DIVISION_HEADS:
            return singular
    return text


def _collect_entry_glosses(entries: Sequence[JmdictEntryRecord]) -> list[str]:
    glosses: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        for gloss in entry.glosses:
            cleaned = sanitize_dictionary_gloss(gloss)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            glosses.append(cleaned)
    return glosses


def _resolve_entry_pos_raw(entries: Sequence[JmdictEntryRecord]) -> str:
    values: list[str] = []
    for entry in entries:
        for pos in entry.pos_values:
            text = str(pos or "").strip()
            if text and text not in values:
                values.append(text)
    return "|".join(values)


def _select_entries_for_reading(
    *,
    entries: Sequence[JmdictEntryRecord],
    target: str,
    reading: str,
) -> list[JmdictEntryRecord]:
    normalized_reading = normalize_reading(reading, language_tag="ja")
    if not normalized_reading:
        return []
    matched: list[JmdictEntryRecord] = []
    for entry in entries:
        surface_forms = set(entry.kanji_forms) | set(entry.kana_forms)
        if target not in surface_forms:
            continue
        if _entry_matches_reading(entry, normalized_reading=normalized_reading):
            matched.append(entry)
    return matched


def _entry_matches_reading(entry: JmdictEntryRecord, *, normalized_reading: str) -> bool:
    for kana in entry.kana_forms:
        if normalize_reading(kana, language_tag="ja") == normalized_reading:
            return True
    return False


def _build_matched_script_forms(
    *,
    target: str,
    reading: str,
    entries: Sequence[JmdictEntryRecord],
    fallback: Optional[Mapping[str, str]],
) -> Optional[dict[str, str]]:
    forms: dict[str, str] = {}
    if contains_kanji(target):
        forms["kanji"] = target
    else:
        for entry in entries:
            if entry.kanji_forms:
                forms["kanji"] = entry.kanji_forms[0]
                break
    normalized_kana = normalize_reading(reading, language_tag="ja")
    if normalized_kana:
        forms["kana"] = normalized_kana
        romaji = kana_to_romaji(normalized_kana)
        if romaji:
            forms["romaji"] = romaji
    return merge_script_forms(forms or None, _normalize_script_forms_map(fallback))


def _resolve_target_word_package(
    *,
    target: str,
    language_pair: str,
    source_dict: str,
    package_hint: Optional[Mapping[str, object]],
    discovered_script_forms: Optional[Mapping[str, str]],
) -> Optional[dict[str, object]]:
    language_tag = resolve_language_tag_from_pair(language_pair)
    normalized_hint = normalize_word_package(
        package_hint,
        fallback_surface=target,
        fallback_language_tag=language_tag,
        fallback_provider="frequency",
    )
    if normalized_hint is None:
        return None
    normalized_hint_script_forms = _normalize_script_forms_map(normalized_hint.get("script_forms"))
    merged_forms = merge_script_forms(
        normalized_hint_script_forms,
        discovered_script_forms,
    )
    merged_word_package = dict(normalized_hint)
    if merged_forms is not None:
        merged_word_package["script_forms"] = merged_forms
    if not str(merged_word_package.get("reading") or "").strip():
        kana = str((merged_forms or {}).get("kana", "")).strip()
        if kana:
            merged_word_package["reading"] = kana
    return normalize_word_package(
        merged_word_package,
        fallback_surface=target,
        fallback_language_tag=language_tag,
        fallback_provider=source_dict,
    )


def _resolve_word_package_script_forms(
    word_package: Optional[Mapping[str, object]],
    *,
    fallback: Optional[Mapping[str, str]],
) -> Optional[dict[str, str]]:
    package_forms = None
    if isinstance(word_package, Mapping):
        raw_package_forms = word_package.get("script_forms")
        if isinstance(raw_package_forms, Mapping):
            package_forms = _normalize_script_forms_map(raw_package_forms)
    return merge_script_forms(package_forms, fallback)


def _normalize_script_forms_map(value: object) -> Optional[dict[str, str]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, str] = {}
    for key, raw in dict(value).items():
        script = str(key or "").strip().lower()
        text = str(raw or "").strip()
        if not script or not text:
            continue
        normalized[script] = text
    return normalized or None


def _normalize_en_ja_pos(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return text.split("|", 1)[0].strip()


def _has_en_ja_content_pos(value: object) -> bool:
    normalized = _normalize_en_ja_pos(value)
    return normalized in _EN_JA_CONTENT_POS_VALUES


def _build_filters(
    config: EnJaRulegenConfig,
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


DEFAULT_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "while",
    "since",
    "for",
    "to",
    "of",
    "in",
    "on",
    "at",
    "by",
    "with",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "am",
    "i",
    "me",
    "my",
    "you",
    "your",
    "he",
    "she",
    "it",
    "they",
    "them",
    "we",
    "us",
    "this",
    "that",
    "these",
    "those",
    "here",
    "there",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "do",
    "does",
    "did",
    "done",
    "have",
    "has",
    "had",
    "will",
    "would",
    "can",
    "could",
    "shall",
    "should",
    "may",
    "might",
    "must",
    "not",
    "no",
    "yes",
}
