#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools
import multiprocessing
from time import perf_counter
from typing import Optional, Sequence

from lexishift_core.replacement.core import VocabRule
from lexishift_core.rulegen.adapters import (
    RulegenAdapterRequest,
    build_en_es_rulegen_config,
    run_rules_with_adapter,
)
from lexishift_core.rulegen.benchmarking import (
    RulegenBenchmarkCaseResult,
    RulegenBenchmarkObjectiveWeights,
    summarize_benchmark_results,
)
from lexishift_core.rulegen.pairs.en_es import (
    EnEsCompiledBenchmarkEvaluationTables,
    EnEsCompiledResources,
    build_en_es_compiled_selected_row_table,
    prepare_en_es_compiled_benchmark_sweep_tables,
)

from rulegen_benchmark_compiled import (
    _build_compiled_rule_table_from_en_es_selected_rows,
    _evaluate_case_payloads_with_table,
    _evaluate_case_results_with_table,
    _summarize_compiled_case_results,
)
from rulegen_benchmark_models import (
    BenchmarkTimingCollector,
    CompiledBenchmarkRuleTable,
    PairBenchmarkContext,
    PreparedSweepRunInputs,
    SweepConfig,
    SweepRun,
    SweepRunEvaluation,
)


_WORKER_CONTEXT: Optional[PairBenchmarkContext] = None
_WORKER_OBJECTIVE_WEIGHTS: Optional[RulegenBenchmarkObjectiveWeights] = None
_WORKER_MATERIALIZE_CASE_RESULTS = True


def _parse_csv_strings(text: str) -> list[str]:
    return [item.strip() for item in str(text or "").split(",") if item.strip()]


def _parse_csv_floats(text: str, *, name: str) -> list[float]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    return [float(item) for item in values]


def _parse_csv_ints(text: str, *, name: str, min_value: Optional[int] = None) -> list[int]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[int] = []
    for item in values:
        value = int(item)
        if min_value is not None:
            value = max(int(min_value), value)
        parsed.append(value)
    return parsed


def _parse_csv_optional_ints(
    text: str,
    *,
    name: str,
    zero_as_none: bool,
) -> list[Optional[int]]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[Optional[int]] = []
    for item in values:
        normalized = item.lower()
        if normalized in {"none", "null", "off"}:
            parsed.append(None)
            continue
        value = int(item)
        if zero_as_none and value <= 0:
            parsed.append(None)
        else:
            parsed.append(max(1, value))
    return parsed


def _parse_csv_bools(text: str, *, name: str) -> list[bool]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[bool] = []
    for item in values:
        normalized = item.lower()
        if normalized in {"1", "true", "on", "yes"}:
            parsed.append(True)
            continue
        if normalized in {"0", "false", "off", "no"}:
            parsed.append(False)
            continue
        raise ValueError(f"{name}: unsupported boolean token '{item}'.")
    return parsed


def _parse_family_set_specs(text: str, *, name: str) -> list[tuple[str, ...]]:
    raw_specs = [item.strip() for item in str(text or "").split(";") if item.strip()]
    if not raw_specs:
        raise ValueError(f"{name}: expected at least one family set.")
    parsed: list[tuple[str, ...]] = []
    for spec in raw_specs:
        lowered = spec.lower()
        if lowered in {"none", "off", "null"}:
            parsed.append(())
            continue
        families = [item.strip() for item in spec.replace(",", "+").split("+") if item.strip()]
        if not families:
            raise ValueError(f"{name}: invalid family set '{spec}'.")
        parsed.append(tuple(dict.fromkeys(families)))
    return parsed


