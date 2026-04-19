#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,
    RuntimeSimilarityBackend,
    SENTENCE_VETO_CONTEXT_VIEWS,
    SENTENCE_VETO_EVIDENCE_VIEWS,
    SENTENCE_VETO_PHRASE_CONTROL_MODES,
    SENTENCE_VETO_SCORERS,
)
from lexishift_core.rulegen.semantic_routing_runtime_policy import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
    SENTENCE_VETO_ACTIVE_RESCUE_MODES,
    SemanticDecisionPolicyConfig,
    _ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
    evaluate_runtime_semantic_match,
)
from semantic_routing_sentence_veto_helpers import (  # noqa: E402
    _accumulate_sentence_veto_summary,
    _append_sample,
    _collect_config_texts,
    _finalize_sentence_veto_breakdown_rows,
    _finalize_sentence_veto_summary,
    _new_sentence_veto_summary,
    _normalize_slice_dimensions,
    _normalize_string_list,
)
from semantic_routing_sentence_veto_reporting import (  # noqa: E402
    compute_sentence_veto_objective,
    render_sentence_veto_markdown as _render_sentence_veto_markdown,
    render_sentence_veto_sweep_markdown as _render_sentence_veto_sweep_markdown,
    select_best_sentence_veto_objective_row,
    sentence_veto_sweep_rank_key,
)

render_sentence_veto_markdown = _render_sentence_veto_markdown
render_sentence_veto_sweep_markdown = _render_sentence_veto_sweep_markdown

DEFAULT_SENTENCE_VETO_DATASET = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_routing_cases" / "en_es_sentence_veto_v2.json"
)
DEFAULT_SENTENCE_VETO_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_latest.json"
)
DEFAULT_SENTENCE_VETO_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_latest.md"
)
DEFAULT_SENTENCE_VETO_SWEEP_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_sweep_latest.json"
)
DEFAULT_SENTENCE_VETO_SWEEP_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_sweep_latest.md"
)


def load_sentence_veto_dataset(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Sentence-veto dataset must be a JSON object.")
    if int(payload.get("schema_version") or 0) != 1:
        raise ValueError("Sentence-veto dataset must declare schema_version=1.")
    if not str(payload.get("pair") or "").strip():
        raise ValueError("Sentence-veto dataset is missing `pair`.")
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)) or not families:
        raise ValueError("Sentence-veto dataset must include a non-empty `families` list.")
    normalized_families: list[dict[str, object]] = []
    for raw_family in families:
        if not isinstance(raw_family, Mapping):
            continue
        family_id = str(raw_family.get("family_id") or "").strip()
        trigger = str(raw_family.get("trigger") or "").strip()
        active = (
            dict(raw_family.get("active") or {})
            if isinstance(raw_family.get("active"), Mapping)
            else {}
        )
        shadows = [
            dict(shadow) for shadow in raw_family.get("shadows", ()) if isinstance(shadow, Mapping)
        ]
        cases = [dict(case) for case in raw_family.get("cases", ()) if isinstance(case, Mapping)]
        if not family_id or not trigger or not active or not cases:
            raise ValueError(
                "Each sentence-veto family must include `family_id`, `trigger`, `active`, and `cases`."
            )
        active_sense_id = str(active.get("sense_id") or "").strip()
        if not active_sense_id:
            raise ValueError(f"Family {family_id!r} is missing `active.sense_id`.")
        shadow_ids = {
            str(shadow.get("sense_id") or "").strip()
            for shadow in shadows
            if str(shadow.get("sense_id") or "").strip()
        }
        for case in cases:
            case_id = str(case.get("case_id") or "").strip()
            sentence = str(case.get("sentence") or "").strip()
            source_phrase = str(case.get("source_phrase") or "").strip()
            gold_winner = str(case.get("gold_winner") or "").strip()
            gold_decision = str(case.get("gold_decision") or "").strip().lower()
            if not case_id or not sentence or not source_phrase or not gold_winner:
                raise ValueError(
                    f"Family {family_id!r} contains a case missing one of "
                    f"`case_id`, `sentence`, `source_phrase`, or `gold_winner`."
                )
            if gold_decision and gold_decision not in {"replace", "abstain"}:
                raise ValueError(
                    f"Family {family_id!r} case {case_id!r} has unsupported gold_decision "
                    f"{gold_decision!r}."
                )
            if gold_winner not in {"none", active_sense_id} and gold_winner not in shadow_ids:
                raise ValueError(
                    f"Family {family_id!r} case {case_id!r} gold_winner {gold_winner!r} "
                    "does not match active or shadow sense ids."
                )
        normalized_families.append(
            {
                "family_id": family_id,
                "trigger": trigger,
                "active": active,
                "shadows": shadows,
                "cases": cases,
            }
        )
    payload["families"] = normalized_families
    return payload


