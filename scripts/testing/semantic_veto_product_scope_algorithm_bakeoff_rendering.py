from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _safe_float,
)


def render_product_scope_algorithm_bakeoff_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    scope = _as_mapping(_as_mapping(report.get("inputs")).get("product_scope"))
    lines = [
        "# en-es Semantic Veto Product-Scope Algorithm Bakeoff",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Product-scope rows retained: `{scope.get('retained_case_count', 0)}`",
        f"- Diagnostic label rows excluded: `{scope.get('excluded_case_count', 0)}`",
        f"- Candidate rows: `{summary.get('candidate_row_count', 0)}`",
        f"- Product target pass rows: `{summary.get('target_pass_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        _checks_table(report.get("e2e_checks")),
        "",
        "## Best Rows",
        "",
        _row_table(report.get("top_rows")),
        "",
        "## Current Policy-Like Rows",
        "",
        _row_table(summary.get("current_policy_like_rows")),
        "",
        "## Best By Scorer",
        "",
        _row_table(summary.get("best_by_scorer")),
        "",
        "## Failure Samples",
        "",
        _failure_samples(report.get("failure_samples")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{item}`" for item in _sequence(report.get("issues")))
    return "\n".join(lines) + "\n"


def _checks_table(value: object) -> str:
    checks = _as_mapping(value)
    if not checks:
        return "_No checks._"
    lines = ["| Check | Value |", "| --- | --- |"]
    for key, raw in checks.items():
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(str(raw))}` |")
    return "\n".join(lines)


def _row_table(value: object) -> str:
    rows = [row for row in _sequence(value) if isinstance(row, Mapping)]
    if not rows:
        return "_No rows._"
    lines = [
        "| Config | Scorer | Phrase | Rescue | min active | margin | Pos allow | Neg abstain | Harm share | Utility | vs no veto | Target |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("config_id") or "")),
                    _escape_md(str(row.get("scorer_id") or "")),
                    _escape_md(str(row.get("phrase_control_mode") or "")),
                    _escape_md(str(row.get("active_rescue_mode") or "")),
                    str(row.get("min_active_score", "")),
                    str(row.get("min_margin", "")),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    _format_percent(row.get("harmful_share_of_replaces")),
                    str(row.get("utility_score", "")),
                    str(row.get("delta_vs_lexical_utility", "")),
                    _escape_md(str(row.get("target_status") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_samples(value: object) -> str:
    samples = _as_mapping(value)
    if not samples:
        return "_No failure samples._"
    lines: list[str] = []
    for config_id, raw_rows in samples.items():
        lines.extend([f"### `{_escape_md(str(config_id))}`", ""])
        rows = [row for row in _sequence(raw_rows) if isinstance(row, Mapping)]
        if not rows:
            lines.append("_No failures._")
            continue
        lines.extend(
            [
                "| Case | Outcome | Scores | Sentence |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in rows[:20]:
            scores = (
                f"a={row.get('active_score', '')}; "
                f"s={row.get('strongest_shadow_score', '')}; "
                f"m={row.get('margin', '')}"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{_escape_md(str(row.get('case_id') or ''))}`",
                        f"`{_escape_md(str(row.get('product_outcome') or ''))}`",
                        f"`{_escape_md(scores)}`",
                        _escape_md(str(row.get("sentence") or "")),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).strip() or "_No failure samples._"


def _shortfall(value: object, threshold: float) -> float:
    if value is None:
        return threshold
    return round(max(0.0, threshold - _safe_float(value)), 4)


def _normalize_float_grid(values: Sequence[float]) -> list[float]:
    return sorted({round(float(value), 6) for value in values})


def _normalize_string_grid(values: Sequence[str]) -> list[str]:
    return [value for value in (str(raw or "").strip() for raw in values) if value]


def _parse_float_grid(value: str) -> list[float]:
    return [float(item.strip()) for item in str(value or "").split(",") if item.strip()]


def _parse_string_grid(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []
