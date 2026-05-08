#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_formula_shape_bakeoff_en_es import (
    PRIMARY_SELECTION_MODE,
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _round4,
    _safe_float,
    _sequence,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_SHAPE_REPORT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_shape_bakeoff_en_es_latest.json"
DEFAULT_SURFACE_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_formula_weight_surface_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_curve_guided_expansion_plan_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_curve_guided_expansion_plan_en_es_latest.md"
)
QUEUE_LIMIT = 24
DEFAULT_ROW_BUDGETS = {
    "P0": {"manual_discovery_rows": 4, "llm_discovery_rows": 16, "locked_eval_rows": 8},
    "P1": {"manual_discovery_rows": 3, "llm_discovery_rows": 10, "locked_eval_rows": 5},
    "P2": {"manual_discovery_rows": 2, "llm_discovery_rows": 6, "locked_eval_rows": 3},
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert semantic-veto formula shape and weight-surface diagnostics into "
            "a curve-guided manual/LLM expansion plan. This is research-only."
        )
    )
    parser.add_argument("--shape-report", type=Path, default=DEFAULT_SHAPE_REPORT)
    parser.add_argument("--surface-report", type=Path, default=DEFAULT_SURFACE_REPORT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_curve_guided_expansion_plan_report(
        shape_payload=_load_json(args.shape_report),
        surface_payload=_load_json(args.surface_report),
        shape_path=args.shape_report,
        surface_path=args.surface_report,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_curve_guided_expansion_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_curve_guided_expansion_plan_report(
    *,
    shape_payload: Mapping[str, object],
    surface_payload: Mapping[str, object],
    shape_path: Path | None = None,
    surface_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    issues: list[str] = []
    cells = _mapping_rows(shape_payload.get("cell_observations"))
    primary_cells = [
        cell for cell in cells if str(cell.get("selection_mode") or "") == PRIMARY_SELECTION_MODE
    ]
    sentinel_cells = [
        cell for cell in cells if str(cell.get("selection_mode") or "") != PRIMARY_SELECTION_MODE
    ]
    if not cells:
        issues.append("shape_report_has_no_cell_observations")
    if not primary_cells:
        issues.append("shape_report_has_no_primary_cells")
    curve_signals = _curve_signals(surface_payload)
    if not curve_signals:
        issues.append("surface_report_has_no_curve_signals")
    top_by_cell = {
        str(row.get("cell_id") or ""): row
        for row in _mapping_rows(shape_payload.get("top_priority_cells"))
    }
    recommendation_by_cell = {
        str(row.get("cell_id") or ""): row
        for row in _mapping_rows(shape_payload.get("recommendations"))
    }
    max_signal = max(
        (_safe_float(row.get("signal_strength")) for row in curve_signals), default=0.0
    )
    queue_rows = _expansion_queue(
        primary_cells=primary_cells,
        top_by_cell=top_by_cell,
        recommendation_by_cell=recommendation_by_cell,
        curve_signals=curve_signals,
        max_signal=max_signal,
    )
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "curve_guided_expansion_plan_established"
            if not issues
            else "curve_guided_expansion_plan_incomplete"
        ),
        "generated_at": generated_at,
        "pair": str(shape_payload.get("pair") or surface_payload.get("pair") or "en-es"),
        "inputs": {
            "shape_report_path": _repo_path(shape_path),
            "surface_report_path": _repo_path(surface_path),
            "shape_report_decision": str(shape_payload.get("decision") or ""),
            "surface_report_decision": str(surface_payload.get("decision") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "objective": (
                "Use observed formula-shape data-help priority plus weight-surface "
                "curve signals to choose cells that will reveal the shape of veto "
                "difficulty with the fewest manual and LLM rows."
            ),
            "selection_scope": "primary pre_outcome cells only",
            "sentinel_policy": "excluded_from_queue_but_counted_in_summary",
            "expansion_score_formula": (
                "0.40*shape_data_help_priority + 0.25*curve_signal_strength + "
                "0.20*uncertainty_width + 0.10*underfilled_rate + "
                "0.05*posterior_failure_rate"
            ),
            "curve_signal_normalization": "divide by strongest positive surface signal in report",
            "priority_policy": "P0 >= 0.75, P1 >= 0.50, otherwise P2",
        },
        "summary": {
            "issues": issues,
            "cell_count": len(cells),
            "primary_cell_count": len(primary_cells),
            "sentinel_cell_count": len(sentinel_cells),
            "curve_signal_count": len(curve_signals),
            "queued_cell_count": len(queue_rows),
            "priority_counts": dict(Counter(str(row.get("priority") or "") for row in queue_rows)),
            "row_budget_totals": _row_budget_totals(queue_rows),
            "strongest_curve_signals": curve_signals[:12],
        },
        "curve_signal_summary": _curve_signal_summary(curve_signals),
        "case_type_summary": _case_type_summary(queue_rows),
        "expansion_queue": queue_rows,
        "authoring_guidance": _authoring_guidance(),
        "limitations": [
            "queue_is_based_on_current_draft_cells_not_representative_browsing",
            "curve_signals_describe_where_scores_move_not_which_runtime_policy_to_promote",
            "internal_locked_eval_split_is_advisory_until_more_cells_exist",
            "recommended_llm_rows_still_need_contract_validation_before_locked_eval",
            "sentinel_cells_are_not_used_for_primary_queue_selection",
        ],
        "next_steps": [
            "Author P0 manual discovery rows first, then rerun difficulty surface and curve reports.",
            "Generate P0 LLM rows only after manual rows confirm the cell contract is real.",
            "Keep locked-eval rows separate from discovery rows before making any promotion claim.",
            "Use the updated curve shape to decide whether the next expansion should target phrase, shadow, or positive-active cells.",
        ],
    }


def render_curve_guided_expansion_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Curve-Guided Expansion Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Primary cells: `{summary.get('primary_cell_count', 0)}`",
        f"- Queued cells: `{summary.get('queued_cell_count', 0)}`",
        f"- Sentinel cells excluded from queue: `{summary.get('sentinel_cell_count', 0)}`",
        "",
        "## Strongest Curve Signals",
        "",
        _curve_signal_table(summary.get("strongest_curve_signals")),
        "",
        "## Expansion Queue",
        "",
        _queue_table(report.get("expansion_queue")),
        "",
        "## Case-Type Summary",
        "",
        _case_type_table(report.get("case_type_summary")),
        "",
        "## Authoring Guidance",
        "",
    ]
    for case_type, guidance in _as_mapping(report.get("authoring_guidance")).items():
        lines.append(f"- `{_escape_md(str(case_type))}`: {guidance}")
    lines.extend(["", "## Methodology", ""])
    methodology = _as_mapping(report.get("methodology"))
    for key in [
        "objective",
        "selection_scope",
        "expansion_score_formula",
        "curve_signal_normalization",
        "priority_policy",
    ]:
        lines.append(f"- `{key}`: {methodology.get(key, '')}")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _curve_signals(surface_payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sweep in _mapping_rows(surface_payload.get("sweep_reports")):
        sweep_id = str(sweep.get("sweep_id") or "")
        for curve in _mapping_rows(sweep.get("feature_curve_summaries")):
            rows.append(
                {
                    "signal_id": f"{sweep_id}::{curve.get('curve_id')}",
                    "sweep_id": sweep_id,
                    "signal_type": "feature_curve",
                    "curve_id": str(curve.get("curve_id") or ""),
                    "gate_id": str(curve.get("gate_id") or "") or None,
                    "feature_ids": [str(curve.get("feature_id") or "")],
                    "best_discovery_spearman": curve.get("best_discovery_spearman"),
                    "best_locked_spearman": curve.get("best_locked_spearman"),
                    "selected_alpha": curve.get("selected_alpha"),
                    "best_alpha": curve.get("best_alpha"),
                    "curve_shape": curve.get("curve_shape"),
                    "signal_strength": _round4(
                        max(0.0, _safe_float(curve.get("best_discovery_spearman")))
                    ),
                }
            )
        for curve in _mapping_rows(sweep.get("pairwise_curve_summaries")):
            rows.append(
                {
                    "signal_id": f"{sweep_id}::{curve.get('curve_id')}",
                    "sweep_id": sweep_id,
                    "signal_type": "pairwise_curve",
                    "curve_id": str(curve.get("curve_id") or ""),
                    "gate_id": str(curve.get("gate_id") or "") or None,
                    "feature_ids": [
                        str(curve.get("left_feature") or ""),
                        str(curve.get("right_feature") or ""),
                    ],
                    "best_discovery_spearman": curve.get("best_discovery_spearman"),
                    "best_locked_spearman": curve.get("best_locked_spearman"),
                    "best_left_alpha": curve.get("best_left_alpha"),
                    "curve_shape": curve.get("curve_shape"),
                    "signal_strength": _round4(
                        max(0.0, _safe_float(curve.get("best_discovery_spearman")))
                    ),
                }
            )
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("signal_strength")),
            str(row.get("sweep_id") or ""),
            str(row.get("curve_id") or ""),
        )
    )
    return rows


