#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
)
from lexishift_core.rulegen.semantic_routing_runtime_policy import (
    DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE,
)
from semantic_routing_sentence_veto_common import build_sentence_veto_report
from semantic_routing_sentence_veto_helpers import (
    _accumulate_sentence_veto_summary,
    _finalize_sentence_veto_summary,
    _new_sentence_veto_summary,
    _normalize_string_list,
)


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
        "en-es:sentence-veto:report:001",
        "en-es:sentence-veto:report:002",
        "en-es:sentence-veto:report:005",
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
