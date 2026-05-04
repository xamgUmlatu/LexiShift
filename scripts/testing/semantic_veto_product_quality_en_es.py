#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_rendering import render_product_quality_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_product_quality_policy_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_product_quality_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_product_quality_en_es_latest.md"
)

OUTCOMES = (
    "positive_allow",
    "positive_abstain",
    "negative_abstain",
    "negative_allow",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute product-oriented semantic-veto quality metrics from configured "
            "case-level validation reports. This harness treats good replacements "
            "as positives and bad replacements as negatives."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy = _load_json(args.policy_json)
    report = build_product_quality_report(policy=policy, policy_path=args.policy_json)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_product_quality_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_product_quality_report(
    *,
    policy: Mapping[str, object],
    policy_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy)
    acceptance = _as_mapping(policy.get("acceptance"))
    lane_reports = []
    all_cases: list[dict[str, object]] = []
    for lane in _mapping_rows(policy.get("lanes")):
        lane_report = _build_lane_report(lane=lane, weights=weights, acceptance=acceptance)
        lane_reports.append(lane_report)
        all_cases.extend(_mapping_rows(lane_report.get("case_traces")))
    measured_lane_types = sorted(
        {
            str(lane.get("lane_type") or "")
            for lane in lane_reports
            if str(lane.get("lane_type") or "").strip()
        }
    )

    overall = _score_cases(cases=all_cases, weights=weights, acceptance=acceptance)
    suite_breakdowns = _breakdowns(
        cases=all_cases,
        key="suite_id",
        weights=weights,
        acceptance=acceptance,
    )
    family_breakdowns = _breakdowns(
        cases=all_cases,
        key="family_id",
        weights=weights,
        acceptance=acceptance,
    )
    source_breakdowns = _breakdowns(
        cases=all_cases,
        key="source_id",
        weights=weights,
        acceptance=acceptance,
    )
    decision = _decision(overall=overall, lane_reports=lane_reports, policy=policy)
    return {
        "schema_version": 1,
        "status": decision["status"],
        "decision": decision["decision"],
        "generated_at": generated_at,
        "pair": str(policy.get("pair") or "en-es"),
        "policy": {
            "path": _repo_path(policy_path),
            "policy_id": str(policy.get("policy_id") or ""),
            "description": str(policy.get("description") or ""),
            "acceptance": dict(acceptance),
            "utility_weights": weights,
        },
        "summary": {
            "case_count": len(all_cases),
            "lane_count": len(lane_reports),
            "measured_lane_types": measured_lane_types,
            "planned_unmeasured_lane_types": _planned_unmeasured_lane_types(
                policy=policy,
                measured_lane_types=measured_lane_types,
            ),
            "overall": overall,
            "decision_rationale": decision["rationale"],
        },
        "lanes": lane_reports,
        "suite_breakdowns": suite_breakdowns,
        "source_breakdowns": source_breakdowns,
        "family_breakdowns": family_breakdowns,
        "failure_rows": _failure_rows(all_cases),
        "case_traces": all_cases,
        "limitations": _limitations(policy=policy, lane_reports=lane_reports),
        "next_steps": _next_steps(decision=decision, policy=policy),
    }


def _build_lane_report(
    *,
    lane: Mapping[str, object],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    lane_id = str(lane.get("lane_id") or "").strip()
    lane_type = str(lane.get("lane_type") or "").strip()
    case_traces: list[dict[str, object]] = []
    source_reports: list[dict[str, object]] = []
    for source in _mapping_rows(lane.get("reports")):
        source_id = str(source.get("source_id") or "").strip()
        suite_id = str(source.get("suite_id") or source_id).strip()
        report, report_path = _source_report(source)
        rows = _case_traces(
            lane_id=lane_id,
            lane_type=lane_type,
            source_id=source_id,
            suite_id=suite_id,
            report=report,
            report_path=report_path,
            weights=weights,
        )
        case_traces.extend(rows)
        source_reports.append(
            {
                "source_id": source_id,
                "suite_id": suite_id,
                "path": _repo_path(report_path),
                "case_count": len(rows),
                "report_status": str(report.get("status") or ""),
                "report_decision": str(report.get("decision") or ""),
                "report_summary": _compact_report_summary(report),
            }
        )
    metrics = _score_cases(cases=case_traces, weights=weights, acceptance=acceptance)
    return {
        "lane_id": lane_id,
        "lane_type": lane_type,
        "description": str(lane.get("description") or ""),
        "interpretation": str(lane.get("interpretation") or ""),
        "source_reports": source_reports,
        "metrics": metrics,
        "case_traces": case_traces,
    }


def _case_traces(
    *,
    lane_id: str,
    lane_type: str,
    source_id: str,
    suite_id: str,
    report: Mapping[str, object],
    report_path: Path | None,
    weights: Mapping[str, float],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in _case_result_rows(report):
        gold_decision = _normalize_decision(row.get("gold_decision"))
        predicted_decision = _normalize_decision(row.get("predicted_decision"))
        product_class = "positive" if gold_decision == "replace" else "negative"
        user_outcome = "allow" if predicted_decision == "replace" else "abstain"
        product_outcome = f"{product_class}_{user_outcome}"
        rows.append(
            {
                "case_id": str(row.get("case_id") or "").strip(),
                "lane_id": lane_id,
                "lane_type": lane_type,
                "source_id": source_id,
                "suite_id": suite_id,
                "report_path": _repo_path(report_path),
                "family_id": str(row.get("family_id") or "").strip(),
                "trigger": str(row.get("trigger") or "").strip(),
                "sentence": str(row.get("sentence") or "").strip(),
                "gold_decision": gold_decision,
                "predicted_decision": predicted_decision,
                "product_class": product_class,
                "user_outcome": user_outcome,
                "product_outcome": product_outcome,
                "utility_contribution": _round4(weights.get(product_outcome, 0.0)),
                "error_type": _error_type(gold=gold_decision, predicted=predicted_decision),
                "active_score": _safe_float(row.get("active_score")),
                "strongest_shadow_score": _safe_float(row.get("strongest_shadow_score")),
                "phrase_control_score": _safe_float(row.get("phrase_control_score")),
                "surface_pos_signal": str(row.get("surface_pos_signal") or "").strip(),
            }
        )
    return rows


def _score_cases(
    *,
    cases: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    counts = Counter(str(row.get("product_outcome") or "") for row in cases)
    return score_product_outcome_counts(
        outcome_counts=counts,
        weights=weights,
        acceptance=acceptance,
    )


def score_product_outcome_counts(
    *,
    outcome_counts: Mapping[str, object],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    counts = Counter(
        {outcome: max(0, int(outcome_counts.get(outcome) or 0)) for outcome in OUTCOMES}
    )
    positive_count = counts["positive_allow"] + counts["positive_abstain"]
    negative_count = counts["negative_abstain"] + counts["negative_allow"]
    case_count = positive_count + negative_count
    utility = sum(weights.get(outcome, 0.0) * counts[outcome] for outcome in OUTCOMES)
    lexical = _baseline_metrics(
        baseline_id="lexical_allow_all",
        positive_count=positive_count,
        negative_count=negative_count,
        weights=weights,
    )
    abstain_all = _baseline_metrics(
        baseline_id="abstain_all",
        positive_count=positive_count,
        negative_count=negative_count,
        weights=weights,
    )
    result = {
        "scope_id": "",
        "case_count": case_count,
        "positive_case_count": positive_count,
        "negative_case_count": negative_count,
        "positive_allow_count": counts["positive_allow"],
        "positive_abstain_count": counts["positive_abstain"],
        "negative_abstain_count": counts["negative_abstain"],
        "negative_allow_count": counts["negative_allow"],
        "positive_allow_rate": _optional_ratio(counts["positive_allow"], positive_count),
        "positive_abstain_rate": _optional_ratio(counts["positive_abstain"], positive_count),
        "negative_abstain_rate": _optional_ratio(counts["negative_abstain"], negative_count),
        "negative_allow_rate": _optional_ratio(counts["negative_allow"], negative_count),
        "utility_score": _round4(utility),
        "utility_per_case": _safe_ratio(utility, case_count),
        "baselines": {
            "lexical_allow_all": lexical,
            "abstain_all": abstain_all,
        },
        "delta_vs_lexical_utility": _round4(utility - _safe_float(lexical.get("utility_score"))),
        "delta_vs_abstain_all_utility": _round4(
            utility - _safe_float(abstain_all.get("utility_score"))
        ),
    }
    result["target_checks"] = _target_checks(metrics=result, acceptance=acceptance)
    return result


def _baseline_metrics(
    *,
    baseline_id: str,
    positive_count: int,
    negative_count: int,
    weights: Mapping[str, float],
) -> dict[str, object]:
    if baseline_id == "lexical_allow_all":
        counts = {
            "positive_allow": positive_count,
            "positive_abstain": 0,
            "negative_abstain": 0,
            "negative_allow": negative_count,
        }
    elif baseline_id == "abstain_all":
        counts = {
            "positive_allow": 0,
            "positive_abstain": positive_count,
            "negative_abstain": negative_count,
            "negative_allow": 0,
        }
    else:
        raise ValueError(f"Unknown baseline: {baseline_id}")
    utility = sum(weights.get(key, 0.0) * value for key, value in counts.items())
    case_count = positive_count + negative_count
    return {
        "baseline_id": baseline_id,
        "case_count": case_count,
        "positive_case_count": positive_count,
        "negative_case_count": negative_count,
        **{f"{key}_count": value for key, value in counts.items()},
        "positive_allow_rate": _optional_ratio(counts["positive_allow"], positive_count),
        "negative_abstain_rate": _optional_ratio(counts["negative_abstain"], negative_count),
        "utility_score": _round4(utility),
        "utility_per_case": _safe_ratio(utility, case_count),
    }


def _target_checks(
    *,
    metrics: Mapping[str, object],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    positive_threshold = _safe_float(acceptance.get("positive_allow_rate_min"))
    negative_threshold = _safe_float(acceptance.get("negative_abstain_rate_min"))
    utility = _safe_float(metrics.get("utility_score"))
    lexical = _safe_float(
        _as_mapping(_as_mapping(metrics.get("baselines")).get("lexical_allow_all")).get(
            "utility_score"
        )
    )
    abstain_all = _safe_float(
        _as_mapping(_as_mapping(metrics.get("baselines")).get("abstain_all")).get("utility_score")
    )
    positive_rate = _safe_float(metrics.get("positive_allow_rate"))
    negative_rate = _safe_float(metrics.get("negative_abstain_rate"))
    positive_count = int(metrics.get("positive_case_count") or 0)
    negative_count = int(metrics.get("negative_case_count") or 0)
    checks = {
        "positive_allow_rate_min": positive_threshold,
        "positive_allow_rate_met": (
            None if positive_count <= 0 else positive_rate >= positive_threshold
        ),
        "negative_abstain_rate_min": negative_threshold,
        "negative_abstain_rate_met": (
            None if negative_count <= 0 else negative_rate >= negative_threshold
        ),
        "utility_beats_lexical_baseline": utility > lexical,
        "utility_beats_abstain_all_baseline": utility > abstain_all,
    }
    required_results = [
        checks["positive_allow_rate_met"],
        checks["negative_abstain_rate_met"],
    ]
    if bool(acceptance.get("utility_must_beat_lexical_baseline")):
        required_results.append(checks["utility_beats_lexical_baseline"])
    if bool(acceptance.get("utility_must_beat_abstain_all_baseline")):
        required_results.append(checks["utility_beats_abstain_all_baseline"])
    applicable = [value for value in required_results if value is not None]
    checks["target_status"] = (
        "insufficient_class_coverage"
        if not applicable
        else "pass"
        if all(bool(value) for value in applicable)
        else "fail"
    )
    return checks


def _decision(
    *,
    overall: Mapping[str, object],
    lane_reports: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
) -> dict[str, object]:
    target_status = str(_as_mapping(overall.get("target_checks")).get("target_status") or "")
    measured_types = {
        str(lane.get("lane_type") or "")
        for lane in lane_reports
        if str(lane.get("lane_type") or "").strip()
    }
    representative_measured = "representative" in measured_types
    if target_status != "pass":
        return {
            "status": "review",
            "decision": "product_target_missed",
            "rationale": [
                "The measured lanes do not meet the initial product target.",
                "Use failure rows to decide whether the next work is evidence, scoring, or policy.",
            ],
        }
    if bool(
        _as_mapping(policy.get("acceptance")).get("representative_lane_required_for_promotion")
    ):
        if not representative_measured:
            return {
                "status": "review",
                "decision": "stress_lane_product_target_pass_representative_unmeasured",
                "rationale": [
                    "The measured stress lane meets the initial product target and beats lexical baseline.",
                    "This is not production evidence because no representative browsing lane has been measured.",
                    "The next useful milestone is to add a representative or LLM-expanded locked lane.",
                ],
            }
    return {
        "status": "ok",
        "decision": "product_target_passed_on_measured_lanes",
        "rationale": [
            "The measured lanes meet the configured product target.",
            "Review lane coverage before treating this as promotion evidence.",
        ],
    }


def _breakdowns(
    *,
    cases: Sequence[Mapping[str, object]],
    key: str,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in cases:
        value = str(row.get(key) or "").strip()
        if value:
            grouped[value].append(row)
    rows = []
    for scope_id, group in sorted(grouped.items()):
        metrics = _score_cases(cases=group, weights=weights, acceptance=acceptance)
        metrics["scope_id"] = scope_id
        rows.append(metrics)
    return rows


def _failure_rows(cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "case_id": str(row.get("case_id") or ""),
            "lane_id": str(row.get("lane_id") or ""),
            "suite_id": str(row.get("suite_id") or ""),
            "trigger": str(row.get("trigger") or ""),
            "product_outcome": str(row.get("product_outcome") or ""),
            "error_type": str(row.get("error_type") or ""),
            "sentence": str(row.get("sentence") or ""),
        }
        for row in cases
        if str(row.get("product_outcome") or "") in {"positive_abstain", "negative_allow"}
    ]


def _next_steps(*, decision: Mapping[str, object], policy: Mapping[str, object]) -> list[str]:
    if (
        str(decision.get("decision") or "")
        == "stress_lane_product_target_pass_representative_unmeasured"
    ):
        return [
            "Add a representative browsing lane before making a broad product-quality claim.",
            "Use LLM generation budget to create admitted positive, negative, and phrase/no-winner rows for that lane.",
            "Keep this stress lane in the report so future candidates cannot hide regressions on known hard cases.",
        ]
    if str(decision.get("decision") or "") == "product_target_missed":
        return [
            "Inspect failure rows and suite breakdowns before changing thresholds.",
            "Prefer data/evidence fixes when negative allows cluster by missing phrase or shadow evidence.",
            "Prefer policy fixes only when score traces already expose the correct no-replace signal.",
        ]
    return list(_as_sequence(policy.get("next_steps")))


def _limitations(
    *,
    policy: Mapping[str, object],
    lane_reports: Sequence[Mapping[str, object]],
) -> list[str]:
    limitations = [
        "product_metrics_do_not_replace_runtime_validation",
        "stress_lane_is_not_representative_browsing",
        "case_labels_are_inherited_from_source_validation_reports",
    ]
    measured_types = {
        str(lane.get("lane_type") or "")
        for lane in lane_reports
        if str(lane.get("lane_type") or "").strip()
    }
    planned = set(_planned_lane_types(policy))
    if planned - measured_types:
        limitations.append("planned_lanes_unmeasured")
    return limitations


def _planned_lane_types(policy: Mapping[str, object]) -> list[str]:
    return sorted(
        {
            str(row.get("lane_type") or "")
            for row in _mapping_rows(policy.get("planned_lanes"))
            if str(row.get("lane_type") or "").strip()
        }
    )


def _planned_unmeasured_lane_types(
    *,
    policy: Mapping[str, object],
    measured_lane_types: Sequence[object],
) -> list[str]:
    measured = {str(value or "").strip() for value in measured_lane_types}
    return [lane_type for lane_type in _planned_lane_types(policy) if lane_type not in measured]


def _source_report(source: Mapping[str, object]) -> tuple[Mapping[str, object], Path | None]:
    inline = source.get("report")
    if isinstance(inline, Mapping):
        return inline, None
    path_text = str(source.get("path") or "").strip()
    if not path_text:
        raise ValueError("Product quality report source needs either inline report or path.")
    path = _resolve_repo_path(path_text)
    return _load_json(path), path


def _compact_report_summary(report: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(report.get("summary"))
    return {
        "case_count": int(summary.get("case_count") or summary.get("cases_total") or 0),
        "gold_replace_cases": int(summary.get("gold_replace_cases") or 0),
        "gold_abstain_cases": int(summary.get("gold_abstain_cases") or 0),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "replace_recall": _safe_float(summary.get("replace_recall")),
        "decision_accuracy": _safe_float(summary.get("decision_accuracy")),
    }


def _case_result_rows(report: Mapping[str, object]) -> list[Mapping[str, object]]:
    configured_rows = _mapping_rows(report.get("configured_case_results"))
    if configured_rows:
        return configured_rows
    row_results = _mapping_rows(report.get("row_results"))
    if row_results:
        return row_results
    return []


def _utility_weights(policy: Mapping[str, object]) -> dict[str, float]:
    raw = _as_mapping(policy.get("utility_weights"))
    weights = {
        "positive_allow": 1.0,
        "positive_abstain": -0.4,
        "negative_abstain": 0.8,
        "negative_allow": -0.6,
    }
    for key in OUTCOMES:
        if key in raw:
            weights[key] = _safe_float(raw.get(key))
    return weights


def _normalize_decision(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"replace", "allow", "yes"}:
        return "replace"
    if text in {"abstain", "no_replace", "no-replace", "no", "none"}:
        return "abstain"
    raise ValueError(f"Unknown semantic-veto decision value: {value!r}")


def _error_type(*, gold: str, predicted: str) -> str:
    if gold == predicted:
        return ""
    if gold == "replace" and predicted != "replace":
        return "false_abstain"
    if gold != "replace" and predicted == "replace":
        return "harmful_replace"
    return "other_mismatch"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return _round4(numerator / denominator)


def _optional_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return _round4(numerator / denominator)


def _round4(value: float) -> float:
    return round(float(value), 4)


def _format_percent(value: object) -> str:
    if value is None or value == "":
        return "n/a"
    return f"{_safe_float(value) * 100:.1f}%"


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
