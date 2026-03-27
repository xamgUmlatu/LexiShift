from __future__ import annotations

from dataclasses import dataclass, field, replace
import os
from pathlib import Path
import re
from typing import Iterable, Mapping, Optional, Sequence

import numpy as np

try:
    import torch
except Exception:  # pragma: no cover - optional dependency
    torch = None

from lexishift_core.pos.normalization import (
    CANONICAL_POS_ADPOSITION,
    CANONICAL_POS_CONJUNCTION,
    CANONICAL_POS_DETERMINER,
    CANONICAL_POS_NOUN,
    CANONICAL_POS_PRONOUN,
)
from lexishift_core.resources.dict_loaders import (
    TranslationGlossRecord,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views
from lexishift_core.rulegen.generation import (
    CandidateNormalizer,
    CandidateFilter,
    DEFAULT_POS_COMPATIBILITY_CLASSES,
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
    extract_candidate_pos_canonical,
    materialize_rule_generation_result,
    resolve_reverse_hygiene_anchor_allowed_from_values,
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
_DEFAULT_STOPWORDS_FROZEN = frozenset(DEFAULT_STOPWORDS)
_COMPILED_FILTER_TABLE_CACHE: dict[
    tuple[int, tuple[object, ...]],
    "EnEsCompiledCandidateFilterTable",
] = {}
_COMPILED_SCORE_TABLE_CACHE: dict[
    tuple[int, tuple[object, ...]],
    "EnEsCompiledCandidateScoreTable",
] = {}
_COMPILED_SELECTED_ROW_TABLE_CACHE: dict[
    tuple[int, tuple[object, ...]],
    "EnEsCompiledSelectedRowTable",
] = {}
_COMPILED_OVERLAY_DEMOTION_ROWS_CACHE: dict[
    tuple[int, tuple[object, ...]],
    tuple[float, ...],
] = {}
_COMPILED_BENCHMARK_VARIANT_CANDIDATE_TABLE_CACHE: dict[
    int,
    "EnEsCompiledCandidateTable",
] = {}
_COMPILED_RESOURCE_CACHE_TOKEN = 0


def _next_compiled_resource_cache_token() -> int:
    global _COMPILED_RESOURCE_CACHE_TOKEN
    _COMPILED_RESOURCE_CACHE_TOKEN += 1
    return int(_COMPILED_RESOURCE_CACHE_TOKEN)


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
    normalized_source_phrases: tuple[str, ...] = ()
    normalized_source_phrase_order_ids: tuple[int, ...] = ()
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
    effective_semantic_demotion_values: tuple[float, ...] = ()
    reverse_check_delta_values: tuple[float, ...] = ()
    reverse_check_strength_values: tuple[Optional[float], ...] = ()
    reverse_hygiene_anchor_allowed_flags: tuple[bool, ...] = ()
    confidence_scores: tuple[float, ...] = ()
    ranking_scores: tuple[float, ...] = ()
    row_sort_keys: tuple[tuple[float, float, int], ...] = ()
    selected_row_signature: tuple[object, ...] = ()
    ranked_candidate_row_ids_by_target_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class EnEsCompiledCandidateFilterTable:
    candidate_ids: tuple[int, ...] = ()
    target_ids: tuple[int, ...] = ()
    normalized_source_phrases: tuple[str, ...] = ()
    definition_group_ids: tuple[int, ...] = ()
    non_empty_flags: tuple[bool, ...] = ()
    gloss_shape_flags: tuple[bool, ...] = ()
    length_flags: tuple[bool, ...] = ()
    possessive_flags: tuple[bool, ...] = ()
    shadowed_interjection_flags: tuple[bool, ...] = ()
    stopword_flags: tuple[bool, ...] = ()
    inflection_artifact_flags: tuple[bool, ...] = ()
    accepted_flags: tuple[bool, ...] = ()
    selected_row_signature: tuple[object, ...] = ()
    accepted_candidate_row_ids_by_target_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )
    accepted_candidate_row_id_groups_by_target_id: Mapping[int, tuple[tuple[int, ...], ...]] = (
        field(default_factory=dict)
    )


@dataclass(frozen=True)
class EnEsCompiledSelectedRowTable:
    targets: tuple[str, ...] = ()
    candidate_row_id_rows: tuple[tuple[int, ...], ...] = ()
    normalized_source_phrase_rows: tuple[tuple[str, ...], ...] = ()
    top1_confidences: tuple[Optional[float], ...] = ()
    variant_rule_counts: tuple[int, ...] = ()
    top1_variant_flags: tuple[bool, ...] = ()
    row_id_by_target: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EnEsCompiledBenchmarkEvaluationTables:
    filter_table: EnEsCompiledCandidateFilterTable = field(
        default_factory=EnEsCompiledCandidateFilterTable
    )
    score_table: EnEsCompiledCandidateScoreTable = field(
        default_factory=EnEsCompiledCandidateScoreTable
    )


@dataclass(frozen=True)
class EnEsCompiledBenchmarkSweepTables:
    filter_table: EnEsCompiledCandidateFilterTable = field(
        default_factory=EnEsCompiledCandidateFilterTable
    )
    score_table: EnEsCompiledCandidateScoreTable = field(
        default_factory=EnEsCompiledCandidateScoreTable
    )
    selected_row_table: EnEsCompiledSelectedRowTable = field(
        default_factory=EnEsCompiledSelectedRowTable
    )


@dataclass(frozen=True)
class EnEsCompiledDefinitionRowGroup:
    row_ids: tuple[int, ...] = ()
    sorted_row_ids: tuple[int, ...] = ()
    best_row_id: int = -1
    sort_key: tuple[float, float, int] = (0.0, 0.0, 0)
    reverse_strength: Optional[float] = None
    allows_reverse_hygiene_anchor: bool = False


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


@dataclass
class _EnEsCompiledScoreBatchProjection:
    cache_key: tuple[int, tuple[object, ...]]
    config: EnEsRulegenConfig
    source_dict_id: Optional[int]
    overlay_rows: tuple[float, ...]
    dict_priority_values: list[float] = field(default_factory=list)
    frequency_weight_values: list[float] = field(default_factory=list)
    pos_match_values: list[float] = field(default_factory=list)
    variant_penalty_values: list[float] = field(default_factory=list)
    phrase_penalty_values: list[float] = field(default_factory=list)
    effective_semantic_demotion_values: list[float] = field(default_factory=list)
    reverse_check_delta_values: list[float] = field(default_factory=list)
    reverse_check_strength_values: list[Optional[float]] = field(default_factory=list)
    reverse_hygiene_anchor_allowed_flags: list[bool] = field(default_factory=list)
    confidence_scores: list[float] = field(default_factory=list)
    ranking_scores: list[float] = field(default_factory=list)
    row_sort_keys: list[tuple[float, float, int]] = field(default_factory=list)
    gloss_weight_cache: dict[Optional[int], float] = field(default_factory=dict)
    pos_match_cache: dict[tuple[str, str], float] = field(default_factory=dict)


@dataclass(frozen=True)
class _EnEsCompiledScoreConfigMatrix:
    source_dict_ids: np.ndarray
    dict_priority: np.ndarray
    gloss_schedule_keys: tuple[tuple[float, ...], ...]
    pos_match_enabled: np.ndarray
    pos_match_exact_bonus: np.ndarray
    pos_match_compatible_bonus: np.ndarray
    compatibility_keys: tuple[Optional[tuple[tuple[str, str], ...]], ...]
    variant_penalty: np.ndarray
    semantic_demotion_scale: np.ndarray
    reverse_enabled: np.ndarray
    reverse_match_bonus: np.ndarray
    reverse_near_bonus: np.ndarray
    reverse_near_rank_max: np.ndarray
    reverse_far_hit_penalty: np.ndarray
    reverse_miss_penalty: np.ndarray
    reverse_exact_hit_ambiguity_threshold: np.ndarray
    reverse_exact_hit_ambiguity_penalty: np.ndarray
    reverse_exact_hit_specificity_bonus: np.ndarray
    score_weight_dict_priority: np.ndarray
    score_weight_frequency_weight: np.ndarray
    score_weight_pos_match: np.ndarray
    score_weight_variant_penalty: np.ndarray
    score_weight_phrase_penalty: np.ndarray
    overlay_rows: np.ndarray


def _resolve_compiled_score_backend(*, config_count: int, row_count: int) -> str:
    requested = str(os.environ.get("LEXISHIFT_RULEGEN_SCORE_BACKEND") or "numpy").strip().lower()
    if requested in {"", "numpy", "cpu"}:
        return "numpy"
    if requested == "auto":
        if (
            torch is None
            or not bool(getattr(torch, "cuda", None))
            or not bool(torch.cuda.is_available())
        ):
            return "numpy"
        return "torch-cuda" if (config_count * row_count) >= 32768 else "numpy"
    if requested in {"torch", "cuda", "torch-cuda"}:
        if (
            torch is None
            or not bool(getattr(torch, "cuda", None))
            or not bool(torch.cuda.is_available())
        ):
            return "numpy"
        return "torch-cuda"
    return "numpy"


@dataclass(frozen=True)
class EnEsCompiledTargetContext:
    target: str
    target_reverse_norm: str
    target_word_package: Optional[Mapping[str, object]]
    target_pos: Mapping[str, object]
    entries: tuple[TranslationGlossRecord, ...]
    dictionary_poses: tuple[Mapping[str, object], ...]
    canonical_inventory: tuple[str, ...]
    dictionary_record_views_by_index: tuple[Mapping[str, object], ...]
    target_provenance_by_index: tuple[Mapping[str, object], ...]
    target_id: int = -1
    base_candidates: tuple[RuleCandidate, ...] = ()
    candidate_facts: tuple[EnEsCompiledCandidateFact, ...] = ()


@dataclass(frozen=True)
class EnEsCompiledResources:
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]]
    reverse_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
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
    cache_token: int = -1


@dataclass(frozen=True)
class EnEsRulegenConfig:
    freedict_es_en_path: Path
    reverse_freedict_en_es_path: Optional[Path] = None
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
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
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
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
        cache_token=_next_compiled_resource_cache_token(),
    )