def _expansion_queue(
    *,
    primary_cells: Sequence[Mapping[str, object]],
    top_by_cell: Mapping[str, Mapping[str, object]],
    recommendation_by_cell: Mapping[str, Mapping[str, object]],
    curve_signals: Sequence[Mapping[str, object]],
    max_signal: float,
) -> list[dict[str, object]]:
    scored = []
    for cell in primary_cells:
        cell_id = str(cell.get("cell_id") or "")
        top = top_by_cell.get(cell_id, {})
        matching_signals = _matching_surface_signals(cell=cell, signals=curve_signals)
        signal_strength = max(
            (_safe_float(row.get("signal_strength")) for row in matching_signals),
            default=0.0,
        )
        signal_norm = signal_strength / max_signal if max_signal > 0 else 0.0
        features = _as_mapping(cell.get("features"))
        uncertainty_width = _uncertainty_width(cell=cell, top=top)
        data_help_priority = _safe_float(top.get("normalized_data_help_priority"))
        if not top and not matching_signals:
            data_help_priority = 0.0
        expansion_score = (
            0.40 * data_help_priority
            + 0.25 * signal_norm
            + 0.20 * uncertainty_width
            + 0.10 * _safe_float(features.get("underfilled_rate"))
            + 0.05 * _safe_float(cell.get("posterior_failure_rate"))
        )
        reasons = _reasons(
            cell=cell,
            top=top,
            matching_signals=matching_signals,
            signal_norm=signal_norm,
            uncertainty_width=uncertainty_width,
        )
        if not reasons:
            continue
        priority = _priority(expansion_score)
        recommendation = recommendation_by_cell.get(cell_id, {})
        row_budgets = _row_budgets(priority=priority, recommendation=recommendation)
        scored.append(
            {
                "priority": priority,
                "cell_id": cell_id,
                "manual_case_type": cell.get("manual_case_type"),
                "heuristic_group": cell.get("heuristic_group"),
                "scorer_id": cell.get("scorer_id"),
                "shadow_contract": cell.get("shadow_contract"),
                "source_rank_bin": cell.get("source_rank_bin"),
                "polysemy_band": cell.get("polysemy_band"),
                "cell_split": cell.get("cell_split"),
                "case_rows": cell.get("case_rows"),
                "failure_count": cell.get("failure_count"),
                "posterior_failure_rate": cell.get("posterior_failure_rate"),
                "uncertainty_width": _round4(uncertainty_width),
                "shape_data_help_priority": _round4(data_help_priority),
                "curve_signal_strength": _round4(signal_norm),
                "expansion_score": _round4(expansion_score),
                "recommended_action": _recommended_action(cell),
                **row_budgets,
                "reasons": reasons,
                "surface_signals": [_signal_public_row(row) for row in matching_signals[:3]],
                "triggers": _sequence(cell.get("triggers"))[:8],
            }
        )
    scored.sort(
        key=lambda row: (
            {"P0": 0, "P1": 1, "P2": 2}.get(str(row.get("priority") or ""), 9),
            -_safe_float(row.get("expansion_score")),
            str(row.get("manual_case_type") or ""),
            str(row.get("cell_id") or ""),
        )
    )
    return scored[:QUEUE_LIMIT]


