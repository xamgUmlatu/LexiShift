from __future__ import annotations

from typing import Mapping

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
)


def _matrix_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No source-target family rows are available in the current input."
    lines = [
        "| Source Band | Target Band | Families | Share | Sample Families |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        samples = []
        for pair in _mapping_rows(row.get("sample_families"))[:8]:
            samples.append(
                f"`{_escape_md(str(pair.get('source') or ''))}` -> "
                f"`{_escape_md(str(pair.get('target') or ''))}`"
            )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source_zipf_band_en') or ''))}`",
                    f"`{_escape_md(str(row.get('target_zipf_band_es') or ''))}`",
                    str(int(row.get("family_count") or 0)),
                    _format_percent(row.get("share")),
                    ", ".join(samples),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _target_scope_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Scope | Band | Targets | Share | Weight Share | Sample Terms |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for scope in rows:
        for row in _mapping_rows(scope.get("breakdowns")):
            count = int(row.get("target_count") or 0)
            if count == 0:
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{_escape_md(str(scope.get('scope_id') or ''))}`",
                        f"`{_escape_md(str(row.get('zipf_band') or ''))}`",
                        str(count),
                        _format_percent(row.get("share")),
                        _format_percent(row.get("weight_share")),
                        ", ".join(
                            f"`{_escape_md(str(term))}`"
                            for term in list(row.get("sample_terms") or [])[:8]
                        ),
                    ]
                )
                + " |"
            )
    return "\n".join(lines)


def render_srs_zipf_bridge_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto SRS Zipf Bridge",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Full SRS-admissible targets: `{summary.get('full_srs_admissible_target_count', 0)}`",
        f"- Journey candidate-slice targets: `{summary.get('journey_srs_candidate_target_count', 0)}`",
        f"- Selected initial-active targets: `{summary.get('srs_selected_initial_active_count', 0)}`",
        f"- Journey source-target pairs: `{summary.get('journey_union_source_target_pair_count', 0)}`",
        f"- Full source-target pairs: `{summary.get('full_source_target_pair_count', 0)}`",
        f"- Source mapping status: `{summary.get('source_mapping_status', '')}`",
        f"- Full targets very-common/common: `{summary.get('full_target_very_common_or_common_count', 0)}` ({_format_percent(summary.get('full_target_very_common_or_common_share'))})",
        f"- Journey targets very-common/common: `{summary.get('journey_candidate_target_very_common_or_common_count', 0)}` ({_format_percent(summary.get('journey_candidate_target_very_common_or_common_share'))})",
        "",
        "## Target-Side SRS Distribution",
        "",
        _target_scope_table(report.get("target_zipf_scopes_es")),
        "",
        "## Source-Side Rule Distribution",
        "",
        "### Full Generated Rule Sources",
        "",
        _source_scope_table(_as_mapping(report.get("full_source_zipf_scope_en"))),
        "",
        "### Journey Rule Sources",
        "",
        _source_scope_table(_as_mapping(report.get("source_zipf_scope_en"))),
        "",
        "## Full Source-Target Family Matrix",
        "",
        _matrix_table(report.get("full_source_target_family_zipf_matrix")),
        "",
        "## Journey Source-Target Family Matrix",
        "",
        _matrix_table(report.get("source_target_family_zipf_matrix")),
        "",
        "## Interpretation",
        "",
        "- The full SRS-admissible target distribution is the denominator for possible user learning exposure under current installed resources.",
        "- The journey slice remains useful as a runtime harness, but it is not the corpus-level denominator.",
        "- The English source-trigger distribution is the denominator for semantic-veto evidence cost.",
        "- Cost planning should join both: high-exposure SRS targets only need LLM semantic-veto data when their published source-trigger families are ambiguity-prone.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _source_scope_table(scope: Mapping[str, object]) -> str:
    lines = [
        "| Scope | Band | Sources | Share | Sample Terms |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in _mapping_rows(scope.get("breakdowns")):
        count = int(row.get("source_count") or 0)
        if count == 0:
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(scope.get('scope_id') or ''))}`",
                    f"`{_escape_md(str(row.get('zipf_band') or ''))}`",
                    str(count),
                    _format_percent(row.get("share")),
                    ", ".join(
                        f"`{_escape_md(str(term))}`"
                        for term in list(row.get("sample_terms") or [])[:8]
                    ),
                ]
            )
            + " |"
        )
    if len(lines) == 2:
        lines.append("| `none` | `n/a` | 0 | n/a |  |")
    return "\n".join(lines)