def _build_sweep_configs(args: argparse.Namespace) -> list[SweepConfig]:
    max_definitions_values = _parse_csv_optional_ints(
        args.max_definitions_values,
        name="max-definitions-values",
        zero_as_none=True,
    )
    max_rules_values = _parse_csv_optional_ints(
        args.max_rules_values,
        name="max-rules-values",
        zero_as_none=True,
    )
    confidence_values = _parse_csv_floats(
        args.confidence_threshold_values,
        name="confidence-threshold-values",
    )
    semantic_demotion_scale_values = _parse_csv_floats(
        args.semantic_demotion_scale_values,
        name="semantic-demotion-scale-values",
    )
    include_variants_values = _parse_csv_bools(
        args.include_variants_values,
        name="include-variants-values",
    )
    pos_scoring_values = _parse_csv_bools(
        args.pos_scoring_values,
        name="pos-scoring-values",
    )
    pos_exact_values = _parse_csv_floats(args.pos_exact_values, name="pos-exact-values")
    pos_compatible_values = _parse_csv_floats(
        args.pos_compatible_values,
        name="pos-compatible-values",
    )
    score_weight_dict_values = _parse_csv_floats(
        args.score_weight_dict_values,
        name="score-weight-dict-values",
    )
    score_weight_frequency_values = _parse_csv_floats(
        args.score_weight_frequency_values,
        name="score-weight-frequency-values",
    )
    score_weight_pos_values = _parse_csv_floats(
        args.score_weight_pos_values,
        name="score-weight-pos-values",
    )
    score_weight_variant_values = _parse_csv_floats(
        args.score_weight_variant_values,
        name="score-weight-variant-values",
    )
    score_weight_phrase_values = _parse_csv_floats(
        args.score_weight_phrase_values,
        name="score-weight-phrase-values",
    )
    score_weight_embedding_values = _parse_csv_floats(
        args.score_weight_embedding_values,
        name="score-weight-embedding-values",
    )
    reverse_check_enabled_values = _parse_csv_bools(
        args.reverse_check_enabled_values,
        name="reverse-check-enabled-values",
    )
    reverse_check_match_bonus_values = _parse_csv_floats(
        args.reverse_check_match_bonus_values,
        name="reverse-check-match-bonus-values",
    )
    reverse_check_near_bonus_values = _parse_csv_floats(
        args.reverse_check_near_bonus_values,
        name="reverse-check-near-bonus-values",
    )
    reverse_check_near_rank_max_values = _parse_csv_ints(
        args.reverse_check_near_rank_max_values,
        name="reverse-check-near-rank-max-values",
        min_value=0,
    )
    reverse_check_far_hit_penalty_values = _parse_csv_floats(
        args.reverse_check_far_hit_penalty_values,
        name="reverse-check-far-hit-penalty-values",
    )
    reverse_check_miss_penalty_values = _parse_csv_floats(
        args.reverse_check_miss_penalty_values,
        name="reverse-check-miss-penalty-values",
    )
    reverse_check_exact_hit_ambiguity_threshold_values = _parse_csv_ints(
        args.reverse_check_exact_hit_ambiguity_threshold_values,
        name="reverse-check-exact-hit-ambiguity-threshold-values",
        min_value=0,
    )
    reverse_check_exact_hit_ambiguity_penalty_values = _parse_csv_floats(
        args.reverse_check_exact_hit_ambiguity_penalty_values,
        name="reverse-check-exact-hit-ambiguity-penalty-values",
    )
    reverse_check_exact_hit_specificity_bonus_values = _parse_csv_floats(
        args.reverse_check_exact_hit_specificity_bonus_values,
        name="reverse-check-exact-hit-specificity-bonus-values",
    )
    kaikki_policy_live_demotion_values = _parse_csv_bools(
        args.kaikki_policy_live_demotion_values,
        name="kaikki-policy-live-demotion-values",
    )
    kaikki_policy_risk_family_sets = _parse_family_set_specs(
        args.kaikki_policy_risk_family_sets,
        name="kaikki-policy-risk-family-sets",
    )
    kaikki_policy_late_sense_penalty_values = _parse_csv_floats(
        args.kaikki_policy_late_sense_penalty_values,
        name="kaikki-policy-late-sense-penalty-values",
    )

    configs: list[SweepConfig] = []
    for combo in itertools.product(
        max_definitions_values,
        max_rules_values,
        confidence_values,
        semantic_demotion_scale_values,
        include_variants_values,
        pos_scoring_values,
        pos_exact_values,
        pos_compatible_values,
        score_weight_dict_values,
        score_weight_frequency_values,
        score_weight_pos_values,
        score_weight_variant_values,
        score_weight_phrase_values,
        score_weight_embedding_values,
        reverse_check_enabled_values,
        reverse_check_match_bonus_values,
        reverse_check_near_bonus_values,
        reverse_check_near_rank_max_values,
        reverse_check_far_hit_penalty_values,
        reverse_check_miss_penalty_values,
        reverse_check_exact_hit_ambiguity_threshold_values,
        reverse_check_exact_hit_ambiguity_penalty_values,
        kaikki_policy_live_demotion_values,
        kaikki_policy_risk_family_sets,
        reverse_check_exact_hit_specificity_bonus_values,
        kaikki_policy_late_sense_penalty_values,
    ):
        configs.append(
            SweepConfig(
                max_definitions_per_target=combo[0],
                max_rules_per_target=combo[1],
                confidence_threshold=float(combo[2]),
                semantic_demotion_scale=float(combo[3]),
                include_variants=bool(combo[4]),
                pos_scoring_enabled=bool(combo[5]),
                pos_exact_match_bonus=float(combo[6]),
                pos_compatible_match_bonus=float(combo[7]),
                score_weight_dict_priority=float(combo[8]),
                score_weight_frequency_weight=float(combo[9]),
                score_weight_pos_match=float(combo[10]),
                score_weight_variant_penalty=float(combo[11]),
                score_weight_phrase_penalty=float(combo[12]),
                score_weight_embedding=float(combo[13]),
                reverse_check_enabled=bool(combo[14]),
                reverse_check_match_bonus=float(combo[15]),
                reverse_check_near_bonus=float(combo[16]),
                reverse_check_near_rank_max=max(0, int(combo[17])),
                reverse_check_far_hit_penalty=float(combo[18]),
                reverse_check_miss_penalty=float(combo[19]),
                reverse_check_exact_hit_ambiguity_threshold=max(0, int(combo[20])),
                reverse_check_exact_hit_ambiguity_penalty=float(combo[21]),
                kaikki_policy_live_demotion=bool(combo[22]),
                kaikki_policy_risk_families=tuple(combo[23]),
                reverse_check_exact_hit_specificity_bonus=float(combo[24]),
                kaikki_policy_late_sense_penalty=float(combo[25]),
            )
        )
    return configs


