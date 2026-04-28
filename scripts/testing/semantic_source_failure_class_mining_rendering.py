#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping, Sequence


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def render_source_failure_class_mining_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    gate = _as_mapping(report.get("quality_gate"))
    leverage = _as_mapping(report.get("leverage"))
    primary_admission = _as_mapping(report.get("primary_admission"))
    primary_heldout = _as_mapping(report.get("primary_heldout"))
    additional_heldouts = [
        row for row in _as_sequence(report.get("additional_heldouts")) if isinstance(row, Mapping)
    ]
    lines = [
        "# en-es Semantic Source Failure-class Mining",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Promotion readiness: `{summary.get('promotion_readiness', '')}`",
        f"- Quality-gate distance: `{summary.get('quality_gate_distance', '')}`",
        f"- Manual overfit risk: `{summary.get('manual_overfit_risk', '')}`",
        "",
        "## Primary Evidence",
        "",
        f"- Admission: `{primary_admission.get('label', '')}`",
        f"- Admission semantic contract: `{primary_admission.get('semantic_contract_complete_family_count', 0)}` / `{primary_admission.get('families_total', 0)}`",
        f"- Admission final rows: `{primary_admission.get('final_admitted_row_count', 0)}`",
        f"- Seed ablation harmful / false abstain: `{primary_admission.get('seed_harmful_replace_count', 0)}` / `{primary_admission.get('seed_false_abstain_count', 0)}`",
        f"- Held-out: `{primary_heldout.get('label', '')}`",
        f"- Held-out cases: `{primary_heldout.get('case_count', 0)}` across `{primary_heldout.get('family_count', 0)}` families",
        f"- Held-out harmful / false abstain: `{primary_heldout.get('harmful_replace_count', 0)}` / `{primary_heldout.get('false_abstain_count', 0)}`",
        f"- Additional held-out suites: `{len(additional_heldouts)}`",
        "",
        "## Failure Classes",
        "",
        _failure_class_table(report.get("failure_classes", ())),
        "",
        "## Leverage And Overfit Boundary",
        "",
        f"- Source rows: `{leverage.get('source_row_count', 0)}`",
        f"- Source families: `{leverage.get('source_family_count', 0)}`",
        f"- Held-out cases per admitted row: `{_fmt_float(leverage.get('heldout_cases_per_admitted_row'))}`",
        f"- Families needed before broad-confidence claim: `{leverage.get('family_breadth_gap', 0)}`",
        f"- Cases needed before broad-confidence claim: `{leverage.get('case_breadth_gap', 0)}`",
        f"- Source-mode false-abstain delta: `{leverage.get('best_comparator_false_abstain_delta', 0)}`",
        f"- Source-mode sense-reject delta: `{leverage.get('best_comparator_sense_reject_delta', 0)}`",
        "",
        "## Quality Gate Distance",
        "",
    ]
    blockers = _as_sequence(gate.get("blockers"))
    tracked = _as_sequence(gate.get("tracked_residuals"))
    lines.append(
        "- Blockers: " + (", ".join(f"`{item}`" for item in blockers) if blockers else "`none`")
    )
    lines.append(
        "- Tracked residuals: "
        + (", ".join(f"`{item}`" for item in tracked) if tracked else "`none`")
    )
    lines.extend(
        [
            "",
            "## Comparator Admissions",
            "",
            _admission_table(report.get("comparator_admissions", ())),
        ]
    )
    if additional_heldouts:
        lines.extend(["", "## Additional Held-out Suites", "", _heldout_table(additional_heldouts)])
    lines.extend(
        ["", "## Source Reports", "", _source_report_table(report.get("source_reports", ()))]
    )
    if _as_mapping(report.get("margin_sweep")):
        margin = _as_mapping(report.get("margin_sweep"))
        lines.extend(
            [
                "",
                "## Margin Sweep",
                "",
                f"- Decision: `{margin.get('decision', '')}`",
                f"- Recommended margin: `{margin.get('recommended_min_margin', '')}`",
                f"- Passing margins: `{', '.join(str(item) for item in _as_sequence(margin.get('passing_margins'))) or 'none'}`",
            ]
        )
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _failure_class_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No failure classes were observed in the supplied artifacts."
    lines = [
        "| Class | Count | Blocks semantic promotion | Tracked residual | Families |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in materialized:
        families = ", ".join(str(item) for item in _as_sequence(row.get("family_tokens")))
        lines.append(
            f"| `{row.get('class_id', '')}` | `{row.get('count', 0)}` | "
            f"`{bool(row.get('blocks_semantic_promotion'))}` | "
            f"`{bool(row.get('tracked_residual'))}` | `{families or 'none'}` |"
        )
    return "\n".join(lines)


def _admission_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No comparator admissions were supplied."
    lines = [
        "| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            f"| `{row.get('label', '')}` | `{row.get('sense_rejected_row_count', 0)}` | "
            f"`{row.get('semantic_contract_complete_family_count', 0)}` / "
            f"`{row.get('families_total', 0)}` | "
            f"`{row.get('seed_harmful_replace_count', 0)}` | "
            f"`{row.get('seed_false_abstain_count', 0)}` |"
        )
    return "\n".join(lines)


def _heldout_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No additional held-out suites were supplied."
    lines = [
        "| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            f"| `{row.get('label', '')}` | `{row.get('heldout_case_scope', '')}` | "
            f"`{row.get('case_count', 0)}` | `{row.get('family_count', 0)}` | "
            f"`{row.get('harmful_replace_count', 0)}` | "
            f"`{row.get('false_abstain_count', 0)}` | "
            f"`{_fmt_float(row.get('decision_accuracy'))}` |"
        )
    return "\n".join(lines)


def _source_report_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No source reports were supplied."
    lines = [
        "| Label | Mode | Families | Rows | Active gaps | Shadow gaps |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            f"| `{row.get('label', '')}` | `{row.get('evidence_mode', '')}` | "
            f"`{row.get('source_family_count', 0)}` | `{row.get('row_count', 0)}` | "
            f"`{len(_as_sequence(row.get('missing_active_family_keys')))}` | "
            f"`{len(_as_sequence(row.get('missing_shadow_family_keys')))}` |"
        )
    return "\n".join(lines)


def _fmt_float(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)
