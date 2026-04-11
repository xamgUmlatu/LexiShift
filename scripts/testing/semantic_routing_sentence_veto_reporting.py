#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping, Sequence


def render_sentence_veto_markdown(report: Mapping[str, object]) -> str:
    config = report.get("config") if isinstance(report.get("config"), Mapping) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# Semantic Routing Sentence Veto Harness",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Scorer: `{config.get('scorer_id', '')}`",
        f"- Model: `{config.get('model_name', '') or 'n/a'}`",
        f"- Context view: `{config.get('context_view', '')}`",
        f"- Evidence view: `{config.get('evidence_view', '')}`",
        f"- Thresholds: `min_active={config.get('min_active_score', '')}`, `min_margin={config.get('min_margin', '')}`",
        "",
        "## Summary",
        "",
        f"- Decision accuracy: `{_render_rate(summary.get('decision_accuracy'))}`",
        f"- Replace precision / recall: `{_render_rate(summary.get('replace_precision'))}` / `{_render_rate(summary.get('replace_recall'))}`",
        f"- Harmful replace / false abstain: `{_render_rate(summary.get('harmful_replace_rate'))}` / `{_render_rate(summary.get('false_abstain_rate'))}`",
        f"- Winner accuracy / shadow-winner accuracy: `{_render_rate(summary.get('winner_accuracy'))}` / `{_render_rate(summary.get('shadow_winner_accuracy'))}`",
        f"- Predicted replace rate: `{_render_rate(summary.get('predicted_replace_rate'))}`",
        "",
        "## Family Breakdown",
        "",
    ]
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("family_breakdown"),
            label_key="family_id",
            label_builder=_build_family_breakdown_label,
        )
    )
    lines.extend(["", "## Gold Winner Type Breakdown", ""])
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("gold_winner_type_breakdown"),
            label_key="gold_winner_type",
        )
    )
    lines.extend(["", "## Slice Tag Breakdown", ""])
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("slice_tag_breakdown"),
            label_key="slice_tag",
            limit=12,
        )
    )
    lines.extend(["", "## Failure Samples", ""])
    lines.extend(
        _render_sentence_veto_failure_block(
            "Harmful replace", report.get("sample_harmful_replace_rows")
        )
    )
    lines.extend(
        _render_sentence_veto_failure_block(
            "False abstain", report.get("sample_false_abstain_rows")
        )
    )
    lines.extend(
        _render_sentence_veto_failure_block("Winner errors", report.get("sample_winner_error_rows"))
    )
    return "\n".join(lines) + "\n"


