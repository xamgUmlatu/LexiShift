from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.dict_loaders import load_freedict_tei_glosses_ordered
from lexishift_core.rule_generation import (
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    SimpleSignalProvider,
)
from lexishift_core.rule_generation_ja_en import DEFAULT_STOPWORDS
from lexishift_core.rule_generation_utils import (
    BasicStringNormalizer,
    InflectionArtifactFilter,
    InflectionVariantExpander,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
)
from lexishift_core.weighting import GlossDecay


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


@dataclass(frozen=True)
class EnDeRulegenConfig:
    freedict_de_en_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    language_pair: str = "en-de"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
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
    inflection_suffixes: Sequence[str] = ("s", "es", "ed", "ing")
    allow_hyphen: bool = True


def build_en_de_pipeline(config: EnDeRulegenConfig) -> RuleGenerationPipeline:
    mapping = config.gloss_mapping or load_freedict_tei_glosses_ordered(
        config.freedict_de_en_path,
        target_lang="en",
    )
    source = FreedictCandidateSource(
        mapping=mapping,
        source_dict="freedict_de_en",
        source_type="translation",
    )
    normalizers = [BasicStringNormalizer()]
    expanders = []
    if config.include_variants:
        expanders.append(InflectionVariantExpander(should_expand=_should_expand_english))

    def variant_penalty_provider(candidate: RuleCandidate) -> float:
        return config.variant_penalty if candidate.metadata.get("variant") else 0.0

    def gloss_decay_weight(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    signal_provider = SimpleSignalProvider(
        dict_priorities={"freedict_de_en": config.dict_priority},
        frequency_provider=gloss_decay_weight,
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
        mapping: Mapping[str, Sequence[str]],
        source_dict: str,
        source_type: str,
    ) -> None:
        self._mapping = mapping
        self._source_dict = source_dict
        self._source_type = source_type

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            sources = list(self._mapping.get(target, []))
            total = len(sources)
            for index, source in enumerate(sources):
                yield RuleCandidate(
                    source_phrase=str(source),
                    replacement=str(target),
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata={
                        "gloss_index": index,
                        "gloss_total": total,
                    },
                )


def _build_filters(config: EnDeRulegenConfig, mapping: Mapping[str, Sequence[str]]) -> list:
    filters = [NonEmptyFilter()]
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
            base_forms.add(str(gloss).strip().lower())
    return base_forms