def build_en_es_compiled_candidate_score_table(
    *,
    compiled_resources: EnEsCompiledResources,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateScoreTable:
    candidate_table = compiled_resources.candidate_table
    return _build_compiled_candidate_score_table_for_table(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        candidate_table_cache_token=("base", int(compiled_resources.cache_token)),
        config=config,
    )


def _build_compiled_candidate_score_table_for_table(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: Optional[EnEsCompiledCandidateTable],
    candidate_table_cache_token: object,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateScoreTable:
    return _build_compiled_candidate_score_tables_for_table(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        candidate_table_cache_token=candidate_table_cache_token,
        configs=(config,),
    )[0]


def _build_compiled_candidate_score_tables_for_table(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: Optional[EnEsCompiledCandidateTable],
    candidate_table_cache_token: object,
    configs: Sequence[EnEsRulegenConfig],
) -> tuple[EnEsCompiledCandidateScoreTable, ...]:
    if candidate_table is None:
        return tuple(EnEsCompiledCandidateScoreTable() for _ in configs)
    if not configs:
        return ()
    resolved_tables: list[Optional[EnEsCompiledCandidateScoreTable]] = [None] * len(configs)
    pending: list[_EnEsCompiledScoreBatchProjection] = []
    for index, config in enumerate(configs):
        cache_key = _build_compiled_score_table_cache_key(
            compiled_resources=compiled_resources,
            candidate_table_cache_token=candidate_table_cache_token,
            config=config,
        )
        cached = _COMPILED_SCORE_TABLE_CACHE.get(cache_key)
        if cached is not None:
            resolved_tables[index] = cached
            continue
        source_dict_id = next(
            (
                int(candidate_source_dict_id)
                for name, candidate_source_dict_id in compiled_resources.source_dict_ids_by_name.items()
                if name == config.source_dict_id
            ),
            None,
        )
        pending.append(
            _EnEsCompiledScoreBatchProjection(
                cache_key=cache_key,
                config=config,
                source_dict_id=source_dict_id,
                overlay_rows=_resolve_compiled_overlay_demotion_rows(
                    compiled_resources=compiled_resources,
                    candidate_table=candidate_table,
                    candidate_table_cache_token=candidate_table_cache_token,
                    config=config,
                ),
            )
        )
    if pending:
        _materialize_compiled_candidate_score_table_batch(
            compiled_resources=compiled_resources,
            candidate_table=candidate_table,
            pending=pending,
        )
        cache_lookup = {
            projection.cache_key: _COMPILED_SCORE_TABLE_CACHE[projection.cache_key]
            for projection in pending
        }
        for index, config in enumerate(configs):
            if resolved_tables[index] is not None:
                continue
            cache_key = _build_compiled_score_table_cache_key(
                compiled_resources=compiled_resources,
                candidate_table_cache_token=candidate_table_cache_token,
                config=config,
            )
            resolved_tables[index] = cache_lookup[cache_key]
    return tuple(
        table if table is not None else EnEsCompiledCandidateScoreTable()
        for table in resolved_tables
    )


def _compatibility_classes_cache_key(
    compatibility_classes: Optional[Mapping[str, str]],
) -> Optional[tuple[tuple[str, str], ...]]:
    if compatibility_classes is None:
        return None
    return tuple(sorted((str(key), str(value)) for key, value in compatibility_classes.items()))


def _vectorized_gloss_decay_values(
    *,
    gloss_indices: np.ndarray,
    schedule: Sequence[float],
) -> np.ndarray:
    if not schedule:
        return np.ones(gloss_indices.shape, dtype=np.float64)
    schedule_array = np.asarray(tuple(float(value) for value in schedule), dtype=np.float64)
    resolved = np.ones(gloss_indices.shape, dtype=np.float64)
    non_negative_mask = gloss_indices >= 0
    if np.any(non_negative_mask):
        clamped_indices = np.clip(
            gloss_indices[non_negative_mask],
            0,
            max(0, int(schedule_array.shape[0]) - 1),
        )
        resolved[non_negative_mask] = schedule_array[clamped_indices]
    return resolved


def _resolve_vectorized_pos_match_masks(
    *,
    source_pos_for_match: Sequence[str],
    target_pos_canonicals: Sequence[str],
    compatibility_classes: Optional[Mapping[str, str]],
) -> tuple[np.ndarray, np.ndarray]:
    source_array = np.asarray(tuple(str(pos or "") for pos in source_pos_for_match), dtype=object)
    target_array = np.asarray(tuple(str(pos or "") for pos in target_pos_canonicals), dtype=object)
    exact_mask = source_array == target_array
    classes = compatibility_classes or DEFAULT_POS_COMPATIBILITY_CLASSES
    source_class_array = np.asarray(
        tuple(str(classes.get(str(pos), "")).strip() for pos in source_array),
        dtype=object,
    )
    target_class_array = np.asarray(
        tuple(str(classes.get(str(pos), "")).strip() for pos in target_array),
        dtype=object,
    )
    compatible_mask = (source_class_array != "") & (source_class_array == target_class_array)
    compatible_mask &= ~exact_mask
    return exact_mask, compatible_mask


def _vectorized_effective_semantic_demotion_values(
    *,
    semantic_demotion_values: np.ndarray,
    scale: float,
) -> np.ndarray:
    if scale <= 0.0:
        return np.zeros(semantic_demotion_values.shape, dtype=np.float64)
    clipped_base = np.clip(semantic_demotion_values.astype(np.float64, copy=False), 0.0, 1.0)
    return np.clip(clipped_base * float(scale), 0.0, 1.0)


def _vectorized_reverse_far_hit_penalty(
    *,
    rank_values: np.ndarray,
    total_values: np.ndarray,
    penalty: float,
) -> np.ndarray:
    normalized_penalty = max(0.0, float(penalty))
    if normalized_penalty <= 0.0:
        return np.zeros(rank_values.shape, dtype=np.float64)
    normalized_rank_values = np.maximum(rank_values.astype(np.int64, copy=False), 0)
    resolved = np.full(rank_values.shape, normalized_penalty, dtype=np.float64)
    scalable_mask = total_values > 1
    if np.any(scalable_mask):
        max_rank_values = np.maximum(
            total_values[scalable_mask].astype(np.int64, copy=False) - 1,
            0,
        )
        effective_rank_values = np.minimum(normalized_rank_values[scalable_mask], max_rank_values)
        scalable_penalties = np.full(
            effective_rank_values.shape, normalized_penalty, dtype=np.float64
        )
        valid_mask = max_rank_values > 0
        if np.any(valid_mask):
            scalable_penalties[valid_mask] = normalized_penalty * (
                effective_rank_values[valid_mask] / max_rank_values[valid_mask].astype(np.float64)
            )
        resolved[scalable_mask] = scalable_penalties
    return resolved


def _vectorized_reverse_exact_hit_ambiguity_penalty(
    *,
    total_values: np.ndarray,
    config: ReverseCheckScoringConfig,
) -> np.ndarray:
    threshold = max(0, int(config.exact_hit_ambiguity_threshold))
    penalty = max(0.0, float(config.exact_hit_ambiguity_penalty))
    if penalty <= 0.0 or threshold <= 0:
        return np.zeros(total_values.shape, dtype=np.float64)
    resolved = np.zeros(total_values.shape, dtype=np.float64)
    overflow_mask = total_values > threshold
    if np.any(overflow_mask):
        overflow_values = np.maximum(
            total_values[overflow_mask].astype(np.int64, copy=False) - threshold,
            0,
        )
        scale_values = np.minimum(
            1.0, overflow_values.astype(np.float64) / float(max(1, threshold))
        )
        resolved[overflow_mask] = penalty * scale_values
    return resolved


def _vectorized_reverse_exact_hit_specificity_bonus(
    *,
    total_values: np.ndarray,
    config: ReverseCheckScoringConfig,
) -> np.ndarray:
    bonus = max(0.0, float(config.exact_hit_specificity_bonus))
    if bonus <= 0.0:
        return np.zeros(total_values.shape, dtype=np.float64)
    normalized_totals = np.maximum(total_values.astype(np.int64, copy=False), 1)
    return bonus / normalized_totals.astype(np.float64)


def _build_compiled_score_config_matrix(
    pending: Sequence[_EnEsCompiledScoreBatchProjection],
) -> _EnEsCompiledScoreConfigMatrix:
    return _EnEsCompiledScoreConfigMatrix(
        source_dict_ids=np.asarray(
            tuple(
                int(projection.source_dict_id) if projection.source_dict_id is not None else -1
                for projection in pending
            ),
            dtype=np.int64,
        ),
        dict_priority=np.asarray(
            tuple(float(projection.config.dict_priority) for projection in pending),
            dtype=np.float64,
        ),
        gloss_schedule_keys=tuple(
            tuple(float(value) for value in projection.config.gloss_decay.schedule)
            for projection in pending
        ),
        pos_match_enabled=np.asarray(
            tuple(bool(projection.config.scoring.pos_match.enabled) for projection in pending),
            dtype=np.bool_,
        ),
        pos_match_exact_bonus=np.asarray(
            tuple(
                np.clip(
                    float(projection.config.scoring.pos_match.exact_match_bonus),
                    0.0,
                    1.0,
                )
                for projection in pending
            ),
            dtype=np.float64,
        ),
        pos_match_compatible_bonus=np.asarray(
            tuple(
                np.clip(
                    float(projection.config.scoring.pos_match.compatible_match_bonus),
                    0.0,
                    1.0,
                )
                for projection in pending
            ),
            dtype=np.float64,
        ),
        compatibility_keys=tuple(
            _compatibility_classes_cache_key(
                projection.config.scoring.pos_match.compatibility_classes
            )
            for projection in pending
        ),
        variant_penalty=np.asarray(
            tuple(float(projection.config.variant_penalty) for projection in pending),
            dtype=np.float64,
        ),
        semantic_demotion_scale=np.asarray(
            tuple(float(projection.config.semantic_demotion_scale) for projection in pending),
            dtype=np.float64,
        ),
        reverse_enabled=np.asarray(
            tuple(bool(projection.config.reverse_check.enabled) for projection in pending),
            dtype=np.bool_,
        ),
        reverse_match_bonus=np.asarray(
            tuple(
                max(0.0, float(projection.config.reverse_check.match_bonus))
                for projection in pending
            ),
            dtype=np.float64,
        ),
        reverse_near_bonus=np.asarray(
            tuple(
                max(0.0, float(projection.config.reverse_check.near_bonus))
                for projection in pending
            ),
            dtype=np.float64,
        ),
        reverse_near_rank_max=np.asarray(
            tuple(
                max(0, int(projection.config.reverse_check.near_rank_max)) for projection in pending
            ),
            dtype=np.int64,
        ),
        reverse_far_hit_penalty=np.asarray(
            tuple(
                max(0.0, float(projection.config.reverse_check.far_hit_penalty))
                for projection in pending
            ),
            dtype=np.float64,
        ),
        reverse_miss_penalty=np.asarray(
            tuple(
                max(0.0, float(projection.config.reverse_check.miss_penalty))
                for projection in pending
            ),
            dtype=np.float64,
        ),
        reverse_exact_hit_ambiguity_threshold=np.asarray(
            tuple(
                max(0, int(projection.config.reverse_check.exact_hit_ambiguity_threshold))
                for projection in pending
            ),
            dtype=np.int64,
        ),
        reverse_exact_hit_ambiguity_penalty=np.asarray(
            tuple(
                max(0.0, float(projection.config.reverse_check.exact_hit_ambiguity_penalty))
                for projection in pending
            ),
            dtype=np.float64,
        ),
        reverse_exact_hit_specificity_bonus=np.asarray(
            tuple(
                max(0.0, float(projection.config.reverse_check.exact_hit_specificity_bonus))
                for projection in pending
            ),
            dtype=np.float64,
        ),
        score_weight_dict_priority=np.asarray(
            tuple(float(projection.config.scoring.weights.dict_priority) for projection in pending),
            dtype=np.float64,
        ),
        score_weight_frequency_weight=np.asarray(
            tuple(
                float(projection.config.scoring.weights.frequency_weight) for projection in pending
            ),
            dtype=np.float64,
        ),
        score_weight_pos_match=np.asarray(
            tuple(float(projection.config.scoring.weights.pos_match) for projection in pending),
            dtype=np.float64,
        ),
        score_weight_variant_penalty=np.asarray(
            tuple(
                float(projection.config.scoring.weights.variant_penalty) for projection in pending
            ),
            dtype=np.float64,
        ),
        score_weight_phrase_penalty=np.asarray(
            tuple(
                float(projection.config.scoring.weights.phrase_penalty) for projection in pending
            ),
            dtype=np.float64,
        ),
        overlay_rows=np.asarray(
            tuple(
                tuple(float(value) for value in projection.overlay_rows) for projection in pending
            ),
            dtype=np.float64,
        ),
    )


def _resolve_vectorized_frequency_weight_matrix(
    *,
    gloss_indices: np.ndarray,
    gloss_schedule_keys: Sequence[tuple[float, ...]],
) -> np.ndarray:
    if not gloss_schedule_keys:
        return np.zeros((0, gloss_indices.shape[0]), dtype=np.float64)
    resolved = np.zeros((len(gloss_schedule_keys), gloss_indices.shape[0]), dtype=np.float64)
    grouped_indices_by_schedule: dict[tuple[float, ...], list[int]] = {}
    for index, schedule_key in enumerate(gloss_schedule_keys):
        grouped_indices_by_schedule.setdefault(schedule_key, []).append(index)
    for schedule_key, indices in grouped_indices_by_schedule.items():
        resolved[np.asarray(indices, dtype=np.int64)] = _vectorized_gloss_decay_values(
            gloss_indices=gloss_indices,
            schedule=schedule_key,
        )
    return resolved


def _resolve_vectorized_pos_match_matrix(
    *,
    source_pos_for_match: Sequence[str],
    target_pos_canonicals: Sequence[str],
    config_matrix: _EnEsCompiledScoreConfigMatrix,
) -> np.ndarray:
    config_count = int(config_matrix.pos_match_enabled.shape[0])
    row_count = len(target_pos_canonicals)
    resolved = np.zeros((config_count, row_count), dtype=np.float64)
    enabled_indices = np.flatnonzero(config_matrix.pos_match_enabled)
    if enabled_indices.size == 0:
        return resolved
    grouped_indices_by_compatibility: dict[
        Optional[tuple[tuple[str, str], ...]],
        list[int],
    ] = {}
    for index in enabled_indices.tolist():
        grouped_indices_by_compatibility.setdefault(
            config_matrix.compatibility_keys[index],
            [],
        ).append(int(index))
    for compatibility_key, grouped_indices in grouped_indices_by_compatibility.items():
        compatibility_classes = dict(compatibility_key) if compatibility_key is not None else None
        exact_mask, compatible_mask = _resolve_vectorized_pos_match_masks(
            source_pos_for_match=source_pos_for_match,
            target_pos_canonicals=target_pos_canonicals,
            compatibility_classes=compatibility_classes,
        )
        grouped_indices_array = np.asarray(grouped_indices, dtype=np.int64)
        resolved[grouped_indices_array] = (
            exact_mask.astype(np.float64)[None, :]
            * config_matrix.pos_match_exact_bonus[grouped_indices_array][:, None]
        ) + (
            compatible_mask.astype(np.float64)[None, :]
            * config_matrix.pos_match_compatible_bonus[grouped_indices_array][:, None]
        )
    return resolved


def _vectorized_reverse_check_delta_matrix(
    *,
    supported_flags: np.ndarray,
    hit_flags: np.ndarray,
    rank_values: np.ndarray,
    total_values: np.ndarray,
    config_matrix: _EnEsCompiledScoreConfigMatrix,
) -> np.ndarray:
    config_count = int(config_matrix.reverse_enabled.shape[0])
    row_count = int(rank_values.shape[0])
    resolved = np.zeros((config_count, row_count), dtype=np.float64)
    if config_count == 0 or row_count == 0:
        return resolved
    supported_mask = config_matrix.reverse_enabled[:, None] & supported_flags[None, :]
    if not np.any(supported_mask):
        return resolved
    hit_mask = np.broadcast_to(hit_flags[None, :], (config_count, row_count))
    rank_matrix = np.broadcast_to(rank_values[None, :], (config_count, row_count))
    total_matrix = np.broadcast_to(total_values[None, :], (config_count, row_count))
    supported_hit_mask = supported_mask & hit_mask
    missing_rank_mask = supported_hit_mask & (rank_matrix < 0)
    if np.any(missing_rank_mask):
        resolved = np.where(
            missing_rank_mask,
            config_matrix.reverse_match_bonus[:, None],
            resolved,
        )
    exact_hit_mask = supported_hit_mask & (rank_matrix == 0)
    if np.any(exact_hit_mask):
        exact_totals = np.maximum(total_matrix.astype(np.int64, copy=False), 1)
        specificity_bonus = config_matrix.reverse_exact_hit_specificity_bonus[
            :, None
        ] / exact_totals.astype(np.float64)
        ambiguity_penalty = np.where(
            total_matrix > config_matrix.reverse_exact_hit_ambiguity_threshold[:, None],
            config_matrix.reverse_exact_hit_ambiguity_penalty[:, None],
            0.0,
        )
        resolved = np.where(
            exact_hit_mask,
            config_matrix.reverse_match_bonus[:, None] + specificity_bonus - ambiguity_penalty,
            resolved,
        )
    near_hit_mask = supported_hit_mask & (rank_matrix > 0)
    near_hit_mask &= rank_matrix <= config_matrix.reverse_near_rank_max[:, None]
    if np.any(near_hit_mask):
        resolved = np.where(
            near_hit_mask,
            config_matrix.reverse_near_bonus[:, None],
            resolved,
        )
    far_hit_mask = supported_hit_mask & (rank_matrix > config_matrix.reverse_near_rank_max[:, None])
    if np.any(far_hit_mask):
        max_rank_values = np.maximum(total_matrix.astype(np.int64, copy=False) - 1, 0)
        effective_rank_values = np.minimum(
            rank_matrix.astype(np.int64, copy=False),
            max_rank_values,
        )
        strength_values = np.ones(resolved.shape, dtype=np.float64)
        valid_mask = far_hit_mask & (max_rank_values > 0)
        if np.any(valid_mask):
            strength_values[valid_mask] = np.clip(
                1.0
                - (
                    effective_rank_values[valid_mask]
                    / max_rank_values[valid_mask].astype(np.float64)
                ),
                0.0,
                1.0,
            )
        far_hit_penalties = config_matrix.reverse_far_hit_penalty[:, None] * strength_values
        resolved = np.where(far_hit_mask, -far_hit_penalties, resolved)
    miss_mask = supported_mask & (~hit_mask)
    if np.any(miss_mask):
        resolved = np.where(
            miss_mask,
            -config_matrix.reverse_miss_penalty[:, None],
            resolved,
        )
    return resolved


def _vectorized_reverse_check_strength_matrix(
    *,
    supported_flags: np.ndarray,
    hit_flags: np.ndarray,
    rank_values: np.ndarray,
    total_values: np.ndarray,
    config_matrix: _EnEsCompiledScoreConfigMatrix,
) -> np.ndarray:
    config_count = int(config_matrix.reverse_enabled.shape[0])
    row_count = int(rank_values.shape[0])
    resolved = np.full((config_count, row_count), np.nan, dtype=np.float64)
    if config_count == 0 or row_count == 0:
        return resolved
    supported_mask = np.broadcast_to(
        supported_flags[None, :],
        (config_count, row_count),
    )
    if not np.any(supported_mask):
        return resolved
    hit_mask = np.broadcast_to(hit_flags[None, :], (config_count, row_count))
    rank_matrix = np.broadcast_to(rank_values[None, :], (config_count, row_count))
    total_matrix = np.broadcast_to(total_values[None, :], (config_count, row_count))
    resolved[supported_mask & (~hit_mask)] = 0.0
    exact_hit_mask = supported_mask & hit_mask & ((rank_matrix < 0) | (rank_matrix == 0))
    if np.any(exact_hit_mask):
        resolved[exact_hit_mask] = 1.0
    ranked_hit_mask = supported_mask & hit_mask & (rank_matrix > 0)
    if not np.any(ranked_hit_mask):
        return resolved
    multi_total_mask = ranked_hit_mask & (total_matrix > 1)
    if np.any(multi_total_mask):
        max_rank_values = np.maximum(total_matrix.astype(np.int64, copy=False) - 1, 0)
        effective_rank_values = np.minimum(
            rank_matrix.astype(np.int64, copy=False),
            max_rank_values,
        )
        strength_values = np.ones(resolved.shape, dtype=np.float64)
        valid_mask = multi_total_mask & (max_rank_values > 0)
        if np.any(valid_mask):
            strength_values[valid_mask] = np.clip(
                1.0
                - (
                    effective_rank_values[valid_mask]
                    / max_rank_values[valid_mask].astype(np.float64)
                ),
                0.0,
                1.0,
            )
        resolved[multi_total_mask] = strength_values[multi_total_mask]
    fallback_mask = ranked_hit_mask & (~multi_total_mask)
    if np.any(fallback_mask):
        fallback_strengths = np.where(
            rank_matrix <= config_matrix.reverse_near_rank_max[:, None],
            0.75,
            0.25,
        )
        resolved[fallback_mask] = fallback_strengths[fallback_mask]
    return resolved


def _compute_confidence_and_ranking_matrices_torch(
    *,
    base_gloss_score_values: np.ndarray,
    config_matrix: _EnEsCompiledScoreConfigMatrix,
    dict_priority_matrix: np.ndarray,
    effective_semantic_demotion_matrix: np.ndarray,
    frequency_weight_matrix: np.ndarray,
    phrase_penalty_values_by_row: np.ndarray,
    pos_match_matrix: np.ndarray,
    reverse_check_delta_matrix: np.ndarray,
    variant_penalty_matrix: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if (
        torch is None
        or not bool(getattr(torch, "cuda", None))
        or not bool(torch.cuda.is_available())
    ):
        raise RuntimeError("Torch CUDA backend requested but CUDA is unavailable.")
    device = torch.device("cuda")
    dict_priority_tensor = torch.as_tensor(
        dict_priority_matrix,
        dtype=torch.float64,
        device=device,
    )
    frequency_weight_tensor = torch.as_tensor(
        frequency_weight_matrix,
        dtype=torch.float64,
        device=device,
    )
    pos_match_tensor = torch.as_tensor(
        pos_match_matrix,
        dtype=torch.float64,
        device=device,
    )
    variant_penalty_tensor = torch.as_tensor(
        variant_penalty_matrix,
        dtype=torch.float64,
        device=device,
    )
    phrase_penalty_tensor = torch.as_tensor(
        phrase_penalty_values_by_row,
        dtype=torch.float64,
        device=device,
    )
    effective_semantic_demotion_tensor = torch.as_tensor(
        effective_semantic_demotion_matrix,
        dtype=torch.float64,
        device=device,
    )
    reverse_check_delta_tensor = torch.as_tensor(
        reverse_check_delta_matrix,
        dtype=torch.float64,
        device=device,
    )
    dict_priority_weight_tensor = torch.as_tensor(
        config_matrix.score_weight_dict_priority,
        dtype=torch.float64,
        device=device,
    )[:, None]
    frequency_weight_weight_tensor = torch.as_tensor(
        config_matrix.score_weight_frequency_weight,
        dtype=torch.float64,
        device=device,
    )[:, None]
    pos_match_weight_tensor = torch.as_tensor(
        config_matrix.score_weight_pos_match,
        dtype=torch.float64,
        device=device,
    )[:, None]
    variant_penalty_weight_tensor = torch.as_tensor(
        config_matrix.score_weight_variant_penalty,
        dtype=torch.float64,
        device=device,
    )[:, None]
    phrase_penalty_weight_tensor = torch.as_tensor(
        config_matrix.score_weight_phrase_penalty,
        dtype=torch.float64,
        device=device,
    )[:, None]
    base_gloss_score_tensor = torch.as_tensor(
        base_gloss_score_values,
        dtype=torch.float64,
        device=device,
    )
    confidence_scores_tensor = torch.clamp(
        (dict_priority_tensor * dict_priority_weight_tensor)
        + (frequency_weight_tensor * frequency_weight_weight_tensor)
        + (pos_match_tensor * pos_match_weight_tensor)
        - (variant_penalty_tensor * variant_penalty_weight_tensor)
        - (phrase_penalty_tensor.unsqueeze(0) * phrase_penalty_weight_tensor),
        0.0,
        1.0,
    )
    ranking_scores_tensor = (
        base_gloss_score_tensor.unsqueeze(0).expand_as(confidence_scores_tensor).clone()
    )
    demoted_mask = effective_semantic_demotion_tensor > 0.0
    ranking_scores_tensor = torch.where(
        demoted_mask,
        torch.clamp(
            ranking_scores_tensor * (1.0 - effective_semantic_demotion_tensor),
            min=0.0,
        ),
        ranking_scores_tensor,
    )
    ranking_scores_tensor = torch.clamp(
        ranking_scores_tensor + reverse_check_delta_tensor,
        0.0,
        1.0,
    )
    if bool(getattr(torch, "cuda", None)):
        torch.cuda.synchronize()
    return (
        confidence_scores_tensor.cpu().numpy(),
        ranking_scores_tensor.cpu().numpy(),
    )


def _vectorized_reverse_check_delta_values(
    *,
    supported_flags: np.ndarray,
    hit_flags: np.ndarray,
    rank_values: np.ndarray,
    total_values: np.ndarray,
    config: ReverseCheckScoringConfig,
) -> np.ndarray:
    resolved = np.zeros(rank_values.shape, dtype=np.float64)
    if not bool(config.enabled):
        return resolved
    supported_mask = supported_flags.astype(bool, copy=False)
    if not np.any(supported_mask):
        return resolved
    hit_mask = hit_flags.astype(bool, copy=False)
    supported_hit_mask = supported_mask & hit_mask
    match_bonus = max(0.0, float(config.match_bonus))
    near_bonus = max(0.0, float(config.near_bonus))
    near_rank_max = max(0, int(config.near_rank_max))
    missing_rank_mask = supported_hit_mask & (rank_values < 0)
    if np.any(missing_rank_mask) and match_bonus > 0.0:
        resolved[missing_rank_mask] = match_bonus
    exact_hit_mask = supported_hit_mask & (rank_values == 0)
    if np.any(exact_hit_mask):
        exact_totals = total_values[exact_hit_mask]
        resolved[exact_hit_mask] = (
            match_bonus
            + _vectorized_reverse_exact_hit_specificity_bonus(
                total_values=exact_totals,
                config=config,
            )
            - _vectorized_reverse_exact_hit_ambiguity_penalty(
                total_values=exact_totals,
                config=config,
            )
        )
    near_hit_mask = supported_hit_mask & (rank_values > 0) & (rank_values <= near_rank_max)
    if np.any(near_hit_mask) and near_bonus > 0.0:
        resolved[near_hit_mask] = near_bonus
    far_hit_penalty = max(0.0, float(config.far_hit_penalty))
    far_hit_mask = supported_hit_mask & (rank_values > near_rank_max)
    if np.any(far_hit_mask) and far_hit_penalty > 0.0:
        resolved[far_hit_mask] = -_vectorized_reverse_far_hit_penalty(
            rank_values=rank_values[far_hit_mask],
            total_values=total_values[far_hit_mask],
            penalty=far_hit_penalty,
        )
    miss_penalty = max(0.0, float(config.miss_penalty))
    miss_mask = supported_mask & (~hit_mask)
    if np.any(miss_mask) and miss_penalty > 0.0:
        resolved[miss_mask] = -miss_penalty
    return resolved


def _vectorized_reverse_check_strength_values(
    *,
    supported_flags: np.ndarray,
    hit_flags: np.ndarray,
    rank_values: np.ndarray,
    total_values: np.ndarray,
    config: ReverseCheckScoringConfig,
) -> np.ndarray:
    resolved = np.full(rank_values.shape, np.nan, dtype=np.float64)
    supported_mask = supported_flags.astype(bool, copy=False)
    if not np.any(supported_mask):
        return resolved
    hit_mask = hit_flags.astype(bool, copy=False)
    resolved[supported_mask & (~hit_mask)] = 0.0
    exact_hit_mask = supported_mask & hit_mask & ((rank_values < 0) | (rank_values == 0))
    if np.any(exact_hit_mask):
        resolved[exact_hit_mask] = 1.0
    ranked_hit_mask = supported_mask & hit_mask & (rank_values > 0)
    if not np.any(ranked_hit_mask):
        return resolved
    multi_total_mask = ranked_hit_mask & (total_values > 1)
    if np.any(multi_total_mask):
        max_rank_values = np.maximum(
            total_values[multi_total_mask].astype(np.int64, copy=False) - 1,
            0,
        )
        effective_rank_values = np.minimum(
            rank_values[multi_total_mask].astype(np.int64, copy=False),
            max_rank_values,
        )
        strength_values = np.ones(effective_rank_values.shape, dtype=np.float64)
        valid_mask = max_rank_values > 0
        if np.any(valid_mask):
            strength_values[valid_mask] = np.clip(
                1.0
                - (
                    effective_rank_values[valid_mask]
                    / max_rank_values[valid_mask].astype(np.float64)
                ),
                0.0,
                1.0,
            )
        resolved[multi_total_mask] = strength_values
    fallback_mask = ranked_hit_mask & (~multi_total_mask)
    if np.any(fallback_mask):
        near_rank_max = max(0, int(config.near_rank_max))
        resolved[fallback_mask] = np.where(
            rank_values[fallback_mask] <= near_rank_max,
            0.75,
            0.25,
        )
    return resolved


def _materialize_compiled_candidate_score_table_batch(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: EnEsCompiledCandidateTable,
    pending: Sequence[_EnEsCompiledScoreBatchProjection],
) -> None:
    if not pending:
        return
    config_matrix = _build_compiled_score_config_matrix(pending)
    config_count = len(pending)
    candidate_ids = tuple(int(candidate_id) for candidate_id in candidate_table.candidate_ids)
    target_ids = tuple(int(target_id) for target_id in candidate_table.target_ids)
    definition_bucket_ids = tuple(
        int(definition_bucket_id) for definition_bucket_id in candidate_table.definition_bucket_ids
    )
    candidate_row_ids_by_target_id = {
        int(target_id): tuple(int(row_id) for row_id in row_ids)
        for target_id, row_ids in candidate_table.candidate_row_ids_by_target_id.items()
    }
    normalized_source_phrases = candidate_table.normalized_source_phrases
    normalized_source_phrase_order_ids = tuple(
        int(order_id) for order_id in candidate_table.normalized_source_phrase_order_ids
    )
    source_pos_canonicals = tuple(
        str(source_pos or "") for source_pos in candidate_table.source_pos_canonicals
    )
    dictionary_pos_canonicals = tuple(
        str(dictionary_pos or "") for dictionary_pos in candidate_table.dictionary_pos_canonicals
    )
    target_pos_canonicals = tuple(
        str(target_pos or "") for target_pos in candidate_table.target_pos_canonicals
    )
    row_count = len(candidate_ids)
    source_dict_ids_array = np.asarray(candidate_table.source_dict_ids, dtype=np.int64)
    gloss_indices_array = np.asarray(candidate_table.gloss_indices, dtype=np.int64)
    variant_flags_array = np.asarray(candidate_table.variant_flags, dtype=np.bool_)
    phrase_penalty_values_by_row = np.asarray(
        tuple(
            1.0 if " " in str(normalized_source_phrase or "") else 0.0
            for normalized_source_phrase in normalized_source_phrases
        ),
        dtype=np.float64,
    )
    reverse_check_supported_flags = np.asarray(
        candidate_table.reverse_check_supported_flags,
        dtype=np.bool_,
    )
    reverse_check_hit_flags = np.asarray(candidate_table.reverse_check_hit_flags, dtype=np.bool_)
    reverse_check_rank_values = np.asarray(
        candidate_table.reverse_check_rank_values, dtype=np.int64
    )
    reverse_check_total_values = np.asarray(
        candidate_table.reverse_check_total_values,
        dtype=np.int64,
    )
    reverse_hygiene_anchor_allowed_flags_by_row = np.asarray(
        tuple(
            resolve_reverse_hygiene_anchor_allowed_from_values(
                hit=bool(reverse_check_hit_flags[row_id]),
                rank=(
                    int(reverse_check_rank_values[row_id])
                    if int(reverse_check_rank_values[row_id]) >= 0
                    else None
                ),
                total=int(reverse_check_total_values[row_id]),
            )
            for row_id in range(row_count)
        ),
        dtype=np.bool_,
    )
    normalized_source_phrase_order_ids_array = np.asarray(
        normalized_source_phrase_order_ids,
        dtype=np.int64,
    )
    phrase_penalty_values_tuple = tuple(
        float(value) for value in phrase_penalty_values_by_row.tolist()
    )
    reverse_hygiene_anchor_allowed_flags_tuple = tuple(
        bool(value) for value in reverse_hygiene_anchor_allowed_flags_by_row.tolist()
    )
    base_gloss_score_values = np.zeros(row_count, dtype=np.float64)
    non_negative_gloss_mask = gloss_indices_array >= 0
    if np.any(non_negative_gloss_mask):
        base_gloss_score_values[non_negative_gloss_mask] = 1.0 / (
            1.0 + gloss_indices_array[non_negative_gloss_mask].astype(np.float64)
        )
    source_pos_for_match = tuple(
        source_pos or dictionary_pos
        for source_pos, dictionary_pos in zip(
            source_pos_canonicals,
            dictionary_pos_canonicals,
        )
    )
    dict_priority_matrix = np.where(
        source_dict_ids_array[None, :] == config_matrix.source_dict_ids[:, None],
        config_matrix.dict_priority[:, None],
        0.0,
    )
    dict_priority_matrix[config_matrix.source_dict_ids < 0] = 0.0
    frequency_weight_matrix = _resolve_vectorized_frequency_weight_matrix(
        gloss_indices=gloss_indices_array,
        gloss_schedule_keys=config_matrix.gloss_schedule_keys,
    )
    pos_match_matrix = _resolve_vectorized_pos_match_matrix(
        source_pos_for_match=source_pos_for_match,
        target_pos_canonicals=target_pos_canonicals,
        config_matrix=config_matrix,
    )
    variant_penalty_matrix = (
        variant_flags_array.astype(np.float64)[None, :] * (config_matrix.variant_penalty[:, None])
    )
    effective_semantic_demotion_matrix = np.clip(
        np.clip(config_matrix.overlay_rows, 0.0, 1.0)
        * np.clip(config_matrix.semantic_demotion_scale[:, None], 0.0, 1.0),
        0.0,
        1.0,
    )
    reverse_check_delta_matrix = _vectorized_reverse_check_delta_matrix(
        supported_flags=reverse_check_supported_flags,
        hit_flags=reverse_check_hit_flags,
        rank_values=reverse_check_rank_values,
        total_values=reverse_check_total_values,
        config_matrix=config_matrix,
    )
    reverse_check_strength_matrix = _vectorized_reverse_check_strength_matrix(
        supported_flags=reverse_check_supported_flags,
        hit_flags=reverse_check_hit_flags,
        rank_values=reverse_check_rank_values,
        total_values=reverse_check_total_values,
        config_matrix=config_matrix,
    )
    backend = _resolve_compiled_score_backend(config_count=config_count, row_count=row_count)
    if backend == "torch-cuda":
        confidence_scores_matrix, ranking_scores_matrix = (
            _compute_confidence_and_ranking_matrices_torch(
                base_gloss_score_values=base_gloss_score_values,
                config_matrix=config_matrix,
                dict_priority_matrix=dict_priority_matrix,
                effective_semantic_demotion_matrix=effective_semantic_demotion_matrix,
                frequency_weight_matrix=frequency_weight_matrix,
                phrase_penalty_values_by_row=phrase_penalty_values_by_row,
                pos_match_matrix=pos_match_matrix,
                reverse_check_delta_matrix=reverse_check_delta_matrix,
                variant_penalty_matrix=variant_penalty_matrix,
            )
        )
    else:
        confidence_scores_matrix = np.clip(
            (dict_priority_matrix * config_matrix.score_weight_dict_priority[:, None])
            + (frequency_weight_matrix * config_matrix.score_weight_frequency_weight[:, None])
            + (pos_match_matrix * config_matrix.score_weight_pos_match[:, None])
            - (variant_penalty_matrix * config_matrix.score_weight_variant_penalty[:, None])
            - (
                phrase_penalty_values_by_row[None, :]
                * config_matrix.score_weight_phrase_penalty[:, None]
            ),
            0.0,
            1.0,
        )
        ranking_scores_matrix = np.broadcast_to(
            base_gloss_score_values, confidence_scores_matrix.shape
        ).copy()
        demoted_mask = effective_semantic_demotion_matrix > 0.0
        if np.any(demoted_mask):
            ranking_scores_matrix[demoted_mask] = np.maximum(
                0.0,
                ranking_scores_matrix[demoted_mask]
                * (1.0 - effective_semantic_demotion_matrix[demoted_mask]),
            )
        ranking_scores_matrix = np.clip(
            ranking_scores_matrix + reverse_check_delta_matrix,
            0.0,
            1.0,
        )
    for projection_index, projection in enumerate(pending):
        dict_priority_values = dict_priority_matrix[projection_index]
        frequency_weight_values = frequency_weight_matrix[projection_index]
        pos_match_values = pos_match_matrix[projection_index]
        variant_penalty_values = variant_penalty_matrix[projection_index]
        effective_semantic_demotion_values = effective_semantic_demotion_matrix[projection_index]
        reverse_check_delta_values = reverse_check_delta_matrix[projection_index]
        reverse_check_strength_values = reverse_check_strength_matrix[projection_index]
        confidence_scores = confidence_scores_matrix[projection_index]
        ranking_scores = ranking_scores_matrix[projection_index]
        row_sort_keys = tuple(
            zip(
                (-ranking_scores).tolist(),
                (-confidence_scores).tolist(),
                normalized_source_phrase_order_ids_array.tolist(),
            )
        )
        ranked_candidate_row_ids_by_target_id = {
            int(target_id): tuple(
                int(row_id)
                for row_id in row_ids_array[
                    np.lexsort(
                        (
                            normalized_source_phrase_order_ids_array[row_ids_array],
                            -confidence_scores[row_ids_array],
                            -ranking_scores[row_ids_array],
                        )
                    )
                ].tolist()
            )
            for target_id, row_ids_array in (
                (
                    target_id,
                    np.asarray(row_ids, dtype=np.int64),
                )
                for target_id, row_ids in sorted(candidate_row_ids_by_target_id.items())
            )
        }
        score_table = EnEsCompiledCandidateScoreTable(
            candidate_ids=candidate_ids,
            target_ids=target_ids,
            definition_bucket_ids=definition_bucket_ids,
            dict_priority_values=tuple(float(value) for value in dict_priority_values.tolist()),
            frequency_weight_values=tuple(
                float(value) for value in frequency_weight_values.tolist()
            ),
            pos_match_values=tuple(float(value) for value in pos_match_values.tolist()),
            variant_penalty_values=tuple(float(value) for value in variant_penalty_values.tolist()),
            phrase_penalty_values=phrase_penalty_values_tuple,
            effective_semantic_demotion_values=tuple(
                float(value) for value in effective_semantic_demotion_values.tolist()
            ),
            reverse_check_delta_values=tuple(
                float(value) for value in reverse_check_delta_values.tolist()
            ),
            reverse_check_strength_values=tuple(
                None if np.isnan(value) else float(value)
                for value in reverse_check_strength_values.tolist()
            ),
            reverse_hygiene_anchor_allowed_flags=reverse_hygiene_anchor_allowed_flags_tuple,
            confidence_scores=tuple(float(value) for value in confidence_scores.tolist()),
            ranking_scores=tuple(float(value) for value in ranking_scores.tolist()),
            row_sort_keys=row_sort_keys,
        )
        score_table = replace(
            score_table,
            selected_row_signature=_build_compiled_score_selected_row_signature(
                score_table=replace(
                    score_table,
                    ranked_candidate_row_ids_by_target_id=ranked_candidate_row_ids_by_target_id,
                )
            ),
            ranked_candidate_row_ids_by_target_id=ranked_candidate_row_ids_by_target_id,
        )
        _COMPILED_SCORE_TABLE_CACHE[projection.cache_key] = score_table


def _build_compiled_score_table_cache_key(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table_cache_token: object | None = None,
    config: EnEsRulegenConfig,
) -> tuple[int, tuple[object, ...]]:
    compatibility_classes = config.scoring.pos_match.compatibility_classes
    return (
        int(compiled_resources.cache_token),
        (
            (
                candidate_table_cache_token
                if candidate_table_cache_token is not None
                else ("base", int(compiled_resources.cache_token))
            ),
            str(config.source_dict_id),
            float(config.dict_priority),
            tuple(float(value) for value in config.gloss_decay.schedule),
            bool(config.scoring.pos_match.enabled),
            float(config.scoring.pos_match.exact_match_bonus),
            float(config.scoring.pos_match.compatible_match_bonus),
            _compatibility_classes_cache_key(compatibility_classes),
            float(config.variant_penalty),
            float(config.semantic_demotion_scale),
            bool(config.reverse_check.enabled),
            float(config.reverse_check.match_bonus),
            float(config.reverse_check.near_bonus),
            int(config.reverse_check.near_rank_max),
            float(config.reverse_check.far_hit_penalty),
            float(config.reverse_check.miss_penalty),
            int(config.reverse_check.exact_hit_ambiguity_threshold),
            float(config.reverse_check.exact_hit_ambiguity_penalty),
            float(config.reverse_check.exact_hit_specificity_bonus),
            float(config.scoring.weights.dict_priority),
            float(config.scoring.weights.frequency_weight),
            float(config.scoring.weights.pos_match),
            float(config.scoring.weights.variant_penalty),
            float(config.scoring.weights.phrase_penalty),
            float(config.scoring.weights.embedding_weight),
            bool(config.kaikki_policy.enable_live_demotion),
            float(config.kaikki_policy.late_sense_clean_earlier_competition_penalty),
            tuple(
                str(name).strip()
                for name in config.kaikki_policy.risk_families
                if str(name).strip()
            ),
        ),
    )


def build_en_es_compiled_candidate_filter_table(
    *,
    compiled_resources: EnEsCompiledResources,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateFilterTable:
    candidate_table = compiled_resources.candidate_table
    return _build_compiled_candidate_filter_table_for_table(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        candidate_table_cache_token=("base", int(compiled_resources.cache_token)),
        config=config,
    )


def _build_compiled_candidate_filter_table_for_table(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: Optional[EnEsCompiledCandidateTable],
    candidate_table_cache_token: object,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateFilterTable:
    if candidate_table is None:
        return EnEsCompiledCandidateFilterTable()
    cache_key = _build_compiled_filter_table_cache_key(
        compiled_resources=compiled_resources,
        candidate_table_cache_token=candidate_table_cache_token,
        config=config,
    )
    cached = _COMPILED_FILTER_TABLE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    stopwords = set(config.stopwords or DEFAULT_STOPWORDS)
    gloss_base_forms = set(compiled_resources.gloss_base_forms)
    normalized_source_phrases: list[str] = []
    definition_group_ids: list[int] = []
    non_empty_flags: list[bool] = []
    gloss_shape_flags: list[bool] = []
    length_flags: list[bool] = []
    possessive_flags: list[bool] = []
    shadowed_interjection_flags: list[bool] = []
    stopword_flags: list[bool] = []
    inflection_artifact_flags: list[bool] = []
    accepted_flags: list[bool] = []
    accepted_candidate_row_ids_by_target_id: dict[int, list[int]] = {}
    accepted_candidate_row_id_groups_by_target_id: dict[int, dict[str, list[int]]] = {}
    accepted_candidate_row_group_order_by_target_id: dict[int, list[str]] = {}
    definition_group_id_by_key: dict[tuple[str, object], int] = {}
    for row_id, candidate_id in enumerate(candidate_table.candidate_ids):
        normalized_phrase = candidate_table.normalized_source_phrases[row_id]
        normalized_source_phrases.append(normalized_phrase)
        definition_bucket_id = int(candidate_table.definition_bucket_ids[row_id])
        definition_group_key: tuple[str, object]
        if definition_bucket_id >= 0:
            definition_group_key = ("definition_bucket_id", definition_bucket_id)
        else:
            definition_group_key = (
                "source_phrase",
                str(normalized_phrase or "").strip().lower(),
            )
        definition_group_ids.append(
            int(
                definition_group_id_by_key.setdefault(
                    definition_group_key,
                    len(definition_group_id_by_key),
                )
            )
        )
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
            group_key = str(normalized_phrase or "").strip().lower()
            groups_by_key = accepted_candidate_row_id_groups_by_target_id.setdefault(
                target_id,
                {},
            )
            if group_key not in groups_by_key:
                accepted_candidate_row_group_order_by_target_id.setdefault(target_id, []).append(
                    group_key
                )
                groups_by_key[group_key] = []
            groups_by_key[group_key].append(row_id)
    filter_table = EnEsCompiledCandidateFilterTable(
        candidate_ids=tuple(int(candidate_id) for candidate_id in candidate_table.candidate_ids),
        target_ids=tuple(int(target_id) for target_id in candidate_table.target_ids),
        normalized_source_phrases=tuple(normalized_source_phrases),
        definition_group_ids=tuple(definition_group_ids),
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
        accepted_candidate_row_id_groups_by_target_id={
            key: tuple(
                tuple(groups_by_key[group_key])
                for group_key in accepted_candidate_row_group_order_by_target_id.get(key, [])
            )
            for key, groups_by_key in sorted(accepted_candidate_row_id_groups_by_target_id.items())
        },
    )
    filter_table = replace(
        filter_table,
        selected_row_signature=_build_compiled_filter_selected_row_signature(
            filter_table=filter_table
        ),
    )
    _COMPILED_FILTER_TABLE_CACHE[cache_key] = filter_table
    return filter_table


def _build_compiled_filter_table_cache_key(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table_cache_token: object | None = None,
    config: EnEsRulegenConfig,
) -> tuple[int, tuple[object, ...]]:
    return (
        int(compiled_resources.cache_token),
        (
            (
                candidate_table_cache_token
                if candidate_table_cache_token is not None
                else ("base", int(compiled_resources.cache_token))
            ),
            bool(config.allow_hyphen),
            bool(config.allow_multiword_glosses),
            bool(config.enable_length_filter),
            int(config.min_source_length),
            (None if config.max_source_length is None else int(config.max_source_length)),
            bool(config.enable_possessive_filter),
            bool(config.enable_stopword_filter),
            (
                frozenset(str(stopword).strip().lower() for stopword in config.stopwords)
                if config.stopwords is not None
                else _DEFAULT_STOPWORDS_FROZEN
            ),
            bool(config.enable_inflection_filter),
            tuple(str(suffix) for suffix in config.inflection_suffixes),
        ),
    )


def _build_compiled_filter_selected_row_signature(
    *,
    filter_table: EnEsCompiledCandidateFilterTable,
) -> tuple[object, ...]:
    return (
        tuple(
            (
                int(target_id),
                tuple(tuple(int(row_id) for row_id in row_group) for row_group in groups),
            )
            for target_id, groups in sorted(
                filter_table.accepted_candidate_row_id_groups_by_target_id.items()
            )
        ),
        tuple(int(group_id) for group_id in filter_table.definition_group_ids),
        tuple(str(source_phrase) for source_phrase in filter_table.normalized_source_phrases),
    )


def _build_compiled_score_selected_row_signature(
    *,
    score_table: EnEsCompiledCandidateScoreTable,
) -> tuple[object, ...]:
    return (
        tuple(
            (int(target_id), tuple(int(row_id) for row_id in row_ids))
            for target_id, row_ids in sorted(
                score_table.ranked_candidate_row_ids_by_target_id.items()
            )
        ),
        tuple(
            None if value is None else float(value)
            for value in score_table.reverse_check_strength_values
        ),
        tuple(bool(flag) for flag in score_table.reverse_hygiene_anchor_allowed_flags),
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


def _resolve_compiled_overlay_demotion_rows(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: EnEsCompiledCandidateTable,
    candidate_table_cache_token: object,
    config: EnEsRulegenConfig,
) -> tuple[float, ...]:
    cache_key = (
        int(compiled_resources.cache_token),
        (
            candidate_table_cache_token,
            bool(config.kaikki_policy.enable_live_demotion),
            float(config.kaikki_policy.late_sense_clean_earlier_competition_penalty),
            tuple(
                str(name).strip()
                for name in config.kaikki_policy.risk_families
                if str(name).strip()
            ),
        ),
    )
    cached = _COMPILED_OVERLAY_DEMOTION_ROWS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    resolved = _build_compiled_overlay_demotion_rows(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        config=config,
    )
    _COMPILED_OVERLAY_DEMOTION_ROWS_CACHE[cache_key] = resolved
    return resolved


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


def _build_compiled_benchmark_variant_candidate_table(
    compiled_resources: EnEsCompiledResources,
) -> EnEsCompiledCandidateTable:
    cached = _COMPILED_BENCHMARK_VARIANT_CANDIDATE_TABLE_CACHE.get(
        int(compiled_resources.cache_token)
    )
    if cached is not None:
        return cached
    base_candidate_table = compiled_resources.candidate_table
    if base_candidate_table is None:
        return EnEsCompiledCandidateTable()
    variant_expander = PairedInflectionVariantExpander(
        should_expand=_should_expand_english,
        target_surface_resolver=_resolve_spanish_target_surface,
    )
    candidate_facts: list[EnEsCompiledCandidateFact] = []
    next_candidate_id = (
        max((int(fact.candidate_id) for fact in compiled_resources.candidate_facts), default=-1) + 1
    )
    for target_context in compiled_resources.compiled_targets_by_target.values():
        for base_candidate, base_fact in zip(
            target_context.base_candidates,
            target_context.candidate_facts,
            strict=False,
        ):
            candidate_facts.append(base_fact)
            normalized_base_candidate = replace(
                base_candidate,
                source_phrase=_normalize_compiled_source_phrase(base_candidate.source_phrase),
            )
            expanded_candidates = tuple(variant_expander.expand(normalized_base_candidate))
            for expanded_candidate in expanded_candidates[1:]:
                candidate_facts.append(
                    _build_compiled_candidate_fact(
                        candidate=expanded_candidate,
                        candidate_id=next_candidate_id,
                        target_id=target_context.target_id,
                        definition_bucket_ids_by_key=compiled_resources.definition_bucket_ids_by_key,
                        family_marker_ids_by_name=compiled_resources.family_marker_ids_by_name,
                        source_dict_ids_by_name=compiled_resources.source_dict_ids_by_name,
                        source_type_ids_by_name=compiled_resources.source_type_ids_by_name,
                    )
                )
                next_candidate_id += 1
    candidate_table = _build_compiled_candidate_table(candidate_facts)
    _COMPILED_BENCHMARK_VARIANT_CANDIDATE_TABLE_CACHE[int(compiled_resources.cache_token)] = (
        candidate_table
    )
    return candidate_table


def _resolve_compiled_benchmark_candidate_table(
    *,
    compiled_resources: EnEsCompiledResources,
    include_variants: bool,
) -> tuple[Optional[EnEsCompiledCandidateTable], object]:
    if not include_variants:
        return compiled_resources.candidate_table, ("base", int(compiled_resources.cache_token))
    return _build_compiled_benchmark_variant_candidate_table(compiled_resources), (
        "benchmark-variants",
        int(compiled_resources.cache_token),
    )


def prepare_en_es_compiled_benchmark_evaluation_tables(
    *,
    configs: Sequence[EnEsRulegenConfig],
) -> tuple[EnEsCompiledBenchmarkEvaluationTables, ...]:
    if not configs:
        return ()
    grouped_indices_by_token: dict[object, list[int]] = {}
    candidate_table_by_token: dict[object, Optional[EnEsCompiledCandidateTable]] = {}
    compiled_resources_by_token: dict[object, EnEsCompiledResources] = {}
    filter_tables: list[Optional[EnEsCompiledCandidateFilterTable]] = [None] * len(configs)
    score_tables: list[Optional[EnEsCompiledCandidateScoreTable]] = [None] * len(configs)
    for index, config in enumerate(configs):
        compiled_resources = config.compiled_resources
        if compiled_resources is None:
            continue
        candidate_table, candidate_table_cache_token = _resolve_compiled_benchmark_candidate_table(
            compiled_resources=compiled_resources,
            include_variants=bool(config.include_variants),
        )
        candidate_table_by_token[candidate_table_cache_token] = candidate_table
        compiled_resources_by_token[candidate_table_cache_token] = compiled_resources
        grouped_indices_by_token.setdefault(candidate_table_cache_token, []).append(index)
        filter_tables[index] = _build_compiled_candidate_filter_table_for_table(
            compiled_resources=compiled_resources,
            candidate_table=candidate_table,
            candidate_table_cache_token=candidate_table_cache_token,
            config=config,
        )
    for candidate_table_cache_token, indices in grouped_indices_by_token.items():
        candidate_table = candidate_table_by_token.get(candidate_table_cache_token)
        compiled_resources = compiled_resources_by_token[candidate_table_cache_token]
        grouped_configs = tuple(configs[index] for index in indices)
        grouped_score_tables = _build_compiled_candidate_score_tables_for_table(
            compiled_resources=compiled_resources,
            candidate_table=candidate_table,
            candidate_table_cache_token=candidate_table_cache_token,
            configs=grouped_configs,
        )
        for index, score_table in zip(indices, grouped_score_tables):
            score_tables[index] = score_table
    return tuple(
        EnEsCompiledBenchmarkEvaluationTables(
            filter_table=(
                filter_tables[index]
                if filter_tables[index] is not None
                else EnEsCompiledCandidateFilterTable()
            ),
            score_table=(
                score_tables[index]
                if score_tables[index] is not None
                else EnEsCompiledCandidateScoreTable()
            ),
        )
        for index in range(len(configs))
    )


def prepare_en_es_compiled_benchmark_sweep_tables(
    *,
    targets: Iterable[str],
    configs: Sequence[EnEsRulegenConfig],
) -> tuple[EnEsCompiledBenchmarkSweepTables, ...]:
    if not configs:
        return ()
    prepared_evaluation_tables = prepare_en_es_compiled_benchmark_evaluation_tables(configs=configs)
    ordered_targets = _materialize_ordered_targets(targets)
    target_context_rows_by_token: dict[
        object, tuple[tuple[str, EnEsCompiledTargetContext], ...]
    ] = {}
    prepared_sweep_tables: list[EnEsCompiledBenchmarkSweepTables] = []
    for index, config in enumerate(configs):
        compiled_resources = config.compiled_resources
        prepared_evaluation = prepared_evaluation_tables[index]
        if compiled_resources is None:
            prepared_sweep_tables.append(
                EnEsCompiledBenchmarkSweepTables(
                    filter_table=prepared_evaluation.filter_table,
                    score_table=prepared_evaluation.score_table,
                )
            )
            continue
        candidate_table, candidate_table_cache_token = _resolve_compiled_benchmark_candidate_table(
            compiled_resources=compiled_resources,
            include_variants=bool(config.include_variants),
        )
        if candidate_table_cache_token not in target_context_rows_by_token:
            target_context_rows_by_token[candidate_table_cache_token] = (
                _resolve_compiled_selected_row_target_context_rows(
                    ordered_targets=ordered_targets,
                    compiled_resources=compiled_resources,
                )
            )
        prepared_sweep_tables.append(
            EnEsCompiledBenchmarkSweepTables(
                filter_table=prepared_evaluation.filter_table,
                score_table=prepared_evaluation.score_table,
                selected_row_table=_build_or_resolve_compiled_selected_row_table(
                    ordered_targets=ordered_targets,
                    target_context_rows=target_context_rows_by_token[candidate_table_cache_token],
                    compiled_resources=compiled_resources,
                    candidate_table_cache_token=candidate_table_cache_token,
                    candidate_table=candidate_table,
                    filter_table=prepared_evaluation.filter_table,
                    score_table=prepared_evaluation.score_table,
                    config=config,
                    include_normalized_source_phrase_rows=False,
                ),
            )
        )
    return tuple(prepared_sweep_tables)


def _materialize_ordered_targets(targets: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(str(target or "").strip() for target in targets if str(target or "").strip())
    )


def _resolve_compiled_selected_row_target_context_rows(
    *,
    ordered_targets: Sequence[str],
    compiled_resources: EnEsCompiledResources,
) -> tuple[tuple[str, EnEsCompiledTargetContext], ...]:
    target_context_rows: list[tuple[str, EnEsCompiledTargetContext]] = []
    for target in ordered_targets:
        context = compiled_resources.compiled_targets_by_target.get(target)
        if context is not None:
            target_context_rows.append((target, context))
    return tuple(target_context_rows)


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
    entries: Sequence[TranslationGlossRecord],
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
    entry: TranslationGlossRecord,
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
        source_pos_canonical=extract_candidate_pos_canonical(
            metadata,
            nested_key="source",
            flat_key="source_pos_canonical",
        ),
        target_pos_canonical=extract_candidate_pos_canonical(
            metadata,
            nested_key="target",
            flat_key="target_pos_canonical",
        ),
        dictionary_pos_canonical=extract_candidate_pos_canonical(
            metadata,
            nested_key="dictionary",
            flat_key="dictionary_pos_canonical",
        ),
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
    normalized_source_phrases: list[str] = []
    normalized_source_phrase_order_ids: list[int] = []
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
        normalized_source_phrases.append(_normalize_compiled_source_phrase(fact.source_phrase))
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

    normalized_source_phrase_order_id_by_phrase = {
        phrase: order_id for order_id, phrase in enumerate(sorted(set(normalized_source_phrases)))
    }
    normalized_source_phrase_order_ids = [
        int(normalized_source_phrase_order_id_by_phrase[phrase])
        for phrase in normalized_source_phrases
    ]

    return EnEsCompiledCandidateTable(
        candidate_ids=tuple(candidate_ids),
        target_ids=tuple(target_ids),
        definition_bucket_ids=tuple(definition_bucket_ids),
        source_phrases=tuple(source_phrases),
        source_phrase_lowers=tuple(source_phrase_lowers),
        normalized_source_phrases=tuple(normalized_source_phrases),
        normalized_source_phrase_order_ids=tuple(normalized_source_phrase_order_ids),
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
    if _can_generate_en_es_results_from_compiled_rows(config):
        return _generate_en_es_results_from_compiled_rows(targets, config=config)
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


def _can_generate_en_es_results_from_compiled_rows(config: EnEsRulegenConfig) -> bool:
    compiled_resources = config.compiled_resources
    if compiled_resources is None or config.include_variants:
        return False
    return compiled_resources.candidate_table is not None


def build_en_es_compiled_selected_row_table(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
    filter_table: Optional[EnEsCompiledCandidateFilterTable] = None,
    score_table: Optional[EnEsCompiledCandidateScoreTable] = None,
    include_normalized_source_phrase_rows: bool = True,
) -> EnEsCompiledSelectedRowTable:
    compiled_resources = config.compiled_resources
    if compiled_resources is None:
        return EnEsCompiledSelectedRowTable()
    candidate_table, candidate_table_cache_token = _resolve_compiled_benchmark_candidate_table(
        compiled_resources=compiled_resources,
        include_variants=bool(config.include_variants),
    )
    if candidate_table is None:
        return EnEsCompiledSelectedRowTable()
    resolved_filter_table = (
        filter_table
        if filter_table is not None
        else _build_compiled_candidate_filter_table_for_table(
            compiled_resources=compiled_resources,
            candidate_table=candidate_table,
            candidate_table_cache_token=candidate_table_cache_token,
            config=config,
        )
    )
    resolved_score_table = (
        score_table
        if score_table is not None
        else _build_compiled_candidate_score_table_for_table(
            compiled_resources=compiled_resources,
            candidate_table=candidate_table,
            candidate_table_cache_token=candidate_table_cache_token,
            config=config,
        )
    )
    ordered_targets = _materialize_ordered_targets(targets)
    target_context_rows = _resolve_compiled_selected_row_target_context_rows(
        ordered_targets=ordered_targets,
        compiled_resources=compiled_resources,
    )
    return _build_or_resolve_compiled_selected_row_table(
        ordered_targets=ordered_targets,
        target_context_rows=target_context_rows,
        compiled_resources=compiled_resources,
        candidate_table_cache_token=candidate_table_cache_token,
        candidate_table=candidate_table,
        filter_table=resolved_filter_table,
        score_table=resolved_score_table,
        config=config,
        include_normalized_source_phrase_rows=include_normalized_source_phrase_rows,
    )


def _build_compiled_selected_row_table_cache_key(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table_cache_token: object,
    ordered_targets: Sequence[str],
    filter_table: EnEsCompiledCandidateFilterTable,
    score_table: EnEsCompiledCandidateScoreTable,
    config: EnEsRulegenConfig,
    include_normalized_source_phrase_rows: bool,
) -> tuple[int, tuple[object, ...]]:
    return (
        int(compiled_resources.cache_token),
        (
            candidate_table_cache_token,
            tuple(str(target) for target in ordered_targets),
            filter_table.selected_row_signature,
            score_table.selected_row_signature,
            tuple(
                float(confidence) >= float(config.confidence_threshold)
                for confidence in score_table.confidence_scores
            ),
            bool(include_normalized_source_phrase_rows),
            (
                None
                if config.max_definitions_per_target is None
                else int(config.max_definitions_per_target)
            ),
            bool(config.interleave_definition_groups),
            None if config.max_rules_per_target is None else int(config.max_rules_per_target),
            bool(config.reverse_check.enabled),
        ),
    )


def _build_or_resolve_compiled_selected_row_table(
    *,
    ordered_targets: Sequence[str],
    target_context_rows: Sequence[tuple[str, EnEsCompiledTargetContext]],
    compiled_resources: EnEsCompiledResources,
    candidate_table_cache_token: object,
    candidate_table: Optional[EnEsCompiledCandidateTable],
    filter_table: EnEsCompiledCandidateFilterTable,
    score_table: EnEsCompiledCandidateScoreTable,
    config: EnEsRulegenConfig,
    include_normalized_source_phrase_rows: bool,
) -> EnEsCompiledSelectedRowTable:
    cache_key = _build_compiled_selected_row_table_cache_key(
        compiled_resources=compiled_resources,
        candidate_table_cache_token=candidate_table_cache_token,
        ordered_targets=ordered_targets,
        filter_table=filter_table,
        score_table=score_table,
        config=config,
        include_normalized_source_phrase_rows=include_normalized_source_phrase_rows,
    )
    cached = _COMPILED_SELECTED_ROW_TABLE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    selected_row_table = _build_en_es_compiled_selected_row_table_from_target_context_rows(
        target_context_rows=target_context_rows,
        candidate_table=candidate_table,
        filter_table=filter_table,
        score_table=score_table,
        config=config,
        include_normalized_source_phrase_rows=include_normalized_source_phrase_rows,
    )
    _COMPILED_SELECTED_ROW_TABLE_CACHE[cache_key] = selected_row_table
    return selected_row_table


def _build_en_es_compiled_selected_row_table_from_target_context_rows(
    *,
    target_context_rows: Sequence[tuple[str, EnEsCompiledTargetContext]],
    candidate_table: Optional[EnEsCompiledCandidateTable],
    filter_table: EnEsCompiledCandidateFilterTable,
    score_table: EnEsCompiledCandidateScoreTable,
    config: EnEsRulegenConfig,
    include_normalized_source_phrase_rows: bool = True,
) -> EnEsCompiledSelectedRowTable:
    if candidate_table is None:
        return EnEsCompiledSelectedRowTable()
    selected_targets: list[str] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    normalized_source_phrase_rows: list[tuple[str, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}
    for target, context in target_context_rows:
        base_candidates = context.base_candidates
        candidate_row_id_groups = filter_table.accepted_candidate_row_id_groups_by_target_id.get(
            context.target_id,
            (),
        )
        accepted_row_ids: list[int] = []
        for row_group in candidate_row_id_groups:
            selected_row_id: Optional[int] = None
            for row_id in row_group:
                local_index = int(candidate_table.local_candidate_indices[row_id])
                if local_index < 0 or local_index >= len(base_candidates):
                    continue
                source_phrase = str(filter_table.normalized_source_phrases[row_id] or "").strip()
                if not source_phrase:
                    continue
                confidence = float(score_table.confidence_scores[row_id])
                if confidence < config.confidence_threshold:
                    continue
                selected_row_id = int(row_id)
                break
            if selected_row_id is not None:
                accepted_row_ids.append(selected_row_id)
        selected_row_ids = _limit_compiled_result_row_ids(
            accepted_row_ids,
            filter_table=filter_table,
            score_table=score_table,
            reverse_check=config.reverse_check,
            max_definitions_per_target=config.max_definitions_per_target,
            interleave_definition_groups=config.interleave_definition_groups,
            max_rules_per_target=config.max_rules_per_target,
        )
        if not selected_row_ids:
            continue
        row_id_by_target[target] = len(selected_targets)
        selected_targets.append(target)
        candidate_row_id_rows.append(tuple(int(row_id) for row_id in selected_row_ids))
        if include_normalized_source_phrase_rows:
            normalized_source_phrase_rows.append(
                tuple(
                    str(filter_table.normalized_source_phrases[int(row_id)] or "").strip()
                    for row_id in selected_row_ids
                )
            )
        else:
            normalized_source_phrase_rows.append(())
        top_row_id = int(selected_row_ids[0])
        top1_confidences.append(float(score_table.confidence_scores[top_row_id]))
        variant_rule_counts.append(
            sum(1 for row_id in selected_row_ids if candidate_table.variant_flags[int(row_id)])
        )
        top1_variant_flags.append(bool(candidate_table.variant_flags[top_row_id]))
    return EnEsCompiledSelectedRowTable(
        targets=tuple(selected_targets),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        normalized_source_phrase_rows=tuple(normalized_source_phrase_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _generate_en_es_results_from_compiled_rows(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
) -> list[RuleGenerationResult]:
    compiled_resources = config.compiled_resources
    if compiled_resources is None or compiled_resources.candidate_table is None:
        return []
    candidate_table = compiled_resources.candidate_table
    filter_table = build_en_es_compiled_candidate_filter_table(
        compiled_resources=compiled_resources,
        config=config,
    )
    score_table = build_en_es_compiled_candidate_score_table(
        compiled_resources=compiled_resources,
        config=config,
    )
    selected_row_table = build_en_es_compiled_selected_row_table(
        targets,
        config=config,
        filter_table=filter_table,
        score_table=score_table,
    )
    rule_config = RuleGenerationConfig(
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        max_definitions_per_target=config.max_definitions_per_target,
        max_rules_per_target=config.max_rules_per_target,
        interleave_definition_groups=config.interleave_definition_groups,
        semantic_demotion_scale=config.semantic_demotion_scale,
        tags=("translation", config.source_dict_id),
    )
    results: list[RuleGenerationResult] = []
    for target in selected_row_table.targets:
        context = compiled_resources.compiled_targets_by_target.get(target)
        if context is None:
            continue
        base_candidates = context.base_candidates
        shadows = (
            _build_kaikki_policy_shadow_by_index(
                dictionary_record_views_by_index=context.dictionary_record_views_by_index,
                canonical_inventory=context.canonical_inventory,
                risk_families=config.kaikki_policy.risk_families,
            )
            if config.kaikki_policy.enable_shadow_metadata
            else tuple({} for _ in base_candidates)
        )
        target_row_id = selected_row_table.row_id_by_target.get(target)
        if target_row_id is None:
            continue
        selected_row_ids = selected_row_table.candidate_row_id_rows[int(target_row_id)]
        for row_id in selected_row_ids:
            local_index = int(candidate_table.local_candidate_indices[row_id])
            if local_index < 0 or local_index >= len(base_candidates):
                continue
            base_candidate = base_candidates[local_index]
            confidence = float(score_table.confidence_scores[row_id])
            metadata = dict(base_candidate.metadata)
            metadata["reverse_check_source_dict"] = config.reverse_source_dict_id or None
            if local_index < len(shadows):
                _apply_kaikki_policy_overlay(
                    metadata=metadata,
                    shadow=shadows[local_index],
                    kaikki_policy=config.kaikki_policy,
                )
            source_phrase = str(filter_table.normalized_source_phrases[row_id] or "").strip()
            if not source_phrase:
                continue
            candidate = replace(
                base_candidate,
                source_phrase=source_phrase,
                language_pair=config.language_pair,
                source_dict=config.source_dict_id,
                source_type="translation",
                metadata=metadata,
            )
            results.append(
                materialize_rule_generation_result(
                    candidate,
                    confidence=confidence,
                    config=rule_config,
                )
            )
    return results


def _limit_compiled_result_row_ids(
    row_ids: Sequence[int],
    *,
    filter_table: EnEsCompiledCandidateFilterTable,
    score_table: EnEsCompiledCandidateScoreTable,
    reverse_check: ReverseCheckScoringConfig,
    max_definitions_per_target: Optional[int],
    interleave_definition_groups: bool,
    max_rules_per_target: Optional[int],
) -> tuple[int, ...]:
    limited_row_ids = tuple(int(row_id) for row_id in row_ids)
    if max_definitions_per_target is not None:
        max_definitions = int(max_definitions_per_target)
        if max_definitions > 0:
            limited_row_ids = _limit_compiled_definition_row_ids(
                limited_row_ids,
                filter_table=filter_table,
                score_table=score_table,
                reverse_check=reverse_check,
                max_definitions_per_target=max_definitions,
                interleave_definition_groups=interleave_definition_groups,
            )
    if max_rules_per_target is not None:
        max_rules = int(max_rules_per_target)
        if max_rules > 0:
            limited_row_ids = _limit_compiled_rule_count_row_ids(
                limited_row_ids,
                score_table=score_table,
                max_rules_per_target=max_rules,
            )
    return limited_row_ids


def _limit_compiled_definition_row_ids(
    row_ids: Sequence[int],
    *,
    filter_table: EnEsCompiledCandidateFilterTable,
    score_table: EnEsCompiledCandidateScoreTable,
    reverse_check: ReverseCheckScoringConfig,
    max_definitions_per_target: int,
    interleave_definition_groups: bool,
) -> tuple[int, ...]:
    materialized_row_ids = tuple(int(row_id) for row_id in row_ids)
    if not materialized_row_ids:
        return ()
    grouped: dict[int, list[int]] = {}
    group_order: list[int] = []
    for row_id in materialized_row_ids:
        definition_key = int(filter_table.definition_group_ids[row_id])
        if definition_key not in grouped:
            grouped[definition_key] = []
            group_order.append(definition_key)
        grouped[definition_key].append(int(row_id))
    sorted_row_ids_by_group_id = _build_compiled_definition_sorted_row_ids_by_group(
        grouped,
        score_table=score_table,
    )

    ranked_groups = sorted(
        (
            _build_compiled_definition_row_group(
                grouped[key],
                sorted_row_ids=sorted_row_ids_by_group_id.get(key),
                score_table=score_table,
            )
            for key in group_order
        ),
        key=lambda group: group.sort_key,
    )
    ranked_groups = _apply_compiled_reverse_definition_hygiene(
        ranked_groups,
        reverse_check=reverse_check,
    )
    selected_groups = [group.sorted_row_ids for group in ranked_groups[:max_definitions_per_target]]
    return _flatten_compiled_definition_groups(
        selected_groups,
        interleave_groups=interleave_definition_groups,
    )


def _build_compiled_definition_sorted_row_ids_by_group(
    grouped_row_ids: Mapping[int, Sequence[int]],
    *,
    score_table: EnEsCompiledCandidateScoreTable,
) -> Mapping[int, tuple[int, ...]]:
    if not grouped_row_ids:
        return {}
    target_ids = {
        int(score_table.target_ids[row_id])
        for row_ids in grouped_row_ids.values()
        for row_id in row_ids
        if 0 <= int(row_id) < len(score_table.target_ids)
    }
    if len(target_ids) != 1:
        return {}
    target_id = next(iter(target_ids))
    ranked_target_row_ids = score_table.ranked_candidate_row_ids_by_target_id.get(target_id)
    if ranked_target_row_ids is None:
        return {}
    row_id_to_group_id = {
        int(row_id): int(group_id)
        for group_id, row_ids in grouped_row_ids.items()
        for row_id in row_ids
    }
    sorted_row_ids_by_group_id: dict[int, list[int]] = {
        int(group_id): [] for group_id in grouped_row_ids
    }
    for row_id in ranked_target_row_ids:
        group_id = row_id_to_group_id.get(int(row_id))
        if group_id is not None:
            sorted_row_ids_by_group_id[group_id].append(int(row_id))
    return {
        int(group_id): tuple(row_ids)
        for group_id, row_ids in sorted_row_ids_by_group_id.items()
        if row_ids
    }


def _build_compiled_definition_row_group(
    row_ids: Sequence[int],
    *,
    sorted_row_ids: Optional[Sequence[int]] = None,
    score_table: EnEsCompiledCandidateScoreTable,
) -> EnEsCompiledDefinitionRowGroup:
    materialized_row_ids = tuple(int(row_id) for row_id in row_ids)
    if not materialized_row_ids:
        return EnEsCompiledDefinitionRowGroup()
    materialized_sorted_row_ids = (
        tuple(int(row_id) for row_id in sorted_row_ids)
        if sorted_row_ids is not None
        else tuple(
            sorted(
                materialized_row_ids,
                key=lambda row_id: _compiled_row_sort_key(row_id, score_table=score_table),
            )
        )
    )
    if not materialized_sorted_row_ids:
        materialized_sorted_row_ids = materialized_row_ids
    best_row_id = int(materialized_sorted_row_ids[0])
    return EnEsCompiledDefinitionRowGroup(
        row_ids=materialized_row_ids,
        sorted_row_ids=materialized_sorted_row_ids,
        best_row_id=best_row_id,
        sort_key=_compiled_row_sort_key(best_row_id, score_table=score_table),
        reverse_strength=score_table.reverse_check_strength_values[best_row_id],
        allows_reverse_hygiene_anchor=bool(
            score_table.reverse_hygiene_anchor_allowed_flags[best_row_id]
        ),
    )


def _compiled_row_sort_key(
    row_id: int,
    *,
    score_table: EnEsCompiledCandidateScoreTable,
) -> tuple[float, float, int]:
    return score_table.row_sort_keys[row_id]


def _apply_compiled_reverse_definition_hygiene(
    ranked_groups: Sequence[EnEsCompiledDefinitionRowGroup],
    *,
    reverse_check: ReverseCheckScoringConfig,
) -> list[EnEsCompiledDefinitionRowGroup]:
    if len(ranked_groups) < 3 or not bool(reverse_check.enabled):
        return list(ranked_groups)
    top_strength = ranked_groups[0].reverse_strength
    if top_strength is None or top_strength < 0.75:
        return list(ranked_groups)
    if not ranked_groups[0].allows_reverse_hygiene_anchor:
        return list(ranked_groups)
    filtered: list[EnEsCompiledDefinitionRowGroup] = [ranked_groups[0]]
    for group in ranked_groups[1:]:
        strength = group.reverse_strength
        if strength is None:
            filtered.append(group)
            continue
        if strength <= 0.20:
            continue
        filtered.append(group)
    return filtered


def _flatten_compiled_definition_groups(
    definition_groups: Sequence[Sequence[int]],
    *,
    interleave_groups: bool,
) -> tuple[int, ...]:
    if not interleave_groups:
        return tuple(int(row_id) for group in definition_groups for row_id in group)
    if not definition_groups:
        return ()
    max_group_size = max(len(group) for group in definition_groups)
    flattened: list[int] = []
    for item_index in range(max_group_size):
        for group in definition_groups:
            if item_index >= len(group):
                continue
            flattened.append(int(group[item_index]))
    return tuple(flattened)


def _limit_compiled_rule_count_row_ids(
    row_ids: Sequence[int],
    *,
    score_table: EnEsCompiledCandidateScoreTable,
    max_rules_per_target: int,
) -> tuple[int, ...]:
    materialized_row_ids = tuple(int(row_id) for row_id in row_ids)
    if not materialized_row_ids:
        return ()
    target_ids = {
        int(score_table.target_ids[row_id])
        for row_id in materialized_row_ids
        if 0 <= int(row_id) < len(score_table.target_ids)
    }
    ranked_row_ids: Sequence[int]
    if len(target_ids) == 1:
        target_id = next(iter(target_ids))
        ranked_target_row_ids = score_table.ranked_candidate_row_ids_by_target_id.get(target_id)
        if ranked_target_row_ids is not None:
            row_id_set = set(materialized_row_ids)
            ranked_row_ids = tuple(
                int(row_id) for row_id in ranked_target_row_ids if row_id in row_id_set
            )
        else:
            ranked_row_ids = sorted(
                materialized_row_ids,
                key=lambda row_id: _compiled_row_sort_key(row_id, score_table=score_table),
            )
    else:
        ranked_row_ids = sorted(
            materialized_row_ids,
            key=lambda row_id: _compiled_row_sort_key(row_id, score_table=score_table),
        )
    return tuple(int(row_id) for row_id in ranked_row_ids[:max_rules_per_target])


class FreedictCandidateSource:
    def __init__(
        self,
        *,
        records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
        source_dict: str,
        source_type: str,
        reverse_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None,
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


def _resolve_gloss_records(
    config: EnEsRulegenConfig,
) -> dict[str, list[TranslationGlossRecord]]:
    if config.gloss_records_by_target is not None:
        return _coerce_gloss_records(config.gloss_records_by_target)
    if config.gloss_mapping is not None:
        return _coerce_gloss_records(config.gloss_mapping)
    return load_translation_gloss_records_ordered(
        config.freedict_es_en_path,
        target_lang="en",
    )


def _coerce_gloss_records(
    mapping: Mapping[str, Sequence[object]],
) -> dict[str, list[TranslationGlossRecord]]:
    records_by_target: dict[str, list[TranslationGlossRecord]] = {}
    for target, entries in mapping.items():
        bucket: list[TranslationGlossRecord] = []
        for entry in entries:
            if isinstance(entry, TranslationGlossRecord):
                bucket.append(entry)
                continue
            bucket.append(TranslationGlossRecord(translation=str(entry), pos_raw=""))
        records_by_target[str(target)] = bucket
    return records_by_target


def _resolve_reverse_gloss_records(
    config: EnEsRulegenConfig,
) -> Optional[dict[str, list[TranslationGlossRecord]]]:
    if config.reverse_gloss_records_by_source is not None:
        return _coerce_gloss_records(config.reverse_gloss_records_by_source)
    if config.reverse_freedict_en_es_path is None:
        return None
    if not config.reverse_freedict_en_es_path.exists():
        return None
    return load_translation_gloss_records_ordered(
        config.reverse_freedict_en_es_path,
        target_lang="es",
    )


def _records_to_gloss_mapping(
    records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
) -> dict[str, list[str]]:
    return {
        target: [entry.translation for entry in entries]
        for target, entries in records_by_target.items()
    }
