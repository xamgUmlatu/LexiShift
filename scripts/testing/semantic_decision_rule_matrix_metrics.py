#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403


def _public_summary(summary: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "cases_total",
        "gold_replace_cases",
        "gold_abstain_cases",
        "gold_active_winner_cases",
        "gold_shadow_winner_cases",
        "gold_none_cases",
        "predicted_replace_cases",
        "predicted_abstain_cases",
        "true_replace_count",
        "true_abstain_count",
        "harmful_replace_count",
        "false_abstain_count",
        "winner_labeled_cases",
        "winner_correct_count",
        "shadow_winner_labeled_cases",
        "shadow_winner_correct_count",
        "phrase_preemption_hit_count",
        "decision_accuracy",
        "replace_precision",
        "replace_recall",
        "harmful_replace_rate",
        "false_abstain_rate",
        "winner_accuracy",
        "shadow_winner_accuracy",
        "predicted_replace_rate",
        "phrase_preemption_hit_rate",
        "phrase_preemption_precision",
    )
    return {key: summary.get(key) for key in keys}


def _objective_score(row: Mapping[str, object]) -> float:
    harmful = int(row.get("harmful_replace_count") or 0)
    false_abstain = int(row.get("false_abstain_count") or 0)
    accuracy_penalty = 1.0 - float(row.get("decision_accuracy") or 0.0)
    winner_penalty = 1.0 - float(row.get("winner_accuracy") or 0.0)
    return round((harmful * 1000.0) + (false_abstain * 10.0) + accuracy_penalty + winner_penalty, 6)


def _rank_key(row: Mapping[str, object]) -> tuple[float, int, int, str]:
    return (
        float(row.get("objective_score") or 0.0),
        int(row.get("harmful_replace_count") or 0),
        int(row.get("false_abstain_count") or 0),
        str(row.get("config_id") or ""),
    )


def _split_rank_key(row: Mapping[str, object], *, split: str) -> tuple[float, int, int, str]:
    split_summary = _split_summary(row, split)
    return (
        float(split_summary.get("objective_score") or 0.0),
        int(split_summary.get("harmful_replace_count") or 0),
        int(split_summary.get("false_abstain_count") or 0),
        str(row.get("config_id") or ""),
    )


def _ranking_quality_key(row: Mapping[str, object]) -> tuple[float, float, str]:
    return (
        -float(row.get("ranking_roc_auc") or 0.0),
        -float(row.get("ranking_average_precision") or 0.0),
        str(row.get("config_id") or ""),
    )


def _select_best(rows: object) -> Mapping[str, object] | None:
    materialized = [row for row in rows or () if isinstance(row, Mapping)]
    if not materialized:
        return None
    return sorted(materialized, key=_rank_key)[0]


def _select_best_for_split(
    rows: object,
    split: str,
) -> Mapping[str, object] | None:
    materialized = [row for row in rows or () if isinstance(row, Mapping)]
    materialized = [
        row for row in materialized if int(_split_summary(row, split).get("cases_total") or 0) > 0
    ]
    if not materialized:
        return None
    return sorted(materialized, key=lambda row: _split_rank_key(row, split=split))[0]


def _select_incumbent(config_rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    controls = [row for row in config_rows if bool(row.get("is_control"))]
    return _select_best(controls) or _select_best(config_rows)


def _public_config_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    keys = (
        "config_id",
        "label",
        "category",
        "algorithm_family",
        "parameter_set_id",
        "is_control",
        "scorer_id",
        "context_view",
        "evidence_selector_context_view",
        "evidence_selector_source_view",
        "sense_representation",
        "aggregation_rule",
        "decision_rule",
        "phrase_handling",
        "evidence_control",
        "source_evidence_scope_id",
        "source_evidence_batch_count",
        "source_evidence_attached_row_count",
        "fit_scope",
        "min_active_score",
        "min_margin",
        "ratio_threshold",
        "softmax_threshold",
        "pairwise_min_win_rate",
        "selection_top_k",
        "cases_total",
        "harmful_replace_count",
        "false_abstain_count",
        "decision_accuracy",
        "winner_accuracy",
        "shadow_winner_accuracy",
        "replace_recall",
        "ranking_roc_auc",
        "ranking_average_precision",
        "ranking_unique_score_count",
        "objective_score",
        "harmful_replace_case_ids",
        "false_abstain_case_ids",
        "predicted_replace_case_ids",
        "replace_case_signature",
    )
    return {key: row.get(key) for key in keys}


def _public_selection_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    return {
        "config_id": str(row.get("config_id") or "").strip(),
        "algorithm_family": str(row.get("algorithm_family") or "").strip(),
        "parameter_set_id": str(row.get("parameter_set_id") or "").strip(),
        "decision_rule": str(row.get("decision_rule") or "").strip(),
        "min_active_score": row.get("min_active_score"),
        "min_margin": row.get("min_margin"),
        "ratio_threshold": row.get("ratio_threshold"),
        "softmax_threshold": row.get("softmax_threshold"),
        "pairwise_min_win_rate": row.get("pairwise_min_win_rate"),
        "overall": _public_config_row(row),
        "discovery": dict(_split_summary(row, "discovery")),
        "locked_eval": dict(_split_summary(row, "locked_eval")),
    }


def _public_case_row(row: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "case_id",
        "original_case_id",
        "family_id",
        "original_family_id",
        "evaluation_suite_id",
        "evaluation_suite_role",
        "gold_decision",
        "gold_winner",
        "gold_winner_type",
        "predicted_decision",
        "predicted_winner",
        "predicted_winner_type",
        "active_score",
        "strongest_shadow_score",
        "margin",
        "replacement_confidence",
        "phrase_preemption_hit",
        "phrase_reason_code",
        "reason_codes",
    )
    return {key: row.get(key) for key in keys}


def _primary_metric_signature(row: Mapping[str, object]) -> str:
    return "|".join(
        (
            f"harm={int(row.get('harmful_replace_count') or 0)}",
            f"false={int(row.get('false_abstain_count') or 0)}",
            f"decision={float(row.get('decision_accuracy') or 0.0):.6f}",
            f"winner={float(row.get('winner_accuracy') or 0.0):.6f}",
        )
    )


def _split_summary(row: Mapping[str, object], split: str) -> Mapping[str, object]:
    summaries = row.get("split_summaries")
    if isinstance(summaries, Mapping):
        summary = summaries.get(split)
        if isinstance(summary, Mapping):
            return summary
    return {}


def _same_config(
    left: Mapping[str, object] | None,
    right: Mapping[str, object] | None,
) -> bool:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    return str(left.get("config_id") or "") == str(right.get("config_id") or "")


def _split_objective_gap(
    left: Mapping[str, object] | None,
    right: Mapping[str, object] | None,
    *,
    split: str,
) -> float | None:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return None
    return _round_float(
        float(_split_summary(left, split).get("objective_score") or 0.0)
        - float(_split_summary(right, split).get("objective_score") or 0.0)
    )


def _selection_locked_objective(row: Mapping[str, object]) -> float:
    selected = row.get("selected_on_discovery")
    if not isinstance(selected, Mapping):
        return 0.0
    locked = selected.get("locked_eval")
    if not isinstance(locked, Mapping):
        return 0.0
    return float(locked.get("objective_score") or 0.0)


def _group_by(
    rows: Sequence[Mapping[str, object]], key: str
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "")].append(row)
    return dict(grouped)


def _negative_control_failed_as_expected(
    row: Mapping[str, object],
    *,
    mode: str,
    incumbent_accuracy: float,
) -> bool:
    harmful = int(row.get("harmful_replace_count") or 0)
    false_abstain = int(row.get("false_abstain_count") or 0)
    accuracy = float(row.get("decision_accuracy") or 0.0)
    if mode == "over_replace":
        return harmful > 0
    if mode == "over_abstain":
        return false_abstain > 0
    if mode in {"collapse", "lexical_leakage"}:
        return accuracy < incumbent_accuracy
    return harmful > 0 or false_abstain > 0 or accuracy < incumbent_accuracy


def _is_harmful_replace(row: Mapping[str, object]) -> bool:
    return row.get("predicted_decision") == "replace" and row.get("gold_decision") != "replace"


def _is_false_abstain(row: Mapping[str, object]) -> bool:
    return row.get("predicted_decision") != "replace" and row.get("gold_decision") == "replace"


def _classify_gold_winner_type(gold_winner: str, *, active_sense_id: str) -> str:
    normalized = str(gold_winner or "").strip()
    if not normalized or normalized in {"none", "abstain"}:
        return "none"
    if normalized == active_sense_id:
        return "active"
    return "shadow"


def _case_split(
    case_id: str,
    *,
    split_modulo: int,
    locked_eval_remainders: Sequence[int],
) -> str:
    modulo = max(2, int(split_modulo))
    digest = hashlib.sha256(str(case_id or "").encode("utf-8")).hexdigest()
    remainder = int(digest[:8], 16) % modulo
    return "locked_eval" if remainder in set(locked_eval_remainders) else "discovery"


