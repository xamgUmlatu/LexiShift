#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_ACTIVE_REPORT = TEST_OUTPUTS_ROOT / (
    "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_"
    "heldout_validation_latest.json"
)
DEFAULT_PHRASE_REPORT = TEST_OUTPUTS_ROOT / (
    "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_"
    "phrase_validation_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / ("semantic_veto_current_evidence_ceiling_wave7_latest.json")
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_veto_current_evidence_ceiling_wave7_latest.md"
)

SURFACE_FRAME_SIGNALS = {"active_noun_frame", "active_modifier_frame"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test whether general runtime-compatible guards can recover the "
            "score-visible wave7 residuals using the current evidence and score "
            "traces only. This is research-only and does not change runtime policy."
        )
    )
    parser.add_argument("--active-report-json", type=Path, default=DEFAULT_ACTIVE_REPORT)
    parser.add_argument("--phrase-report-json", type=Path, default=DEFAULT_PHRASE_REPORT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    active_report = _load_json(args.active_report_json)
    phrase_report = _load_json(args.phrase_report_json)
    report = build_current_evidence_ceiling_report(
        active_report=active_report,
        phrase_report=phrase_report,
        active_report_path=args.active_report_json,
        phrase_report_path=args.phrase_report_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_current_evidence_ceiling_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_current_evidence_ceiling_report(
    *,
    active_report: Mapping[str, object],
    phrase_report: Mapping[str, object],
    active_report_path: Path | None = None,
    phrase_report_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    cases = [
        *_case_rows(suite_id="active_shadow", report=active_report),
        *_case_rows(suite_id="phrase_no_winner", report=phrase_report),
    ]
    baseline = _evaluate_policy(cases=cases, policy=_baseline_policy())
    policies = [_baseline_policy(), *_guard_policies()]
    rows = [_evaluate_policy(cases=cases, policy=policy) for policy in policies]
    optimistic = _optimistic_current_evidence_bound(cases=cases, baseline=baseline)
    representatives = _representative_rows(rows=rows, baseline=baseline)
    assessment = _ceiling_assessment(
        baseline=baseline,
        optimistic=optimistic,
        representatives=representatives,
    )
    return {
        "schema_version": 1,
        "status": "review",
        "decision": assessment["decision"],
        "generated_at": generated_at,
        "research_only": True,
        "source_reports": {
            "active_report": _report_ref(active_report, active_report_path),
            "phrase_report": _report_ref(phrase_report, phrase_report_path),
        },
        "summary": {
            "case_count": len(cases),
            "candidate_policy_count": len(rows),
            "baseline": _summary_row(baseline),
            "optimistic_current_evidence_bound": optimistic,
            "ceiling_assessment": assessment,
        },
        "representative_policies": representatives,
        "top_policies_by_accuracy": _top_rows(rows, key="accuracy_first", limit=10),
        "top_zero_harm_policies": _top_rows(rows, key="zero_harm", limit=10),
        "top_no_regression_policies": _top_rows(rows, key="no_regression", limit=10),
        "limitations": [
            "current_evidence_only_no_new_source_rows",
            "abstain_guard_sweep_only_does_not_recover_false_abstains_to_replace",
            "no_case_ids_no_trigger_specific_rules",
            "fixed_trace_research_only_not_runtime_policy",
        ],
        "next_steps": _next_steps(assessment=assessment),
    }


def render_current_evidence_ceiling_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    baseline = _as_mapping(summary.get("baseline"))
    optimistic = _as_mapping(summary.get("optimistic_current_evidence_bound"))
    assessment = _as_mapping(summary.get("ceiling_assessment"))
    lines = [
        "# en-es Wave7 Current-Evidence Ceiling Validation",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Research only: `{str(report.get('research_only', False)).lower()}`",
        f"- Candidate policies: `{summary.get('candidate_policy_count', 0)}`",
        "",
        "## Result",
        "",
        f"- Baseline: `{baseline.get('correct_case_count', 0)} / "
        f"{baseline.get('case_count', 0)}` correct, "
        f"`{baseline.get('harmful_replace_count', 0)}` harmful, "
        f"`{baseline.get('false_abstain_count', 0)}` false abstain",
        f"- Optimistic current-evidence target: "
        f"`{optimistic.get('optimistic_correct_case_count', 0)} / "
        f"{optimistic.get('case_count', 0)}` correct",
        f"- Best no-regression policy: "
        f"`{_policy_label(_as_mapping(assessment.get('best_no_regression_policy')))}`",
        f"- Best no-regression result: "
        f"`{assessment.get('best_no_regression_correct_case_count', 0)} / "
        f"{baseline.get('case_count', 0)}` correct, "
        f"`{assessment.get('best_no_regression_harmful_replace_count', 0)}` harmful, "
        f"`{assessment.get('best_no_regression_false_abstain_count', 0)}` false abstain",
        f"- Ceiling read: `{assessment.get('ceiling_status', '')}`",
        "",
        "## Representative Policies",
        "",
        _policy_table(report.get("representative_policies")),
        "",
        "## Top Policies By Accuracy",
        "",
        _policy_table(report.get("top_policies_by_accuracy")),
        "",
        "## Top Zero-Harm Policies",
        "",
        _policy_table(report.get("top_zero_harm_policies")),
        "",
        "## Top No-Regression Policies",
        "",
        _policy_table(report.get("top_no_regression_policies")),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(assessment.get("interpretation")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _case_rows(*, suite_id: str, report: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in _mapping_rows(report.get("configured_case_results")):
        materialized = dict(row)
        materialized["suite_id"] = suite_id
        rows.append(materialized)
    return rows


def _baseline_policy() -> dict[str, object]:
    return {
        "policy_id": "baseline_current_policy",
        "scope": "none",
        "phrase_lead_min": None,
        "phrase_close_margin": None,
        "shadow_lead_min": None,
        "nonactive_lead_min": None,
    }


def _guard_policies() -> list[dict[str, object]]:
    policies: list[dict[str, object]] = []
    phrase_lead_values = [
        None,
        0.0,
        0.005,
        0.01,
        0.015,
        0.02,
        0.03,
        0.04,
        0.05,
        0.06,
        0.07,
        0.08,
        0.1,
    ]
    phrase_close_values = [None, 0.0, 0.005, 0.01, 0.02, 0.05]
    shadow_values = [None, 0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1]
    nonactive_values = [None, 0.0, 0.005, 0.01, 0.02, 0.03, 0.05]
    seen: set[str] = set()
    for scope in ("surface_frame", "surface_rescue"):
        for phrase_lead in phrase_lead_values:
            policy = _policy(
                scope=scope,
                phrase_lead_min=phrase_lead,
                phrase_close_margin=None,
                shadow_lead_min=None,
                nonactive_lead_min=None,
            )
            _append_policy(policies=policies, seen=seen, policy=policy)
        for phrase_close in phrase_close_values:
            policy = _policy(
                scope=scope,
                phrase_lead_min=None,
                phrase_close_margin=phrase_close,
                shadow_lead_min=None,
                nonactive_lead_min=None,
            )
            _append_policy(policies=policies, seen=seen, policy=policy)
        for shadow in shadow_values:
            policy = _policy(
                scope=scope,
                phrase_lead_min=None,
                phrase_close_margin=None,
                shadow_lead_min=shadow,
                nonactive_lead_min=None,
            )
            _append_policy(policies=policies, seen=seen, policy=policy)
        for nonactive in nonactive_values:
            policy = _policy(
                scope=scope,
                phrase_lead_min=None,
                phrase_close_margin=None,
                shadow_lead_min=None,
                nonactive_lead_min=nonactive,
            )
            _append_policy(policies=policies, seen=seen, policy=policy)
        for phrase_lead in phrase_lead_values:
            if phrase_lead is None:
                continue
            for shadow in shadow_values:
                if shadow is None:
                    continue
                policy = _policy(
                    scope=scope,
                    phrase_lead_min=phrase_lead,
                    phrase_close_margin=None,
                    shadow_lead_min=shadow,
                    nonactive_lead_min=None,
                )
                _append_policy(policies=policies, seen=seen, policy=policy)
        for phrase_close in phrase_close_values:
            if phrase_close is None:
                continue
            for shadow in shadow_values:
                if shadow is None:
                    continue
                policy = _policy(
                    scope=scope,
                    phrase_lead_min=None,
                    phrase_close_margin=phrase_close,
                    shadow_lead_min=shadow,
                    nonactive_lead_min=None,
                )
                _append_policy(policies=policies, seen=seen, policy=policy)
    return policies


def _append_policy(
    *,
    policies: list[dict[str, object]],
    seen: set[str],
    policy: dict[str, object],
) -> None:
    if policy["policy_id"] in seen:
        return
    seen.add(str(policy["policy_id"]))
    policies.append(policy)


def _policy(
    *,
    scope: str,
    phrase_lead_min: float | None,
    phrase_close_margin: float | None,
    shadow_lead_min: float | None,
    nonactive_lead_min: float | None,
) -> dict[str, object]:
    parts = [scope]
    if phrase_lead_min is not None:
        parts.append(f"phrase_lead>={phrase_lead_min:g}")
    if phrase_close_margin is not None:
        parts.append(f"phrase_close<={phrase_close_margin:g}")
    if shadow_lead_min is not None:
        parts.append(f"shadow_lead>={shadow_lead_min:g}")
    if nonactive_lead_min is not None:
        parts.append(f"nonactive_lead>={nonactive_lead_min:g}")
    return {
        "policy_id": "|".join(parts),
        "scope": scope,
        "phrase_lead_min": phrase_lead_min,
        "phrase_close_margin": phrase_close_margin,
        "shadow_lead_min": shadow_lead_min,
        "nonactive_lead_min": nonactive_lead_min,
    }


def _evaluate_policy(
    *,
    cases: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
) -> dict[str, object]:
    case_results: list[dict[str, object]] = []
    for row in cases:
        base_decision = str(row.get("predicted_decision") or "").strip()
        final_decision = _apply_policy(row=row, policy=policy)
        gold_decision = str(row.get("gold_decision") or "").strip()
        baseline_correct = base_decision == gold_decision
        final_correct = final_decision == gold_decision
        case_results.append(
            {
                "case_id": str(row.get("case_id") or "").strip(),
                "suite_id": str(row.get("suite_id") or "").strip(),
                "trigger": str(row.get("trigger") or "").strip(),
                "gold_decision": gold_decision,
                "baseline_decision": base_decision,
                "final_decision": final_decision,
                "baseline_correct": baseline_correct,
                "final_correct": final_correct,
                "changed": final_decision != base_decision,
                "fixed_residual": final_correct and not baseline_correct,
                "regressed": baseline_correct and not final_correct,
                "score_visible_residual": (
                    (not baseline_correct) and _gold_signal_score_visible(row)
                ),
                "error_type": _decision_error_type(gold=gold_decision, predicted=final_decision),
            }
        )
    correct = sum(1 for row in case_results if row["final_correct"])
    harmful = sum(1 for row in case_results if row["error_type"] == "harmful_replace")
    false_abstain = sum(1 for row in case_results if row["error_type"] == "false_abstain")
    fixed = [row["case_id"] for row in case_results if row["fixed_residual"]]
    regressions = [row["case_id"] for row in case_results if row["regressed"]]
    fixed_score_visible = [
        row["case_id"]
        for row in case_results
        if row["fixed_residual"] and row["score_visible_residual"]
    ]
    remaining_errors = [row["case_id"] for row in case_results if not row["final_correct"]]
    return {
        "policy": dict(policy),
        "policy_id": str(policy.get("policy_id") or ""),
        "case_count": len(case_results),
        "correct_case_count": correct,
        "accuracy": _safe_ratio(correct, len(case_results)),
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
        "fixed_residual_count": len(fixed),
        "fixed_score_visible_residual_count": len(fixed_score_visible),
        "regressed_case_count": len(regressions),
        "changed_case_count": sum(1 for row in case_results if row["changed"]),
        "fixed_case_ids": fixed,
        "fixed_score_visible_case_ids": fixed_score_visible,
        "regressed_case_ids": regressions,
        "remaining_error_case_ids": remaining_errors,
    }


def _apply_policy(*, row: Mapping[str, object], policy: Mapping[str, object]) -> str:
    decision = str(row.get("predicted_decision") or "").strip()
    if decision != "replace" or str(policy.get("scope") or "") == "none":
        return decision
    if not _policy_scope_applies(row=row, policy=policy):
        return decision
    active_score = _safe_float(row.get("active_score"))
    shadow_score = _safe_float(row.get("strongest_shadow_score"))
    phrase_score = _safe_float(row.get("phrase_control_score"))
    best_competitor = max(active_score, shadow_score)
    guard_hit = False
    phrase_lead_min = policy.get("phrase_lead_min")
    if phrase_lead_min is not None:
        guard_hit = guard_hit or phrase_score >= best_competitor + _safe_float(phrase_lead_min)
    phrase_close_margin = policy.get("phrase_close_margin")
    if phrase_close_margin is not None:
        guard_hit = guard_hit or phrase_score >= best_competitor - _safe_float(phrase_close_margin)
    shadow_lead_min = policy.get("shadow_lead_min")
    if shadow_lead_min is not None:
        guard_hit = guard_hit or shadow_score >= active_score + _safe_float(shadow_lead_min)
    nonactive_lead_min = policy.get("nonactive_lead_min")
    if nonactive_lead_min is not None:
        guard_hit = guard_hit or max(shadow_score, phrase_score) >= (
            active_score + _safe_float(nonactive_lead_min)
        )
    return "abstain" if guard_hit else decision


def _policy_scope_applies(*, row: Mapping[str, object], policy: Mapping[str, object]) -> bool:
    scope = str(policy.get("scope") or "")
    signal = str(row.get("surface_pos_signal") or "").strip()
    if scope == "surface_frame":
        return signal in SURFACE_FRAME_SIGNALS
    if scope == "surface_rescue":
        return signal in SURFACE_FRAME_SIGNALS and bool(row.get("active_rescue_applied"))
    return False


def _optimistic_current_evidence_bound(
    *,
    cases: Sequence[Mapping[str, object]],
    baseline: Mapping[str, object],
) -> dict[str, object]:
    score_visible_residuals = [
        str(row.get("case_id") or "")
        for row in cases
        if str(row.get("predicted_decision") or "").strip()
        != str(row.get("gold_decision") or "").strip()
        and _gold_signal_score_visible(row)
    ]
    correct = int(baseline.get("correct_case_count") or 0)
    case_count = len(cases)
    optimistic_correct = min(case_count, correct + len(score_visible_residuals))
    return {
        "case_count": case_count,
        "score_visible_residual_count": len(score_visible_residuals),
        "score_visible_residual_case_ids": score_visible_residuals,
        "optimistic_correct_case_count": optimistic_correct,
        "optimistic_accuracy": _safe_ratio(optimistic_correct, case_count),
        "definition": (
            "baseline correct cases plus all baseline residuals whose gold signal is visible "
            "in the current score trace"
        ),
    }


def _representative_rows(
    *,
    rows: Sequence[Mapping[str, object]],
    baseline: Mapping[str, object],
) -> dict[str, object]:
    return {
        "baseline": _summary_row(baseline),
        "best_accuracy": _summary_row(_sorted_rows(rows, key="accuracy_first")[0]),
        "best_zero_harm": _summary_row(_sorted_rows(rows, key="zero_harm")[0]),
        "best_no_regression": _summary_row(_sorted_rows(rows, key="no_regression")[0]),
    }


def _ceiling_assessment(
    *,
    baseline: Mapping[str, object],
    optimistic: Mapping[str, object],
    representatives: Mapping[str, object],
) -> dict[str, object]:
    best_no_regression = _as_mapping(representatives.get("best_no_regression"))
    best_accuracy = _as_mapping(representatives.get("best_accuracy"))
    optimistic_correct = int(optimistic.get("optimistic_correct_case_count") or 0)
    baseline_correct = int(baseline.get("correct_case_count") or 0)
    best_no_regression_correct = int(best_no_regression.get("correct_case_count") or 0)
    best_accuracy_correct = int(best_accuracy.get("correct_case_count") or 0)
    best_no_regression_harm = int(best_no_regression.get("harmful_replace_count") or 0)
    best_no_regression_false_abstain = int(best_no_regression.get("false_abstain_count") or 0)
    fixed_score_visible = int(best_no_regression.get("fixed_score_visible_residual_count") or 0)
    total_score_visible = int(optimistic.get("score_visible_residual_count") or 0)
    if (
        best_no_regression_correct >= optimistic_correct
        and int(best_no_regression.get("regressed_case_count") or 0) == 0
    ):
        status = "optimistic_ceiling_validated_by_general_guard_sweep"
        decision = "current_evidence_ceiling_survives"
    elif best_no_regression_correct > baseline_correct:
        status = "partial_headroom_but_optimistic_ceiling_collapsed"
        decision = "current_evidence_ceiling_partially_supported"
    elif best_accuracy_correct > baseline_correct:
        status = "headroom_requires_regressions"
        decision = "current_evidence_ceiling_not_validated"
    else:
        status = "no_general_guard_headroom_found"
        decision = "current_evidence_ceiling_collapsed"
    return {
        "decision": decision,
        "ceiling_status": status,
        "baseline_correct_case_count": baseline_correct,
        "optimistic_correct_case_count": optimistic_correct,
        "best_accuracy_correct_case_count": best_accuracy_correct,
        "best_no_regression_correct_case_count": best_no_regression_correct,
        "best_no_regression_harmful_replace_count": best_no_regression_harm,
        "best_no_regression_false_abstain_count": best_no_regression_false_abstain,
        "best_no_regression_fixed_score_visible_residual_count": fixed_score_visible,
        "score_visible_residual_count": total_score_visible,
        "best_no_regression_policy": best_no_regression.get("policy", {}),
        "interpretation": [
            (
                f"The optimistic ceiling would require {optimistic_correct} / "
                f"{baseline.get('case_count', 0)} correct cases."
            ),
            (
                f"The best no-regression guard only reaches {best_no_regression_correct} / "
                f"{baseline.get('case_count', 0)} and fixes {fixed_score_visible} / "
                f"{total_score_visible} score-visible residuals."
            ),
            (
                "Zero-harm guard policies exist in this sweep, but they trade away currently "
                "correct replace cases, so they do not validate the optimistic bound."
            ),
        ],
    }


def _summary_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "policy": row.get("policy", {}),
        "policy_id": str(row.get("policy_id") or ""),
        "case_count": int(row.get("case_count") or 0),
        "correct_case_count": int(row.get("correct_case_count") or 0),
        "accuracy": _safe_float(row.get("accuracy")),
        "harmful_replace_count": int(row.get("harmful_replace_count") or 0),
        "false_abstain_count": int(row.get("false_abstain_count") or 0),
        "fixed_residual_count": int(row.get("fixed_residual_count") or 0),
        "fixed_score_visible_residual_count": int(
            row.get("fixed_score_visible_residual_count") or 0
        ),
        "regressed_case_count": int(row.get("regressed_case_count") or 0),
        "changed_case_count": int(row.get("changed_case_count") or 0),
        "fixed_case_ids": list(_as_sequence(row.get("fixed_case_ids"))),
        "fixed_score_visible_case_ids": list(_as_sequence(row.get("fixed_score_visible_case_ids"))),
        "regressed_case_ids": list(_as_sequence(row.get("regressed_case_ids"))),
        "remaining_error_case_ids": list(_as_sequence(row.get("remaining_error_case_ids"))),
    }


def _top_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
    limit: int,
) -> list[dict[str, object]]:
    return [_summary_row(row) for row in _sorted_rows(rows, key=key)[:limit]]


def _sorted_rows(rows: Sequence[Mapping[str, object]], *, key: str) -> list[Mapping[str, object]]:
    if key == "accuracy_first":
        return sorted(
            rows,
            key=lambda row: (
                -int(row.get("correct_case_count") or 0),
                int(row.get("harmful_replace_count") or 0),
                int(row.get("false_abstain_count") or 0),
                int(row.get("regressed_case_count") or 0),
                str(row.get("policy_id") or ""),
            ),
        )
    if key == "zero_harm":
        return sorted(
            rows,
            key=lambda row: (
                int(row.get("harmful_replace_count") or 0),
                -int(row.get("correct_case_count") or 0),
                int(row.get("false_abstain_count") or 0),
                int(row.get("regressed_case_count") or 0),
                str(row.get("policy_id") or ""),
            ),
        )
    if key == "no_regression":
        return sorted(
            rows,
            key=lambda row: (
                int(row.get("regressed_case_count") or 0),
                -int(row.get("correct_case_count") or 0),
                int(row.get("harmful_replace_count") or 0),
                int(row.get("false_abstain_count") or 0),
                str(row.get("policy_id") or ""),
            ),
        )
    raise ValueError(f"Unknown sort key: {key}")


def _next_steps(*, assessment: Mapping[str, object]) -> list[str]:
    status = str(assessment.get("ceiling_status") or "")
    if status == "optimistic_ceiling_validated_by_general_guard_sweep":
        return [
            "Treat the current-evidence ceiling as plausible enough for a focused runtime-policy design pass.",
            "Confirm the best guard on a separate locked suite before any production-policy claim.",
        ]
    return [
        "Do not treat the optimistic 46/48 current-evidence ceiling as validated.",
        "Use the no-regression policy as a diagnostic: it shows partial phrase/no-winner headroom but leaves harmful replacements.",
        "Move upstream for the remaining gap: raw-source, evidence representation, scoring, and LLM-pipeline bound work.",
    ]


def _decision_error_type(*, gold: str, predicted: str) -> str:
    if predicted == gold:
        return ""
    if predicted == "replace" and gold != "replace":
        return "harmful_replace"
    if predicted != "replace" and gold == "replace":
        return "false_abstain"
    return "other_mismatch"


def _gold_signal_score_visible(row: Mapping[str, object]) -> bool:
    suite_id = str(row.get("suite_id") or "").strip()
    gold_decision = str(row.get("gold_decision") or "").strip()
    active_score = _safe_float(row.get("active_score"))
    shadow_score = _safe_float(row.get("strongest_shadow_score"))
    phrase_score = _safe_float(row.get("phrase_control_score"))
    if gold_decision == "replace":
        return active_score > max(shadow_score, phrase_score)
    if suite_id == "phrase_no_winner":
        return phrase_score >= max(active_score, shadow_score)
    return max(shadow_score, phrase_score) >= active_score


def _report_ref(report: Mapping[str, object], path: Path | None) -> dict[str, object]:
    summary = _as_mapping(report.get("summary"))
    return {
        "path": _repo_path(path),
        "status": str(report.get("status") or ""),
        "decision": str(report.get("decision") or ""),
        "heldout_dataset_id": str(report.get("heldout_dataset_id") or ""),
        "heldout_case_scope": str(report.get("heldout_case_scope") or ""),
        "case_count": int(summary.get("case_count") or 0),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
    }


def _policy_table(value: object) -> str:
    if isinstance(value, Mapping):
        if "policy_id" in value:
            rows = [_as_mapping(value)]
        else:
            rows = [row for row in value.values() if isinstance(row, Mapping)]
    else:
        rows = _mapping_rows(value)
    if not rows:
        return "No policies."
    lines = [
        "| Policy | Correct | Harm | False Abstain | Fixed | Regressed | Changed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_policy_label(row)}`",
                    str(row.get("correct_case_count", 0)),
                    str(row.get("harmful_replace_count", 0)),
                    str(row.get("false_abstain_count", 0)),
                    str(row.get("fixed_residual_count", 0)),
                    str(row.get("regressed_case_count", 0)),
                    str(row.get("changed_case_count", 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _policy_label(row: Mapping[str, object]) -> str:
    return str(row.get("policy_id") or _as_mapping(row.get("policy")).get("policy_id") or "")


def _load_json(path: Path) -> Mapping[str, object]:
    return _as_mapping(json.loads(path.read_text(encoding="utf-8")))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    return [row for row in _as_sequence(value) if isinstance(row, Mapping)]


def _safe_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
