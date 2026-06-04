from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_difficulty_stratification_common import _sequence
from semantic_veto_product_quality_en_es import _as_mapping, _escape_md, _format_percent
from semantic_veto_veto_only_probe_en_es import _mapping_rows


def render_difficulty_stratification_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    diagnostics = _as_mapping(summary.get("metadata_diagnostics"))
    lines = [
        "# en-es Semantic Veto Difficulty Stratification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Runtime policy change: `{_as_mapping(report.get('methodology')).get('runtime_policy_change', '')}`",
        f"- Case rows: `{summary.get('case_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        _mapping_table(report.get("e2e_checks")),
        "",
        "## Overall",
        "",
        _metrics_table([{**_as_mapping(summary.get("overall")), "scope_id": "overall"}]),
        "",
        "## Lanes",
        "",
        _metrics_table(report.get("lane_breakdowns")),
        "",
        "## Source Trigger Rank (English)",
        "",
        _metrics_table(report.get("source_trigger_rank_breakdowns_en")),
        "",
        "## Source Zipf Frequency (English)",
        "",
        _metrics_table(report.get("source_zipf_breakdowns_en")),
        "",
        "## Target Lemma Rank (Spanish)",
        "",
        _metrics_table(report.get("target_lemma_rank_breakdowns_es")),
        "",
        "## Ambiguity Proxies",
        "",
        "### Declared Ambiguity",
        "",
        _metrics_table(report.get("declared_ambiguity_breakdowns")),
        "",
        "### WordNet Sense Count",
        "",
        _metrics_table(report.get("wordnet_sense_count_breakdowns")),
        "",
        "### Translation Candidate Count",
        "",
        _metrics_table(report.get("translation_candidate_count_breakdowns")),
        "",
        "## Score-Surface Proxies",
        "",
        "### Shadow Lead",
        "",
        _metrics_table(report.get("shadow_lead_breakdowns")),
        "",
        "### Phrase Lead",
        "",
        _metrics_table(report.get("phrase_lead_breakdowns")),
        "",
        "## Trigger Risk Summary",
        "",
        _trigger_table(report.get("trigger_risk_summary")),
        "",
        "## Failure Rows",
        "",
        _failure_table(report.get("failure_rows")),
        "",
        "## Metadata Gaps",
        "",
        _mapping_table(diagnostics),
        "",
        "## Key Findings",
        "",
    ]
    for item in _sequence(summary.get("key_findings")):
        lines.append(f"- {item}")
    lines.extend(["", "## Limitations", ""])
    for item in _sequence(report.get("limitations")):
        lines.append(f"- {item}")
    lines.extend(["", "## Next Steps", ""])
    for item in _sequence(report.get("next_steps")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _mapping_table(value: object) -> str:
    mapping = _as_mapping(value)
    if not mapping:
        return "_No values._"
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, raw in mapping.items():
        if isinstance(raw, Mapping):
            rendered = ", ".join(
                f"{inner_key}={inner_value}" for inner_key, inner_value in raw.items()
            )
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            rendered = ", ".join(str(item) for item in raw)
        else:
            rendered = str(raw)
        lines.append(f"| `{_escape_md(str(key))}` | {_escape_md(rendered)} |")
    return "\n".join(lines)


def _metrics_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        checks = _as_mapping(row.get("target_checks"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("scope_id") or "")),
                    str(row.get("case_count", 0)),
                    str(row.get("family_count", 0)),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("positive_abstain_count", 0)),
                    str(row.get("negative_allow_count", 0)),
                    str(row.get("utility_score", "")),
                    _format_percent(row.get("source_rank_known_rate")),
                    _format_percent(row.get("source_zipf_known_rate")),
                    _format_percent(row.get("target_rank_known_rate")),
                    _escape_md(str(checks.get("target_status") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _trigger_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No trigger rows._"
    lines = [
        "| Trigger | Cases | Failures | Neg allow | Pos abstain | Source rank | Zipf band | Sense count | Lanes |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("trigger") or "")),
                    str(row.get("case_count", 0)),
                    str(row.get("failure_count", 0)),
                    str(row.get("negative_allow_count", 0)),
                    str(row.get("positive_abstain_count", 0)),
                    _escape_md(str(row.get("source_trigger_rank_bin_en") or "")),
                    _escape_md(str(row.get("source_zipf_band_en") or "")),
                    str(row.get("max_wordnet_sense_count") or ""),
                    _escape_md(", ".join(str(item) for item in _sequence(row.get("lanes")))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No product failures in the selected rows._"
    lines = [
        "| Case | Lane | Trigger | Target | Outcome | Source rank | Zipf band | Target rank | Sense count | Sentence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("case_id") or "")),
                    _escape_md(str(row.get("lane_id") or "")),
                    _escape_md(str(row.get("trigger") or "")),
                    _escape_md(str(row.get("target_lemma") or "")),
                    _escape_md(str(row.get("product_outcome") or "")),
                    _escape_md(str(row.get("source_trigger_rank_bin_en") or "")),
                    _escape_md(str(row.get("source_zipf_band_en") or "")),
                    _escape_md(str(row.get("target_lemma_rank_bin_es") or "")),
                    str(row.get("wordnet_sense_count") or ""),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _default_report_id(path: Path | None, index: int) -> str:
    if path is not None:
        return path.stem
    return f"inline_report_{index + 1}"
