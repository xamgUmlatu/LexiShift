from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

import numpy as np

try:
    import torch
except Exception:  # pragma: no cover - optional dependency
    torch = None

from lexishift_core.rulegen.generation import DEFAULT_POS_COMPATIBILITY_CLASSES
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_es_compiled_scoring import (
        _EnEsCompiledScoreBatchProjection,
    )


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
    resolved: np.ndarray = np.zeros((config_count, row_count), dtype=np.float64)
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
