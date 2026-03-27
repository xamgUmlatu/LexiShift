from __future__ import annotations

from dataclasses import dataclass, field, replace
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
    PosMatchScoringConfig,
    RuleCandidate,
    RuleConfidenceSignals,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    RuleScoringConfig,
    SimpleSignalProvider,
    build_optional_pos_match_provider,
    score_candidate_pos_match,
    score_canonical_pos_pair,
)
from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
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
    resolve_kaikki_provenance_competition_demotion as _resolve_kaikki_provenance_competition_demotion,
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
    late_sense_clean_earlier_competition_penalty: float = 0.0
    risk_families: tuple[str, ...] = (
        "math_geometry",
        "government_law",
        "hunting_fishing_tools",
        "register_region",
        "abbreviation_ellipsis_formof",
    )


@dataclass(frozen=True)
class EnEsCompiledSignalProvider:
    dict_priorities: Mapping[str, float]
    gloss_decay: GlossDecay = field(default_factory=GlossDecay)
    pos_match: PosMatchScoringConfig = field(default_factory=PosMatchScoringConfig)
    variant_penalty: float = 0.2
    candidate_facts_by_id: Mapping[int, EnEsCompiledCandidateFact] = field(default_factory=dict)
    candidate_row_id_by_candidate_id: Mapping[int, int] = field(default_factory=dict)
    score_table: Optional[EnEsCompiledCandidateScoreTable] = None

    def signals(self, candidate: RuleCandidate) -> RuleConfidenceSignals:
        metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
        fact = self._resolve_candidate_fact(metadata)
        row_id = self._resolve_candidate_row_id(metadata)
        if row_id is not None and self.score_table is not None:
            dict_priority = self.score_table.dict_priority_values[row_id]
            frequency_weight = self.score_table.frequency_weight_values[row_id]
            pos_match = self.score_table.pos_match_values[row_id]
        else:
            dict_priority = self.dict_priorities.get(candidate.source_dict, 0.0)
            gloss_index = (
                fact.gloss_index if fact is not None else self._resolve_gloss_index(metadata)
            )
            frequency_weight = self.gloss_decay.multiplier(gloss_index)
            pos_match = self._resolve_pos_match(candidate, metadata, fact)
        variant_penalty = (
            self.variant_penalty if self._resolve_variant_flag(metadata, fact) else 0.0
        )
        phrase_penalty = 1.0 if self._resolve_phrase_flag(candidate, fact) else 0.0
        return RuleConfidenceSignals(
            dict_priority=dict_priority,
            frequency_weight=frequency_weight,
            pos_match=pos_match,
            variant_penalty=variant_penalty,
            phrase_penalty=phrase_penalty,
            embedding_score=None,
        )

    def _resolve_candidate_fact(
        self,
        metadata: Mapping[str, object],
    ) -> Optional[EnEsCompiledCandidateFact]:
        candidate_id = _normalize_non_negative_optional_int(metadata.get("compiled_candidate_id"))
        if candidate_id is None:
            return None
        return self.candidate_facts_by_id.get(candidate_id)

    def _resolve_candidate_row_id(self, metadata: Mapping[str, object]) -> Optional[int]:
        candidate_id = _normalize_non_negative_optional_int(metadata.get("compiled_candidate_id"))
        if candidate_id is None:
            return None
        row_id = self.candidate_row_id_by_candidate_id.get(candidate_id)
        if row_id is None:
            return None
        return int(row_id)

    def _resolve_gloss_index(self, metadata: Mapping[str, object]) -> Optional[int]:
        gloss_index = _normalize_non_negative_optional_int(metadata.get("gloss_index"))
        return gloss_index if gloss_index is not None else None

    def _resolve_variant_flag(
        self,
        metadata: Mapping[str, object],
        fact: Optional[EnEsCompiledCandidateFact],
    ) -> bool:
        if bool(metadata.get("variant")):
            return True
        if fact is not None:
            return bool(fact.is_variant)
        return False

    def _resolve_phrase_flag(
        self,
        candidate: RuleCandidate,
        fact: Optional[EnEsCompiledCandidateFact],
    ) -> bool:
        source_phrase = str(candidate.source_phrase or "").strip()
        if source_phrase:
            return " " in source_phrase
        if fact is not None:
            return bool(fact.source_phrase_is_phrase)
        return False

    def _resolve_pos_match(
        self,
        candidate: RuleCandidate,
        metadata: Mapping[str, object],
        fact: Optional[EnEsCompiledCandidateFact],
    ) -> float:
        if not bool(self.pos_match.enabled):
            return 0.0
        if fact is not None:
            target = fact.target_pos_canonical
            source = fact.source_pos_canonical or fact.dictionary_pos_canonical
            if source and target:
                return score_canonical_pos_pair(
                    source,
                    target,
                    exact_match_bonus=self.pos_match.exact_match_bonus,
                    compatible_match_bonus=self.pos_match.compatible_match_bonus,
                    compatibility_classes=self.pos_match.compatibility_classes,
                )
        return score_candidate_pos_match(
            candidate,
            exact_match_bonus=self.pos_match.exact_match_bonus,
            compatible_match_bonus=self.pos_match.compatible_match_bonus,
            compatibility_classes=self.pos_match.compatibility_classes,
        )


@dataclass(frozen=True)
class EnEsCompiledCandidateFact:
    candidate_id: int
    target_id: int
    definition_bucket_id: int
    source_dict_id: int
    source_type_id: int
    local_candidate_index: int
    gloss_index: int
    gloss_total: int
    source_phrase: str
    reverse_check_source_norm: str
    reverse_check_target_norm: str
    reverse_check_supported: bool
    reverse_check_hit: bool
    reverse_check_rank: Optional[int]
    reverse_check_total: int
    source_phrase_token_count: int
    source_phrase_is_ascii: bool
    source_phrase_is_phrase: bool
    is_variant: bool
    source_pos_canonical: str
    target_pos_canonical: str
    dictionary_pos_canonical: str
    semantic_demotion_base: float
    semantic_demotion_reason: Optional[str]
    interjection_shadowed: bool
    has_word_package: bool
    has_gloss_provenance: bool
    has_sense_provenance: bool
    has_target_provenance: bool
    current_sense_position: int
    kaikkei_family_names: tuple[str, ...] = ()
    family_marker_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class EnEsCompiledCandidateTable:
    candidate_ids: tuple[int, ...] = ()
    target_ids: tuple[int, ...] = ()
    definition_bucket_ids: tuple[int, ...] = ()
    source_phrases: tuple[str, ...] = ()
    source_phrase_lowers: tuple[str, ...] = ()
    source_dict_ids: tuple[int, ...] = ()
    source_type_ids: tuple[int, ...] = ()
    local_candidate_indices: tuple[int, ...] = ()
    gloss_indices: tuple[int, ...] = ()
    gloss_totals: tuple[int, ...] = ()
    semantic_demotion_bases: tuple[float, ...] = ()
    source_pos_canonicals: tuple[str, ...] = ()
    target_pos_canonicals: tuple[str, ...] = ()
    dictionary_pos_canonicals: tuple[str, ...] = ()
    phrase_flags: tuple[bool, ...] = ()
    variant_flags: tuple[bool, ...] = ()
    interjection_shadowed_flags: tuple[bool, ...] = ()
    reverse_check_supported_flags: tuple[bool, ...] = ()
    reverse_check_hit_flags: tuple[bool, ...] = ()
    reverse_check_rank_values: tuple[int, ...] = ()
    reverse_check_total_values: tuple[int, ...] = ()
    current_sense_positions: tuple[int, ...] = ()
    family_marker_id_rows: tuple[tuple[int, ...], ...] = ()
    candidate_row_id_by_candidate_id: Mapping[int, int] = field(default_factory=dict)
    candidate_row_ids_by_target_id: Mapping[int, tuple[int, ...]] = field(default_factory=dict)
    candidate_row_ids_by_definition_bucket_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )
    candidate_row_ids_by_family_marker_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class EnEsCompiledCandidateScoreTable:
    candidate_ids: tuple[int, ...] = ()
    target_ids: tuple[int, ...] = ()
    definition_bucket_ids: tuple[int, ...] = ()
    dict_priority_values: tuple[float, ...] = ()
    frequency_weight_values: tuple[float, ...] = ()
    pos_match_values: tuple[float, ...] = ()
    variant_penalty_values: tuple[float, ...] = ()
    phrase_penalty_values: tuple[float, ...] = ()
    confidence_scores: tuple[float, ...] = ()
    ranking_scores: tuple[float, ...] = ()


@dataclass(frozen=True)
class EnEsCompiledCandidateFilterTable:
    candidate_ids: tuple[int, ...] = ()
    target_ids: tuple[int, ...] = ()
    normalized_source_phrases: tuple[str, ...] = ()
    non_empty_flags: tuple[bool, ...] = ()
    gloss_shape_flags: tuple[bool, ...] = ()
    length_flags: tuple[bool, ...] = ()
    possessive_flags: tuple[bool, ...] = ()
    shadowed_interjection_flags: tuple[bool, ...] = ()
    stopword_flags: tuple[bool, ...] = ()
    inflection_artifact_flags: tuple[bool, ...] = ()
    accepted_flags: tuple[bool, ...] = ()
    accepted_candidate_row_ids_by_target_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class EnEsCompiledRankingMechanism:
    fallback: DictionaryEntryOrderRankingMechanism = field(
        default_factory=DictionaryEntryOrderRankingMechanism
    )
    candidate_row_id_by_candidate_id: Mapping[int, int] = field(default_factory=dict)
    score_table: Optional[EnEsCompiledCandidateScoreTable] = None

    def score(self, candidate: CandidateRankingContext) -> float:
        metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
        candidate_id = _normalize_non_negative_optional_int(metadata.get("compiled_candidate_id"))
        if candidate_id is not None and self.score_table is not None:
            row_id = self.candidate_row_id_by_candidate_id.get(candidate_id)
            if row_id is not None:
                return float(self.score_table.ranking_scores[int(row_id)])
        return self.fallback.score(candidate)

    def bucket_key(self, candidate: CandidateRankingContext) -> str:
        return self.fallback.bucket_key(candidate)


@dataclass(frozen=True)
class EnEsCompiledTargetContext:
    target: str
    target_reverse_norm: str
    target_word_package: Optional[Mapping[str, object]]
    target_pos: Mapping[str, object]
    entries: tuple[FreedictGlossRecord, ...]
    dictionary_poses: tuple[Mapping[str, object], ...]
    canonical_inventory: tuple[str, ...]
    dictionary_record_views_by_index: tuple[Mapping[str, object], ...]
    target_provenance_by_index: tuple[Mapping[str, object], ...]
    target_id: int = -1
    base_candidates: tuple[RuleCandidate, ...] = ()
    candidate_facts: tuple[EnEsCompiledCandidateFact, ...] = ()


@dataclass(frozen=True)
class EnEsCompiledResources:
    records_by_target: Mapping[str, Sequence[FreedictGlossRecord]]
    reverse_records_by_source: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext] = field(
        default_factory=dict
    )
    target_ids_by_target: Mapping[str, int] = field(default_factory=dict)
    definition_bucket_ids_by_key: Mapping[str, int] = field(default_factory=dict)
    family_marker_ids_by_name: Mapping[str, int] = field(default_factory=dict)
    source_dict_ids_by_name: Mapping[str, int] = field(default_factory=dict)
    source_type_ids_by_name: Mapping[str, int] = field(default_factory=dict)
    candidate_facts: tuple[EnEsCompiledCandidateFact, ...] = ()
    candidate_table: Optional[EnEsCompiledCandidateTable] = None
    gloss_base_forms: frozenset[str] = frozenset()
    reverse_lookup: Optional[Mapping[str, tuple[str, ...]]] = None
    compile_version: int = 3


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
    compiled_resources: Optional[EnEsCompiledResources] = None


def build_en_es_compiled_resources(
    *,
    targets: Iterable[str],
    records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
    reverse_records_by_source: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None,
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
    language_pair: str = "en-es",
    source_dict: str = "freedict_es_en",
    source_type: str = "translation",
    dictionary_pos_source_profile: str = "freedict",
    generic_gloss_demotions: Optional[Mapping[str, float]] = None,
    gloss_base_forms_override: Optional[Sequence[str]] = None,
) -> EnEsCompiledResources:
    normalized_targets = tuple(
        dict.fromkeys(str(target or "").strip() for target in targets if str(target or "").strip())
    )
    package_map = dict(word_packages_by_target or {})
    reverse_lookup = (
        _build_reverse_lookup(reverse_records_by_source)
        if reverse_records_by_source is not None
        else None
    )
    resolved_generic_gloss_demotions = dict(
        generic_gloss_demotions or resolve_pair_generic_gloss_demotions(language_pair)
    )
    compiled_targets_by_target: dict[str, EnEsCompiledTargetContext] = {}
    for target in normalized_targets:
        target_reverse_norm = _normalize_reverse_token(target)
        target_word_package = resolve_target_word_package(
            target=target,
            language_pair=language_pair,
            fallback_provider="frequency",
            package_hint=package_map.get(target),
        )
        target_pos = extract_target_pos_component(
            target_word_package=target_word_package,
            language_pair=language_pair,
        )
        entries = tuple(_collect_sanitized_gloss_records(records_by_target.get(target, ())))
        dictionary_poses = tuple(
            normalize_pos_component(
                entry.pos_raw,
                language_pair=language_pair,
                source_provider=source_dict,
                source_kind="dictionary",
                source_profile=dictionary_pos_source_profile,
            )
            for entry in entries
        )
        canonical_inventory = tuple(
            _extract_canonical_from_component(component) for component in dictionary_poses
        )
        dictionary_record_views_by_index: list[dict[str, object]] = []
        for entry in entries:
            if entry.metadata:
                raw_record = dict(entry.metadata)
                dictionary_record_views = build_kaikki_record_views(raw_record)
                if dictionary_record_views:
                    dictionary_record_views_by_index.append({"kaikki": dictionary_record_views})
                    continue
            dictionary_record_views_by_index.append({})
        target_provenance_by_index = tuple(
            _build_target_provenance_by_index(
                target=target,
                entries=entries,
                canonical_inventory=canonical_inventory,
            )
        )
        base_candidates = _build_static_candidate_inventory(
            target=target,
            language_pair=language_pair,
            source_dict=source_dict,
            source_type=source_type,
            target_reverse_norm=target_reverse_norm,
            target_word_package=target_word_package,
            target_pos=target_pos,
            entries=entries,
            dictionary_poses=dictionary_poses,
            canonical_inventory=canonical_inventory,
            dictionary_record_views_by_index=tuple(dictionary_record_views_by_index),
            target_provenance_by_index=target_provenance_by_index,
            reverse_lookup=reverse_lookup,
            generic_gloss_demotions=resolved_generic_gloss_demotions,
        )
        compiled_targets_by_target[target] = EnEsCompiledTargetContext(
            target=target,
            target_reverse_norm=target_reverse_norm,
            target_word_package=target_word_package,
            target_pos=target_pos,
            entries=entries,
            dictionary_poses=dictionary_poses,
            canonical_inventory=canonical_inventory,
            dictionary_record_views_by_index=tuple(dictionary_record_views_by_index),
            target_provenance_by_index=target_provenance_by_index,
            base_candidates=base_candidates,
        )
    ordered_targets = tuple(sorted(compiled_targets_by_target))
    target_ids_by_target = {target: index for index, target in enumerate(ordered_targets)}
    definition_bucket_ids_by_key = _build_definition_bucket_ids(
        compiled_targets_by_target=compiled_targets_by_target,
        ordered_targets=ordered_targets,
    )
    family_marker_ids_by_name = _build_family_marker_ids(
        compiled_targets_by_target=compiled_targets_by_target,
        ordered_targets=ordered_targets,
    )
    source_dict_ids_by_name = {str(source_dict): 0}
    source_type_ids_by_name = {str(source_type): 0}
    finalized_targets_by_target, candidate_facts = _finalize_compiled_target_contexts(
        compiled_targets_by_target=compiled_targets_by_target,
        ordered_targets=ordered_targets,
        target_ids_by_target=target_ids_by_target,
        definition_bucket_ids_by_key=definition_bucket_ids_by_key,
        family_marker_ids_by_name=family_marker_ids_by_name,
        source_dict_ids_by_name=source_dict_ids_by_name,
        source_type_ids_by_name=source_type_ids_by_name,
    )
    candidate_table = _build_compiled_candidate_table(candidate_facts)
    return EnEsCompiledResources(
        compile_version=3,
        records_by_target=dict(records_by_target),
        reverse_records_by_source=(
            dict(reverse_records_by_source) if reverse_records_by_source is not None else None
        ),
        compiled_targets_by_target=finalized_targets_by_target,
        target_ids_by_target=target_ids_by_target,
        definition_bucket_ids_by_key=definition_bucket_ids_by_key,
        family_marker_ids_by_name=family_marker_ids_by_name,
        source_dict_ids_by_name=source_dict_ids_by_name,
        source_type_ids_by_name=source_type_ids_by_name,
        candidate_facts=candidate_facts,
        candidate_table=candidate_table,
        gloss_base_forms=frozenset(
            gloss_base_forms_override
            if gloss_base_forms_override is not None
            else _build_gloss_base_forms(_records_to_gloss_mapping(records_by_target))
        ),
        reverse_lookup=reverse_lookup,
    )


def build_en_es_compiled_candidate_score_table(
    *,
    compiled_resources: EnEsCompiledResources,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateScoreTable:
    candidate_table = compiled_resources.candidate_table
    if candidate_table is None:
        return EnEsCompiledCandidateScoreTable()
    dict_priority_by_source_dict_id = {
        int(source_dict_id): float(config.dict_priority)
        for name, source_dict_id in compiled_resources.source_dict_ids_by_name.items()
        if name == config.source_dict_id
    }
    scorer = RuleScorer(weights=config.scoring.weights)
    ranking_mechanism = DictionaryEntryOrderRankingMechanism(reverse_check=config.reverse_check)
    effective_semantic_demotion_rows = _build_compiled_overlay_demotion_rows(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        config=config,
    )
    targets_by_id = {
        context.target_id: context.target
        for context in compiled_resources.compiled_targets_by_target.values()
        if context.target_id >= 0
    }
    dict_priority_values: list[float] = []
    frequency_weight_values: list[float] = []
    pos_match_values: list[float] = []
    variant_penalty_values: list[float] = []
    phrase_penalty_values: list[float] = []
    confidence_scores: list[float] = []
    ranking_scores: list[float] = []
    for row_id, candidate_id in enumerate(candidate_table.candidate_ids):
        dict_priority = float(
            dict_priority_by_source_dict_id.get(candidate_table.source_dict_ids[row_id], 0.0)
        )
        gloss_index = candidate_table.gloss_indices[row_id]
        frequency_weight = float(
            config.gloss_decay.multiplier(gloss_index if gloss_index >= 0 else None)
        )
        source_pos = candidate_table.source_pos_canonicals[row_id]
        dictionary_pos = candidate_table.dictionary_pos_canonicals[row_id]
        target_pos = candidate_table.target_pos_canonicals[row_id]
        pos_match = 0.0
        if bool(config.scoring.pos_match.enabled):
            pos_match = score_canonical_pos_pair(
                source_pos or dictionary_pos,
                target_pos,
                exact_match_bonus=config.scoring.pos_match.exact_match_bonus,
                compatible_match_bonus=config.scoring.pos_match.compatible_match_bonus,
                compatibility_classes=config.scoring.pos_match.compatibility_classes,
            )
        variant_penalty = (
            float(config.variant_penalty) if candidate_table.variant_flags[row_id] else 0.0
        )
        phrase_penalty = 1.0 if candidate_table.phrase_flags[row_id] else 0.0
        confidence = float(
            scorer.score(
                RuleConfidenceSignals(
                    dict_priority=dict_priority,
                    frequency_weight=frequency_weight,
                    pos_match=pos_match,
                    variant_penalty=variant_penalty,
                    phrase_penalty=phrase_penalty,
                    embedding_score=None,
                )
            )
        )
        ranking_metadata = {
            "gloss_index": candidate_table.gloss_indices[row_id],
            "semantic_demotion": effective_semantic_demotion_rows[row_id],
            "reverse_check_supported": candidate_table.reverse_check_supported_flags[row_id],
            "reverse_check_hit": candidate_table.reverse_check_hit_flags[row_id],
            "reverse_check_rank": (
                candidate_table.reverse_check_rank_values[row_id]
                if candidate_table.reverse_check_rank_values[row_id] >= 0
                else None
            ),
            "reverse_check_total": candidate_table.reverse_check_total_values[row_id],
        }
        ranking_score = float(
            ranking_mechanism.score(
                CandidateRankingContext(
                    source_phrase=candidate_table.source_phrases[row_id],
                    replacement=str(targets_by_id.get(candidate_table.target_ids[row_id], "")),
                    metadata=ranking_metadata,
                    confidence=confidence,
                    semantic_demotion_scale=config.semantic_demotion_scale,
                )
            )
        )
        dict_priority_values.append(dict_priority)
        frequency_weight_values.append(frequency_weight)
        pos_match_values.append(float(pos_match))
        variant_penalty_values.append(variant_penalty)
        phrase_penalty_values.append(phrase_penalty)
        confidence_scores.append(confidence)
        ranking_scores.append(ranking_score)
    return EnEsCompiledCandidateScoreTable(
        candidate_ids=tuple(int(candidate_id) for candidate_id in candidate_table.candidate_ids),
        target_ids=tuple(int(target_id) for target_id in candidate_table.target_ids),
        definition_bucket_ids=tuple(
            int(definition_bucket_id)
            for definition_bucket_id in candidate_table.definition_bucket_ids
        ),
        dict_priority_values=tuple(dict_priority_values),
        frequency_weight_values=tuple(frequency_weight_values),
        pos_match_values=tuple(pos_match_values),
        variant_penalty_values=tuple(variant_penalty_values),
        phrase_penalty_values=tuple(phrase_penalty_values),
        confidence_scores=tuple(confidence_scores),
        ranking_scores=tuple(ranking_scores),
    )


def build_en_es_compiled_candidate_filter_table(
    *,
    compiled_resources: EnEsCompiledResources,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateFilterTable:
    candidate_table = compiled_resources.candidate_table
    if candidate_table is None:
        return EnEsCompiledCandidateFilterTable()
    stopwords = set(config.stopwords or DEFAULT_STOPWORDS)
    gloss_base_forms = set(compiled_resources.gloss_base_forms)
    normalized_source_phrases: list[str] = []
    non_empty_flags: list[bool] = []
    gloss_shape_flags: list[bool] = []
    length_flags: list[bool] = []
    possessive_flags: list[bool] = []
    shadowed_interjection_flags: list[bool] = []
    stopword_flags: list[bool] = []
    inflection_artifact_flags: list[bool] = []
    accepted_flags: list[bool] = []
    accepted_candidate_row_ids_by_target_id: dict[int, list[int]] = {}
    for row_id, candidate_id in enumerate(candidate_table.candidate_ids):
        normalized_phrase = _normalize_compiled_source_phrase(
            candidate_table.source_phrases[row_id]
        )
        normalized_source_phrases.append(normalized_phrase)
        allows_function_word_phrase = (
            candidate_table.dictionary_pos_canonicals[row_id] in _FUNCTION_WORD_CANONICALS
        )
        non_empty_ok = _compiled_non_empty_accepts(normalized_phrase)
        gloss_shape_ok = _compiled_gloss_shape_accepts(
            normalized_phrase,
            allow_hyphen=config.allow_hyphen,
            allow_multiword_glosses=config.allow_multiword_glosses,
            allows_function_word_phrase=allows_function_word_phrase,
        )
        length_ok = (
            _compiled_length_accepts(
                normalized_phrase,
                min_length=config.min_source_length,
                max_length=config.max_source_length,
            )
            if config.enable_length_filter
            else True
        )
        possessive_ok = (
            _compiled_possessive_accepts(normalized_phrase)
            if config.enable_possessive_filter
            else True
        )
        shadow_ok = not candidate_table.interjection_shadowed_flags[row_id]
        stopword_ok = (
            _compiled_stopword_accepts(
                normalized_phrase,
                stopwords=stopwords,
                allows_function_word_phrase=allows_function_word_phrase,
            )
            if config.enable_stopword_filter
            else True
        )
        inflection_ok = (
            _compiled_inflection_artifact_accepts(
                normalized_phrase,
                base_forms=gloss_base_forms,
                suffixes=config.inflection_suffixes,
            )
            if config.enable_inflection_filter
            else True
        )
        accepted = (
            non_empty_ok
            and gloss_shape_ok
            and length_ok
            and possessive_ok
            and shadow_ok
            and stopword_ok
            and inflection_ok
        )
        non_empty_flags.append(non_empty_ok)
        gloss_shape_flags.append(gloss_shape_ok)
        length_flags.append(length_ok)
        possessive_flags.append(possessive_ok)
        shadowed_interjection_flags.append(shadow_ok)
        stopword_flags.append(stopword_ok)
        inflection_artifact_flags.append(inflection_ok)
        accepted_flags.append(accepted)
        if accepted:
            target_id = int(candidate_table.target_ids[row_id])
            accepted_candidate_row_ids_by_target_id.setdefault(target_id, []).append(row_id)
    return EnEsCompiledCandidateFilterTable(
        candidate_ids=tuple(int(candidate_id) for candidate_id in candidate_table.candidate_ids),
        target_ids=tuple(int(target_id) for target_id in candidate_table.target_ids),
        normalized_source_phrases=tuple(normalized_source_phrases),
        non_empty_flags=tuple(non_empty_flags),
        gloss_shape_flags=tuple(gloss_shape_flags),
        length_flags=tuple(length_flags),
        possessive_flags=tuple(possessive_flags),
        shadowed_interjection_flags=tuple(shadowed_interjection_flags),
        stopword_flags=tuple(stopword_flags),
        inflection_artifact_flags=tuple(inflection_artifact_flags),
        accepted_flags=tuple(accepted_flags),
        accepted_candidate_row_ids_by_target_id={
            key: tuple(value)
            for key, value in sorted(accepted_candidate_row_ids_by_target_id.items())
        },
    )


def _build_compiled_overlay_demotion_rows(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: EnEsCompiledCandidateTable,
    config: EnEsRulegenConfig,
) -> tuple[float, ...]:
    family_name_by_marker_id = {
        int(marker_id): str(name)
        for name, marker_id in compiled_resources.family_marker_ids_by_name.items()
    }
    configured_risk_families = {
        str(name).strip() for name in config.kaikki_policy.risk_families if str(name).strip()
    }
    risky_family_name_rows: list[tuple[str, ...]] = []
    risky_candidate_flags: list[bool] = []
    for family_marker_ids in candidate_table.family_marker_id_rows:
        risky_family_names = tuple(
            family_name_by_marker_id[marker_id]
            for marker_id in family_marker_ids
            if family_name_by_marker_id.get(marker_id) in configured_risk_families
        )
        risky_family_name_rows.append(risky_family_names)
        risky_candidate_flags.append(bool(risky_family_names))

    candidate_row_ids_by_target_id = candidate_table.candidate_row_ids_by_target_id
    same_canonical_competitor_rows_by_row_id: dict[int, tuple[int, ...]] = {}
    fallback_competitor_rows_by_row_id: dict[int, tuple[int, ...]] = {}
    for target_id, row_ids in candidate_row_ids_by_target_id.items():
        rows = tuple(int(row_id) for row_id in row_ids)
        rows_by_canonical: dict[str, list[int]] = {}
        for row_id in rows:
            canonical = str(candidate_table.dictionary_pos_canonicals[row_id] or "").strip().lower()
            if canonical:
                rows_by_canonical.setdefault(canonical, []).append(row_id)
        for row_id in rows:
            canonical = str(candidate_table.dictionary_pos_canonicals[row_id] or "").strip().lower()
            same_canonical_rows = tuple(
                other_row_id
                for other_row_id in rows_by_canonical.get(canonical, ())
                if other_row_id != row_id
            )
            same_canonical_competitor_rows_by_row_id[row_id] = same_canonical_rows
            fallback_competitor_rows_by_row_id[row_id] = tuple(
                other_row_id for other_row_id in rows if other_row_id != row_id
            )

    effective_demotions: list[float] = []
    for row_id, base_demotion in enumerate(candidate_table.semantic_demotion_bases):
        competitor_rows = same_canonical_competitor_rows_by_row_id.get(row_id, ())
        if not competitor_rows:
            competitor_rows = fallback_competitor_rows_by_row_id.get(row_id, ())
        clean_competition_present = any(
            not risky_candidate_flags[other_row_id] for other_row_id in competitor_rows
        )
        local_candidate_index = candidate_table.local_candidate_indices[row_id]
        clean_earlier_competition_present = any(
            (not risky_candidate_flags[other_row_id])
            and candidate_table.local_candidate_indices[other_row_id] < local_candidate_index
            for other_row_id in competitor_rows
        )
        effective_demotion = float(base_demotion)
        if config.kaikki_policy.enable_live_demotion:
            live_demotion, _ = _resolve_kaikki_policy_live_demotion(
                {
                    "would_demote": (
                        bool(risky_family_name_rows[row_id]) and clean_competition_present
                    ),
                    "risky_families": risky_family_name_rows[row_id],
                }
            )
            effective_demotion = max(effective_demotion, float(live_demotion))
        provenance_demotion, _ = _resolve_kaikki_provenance_competition_demotion(
            target_provenance=(
                {"current_sense_position": candidate_table.current_sense_positions[row_id]}
                if candidate_table.current_sense_positions[row_id] > 0
                else None
            ),
            gloss_provenance=None,
            shadow={
                "clean_earlier_competition_present": clean_earlier_competition_present,
            },
            late_sense_clean_earlier_competition_penalty=(
                config.kaikki_policy.late_sense_clean_earlier_competition_penalty
            ),
        )
        effective_demotion = max(effective_demotion, float(provenance_demotion))
        effective_demotions.append(effective_demotion)
    return tuple(effective_demotions)


def _normalize_compiled_source_phrase(source_phrase: object) -> str:
    phrase = str(source_phrase or "")
    normalized = BasicStringNormalizer().normalize(
        RuleCandidate(
            source_phrase=phrase,
            replacement="",
            language_pair="en-es",
            source_dict="compiled",
        )
    )
    normalized = LeadingEnglishInfinitiveNormalizer().normalize(normalized)
    return str(normalized.source_phrase or "").strip()


def _compiled_non_empty_accepts(source_phrase: str) -> bool:
    text = str(source_phrase or "").strip()
    if len(text) < 1:
        return False
    return bool(re.search(r"\w", text))


def _compiled_gloss_shape_accepts(
    source_phrase: str,
    *,
    allow_hyphen: bool,
    allow_multiword_glosses: bool,
    allows_function_word_phrase: bool,
) -> bool:
    phrase = str(source_phrase or "").strip().lower()
    if not phrase:
        return False
    if not allow_hyphen and "-" in phrase:
        return False
    if allow_multiword_glosses or allows_function_word_phrase:
        return bool(_EN_ES_MULTIWORD_RE.fullmatch(phrase))
    return bool(_EN_ES_SINGLE_WORD_RE.fullmatch(phrase))


def _compiled_length_accepts(
    source_phrase: str,
    *,
    min_length: int,
    max_length: Optional[int],
) -> bool:
    text = str(source_phrase or "").strip()
    if len(text) < int(min_length):
        return False
    if max_length is not None and len(text) > int(max_length):
        return False
    return True


def _compiled_possessive_accepts(source_phrase: str) -> bool:
    phrase = str(source_phrase or "").strip()
    return not any(phrase.endswith(suffix) for suffix in ("'s", "’s"))


def _compiled_stopword_accepts(
    source_phrase: str,
    *,
    stopwords: set[str],
    allows_function_word_phrase: bool,
) -> bool:
    phrase = str(source_phrase or "").strip().lower()
    if phrase not in stopwords:
        return True
    return allows_function_word_phrase


def _compiled_inflection_artifact_accepts(
    source_phrase: str,
    *,
    base_forms: set[str],
    suffixes: Sequence[str],
    min_base_length: int = 2,
) -> bool:
    phrase = str(source_phrase or "").strip()
    if not base_forms:
        return True
    for suffix in suffixes:
        normalized_suffix = str(suffix or "")
        if not normalized_suffix or not phrase.endswith(normalized_suffix):
            continue
        base = phrase[: -len(normalized_suffix)]
        if len(base) < int(min_base_length):
            continue
        if base in base_forms:
            return False
    return True


def _build_static_candidate_inventory(
    *,
    target: str,
    language_pair: str,
    source_dict: str,
    source_type: str,
    target_reverse_norm: str,
    target_word_package: Optional[Mapping[str, object]],
    target_pos: Mapping[str, object],
    entries: Sequence[FreedictGlossRecord],
    dictionary_poses: Sequence[Mapping[str, object]],
    canonical_inventory: Sequence[str],
    dictionary_record_views_by_index: Sequence[Mapping[str, object]],
    target_provenance_by_index: Sequence[Mapping[str, object]],
    reverse_lookup: Optional[Mapping[str, tuple[str, ...]]],
    generic_gloss_demotions: Mapping[str, float],
) -> tuple[RuleCandidate, ...]:
    total = len(entries)
    candidates: list[RuleCandidate] = []
    for index, entry in enumerate(entries):
        dictionary_pos = dictionary_poses[index] if index < len(dictionary_poses) else {}
        dictionary_canonical = (
            canonical_inventory[index] if index < len(canonical_inventory) else ""
        )
        dictionary_record_views = (
            dictionary_record_views_by_index[index]
            if index < len(dictionary_record_views_by_index)
            else {}
        )
        target_provenance = (
            target_provenance_by_index[index] if index < len(target_provenance_by_index) else None
        )
        metadata = _build_static_candidate_metadata(
            entry=entry,
            index=index,
            total=total,
            target=target,
            target_reverse_norm=target_reverse_norm,
            target_word_package=target_word_package,
            target_pos=target_pos,
            dictionary_pos=dictionary_pos,
            dictionary_canonical=dictionary_canonical,
            canonical_inventory=canonical_inventory,
            dictionary_record_views=dictionary_record_views,
            target_provenance=target_provenance,
            reverse_lookup=reverse_lookup,
            generic_gloss_demotions=generic_gloss_demotions,
        )
        candidates.append(
            RuleCandidate(
                source_phrase=str(entry.translation),
                replacement=str(target),
                language_pair=language_pair,
                source_dict=source_dict,
                source_type=source_type,
                metadata=metadata,
            )
        )
    return tuple(candidates)


def _build_static_candidate_metadata(
    *,
    entry: FreedictGlossRecord,
    index: int,
    total: int,
    target: str,
    target_reverse_norm: str,
    target_word_package: Optional[Mapping[str, object]],
    target_pos: Mapping[str, object],
    dictionary_pos: Mapping[str, object],
    dictionary_canonical: str,
    canonical_inventory: Sequence[str],
    dictionary_record_views: Mapping[str, object],
    target_provenance: Optional[Mapping[str, object]],
    reverse_lookup: Optional[Mapping[str, tuple[str, ...]]],
    generic_gloss_demotions: Mapping[str, float],
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "gloss_index": index,
        "gloss_total": total,
        "definition_bucket_key": _build_definition_bucket_key(
            entry,
            fallback_index=index,
        ),
        "compiled_candidate_index": index,
    }
    if entry.metadata:
        raw_record = dict(entry.metadata)
        metadata["dictionary_record"] = raw_record
    if dictionary_record_views:
        metadata["dictionary_record_views"] = dict(dictionary_record_views)
    kaikkei_family_names = _extract_kaikki_family_names(dictionary_record_views)
    if kaikkei_family_names:
        metadata["kaikki_family_names"] = kaikkei_family_names
    gloss_provenance = _build_gloss_provenance(entry)
    if gloss_provenance:
        metadata["gloss_provenance"] = gloss_provenance
    sense_provenance = _build_sense_provenance(entry, dictionary_pos=dictionary_pos)
    if sense_provenance:
        metadata["sense_provenance"] = sense_provenance
    if target_provenance:
        metadata["target_provenance"] = target_provenance
    source_reverse_norm = _normalize_reverse_token_with_pos(
        entry.translation,
        pos_raw=entry.pos_raw,
    )
    reverse_targets = (
        reverse_lookup.get(source_reverse_norm, ()) if reverse_lookup is not None else ()
    )
    reverse_rank = (
        reverse_targets.index(target_reverse_norm)
        if target_reverse_norm and target_reverse_norm in reverse_targets
        else None
    )
    metadata.update(
        {
            "reverse_check_supported": reverse_lookup is not None,
            "reverse_check_hit": reverse_rank is not None,
            "reverse_check_rank": reverse_rank,
            "reverse_check_total": len(reverse_targets),
            "reverse_check_source_dict": None,
            "reverse_check_target_norm": target_reverse_norm,
            "reverse_check_source_norm": source_reverse_norm,
        }
    )
    demotion = resolve_generic_gloss_demotion(
        entry.translation,
        demotions=generic_gloss_demotions,
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
    return metadata


def _extract_kaikki_family_names(dictionary_record_views: Mapping[str, object]) -> tuple[str, ...]:
    if not isinstance(dictionary_record_views, Mapping):
        return ()
    kaikki_views = dictionary_record_views.get("kaikki")
    if not isinstance(kaikki_views, Mapping):
        return ()
    combined = kaikki_views.get("combined_families")
    if isinstance(combined, Sequence) and not isinstance(combined, (str, bytes)):
        return tuple(dict.fromkeys(str(value).strip() for value in combined if str(value).strip()))
    family_fields = kaikki_views.get("family_fields")
    if isinstance(family_fields, Mapping):
        return tuple(sorted(str(key).strip() for key in family_fields if str(key).strip()))
    return ()


def _build_definition_bucket_ids(
    *,
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext],
    ordered_targets: Sequence[str],
) -> dict[str, int]:
    keys = {
        str(candidate.metadata.get("definition_bucket_key") or "").strip()
        for target in ordered_targets
        for candidate in compiled_targets_by_target[target].base_candidates
        if str(candidate.metadata.get("definition_bucket_key") or "").strip()
    }
    return {key: index for index, key in enumerate(sorted(keys))}


def _build_family_marker_ids(
    *,
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext],
    ordered_targets: Sequence[str],
) -> dict[str, int]:
    names = {
        family_name
        for target in ordered_targets
        for candidate in compiled_targets_by_target[target].base_candidates
        for family_name in _normalize_family_names(candidate.metadata.get("kaikki_family_names"))
    }
    return {name: index for index, name in enumerate(sorted(names))}


def _normalize_family_names(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def _normalize_optional_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        return text in {"1", "true", "yes", "on"}
    return False


def _normalize_non_negative_optional_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = int(text)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def _normalize_optional_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0
    return 0.0


def _build_compiled_candidate_fact(
    *,
    candidate: RuleCandidate,
    candidate_id: int,
    target_id: int,
    definition_bucket_ids_by_key: Mapping[str, int],
    family_marker_ids_by_name: Mapping[str, int],
    source_dict_ids_by_name: Mapping[str, int],
    source_type_ids_by_name: Mapping[str, int],
) -> EnEsCompiledCandidateFact:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    bucket_key = str(metadata.get("definition_bucket_key") or "").strip()
    family_names = _normalize_family_names(metadata.get("kaikki_family_names"))
    phrase = str(candidate.source_phrase or "").strip()
    semantic_demotion_reason = str(metadata.get("semantic_demotion_reason") or "").strip() or None
    return EnEsCompiledCandidateFact(
        candidate_id=int(candidate_id),
        target_id=int(target_id),
        definition_bucket_id=int(definition_bucket_ids_by_key.get(bucket_key, -1)),
        source_dict_id=int(source_dict_ids_by_name.get(candidate.source_dict, -1)),
        source_type_id=int(source_type_ids_by_name.get(candidate.source_type, -1)),
        local_candidate_index=int(
            _normalize_non_negative_optional_int(metadata.get("compiled_candidate_index")) or 0
        ),
        gloss_index=int(_normalize_non_negative_optional_int(metadata.get("gloss_index")) or 0),
        gloss_total=int(_normalize_non_negative_optional_int(metadata.get("gloss_total")) or 0),
        source_phrase=phrase,
        reverse_check_source_norm=str(metadata.get("reverse_check_source_norm") or "").strip(),
        reverse_check_target_norm=str(metadata.get("reverse_check_target_norm") or "").strip(),
        reverse_check_supported=_normalize_optional_bool(metadata.get("reverse_check_supported")),
        reverse_check_hit=_normalize_optional_bool(metadata.get("reverse_check_hit")),
        reverse_check_rank=_normalize_non_negative_optional_int(metadata.get("reverse_check_rank")),
        reverse_check_total=int(
            _normalize_non_negative_optional_int(metadata.get("reverse_check_total")) or 0
        ),
        source_phrase_token_count=len(phrase.split()) if phrase else 0,
        source_phrase_is_ascii=bool(phrase) and all(ord(ch) < 128 for ch in phrase),
        source_phrase_is_phrase=" " in phrase,
        is_variant=_normalize_optional_bool(metadata.get("variant")),
        source_pos_canonical=str(candidate.metadata.get("source_pos_canonical") or "")
        .strip()
        .lower(),
        target_pos_canonical=str(candidate.metadata.get("target_pos_canonical") or "")
        .strip()
        .lower(),
        dictionary_pos_canonical=str(candidate.metadata.get("dictionary_pos_canonical") or "")
        .strip()
        .lower(),
        semantic_demotion_base=max(
            0.0, _normalize_optional_float(metadata.get("semantic_demotion"))
        ),
        semantic_demotion_reason=semantic_demotion_reason,
        interjection_shadowed=_normalize_optional_bool(metadata.get("interjection_shadowed")),
        has_word_package=isinstance(metadata.get("word_package"), Mapping),
        has_gloss_provenance=isinstance(metadata.get("gloss_provenance"), Mapping),
        has_sense_provenance=isinstance(metadata.get("sense_provenance"), Mapping),
        has_target_provenance=isinstance(metadata.get("target_provenance"), Mapping),
        current_sense_position=int(
            _normalize_non_negative_optional_int(
                (
                    metadata.get("target_provenance").get("current_sense_position")
                    if isinstance(metadata.get("target_provenance"), Mapping)
                    else None
                )
            )
            or 0
        ),
        kaikkei_family_names=family_names,
        family_marker_ids=tuple(
            family_marker_ids_by_name[name]
            for name in family_names
            if name in family_marker_ids_by_name
        ),
    )


def _build_compiled_candidate_table(
    candidate_facts: Sequence[EnEsCompiledCandidateFact],
) -> EnEsCompiledCandidateTable:
    candidate_ids: list[int] = []
    target_ids: list[int] = []
    definition_bucket_ids: list[int] = []
    source_phrases: list[str] = []
    source_phrase_lowers: list[str] = []
    source_dict_ids: list[int] = []
    source_type_ids: list[int] = []
    local_candidate_indices: list[int] = []
    gloss_indices: list[int] = []
    gloss_totals: list[int] = []
    semantic_demotion_bases: list[float] = []
    source_pos_canonicals: list[str] = []
    target_pos_canonicals: list[str] = []
    dictionary_pos_canonicals: list[str] = []
    phrase_flags: list[bool] = []
    variant_flags: list[bool] = []
    interjection_shadowed_flags: list[bool] = []
    reverse_check_supported_flags: list[bool] = []
    reverse_check_hit_flags: list[bool] = []
    reverse_check_rank_values: list[int] = []
    reverse_check_total_values: list[int] = []
    current_sense_positions: list[int] = []
    family_marker_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_by_candidate_id: dict[int, int] = {}
    candidate_row_ids_by_target_id: dict[int, list[int]] = {}
    candidate_row_ids_by_definition_bucket_id: dict[int, list[int]] = {}
    candidate_row_ids_by_family_marker_id: dict[int, list[int]] = {}

    for row_id, fact in enumerate(candidate_facts):
        candidate_ids.append(int(fact.candidate_id))
        target_ids.append(int(fact.target_id))
        definition_bucket_ids.append(int(fact.definition_bucket_id))
        source_phrases.append(str(fact.source_phrase))
        source_phrase_lowers.append(str(fact.source_phrase).lower())
        source_dict_ids.append(int(fact.source_dict_id))
        source_type_ids.append(int(fact.source_type_id))
        local_candidate_indices.append(int(fact.local_candidate_index))
        gloss_indices.append(int(fact.gloss_index))
        gloss_totals.append(int(fact.gloss_total))
        semantic_demotion_bases.append(float(fact.semantic_demotion_base))
        source_pos_canonicals.append(str(fact.source_pos_canonical))
        target_pos_canonicals.append(str(fact.target_pos_canonical))
        dictionary_pos_canonicals.append(str(fact.dictionary_pos_canonical))
        phrase_flags.append(bool(fact.source_phrase_is_phrase))
        variant_flags.append(bool(fact.is_variant))
        interjection_shadowed_flags.append(bool(fact.interjection_shadowed))
        reverse_check_supported_flags.append(bool(fact.reverse_check_supported))
        reverse_check_hit_flags.append(bool(fact.reverse_check_hit))
        reverse_check_rank_values.append(
            int(fact.reverse_check_rank) if fact.reverse_check_rank is not None else -1
        )
        reverse_check_total_values.append(int(fact.reverse_check_total))
        current_sense_positions.append(int(fact.current_sense_position))
        family_marker_id_rows.append(tuple(int(value) for value in fact.family_marker_ids))

        candidate_row_id_by_candidate_id[int(fact.candidate_id)] = row_id
        if fact.target_id >= 0:
            candidate_row_ids_by_target_id.setdefault(int(fact.target_id), []).append(row_id)
        if fact.definition_bucket_id >= 0:
            candidate_row_ids_by_definition_bucket_id.setdefault(
                int(fact.definition_bucket_id), []
            ).append(row_id)
        for family_marker_id in fact.family_marker_ids:
            if family_marker_id >= 0:
                candidate_row_ids_by_family_marker_id.setdefault(int(family_marker_id), []).append(
                    row_id
                )

    return EnEsCompiledCandidateTable(
        candidate_ids=tuple(candidate_ids),
        target_ids=tuple(target_ids),
        definition_bucket_ids=tuple(definition_bucket_ids),
        source_phrases=tuple(source_phrases),
        source_phrase_lowers=tuple(source_phrase_lowers),
        source_dict_ids=tuple(source_dict_ids),
        source_type_ids=tuple(source_type_ids),
        local_candidate_indices=tuple(local_candidate_indices),
        gloss_indices=tuple(gloss_indices),
        gloss_totals=tuple(gloss_totals),
        semantic_demotion_bases=tuple(semantic_demotion_bases),
        source_pos_canonicals=tuple(source_pos_canonicals),
        target_pos_canonicals=tuple(target_pos_canonicals),
        dictionary_pos_canonicals=tuple(dictionary_pos_canonicals),
        phrase_flags=tuple(phrase_flags),
        variant_flags=tuple(variant_flags),
        interjection_shadowed_flags=tuple(interjection_shadowed_flags),
        reverse_check_supported_flags=tuple(reverse_check_supported_flags),
        reverse_check_hit_flags=tuple(reverse_check_hit_flags),
        reverse_check_rank_values=tuple(reverse_check_rank_values),
        reverse_check_total_values=tuple(reverse_check_total_values),
        current_sense_positions=tuple(current_sense_positions),
        family_marker_id_rows=tuple(family_marker_id_rows),
        candidate_row_id_by_candidate_id=dict(candidate_row_id_by_candidate_id),
        candidate_row_ids_by_target_id={
            key: tuple(value) for key, value in sorted(candidate_row_ids_by_target_id.items())
        },
        candidate_row_ids_by_definition_bucket_id={
            key: tuple(value)
            for key, value in sorted(candidate_row_ids_by_definition_bucket_id.items())
        },
        candidate_row_ids_by_family_marker_id={
            key: tuple(value)
            for key, value in sorted(candidate_row_ids_by_family_marker_id.items())
        },
    )


def _finalize_compiled_target_contexts(
    *,
    compiled_targets_by_target: Mapping[str, EnEsCompiledTargetContext],
    ordered_targets: Sequence[str],
    target_ids_by_target: Mapping[str, int],
    definition_bucket_ids_by_key: Mapping[str, int],
    family_marker_ids_by_name: Mapping[str, int],
    source_dict_ids_by_name: Mapping[str, int],
    source_type_ids_by_name: Mapping[str, int],
) -> tuple[dict[str, EnEsCompiledTargetContext], tuple[EnEsCompiledCandidateFact, ...]]:
    finalized_targets_by_target: dict[str, EnEsCompiledTargetContext] = {}
    candidate_facts: list[EnEsCompiledCandidateFact] = []
    next_candidate_id = 0
    for target in ordered_targets:
        target_context = compiled_targets_by_target[target]
        target_id = int(target_ids_by_target.get(target, -1))
        finalized_candidates: list[RuleCandidate] = []
        finalized_facts: list[EnEsCompiledCandidateFact] = []
        for candidate in target_context.base_candidates:
            metadata = dict(candidate.metadata)
            bucket_key = str(metadata.get("definition_bucket_key") or "").strip()
            family_names = _normalize_family_names(metadata.get("kaikki_family_names"))
            metadata["compiled_target_id"] = target_id
            metadata["compiled_candidate_id"] = next_candidate_id
            metadata["compiled_definition_bucket_id"] = definition_bucket_ids_by_key.get(
                bucket_key, -1
            )
            metadata["compiled_family_marker_ids"] = tuple(
                family_marker_ids_by_name[name]
                for name in family_names
                if name in family_marker_ids_by_name
            )
            metadata["compiled_source_dict_id"] = source_dict_ids_by_name.get(
                candidate.source_dict, -1
            )
            metadata["compiled_source_type_id"] = source_type_ids_by_name.get(
                candidate.source_type, -1
            )
            finalized_candidate = replace(candidate, metadata=metadata)
            fact = _build_compiled_candidate_fact(
                candidate=finalized_candidate,
                candidate_id=next_candidate_id,
                target_id=target_id,
                definition_bucket_ids_by_key=definition_bucket_ids_by_key,
                family_marker_ids_by_name=family_marker_ids_by_name,
                source_dict_ids_by_name=source_dict_ids_by_name,
                source_type_ids_by_name=source_type_ids_by_name,
            )
            finalized_candidates.append(finalized_candidate)
            finalized_facts.append(fact)
            candidate_facts.append(fact)
            next_candidate_id += 1
        finalized_targets_by_target[target] = replace(
            target_context,
            target_id=target_id,
            base_candidates=tuple(finalized_candidates),
            candidate_facts=tuple(finalized_facts),
        )
    return finalized_targets_by_target, tuple(candidate_facts)


def _apply_kaikki_policy_overlay(
    *,
    metadata: dict[str, object],
    shadow: Mapping[str, object],
    kaikki_policy: EnEsKaikkiPolicyConfig,
) -> None:
    shadow_metadata = dict(shadow)
    if kaikki_policy.enable_live_demotion:
        demotion, reasons = _resolve_kaikki_policy_live_demotion(shadow_metadata)
        if demotion > 0.0:
            _apply_semantic_demotion(
                metadata,
                demotion=demotion,
                reason=";".join(reasons) if reasons else "kaikki_policy",
            )
            shadow_metadata["live_demotion_applied"] = True
            shadow_metadata["live_demotion_value"] = demotion
            if reasons:
                shadow_metadata["live_demotion_reasons"] = reasons
    provenance_demotion, provenance_reasons = _resolve_kaikki_provenance_competition_demotion(
        target_provenance=(
            metadata.get("target_provenance")
            if isinstance(metadata.get("target_provenance"), Mapping)
            else None
        ),
        gloss_provenance=(
            metadata.get("gloss_provenance")
            if isinstance(metadata.get("gloss_provenance"), Mapping)
            else None
        ),
        shadow=shadow_metadata,
        late_sense_clean_earlier_competition_penalty=(
            kaikki_policy.late_sense_clean_earlier_competition_penalty
        ),
    )
    if provenance_demotion > 0.0:
        _apply_semantic_demotion(
            metadata,
            demotion=provenance_demotion,
            reason=";".join(provenance_reasons) if provenance_reasons else "kaikki_provenance",
        )
        shadow_metadata["provenance_demotion_applied"] = True
        shadow_metadata["provenance_demotion_value"] = provenance_demotion
        if provenance_reasons:
            shadow_metadata["provenance_demotion_reasons"] = provenance_reasons
    if shadow_metadata:
        metadata["kaikki_policy_shadow"] = shadow_metadata


def build_en_es_pipeline(config: EnEsRulegenConfig) -> RuleGenerationPipeline:
    compiled_resources = config.compiled_resources
    compiled_candidate_filter_table = (
        build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=config,
        )
        if compiled_resources is not None and not config.include_variants
        else None
    )
    records_by_target = (
        compiled_resources.records_by_target
        if compiled_resources is not None
        else _resolve_gloss_records(config)
    )
    reverse_records_by_source = (
        compiled_resources.reverse_records_by_source
        if compiled_resources is not None
        else _resolve_reverse_gloss_records(config)
    )
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
        compiled_resources=compiled_resources,
        compiled_filter_table=compiled_candidate_filter_table,
    )
    normalizers: list[CandidateNormalizer] = (
        []
        if compiled_candidate_filter_table is not None
        else [
            BasicStringNormalizer(),
            LeadingEnglishInfinitiveNormalizer(),
        ]
    )
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

    ranking_mechanism = DictionaryEntryOrderRankingMechanism(reverse_check=config.reverse_check)
    if compiled_resources is not None:
        candidate_row_id_by_candidate_id = (
            dict(compiled_resources.candidate_table.candidate_row_id_by_candidate_id)
            if compiled_resources.candidate_table is not None
            else {}
        )
        compiled_candidate_score_table = build_en_es_compiled_candidate_score_table(
            compiled_resources=compiled_resources,
            config=config,
        )
        signal_provider = EnEsCompiledSignalProvider(
            dict_priorities={config.source_dict_id: config.dict_priority},
            gloss_decay=config.gloss_decay,
            pos_match=config.scoring.pos_match,
            variant_penalty=config.variant_penalty,
            candidate_facts_by_id={
                fact.candidate_id: fact for fact in compiled_resources.candidate_facts
            },
            candidate_row_id_by_candidate_id=candidate_row_id_by_candidate_id,
            score_table=compiled_candidate_score_table,
        )
        ranking_mechanism = EnEsCompiledRankingMechanism(
            fallback=ranking_mechanism,
            candidate_row_id_by_candidate_id=candidate_row_id_by_candidate_id,
            score_table=compiled_candidate_score_table,
        )
    else:
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
        filters=_build_filters(
            config,
            gloss_mapping=(
                None
                if compiled_resources is not None
                else _records_to_gloss_mapping(records_by_target)
            ),
            gloss_base_forms=(
                set(compiled_resources.gloss_base_forms) if compiled_resources is not None else None
            ),
        )
        if compiled_candidate_filter_table is None
        else [],
        scorer=RuleScorer(weights=config.scoring.weights),
        signal_provider=signal_provider,
        ranking_mechanism=ranking_mechanism,
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
        compiled_resources: Optional[EnEsCompiledResources] = None,
        compiled_filter_table: Optional[EnEsCompiledCandidateFilterTable] = None,
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._reverse_source_dict = str(reverse_source_dict or "").strip()
        self._compiled_targets_by_target = (
            dict(compiled_resources.compiled_targets_by_target)
            if compiled_resources is not None
            else {}
        )
        self._reverse_lookup = (
            compiled_resources.reverse_lookup
            if compiled_resources is not None and compiled_resources.reverse_lookup is not None
            else (
                _build_reverse_lookup(reverse_records_by_source)
                if reverse_records_by_source is not None
                else None
            )
        )
        self._compiled_candidate_table = (
            compiled_resources.candidate_table if compiled_resources is not None else None
        )
        self._compiled_filter_table = compiled_filter_table
        self._compiled_base_candidates_by_id = (
            {
                int(candidate_id): candidate
                for context in self._compiled_targets_by_target.values()
                for candidate in context.base_candidates
                for candidate_id in (
                    _normalize_non_negative_optional_int(
                        (
                            candidate.metadata.get("compiled_candidate_id")
                            if isinstance(candidate.metadata, Mapping)
                            else None
                        )
                    ),
                )
                if candidate_id is not None
            }
            if compiled_filter_table is not None
            else {}
        )
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._dictionary_pos_source_profile = str(dictionary_pos_source_profile or "").strip() or (
            "freedict"
        )
        self._kaikki_policy = kaikki_policy or EnEsKaikkiPolicyConfig()

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            compiled_target = self._compiled_targets_by_target.get(target)
            if compiled_target is not None:
                canonical_inventory = compiled_target.canonical_inventory
                dictionary_record_views_by_index = compiled_target.dictionary_record_views_by_index
                base_candidates = compiled_target.base_candidates
                kaikkei_policy_shadow_by_index = (
                    _build_kaikki_policy_shadow_by_index(
                        dictionary_record_views_by_index=dictionary_record_views_by_index,
                        canonical_inventory=canonical_inventory,
                        risk_families=self._kaikki_policy.risk_families,
                    )
                    if self._kaikki_policy.enable_shadow_metadata
                    else [{} for _ in base_candidates]
                )
                if (
                    self._compiled_filter_table is not None
                    and self._compiled_candidate_table is not None
                ):
                    accepted_row_ids = (
                        self._compiled_filter_table.accepted_candidate_row_ids_by_target_id.get(
                            compiled_target.target_id,
                            (),
                        )
                    )
                    for row_id in accepted_row_ids:
                        candidate_id = int(self._compiled_candidate_table.candidate_ids[row_id])
                        base_candidate = self._compiled_base_candidates_by_id.get(candidate_id)
                        if base_candidate is None:
                            continue
                        metadata = dict(base_candidate.metadata)
                        metadata["reverse_check_source_dict"] = self._reverse_source_dict or None
                        local_index = int(
                            _normalize_non_negative_optional_int(
                                metadata.get("compiled_candidate_index")
                            )
                            or 0
                        )
                        if local_index < len(kaikkei_policy_shadow_by_index):
                            _apply_kaikki_policy_overlay(
                                metadata=metadata,
                                shadow=kaikkei_policy_shadow_by_index[local_index],
                                kaikki_policy=self._kaikki_policy,
                            )
                        yield replace(
                            base_candidate,
                            source_phrase=self._compiled_filter_table.normalized_source_phrases[
                                row_id
                            ],
                            language_pair=language_pair,
                            source_dict=self._source_dict,
                            source_type=self._source_type,
                            metadata=metadata,
                        )
                    continue
            else:
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
                entries = tuple(
                    _collect_sanitized_gloss_records(self._records_by_target.get(target, ()))
                )
                dictionary_poses = tuple(
                    normalize_pos_component(
                        entry.pos_raw,
                        language_pair=language_pair,
                        source_provider=self._source_dict,
                        source_kind="dictionary",
                        source_profile=self._dictionary_pos_source_profile,
                    )
                    for entry in entries
                )
                canonical_inventory = tuple(
                    _extract_canonical_from_component(component) for component in dictionary_poses
                )
                dictionary_record_views_by_index = []
                for entry in entries:
                    if entry.metadata:
                        raw_record = dict(entry.metadata)
                        dictionary_record_views = build_kaikki_record_views(raw_record)
                        if dictionary_record_views:
                            dictionary_record_views_by_index.append(
                                {"kaikki": dictionary_record_views}
                            )
                            continue
                    dictionary_record_views_by_index.append({})
                target_provenance_by_index = tuple(
                    _build_target_provenance_by_index(
                        target=target,
                        entries=entries,
                        canonical_inventory=canonical_inventory,
                    )
                )
                base_candidates = _build_static_candidate_inventory(
                    target=target,
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    target_reverse_norm=target_reverse_norm,
                    target_word_package=target_word_package,
                    target_pos=target_pos,
                    entries=entries,
                    dictionary_poses=dictionary_poses,
                    canonical_inventory=canonical_inventory,
                    dictionary_record_views_by_index=tuple(dictionary_record_views_by_index),
                    target_provenance_by_index=target_provenance_by_index,
                    reverse_lookup=self._reverse_lookup,
                    generic_gloss_demotions=self._generic_gloss_demotions,
                )
                kaikkei_policy_shadow_by_index = (
                    _build_kaikki_policy_shadow_by_index(
                        dictionary_record_views_by_index=dictionary_record_views_by_index,
                        canonical_inventory=canonical_inventory,
                        risk_families=self._kaikki_policy.risk_families,
                    )
                    if self._kaikki_policy.enable_shadow_metadata
                    else [{} for _ in base_candidates]
                )
            for index, base_candidate in enumerate(base_candidates):
                metadata = dict(base_candidate.metadata)
                metadata["reverse_check_source_dict"] = self._reverse_source_dict or None
                if index < len(kaikkei_policy_shadow_by_index):
                    _apply_kaikki_policy_overlay(
                        metadata=metadata,
                        shadow=kaikkei_policy_shadow_by_index[index],
                        kaikki_policy=self._kaikki_policy,
                    )
                yield replace(
                    base_candidate,
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata=metadata,
                )


def _build_filters(
    config: EnEsRulegenConfig,
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None,
    gloss_base_forms: Optional[set[str]] = None,
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
        base_forms = (
            set(gloss_base_forms)
            if gloss_base_forms is not None
            else _build_gloss_base_forms(gloss_mapping or {})
        )
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
