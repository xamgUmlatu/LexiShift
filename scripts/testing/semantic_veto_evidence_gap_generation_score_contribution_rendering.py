from __future__ import annotations

from typing import Mapping

from semantic_veto_evidence_gap_generation_score_contribution_core import (
    _as_mapping,
    _as_sequence,
    _fmt,
    _mapping_rows,
    _report_modes,
)


def render_evidence_gap_score_contribution_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    comparisons = _as_mapping(report.get("comparisons"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Score Contribution",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}`",
        f"- Admitted generated items: `{summary.get('admitted_item_count', 0)}`",
        f"- Waived generated items: `{summary.get('waived_item_count', 0)}`",
        "",
        "## Overall Metrics",
        "",
        "| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in _report_modes(include_base=True):
        row = _as_mapping(summary.get(mode))
        lines.append(
            f"| `{mode}` | {row.get('cases_total', 0)} | {_fmt(row.get('decision_accuracy'))} | "
            f"{_fmt(row.get('replace_recall'))} | {row.get('harmful_replace_count', 0)} | "
            f"{row.get('false_abstain_count', 0)} | {_fmt(row.get('winner_accuracy'))} |"
        )
    lines.extend(
        [
            "",
            "## Deltas",
            "",
            "| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for mode, comparison in comparisons.items():
        row = _as_mapping(comparison)
        lines.append(
            f"| `{mode}` | {_fmt(row.get('decision_accuracy_delta'))} | "
            f"{_fmt(row.get('replace_recall_delta'))} | {row.get('harmful_replace_delta', 0)} | "
            f"{row.get('false_abstain_delta', 0)} | {_fmt(row.get('winner_accuracy_delta'))} |"
        )
    lines.extend(
        [
            "",
            "## Policy Sweep Best By Harmful Budget",
            "",
            "| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |",
            "| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for budget, row in _as_mapping(report.get("best_by_harmful_budget")).items():
        rows = _as_mapping(row)
        lines.append(
            f"| {budget} | `{rows.get('application_mode', '')}` | "
            f"{_fmt(rows.get('min_active_score'))} | {_fmt(rows.get('min_margin'))} | "
            f"`{rows.get('phrase_control_mode', '')}` | `{rows.get('active_rescue_mode', '')}` | "
            f"{_fmt(rows.get('decision_accuracy'))} | {_fmt(rows.get('replace_recall'))} | "
            f"{rows.get('harmful_replace_count', 0)} | {rows.get('false_abstain_count', 0)} | "
            f"{_fmt(rows.get('winner_accuracy'))} |"
        )
    lines.extend(["", "## Application Summary", ""])
    for mode, app_summary in _as_mapping(report.get("application_summary")).items():
        lines.append(f"### `{mode}`")
        rows = _as_mapping(app_summary)
        lines.append(f"- Active evidence items applied: `{rows.get('active_items_applied', 0)}`")
        lines.append(f"- Active evidence items ignored: `{rows.get('active_items_ignored', 0)}`")
        lines.append(
            f"- Existing shadow evidence items applied: `{rows.get('existing_shadow_items_applied', 0)}`"
        )
        lines.append(
            f"- Synthetic shadow evidence items applied: `{rows.get('synthetic_shadow_items_applied', 0)}`"
        )
        lines.append(f"- Shadow evidence items ignored: `{rows.get('shadow_items_ignored', 0)}`")
        lines.append(f"- Ignored no-winner items: `{rows.get('no_winner_items_ignored', 0)}`")
        lines.append("")
    lines.extend(
        [
            "## Changed Cases",
            "",
            "| Mode | Case | Gold | Base | Candidate | Active Δ | Shadow Δ | Sentence |",
            "| --- | --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    changed_rows = []
    for mode, rows in _as_mapping(report.get("case_deltas")).items():
        for row in _mapping_rows(rows):
            if bool(row.get("decision_changed")) or bool(row.get("winner_changed")):
                changed_rows.append((mode, row))
    for mode, row in changed_rows[:30]:
        lines.append(
            f"| `{mode}` | `{row.get('case_id', '')}` | `{row.get('gold_decision', '')}` | "
            f"`{row.get('base_predicted_decision', '')}` | `{row.get('candidate_predicted_decision', '')}` | "
            f"{_fmt(row.get('active_score_delta'))} | {_fmt(row.get('strongest_shadow_score_delta'))} | "
            f"{_escape_md(str(row.get('sentence') or ''))} |"
        )
    if not changed_rows:
        lines.append("| _None._ |  |  |  |  |  |  |  |")
    lines.extend(["## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
