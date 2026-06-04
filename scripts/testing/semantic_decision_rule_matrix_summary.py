#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403
from semantic_decision_rule_matrix_metrics import *  # noqa: F403


def _config_summary_row(
    *,
    config: Mapping[str, object],
    summary: Mapping[str, object],
    case_rows: Sequence[Mapping[str, object]],
    family_breakdown: Sequence[Mapping[str, object]],
    suite_breakdown: Sequence[Mapping[str, object]],
    slice_tag_breakdown: Sequence[Mapping[str, object]],
    gold_winner_type_breakdown: Sequence[Mapping[str, object]],
    harmful_replace_rows: Sequence[Mapping[str, object]],
    false_abstain_rows: Sequence[Mapping[str, object]],
    winner_error_rows: Sequence[Mapping[str, object]],
    drop_source_families: Sequence[str],
    threshold_override: Mapping[str, object] | None,
) -> dict[str, object]:
    row = {
        "config_id": str(config.get("config_id") or "").strip(),
        "label": str(config.get("label") or "").strip(),
        "category": str(config.get("category") or "").strip(),
        "algorithm_family": str(
            config.get("algorithm_family") or config.get("decision_rule") or ""
        ).strip(),
        "parameter_set_id": str(config.get("parameter_set_id") or "").strip(),
        "manifest_index": int(config.get("manifest_index") or 0),
        "is_control": bool(config.get("is_control")),
        "expected_failure_mode": str(config.get("expected_failure_mode") or "").strip(),
        "scorer_id": str(config.get("scorer_id") or "").strip(),
        "model_name": str(config.get("model_name") or "").strip(),
        "context_view": str(config.get("context_view") or "").strip(),
        "evidence_selector_context_view": str(
            config.get("evidence_selector_context_view") or ""
        ).strip(),
        "evidence_selector_source_view": str(
            config.get("evidence_selector_source_view") or ""
        ).strip(),
        "sense_representation": str(config.get("sense_representation") or "").strip(),
        "aggregation_rule": str(config.get("aggregation_rule") or "").strip(),
        "decision_rule": str(config.get("decision_rule") or "").strip(),
        "phrase_handling": str(config.get("phrase_handling") or "").strip(),
        "evidence_control": str(config.get("evidence_control") or "normal").strip(),
        "source_evidence_scope_id": str(config.get("source_evidence_scope_id") or "").strip(),
        "source_evidence_batch_count": len(_as_mapping_rows(config.get("source_evidence_batches"))),
        "source_evidence_attached_row_count": sum(
            int(batch.get("attached_row_count") or 0)
            for batch in _as_mapping_rows(config.get("source_evidence_batches"))
        ),
        "fit_scope": str(config.get("fit_scope") or "").strip(),
        "min_active_score": float(config.get("min_active_score") or 0.0),
        "min_margin": float(config.get("min_margin") or 0.0),
        "ratio_threshold": float(config.get("ratio_threshold") or 1.0),
        "softmax_threshold": float(config.get("softmax_threshold") or 0.5),
        "pairwise_min_win_rate": float(config.get("pairwise_min_win_rate") or 0.75),
        "top_k": int(config.get("top_k") or 2),
        "selection_top_k": int(config.get("selection_top_k") or config.get("top_k") or 2),
        "drop_source_families": list(drop_source_families),
        "threshold_override": dict(threshold_override or {}),
    }
    row.update(_public_summary(summary))
    row.update(_ranking_metrics(case_rows))
    row["split_summaries"] = _build_split_summaries(case_rows)
    row["objective_score"] = _objective_score(row)
    row["family_breakdown"] = list(family_breakdown)
    row["suite_breakdown"] = list(suite_breakdown)
    row["slice_tag_breakdown"] = list(slice_tag_breakdown)
    row["gold_winner_type_breakdown"] = list(gold_winner_type_breakdown)
    row["harmful_replace_case_ids"] = [
        str(case.get("case_id") or "") for case in case_rows if _is_harmful_replace(case)
    ]
    row["false_abstain_case_ids"] = [
        str(case.get("case_id") or "") for case in case_rows if _is_false_abstain(case)
    ]
    row["predicted_replace_case_ids"] = [
        str(case.get("case_id") or "")
        for case in case_rows
        if str(case.get("predicted_decision") or "") == "replace"
    ]
    row["replace_case_signature"] = _case_id_signature(row["predicted_replace_case_ids"])
    row["winner_signature"] = _case_id_signature(
        [
            f"{case.get('case_id')}={case.get('predicted_winner')}"
            for case in case_rows
            if str(case.get("case_id") or "")
        ]
    )
    row["sample_harmful_replace_rows"] = [_public_case_row(case) for case in harmful_replace_rows]
    row["sample_false_abstain_rows"] = [_public_case_row(case) for case in false_abstain_rows]
    row["sample_winner_error_rows"] = [_public_case_row(case) for case in winner_error_rows]
    return row


def _build_best_by_constraint(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    zero_harm = [row for row in candidates if int(row.get("harmful_replace_count") or 0) == 0]
    incumbent_false = int(incumbent.get("false_abstain_count") or 0) if incumbent else None
    incumbent_winner = float(incumbent.get("winner_accuracy") or 0.0) if incumbent else 0.0
    incumbent_accuracy = float(incumbent.get("decision_accuracy") or 0.0) if incumbent else 0.0
    promotable = [
        row
        for row in zero_harm
        if incumbent_false is None
        or (
            int(row.get("false_abstain_count") or 0) <= incumbent_false
            and float(row.get("winner_accuracy") or 0.0) >= incumbent_winner
            and float(row.get("decision_accuracy") or 0.0) >= incumbent_accuracy
        )
    ]
    return {
        "incumbent_control": _public_config_row(incumbent),
        "best_overall": _public_config_row(_select_best(candidates)),
        "best_zero_harm": _public_config_row(_select_best(zero_harm)),
        "best_promotable_candidate": _public_config_row(_select_best(promotable)),
        "best_by_decision_rule": {
            key: _public_config_row(_select_best(value))
            for key, value in _group_by(candidates, "decision_rule").items()
        },
        "best_by_scorer": {
            key: _public_config_row(_select_best(value))
            for key, value in _group_by(candidates, "scorer_id").items()
        },
    }


def _build_family_bakeoff_summary(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped = _group_by(candidates, "algorithm_family")
    incumbent_false = int(incumbent.get("false_abstain_count") or 0) if incumbent else None
    incumbent_winner = float(incumbent.get("winner_accuracy") or 0.0) if incumbent else 0.0
    incumbent_accuracy = float(incumbent.get("decision_accuracy") or 0.0) if incumbent else 0.0
    rows: list[dict[str, object]] = []
    for family, family_rows in sorted(grouped.items()):
        zero_harm = [row for row in family_rows if int(row.get("harmful_replace_count") or 0) == 0]
        promotable = [
            row
            for row in zero_harm
            if incumbent_false is None
            or (
                int(row.get("false_abstain_count") or 0) <= incumbent_false
                and float(row.get("winner_accuracy") or 0.0) >= incumbent_winner
                and float(row.get("decision_accuracy") or 0.0) >= incumbent_accuracy
            )
        ]
        rows.append(
            {
                "algorithm_family": family,
                "config_count": len(family_rows),
                "zero_harm_config_count": len(zero_harm),
                "best_row": _public_config_row(_select_best(family_rows)),
                "best_zero_harm_row": _public_config_row(_select_best(zero_harm)),
                "best_promotable_row": _public_config_row(_select_best(promotable)),
            }
        )
    rows.sort(
        key=lambda row: (
            float(
                (row.get("best_zero_harm_row") or row.get("best_row") or {}).get("objective_score")
                or 0.0
            ),
            str(row.get("algorithm_family") or ""),
        )
    )
    return rows


def _build_decision_signature_summary(
    config_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped = _group_by(candidates, "replace_case_signature")
    cluster_rows: list[dict[str, object]] = []
    for signature, rows in grouped.items():
        sorted_rows = sorted(rows, key=_rank_key)
        best = sorted_rows[0] if sorted_rows else {}
        cluster_rows.append(
            {
                "signature": signature,
                "config_count": len(sorted_rows),
                "sample_config_ids": [str(row.get("config_id") or "") for row in sorted_rows[:5]],
                "algorithm_families": sorted(
                    {
                        str(row.get("algorithm_family") or "")
                        for row in sorted_rows
                        if str(row.get("algorithm_family") or "")
                    }
                ),
                "best_row": _public_config_row(best),
            }
        )
    cluster_rows.sort(
        key=lambda row: (
            -int(row.get("config_count") or 0),
            str(row.get("signature") or ""),
        )
    )
    return {
        "unique_replace_signature_count": len(grouped),
        "largest_replace_signature_size": int(cluster_rows[0].get("config_count") or 0)
        if cluster_rows
        else 0,
        "top_replace_signature_clusters": cluster_rows[:12],
    }


def _build_metric_tie_summary(
    config_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in candidates:
        grouped[_primary_metric_signature(row)].append(row)
    tie_rows: list[dict[str, object]] = []
    for signature, rows in grouped.items():
        if len(rows) <= 1:
            continue
        roc_values = [
            float(row.get("ranking_roc_auc"))
            for row in rows
            if row.get("ranking_roc_auc") is not None
        ]
        ap_values = [
            float(row.get("ranking_average_precision"))
            for row in rows
            if row.get("ranking_average_precision") is not None
        ]
        sorted_rows = sorted(rows, key=_ranking_quality_key)
        tie_rows.append(
            {
                "metric_signature": signature,
                "config_count": len(rows),
                "unique_replace_signature_count": len(
                    {
                        str(row.get("replace_case_signature") or "")
                        for row in rows
                        if str(row.get("replace_case_signature") or "")
                    }
                ),
                "algorithm_families": sorted(
                    {
                        str(row.get("algorithm_family") or "")
                        for row in rows
                        if str(row.get("algorithm_family") or "")
                    }
                ),
                "roc_auc_min": min(roc_values) if roc_values else None,
                "roc_auc_max": max(roc_values) if roc_values else None,
                "average_precision_min": min(ap_values) if ap_values else None,
                "average_precision_max": max(ap_values) if ap_values else None,
                "best_ranking_row": _public_config_row(sorted_rows[0]),
                "worst_ranking_row": _public_config_row(sorted_rows[-1]),
                "sample_config_ids": [
                    str(row.get("config_id") or "") for row in sorted(rows, key=_rank_key)[:8]
                ],
            }
        )
    tie_rows.sort(
        key=lambda row: (
            -int(row.get("config_count") or 0),
            -int(row.get("unique_replace_signature_count") or 0),
            str(row.get("metric_signature") or ""),
        )
    )
    return {
        "tied_group_count": len(tie_rows),
        "largest_tied_group_size": int(tie_rows[0].get("config_count") or 0) if tie_rows else 0,
        "top_tied_groups": tie_rows[:20],
    }


def _build_selection_validation_summary(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped = _group_by(candidates, "algorithm_family")
    rows: list[dict[str, object]] = []
    for family, family_rows in sorted(grouped.items()):
        selected_on_discovery = _select_best_for_split(family_rows, "discovery")
        selected_on_all_cases = _select_best(family_rows)
        locked_oracle = _select_best_for_split(family_rows, "locked_eval")
        if not selected_on_discovery:
            continue
        rows.append(
            {
                "algorithm_family": family,
                "config_count": len(family_rows),
                "selected_on_discovery": _public_selection_row(selected_on_discovery),
                "selected_on_all_cases": _public_selection_row(selected_on_all_cases),
                "locked_oracle": _public_selection_row(locked_oracle),
                "matches_all_case_selection": _same_config(
                    selected_on_discovery,
                    selected_on_all_cases,
                ),
                "matches_locked_oracle": _same_config(selected_on_discovery, locked_oracle),
                "locked_objective_gap_vs_oracle": _split_objective_gap(
                    selected_on_discovery,
                    locked_oracle,
                    split="locked_eval",
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            _selection_locked_objective(row),
            str(row.get("algorithm_family") or ""),
        )
    )
    return {
        "selection_policy": (
            "select the best config inside each algorithm family using discovery-split "
            "objective only; report locked-eval metrics after selection"
        ),
        "incumbent_config_id": str(incumbent.get("config_id") or "").strip()
        if isinstance(incumbent, Mapping)
        else "",
        "rows": rows,
    }


def _build_incumbent_delta_summary(
    config_rows: Sequence[Mapping[str, object]],
    case_results: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(incumbent, Mapping):
        return {}
    incumbent_config_id = str(incumbent.get("config_id") or "").strip()
    by_config: dict[str, dict[str, Mapping[str, object]]] = defaultdict(dict)
    for row in case_results:
        config_id = str(row.get("config_id") or "").strip()
        case_id = str(row.get("case_id") or "").strip()
        if config_id and case_id:
            by_config[config_id][case_id] = row
    incumbent_rows = by_config.get(incumbent_config_id, {})
    if not incumbent_rows:
        return {"incumbent_config_id": incumbent_config_id, "top_delta_rows": []}
    delta_rows: list[dict[str, object]] = []
    identical_decision_count = 0
    for config in config_rows:
        config_id = str(config.get("config_id") or "").strip()
        if not config_id or config_id == incumbent_config_id:
            continue
        if str(config.get("expected_failure_mode") or ""):
            continue
        case_lookup = by_config.get(config_id, {})
        delta = _config_delta_against_incumbent(
            config_id=config_id,
            case_lookup=case_lookup,
            incumbent_lookup=incumbent_rows,
        )
        if int(delta.get("decision_changed_count") or 0) == 0:
            identical_decision_count += 1
        delta_rows.append(delta)
    delta_rows.sort(
        key=lambda row: (
            -int(row.get("decision_changed_count") or 0),
            -int(row.get("false_abstain_fixed_count") or 0),
            int(row.get("harmful_introduced_count") or 0),
            str(row.get("config_id") or ""),
        )
    )
    return {
        "incumbent_config_id": incumbent_config_id,
        "compared_config_count": len(delta_rows),
        "identical_decision_count": identical_decision_count,
        "top_delta_rows": delta_rows[:40],
    }


def _config_delta_against_incumbent(
    *,
    config_id: str,
    case_lookup: Mapping[str, Mapping[str, object]],
    incumbent_lookup: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    decision_changed: list[str] = []
    winner_changed: list[str] = []
    false_abstain_fixed: list[str] = []
    false_abstain_introduced: list[str] = []
    harmful_fixed: list[str] = []
    harmful_introduced: list[str] = []
    replace_gained: list[str] = []
    replace_lost: list[str] = []
    for case_id, incumbent_row in incumbent_lookup.items():
        row = case_lookup.get(case_id)
        if not row:
            continue
        incumbent_decision = str(incumbent_row.get("predicted_decision") or "")
        decision = str(row.get("predicted_decision") or "")
        gold_decision = str(row.get("gold_decision") or "")
        if decision != incumbent_decision:
            decision_changed.append(case_id)
        if str(row.get("predicted_winner") or "") != str(
            incumbent_row.get("predicted_winner") or ""
        ):
            winner_changed.append(case_id)
        if incumbent_decision != "replace" and decision == "replace":
            replace_gained.append(case_id)
        if incumbent_decision == "replace" and decision != "replace":
            replace_lost.append(case_id)
        if incumbent_decision != "replace" and gold_decision == "replace" and decision == "replace":
            false_abstain_fixed.append(case_id)
        if incumbent_decision == "replace" and gold_decision == "replace" and decision != "replace":
            false_abstain_introduced.append(case_id)
        if (
            incumbent_decision == "replace"
            and str(incumbent_row.get("gold_decision") or "") != "replace"
            and decision != "replace"
        ):
            harmful_fixed.append(case_id)
        if incumbent_decision != "replace" and decision == "replace" and gold_decision != "replace":
            harmful_introduced.append(case_id)
    return {
        "config_id": config_id,
        "decision_changed_count": len(decision_changed),
        "winner_changed_count": len(winner_changed),
        "replace_gained_count": len(replace_gained),
        "replace_lost_count": len(replace_lost),
        "false_abstain_fixed_count": len(false_abstain_fixed),
        "false_abstain_introduced_count": len(false_abstain_introduced),
        "harmful_fixed_count": len(harmful_fixed),
        "harmful_introduced_count": len(harmful_introduced),
        "sample_decision_changed_case_ids": decision_changed[:8],
        "sample_false_abstain_fixed_case_ids": false_abstain_fixed[:8],
        "sample_false_abstain_introduced_case_ids": false_abstain_introduced[:8],
        "sample_harmful_introduced_case_ids": harmful_introduced[:8],
    }


def _build_negative_control_summary(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    incumbent_accuracy = float(incumbent.get("decision_accuracy") or 0.0) if incumbent else 1.0
    rows: list[dict[str, object]] = []
    for row in config_rows:
        mode = str(row.get("expected_failure_mode") or "").strip()
        if not mode:
            continue
        failed_as_expected = _negative_control_failed_as_expected(
            row,
            mode=mode,
            incumbent_accuracy=incumbent_accuracy,
        )
        public = _public_config_row(row) or {}
        public["expected_failure_mode"] = mode
        public["status"] = "failed_as_expected" if failed_as_expected else "unexpectedly_safe"
        rows.append(public)
    if not rows:
        return {"status": "not_applicable", "rows": []}
    status = (
        "ok"
        if rows and all(row.get("status") == "failed_as_expected" for row in rows)
        else "review"
    )
    return {"status": status, "rows": rows}


def _build_overfitting_checks(
    config_rows: Sequence[Mapping[str, object]],
    case_results: Sequence[Mapping[str, object]],
    *,
    defaults: Mapping[str, object],
) -> dict[str, object]:
    by_config: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in case_results:
        by_config[str(row.get("config_id") or "")].append(row)
    rows: list[dict[str, object]] = []
    for config in config_rows:
        config_id = str(config.get("config_id") or "").strip()
        cases = by_config.get(config_id, [])
        discovery = [case for case in cases if str(case.get("split") or "") == "discovery"]
        locked = [case for case in cases if str(case.get("split") or "") == "locked_eval"]
        discovery_summary = _summary_from_cases(discovery)
        locked_summary = _summary_from_cases(locked)
        leave_one_out = _leave_one_family_out(cases)
        rows.append(
            {
                "config_id": config_id,
                "discovery_cases": discovery_summary.get("cases_total", 0),
                "locked_eval_cases": locked_summary.get("cases_total", 0),
                "discovery_objective_score": _objective_score(discovery_summary),
                "locked_eval_objective_score": _objective_score(locked_summary),
                "worst_leave_one_family": leave_one_out.get("worst_family_id", ""),
                "worst_leave_one_family_objective_score": leave_one_out.get(
                    "worst_objective_score"
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            float(row.get("locked_eval_objective_score") or 0.0),
            float(row.get("discovery_objective_score") or 0.0),
            str(row.get("config_id") or ""),
        )
    )
    return {
        "split_policy": "deterministic_case_id_hash_modulo",
        "split_modulo": int(defaults.get("split_modulo") or 4),
        "locked_eval_remainders": _normalize_ints(
            defaults.get("locked_eval_remainders"),
            default=(0,),
        ),
        "rows": rows,
    }


def _leave_one_family_out(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    family_ids = sorted(
        {str(case.get("family_id") or "") for case in cases if case.get("family_id")}
    )
    rows: list[dict[str, object]] = []
    for family_id in family_ids:
        summary = _summary_from_cases(
            [case for case in cases if case.get("family_id") != family_id]
        )
        rows.append(
            {
                "family_id": family_id,
                "objective_score": _objective_score(summary),
                "harmful_replace_count": summary.get("harmful_replace_count"),
                "false_abstain_count": summary.get("false_abstain_count"),
            }
        )
    if not rows:
        return {}
    worst = sorted(
        rows, key=lambda row: (-float(row.get("objective_score") or 0.0), row["family_id"])
    )[0]
    return {
        "rows": rows,
        "worst_family_id": worst["family_id"],
        "worst_objective_score": worst["objective_score"],
    }


def _build_recommendation(report: Mapping[str, object]) -> str:
    best = (
        report.get("best_by_constraint")
        if isinstance(report.get("best_by_constraint"), Mapping)
        else {}
    )
    incumbent = (
        best.get("incumbent_control") if isinstance(best.get("incumbent_control"), Mapping) else {}
    )
    candidate = (
        best.get("best_promotable_candidate")
        if isinstance(best.get("best_promotable_candidate"), Mapping)
        else {}
    )
    negative = (
        report.get("negative_control_summary")
        if isinstance(report.get("negative_control_summary"), Mapping)
        else {}
    )
    if not candidate:
        return (
            "No candidate cleared the incumbent-aware promotability screen; treat the matrix "
            "as evidence for source coverage or representation work before policy promotion."
        )
    notes = [
        f"Best promotable candidate is `{candidate.get('config_id', '')}`",
        f"with harmful `{int(candidate.get('harmful_replace_count') or 0)}`",
        f"and false abstain `{int(candidate.get('false_abstain_count') or 0)}`",
    ]
    if incumbent:
        notes.append(f"against incumbent `{incumbent.get('config_id', '')}`")
    negative_status = str(negative.get("status") or "").strip()
    if negative_status == "ok":
        notes.append("and negative controls failed as expected")
    elif negative_status == "not_applicable":
        notes.append("with negative controls delegated to the companion broad matrix")
    else:
        notes.append("but negative-control sanity needs review before promotion")
    return "; ".join(notes) + "."
