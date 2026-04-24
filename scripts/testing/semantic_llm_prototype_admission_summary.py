from __future__ import annotations

from typing import Mapping, Sequence


def build_prototype_summary_findings(
    config_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    lookup = {
        str(row.get("config_id") or "").strip(): row
        for row in config_rows
        if str(row.get("config_id") or "").strip()
    }
    family_guard = _summary_metrics(lookup.get("prototype_reviewed_examples_family_guard"))
    active_guard = _summary_metrics(lookup.get("prototype_reviewed_examples_active_guard"))
    phrase_containment_guard = _summary_metrics(
        lookup.get("prototype_reviewed_examples_phrase_containment_guard")
    )
    surface_pos_rescue_guard = _summary_metrics(
        lookup.get("prototype_reviewed_examples_surface_pos_rescue_guard")
    )
    phrase_prototype_guard = _summary_metrics(
        lookup.get("prototype_reviewed_examples_phrase_prototype_guard")
    )
    return {
        "family_guard_result": family_guard,
        "active_guard_result": active_guard,
        "phrase_containment_guard_result": phrase_containment_guard,
        "surface_pos_rescue_guard_result": surface_pos_rescue_guard,
        "phrase_prototype_guard_result": phrase_prototype_guard,
        "active_guard_reduces_phrase_leak_without_false_abstain": int(
            active_guard.get("harmful_replace_count") or 0
        )
        < int(family_guard.get("harmful_replace_count") or 0)
        and int(active_guard.get("false_abstain_count") or 0)
        <= int(family_guard.get("false_abstain_count") or 0),
        "phrase_prototype_guard_clears_active_guard_residue": int(
            phrase_prototype_guard.get("harmful_replace_count") or 0
        )
        < int(active_guard.get("harmful_replace_count") or 0)
        and int(phrase_prototype_guard.get("false_abstain_count") or 0)
        <= int(active_guard.get("false_abstain_count") or 0),
        "phrase_containment_avoids_phrase_prototype_overreach": int(
            phrase_containment_guard.get("harmful_replace_count") or 0
        )
        <= int(phrase_prototype_guard.get("harmful_replace_count") or 0)
        and int(phrase_containment_guard.get("false_abstain_count") or 0)
        <= int(phrase_prototype_guard.get("false_abstain_count") or 0),
        "surface_pos_rescue_clears_containment_residue": int(
            surface_pos_rescue_guard.get("harmful_replace_count") or 0
        )
        <= int(phrase_containment_guard.get("harmful_replace_count") or 0)
        and int(surface_pos_rescue_guard.get("false_abstain_count") or 0)
        < int(phrase_containment_guard.get("false_abstain_count") or 0),
    }


def build_prototype_case_matrix(
    config_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    config_lookups = {
        str(config.get("config_id") or "").strip(): {
            str(row.get("case_id") or "").strip(): row
            for row in config.get("row_results", ())
            if isinstance(row, Mapping) and str(row.get("case_id") or "").strip()
        }
        for config in config_rows
        if str(config.get("config_id") or "").strip()
    }
    focus_case_ids: set[str] = set()
    for config in config_rows:
        focus_case_ids.update(_case_id_set(config.get("harmful_replace_case_ids")))
        focus_case_ids.update(_case_id_set(config.get("false_abstain_case_ids")))
    rows: list[dict[str, object]] = []
    for case_id in sorted(focus_case_ids):
        configs = {}
        gold_decision = ""
        family_id = ""
        for config_id, lookup in config_lookups.items():
            row = lookup.get(case_id)
            if row is None:
                continue
            gold_decision = gold_decision or str(row.get("gold_decision") or "").strip()
            family_id = family_id or str(row.get("family_id") or "").strip()
            configs[config_id] = _case_prediction(row)
        rows.append(
            {
                "case_id": case_id,
                "family_id": family_id,
                "gold_decision": gold_decision,
                "configs": configs,
            }
        )
    return rows


def build_prototype_recommendation(report: Mapping[str, object]) -> str:
    findings = report.get("summary_findings")
    best_guard = {}
    if isinstance(findings, Mapping):
        best_guard = _best_summary_result(
            [
                findings.get("surface_pos_rescue_guard_result"),
                findings.get("phrase_containment_guard_result"),
            ]
        )
    scope = str(report.get("evaluation_scope") or "").strip()
    if (
        int(best_guard.get("harmful_replace_count") or 0) == 0
        and int(best_guard.get("false_abstain_count") or 0) == 0
    ):
        verdict = "clears this evaluation slice"
    else:
        verdict = "still leaves residual cases on this evaluation slice"
    source_note = _source_note(report)
    return (
        "Keep the user-facing UX binary, but move the internal experiment from a single "
        "evidence string toward prototype admission: context competes against active and "
        "shadow example frames, while phrase-control evidence can only abstain through local "
        "containment-pattern matches. "
        f"The best local guard {verdict} ({_format_metric_summary(best_guard)}) "
        f"on `{scope}`; keep broad phrase-control prototype scoring as an overreach control only. "
        f"{source_note}"
    )


def _source_note(report: Mapping[str, object]) -> str:
    source_id = str(report.get("evidence_source_id") or "").strip()
    if (
        str(report.get("evidence_source") or "").strip() == "reviewed_dataset"
        or source_id == "reviewed_sentence_veto_example_frames"
    ):
        return (
            "The reviewed examples are internal oracle data, not runtime-publishable evidence; "
            "use this as the acceptance target for external or generated example-frame sources."
        )
    batch_id = str(report.get("evidence_batch_id") or "").strip()
    source_id = source_id or "evidence_batch"
    return (
        f"The `{source_id}` batch `{batch_id}` is source evidence, but it should clear the "
        "required-family contract gate before any promotion or runtime publication claim."
    )


def _summary_metrics(config: object) -> dict[str, object]:
    if not isinstance(config, Mapping):
        return {}
    summary = config.get("summary") if isinstance(config.get("summary"), Mapping) else {}
    return {
        "decision_accuracy": _round_float(summary.get("decision_accuracy")),
        "replace_recall": _round_float(summary.get("replace_recall")),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
    }


def _best_summary_result(values: Sequence[object]) -> dict[str, object]:
    rows = [dict(value) for value in values if isinstance(value, Mapping)]
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            float(row.get("decision_accuracy") or 0.0),
            float(row.get("replace_recall") or 0.0),
            -int(row.get("harmful_replace_count") or 0),
            -int(row.get("false_abstain_count") or 0),
        ),
    )


def _case_prediction(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
        "active_score": _round_float(row.get("active_score")),
        "strongest_shadow_score": _round_float(row.get("strongest_shadow_score")),
        "phrase_control_score": _round_float(row.get("phrase_control_score")),
        "margin": _round_float(row.get("margin")),
        "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        "phrase_containment_hit": bool(row.get("phrase_containment_hit")),
        "active_rescue_applied": bool(row.get("active_rescue_applied")),
        "surface_pos_signal": str(row.get("surface_pos_signal") or "").strip(),
        "surface_pos_preemption_applied": bool(row.get("surface_pos_preemption_applied")),
    }


def _format_metric_summary(value: Mapping[str, object]) -> str:
    return (
        f"`{_pct(value.get('decision_accuracy'))}` accuracy / "
        f"`{_pct(value.get('replace_recall'))}` recall / "
        f"`{value.get('harmful_replace_count', 0)}` harmful / "
        f"`{value.get('false_abstain_count', 0)}` false abstains"
    )


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _round_float(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _case_id_set(value: object) -> set[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {str(item).strip() for item in value if str(item).strip()}
    text = str(value or "").strip()
    return {text} if text else set()
