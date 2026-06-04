from __future__ import annotations

from typing import Mapping


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Animals/Plants Existing Signal Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Rows measured: `{report.get('row_count', 0)}`",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Family Summary", ""])
    lines.append("| Family | Candidates | Share | Tiers | Confidence Bands | Review Required |")
    lines.append("| --- | ---: | ---: | --- | --- | ---: |")
    for family in _mapping_rows(report.get("families")):
        lines.append(
            f"| `{family.get('family', '')}` | {family.get('candidate_count', 0)} | "
            f"{_pct(family.get('candidate_share'))} | {_compact_counts(family.get('tier_counts'))} | "
            f"{_compact_counts(family.get('confidence_band_counts'))} | "
            f"{family.get('review_required_count', 0)} |"
        )
    for family in _mapping_rows(report.get("families")):
        lines.extend(["", f"## `{family.get('family', '')}` Top Candidates", ""])
        rows = _mapping_rows(family.get("top_candidates"))
        if not rows:
            lines.append("_No candidates found._")
            continue
        lines.append("| Lemma | Confidence | Band | Tier | Evidence |")
        lines.append("| --- | ---: | --- | --- | --- |")
        for row in rows[:12]:
            evidence = _mapping_rows(row.get("evidence"))
            top_evidence = evidence[0] if evidence else {}
            lines.append(
                f"| `{row.get('lemma', '')}` | {row.get('confidence', 0)} | "
                f"`{row.get('confidence_band', '')}` | `{row.get('best_tier', '')}` | "
                f"`{top_evidence.get('source_channel', '')}:{top_evidence.get('source_label', '')}` |"
            )
    lines.extend(["", "## Broad Exclusions Sample", ""])
    broad_exclusions = _mapping_rows(report.get("broad_exclusions"))
    if not broad_exclusions:
        lines.append("_No broad-only exclusions sampled._")
    else:
        lines.append("| Lemma | Excluded Labels |")
        lines.append("| --- | --- |")
        for row in broad_exclusions[:12]:
            lines.append(
                f"| `{row.get('lemma', '')}` | `{', '.join(row.get('excluded_labels', []))}` |"
            )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _compact_counts(value: object) -> str:
    mapping = value if isinstance(value, Mapping) else {}
    return ", ".join(f"{key}={value}" for key, value in mapping.items()) or "none"


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"
