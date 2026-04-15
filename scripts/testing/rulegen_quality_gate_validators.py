from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

try:
    from .rulegen_quality_gate_core import (
        QualityFinding,
        as_float,
        as_int,
        metric_vector_key,
        pair_best_summary,
        record,
    )
except Exception:  # noqa: BLE001
    from rulegen_quality_gate_core import (  # type: ignore[no-redef]
        QualityFinding,
        as_float,
        as_int,
        metric_vector_key,
        pair_best_summary,
        record,
    )


def validate_dataset_contract(
    *,
    dataset_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
    benchmark_pairs: set[str] | None = None,
) -> None:
    contract = policy_payload.get("dataset_contract")
    if not isinstance(contract, Mapping):
        record(
            findings,
            level="WARN",
            code="DATASET_CONTRACT_MISSING",
            message="Policy has no dataset_contract section; skipping dataset contract checks.",
        )
        return

    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence):
        record(
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
        record(
            findings,
            level="FAIL",
            code="DATASET_REQUIRED_FIELDS",
            message="Dataset case fields are missing/blank.",
            details="\n".join(missing_field_rows[:20]),
        )
    else:
        record(
            findings,
            level="PASS",
            code="DATASET_REQUIRED_FIELDS",
            message="Dataset required-case fields are present.",
        )

    if bad_tier_rows:
        record(
            findings,
            level="FAIL",
            code="DATASET_TIER_VALUES",
            message="Dataset contains invalid case tiers.",
            details="\n".join(bad_tier_rows[:20]),
        )
    elif allowed_tier_values:
        record(
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
            if benchmark_pairs and pair_key not in benchmark_pairs:
                continue
            required = as_int(minimum)
            actual = int(case_count_by_pair.get(pair_key, 0))
            if actual < required:
                deficits.append(f"{pair_key}: required>={required}, actual={actual}")
        if deficits:
            record(
                findings,
                level="FAIL",
                code="DATASET_MIN_CASES",
                message="Dataset pair case counts are below policy minimums.",
                details="\n".join(deficits),
            )
        else:
            record(
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
            if benchmark_pairs and pair_key not in benchmark_pairs:
                continue
            required = as_int(minimum)
            actual = int(hard_count_by_pair.get(pair_key, 0))
            if actual < required:
                deficits.append(f"{pair_key}: required_hard>={required}, actual={actual}")
        if deficits:
            record(
                findings,
                level="FAIL",
                code="DATASET_MIN_HARD_CASES",
                message="Dataset hard-case counts are below policy minimums.",
                details="\n".join(deficits),
            )
        else:
            record(
                findings,
                level="PASS",
                code="DATASET_MIN_HARD_CASES",
                message="Dataset hard-case counts meet policy minimums.",
            )


def validate_benchmark_pairs(
    *,
    benchmark_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
    advisory_required_pairs: bool = False,
) -> None:
    pairs_payload = benchmark_payload.get("pairs")
    if not isinstance(pairs_payload, Mapping):
        record(
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
        record(
            findings,
            level=("WARN" if advisory_required_pairs else "FAIL"),
            code="BENCHMARK_REQUIRED_PAIRS_MISSING",
            message=(
                "Required benchmark pairs are missing from benchmark artifact."
                if not advisory_required_pairs
                else "Required benchmark pairs are missing from benchmark artifact (advisory mode)."
            ),
            details=", ".join(sorted(missing_required)),
        )
    else:
        record(
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
        record(
            findings,
            level="WARN",
            code="BENCHMARK_RECOMMENDED_PAIRS_MISSING",
            message="Recommended benchmark pairs are missing (not yet gated).",
            details=", ".join(sorted(missing_recommended)),
        )


def validate_quality_floors(
    *,
    benchmark_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    floors = policy_payload.get("benchmark_quality_floors")
    if not isinstance(floors, Mapping):
        record(
            findings,
            level="WARN",
            code="QUALITY_FLOORS_MISSING",
            message="Policy has no benchmark_quality_floors; skipping floor checks.",
        )
        return

    best_by_pair = pair_best_summary(benchmark_payload)
    for pair, pair_floor in floors.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(pair_floor, Mapping):
            continue
        summary = best_by_pair.get(pair_key)
        if summary is None:
            record(
                findings,
                level="WARN",
                code="QUALITY_FLOOR_PAIR_MISSING",
                message=f"No benchmark summary for pair '{pair_key}'; skipping its quality floor checks.",
            )
            continue

        checks: list[tuple[str, str, float, float]] = [
            (
                "min_top1_accuracy",
                "top1_accuracy",
                as_float(pair_floor.get("min_top1_accuracy"), default=0.0),
                as_float(summary.get("top1_accuracy"), default=0.0),
            ),
            (
                "min_top3_recall",
                "top3_recall",
                as_float(pair_floor.get("min_top3_recall"), default=0.0),
                as_float(summary.get("top3_recall"), default=0.0),
            ),
        ]
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
            actual = as_float(summary.get("forbidden_top1_rate"), default=0.0)
            threshold = as_float(max_forbidden_top1)
            if actual > threshold:
                floor_failures.append(
                    f"forbidden_top1_rate={actual:.4f} above max_forbidden_top1_rate={threshold:.4f}"
                )
        if max_forbidden_any is not None:
            actual = as_float(summary.get("forbidden_any_rate"), default=0.0)
            threshold = as_float(max_forbidden_any)
            if actual > threshold:
                floor_failures.append(
                    f"forbidden_any_rate={actual:.4f} above max_forbidden_any_rate={threshold:.4f}"
                )
        if max_avg_rules is not None:
            actual = as_float(summary.get("avg_rules_per_target"), default=0.0)
            threshold = as_float(max_avg_rules)
            if actual > threshold:
                floor_failures.append(
                    f"avg_rules_per_target={actual:.4f} above max_avg_rules_per_target={threshold:.4f}"
                )

        if floor_failures:
            record(
                findings,
                level="FAIL",
                code="QUALITY_FLOOR_BREACH",
                message=f"Quality floor failed for pair '{pair_key}'.",
                details="\n".join(floor_failures),
            )
        else:
            record(
                findings,
                level="PASS",
                code="QUALITY_FLOOR_OK",
                message=f"Quality floor satisfied for pair '{pair_key}'.",
            )


def validate_delta_budgets(
    *,
    benchmark_payload: Mapping[str, object],
    baseline_payload: Mapping[str, object] | None,
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    if baseline_payload is None:
        record(
            findings,
            level="WARN",
            code="DELTA_BASELINE_MISSING",
            message="No baseline payload provided; skipping delta budget checks.",
        )
        return
    baseline_best = baseline_payload.get("benchmark_best_by_pair")
    if not isinstance(baseline_best, Mapping):
        record(
            findings,
            level="WARN",
            code="DELTA_BASELINE_EMPTY",
            message="Baseline payload has no benchmark_best_by_pair; skipping delta checks.",
        )
        return
    budgets = policy_payload.get("delta_budgets")
    if not isinstance(budgets, Mapping):
        record(
            findings,
            level="WARN",
            code="DELTA_BUDGETS_MISSING",
            message="Policy has no delta_budgets; skipping delta checks.",
        )
        return

    best_by_pair = pair_best_summary(benchmark_payload)
    budget_top1_drop = as_float(budgets.get("max_top1_accuracy_drop"), default=0.0)
    budget_top3_drop = as_float(budgets.get("max_top3_recall_drop"), default=0.0)
    budget_forbidden_top1_inc = as_float(
        budgets.get("max_forbidden_top1_rate_increase"), default=0.0
    )
    budget_forbidden_any_inc = as_float(budgets.get("max_forbidden_any_rate_increase"), default=0.0)
    budget_avg_rules_inc = as_float(budgets.get("max_avg_rules_per_target_increase"), default=0.0)

    any_checked = False
    for pair, baseline_summary in baseline_best.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(baseline_summary, Mapping):
            continue
        current_summary = best_by_pair.get(pair_key)
        if current_summary is None:
            record(
                findings,
                level="WARN",
                code="DELTA_PAIR_MISSING",
                message=f"Pair '{pair_key}' exists in baseline but not current benchmark.",
            )
            continue

        any_checked = True
        base_top1 = as_float(baseline_summary.get("top1_accuracy"), default=0.0)
        base_top3 = as_float(baseline_summary.get("top3_recall"), default=0.0)
        base_forbidden_top1 = as_float(baseline_summary.get("forbidden_top1_rate"), default=0.0)
        base_forbidden_any = as_float(baseline_summary.get("forbidden_any_rate"), default=0.0)
        base_avg_rules = as_float(baseline_summary.get("avg_rules_per_target"), default=0.0)

        cur_top1 = as_float(current_summary.get("top1_accuracy"), default=0.0)
        cur_top3 = as_float(current_summary.get("top3_recall"), default=0.0)
        cur_forbidden_top1 = as_float(current_summary.get("forbidden_top1_rate"), default=0.0)
        cur_forbidden_any = as_float(current_summary.get("forbidden_any_rate"), default=0.0)
        cur_avg_rules = as_float(current_summary.get("avg_rules_per_target"), default=0.0)

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
            record(
                findings,
                level="FAIL",
                code="DELTA_BUDGET_BREACH",
                message=f"Delta budgets failed for pair '{pair_key}'.",
                details="\n".join(failures),
            )
        else:
            record(
                findings,
                level="PASS",
                code="DELTA_BUDGET_OK",
                message=f"Delta budgets satisfied for pair '{pair_key}'.",
            )

    if not any_checked:
        record(
            findings,
            level="WARN",
            code="DELTA_NO_PAIRS_CHECKED",
            message="No overlapping pairs between baseline and current benchmark for delta checks.",
        )


def validate_saturation(
    *,
    benchmark_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
    strict_saturation: bool,
) -> None:
    saturation = policy_payload.get("saturation")
    if not isinstance(saturation, Mapping):
        record(
            findings,
            level="WARN",
            code="SATURATION_POLICY_MISSING",
            message="Policy has no saturation section; skipping saturation checks.",
        )
        return

    warn_share = as_float(saturation.get("warn_if_top_metric_vector_share_gte"), default=1.1)
    fail_share = as_float(saturation.get("fail_if_top_metric_vector_share_gt"), default=2.0)
    warn_unique_lt = as_int(saturation.get("warn_if_unique_metric_vectors_lt"), default=0)
    pairs_payload = benchmark_payload.get("pairs")
    if not isinstance(pairs_payload, Mapping):
        return

    for pair, pair_payload in pairs_payload.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(pair_payload, Mapping):
            continue
        runs = pair_payload.get("runs")
        if not isinstance(runs, Sequence) or not runs:
            record(
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
            metric_counts[metric_vector_key(run)] += 1

        run_count = max(1, len(runs))
        top_count = max(metric_counts.values()) if metric_counts else 0
        top_share = float(top_count) / float(run_count)
        unique_vectors = len(metric_counts)

        if top_share > fail_share:
            record(
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
            record(
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
            record(
                findings,
                level="PASS",
                code="SATURATION_TOP_VECTOR_OK",
                message=f"Pair '{pair_key}' top metric vector share={top_share:.3f} is below warning threshold.",
                details=f"run_count={run_count} unique_vectors={unique_vectors} top_count={top_count}",
            )

        if warn_unique_lt > 0 and unique_vectors < warn_unique_lt:
            record(
                findings,
                level=("FAIL" if strict_saturation else "WARN"),
                code="SATURATION_UNIQUE_VECTOR_WARN",
                message=(
                    f"Pair '{pair_key}' unique metric vectors={unique_vectors} below expected "
                    f"minimum={warn_unique_lt}."
                ),
            )


def validate_pos_guardrails(
    *,
    pos_probe_payload: Mapping[str, object] | None,
    pos_inventory_payload: Mapping[str, object] | None,
    baseline_payload: Mapping[str, object] | None,
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
) -> None:
    guardrails = policy_payload.get("pos_guardrails")
    if not isinstance(guardrails, Mapping):
        record(
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
        record(
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
        increase_budget = as_float(guardrails.get("max_bucket_mismatch_rate_increase"), default=0.0)

        for pair, threshold_value in max_mismatch.items():
            pair_key = str(pair).strip().lower()
            threshold = as_float(threshold_value)
            report = pair_reports_map.get(pair_key)
            if not isinstance(report, Mapping):
                record(
                    findings,
                    level="FAIL",
                    code="POS_PAIR_REPORT_MISSING",
                    message=f"POS probe has no pair report for '{pair_key}'.",
                )
                continue
            current_rate = as_float(report.get("bucket_mismatch_rate"), default=1.0)
            if current_rate > threshold:
                record(
                    findings,
                    level="FAIL",
                    code="POS_MISMATCH_RATE_BREACH",
                    message=(
                        f"Pair '{pair_key}' bucket_mismatch_rate={current_rate:.4f} exceeds "
                        f"threshold={threshold:.4f}."
                    ),
                )
            else:
                record(
                    findings,
                    level="PASS",
                    code="POS_MISMATCH_RATE_OK",
                    message=(
                        f"Pair '{pair_key}' bucket_mismatch_rate={current_rate:.4f} "
                        f"within threshold={threshold:.4f}."
                    ),
                )

            baseline_rate = as_float(baseline_mismatch_by_pair.get(pair_key), default=current_rate)
            increase = max(0.0, current_rate - baseline_rate)
            if increase > increase_budget:
                record(
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
        record(
            findings,
            level="WARN",
            code="POS_INVENTORY_MISSING",
            message="No POS inventory payload provided; skipping unknown-tag growth checks.",
        )
        return

    rows = pos_inventory_payload.get("rows")
    if not isinstance(rows, Sequence):
        record(
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
        current_unknown_by_pack[filename] = as_int(raw_unknown) if raw_unknown is not None else None

    default_budget = as_int(guardrails.get("default_unknown_pos_growth_budget"), default=0)
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
        if not pack or baseline_value is None:
            continue

        if pack not in current_unknown_by_pack:
            if pack in allow_missing:
                record(
                    findings,
                    level="WARN",
                    code="POS_UNKNOWN_PACK_MISSING_ALLOWED",
                    message=f"Pack '{pack}' missing in current inventory but listed as allowed missing.",
                )
                continue
            record(
                findings,
                level="FAIL",
                code="POS_UNKNOWN_PACK_MISSING",
                message=f"Pack '{pack}' is missing in current POS inventory payload.",
            )
            continue

        current_value = current_unknown_by_pack.get(pack)
        if current_value is None:
            if pack in allow_missing:
                record(
                    findings,
                    level="WARN",
                    code="POS_UNKNOWN_COUNT_NULL_ALLOWED",
                    message=f"Pack '{pack}' unknown tag count is null and is allowed missing.",
                )
                continue
            record(
                findings,
                level="FAIL",
                code="POS_UNKNOWN_COUNT_NULL",
                message=f"Pack '{pack}' unknown tag count is null.",
            )
            continue

        base_count = as_int(baseline_value)
        budget = as_int(budget_by_pack.get(pack), default=default_budget)
        allowed_max = base_count + budget
        if current_value > allowed_max:
            record(
                findings,
                level="FAIL",
                code="POS_UNKNOWN_GROWTH_BREACH",
                message=(
                    f"Pack '{pack}' unknown_pos_inventory_size={current_value} exceeds "
                    f"allowed_max={allowed_max} (baseline={base_count}, budget={budget})."
                ),
            )
        else:
            record(
                findings,
                level="PASS",
                code="POS_UNKNOWN_GROWTH_OK",
                message=(
                    f"Pack '{pack}' unknown_pos_inventory_size={current_value} within "
                    f"allowed_max={allowed_max} (baseline={base_count}, budget={budget})."
                ),
            )
