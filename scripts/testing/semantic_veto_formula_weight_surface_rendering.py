from __future__ import annotations

from typing import Mapping

from semantic_veto_formula_shape_bakeoff_common import _sequence
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _mapping_rows,
    _safe_float,
)


def render_formula_weight_surface_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Formula Weight Surface",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Cells: `{summary.get('cell_count', 0)}`",
        f"- Primary cells: `{summary.get('primary_cell_count', 0)}`",
        f"- Sweeps: `{summary.get('sweep_count', 0)}`",
        "",
        "## Sweep Maxima",
        "",
        _sweep_summary_table(summary.get("sweep_overview")),
        "",
        "## Feature Curves",
        "",
        _feature_curve_table(report.get("sweep_reports")),
        "",
        "## Pairwise Probes",
        "",
        _pairwise_curve_table(report.get("sweep_reports")),
        "",
        "## Interpretation",
        "",
    ]
    for row in _mapping_rows(summary.get("sweep_overview")):
        lines.append(
            f"- `{row.get('sweep_id', '')}`: `{row.get('surface_shape', '')}`; "
            f"discovery-locked gap `{_metric(row.get('overfit_gap'))}`; "
            f"plateau fraction `{_metric(row.get('plateau_fraction'))}`."
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _feature_curve_table(value: object, *, limit: int = 24) -> str:
    rows = [
        dict(row, sweep_id=sweep.get("sweep_id"))
        for sweep in _mapping_rows(value)
        for row in _mapping_rows(sweep.get("feature_curve_summaries"))
    ]
    if not rows:
        return "_No rows._"
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("best_discovery_spearman")),
            str(row.get("sweep_id") or ""),
            str(row.get("curve_id") or ""),
        )
    )
    lines = [
        "| Sweep | Curve | Selected alpha | Best alpha | Best discovery rho | Best locked rho | Shape |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('sweep_id') or ''))}`",
                    f"`{_escape_md(str(row.get('curve_id') or ''))}`",
                    _metric(row.get("selected_alpha")),
                    _metric(row.get("best_alpha")),
                    _metric(row.get("best_discovery_spearman")),
                    _metric(row.get("best_locked_spearman")),
                    f"`{_escape_md(str(row.get('curve_shape') or ''))}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _sweep_summary_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Sweep | Samples | Discovery rho | Locked rho | Primary rho | Top-k lift | Plateau | Discovery-locked gap | Shape |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('sweep_id') or ''))}`",
                    str(row.get("sampled_candidate_count") or 0),
                    _metric(row.get("selected_discovery_spearman")),
                    _metric(row.get("selected_locked_spearman")),
                    _metric(row.get("selected_primary_spearman")),
                    _metric(row.get("selected_top_k_lift")),
                    _metric(row.get("plateau_fraction")),
                    _metric(row.get("overfit_gap")),
                    f"`{_escape_md(str(row.get('surface_shape') or ''))}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _pairwise_curve_table(value: object, *, limit: int = 18) -> str:
    rows = [
        dict(row, sweep_id=sweep.get("sweep_id"))
        for sweep in _mapping_rows(value)
        for row in _mapping_rows(sweep.get("pairwise_curve_summaries"))
    ]
    if not rows:
        return "_No rows._"
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("best_discovery_spearman")),
            str(row.get("sweep_id") or ""),
            str(row.get("curve_id") or ""),
        )
    )
    lines = [
        "| Sweep | Pair | Best left alpha | Best discovery rho | Best locked rho | Shape |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('sweep_id') or ''))}`",
                    f"`{_escape_md(str(row.get('curve_id') or ''))}`",
                    _metric(row.get("best_left_alpha")),
                    _metric(row.get("best_discovery_spearman")),
                    _metric(row.get("best_locked_spearman")),
                    f"`{_escape_md(str(row.get('curve_shape') or ''))}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _metric(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
