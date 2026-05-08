from __future__ import annotations

from typing import Mapping

from semantic_veto_heuristic_difficulty_surface_common import (
    _as_mapping,
    _escape_md,
    _mapping_rows,
    _sequence,
)
from semantic_veto_product_quality_en_es import _format_percent


def render_heuristic_difficulty_surface_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    overall = _as_mapping(summary.get("overall"))
    primary = _as_mapping(summary.get("primary_only"))
    lines = [
        "# en-es Semantic Veto Heuristic Difficulty Surface",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Score rows: `{summary.get('score_row_count', 0)}`",
        f"- Authored triggers: `{summary.get('authored_trigger_count', 0)}`",
        f"- Primary rows / sentinel rows: `{summary.get('primary_score_row_count', 0)}` / `{summary.get('sentinel_score_row_count', 0)}`",
        f"- Overall difficulty: `{_format_percent(_as_mapping(overall.get('difficulty_scores')).get('overall_veto_difficulty'))}`",
        f"- Primary-only difficulty: `{_format_percent(_as_mapping(primary.get('difficulty_scores')).get('overall_veto_difficulty'))}`",
        "",
        "## Methodology",
        "",
        "This report treats the current frequency/polysemy heuristic as a control, "
        "not as the final formula. It compares source-word features, case shape, "
        "score-surface features, and observed product outcomes while keeping the "
        "outcome-informed sentinel group out of primary heuristic validation.",
        "",
        "## Scorer Summary",
        "",
        _breakdown_table(_as_mapping(report.get("breakdowns")).get("scorer")),
        "",
        "## Case-Type Difficulty",
        "",
        _breakdown_table(_as_mapping(report.get("breakdowns")).get("scorer_x_manual_case_type")),
        "",
        "## Primary Heuristic Groups",
        "",
        _breakdown_table(
            _as_mapping(report.get("breakdowns")).get("primary_scorer_x_heuristic_group")
        ),
        "",
        "## Formula Bakeoff",
        "",
        _formula_table(_as_mapping(report.get("formula_bakeoff")).get("comparison_rows")),
        "",
        "## Failure Concentration",
        "",
        _failure_table(report.get("failure_concentration")),
        "",
        "## Expansion Planner",
        "",
        _expansion_table(_as_mapping(report.get("expansion_plan")).get("recommendations")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _breakdown_table(value: object, *, limit: int = 18) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Scope | Cases | Pos allow | Neg abstain | Pos diff | Shadow diff | Phrase diff | Overall diff |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:limit]:
        metrics = _as_mapping(row.get("metrics"))
        difficulty = _as_mapping(metrics.get("difficulty_scores"))
        scope = str(row.get("scope_id") or row.get("value") or "")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(scope)}`",
                    str(int(metrics.get("case_count") or row.get("case_rows") or 0)),
                    _format_percent(metrics.get("positive_allow_rate")),
                    _format_percent(metrics.get("negative_abstain_rate")),
                    _format_percent(difficulty.get("positive_allow_difficulty")),
                    _format_percent(difficulty.get("shadow_negative_difficulty")),
                    _format_percent(difficulty.get("phrase_no_winner_difficulty")),
                    _format_percent(difficulty.get("overall_veto_difficulty")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _formula_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No formula rows._"
    lines = [
        "| Formula | Scorer | Compared | Excluded sentinel | Excluded missing rank | Spearman r | Top predicted triggers |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        top = ", ".join(
            f"{item.get('trigger')}:{_format_percent(item.get('observed_difficulty'))}"
            for item in _mapping_rows(row.get("top_predicted"))[:4]
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('formula_id') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    str(int(row.get("compared_triggers") or 0)),
                    str(int(row.get("excluded_sentinel_triggers") or 0)),
                    str(int(row.get("excluded_missing_rank_triggers") or 0)),
                    str(row.get("spearman_rank_correlation")),
                    _escape_md(top),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No failure concentration rows._"
    lines = [
        "| Dimension | Value | Scorer | Cases | Failures | Failure rate | Failure share | Pos abstain | Neg allow |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:16]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('dimension') or ''))}`",
                    f"`{_escape_md(str(row.get('value') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    str(int(row.get("case_rows") or 0)),
                    str(int(row.get("failure_count") or 0)),
                    _format_percent(row.get("failure_rate")),
                    _format_percent(row.get("failure_share_of_scorer_failures")),
                    str(int(row.get("positive_abstain_count") or 0)),
                    str(int(row.get("negative_allow_count") or 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _expansion_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No expansion recommendations._"
    lines = [
        "| Priority | Cell | Reason | Action | Manual | LLM discovery | Locked eval |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows[:20]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('priority') or ''))}`",
                    f"`{_escape_md(str(row.get('cell_id') or ''))}`",
                    f"`{_escape_md(str(row.get('reason') or ''))}`",
                    _escape_md(str(row.get("recommended_action") or "")),
                    str(int(row.get("manual_discovery_rows") or 0)),
                    str(int(row.get("llm_discovery_rows") or 0)),
                    str(int(row.get("locked_eval_rows") or 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
