from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
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
from lexishift_core.rulegen.pairs.ja_en import DEFAULT_STOPWORDS
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionArtifactFilter,
    PairedInflectionVariantExpander,
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


_SPANISH_NOUN_WORD_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$")


def _resolve_spanish_target_surface(candidate: RuleCandidate, form: str) -> Optional[str]:
    if form != "plural":
        return None
    return _pluralize_spanish_noun(candidate.replacement)


def _pluralize_spanish_noun(word: str) -> Optional[str]:
    text = str(word or "").strip()
    if not text or not _SPANISH_NOUN_WORD_RE.match(text):
        return None
    lowered = text.lower()
    if lowered.endswith("z"):
        return text[:-1] + "ces"
    if lowered.endswith(("a", "e", "i", "o", "u", "á", "é", "ó")):
        return text + "s"
    if lowered.endswith(("í", "ú")):
        return text + "es"
    if lowered.endswith(("s", "x")):
        return None
    return text + "es"


@dataclass(frozen=True)
class EnEsRulegenConfig:
    freedict_es_en_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    language_pair: str = "en-es"
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


def build_en_es_pipeline(config: EnEsRulegenConfig) -> RuleGenerationPipeline:
    mapping = config.gloss_mapping or load_freedict_glosses_ordered(
        config.freedict_es_en_path,
        target_lang="en",
    )
    source = FreedictCandidateSource(
        mapping=mapping,
        source_dict="freedict_es_en",
        source_type="translation",
    )
    normalizers = [BasicStringNormalizer()]
    expanders = []
    if config.include_variants:
        expanders.append(
            PairedInflectionVariantExpander(
                should_expand=_should_expand_english,
                target_surface_resolver=_resolve_spanish_target_surface,
            )
        )

    def variant_penalty_provider(candidate: RuleCandidate) -> float:
        return config.variant_penalty if candidate.metadata.get("variant") else 0.0

    def gloss_decay_weight(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    signal_provider = SimpleSignalProvider(
        dict_priorities={"freedict_es_en": config.dict_priority},
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


def generate_en_es_results(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
) -> list[RuleGenerationResult]:
    pipeline = build_en_es_pipeline(config)
    rule_config = RuleGenerationConfig(
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        tags=("translation", "freedict_es_en"),
    )
    return pipeline.generate_results(targets, config=rule_config)


def generate_en_es_rules(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
):
    return [result.rule for result in generate_en_es_results(targets, config=config)]


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


def _build_filters(
    config: EnEsRulegenConfig,
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
            base_forms.add(str(gloss).strip().lower())
    return base_forms
