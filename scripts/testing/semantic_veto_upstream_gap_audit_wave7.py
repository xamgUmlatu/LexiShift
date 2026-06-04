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
DEFAULT_BOUND_LADDER_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_veto_bound_ladder_wave7_residuals_latest.json"
)
DEFAULT_CEILING_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_veto_current_evidence_ceiling_wave7_latest.json"
)
DEFAULT_FRAME_EVIDENCE_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.json"
)
DEFAULT_PHRASE_EVIDENCE_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_wordnet_alternate_sense_phrase_wave7_source_class_breadth_v1_triage_latest.json"
)
DEFAULT_ADMISSION_JSON = TEST_OUTPUTS_ROOT / (
    "semantic_source_admission_cycle_wave7_source_class_breadth_v1_"
    "phrase_control_triage_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_upstream_gap_audit_wave7_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_upstream_gap_audit_wave7_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify wave7 semantic-veto residuals after the current-evidence "
            "ceiling sweep. This is a research-only upstream gap audit: it does "
            "not change runtime policy and does not generate new evidence."
        )
    )
    parser.add_argument("--residual-probe-json", type=Path, default=DEFAULT_RESIDUAL_PROBE_JSON)
    parser.add_argument("--bound-ladder-json", type=Path, default=DEFAULT_BOUND_LADDER_JSON)
    parser.add_argument("--ceiling-json", type=Path, default=DEFAULT_CEILING_JSON)
    parser.add_argument("--frame-evidence-json", type=Path, default=DEFAULT_FRAME_EVIDENCE_JSON)
    parser.add_argument("--phrase-evidence-json", type=Path, default=DEFAULT_PHRASE_EVIDENCE_JSON)
    parser.add_argument("--admission-json", type=Path, default=DEFAULT_ADMISSION_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_upstream_gap_audit_report(
        residual_probe=_load_json(args.residual_probe_json),
        bound_ladder=_load_json(args.bound_ladder_json),
        current_evidence_ceiling=_load_json(args.ceiling_json),
        frame_evidence=_load_optional_json(args.frame_evidence_json),
        phrase_evidence=_load_optional_json(args.phrase_evidence_json),
        admission_report=_load_optional_json(args.admission_json),
        residual_probe_path=args.residual_probe_json,
        bound_ladder_path=args.bound_ladder_json,
        current_evidence_ceiling_path=args.ceiling_json,
        frame_evidence_path=args.frame_evidence_json,
        phrase_evidence_path=args.phrase_evidence_json,
        admission_report_path=args.admission_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_upstream_gap_audit_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_upstream_gap_audit_report(
    *,
    residual_probe: Mapping[str, object],
    bound_ladder: Mapping[str, object],
    current_evidence_ceiling: Mapping[str, object],
    frame_evidence: Mapping[str, object] | None = None,
    phrase_evidence: Mapping[str, object] | None = None,
    admission_report: Mapping[str, object] | None = None,
    residual_probe_path: Path | None = None,
    bound_ladder_path: Path | None = None,
    current_evidence_ceiling_path: Path | None = None,
    frame_evidence_path: Path | None = None,
    phrase_evidence_path: Path | None = None,
    admission_report_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    bound_by_case = {
        str(row.get("case_id") or ""): row for row in _mapping_rows(bound_ladder.get("case_bounds"))
    }
    frame_by_trigger = _family_rows_by_trigger(frame_evidence)
    phrase_by_trigger = _family_rows_by_trigger(phrase_evidence)
    best_no_regression = _as_mapping(
        _as_mapping(current_evidence_ceiling.get("representative_policies")).get(
            "best_no_regression"
        )
    )
    best_zero_harm = _as_mapping(
        _as_mapping(current_evidence_ceiling.get("representative_policies")).get("best_zero_harm")
    )
    case_rows = [
        _audit_case(
            row=row,
            bound_case=bound_by_case.get(str(row.get("case_id") or ""), {}),
            best_no_regression=best_no_regression,
            best_zero_harm=best_zero_harm,
            frame_family=frame_by_trigger.get(str(row.get("trigger") or "")),
            phrase_family=phrase_by_trigger.get(str(row.get("trigger") or "")),
        )
        for row in _mapping_rows(residual_probe.get("residual_cases"))
    ]
    summary = _summary(
        cases=case_rows,
        current_evidence_ceiling=current_evidence_ceiling,
        admission_report=admission_report,
        frame_evidence=frame_evidence,
        phrase_evidence=phrase_evidence,
    )
    return {
        "schema_version": 1,
        "status": "review",
        "decision": summary["decision"],
        "generated_at": generated_at,
        "research_only": True,
        "source_reports": {
            "residual_probe": _source_ref(residual_probe, residual_probe_path),
            "bound_ladder": _source_ref(bound_ladder, bound_ladder_path),
            "current_evidence_ceiling": _source_ref(
                current_evidence_ceiling,
                current_evidence_ceiling_path,
            ),
            "frame_evidence": _source_ref(frame_evidence, frame_evidence_path),
            "phrase_evidence": _source_ref(phrase_evidence, phrase_evidence_path),
            "admission_report": _source_ref(admission_report, admission_report_path),
        },
        "summary": summary,
        "case_audits": case_rows,
        "class_summaries": _class_summaries(case_rows),
        "next_steps": _next_steps(summary=summary),
        "limitations": [
            "research_only_not_promotion_evidence",
            "raw_source_availability_is_inferred_from_existing_source_reports",
            "does_not_run_new_scorers_or_generate_new_llm_rows",
            "case_classification_is_for_work_routing_not_runtime_policy",
        ],
    }


def render_upstream_gap_audit_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Wave7 Upstream Gap Audit",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Research only: `{str(report.get('research_only', False)).lower()}`",
        "",
        "## Summary",
        "",
        f"- Residual cases audited: `{summary.get('residual_case_count', 0)}`",
        f"- Fixed by best no-regression guard: "
        f"`{summary.get('fixed_by_best_no_regression_count', 0)}`",
        f"- Still failing after best no-regression guard: "
        f"`{summary.get('still_failing_after_best_no_regression_count', 0)}`",
        f"- Current-evidence ceiling status: "
        f"`{summary.get('current_evidence_ceiling_status', '')}`",
        f"- Admission rows: `{summary.get('final_admitted_row_count', 0)}`",
        f"- Source-class frame rows: `{summary.get('source_class_frame_row_count', 0)}`",
        f"- Phrase-control candidate rows: `{summary.get('phrase_control_source_row_count', 0)}`",
        "",
        "## Bottleneck Counts",
        "",
        _count_table(summary.get("bottleneck_counts")),
        "",
        "## Class Summaries",
        "",
        _class_table(report.get("class_summaries")),
        "",
        "## Case Audits",
        "",
        _case_table(report.get("case_audits")),
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


def _audit_case(
    *,
    row: Mapping[str, object],
    bound_case: Mapping[str, object],
    best_no_regression: Mapping[str, object],
    best_zero_harm: Mapping[str, object],
    frame_family: Mapping[str, object] | None,
    phrase_family: Mapping[str, object] | None,
) -> dict[str, object]:
    case_id = str(row.get("case_id") or "").strip()
    score_visible = bool(bound_case.get("score_visible_for_gold"))
    fixed_by_no_regression = case_id in {
        str(value) for value in _as_sequence(best_no_regression.get("fixed_case_ids"))
    }
    fixed_by_zero_harm = case_id in {
        str(value) for value in _as_sequence(best_zero_harm.get("fixed_case_ids"))
    }
    family_source = _family_source_summary(frame_family, phrase_family)
    bottleneck = _bottleneck(
        row=row,
        bound_case=bound_case,
        fixed_by_no_regression=fixed_by_no_regression,
        fixed_by_zero_harm=fixed_by_zero_harm,
        family_source=family_source,
    )
    return {
        "case_id": case_id,
        "suite_id": str(row.get("suite_id") or "").strip(),
        "trigger": str(row.get("trigger") or "").strip(),
        "sentence": str(row.get("sentence") or "").strip(),
        "failure_class": str(row.get("failure_class") or "").strip(),
        "decision_error_type": str(row.get("decision_error_type") or "").strip(),
        "gold_decision": str(row.get("gold_decision") or "").strip(),
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "score_visible_for_gold": score_visible,
        "required_evidence_lane": str(bound_case.get("required_evidence_lane") or ""),
        "representation_status": str(bound_case.get("representation_status") or ""),
        "llm_evidence_opportunity": str(bound_case.get("llm_evidence_opportunity") or ""),
        "fixed_by_best_no_regression_guard": fixed_by_no_regression,
        "fixed_by_zero_harm_guard": fixed_by_zero_harm,
        "bottleneck": bottleneck["bottleneck"],
        "bottleneck_reason": bottleneck["reason"],
        "recommended_next_action": bottleneck["next_action"],
        "active_score": _safe_float(row.get("active_score")),
        "strongest_shadow_score": _safe_float(row.get("strongest_shadow_score")),
        "phrase_control_score": _safe_float(row.get("phrase_control_score")),
        "active_evidence_text": str(row.get("active_evidence_text") or "").strip(),
        "strongest_shadow_evidence_text": str(
            row.get("strongest_shadow_evidence_text") or ""
        ).strip(),
        "phrase_control_evidence_text": str(row.get("phrase_control_evidence_text") or "").strip(),
        "source_summary": family_source,
    }


def _bottleneck(
    *,
    row: Mapping[str, object],
    bound_case: Mapping[str, object],
    fixed_by_no_regression: bool,
    fixed_by_zero_harm: bool,
    family_source: Mapping[str, object],
) -> dict[str, str]:
    suite_id = str(row.get("suite_id") or "")
    failure_class = str(row.get("failure_class") or "")
    score_visible = bool(bound_case.get("score_visible_for_gold"))
    if fixed_by_no_regression:
        return {
            "bottleneck": "general_guard_headroom_confirmed",
            "reason": "The best no-regression guard fixes this residual using current scores.",
            "next_action": "Keep as diagnostic headroom and confirm on a broader locked suite before policy promotion.",
        }
    if not score_visible:
        return {
            "bottleneck": "evidence_representation_or_scorer_gap",
            "reason": "The gold lane has admitted text, but the current score trace does not make it win.",
            "next_action": "Audit raw source wording and try stronger contrastive evidence or scorer aggregation before policy tuning.",
        }
    if fixed_by_zero_harm and suite_id == "phrase_no_winner":
        return {
            "bottleneck": "guard_signal_collides_with_valid_active_replace",
            "reason": "Abstain guards can fix this phrase/no-winner residual, but the zero-harm policy regresses active replace cases.",
            "next_action": "Improve phrase/no-winner evidence specificity or add a separately validated no-winner guard signal.",
        }
    if failure_class == "shadow_quantity_evidence_underweighted":
        return {
            "bottleneck": "shadow_signal_visible_but_guard_threshold_insufficient",
            "reason": "Quantity shadow evidence is visible, but a no-regression guard does not safely catch it.",
            "next_action": "Strengthen quantity/commercial source evidence or test a non-trigger-specific quantity-frame feature.",
        }
    return {
        "bottleneck": "score_visible_but_not_safely_recoverable",
        "reason": "The gold signal is visible, but current general guards either miss it or cause regressions.",
        "next_action": "Move upstream to evidence representation or add a new general feature before more scalar sweeps.",
    }


def _summary(
    *,
    cases: Sequence[Mapping[str, object]],
    current_evidence_ceiling: Mapping[str, object],
    admission_report: Mapping[str, object] | None,
    frame_evidence: Mapping[str, object] | None,
    phrase_evidence: Mapping[str, object] | None,
) -> dict[str, object]:
    ceiling_assessment = _as_mapping(
        _as_mapping(current_evidence_ceiling.get("summary")).get("ceiling_assessment")
    )
    admission_summary = _as_mapping(_as_mapping(admission_report).get("summary"))
    frame_summary = _as_mapping(_as_mapping(frame_evidence).get("summary"))
    phrase_summary = _as_mapping(_as_mapping(phrase_evidence).get("summary"))
    bottleneck_counts = dict(
        sorted(Counter(str(case.get("bottleneck") or "") for case in cases).items())
    )
    fixed_count = sum(1 for case in cases if bool(case.get("fixed_by_best_no_regression_guard")))
    still_failing = len(cases) - fixed_count
    decision = (
        "upstream_work_required_before_acceptance_target"
        if still_failing
        else "current_evidence_guard_headroom_requires_confirmation"
    )
    return {
        "decision": decision,
        "residual_case_count": len(cases),
        "fixed_by_best_no_regression_count": fixed_count,
        "still_failing_after_best_no_regression_count": still_failing,
        "fixed_by_zero_harm_count": sum(
            1 for case in cases if bool(case.get("fixed_by_zero_harm_guard"))
        ),
        "current_evidence_ceiling_status": str(ceiling_assessment.get("ceiling_status") or ""),
        "current_evidence_best_no_regression_correct": int(
            ceiling_assessment.get("best_no_regression_correct_case_count") or 0
        ),
        "current_evidence_optimistic_correct": int(
            ceiling_assessment.get("optimistic_correct_case_count") or 0
        ),
        "final_admitted_row_count": int(admission_summary.get("final_admitted_row_count") or 0),
        "source_class_frame_row_count": int(frame_summary.get("row_count") or 0),
        "phrase_control_source_row_count": int(phrase_summary.get("row_count") or 0),
        "bottleneck_counts": bottleneck_counts,
        "interpretation": [
            (
                "The current-evidence guard sweep found real but limited headroom: "
                f"{fixed_count} residuals are fixed by the best no-regression guard, "
                f"leaving {still_failing} residuals for upstream work."
            ),
            (
                "The remaining cases are not simply missing admitted evidence: the audit "
                "sees source rows and phrase rows, but the score/guard representation is not "
                "sufficiently separable."
            ),
            (
                "The next useful target is not another scalar sweep. It is evidence wording, "
                "raw-source/representation review, scorer aggregation, or an explicitly measured "
                "LLM-pipeline bound."
            ),
        ],
    }


def _class_summaries(cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for case in cases:
        grouped.setdefault(str(case.get("bottleneck") or ""), []).append(case)
    rows: list[dict[str, object]] = []
    for bottleneck in sorted(grouped):
        materialized = grouped[bottleneck]
        rows.append(
            {
                "bottleneck": bottleneck,
                "case_count": len(materialized),
                "case_ids": [str(case.get("case_id") or "") for case in materialized],
                "triggers": sorted({str(case.get("trigger") or "") for case in materialized}),
                "failure_classes": sorted(
                    {str(case.get("failure_class") or "") for case in materialized}
                ),
                "recommended_next_actions": sorted(
                    {str(case.get("recommended_next_action") or "") for case in materialized}
                ),
            }
        )
    return rows


def _next_steps(*, summary: Mapping[str, object]) -> list[str]:
    return [
        "Use this audit to choose upstream work, not to promote a runtime policy.",
        "First inspect the evidence/scorer gap cases where gold evidence is admitted but not score-visible.",
        "Then design a phrase/no-winner representation or guard signal that avoids regressing active replace rows.",
        "Only after those two lanes should an LLM-pipeline bound be run against locked residual cases.",
    ]


def _family_source_summary(
    frame_family: Mapping[str, object] | None,
    phrase_family: Mapping[str, object] | None,
) -> dict[str, object]:
    frame = _as_mapping(frame_family)
    phrase = _as_mapping(phrase_family)
    sense_rows = _mapping_rows(frame.get("sense_rows"))
    return {
        "source_class_family_present": bool(frame),
        "source_class_row_count": int(frame.get("row_count") or 0),
        "source_class_matching_sense_count": int(frame.get("matching_sense_count") or 0),
        "source_class_active_row_count": int(frame.get("active_row_count") or 0),
        "source_class_shadow_row_count": int(frame.get("shadow_row_count") or 0),
        "source_class_relation_types": sorted(
            {str(row.get("relation_type") or "") for row in sense_rows if row.get("relation_type")}
        ),
        "source_class_support_sources": sorted(
            {
                str(source)
                for row in sense_rows
                for source in _as_sequence(row.get("support_sources"))
                if str(source)
            }
        ),
        "phrase_source_family_present": bool(phrase),
        "phrase_source_candidate_sense_count": int(phrase.get("candidate_sense_count") or 0),
        "phrase_source_row_count": int(phrase.get("row_count") or 0),
        "phrase_source_active_like_skip_count": int(phrase.get("active_like_skip_count") or 0),
    }


def _family_rows_by_trigger(report: Mapping[str, object] | None) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("trigger") or ""): row
        for row in _mapping_rows(_as_mapping(report).get("family_rows"))
    }


def _source_ref(report: Mapping[str, object] | None, path: Path | None) -> dict[str, object]:
    payload = _as_mapping(report)
    summary = _as_mapping(payload.get("summary"))
    return {
        "path": _repo_path(path),
        "status": str(payload.get("status") or ""),
        "decision": str(payload.get("decision") or ""),
        "summary": {
            key: summary[key]
            for key in sorted(summary)
            if key.endswith("_count") or key in {"row_count", "case_count", "families_total"}
        },
    }


def _count_table(value: object) -> str:
    counts = _as_mapping(value)
    if not counts:
        return "No bottlenecks."
    lines = ["| Bottleneck | Cases |", "| --- | ---: |"]
    for key in sorted(counts):
        lines.append(f"| `{key}` | {counts[key]} |")
    return "\n".join(lines)


def _class_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No class summaries."
    lines = [
        "| Bottleneck | Cases | Triggers | Failure Classes | Next Actions |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('bottleneck', '')}`",
                    str(row.get("case_count", 0)),
                    _code_list(row.get("triggers")),
                    _code_list(row.get("failure_classes")),
                    _text_list(row.get("recommended_next_actions")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _case_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No cases."
    lines = [
        "| Case | Error | Score Visible | No-Regression Fix | Bottleneck | Source Rows | Phrase Rows | Next Action |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        source_summary = _as_mapping(row.get("source_summary"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('decision_error_type', '')}`",
                    f"`{str(bool(row.get('score_visible_for_gold'))).lower()}`",
                    f"`{str(bool(row.get('fixed_by_best_no_regression_guard'))).lower()}`",
                    f"`{row.get('bottleneck', '')}`",
                    str(source_summary.get("source_class_row_count", 0)),
                    str(source_summary.get("phrase_source_row_count", 0)),
                    _md_text(row.get("recommended_next_action")),
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


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _code_list(value: object) -> str:
    values = [str(item) for item in _as_sequence(value) if str(item)]
    return ", ".join(f"`{item}`" for item in values) or "`none`"


def _text_list(value: object) -> str:
    values = [_md_text(item) for item in _as_sequence(value) if str(item)]
    return "<br>".join(values) or ""


def _md_text(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
