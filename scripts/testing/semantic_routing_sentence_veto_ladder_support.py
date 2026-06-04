#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
)
from semantic_routing_sentence_veto_common import build_sentence_veto_report
from semantic_routing_sentence_veto_helpers import _append_sample, _safe_rate


def build_sentence_veto_ladder_report(
    *,
    dataset_path: Path,
    scorer_id: str = "sentence_transformer_cosine",
    context_view: str = "masked_sentence",
    evidence_view: str = "all_evidence_text",
    min_active_score: float = 0.0,
    min_margin: float = 0.0,
    phrase_control_mode: str = "noun_family_frame_guard",
    active_rescue_mode: str = "sense_label_near_tie_active_rescue",
    soft_min_active_scores: Sequence[float] = (0.50, 0.52, 0.55, 0.58, 0.60),
    soft_min_margins: Sequence[float] = (-0.20, -0.15, -0.10, -0.05, -0.03, -0.02, -0.01, 0.0),
    soft_false_positive_budgets: Sequence[int] = (0, 1, 2),
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    base_report = build_sentence_veto_report(
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
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    normalized_soft_min_active_scores = sorted(
        {float(value) for value in soft_min_active_scores if isinstance(value, (int, float))}
    )
    normalized_soft_min_margins = sorted(
        {float(value) for value in soft_min_margins if isinstance(value, (int, float))}
    )
    normalized_soft_false_positive_budgets = sorted(
        {
            max(0, int(value))
            for value in soft_false_positive_budgets
            if isinstance(value, (int, float))
        }
    )
    if not normalized_soft_min_active_scores or not normalized_soft_min_margins:
        raise ValueError(
            "Sentence-veto ladder sweep requires non-empty soft-active and soft-margin grids."
        )
    if not normalized_soft_false_positive_budgets:
        raise ValueError(
            "Sentence-veto ladder sweep requires at least one soft false-positive budget."
        )

    rows: list[dict[str, object]] = []
    for soft_min_active_score in normalized_soft_min_active_scores:
        for soft_min_margin in normalized_soft_min_margins:
            rows.append(
                _simulate_sentence_veto_ladder_row(
                    base_report,
                    soft_min_active_score=float(soft_min_active_score),
                    soft_min_margin=float(soft_min_margin),
                )
            )
    rows.sort(key=sentence_veto_ladder_rank_key)
    best_row = dict(rows[0]) if rows else None
    best_rows_by_soft_false_positive_budget: list[dict[str, object]] = []
    for soft_false_positive_budget in normalized_soft_false_positive_budgets:
        best_budget_row = select_best_sentence_veto_ladder_row(
            rows,
            max_soft_false_positive_count=soft_false_positive_budget,
        )
        if best_budget_row is None:
            continue
        best_rows_by_soft_false_positive_budget.append(
            {
                "soft_false_positive_budget": int(soft_false_positive_budget),
                "row": best_budget_row,
            }
        )
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(base_report.get("pair") or "").strip(),
        "dataset_id": str(base_report.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "base_config": dict(base_report.get("config") or {}),
        "base_summary": dict(base_report.get("summary") or {}),
        "grid": {
            "soft_min_active_scores": normalized_soft_min_active_scores,
            "soft_min_margins": normalized_soft_min_margins,
            "soft_false_positive_budgets": normalized_soft_false_positive_budgets,
            "apply_over_current_abstains_only": True,
        },
        "row_count": len(rows),
        "best_row": best_row,
        "best_rows_by_soft_false_positive_budget": best_rows_by_soft_false_positive_budget,
        "rows": rows,
    }


def select_best_sentence_veto_ladder_row(
    rows: Sequence[Mapping[str, object]],
    *,
    max_soft_false_positive_count: int | None = None,
) -> dict[str, object] | None:
    candidate_rows: list[Mapping[str, object]] = []
    for row in rows:
        soft_false_positive_count = int(row.get("soft_false_positive_count") or 0)
        if max_soft_false_positive_count is not None and soft_false_positive_count > max(
            0, int(max_soft_false_positive_count)
        ):
            continue
        candidate_rows.append(row)
    if not candidate_rows:
        return None
    return dict(min(candidate_rows, key=sentence_veto_ladder_rank_key))


def sentence_veto_ladder_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        int(row.get("soft_false_positive_count") or 0),
        int(row.get("remaining_missed_replace_count") or 0),
        int(row.get("soft_affordance_count") or 0),
        -float(row.get("soft_min_active_score") or 0.0),
        -float(row.get("soft_min_margin") or 0.0),
    )


def build_sentence_veto_ladder_case_rows(
    base_report: Mapping[str, object],
    *,
    soft_min_active_score: float,
    soft_min_margin: float,
) -> list[dict[str, object]]:
    rows = (
        base_report.get("row_results")
        if isinstance(base_report.get("row_results"), Sequence)
        and not isinstance(base_report.get("row_results"), (str, bytes))
        else []
    )
    case_rows: list[dict[str, object]] = []
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        row = dict(raw_row)
        hard_predicted_decision = str(row.get("predicted_decision") or "").strip().lower()
        ladder_decision = "abstain"
        if hard_predicted_decision == "replace":
            ladder_decision = "replace"
        elif not bool(row.get("phrase_preemption_hit")):
            active_score = float(row.get("active_score") or 0.0)
            margin = float(row.get("margin") or 0.0)
            if active_score >= float(soft_min_active_score) and margin >= float(soft_min_margin):
                ladder_decision = "soft_affordance"
        case_rows.append(
            {
                **row,
                "hard_predicted_decision": hard_predicted_decision,
                "ladder_decision": ladder_decision,
                "soft_min_active_score": float(soft_min_active_score),
                "soft_min_margin": float(soft_min_margin),
            }
        )
    return case_rows


def _simulate_sentence_veto_ladder_row(
    base_report: Mapping[str, object],
    *,
    soft_min_active_score: float,
    soft_min_margin: float,
) -> dict[str, object]:
    base_summary = (
        base_report.get("summary") if isinstance(base_report.get("summary"), Mapping) else {}
    )
    rows = build_sentence_veto_ladder_case_rows(
        base_report,
        soft_min_active_score=float(soft_min_active_score),
        soft_min_margin=float(soft_min_margin),
    )
    cases_total = int(base_summary.get("cases_total") or 0)
    gold_replace_cases = int(base_summary.get("gold_replace_cases") or 0)
    gold_abstain_cases = int(base_summary.get("gold_abstain_cases") or 0)
    replace_count = 0
    abstain_count = 0
    soft_affordance_count = 0
    hard_true_positive_count = 0
    hard_false_positive_count = 0
    soft_true_positive_count = 0
    soft_false_positive_count = 0
    remaining_missed_replace_count = 0
    sample_soft_true_positive_rows: list[dict[str, object]] = []
    sample_soft_false_positive_rows: list[dict[str, object]] = []
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        row = dict(raw_row)
        gold_decision = str(row.get("gold_decision") or "").strip().lower()
        ladder_decision = str(row.get("ladder_decision") or "").strip().lower()
        if ladder_decision == "replace":
            replace_count += 1
            if gold_decision == "replace":
                hard_true_positive_count += 1
            else:
                hard_false_positive_count += 1
        elif ladder_decision == "soft_affordance":
            soft_affordance_count += 1
            if gold_decision == "replace":
                soft_true_positive_count += 1
                _append_sample(sample_soft_true_positive_rows, row)
            else:
                soft_false_positive_count += 1
                _append_sample(sample_soft_false_positive_rows, row)
        else:
            abstain_count += 1
            if gold_decision == "replace":
                remaining_missed_replace_count += 1
    hard_replace_recall = _safe_rate(hard_true_positive_count, gold_replace_cases)
    hard_replace_precision = _safe_rate(hard_true_positive_count, replace_count)
    hard_harmful_replace_rate = _safe_rate(hard_false_positive_count, gold_abstain_cases)
    replace_or_soft_recall = _safe_rate(
        hard_true_positive_count + soft_true_positive_count,
        gold_replace_cases,
    )
    soft_precision = _safe_rate(soft_true_positive_count, soft_affordance_count)
    soft_noise_rate = _safe_rate(soft_false_positive_count, gold_abstain_cases)
    surfaced_precision = _safe_rate(
        hard_true_positive_count + soft_true_positive_count,
        replace_count + soft_affordance_count,
    )
    soft_affordance_rate = _safe_rate(soft_affordance_count, cases_total)
    remaining_missed_replace_rate = _safe_rate(remaining_missed_replace_count, gold_replace_cases)
    base_replace_recall = base_summary.get("replace_recall")
    replace_or_soft_recall_lift = None
    if isinstance(base_replace_recall, (float, int)) and replace_or_soft_recall is not None:
        replace_or_soft_recall_lift = float(replace_or_soft_recall) - float(base_replace_recall)
    return {
        "config_id": f"soft:a={float(soft_min_active_score):.2f}:m={float(soft_min_margin):.2f}",
        "soft_min_active_score": float(soft_min_active_score),
        "soft_min_margin": float(soft_min_margin),
        "replace_count": replace_count,
        "soft_affordance_count": soft_affordance_count,
        "abstain_count": abstain_count,
        "hard_true_positive_count": hard_true_positive_count,
        "hard_false_positive_count": hard_false_positive_count,
        "soft_true_positive_count": soft_true_positive_count,
        "soft_false_positive_count": soft_false_positive_count,
        "remaining_missed_replace_count": remaining_missed_replace_count,
        "hard_replace_recall": hard_replace_recall,
        "hard_replace_precision": hard_replace_precision,
        "hard_harmful_replace_rate": hard_harmful_replace_rate,
        "replace_or_soft_recall": replace_or_soft_recall,
        "replace_or_soft_recall_lift": replace_or_soft_recall_lift,
        "soft_precision": soft_precision,
        "soft_noise_rate": soft_noise_rate,
        "surfaced_precision": surfaced_precision,
        "soft_affordance_rate": soft_affordance_rate,
        "remaining_missed_replace_rate": remaining_missed_replace_rate,
        "sample_soft_true_positive_rows": sample_soft_true_positive_rows,
        "sample_soft_false_positive_rows": sample_soft_false_positive_rows,
    }
