#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from time import perf_counter
from typing import Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.lp_capabilities import resolve_pair_capability  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.rulegen.benchmarking import (  # noqa: E402
    RulegenBenchmarkObjectiveWeights,
)

from rulegen_benchmark_compiled import (  # noqa: E402
    _build_compiled_case_refs,
    _build_compiled_case_result_table,
    _build_compiled_case_table,
    _build_compiled_rule_table,
    _build_compiled_rule_table_from_en_es_selected_rows,
    _build_compiled_rule_table_from_rules,
    _evaluate_benchmark_case_compiled,
    _evaluate_case_payloads_with_table,
    _evaluate_case_results,
    _evaluate_case_results_with_table,
    _summarize_compiled_case_results,
)
from rulegen_benchmark_models import (  # noqa: E402
    BenchmarkTimingCollector,
    CompiledBenchmarkCaseRef,
    CompiledBenchmarkCaseResultTable,
    CompiledBenchmarkCaseTable,
    PairBenchmarkContext,
    SweepConfig,
    SweepRun,
    SweepRunEvaluation,
    _format_exact_hit_ambiguity_label,
    _format_exact_hit_specificity_label,
    _format_kaikki_policy_family_label,
    _format_kaikki_provenance_label,
)
from rulegen_benchmark_reporting import (  # noqa: E402
    DEFAULT_PRESET_PATH,
    _build_pair_report_payload,
    _build_parser,
    _config_from_payload,
    _load_html_report_renderer,
    _load_json_object,
    _load_pair_runs_from_report_payload,
    _load_render_inputs_from_report_payload,
    _render_markdown_report,
    _render_report_artifacts,
    _resolve_cli_with_preset,
    _resolve_path_from_report_payload,
    _run_from_payload,
    _summary_from_payload,
    _write_benchmark_outputs,
)
from rulegen_benchmark_resources import (  # noqa: E402
    _build_en_es_reverse_headword_norm_index,
    _build_pair_benchmark_context,
    _build_pair_compiled_rulegen_context,
    _build_pair_resources_payload,
    _build_reverse_preload_headwords,
    _build_word_package_snapshot,
    _compute_file_sha256,
    _compute_file_sha256_uncached,
    _expand_reverse_preload_headwords,
    _load_dataset_cases,
    _load_frozen_word_package_snapshots,
    _preload_pair_gloss_records,
    _resolve_pair_resources_for_benchmark,
    _load_store,
)
from rulegen_benchmark_sweep import (  # noqa: E402
    ProcessPoolExecutor,
    _build_sweep_configs,
    _evaluate_sweep_run,
    _evaluate_sweep_run_from_worker_state,
    _parse_family_set_specs,
    _run_pair_sweep,
    as_completed,
    run_rules_with_adapter,
)

__all__ = [
    "BenchmarkTimingCollector",
    "CompiledBenchmarkCaseRef",
    "CompiledBenchmarkCaseResultTable",
    "CompiledBenchmarkCaseTable",
    "DEFAULT_PRESET_PATH",
    "PairBenchmarkContext",
    "ProcessPoolExecutor",
    "SweepConfig",
    "SweepRun",
    "SweepRunEvaluation",
    "_build_compiled_case_refs",
    "_build_compiled_case_result_table",
    "_build_compiled_case_table",
    "_build_compiled_rule_table",
    "_build_compiled_rule_table_from_en_es_selected_rows",
    "_build_compiled_rule_table_from_rules",
    "_build_en_es_reverse_headword_norm_index",
    "_build_pair_benchmark_context",
    "_build_pair_compiled_rulegen_context",
    "_build_pair_report_payload",
    "_build_pair_resources_payload",
    "_build_parser",
    "_build_reverse_preload_headwords",
    "_build_sweep_configs",
    "_build_word_package_snapshot",
    "_compute_file_sha256",
    "_compute_file_sha256_uncached",
    "_config_from_payload",
    "_evaluate_benchmark_case_compiled",
    "_evaluate_case_payloads_with_table",
    "_evaluate_case_results",
    "_evaluate_case_results_with_table",
    "_evaluate_sweep_run",
    "_evaluate_sweep_run_from_worker_state",
    "_expand_reverse_preload_headwords",
    "_format_exact_hit_ambiguity_label",
    "_format_exact_hit_specificity_label",
    "_format_kaikki_policy_family_label",
    "_format_kaikki_provenance_label",
    "_load_dataset_cases",
    "_load_frozen_word_package_snapshots",
    "_load_html_report_renderer",
    "_load_json_object",
    "_load_pair_runs_from_report_payload",
    "_load_render_inputs_from_report_payload",
    "_load_store",
    "_parse_family_set_specs",
    "_preload_pair_gloss_records",
    "_render_markdown_report",
    "_render_report_artifacts",
    "_resolve_cli_with_preset",
    "_resolve_pair_resources_for_benchmark",
    "_resolve_path_from_report_payload",
    "_run_from_payload",
    "_run_pair_sweep",
    "_summarize_compiled_case_results",
    "_summary_from_payload",
    "_write_benchmark_outputs",
    "as_completed",
    "main",
    "run_rules_with_adapter",
]


