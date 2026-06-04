from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (
    build_runtime_context_views,
    resolve_runtime_evidence_text,
)


def _collect_config_texts(
    dataset: Mapping[str, object],
    *,
    context_view: str,
    evidence_view: str,
    window_tokens: int,
    mask_token: str,
) -> list[str]:
    texts: list[str] = []
    for family in dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = family.get("active")
        if isinstance(active, Mapping):
            texts.append(resolve_runtime_evidence_text(active, evidence_view=evidence_view))
        shadows = family.get("shadows")
        if isinstance(shadows, Sequence) and not isinstance(shadows, (str, bytes)):
            for shadow in shadows:
                if isinstance(shadow, Mapping):
                    texts.append(resolve_runtime_evidence_text(shadow, evidence_view=evidence_view))
        cases = family.get("cases")
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes)):
            for case in cases:
                if not isinstance(case, Mapping):
                    continue
                context_views = build_runtime_context_views(
                    str(case.get("sentence") or "").strip(),
                    source_phrase=str(
                        case.get("source_phrase") or case.get("trigger") or ""
                    ).strip(),
                    mask_token=mask_token,
                    window_tokens=window_tokens,
                )
                texts.append(str(context_views.get(context_view) or "").strip())
    return [text for text in texts if str(text or "").strip()]


def _accumulate_sentence_veto_summary(
    summary: dict[str, object],
    *,
    result: object,
) -> None:
    gold_decision = str(getattr(result, "gold_decision", "") or "").strip()
    predicted_decision = str(getattr(result, "predicted_decision", "") or "").strip()
    gold_winner_type = str(getattr(result, "gold_winner_type", "") or "").strip()
    predicted_winner = str(getattr(result, "predicted_winner", "") or "").strip()
    gold_winner = str(getattr(result, "gold_winner", "") or "").strip()
    summary["cases_total"] += 1
    if gold_decision == "replace":
        summary["gold_replace_cases"] += 1
    else:
        summary["gold_abstain_cases"] += 1
    if gold_winner_type == "active":
        summary["gold_active_winner_cases"] += 1
    elif gold_winner_type == "shadow":
        summary["gold_shadow_winner_cases"] += 1
    else:
        summary["gold_none_cases"] += 1
    if predicted_decision == "replace":
        summary["predicted_replace_cases"] += 1
    else:
        summary["predicted_abstain_cases"] += 1
    if predicted_decision == "replace" and gold_decision == "replace":
        summary["true_replace_count"] += 1
    elif predicted_decision == "replace":
        summary["harmful_replace_count"] += 1
    elif gold_decision == "replace":
        summary["false_abstain_count"] += 1
    else:
        summary["true_abstain_count"] += 1
    if gold_winner_type in {"active", "shadow"}:
        summary["winner_labeled_cases"] += 1
        if predicted_winner == gold_winner:
            summary["winner_correct_count"] += 1
    if gold_winner_type == "shadow":
        summary["shadow_winner_labeled_cases"] += 1
        if predicted_winner == gold_winner:
            summary["shadow_winner_correct_count"] += 1
    if bool(getattr(result, "phrase_preemption_hit", False)):
        summary["phrase_preemption_hit_count"] += 1
        if gold_decision == "replace":
            summary["phrase_preemption_harmful_block_count"] += 1
        else:
            summary["phrase_preemption_correct_abstain_count"] += 1
    if bool(getattr(result, "active_rescue_applied", False)):
        summary["active_rescue_applied_count"] += 1
        if gold_decision == "replace":
            summary["active_rescue_correct_replace_count"] += 1
        else:
            summary["active_rescue_harmful_replace_count"] += 1


def _new_sentence_veto_summary() -> dict[str, object]:
    return {
        "cases_total": 0,
        "gold_replace_cases": 0,
        "gold_abstain_cases": 0,
        "gold_active_winner_cases": 0,
        "gold_shadow_winner_cases": 0,
        "gold_none_cases": 0,
        "predicted_replace_cases": 0,
        "predicted_abstain_cases": 0,
        "true_replace_count": 0,
        "true_abstain_count": 0,
        "harmful_replace_count": 0,
        "false_abstain_count": 0,
        "winner_labeled_cases": 0,
        "winner_correct_count": 0,
        "shadow_winner_labeled_cases": 0,
        "shadow_winner_correct_count": 0,
        "phrase_preemption_hit_count": 0,
        "phrase_preemption_correct_abstain_count": 0,
        "phrase_preemption_harmful_block_count": 0,
        "active_rescue_applied_count": 0,
        "active_rescue_correct_replace_count": 0,
        "active_rescue_harmful_replace_count": 0,
    }


