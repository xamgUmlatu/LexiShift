from __future__ import annotations

import json
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
    _safe_float,
)


CASE_TYPES = ("positive_active", "shadow_negative", "phrase_no_winner")
PRIMARY_TARGET_ID = "base_product_prior"


def _target_metrics(band: Mapping[str, object], target_id: str) -> dict[str, object]:
    for row in _mapping_rows(band.get("target_normalized_metrics")):
        if str(row.get("target_id") or "") == target_id:
            return dict(row)
    return {}


def render_product_scope_band_grading_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Product-Scope Band Grading",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Formula scopes: `{summary.get('formula_scope_count', 0)}`",
        f"- Score-surface rows: `{summary.get('score_surface_row_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("purpose") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("normalization_boundary") or ""),
        "",
        "## Normalization Targets",
        "",
        _target_table(report.get("normalization_targets")),
        "",
        "## Best By Primary Band Grade",
        "",
        _grade_table(_as_mapping(summary).get("best_by_primary_band_grade")),
        "",
        "## Representative Comparison",
        "",
        _grade_table(_as_mapping(summary).get("representative_comparison")),
        "",
        "## Top Band Details",
        "",
        _detail_table(report.get("top_formula_band_details")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _target_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No normalization targets._"
    headers = ["target", "positive", "shadow", "phrase/no-winner", "source"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        weights = _as_mapping(row.get("case_type_weights"))
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("target_id") or ""),
                    _format_percent(weights.get("positive_active")),
                    _format_percent(weights.get("shadow_negative")),
                    _format_percent(weights.get("phrase_no_winner")),
                    str(row.get("source") or ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _grade_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No grade rows._"
    headers = [
        "scorer",
        "formula",
        "raw high-low",
        "SRS high-low",
        "order",
        "measured min",
        "unmeasured max",
        "grade",
        "bands",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("scorer_id") or ""),
                    str(row.get("formula_id") or ""),
                    _format_signed_percent(row.get("raw_high_low_failure_delta")),
                    _format_signed_percent(row.get("primary_normalized_high_low_failure_delta")),
                    _number(row.get("primary_normalized_order_score")),
                    _format_percent(row.get("primary_min_measured_target_weight")),
                    _format_percent(row.get("primary_max_unmeasured_target_weight")),
                    _number(row.get("primary_grade_score")),
                    json.dumps(row.get("band_family_counts") or {}, sort_keys=True),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _detail_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)[:12]
    if not rows:
        return "_No detail rows._"
    headers = [
        "scorer",
        "formula",
        "band",
        "families",
        "cases",
        "raw failure",
        "SRS measured failure",
        "SRS unmeasured",
        "case-type counts",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        for band in _mapping_rows(row.get("band_metrics")):
            target = _target_metrics(band, PRIMARY_TARGET_ID)
            lines.append(
                "| "
                + " | ".join(
                    _escape_md(value)
                    for value in [
                        str(row.get("scorer_id") or ""),
                        str(row.get("formula_id") or ""),
                        str(band.get("band_id") or ""),
                        str(band.get("family_count") or 0),
                        str(band.get("case_count") or 0),
                        _format_percent(band.get("raw_failure_rate")),
                        _format_percent(target.get("measured_only_failure_rate")),
                        _format_percent(target.get("unmeasured_target_weight")),
                        _case_type_count_cell(band.get("case_type_metrics")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines)


def _case_type_count_cell(metrics_obj: object) -> str:
    metrics = _as_mapping(metrics_obj)
    return ", ".join(
        f"{case_type}:{int(_as_mapping(metrics.get(case_type)).get('case_count') or 0)}"
        for case_type in CASE_TYPES
    )


def _sample_triggers(rows: Sequence[Mapping[str, object]]) -> list[str]:
    seen = []
    for row in rows:
        trigger = str(row.get("trigger") or row.get("source_phrase") or "")
        if trigger and trigger not in seen:
            seen.append(trigger)
        if len(seen) >= 8:
            break
    return seen


def _format_signed_percent(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{100 * _safe_float(value):+.1f}%"


def _number(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_safe_float(value):.4f}"
