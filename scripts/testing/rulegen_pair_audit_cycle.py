#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

from rulegen_reverse_profiles import REVERSE_CHECK_PROFILES


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _print_command(command: list[str]) -> None:
    print(f"+ {shlex.join(command)}")


def _run_command(command: list[str]) -> int:
    _print_command(command)
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )
    return int(result.returncode)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return path.resolve()


def _summarize_benchmark(path: Path, *, pairs: list[str]) -> None:
    payload = _load_json(path)
    pair_payload = payload.get("pairs")
    if not isinstance(pair_payload, dict):
        return
    print("benchmark_summary:")
    for pair in pairs:
        pair_key = str(pair).strip().lower()
        details = pair_payload.get(pair_key)
        if not isinstance(details, dict):
            continue
        best = details.get("best_run")
        if not isinstance(best, dict):
            continue
        summary = best.get("summary")
        if not isinstance(summary, dict):
            continue
        config = str(best.get("config_label") or "").strip()
        objective = float(summary.get("objective_score") or 0.0)
        top1 = float(summary.get("top1_accuracy") or 0.0)
        top3 = float(summary.get("top3_recall") or 0.0)
        forbidden_any = float(summary.get("forbidden_any_rate") or 0.0)
        avg_rules = float(summary.get("avg_rules_per_target") or 0.0)
        print(
            f"  [{pair_key}] objective={objective:.3f} "
            f"top1={top1:.2%} top3={top3:.2%} "
            f"forbidden_any={forbidden_any:.2%} avg_rules={avg_rules:.2f}"
        )
        print(f"    config={config}")


def _summarize_triage(path: Path) -> None:
    payload = _load_json(path)
    items = payload.get("items")
    if not isinstance(items, list):
        return
    print(f"triage_items: {len(items)}")
    for index, item in enumerate(items[:10], start=1):
        if not isinstance(item, dict):
            continue
        pair = str(item.get("pair") or "")
        case_id = str(item.get("case_id") or "")
        status = str(item.get("status") or "")
        top1 = str(item.get("top1_source") or "")
        print(f"  {index}. [{pair}] {case_id} status={status} top1={top1}")


def _build_cycle_commands(
    *,
    pairs: list[str],
    benchmark_preset: str | None,
    quality_gate_pair_scope: str | None,
    max_definitions_values: str,
    max_rules_values: str,
    confidence_threshold_values: str,
    semantic_demotion_scale_values: str,
    include_variants_values: str,
    pos_scoring_values: str,
    score_weight_pos_values: str,
    reverse_enabled_values: str,
    reverse_match_bonus_values: str,
    reverse_near_bonus_values: str,
    reverse_near_rank_max_values: str,
    reverse_far_hit_penalty_values: str,
    reverse_miss_penalty_values: str,
    top_runs: int,
    max_configurations: int,
    benchmark_json: Path,
    benchmark_markdown: Path,
    benchmark_html: Path,
    quality_gate_json: Path,
    triage_json: Path,
    triage_markdown: Path,
    policy_json: Path,
    baseline_json: Path,
    pos_probe_json: Path,
    pos_inventory_json: Path,
) -> tuple[list[str], list[str], list[str], list[str]]:
    benchmark_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_benchmark.py"),
    ]
    if benchmark_preset:
        benchmark_cmd.extend(["--preset", str(benchmark_preset)])
    else:
        benchmark_cmd.extend(
            [
                "--pairs",
                ",".join(pairs),
                "--max-definitions-values",
                str(max_definitions_values),
                "--max-rules-values",
                str(max_rules_values),
                "--confidence-threshold-values",
                str(confidence_threshold_values),
                "--semantic-demotion-scale-values",
                str(semantic_demotion_scale_values),
                "--include-variants-values",
                str(include_variants_values),
                "--pos-scoring-values",
                str(pos_scoring_values),
                "--score-weight-pos-values",
                str(score_weight_pos_values),
                "--reverse-check-enabled-values",
                str(reverse_enabled_values),
                "--reverse-check-match-bonus-values",
                str(reverse_match_bonus_values),
                "--reverse-check-near-bonus-values",
                str(reverse_near_bonus_values),
                "--reverse-check-near-rank-max-values",
                str(reverse_near_rank_max_values),
                "--reverse-check-far-hit-penalty-values",
                str(reverse_far_hit_penalty_values),
                "--reverse-check-miss-penalty-values",
                str(reverse_miss_penalty_values),
                "--max-configurations",
                str(int(max_configurations)),
            ]
        )
    benchmark_cmd.extend(
        [
            "--top-runs",
            str(int(top_runs)),
            "--compute-only",
            "--json-output",
            str(benchmark_json),
        ]
    )
    render_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_benchmark.py"),
        "--render-from-json",
        str(benchmark_json),
        "--top-runs",
        str(int(top_runs)),
        "--markdown-output",
        str(benchmark_markdown),
        "--html-output",
        str(benchmark_html),
    ]
    gate_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_quality_gate.py"),
        "--benchmark-json",
        str(benchmark_json),
        "--policy-json",
        str(policy_json),
        "--baseline-json",
        str(baseline_json),
        "--pos-probe-json",
        str(pos_probe_json),
        "--pos-inventory-json",
        str(pos_inventory_json),
        "--json-out",
        str(quality_gate_json),
    ]
    if quality_gate_pair_scope:
        gate_cmd.extend(["--pair-scope", str(quality_gate_pair_scope)])
    triage_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_benchmark_triage.py"),
        "--benchmark-json",
        str(benchmark_json),
        "--json-out",
        str(triage_json),
        "--markdown-out",
        str(triage_markdown),
    ]
    return benchmark_cmd, render_cmd, gate_cmd, triage_cmd


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run focused rulegen audit loop for selected language pairs "
            "(benchmark sweep -> quality gate -> triage extraction)."
        )
    )
    parser.add_argument(
        "--pairs",
        default="en-es,en-ja",
        help="Comma-separated language pairs (default: en-es,en-ja).",
    )
    parser.add_argument(
        "--benchmark-preset",
        default=None,
        help=(
            "Optional named benchmark preset passed through to rulegen_benchmark.py. "
            "When set, the preset defines the benchmark matrix and pair-specific tuning values."
        ),
    )
    parser.add_argument(
        "--quality-gate-pair-scope",
        default=None,
        help=(
            "Optional pair key to scope the quality gate to one benchmark lane. "
            "Useful for dedicated per-pair latest artifacts."
        ),
    )
    parser.add_argument(
        "--max-definitions-values",
        default="3",
    )
    parser.add_argument(
        "--max-rules-values",
        default="none,1",
    )
    parser.add_argument(
        "--confidence-threshold-values",
        default="0.0,0.05",
    )
    parser.add_argument(
        "--semantic-demotion-scale-values",
        default="1.0",
    )
    parser.add_argument(
        "--include-variants-values",
        default="false",
    )
    parser.add_argument(
        "--pos-scoring-values",
        default="true,false",
    )
    parser.add_argument(
        "--score-weight-pos-values",
        default="0.0,0.1",
    )
    parser.add_argument(
        "--reverse-check-enabled-values",
        default=None,
    )
    parser.add_argument(
        "--reverse-check-match-bonus-values",
        default=None,
    )
    parser.add_argument(
        "--reverse-check-near-bonus-values",
        default=None,
    )
    parser.add_argument(
        "--reverse-check-near-rank-max-values",
        default=None,
    )
    parser.add_argument(
        "--reverse-check-far-hit-penalty-values",
        default=None,
    )
    parser.add_argument(
        "--reverse-check-miss-penalty-values",
        default=None,
    )
    parser.add_argument(
        "--reverse-check-profile",
        choices=tuple(REVERSE_CHECK_PROFILES.keys()),
        default="default",
        help="Preset for reverse-check sweep values.",
    )
    parser.add_argument(
        "--top-runs",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--max-configurations",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "rulegen_benchmark_en_es_en_ja_latest.json",
    )
    parser.add_argument(
        "--benchmark-markdown",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_en_ja_latest.md",
    )
    parser.add_argument(
        "--benchmark-html",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "rulegen_benchmark_en_es_en_ja_latest.html",
    )
    parser.add_argument(
        "--triage-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "rulegen_benchmark_triage_en_es_en_ja_latest.json",
    )
    parser.add_argument(
        "--triage-markdown",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "rulegen_benchmark_triage_en_es_en_ja_latest.md",
    )
    parser.add_argument(
        "--policy-json",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_quality_policy.json",
    )
    parser.add_argument(
        "--baseline-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "baselines"
        / "rulegen_quality_baseline.json",
    )
    parser.add_argument(
        "--quality-gate-json",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_quality_gate_latest.json",
    )
    parser.add_argument(
        "--pos-probe-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "phase6_pos_inventory"
        / "phase6_pos_probe_2026-02-23_final.json",
    )
    parser.add_argument(
        "--pos-inventory-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "phase6_pos_inventory"
        / "phase6_pos_inventory_2026-02-23_final.json",
    )
    parser.add_argument(
        "--strict-gate",
        action="store_true",
        help="Exit non-zero if quality gate fails.",
    )
    args = parser.parse_args()

    args.benchmark_json = _resolve_repo_path(args.benchmark_json)
    args.benchmark_markdown = _resolve_repo_path(args.benchmark_markdown)
    args.benchmark_html = _resolve_repo_path(args.benchmark_html)
    args.triage_json = _resolve_repo_path(args.triage_json)
    args.triage_markdown = _resolve_repo_path(args.triage_markdown)
    args.policy_json = _resolve_repo_path(args.policy_json)
    args.baseline_json = _resolve_repo_path(args.baseline_json)
    args.quality_gate_json = _resolve_repo_path(args.quality_gate_json)
    args.pos_probe_json = _resolve_repo_path(args.pos_probe_json)
    args.pos_inventory_json = _resolve_repo_path(args.pos_inventory_json)

    reverse_profile = REVERSE_CHECK_PROFILES[str(args.reverse_check_profile)]
    reverse_enabled_values = (
        str(args.reverse_check_enabled_values)
        if args.reverse_check_enabled_values is not None
        else reverse_profile["enabled_values"]
    )
    reverse_match_bonus_values = (
        str(args.reverse_check_match_bonus_values)
        if args.reverse_check_match_bonus_values is not None
        else reverse_profile["match_bonus_values"]
    )
    reverse_near_bonus_values = (
        str(args.reverse_check_near_bonus_values)
        if args.reverse_check_near_bonus_values is not None
        else reverse_profile["near_bonus_values"]
    )
    reverse_near_rank_max_values = (
        str(args.reverse_check_near_rank_max_values)
        if args.reverse_check_near_rank_max_values is not None
        else reverse_profile["near_rank_max_values"]
    )
    reverse_far_hit_penalty_values = (
        str(args.reverse_check_far_hit_penalty_values)
        if args.reverse_check_far_hit_penalty_values is not None
        else reverse_profile["far_hit_penalty_values"]
    )
    reverse_miss_penalty_values = (
        str(args.reverse_check_miss_penalty_values)
        if args.reverse_check_miss_penalty_values is not None
        else reverse_profile["miss_penalty_values"]
    )

    pairs = [item.strip().lower() for item in str(args.pairs).split(",") if item.strip()]
    if not pairs:
        raise ValueError("No pairs provided.")

    benchmark_cmd, render_cmd, gate_cmd, triage_cmd = _build_cycle_commands(
        pairs=pairs,
        benchmark_preset=(
            str(args.benchmark_preset).strip() if str(args.benchmark_preset or "").strip() else None
        ),
        quality_gate_pair_scope=(
            str(args.quality_gate_pair_scope).strip().lower()
            if str(args.quality_gate_pair_scope or "").strip()
            else None
        ),
        max_definitions_values=str(args.max_definitions_values),
        max_rules_values=str(args.max_rules_values),
        confidence_threshold_values=str(args.confidence_threshold_values),
        semantic_demotion_scale_values=str(args.semantic_demotion_scale_values),
        include_variants_values=str(args.include_variants_values),
        pos_scoring_values=str(args.pos_scoring_values),
        score_weight_pos_values=str(args.score_weight_pos_values),
        reverse_enabled_values=reverse_enabled_values,
        reverse_match_bonus_values=reverse_match_bonus_values,
        reverse_near_bonus_values=reverse_near_bonus_values,
        reverse_near_rank_max_values=reverse_near_rank_max_values,
        reverse_far_hit_penalty_values=reverse_far_hit_penalty_values,
        reverse_miss_penalty_values=reverse_miss_penalty_values,
        top_runs=int(args.top_runs),
        max_configurations=int(args.max_configurations),
        benchmark_json=args.benchmark_json,
        benchmark_markdown=args.benchmark_markdown,
        benchmark_html=args.benchmark_html,
        quality_gate_json=args.quality_gate_json,
        triage_json=args.triage_json,
        triage_markdown=args.triage_markdown,
        policy_json=args.policy_json,
        baseline_json=args.baseline_json,
        pos_probe_json=args.pos_probe_json,
        pos_inventory_json=args.pos_inventory_json,
    )

    benchmark_rc = _run_command(benchmark_cmd)
    if benchmark_rc != 0:
        raise SystemExit(benchmark_rc)

    render_rc = _run_command(render_cmd)
    if render_rc != 0:
        raise SystemExit(render_rc)

    gate_rc = _run_command(gate_cmd)
    triage_rc = _run_command(triage_cmd)
    if triage_rc != 0:
        raise SystemExit(triage_rc)

    print(f"benchmark_json: {args.benchmark_json}")
    print(f"benchmark_markdown: {args.benchmark_markdown}")
    print(f"benchmark_html: {args.benchmark_html}")
    print(f"quality_gate_json: {args.quality_gate_json}")
    print(f"triage_json: {args.triage_json}")
    print(f"triage_markdown: {args.triage_markdown}")
    print(f"quality_gate_exit_code: {gate_rc}")

    _summarize_benchmark(args.benchmark_json, pairs=pairs)
    _summarize_triage(args.triage_json)

    if args.strict_gate and gate_rc != 0:
        raise SystemExit(gate_rc)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"error: {exc}") from exc
