from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import (
    load_jmdict_glosses_and_script_forms,
)
from lexishift_core.frequency import (
    FrequencyLexicon,
    FrequencySourceConfig,
    build_frequency_provider,
    load_frequency_lexicon,
)
from lexishift_core.rulegen.generation import (
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    SimpleSignalProvider,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionVariantExpander,
    InflectionArtifactFilter,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
)
from lexishift_core.scoring.weighting import GlossDecay


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


@dataclass(frozen=True)
class JaEnRulegenConfig:
    jmdict_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    script_forms_by_target: Optional[Mapping[str, Mapping[str, str]]] = None
    language_pair: str = "en-ja"
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
    frequency_config: Optional[FrequencySourceConfig] = None
    frequency_lexicon: Optional[FrequencyLexicon] = None
    frequency_provider: Optional[Callable[[RuleCandidate], float]] = None
    embedding_provider: Optional[Callable[[RuleCandidate], Optional[float]]] = None


def build_ja_en_pipeline(config: JaEnRulegenConfig) -> RuleGenerationPipeline:
    script_forms_by_target: Mapping[str, Mapping[str, str]] = (
        config.script_forms_by_target or {}
    )
    if config.gloss_mapping is not None:
        mapping = config.gloss_mapping
    else:
        mapping, discovered_forms = load_jmdict_glosses_and_script_forms(config.jmdict_path)
        if not script_forms_by_target:
            script_forms_by_target = discovered_forms
    source = JmdictCandidateSource(
        mapping=mapping,
        source_dict="jmdict",
        source_type="translation",
        script_forms_by_target=script_forms_by_target,
    )
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
        filters=_build_filters(config, mapping),
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
    def __init__(
        self,
        *,
        mapping: Mapping[str, Sequence[str]],
        source_dict: str,
        source_type: str,
        script_forms_by_target: Optional[Mapping[str, Mapping[str, str]]] = None,
    ) -> None:
        self._mapping = mapping
        self._source_dict = source_dict
        self._source_type = source_type
        self._script_forms_by_target = script_forms_by_target or {}

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            sources = list(self._mapping.get(target, []))
            total = len(sources)
            script_forms = self._script_forms_by_target.get(target)
            for index, source in enumerate(sources):
                metadata = {
                    "gloss_index": index,
                    "gloss_total": total,
                }
                if isinstance(script_forms, Mapping):
                    normalized_script_forms = {
                        str(key): str(value)
                        for key, value in dict(script_forms).items()
                        if str(key).strip() and str(value).strip()
                    }
                    if normalized_script_forms:
                        metadata["script_forms"] = normalized_script_forms
                yield RuleCandidate(
                    source_phrase=str(source),
                    replacement=str(target),
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata=metadata,
                )


def _build_filters(config: JaEnRulegenConfig, mapping: Mapping[str, Sequence[str]]) -> list:
    filters = [NonEmptyFilter()]
    if not config.allow_multiword_glosses:
        filters.append(SingleWordFilter(allow_hyphen=config.allow_hyphen))
    if config.enable_length_filter:
        filters.append(LengthFilter(min_length=config.min_source_length, max_length=config.max_source_length))
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
