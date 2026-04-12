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
    build_runtime_context_views,
    evaluate_runtime_veto_case,
    resolve_runtime_evidence_text,
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
DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE = "off"
SENTENCE_VETO_ACTIVE_RESCUE_MODES = (
    "off",
    "sense_label_near_tie_active_rescue",
)
_ACTIVE_RESCUE_PRIMARY_MARGIN_FLOOR = -0.02
_ACTIVE_RESCUE_BACKUP_MARGIN_FLOOR = 0.02
_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW = "sense_label"


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
            result = evaluate_runtime_veto_case(
                family_id=family_id,
                case=case,
                active_sense=active,
                shadow_senses=shadows,
                scorer=backend,
                context_view=context_view,
                evidence_view=evidence_view,
                min_active_score=min_active_score,
                min_margin=min_margin,
                phrase_control_mode=phrase_control_mode,
                family_pos_tags=family_pos_tags,
                window_tokens=window_tokens,
                mask_token=mask_token,
            )
            rescue_backup_result = None
            active_rescue_applied = False
            active_rescue_reason_code = ""
            summary_result_payload = dict(result.__dict__)
            summary_result_payload["active_rescue_applied"] = False
            summary_result_payload["active_rescue_reason_code"] = ""
            summary_result = SimpleNamespace(**summary_result_payload)
            if (
                backup_backend is not None
                and result.predicted_decision != "replace"
                and not result.phrase_preemption_hit
                and float(result.margin) >= _ACTIVE_RESCUE_PRIMARY_MARGIN_FLOOR
            ):
                rescue_backup_result = evaluate_runtime_veto_case(
                    family_id=family_id,
                    case=case,
                    active_sense=active,
                    shadow_senses=shadows,
                    scorer=backup_backend,
                    context_view=context_view,
                    evidence_view=_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
                    min_active_score=min_active_score,
                    min_margin=min_margin,
                    phrase_control_mode=phrase_control_mode,
                    family_pos_tags=family_pos_tags,
                    window_tokens=window_tokens,
                    mask_token=mask_token,
                )
                if (
                    rescue_backup_result.predicted_decision == "replace"
                    and rescue_backup_result.predicted_winner_type == "active"
                    and float(rescue_backup_result.margin) >= _ACTIVE_RESCUE_BACKUP_MARGIN_FLOOR
                ):
                    summary_result_payload = dict(result.__dict__)
                    summary_result_payload["predicted_decision"] = "replace"
                    summary_result_payload["predicted_winner"] = (
                        rescue_backup_result.predicted_winner
                    )
                    summary_result_payload["predicted_winner_type"] = (
                        rescue_backup_result.predicted_winner_type
                    )
                    summary_result_payload["active_rescue_applied"] = True
                    summary_result_payload["active_rescue_reason_code"] = (
                        "sense_label_near_tie_active_rescue"
                    )
                    summary_result = SimpleNamespace(**summary_result_payload)
                    active_rescue_applied = True
                    active_rescue_reason_code = "sense_label_near_tie_active_rescue"
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
                "active_rescue_applied": active_rescue_applied,
                "active_rescue_reason_code": active_rescue_reason_code,
                "active_rescue_primary_margin": result.margin,
                "active_rescue_backup_margin": (
                    rescue_backup_result.margin if rescue_backup_result is not None else None
                ),
                "active_rescue_backup_predicted_decision": (
                    rescue_backup_result.predicted_decision
                    if rescue_backup_result is not None
                    else ""
                ),
                "active_rescue_backup_predicted_winner": (
                    rescue_backup_result.predicted_winner
                    if rescue_backup_result is not None
                    else ""
                ),
                "active_rescue_backup_evidence_view": (
                    _ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW if rescue_backup_result is not None else ""
                ),
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
