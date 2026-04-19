from __future__ import annotations

from collections import OrderedDict
from typing import Mapping, Optional, Protocol, Sequence, TypeVar

from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
    CandidateRankingMechanism,
    DictionaryEntryOrderRankingMechanism,
    ReverseCheckScoringConfig,
    build_ranking_sort_key,
    resolve_reverse_check_strength,
)

REVERSE_HYGIENE_MIN_GROUP_COUNT = 3
REVERSE_HYGIENE_STRONG_TOP_STRENGTH = 0.75
REVERSE_HYGIENE_WEAK_GROUP_STRENGTH = 0.20
REVERSE_HYGIENE_EXACT_HIT_MAX_TOTAL = 12


class _RuleCandidateLike(Protocol):
    source_phrase: str
    replacement: str
    metadata: Mapping[str, object]


class RuleGenerationResultLike(Protocol):
    candidate: _RuleCandidateLike
    confidence: float


_ResultT = TypeVar("_ResultT", bound=RuleGenerationResultLike)


def limit_rule_generation_results(
    results: Sequence[_ResultT],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    max_definitions_per_target: Optional[int] = None,
    interleave_definition_groups: bool = False,
    max_rules_per_target: Optional[int] = None,
    semantic_demotion_scale: float = 1.0,
) -> list[_ResultT]:
    limited_results = list(results)
    if max_definitions_per_target is not None:
        max_definitions = int(max_definitions_per_target)
        if max_definitions > 0:
            limited_results = _limit_results_per_target_with_ranking(
                limited_results,
                ranking_mechanism=ranking_mechanism,
                max_definitions_per_target=max_definitions,
                interleave_definition_groups=interleave_definition_groups,
                semantic_demotion_scale=semantic_demotion_scale,
            )
    if max_rules_per_target is not None:
        max_rules = int(max_rules_per_target)
        if max_rules > 0:
            limited_results = _limit_rule_count_per_target_with_ranking(
                limited_results,
                ranking_mechanism=ranking_mechanism,
                max_rules_per_target=max_rules,
                semantic_demotion_scale=semantic_demotion_scale,
            )
    return limited_results


def _limit_results_per_target_with_ranking(
    results: Sequence[_ResultT],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    max_definitions_per_target: int,
    interleave_definition_groups: bool,
    semantic_demotion_scale: float,
) -> list[_ResultT]:
    grouped: OrderedDict[str, OrderedDict[str, list[_ResultT]]] = OrderedDict()
    for result in results:
        target_key = str(result.candidate.replacement or "").strip().lower()
        context = _build_ranking_context_for_result(
            result,
            semantic_demotion_scale=semantic_demotion_scale,
        )
        definition_key = ranking_mechanism.bucket_key(context)
        target_groups = grouped.setdefault(target_key, OrderedDict())
        target_groups.setdefault(definition_key, []).append(result)

    limited: list[_ResultT] = []
    for definition_groups in grouped.values():
        ranked_definitions: Sequence[Sequence[_ResultT]] = sorted(
            definition_groups.values(),
            key=lambda group: _definition_group_sort_key_with_ranking(
                group,
                ranking_mechanism=ranking_mechanism,
                semantic_demotion_scale=semantic_demotion_scale,
            ),
        )
        ranked_definitions = _apply_reverse_definition_hygiene_with_ranking(
            ranked_definitions,
            ranking_mechanism=ranking_mechanism,
            semantic_demotion_scale=semantic_demotion_scale,
        )
        selected_groups = [
            sorted(
                definition_group,
                key=lambda result: _ranking_sort_key_for_result(
                    result,
                    ranking_mechanism=ranking_mechanism,
                    semantic_demotion_scale=semantic_demotion_scale,
                ),
            )
            for definition_group in ranked_definitions[:max_definitions_per_target]
        ]
        limited.extend(
            _flatten_definition_groups(
                selected_groups,
                interleave_groups=interleave_definition_groups,
            )
        )
    return limited


def _flatten_definition_groups(
    definition_groups: Sequence[Sequence[_ResultT]],
    *,
    interleave_groups: bool,
) -> list[_ResultT]:
    if not interleave_groups:
        ordered_results: list[_ResultT] = []
        for group in definition_groups:
            ordered_results.extend(group)
        return ordered_results
    if not definition_groups:
        return []
    max_group_size = max(len(group) for group in definition_groups)
    interleaved_results: list[_ResultT] = []
    for item_index in range(max_group_size):
        for group in definition_groups:
            if item_index >= len(group):
                continue
            interleaved_results.append(group[item_index])
    return interleaved_results


def _apply_reverse_definition_hygiene_with_ranking(
    ranked_groups: Sequence[Sequence[_ResultT]],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    semantic_demotion_scale: float,
) -> list[Sequence[_ResultT]]:
    if len(ranked_groups) < REVERSE_HYGIENE_MIN_GROUP_COUNT:
        return list(ranked_groups)
    reverse_config = _resolve_reverse_check_config(ranking_mechanism)
    if reverse_config is None or not bool(reverse_config.enabled):
        return list(ranked_groups)
    top_strength = _definition_group_reverse_strength_with_ranking(
        ranked_groups[0],
        ranking_mechanism=ranking_mechanism,
        semantic_demotion_scale=semantic_demotion_scale,
    )
    if top_strength is None or top_strength < REVERSE_HYGIENE_STRONG_TOP_STRENGTH:
        return list(ranked_groups)
    if not _definition_group_allows_reverse_hygiene_anchor(ranked_groups[0]):
        return list(ranked_groups)
    filtered: list[Sequence[_ResultT]] = [ranked_groups[0]]
    for group in ranked_groups[1:]:
        strength = _definition_group_reverse_strength_with_ranking(
            group,
            ranking_mechanism=ranking_mechanism,
            semantic_demotion_scale=semantic_demotion_scale,
        )
        if strength is None:
            filtered.append(group)
            continue
        if strength <= REVERSE_HYGIENE_WEAK_GROUP_STRENGTH:
            continue
        filtered.append(group)
    return filtered


def _definition_group_sort_key_with_ranking(
    results: Sequence[_ResultT],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    semantic_demotion_scale: float,
) -> tuple[float, float, str]:
    best = min(
        results,
        key=lambda result: _ranking_sort_key_for_result(
            result,
            ranking_mechanism=ranking_mechanism,
            semantic_demotion_scale=semantic_demotion_scale,
        ),
    )
    return _ranking_sort_key_for_result(
        best,
        ranking_mechanism=ranking_mechanism,
        semantic_demotion_scale=semantic_demotion_scale,
    )


def _definition_group_reverse_strength_with_ranking(
    results: Sequence[_ResultT],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    semantic_demotion_scale: float,
) -> Optional[float]:
    reverse_config = _resolve_reverse_check_config(ranking_mechanism)
    if reverse_config is None:
        return None
    best = min(
        results,
        key=lambda result: _ranking_sort_key_for_result(
            result,
            ranking_mechanism=ranking_mechanism,
            semantic_demotion_scale=semantic_demotion_scale,
        ),
    )
    context = _build_ranking_context_for_result(
        best,
        semantic_demotion_scale=semantic_demotion_scale,
    )
    return resolve_reverse_check_strength(
        context.metadata,
        config=reverse_config,
    )


def _definition_group_allows_reverse_hygiene_anchor(
    results: Sequence[RuleGenerationResultLike],
) -> bool:
    if not results:
        return False
    metadata = results[0].candidate.metadata
    if not isinstance(metadata, Mapping):
        return True
    return resolve_reverse_hygiene_anchor_allowed_from_values(
        hit=metadata.get("reverse_check_hit"),
        rank=_extract_optional_non_negative_int(metadata.get("reverse_check_rank")),
        total=_extract_optional_non_negative_int(metadata.get("reverse_check_total")),
    )


def resolve_reverse_hygiene_anchor_allowed_from_values(
    *,
    hit: object,
    rank: Optional[int],
    total: Optional[int],
) -> bool:
    if hit is not True:
        return True
    if rank != 0:
        return True
    if total is None:
        return True
    return total <= REVERSE_HYGIENE_EXACT_HIT_MAX_TOTAL


def _ranking_sort_key_for_result(
    result: RuleGenerationResultLike,
    *,
    ranking_mechanism: CandidateRankingMechanism,
    semantic_demotion_scale: float,
) -> tuple[float, float, str]:
    context = _build_ranking_context_for_result(
        result,
        semantic_demotion_scale=semantic_demotion_scale,
    )
    score = ranking_mechanism.score(context)
    return build_ranking_sort_key(context, score=score)


def _build_ranking_context_for_result(
    result: RuleGenerationResultLike,
    *,
    semantic_demotion_scale: float,
) -> CandidateRankingContext:
    return CandidateRankingContext(
        source_phrase=result.candidate.source_phrase,
        replacement=result.candidate.replacement,
        metadata=result.candidate.metadata,
        confidence=result.confidence,
        semantic_demotion_scale=semantic_demotion_scale,
    )


def _resolve_reverse_check_config(
    ranking_mechanism: CandidateRankingMechanism,
):
    if isinstance(ranking_mechanism, DictionaryEntryOrderRankingMechanism):
        return ranking_mechanism.reverse_check
    reverse_check = getattr(ranking_mechanism, "reverse_check", None)
    if isinstance(reverse_check, ReverseCheckScoringConfig):
        return reverse_check
    fallback = getattr(ranking_mechanism, "fallback", None)
    if isinstance(fallback, DictionaryEntryOrderRankingMechanism):
        return fallback.reverse_check
    return None


def _limit_rule_count_per_target_with_ranking(
    results: Sequence[_ResultT],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    max_rules_per_target: int,
    semantic_demotion_scale: float,
) -> list[_ResultT]:
    grouped: OrderedDict[str, list[_ResultT]] = OrderedDict()
    for result in results:
        target_key = str(result.candidate.replacement or "").strip().lower()
        grouped.setdefault(target_key, []).append(result)

    limited: list[_ResultT] = []
    for group in grouped.values():
        ranked = sorted(
            group,
            key=lambda result: _ranking_sort_key_for_result(
                result,
                ranking_mechanism=ranking_mechanism,
                semantic_demotion_scale=semantic_demotion_scale,
            ),
        )
        limited.extend(ranked[:max_rules_per_target])
    return limited


def _extract_optional_non_negative_int(value: object) -> Optional[int]:
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
