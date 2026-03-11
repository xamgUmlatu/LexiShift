#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys


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
        default="false",
    )
    parser.add_argument(
        "--reverse-check-match-bonus-values",
        default="0.2",
    )
    parser.add_argument(
        "--reverse-check-near-bonus-values",
        default="0.1",
    )
    parser.add_argument(
        "--reverse-check-near-rank-max-values",
        default="2",
    )
    parser.add_argument(
        "--reverse-check-miss-penalty-values",
        default="0.2",
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

    pairs = [item.strip().lower() for item in str(args.pairs).split(",") if item.strip()]
    if not pairs:
        raise ValueError("No pairs provided.")

    benchmark_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_benchmark.py"),
        "--pairs",
        ",".join(pairs),
        "--max-definitions-values",
        str(args.max_definitions_values),
        "--max-rules-values",
        str(args.max_rules_values),
        "--confidence-threshold-values",
        str(args.confidence_threshold_values),
        "--semantic-demotion-scale-values",
        str(args.semantic_demotion_scale_values),
        "--include-variants-values",
        str(args.include_variants_values),
        "--pos-scoring-values",
        str(args.pos_scoring_values),
        "--score-weight-pos-values",
        str(args.score_weight_pos_values),
        "--reverse-check-enabled-values",
        str(args.reverse_check_enabled_values),
        "--reverse-check-match-bonus-values",
        str(args.reverse_check_match_bonus_values),
        "--reverse-check-near-bonus-values",
        str(args.reverse_check_near_bonus_values),
        "--reverse-check-near-rank-max-values",
        str(args.reverse_check_near_rank_max_values),
        "--reverse-check-miss-penalty-values",
        str(args.reverse_check_miss_penalty_values),
        "--max-configurations",
        str(int(args.max_configurations)),
        "--top-runs",
        str(int(args.top_runs)),
        "--json-output",
        str(args.benchmark_json),
        "--markdown-output",
        str(args.benchmark_markdown),
        "--html-output",
        str(args.benchmark_html),
    ]

    gate_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_quality_gate.py"),
        "--benchmark-json",
        str(args.benchmark_json),
        "--policy-json",
        str(args.policy_json),
        "--baseline-json",
        str(args.baseline_json),
        "--pos-probe-json",
        str(args.pos_probe_json),
        "--pos-inventory-json",
        str(args.pos_inventory_json),
        "--json-out",
        str(args.quality_gate_json),
    ]

    triage_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_benchmark_triage.py"),
        "--benchmark-json",
        str(args.benchmark_json),
        "--json-out",
        str(args.triage_json),
        "--markdown-out",
        str(args.triage_markdown),
    ]

    benchmark_rc = _run_command(benchmark_cmd)
    if benchmark_rc != 0:
        raise SystemExit(benchmark_rc)

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
