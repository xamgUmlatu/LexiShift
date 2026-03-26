from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.pos.normalization import (
    CANONICAL_POS_ADPOSITION,
    CANONICAL_POS_CONJUNCTION,
    CANONICAL_POS_DETERMINER,
    CANONICAL_POS_NOUN,
    CANONICAL_POS_PRONOUN,
)
from lexishift_core.resources.dict_loaders import (
    FreedictGlossRecord,
    load_freedict_gloss_records_ordered,
)
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views
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
from lexishift_core.rulegen.ranking import (
    DictionaryEntryOrderRankingMechanism,
    ReverseCheckScoringConfig,
)
from lexishift_core.rulegen.pairs.en_ja import DEFAULT_STOPWORDS
from lexishift_core.rulegen.pairs.en_es_support import (
    apply_semantic_demotion as _apply_semantic_demotion,
    build_definition_bucket_key as _build_definition_bucket_key,
    build_gloss_provenance as _build_gloss_provenance,
    build_kaikki_policy_shadow_by_index as _build_kaikki_policy_shadow_by_index,
    build_reverse_lookup as _build_reverse_lookup,
    build_sense_provenance as _build_sense_provenance,
    build_target_provenance_by_index as _build_target_provenance_by_index,
    collect_sanitized_gloss_records as _collect_sanitized_gloss_records,
    extract_canonical_from_component as _extract_canonical_from_component,
    normalize_reverse_token as _normalize_reverse_token,
    normalize_reverse_token_with_pos as _normalize_reverse_token_with_pos,
    resolve_kaikki_policy_live_demotion as _resolve_kaikki_policy_live_demotion,
    resolve_kaikki_register_demotion as _resolve_kaikki_register_demotion,
    should_demote_shadowed_adverb as _should_demote_shadowed_adverb,
    should_shadow_interjection as _should_shadow_interjection,
)
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.semantic_demotion import (
    resolve_generic_gloss_demotion,
    resolve_pair_generic_gloss_demotions,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionArtifactFilter,
    LeadingEnglishInfinitiveNormalizer,
    PairedInflectionVariantExpander,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    sanitize_dictionary_gloss,
)
from lexishift_core.scoring.weighting import GlossDecay


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


_SPANISH_NOUN_WORD_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$")
_EN_ES_SINGLE_WORD_RE = re.compile(r"^[a-z0-9-]+$")
_EN_ES_MULTIWORD_RE = re.compile(r"^[a-z0-9-]+(?: [a-z0-9-]+){0,3}$")
_FUNCTION_WORD_CANONICALS = frozenset(
    {
        CANONICAL_POS_DETERMINER,
        CANONICAL_POS_PRONOUN,
        CANONICAL_POS_ADPOSITION,
        CANONICAL_POS_CONJUNCTION,
    }
)


def _resolve_spanish_target_surface(candidate: RuleCandidate, form: str) -> Optional[str]:
    if form != "plural":
        return None
    if _extract_target_pos_canonical(candidate) != CANONICAL_POS_NOUN:
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


def _extract_target_pos_canonical(candidate: RuleCandidate) -> str:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    pos = metadata.get("pos")
    if isinstance(pos, Mapping):
        target = pos.get("target")
        if isinstance(target, Mapping):
            canonical = str(target.get("canonical") or "").strip().lower()
            if canonical:
                return canonical
    return str(metadata.get("target_pos_canonical") or "").strip().lower()


def _extract_dictionary_pos_canonical(candidate: RuleCandidate) -> str:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    pos = metadata.get("pos")
    if isinstance(pos, Mapping):
        dictionary = pos.get("dictionary") or pos.get("source")
        if isinstance(dictionary, Mapping):
            canonical = str(dictionary.get("canonical") or "").strip().lower()
            if canonical:
                return canonical
    return str(metadata.get("dictionary_pos_canonical") or "").strip().lower()


def _candidate_allows_function_word_phrase(candidate: RuleCandidate) -> bool:
    return _extract_dictionary_pos_canonical(candidate) in _FUNCTION_WORD_CANONICALS