def _run_sort_key(run: SweepRun) -> tuple[float, float, float, float, float, float]:
    summary = run.summary
    return (
        -float(summary.objective_score),
        -float(summary.top1_accuracy),
        -float(summary.top3_recall),
        float(summary.forbidden_top1_rate),
        float(summary.forbidden_any_rate),
        float(summary.avg_rules_per_target),
    )


def _group_rules_by_target(rules: Sequence[VocabRule]) -> dict[str, list[VocabRule]]:
    by_target: dict[str, list[VocabRule]] = {}
    for rule in rules:
        target = str(rule.replacement or "").strip()
        if not target:
            continue
        by_target.setdefault(target, []).append(rule)
    return by_target


def _build_rulegen_adapter_request(
    *,
    context: PairBenchmarkContext,
    config: SweepConfig,
) -> RulegenAdapterRequest:
    return RulegenAdapterRequest(
        pair=context.pair,
        targets=context.targets,
        language_pair=context.pair,
        confidence_threshold=config.confidence_threshold,
        max_definitions_per_target=config.max_definitions_per_target,
        max_rules_per_target=config.max_rules_per_target,
        semantic_demotion_scale=config.semantic_demotion_scale,
        include_variants=config.include_variants,
        scoring=config.scoring(),
        reverse_check=config.reverse_check(),
        jmdict_path=context.jmdict_path,
        translation_dict_path=context.translation_dict_path,
        reverse_translation_dict_path=context.reverse_translation_dict_path,
        gloss_records_by_target=context.gloss_records_by_target,
        reverse_gloss_records_by_source=context.reverse_gloss_records_by_source,
        compiled_pair_context=context.compiled_pair_context,
        word_packages_by_target=context.word_packages_by_target,
        kaikki_policy_live_demotion=config.kaikki_policy_live_demotion,
        kaikki_policy_risk_families=config.kaikki_policy_risk_families,
        kaikki_policy_late_sense_penalty=config.kaikki_policy_late_sense_penalty,
    )


def _can_evaluate_sweep_run_from_en_es_compiled_rows(
    *,
    context: PairBenchmarkContext,
    config: SweepConfig,
) -> bool:
    if context.pair != "en-es":
        return False
    if context.compiled_case_table is None or context.translation_dict_path is None:
        return False
    compiled_pair_context = context.compiled_pair_context
    if not isinstance(compiled_pair_context, EnEsCompiledResources):
        return False
    return compiled_pair_context.candidate_table is not None


def _prepare_compiled_en_es_sweep_inputs(
    *,
    context: PairBenchmarkContext,
    sweep_configs: Sequence[SweepConfig],
) -> tuple[Optional[PreparedSweepRunInputs], ...]:
    if context.pair != "en-es":
        return tuple(None for _ in sweep_configs)
    if context.compiled_case_table is None or context.translation_dict_path is None:
        return tuple(None for _ in sweep_configs)
    compiled_pair_context = context.compiled_pair_context
    if not isinstance(compiled_pair_context, EnEsCompiledResources):
        return tuple(None for _ in sweep_configs)
    requests = tuple(
        _build_rulegen_adapter_request(context=context, config=config) for config in sweep_configs
    )
    en_es_configs = tuple(build_en_es_rulegen_config(request) for request in requests)
    prepared_tables = prepare_en_es_compiled_benchmark_sweep_tables(
        targets=context.targets,
        configs=en_es_configs,
    )
    return tuple(
        PreparedSweepRunInputs(
            request=request,
            compiled_pair_config=en_es_config,
            en_es_tables=EnEsCompiledBenchmarkEvaluationTables(
                filter_table=prepared_table.filter_table,
                score_table=prepared_table.score_table,
            ),
            en_es_selected_row_table=prepared_table.selected_row_table,
        )
        for request, en_es_config, prepared_table in zip(
            requests,
            en_es_configs,
            prepared_tables,
        )
    )


def _evaluate_sweep_run(
    *,
    context: PairBenchmarkContext,
    config: SweepConfig,
    run_index: int,
    objective_weights: RulegenBenchmarkObjectiveWeights,
    timing: Optional[BenchmarkTimingCollector] = None,
    materialize_case_results: bool = True,
    prepared_inputs: Optional[PreparedSweepRunInputs] = None,
) -> SweepRunEvaluation:
    phase_timings: dict[str, float] = {}
    case_results: tuple[RulegenBenchmarkCaseResult, ...] = ()
    rules: Sequence[VocabRule] = ()
    compiled_rule_table: Optional[CompiledBenchmarkRuleTable] = None
    request = (
        prepared_inputs.request
        if prepared_inputs is not None
        else _build_rulegen_adapter_request(context=context, config=config)
    )

    started = perf_counter()
    if _can_evaluate_sweep_run_from_en_es_compiled_rows(context=context, config=config):
        compiled_case_table = context.compiled_case_table
        assert compiled_case_table is not None
        en_es_config = (
            prepared_inputs.compiled_pair_config
            if prepared_inputs is not None and prepared_inputs.compiled_pair_config is not None
            else build_en_es_rulegen_config(request)
        )
        selected_row_table = (
            prepared_inputs.en_es_selected_row_table
            if prepared_inputs is not None and prepared_inputs.en_es_selected_row_table is not None
            else build_en_es_compiled_selected_row_table(
                context.targets,
                config=en_es_config,
                filter_table=(
                    prepared_inputs.en_es_tables.filter_table
                    if prepared_inputs is not None and prepared_inputs.en_es_tables is not None
                    else None
                ),
                score_table=(
                    prepared_inputs.en_es_tables.score_table
                    if prepared_inputs is not None and prepared_inputs.en_es_tables is not None
                    else None
                ),
            )
        )
        compiled_rule_table = _build_compiled_rule_table_from_en_es_selected_rows(
            selected_row_table=selected_row_table,
            compiled_case_table=compiled_case_table,
            filter_table=prepared_inputs.en_es_tables if prepared_inputs is not None else None,
            compiled_pair_context=context.compiled_pair_context,
        )
    else:
        rules = run_rules_with_adapter(request)
    phase_timings["run_config"] = perf_counter() - started

    started = perf_counter()
    if context.compiled_case_table is not None:
        phase_timings["group_rules"] = 0.0
        case_result_payloads, compiled_case_result_table = _evaluate_case_payloads_with_table(
            context=context,
            rules=rules,
            compiled_rule_table=compiled_rule_table,
            include_payloads=materialize_case_results,
        )
    else:
        grouped_started = perf_counter()
        rules_by_target = _group_rules_by_target(rules)
        phase_timings["group_rules"] = perf_counter() - grouped_started
        case_results, compiled_case_result_table = _evaluate_case_results_with_table(
            context=context,
            rules_by_target=rules_by_target,
        )
        case_result_payloads = (
            tuple(result.to_dict() for result in case_results) if materialize_case_results else ()
        )
    phase_timings["evaluate_cases"] = perf_counter() - started

    started = perf_counter()
    if compiled_case_result_table is not None:
        summary = _summarize_compiled_case_results(
            pair=context.pair,
            case_result_table=compiled_case_result_table,
            objective_weights=objective_weights,
        )
    else:
        summary = summarize_benchmark_results(
            pair=context.pair,
            case_results=case_results,
            objective_weights=objective_weights,
        )
    phase_timings["summarize_run"] = perf_counter() - started

    run = SweepRun(
        pair=context.pair,
        run_index=run_index,
        config=config,
        summary=summary,
        case_results=case_result_payloads,
    )
    if timing is not None:
        for phase, duration in phase_timings.items():
            timing.add(phase, duration, pair=context.pair)
    return SweepRunEvaluation(run=run, phase_timings=phase_timings)


