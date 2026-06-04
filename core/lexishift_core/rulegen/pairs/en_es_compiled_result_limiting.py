from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from lexishift_core.rulegen.pairs.en_es_compiled_filtering import EnEsCompiledCandidateFilterTable
from lexishift_core.rulegen.pairs.en_es_compiled_scoring import EnEsCompiledCandidateScoreTable
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig


@dataclass(frozen=True)
class EnEsCompiledDefinitionRowGroup:
    row_ids: tuple[int, ...] = ()
    sorted_row_ids: tuple[int, ...] = ()
    best_row_id: int = -1
    sort_key: tuple[float, float, int] = (0.0, 0.0, 0)
    reverse_strength: Optional[float] = None
    allows_reverse_hygiene_anchor: bool = False


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
