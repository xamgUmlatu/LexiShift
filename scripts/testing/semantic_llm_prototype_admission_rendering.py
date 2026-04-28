from __future__ import annotations

from typing import Mapping


def render_prototype_admission_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic LLM Prototype Admission Probe",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Scope: `{report.get('evaluation_scope', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
        f"- Scorer: `{report.get('scorer_id', '')}`",
        f"- Context view: `{report.get('context_view', '')}`",
        f"- Decision contract: `{report.get('decision_contract', '')}`",
        f"- Runtime publishable: `{report.get('runtime_publishable', False)}`",
        "",
        "## Prototype Results",
        "",
        "| Config | Phrase Guard | Evidence Mode | Cases | Harmful | False Abstain | Replace Recall | Decision Acc. | Runtime Phrase Hits | Containment Hits |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report.get("configurations", ()):
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('label', row.get('config_id', ''))}`",
                    f"`{row.get('phrase_guard_pos_scope', '')}`",
                    f"`{row.get('phrase_control_evidence_mode', '')}`",
                    str(summary.get("cases_total", 0)),
                    str(summary.get("harmful_replace_count", 0)),
                    str(summary.get("false_abstain_count", 0)),
                    _pct(summary.get("replace_recall")),
                    _pct(summary.get("decision_accuracy")),
                    str(summary.get("phrase_preemption_hit_count", 0)),
                    str(summary.get("phrase_containment_hit_count", 0)),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Residual Case Matrix",
            "",
            "| Case | Gold | Family Guard | Active Guard | Phrase Containment Guard | Surface-POS Rescue Guard | Phrase Prototype Guard |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.get("case_matrix", ()):
        if not isinstance(row, Mapping):
            continue
        configs = row.get("configs") if isinstance(row.get("configs"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('gold_decision', '')}`",
                    _format_case_config(configs.get("prototype_reviewed_examples_family_guard")),
                    _format_case_config(configs.get("prototype_reviewed_examples_active_guard")),
                    _format_case_config(
                        configs.get("prototype_reviewed_examples_phrase_containment_guard")
                    ),
                    _format_case_config(
                        configs.get("prototype_reviewed_examples_surface_pos_rescue_guard")
                    ),
                    _format_case_config(
                        configs.get("prototype_reviewed_examples_phrase_prototype_guard")
                    ),
                ]
            )
            + " |"
        )
    if not report.get("case_matrix"):
        lines.append("| `none` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` |")

    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _format_case_config(value: object) -> str:
    if not isinstance(value, Mapping):
        return "`n/a`"
    return (
        f"`{value.get('predicted_decision', '')}` "
        f"m={value.get('margin', '')} "
        f"a={value.get('active_score', '')} "
        f"s={value.get('strongest_shadow_score', '')} "
        f"p={value.get('phrase_control_score', '')} "
        f"pc={str(bool(value.get('phrase_containment_hit'))).lower()} "
        f"ar={str(bool(value.get('active_rescue_applied'))).lower()}"
    )


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"