def build_sentence_veto_report(
    *,
    dataset_path: Path,
    scorer_id: str,
    context_view: str = DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    evidence_view: str = DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    min_active_score: float = DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    phrase_control_mode: str = DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,
    active_rescue_mode: str = DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    dataset = load_sentence_veto_dataset(dataset_path)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    backend = RuntimeSimilarityBackend(
        scorer_id=scorer_id,
        model_name=str(model_name or "").strip(),
    )
    backend.fit(
        _collect_config_texts(
            dataset,
            context_view=context_view,
            evidence_view=evidence_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
    )
    resolved_active_rescue_mode = (
        str(active_rescue_mode or "").strip() or DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE
    )
    if resolved_active_rescue_mode not in SENTENCE_VETO_ACTIVE_RESCUE_MODES:
        raise ValueError(
            f"Unsupported sentence-veto active rescue mode: {resolved_active_rescue_mode!r}; "
            f"expected one of {SENTENCE_VETO_ACTIVE_RESCUE_MODES!r}"
        )
    policy = SemanticDecisionPolicyConfig(
        policy_id="sentence_veto_harness",
        pair=str(dataset.get("pair") or "").strip() or "en-es",
        scorer_id=scorer_id,
        model_name=str(model_name or "").strip(),
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=float(min_active_score),
        min_margin=float(min_margin),
        phrase_control_mode=phrase_control_mode,
        active_rescue_mode=resolved_active_rescue_mode,
        window_tokens=int(window_tokens),
        mask_token=str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    )
    backup_backend: RuntimeSimilarityBackend | None = None
    if resolved_active_rescue_mode != DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE:
        backup_backend = RuntimeSimilarityBackend(
            scorer_id=scorer_id,
            model_name=str(model_name or "").strip(),
        )
        backup_backend.fit(
            _collect_config_texts(
                dataset,
                context_view=context_view,
                evidence_view=_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
                window_tokens=window_tokens,
                mask_token=mask_token,
            )
        )

    summary = _new_sentence_veto_summary()
    family_breakdown: dict[str, dict[str, object]] = {}
    slice_tag_breakdown: dict[str, dict[str, object]] = {}
    gold_winner_type_breakdown: dict[str, dict[str, object]] = {}
    row_results: list[dict[str, object]] = []
    harmful_replace_rows: list[dict[str, object]] = []
    false_abstain_rows: list[dict[str, object]] = []
    winner_error_rows: list[dict[str, object]] = []

    for family in dataset["families"]:
        family_id = str(family.get("family_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        active = dict(family.get("active") or {})
        shadows = [dict(shadow) for shadow in family.get("shadows", ())]
        family_pos_tags = [
            str(value or "").strip()
            for value in (
                active.get("canonical_pos"),
                *(shadow.get("canonical_pos") for shadow in shadows),
            )
            if str(value or "").strip()
        ]
        family_entry = family_breakdown.setdefault(
            family_id,
            {
                "family_id": family_id,
                "trigger": trigger,
                "active_target": str(active.get("target_lemma") or "").strip(),
                "shadow_targets": [
                    str(shadow.get("target_lemma") or "").strip()
                    for shadow in shadows
                    if str(shadow.get("target_lemma") or "").strip()
                ],
                "summary": _new_sentence_veto_summary(),
            },
        )
        for case in family.get("cases", ()):
            result = evaluate_runtime_semantic_match(
                match_id=str(case.get("case_id") or "").strip(),
                sentence=str(case.get("sentence") or "").strip(),
                source_phrase=str(case.get("source_phrase") or "").strip(),
                active_sense=active,
                shadow_senses=shadows,
                policy=policy,
                scorer=backend,
                backup_scorer=backup_backend,
                family_id=family_id,
                family_pos_tags=family_pos_tags,
            )
            summary_result_payload = dict(result.__dict__)
            summary_result_payload["gold_decision"] = (
                str(case.get("gold_decision") or "").strip().lower()
            )
            summary_result_payload["gold_winner"] = str(case.get("gold_winner") or "").strip()
            if summary_result_payload["gold_decision"] not in {"replace", "abstain"}:
                summary_result_payload["gold_decision"] = (
                    "replace"
                    if summary_result_payload["gold_winner"]
                    == str(active.get("sense_id") or "").strip()
                    else "abstain"
                )
            if not summary_result_payload["gold_winner"] or summary_result_payload[
                "gold_winner"
            ] in {
                "none",
                "abstain",
            }:
                summary_result_payload["gold_winner_type"] = "none"
            elif summary_result_payload["gold_winner"] == str(active.get("sense_id") or "").strip():
                summary_result_payload["gold_winner_type"] = "active"
            else:
                summary_result_payload["gold_winner_type"] = "shadow"
            summary_result = SimpleNamespace(**summary_result_payload)
            row_payload = {
                "case_id": summary_result.case_id,
                "family_id": summary_result.family_id,
                "trigger": trigger,
                "sentence": str(case.get("sentence") or "").strip(),
                "source_phrase": str(case.get("source_phrase") or "").strip(),
                "gold_decision": summary_result.gold_decision,
                "gold_winner": summary_result.gold_winner,
                "gold_winner_type": summary_result.gold_winner_type,
                "predicted_decision": summary_result.predicted_decision,
                "predicted_winner": summary_result.predicted_winner,
                "predicted_winner_type": summary_result.predicted_winner_type,
                "active_score": result.active_score,
                "strongest_shadow_score": result.strongest_shadow_score,
                "margin": result.margin,
                "strongest_shadow_id": result.strongest_shadow_id,
                "context_text": result.context_text,
                "active_evidence_text": result.active_evidence_text,
                "strongest_shadow_evidence_text": result.strongest_shadow_evidence_text,
                "phrase_preemption_hit": bool(result.phrase_preemption_hit),
                "matched_phrase_pattern": result.matched_phrase_pattern,
                "phrase_reason_code": result.phrase_reason_code,
                "active_rescue_mode": resolved_active_rescue_mode,
                "active_rescue_applied": bool(result.active_rescue_applied),
                "active_rescue_reason_code": result.active_rescue_reason_code,
                "active_rescue_primary_margin": result.active_rescue_primary_margin,
                "active_rescue_backup_margin": result.active_rescue_backup_margin,
                "active_rescue_backup_predicted_decision": result.active_rescue_backup_predicted_decision,
                "active_rescue_backup_predicted_winner": result.active_rescue_backup_predicted_winner,
                "active_rescue_backup_evidence_view": result.active_rescue_backup_evidence_view,
                "slice_tags": _normalize_string_list(case.get("slice_tags")),
                "slice_dimensions": _normalize_slice_dimensions(case.get("slice_dimensions")),
                "notes": str(case.get("notes") or "").strip(),
            }
            row_results.append(row_payload)
            _accumulate_sentence_veto_summary(summary, result=summary_result)
            _accumulate_sentence_veto_summary(family_entry["summary"], result=summary_result)
            winner_type_entry = gold_winner_type_breakdown.setdefault(
                summary_result.gold_winner_type,
                {
                    "gold_winner_type": summary_result.gold_winner_type,
                    "summary": _new_sentence_veto_summary(),
                },
            )
            _accumulate_sentence_veto_summary(winner_type_entry["summary"], result=summary_result)
            for slice_tag in row_payload["slice_tags"]:
                slice_tag_entry = slice_tag_breakdown.setdefault(
                    slice_tag,
                    {
                        "slice_tag": slice_tag,
                        "summary": _new_sentence_veto_summary(),
                    },
                )
                _accumulate_sentence_veto_summary(
                    slice_tag_entry["summary"],
                    result=summary_result,
                )
            if (
                summary_result.predicted_decision == "replace"
                and summary_result.gold_decision != "replace"
            ):
                _append_sample(harmful_replace_rows, row_payload)
            if (
                summary_result.predicted_decision != "replace"
                and summary_result.gold_decision == "replace"
            ):
                _append_sample(false_abstain_rows, row_payload)
            if (
                summary_result.gold_winner_type in {"active", "shadow"}
                and summary_result.predicted_winner != summary_result.gold_winner
            ):
                _append_sample(winner_error_rows, row_payload)

    _finalize_sentence_veto_summary(summary)
    family_breakdown_rows = _finalize_sentence_veto_breakdown_rows(
        tuple(family_breakdown.values()),
        primary_sort_key="family_id",
    )
    slice_tag_breakdown_rows = _finalize_sentence_veto_breakdown_rows(
        tuple(slice_tag_breakdown.values()),
        primary_sort_key="slice_tag",
        sort_by_cases_desc=True,
    )
    winner_type_breakdown_rows = _finalize_sentence_veto_breakdown_rows(
        tuple(gold_winner_type_breakdown.values()),
        primary_sort_key="gold_winner_type",
        preferred_order=("active", "shadow", "none"),
    )
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(dataset.get("pair") or "").strip(),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "config": {
            "scorer_id": scorer_id,
            "model_name": model_name,
            "context_view": context_view,
            "evidence_view": evidence_view,
            "min_active_score": float(min_active_score),
            "min_margin": float(min_margin),
            "phrase_control_mode": phrase_control_mode,
            "active_rescue_mode": resolved_active_rescue_mode,
            "window_tokens": int(window_tokens),
            "mask_token": str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
        },
        "summary": summary,
        "family_breakdown": family_breakdown_rows,
        "slice_tag_breakdown": slice_tag_breakdown_rows,
        "gold_winner_type_breakdown": winner_type_breakdown_rows,
        "row_results": row_results,
        "sample_harmful_replace_rows": harmful_replace_rows,
        "sample_false_abstain_rows": false_abstain_rows,
        "sample_winner_error_rows": winner_error_rows,
    }


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