def render_sentence_veto_sweep_markdown(report: Mapping[str, object]) -> str:
    grid = report.get("grid") if isinstance(report.get("grid"), Mapping) else {}
    best_row = report.get("best_row") if isinstance(report.get("best_row"), Mapping) else {}
    best_objective_row = (
        report.get("best_objective_row")
        if isinstance(report.get("best_objective_row"), Mapping)
        else {}
    )
    best_rows_by_harmful_replace_budget = (
        report.get("best_rows_by_harmful_replace_budget")
        if isinstance(report.get("best_rows_by_harmful_replace_budget"), Sequence)
        and not isinstance(report.get("best_rows_by_harmful_replace_budget"), (str, bytes))
        else []
    )
    best_by_scorer = (
        report.get("best_by_scorer")
        if isinstance(report.get("best_by_scorer"), Sequence)
        and not isinstance(report.get("best_by_scorer"), (str, bytes))
        else []
    )
    rows = (
        report.get("rows")
        if isinstance(report.get("rows"), Sequence)
        and not isinstance(report.get("rows"), (str, bytes))
        else []
    )
    lines = [
        "# Semantic Routing Sentence Veto Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Grid size: `{report.get('row_count', 0)}`",
        f"- Scorers: `{', '.join(str(value) for value in grid.get('scorers', ()))}`",
        f"- Context views: `{', '.join(str(value) for value in grid.get('context_views', ()))}`",
        f"- Evidence views: `{', '.join(str(value) for value in grid.get('evidence_views', ()))}`",
        "",
        "## Best Overall",
        "",
    ]
    if best_row:
        lines.extend(_render_sentence_veto_sweep_row(best_row))
    lines.extend(["", "## Best By Harmful-Replace Budget", ""])
    for budget_entry in best_rows_by_harmful_replace_budget[:10]:
        if not isinstance(budget_entry, Mapping):
            continue
        budget_row = budget_entry.get("row")
        if not isinstance(budget_row, Mapping):
            continue
        lines.append(
            f"- Budget: `harmful_replace_count <= {int(budget_entry.get('harmful_replace_budget') or 0)}`"
        )
        lines.extend(_render_sentence_veto_sweep_row(budget_row))
        lines.append("")
    lines.extend(["## Best Objective", ""])
    if best_objective_row:
        lines.extend(_render_sentence_veto_sweep_row(best_objective_row))
        lines.append("")
    lines.extend(["", "## Best By Scorer", ""])
    for row in best_by_scorer[:10]:
        lines.extend(_render_sentence_veto_sweep_row(row))
        lines.append("")
    lines.extend(["## Top Configs", ""])
    lines.append(
        "| Rank | Scorer | Context | Evidence | min_active | min_margin | Harmful Cnt | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |"
    )
    lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for index, row in enumerate(rows[:12], start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    str(row.get("scorer_id") or ""),
                    str(row.get("context_view") or ""),
                    str(row.get("evidence_view") or ""),
                    f"{float(row.get('min_active_score') or 0.0):.2f}",
                    f"{float(row.get('min_margin') or 0.0):.2f}",
                    str(int(row.get("harmful_replace_count") or 0)),
                    _render_rate(row.get("decision_accuracy")),
                    _render_rate(row.get("harmful_replace_rate")),
                    _render_rate(row.get("false_abstain_rate")),
                    _render_rate(row.get("winner_accuracy")),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def compute_sentence_veto_objective(row: Mapping[str, object]) -> float:
    return (
        coerce_metric(row.get("decision_accuracy"), default=0.0)
        + coerce_metric(row.get("replace_precision"), default=0.0)
        + coerce_metric(row.get("replace_recall"), default=0.0)
        + coerce_metric(row.get("winner_accuracy"), default=0.0)
        - (2.0 * coerce_metric(row.get("harmful_replace_rate"), default=0.0))
        - coerce_metric(row.get("false_abstain_rate"), default=0.0)
    )


def sentence_veto_sweep_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        coerce_metric(row.get("harmful_replace_rate"), default=1.0),
        int(row.get("harmful_replace_count") or 0),
        coerce_metric(row.get("false_abstain_rate"), default=1.0),
        -coerce_metric(row.get("decision_accuracy"), default=0.0),
        -coerce_metric(row.get("winner_accuracy"), default=0.0),
        -coerce_metric(row.get("shadow_winner_accuracy"), default=0.0),
        -coerce_metric(row.get("replace_precision"), default=0.0),
        -coerce_metric(row.get("replace_recall"), default=0.0),
        str(row.get("scorer_id") or ""),
        str(row.get("context_view") or ""),
        str(row.get("evidence_view") or ""),
        coerce_metric(row.get("min_active_score"), default=0.0),
        coerce_metric(row.get("min_margin"), default=0.0),
    )


def select_best_sentence_veto_objective_row(
    rows: Sequence[Mapping[str, object]],
    *,
    max_harmful_replace_count: int | None = None,
) -> dict[str, object] | None:
    candidate_rows: list[Mapping[str, object]] = []
    for row in rows:
        harmful_replace_count = int(row.get("harmful_replace_count") or 0)
        if max_harmful_replace_count is not None and harmful_replace_count > max(
            0, int(max_harmful_replace_count)
        ):
            continue
        candidate_rows.append(row)
    if not candidate_rows:
        return None
    best_row = max(candidate_rows, key=_sentence_veto_objective_rank_key)
    return dict(best_row)


def coerce_metric(value: object, *, default: float) -> float:
    if isinstance(value, (float, int)):
        return float(value)
    return float(default)


def _sentence_veto_objective_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        compute_sentence_veto_objective(row),
        -int(row.get("harmful_replace_count") or 0),
        -coerce_metric(row.get("decision_accuracy"), default=0.0),
        -coerce_metric(row.get("replace_recall"), default=0.0),
        -coerce_metric(row.get("winner_accuracy"), default=0.0),
        -coerce_metric(row.get("shadow_winner_accuracy"), default=0.0),
        -coerce_metric(row.get("replace_precision"), default=0.0),
        str(row.get("scorer_id") or ""),
        str(row.get("context_view") or ""),
        str(row.get("evidence_view") or ""),
        -coerce_metric(row.get("min_active_score"), default=0.0),
        -coerce_metric(row.get("min_margin"), default=0.0),
    )


def _render_sentence_veto_failure_block(title: str, rows: object) -> list[str]:
    lines = [f"### {title}", ""]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        lines.append("- none")
        lines.append("")
        return lines
    for row in rows[:6]:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('case_id', '')}` `{row.get('predicted_decision', '')}` vs "
            f"`{row.get('gold_decision', '')}` | trigger `{row.get('source_phrase', '')}` | "
            f"margin `{float(row.get('margin') or 0.0):.3f}`"
        )
        lines.append(f"  sentence: {row.get('sentence', '')}")
    lines.append("")
    return lines


def _render_sentence_veto_sweep_row(row: Mapping[str, object]) -> list[str]:
    return [
        f"- Config: `{row.get('config_id', '')}`",
        f"- Harmful replace count / false abstain count: "
        f"`{int(row.get('harmful_replace_count') or 0)}` / "
        f"`{int(row.get('false_abstain_count') or 0)}`",
        f"- Decision accuracy / harmful replace / false abstain: "
        f"`{_render_rate(row.get('decision_accuracy'))}` / "
        f"`{_render_rate(row.get('harmful_replace_rate'))}` / "
        f"`{_render_rate(row.get('false_abstain_rate'))}`",
        f"- Replace precision / recall: "
        f"`{_render_rate(row.get('replace_precision'))}` / "
        f"`{_render_rate(row.get('replace_recall'))}`",
        f"- Winner accuracy / shadow-winner accuracy: "
        f"`{_render_rate(row.get('winner_accuracy'))}` / "
        f"`{_render_rate(row.get('shadow_winner_accuracy'))}`",
    ]


def _render_sentence_veto_breakdown_table(
    rows: object,
    *,
    label_key: str,
    label_builder: object | None = None,
    limit: int | None = None,
) -> list[str]:
    lines = [
        "| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        lines.append("| none | 0 | n/a | n/a | n/a | n/a |")
        return lines
    rendered_count = 0
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        label = ""
        if callable(label_builder):
            label = str(label_builder(row) or "").strip()
        if not label:
            label = str(row.get(label_key) or "").strip()
        if not label:
            continue
        lines.append(
            "| "
            + " | ".join(
                (
                    label,
                    str(int(summary.get("cases_total") or 0)),
                    _render_rate(summary.get("decision_accuracy")),
                    _render_rate(summary.get("replace_recall")),
                    _render_rate(summary.get("harmful_replace_rate")),
                    _render_rate(summary.get("winner_accuracy")),
                )
            )
            + " |"
        )
        rendered_count += 1
        if limit is not None and rendered_count >= max(0, int(limit)):
            break
    if rendered_count <= 0:
        lines.append("| none | 0 | n/a | n/a | n/a | n/a |")
    return lines


def _build_family_breakdown_label(row: Mapping[str, object]) -> str:
    trigger = str(row.get("trigger") or "").strip()
    active_target = str(row.get("active_target") or "").strip()
    shadow_targets = _normalize_string_list(row.get("shadow_targets"))
    if trigger and active_target and shadow_targets:
        return f"{trigger} -> {active_target} vs {', '.join(shadow_targets)}"
    if trigger and active_target:
        return f"{trigger} -> {active_target}"
    return str(row.get("family_id") or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"
