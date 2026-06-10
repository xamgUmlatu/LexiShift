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
from lexishift_core.resources.dict_loaders import FreedictGlossRecord, TranslationGlossRecord
from lexishift_core.rulegen.generation import (
    CandidateNormalizer,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    RuleScoringConfig,
    SimpleSignalProvider,
    VariantExpander,
    build_optional_pos_match_provider,
)
from lexishift_core.rulegen.pairs.en_de_gloss_processing import (
    _apply_kaikki_policy_overlay,
    _expand_en_de_gloss_variants,
    _extract_kaikki_family_names,
    _extract_source_frequency_prior,
    _normalize_competition_penalty,
    _resolve_cleaner_later_competition,
    _resolve_en_de_kaikki_register_demotion,
    _resolve_en_de_marked_sense_demotion,
    _resolve_sense_defaultness_competition,
    _resolve_sense_representative_indexes,
)
from lexishift_core.rulegen.pairs.en_de_live_source import (
    FreedictCandidateSource,
    _build_filters,
    _build_gloss_base_forms,
    _collect_sanitized_gloss_records,
    _records_to_gloss_mapping,
    _resolve_gloss_records,
    _resolve_reverse_gloss_records,
    _should_expand_english,
)
from lexishift_core.rulegen.pairs.en_es_support import build_reverse_lookup as _build_reverse_lookup
from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
    ReverseCheckScoringConfig,
)
from lexishift_core.rulegen.semantic_demotion import resolve_pair_generic_gloss_demotions
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionVariantExpander,
    LeadingEnglishInfinitiveNormalizer,
)
from lexishift_core.scoring.weighting import GlossDecay

_COMPAT_REEXPORTS = (
    _apply_kaikki_policy_overlay,
    _build_gloss_base_forms,
    _collect_sanitized_gloss_records,
    _expand_en_de_gloss_variants,
    _extract_kaikki_family_names,
    _normalize_competition_penalty,
    _resolve_cleaner_later_competition,
    _resolve_en_de_kaikki_register_demotion,
    _resolve_en_de_marked_sense_demotion,
    _resolve_sense_defaultness_competition,
    _resolve_sense_representative_indexes,
)


@dataclass(frozen=True)
class EnDeRulegenConfig:
    translation_dict_path: Path
    reverse_translation_dict_path: Optional[Path] = None
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    language_pair: str = "en-de"
    source_dict_id: str = "freedict_de_en"
    reverse_source_dict_id: Optional[str] = None
    dictionary_pos_source_profile: str = "freedict"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    interleave_definition_groups: bool = False
    sense_representative_selection: bool = False
    semantic_demotion_scale: float = 1.0
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    include_variants: bool = True
    variant_penalty: float = 0.2
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
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
    cleaner_later_competition_penalty: float = 0.0
    sense_defaultness_competition_penalty: float = 0.0
    kaikki_policy: "EnDeKaikkiPolicyConfig" = field(
        default_factory=lambda: EnDeKaikkiPolicyConfig()
    )


@dataclass(frozen=True)
class EnDeKaikkiPolicyConfig:
    enable_shadow_metadata: bool = True
    enable_live_demotion: bool = False
    enable_register_demotion: bool = False
    late_sense_clean_earlier_competition_penalty: float = 0.0
    risk_families: tuple[str, ...] = (
        "math_geometry",
        "government_law",
        "hunting_fishing_tools",
        "register_region",
        "abbreviation_ellipsis_formof",
    )


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
    reverse_records_by_source = (
        _resolve_reverse_gloss_records(config)
        if bool(config.reverse_check.enabled) or config.reverse_gloss_records_by_source is not None
        else None
    )
    reverse_lookup = (
        _build_reverse_lookup(reverse_records_by_source)
        if reverse_records_by_source is not None
        else None
    )
    mapping = _records_to_gloss_mapping(records_by_target)
    source = FreedictCandidateSource(
        records_by_target=records_by_target,
        source_dict=config.source_dict_id,
        source_type="translation",
        dictionary_pos_source_profile=config.dictionary_pos_source_profile,
        word_packages_by_target=config.word_packages_by_target,
        reverse_lookup=reverse_lookup,
        reverse_source_dict_id=config.reverse_source_dict_id,
        generic_gloss_demotions=(
            config.generic_gloss_demotions if config.enable_exact_gloss_demotions else {}
        ),
        source_frequency_provider=source_frequency_provider,
        cleaner_later_competition_penalty=config.cleaner_later_competition_penalty,
        sense_representative_selection=config.sense_representative_selection,
        sense_defaultness_competition_penalty=config.sense_defaultness_competition_penalty,
        kaikki_policy=config.kaikki_policy,
    )
    normalizers: list[CandidateNormalizer] = [
        BasicStringNormalizer(),
        LeadingEnglishInfinitiveNormalizer(),
    ]
    expanders: list[VariantExpander] = []
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
            fallback=DictionaryEntryOrderRankingMechanism(reverse_check=config.reverse_check),
            prior_weight=float(config.scoring.weights.frequency_weight),
        )
        if source_frequency_provider is not None
        else DictionaryEntryOrderRankingMechanism(reverse_check=config.reverse_check)
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
            interleave_definition_groups=config.interleave_definition_groups,
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
