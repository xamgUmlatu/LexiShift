#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_routing_runtime_policy import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
    _ACTIVE_RESCUE_BACKUP_MARGIN_FLOOR,
    _ACTIVE_RESCUE_PRIMARY_MARGIN_FLOOR,
)
from semantic_routing_sentence_veto_support import build_sentence_veto_report  # noqa: E402
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float,
    _utility_weights,
    score_product_outcome_counts,
)
from semantic_veto_product_scope_filter_en_es import (  # noqa: E402
    PRODUCT_SCOPE_BROWSER_SOFT_ASSIST,
    classify_semantic_veto_product_scope,
    filter_sentence_veto_dataset_for_product_scope,
)
from semantic_veto_product_scope_algorithm_bakeoff_rendering import (  # noqa: E402
    _normalize_float_grid,
    _normalize_string_grid,
    _parse_float_grid,
    _parse_string_grid,
    _shortfall,
    render_product_scope_algorithm_bakeoff_markdown,
)


TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATASET = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_POLICY = TEST_INPUTS_ROOT / "semantic_veto_product_quality_policy_en_es.json"
DEFAULT_FILTERED_DATASET_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_repaired_full_dataset_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_algorithm_bakeoff_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_algorithm_bakeoff_en_es_latest.md"
)
DEFAULT_MIN_ACTIVE_GRID = "0.00,0.005,0.01,0.015,0.02,0.025,0.03,0.035,0.04,0.05,0.075,0.10"
DEFAULT_MIN_MARGIN_GRID = "-0.05,-0.025,-0.015,-0.01,-0.005,0.00,0.005,0.01,0.015,0.025,0.05"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rerun the semantic-veto algorithm-parameter bakeoff after excluding "
            "diagnostic label-preservation rows that are not product errors."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--filtered-dataset-out", type=Path, default=DEFAULT_FILTERED_DATASET_OUT)
    parser.add_argument("--scorers", default="tfidf_cosine,sentence_transformer_cosine")
    parser.add_argument("--context-views", default="masked_sentence")
    parser.add_argument("--evidence-views", default="all_evidence_text")
    parser.add_argument("--backup-evidence-view", default="sense_label")
    parser.add_argument("--min-active-grid", default=DEFAULT_MIN_ACTIVE_GRID)
    parser.add_argument("--min-margin-grid", default=DEFAULT_MIN_MARGIN_GRID)
    parser.add_argument("--phrase-control-modes", default="off,noun_family_frame_guard")
    parser.add_argument(
        "--active-rescue-modes",
        default="off,sense_label_near_tie_active_rescue",
    )
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dataset = _load_json(args.dataset_json)
    filtered_dataset, product_scope_summary = filter_sentence_veto_dataset_for_product_scope(
        dataset
    )
    args.filtered_dataset_out.parent.mkdir(parents=True, exist_ok=True)
    args.filtered_dataset_out.write_text(
        json.dumps(filtered_dataset, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    trace_sources = materialize_trace_sources(
        filtered_dataset_path=args.filtered_dataset_out,
        scorers=_parse_string_grid(args.scorers),
        context_views=_parse_string_grid(args.context_views),
        evidence_views=_parse_string_grid(args.evidence_views),
        backup_evidence_view=str(args.backup_evidence_view or "").strip() or "sense_label",
    )
    report = build_product_scope_algorithm_bakeoff_report(
        policy_payload=_load_json(args.policy_json),
        trace_sources=trace_sources,
        product_scope_summary=product_scope_summary,
        dataset_path=args.dataset_json,
        filtered_dataset_path=args.filtered_dataset_out,
        policy_path=args.policy_json,
        min_active_scores=_parse_float_grid(args.min_active_grid),
        min_margins=_parse_float_grid(args.min_margin_grid),
        phrase_control_modes=_parse_string_grid(args.phrase_control_modes),
        active_rescue_modes=_parse_string_grid(args.active_rescue_modes),
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_product_scope_algorithm_bakeoff_markdown(report))
    print(f"Wrote filtered dataset to {args.filtered_dataset_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def materialize_trace_sources(
    *,
    filtered_dataset_path: Path,
    scorers: Sequence[str],
    context_views: Sequence[str],
    evidence_views: Sequence[str],
    backup_evidence_view: str,
) -> list[dict[str, object]]:
    trace_sources: list[dict[str, object]] = []
    for scorer_id in scorers:
        for context_view in context_views:
            for evidence_view in evidence_views:
                primary_report = build_sentence_veto_report(
                    dataset_path=filtered_dataset_path,
                    scorer_id=scorer_id,
                    context_view=context_view,
                    evidence_view=evidence_view,
                    min_active_score=0.0,
                    min_margin=-1.0,
                    phrase_control_mode="off",
                    active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
                )
                backup_report = build_sentence_veto_report(
                    dataset_path=filtered_dataset_path,
                    scorer_id=scorer_id,
                    context_view=context_view,
                    evidence_view=backup_evidence_view,
                    min_active_score=0.0,
                    min_margin=-1.0,
                    phrase_control_mode="off",
                    active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
                )
                trace_sources.append(
                    {
                        "source_id": (
                            f"{scorer_id}:{context_view}:{evidence_view}:"
                            f"backup={backup_evidence_view}"
                        ),
                        "scorer_id": scorer_id,
                        "context_view": context_view,
                        "evidence_view": evidence_view,
                        "backup_evidence_view": backup_evidence_view,
                        "primary_report": primary_report,
                        "backup_report": backup_report,
                    }
                )
    return trace_sources


def build_product_scope_algorithm_bakeoff_report(
    *,
    policy_payload: Mapping[str, object],
    trace_sources: Sequence[Mapping[str, object]],
    product_scope_summary: Mapping[str, object],
    dataset_path: Path | None = None,
    filtered_dataset_path: Path | None = None,
    policy_path: Path | None = None,
    min_active_scores: Sequence[float] = (),
    min_margins: Sequence[float] = (),
    phrase_control_modes: Sequence[str] = (),
    active_rescue_modes: Sequence[str] = (),
    top_n: int = 20,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    weights = _utility_weights(policy_payload)
    acceptance = _as_mapping(policy_payload.get("acceptance"))
    active_grid = _normalize_float_grid(min_active_scores)
    margin_grid = _normalize_float_grid(min_margins)
    phrase_modes = _normalize_string_grid(phrase_control_modes)
    rescue_modes = _normalize_string_grid(active_rescue_modes)
    issues: list[str] = []
    if not trace_sources:
        issues.append("no_trace_sources")
    if not active_grid:
        issues.append("empty_min_active_grid")
    if not margin_grid:
        issues.append("empty_min_margin_grid")
    if not phrase_modes:
        issues.append("empty_phrase_control_modes")
    if not rescue_modes:
        issues.append("empty_active_rescue_modes")

    source_summaries: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    selected_failure_rows: dict[str, list[dict[str, object]]] = {}
    for source in trace_sources:
        normalized = _normalize_trace_source(source)
        primary_rows = normalized["primary_rows"]
        backup_rows_by_case = normalized["backup_rows_by_case"]
        source_summaries.append(
            {
                "source_id": normalized["source_id"],
                "scorer_id": normalized["scorer_id"],
                "context_view": normalized["context_view"],
                "evidence_view": normalized["evidence_view"],
                "backup_evidence_view": normalized["backup_evidence_view"],
                "primary_row_count": len(primary_rows),
                "backup_row_count": len(backup_rows_by_case),
            }
        )
        if not primary_rows:
            issues.append(f"no_primary_rows:{normalized['source_id']}")
            continue
        for phrase_control_mode in phrase_modes:
            for active_rescue_mode in rescue_modes:
                for min_active_score in active_grid:
                    for min_margin in margin_grid:
                        row, failures = _candidate_row(
                            source=normalized,
                            backup_rows_by_case=backup_rows_by_case,
                            min_active_score=min_active_score,
                            min_margin=min_margin,
                            phrase_control_mode=phrase_control_mode,
                            active_rescue_mode=active_rescue_mode,
                            weights=weights,
                            acceptance=acceptance,
                        )
                        candidate_rows.append(row)
                        if failures:
                            selected_failure_rows[row["config_id"]] = failures

    ranked_rows = sorted(candidate_rows, key=_candidate_rank_key)
    target_pass_rows = [
        row
        for row in ranked_rows
        if str(_as_mapping(row.get("target_checks")).get("target_status") or "") == "pass"
    ]
    status = "ok" if target_pass_rows and not issues else "review"
    summary = {
        "candidate_row_count": len(candidate_rows),
        "target_pass_count": len(target_pass_rows),
        "top_n": max(1, int(top_n)),
        "best_product_rank_row": _public_candidate_row(ranked_rows[0] if ranked_rows else None),
        "best_target_pass_row": _public_candidate_row(
            target_pass_rows[0] if target_pass_rows else None
        ),
        "highest_utility_row": _public_candidate_row(_best_by_utility(ranked_rows)),
        "high_recall_soft_assist_row": _public_candidate_row(
            _best_high_recall_soft_assist(ranked_rows)
        ),
        "safest_80pct_positive_row": _public_candidate_row(_safest_positive_target(ranked_rows)),
        "current_policy_like_rows": _current_policy_like_rows(ranked_rows),
        "best_by_scorer": _best_by_scorer(ranked_rows),
    }
    best_config_id = str(_as_mapping(summary.get("best_product_rank_row")).get("config_id") or "")
    high_recall_config_id = str(
        _as_mapping(summary.get("high_recall_soft_assist_row")).get("config_id") or ""
    )
    failure_config_ids = [
        config_id for config_id in (best_config_id, high_recall_config_id) if config_id
    ]
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "product_scope_algorithm_candidate_found"
            if target_pass_rows
            else "product_scope_algorithm_candidate_not_found"
        ),
        "generated_at": generated_at,
        "pair": str(policy_payload.get("pair") or "en-es"),
        "policy": {
            "path": _repo_path(policy_path),
            "policy_id": str(policy_payload.get("policy_id") or ""),
            "acceptance": dict(acceptance),
            "utility_weights": weights,
        },
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "filtered_dataset_path": _repo_path(filtered_dataset_path),
            "product_scope": dict(product_scope_summary),
        },
        "methodology": {
            "selection_scope": PRODUCT_SCOPE_BROWSER_SOFT_ASSIST,
            "selection_rule": (
                "Rank algorithm parameter rows under the configured product utility after "
                "excluding diagnostic label-preservation rows."
            ),
            "swept_parameters": [
                "scorer_id",
                "context_view",
                "evidence_view",
                "min_active_score",
                "min_margin",
                "phrase_control_mode",
                "active_rescue_mode",
            ],
            "active_rescue_replay": (
                "Uses a paired sense_label score trace and the same near-tie rescue "
                "floors as runtime policy."
            ),
            "runtime_policy_change": "none",
        },
        "e2e_checks": {
            "product_scope_filter_applied": bool(
                int(product_scope_summary.get("excluded_case_count") or 0) >= 0
            ),
            "diagnostic_label_rows_excluded": int(
                product_scope_summary.get("excluded_case_count") or 0
            ),
            "product_scope_rows_retained": int(
                product_scope_summary.get("retained_case_count") or 0
            ),
            "trace_sources_read": len(source_summaries),
            "candidate_rows_emitted": len(candidate_rows),
            "score_product_outcome_counts_used": True,
            "active_rescue_backup_scores_available": all(
                int(row.get("backup_row_count") or 0) >= int(row.get("primary_row_count") or 0)
                for row in source_summaries
            ),
            "issue_count": len(issues),
        },
        "summary": summary,
        "grid": {
            "min_active_scores": active_grid,
            "min_margins": margin_grid,
            "phrase_control_modes": phrase_modes,
            "active_rescue_modes": rescue_modes,
        },
        "trace_sources": source_summaries,
        "top_rows": [_public_candidate_row(row) for row in ranked_rows[: max(1, int(top_n))]],
        "target_pass_rows": [
            _public_candidate_row(row) for row in target_pass_rows[: max(1, int(top_n))]
        ],
        "failure_samples": {
            config_id: selected_failure_rows.get(config_id, [])[:20]
            for config_id in failure_config_ids
        },
        "rows": [_public_candidate_row(row) for row in ranked_rows],
        "issues": issues,
        "limitations": [
            "product_scope_filter_only_removes_the_current_synthetic_internal_project_code_template",
            "filtered_repaired_full_is_still_not_a_final_browsing_distribution",
            "threshold_selection_here_is_discovery_research_not_runtime_promotion",
            "band_and_llm_allocation_sweeps_must_be_rerun_after_selecting_candidate_rows",
        ],
        "next_steps": [
            "Use the top product-scope candidate rows as inputs to the corrected band and heuristic sweeps.",
            "Carry at least one conservative row and one high-recall soft-assist row forward as comparators.",
            "Do not spend on broad LLM generation until the corrected band read is regenerated.",
        ],
    }


def _candidate_row(
    *,
    source: Mapping[str, object],
    backup_rows_by_case: Mapping[str, Mapping[str, object]],
    min_active_score: float,
    min_margin: float,
    phrase_control_mode: str,
    active_rescue_mode: str,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    outcome_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    active_rescue_applied = 0
    phrase_preemption_applied = 0
    failures: list[dict[str, object]] = []
    for row in _mapping_rows(source.get("primary_rows")):
        scope = classify_semantic_veto_product_scope(row)
        if not bool(scope.get("include_in_product_scope")):
            continue
        case_id = str(row.get("case_id") or "")
        predicted, metadata = _replay_decision(
            row=row,
            backup_row=backup_rows_by_case.get(case_id),
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        )
        gold = _normalize_decision(row.get("gold_decision"))
        decision_counts[predicted] += 1
        if metadata["active_rescue_applied"]:
            active_rescue_applied += 1
        if metadata["phrase_preemption_applied"]:
            phrase_preemption_applied += 1
        outcome = _product_outcome(gold=gold, predicted=predicted)
        outcome_counts[outcome] += 1
        if outcome in {"positive_abstain", "negative_allow"} and len(failures) < 50:
            failures.append(
                {
                    "case_id": case_id,
                    "family_id": str(row.get("family_id") or ""),
                    "trigger": str(row.get("trigger") or row.get("source_phrase") or ""),
                    "gold_decision": gold,
                    "predicted_decision": predicted,
                    "product_outcome": outcome,
                    "active_score": _round4(row.get("active_score")),
                    "strongest_shadow_score": _round4(row.get("strongest_shadow_score")),
                    "margin": _round4(
                        _safe_float(row.get("active_score"))
                        - _safe_float(row.get("strongest_shadow_score"))
                    ),
                    "sentence": str(row.get("sentence") or ""),
                    "reason": metadata["reason"],
                }
            )
    metrics = score_product_outcome_counts(
        outcome_counts=outcome_counts,
        weights=weights,
        acceptance=acceptance,
    )
    predicted_replace = outcome_counts["positive_allow"] + outcome_counts["negative_allow"]
    harmful_share = (
        outcome_counts["negative_allow"] / predicted_replace if predicted_replace else None
    )
    target_checks = _as_mapping(metrics.get("target_checks"))
    config_id = (
        f"{source.get('scorer_id')}:{source.get('context_view')}:{source.get('evidence_view')}:"
        f"phrase={phrase_control_mode}:rescue={active_rescue_mode}:"
        f"a={min_active_score:.3f}:m={min_margin:.3f}"
    )
    positive_shortfall = _shortfall(
        metrics.get("positive_allow_rate"),
        _safe_float(acceptance.get("positive_allow_rate_min")),
    )
    negative_shortfall = _shortfall(
        metrics.get("negative_abstain_rate"),
        _safe_float(acceptance.get("negative_abstain_rate_min")),
    )
    return (
        {
            "config_id": config_id,
            "source_id": str(source.get("source_id") or ""),
            "scorer_id": str(source.get("scorer_id") or ""),
            "context_view": str(source.get("context_view") or ""),
            "evidence_view": str(source.get("evidence_view") or ""),
            "backup_evidence_view": str(source.get("backup_evidence_view") or ""),
            "decision_rule": "active_score_minus_strongest_shadow_with_optional_phrase_and_rescue",
            "phrase_control_mode": phrase_control_mode,
            "active_rescue_mode": active_rescue_mode,
            "min_active_score": float(min_active_score),
            "min_margin": float(min_margin),
            "outcome_counts": dict(outcome_counts),
            "metrics": metrics,
            "target_checks": dict(target_checks),
            "target_distance": round(positive_shortfall + negative_shortfall, 4),
            "positive_allow_shortfall": positive_shortfall,
            "negative_abstain_shortfall": negative_shortfall,
            "predicted_replace_count": predicted_replace,
            "predicted_abstain_count": decision_counts["abstain"],
            "harmful_share_of_replaces": None if harmful_share is None else round(harmful_share, 4),
            "active_rescue_applied_count": active_rescue_applied,
            "phrase_preemption_applied_count": phrase_preemption_applied,
        },
        failures,
    )


def _replay_decision(
    *,
    row: Mapping[str, object],
    backup_row: Mapping[str, object] | None,
    min_active_score: float,
    min_margin: float,
    phrase_control_mode: str,
    active_rescue_mode: str,
) -> tuple[str, dict[str, object]]:
    active_score = _safe_float(row.get("active_score"))
    shadow_score = _safe_float(row.get("strongest_shadow_score"))
    margin = active_score - shadow_score
    predicted = (
        "replace"
        if active_score >= float(min_active_score) and margin >= float(min_margin)
        else "abstain"
    )
    reason = "active_threshold_passed" if predicted == "replace" else "threshold_blocked"
    phrase_preemption_applied = False
    if phrase_control_mode == "noun_family_frame_guard" and bool(row.get("phrase_preemption_hit")):
        if predicted == "replace":
            phrase_preemption_applied = True
        predicted = "abstain"
        reason = "phrase_preemption"

    active_rescue_applied = False
    if (
        active_rescue_mode == "sense_label_near_tie_active_rescue"
        and predicted != "replace"
        and not bool(row.get("phrase_preemption_hit"))
        and margin >= _ACTIVE_RESCUE_PRIMARY_MARGIN_FLOOR
        and isinstance(backup_row, Mapping)
    ):
        backup_active = _safe_float(backup_row.get("active_score"))
        backup_shadow = _safe_float(backup_row.get("strongest_shadow_score"))
        backup_margin = backup_active - backup_shadow
        if (
            backup_active >= float(min_active_score)
            and backup_margin >= float(min_margin)
            and backup_margin >= _ACTIVE_RESCUE_BACKUP_MARGIN_FLOOR
        ):
            predicted = "replace"
            active_rescue_applied = True
            reason = "sense_label_near_tie_active_rescue"
    return predicted, {
        "reason": reason,
        "active_rescue_applied": active_rescue_applied,
        "phrase_preemption_applied": phrase_preemption_applied,
    }


def _normalize_trace_source(source: Mapping[str, object]) -> dict[str, object]:
    primary_report = _as_mapping(source.get("primary_report"))
    backup_report = _as_mapping(source.get("backup_report"))
    primary_config = _as_mapping(primary_report.get("config"))
    backup_config = _as_mapping(backup_report.get("config"))
    primary_rows = [
        row
        for row in _mapping_rows(primary_report.get("row_results"))
        if bool(classify_semantic_veto_product_scope(row).get("include_in_product_scope"))
    ]
    backup_rows = [
        row
        for row in _mapping_rows(backup_report.get("row_results"))
        if bool(classify_semantic_veto_product_scope(row).get("include_in_product_scope"))
    ]
    return {
        "source_id": str(source.get("source_id") or ""),
        "scorer_id": str(source.get("scorer_id") or primary_config.get("scorer_id") or ""),
        "context_view": str(source.get("context_view") or primary_config.get("context_view") or ""),
        "evidence_view": str(
            source.get("evidence_view") or primary_config.get("evidence_view") or ""
        ),
        "backup_evidence_view": str(
            source.get("backup_evidence_view") or backup_config.get("evidence_view") or ""
        ),
        "primary_rows": primary_rows,
        "backup_rows_by_case": {str(row.get("case_id") or ""): row for row in backup_rows},
    }


def _product_outcome(*, gold: str, predicted: str) -> str:
    product_class = "positive" if gold == "replace" else "negative"
    user_outcome = "allow" if predicted == "replace" else "abstain"
    return f"{product_class}_{user_outcome}"


def _normalize_decision(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"replace", "allow", "yes"}:
        return "replace"
    if text in {"abstain", "no", "none", "no_replace", "no-replace"}:
        return "abstain"
    raise ValueError(f"Unknown decision: {value!r}")


def _candidate_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    metrics = _as_mapping(row.get("metrics"))
    checks = _as_mapping(row.get("target_checks"))
    harmful_share = row.get("harmful_share_of_replaces")
    return (
        str(checks.get("target_status") or "") != "pass",
        -_safe_float(metrics.get("utility_score")),
        _safe_float(row.get("target_distance")),
        1.0 if harmful_share is None else _safe_float(harmful_share),
        -_safe_float(metrics.get("positive_allow_rate")),
        -_safe_float(metrics.get("negative_abstain_rate")),
        str(row.get("config_id") or ""),
    )


def _best_by_utility(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    if not rows:
        return None
    return sorted(
        rows,
        key=lambda row: (
            -_safe_float(_as_mapping(row.get("metrics")).get("utility_score")),
            _safe_float(row.get("target_distance")),
            str(row.get("config_id") or ""),
        ),
    )[0]


def _best_high_recall_soft_assist(
    rows: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    candidates = [
        row
        for row in rows
        if _safe_float(_as_mapping(row.get("metrics")).get("positive_allow_rate")) >= 0.8
        and (
            row.get("harmful_share_of_replaces") is None
            or _safe_float(row.get("harmful_share_of_replaces")) <= 0.30
        )
    ]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (
            -_safe_float(_as_mapping(row.get("metrics")).get("positive_allow_rate")),
            _safe_float(row.get("harmful_share_of_replaces")),
            -_safe_float(_as_mapping(row.get("metrics")).get("utility_score")),
            str(row.get("config_id") or ""),
        ),
    )[0]


def _safest_positive_target(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    candidates = [
        row
        for row in rows
        if _safe_float(_as_mapping(row.get("metrics")).get("positive_allow_rate")) >= 0.8
    ]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (
            int(_as_mapping(row.get("metrics")).get("negative_allow_count") or 0),
            -_safe_float(_as_mapping(row.get("metrics")).get("negative_abstain_rate")),
            -_safe_float(_as_mapping(row.get("metrics")).get("utility_score")),
            str(row.get("config_id") or ""),
        ),
    )[0]


def _current_policy_like_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    wanted = {
        (
            "tfidf_cosine",
            "masked_sentence",
            "all_evidence_text",
            "noun_family_frame_guard",
            "sense_label_near_tie_active_rescue",
            0.05,
            0.0,
        ),
        (
            "sentence_transformer_cosine",
            "masked_sentence",
            "all_evidence_text",
            "noun_family_frame_guard",
            "sense_label_near_tie_active_rescue",
            0.0,
            0.0,
        ),
    }
    found = []
    for row in rows:
        key = (
            str(row.get("scorer_id") or ""),
            str(row.get("context_view") or ""),
            str(row.get("evidence_view") or ""),
            str(row.get("phrase_control_mode") or ""),
            str(row.get("active_rescue_mode") or ""),
            round(_safe_float(row.get("min_active_score")), 3),
            round(_safe_float(row.get("min_margin")), 3),
        )
        if key in wanted:
            found.append(_public_candidate_row(row))
    return found


def _best_by_scorer(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for scorer_id in sorted({str(row.get("scorer_id") or "") for row in rows}):
        scorer_rows = [row for row in rows if str(row.get("scorer_id") or "") == scorer_id]
        if scorer_rows:
            output.append(_public_candidate_row(sorted(scorer_rows, key=_candidate_rank_key)[0]))
    return output


def _public_candidate_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    metrics = _as_mapping(row.get("metrics"))
    checks = _as_mapping(row.get("target_checks"))
    return {
        "config_id": str(row.get("config_id") or ""),
        "source_id": str(row.get("source_id") or ""),
        "scorer_id": str(row.get("scorer_id") or ""),
        "context_view": str(row.get("context_view") or ""),
        "evidence_view": str(row.get("evidence_view") or ""),
        "backup_evidence_view": str(row.get("backup_evidence_view") or ""),
        "decision_rule": str(row.get("decision_rule") or ""),
        "phrase_control_mode": str(row.get("phrase_control_mode") or ""),
        "active_rescue_mode": str(row.get("active_rescue_mode") or ""),
        "min_active_score": row.get("min_active_score"),
        "min_margin": row.get("min_margin"),
        "positive_allow_rate": metrics.get("positive_allow_rate"),
        "negative_abstain_rate": metrics.get("negative_abstain_rate"),
        "positive_allow_count": metrics.get("positive_allow_count"),
        "positive_abstain_count": metrics.get("positive_abstain_count"),
        "negative_abstain_count": metrics.get("negative_abstain_count"),
        "negative_allow_count": metrics.get("negative_allow_count"),
        "utility_score": metrics.get("utility_score"),
        "delta_vs_lexical_utility": metrics.get("delta_vs_lexical_utility"),
        "target_status": str(checks.get("target_status") or ""),
        "target_distance": row.get("target_distance"),
        "harmful_share_of_replaces": row.get("harmful_share_of_replaces"),
        "predicted_replace_count": row.get("predicted_replace_count"),
        "active_rescue_applied_count": row.get("active_rescue_applied_count"),
        "phrase_preemption_applied_count": row.get("phrase_preemption_applied_count"),
    }


def _round4(value: object) -> float:
    return round(_safe_float(value), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
