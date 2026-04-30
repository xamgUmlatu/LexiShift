#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_RESIDUAL_PROBE_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_wave7_residual_blocker_probe_wave7_source_class_breadth_v1_"
    "phrase_control_triage_latest.json"
)
DEFAULT_ADMISSION_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_source_admission_cycle_wave7_source_class_breadth_v1_"
    "phrase_control_triage_latest.json"
)
DEFAULT_FRAME_EVIDENCE_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / ("semantic_veto_bound_ladder_wave7_residuals_latest.json")
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / ("semantic_veto_bound_ladder_wave7_residuals_latest.md")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a research-only semantic-veto bound ladder over the current "
            "wave7 residual blocker probe. This script does not gate promotion "
            "or change runtime policy."
        )
    )
    parser.add_argument("--residual-probe-json", type=Path, default=DEFAULT_RESIDUAL_PROBE_JSON)
    parser.add_argument("--admission-json", type=Path, default=DEFAULT_ADMISSION_JSON)
    parser.add_argument("--frame-evidence-json", type=Path, default=DEFAULT_FRAME_EVIDENCE_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    residual_probe = _load_json(args.residual_probe_json)
    admission_report = _load_optional_json(args.admission_json)
    frame_evidence_report = _load_optional_json(args.frame_evidence_json)
    report = build_bound_ladder_report(
        residual_probe=residual_probe,
        admission_report=admission_report,
        frame_evidence_report=frame_evidence_report,
        residual_probe_path=args.residual_probe_json,
        admission_report_path=args.admission_json,
        frame_evidence_report_path=args.frame_evidence_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_bound_ladder_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_bound_ladder_report(
    *,
    residual_probe: Mapping[str, object],
    admission_report: Mapping[str, object] | None = None,
    frame_evidence_report: Mapping[str, object] | None = None,
    residual_probe_path: Path | None = None,
    admission_report_path: Path | None = None,
    frame_evidence_report_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    cases = [_case_bound_row(row) for row in _mapping_rows(residual_probe.get("residual_cases"))]
    lower = _lower_bound(residual_probe=residual_probe, residual_cases=cases)
    current_evidence = _current_evidence_bound(lower_bound=lower, residual_cases=cases)
    admitted_evidence = _admitted_evidence_bound(residual_cases=cases)
    oracle = _oracle_evidence_bound(lower_bound=lower, residual_cases=cases)
    policy = _runtime_policy_bound(residual_probe=residual_probe)
    llm = _llm_pipeline_bound()
    admission_summary = _admission_summary(admission_report, admission_report_path)
    frame_summary = _frame_evidence_summary(frame_evidence_report, frame_evidence_report_path)
    decision = _decision(
        lower_bound=lower,
        current_evidence_bound=current_evidence,
        runtime_policy_bound=policy,
        llm_pipeline_bound=llm,
    )
    return {
        "schema_version": 1,
        "status": "review",
        "decision": decision,
        "generated_at": generated_at,
        "research_only": True,
        "source_reports": {
            "residual_probe": {
                "path": _repo_path(residual_probe_path),
                "status": str(residual_probe.get("status") or ""),
                "decision": str(residual_probe.get("decision") or ""),
            },
            "admission_report": admission_summary,
            "frame_evidence_report": frame_summary,
        },
        "bounds": {
            "end_to_end_lower_bound": lower,
            "current_evidence_upper_bound": current_evidence,
            "admitted_evidence_presence_bound": admitted_evidence,
            "runtime_policy_family_bound": policy,
            "llm_pipeline_bound": llm,
            "oracle_evidence_bound": oracle,
        },
        "summary": _summary(
            lower_bound=lower,
            current_evidence_bound=current_evidence,
            admitted_evidence_bound=admitted_evidence,
            runtime_policy_bound=policy,
            oracle_evidence_bound=oracle,
            cases=cases,
        ),
        "case_bounds": cases,
        "next_steps": _next_steps(
            current_evidence_bound=current_evidence,
            admitted_evidence_bound=admitted_evidence,
            runtime_policy_bound=policy,
        ),
        "limitations": [
            "research_only_not_quality_gate",
            "uses_existing_wave7_residual_artifacts_only",
            "llm_pipeline_not_measured",
            "oracle_evidence_bound_is_diagnostic_not_promotion_evidence",
            "score_visibility_is_a_heuristic_not_a_formal_language_bound",
        ],
    }


def render_bound_ladder_markdown(report: Mapping[str, object]) -> str:
    bounds = _as_mapping(report.get("bounds"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Bound Ladder: Wave7 Residuals",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Research only: `{str(report.get('research_only', False)).lower()}`",
        "",
        "## Summary",
        "",
        f"- Locked cases: `{summary.get('locked_case_count', 0)}`",
        f"- Current correct cases: `{summary.get('current_correct_case_count', 0)}`",
        f"- Current accuracy: `{_format_percent(summary.get('current_accuracy', 0.0))}`",
        f"- Current harmful replacements: `{summary.get('current_harmful_replace_count', 0)}`",
        f"- Current false abstains: `{summary.get('current_false_abstain_count', 0)}`",
        f"- Score-visible residuals: `{summary.get('score_visible_residual_count', 0)}`",
        f"- Residuals likely needing better evidence/scoring: "
        f"`{summary.get('not_score_visible_residual_count', 0)}`",
        f"- Existing runtime-shaped sweep pass count: "
        f"`{summary.get('runtime_policy_family_passing_count', 0)}`",
        "",
        "## Bound Ladder",
        "",
        _bound_table(bounds),
        "",
        "## Case Bounds",
        "",
        _case_table(report.get("case_bounds")),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(summary.get("interpretation")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _case_bound_row(row: Mapping[str, object]) -> dict[str, object]:
    suite_id = str(row.get("suite_id") or "").strip()
    gold_decision = str(row.get("gold_decision") or "").strip()
    active_score = _safe_float(row.get("active_score"))
    shadow_score = _safe_float(row.get("strongest_shadow_score"))
    phrase_score = _safe_float(row.get("phrase_control_score"))
    score_visible = _gold_signal_score_visible(
        suite_id=suite_id,
        gold_decision=gold_decision,
        active_score=active_score,
        shadow_score=shadow_score,
        phrase_score=phrase_score,
    )
    required_evidence = _required_evidence(row=row, suite_id=suite_id, gold_decision=gold_decision)
    evidence_present = bool(str(required_evidence["text"]).strip())
    representation = _representation_status(
        evidence_present=evidence_present,
        score_visible=score_visible,
        suite_id=suite_id,
    )
    return {
        "case_id": str(row.get("case_id") or "").strip(),
        "suite_id": suite_id,
        "trigger": str(row.get("trigger") or "").strip(),
        "sentence": str(row.get("sentence") or "").strip(),
        "failure_class": str(row.get("failure_class") or "").strip(),
        "remediation_lane": str(row.get("remediation_lane") or "").strip(),
        "decision_error_type": str(row.get("decision_error_type") or "").strip(),
        "gold_decision": gold_decision,
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "active_score": active_score,
        "strongest_shadow_score": shadow_score,
        "phrase_control_score": phrase_score,
        "score_visible_for_gold": score_visible,
        "score_visibility_reason": _score_visibility_reason(
            suite_id=suite_id,
            gold_decision=gold_decision,
            score_visible=score_visible,
        ),
        "required_evidence_lane": required_evidence["lane"],
        "required_evidence_text": required_evidence["text"],
        "admitted_gold_evidence_present": evidence_present,
        "representation_status": representation,
        "current_evidence_bound_read": (
            "potentially_recoverable_by_better_rule_or_guard"
            if score_visible
            else "likely_needs_better_evidence_scoring_or_aggregation"
        ),
        "llm_evidence_opportunity": _llm_opportunity(
            score_visible=score_visible,
            evidence_present=evidence_present,
            suite_id=suite_id,
        ),
        "oracle_evidence_likely_fixable": True,
    }


def _lower_bound(
    *,
    residual_probe: Mapping[str, object],
    residual_cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    score_surface = _as_mapping(residual_probe.get("score_surface"))
    active_report = _as_mapping(score_surface.get("active_report"))
    phrase_report = _as_mapping(score_surface.get("phrase_report"))
    active_cases = int(active_report.get("case_count") or 0)
    phrase_cases = int(phrase_report.get("case_count") or 0)
    if active_cases + phrase_cases <= 0:
        summary = _as_mapping(residual_probe.get("summary"))
        active_cases = int(summary.get("active_shadow_failure_count") or 0)
        phrase_cases = int(summary.get("phrase_no_winner_failure_count") or 0)
    locked_cases = active_cases + phrase_cases
    harmful = int(active_report.get("harmful_replace_count") or 0) + int(
        phrase_report.get("harmful_replace_count") or 0
    )
    false_abstain = int(active_report.get("false_abstain_count") or 0) + int(
        phrase_report.get("false_abstain_count") or 0
    )
    if harmful + false_abstain <= 0:
        harmful = sum(
            1 for case in residual_cases if case["decision_error_type"] == "harmful_replace"
        )
        false_abstain = sum(
            1 for case in residual_cases if case["decision_error_type"] == "false_abstain"
        )
    residual_count = len(residual_cases)
    correct = max(0, locked_cases - residual_count)
    return {
        "bound_type": "observed_lower_bound",
        "locked_case_count": locked_cases,
        "current_correct_case_count": correct,
        "current_accuracy": _safe_ratio(correct, locked_cases),
        "current_residual_case_count": residual_count,
        "current_harmful_replace_count": harmful,
        "current_false_abstain_count": false_abstain,
        "interpretation": (
            "This is the best actually observed current wave7 phrase-control triage result, "
            "not a production acceptance target."
        ),
    }


def _current_evidence_bound(
    *,
    lower_bound: Mapping[str, object],
    residual_cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    score_visible = [case for case in residual_cases if bool(case.get("score_visible_for_gold"))]
    not_visible = [case for case in residual_cases if not bool(case.get("score_visible_for_gold"))]
    locked_cases = int(lower_bound.get("locked_case_count") or 0)
    current_correct = int(lower_bound.get("current_correct_case_count") or 0)
    optimistic_correct = min(locked_cases, current_correct + len(score_visible))
    return {
        "bound_type": "heuristic_current_evidence_upper_bound",
        "score_visible_residual_count": len(score_visible),
        "not_score_visible_residual_count": len(not_visible),
        "score_visible_case_ids": [str(case.get("case_id") or "") for case in score_visible],
        "not_score_visible_case_ids": [str(case.get("case_id") or "") for case in not_visible],
        "optimistic_correct_case_count": optimistic_correct,
        "optimistic_accuracy_if_all_score_visible_residuals_are_safely_recovered": _safe_ratio(
            optimistic_correct,
            locked_cases,
        ),
        "interpretation": (
            "This is an optimistic score-visibility ceiling. It assumes a future rule can "
            "recover all score-visible residuals without causing regressions. Existing "
            "wave7 sweeps do not prove such a rule exists."
        ),
    }


def _admitted_evidence_bound(residual_cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    present = [case for case in residual_cases if bool(case.get("admitted_gold_evidence_present"))]
    missing = [
        case for case in residual_cases if not bool(case.get("admitted_gold_evidence_present"))
    ]
    return {
        "bound_type": "admitted_evidence_presence_bound",
        "residual_case_count": len(residual_cases),
        "admitted_gold_evidence_present_count": len(present),
        "admitted_gold_evidence_missing_count": len(missing),
        "missing_case_ids": [str(case.get("case_id") or "") for case in missing],
        "representation_status_counts": dict(
            sorted(
                Counter(
                    str(case.get("representation_status") or "") for case in residual_cases
                ).items()
            )
        ),
        "interpretation": (
            "This checks whether a relevant admitted evidence field is non-empty. It is not "
            "a raw-source inventory audit and it does not prove the wording is strong enough."
        ),
    }


def _runtime_policy_bound(residual_probe: Mapping[str, object]) -> dict[str, object]:
    policy_context = _as_mapping(residual_probe.get("policy_context"))
    policy_summary = _as_mapping(policy_context.get("summary"))
    rescue = _as_mapping(policy_context.get("rescue_sweep"))
    margin = _as_mapping(policy_context.get("no_surface_margin_sweep"))
    passing = int(policy_summary.get("combined_passing_policy_count") or 0)
    return {
        "bound_type": "measured_runtime_policy_family_bound",
        "combined_passing_policy_count": passing,
        "rescue_sweep_passing_policy_count": int(rescue.get("passing_policy_count") or 0),
        "no_surface_margin_sweep_passing_policy_count": int(
            margin.get("passing_policy_count") or 0
        ),
        "scope": "existing_wave7_rescue_and_no_surface_margin_sweeps",
        "interpretation": (
            "The tested runtime-shaped policy families have no combined pass. This is a "
            "negative signal for simple scalar tuning, not a formal proof over all possible "
            "runtime-compatible policies."
        ),
    }


def _llm_pipeline_bound() -> dict[str, object]:
    return {
        "bound_type": "llm_pipeline_bound",
        "status": "not_measured",
        "measured_case_count": 0,
        "interpretation": (
            "Planned LLM-generated evidence is not included in the current bound value. "
            "Measure it separately with locked cases, generation prompts, admission, leakage "
            "filters, sense checks, scoring, and downstream validation all included."
        ),
    }


def _oracle_evidence_bound(
    *,
    lower_bound: Mapping[str, object],
    residual_cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    locked_cases = int(lower_bound.get("locked_case_count") or 0)
    current_correct = int(lower_bound.get("current_correct_case_count") or 0)
    likely_fixable = [
        case for case in residual_cases if bool(case.get("oracle_evidence_likely_fixable"))
    ]
    optimistic_correct = min(locked_cases, current_correct + len(likely_fixable))
    return {
        "bound_type": "diagnostic_oracle_evidence_bound",
        "likely_fixable_residual_count": len(likely_fixable),
        "likely_fixable_case_ids": [str(case.get("case_id") or "") for case in likely_fixable],
        "optimistic_correct_case_count": optimistic_correct,
        "optimistic_accuracy_if_oracle_evidence_and_guarding_solve_residuals": _safe_ratio(
            optimistic_correct,
            locked_cases,
        ),
        "interpretation": (
            "This is diagnostic only. It says the residuals look evidence/guard-fixable, "
            "but it does not prove the planned LLM pipeline can generate the needed rows."
        ),
    }


def _admission_summary(
    report: Mapping[str, object] | None,
    path: Path | None,
) -> dict[str, object]:
    payload = _as_mapping(report)
    summary = _as_mapping(payload.get("summary"))
    return {
        "path": _repo_path(path),
        "status": str(payload.get("status") or ""),
        "decision": str(payload.get("decision") or ""),
        "final_admitted_row_count": int(summary.get("final_admitted_row_count") or 0),
        "leakage_rejected_row_count": int(summary.get("leakage_rejected_row_count") or 0),
        "sense_rejected_row_count": int(summary.get("sense_rejected_row_count") or 0),
        "semantic_contract_complete_family_count": int(
            summary.get("semantic_contract_complete_family_count") or 0
        ),
        "phrase_contract_complete_family_count": int(
            summary.get("phrase_contract_complete_family_count") or 0
        ),
    }


def _frame_evidence_summary(
    report: Mapping[str, object] | None,
    path: Path | None,
) -> dict[str, object]:
    payload = _as_mapping(report)
    summary = _as_mapping(payload.get("summary"))
    return {
        "path": _repo_path(path),
        "status": str(payload.get("status") or ""),
        "decision": str(payload.get("decision") or ""),
        "family_count": int(summary.get("family_count") or 0),
        "matching_sense_count": int(summary.get("matching_sense_count") or 0),
        "row_count": int(summary.get("row_count") or 0),
    }


def _summary(
    *,
    lower_bound: Mapping[str, object],
    current_evidence_bound: Mapping[str, object],
    admitted_evidence_bound: Mapping[str, object],
    runtime_policy_bound: Mapping[str, object],
    oracle_evidence_bound: Mapping[str, object],
    cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    current_accuracy = _safe_float(lower_bound.get("current_accuracy"))
    score_visible = int(current_evidence_bound.get("score_visible_residual_count") or 0)
    not_visible = int(current_evidence_bound.get("not_score_visible_residual_count") or 0)
    interpretation = [
        (
            "The current wave7 result is a lower bound, not an acceptable target: "
            f"{lower_bound.get('current_harmful_replace_count', 0)} harmful replacements "
            f"and {lower_bound.get('current_false_abstain_count', 0)} false abstains remain."
        ),
        (
            f"{score_visible} residuals have the gold signal visible in current scores; "
            "these are candidates for guard or decision-rule repair."
        ),
        (
            f"{not_visible} residuals do not expose the gold signal under the current "
            "score shape; these point toward better evidence, scoring, or aggregation."
        ),
        (
            "The LLM pipeline bound is intentionally not measured yet, so generated data "
            "should not be counted in the current acceptance target."
        ),
    ]
    return {
        "locked_case_count": int(lower_bound.get("locked_case_count") or 0),
        "current_correct_case_count": int(lower_bound.get("current_correct_case_count") or 0),
        "current_accuracy": current_accuracy,
        "current_harmful_replace_count": int(lower_bound.get("current_harmful_replace_count") or 0),
        "current_false_abstain_count": int(lower_bound.get("current_false_abstain_count") or 0),
        "residual_case_count": len(cases),
        "score_visible_residual_count": score_visible,
        "not_score_visible_residual_count": not_visible,
        "admitted_gold_evidence_present_count": int(
            admitted_evidence_bound.get("admitted_gold_evidence_present_count") or 0
        ),
        "runtime_policy_family_passing_count": int(
            runtime_policy_bound.get("combined_passing_policy_count") or 0
        ),
        "oracle_likely_fixable_residual_count": int(
            oracle_evidence_bound.get("likely_fixable_residual_count") or 0
        ),
        "failure_class_counts": dict(
            sorted(Counter(str(case.get("failure_class") or "") for case in cases).items())
        ),
        "interpretation": interpretation,
    }


def _next_steps(
    *,
    current_evidence_bound: Mapping[str, object],
    admitted_evidence_bound: Mapping[str, object],
    runtime_policy_bound: Mapping[str, object],
) -> list[str]:
    steps = [
        "Treat the current wave7 result as the observed lower bound, not the acceptable goal.",
        "Keep LLM-generated evidence out of acceptance estimates until an LLM-pipeline bound is run.",
    ]
    if int(runtime_policy_bound.get("combined_passing_policy_count") or 0) <= 0:
        steps.append(
            "Do not claim scalar policy tuning can close the gap; existing runtime-shaped sweeps have zero combined passing policies."
        )
    if int(current_evidence_bound.get("not_score_visible_residual_count") or 0) > 0:
        steps.append(
            "Prioritize evidence/scorer work for residuals whose gold signal is not visible in current scores."
        )
    if int(admitted_evidence_bound.get("admitted_gold_evidence_missing_count") or 0) <= 0:
        steps.append(
            "Run a deeper raw-source and representation audit before assuming the problem is missing source coverage."
        )
    steps.append(
        "Prototype the LLM-pipeline bound separately: generate evidence on locked residual cases, run admission and leakage checks, then rerun heldout validation."
    )
    return steps


def _decision(
    *,
    lower_bound: Mapping[str, object],
    current_evidence_bound: Mapping[str, object],
    runtime_policy_bound: Mapping[str, object],
    llm_pipeline_bound: Mapping[str, object],
) -> str:
    if str(llm_pipeline_bound.get("status") or "") == "not_measured":
        return "bounds_reference_only_llm_lane_unmeasured"
    if int(runtime_policy_bound.get("combined_passing_policy_count") or 0) <= 0:
        return "current_policy_family_ceiling_below_acceptance"
    if int(current_evidence_bound.get("not_score_visible_residual_count") or 0) > 0:
        return "current_evidence_bound_requires_upstream_work"
    if int(lower_bound.get("current_harmful_replace_count") or 0) > 0:
        return "observed_lower_bound_below_acceptance"
    return "bounds_ready_for_acceptance_discussion"


def _required_evidence(
    *,
    row: Mapping[str, object],
    suite_id: str,
    gold_decision: str,
) -> dict[str, str]:
    if gold_decision == "replace":
        return {
            "lane": "active",
            "text": str(row.get("active_evidence_text") or "").strip(),
        }
    if suite_id == "phrase_no_winner":
        return {
            "lane": "phrase_control",
            "text": str(row.get("phrase_control_evidence_text") or "").strip(),
        }
    return {
        "lane": "shadow",
        "text": str(row.get("strongest_shadow_evidence_text") or "").strip(),
    }


def _gold_signal_score_visible(
    *,
    suite_id: str,
    gold_decision: str,
    active_score: float,
    shadow_score: float,
    phrase_score: float,
) -> bool:
    if gold_decision == "replace":
        return active_score > max(shadow_score, phrase_score)
    if suite_id == "phrase_no_winner":
        return phrase_score >= max(active_score, shadow_score)
    return max(shadow_score, phrase_score) >= active_score


def _score_visibility_reason(
    *,
    suite_id: str,
    gold_decision: str,
    score_visible: bool,
) -> str:
    if gold_decision == "replace":
        return (
            "active_score_beats_competitors" if score_visible else "active_score_under_competitors"
        )
    if suite_id == "phrase_no_winner":
        return "phrase_score_beats_best_sense" if score_visible else "phrase_score_under_best_sense"
    return "shadow_or_phrase_beats_active" if score_visible else "active_score_beats_abstain_signal"


def _representation_status(
    *,
    evidence_present: bool,
    score_visible: bool,
    suite_id: str,
) -> str:
    if not evidence_present:
        return "gold_evidence_missing_from_admitted_rows"
    if score_visible and suite_id == "phrase_no_winner":
        return "phrase_signal_present_but_guard_failed"
    if score_visible:
        return "score_visible_but_policy_failed"
    return "evidence_present_but_not_score_visible"


def _llm_opportunity(
    *,
    score_visible: bool,
    evidence_present: bool,
    suite_id: str,
) -> str:
    if not evidence_present:
        return "generate_missing_gold_evidence"
    if suite_id == "phrase_no_winner":
        return "generate_exact_no_winner_phrase_evidence_and_guard_examples"
    if score_visible:
        return "generation_may_help_but_policy_guard_is_primary"
    return "generate_stronger_contrastive_active_shadow_evidence"


def _bound_table(bounds: Mapping[str, object]) -> str:
    lines = [
        "| Bound | Value | Meaning |",
        "| --- | --- | --- |",
    ]
    for key in (
        "end_to_end_lower_bound",
        "current_evidence_upper_bound",
        "admitted_evidence_presence_bound",
        "runtime_policy_family_bound",
        "llm_pipeline_bound",
        "oracle_evidence_bound",
    ):
        row = _as_mapping(bounds.get(key))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{key}`",
                    _bound_value(key, row),
                    _md_text(row.get("interpretation")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _bound_value(key: str, row: Mapping[str, object]) -> str:
    if key == "end_to_end_lower_bound":
        return (
            f"`{_format_percent(row.get('current_accuracy'))}` accuracy, "
            f"`{row.get('current_harmful_replace_count', 0)}` harm, "
            f"`{row.get('current_false_abstain_count', 0)}` false abstain"
        )
    if key == "current_evidence_upper_bound":
        return f"`{_format_percent(row.get('optimistic_accuracy_if_all_score_visible_residuals_are_safely_recovered'))}` optimistic"
    if key == "admitted_evidence_presence_bound":
        return (
            f"`{row.get('admitted_gold_evidence_present_count', 0)}` / "
            f"`{row.get('residual_case_count', 0)}` residuals have admitted gold-lane evidence"
        )
    if key == "runtime_policy_family_bound":
        return f"`{row.get('combined_passing_policy_count', 0)}` combined passing policies"
    if key == "llm_pipeline_bound":
        return f"`{row.get('status', 'unknown')}`"
    if key == "oracle_evidence_bound":
        return f"`{_format_percent(row.get('optimistic_accuracy_if_oracle_evidence_and_guarding_solve_residuals'))}` diagnostic optimistic"
    return ""


def _case_table(value: object) -> str:
    cases = _mapping_rows(value)
    if not cases:
        return "No residual cases."
    lines = [
        "| Case | Error | Class | Evidence Lane | Evidence Present | Score Visible | Representation | LLM Opportunity |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in cases:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('decision_error_type', '')}`",
                    f"`{row.get('failure_class', '')}`",
                    f"`{row.get('required_evidence_lane', '')}`",
                    f"`{str(bool(row.get('admitted_gold_evidence_present'))).lower()}`",
                    f"`{str(bool(row.get('score_visible_for_gold'))).lower()}`",
                    f"`{row.get('representation_status', '')}`",
                    f"`{row.get('llm_evidence_opportunity', '')}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _load_json(path: Path) -> Mapping[str, object]:
    return _as_mapping(json.loads(path.read_text(encoding="utf-8")))


def _load_optional_json(path: Path) -> Mapping[str, object] | None:
    if not path.exists():
        return None
    return _load_json(path)


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


def _format_percent(value: object) -> str:
    return f"{_safe_float(value) * 100:.2f}%"


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _md_text(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
