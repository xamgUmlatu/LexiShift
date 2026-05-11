from __future__ import annotations

from typing import Mapping

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
)


def render_active_only_full_generation_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Active-Only Full Generation Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Denominator source-target families: `{summary.get('denominator_family_count', 0)}`",
        f"- Current active-only covered families: `{summary.get('covered_denominator_family_count', 0)}` ({_format_percent(summary.get('covered_denominator_family_share'))})",
        f"- Uncovered active-only families: `{summary.get('uncovered_family_count', 0)}`",
        f"- Runnable request packet families: `{summary.get('selected_request_family_count', 0)}`",
        f"- Runnable request packet expected items: `{summary.get('selected_expected_generated_item_count', 0)}`",
        f"- Runnable request packet estimated input tokens: `{summary.get('selected_estimated_input_tokens', 0)}`",
        f"- Runnable request packet output-token budget: `{summary.get('selected_expected_output_token_budget', 0)}`",
        f"- Source-target review: `{_source_target_review_summary_label(summary)}`",
        "",
        "## What This Means",
        "",
        "The current pack is a product-smoke control, not full en-es coverage. This "
        "report treats the SRS Zipf bridge full source-target pairs as the current "
        "installed en-es semantic-veto denominator, then prepares only the next "
        "active-only tranche for safe generation.",
        "",
        "## Source-Band Coverage",
        "",
        _coverage_table(report.get("coverage_by_source_band"), "Band"),
        "",
        "## Target-Band Coverage",
        "",
        _coverage_table(report.get("coverage_by_target_band"), "Band"),
        "",
        "## Queue Plan",
        "",
        "Known rejected source-target rows are excluded from this queue, but future "
        "tranche rows may still require the same pre-spend review before live calls.",
        "",
        "| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("tranche_plan")):
        tier_mix = ", ".join(
            f"{key}:{value}" for key, value in _as_mapping(row.get("priority_tier_counts")).items()
        )
        lines.append(
            f"| `{_escape_md(str(row.get('tranche_id') or ''))}` | "
            f"{row.get('family_count', 0)} | {row.get('request_count', 0)} | "
            f"{row.get('expected_generated_item_count', 0)} | "
            f"{row.get('estimated_input_tokens', 0)} | "
            f"{row.get('expected_output_token_budget', 0)} | "
            f"{_escape_md(tier_mix)} |"
        )
    lines.extend(
        [
            "",
            "## Selected Request Families",
            "",
            "| Rank | Tier | Source | Target | Source band | Target band | Need | Review |",
            "| ---: | --- | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("selected_request_families"))[:75]:
        lines.append(
            f"| {row.get('global_need_rank', 0)} | "
            f"`{_escape_md(str(row.get('priority_tier') or ''))}` | "
            f"`{_escape_md(str(row.get('source') or ''))}` | "
            f"`{_escape_md(str(row.get('target') or ''))}` | "
            f"`{_escape_md(str(row.get('source_zipf_band_en') or ''))}` | "
            f"`{_escape_md(str(row.get('target_zipf_band_es') or ''))}` | "
            f"{float(row.get('active_only_generation_need_score') or 0.0):.4f} | "
            f"`{_escape_md(str(row.get('source_target_review_decision') or ''))}` |"
        )
    lines.extend(["", *_run_command_section(summary), "", "## Guardrails", ""])
    lines.extend(["| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(str(key))}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", []))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", []))
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("issues", []))
    return "\n".join(lines) + "\n"


def _coverage_table(value: object, label: str) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No coverage rows available."
    lines = [
        f"| {label} | Families | Covered | Covered Share | Uncovered | Sample Uncovered |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        samples = ", ".join(
            f"`{_escape_md(str(sample.get('source') or ''))}` -> "
            f"`{_escape_md(str(sample.get('target') or ''))}`"
            for sample in _mapping_rows(row.get("sample_uncovered"))[:6]
        )
        band = str(row.get("source_band") or row.get("target_band") or "")
        lines.append(
            f"| `{_escape_md(band)}` | {row.get('family_count', 0)} | "
            f"{row.get('covered_family_count', 0)} | "
            f"{_format_percent(row.get('covered_share'))} | "
            f"{row.get('uncovered_family_count', 0)} | {samples} |"
        )
    return "\n".join(lines)


def _source_target_review_summary_label(summary: Mapping[str, object]) -> str:
    if not bool(summary.get("source_target_review_active")):
        return "not_applied"
    counts = _as_mapping(summary.get("source_target_review_status_counts"))
    if not counts:
        return "applied"
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items()))


def _run_command_section(summary: Mapping[str, object]) -> list[str]:
    selected_request_count = int(summary.get("selected_request_count") or 0)
    if selected_request_count <= 0:
        return [
            "## No Runnable Paid Command Yet",
            "",
            "The selected request packet is empty. Expand source-target review before "
            "running the paid generation harness.",
        ]
    return [
        "## Safe First-Run Command Shape",
        "",
        "```bash",
        "python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \\",
        "  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_latest.json \\",
        f"  --run-id {_safe_first_run_id(summary)} \\",
        f"  --max-requests {selected_request_count} \\",
        f"  --require-selected-request-count {selected_request_count} \\",
        f"  --expected-output-tokens {_expected_output_tokens_per_request(summary)} \\",
        "  --input-rate-per-1m <current-input-rate> \\",
        "  --output-rate-per-1m <current-output-rate> \\",
        "  --max-estimated-cost-usd <small-tranche-budget> \\",
        "  --max-estimated-cost-ceiling-usd <small-tranche-ceiling> \\",
        "  --execute-live --resume",
        "```",
    ]


def _safe_first_run_id(summary: Mapping[str, object]) -> str:
    if bool(summary.get("source_target_review_active")):
        return "en-es-active-only-full-v1-tranche-001-approved"
    return "en-es-active-only-full-v1-tranche-001"


def _expected_output_tokens_per_request(summary: Mapping[str, object]) -> int:
    request_count = int(summary.get("selected_request_count") or 0)
    output_budget = int(summary.get("selected_expected_output_token_budget") or 0)
    if request_count <= 0 or output_budget <= 0:
        return 180
    return max(1, int(round(output_budget / request_count)))
