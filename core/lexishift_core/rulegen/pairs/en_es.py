from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.generation import (
    CandidateNormalizer,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    RuleScoringConfig,
    SimpleSignalProvider,
    build_optional_pos_match_provider,
    materialize_rule_generation_result,
    resolve_reverse_hygiene_anchor_allowed_from_values,
)
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views
from lexishift_core.rulegen.ranking import (
    DictionaryEntryOrderRankingMechanism,
    ReverseCheckScoringConfig,
)
from lexishift_core.rulegen.pairs.en_es_compiled_filtering import (
    EnEsCompiledCandidateFilterTable,
    _build_compiled_filter_table_cache_key,
    build_en_es_compiled_candidate_filter_table,
)
from lexishift_core.rulegen.pairs.en_es_compiled_inventory import (
    EnEsCompiledCandidateTable,
    EnEsCompiledResources,
    EnEsCompiledTargetContext,
    _build_compiled_candidate_table,
    _build_definition_bucket_ids,
    _build_family_marker_ids,
    _build_static_candidate_inventory,
    _finalize_compiled_target_contexts,
)
from lexishift_core.rulegen.pairs.en_es_compiled_scoring import (
    EnEsCompiledCandidateScoreTable,
    EnEsCompiledRankingMechanism,
    EnEsCompiledSignalProvider,
    _EnEsCompiledScoreBatchProjection,
    _build_compiled_score_table_cache_key,
    _materialize_compiled_candidate_score_table_batch,
)
from lexishift_core.rulegen.pairs.en_es_compiled_selection import (
    EnEsCompiledBenchmarkEvaluationTables,
    EnEsCompiledBenchmarkSweepTables,
    EnEsCompiledSelectedRowTable,
    _build_compiled_definition_row_group,
    build_en_es_compiled_selected_row_table as _build_en_es_compiled_selected_row_table,
    generate_en_es_results_from_compiled_rows as _generate_en_es_results_from_compiled_rows_impl,
    prepare_en_es_compiled_benchmark_evaluation_tables as _prepare_en_es_compiled_benchmark_evaluation_tables,
    prepare_en_es_compiled_benchmark_sweep_tables as _prepare_en_es_compiled_benchmark_sweep_tables,
)
from lexishift_core.rulegen.pairs.en_es_live_source import (
    FreedictCandidateSource,
    _build_filters,
    _build_gloss_base_forms,
    _records_to_gloss_mapping,
    _resolve_gloss_records,
    _resolve_reverse_gloss_records,
    _resolve_spanish_target_surface,
    _should_expand_english,
)
from lexishift_core.rulegen.pairs.en_es_support import (
    apply_semantic_demotion as _apply_semantic_demotion,
    build_gloss_provenance as _build_gloss_provenance,
    build_reverse_lookup as _build_reverse_lookup,
    build_target_provenance_by_index as _build_target_provenance_by_index,
    collect_sanitized_gloss_records as _collect_sanitized_gloss_records,
    extract_canonical_from_component as _extract_canonical_from_component,
    normalize_reverse_token as _normalize_reverse_token,
    resolve_kaikki_policy_live_demotion as _resolve_kaikki_policy_live_demotion,
    resolve_kaikki_provenance_competition_demotion as _resolve_kaikki_provenance_competition_demotion,
)
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.semantic_demotion import resolve_pair_generic_gloss_demotions
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    LeadingEnglishInfinitiveNormalizer,
    PairedInflectionVariantExpander,
)
from lexishift_core.scoring.weighting import GlossDecay

_COMPAT_REEXPORTS = (
    _build_compiled_filter_table_cache_key,
    _build_compiled_definition_row_group,
    _build_gloss_provenance,
    build_candidate_pos_metadata,
    materialize_rule_generation_result,
)
_COMPILED_SCORE_TABLE_CACHE: dict[
    tuple[int, tuple[object, ...]],
    "EnEsCompiledCandidateScoreTable",
] = {}
_COMPILED_OVERLAY_DEMOTION_ROWS_CACHE: dict[
    tuple[int, tuple[object, ...]],
    tuple[float, ...],
] = {}
_COMPILED_RESOURCE_CACHE_TOKEN = 0


