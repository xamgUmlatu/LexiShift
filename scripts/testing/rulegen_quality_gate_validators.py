from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

try:
    from .rulegen_quality_gate_core import (
        QualityFinding,
        as_float,
        as_int,
        pair_best_summary,
        record,
    )
    from .rulegen_quality_gate_guardrail_validators import (
        validate_pos_guardrails as _validate_pos_guardrails,
        validate_saturation as _validate_saturation,
    )
except Exception:  # noqa: BLE001
    from rulegen_quality_gate_core import (  # type: ignore[no-redef]
        QualityFinding,
        as_float,
        as_int,
        pair_best_summary,
        record,
    )
    from rulegen_quality_gate_guardrail_validators import (  # type: ignore[no-redef]
        validate_pos_guardrails as _validate_pos_guardrails,
        validate_saturation as _validate_saturation,
    )

validate_saturation = _validate_saturation
validate_pos_guardrails = _validate_pos_guardrails


def validate_dataset_contract(
    *,
    dataset_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    findings: list[QualityFinding],
    pair_scope: str | None = None,
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
    scoped_pair = str(pair_scope or "").strip().lower()

    for index, case in enumerate(raw_cases):
        if not isinstance(case, Mapping):
            if scoped_pair:
                continue
            missing_field_rows.append(f"index={index}: case is not an object")
            continue
        pair = str(case.get("pair") or "").strip().lower()
        if scoped_pair and pair != scoped_pair:
            continue
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
        contract_items = (
            [(scoped_pair, min_cases_per_pair.get(scoped_pair))]
            if scoped_pair
            else list(min_cases_per_pair.items())
        )
        for pair, minimum in contract_items:
            if minimum is None:
                continue
            pair_key = str(pair).strip().lower()
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
        contract_items = (
            [(scoped_pair, min_hard_cases_per_pair.get(scoped_pair))]
            if scoped_pair
            else list(min_hard_cases_per_pair.items())
        )
        for pair, minimum in contract_items:
            if minimum is None:
                continue
            pair_key = str(pair).strip().lower()
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
    pair_scope: str | None = None,
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
    scoped_pair = str(pair_scope or "").strip().lower()
    if scoped_pair:
        if scoped_pair not in available_pairs:
            record(
                findings,
                level="FAIL",
                code="BENCHMARK_SCOPE_PAIR_MISSING",
                message=f"Scoped benchmark pair '{scoped_pair}' is missing from benchmark artifact.",
            )
        else:
            record(
                findings,
                level="PASS",
                code="BENCHMARK_SCOPE_PAIR_PRESENT",
                message=f"Scoped benchmark pair '{scoped_pair}' is present in benchmark artifact.",
            )
        return

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
            level="FAIL",
            code="BENCHMARK_REQUIRED_PAIRS_MISSING",
            message="Required benchmark pairs are missing from benchmark artifact.",
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
    pair_scope: str | None = None,
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
    scoped_pair = str(pair_scope or "").strip().lower()
    if scoped_pair:
        pair_floor = floors.get(scoped_pair)
        if not isinstance(pair_floor, Mapping):
            record(
                findings,
                level="WARN",
                code="QUALITY_FLOOR_SCOPE_UNCONFIGURED",
                message=f"No quality floor is configured for scoped pair '{scoped_pair}'; skipping floor checks.",
            )
            return
        floor_items: Sequence[tuple[object, object]] = ((scoped_pair, pair_floor),)
    else:
        floor_items = tuple(floors.items())

    for pair, pair_floor in floor_items:
        pair_key = str(pair).strip().lower()
        if not isinstance(pair_floor, Mapping):
            continue
        summary = best_by_pair.get(pair_key)
        if summary is None:
            if scoped_pair:
                record(
                    findings,
                    level="FAIL",
                    code="QUALITY_FLOOR_SCOPE_PAIR_MISSING",
                    message=f"Scoped benchmark pair '{pair_key}' has no best-run summary for floor checks.",
                )
            else:
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
    pair_scope: str | None = None,
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

    def _evaluate_pair(pair_key: str, baseline_summary: Mapping[str, object]) -> bool:
        current_summary = best_by_pair.get(pair_key)
        if current_summary is None:
            record(
                findings,
                level="WARN",
                code="DELTA_PAIR_MISSING",
                message=f"Pair '{pair_key}' exists in baseline but not current benchmark.",
            )
            return False

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
        return True

    scoped_pair = str(pair_scope or "").strip().lower()
    if scoped_pair:
        current_summary = best_by_pair.get(scoped_pair)
        if current_summary is None:
            record(
                findings,
                level="FAIL",
                code="DELTA_SCOPE_PAIR_MISSING",
                message=f"Scoped benchmark pair '{scoped_pair}' has no current summary for delta checks.",
            )
            return
        baseline_summary = baseline_best.get(scoped_pair)
        if not isinstance(baseline_summary, Mapping):
            record(
                findings,
                level="WARN",
                code="DELTA_SCOPE_BASELINE_MISSING",
                message=f"Scoped pair '{scoped_pair}' has no baseline metrics; skipping delta checks.",
            )
            return
        _evaluate_pair(scoped_pair, baseline_summary)
        return

    any_checked = False
    for pair, baseline_summary in baseline_best.items():
        pair_key = str(pair).strip().lower()
        if not isinstance(baseline_summary, Mapping):
            continue
        if _evaluate_pair(pair_key, baseline_summary):
            any_checked = True

    if not any_checked:
        record(
            findings,
            level="WARN",
            code="DELTA_NO_PAIRS_CHECKED",
            message="No overlapping pairs between baseline and current benchmark for delta checks.",
        )