def _matching_surface_signals(
    *,
    cell: Mapping[str, object],
    signals: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    case_type = str(cell.get("manual_case_type") or "")
    features = _as_mapping(cell.get("features"))
    result = []
    for signal in signals:
        gate_id = str(signal.get("gate_id") or "")
        curve_id = str(signal.get("curve_id") or "")
        feature_ids = [str(value) for value in _sequence(signal.get("feature_ids")) if value]
        if gate_id:
            if gate_id == case_type:
                result.append(signal)
            continue
        if curve_id.startswith(f"{case_type}."):
            result.append(signal)
            continue
        if _features_apply(case_type=case_type, features=features, feature_ids=feature_ids):
            result.append(signal)
    result.sort(
        key=lambda row: (
            -_safe_float(row.get("signal_strength")),
            str(row.get("curve_id") or ""),
        )
    )
    return result


def _features_apply(
    *,
    case_type: str,
    features: Mapping[str, object],
    feature_ids: Sequence[str],
) -> bool:
    if not feature_ids:
        return False
    if any(
        _feature_applies(case_type=case_type, features=features, feature_id=item)
        for item in feature_ids
    ):
        return True
    return False


def _feature_applies(
    *,
    case_type: str,
    features: Mapping[str, object],
    feature_id: str,
) -> bool:
    value = _safe_float(features.get(feature_id))
    if value > 0.15:
        return True
    if feature_id in {
        "underfilled_rate",
        "phrase_score_missing_rate",
        "phrase_surface_pattern_rate",
    }:
        return case_type == "phrase_no_winner" and value > 0
    if feature_id in {"active_low_rate"}:
        return case_type == "positive_active" and value > 0
    if feature_id in {"near_tie_rate", "shadow_contract_risk"}:
        return case_type == "shadow_negative" and value > 0
    if feature_id in {"rank_missing_rate"}:
        return _safe_float(features.get("rank_missing_rate")) > 0
    return False


def _uncertainty_width(*, cell: Mapping[str, object], top: Mapping[str, object]) -> float:
    if top.get("uncertainty_width") is not None:
        return _safe_float(top.get("uncertainty_width"))
    interval = _as_mapping(cell.get("uncertainty_interval"))
    if interval.get("width") is not None:
        return _safe_float(interval.get("width"))
    return 0.0


def _reasons(
    *,
    cell: Mapping[str, object],
    top: Mapping[str, object],
    matching_signals: Sequence[Mapping[str, object]],
    signal_norm: float,
    uncertainty_width: float,
) -> list[str]:
    features = _as_mapping(cell.get("features"))
    reasons = []
    if top:
        reasons.append("top_shape_data_help_cell")
    if signal_norm >= 0.65:
        reasons.append("strong_surface_curve_signal")
    elif matching_signals:
        reasons.append("surface_curve_signal")
    if _safe_float(features.get("underfilled_rate")) >= 0.5:
        reasons.append("underfilled_cell")
    if uncertainty_width >= 0.5:
        reasons.append("high_uncertainty")
    case_type = str(cell.get("manual_case_type") or "")
    if case_type == "phrase_no_winner":
        reasons.append("phrase_no_winner_priority")
    if case_type == "shadow_negative" and _safe_float(features.get("near_tie_rate")) > 0:
        reasons.append("near_tie_shadow")
    if case_type == "positive_active" and _safe_float(features.get("active_low_rate")) > 0:
        reasons.append("positive_active_low_score")
    return sorted(set(reasons))


def _priority(score: float) -> str:
    if score >= 0.75:
        return "P0"
    if score >= 0.50:
        return "P1"
    return "P2"


def _row_budgets(
    *,
    priority: str,
    recommendation: Mapping[str, object],
) -> dict[str, int]:
    defaults = DEFAULT_ROW_BUDGETS.get(priority, DEFAULT_ROW_BUDGETS["P2"])
    if str(recommendation.get("priority") or "") != priority:
        recommendation = {}
    return {
        "manual_discovery_rows": int(
            recommendation.get("manual_discovery_rows") or defaults["manual_discovery_rows"]
        ),
        "llm_discovery_rows": int(
            recommendation.get("llm_discovery_rows") or defaults["llm_discovery_rows"]
        ),
        "locked_eval_rows": int(
            recommendation.get("locked_eval_rows") or defaults["locked_eval_rows"]
        ),
    }


def _recommended_action(cell: Mapping[str, object]) -> str:
    case_type = str(cell.get("manual_case_type") or "")
    if case_type == "phrase_no_winner":
        return "add_order_sensitive_phrase_no_winner_rows"
    if case_type == "shadow_negative":
        return "add_real_alternate_sense_shadow_negative_rows"
    if case_type == "positive_active":
        return "add_valid_replacement_positive_context_rows"
    return "add_discovery_rows_then_locked_eval_rows"


def _signal_public_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "signal_id": row.get("signal_id"),
        "sweep_id": row.get("sweep_id"),
        "signal_type": row.get("signal_type"),
        "curve_id": row.get("curve_id"),
        "gate_id": row.get("gate_id"),
        "feature_ids": row.get("feature_ids"),
        "best_discovery_spearman": row.get("best_discovery_spearman"),
        "best_locked_spearman": row.get("best_locked_spearman"),
        "curve_shape": row.get("curve_shape"),
    }


