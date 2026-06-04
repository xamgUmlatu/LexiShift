from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

try:
    from .rulegen_quality_gate_core import (
        QualityFinding,
        as_float,
        as_int,
        metric_vector_key,
        record,
    )
except Exception:  # noqa: BLE001
    from rulegen_quality_gate_core import (  # type: ignore[no-redef]
        QualityFinding,
        as_float,
        as_int,
        metric_vector_key,
        record,
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