def main(argv: Optional[Sequence[str]] = None) -> None:
    wall_clock_started = perf_counter()
    timing = BenchmarkTimingCollector()
    args, selected_preset = _resolve_cli_with_preset(
        argv=tuple(argv) if argv is not None else tuple(sys.argv[1:])
    )
    if args.compute_only and args.render_from_json is not None:
        raise ValueError("--compute-only and --render-from-json cannot be combined.")

    if args.render_from_json is not None:
        started = perf_counter()
        report_payload = _load_json_object(args.render_from_json)
        timing.add("load_report_json", perf_counter() - started)
        started = perf_counter()
        pair_runs, cases_by_pair = _load_render_inputs_from_report_payload(report_payload)
        timing.add("load_render_inputs", perf_counter() - started)
        markdown_report, html_report, timing_payload = _render_report_artifacts(
            report_payload=report_payload,
            pair_runs=pair_runs,
            cases_by_pair=cases_by_pair,
            top_n=max(1, int(args.top_runs)),
            timing=timing,
            wall_clock_started=wall_clock_started,
        )
        _write_benchmark_outputs(
            report_payload=report_payload,
            markdown_report=markdown_report,
            html_report=html_report,
            json_output=None,
            markdown_output=args.markdown_output,
            html_output=args.html_output,
            timing_payload=timing_payload,
            timing_json_output=args.timing_json_output,
        )
        print(f"source_json: {args.render_from_json}")
        print(f"markdown_output: {args.markdown_output}")
        print(f"html_output: {args.html_output}")
        if args.timing_json_output is not None:
            print(f"timing_json_output: {args.timing_json_output}")
        return

    pair_filter = (
        {item.strip().lower() for item in args.pairs.split(",") if item.strip()}
        if args.pairs
        else None
    )
    started = perf_counter()
    dataset_payload, cases_by_pair = _load_dataset_cases(args.dataset, pair_filter=pair_filter)
    timing.add("load_dataset", perf_counter() - started)
    if not cases_by_pair:
        raise ValueError("No benchmark cases found after applying filters.")

    started = perf_counter()
    sweep_configs = _build_sweep_configs(args)
    timing.add("build_sweep_configs", perf_counter() - started)
    if len(sweep_configs) > max(1, int(args.max_configurations)):
        raise ValueError(
            f"Sweep combinations={len(sweep_configs)} exceed --max-configurations={args.max_configurations}."
        )

    objective_weights = RulegenBenchmarkObjectiveWeights(
        top1_accuracy=float(args.objective_top1_weight),
        top3_recall=float(args.objective_top3_weight),
        forbidden_top1_rate=float(args.objective_forbidden_top1_weight),
        forbidden_any_rate=float(args.objective_forbidden_any_weight),
        avg_rules_per_target=float(args.objective_avg_rules_weight),
        variant_top1_rate=float(args.objective_variant_top1_weight),
    )

    started = perf_counter()
    paths = build_helper_paths(args.data_root)
    store = _load_store(paths, profile_id=args.profile_id)
    timing.add("load_store", perf_counter() - started)
    frozen_word_package_snapshots = (
        _load_frozen_word_package_snapshots(args.word_package_snapshot_json)
        if args.word_package_snapshot_json is not None
        else {}
    )

    translation_dict_overrides: dict[str, Optional[Path]] = {
        "en-de": args.translation_dict_en_de,
        "en-es": args.translation_dict_en_es,
        "es-en": args.translation_dict_es_en,
    }
    reverse_translation_dict_overrides: dict[str, Optional[Path]] = {
        "en-es": args.translation_dict_es_en,
        "es-en": args.translation_dict_en_es,
    }

    pair_runs: dict[str, list[SweepRun]] = {}
    pair_resources: dict[str, dict[str, object]] = {}
    pair_word_package_snapshots: dict[str, dict[str, object]] = {}
    for pair, cases in sorted(cases_by_pair.items()):
        capability = resolve_pair_capability(pair)
        if capability.rulegen_mode is None:
            continue
        context = _build_pair_benchmark_context(
            paths=paths,
            store=store,
            pair=pair,
            cases=cases,
            jmdict_override=args.jmdict,
            translation_dict_override=translation_dict_overrides.get(pair),
            reverse_translation_dict_override=reverse_translation_dict_overrides.get(pair),
            frozen_word_package_snapshots=frozen_word_package_snapshots,
            timing=timing,
        )
        pair_resources[pair] = dict(context.resources)
        pair_word_package_snapshots[pair] = dict(context.word_package_snapshot)

        pair_run_list = _run_pair_sweep(
            context=context,
            sweep_configs=sweep_configs,
            objective_weights=objective_weights,
            jobs=args.jobs,
            timing=timing,
            materialize_case_results=args.include_case_results,
        )
        pair_runs[pair] = pair_run_list

    timing_payload = timing.to_dict(wall_clock_seconds=perf_counter() - wall_clock_started)
    report_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(args.dataset),
        "dataset_metadata": {
            key: value for key, value in dataset_payload.items() if key != "cases"
        },
        "profile_id": str(args.profile_id),
        "data_root": str(paths.data_root),
        "sweep": {
            "pair_filter": sorted(pair_filter) if pair_filter else None,
            "configuration_count": len(sweep_configs),
            "jobs": max(1, int(args.jobs)),
            "word_package_snapshot_json": (
                str(args.word_package_snapshot_json)
                if args.word_package_snapshot_json is not None
                else None
            ),
            "preset": (
                {
                    "name": selected_preset.name,
                    "description": selected_preset.description,
                    "preset_file": str(args.preset_file),
                    "args": list(selected_preset.args),
                }
                if selected_preset is not None
                else None
            ),
            "objective_weights": {
                "top1_accuracy": objective_weights.top1_accuracy,
                "top3_recall": objective_weights.top3_recall,
                "forbidden_top1_rate": objective_weights.forbidden_top1_rate,
                "forbidden_any_rate": objective_weights.forbidden_any_rate,
                "avg_rules_per_target": objective_weights.avg_rules_per_target,
                "variant_top1_rate": objective_weights.variant_top1_rate,
            },
        },
        "resources": pair_resources,
        "timing": timing_payload,
        "pairs": {},
    }

    for pair, runs in sorted(pair_runs.items()):
        report_payload["pairs"][pair] = _build_pair_report_payload(
            case_count=len(cases_by_pair.get(pair, ())),
            runs=runs,
            resources=pair_resources.get(pair, {}),
            word_package_snapshot=pair_word_package_snapshots.get(pair, {}),
            include_case_results=args.include_case_results,
        )

    timing_payload = timing.to_dict(wall_clock_seconds=perf_counter() - wall_clock_started)
    report_payload["timing"] = timing_payload
    markdown_report: Optional[str] = None
    html_report: Optional[str] = None
    if not args.compute_only:
        markdown_report, html_report, timing_payload = _render_report_artifacts(
            report_payload=report_payload,
            pair_runs=pair_runs,
            cases_by_pair=cases_by_pair,
            top_n=max(1, int(args.top_runs)),
            timing=timing,
            wall_clock_started=wall_clock_started,
        )
    _write_benchmark_outputs(
        report_payload=report_payload,
        markdown_report=markdown_report,
        html_report=html_report,
        json_output=args.json_output,
        markdown_output=(None if args.compute_only else args.markdown_output),
        html_output=(None if args.compute_only else args.html_output),
        timing_payload=timing_payload,
        timing_json_output=args.timing_json_output,
    )

    print(f"pairs: {len(pair_runs)}")
    print(f"configs_per_pair: {len(sweep_configs)}")
    print(f"json_output: {args.json_output}")
    if args.compute_only:
        print("materialization: skipped (--compute-only)")
    else:
        print(f"markdown_output: {args.markdown_output}")
        print(f"html_output: {args.html_output}")
    if args.timing_json_output is not None:
        print(f"timing_json_output: {args.timing_json_output}")
    for pair, runs in sorted(pair_runs.items()):
        if not runs:
            continue
        best = runs[0]
        summary = best.summary
        print(
            f"[{pair}] best objective={summary.objective_score:.3f} "
            f"top1={summary.top1_accuracy:.2%} "
            f"top3={summary.top3_recall:.2%} "
            f"forbid_top1={summary.forbidden_top1_rate:.2%} "
            f"config={best.config.label()}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
