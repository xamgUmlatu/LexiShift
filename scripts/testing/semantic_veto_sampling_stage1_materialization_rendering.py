from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _as_mapping, _escape_md, _mapping_rows


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return []


def _representative_preview_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Rank | Trigger | Target | Gold | Source case |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("selection_rank") or ""),
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('target_lemma') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_decision') or ''))}`",
                    f"`{_escape_md(str(row.get('source_case_id') or ''))}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_sampling_stage1_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    outputs = _as_mapping(report.get("outputs"))
    lines = [
        "# en-es Semantic Veto Sampling Stage 1 Materialization",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Representative frame: `{outputs.get('representative_frame_path', '')}`",
        f"- P0 dataset: `{outputs.get('p0_dataset_path', '')}`",
        "",
        "## Summary",
        "",
        _summary_table(summary),
        "",
        "## Representative Frame",
        "",
        _representative_preview_table(report.get("representative_frame_preview")),
        "",
        "## P0 Manual Rows",
        "",
        _p0_table(report.get("p0_authored_rows")),
        "",
        "## Bias Controls",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("bias_controls")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _summary_table(summary: Mapping[str, object]) -> str:
    rows = [
        ("representative target locked rows", summary.get("target_locked_eval_rows")),
        ("representative available rows", summary.get("available_representative_rows")),
        ("representative selected locked rows", summary.get("selected_locked_eval_rows")),
        (
            "representative remaining rows needed",
            summary.get("remaining_representative_rows_needed"),
        ),
        ("P0 curve cells", summary.get("p0_curve_cell_count")),
        ("P0 manual cases", summary.get("p0_manual_case_count")),
        ("P0 triggers", summary.get("p0_trigger_count")),
    ]
    lines = ["| Metric | Value |", "| --- | ---: |"]
    lines.extend(f"| {name} | `{value}` |" for name, value in rows)
    return "\n".join(lines)


def _p0_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Case | Type | Scorer | Trigger | Decision | Sentence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('case_id') or ''))}`",
                    f"`{_escape_md(str(row.get('manual_case_type') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_decision') or ''))}`",
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
