from __future__ import annotations

from typing import Any, Mapping, Sequence


DEFAULT_ENCOUNTER_STALE_AGE_DAYS = 7


def render_markdown(report: Mapping[str, Any]) -> str:
    scope = _as_mapping(report.get("scope"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# SRS Resource Budget Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Pair: `{scope.get('pair', '')}`",
        f"- Profile: `{scope.get('profile_id', '')}`",
        f"- Data root exists: `{scope.get('data_root_exists', False)}`",
        "",
        "## Summary",
        "",
        f"- Code budget rows: `{summary.get('code_budget_row_count', 0)}`",
        f"- Bounded code rows: `{summary.get('bounded_code_row_count', 0)}`",
        f"- Helper artifact rows: `{summary.get('helper_artifact_row_count', 0)}`",
        f"- Helper artifact bytes: `{summary.get('helper_artifact_total_bytes', 0)}`",
        f"- Active SRS items: `{summary.get('active_item_count', 0)}`",
        f"- Zero-exposure active items: `{summary.get('zero_exposure_active_count', 0)}`",
        f"- Zero-feedback active items: `{summary.get('zero_feedback_active_count', 0)}`",
        f"- Stale unseen active items: `{summary.get('stale_unseen_active_count', 0)}`"
        f" over `{summary.get('encounter_stale_age_days', DEFAULT_ENCOUNTER_STALE_AGE_DAYS)}` days",
        f"- Age-unknown unseen active items: `{summary.get('age_unknown_unseen_active_count', 0)}`",
        "",
        "## Code Budgets",
        "",
        "| Surface | Budget | Cap | Current | Status | Notes |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    _append_code_budget_rows(lines, report)
    _append_helper_artifact_rows(lines, report)
    _append_encounter_starvation_rows(lines, report)
    _append_findings(lines, report)
    return "\n".join(lines).rstrip() + "\n"


def _append_code_budget_rows(lines: list[str], report: Mapping[str, Any]) -> None:
    for row in _mapping_rows(report.get("code_budget_rows")):
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('surface', '')}`",
                    f"`{row.get('budget', '')}`",
                    str(row.get("cap", "")),
                    str(row.get("current", "")),
                    f"`{row.get('status', '')}`",
                    str(row.get("notes", "")),
                )
            )
            + " |"
        )


def _append_helper_artifact_rows(lines: list[str], report: Mapping[str, Any]) -> None:
    lines.extend(
        [
            "",
            "## Helper Artifacts",
            "",
            "| Artifact | Exists | Bytes | Key Counts | Status |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for row in _mapping_rows(_as_mapping(report.get("helper_artifacts")).get("artifacts")):
        counts = ", ".join(
            f"{key}={value}" for key, value in _as_mapping(row.get("counts")).items()
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('id', '')}`",
                    f"`{row.get('exists', False)}`",
                    str(row.get("bytes", 0)),
                    counts,
                    f"`{row.get('status', '')}`",
                )
            )
            + " |"
        )


def _append_encounter_starvation_rows(lines: list[str], report: Mapping[str, Any]) -> None:
    stale_rows = _mapping_rows(
        _as_mapping(report.get("helper_artifacts")).get("stale_active_preview")
    )
    lines.extend(["", "## Encounter-Starvation Preview", ""])
    if not stale_rows:
        lines.append(
            "- No zero-exposure/zero-feedback active items were visible in the audited helper store."
        )
        return
    lines.extend(
        [
            "| Lemma | Age | Exposures | Reviews | Rule Count | Source Phrases |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in stale_rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('lemma', '')}`",
                    _format_age(row),
                    str(row.get("exposures", 0)),
                    str(row.get("review_count", 0)),
                    str(row.get("rule_count", 0)),
                    str(row.get("source_phrase_count", 0)),
                )
            )
            + " |"
        )


def _append_findings(lines: list[str], report: Mapping[str, Any]) -> None:
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in _string_list(report.get("limitations")):
        lines.append(f"- {limitation}")


def _format_age(row: Mapping[str, Any]) -> str:
    value = row.get("admitted_age_days")
    return "unknown" if value is None else str(value)


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value]
