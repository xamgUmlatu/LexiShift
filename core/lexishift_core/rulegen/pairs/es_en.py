from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import load_freedict_glosses_ordered
from lexishift_core.rulegen.generation import (
    CandidateFilter,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    SimpleSignalProvider,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    LengthFilter,
    NonEmptyFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
)
from lexishift_core.scoring.weighting import GlossDecay

DEFAULT_SPANISH_STOPWORDS = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "de",
    "del",
    "a",
    "al",
    "y",
    "o",
    "pero",
    "en",
    "con",
    "por",
    "para",
}


@dataclass(frozen=True)
class EsEnRulegenConfig:
    freedict_en_es_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    language_pair: str = "es-en"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()
    enable_punctuation_filter: bool = True
    enable_stopword_filter: bool = True
    enable_length_filter: bool = True
    min_source_length: int = 2
    max_source_length: Optional[int] = None
    stopwords: Optional[set[str]] = None
    allow_hyphen: bool = True


def build_es_en_pipeline(config: EsEnRulegenConfig) -> RuleGenerationPipeline:
    mapping = config.gloss_mapping or load_freedict_glosses_ordered(
        config.freedict_en_es_path,
        target_lang="es",
    )
    source = FreedictCandidateSource(
        mapping=mapping,
        source_dict="freedict_en_es",
        source_type="translation",
    )
    normalizers = [BasicStringNormalizer()]

    def gloss_decay_weight(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    signal_provider = SimpleSignalProvider(
        dict_priorities={"freedict_en_es": config.dict_priority},
        frequency_provider=gloss_decay_weight,
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=[],
        filters=_build_filters(config),
        scorer=RuleScorer(),
        signal_provider=signal_provider,
    )


def generate_es_en_results(
    targets: Iterable[str],
    *,
    config: EsEnRulegenConfig,
) -> list[RuleGenerationResult]:
    pipeline = build_es_en_pipeline(config)
    rule_config = RuleGenerationConfig(
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        tags=("translation", "freedict_en_es"),
    )
    return pipeline.generate_results(targets, config=rule_config)


def generate_es_en_rules(
    targets: Iterable[str],
    *,
    config: EsEnRulegenConfig,
):
    return [result.rule for result in generate_es_en_results(targets, config=config)]


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


def _build_filters(config: EsEnRulegenConfig) -> list[CandidateFilter]:
    filters: list[CandidateFilter] = [NonEmptyFilter()]
    if not config.allow_multiword_glosses:
        filters.append(SingleWordFilter(allow_hyphen=config.allow_hyphen))
    if config.enable_length_filter:
        filters.append(
            LengthFilter(min_length=config.min_source_length, max_length=config.max_source_length)
        )
    if config.enable_punctuation_filter:
        filters.append(PunctuationFilter())
    if config.enable_stopword_filter:
        stopwords = config.stopwords or DEFAULT_SPANISH_STOPWORDS
        filters.append(StopwordFilter(stopwords=stopwords))
    return filters