def _next_compiled_resource_cache_token() -> int:
    global _COMPILED_RESOURCE_CACHE_TOKEN
    _COMPILED_RESOURCE_CACHE_TOKEN += 1
    return int(_COMPILED_RESOURCE_CACHE_TOKEN)


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
class EnEsRulegenConfig:
    translation_dict_path: Path
    reverse_translation_dict_path: Optional[Path] = None
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
    enable_exact_gloss_demotions: bool = False
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
    enable_exact_gloss_demotions: bool = False,
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
    resolved_generic_gloss_demotions = (
        dict(generic_gloss_demotions or resolve_pair_generic_gloss_demotions(language_pair))
        if enable_exact_gloss_demotions
        else {}
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
        built_tables = _materialize_compiled_candidate_score_table_batch(
            compiled_resources=compiled_resources,
            candidate_table=candidate_table,
            pending=pending,
            reverse_hygiene_anchor_resolver=resolve_reverse_hygiene_anchor_allowed_from_values,
        )
        _COMPILED_SCORE_TABLE_CACHE.update(built_tables)
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


def prepare_en_es_compiled_benchmark_evaluation_tables(
    *,
    configs: Sequence[EnEsRulegenConfig],
) -> tuple[EnEsCompiledBenchmarkEvaluationTables, ...]:
    return _prepare_en_es_compiled_benchmark_evaluation_tables(
        configs=configs,
        build_score_tables_for_table=_build_compiled_candidate_score_tables_for_table,
        variant_should_expand=_should_expand_english,
        target_surface_resolver=_resolve_spanish_target_surface,
    )


def prepare_en_es_compiled_benchmark_sweep_tables(
    *,
    targets: Iterable[str],
    configs: Sequence[EnEsRulegenConfig],
) -> tuple[EnEsCompiledBenchmarkSweepTables, ...]:
    return _prepare_en_es_compiled_benchmark_sweep_tables(
        targets=targets,
        configs=configs,
        build_score_tables_for_table=_build_compiled_candidate_score_tables_for_table,
        variant_should_expand=_should_expand_english,
        target_surface_resolver=_resolve_spanish_target_surface,
    )


def build_en_es_compiled_selected_row_table(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
    filter_table: Optional[EnEsCompiledCandidateFilterTable] = None,
    score_table: Optional[EnEsCompiledCandidateScoreTable] = None,
    include_normalized_source_phrase_rows: bool = True,
) -> EnEsCompiledSelectedRowTable:
    return _build_en_es_compiled_selected_row_table(
        targets,
        config=config,
        build_score_table_for_table=_build_compiled_candidate_score_table_for_table,
        variant_should_expand=_should_expand_english,
        target_surface_resolver=_resolve_spanish_target_surface,
        filter_table=filter_table,
        score_table=score_table,
        include_normalized_source_phrase_rows=include_normalized_source_phrase_rows,
    )


def _generate_en_es_results_from_compiled_rows(
    targets: Iterable[str],
    *,
    config: EnEsRulegenConfig,
) -> list[RuleGenerationResult]:
    return _generate_en_es_results_from_compiled_rows_impl(
        targets,
        config=config,
        build_score_table_for_table=_build_compiled_candidate_score_table_for_table,
        apply_kaikki_policy_overlay=_apply_kaikki_policy_overlay,
        variant_should_expand=_should_expand_english,
        target_surface_resolver=_resolve_spanish_target_surface,
        materialize_rule_generation_result_fn=materialize_rule_generation_result,
    )


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
        generic_gloss_demotions=(
            config.generic_gloss_demotions if config.enable_exact_gloss_demotions else {}
        ),
        dictionary_pos_source_profile=config.dictionary_pos_source_profile,
        kaikki_policy=config.kaikki_policy,
        compiled_resources=compiled_resources,
        compiled_filter_table=compiled_candidate_filter_table,
        apply_kaikki_policy_overlay=_apply_kaikki_policy_overlay,
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
    if config.enable_exact_gloss_demotions:
        return False
    compiled_resources = config.compiled_resources
    if compiled_resources is None or config.include_variants:
        return False
    return compiled_resources.candidate_table is not None
