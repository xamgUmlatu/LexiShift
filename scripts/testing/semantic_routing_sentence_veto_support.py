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
    _safe_rate,
)
from semantic_routing_sentence_veto_reporting import (  # noqa: E402
    compute_sentence_veto_objective,
    render_sentence_veto_phrase_leak_probe_markdown as _render_sentence_veto_phrase_leak_probe_markdown,
    render_sentence_veto_ladder_markdown as _render_sentence_veto_ladder_markdown,
    render_sentence_veto_markdown as _render_sentence_veto_markdown,
    render_sentence_veto_sweep_markdown as _render_sentence_veto_sweep_markdown,
    render_sentence_veto_weak_active_probe_markdown as _render_sentence_veto_weak_active_probe_markdown,
    select_best_sentence_veto_objective_row,
    sentence_veto_sweep_rank_key,
)

render_sentence_veto_markdown = _render_sentence_veto_markdown
render_sentence_veto_sweep_markdown = _render_sentence_veto_sweep_markdown
render_sentence_veto_ladder_markdown = _render_sentence_veto_ladder_markdown
render_sentence_veto_weak_active_probe_markdown = _render_sentence_veto_weak_active_probe_markdown
render_sentence_veto_phrase_leak_probe_markdown = _render_sentence_veto_phrase_leak_probe_markdown

SENTENCE_VETO_PHRASE_GUARD_POS_SCOPES = (
    "family_all",
    "active_only",
)

DEFAULT_SENTENCE_VETO_DATASET = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_routing_cases" / "en_es_sentence_veto_v9.json"
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
DEFAULT_SENTENCE_VETO_LADDER_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_ladder_latest.json"
)
DEFAULT_SENTENCE_VETO_LADDER_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_ladder_latest.md"
)
DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_routing_sentence_veto_weak_active_latest.json"
)
DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_weak_active_latest.md"
)
DEFAULT_SENTENCE_VETO_PHRASE_LEAK_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_routing_sentence_veto_phrase_leak_latest.json"
)
DEFAULT_SENTENCE_VETO_PHRASE_LEAK_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_phrase_leak_latest.md"
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


def _resolve_sentence_veto_phrase_guard_pos_tags(
    *,
    active_sense: Mapping[str, object],
    shadow_senses: Sequence[Mapping[str, object]],
    phrase_guard_pos_scope: str,
) -> tuple[str, ...]:
    resolved_scope = str(phrase_guard_pos_scope or "").strip() or "family_all"
    if resolved_scope not in SENTENCE_VETO_PHRASE_GUARD_POS_SCOPES:
        raise ValueError(
            f"Unsupported sentence-veto phrase guard pos scope: {resolved_scope!r}; "
            f"expected one of {SENTENCE_VETO_PHRASE_GUARD_POS_SCOPES!r}"
        )
    if resolved_scope == "active_only":
        active_pos = str(active_sense.get("canonical_pos") or "").strip()
        return (active_pos,) if active_pos else ()
    return tuple(
        {
            str(value or "").strip()
            for value in (
                active_sense.get("canonical_pos"),
                *(shadow.get("canonical_pos") for shadow in shadow_senses),
            )
            if str(value or "").strip()
        }
    )


