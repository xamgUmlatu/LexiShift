from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.rulegen.generation import (
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationResult,
    materialize_rule_generation_result,
)
from lexishift_core.rulegen.pairs.en_es_compiled_filtering import (
    EnEsCompiledCandidateFilterTable,
    _build_compiled_candidate_filter_table_for_table,
)
from lexishift_core.rulegen.pairs.en_es_compiled_inventory import (
    EnEsCompiledCandidateFact,
    EnEsCompiledCandidateTable,
    EnEsCompiledResources,
    EnEsCompiledTargetContext,
    _build_compiled_candidate_fact,
    _build_compiled_candidate_table,
    _normalize_compiled_source_phrase,
)
from lexishift_core.rulegen.pairs.en_es_compiled_result_limiting import (
    EnEsCompiledDefinitionRowGroup as _EnEsCompiledDefinitionRowGroup,
    _build_compiled_definition_row_group as _build_compiled_definition_row_group_impl,
    _limit_compiled_result_row_ids,
)
from lexishift_core.rulegen.pairs.en_es_compiled_scoring import EnEsCompiledCandidateScoreTable
from lexishift_core.rulegen.utils import PairedInflectionVariantExpander

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_es import EnEsRulegenConfig


ScoreTableBuilder = Callable[..., EnEsCompiledCandidateScoreTable]
ScoreTablesBuilder = Callable[..., tuple[EnEsCompiledCandidateScoreTable, ...]]
KaikkiPolicyOverlayApplier = Callable[..., None]
ShouldExpand = Callable[[RuleCandidate], bool]
TargetSurfaceResolver = Callable[[RuleCandidate, str], Optional[str]]

_COMPILED_SELECTED_ROW_TABLE_CACHE: dict[
    tuple[int, tuple[object, ...]],
    "EnEsCompiledSelectedRowTable",
] = {}
_COMPILED_BENCHMARK_VARIANT_CANDIDATE_TABLE_CACHE: dict[
    int,
    EnEsCompiledCandidateTable,
] = {}

EnEsCompiledDefinitionRowGroup = _EnEsCompiledDefinitionRowGroup
_build_compiled_definition_row_group = _build_compiled_definition_row_group_impl


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


def build_en_es_compiled_selected_row_table(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
    build_score_table_for_table: ScoreTableBuilder,
    variant_should_expand: ShouldExpand,
    target_surface_resolver: TargetSurfaceResolver,
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
        variant_should_expand=variant_should_expand,
        target_surface_resolver=target_surface_resolver,
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
        else build_score_table_for_table(
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


def prepare_en_es_compiled_benchmark_evaluation_tables(
    *,
    configs: Sequence[EnEsRulegenConfig],
    build_score_tables_for_table: ScoreTablesBuilder,
    variant_should_expand: ShouldExpand,
    target_surface_resolver: TargetSurfaceResolver,
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
            variant_should_expand=variant_should_expand,
            target_surface_resolver=target_surface_resolver,
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
        grouped_score_tables = build_score_tables_for_table(
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
    build_score_tables_for_table: ScoreTablesBuilder,
    variant_should_expand: ShouldExpand,
    target_surface_resolver: TargetSurfaceResolver,
) -> tuple[EnEsCompiledBenchmarkSweepTables, ...]:
    if not configs:
        return ()
    prepared_evaluation_tables = prepare_en_es_compiled_benchmark_evaluation_tables(
        configs=configs,
        build_score_tables_for_table=build_score_tables_for_table,
        variant_should_expand=variant_should_expand,
        target_surface_resolver=target_surface_resolver,
    )
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
            variant_should_expand=variant_should_expand,
            target_surface_resolver=target_surface_resolver,
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


def generate_en_es_results_from_compiled_rows(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
    build_score_table_for_table: ScoreTableBuilder,
    apply_kaikki_policy_overlay: KaikkiPolicyOverlayApplier,
    variant_should_expand: ShouldExpand,
    target_surface_resolver: TargetSurfaceResolver,
    materialize_rule_generation_result_fn=materialize_rule_generation_result,
) -> list[RuleGenerationResult]:
    compiled_resources = config.compiled_resources
    if compiled_resources is None or compiled_resources.candidate_table is None:
        return []
    candidate_table = compiled_resources.candidate_table
    filter_table = _build_compiled_candidate_filter_table_for_table(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        candidate_table_cache_token=("base", int(compiled_resources.cache_token)),
        config=config,
    )
    score_table = build_score_table_for_table(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        candidate_table_cache_token=("base", int(compiled_resources.cache_token)),
        config=config,
    )
    selected_row_table = build_en_es_compiled_selected_row_table(
        targets,
        config=config,
        build_score_table_for_table=build_score_table_for_table,
        variant_should_expand=variant_should_expand,
        target_surface_resolver=target_surface_resolver,
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
            tuple(
                {
                    **shadow,
                }
                for shadow in (
                    _build_kaikki_policy_shadow_rows(
                        dictionary_record_views_by_index=context.dictionary_record_views_by_index,
                        canonical_inventory=context.canonical_inventory,
                        risk_families=config.kaikki_policy.risk_families,
                    )
                )
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
                apply_kaikki_policy_overlay(
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
                materialize_rule_generation_result_fn(
                    candidate,
                    confidence=confidence,
                    config=rule_config,
                )
            )
    return results


def _build_compiled_benchmark_variant_candidate_table(
    compiled_resources: EnEsCompiledResources,
    *,
    variant_should_expand: ShouldExpand,
    target_surface_resolver: TargetSurfaceResolver,
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
        should_expand=variant_should_expand,
        target_surface_resolver=target_surface_resolver,
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
    variant_should_expand: ShouldExpand,
    target_surface_resolver: TargetSurfaceResolver,
) -> tuple[Optional[EnEsCompiledCandidateTable], object]:
    if not include_variants:
        return compiled_resources.candidate_table, ("base", int(compiled_resources.cache_token))
    return _build_compiled_benchmark_variant_candidate_table(
        compiled_resources,
        variant_should_expand=variant_should_expand,
        target_surface_resolver=target_surface_resolver,
    ), (
        "benchmark-variants",
        int(compiled_resources.cache_token),
    )


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


def _build_kaikki_policy_shadow_rows(
    *,
    dictionary_record_views_by_index: Sequence[Mapping[str, object]],
    canonical_inventory: Sequence[str],
    risk_families: Sequence[str],
) -> tuple[dict[str, object], ...]:
    from lexishift_core.rulegen.pairs.en_es_support import build_kaikki_policy_shadow_by_index

    return tuple(
        dict(shadow)
        for shadow in build_kaikki_policy_shadow_by_index(
            dictionary_record_views_by_index=dictionary_record_views_by_index,
            canonical_inventory=canonical_inventory,
            risk_families=risk_families,
        )
    )