@dataclass(frozen=True)
class EnEsGlossShapeFilter:
    allow_hyphen: bool = True
    allow_multiword_glosses: bool = False

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = str(candidate.source_phrase or "").strip().lower()
        if not phrase:
            return False
        if not self.allow_hyphen and "-" in phrase:
            return False
        if self.allow_multiword_glosses or _candidate_allows_function_word_phrase(candidate):
            return bool(_EN_ES_MULTIWORD_RE.fullmatch(phrase))
        return bool(_EN_ES_SINGLE_WORD_RE.fullmatch(phrase))


@dataclass(frozen=True)
class EnEsStopwordFilter:
    stopwords: set[str]

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = str(candidate.source_phrase or "").strip().lower()
        if phrase not in self.stopwords:
            return True
        return _candidate_allows_function_word_phrase(candidate)


@dataclass(frozen=True)
class ShadowedInterjectionFilter:
    metadata_key: str = "interjection_shadowed"

    def accept(self, candidate: RuleCandidate) -> bool:
        metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
        return not bool(metadata.get(self.metadata_key))


@dataclass(frozen=True)
class EnEsKaikkiPolicyConfig:
    enable_shadow_metadata: bool = True
    enable_live_demotion: bool = False
    risk_families: tuple[str, ...] = (
        "math_geometry",
        "government_law",
        "hunting_fishing_tools",
        "register_region",
        "abbreviation_ellipsis_formof",
    )


@dataclass(frozen=True)
class EnEsRulegenConfig:
    freedict_es_en_path: Path
    reverse_freedict_en_es_path: Optional[Path] = None
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    language_pair: str = "en-es"
    source_dict_id: str = "freedict_es_en"
    reverse_source_dict_id: str = "freedict_en_es"
    dictionary_pos_source_profile: str = "freedict"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    interleave_definition_groups: bool = True
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
    inflection_suffixes: Sequence[str] = ("s", "es", "ed", "ing")
    allow_hyphen: bool = True
    generic_gloss_demotions: Mapping[str, float] = field(
        default_factory=lambda: resolve_pair_generic_gloss_demotions("en-es")
    )
    kaikki_policy: EnEsKaikkiPolicyConfig = field(default_factory=EnEsKaikkiPolicyConfig)


def build_en_es_pipeline(config: EnEsRulegenConfig) -> RuleGenerationPipeline:
    records_by_target = _resolve_gloss_records(config)
    reverse_records_by_source = _resolve_reverse_gloss_records(config)
    mapping = _records_to_gloss_mapping(records_by_target)
    source = FreedictCandidateSource(
        records_by_target=records_by_target,
        source_dict=config.source_dict_id,
        source_type="translation",
        reverse_records_by_source=reverse_records_by_source,
        reverse_source_dict=config.reverse_source_dict_id,
        word_packages_by_target=config.word_packages_by_target,
        generic_gloss_demotions=config.generic_gloss_demotions,
        dictionary_pos_source_profile=config.dictionary_pos_source_profile,
        kaikki_policy=config.kaikki_policy,
    )
    normalizers: list[CandidateNormalizer] = [
        BasicStringNormalizer(),
        LeadingEnglishInfinitiveNormalizer(),
    ]
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
        dict_priorities={config.source_dict_id: config.dict_priority},
        frequency_provider=gloss_decay_weight,
        pos_match_provider=build_optional_pos_match_provider(config.scoring.pos_match),
        variant_penalty_provider=variant_penalty_provider,
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=expanders,
        filters=_build_filters(config, mapping),
        scorer=RuleScorer(weights=config.scoring.weights),
        signal_provider=signal_provider,
        ranking_mechanism=DictionaryEntryOrderRankingMechanism(reverse_check=config.reverse_check),
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
        max_definitions_per_target=config.max_definitions_per_target,
        max_rules_per_target=config.max_rules_per_target,
        interleave_definition_groups=config.interleave_definition_groups,
        semantic_demotion_scale=config.semantic_demotion_scale,
        tags=("translation", config.source_dict_id),
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
        records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
        source_dict: str,
        source_type: str,
        reverse_records_by_source: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None,
        reverse_source_dict: str = "",
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
        dictionary_pos_source_profile: str = "freedict",
        kaikki_policy: Optional[EnEsKaikkiPolicyConfig] = None,
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._reverse_source_dict = str(reverse_source_dict or "").strip()
        self._reverse_lookup = (
            _build_reverse_lookup(reverse_records_by_source)
            if reverse_records_by_source is not None
            else None
        )
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._dictionary_pos_source_profile = str(dictionary_pos_source_profile or "").strip() or (
            "freedict"
        )
        self._kaikki_policy = kaikki_policy or EnEsKaikkiPolicyConfig()

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            target_reverse_norm = _normalize_reverse_token(target)
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
            dictionary_poses = [
                normalize_pos_component(
                    entry.pos_raw,
                    language_pair=language_pair,
                    source_provider=self._source_dict,
                    source_kind="dictionary",
                    source_profile=self._dictionary_pos_source_profile,
                )
                for entry in entries
            ]
            canonical_inventory = [
                _extract_canonical_from_component(component) for component in dictionary_poses
            ]
            dictionary_record_views_by_index: list[dict[str, object]] = []
            for entry in entries:
                if entry.metadata:
                    raw_record = dict(entry.metadata)
                    dictionary_record_views = build_kaikki_record_views(raw_record)
                    if dictionary_record_views:
                        dictionary_record_views_by_index.append({"kaikki": dictionary_record_views})
                        continue
                dictionary_record_views_by_index.append({})
            target_provenance_by_index = _build_target_provenance_by_index(
                target=target,
                entries=entries,
                canonical_inventory=canonical_inventory,
            )
            kaikkei_policy_shadow_by_index = (
                _build_kaikki_policy_shadow_by_index(
                    dictionary_record_views_by_index=dictionary_record_views_by_index,
                    canonical_inventory=canonical_inventory,
                    risk_families=self._kaikki_policy.risk_families,
                )
                if self._kaikki_policy.enable_shadow_metadata
                else [{} for _ in entries]
            )
            for index, entry in enumerate(entries):
                dictionary_pos = dictionary_poses[index]
                dictionary_canonical = canonical_inventory[index]
                metadata: dict[str, object] = {
                    "gloss_index": index,
                    "gloss_total": total,
                    "definition_bucket_key": _build_definition_bucket_key(
                        entry,
                        fallback_index=index,
                    ),
                }
                if entry.metadata:
                    raw_record = dict(entry.metadata)
                    metadata["dictionary_record"] = raw_record
                    dictionary_record_views = (
                        dictionary_record_views_by_index[index]
                        if index < len(dictionary_record_views_by_index)
                        else {}
                    )
                    if dictionary_record_views:
                        metadata["dictionary_record_views"] = dictionary_record_views
                gloss_provenance = _build_gloss_provenance(entry)
                if gloss_provenance:
                    metadata["gloss_provenance"] = gloss_provenance
                sense_provenance = _build_sense_provenance(entry, dictionary_pos=dictionary_pos)
                if sense_provenance:
                    metadata["sense_provenance"] = sense_provenance
                if index < len(target_provenance_by_index):
                    metadata["target_provenance"] = target_provenance_by_index[index]
                if index < len(kaikkei_policy_shadow_by_index):
                    kaikkei_policy_shadow = dict(kaikkei_policy_shadow_by_index[index])
                    if self._kaikki_policy.enable_live_demotion:
                        demotion, reasons = _resolve_kaikki_policy_live_demotion(
                            kaikkei_policy_shadow
                        )
                        if demotion > 0.0:
                            _apply_semantic_demotion(
                                metadata,
                                demotion=demotion,
                                reason=";".join(reasons) if reasons else "kaikki_policy",
                            )
                            kaikkei_policy_shadow["live_demotion_applied"] = True
                            kaikkei_policy_shadow["live_demotion_value"] = demotion
                            if reasons:
                                kaikkei_policy_shadow["live_demotion_reasons"] = reasons
                    if kaikkei_policy_shadow:
                        metadata["kaikki_policy_shadow"] = kaikkei_policy_shadow
                source_reverse_norm = _normalize_reverse_token_with_pos(
                    entry.translation,
                    pos_raw=entry.pos_raw,
                )
                reverse_targets = (
                    self._reverse_lookup.get(source_reverse_norm, ())
                    if self._reverse_lookup is not None
                    else ()
                )
                reverse_rank = (
                    reverse_targets.index(target_reverse_norm)
                    if target_reverse_norm and target_reverse_norm in reverse_targets
                    else None
                )
                metadata.update(
                    {
                        "reverse_check_supported": self._reverse_lookup is not None,
                        "reverse_check_hit": reverse_rank is not None,
                        "reverse_check_rank": reverse_rank,
                        "reverse_check_total": len(reverse_targets),
                        "reverse_check_source_dict": self._reverse_source_dict or None,
                        "reverse_check_target_norm": target_reverse_norm,
                        "reverse_check_source_norm": source_reverse_norm,
                    }
                )
                demotion = resolve_generic_gloss_demotion(
                    entry.translation,
                    demotions=self._generic_gloss_demotions,
                )
                if demotion > 0.0:
                    metadata["semantic_demotion"] = demotion
                    metadata["semantic_demotion_reason"] = "generic_gloss"
                if _should_shadow_interjection(
                    current_canonical=dictionary_canonical,
                    entry_metadata=entry.metadata,
                    earlier_canonicals=canonical_inventory[:index],
                ):
                    metadata["interjection_shadowed"] = True
                if _should_demote_shadowed_adverb(
                    current_canonical=dictionary_canonical,
                    canonical_inventory=canonical_inventory,
                ):
                    _apply_semantic_demotion(
                        metadata,
                        demotion=0.65,
                        reason="function_word_adverb_shadowed",
                    )
                register_demotion = _resolve_kaikki_register_demotion(entry.metadata)
                if register_demotion > 0.0:
                    _apply_semantic_demotion(
                        metadata,
                        demotion=register_demotion,
                        reason="kaikki_register_or_region",
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
    config: EnEsRulegenConfig,
    mapping: Mapping[str, Sequence[str]],
) -> list[CandidateFilter]:
    filters: list[CandidateFilter] = [NonEmptyFilter()]
    filters.append(
        EnEsGlossShapeFilter(
            allow_hyphen=config.allow_hyphen,
            allow_multiword_glosses=config.allow_multiword_glosses,
        )
    )
    if config.enable_length_filter:
        filters.append(
            LengthFilter(min_length=config.min_source_length, max_length=config.max_source_length)
        )
    if config.enable_possessive_filter:
        filters.append(PossessiveFilter())
    filters.append(ShadowedInterjectionFilter())
    if config.enable_stopword_filter:
        stopwords = config.stopwords or DEFAULT_STOPWORDS
        filters.append(EnEsStopwordFilter(stopwords=stopwords))
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


def _resolve_gloss_records(config: EnEsRulegenConfig) -> dict[str, list[FreedictGlossRecord]]:
    if config.gloss_records_by_target is not None:
        return _coerce_gloss_records(config.gloss_records_by_target)
    if config.gloss_mapping is not None:
        return _coerce_gloss_records(config.gloss_mapping)
    return load_freedict_gloss_records_ordered(
        config.freedict_es_en_path,
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


def _resolve_reverse_gloss_records(
    config: EnEsRulegenConfig,
) -> Optional[dict[str, list[FreedictGlossRecord]]]:
    if config.reverse_gloss_records_by_source is not None:
        return _coerce_gloss_records(config.reverse_gloss_records_by_source)
    if config.reverse_freedict_en_es_path is None:
        return None
    if not config.reverse_freedict_en_es_path.exists():
        return None
    return load_freedict_gloss_records_ordered(
        config.reverse_freedict_en_es_path,
        target_lang="es",
    )


def _records_to_gloss_mapping(
    records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
) -> dict[str, list[str]]:
    return {
        target: [entry.translation for entry in entries]
        for target, entries in records_by_target.items()
    }
