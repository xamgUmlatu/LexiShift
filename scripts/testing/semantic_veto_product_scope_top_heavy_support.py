from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _mapping_rows,
    _safe_float,
)
from semantic_veto_product_scope_band_grading_en_es import _target_metrics


def render_top_heavy_band_grading_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Product-Scope Top-Heavy Band Grading",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Formula scopes evaluated: `{summary.get('evaluated_formula_scope_count', 0)} / {summary.get('source_formula_scope_count', 0)}`",
        f"- Strategy scopes: `{summary.get('strategy_scope_count', 0)}`",
        f"- Band strategies: `{summary.get('band_strategy_count', 0)}`",
        f"- Ranking modes: `{summary.get('ranking_mode_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("purpose") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("primary_grade") or ""),
        "",
        "## Band Strategies",
        "",
        _strategy_table(report.get("band_strategies")),
        "",
        "## Ranking Modes",
        "",
        _ranking_mode_table(report.get("ranking_modes")),
        "",
        "## Best By Top-Heavy Grade",
        "",
        _top_heavy_table(summary.get("best_by_top_heavy_grade")),
        "",
        "## Accepted Candidate Takeaway",
        "",
        _accepted_takeaway_table(summary.get("accepted_candidate_takeaway")),
        "",
        "## Best By Strategy",
        "",
        _top_heavy_table(summary.get("best_by_strategy")),
        "",
        "## Best By Ranking Mode",
        "",
        _top_heavy_table(summary.get("best_by_ranking_mode")),
        "",
        "## Accepted Candidate Strategy Rows",
        "",
        _top_heavy_table(summary.get("accepted_candidate_strategy_rows")),
        "",
        "## Detail Rows",
        "",
        _detail_table(report.get("top_strategy_grade_details")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _combined_metrics(
    band_metrics: Sequence[Mapping[str, object]], target_id: str
) -> dict[str, object]:
    total_weight = 0.0
    weighted_failure = 0.0
    max_unmeasured = 0.0
    for band in band_metrics:
        family_count = int(band.get("family_count") or 0)
        if family_count <= 0:
            continue
        metrics = _target_metrics(band, target_id)
        rate = metrics.get("measured_only_failure_rate")
        if rate is None:
            max_unmeasured = max(
                max_unmeasured, _safe_float(metrics.get("unmeasured_target_weight"))
            )
            continue
        total_weight += family_count
        weighted_failure += family_count * _safe_float(rate)
        max_unmeasured = max(max_unmeasured, _safe_float(metrics.get("unmeasured_target_weight")))
    rate = weighted_failure / total_weight if total_weight else None
    return {
        "measured_only_failure_rate": _round4(rate),
        "max_unmeasured_target_weight": _round4(max_unmeasured),
    }


def _accepted_candidate(payload: Mapping[str, object]) -> dict[str, object]:
    candidate = _as_mapping(_as_mapping(payload.get("summary")).get("candidate"))
    scorer_id = str(candidate.get("scorer_id") or "")
    formula_id = str(candidate.get("formula_id") or "")
    if not scorer_id or not formula_id:
        return {}
    return {
        "scorer_id": scorer_id,
        "formula_id": formula_id,
        "formula_family": str(candidate.get("formula_family") or ""),
        "weights": dict(_as_mapping(candidate.get("weights"))),
    }


def _matches_candidate(row: Mapping[str, object], candidate: Mapping[str, object]) -> bool:
    return str(row.get("scorer_id") or "") == str(candidate.get("scorer_id") or "") and str(
        row.get("formula_id") or ""
    ) == str(candidate.get("formula_id") or "")


def _best_by_strategy(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    best = []
    for strategy_id in sorted({str(row.get("band_strategy_id") or "") for row in rows}):
        group = [row for row in rows if row.get("band_strategy_id") == strategy_id]
        if group:
            best.append(sorted(group, key=_top_heavy_sort_key)[0])
    return _public_top_heavy_rows(sorted(best, key=_top_heavy_sort_key))


def _best_by_ranking_mode(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    best = []
    for ranking_mode_id in sorted({str(row.get("ranking_mode_id") or "") for row in rows}):
        group = [row for row in rows if row.get("ranking_mode_id") == ranking_mode_id]
        if group:
            best.append(sorted(group, key=_top_heavy_sort_key)[0])
    return _public_top_heavy_rows(sorted(best, key=_top_heavy_sort_key))


def _accepted_takeaway(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    control_rows = [
        row
        for row in rows
        if row.get("band_strategy_id") == "equal_tertiles_33_33_34"
        and row.get("ranking_mode_id") == "algorithm_need"
    ]
    control = sorted(control_rows, key=_top_heavy_sort_key)[0] if control_rows else None
    top_heavy_rows = [
        row for row in rows if row.get("band_strategy_id") != "equal_tertiles_33_33_34"
    ]
    best_top_heavy = sorted(top_heavy_rows, key=_top_heavy_sort_key)[0] if top_heavy_rows else None
    control_grade = _safe_float(_as_mapping(control).get("top_heavy_grade_score"))
    top_heavy_grade = _safe_float(_as_mapping(best_top_heavy).get("top_heavy_grade_score"))
    if best_top_heavy is None:
        decision = "no_top_heavy_candidate_available"
    elif top_heavy_grade > control_grade:
        decision = "top_heavy_beats_equal_tertile_control_for_accepted_candidate"
    elif top_heavy_grade > 0:
        decision = "top_heavy_has_signal_but_does_not_beat_equal_tertile_control"
    else:
        decision = "top_heavy_has_no_positive_signal_for_accepted_candidate"
    return {
        "decision": decision,
        "control_equal_tertile_algorithm_need": _public_top_heavy_rows([control])
        if control
        else [],
        "best_top_heavy_candidate": _public_top_heavy_rows([best_top_heavy])
        if best_top_heavy
        else [],
        "top_heavy_grade_ratio_to_control": _round4(top_heavy_grade / control_grade)
        if control_grade
        else None,
    }


def _public_top_heavy_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "formula_id": row.get("formula_id"),
            "formula_family": row.get("formula_family"),
            "scorer_id": row.get("scorer_id"),
            "ranking_mode_id": row.get("ranking_mode_id"),
            "band_strategy_id": row.get("band_strategy_id"),
            "band_family_counts": row.get("band_family_counts"),
            "high_family_share": row.get("high_family_share"),
            "primary_high_failure_rate": row.get("primary_high_failure_rate"),
            "primary_rest_failure_rate": row.get("primary_rest_failure_rate"),
            "primary_all_failure_rate": row.get("primary_all_failure_rate"),
            "primary_high_rest_failure_delta": row.get("primary_high_rest_failure_delta"),
            "primary_high_failure_lift": row.get("primary_high_failure_lift"),
            "primary_normalized_high_low_failure_delta": row.get(
                "primary_normalized_high_low_failure_delta"
            ),
            "primary_normalized_order_score": row.get("primary_normalized_order_score"),
            "primary_min_measured_target_weight": row.get("primary_min_measured_target_weight"),
            "primary_max_unmeasured_target_weight": row.get("primary_max_unmeasured_target_weight"),
            "top_heavy_grade_score": row.get("top_heavy_grade_score"),
            "rank_metrics": row.get("rank_metrics"),
            "weights": row.get("weights"),
            "high_sample_triggers": row.get("high_sample_triggers"),
            "low_sample_triggers": row.get("low_sample_triggers"),
        }
        for row in rows
    ]


def _ranking_mode_definitions() -> list[dict[str, object]]:
    return [
        {
            "ranking_mode_id": "algorithm_need",
            "formula": "need_score",
            "description": "Control: use the formula score directly.",
        },
        {
            "ranking_mode_id": "source_exposure_product",
            "formula": "need_score * source_zipf_risk",
            "description": "Product-impact hypothesis: a hard rare family may matter less than a moderately hard common family.",
        },
        {
            "ranking_mode_id": "source_exposure_blend_25",
            "formula": "0.75 * need_score + 0.25 * source_zipf_risk",
            "description": "Light exposure weighting while mostly preserving algorithmic need.",
        },
        {
            "ranking_mode_id": "source_exposure_blend_50",
            "formula": "0.50 * need_score + 0.50 * source_zipf_risk",
            "description": "Balanced need/exposure ranking for the daily-language concentration hypothesis.",
        },
    ]


def _top_heavy_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float, float, str]:
    return (
        -_safe_float(row.get("top_heavy_grade_score")),
        -_safe_float(row.get("primary_high_rest_failure_delta")),
        -_safe_float(row.get("primary_high_failure_lift")),
        -_safe_float(row.get("primary_normalized_order_score")),
        _safe_float(row.get("primary_max_unmeasured_target_weight")),
        str(row.get("scope_id") or ""),
    )


def _sample_ranked_triggers(
    ranked: Sequence[Mapping[str, object]], family_ids: Sequence[str], limit: int = 8
) -> list[str]:
    wanted = set(family_ids)
    rows = [
        row
        for row in sorted(
            ranked,
            key=lambda item: (
                -_safe_float(item.get("ranking_score")),
                str(item.get("family_id") or ""),
            ),
        )
        if str(row.get("family_id") or "") in wanted
    ]
    return [
        f"{row.get('trigger')}->{row.get('target_lemma')}:{_round4(_safe_float(row.get('ranking_score')))}"
        for row in rows[:limit]
    ]


def _strategy_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No band strategies._"
    lines = [
        "| Strategy | High | Middle | Low | Description |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{_escape_md(str(row.get('strategy_id') or ''))}` | "
            f"{_format_percent(row.get('high_fraction'))} | "
            f"{_format_percent(row.get('middle_fraction'))} | "
            f"{_format_percent(row.get('low_fraction'))} | "
            f"{_escape_md(str(row.get('description') or ''))} |"
        )
    return "\n".join(lines)


def _ranking_mode_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No ranking modes._"
    lines = [
        "| Ranking mode | Formula | Description |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{_escape_md(str(row.get('ranking_mode_id') or ''))}` | "
            f"`{_escape_md(str(row.get('formula') or ''))}` | "
            f"{_escape_md(str(row.get('description') or ''))} |"
        )
    return "\n".join(lines)


def _top_heavy_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No grade rows._"
    lines = [
        "| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{_escape_md(str(row.get('band_strategy_id') or ''))}` | "
            f"`{_escape_md(str(row.get('ranking_mode_id') or ''))}` | "
            f"`{_escape_md(str(row.get('formula_id') or ''))}` | "
            f"`{_escape_md(str(row.get('scorer_id') or ''))}` | "
            f"`{_escape_md(json.dumps(row.get('band_family_counts') or {}, sort_keys=True))}` | "
            f"{_format_percent(row.get('primary_high_failure_rate'))} | "
            f"{_format_percent(row.get('primary_rest_failure_rate'))} | "
            f"{_format_percent(row.get('primary_high_rest_failure_delta'))} | "
            f"{_round4(_safe_float(row.get('primary_high_failure_lift')))} | "
            f"{_round4(_safe_float(row.get('top_heavy_grade_score')))} | "
            f"{_escape_md(', '.join(str(item) for item in row.get('high_sample_triggers') or []))} |"
        )
    return "\n".join(lines)


def _accepted_takeaway_table(value: object) -> str:
    takeaway = _as_mapping(value)
    if not takeaway:
        return "_No accepted-candidate takeaway._"
    lines = [
        f"- Decision: `{_escape_md(str(takeaway.get('decision') or ''))}`",
        f"- Top-heavy/control grade ratio: `{_round4(_safe_float(takeaway.get('top_heavy_grade_ratio_to_control')))}`",
        "",
        "Control:",
        "",
        _top_heavy_table(takeaway.get("control_equal_tertile_algorithm_need")),
        "",
        "Best top-heavy alternative:",
        "",
        _top_heavy_table(takeaway.get("best_top_heavy_candidate")),
    ]
    return "\n".join(lines)


def _detail_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No detail rows._"
    compact = []
    for row in rows[:30]:
        compact.append(
            {
                "band_strategy_id": row.get("band_strategy_id"),
                "ranking_mode_id": row.get("ranking_mode_id"),
                "formula_id": row.get("formula_id"),
                "scorer_id": row.get("scorer_id"),
                "top_heavy_grade_score": row.get("top_heavy_grade_score"),
                "primary_high_rest_failure_delta": row.get("primary_high_rest_failure_delta"),
                "band_family_counts": row.get("band_family_counts"),
                "high_sample_triggers": row.get("high_sample_triggers"),
            }
        )
    return "```json\n" + json.dumps(compact, ensure_ascii=False, indent=2) + "\n```"


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _mean_float(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
