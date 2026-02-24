#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class QualityFinding:
    level: str  # PASS | WARN | FAIL
    code: str
    message: str
    details: str | None = None


@dataclass(frozen=True)
class QualityReport:
    benchmark_json: str
    policy_json: str
    baseline_json: str | None
    dataset_json: str | None
    pos_probe_json: str | None
    pos_inventory_json: str | None
    findings: list[QualityFinding]

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_json": self.benchmark_json,
            "policy_json": self.policy_json,
            "baseline_json": self.baseline_json,
            "dataset_json": self.dataset_json,
            "pos_probe_json": self.pos_probe_json,
            "pos_inventory_json": self.pos_inventory_json,
            "findings": [asdict(item) for item in self.findings],
        }


def _read_json(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _as_float(value: object, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _metric_vector_key(run: Mapping[str, object]) -> tuple[float, float, float, float, float, float]:
    summary = run.get("summary")
    if not isinstance(summary, Mapping):
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return (
        _as_float(summary.get("objective_score")),
        _as_float(summary.get("top1_accuracy")),
        _as_float(summary.get("top3_recall")),
        _as_float(summary.get("forbidden_top1_rate")),
        _as_float(summary.get("forbidden_any_rate")),
        _as_float(summary.get("avg_rules_per_target")),
    )


def _pair_best_summary(
    benchmark_payload: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    pairs = benchmark_payload.get("pairs")
    if not isinstance(pairs, Mapping):
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for pair, pair_payload in pairs.items():
        if not isinstance(pair_payload, Mapping):
            continue
        best_run = pair_payload.get("best_run")
        if not isinstance(best_run, Mapping):
            continue
        summary = best_run.get("summary")
        if not isinstance(summary, Mapping):
            continue
        result[str(pair)] = summary
    return result


def _dataset_from_payload(
    benchmark_payload: Mapping[str, object],
    explicit_dataset: Path | None,
) -> Path | None:
    if explicit_dataset is not None:
        return explicit_dataset
    dataset_path = str(benchmark_payload.get("dataset_path") or "").strip()
    if not dataset_path:
        return None
    path = Path(dataset_path)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def _record(
    findings: list[QualityFinding],
    *,
    level: str,
    code: str,
    message: str,
    details: str | None = None,
) -> None:
    findings.append(QualityFinding(level=level, code=code, message=message, details=details))


def _validate_dataset_contract(
    *,
    dataset_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    contract = policy_payload.get("dataset_contract")
    if not isinstance(contract, Mapping):
        _record(
            findings,
            level="WARN",
            code="DATASET_CONTRACT_MISSING",
            message="Policy has no dataset_contract section; skipping dataset contract checks.",
        )
        return

    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence):
        _record(
            findings,
            level="FAIL",
            code="DATASET_CASES_MISSING",
            message="Dataset has no 'cases' array.",
        )
        return

    required_fields = contract.get("required_case_fields")
    required_case_fields = (
        [str(item) for item in required_fields if str(item).strip()]
        if isinstance(required_fields, Sequence)
        else []
    )
    allowed_tiers = contract.get("allowed_tiers")
    allowed_tier_values = (
        {str(item).strip() for item in allowed_tiers if str(item).strip()}
        if isinstance(allowed_tiers, Sequence)
        else set()
    )

    case_count_by_pair: Counter[str] = Counter()
    hard_count_by_pair: Counter[str] = Counter()

    missing_field_rows: list[str] = []
    bad_tier_rows: list[str] = []

    for index, case in enumerate(raw_cases):
        if not isinstance(case, Mapping):
            missing_field_rows.append(f"index={index}: case is not an object")
            continue
        pair = str(case.get("pair") or "").strip().lower()
        if pair:
            case_count_by_pair[pair] += 1
        for field in required_case_fields:
            value = case.get(field)
            if value is None:
                missing_field_rows.append(
                    f"index={index} case_id={case.get('case_id')} missing field '{field}'"
                )
                continue
            if isinstance(value, str) and not value.strip():
                missing_field_rows.append(
                    f"index={index} case_id={case.get('case_id')} has blank field '{field}'"
                )
        tier = str(case.get("tier") or "").strip()
        if allowed_tier_values and tier not in allowed_tier_values:
            bad_tier_rows.append(
                f"index={index} case_id={case.get('case_id')} has invalid tier '{tier}'"
            )
        if pair and tier == "hard":
            hard_count_by_pair[pair] += 1

    if missing_field_rows:
        _record(
            findings,
            level="FAIL",
            code="DATASET_REQUIRED_FIELDS",
            message="Dataset case fields are missing/blank.",
            details="\n".join(missing_field_rows[:20]),
        )
    else:
        _record(
            findings,
            level="PASS",
            code="DATASET_REQUIRED_FIELDS",
            message="Dataset required-case fields are present.",
        )

    if bad_tier_rows:
        _record(
            findings,
            level="FAIL",
            code="DATASET_TIER_VALUES",
            message="Dataset contains invalid case tiers.",
            details="\n".join(bad_tier_rows[:20]),
        )
    elif allowed_tier_values:
        _record(
            findings,
            level="PASS",
            code="DATASET_TIER_VALUES",
            message="Dataset case tiers use allowed values.",
        )

    min_cases_per_pair = contract.get("min_cases_per_pair")
    if isinstance(min_cases_per_pair, Mapping):
        deficits: list[str] = []
        for pair, minimum in min_cases_per_pair.items():
            pair_key = str(pair).strip().lower()
            required = _as_int(minimum)
            actual = int(case_count_by_pair.get(pair_key, 0))
            if actual < required:
                deficits.append(f"{pair_key}: required>={required}, actual={actual}")
        if deficits:
            _record(
                findings,
                level="FAIL",
                code="DATASET_MIN_CASES",
                message="Dataset pair case counts are below policy minimums.",
                details="\n".join(deficits),
            )
        else:
            _record(
                findings,
                level="PASS",
                code="DATASET_MIN_CASES",
                message="Dataset pair case counts meet policy minimums.",
            )

    min_hard_cases_per_pair = contract.get("min_hard_cases_per_pair")
    if isinstance(min_hard_cases_per_pair, Mapping):
        deficits: list[str] = []
        for pair, minimum in min_hard_cases_per_pair.items():
            pair_key = str(pair).strip().lower()
            required = _as_int(minimum)
            actual = int(hard_count_by_pair.get(pair_key, 0))
            if actual < required:
                deficits.append(f"{pair_key}: required_hard>={required}, actual={actual}")
        if deficits:
            _record(
                findings,
                level="FAIL",
                code="DATASET_MIN_HARD_CASES",
                message="Dataset hard-case counts are below policy minimums.",
                details="\n".join(deficits),
            )
        else:
            _record(
                findings,
                level="PASS",
                code="DATASET_MIN_HARD_CASES",
                message="Dataset hard-case counts meet policy minimums.",
            )


def _validate_benchmark_pairs(
    *,
    benchmark_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    pairs_payload = benchmark_payload.get("pairs")
    if not isinstance(pairs_payload, Mapping):
        _record(
            findings,
            level="FAIL",
            code="BENCHMARK_PAIRS_MISSING",
            message="Benchmark payload has no 'pairs' object.",
        )
        return

    available_pairs = {str(pair).strip().lower() for pair in pairs_payload.keys()}

    required = policy_payload.get("required_benchmark_pairs")
    required_pairs = (
        [str(item).strip().lower() for item in required if str(item).strip()]
        if isinstance(required, Sequence)
        else []
    )
    missing_required = [pair for pair in required_pairs if pair not in available_pairs]
    if missing_required:
        _record(
            findings,
            level="FAIL",
            code="BENCHMARK_REQUIRED_PAIRS_MISSING",
            message="Required benchmark pairs are missing from benchmark artifact.",
            details=", ".join(sorted(missing_required)),
        )
    else:
        _record(
            findings,
            level="PASS",
            code="BENCHMARK_REQUIRED_PAIRS_PRESENT",
            message="Required benchmark pairs are present in benchmark artifact.",
        )

    recommended = policy_payload.get("recommended_benchmark_pairs")
    recommended_pairs = (
        [str(item).strip().lower() for item in recommended if str(item).strip()]
        if isinstance(recommended, Sequence)
        else []
    )
    missing_recommended = [pair for pair in recommended_pairs if pair not in available_pairs]
    if missing_recommended:
        _record(
            findings,
            level="WARN",
            code="BENCHMARK_RECOMMENDED_PAIRS_MISSING",
            message="Recommended benchmark pairs are missing (not yet gated).",
            details=", ".join(sorted(missing_recommended)),
        )


def _validate_quality_floors(
    *,
    benchmark_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    floors = policy_payload.get("benchmark_quality_floors")
    if not isinstance(floors, Mapping):
        _record(
            findings,
            level="WARN",
            code="QUALITY_FLOORS_MISSING",
            message="Policy has no benchmark_quality_floors; skipping floor checks.",
        )
        return

    best_by_pair = _pair_best_summary(benchmark_payload)
    for pair, pair_floor in floors.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(pair_floor, Mapping):
            continue
        summary = best_by_pair.get(pair_key)
        if summary is None:
            _record(
                findings,
                level="WARN",
                code="QUALITY_FLOOR_PAIR_MISSING",
                message=f"No benchmark summary for pair '{pair_key}'; skipping its quality floor checks.",
            )
            continue

        checks: list[tuple[str, str, float, float]] = []
        checks.append(
            (
                "min_top1_accuracy",
                "top1_accuracy",
                _as_float(pair_floor.get("min_top1_accuracy"), default=0.0),
                _as_float(summary.get("top1_accuracy"), default=0.0),
            )
        )
        checks.append(
            (
                "min_top3_recall",
                "top3_recall",
                _as_float(pair_floor.get("min_top3_recall"), default=0.0),
                _as_float(summary.get("top3_recall"), default=0.0),
            )
        )

        max_forbidden_top1 = pair_floor.get("max_forbidden_top1_rate")
        max_forbidden_any = pair_floor.get("max_forbidden_any_rate")
        max_avg_rules = pair_floor.get("max_avg_rules_per_target")

        floor_failures: list[str] = []

        for floor_key, metric_key, threshold, actual in checks:
            if threshold > 0.0 and actual < threshold:
                floor_failures.append(
                    f"{metric_key}={actual:.4f} below {floor_key}={threshold:.4f}"
                )

        if max_forbidden_top1 is not None:
            actual = _as_float(summary.get("forbidden_top1_rate"), default=0.0)
            threshold = _as_float(max_forbidden_top1)
            if actual > threshold:
                floor_failures.append(
                    f"forbidden_top1_rate={actual:.4f} above max_forbidden_top1_rate={threshold:.4f}"
                )

        if max_forbidden_any is not None:
            actual = _as_float(summary.get("forbidden_any_rate"), default=0.0)
            threshold = _as_float(max_forbidden_any)
            if actual > threshold:
                floor_failures.append(
                    f"forbidden_any_rate={actual:.4f} above max_forbidden_any_rate={threshold:.4f}"
                )

        if max_avg_rules is not None:
            actual = _as_float(summary.get("avg_rules_per_target"), default=0.0)
            threshold = _as_float(max_avg_rules)
            if actual > threshold:
                floor_failures.append(
                    f"avg_rules_per_target={actual:.4f} above max_avg_rules_per_target={threshold:.4f}"
                )

        if floor_failures:
            _record(
                findings,
                level="FAIL",
                code="QUALITY_FLOOR_BREACH",
                message=f"Quality floor failed for pair '{pair_key}'.",
                details="\n".join(floor_failures),
            )
        else:
            _record(
                findings,
                level="PASS",
                code="QUALITY_FLOOR_OK",
                message=f"Quality floor satisfied for pair '{pair_key}'.",
            )


def _validate_delta_budgets(
    *,
    benchmark_payload: Mapping[str, object],
    baseline_payload: Mapping[str, object] | None,
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    if baseline_payload is None:
        _record(
            findings,
            level="WARN",
            code="DELTA_BASELINE_MISSING",
            message="No baseline payload provided; skipping delta budget checks.",
        )
        return

    baseline_best = baseline_payload.get("benchmark_best_by_pair")
    if not isinstance(baseline_best, Mapping):
        _record(
            findings,
            level="WARN",
            code="DELTA_BASELINE_EMPTY",
            message="Baseline payload has no benchmark_best_by_pair; skipping delta checks.",
        )
        return

    budgets = policy_payload.get("delta_budgets")
    if not isinstance(budgets, Mapping):
        _record(
            findings,
            level="WARN",
            code="DELTA_BUDGETS_MISSING",
            message="Policy has no delta_budgets; skipping delta checks.",
        )
        return

    best_by_pair = _pair_best_summary(benchmark_payload)

    budget_top1_drop = _as_float(budgets.get("max_top1_accuracy_drop"), default=0.0)
    budget_top3_drop = _as_float(budgets.get("max_top3_recall_drop"), default=0.0)
    budget_forbidden_top1_inc = _as_float(
        budgets.get("max_forbidden_top1_rate_increase"),
        default=0.0,
    )
    budget_forbidden_any_inc = _as_float(
        budgets.get("max_forbidden_any_rate_increase"),
        default=0.0,
    )
    budget_avg_rules_inc = _as_float(
        budgets.get("max_avg_rules_per_target_increase"),
        default=0.0,
    )

    any_checked = False
    for pair, baseline_summary in baseline_best.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(baseline_summary, Mapping):
            continue
        current_summary = best_by_pair.get(pair_key)
        if current_summary is None:
            _record(
                findings,
                level="WARN",
                code="DELTA_PAIR_MISSING",
                message=f"Pair '{pair_key}' exists in baseline but not current benchmark.",
            )
            continue

        any_checked = True

        base_top1 = _as_float(baseline_summary.get("top1_accuracy"), default=0.0)
        base_top3 = _as_float(baseline_summary.get("top3_recall"), default=0.0)
        base_forbidden_top1 = _as_float(baseline_summary.get("forbidden_top1_rate"), default=0.0)
        base_forbidden_any = _as_float(baseline_summary.get("forbidden_any_rate"), default=0.0)
        base_avg_rules = _as_float(baseline_summary.get("avg_rules_per_target"), default=0.0)

        cur_top1 = _as_float(current_summary.get("top1_accuracy"), default=0.0)
        cur_top3 = _as_float(current_summary.get("top3_recall"), default=0.0)
        cur_forbidden_top1 = _as_float(current_summary.get("forbidden_top1_rate"), default=0.0)
        cur_forbidden_any = _as_float(current_summary.get("forbidden_any_rate"), default=0.0)
        cur_avg_rules = _as_float(current_summary.get("avg_rules_per_target"), default=0.0)

        failures: list[str] = []

        top1_drop = max(0.0, base_top1 - cur_top1)
        if top1_drop > budget_top1_drop:
            failures.append(
                f"top1_accuracy drop={top1_drop:.4f} exceeds budget={budget_top1_drop:.4f}"
            )

        top3_drop = max(0.0, base_top3 - cur_top3)
        if top3_drop > budget_top3_drop:
            failures.append(
                f"top3_recall drop={top3_drop:.4f} exceeds budget={budget_top3_drop:.4f}"
            )

        forbidden_top1_inc = max(0.0, cur_forbidden_top1 - base_forbidden_top1)
        if forbidden_top1_inc > budget_forbidden_top1_inc:
            failures.append(
                "forbidden_top1_rate increase="
                f"{forbidden_top1_inc:.4f} exceeds budget={budget_forbidden_top1_inc:.4f}"
            )

        forbidden_any_inc = max(0.0, cur_forbidden_any - base_forbidden_any)
        if forbidden_any_inc > budget_forbidden_any_inc:
            failures.append(
                f"forbidden_any_rate increase={forbidden_any_inc:.4f} exceeds budget={budget_forbidden_any_inc:.4f}"
            )

        avg_rules_inc = max(0.0, cur_avg_rules - base_avg_rules)
        if avg_rules_inc > budget_avg_rules_inc:
            failures.append(
                f"avg_rules_per_target increase={avg_rules_inc:.4f} exceeds budget={budget_avg_rules_inc:.4f}"
            )

        if failures:
            _record(
                findings,
                level="FAIL",
                code="DELTA_BUDGET_BREACH",
                message=f"Delta budgets failed for pair '{pair_key}'.",
                details="\n".join(failures),
            )
        else:
            _record(
                findings,
                level="PASS",
                code="DELTA_BUDGET_OK",
                message=f"Delta budgets satisfied for pair '{pair_key}'.",
            )

    if not any_checked:
        _record(
            findings,
            level="WARN",
            code="DELTA_NO_PAIRS_CHECKED",
            message="No overlapping pairs between baseline and current benchmark for delta checks.",
        )


def _validate_saturation(
    *,
    benchmark_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
    strict_saturation: bool,
) -> None:
    saturation = policy_payload.get("saturation")
    if not isinstance(saturation, Mapping):
        _record(
            findings,
            level="WARN",
            code="SATURATION_POLICY_MISSING",
            message="Policy has no saturation section; skipping saturation checks.",
        )
        return

    warn_share = _as_float(saturation.get("warn_if_top_metric_vector_share_gte"), default=1.1)
    fail_share = _as_float(saturation.get("fail_if_top_metric_vector_share_gt"), default=2.0)
    warn_unique_lt = _as_int(saturation.get("warn_if_unique_metric_vectors_lt"), default=0)

    pairs_payload = benchmark_payload.get("pairs")
    if not isinstance(pairs_payload, Mapping):
        return

    for pair, pair_payload in pairs_payload.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(pair_payload, Mapping):
            continue
        runs = pair_payload.get("runs")
        if not isinstance(runs, Sequence) or not runs:
            _record(
                findings,
                level="WARN",
                code="SATURATION_NO_RUNS",
                message=f"Pair '{pair_key}' has no runs for saturation analysis.",
            )
            continue

        metric_counts: Counter[tuple[float, float, float, float, float, float]] = Counter()
        for run in runs:
            if not isinstance(run, Mapping):
                continue
            metric_counts[_metric_vector_key(run)] += 1

        run_count = max(1, len(runs))
        top_count = max(metric_counts.values()) if metric_counts else 0
        top_share = float(top_count) / float(run_count)
        unique_vectors = len(metric_counts)

        if top_share > fail_share:
            _record(
                findings,
                level="FAIL",
                code="SATURATION_TOP_VECTOR_FAIL",
                message=(
                    f"Pair '{pair_key}' top metric vector share={top_share:.3f} exceeds "
                    f"fail threshold>{fail_share:.3f}."
                ),
                details=f"run_count={run_count} unique_vectors={unique_vectors} top_count={top_count}",
            )
        elif top_share >= warn_share:
            _record(
                findings,
                level=("FAIL" if strict_saturation else "WARN"),
                code="SATURATION_TOP_VECTOR_WARN",
                message=(
                    f"Pair '{pair_key}' top metric vector share={top_share:.3f} indicates low sensitivity "
                    f"(warn threshold>={warn_share:.3f})."
                ),
                details=f"run_count={run_count} unique_vectors={unique_vectors} top_count={top_count}",
            )
        else:
            _record(
                findings,
                level="PASS",
                code="SATURATION_TOP_VECTOR_OK",
                message=f"Pair '{pair_key}' top metric vector share={top_share:.3f} is below warning threshold.",
                details=f"run_count={run_count} unique_vectors={unique_vectors} top_count={top_count}",
            )

        if warn_unique_lt > 0 and unique_vectors < warn_unique_lt:
            _record(
                findings,
                level=("FAIL" if strict_saturation else "WARN"),
                code="SATURATION_UNIQUE_VECTOR_WARN",
                message=(
                    f"Pair '{pair_key}' unique metric vectors={unique_vectors} below expected "
                    f"minimum={warn_unique_lt}."
                ),
            )


def _validate_pos_guardrails(
    *,
    pos_probe_payload: Mapping[str, object] | None,
    pos_inventory_payload: Mapping[str, object] | None,
    baseline_payload: Mapping[str, object] | None,
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    guardrails = policy_payload.get("pos_guardrails")
    if not isinstance(guardrails, Mapping):
        _record(
            findings,
            level="WARN",
            code="POS_GUARDRAILS_MISSING",
            message="Policy has no pos_guardrails section; skipping POS checks.",
        )
        return

    baseline_mismatch = (
        baseline_payload.get("pos_pair_mismatch_rate")
        if isinstance(baseline_payload, Mapping)
        else None
    )
    baseline_mismatch_by_pair = baseline_mismatch if isinstance(baseline_mismatch, Mapping) else {}
    baseline_unknown = (
        baseline_payload.get("pos_unknown_counts")
        if isinstance(baseline_payload, Mapping)
        else None
    )
    baseline_unknown_by_pack = baseline_unknown if isinstance(baseline_unknown, Mapping) else {}

    if pos_probe_payload is None:
        _record(
            findings,
            level="WARN",
            code="POS_PROBE_MISSING",
            message="No POS probe payload provided; skipping mismatch-rate checks.",
        )
    else:
        pair_reports = pos_probe_payload.get("pair_reports")
        pair_reports_map = pair_reports if isinstance(pair_reports, Mapping) else {}
        max_by_pair = guardrails.get("max_bucket_mismatch_rate_by_pair")
        max_mismatch = max_by_pair if isinstance(max_by_pair, Mapping) else {}
        increase_budget = _as_float(
            guardrails.get("max_bucket_mismatch_rate_increase"),
            default=0.0,
        )

        for pair, threshold_value in max_mismatch.items():
            pair_key = str(pair).strip().lower()
            threshold = _as_float(threshold_value)
            report = pair_reports_map.get(pair_key)
            if not isinstance(report, Mapping):
                _record(
                    findings,
                    level="FAIL",
                    code="POS_PAIR_REPORT_MISSING",
                    message=f"POS probe has no pair report for '{pair_key}'.",
                )
                continue
            current_rate = _as_float(report.get("bucket_mismatch_rate"), default=1.0)
            if current_rate > threshold:
                _record(
                    findings,
                    level="FAIL",
                    code="POS_MISMATCH_RATE_BREACH",
                    message=(
                        f"Pair '{pair_key}' bucket_mismatch_rate={current_rate:.4f} exceeds "
                        f"threshold={threshold:.4f}."
                    ),
                )
            else:
                _record(
                    findings,
                    level="PASS",
                    code="POS_MISMATCH_RATE_OK",
                    message=(
                        f"Pair '{pair_key}' bucket_mismatch_rate={current_rate:.4f} "
                        f"within threshold={threshold:.4f}."
                    ),
                )

            baseline_rate = _as_float(baseline_mismatch_by_pair.get(pair_key), default=current_rate)
            increase = max(0.0, current_rate - baseline_rate)
            if increase > increase_budget:
                _record(
                    findings,
                    level="FAIL",
                    code="POS_MISMATCH_RATE_DELTA_BREACH",
                    message=(
                        f"Pair '{pair_key}' mismatch-rate increase={increase:.4f} exceeds "
                        f"budget={increase_budget:.4f}."
                    ),
                    details=f"baseline={baseline_rate:.4f} current={current_rate:.4f}",
                )

    if pos_inventory_payload is None:
        _record(
            findings,
            level="WARN",
            code="POS_INVENTORY_MISSING",
            message="No POS inventory payload provided; skipping unknown-tag growth checks.",
        )
        return

    rows = pos_inventory_payload.get("rows")
    if not isinstance(rows, Sequence):
        _record(
            findings,
            level="FAIL",
            code="POS_INVENTORY_ROWS_MISSING",
            message="POS inventory payload has no rows array.",
        )
        return

    current_unknown_by_pack: dict[str, int | None] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        filename = str(row.get("filename") or "").strip()
        if not filename:
            continue
        raw_unknown = row.get("unknown_pos_inventory_size")
        current_unknown_by_pack[filename] = _as_int(raw_unknown) if raw_unknown is not None else None

    default_budget = _as_int(guardrails.get("default_unknown_pos_growth_budget"), default=0)
    budget_by_pack_payload = guardrails.get("unknown_pos_growth_budget_by_pack")
    budget_by_pack = budget_by_pack_payload if isinstance(budget_by_pack_payload, Mapping) else {}
    allow_missing_payload = guardrails.get("allow_missing_packs")
    allow_missing = (
        {str(item).strip() for item in allow_missing_payload if str(item).strip()}
        if isinstance(allow_missing_payload, Sequence)
        else set()
    )

    for filename, baseline_value in baseline_unknown_by_pack.items():
        pack = str(filename).strip()
        if not pack:
            continue
        if baseline_value is None:
            continue

        if pack not in current_unknown_by_pack:
            if pack in allow_missing:
                _record(
                    findings,
                    level="WARN",
                    code="POS_UNKNOWN_PACK_MISSING_ALLOWED",
                    message=f"Pack '{pack}' missing in current inventory but listed as allowed missing.",
                )
                continue
            _record(
                findings,
                level="FAIL",
                code="POS_UNKNOWN_PACK_MISSING",
                message=f"Pack '{pack}' is missing in current POS inventory payload.",
            )
            continue

        current_value = current_unknown_by_pack.get(pack)
        if current_value is None:
            if pack in allow_missing:
                _record(
                    findings,
                    level="WARN",
                    code="POS_UNKNOWN_COUNT_NULL_ALLOWED",
                    message=f"Pack '{pack}' unknown tag count is null and is allowed missing.",
                )
                continue
            _record(
                findings,
                level="FAIL",
                code="POS_UNKNOWN_COUNT_NULL",
                message=f"Pack '{pack}' unknown tag count is null.",
            )
            continue

        base_count = _as_int(baseline_value)
        budget = _as_int(budget_by_pack.get(pack), default=default_budget)
        allowed_max = base_count + budget
        if current_value > allowed_max:
            _record(
                findings,
                level="FAIL",
                code="POS_UNKNOWN_GROWTH_BREACH",
                message=(
                    f"Pack '{pack}' unknown_pos_inventory_size={current_value} exceeds "
                    f"allowed_max={allowed_max} (baseline={base_count}, budget={budget})."
                ),
            )
        else:
            _record(
                findings,
                level="PASS",
                code="POS_UNKNOWN_GROWTH_OK",
                message=(
                    f"Pack '{pack}' unknown_pos_inventory_size={current_value} within "
                    f"allowed_max={allowed_max} (baseline={base_count}, budget={budget})."
                ),
            )


def _print_findings(findings: Sequence[QualityFinding]) -> None:
    for finding in findings:
        print(f"[{finding.level}] {finding.code}: {finding.message}")
        if finding.details:
            for line in str(finding.details).splitlines():
                print(f"  {line}")


def main() -> None:
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
        default=PROJECT_ROOT / "docs" / "test_outputs" / "baselines" / "rulegen_quality_baseline.json",
        help="Baseline metrics JSON used for delta-budget checks.",
    )
    parser.add_argument(
        "--dataset-json",
        type=Path,
        help="Optional benchmark dataset JSON override (defaults to benchmark dataset_path).",
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
    args = parser.parse_args()

    findings: list[QualityFinding] = []

    benchmark_payload: Mapping[str, object] | None = None
    policy_payload: Mapping[str, object] | None = None
    baseline_payload: Mapping[str, object] | None = None
    dataset_payload: Mapping[str, object] | None = None
    pos_probe_payload: Mapping[str, object] | None = None
    pos_inventory_payload: Mapping[str, object] | None = None

    try:
        benchmark_payload = _read_json(args.benchmark_json)
    except Exception as exc:  # noqa: BLE001
        _record(
            findings,
            level="FAIL",
            code="BENCHMARK_LOAD_ERROR",
            message=f"Failed to load benchmark JSON: {args.benchmark_json}",
            details=str(exc),
        )

    try:
        policy_payload = _read_json(args.policy_json)
    except Exception as exc:  # noqa: BLE001
        _record(
            findings,
            level="FAIL",
            code="POLICY_LOAD_ERROR",
            message=f"Failed to load policy JSON: {args.policy_json}",
            details=str(exc),
        )

    if args.baseline_json.exists():
        try:
            baseline_payload = _read_json(args.baseline_json)
        except Exception as exc:  # noqa: BLE001
            _record(
                findings,
                level="FAIL",
                code="BASELINE_LOAD_ERROR",
                message=f"Failed to load baseline JSON: {args.baseline_json}",
                details=str(exc),
            )
    else:
        _record(
            findings,
            level="WARN",
            code="BASELINE_NOT_FOUND",
            message=f"Baseline file does not exist: {args.baseline_json}",
        )

    if args.pos_probe_json.exists():
        try:
            pos_probe_payload = _read_json(args.pos_probe_json)
        except Exception as exc:  # noqa: BLE001
            _record(
                findings,
                level="FAIL",
                code="POS_PROBE_LOAD_ERROR",
                message=f"Failed to load POS probe JSON: {args.pos_probe_json}",
                details=str(exc),
            )
    else:
        _record(
            findings,
            level="WARN",
            code="POS_PROBE_NOT_FOUND",
            message=f"POS probe artifact not found: {args.pos_probe_json}",
        )

    if args.pos_inventory_json.exists():
        try:
            pos_inventory_payload = _read_json(args.pos_inventory_json)
        except Exception as exc:  # noqa: BLE001
            _record(
                findings,
                level="FAIL",
                code="POS_INVENTORY_LOAD_ERROR",
                message=f"Failed to load POS inventory JSON: {args.pos_inventory_json}",
                details=str(exc),
            )
    else:
        _record(
            findings,
            level="WARN",
            code="POS_INVENTORY_NOT_FOUND",
            message=f"POS inventory artifact not found: {args.pos_inventory_json}",
        )

    if benchmark_payload is not None:
        dataset_path = _dataset_from_payload(benchmark_payload, args.dataset_json)
        if dataset_path is None:
            _record(
                findings,
                level="FAIL",
                code="DATASET_PATH_UNRESOLVED",
                message="Could not resolve dataset JSON path from args or benchmark payload.",
            )
        elif dataset_path.exists():
            try:
                dataset_payload = _read_json(dataset_path)
            except Exception as exc:  # noqa: BLE001
                _record(
                    findings,
                    level="FAIL",
                    code="DATASET_LOAD_ERROR",
                    message=f"Failed to load dataset JSON: {dataset_path}",
                    details=str(exc),
                )
        else:
            _record(
                findings,
                level="FAIL",
                code="DATASET_NOT_FOUND",
                message=f"Dataset path does not exist: {dataset_path}",
            )

    if benchmark_payload is not None and policy_payload is not None:
        _validate_benchmark_pairs(
            benchmark_payload=benchmark_payload,
            policy_payload=policy_payload,
            findings=findings,
        )
        _validate_quality_floors(
            benchmark_payload=benchmark_payload,
            policy_payload=policy_payload,
            findings=findings,
        )
        _validate_delta_budgets(
            benchmark_payload=benchmark_payload,
            baseline_payload=baseline_payload,
            policy_payload=policy_payload,
            findings=findings,
        )
        _validate_saturation(
            benchmark_payload=benchmark_payload,
            policy_payload=policy_payload,
            findings=findings,
            strict_saturation=bool(args.strict_saturation),
        )

    if dataset_payload is not None and policy_payload is not None:
        _validate_dataset_contract(
            dataset_payload=dataset_payload,
            policy_payload=policy_payload,
            findings=findings,
        )

    if policy_payload is not None:
        _validate_pos_guardrails(
            pos_probe_payload=pos_probe_payload,
            pos_inventory_payload=pos_inventory_payload,
            baseline_payload=baseline_payload,
            policy_payload=policy_payload,
            findings=findings,
        )

    _print_findings(findings)

    fail_count = sum(1 for item in findings if item.level == "FAIL")
    warn_count = sum(1 for item in findings if item.level == "WARN")
    pass_count = sum(1 for item in findings if item.level == "PASS")
    print(f"summary: pass={pass_count} warn={warn_count} fail={fail_count}")

    report = QualityReport(
        benchmark_json=str(args.benchmark_json),
        policy_json=str(args.policy_json),
        baseline_json=str(args.baseline_json) if args.baseline_json else None,
        dataset_json=str(args.dataset_json) if args.dataset_json else None,
        pos_probe_json=str(args.pos_probe_json) if args.pos_probe_json else None,
        pos_inventory_json=str(args.pos_inventory_json) if args.pos_inventory_json else None,
        findings=findings,
    )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    should_fail = fail_count > 0 or (bool(args.fail_on_warn) and warn_count > 0)
    raise SystemExit(1 if should_fail else 0)


if __name__ == "__main__":
    main()
