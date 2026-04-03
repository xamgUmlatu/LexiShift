from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.frequency.providers import (
    SqliteFrequencyProvider,
    SqliteFrequencyProviderConfig,
)
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig
from lexishift_core.replacement.inflect import FORM_PLURAL, InflectionSpec
from lexishift_core.resources.dict_loaders import (
    FreedictGlossRecord,
    load_freedict_gloss_records_ordered,
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
from lexishift_core.rulegen.pairs.en_ja import DEFAULT_STOPWORDS
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
)
from lexishift_core.rulegen.semantic_demotion import (
    resolve_generic_gloss_demotion,
    resolve_pair_generic_gloss_demotions,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionArtifactFilter,
    InflectionVariantExpander,
    LeadingEnglishInfinitiveNormalizer,
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
        default_factory=lambda: resolve_pair_generic_gloss_demotions("en-de")
    )
    enable_exact_gloss_demotions: bool = False
    enable_source_frequency_prior: bool = False
    source_frequency_db_path: Optional[Path] = None


def _extract_source_frequency_prior(metadata: Mapping[str, object]) -> float:
    raw = metadata.get("source_frequency_prior")
    if isinstance(raw, bool):
        return 1.0 if raw else 0.0
    if isinstance(raw, (int, float)):
        return max(0.0, min(1.0, float(raw)))
    return 0.0


@dataclass(frozen=True)
class EnDeSourceFrequencyRankingMechanism:
    fallback: DictionaryEntryOrderRankingMechanism = field(
        default_factory=DictionaryEntryOrderRankingMechanism
    )
    prior_weight: float = 0.0

    def score(self, candidate: CandidateRankingContext) -> float:
        base_score = self.fallback.score(candidate)
        if self.prior_weight <= 0.0:
            return base_score
        prior = _extract_source_frequency_prior(candidate.metadata)
        return base_score + (prior * self.prior_weight)

    def bucket_key(self, candidate: CandidateRankingContext) -> str:
        return self.fallback.bucket_key(candidate)


def build_en_de_pipeline(
    config: EnDeRulegenConfig,
    *,
    source_frequency_provider: Optional[Callable[[str], float]] = None,
) -> RuleGenerationPipeline:
    records_by_target = _resolve_gloss_records(config)
    mapping = _records_to_gloss_mapping(records_by_target)
    source = FreedictCandidateSource(
        records_by_target=records_by_target,
        source_dict="freedict_de_en",
        source_type="translation",
        word_packages_by_target=config.word_packages_by_target,
        generic_gloss_demotions=(
            config.generic_gloss_demotions if config.enable_exact_gloss_demotions else {}
        ),
        source_frequency_provider=source_frequency_provider,
    )
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

    def gloss_decay_weight(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    frequency_provider = gloss_decay_weight
    if source_frequency_provider is not None:

        def frequency_provider(candidate: RuleCandidate) -> float:
            return _extract_source_frequency_prior(candidate.metadata) * gloss_decay_weight(
                candidate
            )

    signal_provider = SimpleSignalProvider(
        dict_priorities={"freedict_de_en": config.dict_priority},
        frequency_provider=frequency_provider,
        pos_match_provider=build_optional_pos_match_provider(config.scoring.pos_match),
        variant_penalty_provider=variant_penalty_provider,
    )
    ranking_mechanism = (
        EnDeSourceFrequencyRankingMechanism(
            prior_weight=float(config.scoring.weights.frequency_weight),
        )
        if source_frequency_provider is not None
        else DictionaryEntryOrderRankingMechanism()
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=expanders,
        filters=_build_filters(config, mapping),
        scorer=RuleScorer(weights=config.scoring.weights),
        signal_provider=signal_provider,
        ranking_mechanism=ranking_mechanism,
    )


def generate_en_de_results(
    targets: Iterable[str],
    *,
    config: EnDeRulegenConfig,
) -> list[RuleGenerationResult]:
    source_frequency_store: Optional[SqliteFrequencyProvider] = None
    source_frequency_provider: Optional[Callable[[str], float]] = None
    if config.enable_source_frequency_prior and config.source_frequency_db_path is not None:
        source_frequency_store = SqliteFrequencyProvider(
            SqliteFrequencyProviderConfig(
                sqlite=SqliteFrequencyConfig(path=config.source_frequency_db_path)
            )
        )

        def source_frequency_provider(source_phrase: str) -> float:
            return source_frequency_store.weight_phrase(str(source_phrase), reducer="avg")

    try:
        pipeline = build_en_de_pipeline(
            config,
            source_frequency_provider=source_frequency_provider,
        )
        rule_config = RuleGenerationConfig(
            language_pair=config.language_pair,
            confidence_threshold=config.confidence_threshold,
            max_definitions_per_target=config.max_definitions_per_target,
            max_rules_per_target=config.max_rules_per_target,
            semantic_demotion_scale=config.semantic_demotion_scale,
            tags=("translation", "freedict_de_en"),
        )
        return pipeline.generate_results(targets, config=rule_config)
    finally:
        if source_frequency_store is not None:
            source_frequency_store.close()


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
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
        source_frequency_provider: Optional[Callable[[str], float]] = None,
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._source_frequency_provider = source_frequency_provider

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
                demotion = resolve_generic_gloss_demotion(
                    entry.translation,
                    demotions=self._generic_gloss_demotions,
                )
                if demotion > 0.0:
                    metadata["semantic_demotion"] = demotion
                    metadata["semantic_demotion_reason"] = "generic_gloss"
                if self._source_frequency_provider is not None:
                    metadata["source_frequency_prior"] = self._source_frequency_provider(
                        entry.translation
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
            cleaned.append(
                FreedictGlossRecord(
                    translation=sanitized,
                    pos_raw=normalized_pos,
                    metadata=dict(record.metadata),
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
