from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.replacement.inflect import FORM_PLURAL, InflectionSpec
from lexishift_core.resources.dict_loaders import (
    FreedictGlossRecord,
    load_freedict_gloss_records_ordered,
)
from lexishift_core.rulegen.generation import (
    CandidateFilter,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    SimpleSignalProvider,
    build_pos_match_provider,
)
from lexishift_core.rulegen.pairs.ja_en import DEFAULT_STOPWORDS
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionArtifactFilter,
    InflectionVariantExpander,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
    sanitize_dictionary_gloss,
)
from lexishift_core.scoring.weighting import GlossDecay


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


@dataclass(frozen=True)
class EnDeRulegenConfig:
    freedict_de_en_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    language_pair: str = "en-de"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    max_definitions_per_target: int = 3
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


def build_en_de_pipeline(config: EnDeRulegenConfig) -> RuleGenerationPipeline:
    records_by_target = _resolve_gloss_records(config)
    mapping = _records_to_gloss_mapping(records_by_target)
    source = FreedictCandidateSource(
        records_by_target=records_by_target,
        source_dict="freedict_de_en",
        source_type="translation",
        word_packages_by_target=config.word_packages_by_target,
    )
    normalizers = [BasicStringNormalizer()]
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

    def gloss_decay_weight(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    signal_provider = SimpleSignalProvider(
        dict_priorities={"freedict_de_en": config.dict_priority},
        frequency_provider=gloss_decay_weight,
        pos_match_provider=build_pos_match_provider(),
        variant_penalty_provider=variant_penalty_provider,
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=expanders,
        filters=_build_filters(config, mapping),
        scorer=RuleScorer(),
        signal_provider=signal_provider,
    )


def generate_en_de_results(
    targets: Iterable[str],
    *,
    config: EnDeRulegenConfig,
) -> list[RuleGenerationResult]:
    pipeline = build_en_de_pipeline(config)
    rule_config = RuleGenerationConfig(
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        max_definitions_per_target=config.max_definitions_per_target,
        tags=("translation", "freedict_de_en"),
    )
    return pipeline.generate_results(targets, config=rule_config)


def generate_en_de_rules(
    targets: Iterable[str],
    *,
    config: EnDeRulegenConfig,
):
    return [result.rule for result in generate_en_de_results(targets, config=config)]


class FreedictCandidateSource:
    def __init__(
        self,
        *,
        records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
        source_dict: str,
        source_type: str,
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._word_packages_by_target = word_packages_by_target or {}

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
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
            for index, entry in enumerate(entries):
                dictionary_pos = normalize_pos_component(
                    entry.pos_raw,
                    language_pair=language_pair,
                    source_provider=self._source_dict,
                    source_kind="dictionary",
                    source_profile="freedict",
                )
                metadata: dict[str, object] = {
                    "gloss_index": index,
                    "gloss_total": total,
                }
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
    return load_freedict_gloss_records_ordered(
        config.freedict_de_en_path,
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
        sanitized = sanitize_dictionary_gloss(record.translation)
        if not sanitized:
            continue
        normalized_pos = str(record.pos_raw or "").strip()
        existing_index = seen.get(sanitized)
        if existing_index is None:
            cleaned.append(FreedictGlossRecord(translation=sanitized, pos_raw=normalized_pos))
            seen[sanitized] = len(cleaned) - 1
            continue
        if not cleaned[existing_index].pos_raw and normalized_pos:
            cleaned[existing_index] = FreedictGlossRecord(
                translation=sanitized,
                pos_raw=normalized_pos,
            )
    return cleaned