def _init_sweep_worker(
    context: PairBenchmarkContext,
    objective_weights: RulegenBenchmarkObjectiveWeights,
    materialize_case_results: bool,
) -> None:
    global _WORKER_CONTEXT, _WORKER_OBJECTIVE_WEIGHTS, _WORKER_MATERIALIZE_CASE_RESULTS
    _WORKER_CONTEXT = context
    _WORKER_OBJECTIVE_WEIGHTS = objective_weights
    _WORKER_MATERIALIZE_CASE_RESULTS = bool(materialize_case_results)


def _evaluate_sweep_run_from_worker_state(
    run_index: int,
    config: SweepConfig,
) -> SweepRunEvaluation:
    if _WORKER_CONTEXT is None or _WORKER_OBJECTIVE_WEIGHTS is None:
        raise RuntimeError("Sweep worker context not initialized.")
    return _evaluate_sweep_run(
        context=_WORKER_CONTEXT,
        config=config,
        run_index=run_index,
        objective_weights=_WORKER_OBJECTIVE_WEIGHTS,
        materialize_case_results=bool(_WORKER_MATERIALIZE_CASE_RESULTS),
    )


def _resolve_job_count(requested_jobs: int, *, config_count: int) -> int:
    jobs = max(1, int(requested_jobs))
    if config_count <= 0:
        return 1
    return min(jobs, config_count)


def _run_pair_sweep(
    *,
    context: PairBenchmarkContext,
    sweep_configs: Sequence[SweepConfig],
    objective_weights: RulegenBenchmarkObjectiveWeights,
    jobs: int,
    timing: Optional[BenchmarkTimingCollector] = None,
    materialize_case_results: bool = True,
) -> list[SweepRun]:
    evaluations: list[SweepRunEvaluation] = []
    max_workers = _resolve_job_count(jobs, config_count=len(sweep_configs))
    materialize_case_results_during_sweep = materialize_case_results or len(sweep_configs) <= 1
    prepared_inputs_by_run_index: tuple[Optional[PreparedSweepRunInputs], ...] = tuple(
        None for _ in sweep_configs
    )
    if max_workers <= 1 or len(sweep_configs) <= 1:
        if sweep_configs and context.pair == "en-es":
            started = perf_counter()
            prepared_inputs_by_run_index = _prepare_compiled_en_es_sweep_inputs(
                context=context,
                sweep_configs=sweep_configs,
            )
            if timing is not None:
                timing.add(
                    "prepare_compiled_sweep_inputs",
                    perf_counter() - started,
                    pair=context.pair,
                )
        for run_index, config in enumerate(sweep_configs, start=1):
            evaluations.append(
                _evaluate_sweep_run(
                    context=context,
                    config=config,
                    run_index=run_index,
                    objective_weights=objective_weights,
                    timing=timing,
                    materialize_case_results=materialize_case_results_during_sweep,
                    prepared_inputs=prepared_inputs_by_run_index[run_index - 1],
                )
            )
    else:
        with ProcessPoolExecutor(
            max_workers=max_workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_init_sweep_worker,
            initargs=(context, objective_weights, materialize_case_results_during_sweep),
        ) as executor:
            future_by_run_index = {
                executor.submit(_evaluate_sweep_run_from_worker_state, run_index, config): run_index
                for run_index, config in enumerate(sweep_configs, start=1)
            }
            for future in as_completed(future_by_run_index):
                evaluations.append(future.result())
        evaluations.sort(key=lambda evaluation: evaluation.run.run_index)
        if timing is not None:
            for evaluation in evaluations:
                for phase, duration in evaluation.phase_timings.items():
                    timing.add(phase, duration, pair=context.pair)
    pair_run_list = [evaluation.run for evaluation in evaluations]
    started = perf_counter()
    pair_run_list.sort(key=_run_sort_key)
    if timing is not None:
        timing.add("sort_pair_runs", perf_counter() - started, pair=context.pair)
    if (
        not materialize_case_results
        and len(sweep_configs) > 1
        and pair_run_list
        and not pair_run_list[0].case_results
    ):
        started = perf_counter()
        pair_run_list[0] = _evaluate_sweep_run(
            context=context,
            config=pair_run_list[0].config,
            run_index=pair_run_list[0].run_index,
            objective_weights=objective_weights,
            materialize_case_results=True,
            prepared_inputs=prepared_inputs_by_run_index[pair_run_list[0].run_index - 1],
        ).run
        if timing is not None:
            timing.add(
                "rehydrate_best_run_case_results",
                perf_counter() - started,
                pair=context.pair,
            )
    return pair_run_list
