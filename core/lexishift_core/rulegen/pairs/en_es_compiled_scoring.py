from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Mapping, Optional, Sequence, cast

import numpy as np

from lexishift_core.rulegen.generation import (
    PosMatchScoringConfig,
    RuleCandidate,
    RuleConfidenceSignals,
    resolve_reverse_hygiene_anchor_allowed_from_values,
    score_candidate_pos_match,
    score_canonical_pos_pair,
)
from lexishift_core.rulegen.pairs.en_es_compiled_inventory import (
    EnEsCompiledCandidateFact,
    EnEsCompiledCandidateTable,
    EnEsCompiledResources,
    _normalize_non_negative_optional_int,
)
from lexishift_core.rulegen.pairs.en_es_compiled_score_math import (
    _build_compiled_score_config_matrix,
    _compatibility_classes_cache_key,
    _compute_confidence_and_ranking_matrices_torch,
    _resolve_compiled_score_backend,
    _resolve_vectorized_frequency_weight_matrix,
    _resolve_vectorized_pos_match_matrix,
    _vectorized_reverse_check_delta_matrix,
    _vectorized_reverse_check_strength_matrix,
)
from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
)
from lexishift_core.scoring.weighting import GlossDecay

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_es import EnEsRulegenConfig


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


def _materialize_compiled_candidate_score_table_batch(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: EnEsCompiledCandidateTable,
    pending: Sequence[_EnEsCompiledScoreBatchProjection],
    reverse_hygiene_anchor_resolver=resolve_reverse_hygiene_anchor_allowed_from_values,
) -> dict[tuple[int, tuple[object, ...]], EnEsCompiledCandidateScoreTable]:
    if not pending:
        return {}
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
            reverse_hygiene_anchor_resolver(
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
        float(value) for value in cast(list[float], phrase_penalty_values_by_row.tolist())
    )
    reverse_hygiene_anchor_allowed_flags_tuple = tuple(
        bool(value)
        for value in cast(list[bool], reverse_hygiene_anchor_allowed_flags_by_row.tolist())
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

    built_tables: dict[tuple[int, tuple[object, ...]], EnEsCompiledCandidateScoreTable] = {}
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
                cast(list[float], (-ranking_scores).tolist()),
                cast(list[float], (-confidence_scores).tolist()),
                cast(list[int], normalized_source_phrase_order_ids_array.tolist()),
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
        built_tables[projection.cache_key] = score_table
    return built_tables


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
