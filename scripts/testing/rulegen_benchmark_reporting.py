#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.rulegen.benchmarking import (
    RulegenBenchmarkCase,
    RulegenBenchmarkSummary,
)

from rulegen_benchmark_models import BenchmarkTimingCollector, SweepConfig, SweepRun
from rulegen_benchmark_presets import (
    BenchmarkPreset,
    format_benchmark_presets_listing,
    load_benchmark_presets,
)
from rulegen_benchmark_resources import _load_dataset_cases
from rulegen_benchmark_sweep import _run_sort_key


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRESET_PATH = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"


def _build_pair_report_payload(
    *,
    case_count: int,
    runs: Sequence[SweepRun],
    resources: Mapping[str, object],
    word_package_snapshot: Mapping[str, object],
    include_case_results: bool,
) -> dict[str, object]:
    return {
        "case_count": int(case_count),
        "run_count": len(runs),
        "resources": dict(resources),
        "word_package_snapshot": dict(word_package_snapshot),
        "best_run": runs[0].to_dict(include_case_results=True) if runs else None,
        "runs": [run.to_dict(include_case_results=include_case_results) for run in runs],
    }


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return dict(payload)


def _resolve_path_from_report_payload(value: object, *, project_root: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Expected non-empty path in benchmark report payload.")
    path = Path(text)
    candidates: list[Path] = []
    if path.is_absolute() or text.startswith(("/", "\\")):
        candidates.append(path)
        parts = list(path.parts)
        if "docs" in parts:
            docs_index = parts.index("docs")
            candidates.append((project_root / Path(*parts[docs_index:])).resolve())
        candidates.append((project_root / "docs" / "test_inputs" / path.name).resolve())
        if path.suffix.lower() == ".json":
            candidates.append((project_root / "docs" / "test_inputs" / path.stem).resolve())
    else:
        candidates.append((project_root / path).resolve())
        if path.suffix.lower() == ".json":
            candidates.append((project_root / path.stem).resolve())

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return candidates[0].resolve()


def _summary_from_payload(payload: Mapping[str, object]) -> RulegenBenchmarkSummary:
    return RulegenBenchmarkSummary(
        pair=str(payload.get("pair") or "").strip(),
        case_count=int(payload.get("case_count") or 0),
        top1_correct_count=int(payload.get("top1_correct_count") or 0),
        top3_contains_expected_count=int(payload.get("top3_contains_expected_count") or 0),
        forbidden_top1_count=int(payload.get("forbidden_top1_count") or 0),
        forbidden_any_count=int(payload.get("forbidden_any_count") or 0),
        avg_rules_per_target=float(payload.get("avg_rules_per_target") or 0.0),
        avg_top1_confidence=(
            float(payload["avg_top1_confidence"])
            if payload.get("avg_top1_confidence") is not None
            else None
        ),
        variant_rule_count=int(payload.get("variant_rule_count") or 0),
        total_rule_count=int(payload.get("total_rule_count") or 0),
        variant_top1_count=int(payload.get("variant_top1_count") or 0),
        top1_accuracy=float(payload.get("top1_accuracy") or 0.0),
        top3_recall=float(payload.get("top3_recall") or 0.0),
        forbidden_top1_rate=float(payload.get("forbidden_top1_rate") or 0.0),
        forbidden_any_rate=float(payload.get("forbidden_any_rate") or 0.0),
        variant_rule_rate=float(payload.get("variant_rule_rate") or 0.0),
        variant_top1_rate=float(payload.get("variant_top1_rate") or 0.0),
        objective_score=float(payload.get("objective_score") or 0.0),
    )


def _config_from_payload(payload: Mapping[str, object]) -> SweepConfig:
    families = payload.get("kaikki_policy_risk_families") or ()
    if isinstance(families, Sequence) and not isinstance(families, (str, bytes)):
        normalized_families = tuple(
            str(item or "").strip() for item in families if str(item or "").strip()
        )
    else:
        normalized_families = ()
    return SweepConfig(
        max_definitions_per_target=(
            int(payload["max_definitions_per_target"])
            if payload.get("max_definitions_per_target") is not None
            else None
        ),
        max_rules_per_target=(
            int(payload["max_rules_per_target"])
            if payload.get("max_rules_per_target") is not None
            else None
        ),
        confidence_threshold=float(payload.get("confidence_threshold") or 0.0),
        semantic_demotion_scale=float(payload.get("semantic_demotion_scale") or 0.0),
        exact_gloss_demotion_enabled=bool(payload.get("exact_gloss_demotion_enabled", False)),
        include_variants=bool(payload.get("include_variants", False)),
        pos_scoring_enabled=bool(payload.get("pos_scoring_enabled", False)),
        pos_exact_match_bonus=float(payload.get("pos_exact_match_bonus") or 0.0),
        pos_compatible_match_bonus=float(payload.get("pos_compatible_match_bonus") or 0.0),
        score_weight_dict_priority=float(payload.get("score_weight_dict_priority") or 0.0),
        score_weight_frequency_weight=float(payload.get("score_weight_frequency_weight") or 0.0),
        score_weight_pos_match=float(payload.get("score_weight_pos_match") or 0.0),
        score_weight_variant_penalty=float(payload.get("score_weight_variant_penalty") or 0.0),
        score_weight_phrase_penalty=float(payload.get("score_weight_phrase_penalty") or 0.0),
        score_weight_embedding=float(payload.get("score_weight_embedding") or 0.0),
        reverse_check_enabled=bool(payload.get("reverse_check_enabled", False)),
        reverse_check_match_bonus=float(payload.get("reverse_check_match_bonus") or 0.0),
        reverse_check_near_bonus=float(payload.get("reverse_check_near_bonus") or 0.0),
        reverse_check_near_rank_max=int(payload.get("reverse_check_near_rank_max") or 0),
        reverse_check_far_hit_penalty=float(payload.get("reverse_check_far_hit_penalty") or 0.0),
        reverse_check_miss_penalty=float(payload.get("reverse_check_miss_penalty") or 0.0),
        reverse_check_exact_hit_ambiguity_threshold=int(
            payload.get("reverse_check_exact_hit_ambiguity_threshold") or 0
        ),
        reverse_check_exact_hit_ambiguity_penalty=float(
            payload.get("reverse_check_exact_hit_ambiguity_penalty") or 0.0
        ),
        kaikki_policy_live_demotion=bool(payload.get("kaikki_policy_live_demotion", False)),
        kaikki_policy_risk_families=normalized_families,
        reverse_check_exact_hit_specificity_bonus=float(
            payload.get("reverse_check_exact_hit_specificity_bonus") or 0.0
        ),
        kaikki_policy_late_sense_penalty=float(
            payload.get("kaikki_policy_late_sense_penalty") or 0.0
        ),
    )


def _run_from_payload(
    payload: Mapping[str, object],
    *,
    case_results_override: Optional[Sequence[Mapping[str, object]]] = None,
) -> SweepRun:
    raw_config = payload.get("config")
    if not isinstance(raw_config, Mapping):
        raise ValueError("Benchmark run payload is missing `config` object.")
    raw_summary = payload.get("summary")
    if not isinstance(raw_summary, Mapping):
        raise ValueError("Benchmark run payload is missing `summary` object.")
    raw_case_results = payload.get("case_results")
    case_results: tuple[dict[str, object], ...] = ()
    if case_results_override is not None:
        case_results = tuple(dict(item) for item in case_results_override)
    elif isinstance(raw_case_results, Sequence) and not isinstance(raw_case_results, (str, bytes)):
        case_results = tuple(dict(item) for item in raw_case_results if isinstance(item, Mapping))
    return SweepRun(
        pair=str(payload.get("pair") or "").strip(),
        run_index=int(payload.get("run_index") or 0),
        config=_config_from_payload(raw_config),
        summary=_summary_from_payload(raw_summary),
        case_results=case_results,
    )


def _load_pair_runs_from_report_payload(
    report_payload: Mapping[str, object],
) -> dict[str, list[SweepRun]]:
    raw_pairs = report_payload.get("pairs")
    if not isinstance(raw_pairs, Mapping):
        raise ValueError("Benchmark report payload is missing `pairs` object.")
    pair_runs: dict[str, list[SweepRun]] = {}
    for raw_pair, raw_pair_payload in raw_pairs.items():
        pair = str(raw_pair or "").strip()
        if not pair or not isinstance(raw_pair_payload, Mapping):
            continue
        best_run_payload = raw_pair_payload.get("best_run")
        best_case_results: Optional[tuple[dict[str, object], ...]] = None
        best_run_index: Optional[int] = None
        if isinstance(best_run_payload, Mapping):
            best_run_index = int(best_run_payload.get("run_index") or 0)
            raw_case_results = best_run_payload.get("case_results")
            if isinstance(raw_case_results, Sequence) and not isinstance(
                raw_case_results, (str, bytes)
            ):
                best_case_results = tuple(
                    dict(item) for item in raw_case_results if isinstance(item, Mapping)
                )
        runs: list[SweepRun] = []
        raw_runs = raw_pair_payload.get("runs")
        if isinstance(raw_runs, Sequence) and not isinstance(raw_runs, (str, bytes)):
            for raw_run in raw_runs:
                if not isinstance(raw_run, Mapping):
                    continue
                run_index = int(raw_run.get("run_index") or 0)
                case_results_override = (
                    best_case_results
                    if best_case_results is not None and best_run_index == run_index
                    else None
                )
                runs.append(
                    _run_from_payload(
                        raw_run,
                        case_results_override=case_results_override,
                    )
                )
        if not runs and isinstance(best_run_payload, Mapping):
            runs.append(
                _run_from_payload(
                    best_run_payload,
                    case_results_override=best_case_results,
                )
            )
        runs.sort(key=_run_sort_key)
        pair_runs[pair] = runs
    return pair_runs


def _load_html_report_renderer():
    module_name = "rulegen_benchmark_html"
    if __package__:
        module_name = f"{__package__}.rulegen_benchmark_html"
    module = __import__(module_name, fromlist=["render_html_report"])
    return module.render_html_report


def _render_markdown_report(
    *,
    pair_runs: Mapping[str, Sequence[SweepRun]],
    top_n: int,
) -> str:
    lines: list[str] = [
        "# Rulegen Benchmark Sweep",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for pair, runs in sorted(pair_runs.items()):
        lines.append(f"## {pair}")
        lines.append("")
        if not runs:
            lines.append("No runs.")
            lines.append("")
            continue
        lines.append(
            "| Rank | Objective | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Config |"
        )
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---|")
        for rank, run in enumerate(runs[:top_n], start=1):
            summary = run.summary
            lines.append(
                "| "
                f"{rank} | "
                f"{summary.objective_score:.3f} | "
                f"{summary.top1_accuracy:.2%} | "
                f"{summary.top3_recall:.2%} | "
                f"{summary.forbidden_top1_rate:.2%} | "
                f"{summary.forbidden_any_rate:.2%} | "
                f"{summary.avg_rules_per_target:.2f} | "
                f"`{run.config.label()}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _write_benchmark_outputs(
    *,
    report_payload: Mapping[str, object],
    markdown_report: Optional[str],
    html_report: Optional[str],
    json_output: Optional[Path],
    markdown_output: Optional[Path],
    html_output: Optional[Path],
    timing_payload: Mapping[str, object],
    timing_json_output: Optional[Path],
) -> None:
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(report_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if markdown_output is not None and markdown_report is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(markdown_report, encoding="utf-8")
    if html_output is not None and html_report is not None:
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_text(html_report, encoding="utf-8")
    if timing_json_output is not None:
        timing_json_output.parent.mkdir(parents=True, exist_ok=True)
        timing_json_output.write_text(
            json.dumps(timing_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _render_report_artifacts(
    *,
    report_payload: dict[str, object],
    pair_runs: Mapping[str, Sequence[SweepRun]],
    cases_by_pair: Mapping[str, Sequence[RulegenBenchmarkCase]],
    top_n: int,
    timing: BenchmarkTimingCollector,
    wall_clock_started: float,
) -> tuple[str, str, dict[str, object]]:
    from time import perf_counter

    started = perf_counter()
    markdown_report = _render_markdown_report(pair_runs=pair_runs, top_n=top_n)
    timing.add("render_markdown", perf_counter() - started)

    report_payload["timing"] = timing.to_dict(
        wall_clock_seconds=perf_counter() - wall_clock_started
    )
    started = perf_counter()
    html_report = _load_html_report_renderer()(
        report_payload=report_payload,
        pair_runs=pair_runs,
        cases_by_pair=cases_by_pair,
        top_n=top_n,
    )
    timing.add("render_html", perf_counter() - started)
    timing_payload = timing.to_dict(wall_clock_seconds=perf_counter() - wall_clock_started)
    report_payload["timing"] = timing_payload
    return markdown_report, html_report, timing_payload


def _load_render_inputs_from_report_payload(
    report_payload: Mapping[str, object],
) -> tuple[dict[str, list[SweepRun]], dict[str, list[RulegenBenchmarkCase]]]:
    pair_runs = _load_pair_runs_from_report_payload(report_payload)
    dataset_path = _resolve_path_from_report_payload(
        report_payload.get("dataset_path"),
        project_root=PROJECT_ROOT,
    )
    pair_filter = set(pair_runs) or None
    _, cases_by_pair = _load_dataset_cases(dataset_path, pair_filter=pair_filter)
    return pair_runs, cases_by_pair


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep rulegen parameters over labeled benchmark cases and rank settings by objective score."
        )
    )
    parser.add_argument(
        "--preset-file",
        type=Path,
        default=DEFAULT_PRESET_PATH,
        help="Path to benchmark preset registry JSON.",
    )
    parser.add_argument(
        "--preset",
        help="Optional named benchmark preset from the preset registry.",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available benchmark presets and exit.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases",
        help="Path to benchmark dataset JSON file or LP-specific dataset directory.",
    )
    parser.add_argument(
        "--pairs",
        help="Optional comma-separated pair filter (default: all pairs present in dataset).",
    )
    parser.add_argument(
        "--profile-id", default="default", help="SRS profile id for word_package hints."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override LexiShift data root (default: platform data dir or LEXISHIFT_DATA_DIR).",
    )
    parser.add_argument(
        "--word-package-snapshot-json",
        type=Path,
        help=(
            "Optional frozen per-pair word_package snapshot JSON. When provided for a pair, "
            "the benchmark uses it instead of the live SRS store for that pair."
        ),
    )
    parser.add_argument("--jmdict", type=Path, help="Optional JMdict override path.")
    parser.add_argument(
        "--translation-dict-en-de",
        dest="translation_dict_en_de",
        type=Path,
        help="Optional translation-dictionary override for en-de pair (deu-eng.sqlite).",
    )
    parser.add_argument(
        "--translation-dict-en-es",
        dest="translation_dict_en_es",
        type=Path,
        help=(
            "Optional translation-dictionary override for en-es pair "
            "(wiktionary-es-en.sqlite / spa-eng.sqlite)."
        ),
    )
    parser.add_argument(
        "--translation-dict-es-en",
        dest="translation_dict_es_en",
        type=Path,
        help="Optional translation-dictionary override for es-en pair (eng-spa.sqlite).",
    )
    parser.add_argument("--max-definitions-values", default="3")
    parser.add_argument("--max-rules-values", default="none")
    parser.add_argument("--confidence-threshold-values", default="0.0")
    parser.add_argument("--semantic-demotion-scale-values", default="1.0")
    parser.add_argument("--exact-gloss-demotion-values", default="false")
    parser.add_argument("--include-variants-values", default="true,false")
    parser.add_argument("--pos-scoring-values", default="true,false")
    parser.add_argument("--pos-exact-values", default="1.0")
    parser.add_argument("--pos-compatible-values", default="0.5")
    parser.add_argument("--score-weight-dict-values", default="0.6")
    parser.add_argument("--score-weight-frequency-values", default="0.2")
    parser.add_argument("--score-weight-pos-values", default="0.1")
    parser.add_argument("--score-weight-variant-values", default="0.1")
    parser.add_argument("--score-weight-phrase-values", default="0.1")
    parser.add_argument("--score-weight-embedding-values", default="0.2")
    parser.add_argument("--reverse-check-enabled-values", default="false,true")
    parser.add_argument("--reverse-check-match-bonus-values", default="0.2")
    parser.add_argument("--reverse-check-near-bonus-values", default="0.1")
    parser.add_argument("--reverse-check-near-rank-max-values", default="2")
    parser.add_argument("--reverse-check-far-hit-penalty-values", default="0.0")
    parser.add_argument("--reverse-check-miss-penalty-values", default="0.2")
    parser.add_argument("--reverse-check-exact-hit-ambiguity-threshold-values", default="0")
    parser.add_argument("--reverse-check-exact-hit-ambiguity-penalty-values", default="0.0")
    parser.add_argument(
        "--reverse-check-exact-hit-specificity-bonus-values",
        default="0.0,0.1,0.2",
    )
    parser.add_argument("--kaikki-policy-live-demotion-values", default="false,true")
    parser.add_argument(
        "--kaikki-policy-risk-family-sets",
        default=(
            "math_geometry+government_law+hunting_fishing_tools+"
            "register_region+abbreviation_ellipsis_formof"
        ),
    )
    parser.add_argument(
        "--kaikki-policy-late-sense-penalty-values",
        default="0.0,0.1,0.2",
    )
    parser.add_argument("--objective-top1-weight", type=float, default=100.0)
    parser.add_argument("--objective-top3-weight", type=float, default=60.0)
    parser.add_argument("--objective-forbidden-top1-weight", type=float, default=120.0)
    parser.add_argument("--objective-forbidden-any-weight", type=float, default=80.0)
    parser.add_argument("--objective-avg-rules-weight", type=float, default=6.0)
    parser.add_argument("--objective-variant-top1-weight", type=float, default=10.0)
    parser.add_argument(
        "--max-configurations",
        type=int,
        default=500,
        help="Safety cap for number of sweep combinations per pair.",
    )
    parser.add_argument("--top-runs", type=int, default=10, help="Top-N runs per pair in markdown.")
    parser.add_argument(
        "--include-case-results",
        action="store_true",
        help="Include per-case rule outputs for every run in JSON output.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_latest.json",
        help="Path to write JSON report.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_latest.md",
        help="Path to write markdown leaderboard.",
    )
    parser.add_argument(
        "--html-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_latest.html",
        help="Path to write styled HTML dashboard.",
    )
    parser.add_argument(
        "--timing-json-output",
        type=Path,
        help="Optional path to write benchmark timing breakdown JSON.",
    )
    parser.add_argument(
        "--compute-only",
        action="store_true",
        help="Write JSON compute output only and skip markdown/HTML materialization.",
    )
    parser.add_argument(
        "--render-from-json",
        type=Path,
        help="Load an existing benchmark JSON report and render markdown/HTML without rerunning the sweep.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of worker processes to use for config execution (default: 1).",
    )
    return parser


def _resolve_cli_with_preset(
    *,
    argv: Sequence[str],
) -> tuple[argparse.Namespace, Optional[BenchmarkPreset]]:
    parser = _build_parser()
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--preset-file", type=Path, default=DEFAULT_PRESET_PATH)
    pre_parser.add_argument("--preset")
    pre_parser.add_argument("--list-presets", action="store_true")
    pre_args, remaining_argv = pre_parser.parse_known_args(list(argv))
    preset_file = Path(pre_args.preset_file)
    presets = load_benchmark_presets(preset_file)
    if pre_args.list_presets:
        print(format_benchmark_presets_listing(presets))
        raise SystemExit(0)
    selected_preset: Optional[BenchmarkPreset] = None
    effective_argv = list(remaining_argv)
    preset_name = str(pre_args.preset or "").strip()
    if preset_name:
        selected_preset = presets.get(preset_name)
        if selected_preset is None:
            available = ", ".join(sorted(presets))
            raise ValueError(
                f"Unknown preset `{preset_name}` in {preset_file}. Available: {available}"
            )
        effective_argv = list(selected_preset.args) + effective_argv
    args = parser.parse_args(effective_argv)
    args.preset_file = preset_file
    args.preset = selected_preset.name if selected_preset is not None else None
    args.list_presets = False
    return args, selected_preset
