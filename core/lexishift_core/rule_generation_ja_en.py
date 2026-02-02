from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from lexishift_core.dict_loaders import load_jmdict_glosses
from lexishift_core.frequency import (
    FrequencyLexicon,
    FrequencySourceConfig,
    build_frequency_provider,
    load_frequency_lexicon,
)
from lexishift_core.rule_generation import (
    MappingCandidateSource,
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
)


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


@dataclass(frozen=True)
class JaEnRulegenConfig:
    jmdict_path: Path
    language_pair: str = "en-ja"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    include_variants: bool = True
    variant_penalty: float = 0.2
    frequency_config: Optional[FrequencySourceConfig] = None
    frequency_lexicon: Optional[FrequencyLexicon] = None
    frequency_provider: Optional[Callable[[RuleCandidate], float]] = None
    embedding_provider: Optional[Callable[[RuleCandidate], Optional[float]]] = None


def build_ja_en_pipeline(config: JaEnRulegenConfig) -> RuleGenerationPipeline:
    mapping = load_jmdict_glosses(config.jmdict_path)
    source = MappingCandidateSource(mapping=mapping, source_dict="jmdict", source_type="translation")
    normalizers = [BasicStringNormalizer()]
    expanders = []
    if config.include_variants:
        expanders.append(InflectionVariantExpander(should_expand=_should_expand_english))

    def variant_penalty_provider(candidate: RuleCandidate) -> float:
        return config.variant_penalty if candidate.metadata.get("variant") else 0.0

    frequency_provider = config.frequency_provider
    if frequency_provider is None:
        if config.frequency_lexicon is not None:
            frequency_provider = build_frequency_provider(config.frequency_lexicon)
        elif config.frequency_config is not None:
            lexicon = load_frequency_lexicon(config.frequency_config)
            frequency_provider = build_frequency_provider(lexicon)

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
        filters=[NonEmptyFilter()],
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
