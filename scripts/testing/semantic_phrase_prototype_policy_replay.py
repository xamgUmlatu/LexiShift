#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping

from semantic_llm_prototype_admission_config import (
    ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR,
    phrase_preemption_should_apply,
)


def replay_phrase_prototype_policy_summary(
    row_results: object,
    *,
    min_active_score: float,
    min_margin: float,
    phrase_prototype_margin: float,
    use_surface_pos: bool = False,
) -> dict[str, object]:
    rows = [row for row in row_results or () if isinstance(row, Mapping)]
    case_count = len(rows)
    gold_replace = 0
    gold_abstain = 0
    correct = 0
    true_replace = 0
    harmful_ids: list[str] = []
    false_ids: list[str] = []
    rescue_count = 0
    for row in rows:
        gold = str(row.get("gold_decision") or "").strip()
        if gold == "replace":
            gold_replace += 1
        else:
            gold_abstain += 1
        predicted, active_rescue_applied = replay_semantic_policy_decision(
            row,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_prototype_margin=phrase_prototype_margin,
            use_surface_pos=use_surface_pos,
        )
        if active_rescue_applied:
            rescue_count += 1
        if predicted == gold:
            correct += 1
        if predicted == "replace" and gold == "replace":
            true_replace += 1
        if predicted == "replace" and gold != "replace":
            harmful_ids.append(str(row.get("case_id") or "").strip())
        if predicted != "replace" and gold == "replace":
            false_ids.append(str(row.get("case_id") or "").strip())
    return {
        "case_count": case_count,
        "gold_replace_cases": gold_replace,
        "gold_abstain_cases": gold_abstain,
        "harmful_replace_count": len(harmful_ids),
        "false_abstain_count": len(false_ids),
        "harmful_replace_case_ids": harmful_ids,
        "false_abstain_case_ids": false_ids,
        "replace_recall": (true_replace / gold_replace) if gold_replace else 0.0,
        "decision_accuracy": (correct / case_count) if case_count else 0.0,
        "active_rescue_applied_count": rescue_count,
    }


def replay_semantic_policy_decision(
    row: Mapping[str, object],
    *,
    min_active_score: float,
    min_margin: float,
    phrase_prototype_margin: float,
    use_surface_pos: bool,
) -> tuple[str, bool]:
    active_score = float(row.get("active_score") or 0.0)
    shadow_score = float(row.get("strongest_shadow_score") or 0.0)
    phrase_score = float(row.get("phrase_control_score") or 0.0)
    has_active_evidence = bool(str(row.get("active_evidence_text") or "").strip())
    has_phrase_evidence = bool(str(row.get("phrase_control_evidence_text") or "").strip())
    predicted = (
        "replace"
        if has_active_evidence
        and active_score >= float(min_active_score)
        and active_score - shadow_score >= float(min_margin)
        else "abstain"
    )
    if has_phrase_evidence and phrase_score >= max(active_score, shadow_score) + float(
        phrase_prototype_margin
    ):
        predicted = "abstain"
    phrase_preemption_applied = phrase_preemption_should_apply(
        phrase_preemption_hit=bool(row.get("phrase_preemption_hit")),
        decision_before_phrase_preemption=predicted,
        active_score=active_score,
        strongest_shadow_score=shadow_score,
        phrase_control_score=phrase_score,
        phrase_prototype_margin=phrase_prototype_margin,
    )
    if phrase_preemption_applied:
        predicted = "abstain"
    active_rescue_applied = False
    if use_surface_pos:
        signal = str(row.get("surface_pos_signal") or "").strip()
        if signal in {"active_noun_frame", "active_modifier_frame"} and predicted != "replace":
            if not has_active_evidence:
                pass
            elif signal == "active_noun_frame" and not _surface_pos_noun_shadow_verb_like(row):
                pass
            elif (
                signal == "active_modifier_frame"
                and active_score - shadow_score < ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR
            ):
                pass
            else:
                predicted = "replace"
                active_rescue_applied = True
        elif signal in {"non_active_nominal_frame", "shadow_verb_frame"} and predicted == "replace":
            predicted = "abstain"
    return predicted, active_rescue_applied


def _surface_pos_noun_shadow_verb_like(row: Mapping[str, object]) -> bool:
    explicit = row.get("surface_pos_noun_shadow_verb_like")
    if isinstance(explicit, bool):
        return explicit
    if str(row.get("surface_pos_rescue_blocked_reason") or "").strip() == (
        "strongest_shadow_not_verb_like"
    ):
        return False
    return True
