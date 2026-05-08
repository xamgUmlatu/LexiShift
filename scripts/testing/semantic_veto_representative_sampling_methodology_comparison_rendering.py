from __future__ import annotations

from typing import Mapping

from semantic_veto_product_quality_en_es import _as_mapping, _escape_md, _mapping_rows
from semantic_veto_representative_sampling_methodology_comparison_core import _fmt


def render_sampling_methodology_comparison_markdown(report: Mapping[str, object]) -> str:
    comparison = _as_mapping(report.get("comparison"))
    old = _as_mapping(comparison.get("old_heuristic_group_pilot"))
    new = _as_mapping(comparison.get("representative_sampler"))
    delta = _as_mapping(comparison.get("delta"))
    stability = _as_mapping(report.get("sampling_stability"))
    lines = [
        "# en-es Semantic Veto Sampling Methodology Comparison",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        "",
        "## Main Comparison",
        "",
        "| Metric | Old heuristic-group pilot | Representative sampler | Delta / Read |",
        "| --- | ---: | ---: | --- |",
        f"| selected/source sampled triggers | {old.get('primary_selected_trigger_count', 0)} primary + {old.get('sentinel_trigger_count', 0)} sentinel | {new.get('sampled_trigger_count', 0)} | {delta.get('sampled_trigger_multiplier_vs_old_primary', '')}x sampled vs old primary |",
        f"| candidate universe | {old.get('candidate_pool_count', 0)} | {new.get('candidate_universe_count', 0)} | same eligible pool |",
        f"| represented non-empty fine cells | {old.get('primary_new_cell_coverage_count', 0)} / {new.get('nonempty_cell_count', 0)} | {new.get('sampled_nonempty_cell_count', 0)} / {new.get('nonempty_cell_count', 0)} | representative sampler covers all non-empty cells |",
        f"| source-ready target families | not measured on old pilot | {new.get('source_ready_family_count', 0)} / {new.get('construction_attempt_count', 0)} | construction coverage, not accuracy |",
        "",
        "The old lane selected four words per coarse primary group. It was not random: "
        "within each group it sorted by source rank, then by high WordNet sense/POS "
        "counts. The new lane samples inside every non-empty fine cell and records "
        "weights so universe-level means do not treat rare cells as common cells.",
        "",
        "## Old Group Bias",
        "",
        "| Group | Eligible | Selected | Selected share | Selected rank mean | Eligible rank mean |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in _mapping_rows(old.get("primary_group_bias")):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('group_id') or ''))}`",
                    str(row.get("eligible_count") or 0),
                    str(row.get("selected_count") or 0),
                    _fmt(row.get("selected_share")),
                    _fmt(row.get("selected_rank_mean")),
                    _fmt(row.get("eligible_rank_mean")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Sampling Stability",
            "",
            "| Sample per cell | Runs | Sample count range | Cell coverage | Mean pairwise overlap | Max weighted rank TVD |",
            "| ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(stability.get("by_sample_size")):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("sample_per_cell") or ""),
                    str(row.get("run_count") or 0),
                    f"{row.get('sampled_trigger_count_min', 0)}-{row.get('sampled_trigger_count_max', 0)}",
                    f"{_fmt(row.get('nonempty_cell_coverage_rate_min'))}-{_fmt(row.get('nonempty_cell_coverage_rate_max'))}",
                    _fmt(row.get("mean_pairwise_jaccard")),
                    _fmt(row.get("weighted_rank_tvd_max")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Weighted rank/polysemy/POS distributions match the candidate universe for "
            "the cell-defining features whenever every non-empty cell has a sample. "
            "That does not prove downstream source-ready or scoring rates; it only "
            "means the source-band frame is no longer the old hard-case slice.",
            "",
            "## Construction Stability",
            "",
            "| Sample per cell | Runs | Source-ready rate range | Source-ready count range | Weak count range | Blocked count range |",
            "| ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    construction_stability = _as_mapping(report.get("construction_stability"))
    for row in _mapping_rows(construction_stability.get("by_sample_size")):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("sample_per_cell") or ""),
                    str(row.get("run_count") or 0),
                    f"{_fmt(row.get('source_ready_rate_min'))}-{_fmt(row.get('source_ready_rate_max'))}",
                    f"{row.get('source_ready_family_count_min', 0)}-{row.get('source_ready_family_count_max', 0)}",
                    f"{row.get('weak_diagnostic_family_count_min', 0)}-{row.get('weak_diagnostic_family_count_max', 0)}",
                    f"{row.get('blocked_count_min', 0)}-{row.get('blocked_count_max', 0)}",
                ]
            )
            + " |"
        )
    if not _mapping_rows(construction_stability.get("by_sample_size")):
        lines.append("| _not run_ | 0 |  |  |  |  |")
    lines.extend(
        [
            "",
            "This is still construction coverage, not final allow/abstain accuracy. It "
            "tests whether the low source-ready rate is tied to one unlucky seed.",
            "",
            "## Sweep Rerun Status",
            "",
            "| Sweep | Status | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("sweep_rerun_status")):
        lines.append(
            f"| `{_escape_md(str(row.get('sweep') or ''))}` | "
            f"`{_escape_md(str(row.get('status') or ''))}` | "
            f"{_escape_md(str(row.get('reason') or ''))} |"
        )
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"
