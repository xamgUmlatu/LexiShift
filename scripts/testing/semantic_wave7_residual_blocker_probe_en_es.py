#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
DEFAULT_RESCUE_SWEEP = TEST_OUTPUTS_ROOT / (
    "semantic_surface_pos_rescue_policy_sweep_wave7_source_class_breadth_v1_"
    "phrase_control_triage_latest.json"
)
DEFAULT_NO_SURFACE_MARGIN_SWEEP = TEST_OUTPUTS_ROOT / (
    "semantic_source_margin_policy_sweep_wave7_source_class_breadth_v1_"
    "phrase_control_no_surface_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_wave7_residual_blocker_probe_wave7_source_class_breadth_v1_"
    "phrase_control_triage_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_wave7_residual_blocker_probe_wave7_source_class_breadth_v1_"
    "phrase_control_triage_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify the residual wave7 source-class breadth blockers before "
            "any scalar rescue or margin tuning. This is a fixed-trace diagnostic: "
            "it reads existing scorer-backed validation and sweep artifacts."
        )
    )
    parser.add_argument("--active-report-json", type=Path, default=DEFAULT_ACTIVE_REPORT)
    parser.add_argument("--phrase-report-json", type=Path, default=DEFAULT_PHRASE_REPORT)
    parser.add_argument("--rescue-sweep-json", type=Path, default=DEFAULT_RESCUE_SWEEP)
    parser.add_argument(
        "--no-surface-margin-sweep-json",
        type=Path,
        default=DEFAULT_NO_SURFACE_MARGIN_SWEEP,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    active_report = _load_json(args.active_report_json)
    phrase_report = _load_json(args.phrase_report_json)
    rescue_sweep = _load_optional_json(args.rescue_sweep_json)
    no_surface_margin_sweep = _load_optional_json(args.no_surface_margin_sweep_json)
    report = build_wave7_residual_blocker_probe_report(
        active_report=active_report,
        phrase_report=phrase_report,
        rescue_sweep=rescue_sweep,
        no_surface_margin_sweep=no_surface_margin_sweep,
        active_report_path=args.active_report_json,
        phrase_report_path=args.phrase_report_json,
        rescue_sweep_path=args.rescue_sweep_json,
        no_surface_margin_sweep_path=args.no_surface_margin_sweep_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_wave7_residual_blocker_probe_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_wave7_residual_blocker_probe_report(
    *,
    active_report: Mapping[str, object],
    phrase_report: Mapping[str, object],
    rescue_sweep: Mapping[str, object] | None = None,
    no_surface_margin_sweep: Mapping[str, object] | None = None,
    active_report_path: Path | None = None,
    phrase_report_path: Path | None = None,
    rescue_sweep_path: Path | None = None,
    no_surface_margin_sweep_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    cases = [
        *_failure_cases(
            suite_id="active_shadow",
            report=active_report,
            report_path=active_report_path,
        ),
        *_failure_cases(
            suite_id="phrase_no_winner",
            report=phrase_report,
            report_path=phrase_report_path,
        ),
    ]
    class_summaries = _class_summaries(cases)
    policy_context = _policy_context(
        rescue_sweep=rescue_sweep,
        no_surface_margin_sweep=no_surface_margin_sweep,
        rescue_sweep_path=rescue_sweep_path,
        no_surface_margin_sweep_path=no_surface_margin_sweep_path,
    )
    scalar_pass_count = int(policy_context["summary"]["combined_passing_policy_count"])
    status = "ok" if not cases else "review"
    decision = (
        "no_residual_blockers"
        if not cases
        else (
            "targeted_remediation_required"
            if scalar_pass_count <= 0
            else "targeted_remediation_or_confirmed_policy_required"
        )
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "generated_at": generated_at,
        "score_surface": {
            "active_report": _report_ref(active_report, active_report_path),
            "phrase_report": _report_ref(phrase_report, phrase_report_path),
        },
        "summary": {
            "residual_case_count": len(cases),
            "active_shadow_failure_count": sum(
                1 for case in cases if case["suite_id"] == "active_shadow"
            ),
            "phrase_no_winner_failure_count": sum(
                1 for case in cases if case["suite_id"] == "phrase_no_winner"
            ),
            "harmful_replace_count": sum(
                1 for case in cases if case["decision_error_type"] == "harmful_replace"
            ),
            "false_abstain_count": sum(
                1 for case in cases if case["decision_error_type"] == "false_abstain"
            ),
            "failure_class_count": len(class_summaries),
            "remediation_lanes": sorted(
                {
                    str(case.get("remediation_lane") or "")
                    for case in cases
                    if str(case.get("remediation_lane") or "")
                }
            ),
            "scalar_policy_pass_available": scalar_pass_count > 0,
            "combined_passing_policy_count": scalar_pass_count,
        },
        "class_summaries": class_summaries,
        "residual_cases": cases,
        "policy_context": policy_context,
        "next_steps": _next_steps(cases=cases, scalar_pass_count=scalar_pass_count),
        "limitations": [
            "fixed_trace_probe_not_runtime_policy",
            "does_not_rescore_or_regenerate_evidence",
            "classifies_current_wave7_phrase_control_triage_reports_only",
        ],
    }


def render_wave7_residual_blocker_probe_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    policy_summary = _as_mapping(_as_mapping(report.get("policy_context")).get("summary"))
    lines = [
        "# en-es Wave7 Residual Blocker Probe",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Residual cases: `{summary.get('residual_case_count', 0)}`",
        f"- Active/shadow failures: `{summary.get('active_shadow_failure_count', 0)}`",
        f"- Phrase/no-winner failures: `{summary.get('phrase_no_winner_failure_count', 0)}`",
        f"- Combined passing policies already available: "
        f"`{policy_summary.get('combined_passing_policy_count', 0)}`",
        "",
        "## Class Summaries",
        "",
        _class_summary_table(report.get("class_summaries")),
        "",
        "## Residual Cases",
        "",
        _case_table(report.get("residual_cases")),
        "",
        "## Policy Context",
        "",
        _policy_context_table(report.get("policy_context")),
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _failure_cases(
    *,
    suite_id: str,
    report: Mapping[str, object],
    report_path: Path | None,
) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for row in _as_sequence(report.get("configured_case_results")):
        if not isinstance(row, Mapping):
            continue
        gold = str(row.get("gold_decision") or "").strip()
        predicted = str(row.get("predicted_decision") or "").strip()
        if predicted == gold:
            continue
        classification = _classify_failure(row=row, suite_id=suite_id)
        active_score = _safe_float(row.get("active_score"))
        shadow_score = _safe_float(row.get("strongest_shadow_score"))
        phrase_score = _safe_float(row.get("phrase_control_score"))
        cases.append(
            {
                "suite_id": suite_id,
                "report_path": _repo_path(report_path),
                "case_id": str(row.get("case_id") or "").strip(),
                "family_id": str(row.get("family_id") or "").strip(),
                "trigger": str(row.get("trigger") or "").strip(),
                "sentence": str(row.get("sentence") or "").strip(),
                "gold_decision": gold,
                "predicted_decision": predicted,
                "decision_error_type": _decision_error_type(gold=gold, predicted=predicted),
                "predicted_winner": str(row.get("predicted_winner") or "").strip(),
                "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
                "active_score": active_score,
                "strongest_shadow_score": shadow_score,
                "phrase_control_score": phrase_score,
                "margin": _round_float(active_score - shadow_score),
                "phrase_lead_to_best": _round_float(phrase_score - max(active_score, shadow_score)),
                "phrase_prototype_margin": _safe_float(row.get("phrase_prototype_margin")),
                "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
                "matched_phrase_pattern": str(row.get("matched_phrase_pattern") or "").strip(),
                "surface_pos_signal": str(row.get("surface_pos_signal") or "").strip(),
                "surface_pos_rescue_blocked_reason": str(
                    row.get("surface_pos_rescue_blocked_reason") or ""
                ).strip(),
                "active_evidence_text": str(row.get("active_evidence_text") or "").strip(),
                "strongest_shadow_evidence_text": str(
                    row.get("strongest_shadow_evidence_text") or ""
                ).strip(),
                "phrase_control_evidence_text": str(
                    row.get("phrase_control_evidence_text") or ""
                ).strip(),
                **classification,
            }
        )
    return cases


def _classify_failure(*, row: Mapping[str, object], suite_id: str) -> dict[str, str]:
    gold = str(row.get("gold_decision") or "").strip()
    predicted = str(row.get("predicted_decision") or "").strip()
    trigger = str(row.get("trigger") or "").strip()
    active_score = _safe_float(row.get("active_score"))
    shadow_score = _safe_float(row.get("strongest_shadow_score"))
    phrase_score = _safe_float(row.get("phrase_control_score"))
    margin = active_score - shadow_score
    phrase_lead = phrase_score - max(active_score, shadow_score)
    signal = str(row.get("surface_pos_signal") or "").strip()
    predicted_winner = str(row.get("predicted_winner") or "").strip()
    shadow_evidence = str(row.get("strongest_shadow_evidence_text") or "").lower()

    if suite_id == "active_shadow" and predicted == "replace" and gold != "replace":
        if trigger == "gross" and any(token in shadow_evidence for token in ("dozen", "gross")):
            return _classification(
                "shadow_quantity_evidence_underweighted",
                "shadow_evidence_repair",
                "Quantity shadow evidence is present but loses to the active disgust sense.",
                "Strengthen or separate source evidence for quantity/commercial frames before threshold tuning.",
            )
        return _classification(
            "active_shadow_harmful_replace",
            "active_shadow_guard_design",
            "Active evidence wins on a gold-abstain active/shadow case.",
            "Inspect active/shadow guard features before changing a global margin.",
        )

    if suite_id == "active_shadow" and predicted != "replace" and gold == "replace":
        if bool(row.get("phrase_preemption_hit")) and margin >= 0.1:
            return _classification(
                "phrase_preemption_overreach_on_strong_active",
                "phrase_preemption_guard",
                "Phrase preemption overrides a strong active score.",
                "Add a focused preemption guard or scorer-backed rerun for strong-active preposition frames.",
            )
        if predicted_winner == "phrase_control" or phrase_lead >= 0.0:
            return _classification(
                "phrase_control_overlap_overblocks_active",
                "overlap_evidence_repair",
                "Phrase-control evidence semantically overlaps the active sentence and overblocks it.",
                "Repair phrase-control evidence or add overlap-aware guard tests before scalar tuning.",
            )
        if shadow_score > active_score:
            return _classification(
                "shadow_overlap_overblocks_active",
                "shadow_evidence_repair",
                "Shadow evidence scores above the correct active sense.",
                "Improve active-vs-shadow evidence contrast for the family before scalar tuning.",
            )
        return _classification(
            "active_false_abstain_unclassified",
            "focused_heldout_rerun",
            "False abstain does not match an existing residual subtype.",
            "Add a narrow diagnostic row before applying any broad policy.",
        )

    if suite_id == "phrase_no_winner" and predicted == "replace" and gold != "replace":
        if signal in {"active_noun_frame", "active_modifier_frame"}:
            if phrase_lead >= _safe_float(row.get("phrase_prototype_margin")):
                return _classification(
                    "surface_rescue_overrode_dominant_phrase_control",
                    "phrase_no_winner_rescue_guard",
                    "Surface-POS rescue permits replace despite dominant phrase-control evidence.",
                    "Make phrase/no-winner rescue guard account for dominant phrase-control evidence.",
                )
            return _classification(
                "surface_rescue_leaks_when_phrase_control_close",
                "phrase_no_winner_rescue_guard",
                "Surface-POS rescue leaks when phrase-control evidence is close to the best sense.",
                "Test a close-phrase guard instead of increasing the global active margin.",
            )
        return _classification(
            "phrase_no_winner_harmful_replace",
            "phrase_no_winner_guard_design",
            "Phrase/no-winner case still predicts replace without a surface rescue class.",
            "Add a phrase/no-winner focused guard or evidence diagnostic.",
        )

    return _classification(
        "residual_unclassified",
        "focused_heldout_rerun",
        "Residual failure does not match a known wave7 subtype.",
        "Add a focused heldout rerun before policy changes.",
    )


def _classification(
    class_id: str,
    remediation_lane: str,
    diagnosis: str,
    remediation_hypothesis: str,
) -> dict[str, str]:
    return {
        "failure_class": class_id,
        "remediation_lane": remediation_lane,
        "diagnosis": diagnosis,
        "remediation_hypothesis": remediation_hypothesis,
        "scalar_policy_warning": "do_not_treat_as_single_threshold_problem",
    }


def _class_summaries(cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for case in cases:
        grouped[str(case.get("failure_class") or "residual_unclassified")].append(case)
    summaries: list[dict[str, object]] = []
    for class_id in sorted(grouped):
        rows = grouped[class_id]
        first = rows[0]
        summaries.append(
            {
                "failure_class": class_id,
                "case_count": len(rows),
                "case_ids": [str(row.get("case_id") or "") for row in rows],
                "triggers": sorted({str(row.get("trigger") or "") for row in rows}),
                "suite_ids": sorted({str(row.get("suite_id") or "") for row in rows}),
                "decision_error_types": dict(
                    sorted(
                        Counter(str(row.get("decision_error_type") or "") for row in rows).items()
                    )
                ),
                "remediation_lane": str(first.get("remediation_lane") or ""),
                "diagnosis": str(first.get("diagnosis") or ""),
                "remediation_hypothesis": str(first.get("remediation_hypothesis") or ""),
                "scalar_policy_warning": str(first.get("scalar_policy_warning") or ""),
            }
        )
    return summaries


def _policy_context(
    *,
    rescue_sweep: Mapping[str, object] | None,
    no_surface_margin_sweep: Mapping[str, object] | None,
    rescue_sweep_path: Path | None,
    no_surface_margin_sweep_path: Path | None,
) -> dict[str, object]:
    rescue_summary = _as_mapping(_as_mapping(rescue_sweep).get("summary"))
    margin_summary = _as_mapping(_as_mapping(no_surface_margin_sweep).get("summary"))
    rescue_passing = int(rescue_summary.get("passing_policy_count") or 0)
    margin_passing = int(margin_summary.get("passing_policy_count") or 0)
    return {
        "rescue_sweep": {
            "path": _repo_path(rescue_sweep_path),
            "status": str(_as_mapping(rescue_sweep).get("status") or ""),
            "decision": str(_as_mapping(rescue_sweep).get("decision") or ""),
            "policy_count": int(rescue_summary.get("policy_count") or 0),
            "passing_policy_count": rescue_passing,
            "recommended_policy": rescue_summary.get("recommended_policy"),
        },
        "no_surface_margin_sweep": {
            "path": _repo_path(no_surface_margin_sweep_path),
            "status": str(_as_mapping(no_surface_margin_sweep).get("status") or ""),
            "decision": str(_as_mapping(no_surface_margin_sweep).get("decision") or ""),
            "row_count": int(margin_summary.get("row_count") or 0),
            "passing_policy_count": margin_passing,
            "recommended_policy": margin_summary.get("recommended_policy"),
        },
        "summary": {
            "combined_passing_policy_count": rescue_passing + margin_passing,
            "existing_policy_context": (
                "no_existing_scalar_or_rescue_policy_passes"
                if rescue_passing + margin_passing <= 0
                else "existing_policy_candidate_requires_scorer_backing"
            ),
        },
    }


def _next_steps(*, cases: Sequence[Mapping[str, object]], scalar_pass_count: int) -> list[str]:
    if not cases:
        return ["No residual blockers detected; rerun the breadth gate before promotion claims."]
    lanes = {str(case.get("remediation_lane") or "") for case in cases}
    steps: list[str] = []
    if "shadow_evidence_repair" in lanes:
        steps.append(
            "Repair or split shadow/active evidence for `gross`, `fix`, and similar overlap cases."
        )
    if "phrase_preemption_guard" in lanes:
        steps.append(
            "Design a focused phrase-preemption guard for strong-active cases such as `even`."
        )
    if "overlap_evidence_repair" in lanes:
        steps.append(
            "Audit phrase-control overlap before letting phrase evidence veto active adjective cases."
        )
    if "phrase_no_winner_rescue_guard" in lanes:
        steps.append(
            "Constrain surface-POS rescue against phrase/no-winner rows with dominant or close phrase evidence."
        )
    if scalar_pass_count <= 0:
        steps.append(
            "Do not tune one global scalar policy yet; the current sweeps have zero combined passing policies."
        )
    steps.append(
        "After a targeted guard or evidence patch, rerun both wave7 heldout suites, rescue sweep, no-surface margin sweep, failure mining, registry summary, focused tests, doc-reference checks, and git diff whitespace checks."
    )
    return steps


def _decision_error_type(*, gold: str, predicted: str) -> str:
    if predicted == "replace" and gold != "replace":
        return "harmful_replace"
    if predicted != "replace" and gold == "replace":
        return "false_abstain"
    return "other_mismatch"


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


def _class_summary_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No residual failure classes."
    lines = [
        "| Class | Cases | Triggers | Lane | Diagnosis | Next Hypothesis |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('failure_class', '')}`",
                    str(row.get("case_count", 0)),
                    _code_list(row.get("triggers")),
                    f"`{row.get('remediation_lane', '')}`",
                    _md_text(row.get("diagnosis")),
                    _md_text(row.get("remediation_hypothesis")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _case_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No residual cases."
    lines = [
        "| Case | Suite | Error | Class | Active | Shadow | Phrase | Margin | Phrase Lead | Signals | Evidence |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in materialized:
        signals = ", ".join(
            item
            for item in (
                "phrase_preempt" if row.get("phrase_preemption_hit") else "",
                str(row.get("matched_phrase_pattern") or "").strip(),
                str(row.get("surface_pos_signal") or "").strip(),
                str(row.get("surface_pos_rescue_blocked_reason") or "").strip(),
            )
            if item
        )
        evidence = " / ".join(
            _short_text(row.get(key))
            for key in (
                "active_evidence_text",
                "strongest_shadow_evidence_text",
                "phrase_control_evidence_text",
            )
            if str(row.get(key) or "").strip()
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('suite_id', '')}`",
                    f"`{row.get('decision_error_type', '')}`",
                    f"`{row.get('failure_class', '')}`",
                    _format_float(row.get("active_score")),
                    _format_float(row.get("strongest_shadow_score")),
                    _format_float(row.get("phrase_control_score")),
                    _format_float(row.get("margin")),
                    _format_float(row.get("phrase_lead_to_best")),
                    _md_text(signals),
                    _md_text(evidence),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _policy_context_table(value: object) -> str:
    context = _as_mapping(value)
    rows = []
    for label in ("rescue_sweep", "no_surface_margin_sweep"):
        row = _as_mapping(context.get(label))
        rows.append(
            [
                label,
                str(row.get("status") or ""),
                str(row.get("decision") or ""),
                str(row.get("policy_count") or row.get("row_count") or 0),
                str(row.get("passing_policy_count") or 0),
                str(row.get("path") or ""),
            ]
        )
    lines = [
        "| Artifact | Status | Decision | Policies/Rows | Passing | Path |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row[0]}`",
                    f"`{row[1]}`",
                    f"`{row[2]}`",
                    row[3],
                    row[4],
                    f"`{row[5]}`",
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


def _safe_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _round_float(value: float) -> float:
    return round(float(value), 4)


def _format_float(value: object) -> str:
    formatted = f"{_safe_float(value):.4f}".rstrip("0").rstrip(".")
    return f"`{formatted}`"


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _code_list(values: object) -> str:
    items = [str(value) for value in _as_sequence(values) if str(value)]
    return ", ".join(f"`{item}`" for item in items) or "`none`"


def _md_text(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _short_text(value: object, *, limit: int = 84) -> str:
    text = _md_text(value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