def build_sentence_veto_report(
    *,
    dataset_path: Path,
    scorer_id: str,
    context_view: str = DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    evidence_view: str = DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    min_active_score: float = DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    phrase_control_mode: str = DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,
    phrase_guard_pos_scope: str = "family_all",
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
        family_pos_tags = list(
            _resolve_sentence_veto_phrase_guard_pos_tags(
                active_sense=active,
                shadow_senses=shadows,
                phrase_guard_pos_scope=phrase_guard_pos_scope,
            )
        )
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
            "phrase_guard_pos_scope": str(phrase_guard_pos_scope or "").strip() or "family_all",
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


def build_sentence_veto_weak_active_probe_report(
    *,
    dataset_path: Path,
    scorer_id: str = "sentence_transformer_cosine",
    context_view: str = "masked_sentence",
    evidence_view: str = "all_evidence_text",
    min_active_score: float = 0.0,
    min_margin: float = 0.0,
    phrase_control_mode: str = "noun_family_frame_guard",
    active_rescue_mode: str = "sense_label_near_tie_active_rescue",
    overlay_primary_margin_floors: Sequence[float] = (-0.02, -0.03, -0.04, -0.05),
    overlay_backup_margin_floor: float = 0.02,
    focus_slice_tags: Sequence[str] = ("weak_active_support",),
    explicit_focus_case_ids: Sequence[str] = (
        "en-es:sentence-veto:ball:002",
        "en-es:sentence-veto:plant:002",
    ),
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    current_default_report = build_sentence_veto_report(
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
    primary_no_rescue_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    masked_sense_label_primary_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view="sense_label",
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    raw_sentence_primary_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view="raw_sentence",
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    raw_window_primary_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view="raw_window",
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )

    focus_case_ids = _collect_sentence_veto_focus_case_ids(
        current_default_report,
        focus_slice_tags=focus_slice_tags,
        explicit_focus_case_ids=explicit_focus_case_ids,
    )
    overlay_candidates = [
        _simulate_sentence_veto_rescue_overlay_row(
            primary_report=primary_no_rescue_report,
            backup_report=masked_sense_label_primary_report,
            primary_margin_floor=float(primary_margin_floor),
            backup_margin_floor=float(overlay_backup_margin_floor),
            focus_case_ids=focus_case_ids,
        )
        for primary_margin_floor in sorted(
            {
                float(value)
                for value in overlay_primary_margin_floors
                if isinstance(value, (int, float))
            }
        )
    ]
    overlay_candidates.sort(key=sentence_veto_overlay_rank_key)
    zero_harmful_overlay = next(
        (
            dict(candidate)
            for candidate in overlay_candidates
            if int(
                (
                    candidate.get("summary")
                    if isinstance(candidate.get("summary"), Mapping)
                    else {}
                ).get("harmful_replace_count")
                or 0
            )
            == 0
        ),
        None,
    )
    selected_overlay = (
        dict(zero_harmful_overlay)
        if isinstance(zero_harmful_overlay, Mapping)
        else dict(overlay_candidates[0])
        if overlay_candidates
        else None
    )
    selected_overlay_is_zero_harmful = isinstance(zero_harmful_overlay, Mapping)

    config_entries = [
        _build_sentence_veto_weak_active_probe_config_entry(
            report=current_default_report,
            config_id="current_default",
            label="Current default runtime row",
            description=(
                "Masked sentence plus all-evidence primary, phrase guard, and the current near-tie "
                "sense-label rescue."
            ),
            focus_case_ids=focus_case_ids,
        ),
        _build_sentence_veto_weak_active_probe_config_entry(
            report=masked_sense_label_primary_report,
            config_id="masked_sense_label_primary",
            label="Masked sentence plus sense-label primary",
            description=(
                "Swaps the primary evidence surface to sense labels while keeping the same masked "
                "context and hard thresholds."
            ),
            focus_case_ids=focus_case_ids,
        ),
        _build_sentence_veto_weak_active_probe_config_entry(
            report=raw_sentence_primary_report,
            config_id="raw_sentence_primary",
            label="Raw sentence plus all-evidence primary",
            description=(
                "Broadens the primary context view to the full raw sentence while leaving the "
                "evidence surface unchanged."
            ),
            focus_case_ids=focus_case_ids,
        ),
        _build_sentence_veto_weak_active_probe_config_entry(
            report=raw_window_primary_report,
            config_id="raw_window_primary",
            label="Raw window plus all-evidence primary",
            description=(
                "Uses a local raw-context window as the primary view to test whether the park-like "
                "misses are recoverable via broader lexical context."
            ),
            focus_case_ids=focus_case_ids,
        ),
    ]
    selected_overlay_label = ""
    if selected_overlay is not None:
        selected_overlay_label = (
            "Best zero-harmful rescue overlay"
            if selected_overlay_is_zero_harmful
            else "Best bounded rescue overlay"
        )
        config_entries.append(
            {
                **selected_overlay,
                "label": selected_overlay_label,
                "description": (
                    "Keeps the current masked all-evidence primary, then widens the rescue trigger "
                    "floor while requiring an active winner from the sense-label backup."
                ),
            }
        )

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(current_default_report.get("pair") or "").strip(),
        "dataset_id": str(current_default_report.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "focus_slice_tags": _normalize_string_list(focus_slice_tags),
        "focus_case_ids": focus_case_ids,
        "explicit_focus_case_ids": _normalize_string_list(explicit_focus_case_ids),
        "base_config": dict(current_default_report.get("config") or {}),
        "configurations": config_entries,
        "overlay_candidates": overlay_candidates,
        "selected_overlay_config_id": (
            str(selected_overlay.get("config_id") or "").strip()
            if isinstance(selected_overlay, Mapping)
            else ""
        ),
        "selected_overlay_label": selected_overlay_label,
        "selected_overlay_is_zero_harmful": bool(selected_overlay_is_zero_harmful),
        "best_zero_harmful_overlay_config_id": (
            str(zero_harmful_overlay.get("config_id") or "").strip()
            if isinstance(zero_harmful_overlay, Mapping)
            else ""
        ),
        "zero_harmful_overlay_available": bool(selected_overlay_is_zero_harmful),
    }


def sentence_veto_overlay_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
    return (
        int(summary.get("harmful_replace_count") or 0),
        int(summary.get("false_abstain_count") or 0),
        -float(summary.get("decision_accuracy") or 0.0),
        -float(summary.get("replace_recall") or 0.0),
        -int(summary.get("active_rescue_applied_count") or 0),
        -float(row.get("primary_margin_floor") or 0.0),
    )


def _collect_sentence_veto_focus_case_ids(
    report: Mapping[str, object],
    *,
    focus_slice_tags: Sequence[str],
    explicit_focus_case_ids: Sequence[str],
) -> list[str]:
    row_results = (
        report.get("row_results")
        if isinstance(report.get("row_results"), Sequence)
        and not isinstance(report.get("row_results"), (str, bytes))
        else []
    )
    requested_tags = set(_normalize_string_list(focus_slice_tags))
    explicit_case_ids = _normalize_string_list(explicit_focus_case_ids)
    focus_case_ids: list[str] = []
    for raw_row in row_results:
        if not isinstance(raw_row, Mapping):
            continue
        case_id = str(raw_row.get("case_id") or "").strip()
        slice_tags = set(_normalize_string_list(raw_row.get("slice_tags")))
        if case_id and requested_tags.intersection(slice_tags) and case_id not in focus_case_ids:
            focus_case_ids.append(case_id)
    for case_id in explicit_case_ids:
        if case_id and case_id not in focus_case_ids:
            focus_case_ids.append(case_id)
    return focus_case_ids


def _build_sentence_veto_weak_active_probe_config_entry(
    *,
    report: Mapping[str, object],
    config_id: str,
    label: str,
    description: str,
    focus_case_ids: Sequence[str],
) -> dict[str, object]:
    row_index = _index_sentence_veto_rows(report)
    summary = dict(report.get("summary") or {})
    return {
        "config_id": config_id,
        "label": label,
        "kind": "runtime_row",
        "description": description,
        "config": dict(report.get("config") or {}),
        "summary": summary,
        "focus_cases": [
            _build_sentence_veto_focus_case_payload(row_index[case_id])
            for case_id in focus_case_ids
            if case_id in row_index
        ],
        "harmful_replace_case_ids": [
            case_id
            for case_id, row in row_index.items()
            if str(row.get("predicted_decision") or "").strip().lower() == "replace"
            and str(row.get("gold_decision") or "").strip().lower() != "replace"
        ],
        "false_abstain_case_ids": [
            case_id
            for case_id, row in row_index.items()
            if str(row.get("predicted_decision") or "").strip().lower() != "replace"
            and str(row.get("gold_decision") or "").strip().lower() == "replace"
        ],
        "active_rescue_case_ids": [
            case_id for case_id, row in row_index.items() if bool(row.get("active_rescue_applied"))
        ],
        "phrase_preemption_case_ids": [
            case_id for case_id, row in row_index.items() if bool(row.get("phrase_preemption_hit"))
        ],
    }


def _simulate_sentence_veto_rescue_overlay_row(
    *,
    primary_report: Mapping[str, object],
    backup_report: Mapping[str, object],
    primary_margin_floor: float,
    backup_margin_floor: float,
    focus_case_ids: Sequence[str],
) -> dict[str, object]:
    simulated_rows = build_sentence_veto_rescue_overlay_case_rows(
        primary_report=primary_report,
        backup_report=backup_report,
        primary_margin_floor=primary_margin_floor,
        backup_margin_floor=backup_margin_floor,
    )
    summary = _new_sentence_veto_summary()
    rescued_case_ids: list[str] = []
    harmful_replace_case_ids: list[str] = []
    false_abstain_case_ids: list[str] = []
    for simulated_row in simulated_rows:
        case_id = str(simulated_row.get("case_id") or "").strip()
        if bool(simulated_row.get("active_rescue_applied")) and case_id:
            rescued_case_ids.append(case_id)
        if (
            str(simulated_row.get("predicted_decision") or "").strip().lower() == "replace"
            and str(simulated_row.get("gold_decision") or "").strip().lower() != "replace"
            and case_id
        ):
            harmful_replace_case_ids.append(case_id)
        if (
            str(simulated_row.get("predicted_decision") or "").strip().lower() != "replace"
            and str(simulated_row.get("gold_decision") or "").strip().lower() == "replace"
            and case_id
        ):
            false_abstain_case_ids.append(case_id)
        _accumulate_sentence_veto_summary(
            summary,
            result=SimpleNamespace(
                gold_decision=str(simulated_row.get("gold_decision") or "").strip().lower(),
                gold_winner=str(simulated_row.get("gold_winner") or "").strip(),
                gold_winner_type=str(simulated_row.get("gold_winner_type") or "").strip(),
                predicted_decision=str(simulated_row.get("predicted_decision") or "").strip(),
                predicted_winner=str(simulated_row.get("predicted_winner") or "").strip(),
                phrase_preemption_hit=bool(simulated_row.get("phrase_preemption_hit")),
                active_rescue_applied=bool(simulated_row.get("active_rescue_applied")),
            ),
        )
    _finalize_sentence_veto_summary(summary)
    row_index = {str(row.get("case_id") or "").strip(): row for row in simulated_rows}
    return {
        "config_id": (
            f"overlay:p={float(primary_margin_floor):.2f}:b={float(backup_margin_floor):.2f}"
        ),
        "kind": "simulated_rescue_overlay",
        "config": {
            "primary_context_view": "masked_sentence",
            "primary_evidence_view": "all_evidence_text",
            "backup_evidence_view": "sense_label",
            "phrase_control_mode": "noun_family_frame_guard",
            "primary_margin_floor": float(primary_margin_floor),
            "backup_margin_floor": float(backup_margin_floor),
        },
        "summary": summary,
        "focus_cases": [
            _build_sentence_veto_focus_case_payload(row_index[case_id])
            for case_id in focus_case_ids
            if case_id in row_index
        ],
        "harmful_replace_case_ids": harmful_replace_case_ids,
        "false_abstain_case_ids": false_abstain_case_ids,
        "active_rescue_case_ids": rescued_case_ids,
        "phrase_preemption_case_ids": [
            str(row.get("case_id") or "").strip()
            for row in simulated_rows
            if bool(row.get("phrase_preemption_hit")) and str(row.get("case_id") or "").strip()
        ],
        "primary_margin_floor": float(primary_margin_floor),
        "backup_margin_floor": float(backup_margin_floor),
        "row_results": simulated_rows,
    }


def _build_sentence_veto_phrase_leak_delta(
    *,
    baseline: Mapping[str, object],
    candidate: Mapping[str, object],
) -> dict[str, object]:
    baseline_index = _index_sentence_veto_rows(baseline)
    candidate_index = _index_sentence_veto_rows(candidate)
    changed_rows: list[dict[str, object]] = []
    new_phrase_preemption_rows: list[dict[str, object]] = []
    for case_id, baseline_row in baseline_index.items():
        candidate_row = candidate_index.get(case_id)
        if not isinstance(candidate_row, Mapping):
            continue
        baseline_decision = str(baseline_row.get("predicted_decision") or "").strip()
        candidate_decision = str(candidate_row.get("predicted_decision") or "").strip()
        baseline_phrase = bool(baseline_row.get("phrase_preemption_hit"))
        candidate_phrase = bool(candidate_row.get("phrase_preemption_hit"))
        row_payload = {
            "case_id": case_id,
            "family_id": str(
                candidate_row.get("family_id") or baseline_row.get("family_id") or ""
            ).strip(),
            "sentence": str(
                candidate_row.get("sentence") or baseline_row.get("sentence") or ""
            ).strip(),
            "gold_decision": str(
                candidate_row.get("gold_decision") or baseline_row.get("gold_decision") or ""
            ).strip(),
            "baseline_predicted_decision": baseline_decision,
            "candidate_predicted_decision": candidate_decision,
            "baseline_phrase_preemption_hit": baseline_phrase,
            "candidate_phrase_preemption_hit": candidate_phrase,
            "baseline_phrase_reason_code": str(
                baseline_row.get("phrase_reason_code") or ""
            ).strip(),
            "candidate_phrase_reason_code": str(
                candidate_row.get("phrase_reason_code") or ""
            ).strip(),
        }
        if baseline_decision != candidate_decision:
            changed_rows.append(row_payload)
        elif candidate_phrase and not baseline_phrase:
            new_phrase_preemption_rows.append(row_payload)
    return {
        "changed_decision_rows": changed_rows,
        "changed_decision_case_ids": [
            str(row.get("case_id") or "").strip() for row in changed_rows
        ],
        "new_phrase_preemption_rows": new_phrase_preemption_rows,
        "new_phrase_preemption_case_ids": [
            str(row.get("case_id") or "").strip() for row in new_phrase_preemption_rows
        ],
    }


def build_sentence_veto_phrase_leak_probe_report(
    *,
    dataset_path: Path,
    scorer_id: str = "sentence_transformer_cosine",
    context_view: str = "masked_sentence",
    evidence_view: str = "all_evidence_text",
    min_active_score: float = 0.0,
    min_margin: float = 0.0,
    phrase_control_mode: str = "noun_family_frame_guard",
    active_rescue_mode: str = "sense_label_near_tie_active_rescue",
    overlay_primary_margin_floor: float = -0.05,
    overlay_backup_margin_floor: float = 0.02,
    explicit_focus_case_ids: Sequence[str] = (
        "en-es:sentence-veto:play:001",
        "en-es:sentence-veto:play:002",
        "en-es:sentence-veto:play:003",
        "en-es:sentence-veto:play:004",
        "en-es:sentence-veto:play:005",
        "en-es:sentence-veto:watch:001",
        "en-es:sentence-veto:watch:002",
        "en-es:sentence-veto:watch:003",
        "en-es:sentence-veto:watch:004",
        "en-es:sentence-veto:watch:005",
        "en-es:sentence-veto:drink:001",
        "en-es:sentence-veto:drink:002",
        "en-es:sentence-veto:drink:005",
        "en-es:sentence-veto:park:001",
        "en-es:sentence-veto:park:005",
        "en-es:sentence-veto:check:001",
        "en-es:sentence-veto:check:002",
        "en-es:sentence-veto:check:005",
        "en-es:sentence-veto:order:001",
        "en-es:sentence-veto:order:002",
        "en-es:sentence-veto:order:005",
        "en-es:sentence-veto:trip:001",
        "en-es:sentence-veto:trip:002",
        "en-es:sentence-veto:trip:005",
    ),
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    current_default_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        phrase_guard_pos_scope="family_all",
        active_rescue_mode=active_rescue_mode,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    active_only_default_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        phrase_guard_pos_scope="active_only",
        active_rescue_mode=active_rescue_mode,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    current_primary_no_rescue_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        phrase_guard_pos_scope="family_all",
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    active_only_primary_no_rescue_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        phrase_guard_pos_scope="active_only",
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    current_backup_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view="sense_label",
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        phrase_guard_pos_scope="family_all",
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    active_only_backup_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view="sense_label",
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_control_mode=phrase_control_mode,
        phrase_guard_pos_scope="active_only",
        active_rescue_mode=DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
        model_name=model_name,
        window_tokens=window_tokens,
        mask_token=mask_token,
    )
    focus_case_ids = _normalize_string_list(explicit_focus_case_ids)
    current_overlay = _simulate_sentence_veto_rescue_overlay_row(
        primary_report=current_primary_no_rescue_report,
        backup_report=current_backup_report,
        primary_margin_floor=float(overlay_primary_margin_floor),
        backup_margin_floor=float(overlay_backup_margin_floor),
        focus_case_ids=focus_case_ids,
    )
    active_only_overlay = _simulate_sentence_veto_rescue_overlay_row(
        primary_report=active_only_primary_no_rescue_report,
        backup_report=active_only_backup_report,
        primary_margin_floor=float(overlay_primary_margin_floor),
        backup_margin_floor=float(overlay_backup_margin_floor),
        focus_case_ids=focus_case_ids,
    )
    current_overlay["config"]["phrase_guard_pos_scope"] = "family_all"
    active_only_overlay["config"]["phrase_guard_pos_scope"] = "active_only"

    hard_row_entries = [
        _build_sentence_veto_weak_active_probe_config_entry(
            report=current_default_report,
            config_id="current_default",
            label="Current mixed-POS phrase guard",
            description=(
                "Current sentence-transformer runtime row using the family-wide POS gate. "
                "Mixed noun/verb families skip phrase preemption entirely."
            ),
            focus_case_ids=focus_case_ids,
        ),
        _build_sentence_veto_weak_active_probe_config_entry(
            report=active_only_default_report,
            config_id="active_only_phrase_guard",
            label="Active-sense noun phrase guard",
            description=(
                "Testing-only variant that anchors phrase preemption to the active sense POS "
                "for mixed noun/verb families."
            ),
            focus_case_ids=focus_case_ids,
        ),
    ]
    overlay_entries = [
        {
            **current_overlay,
            "config_id": "current_overlay",
            "label": "Current widened overlay",
            "description": ("Current bounded overlay over the mixed-POS phrase-guard primary row."),
        },
        {
            **active_only_overlay,
            "config_id": "active_only_overlay",
            "label": "Active-sense noun guard overlay",
            "description": (
                "Testing-only bounded overlay when phrase preemption uses the active-sense noun "
                "POS on mixed noun/verb families."
            ),
        },
    ]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(current_default_report.get("pair") or "").strip(),
        "dataset_id": str(current_default_report.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "focus_case_ids": focus_case_ids,
        "base_config": dict(current_default_report.get("config") or {}),
        "overlay_parameters": {
            "primary_margin_floor": float(overlay_primary_margin_floor),
            "backup_margin_floor": float(overlay_backup_margin_floor),
        },
        "hard_row_entries": hard_row_entries,
        "hard_row_delta": _build_sentence_veto_phrase_leak_delta(
            baseline=current_default_report,
            candidate=active_only_default_report,
        ),
        "overlay_entries": overlay_entries,
        "overlay_delta": _build_sentence_veto_phrase_leak_delta(
            baseline={"row_results": current_overlay.get("row_results") or ()},
            candidate={"row_results": active_only_overlay.get("row_results") or ()},
        ),
    }


def build_sentence_veto_rescue_overlay_case_rows(
    *,
    primary_report: Mapping[str, object],
    backup_report: Mapping[str, object],
    primary_margin_floor: float,
    backup_margin_floor: float,
) -> list[dict[str, object]]:
    primary_row_index = _index_sentence_veto_rows(primary_report)
    backup_row_index = _index_sentence_veto_rows(backup_report)
    simulated_rows: list[dict[str, object]] = []
    for case_id, primary_row in primary_row_index.items():
        backup_row = backup_row_index.get(case_id, {})
        predicted_decision = str(primary_row.get("predicted_decision") or "").strip().lower()
        predicted_winner = str(primary_row.get("predicted_winner") or "").strip()
        predicted_winner_type = str(primary_row.get("predicted_winner_type") or "").strip()
        active_rescue_applied = False
        if (
            predicted_decision != "replace"
            and not bool(primary_row.get("phrase_preemption_hit"))
            and float(primary_row.get("margin") or 0.0) >= float(primary_margin_floor)
            and str(backup_row.get("predicted_decision") or "").strip().lower() == "replace"
            and str(backup_row.get("predicted_winner_type") or "").strip() == "active"
            and float(backup_row.get("margin") or 0.0) >= float(backup_margin_floor)
        ):
            predicted_decision = "replace"
            predicted_winner = str(backup_row.get("predicted_winner") or "").strip()
            predicted_winner_type = str(backup_row.get("predicted_winner_type") or "").strip()
            active_rescue_applied = True
        simulated_row = {
            **primary_row,
            "predicted_decision": predicted_decision,
            "predicted_winner": predicted_winner,
            "predicted_winner_type": predicted_winner_type,
            "active_rescue_applied": active_rescue_applied,
            "active_rescue_reason_code": (
                "simulated_sense_label_near_tie_active_rescue" if active_rescue_applied else ""
            ),
            "active_rescue_backup_margin": backup_row.get("margin"),
            "active_rescue_backup_predicted_decision": backup_row.get("predicted_decision"),
            "active_rescue_backup_predicted_winner": backup_row.get("predicted_winner"),
            "active_rescue_backup_evidence_view": "sense_label",
            "active_rescue_primary_margin": primary_row.get("margin"),
            "primary_margin_floor": float(primary_margin_floor),
            "backup_margin_floor": float(backup_margin_floor),
        }
        simulated_rows.append(simulated_row)
    return simulated_rows


def _build_sentence_veto_focus_case_payload(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "case_id": str(row.get("case_id") or "").strip(),
        "family_id": str(row.get("family_id") or "").strip(),
        "gold_decision": str(row.get("gold_decision") or "").strip(),
        "gold_winner_type": str(row.get("gold_winner_type") or "").strip(),
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
        "active_score": row.get("active_score"),
        "strongest_shadow_score": row.get("strongest_shadow_score"),
        "margin": row.get("margin"),
        "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        "matched_phrase_pattern": str(row.get("matched_phrase_pattern") or "").strip(),
        "phrase_reason_code": str(row.get("phrase_reason_code") or "").strip(),
        "active_rescue_applied": bool(row.get("active_rescue_applied")),
        "active_rescue_backup_margin": row.get("active_rescue_backup_margin"),
        "active_rescue_backup_predicted_decision": row.get(
            "active_rescue_backup_predicted_decision"
        ),
        "active_rescue_backup_evidence_view": row.get("active_rescue_backup_evidence_view"),
        "slice_tags": _normalize_string_list(row.get("slice_tags")),
    }


def _index_sentence_veto_rows(report: Mapping[str, object]) -> dict[str, dict[str, object]]:
    row_results = (
        report.get("row_results")
        if isinstance(report.get("row_results"), Sequence)
        and not isinstance(report.get("row_results"), (str, bytes))
        else []
    )
    indexed: dict[str, dict[str, object]] = {}
    for raw_row in row_results:
        if not isinstance(raw_row, Mapping):
            continue
        case_id = str(raw_row.get("case_id") or "").strip()
        if case_id:
            indexed[case_id] = dict(raw_row)
    return indexed