def _summary_from_cases(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    summary = _new_sentence_veto_summary()
    for case in cases:
        _accumulate_sentence_veto_summary(summary, result=SimpleNamespace(**dict(case)))
    _finalize_sentence_veto_summary(summary)
    return summary


def _build_split_summaries(cases: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for split in ("discovery", "locked_eval"):
        split_cases = [case for case in cases if str(case.get("split") or "") == split]
        summary = _summary_from_cases(split_cases)
        public = _public_summary(summary)
        public.update(_ranking_metrics(split_cases))
        public["objective_score"] = _objective_score(public)
        rows[split] = public
    return rows


def _ranking_metrics(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    scored_rows: list[tuple[float, int, str]] = []
    for row in cases:
        case_id = str(row.get("case_id") or "").strip()
        label = 1 if str(row.get("gold_decision") or "") == "replace" else 0
        score = _finite_score(row.get("replacement_confidence"))
        scored_rows.append((score, label, case_id))
    positives = sum(label for _score, label, _case_id in scored_rows)
    negatives = len(scored_rows) - positives
    positive_scores = [score for score, label, _case_id in scored_rows if label == 1]
    negative_scores = [score for score, label, _case_id in scored_rows if label == 0]
    return {
        "ranking_positive_cases": positives,
        "ranking_negative_cases": negatives,
        "ranking_roc_auc": _roc_auc(scored_rows),
        "ranking_average_precision": _average_precision(scored_rows),
        "ranking_unique_score_count": len({score for score, _label, _case_id in scored_rows}),
        "ranking_positive_score_mean": _mean(positive_scores),
        "ranking_negative_score_mean": _mean(negative_scores),
        "ranking_positive_score_min": min(positive_scores) if positive_scores else None,
        "ranking_positive_score_max": max(positive_scores) if positive_scores else None,
        "ranking_negative_score_min": min(negative_scores) if negative_scores else None,
        "ranking_negative_score_max": max(negative_scores) if negative_scores else None,
    }


def _roc_auc(scored_rows: Sequence[tuple[float, int, str]]) -> float | None:
    positives = sum(label for _score, label, _case_id in scored_rows)
    negatives = len(scored_rows) - positives
    if positives <= 0 or negatives <= 0:
        return None
    sorted_rows = sorted(scored_rows, key=lambda row: row[0])
    rank_lookup: dict[str, float] = {}
    start = 0
    while start < len(sorted_rows):
        end = start + 1
        while end < len(sorted_rows) and sorted_rows[end][0] == sorted_rows[start][0]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        for _score, _label, case_id in sorted_rows[start:end]:
            rank_lookup[case_id] = average_rank
        start = end
    positive_rank_sum = sum(
        rank_lookup[case_id] for _score, label, case_id in scored_rows if label == 1
    )
    auc = (positive_rank_sum - (positives * (positives + 1) / 2.0)) / (positives * negatives)
    return _round_float(auc)


def _average_precision(scored_rows: Sequence[tuple[float, int, str]]) -> float | None:
    positives = sum(label for _score, label, _case_id in scored_rows)
    if positives <= 0:
        return None
    sorted_rows = sorted(scored_rows, key=lambda row: (-row[0], row[2]))
    true_positive_count = 0
    precision_sum = 0.0
    for index, (_score, label, _case_id) in enumerate(sorted_rows, start=1):
        if label != 1:
            continue
        true_positive_count += 1
        precision_sum += true_positive_count / index
    return _round_float(precision_sum / positives)


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return _round_float(sum(values) / len(values))


def _finite_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isinf(score):
        return 1_000_000.0 if score > 0 else -1_000_000.0
    if math.isnan(score):
        return 0.0
    return score


def _render_public_config_row(label: str, row: Mapping[str, object]) -> list[str]:
    return [
        f"- {label}: `{row.get('config_id', '')}`",
        f"  - Harmful / false abstain: `{int(row.get('harmful_replace_count') or 0)}` / `{int(row.get('false_abstain_count') or 0)}`",
        f"  - Decision / winner accuracy: `{_render_rate(row.get('decision_accuracy'))}` / `{_render_rate(row.get('winner_accuracy'))}`",
        f"  - Shape: `{row.get('scorer_id', '')}:{row.get('context_view', '')}:{row.get('sense_representation', '')}:{row.get('aggregation_rule', '')}:{row.get('decision_rule', '')}:{row.get('phrase_handling', '')}`",
        f"  - Source scope: `{row.get('source_evidence_scope_id', '')}` (`{int(row.get('source_evidence_attached_row_count') or 0)}` attached rows)",
    ]


def _as_mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _breakdown_summary(row: Mapping[str, object]) -> Mapping[str, object]:
    summary = row.get("summary")
    return summary if isinstance(summary, Mapping) else row


def _render_rate(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "n/a"


def _render_float(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def _render_range(left: object, right: object) -> str:
    return f"{_render_float(left)}..{_render_float(right)}"


__all__ = [name for name in globals() if not name.startswith("__")]
