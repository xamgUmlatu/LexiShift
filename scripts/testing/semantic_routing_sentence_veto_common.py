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

SENTENCE_VETO_PHRASE_GUARD_POS_SCOPES = (
    "family_all",
    "active_only",
)

DEFAULT_SENTENCE_VETO_DATASET = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_sentence_veto_v10.json"
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
