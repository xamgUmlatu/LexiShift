from __future__ import annotations

from typing import Mapping


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es SRS Topic Family Depth Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Frontier count: `{summary.get('frontier_count', 0)}`",
        f"- Missing optional frontiers: `{summary.get('missing_optional_frontier_count', 0)}`",
        "",
        "## Scope",
        "",
        (
            "This is a read-only coverage/depth audit for the product-owned SRS "
            "topic/register taxonomy. It does not download sources, write overlays, "
            "mutate SRS state, or enable admission lift."
        ),
        "",
        "## Findings",
        "",
    ]
    for finding in report.get("findings", []):
        item = _as_mapping(finding)
        lines.append(
            f"- `{item.get('level', '')}` `{item.get('code', '')}`: {item.get('message', '')}"
        )
    lines.extend(["", "## Frontier Coverage", ""])
    for frontier in report.get("frontiers", []):
        item = _as_mapping(frontier)
        lines.extend(
            [
                f"### `{item.get('label', '')}`",
                "",
                f"- exists: `{item.get('exists', False)}`",
                f"- status: `{item.get('status', '')}`",
                f"- seeds measured: `{item.get('seed_count', 0)}`",
                f"- unique lemmas: `{item.get('unique_lemma_count', 0)}`",
                "",
            ]
        )
        if not item.get("exists"):
            lines.append(f"- missing path: `{item.get('frequency_db', '')}`")
            lines.append("")
            continue
        lines.extend(
            [
                "| Family | Axis | State | Trusted Rows | Bands | Max Difficulty | "
                "Review-Only Rows | Posture |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for family in _mapping_rows(item.get("families")):
            lines.append(
                f"| `{family.get('family', '')}` | `{family.get('axis', '')}` | "
                f"`{family.get('readiness_state', '')}` | "
                f"{family.get('trusted_candidate_count', 0)} | "
                f"{family.get('trusted_nonempty_band_count', 0)} | "
                f"{_number_or_na(family.get('trusted_max_difficulty'))} | "
                f"{family.get('review_only_candidate_count', 0)} | "
                f"`{family.get('coverage_posture', '')}` |"
            )
        lines.extend(["", "#### Trusted Examples", ""])
        for family in _mapping_rows(item.get("families")):
            if int(family.get("trusted_candidate_count") or 0) <= 0:
                continue
            lines.append(
                f"- `{family.get('family', '')}`: "
                + ", ".join(
                    f"`{row.get('lemma')}` ({row.get('difficulty')})"
                    for row in _mapping_rows(family.get("trusted_top_examples"))[:5]
                )
            )
        lines.extend(["", "#### Register Review-Only Examples", ""])
        for family in _mapping_rows(item.get("families")):
            if str(family.get("axis") or "") != "register":
                continue
            examples = _mapping_rows(family.get("review_only_examples"))
            if not examples:
                lines.append(f"- `{family.get('family', '')}`: none")
                continue
            lines.append(
                f"- `{family.get('family', '')}`: "
                + ", ".join(
                    f"`{row.get('lemma')}` ({', '.join(row.get('source_labels', []))})"
                    for row in examples[:5]
                )
            )
        lines.append("")
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _number_or_na(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "n/a"
