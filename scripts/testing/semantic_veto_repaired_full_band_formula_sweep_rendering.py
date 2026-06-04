from __future__ import annotations

import json
from typing import Mapping

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
    _safe_float,
)


def _number(value: object) -> str:
    number = _safe_float(value)
    if value is None:
        return "n/a"
    return f"{number:.4f}"


def _comparison_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    headers = [
        "scope",
        "formula",
        "family",
        "scorer",
        "discovery rho",
        "locked rho",
        "top-k lift",
        "brier",
        "top triggers",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("scope_id") or ""),
                    str(row.get("formula_id") or ""),
                    str(row.get("formula_family") or ""),
                    str(row.get("scorer_id") or ""),
                    _number(row.get("discovery_spearman")),
                    _number(row.get("internal_locked_eval_spearman")),
                    _number(row.get("top_k_lift")),
                    _number(row.get("brier_score")),
                    ", ".join(str(item) for item in row.get("top_k_triggers", [])[:5]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_repaired_full_band_formula_sweep_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Repaired-Full Band Formula Sweep",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Observations: `{summary.get('observation_count', 0)}`",
        f"- Fixed formulas: `{summary.get('fixed_formula_count', 0)}`",
        f"- Sweep formulas: `{summary.get('sweep_formula_count', 0)}`",
        f"- Split counts: `{json.dumps(summary.get('split_counts', {}), sort_keys=True)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("purpose") or ""),
        "",
        "Formula inputs are family-level signals that can be computed before seeing the "
        "test outcomes. Gold labels and predicted outcomes are used only for evaluation.",
        "",
        "## Best Formula By Scope",
        "",
        _comparison_table(summary.get("best_by_scope")),
        "",
        "## Top Need Rows",
        "",
        _top_need_table(report.get("top_need_rows")),
        "",
        "## Formula Definitions",
        "",
        _definition_table(report.get("formula_definitions")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _definition_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    lines = ["| Formula family | Description |", "| --- | --- |"]
    for row in rows:
        lines.append(
            f"| `{_escape_md(str(row.get('formula_family') or ''))}` | "
            f"{_escape_md(str(row.get('description') or ''))} |"
        )
    return "\n".join(lines)


def _top_need_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    headers = [
        "scorer",
        "rank",
        "trigger",
        "target",
        "need",
        "observed failure",
        "cases",
        "formula",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("scorer_id") or ""),
                    str(row.get("priority_rank") or ""),
                    str(row.get("trigger") or ""),
                    str(row.get("target_lemma") or ""),
                    _number(row.get("predicted_need")),
                    _format_percent(row.get("observed_failure_rate")),
                    f"{row.get('failure_count', 0)} / {row.get('case_count', 0)}",
                    ", ".join(str(item) for item in row.get("formula_ids", [])),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
