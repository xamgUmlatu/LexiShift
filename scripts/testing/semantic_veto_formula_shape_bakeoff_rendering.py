from __future__ import annotations

from typing import Mapping

from semantic_veto_product_quality_en_es import _as_mapping, _escape_md, _mapping_rows, _safe_float
from semantic_veto_formula_shape_bakeoff_common import _metric, _sequence


def render_formula_shape_bakeoff_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Formula-Shape Bakeoff",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Cells: `{summary.get('cell_count', 0)}`",
        f"- Primary cells / sentinel cells: `{summary.get('primary_cell_count', 0)}` / `{summary.get('sentinel_cell_count', 0)}`",
        f"- Formula count: `{summary.get('formula_count', 0)}`",
        "",
        "## Methodology",
        "",
        "This report compares formula shapes for ranking cells that need more "
        "manual or LLM data. It does not change runtime policy. Sentinel cells "
        "are excluded from primary validation, and missing rank is represented "
        "as its own indicator instead of being silently imputed.",
        "",
        "## Best Formula By Scope",
        "",
        _comparison_table(summary.get("best_formula_by_scope")),
        "",
        "## Primary Formula Comparison",
        "",
        _comparison_table(report.get("comparison_rows"), primary_only=True),
        "",
        "## Parameter Sweeps",
        "",
        _parameter_sweep_table(report.get("parameter_sweep_results")),
        "",
        "## Negative Controls",
        "",
        _negative_control_table(report.get("negative_control_rows")),
        "",
        "## Calibration",
        "",
        _calibration_table(report.get("calibration_rows")),
        "",
        "## Top Data-Help Cells",
        "",
        _priority_table(report.get("top_priority_cells")),
        "",
        "## Recommendations",
        "",
    ]
    for row in _mapping_rows(report.get("recommendations")):
        lines.append(
            f"- `{row.get('priority', '')}` `{row.get('cell_id', '')}`: "
            f"{row.get('recommended_action', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _comparison_table(value: object, *, primary_only: bool = False, limit: int = 20) -> str:
    rows = _mapping_rows(value)
    if primary_only:
        rows = [row for row in rows if str(row.get("scope_id") or "") == "primary_all_scorers"]
    if not rows:
        return "_No rows._"
    lines = [
        "| Formula | Scope | Cells | Spearman | Kendall | Brier | Top-k lift | Priority lift | Locked Spearman |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('formula_id') or ''))}`",
                    f"`{_escape_md(str(row.get('scope_id') or ''))}`",
                    str(row.get("cell_count") or 0),
                    _metric(row.get("spearman_rank_correlation")),
                    _metric(row.get("kendall_tau")),
                    _metric(row.get("brier_score")),
                    _metric(row.get("top_k_lift")),
                    _metric(row.get("priority_top_k_lift")),
                    _metric(row.get("internal_locked_eval_spearman")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _parameter_sweep_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Sweep | Samples | Selected Formula | Discovery Spearman | Discovery Brier | Locked Spearman | Primary Spearman | Top weights |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        discovery = _as_mapping(row.get("selected_discovery_metrics"))
        locked = _as_mapping(row.get("selected_internal_locked_eval_metrics"))
        primary = _as_mapping(row.get("selected_primary_all_metrics"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('sweep_id') or ''))}`",
                    str(row.get("sampled_candidate_count") or 0),
                    f"`{_escape_md(str(row.get('formula_id') or ''))}`",
                    _metric(discovery.get("spearman_rank_correlation")),
                    _metric(discovery.get("brier_score")),
                    _metric(locked.get("spearman_rank_correlation")),
                    _metric(primary.get("spearman_rank_correlation")),
                    _escape_md(_top_weight_summary(row.get("selected_weights"))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _top_weight_summary(value: object, *, limit: int = 4) -> str:
    if not isinstance(value, Mapping):
        return ""
    flat: list[tuple[str, float]] = []
    for key, raw in value.items():
        if isinstance(raw, Mapping):
            for sub_key, sub_value in raw.items():
                flat.append((f"{key}.{sub_key}", _safe_float(sub_value)))
        else:
            flat.append((str(key), _safe_float(raw)))
    flat.sort(key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{key}={weight:.2f}" for key, weight in flat[:limit])


def _negative_control_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Control | Cells | Spearman | Brier | Top-k lift | Priority lift |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('formula_id') or ''))}`",
                    str(row.get("cell_count") or 0),
                    _metric(row.get("spearman_rank_correlation")),
                    _metric(row.get("brier_score")),
                    _metric(row.get("top_k_lift")),
                    _metric(row.get("priority_top_k_lift")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _calibration_table(value: object, *, limit: int = 24) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Formula | Scorer | Bucket | Cells | Predicted | Observed | Abs error |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('formula_id') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    f"`{_escape_md(str(row.get('bucket_id') or ''))}`",
                    str(row.get("cell_count") or 0),
                    _metric(row.get("predicted_mean")),
                    _metric(row.get("observed_mean")),
                    _metric(row.get("absolute_error")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _priority_table(value: object, *, limit: int = 18) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Formula | Cell | Type | Group | Scorer | Risk | Observed | Priority | Rows | Triggers |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:limit]:
        triggers = ", ".join(str(item) for item in _sequence(row.get("triggers"))[:4])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('formula_id') or ''))}`",
                    f"`{_escape_md(str(row.get('cell_id') or ''))}`",
                    f"`{_escape_md(str(row.get('manual_case_type') or ''))}`",
                    f"`{_escape_md(str(row.get('heuristic_group') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    _metric(row.get("predicted_failure_risk")),
                    _metric(row.get("posterior_failure_rate")),
                    _metric(row.get("normalized_data_help_priority")),
                    str(row.get("case_rows") or 0),
                    _escape_md(triggers),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