def _finalize_sentence_veto_summary(summary: Mapping[str, object]) -> None:
    cases_total = int(summary.get("cases_total") or 0)
    gold_replace_cases = int(summary.get("gold_replace_cases") or 0)
    gold_abstain_cases = int(summary.get("gold_abstain_cases") or 0)
    predicted_replace_cases = int(summary.get("predicted_replace_cases") or 0)
    winner_labeled_cases = int(summary.get("winner_labeled_cases") or 0)
    shadow_winner_labeled_cases = int(summary.get("shadow_winner_labeled_cases") or 0)
    true_replace_count = int(summary.get("true_replace_count") or 0)
    true_abstain_count = int(summary.get("true_abstain_count") or 0)
    harmful_replace_count = int(summary.get("harmful_replace_count") or 0)
    false_abstain_count = int(summary.get("false_abstain_count") or 0)
    winner_correct_count = int(summary.get("winner_correct_count") or 0)
    shadow_winner_correct_count = int(summary.get("shadow_winner_correct_count") or 0)
    phrase_preemption_hit_count = int(summary.get("phrase_preemption_hit_count") or 0)
    phrase_preemption_correct_abstain_count = int(
        summary.get("phrase_preemption_correct_abstain_count") or 0
    )
    active_rescue_applied_count = int(summary.get("active_rescue_applied_count") or 0)
    active_rescue_correct_replace_count = int(
        summary.get("active_rescue_correct_replace_count") or 0
    )

    summary["decision_accuracy"] = _safe_rate(true_replace_count + true_abstain_count, cases_total)
    summary["replace_precision"] = _safe_rate(true_replace_count, predicted_replace_cases)
    summary["replace_recall"] = _safe_rate(true_replace_count, gold_replace_cases)
    summary["harmful_replace_rate"] = _safe_rate(harmful_replace_count, gold_abstain_cases)
    summary["false_abstain_rate"] = _safe_rate(false_abstain_count, gold_replace_cases)
    summary["winner_accuracy"] = _safe_rate(winner_correct_count, winner_labeled_cases)
    summary["shadow_winner_accuracy"] = _safe_rate(
        shadow_winner_correct_count,
        shadow_winner_labeled_cases,
    )
    summary["predicted_replace_rate"] = _safe_rate(predicted_replace_cases, cases_total)
    summary["phrase_preemption_hit_rate"] = _safe_rate(phrase_preemption_hit_count, cases_total)
    summary["phrase_preemption_precision"] = _safe_rate(
        phrase_preemption_correct_abstain_count,
        phrase_preemption_hit_count,
    )
    summary["active_rescue_applied_rate"] = _safe_rate(active_rescue_applied_count, cases_total)
    summary["active_rescue_precision"] = _safe_rate(
        active_rescue_correct_replace_count,
        active_rescue_applied_count,
    )


def _finalize_sentence_veto_breakdown_rows(
    rows: object,
    *,
    primary_sort_key: str,
    sort_by_cases_desc: bool = False,
    preferred_order: Sequence[str] = (),
) -> list[dict[str, object]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    preferred_order_lookup = {
        value: index for index, value in enumerate(_normalize_string_list(preferred_order))
    }
    finalized_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary")
        if not isinstance(summary, Mapping):
            continue
        summary_payload = dict(summary)
        _finalize_sentence_veto_summary(summary_payload)
        payload = dict(row)
        payload["summary"] = summary_payload
        finalized_rows.append(payload)
    if sort_by_cases_desc:
        finalized_rows.sort(
            key=lambda row: (
                -int(
                    (row.get("summary", {}) if isinstance(row.get("summary"), Mapping) else {}).get(
                        "cases_total"
                    )
                    or 0
                ),
                str(row.get(primary_sort_key) or ""),
            )
        )
        return finalized_rows
    if preferred_order_lookup:
        finalized_rows.sort(
            key=lambda row: (
                preferred_order_lookup.get(
                    str(row.get(primary_sort_key) or "").strip(),
                    len(preferred_order_lookup),
                ),
                str(row.get(primary_sort_key) or ""),
            )
        )
        return finalized_rows
    finalized_rows.sort(key=lambda row: str(row.get(primary_sort_key) or ""))
    return finalized_rows


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, raw_values in value.items():
        dimension_name = str(key or "").strip()
        values = _normalize_string_list(raw_values)
        if dimension_name and values:
            normalized[dimension_name] = values
    return normalized


def _append_sample(
    container: list[dict[str, object]], row: Mapping[str, object], *, limit: int = 8
) -> None:
    if len(container) < limit:
        container.append(dict(row))


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator
