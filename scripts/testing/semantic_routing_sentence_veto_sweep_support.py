#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,
    SENTENCE_VETO_CONTEXT_VIEWS,
    SENTENCE_VETO_EVIDENCE_VIEWS,
    SENTENCE_VETO_PHRASE_CONTROL_MODES,
    SENTENCE_VETO_SCORERS,
)
from lexishift_core.rulegen.semantic_routing_runtime_policy import (
    DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
    SENTENCE_VETO_ACTIVE_RESCUE_MODES,
)
from semantic_routing_sentence_veto_common import (
    build_sentence_veto_report,
    load_sentence_veto_dataset,
)
from semantic_routing_sentence_veto_helpers import _normalize_string_list
from semantic_routing_sentence_veto_reporting import (
    compute_sentence_veto_objective,
    select_best_sentence_veto_objective_row,
    sentence_veto_sweep_rank_key,
)


def build_sentence_veto_sweep_report(
    *,
    dataset_path: Path,
    scorers: Sequence[str],
    context_views: Sequence[str],
    evidence_views: Sequence[str],
    min_active_scores: Sequence[float],
    min_margins: Sequence[float],
    phrase_control_modes: Sequence[str] = (DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,),
    active_rescue_modes: Sequence[str] = (DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,),
    harmful_replace_budgets: Sequence[int] = (0, 1, 2),
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    dataset = load_sentence_veto_dataset(dataset_path)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    rows: list[dict[str, object]] = []

    normalized_scorers = [
        value for value in _normalize_string_list(scorers) if value in SENTENCE_VETO_SCORERS
    ]
    normalized_context_views = [
        value
        for value in _normalize_string_list(context_views)
        if value in SENTENCE_VETO_CONTEXT_VIEWS
    ]
    normalized_evidence_views = [
        value
        for value in _normalize_string_list(evidence_views)
        if value in SENTENCE_VETO_EVIDENCE_VIEWS
    ]
    normalized_phrase_control_modes = [
        value
        for value in _normalize_string_list(phrase_control_modes)
        if value in SENTENCE_VETO_PHRASE_CONTROL_MODES
    ]
    normalized_active_rescue_modes = [
        value
        for value in _normalize_string_list(active_rescue_modes)
        if value in SENTENCE_VETO_ACTIVE_RESCUE_MODES
    ]
    normalized_harmful_replace_budgets = sorted(
        {max(0, int(value)) for value in harmful_replace_budgets if isinstance(value, (int, float))}
    )
    normalized_min_active_scores = [float(value) for value in min_active_scores]
    normalized_min_margins = [float(value) for value in min_margins]
    if (
        not normalized_scorers
        or not normalized_context_views
        or not normalized_evidence_views
        or not normalized_phrase_control_modes
        or not normalized_active_rescue_modes
    ):
        raise ValueError(
            "Sentence-veto sweep requires non-empty scorer, context-view, evidence-view, phrase-control mode, and active-rescue mode sets."
        )
    if not normalized_min_active_scores or not normalized_min_margins:
        raise ValueError("Sentence-veto sweep requires non-empty min-active and min-margin grids.")
    if not normalized_harmful_replace_budgets:
        raise ValueError("Sentence-veto sweep requires at least one harmful-replace budget.")

    for scorer_id in normalized_scorers:
        for context_view in normalized_context_views:
            for evidence_view in normalized_evidence_views:
                for phrase_control_mode in normalized_phrase_control_modes:
                    for active_rescue_mode in normalized_active_rescue_modes:
                        for min_active_score in normalized_min_active_scores:
                            for min_margin in normalized_min_margins:
                                report = build_sentence_veto_report(
                                    dataset_path=dataset_path,
                                    scorer_id=scorer_id,
                                    context_view=context_view,
                                    evidence_view=evidence_view,
                                    min_active_score=min_active_score,
                                    min_margin=min_margin,
                                    phrase_control_mode=phrase_control_mode,
                                    active_rescue_mode=active_rescue_mode,
                                    model_name=model_name,
                                    window_tokens=window_tokens,
                                    mask_token=mask_token,
                                )
                                summary = dict(report.get("summary") or {})
                                row = {
                                    "config_id": (
                                        f"{scorer_id}:{context_view}:{evidence_view}:"
                                        f"p={phrase_control_mode}:"
                                        f"r={active_rescue_mode}:"
                                        f"a={min_active_score:.2f}:m={min_margin:.2f}"
                                    ),
                                    "scorer_id": scorer_id,
                                    "model_name": model_name,
                                    "context_view": context_view,
                                    "evidence_view": evidence_view,
                                    "phrase_control_mode": phrase_control_mode,
                                    "active_rescue_mode": active_rescue_mode,
                                    "min_active_score": float(min_active_score),
                                    "min_margin": float(min_margin),
                                    "decision_accuracy": summary.get("decision_accuracy"),
                                    "replace_precision": summary.get("replace_precision"),
                                    "replace_recall": summary.get("replace_recall"),
                                    "harmful_replace_rate": summary.get("harmful_replace_rate"),
                                    "false_abstain_rate": summary.get("false_abstain_rate"),
                                    "winner_accuracy": summary.get("winner_accuracy"),
                                    "shadow_winner_accuracy": summary.get("shadow_winner_accuracy"),
                                    "predicted_replace_rate": summary.get("predicted_replace_rate"),
                                    "phrase_preemption_hit_rate": summary.get(
                                        "phrase_preemption_hit_rate"
                                    ),
                                    "phrase_preemption_precision": summary.get(
                                        "phrase_preemption_precision"
                                    ),
                                    "phrase_preemption_hit_count": int(
                                        summary.get("phrase_preemption_hit_count") or 0
                                    ),
                                    "active_rescue_applied_rate": summary.get(
                                        "active_rescue_applied_rate"
                                    ),
                                    "active_rescue_precision": summary.get(
                                        "active_rescue_precision"
                                    ),
                                    "active_rescue_applied_count": int(
                                        summary.get("active_rescue_applied_count") or 0
                                    ),
                                    "harmful_replace_count": int(
                                        summary.get("harmful_replace_count") or 0
                                    ),
                                    "false_abstain_count": int(
                                        summary.get("false_abstain_count") or 0
                                    ),
                                    "gold_abstain_cases": int(
                                        summary.get("gold_abstain_cases") or 0
                                    ),
                                    "gold_replace_cases": int(
                                        summary.get("gold_replace_cases") or 0
                                    ),
                                    "summary": summary,
                                }
                                row["objective_score"] = compute_sentence_veto_objective(row)
                                rows.append(row)

    rows.sort(key=sentence_veto_sweep_rank_key)
    best_row = dict(rows[0]) if rows else None
    best_objective_row = select_best_sentence_veto_objective_row(rows)
    best_rows_by_harmful_replace_budget: list[dict[str, object]] = []
    for harmful_replace_budget in normalized_harmful_replace_budgets:
        best_budget_row = select_best_sentence_veto_objective_row(
            rows,
            max_harmful_replace_count=harmful_replace_budget,
        )
        if best_budget_row is None:
            continue
        best_rows_by_harmful_replace_budget.append(
            {
                "harmful_replace_budget": int(harmful_replace_budget),
                "row": best_budget_row,
            }
        )
    best_by_scorer: list[dict[str, object]] = []
    for scorer_id in normalized_scorers:
        scorer_rows = [row for row in rows if str(row.get("scorer_id") or "").strip() == scorer_id]
        if scorer_rows:
            best_by_scorer.append(dict(scorer_rows[0]))
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(dataset.get("pair") or "").strip(),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "grid": {
            "scorers": normalized_scorers,
            "context_views": normalized_context_views,
            "evidence_views": normalized_evidence_views,
            "phrase_control_modes": normalized_phrase_control_modes,
            "active_rescue_modes": normalized_active_rescue_modes,
            "min_active_scores": normalized_min_active_scores,
            "min_margins": normalized_min_margins,
            "harmful_replace_budgets": normalized_harmful_replace_budgets,
            "model_name": model_name,
            "window_tokens": int(window_tokens),
            "mask_token": str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
        },
        "row_count": len(rows),
        "best_row": best_row,
        "best_objective_row": best_objective_row,
        "best_rows_by_harmful_replace_budget": best_rows_by_harmful_replace_budget,
        "best_by_scorer": best_by_scorer,
        "rows": rows,
    }
