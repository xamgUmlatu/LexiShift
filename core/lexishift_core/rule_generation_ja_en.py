from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.dict_loaders import load_jmdict_glosses_ordered
from lexishift_core.frequency import (
    FrequencyLexicon,
    FrequencySourceConfig,
    build_frequency_provider,
    load_frequency_lexicon,
)
from lexishift_core.rule_generation import (
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    SimpleSignalProvider,
)
from lexishift_core.rule_generation_utils import (
    BasicStringNormalizer,
    InflectionVariantExpander,
    NonEmptyFilter,
    SingleWordFilter,
)
from lexishift_core.weighting import GlossDecay


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


@dataclass(frozen=True)
class JaEnRulegenConfig:
    jmdict_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    language_pair: str = "en-ja"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    include_variants: bool = True
    variant_penalty: float = 0.2
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()
    frequency_config: Optional[FrequencySourceConfig] = None
    frequency_lexicon: Optional[FrequencyLexicon] = None
    frequency_provider: Optional[Callable[[RuleCandidate], float]] = None
    embedding_provider: Optional[Callable[[RuleCandidate], Optional[float]]] = None


def build_ja_en_pipeline(config: JaEnRulegenConfig) -> RuleGenerationPipeline:
    mapping = config.gloss_mapping or load_jmdict_glosses_ordered(config.jmdict_path)
    source = JmdictCandidateSource(mapping=mapping, source_dict="jmdict", source_type="translation")
    normalizers = [BasicStringNormalizer()]
    expanders = []
    if config.include_variants:
        expanders.append(InflectionVariantExpander(should_expand=_should_expand_english))

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
        dict_priorities={"jmdict": config.dict_priority},
        frequency_provider=frequency_provider,
        variant_penalty_provider=variant_penalty_provider,
        embedding_provider=config.embedding_provider,
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=expanders,
        filters=_build_filters(config),
        scorer=RuleScorer(),
        signal_provider=signal_provider,
    )


def generate_ja_en_results(
    targets: Iterable[str],
    *,
    config: JaEnRulegenConfig,
) -> list[RuleGenerationResult]:
    pipeline = build_ja_en_pipeline(config)
    rule_config = RuleGenerationConfig(
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        tags=("translation", "jmdict"),
    )
    return pipeline.generate_results(targets, config=rule_config)


def generate_ja_en_rules(
    targets: Iterable[str],
    *,
    config: JaEnRulegenConfig,
):
    return [result.rule for result in generate_ja_en_results(targets, config=config)]


class JmdictCandidateSource:
    def __init__(self, *, mapping: dict[str, set[str]], source_dict: str, source_type: str) -> None:
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


def _build_filters(config: JaEnRulegenConfig) -> list:
    filters = [NonEmptyFilter()]
    if not config.allow_multiword_glosses:
        filters.append(SingleWordFilter())
    return filters
