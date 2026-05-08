from __future__ import annotations

import json
from typing import Mapping

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
)
from semantic_veto_translation_ambiguity_heuristic_common import _number


def render_translation_ambiguity_heuristic_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    signal = _as_mapping(summary.get("signal_summary"))
    lines = [
        "# en-es Semantic Veto Translation-Ambiguity Heuristic Bakeoff",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory sources: `{summary.get('inventory_source_count', 0)}`",
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
        "Formula inputs are programmatic pre-outcome signals. Gold labels and predicted "
        "veto outcomes are used only to evaluate whether a heuristic actually ranks "
        "hard families higher.",
        "",
        "## Signal Read",
        "",
        f"- Best stable formula: `{signal.get('best_stable_formula_id', 'none')}`",
        f"- Best stable scorer: `{signal.get('best_stable_scorer_id', 'none')}`",
        f"- Best stable locked rho: `{_number(signal.get('best_stable_locked_spearman'))}`",
        f"- Best stable top-k lift: `{_number(signal.get('best_stable_top_k_lift'))}`",
        f"- Strong allocator found: `{signal.get('strong_allocator_found', False)}`",
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
                    str(row.get("formula_id") or ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


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
                    ", ".join(str(item) for item in row.get("top_k_triggers", [])[:5]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