def _curve_signal_summary(signals: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    summary = []
    for row in signals[:18]:
        summary.append(
            {
                **_signal_public_row(row),
                "signal_strength": row.get("signal_strength"),
                "interpretation": _signal_interpretation(row),
            }
        )
    return summary


def _signal_interpretation(row: Mapping[str, object]) -> str:
    curve_id = str(row.get("curve_id") or "")
    features = set(str(item) for item in _sequence(row.get("feature_ids")))
    if curve_id.startswith("phrase_no_winner") or "underfilled_rate" in features:
        return "expand phrase/no-winner cells before reading the weight curve as stable"
    if "rank_missing_rate" in features:
        return "separate missing-rank cells from ranked-frequency controls"
    if "near_tie_rate" in features:
        return "add shadow-negative near-tie rows to measure alternate-sense competition"
    if "active_low_rate" in features:
        return "add positive-active rows where active evidence is weak or near threshold"
    return "use as a cell-selection signal, not as a runtime coefficient"


def _case_type_summary(queue_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in queue_rows:
        grouped[str(row.get("manual_case_type") or "")].append(row)
    result = []
    for case_type, rows in sorted(grouped.items()):
        result.append(
            {
                "manual_case_type": case_type,
                "queued_cells": len(rows),
                "p0_cells": sum(1 for row in rows if row.get("priority") == "P0"),
                "manual_discovery_rows": sum(
                    int(row.get("manual_discovery_rows") or 0) for row in rows
                ),
                "llm_discovery_rows": sum(int(row.get("llm_discovery_rows") or 0) for row in rows),
                "locked_eval_rows": sum(int(row.get("locked_eval_rows") or 0) for row in rows),
                "mean_expansion_score": _round4(
                    sum(_safe_float(row.get("expansion_score")) for row in rows) / len(rows)
                )
                if rows
                else None,
            }
        )
    result.sort(
        key=lambda row: (
            -int(row.get("p0_cells") or 0),
            -_safe_float(row.get("mean_expansion_score")),
            str(row.get("manual_case_type") or ""),
        )
    )
    return result


def _row_budget_totals(queue_rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {
        "manual_discovery_rows": sum(
            int(row.get("manual_discovery_rows") or 0) for row in queue_rows
        ),
        "llm_discovery_rows": sum(int(row.get("llm_discovery_rows") or 0) for row in queue_rows),
        "locked_eval_rows": sum(int(row.get("locked_eval_rows") or 0) for row in queue_rows),
    }


def _authoring_guidance() -> dict[str, str]:
    return {
        "phrase_no_winner": (
            "Write sentences where the source surface form appears, but the target "
            "replacement should not appear; include word-order, punctuation, short "
            "utterance, and idiom-like variants."
        ),
        "shadow_negative": (
            "Write real alternate-sense contexts with a clearly better shadow meaning; "
            "avoid fake shadows that merely contain contrastive keywords."
        ),
        "positive_active": (
            "Write natural contexts where the replacement is correct, especially cases "
            "where current active evidence is weak, short, or near the threshold."
        ),
    }


def _curve_signal_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Sweep | Curve | Gate | Features | Best discovery | Best locked | Shape |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        features = ", ".join(str(item) for item in _sequence(row.get("feature_ids")))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('sweep_id') or ''))}`",
                    f"`{_escape_md(str(row.get('curve_id') or ''))}`",
                    f"`{_escape_md(str(row.get('gate_id') or ''))}`",
                    f"`{_escape_md(features)}`",
                    _metric(row.get("best_discovery_spearman")),
                    _metric(row.get("best_locked_spearman")),
                    f"`{_escape_md(str(row.get('curve_shape') or ''))}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _queue_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Priority | Case type | Group | Scorer | Score | Reasons | Manual | LLM | Locked |",
        "| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        reasons = ", ".join(str(item) for item in _sequence(row.get("reasons")))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('priority') or ''))}`",
                    f"`{_escape_md(str(row.get('manual_case_type') or ''))}`",
                    f"`{_escape_md(str(row.get('heuristic_group') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    _metric(row.get("expansion_score")),
                    _escape_md(reasons),
                    str(row.get("manual_discovery_rows") or 0),
                    str(row.get("llm_discovery_rows") or 0),
                    str(row.get("locked_eval_rows") or 0),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _case_type_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Case type | Cells | P0 cells | Manual | LLM | Locked | Mean score |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('manual_case_type') or ''))}`",
                    str(row.get("queued_cells") or 0),
                    str(row.get("p0_cells") or 0),
                    str(row.get("manual_discovery_rows") or 0),
                    str(row.get("llm_discovery_rows") or 0),
                    str(row.get("locked_eval_rows") or 0),
                    _metric(row.get("mean_expansion_score")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _metric(value: object) -> str:
    if value is None:
        return ""
    return f"{_safe_float(value):.4f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
