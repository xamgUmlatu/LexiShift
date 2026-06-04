#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

try:
    from .rulegen_benchmark_dataset import load_benchmark_dataset_payload
    from .rulegen_quality_gate_support import (
        QualityFinding,
        QualityReport,
        dataset_from_payload,
        print_findings,
        read_json,
        record,
        summarize_findings,
        validate_benchmark_pairs,
        validate_dataset_contract,
        validate_delta_budgets,
        validate_pos_guardrails,
        validate_quality_floors,
        validate_saturation,
    )
except Exception:  # noqa: BLE001
    from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # type: ignore[no-redef]
    from rulegen_quality_gate_support import (  # type: ignore[no-redef]
        QualityFinding,
        QualityReport,
        dataset_from_payload,
        print_findings,
        read_json,
        record,
        summarize_findings,
        validate_benchmark_pairs,
        validate_dataset_contract,
        validate_delta_budgets,
        validate_pos_guardrails,
        validate_quality_floors,
        validate_saturation,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate benchmark + POS artifacts against policy and baseline budgets to stabilize "
            "rulegen iteration quality."
        )
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_latest.json",
        help="Benchmark report JSON output from scripts/testing/rulegen_benchmark.py",
    )
    parser.add_argument(
        "--policy-json",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_quality_policy.json",
        help="Quality policy JSON with floors, budgets, and guardrails.",
    )
    parser.add_argument(
        "--baseline-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "baselines"
        / "rulegen_quality_baseline.json",
        help="Baseline metrics JSON used for delta-budget checks.",
    )
    parser.add_argument(
        "--dataset-json",
        type=Path,
        help=(
            "Optional benchmark dataset file or directory override "
            "(defaults to benchmark dataset_path)."
        ),
    )
    parser.add_argument(
        "--pair-scope",
        help=(
            "Optional pair key to scope pair-level checks to a single benchmark lane. "
            "Useful for advisory per-pair latest artifacts such as en-de."
        ),
    )
    parser.add_argument(
        "--pos-probe-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "phase6_pos_inventory"
        / "phase6_pos_probe_2026-02-23_final.json",
        help="POS probe JSON artifact for mismatch-rate checks.",
    )
    parser.add_argument(
        "--pos-inventory-json",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "phase6_pos_inventory"
        / "phase6_pos_inventory_2026-02-23_final.json",
        help="POS inventory JSON artifact for unknown-tag growth checks.",
    )
    parser.add_argument(
        "--strict-saturation",
        action="store_true",
        help="Treat saturation warnings as failures.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Return non-zero if any WARN findings are present.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to write machine-readable gate report JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pair_scope = str(args.pair_scope or "").strip().lower() or None
    findings: list[QualityFinding] = []

    benchmark_payload: Mapping[str, object] | None = None
    policy_payload: Mapping[str, object] | None = None
    baseline_payload: Mapping[str, object] | None = None
    dataset_payload: Mapping[str, object] | None = None
    pos_probe_payload: Mapping[str, object] | None = None
    pos_inventory_payload: Mapping[str, object] | None = None

    try:
        benchmark_payload = read_json(args.benchmark_json)
    except Exception as exc:  # noqa: BLE001
        record(
            findings,
            level="FAIL",
            code="BENCHMARK_LOAD_ERROR",
            message=f"Failed to load benchmark JSON: {args.benchmark_json}",
            details=str(exc),
        )

    try:
        policy_payload = read_json(args.policy_json)
    except Exception as exc:  # noqa: BLE001
        record(
            findings,
            level="FAIL",
            code="POLICY_LOAD_ERROR",
            message=f"Failed to load policy JSON: {args.policy_json}",
            details=str(exc),
        )

    if args.baseline_json.exists():
        try:
            baseline_payload = read_json(args.baseline_json)
        except Exception as exc:  # noqa: BLE001
            record(
                findings,
                level="FAIL",
                code="BASELINE_LOAD_ERROR",
                message=f"Failed to load baseline JSON: {args.baseline_json}",
                details=str(exc),
            )
    else:
        record(
            findings,
            level="WARN",
            code="BASELINE_NOT_FOUND",
            message=f"Baseline file does not exist: {args.baseline_json}",
        )

    if args.pos_probe_json.exists():
        try:
            pos_probe_payload = read_json(args.pos_probe_json)
        except Exception as exc:  # noqa: BLE001
            record(
                findings,
                level="FAIL",
                code="POS_PROBE_LOAD_ERROR",
                message=f"Failed to load POS probe JSON: {args.pos_probe_json}",
                details=str(exc),
            )
    else:
        record(
            findings,
            level="WARN",
            code="POS_PROBE_NOT_FOUND",
            message=f"POS probe artifact not found: {args.pos_probe_json}",
        )

    if args.pos_inventory_json.exists():
        try:
            pos_inventory_payload = read_json(args.pos_inventory_json)
        except Exception as exc:  # noqa: BLE001
            record(
                findings,
                level="FAIL",
                code="POS_INVENTORY_LOAD_ERROR",
                message=f"Failed to load POS inventory JSON: {args.pos_inventory_json}",
                details=str(exc),
            )
    else:
        record(
            findings,
            level="WARN",
            code="POS_INVENTORY_NOT_FOUND",
            message=f"POS inventory artifact not found: {args.pos_inventory_json}",
        )

    if benchmark_payload is not None:
        dataset_path = dataset_from_payload(
            benchmark_payload,
            args.dataset_json,
            project_root=PROJECT_ROOT,
        )
        if dataset_path is None:
            record(
                findings,
                level="FAIL",
                code="DATASET_PATH_UNRESOLVED",
                message="Could not resolve dataset JSON path from args or benchmark payload.",
            )
        elif dataset_path.exists():
            try:
                dataset_payload = load_benchmark_dataset_payload(dataset_path)
            except Exception as exc:  # noqa: BLE001
                record(
                    findings,
                    level="FAIL",
                    code="DATASET_LOAD_ERROR",
                    message=f"Failed to load dataset JSON: {dataset_path}",
                    details=str(exc),
                )
        else:
            record(
                findings,
                level="FAIL",
                code="DATASET_NOT_FOUND",
                message=f"Dataset path does not exist: {dataset_path}",
            )

    if benchmark_payload is not None and policy_payload is not None:
        validate_benchmark_pairs(
            benchmark_payload=benchmark_payload,
            policy_payload=policy_payload,
            findings=findings,
            pair_scope=pair_scope,
        )
        validate_quality_floors(
            benchmark_payload=benchmark_payload,
            policy_payload=policy_payload,
            findings=findings,
            pair_scope=pair_scope,
        )
        validate_delta_budgets(
            benchmark_payload=benchmark_payload,
            baseline_payload=baseline_payload,
            policy_payload=policy_payload,
            findings=findings,
            pair_scope=pair_scope,
        )
        validate_saturation(
            benchmark_payload=benchmark_payload,
            policy_payload=policy_payload,
            findings=findings,
            strict_saturation=bool(args.strict_saturation),
        )

    if dataset_payload is not None and policy_payload is not None:
        validate_dataset_contract(
            dataset_payload=dataset_payload,
            policy_payload=policy_payload,
            findings=findings,
            pair_scope=pair_scope,
        )

    if policy_payload is not None:
        validate_pos_guardrails(
            pos_probe_payload=pos_probe_payload,
            pos_inventory_payload=pos_inventory_payload,
            baseline_payload=baseline_payload,
            policy_payload=policy_payload,
            findings=findings,
        )

    print_findings(findings)

    summary = summarize_findings(findings, fail_on_warn=bool(args.fail_on_warn))
    fail_count = int(summary["fail_count"])
    warn_count = int(summary["warn_count"])
    pass_count = int(summary["pass_count"])
    print(f"summary: pass={pass_count} warn={warn_count} fail={fail_count}")

    report = QualityReport(
        benchmark_json=str(args.benchmark_json),
        policy_json=str(args.policy_json),
        baseline_json=str(args.baseline_json) if args.baseline_json else None,
        dataset_json=str(args.dataset_json) if args.dataset_json else None,
        pair_scope=str(args.pair_scope).strip().lower() or None,
        pos_probe_json=str(args.pos_probe_json) if args.pos_probe_json else None,
        pos_inventory_json=str(args.pos_inventory_json) if args.pos_inventory_json else None,
        strict_saturation=bool(args.strict_saturation),
        fail_on_warn=bool(args.fail_on_warn),
        summary=summary,
        findings=findings,
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    should_fail = bool(summary["should_fail"])
    raise SystemExit(1 if should_fail else 0)


if __name__ == "__main__":
    main()
