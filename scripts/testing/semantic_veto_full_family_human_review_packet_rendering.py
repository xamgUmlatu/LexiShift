from __future__ import annotations

import json
from typing import Mapping

from semantic_veto_full_family_human_review_packet_core import (
    _mapping_rows,
    _sequence,
)
from semantic_veto_product_quality_en_es import _as_mapping, _escape_md


def _family_section(family: Mapping[str, object]) -> list[str]:
    title = (
        f"### {family.get('review_id', '')}: "
        f"{family.get('trigger', '')} -> {family.get('target_lemma', '')}"
    )
    active = _as_mapping(family.get("active_evidence"))
    active_views = _as_mapping(active.get("evidence_views"))
    lines = [
        title,
        "",
        f"- Source band: `{family.get('source_zipf_band_en', '')}`",
        f"- Target band: `{family.get('target_zipf_band_es', '')}`",
        f"- Polysemy/POS: `{family.get('polysemy_band', '')}` / `{family.get('pos_shape', '')}`",
        f"- Review status: `{family.get('human_review_status', '')}`",
        f"- Active sense status: `{family.get('active_sense_status', '')}`",
        f"- Agent pre-triage weaknesses: `{', '.join(_sequence(family.get('agent_pretriage_weaknesses'))) or 'none'}`",
        "",
        "**Active Evidence**",
        "",
        f"- Target: `{active.get('target_lemma', '')}`",
        f"- POS: `{active.get('canonical_pos', '')}`",
        f"- Label: {active_views.get('sense_label', '')}",
        f"- Gloss: {active_views.get('gloss_text', '')}",
        "",
        "**Candidate WordNet Senses**",
        "",
        _sense_table(family.get("candidate_wordnet_senses")),
        "",
        "**Family Review Fields**",
        "",
        "```text",
        "human_review_status:",
        "active_sense_status:",
        "active_sense_notes:",
        "corrected_active_evidence:",
        "family_disposition:",
        "```",
        "",
        "**Case Rows**",
        "",
        _case_table(family.get("case_review_rows")),
        "",
    ]
    return lines


def _case_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No case rows._"
    lines = [
        "| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('case_id') or ''))}`",
                    f"`{_escape_md(str(row.get('manual_case_type') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_decision') or ''))}`",
                    f"`{_escape_md(str(row.get('proposed_row_quality_status') or ''))}`",
                    _escape_md(", ".join(_sequence(row.get("agent_pretriage_weaknesses")))),
                    _escape_md(str(row.get("sentence") or "")),
                    "pending user review",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _weakness_list(value: object) -> str:
    rows = [str(item) for item in _sequence(value) if str(item)]
    if not rows:
        return "- `none`"
    return "\n".join(f"- `{_escape_md(item)}`" for item in rows)


def render_human_review_packet_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Human Review Packet",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Review families: `{summary.get('review_family_count', 0)}` / `{summary.get('dataset_family_count', 0)}`",
        f"- Review cases: `{summary.get('review_case_count', 0)}`",
        f"- Trusted rows: `{summary.get('trusted_case_count', 0)}`",
        "",
        "## Review Rule",
        "",
        "Every semantic decision in this packet is a proposal only. A family or case "
        "becomes trusted only after the user explicitly approves it.",
        "",
        "## Summary",
        "",
        _summary_table(summary),
        "",
        "## Requested User Decisions",
        "",
        "- For each family: decide whether the active English sense really matches the Spanish target.",
        "- For each case: approve, reject, rewrite, or mark diagnostic-only.",
        "- For phrase/no-winner rows: choose the subtype or replace the template with a realistic negative context.",
        "",
        "## Weakness Taxonomy",
        "",
        _weakness_taxonomy_table(report.get("weakness_taxonomy")),
        "",
        "## Packet Weaknesses",
        "",
        _weakness_list(_as_mapping(summary).get("packet_weaknesses")),
        "",
    ]
    for family in _mapping_rows(report.get("family_review_rows")):
        lines.extend(_family_section(family))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _summary_table(value: Mapping[str, object]) -> str:
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, raw in value.items():
        rendered = (
            json.dumps(raw, ensure_ascii=False, sort_keys=True)
            if isinstance(raw, (dict, list, tuple))
            else str(raw)
        )
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _weakness_taxonomy_table(value: object) -> str:
    taxonomy = _as_mapping(value)
    rows = _mapping_rows(taxonomy.get("weakness_types"))
    if not rows:
        return "_No weakness taxonomy loaded._"
    purpose = str(taxonomy.get("purpose") or "").strip()
    lines = []
    if purpose:
        lines.extend([_escape_md(purpose), ""])
    lines.extend(
        [
            "| ID | Scope | Severity | Detection | Meaning | Avoid By | Review Action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('id') or ''))}`",
                    f"`{_escape_md(str(row.get('scope') or ''))}`",
                    f"`{_escape_md(str(row.get('severity') or ''))}`",
                    f"`{_escape_md(str(row.get('detection') or ''))}`",
                    _escape_md(str(row.get("meaning") or "")),
                    _escape_md(str(row.get("avoid_by") or "")),
                    _escape_md(str(row.get("review_action") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _sense_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No candidate WordNet senses found._"
    lines = [
        "| Rank | POS | Definition | Examples |",
        "| ---: | --- | --- | --- |",
    ]
    for row in rows:
        examples = "; ".join(str(item) for item in _sequence(row.get("examples"))[:2])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("candidate_rank") or ""),
                    f"`{_escape_md(str(row.get('pos') or ''))}`",
                    _escape_md(str(row.get("definition") or "")),
                    _escape_md(examples),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
