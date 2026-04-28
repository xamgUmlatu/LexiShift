from __future__ import annotations

from typing import Mapping, Sequence


def render_prototype_ablation_matrix_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic LLM Prototype Ablation Matrix",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
        f"- Decision contract: `{report.get('decision_contract', '')}`",
        f"- Matrix rows: `{report.get('row_count', 0)}`",
        f"- Prototype report runs: `{report.get('run_report_count', 0)}`",
        "",
        "## Best Rows",
        "",
        _row_table(
            [
                row
                for row in (report.get("best_row"), report.get("best_candidate_source_row"))
                if isinstance(row, Mapping)
            ],
            empty_label="No best rows.",
        ),
        "",
        "## Candidate Source Rows",
        "",
        _row_table(
            [
                row
                for row in (
                    report.get("best_candidate_source_row"),
                    *_mapping_values(report.get("best_candidate_by_scope")),
                )
                if isinstance(row, Mapping)
            ],
            empty_label="No candidate source rows.",
        ),
        "",
        "## Best by Source Mode",
        "",
        _row_table(_mapping_values(report.get("best_by_source_mode")), empty_label="No sources."),
        "",
        "## Candidate by Decision Shape",
        "",
        _row_table(
            _mapping_values(report.get("best_candidate_by_decision_shape")),
            empty_label="No decision shapes.",
        ),
        "",
        "## Candidate by Context View",
        "",
        _row_table(
            _mapping_values(report.get("best_candidate_by_context_view")),
            empty_label="No contexts.",
        ),
        "",
        "## Top Matrix Rows",
        "",
        _row_table(
            [row for row in report.get("rows", ()) if isinstance(row, Mapping)][:20],
            empty_label="No rows.",
        ),
        "",
        "## Assumption Audit",
        "",
    ]
    _append_assumption_audit(lines, report)
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    _append_skipped_sources(lines, report)
    return "\n".join(lines) + "\n"


def _append_assumption_audit(lines: list[str], report: Mapping[str, object]) -> None:
    audit = (
        report.get("assumption_audit")
        if isinstance(report.get("assumption_audit"), Mapping)
        else {}
    )
    for key in (
        "best_oracle_row",
        "best_candidate_source_row",
        "best_empty_baseline_row",
        "best_without_surface_pos_row",
        "best_viable_without_surface_pos_row",
        "best_without_phrase_control_row",
        "best_generated_composite_row",
        "best_generated_active_only_row",
        "best_generated_no_phrase_row",
        "best_generated_no_shadow_row",
    ):
        value = audit.get(key)
        if isinstance(value, Mapping):
            lines.append(f"- {key}: {_inline_row(value)}")
    simplified = audit.get("simplification_candidates")
    if isinstance(simplified, Sequence) and not isinstance(simplified, (str, bytes)) and simplified:
        lines.extend(["", "### Simplification Candidates", "", _row_table(simplified[:10])])


def _append_skipped_sources(lines: list[str], report: Mapping[str, object]) -> None:
    if not report.get("skipped_sources"):
        return
    lines.extend(["", "## Skipped Sources", ""])
    for item in report.get("skipped_sources", ()):
        if isinstance(item, Mapping):
            lines.append(
                f"- `{item.get('source_mode', '')}`: `{item.get('reason', '')}` "
                f"({item.get('path', '')})"
            )


def _row_table(rows: Sequence[object], *, empty_label: str = "No rows.") -> str:
    materialized = [row for row in rows if isinstance(row, Mapping)]
    if not materialized:
        return empty_label
    lines = [
        "| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |",
        "| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('source_mode', '')}`",
                    f"`{row.get('scope', '')}`",
                    f"`{row.get('scorer_id', '')}`",
                    f"`{row.get('context_view', '')}`",
                    str(row.get("min_active_score", 0.0)),
                    str(row.get("min_margin", 0.0)),
                    f"`{row.get('decision_shape', '')}`",
                    str(row.get("cases_total", 0)),
                    str(row.get("harmful_replace_count", 0)),
                    str(row.get("false_abstain_count", 0)),
                    _pct(row.get("replace_recall")),
                    _pct(row.get("decision_accuracy")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _inline_row(row: Mapping[str, object]) -> str:
    return (
        f"`{row.get('source_mode', '')}` / `{row.get('scope', '')}` / "
        f"`{row.get('scorer_id', '')}` / `{row.get('context_view', '')}` / "
        f"`{row.get('decision_shape', '')}` -> "
        f"{row.get('harmful_replace_count', 0)} harmful, "
        f"{row.get('false_abstain_count', 0)} false abstain, "
        f"{_pct(row.get('replace_recall'))} recall"
    )


def _mapping_values(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return []
    return [row for row in value.values() if isinstance(row, Mapping)]


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"
